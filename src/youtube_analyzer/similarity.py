"""Σημασιολογική (TF-IDF) αναζήτηση ομοιότητας μεταξύ αποσπασμάτων κειμένου.

Καθαρή λογική πάνω από scikit-learn — καμία δικτυακή κλήση. Χρησιμοποιείται
από το compare.py για να βρει σε ποια άλλα βίντεο/τμήματα «αναλύεται» ένα
δοσμένο απόσπασμα.
"""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Greeklish/πολυγλωσσικά stopwords δεν χρειάζονται εδώ: το TF-IDF με char n-grams
# αγνοεί σιωπηρά πολύ κοινές λέξεις (χαμηλό idf) και δουλεύει ανεξαρτήτως γλώσσας
# επειδή βασίζεται σε ακολουθίες χαρακτήρων, όχι σε γλωσσο-ειδικό tokenization.
_VECTORIZER_KWARGS = dict(
    analyzer="char_wb",
    ngram_range=(3, 5),
    min_df=1,
    sublinear_tf=True,
)


@dataclass
class ScoredIndex:
    """Ένα αποτέλεσμα σύγκρισης: δείκτης στο corpus + σκορ ομοιότητας [0, 1]."""

    index: int
    score: float


def rank_by_similarity(query_text: str, corpus_texts: list[str], top_k: int = 10, min_score: float = 0.0) -> list[ScoredIndex]:
    """Κατατάσσει τα κείμενα του corpus κατά ομοιότητα με το query_text.

    Επιστρέφει τα top_k αποτελέσματα με score >= min_score, φθίνουσα ταξινόμηση.
    Λειτουργεί ανεξαρτήτως γλώσσας (char n-gram TF-IDF): δεν απαιτεί το query
    και το corpus να είναι στην ίδια γλώσσα να λειτουργήσουν τα n-grams μεταξύ
    τους σωστά, όμως η αντιστοίχιση είναι ουσιαστική μόνο όταν συγκρίνονται
    κείμενα στην ίδια γλώσσα (π.χ. αγγλικό απόσπασμα εναντίον αγγλικών chunks).
    """
    if not corpus_texts:
        return []

    vectorizer = TfidfVectorizer(**_VECTORIZER_KWARGS)
    matrix = vectorizer.fit_transform([query_text, *corpus_texts])
    query_vec = matrix[0]
    corpus_matrix = matrix[1:]

    sims = cosine_similarity(query_vec, corpus_matrix)[0]

    ranked = sorted(
        (ScoredIndex(i, float(score)) for i, score in enumerate(sims) if score >= min_score),
        key=lambda r: r.score,
        reverse=True,
    )
    return ranked[:top_k]
