"""Statistische Pruefwerkzeuge fuer Muster-Auswertungen (2026-08-02).

Entstanden an einem Tag, an dem fuenf von sieben Befunden bei der Nachpruefung
gefallen sind - immer nach demselben Muster: eine Kennzahl sah belastbar aus,
haing aber an wenigen Ausreissern, an einer willkuerlich gewaehlten
Bucket-Grenze oder an einem fehlenden Vergleichsmassstab. Die Pruefungen dafuer
existierten nur als Text in `Basisinfos/Test_und_Verifikationsmethodik.md` und
mussten jedes Mal von Hand nachgezogen werden. Dieses Modul giesst sie in Code,
damit sie automatisch mitlaufen.

ABGRENZUNG zu `backward_tracking.py`: dort liegen bereits
`_binomialtest_zweiseitig_p_wert()` (exakter Test ohne scipy) und
`compute_baseline_vergleich()` (Muenzwurf / CRV-Break-even / regimenaiv,
2026-07-29). Die werden NICHT dupliziert und auch nicht verschoben - sechs
Module importieren aus jener Datei, ein Umzug waere unnoetiges Risiko. Hier
stehen nur die drei Dinge, die es noch nicht gab:

1. `wilson_intervall()` - Konfidenzintervall fuer Anteile
2. `beitrags_konzentration()` - Methodik 2.5.5
3. `mechanische_basislinie()` / `basislinie_je_indikator_bucket()` - die Latte,
   gegen die jede Signalgruppe antreten muss

Bewusst OHNE numpy/scipy: reine Standardbibliothek, wie der bestehende
Binomialtest. Das Modul ist datenquellen-unabhaengig (nimmt OHLC-Zeilen als
Dicts entgegen) und damit sowohl gegen die DB als auch gegen einen
Notebook-Export verwendbar.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence


def wilson_intervall(erfolge: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson-Konfidenzintervall fuer einen Anteil (Rueckgabe 0..1).

    Gegenueber der Normal-Approximation auch bei kleinem n und Quoten nahe 0
    oder 1 brauchbar - genau der Bereich, in dem dieses Projekt arbeitet
    (n=20..300, Trefferquoten teils 0%).

    `z`: 1.96 = 95%. Fuer mehrfach getestete Hypothesen Bonferroni-korrigiert
    uebergeben, z.B. bei 6 Zellen 2.64 (entspricht alpha 0,05/6) - genau daran
    ist am 02.08. ein Befund gescheitert, der unkorrigiert signifikant aussah.
    """
    if n <= 0:
        return (0.0, 0.0)
    p_hut = erfolge / n
    nenner = 1 + z * z / n
    mitte = (p_hut + z * z / (2 * n)) / nenner
    radius = z * math.sqrt(p_hut * (1 - p_hut) / n + z * z / (4 * n * n)) / nenner
    return (max(0.0, mitte - radius), min(1.0, mitte + radius))


def beitrags_konzentration(werte: Sequence[float], top_n: int = 5) -> dict | None:
    """Methodik 2.5.5: wieviel des Ergebnisses haengt an den groessten Einzelwerten?

    Der bestehende Symbol-Konzentrations-Check (2.5) prueft die Verteilung nach
    ANZAHL. Am 02.08. bestand ein Befund ihn glatt (groesstes Symbol nur 7,7%
    der Faelle) und war trotzdem ein Artefakt: die fuenf groessten Gewinner
    trugen 81% der Gesamtsumme. Anzahl- und Beitrags-Konzentration sind zwei
    verschiedene Dinge.

    Rueckgabe (None bei leerer Eingabe):
    - `mittelwert`, `median`
    - `top_n_beitrag_pct`: Anteil der `top_n` groessten Werte an der Summe.
      Kann >100% oder negativ sein, wenn die Restsumme das Vorzeichen dreht -
      genau dann ist die Kennzahl besonders fragil.
    - `mittelwert_ohne_top_n`, `vorzeichen_kippt`: das eigentliche Urteil.
      `vorzeichen_kippt=True` heisst: der Befund haengt an wenigen Ausreissern
      und ist NICHT belastbar, unabhaengig davon wie gut die Anzahl-Verteilung
      aussieht.
    """
    werte = [w for w in werte if w is not None]
    if not werte:
        return None
    summe = sum(werte)
    mittel = summe / len(werte)
    sortiert = sorted(werte, reverse=True)
    top = sortiert[:top_n]
    rest = sortiert[top_n:]
    mittel_ohne = (sum(rest) / len(rest)) if rest else None
    return {
        "anzahl": len(werte),
        "mittelwert": mittel,
        "median": _median(werte),
        "top_n": min(top_n, len(werte)),
        "top_n_summe": sum(top),
        "top_n_beitrag_pct": (sum(top) / summe * 100) if summe else None,
        "mittelwert_ohne_top_n": mittel_ohne,
        "vorzeichen_kippt": (
            mittel_ohne is not None and (mittel >= 0) != (mittel_ohne >= 0)
        ),
    }


def _median(werte: Sequence[float]) -> float:
    s = sorted(werte)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def _true_range(zeilen: Sequence[dict]) -> list[float | None]:
    tr: list[float | None] = [None]
    for i in range(1, len(zeilen)):
        hoch, tief = zeilen[i]["high"], zeilen[i]["low"]
        vorher = zeilen[i - 1]["close"]
        tr.append(max(hoch - tief, abs(hoch - vorher), abs(tief - vorher)))
    return tr


