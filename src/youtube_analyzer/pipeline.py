"""Ενορχήστρωση: ενώνει τα I/O modules (youtube_client, transcribe, translate)
με την καθαρή λογική (chunking, summary) για να παράγει ένα πλήρες
VideoAnalysis, ή ελληνικούς υπότιτλους. Χρησιμοποιείται από το cli.py.

Απαιτεί δίκτυο (και προαιρετικά faster-whisper/deep-translator εγκατεστημένα)
— δεν καλείται από unit tests καθαρής λογικής.
"""

from __future__ import annotations

import logging
import tempfile

from .chunking import DEFAULT_CHUNK_SECONDS, build_chunks
from .models import Transcript, TranscriptSegment, VideoAnalysis
from .summary import build_topics, extract_resources
from .transcribe import DEFAULT_MODEL_SIZE

logger = logging.getLogger(__name__)


def get_transcript(
    url_or_id: str,
    asr_model: str = DEFAULT_MODEL_SIZE,
    preferred_langs: list[str] | None = None,
    force_asr: bool = False,
) -> Transcript:
    """Επιστρέφει το transcript ενός βίντεο ανεξαρτήτως γλώσσας και ανεξαρτήτως
    αν υπάρχουν ήδη υπότιτλοι: πρώτα δοκιμάζει υπάρχοντες υπότιτλους/CC σε
    οποιαδήποτε γλώσσα, αλλιώς κατεβάζει τον ήχο και τρέχει ASR (Whisper)."""
    from . import youtube_client
    from .transcribe import transcribe_audio

    if not force_asr:
        captions = youtube_client.fetch_captions(url_or_id, preferred_langs)
        if captions is not None and captions.segments:
            logger.info("Βρέθηκαν υπάρχοντες υπότιτλοι (%s, γλώσσα=%s)", captions.source, captions.language)
            return captions

    logger.info("Δεν βρέθηκαν υπότιτλοι/CC — εκτέλεση ASR (Whisper, μοντέλο=%s)...", asr_model)
    video_id = youtube_client.extract_video_id(url_or_id)
    with tempfile.TemporaryDirectory() as tmp_dir:
        audio_path = youtube_client.download_audio(url_or_id, tmp_dir)
        return transcribe_audio(audio_path, video_id, model_size=asr_model)


def analyze_video(
    url_or_id: str,
    asr_model: str = DEFAULT_MODEL_SIZE,
    chunk_seconds: float = DEFAULT_CHUNK_SECONDS,
    translate_summary: bool = True,
    max_bullets_per_topic: int = 3,
) -> VideoAnalysis:
    """Πλήρης ανάλυση ενός βίντεο: μεταδεδομένα + transcript (υπότιτλοι ή ASR)
    + θεματική περίληψη (μεταφρασμένη στα ελληνικά αν translate_summary=True
    και το βίντεο δεν είναι ήδη στα ελληνικά) + πόροι από την περιγραφή."""
    from . import youtube_client
    from .translate import translate_text_to_greek

    metadata = youtube_client.fetch_metadata(url_or_id)
    transcript = get_transcript(url_or_id, asr_model=asr_model)
    chunks = build_chunks(transcript, chunk_seconds=chunk_seconds)
    topics = build_topics(chunks, max_bullets_per_topic=max_bullets_per_topic)

    if translate_summary and transcript.language and not transcript.language.startswith("el"):
        for topic in topics:
            topic.title = translate_text_to_greek(topic.title, source_lang=transcript.language)
            topic.bullets = [translate_text_to_greek(b, source_lang=transcript.language) for b in topic.bullets]

    resources = extract_resources(metadata.description)

    return VideoAnalysis(metadata=metadata, transcript=transcript, chunks=chunks, topics=topics, resources=resources)


def build_greek_subtitles(url_or_id: str, asr_model: str = DEFAULT_MODEL_SIZE) -> list[TranscriptSegment]:
    """Παράγει χρονισμένα segments στα ελληνικά, έτοιμα για subtitles.segments_to_srt."""
    from .translate import translate_segments_to_greek

    transcript = get_transcript(url_or_id, asr_model=asr_model)
    if transcript.language and transcript.language.startswith("el"):
        return transcript.segments
    return translate_segments_to_greek(transcript.segments, source_lang=transcript.language or "auto")


def build_lesson_report(
    url_or_id: str,
    start: float,
    end: float,
    max_related: int = 5,
    fps: float = 1.0,
    crop_bottom_fraction: float | None = 0.5,
    asr_model: str = DEFAULT_MODEL_SIZE,
    library_dir: str | None = None,
):
    """Πλήρες «μάθημα»: (1) αναλύει το πηγαίο βίντεο, (2) αναζητά μόνο του
    σχετικά βίντεο στο YouTube με βάση τον τίτλο και τα αναλύει κι αυτά ώστε
    να μπουν στη βιβλιοθήκη, (3) συγκρίνει το [start, end] απόσπασμα έναντι
    όλης της βιβλιοθήκης, και (4) διαβάζει με OCR το tab/notation που
    εμφανίζεται στην οθόνη στο ίδιο διάστημα, συγχρονισμένο με τον χρόνο.

    Επιστρέφει (source: VideoAnalysis, matches: list[SegmentMatch], tab_frames: list[TabFrame]).
    """
    from . import youtube_client
    from .compare import compare_segment
    from .library import DEFAULT_LIBRARY_DIR, load_all, save_analysis
    from .ocr_tab import extract_tab_ocr

    library_dir = library_dir or DEFAULT_LIBRARY_DIR

    source = analyze_video(url_or_id, asr_model=asr_model)
    save_analysis(source, library_dir=library_dir)

    related_entries = youtube_client.search_videos(source.metadata.title, max_results=max_related + 1)
    related_ids = youtube_client.filter_search_results(
        related_entries, exclude_video_id=source.metadata.video_id, max_results=max_related
    )
    for vid in related_ids:
        try:
            related = analyze_video(vid, asr_model=asr_model)
            save_analysis(related, library_dir=library_dir)
        except Exception:
            logger.warning("Παράλειψη σχετικού βίντεο %s (αποτυχία ανάλυσης)", vid, exc_info=True)

    corpus = load_all(library_dir=library_dir)
    matches = compare_segment(source, start, end, corpus)

    tab_frames = extract_tab_ocr(url_or_id, start, end, fps=fps, crop_bottom_fraction=crop_bottom_fraction)

    return source, matches, tab_frames
