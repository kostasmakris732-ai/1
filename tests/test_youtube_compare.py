import pytest

from youtube_analyzer.chunking import build_chunks
from youtube_analyzer.compare import compare_segment
from youtube_analyzer.models import Transcript, TranscriptSegment, VideoAnalysis, VideoMetadata


def _analysis(video_id: str, title: str, texts: list[str], chunk_seconds: float = 45) -> VideoAnalysis:
    segments = []
    t = 0.0
    for text in texts:
        dur = 20.0
        segments.append(TranscriptSegment(start=t, end=t + dur, text=text))
        t += dur
    transcript = Transcript(video_id=video_id, language="el", source="captions", segments=segments)
    chunks = build_chunks(transcript, chunk_seconds=chunk_seconds)
    metadata = VideoMetadata(video_id=video_id, url=f"https://youtu.be/{video_id}", title=title)
    return VideoAnalysis(metadata=metadata, transcript=transcript, chunks=chunks)


def test_compare_segment_finds_matching_video_in_corpus():
    source = _analysis(
        "source0001a",
        "Πηγαίο βίντεο",
        [
            "Καλησπέρα σε όλους, ξεκινάμε το βίντεο.",
            "Τα επιτόκια της κεντρικής τράπεζας επηρεάζουν την αγορά μετοχών.",
            "Ευχαριστώ που παρακολουθήσατε.",
        ],
    )
    related = _analysis(
        "related0001",
        "Σχετικό βίντεο για οικονομικά",
        [
            "Σήμερα θα μιλήσουμε για μαγειρική.",
            "Η αύξηση επιτοκίων από την κεντρική τράπεζα επηρεάζει άμεσα τις μετοχές.",
            "Καλή σας όρεξη.",
        ],
    )
    unrelated = _analysis(
        "unrelated01",
        "Άσχετο βίντεο",
        ["Σήμερα θα φτιάξουμε μια τούρτα σοκολάτας με φράουλες και κρέμα."],
    )

    # Το δεύτερο segment του source (20s-40s) μιλάει για επιτόκια/μετοχές.
    matches = compare_segment(source, start=20, end=40, corpus=[source, related, unrelated], top_k=5, min_score=0.05)

    assert matches, "Έπρεπε να βρεθεί τουλάχιστον ένα ταιριαστό απόσπασμα"
    assert matches[0].video_id == "related0001"
    assert all(m.video_id != "source0001a" for m in matches)  # δεν συγκρίνεται με τον εαυτό του


def test_compare_segment_raises_on_empty_range():
    source = _analysis("source0002a", "Πηγαίο", ["Κάποιο κείμενο εδώ."])
    with pytest.raises(ValueError):
        compare_segment(source, start=1000, end=1010, corpus=[source])


def test_compare_segment_empty_corpus_returns_no_matches():
    source = _analysis("source0003a", "Πηγαίο", ["Κάποιο κείμενο εδώ για δοκιμή."])
    matches = compare_segment(source, start=0, end=20, corpus=[source])
    assert matches == []
