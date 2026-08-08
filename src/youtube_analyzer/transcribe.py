"""ASR fallback (αναγνώριση ομιλίας) μέσω faster-whisper.

Χρησιμοποιείται μόνο όταν το βίντεο ΔΕΝ έχει καθόλου υπάρχοντες υπότιτλους/CC
(δες youtube_client.fetch_captions). Το Whisper είναι πολυγλωσσικό και
ανιχνεύει αυτόματα τη γλώσσα ομιλίας — έτσι η ανάλυση δουλεύει ανεξαρτήτως
γλώσσας του βίντεο. Lazy import ώστε το πακέτο να μη χρειάζεται
εγκατεστημένο το (βαρύ) faster-whisper για ό,τι δεν το χρειάζεται.
"""

from __future__ import annotations

from .models import Transcript, TranscriptSegment

DEFAULT_MODEL_SIZE = "small"


def transcribe_audio(audio_path: str, video_id: str, model_size: str = DEFAULT_MODEL_SIZE, language: str | None = None) -> Transcript:
    """Μεταγράφει ένα αρχείο ήχου σε χρονισμένο Transcript.

    Αν language=None, το Whisper ανιχνεύει αυτόματα τη γλώσσα ομιλίας.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "Το faster-whisper δεν είναι εγκατεστημένο. Εγκατέστησέ το με "
            "`pip install faster-whisper` για να ενεργοποιηθεί το ASR fallback "
            "(απαιτείται όταν το βίντεο δεν έχει υπάρχοντες υπότιτλους)."
        ) from exc

    model = WhisperModel(model_size, compute_type="int8")
    segments_iter, info = model.transcribe(audio_path, language=language, vad_filter=True)

    segments = [
        TranscriptSegment(start=float(s.start), end=float(s.end), text=s.text.strip(), lang=info.language)
        for s in segments_iter
        if s.text.strip()
    ]
    return Transcript(video_id=video_id, language=info.language, source="asr", segments=segments)
