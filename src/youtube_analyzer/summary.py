"""Εξαγωγή δομημένης περίληψης (θεματικές ενότητες + bullets) από transcript
chunks, και εξαγωγή πόρων/links από την περιγραφή του βίντεο.

Καθαρή λογική, γλωσσο-ανεξάρτητη (βασίζεται σε συχνότητα λέξεων, όχι σε
γλωσσο-ειδικά μοντέλα) — δουλεύει το ίδιο σε ελληνικά, αγγλικά ή οποιαδήποτε
άλλη γλώσσα με λατινικό/ελληνικό/κυριλλικό αλφάβητο. Καμία δικτυακή κλήση.
"""

from __future__ import annotations

import re
from collections import Counter

from .models import TextChunk, TopicSection

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+")
_WORD_RE = re.compile(r"\w+", re.UNICODE)
_URL_RE = re.compile(r"https?://[^\s<>\)\]\"']+")

MAX_TITLE_CHARS = 80


def split_sentences(text: str) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def _word_frequencies(sentences: list[str]) -> Counter:
    freq: Counter = Counter()
    for sent in sentences:
        for w in _WORD_RE.findall(sent.lower()):
            if len(w) > 2:  # φιλτράρει άρθρα/μόρια κοντών λέξεων, ανεξαρτήτως γλώσσας
                freq[w] += 1
    return freq


def _score_sentence(sentence: str, freq: Counter) -> float:
    words = [w for w in _WORD_RE.findall(sentence.lower()) if len(w) > 2]
    if not words:
        return 0.0
    return sum(freq[w] for w in words) / len(words)


def top_sentences(text: str, max_sentences: int = 3) -> list[str]:
    """Εξαγωγική περίληψη: επιλέγει τις πιο «αντιπροσωπευτικές» προτάσεις
    (υψηλότερη μέση συχνότητα λέξεων) διατηρώντας τη σειρά εμφάνισής τους."""
    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return sentences

    freq = _word_frequencies(sentences)
    scored = [(i, s, _score_sentence(s, freq)) for i, s in enumerate(sentences)]
    top = sorted(scored, key=lambda t: t[2], reverse=True)[:max_sentences]
    top_sorted_by_position = sorted(top, key=lambda t: t[0])
    return [s for _, s, _ in top_sorted_by_position]


def _make_title(text: str) -> str:
    sentences = split_sentences(text)
    title = sentences[0] if sentences else text
    if len(title) > MAX_TITLE_CHARS:
        title = title[:MAX_TITLE_CHARS].rsplit(" ", 1)[0] + "…"
    return title


def build_topics(chunks: list[TextChunk], max_bullets_per_topic: int = 3) -> list[TopicSection]:
    """Χτίζει μία θεματική ενότητα ανά chunk, με τίτλο (πρώτη πρόταση) και
    bullets (εξαγωγική περίληψη του chunk)."""
    topics = []
    for chunk in chunks:
        if not chunk.text.strip():
            continue
        bullets = top_sentences(chunk.text, max_sentences=max_bullets_per_topic)
        topics.append(
            TopicSection(title=_make_title(chunk.text), start=chunk.start, end=chunk.end, bullets=bullets)
        )
    return topics


def extract_resources(description: str) -> list[tuple[str, str]]:
    """Εξάγει (ετικέτα, URL) ζεύγη από την περιγραφή ενός βίντεο.

    Η ετικέτα είναι η λέξη/φράση που προηγείται του URL στην ίδια γραμμή
    (π.χ. "Site: https://..." -> "Site"), αλλιώς το domain name.
    """
    resources: list[tuple[str, str]] = []
    for line in description.splitlines():
        for m in _URL_RE.finditer(line):
            url = m.group(0).rstrip(".,;:")
            prefix = line[: m.start()].strip(" -•*:\t")
            if prefix and len(prefix) <= 60:
                label = prefix
            else:
                domain_m = re.search(r"https?://(?:www\.)?([^/]+)", url)
                label = domain_m.group(1) if domain_m else url
            resources.append((label, url))
    return resources
