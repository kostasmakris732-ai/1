"""Ομαδοποίηση λεπτόκοκκων transcript segments σε χοντρόκοκκα TextChunks.

Τα chunks είναι η μονάδα πάνω στην οποία γίνεται η θεματική περίληψη και η
σύγκριση/αντιστοίχιση αποσπασμάτων μεταξύ βίντεο (compare.py). Καθαρή λογική.
"""

from __future__ import annotations

from .models import TextChunk, Transcript

DEFAULT_CHUNK_SECONDS = 45.0


def build_chunks(transcript: Transcript, chunk_seconds: float = DEFAULT_CHUNK_SECONDS) -> list[TextChunk]:
    """Ομαδοποιεί διαδοχικά segments σε chunks διάρκειας ~chunk_seconds.

    Ένα chunk κλείνει όταν η διάρκειά του ξεπεράσει το όριο· έτσι δεν κόβονται
    segments στη μέση και κάθε chunk έχει ρεαλιστική χρονική αγκύρωση.
    """
    chunks: list[TextChunk] = []
    cur_texts: list[str] = []
    cur_start: float | None = None
    cur_end: float | None = None

    for seg in transcript.segments:
        text = seg.text.strip()
        if not text:
            continue
        if cur_start is None:
            cur_start = seg.start
        cur_end = seg.end
        cur_texts.append(text)

        if cur_end - cur_start >= chunk_seconds:
            chunks.append(TextChunk(transcript.video_id, cur_start, cur_end, " ".join(cur_texts)))
            cur_texts, cur_start, cur_end = [], None, None

    if cur_texts and cur_start is not None and cur_end is not None:
        chunks.append(TextChunk(transcript.video_id, cur_start, cur_end, " ".join(cur_texts)))

    return chunks


def chunks_overlapping(chunks: list[TextChunk], start: float, end: float) -> list[TextChunk]:
    """Επιστρέφει τα chunks που επικαλύπτονται χρονικά με το [start, end]."""
    return [c for c in chunks if c.start < end and c.end > start]
