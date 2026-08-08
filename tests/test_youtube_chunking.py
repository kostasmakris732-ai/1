from youtube_analyzer.chunking import build_chunks, chunks_overlapping
from youtube_analyzer.models import TextChunk, Transcript, TranscriptSegment


def _transcript():
    segments = [
        TranscriptSegment(start=0, end=20, text="Πρώτο κομμάτι κειμένου."),
        TranscriptSegment(start=20, end=50, text="Δεύτερο κομμάτι κειμένου, μεγαλύτερο."),
        TranscriptSegment(start=50, end=70, text="Τρίτο κομμάτι."),
        TranscriptSegment(start=70, end=71, text=""),  # κενό -> αγνοείται
        TranscriptSegment(start=71, end=100, text="Τέταρτο κομμάτι, κλείνει το δεύτερο chunk."),
    ]
    return Transcript(video_id="vid1", language="el", source="captions", segments=segments)


def test_build_chunks_groups_by_duration():
    chunks = build_chunks(_transcript(), chunk_seconds=45)
    # Το πρώτο chunk κλείνει μόλις η αθροιστική διάρκεια >= 45s (0..50).
    assert chunks[0].start == 0
    assert chunks[0].end == 50
    assert "Πρώτο" in chunks[0].text and "Δεύτερο" in chunks[0].text
    # Το δεύτερο chunk μαζεύει το υπόλοιπο.
    assert chunks[1].start == 50
    assert chunks[1].end == 100
    assert "Τρίτο" in chunks[1].text and "Τέταρτο" in chunks[1].text


def test_build_chunks_empty_transcript():
    t = Transcript(video_id="v", language="el", source="captions", segments=[])
    assert build_chunks(t) == []


def test_chunks_overlapping_filters_correctly():
    chunks = [
        TextChunk("v", 0, 45, "a"),
        TextChunk("v", 45, 90, "b"),
        TextChunk("v", 90, 130, "c"),
    ]
    result = chunks_overlapping(chunks, 40, 46)
    assert [c.text for c in result] == ["a", "b"]

    result_none = chunks_overlapping(chunks, 200, 210)
    assert result_none == []
