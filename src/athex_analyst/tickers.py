"""Universe of ATHEX (Χρηματιστήριο Αθηνών) large-cap tickers, Yahoo Finance format.

This list is curated by hand and should be reviewed periodically against the
official FTSE/Athex Large Cap index composition at athexgroup.gr, since index
constituents change on quarterly/semi-annual reviews.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Stock:
    symbol: str  # Yahoo Finance ticker, e.g. "OPAP.AT"
    name_el: str  # Greek display name
    sector: str


ATHEX_LARGE_CAP: list[Stock] = [
    Stock("ETE.AT", "Εθνική Τράπεζα", "Τράπεζες"),
    Stock("ALPHA.AT", "Alpha Bank", "Τράπεζες"),
    Stock("EUROB.AT", "Eurobank", "Τράπεζες"),
    Stock("TPEIR.AT", "Τράπεζα Πειραιώς", "Τράπεζες"),
    Stock("OPAP.AT", "ΟΠΑΠ", "Τυχερά Παιχνίδια"),
    Stock("HTO.AT", "ΟΤΕ", "Τηλεπικοινωνίες"),
    Stock("MYTIL.AT", "Μυτιληναίος", "Βιομηχανία/Ενέργεια"),
    Stock("PPC.AT", "ΔΕΗ", "Ενέργεια"),
    Stock("ELPE.AT", "HELLENiQ Energy", "Ενέργεια/Διύλιση"),
    Stock("MOH.AT", "Motor Oil", "Ενέργεια/Διύλιση"),
    Stock("GEKTERNA.AT", "GEK Τέρνα", "Κατασκευές/Ενέργεια"),
    Stock("TITC.AT", "Τιτάν Cement", "Δομικά Υλικά"),
    Stock("LAMDA.AT", "Lamda Development", "Ακίνητα"),
    Stock("EXAE.AT", "Ελληνικά Χρηματιστήρια (ΕΧΑΕ)", "Χρηματοοικονομικές Υπηρεσίες"),
    Stock("EYDAP.AT", "ΕΥΔΑΠ", "Κοινή Ωφέλεια"),
    Stock("AEGN.AT", "Aegean Airlines", "Αερομεταφορές"),
    Stock("SAR.AT", "Σαράντης", "Καταναλωτικά Αγαθά"),
    Stock("BELA.AT", "Jumbo", "Λιανεμπόριο"),
    Stock("QUAL.AT", "Quest Holdings", "Τεχνολογία"),
    Stock("KRI.AT", "Κρι-Κρι", "Τρόφιμα"),
    Stock("ELHA.AT", "Elval Halcor", "Βιομηχανία Μετάλλων"),
    Stock("PLAT.AT", "Πλαστικά Θράκης", "Βιομηχανία"),
    Stock("INTRK.AT", "Intracom Holdings", "Τεχνολογία"),
    Stock("INKAT.AT", "Ιντρακάτ", "Κατασκευές"),
    Stock("AVAX.AT", "AVAX", "Κατασκευές"),
]


def get_universe() -> list[Stock]:
    return list(ATHEX_LARGE_CAP)


def symbols() -> list[str]:
    return [s.symbol for s in ATHEX_LARGE_CAP]
