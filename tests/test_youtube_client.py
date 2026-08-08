import pytest

from youtube_analyzer.youtube_client import canonical_url, extract_video_id, filter_search_results


@pytest.mark.parametrize(
    "value,expected",
    [
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ?t=90", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=90s", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ],
)
def test_extract_video_id(value, expected):
    assert extract_video_id(value) == expected


def test_extract_video_id_invalid_raises():
    with pytest.raises(ValueError):
        extract_video_id("not a youtube url")


def test_canonical_url():
    assert canonical_url("dQw4w9WgXcQ") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_filter_search_results_excludes_source_and_dedupes():
    entries = [
        {"id": "source0001a", "title": "Το ίδιο το πηγαίο βίντεο"},
        {"id": "related0001", "title": "Σχετικό 1"},
        {"id": "related0001", "title": "Διπλότυπο"},
        {"id": None, "title": "Χωρίς id"},
        {"id": "related0002", "title": "Σχετικό 2"},
    ]
    ids = filter_search_results(entries, exclude_video_id="source0001a", max_results=5)
    assert ids == ["related0001", "related0002"]


def test_filter_search_results_respects_max_results():
    entries = [{"id": f"vid{i:08d}"} for i in range(10)]
    ids = filter_search_results(entries, exclude_video_id="none", max_results=3)
    assert len(ids) == 3
