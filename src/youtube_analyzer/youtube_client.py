"""Δικτυακή πρόσβαση στο YouTube: μεταδεδομένα, υπάρχοντες υπότιτλοι/CC, ήχος.

Όλες οι βαριές εξαρτήσεις (`yt_dlp`, `youtube_transcript_api`) γίνονται lazy
import μέσα στις συναρτήσεις, ώστε τα υπόλοιπα modules (και τα unit tests
καθαρής λογικής) να μη χρειάζονται εγκατεστημένα αυτά τα πακέτα ή πρόσβαση
στο δίκτυο.
"""

from __future__ import annotations

import re

from .models import Transcript, TranscriptSegment, VideoMetadata

_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")
_URL_PATTERNS = [
    re.compile(r"(?:v=|/)([a-zA-Z0-9_-]{11})(?:[&?/]|$)"),
]

# Οι web/mweb clients του yt-dlp πυροδοτούν συχνά το bot-check του YouTube
# ("Sign in to confirm you're not a bot") σε IP εικονικών μηχανών (π.χ.
# GitHub Actions runners). Οι android/ios clients δεν απαιτούν το ίδιο
# PO token και συνήθως το αποφεύγουν χωρίς να χρειάζονται cookies σύνδεσης.
_PLAYER_CLIENT_FALLBACK = {"youtube": {"player_client": ["android", "ios", "web"]}}


def _base_ydl_opts(**overrides) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extractor_args": _PLAYER_CLIENT_FALLBACK,
    }
    opts.update(overrides)
    return opts


def extract_video_id(url_or_id: str) -> str:
    """Εξάγει το 11-χαρακτήρων video ID από URL ή το επιστρέφει ως έχει αν
    ήδη είναι ID."""
    s = url_or_id.strip()
    if _VIDEO_ID_RE.match(s):
        return s
    for pattern in _URL_PATTERNS:
        m = pattern.search(s)
        if m:
            return m.group(1)
    raise ValueError(f"Δεν αναγνωρίστηκε YouTube video ID στο: {url_or_id!r}")


def canonical_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def fetch_metadata(url_or_id: str) -> VideoMetadata:
    """Αντλεί τίτλο, κανάλι, διάρκεια, ημερομηνία και περιγραφή μέσω yt-dlp
    (χωρίς λήψη του ίδιου του βίντεο)."""
    import yt_dlp

    video_id = extract_video_id(url_or_id)
    url = canonical_url(video_id)

    opts = _base_ydl_opts(skip_download=True)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return VideoMetadata(
        video_id=video_id,
        url=url,
        title=info.get("title", ""),
        channel=info.get("uploader") or info.get("channel") or "",
        duration_s=float(info.get("duration") or 0.0),
        upload_date=info.get("upload_date"),
        description=info.get("description") or "",
        declared_language=info.get("language"),
    )


def fetch_captions(url_or_id: str, preferred_langs: list[str] | None = None) -> Transcript | None:
    """Ανακτά υπάρχοντες υπότιτλους/CC (χειροκίνητους ή αυτόματους) σε
    ΟΠΟΙΑΔΗΠΟΤΕ διαθέσιμη γλώσσα. Επιστρέφει None αν δεν υπάρχουν καθόλου
    (π.χ. TranscriptsDisabled), οπότε καλείται ASR fallback (βλ. transcribe.py).
    """
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
    )

    video_id = extract_video_id(url_or_id)
    preferred_langs = preferred_langs or []

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except (TranscriptsDisabled, VideoUnavailable, NoTranscriptFound):
        return None

    chosen = None
    # 1) Προτίμηση σε προτιμώμενες γλώσσες, χειροκίνητοι πρώτα.
    if preferred_langs:
        try:
            chosen = transcript_list.find_manually_created_transcript(preferred_langs)
        except Exception:
            try:
                chosen = transcript_list.find_transcript(preferred_langs)
            except Exception:
                chosen = None

    # 2) Οποιαδήποτε χειροκίνητη γλώσσα.
    if chosen is None:
        for t in transcript_list:
            if not t.is_generated:
                chosen = t
                break

    # 3) Οποιαδήποτε αυτόματη γλώσσα — "ανεξαρτήτως γλώσσας".
    if chosen is None:
        for t in transcript_list:
            chosen = t
            break

    if chosen is None:
        return None

    raw = chosen.fetch()
    segments = [
        TranscriptSegment(
            start=float(item["start"]),
            end=float(item["start"]) + float(item.get("duration", 0.0)),
            text=item["text"],
            lang=chosen.language_code,
        )
        for item in raw
    ]
    return Transcript(video_id=video_id, language=chosen.language_code, source="captions", segments=segments)


def download_audio(url_or_id: str, out_dir: str) -> str:
    """Κατεβάζει μόνο τον ήχο (χωρίς video track) για χρήση ως είσοδο στο ASR
    fallback όταν δεν υπάρχουν καθόλου υπότιτλοι/CC. Επιστρέφει το path του
    παραγόμενου αρχείου ήχου."""
    import os

    import yt_dlp

    video_id = extract_video_id(url_or_id)
    url = canonical_url(video_id)
    out_template = os.path.join(out_dir, f"{video_id}.%(ext)s")

    opts = _base_ydl_opts(
        format="bestaudio/best",
        outtmpl=out_template,
        postprocessors=[{"key": "FFmpegExtractAudio", "preferredcodec": "wav", "preferredquality": "192"}],
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    return os.path.join(out_dir, f"{video_id}.wav")


def search_videos(query: str, max_results: int = 5) -> list[dict]:
    """Αναζητά στο YouTube (χωρίς API key, μέσω yt-dlp `ytsearch`) και
    επιστρέφει ελαφριά αποτελέσματα (id, title, url, ...)."""
    import yt_dlp

    opts = _base_ydl_opts(skip_download=True, extract_flat="in_playlist")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
    return info.get("entries") or []


def filter_search_results(entries: list[dict], exclude_video_id: str, max_results: int) -> list[str]:
    """Καθαρή λογική: από τα ακατέργαστα αποτελέσματα search_videos, κρατά τα
    πρώτα max_results έγκυρα video IDs, αποκλείοντας το ίδιο το πηγαίο βίντεο
    και τυχόν διπλότυπα/ελλιπείς εγγραφές."""
    seen: set[str] = set()
    ids: list[str] = []
    for entry in entries:
        vid = entry.get("id")
        if not vid or vid == exclude_video_id or vid in seen:
            continue
        seen.add(vid)
        ids.append(vid)
        if len(ids) >= max_results:
            break
    return ids