def mechanische_basislinie(
    serien: dict[str, Sequence[dict]],
    *,
    stop_abstand_relativ: float = 0.067,
    crv: float = 2.0,
    horizont_tage: int = 14,
    tag_filter: Callable[[Sequence[dict], int], bool] | None = None,
) -> dict:
    """Die Latte: wie oft wird das Ziel vor dem Stop erreicht, wenn man an
    einem BELIEBIGEN Tag einsteigt?

    Beantwortet die Frage, die vor dem 02.08. nirgends beantwortbar war:
    "ist diese Trefferquote ueberhaupt besser als ein Zufallseinstieg?" - ohne
    diesen Massstab wurde jede Quote gegen das Bauchgefuehl interpretiert.
    Ergaenzt `backward_tracking.compute_baseline_vergleich()`, das gegen
    Muenzwurf und rechnerischen Break-even prueft, aber nicht gegen echtes
    Marktverhalten.

    `serien`: {symbol: [OHLC-Zeilen]}, jede Zeile mit high/low/close,
    chronologisch. Quelle egal (DB oder Notebook-Export).
    `stop_abstand_relativ`: Vorgabewert 6,7% = Median der echten Signale.
    `tag_filter(zeilen, i) -> bool`: optionale Einschraenkung auf vergleichbare
    Marktphasen (z.B. nur Baer-Tage). WICHTIG - ohne passenden Filter misst man
    Marktphasen statt Signalqualitaet.

    Konservativ wie der Produktivcode (`hebel_backward_tracking.py`): liegen
    Stop UND Ziel im selben Tagesbalken, zaehlt der STOP. Die Reihenfolge
    innerhalb des Tages ist aus Tagesdaten nicht rekonstruierbar; die
    pessimistische Annahme haelt die Basislinie eher zu niedrig als zu hoch.
    """
    treffer = verluste = offen = 0
    for zeilen in serien.values():
        if len(zeilen) <= horizont_tage:
            continue
        for i in range(len(zeilen) - horizont_tage):
            if tag_filter is not None and not tag_filter(zeilen, i):
                continue
            einstieg = zeilen[i].get("close")
            if not einstieg or einstieg <= 0:
                continue
            stop = einstieg * (1 - stop_abstand_relativ)
            ziel = einstieg * (1 + stop_abstand_relativ * crv)
            for j in range(i + 1, i + 1 + horizont_tage):
                if zeilen[j]["low"] <= stop:
                    verluste += 1
                    break
                if zeilen[j]["high"] >= ziel:
                    treffer += 1
                    break
            else:
                offen += 1

    entschieden = treffer + verluste
    quote = treffer / entschieden if entschieden else None
    breakeven = 1 / (1 + crv)
    return {
        "treffer": treffer,
        "verluste": verluste,
        "offen": offen,
        "entschieden": entschieden,
        "trefferquote": quote,
        "break_even_quote": breakeven,
        "differenz_prozentpunkte": (
            (quote - breakeven) * 100 if quote is not None else None
        ),
        "erwartungswert_r": (
            quote * crv - (1 - quote) if quote is not None else None
        ),
        "parameter": {
            "stop_abstand_relativ": stop_abstand_relativ,
            "crv": crv,
            "horizont_tage": horizont_tage,
            "tag_filter_aktiv": tag_filter is not None,
        },
    }


def basislinie_je_indikator_bucket(
    serien: dict[str, Sequence[dict]],
    indikator: Callable[[Sequence[dict]], Sequence[float | None]],
    grenzen: Sequence[float],
    **basislinie_kwargs,
) -> dict[int, dict]:
    """Mechanische Basislinie getrennt nach Indikator-Niveau.

    Notwendig, sobald ein Befund an einen Indikator gekoppelt ist: eine globale
    Basislinie wuerde "in Seitwaertsphasen laeuft alles schlechter" mit "unsere
    Signale sind dort schlechter" vermischen - eine Marktphasen- statt einer
    Signalqualitaets-Aussage.

    ACHTUNG bei den Grenzen (Methodik 2.5.6): aus der Literatur uebernommene
    Standardwerte sind zunaechst Hypothesen, keine Parameter. Vor Verwendung
    verschieben und pruefen, ob der Effekt haelt - sonst misst man die
    Bucket-Wahl. Am 02.08. stellte sich so heraus, dass ein vermeintlicher
    "ADX>30"-Bucket in Wahrheit der Randbereich der Datenspanne war.

    Rueckgabe: {bucket_index: <mechanische_basislinie()-Ergebnis>}, Index 0 =
    unterhalb der ersten Grenze.
    """
    ergebnis: dict[int, dict] = {}
    for bucket in range(len(grenzen) + 1):
        def filter_fuer_bucket(zeilen, i, _b=bucket):
            werte = _indikator_cache(indikator, zeilen)
            wert = werte[i] if i < len(werte) else None
            if wert is None:
                return False
            return sum(1 for g in grenzen if wert >= g) == _b

        ergebnis[bucket] = mechanische_basislinie(
            serien, tag_filter=filter_fuer_bucket, **basislinie_kwargs
        )
    return ergebnis


_INDIKATOR_CACHE: dict[tuple[int, int], Sequence[float | None]] = {}


def _indikator_cache(indikator, zeilen):
    """Ohne Cache wuerde der Indikator je Bucket und Tag neu ueber die ganze
    Serie laufen - bei 4 Buckets x 3.000 Tagen ein Vielfaches der noetigen
    Arbeit. Schluessel ist die Objekt-Identitaet der Serie plus die Funktion."""
    key = (id(indikator), id(zeilen))
    werte = _INDIKATOR_CACHE.get(key)
    if werte is None:
        werte = indikator(zeilen)
        _INDIKATOR_CACHE[key] = werte
    return werte


def cache_leeren() -> None:
    """Nach einem Auswertungslauf aufrufen - die Cache-Schluessel sind
    Objekt-IDs und werden nach Freigabe der Serien wiederverwendet."""
    _INDIKATOR_CACHE.clear()
