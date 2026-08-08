"""Ανάγνωση ταμπλατούρας/notation που εμφανίζεται πάνω στην εικόνα ενός
βίντεο (π.χ. μαθήματα κιθάρας/μπάσου με tab overlay), μέσω OCR σε
δειγματοληπτημένα frames — συγχρονισμένη με τον χρόνο του βίντεο.

Η `merge_tab_samples` είναι καθαρή λογική (ελέγξιμη χωρίς πραγματικό OCR):
παίρνει ακατέργαστα δείγματα (χρόνος, κείμενο OCR) — ένα ανά δειγματοληπτημένο
frame — και τα συνενώνει σε σταθερά χρονικά διαστήματα, φιλτράροντας θόρυβο
OCR (πολύ κοντό κείμενο) και ανεκτικό σε μικρές διαφορές OCR μεταξύ γειτονικών
frames του ίδιου tab (fuzzy matching).

Οι υπόλοιπες συναρτήσεις (download_clip, extract_frames, ocr_frame) κάνουν
I/O (yt-dlp, ffmpeg, tesseract) — lazy imports, καμία εκτέλεση από unit tests.
"""

from __future__ import annotations

import difflib
import re

from .models import TabFrame

DEFAULT_FPS = 1.0
DEFAULT_MIN_CHARS = 4
DEFAULT_SIMILARITY_THRESHOLD = 0.82


def _normalize(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.strip())


def _similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def merge_tab_samples(
    samples: list[tuple[float, str]],
    frame_duration: float = 1.0 / DEFAULT_FPS,
    min_chars: int = DEFAULT_MIN_CHARS,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[TabFrame]:
    """Συνενώνει διαδοχικά OCR δείγματα (χρόνος, ακατέργαστο κείμενο) σε
    TabFrames με σταθερό κείμενο, ταξινομημένα χρονικά.

    - Δείγματα με κανονικοποιημένο κείμενο μικρότερο από min_chars αγνοούνται
      (συνήθως θόρυβος OCR από κενά/μεταβατικά frames).
    - Δύο διαδοχικά δείγματα θεωρούνται «ίδιο tab» (συνενώνονται σε ένα
      TabFrame) αν η ομοιότητά τους (SequenceMatcher ratio) είναι >=
      similarity_threshold — απορροφά μικρές διαφορές OCR (π.χ. συμπίεση
      βίντεο) χωρίς να χάνεται πραγματική αλλαγή στο tab.
    """
    frames: list[TabFrame] = []
    for time, raw_text in sorted(samples, key=lambda s: s[0]):
        text = _normalize(raw_text)
        if len(text) < min_chars:
            continue

        if frames and _similar(text, frames[-1].text) >= similarity_threshold:
            frames[-1].end = time + frame_duration
            continue

        frames.append(TabFrame(start=time, end=time + frame_duration, text=text))

    return frames


def download_clip(url_or_id: str, start: float, end: float, out_dir: str) -> str:
    """Κατεβάζει (μόνο) το χρονικό διάστημα [start, end] του βίντεο ως video
    clip, για εξαγωγή frames. Επιστρέφει το path του .mp4."""
    import os

    import yt_dlp

    from .youtube_client import _base_ydl_opts, canonical_url, extract_video_id

    video_id = extract_video_id(url_or_id)
    url = canonical_url(video_id)
    out_template = os.path.join(out_dir, f"{video_id}_clip.%(ext)s")

    opts = _base_ydl_opts(
        format="bestvideo[height<=720]+bestaudio/best[height<=720]",
        outtmpl=out_template,
        download_ranges=yt_dlp.utils.download_range_func(None, [(start, end)]),
        force_keyframes_at_cuts=True,
        merge_output_format="mp4",
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    return os.path.join(out_dir, f"{video_id}_clip.mp4")


def extract_frames(video_path: str, out_dir: str, fps: float = DEFAULT_FPS) -> list[str]:
    """Εξάγει frames του clip σε σταθερό ρυθμό (fps) μέσω ffmpeg. Επιστρέφει
    τα paths των εικόνων, ταξινομημένα χρονικά."""
    import glob
    import os
    import subprocess
    from pathlib import Path

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    pattern = os.path.join(out_dir, "frame_%05d.png")
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vf", f"fps={fps}", pattern],
        check=True,
        capture_output=True,
    )
    return sorted(glob.glob(os.path.join(out_dir, "frame_*.png")))


def ocr_frame(path: str, crop_bottom_fraction: float | None = 0.5) -> str:
    """OCR ενός frame. Προαιρετικά περικόπτει μόνο το κάτω μέρος της εικόνας
    (crop_bottom_fraction), εκεί όπου συνήθως εμφανίζεται το tab overlay στα
    περισσότερα μαθήματα οργάνων — μειώνει θόρυβο OCR από το υπόλοιπο πλάνο."""
    import pytesseract
    from PIL import Image

    img = Image.open(path)
    if crop_bottom_fraction:
        w, h = img.size
        img = img.crop((0, int(h * (1 - crop_bottom_fraction)), w, h))
    return pytesseract.image_to_string(img)


def extract_tab_ocr(
    url_or_id: str,
    start: float,
    end: float,
    fps: float = DEFAULT_FPS,
    crop_bottom_fraction: float | None = 0.5,
) -> list[TabFrame]:
    """Πλήρης pipeline: κατεβάζει το κλιπ [start, end], εξάγει frames στο fps,
    κάνει OCR σε καθένα, και συνενώνει σε χρονισμένα TabFrames."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        clip_path = download_clip(url_or_id, start, end, tmp_dir)
        frame_paths = extract_frames(clip_path, tmp_dir, fps=fps)

        samples = []
        for i, path in enumerate(frame_paths):
            time = start + i / fps
            text = ocr_frame(path, crop_bottom_fraction=crop_bottom_fraction)
            samples.append((time, text))

    return merge_tab_samples(samples, frame_duration=1.0 / fps)
