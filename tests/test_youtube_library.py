from youtube_analyzer.library import list_video_ids, load_all, load_analysis, save_analysis
from youtube_analyzer.models import TextChunk, Transcript, TranscriptSegment, TopicSection, VideoAnalysis, VideoMetadata


def _make_analysis(video_id: str, title: str) -> VideoAnalysis:
    metadata = VideoMetadata(video_id=video_id, url=f"https://youtu.be/{video_id}", title=title, channel="Κανάλι")
    transcript = Transcript(
        video_id=video_id,
        language="el",
        source="captions",
        segments=[TranscriptSegment(start=0, end=5, text="Γεια σας.")],
    )
    chunks = [TextChunk(video_id, 0, 5, "Γεια σας.")]
    topics = [TopicSection(title="Εισαγωγή", start=0, end=5, bullets=["Γεια σας."])]
    return VideoAnalysis(metadata=metadata, transcript=transcript, chunks=chunks, topics=topics, resources=[("Site", "https://example.com")])


def test_save_and_load_roundtrip(tmp_path):
    analysis = _make_analysis("abc12345678", "Τίτλος Δοκιμής")
    save_analysis(analysis, library_dir=tmp_path)

    loaded = load_analysis("abc12345678", library_dir=tmp_path)
    assert loaded is not None
    assert loaded.metadata.title == "Τίτλος Δοκιμής"
    assert loaded.transcript.segments[0].text == "Γεια σας."
    assert loaded.chunks[0].text == "Γεια σας."
    assert loaded.topics[0].title == "Εισαγωγή"
    assert loaded.resources == [("Site", "https://example.com")]


def test_load_analysis_missing_returns_none(tmp_path):
    assert load_analysis("doesnotexist", library_dir=tmp_path) is None


def test_list_video_ids_empty_dir(tmp_path):
    assert list_video_ids(tmp_path / "nonexistent") == []


def test_list_and_load_all(tmp_path):
    save_analysis(_make_analysis("vid00000001", "Ένα"), library_dir=tmp_path)
    save_analysis(_make_analysis("vid00000002", "Δύο"), library_dir=tmp_path)

    ids = list_video_ids(tmp_path)
    assert ids == ["vid00000001", "vid00000002"]

    all_analyses = load_all(tmp_path)
    assert {a.metadata.video_id for a in all_analyses} == {"vid00000001", "vid00000002"}
