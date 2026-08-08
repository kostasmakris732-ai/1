"""Σύγκριση αποσπάσματος ενός βίντεο έναντι όλων των άλλων βίντεο στη βιβλιοθήκη.

Απαντά στο ερώτημα: «το τμήμα X (start–end) αυτού του βίντεο, σε ποια άλλα
βίντεο της βιβλιοθήκης αναλύεται/συζητιέται, και σε ποιο ακριβώς τμήμα τους;»

Καθαρή λογική πάνω από similarity.py — χωρίς I/O (η βιβλιοθήκη περνιέται ήδη
φορτωμένη ως λίστα VideoAnalysis).
"""

from __future__ import annotations

from .chunking import chunks_overlapping
from .models import SegmentMatch, VideoAnalysis

DEFAULT_TOP_K = 10
DEFAULT_MIN_SCORE = 0.12
SNIPPET_MAX_CHARS = 220


def compare_segment(
    source: VideoAnalysis,
    start: float,
    end: float,
    corpus: list[VideoAnalysis],
    top_k: int = DEFAULT_TOP_K,
    min_score: float = DEFAULT_MIN_SCORE,
) -> list[SegmentMatch]:
    """Βρίσκει τα πιο όμοια σημασιολογικά αποσπάσματα σε ΑΛΛΑ βίντεο της
    βιβλιοθήκης, για το χρονικό διάστημα [start, end] του source βίντεο."""
    from .similarity import rank_by_similarity  # lazy: αποφεύγει το βαρύ sklearn import αν δεν χρειάζεται

    overlapping = chunks_overlapping(source.chunks, start, end)
    query_text = " ".join(c.text for c in overlapping).strip()
    if not query_text:
        raise ValueError(
            f"Δεν βρέθηκε περιεχόμενο transcript στο διάστημα "
            f"{start:.0f}s–{end:.0f}s του βίντεο {source.metadata.video_id!r}."
        )

    corpus_chunks = []
    chunk_owners = []
    for video in corpus:
        if video.metadata.video_id == source.metadata.video_id:
            continue
        for chunk in video.chunks:
            corpus_chunks.append(chunk)
            chunk_owners.append(video)

    ranked = rank_by_similarity(
        query_text, [c.text for c in corpus_chunks], top_k=top_k, min_score=min_score
    )

    matches = []
    for scored in ranked:
        chunk = corpus_chunks[scored.index]
        video = chunk_owners[scored.index]
        snippet = chunk.text if len(chunk.text) <= SNIPPET_MAX_CHARS else chunk.text[:SNIPPET_MAX_CHARS].rsplit(" ", 1)[0] + "…"
        matches.append(
            SegmentMatch(
                video_id=video.metadata.video_id,
                title=video.metadata.title,
                start=chunk.start,
                end=chunk.end,
                score=scored.score,
                snippet=snippet,
            )
        )
    return matches
