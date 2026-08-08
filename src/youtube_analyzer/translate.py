"""Μετάφραση transcript segments στα ελληνικά, με διατήρηση του χρονισμού.

Χρησιμοποιεί deep-translator (Google Translate web endpoint, χωρίς API key).
Lazy import — απαιτεί δίκτυο, οπότε δεν καλείται από unit tests.
"""

from __future__ import annotations

from .models import Transcript, TranscriptSegment

TARGET_LANG = "el"
_MAX_CHARS_PER_REQUEST = 4500  # όριο ασφαλείας κάτω από το ~5000 του Google Translate


def _batch_segments(segments: list[TranscriptSegment], max_chars: int) -> list[list[TranscriptSegment]]:
    """Ομαδοποιεί segments σε δέσμες που δεν ξεπερνούν το όριο χαρακτήρων,
    ώστε να γίνονται λιγότερα, μεγαλύτερα requests αντί για ένα ανά segment."""
    batches: list[list[TranscriptSegment]] = []
    current: list[TranscriptSegment] = []
    current_len = 0

    for seg in segments:
        seg_len = len(seg.text) + 1
        if current and current_len + seg_len > max_chars:
            batches.append(current)
            current, current_len = [], 0
        current.append(seg)
        current_len += seg_len

    if current:
        batches.append(current)
    return batches


_SEP = "\n‖\n"  # διαχωριστικό απίθανο να εμφανιστεί σε φυσική ομιλία


def translate_segments_to_greek(segments: list[TranscriptSegment], source_lang: str = "auto") -> list[TranscriptSegment]:
    """Μεταφράζει το κείμενο κάθε segment στα ελληνικά, διατηρώντας start/end.

    Τα segments μιας δέσμης ενώνονται με διαχωριστικό, μεταφράζονται μαζί (πιο
    αποδοτικό δικτυακά) και ξαναχωρίζονται — αν ο αριθμός γραμμών δεν ταιριάζει
    μετά τη μετάφραση (σπάνιο, λόγω αναδιατύπωσης), γίνεται fallback σε
    μετάφραση ένα-προς-ένα για εκείνη τη δέσμη.
    """
    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source=source_lang, target=TARGET_LANG)
    out: list[TranscriptSegment] = []

    for batch in _batch_segments(segments, _MAX_CHARS_PER_REQUEST):
        joined = _SEP.join(seg.text for seg in batch)
        translated = translator.translate(joined)
        parts = translated.split(_SEP.strip()) if translated else []
        parts = [p.strip("\n ") for p in parts]

        if len(parts) != len(batch):
            # Fallback: μετάφραση ένα-προς-ένα για αυτή τη δέσμη.
            parts = [translator.translate(seg.text) or "" for seg in batch]

        for seg, text in zip(batch, parts):
            out.append(TranscriptSegment(start=seg.start, end=seg.end, text=text, lang=TARGET_LANG))

    return out


def translate_transcript_to_greek(transcript: Transcript) -> Transcript:
    if transcript.language == TARGET_LANG:
        return transcript
    translated = translate_segments_to_greek(transcript.segments, source_lang=transcript.language or "auto")
    return Transcript(video_id=transcript.video_id, language=TARGET_LANG, source=transcript.source, segments=translated)


def translate_text_to_greek(text: str, source_lang: str = "auto") -> str:
    from deep_translator import GoogleTranslator

    if not text.strip():
        return text
    return GoogleTranslator(source=source_lang, target=TARGET_LANG).translate(text) or text
