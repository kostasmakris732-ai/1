"""Δημιουργία αρχείων υποτίτλων (SRT/WebVTT) από χρονισμένα segments.

Καθαρή λογική, χωρίς I/O — τα αρχεία γράφονται από το cli.py.
"""

from __future__ import annotations

import textwrap

from .models import TranscriptSegment
from .timecode import format_srt_timestamp, format_vtt_timestamp

MAX_CHARS_PER_LINE = 42
MAX_LINES_PER_CUE = 2
MAX_CUE_DURATION_S = 7.0
MIN_CUE_DURATION_S = 1.0


def _wrap_lines(text: str) -> list[str]:
    text = " ".join(text.split())
    return textwrap.wrap(text, width=MAX_CHARS_PER_LINE, break_long_words=False) or [""]


def _split_into_cue_texts(text: str) -> list[str]:
    """Σπάει το κείμενο σε ένα ή περισσότερα cues των MAX_LINES_PER_CUE
    γραμμών, ώστε καμία γραμμή να μην ξεπερνά το MAX_CHARS_PER_LINE — αντί να
    στριμώχνει υπερβολικό κείμενο σε μία γραμμή."""
    lines = _wrap_lines(text)
    cues = [
        "\n".join(lines[i : i + MAX_LINES_PER_CUE])
        for i in range(0, len(lines), MAX_LINES_PER_CUE)
    ]
    return cues or [""]


def normalize_cue_timing(start: float, end: float) -> tuple[float, float]:
    """Επιβάλλει ελάχιστη/μέγιστη διάρκεια cue ώστε οι υπότιτλοι να είναι ευανάγνωστοι."""
    start = max(0.0, start)
    end = max(start + MIN_CUE_DURATION_S, end)
    if end - start > MAX_CUE_DURATION_S:
        end = start + MAX_CUE_DURATION_S
    return start, end


def _cue_windows(seg: TranscriptSegment, n_cues: int) -> list[tuple[float, float]]:
    """Χωρίζει τη χρονική διάρκεια ενός segment σε n_cues ίσα διαδοχικά
    παράθυρα (όταν το κείμενο έπρεπε να σπάσει σε πάνω από ένα cue).

    Για ένα μοναδικό cue εφαρμόζεται το συνηθισμένο όριο ελάχιστης/μέγιστης
    διάρκειας· όταν σπάει σε πολλά cues, χρησιμοποιείται η πλήρη (μη
    περικομμένη) διάρκεια του segment ώστε να μη χαθεί χρόνος ανάγνωσης.
    """
    if n_cues <= 1:
        return [normalize_cue_timing(seg.start, seg.end)]

    start = max(0.0, seg.start)
    end = max(start + MIN_CUE_DURATION_S, seg.end)
    span = (end - start) / n_cues
    windows = []
    for i in range(n_cues):
        w_start = start + i * span
        w_end = start + (i + 1) * span if i < n_cues - 1 else end
        windows.append((w_start, w_end))
    return windows


def _iter_cues(segments: list[TranscriptSegment]):
    for seg in segments:
        if not seg.text.strip():
            continue
        cue_texts = _split_into_cue_texts(seg.text)
        windows = _cue_windows(seg, len(cue_texts))
        for (start, end), text in zip(windows, cue_texts):
            yield start, end, text


def segments_to_srt(segments: list[TranscriptSegment]) -> str:
    """Μετατρέπει μια λίστα segments σε περιεχόμενο αρχείου .srt."""
    blocks = [
        f"{i}\n{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}\n{text}\n"
        for i, (start, end, text) in enumerate(_iter_cues(segments), start=1)
    ]
    return "\n".join(blocks) + ("\n" if blocks else "")


def segments_to_vtt(segments: list[TranscriptSegment]) -> str:
    """Μετατρέπει μια λίστα segments σε περιεχόμενο αρχείου .vtt (WebVTT)."""
    blocks = ["WEBVTT", ""]
    for start, end, text in _iter_cues(segments):
        blocks.append(f"{format_vtt_timestamp(start)} --> {format_vtt_timestamp(end)}")
        blocks.append(text)
        blocks.append("")
    return "\n".join(blocks)
