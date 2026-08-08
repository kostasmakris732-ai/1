"""Μετατροπές χρόνου: parsing, μορφοποίηση, SRT timestamps, YouTube deep-links.

Καθαρή λογική, χωρίς I/O — πλήρως ελέγξιμη με unit tests.
"""

from __future__ import annotations

import re

_HMS_RE = re.compile(r"^(?:(\d+):)?(?:(\d+):)?(\d+(?:\.\d+)?)$")
_UNITS_RE = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?$", re.IGNORECASE)


def parse_timecode(value: str | float | int) -> float:
    """Δέχεται "1:23:45", "12:34", "754", "1h2m3s", "12.5" και επιστρέφει δευτερόλεπτα.

    Ρίχνει ValueError αν η μορφή δεν αναγνωρίζεται.
    """
    if isinstance(value, (int, float)):
        return float(value)

    s = value.strip()
    if not s:
        raise ValueError("Κενή τιμή χρόνου")

    m = _HMS_RE.match(s)
    if m and any(m.groups()):
        parts = [g for g in m.groups() if g is not None]
        parts = [float(p) for p in parts]
        seconds = 0.0
        for p in parts:
            seconds = seconds * 60 + p
        return seconds

    m = _UNITS_RE.match(s)
    if m and any(m.groups()):
        h, mnt, sec = m.groups()
        return float(h or 0) * 3600 + float(mnt or 0) * 60 + float(sec or 0)

    raise ValueError(f"Μη αναγνωρίσιμη μορφή χρόνου: {value!r}")


def format_timecode(seconds: float, always_hours: bool = False) -> str:
    """Επιστρέφει "MM:SS" ή "H:MM:SS" (ώρες μόνο αν χρειάζεται ή always_hours=True)."""
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h or always_hours:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_srt_timestamp(seconds: float) -> str:
    """Μορφή SRT: HH:MM:SS,mmm"""
    seconds = max(0.0, seconds)
    total_ms = int(round(seconds * 1000))
    h, rem_ms = divmod(total_ms, 3_600_000)
    m, rem_ms = divmod(rem_ms, 60_000)
    s, ms = divmod(rem_ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_vtt_timestamp(seconds: float) -> str:
    """Μορφή WebVTT: HH:MM:SS.mmm"""
    return format_srt_timestamp(seconds).replace(",", ".")


def youtube_timestamp_link(video_id_or_url: str, seconds: float) -> str:
    """Δημιουργεί ένα κλικάρισμα link YouTube που ξεκινά στο δοσμένο δευτερόλεπτο."""
    t = max(0, int(round(seconds)))
    if video_id_or_url.startswith("http://") or video_id_or_url.startswith("https://"):
        sep = "&" if "?" in video_id_or_url else "?"
        base = video_id_or_url.split("&t=")[0].split("?t=")[0]
        return f"{base}{sep}t={t}s"
    return f"https://youtu.be/{video_id_or_url}?t={t}s"
