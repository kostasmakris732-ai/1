# ΧΑΑ Financial Analyst

Αυτόματος, κανονο-βασισμένος (rule-based) χρηματοοικονομικός αναλυτής για τις
μεγάλες κεφαλαιοποιήσεις του Χρηματιστηρίου Αθηνών (ΧΑΑ). Παράγει καθημερινή
αναφορά **πριν την έναρξη** της συνεδρίασης και μπορεί να ξανατρέξει
**on-demand** οποιαδήποτε στιγμή κατά τη διάρκειά της.

> ⚠️ **Δεν αποτελεί επενδυτική συμβουλή.** Βλ. [Αποποίηση ευθύνης](#αποποίηση-ευθύνης) παρακάτω.

## Πώς δουλεύει

1. **Δεδομένα**: Άντληση ιστορικών τιμών (OHLCV) και βασικών θεμελιωδών
   στοιχείων μέσω [Yahoo Finance](https://finance.yahoo.com) (`yfinance`) για
   ~25 μετοχές μεγάλης κεφαλαιοποίησης του ΧΑΑ (`src/athex_analyst/tickers.py`).
   Τα δεδομένα έχουν **καθυστέρηση ~15-20 λεπτών**, δεν είναι tick-by-tick
   real-time feed — δεν υπάρχει δωρεάν τέτοιο feed για το ΧΑΑ.
2. **Τεχνική ανάλυση**: SMA(50/200), RSI(14), MACD, Bollinger Bands, όγκος
   συναλλαγών σε σχέση με τον μέσο όρο, θέση εντός εύρους 52 εβδομάδων.
3. **Θεμελιώδη** (best-effort, τα δεδομένα του Yahoo για ελληνικές μετοχές
   είναι συχνά ελλιπή): P/E, μερισματική απόδοση.
4. **Σκοράρισμα**: κάθε σήμα προσθέτει/αφαιρεί πόντους σε ένα διαφανές,
   εξηγήσιμο σκορ από -100 έως +100 (`src/athex_analyst/scoring.py`). Οι
   μετοχές ταξινομούνται και κατηγοριοποιούνται σε ΙΣΧΥΡΗ ΑΓΟΡΑ / ΑΓΟΡΑ /
   ΟΥΔΕΤΕΡΟ / ΑΠΟΦΥΓΗ.
5. **Έξοδος**: αναφορά Markdown (`reports/premarket.md`) + στατικό HTML
   dashboard (`reports/dashboard.html`).

Δεν υπάρχει μοντέλο πρόβλεψης ή machine learning — είναι ένα διαφανές σύνολο
κανόνων που μπορείς να διαβάσεις γραμμή-γραμμή στο `scoring.py`.

## Πριν την έναρξη + on-demand: πώς παραδίδεται

Το περιβάλλον όπου τρέχει ο Claude agent session δεν έχει γενικά πρόσβαση στο
διαδίκτυο (sandbox egress policy), οπότε η άντληση δεδομένων **δεν** μπορεί να
γίνει μέσα σε μια συνομιλία chat. Αντ' αυτού, η λογική τρέχει μέσω
**GitHub Actions** (`\.github/workflows/athex_report.yml`), το οποίο έχει
πλήρη πρόσβαση internet:

- **Προγραμματισμένο** run καθημερινά (Δευτ–Παρ) στις 06:30 UTC — πριν την
  προσυνεδρίαση του ΧΑΑ (βλ. σχόλιο στο workflow για τις ζώνες ώρας).
- **On-demand**: χειροκίνητο "Run workflow" στο GitHub Actions tab, ή ζήτησέ
  το μέσα στη συνομιλία με τον Claude agent — μπορεί να πυροδοτήσει το ίδιο
  workflow μέσω του GitHub API.

Κάθε run:
- Ενημερώνει τα `reports/premarket.md` και `reports/dashboard.html` στο repo.
- Ανοίγει (ή σχολιάζει, αν υπάρχει ήδη) ένα GitHub Issue με ετικέτα
  `athex-report` και την πλήρη αναφορά της ημέρας, ώστε να ειδοποιείσαι.
- Ανεβάζει το HTML dashboard ως workflow artifact.

**Σημείωση**: τα scheduled (cron) runs στο GitHub Actions εκτελούνται μόνο
από το default branch του repository. Μέχρι να γίνει merge αυτού του
branch/PR, μόνο το `workflow_dispatch` (on-demand) θα δουλεύει.

## Τοπική εκτέλεση

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m athex_analyst.cli \
  --report reports/premarket.md \
  --dashboard reports/dashboard.html \
  --title "Πρωινή Αναφορά ΧΑΑ"
```

Χρήσιμες παράμετροι: `--top N` (πλήθος κορυφαίων προτάσεων), `--period 6mo|1y|2y`
(εύρος ιστορικού για τους δείκτες), `--no-report` / `--no-dashboard`.

## Σύνολο μετοχών

Η λίστα `FTSE/Athex Large Cap` στο `src/athex_analyst/tickers.py` είναι
χειροκίνητα επιμελημένη με βάση γνωστές μεγάλες/ρευστές μετοχές του ΧΑΑ. Η
σύνθεση του επίσημου δείκτη αλλάζει περιοδικά (τριμηνιαία/εξαμηνιαία
αναθεώρηση) — να επαληθεύεται κατά καιρούς έναντι
[athexgroup.gr](https://www.athexgroup.gr) και να ενημερώνεται η λίστα.

## Tests

```bash
pip install -r requirements.txt pytest
PYTHONPATH=src pytest tests/ -v
```

Τα tests χρησιμοποιούν συνθετικά δεδομένα (χωρίς δικτυακές κλήσεις).

---

# YouTube Analyzer

Πανίσχυρο εργαλείο ανάλυσης βίντεο YouTube (`src/youtube_analyzer/`), ανεξάρτητο
από τον αναλυτή ΧΑΑ. Τρεις βασικές λειτουργίες:

1. **`analyze`** — πλήρης ανάλυση ενός βίντεο: μεταδεδομένα, transcript
   (υπάρχοντες υπότιτλοι/CC σε **οποιαδήποτε γλώσσα**, ή αυτόματη αναγνώριση
   ομιλίας μέσω Whisper αν το βίντεο δεν έχει καθόλου υπότιτλους), δομημένη
   περίληψη ανά θεματική ενότητα με ρολόι-links, και πόροι/links από την
   περιγραφή. Η περίληψη μεταφράζεται αυτόματα στα ελληνικά όταν το βίντεο
   είναι σε άλλη γλώσσα. Το αποτέλεσμα αποθηκεύεται και στην τοπική
   "βιβλιοθήκη" (`data/youtube_library/`) για μελλοντικές συγκρίσεις.
2. **`compare`** — δίνεις ένα χρονικό απόσπασμα ενός βίντεο (π.χ. `--start
   12:34 --end 15:10`) και σου λέει σε ποια **άλλα** βίντεο της βιβλιοθήκης
   αναλύεται σημασιολογικά παρόμοιο περιεχόμενο, και σε ποιο ακριβώς τμήμα
   τους (με clickable timestamp links). Χρησιμοποιεί TF-IDF ομοιότητα πάνω
   στο transcript κείμενο.
3. **`subtitles`** — παράγει αρχείο `.srt` με ελληνικούς υπότιτλους για
   οποιοδήποτε βίντεο, ανεξαρτήτως της αρχικής γλώσσας ομιλίας.

## Τοπική εκτέλεση

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m youtube_analyzer.cli analyze "https://www.youtube.com/watch?v=VIDEO_ID"
PYTHONPATH=src python -m youtube_analyzer.cli subtitles "https://youtu.be/VIDEO_ID"
PYTHONPATH=src python -m youtube_analyzer.cli compare "https://youtu.be/VIDEO_ID" --start 12:34 --end 15:10
PYTHONPATH=src python -m youtube_analyzer.cli library-list
```

Απαιτεί `ffmpeg` εγκατεστημένο στο σύστημα όταν ενεργοποιείται το ASR
fallback (Whisper), για την εξαγωγή ήχου από το βίντεο.

## Πώς δουλεύει (αρχιτεκτονική)

- `youtube_client.py` — μεταδεδομένα + λήψη ήχου μέσω `yt-dlp`, υπάρχοντες
  υπότιτλοι μέσω `youtube-transcript-api` (οποιαδήποτε γλώσσα, χειροκίνητοι ή
  αυτόματοι).
- `transcribe.py` — ASR fallback (`faster-whisper`) όταν δεν υπάρχουν καθόλου
  υπότιτλοι· αυτόματη ανίχνευση γλώσσας ομιλίας.
- `translate.py` — μετάφραση στα ελληνικά (`deep-translator`), με batching
  ώστε να διατηρείται ο χρονισμός.
- `chunking.py` / `summary.py` — ομαδοποίηση transcript σε θεματικά τμήματα
  και εξαγωγική περίληψη (συχνότητα λέξεων· γλωσσο-ανεξάρτητη λογική).
- `similarity.py` / `compare.py` — TF-IDF (char n-grams) σύγκριση αποσπάσματος
  έναντι όλων των chunks στη βιβλιοθήκη.
- `library.py` — τοπική αποθήκευση αναλύσεων (JSON ανά βίντεο) στο
  `data/youtube_library/`.
- `subtitles.py` — παραγωγή `.srt`/`.vtt` με σωστό word-wrap και διάσπαση σε
  πολλαπλά cues όταν το κείμενο είναι μεγάλο.
- `report.py` — Markdown αναφορές (ελληνικά) στο `reports/youtube/`.

Όλα τα modules καθαρής λογικής (`timecode`, `subtitles`, `chunking`,
`summary`, `similarity`, `compare`, `library`, `report`) ελέγχονται με unit
tests πάνω σε συνθετικά δεδομένα, χωρίς δικτυακές κλήσεις. Τα I/O modules
(`youtube_client`, `transcribe`, `translate`) κάνουν lazy imports των βαριών
εξαρτήσεών τους και τρέχουν πραγματικά μόνο μέσω του GitHub Actions workflow
`.github/workflows/youtube_analyzer.yml` (on-demand, `workflow_dispatch`),
που έχει πλήρη πρόσβαση internet.

### Tests

```bash
pip install -r requirements.txt pytest
PYTHONPATH=src pytest tests/test_youtube_*.py -v
```

## Αποποίηση ευθύνης

Η παρούσα εφαρμογή παράγει αυτόματα αναφορές με βάση κανόνες τεχνικής
ανάλυσης (SMA/RSI/MACD/Bollinger) και βασικών θεμελιωδών στοιχείων, πάνω σε
δεδομένα του Yahoo Finance με καθυστέρηση. **ΔΕΝ αποτελεί επενδυτική
συμβουλή, σύσταση αγοράς/πώλησης χρηματοπιστωτικών μέσων, ούτε
εξατομικευμένη επενδυτική υπηρεσία** υπό την έννοια του ν.4514/2018 (MiFID
II) ή οποιουδήποτε άλλου ισχύοντος νομοθετικού πλαισίου. Η επένδυση σε
μετοχές ενέχει κίνδυνο απώλειας κεφαλαίου. Πριν από κάθε επενδυτική απόφαση,
συμβουλευτείτε αδειοδοτημένο επενδυτικό σύμβουλο ή ΑΕΠΕΥ.
