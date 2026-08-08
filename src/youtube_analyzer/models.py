"""Πυρηνικά δεδομενικά μοντέλα (dataclasses) — χωρίς I/O, χωρίς δικτυακές κλήσεις."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TranscriptSegment:
    """Ένα χρονισμένο απόσπασμα κειμένου μέσα σε ένα βίντεο."""

    start: float  # δευτερόλεπτα από την αρχή του βίντεο
    end: float  # δευτερόλεπτα από την αρχή του βίντεο
    text: str
    lang: str = "und"  # κωδικός γλώσσας ISO 639-1, "und" = άγνωστη

    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class Transcript:
    """Πλήρες, χρονισμένο transcript ενός βίντεο."""

    video_id: str
    language: str  # κυρίαρχη γλώσσα του transcript
    source: str  # "captions" (υπότιτλοι/CC) ή "asr" (αυτόματη αναγνώριση ομιλίας)
    segments: list[TranscriptSegment] = field(default_factory=list)

    def full_text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments if s.text.strip())

    def duration(self) -> float:
        return max((s.end for s in self.segments), default=0.0)


@dataclass
class VideoMetadata:
    """Μεταδεδομένα ενός βίντεο YouTube."""

    video_id: str
    url: str
    title: str = ""
    channel: str = ""
    duration_s: float = 0.0
    upload_date: str | None = None  # YYYYMMDD
    description: str = ""
    declared_language: str | None = None


@dataclass
class TextChunk:
    """Ένα «χοντρόκοκκο» τμήμα κειμένου (ομαδοποίηση διαδοχικών segments) —
    η μονάδα πάνω στην οποία γίνεται η σύγκριση/αντιστοίχιση μεταξύ βίντεο."""

    video_id: str
    start: float
    end: float
    text: str


@dataclass
class TopicSection:
    """Μία ενότητα/θεματική της περίληψης, με χρονική αγκύρωση στο βίντεο."""

    title: str
    start: float
    end: float
    bullets: list[str] = field(default_factory=list)


@dataclass
class VideoAnalysis:
    """Το πλήρες αποτέλεσμα ανάλυσης ενός βίντεο, έτοιμο για αποθήκευση στη
    βιβλιοθήκη και για σύγκριση με άλλα βίντεο."""

    metadata: VideoMetadata
    transcript: Transcript
    chunks: list[TextChunk] = field(default_factory=list)
    topics: list[TopicSection] = field(default_factory=list)
    resources: list[tuple[str, str]] = field(default_factory=list)  # (label, url)


@dataclass
class SegmentMatch:
    """Ένα αποτέλεσμα σύγκρισης: το εν λόγω απόσπασμα εντοπίστηκε (σημασιολογικά)
    και σε αυτό το τμήμα αυτού του άλλου βίντεο."""

    video_id: str
    title: str
    start: float
    end: float
    score: float
    snippet: str
