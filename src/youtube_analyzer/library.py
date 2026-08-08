"""Τοπική «βιβλιοθήκη» ήδη αναλυμένων βίντεο (JSON ανά βίντεο).

Πάνω σε αυτή τη βιβλιοθήκη δουλεύει το compare.py: για να πούμε "αυτό το
απόσπασμα analyzeται και σε άλλα βίντεο", πρέπει πρώτα τα άλλα βίντεο να
έχουν περάσει από `analyze` και να έχουν αποθηκευτεί εδώ. Καθαρό τοπικό I/O
(δίσκος) — καμία δικτυακή κλήση.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import TextChunk, Transcript, TranscriptSegment, TopicSection, VideoAnalysis, VideoMetadata

DEFAULT_LIBRARY_DIR = "data/youtube_library"


def _analysis_path(library_dir: str | Path, video_id: str) -> Path:
    return Path(library_dir) / f"{video_id}.json"


def save_analysis(analysis: VideoAnalysis, library_dir: str | Path = DEFAULT_LIBRARY_DIR) -> Path:
    Path(library_dir).mkdir(parents=True, exist_ok=True)
    path = _analysis_path(library_dir, analysis.metadata.video_id)
    path.write_text(json.dumps(asdict(analysis), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _analysis_from_dict(d: dict) -> VideoAnalysis:
    metadata = VideoMetadata(**d["metadata"])
    transcript = Transcript(
        video_id=d["transcript"]["video_id"],
        language=d["transcript"]["language"],
        source=d["transcript"]["source"],
        segments=[TranscriptSegment(**s) for s in d["transcript"]["segments"]],
    )
    chunks = [TextChunk(**c) for c in d.get("chunks", [])]
    topics = [TopicSection(**t) for t in d.get("topics", [])]
    resources = [tuple(r) for r in d.get("resources", [])]
    return VideoAnalysis(metadata=metadata, transcript=transcript, chunks=chunks, topics=topics, resources=resources)


def load_analysis(video_id: str, library_dir: str | Path = DEFAULT_LIBRARY_DIR) -> VideoAnalysis | None:
    path = _analysis_path(library_dir, video_id)
    if not path.exists():
        return None
    return _analysis_from_dict(json.loads(path.read_text(encoding="utf-8")))


def list_video_ids(library_dir: str | Path = DEFAULT_LIBRARY_DIR) -> list[str]:
    d = Path(library_dir)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def load_all(library_dir: str | Path = DEFAULT_LIBRARY_DIR) -> list[VideoAnalysis]:
    return [a for vid in list_video_ids(library_dir) if (a := load_analysis(vid, library_dir)) is not None]
