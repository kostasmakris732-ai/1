import pytest

from youtube_analyzer.timecode import (
    format_srt_timestamp,
    format_timecode,
    format_vtt_timestamp,
    parse_timecode,
    youtube_timestamp_link,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("12:34", 12 * 60 + 34),
        ("1:02:03", 3723),
        ("754", 754),
        ("12.5", 12.5),
        ("1h2m3s", 3723),
        ("2m30s", 150),
        ("45s", 45),
    ],
)
def test_parse_timecode(text, expected):
    assert parse_timecode(text) == pytest.approx(expected)


def test_parse_timecode_numeric_passthrough():
    assert parse_timecode(90) == 90.0
    assert parse_timecode(12.5) == 12.5


def test_parse_timecode_invalid():
    with pytest.raises(ValueError):
        parse_timecode("not-a-time")


def test_format_timecode_no_hours_when_not_needed():
    assert format_timecode(90) == "01:30"
    assert format_timecode(3661) == "1:01:01"


def test_format_timecode_always_hours():
    assert format_timecode(90, always_hours=True) == "0:01:30"


def test_format_srt_timestamp():
    assert format_srt_timestamp(3723.5) == "01:02:03,500"
    assert format_srt_timestamp(0) == "00:00:00,000"


def test_format_vtt_timestamp():
    assert format_vtt_timestamp(3723.5) == "01:02:03.500"


def test_youtube_timestamp_link_from_id():
    assert youtube_timestamp_link("abc12345678", 90) == "https://youtu.be/abc12345678?t=90s"


def test_youtube_timestamp_link_from_url():
    url = "https://www.youtube.com/watch?v=abc12345678"
    assert youtube_timestamp_link(url, 90) == f"{url}&t=90s"


def test_roundtrip_parse_format():
    for s in [0, 59, 60, 3599, 3600, 7325]:
        formatted = format_timecode(s, always_hours=True)
        assert int(round(parse_timecode(formatted))) == s
