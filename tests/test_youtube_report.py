from youtube_analyzer.models import (
    SegmentMatch,
    TextChunk,
    Transcript,
    TranscriptSegment,
    TopicSection,
    VideoAnalysis,
    VideoMetadata,
)
from youtube_analyzer.report import build_analysis_markdown, build_compare_markdown


def _analysis():
    metadata = VideoMetadata(
        video_id="abc12345678",
        url="https://youtu.be/abc12345678",
        title="Δοκιμαστικό Βίντεο",
        channel="Κανάλι Δοκιμής",
        duration_s=125,
        upload_date="20260101",
        description="Site: https://example.com",
    )
    transcript = Transcript(
        video_id="abc12345678",
        language="el",
        source="captions",
        segments=[TranscriptSegment(0, 5, "Γεια σας.")],
    )
    chunks = [TextChunk("abc12345678", 0, 45, "Γεια σας.")]
    topics = [TopicSection(title="Εισαγωγή", start=0, end=45, bullets=["Καλωσορίσατε.", "Ξεκινάμε."])]
    return VideoAnalysis(metadata=metadata, transcript=transcript, chunks=chunks, topics=topics, resources=[("Site", "https://example.com")])


def test_build_analysis_markdown_contains_key_sections():
    md = build_analysis_markdown(_analysis())
    assert "# Δοκιμαστικό Βίντεο" in md
    assert "Κανάλι Δοκιμής" in md
    assert "## 📋 Περίληψη ανά θεματική ενότητα" in md
    assert "Εισαγωγή" in md
    assert "Καλωσορίσατε." in md
    assert "## 🔗 Πόροι/links από την περιγραφή" in md
    assert "https://example.com" in md
    assert "captions" not in md or "υπότιτλοι" in md  # πρέπει να εμφανίζεται η ελληνική ετικέτα πηγής


def test_build_compare_markdown_with_matches():
    source = _analysis()
    matches = [
        SegmentMatch(video_id="other0001a", title="Άλλο Βίντεο", start=30, end=60, score=0.42, snippet="κάποιο απόσπασμα κειμένου"),
    ]
    md = build_compare_markdown(source, start=0, end=45, matches=matches)
    assert "Άλλο Βίντεο" in md
    assert "42%" in md
    assert "κάποιο απόσπασμα κειμένου" in md


def test_build_compare_markdown_no_matches():
    md = build_compare_markdown(_analysis(), start=0, end=45, matches=[])
    assert "Δεν βρέθηκαν" in md
