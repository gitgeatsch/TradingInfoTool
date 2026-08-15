# -*- coding: utf-8 -*-
"""Die EINE Stelle, an der die Eingabe fuer die Rollen entsteht.

WARUM ES DIESE DATEI GIBT (12.08.2026). Bis hierher baute jedes Messskript die
Eingabe selbst zusammen - `pruefe_rollenkette`, `messe_degradierung`,
`messe_faktorzahl`, `messe_dritter_faktor`, `messe_abgleich_alt_neu`,
`messe_marktphasen`. Sechs Stellen mit demselben Aufbau.

Das hatte zwei Folgen, beide belegt:

  * Die Finanzierungsrate war gebaut (Faktenmappe 12.9) und liess sich trotzdem
    nicht "anschliessen" - es gab keinen Ort dafuer. Sie haette in sechs
    Skripte einzeln eingesetzt werden muessen.
  * Zwei Skripte riefen die Marktbreite mit `mit_bezug=False` auf, zwei mit
    `True`. Der Kalibrierungssatz, der die Zuspitzung eindaemmen soll, fehlte
    also in der Haelfte aller Messungen - unbemerkt (Arbeitsstand 7.14).

Wer die Eingabe aendern will, aendert sie hier. Wer sie an sechs Stellen
aendert, aendert sie an fuenf.

WAS HIER NICHT HINEINGEHOERT: Netzwerkaufrufe im Zweifel. `finanzierung` wird
als fertige Zusammenfassung uebergeben, nicht hier geholt - sonst haengt eine
Beschreibung an einer Boersen-API und faellt mit ihr aus. Der Aufrufer holt und
entscheidet, was bei einem Ausfall geschieht.
"""
from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)


def baue_lagebild_eingabe(reihen: dict, datum: str) -> dict:
    """Eingabe fuer das Lagebild - seit 12.08. aus `agent/marktlage.py`.

    DIE MARKTBREITE IST HIER RAUS (L1). Sie stand hier bis heute, und der
    Vorgaengertext an dieser Stelle begruendete sorgfaeltig, warum ihr
    historischer Bezug unverzichtbar sei - "die einzige Kalibrierung, die das
    Modell vor einer Zuspitzung schuetzt". Der Satz stimmte, solange es nichts
    anderes gab. Gemessen hat die Marktbreite nicht getragen:

        SUBJEKT FALSCH  "Von 44 beobachteten Coins" - 11 davon sind keine
                        Coins (PLTR, VST, CAT, vier ETF, drei Rohstoff-
                        Referenzen, SPY). Ein Viertel des Korbs
        EIN KORB FUER   dieselbe Zahl ging an jede Assetklasse; eine
        ALLE            Aktienentscheidung sah eine "Coin"-Breite
        BEZUG WANDERT   der historische Vergleich misst gegen einen Korb, den
                        es nie gab: vor 250 Handelstagen 34 Reihen, heute 44 -
                        23 % kamen seither dazu. Die Kalibrierung stand auf
                        einer Bezugsgroesse, die sich mitbewegt
        RICHTUNG INVERS kein Zeitpunkt mit breitem Markt war je ein guter
                        Einstieg (Arbeitsstand 7.4)

    DIE KALIBRIERUNG GEHT NICHT VERLOREN, sie wandert: L2 und L4 liefern
    Perzentile der eigenen Historie, L3 nennt Zahlen mit benanntem Fenster.
    `waechter_zuspitzung` musste dafuer die neue Schreibweise lernen - ohne das
    haette er nach der Streichung jeden Grad als unbelegt gemeldet, auch den
    wahren."""
    from agent.marktlage import beschreibe_marktlage
    return {"marktlage": beschreibe_marktlage(reihen, datum, lade_stimmung(),
                                              lade_makro())}


def lade_stimmung(db: str = "data/tradinginfotool.db") -> dict:
    """Fear & Greed je Tag - die einzige Groesse des Lagebilds, die NICHT aus
    der Kursreihe stammt.

    FAIL-SOFT UND GEZAEHLT: faellt die Tabelle aus, kommt ein leeres dict und
    der Satz entfaellt. Das ist richtig - ein Satz "keine Stimmungsdaten" waere
    ueber alle Anker identisch und damit ein konstantes Feld (R-T6). Der
    Aufrufer sieht am fehlenden Satz, dass etwas fehlt.

    Historie nachgeladen am 12.08. mit `lade_fear_greed_nach.py`: 3.111 Tage ab
    2018-02-01. Vorher waren es 10 - die Tabelle wurde erst am 07.07.2026
    angelegt, in der Produktion ebenso (an fuenf Notebook-Sicherungen
    geprueft)."""
    import sqlite3
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            return {t: v for t, v in con.execute(
                "SELECT date, fear_greed_value FROM macro_snapshot "
                "WHERE fear_greed_value IS NOT NULL")}
        finally:
            con.close()
    except Exception:                                        # noqa: BLE001
        return {}


def stempel_gleichlauf(antwort: dict, reihen: dict, datum: str) -> dict:
    """Haengt den gerechneten Gleichlauf an die ANTWORT der Rolle Lagebild.

    WARUM AN DIE ANTWORT UND NICHT AN DIE EINGABE. Der gesamte Eingabe-Dict
    geht als Nachricht an das Modell. Stuende der Gleichlauf dort, waere er
    eine abgeleitete Wiederholung der Zahlen, die zwei Zeilen darueber schon
    stehen - eine vierte Kennzahl, die nichts Neues traegt, aber Gewicht
    bekommt (R-T9). Das Modell soll die drei Jahresrenditen selbst lesen.

    Gebraucht wird der Wert danach: von der naechsten Rolle als zaehlbarer
    Festpunkt neben der Prosa, von jeder Messung als Verteilung, und vom
    Gegenpruefer als Bezug, gegen den ein Widerspruch pruefbar wird."""
    from agent.marktlage import gleichlauf
    antwort["gleichlauf"] = gleichlauf(reihen, datum)["wert"]
    return antwort


def lade_makro(db: str = "data/tradinginfotool.db") -> dict:
    """Netto-Liquiditaet und Zinskurven-Spread je Tag - die einzigen Fakten des
    Lagebilds, die mit KEINER unserer Kursreihen zu tun haben.

    Aus der DATENBANK, nicht live. Ein heute geholter Makrowert in einem Anker
    von 2022 waere ein Leck, kein Fakt. Historie nachgeladen am 12.08. mit
    `lade_makro_historie_nach.py`: 501 Wochenwerte Liquiditaet ab 2017-01 und
    2.414 Tageswerte Zinsen.

    FAIL-SOFT: faellt etwas aus, entfaellt der Satz. Ein Satz "keine
    Makrodaten" waere ueber alle Anker identisch und damit ein konstantes Feld
    (R-T6)."""
    import sqlite3
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            liq = {t: v for t, v in con.execute(
                "SELECT date, netto_liquiditaet_mrd FROM macro_snapshot "
                "WHERE netto_liquiditaet_mrd IS NOT NULL")}
            zins = {t: round(z - k, 4) for t, z, k in con.execute(
                "SELECT date, rendite_10j_pct, rendite_kurz_pct FROM "
                "macro_snapshot WHERE rendite_10j_pct IS NOT NULL "
                "AND rendite_kurz_pct IS NOT NULL")}
            return {"liquiditaet": liq, "zinskurve": zins}
        finally:
            con.close()
    except Exception:                                        # noqa: BLE001
        return {}


def baue_befund_eingabe(*, symbol: str, reihe: list, index: int,
                        kurs_eur: float, atr: float,
                        menge: float | None = None,
                        einstand_eur: float | None = None,
                        finanzierung: dict | None = None,
                        lagebild: dict | None = None,
                        instrument: str = "spot",
                        strategie: str = "einstieg",
                        assetklasse: str | None = None,
                        gegenseite: str | None = None,
                        referenz: dict | None = None,
                        bloecke_ziel: dict | None = None) -> dict:
    """Eingabe fuer Befund und Entscheidung - alle Bloecke an einer Stelle.

    `instrument`/`strategie` (12.08.2026, Paket 2): WAS gehandelt wird und WIE.
    Vorgabe, keine Frage - der Aufrufer weiss es immer, weil Spot und Hebel
    getrennte Pipelines sind. Die Vorgabewerte sind der bisherige stille
    Zustand (spot/einstieg), damit kein Aufrufer bricht; wer Hebel bewertet,
    MUSS ihn nennen, sonst fehlen die Finanzierungskosten in der Beurteilung.

    `lagebild` ist die ANTWORT der Rolle Lagebild. Weitergereicht wird ihre
    Prosa (`lage`) und, wenn vorhanden, der deterministische `gleichlauf` -
    NICHT mehr das Feld `traegt`. Das war eine Marktbreite-Kategorie und ist
    mit der Marktbreite entfallen (Begruendung in `rolle_analyst.py`).

    Der Unterschied ist nicht nur ein Feldname: `traegt` kam aus dem Modell und
    konnte falsch sein, `gleichlauf` ist gerechnet. Wo beides nebeneinander
    steht - gerechneter Festpunkt und Modellprosa -, wird ein Widerspruch
    pruefbar statt zur Geschmacksfrage (R-T8)."""
    from agent.handelsauftrag import beschreibe as beschreibe_auftrag
    from agent.lagebeschreibung import beschreibe_lage
    aus = {"asset": symbol,
           # DER AUFTRAG STEHT ZUERST (Paket 2, R-T9: was zuerst steht, wiegt
           # schwerer). Er ist die BEDINGUNG, unter der alles Weitere zu lesen
           # ist - dieselben Kursfakten bedeuten bei 3x Hebel etwas anderes als
           # bei einem Spot-Einmalkauf. Ein Haendler, der das nicht weiss,
           # urteilt ueber einen Trade, den er nicht kennt.
           "auftrag": beschreibe_auftrag(instrument, strategie),
           "stand": beschreibe_lage(symbol=symbol, reihe=reihe, index=index,
                                    kurs_eur=kurs_eur, atr=atr, menge=menge,
                                    einstand_eur=einstand_eur,
                                    finanzierung=finanzierung,
                                    instrument=instrument,
                                    gegenseite=gegenseite,
                                    referenz=referenz,
                                    bloecke_ziel=bloecke_ziel)}
    if lagebild:
        beurteilung = {"lage": lagebild.get("lage")}
        if lagebild.get("gleichlauf"):
            beurteilung["gleichlauf"] = lagebild["gleichlauf"]
        # NUR DAS URTEIL ZUR EIGENEN KLASSE (Paket 3). Alle drei zu schicken
        # hiesse, dem Trader zwei Maerkte vorzulegen, ueber die er nicht
        # entscheidet - und was dasteht, wiegt (R-T9). `etf` folgt `aktien`,
        # weil beide denselben Leitmarkt haben.
        #
        # ⚠️ DIESE ZUORDNUNG GRIFF FUER ZWEI GRUPPEN NIE (gefunden 16.08.2026
        # beim Rendern, nicht beim Lesen). Sie war gegen die ASSETKLASSE der
        # Watchlist geschrieben - `krypto | aktien | rohstoffe | etf` -, der
        # Aufrufer `rollen_lauf` uebergibt aber die GRUPPE: `krypto | aktien |
        # rohstoffe | themen_etf | hedge`. Genau die drei Begriffe, die
        # `agent/assetklassen.py` in seinem Kopf auseinanderhaelt, weil sie
        # sich aehnlich sehen und es nicht sind.
        #
        # FOLGE: bei `themen_etf` und `hedge` fand die Schleife keinen
        # Eintrag, und die Einstufung des Leitmarkts fehlte im Prompt -
        # lautlos, weil ein fehlender Schluessel kein Fehler ist. Drei von
        # fuenf Gruppen bekamen sie, zwei nicht.
        #
        # BEIDE VOKABULARE STEHEN JETZT DRIN. `etf` bleibt fuer Aufrufer, die
        # die Assetklasse uebergeben (die Messskripte tun das).
        klasse = {"etf": "aktien", "themen_etf": "aktien",
                  "hedge": "aktien"}.get(assetklasse, assetklasse)
        for eintrag in (lagebild.get("klassen") or []):
            if eintrag.get("klasse") == klasse:
                beurteilung["klasse"] = eintrag
                break
        aus["marktlage_beurteilung"] = beurteilung
    return aus


def hole_finanzierung(symbol: str, datum: str, session=None,
                      zwischenspeicher: dict | None = None) -> dict | None:
    """Finanzierungsrate zum ANKERTAG, kausal abgeschnitten.

    FAIL-SOFT UND STILL: Faellt die Boerse aus oder kennt sie das Symbol nicht,
    kommt None zurueck und der Block entfaellt. Das ist richtig so - ein Satz
    "keine Finanzierungsdaten" waere fuer alle Aktien, ETF und Rohstoffe
    identisch und damit ein konstantes Feld (B10).

    ABER: der Aufrufer muss zaehlen, wie oft None kam. Ein stiller Ausfall, den
    niemand zaehlt, ist genau das U-Boot, das dieses Projekt mehrfach bezahlt
    hat. `zwischenspeicher` dient zugleich der Taktung - dieselbe Kombination
    wird nur einmal geholt."""
    from datetime import datetime, timezone
    schluessel = (symbol, datum[:10])
    if zwischenspeicher is not None and schluessel in zwischenspeicher:
        return zwischenspeicher[schluessel]
    ergebnis = None
    try:
        from api.derivatives import get_funding_history, summarize_funding
        ende = int(datetime.fromisoformat(datum[:10]).replace(
            tzinfo=timezone.utc).timestamp() * 1000)
        ergebnis = summarize_funding(
            get_funding_history(f"{symbol}USDT", 100, session, ende))
    except Exception:                                            # noqa: BLE001
        ergebnis = None
    if zwischenspeicher is not None:
        zwischenspeicher[schluessel] = ergebnis
    return ergebnis


# --- Der Sektorbezug fuer Themen-ETF (Phase I, Schritt 4, 16.08.2026) -------
#
# NICHTS DAVON IST NEU. `agent/themen_etf/pipeline._compute_sektor_rotation()`
# rechnet dieselbe Groesse gegen dieselbe Reihe, seit es Themen-ETF gibt. Sie
# hing an der ALTEN Pipeline und hat die Rollen-Kette nie erreicht - der
# haeufigste Befund dieses Projekts, und hier noch einmal.
#
# WARUM DIE RECHNUNG TROTZDEM HIER STEHT und nicht importiert wird: die dortige
# Fassung liest die VOLLE Reihe aus der Datenbank und nimmt `[-1]`. In der
# Rollen-Kette gibt es einen Ankertag, und ein Backtest, der die letzte Kerze
# der Datenbank benutzt, liest die Zukunft. Die Formel ist dieselbe
# (`etf_perf - benchmark_perf`), die Kausalitaet ist es nicht.
BENCHMARK_SYMBOL = "_THEMEN_ETF_BENCHMARK_SPY"
BENCHMARK_NAME = "der breite Markt (S&P-500-ETF)"

# Wieviel Rueckstand die Benchmark-Reihe haben darf. Sie ist eine
# BOERSENreihe: ueber ein langes Wochenende sind drei Tage normal, mehr als
# eine Woche heisst, dass sie nicht mehr nachgefuehrt wird - und dann waere der
# Vergleich eine Aussage ueber verschiedene Zeitpunkte.
BENCHMARK_MAX_RUECKSTAND_TAGE = 7

_benchmark_speicher: dict = {}


def _benchmark_reihe(db: str | None = None) -> list:
    """(Datum, Schluss) der Vergleichsreihe, aufsteigend. Einmal je Datei."""
    import sqlite3
    pfad = db or DB
    if pfad in _benchmark_speicher:
        return _benchmark_speicher[pfad]
    reihe = []
    try:
        c = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)
        try:
            reihe = [(str(d), float(s)) for d, s in c.execute(
                "SELECT date, close FROM price_history_ohlc WHERE symbol = ? "
                "AND close IS NOT NULL ORDER BY date ASC", (BENCHMARK_SYMBOL,))]
        finally:
            c.close()
    except Exception:                                        # noqa: BLE001
        reihe = []
    _benchmark_speicher[pfad] = reihe
    return reihe


def _stand_am(reihe: list, datum: str) -> tuple[str, float] | None:
    """Der juengste Schlusskurs mit Datum <= `datum` - streng kausal.

    NICHT der naechstgelegene. Ein Feiertag darf den Vergleich nach hinten
    verschieben, niemals nach vorn: der naechstgelegene Wert waere an einem
    Brueckentag der von MORGEN."""
    import bisect
    i = bisect.bisect_right([d for d, _ in reihe], str(datum)[:10]) - 1
    return reihe[i] if i >= 0 else None


def relative_staerke(reihe: list, index: int, db: str | None = None,
                     fenster: tuple = (30, 90)) -> dict | None:
    """Um wieviele Prozentpunkte lief dieser Wert besser als der breite Markt?

    Gibt None, wenn die Vergleichsreihe fehlt, zu alt ist oder das Fenster
    nicht in die eigene Historie passt. Dann entfaellt der Block - ein Satz
    "kein Vergleich moeglich" waere fuer alle betroffenen ETF identisch, und
    die fehlende Historie steht ohnehin schon im Luecken-Block."""
    b = _benchmark_reihe(db)
    if not b or index < 0 or index >= len(reihe):
        return None
    heute = str(reihe[index].date)[:10]
    jetzt = _stand_am(b, heute)
    if not jetzt:
        return None
    from datetime import date
    try:
        rueckstand = (date.fromisoformat(heute)
                      - date.fromisoformat(jetzt[0])).days
    except ValueError:
        return None
    if rueckstand > BENCHMARK_MAX_RUECKSTAND_TAGE:
        logger.info("Vergleichsreihe %s haengt %d Tage zurueck - kein "
                    "Sektorbezug", BENCHMARK_SYMBOL, rueckstand)
        return None

    aus: dict = {"name": BENCHMARK_NAME}
    e1 = float(reihe[index].close)
    for tage in fenster:
        j = index - int(tage)
        if j < 0:
            continue
        e0 = float(reihe[j].close)
        frueher = _stand_am(b, str(reihe[j].date)[:10])
        if e0 <= 0 or not frueher or frueher[1] <= 0:
            continue
        aus[f"rel_{tage}"] = round(100.0 * (e1 / e0 - 1.0)
                                   - 100.0 * (jetzt[1] / frueher[1] - 1.0), 2)
    return aus if len(aus) > 1 else None


def pruefe_lagebild(ausgabe: dict, eingabe: dict) -> dict:
    """Der Waechter auf der NAHT zwischen den Rollen (R-T8).

    Die bestehenden Waechter pruefen EINGABEN. Die Ausgabe des Lagebilds ist die
    Eingabe der Entscheidung - und wurde nie geprueft. Belegt am 11.08.: aus
    "8 % ueber der 50-Tage-Linie, in 46 % der Faelle war dieser Anteil
    niedriger" wurde "extreme Schieflage mit starkem Abwaertsdruck", und dieser
    Satz erreichte die Entscheidung als Beleg mit Gewicht HOCH.

    VERMERKEN, NICHT ABLEHNEN. Eine Ablehnung erzeugt eine Wiederholung und am
    Ende kein Signal - derselbe Deadloop an anderer Stelle (R-A5). Und den Text
    umzuschreiben waere schlimmer: dann stuende dort ein Satz, den niemand
    verantwortet. Der Verstoss wird gezaehlt und sichtbar gemacht; was daraus
    folgt, ist eine Entscheidung des Nutzers, keine des Waechters."""
    from agent.waechter_zuspitzung import pruefe
    text = " ".join(str(v) for v in (ausgabe.get("lage"), *(ausgabe.get("belege") or [])))
    ergebnis = pruefe(text, eingabe.get("marktlage") or [])
    if ergebnis.get("verstoss"):
        ausgabe["_zuspitzung"] = (
            f"unbelegte Gradbehauptung {ergebnis['hart']} - {ergebnis['grund']}")
    return ergebnis


# --- Geteilte Helfer (12.08.2026) -------------------------------------------
#
# WARUM SIE HIERHER WANDERN. Bis heute standen `_bestand`, `_kurs_eur`, `_atr`,
# `frage` und `_client` in `pruefe_rollenkette.py` - einem SKRIPT. Sieben
# Messskripte importierten sie von dort und bogen dessen Modulkonstante `DB`
# um. Ein Skript als Bibliothek zu benutzen funktioniert, bis jemand es
# ausfuehrt oder umbenennt.
#
# Sie liegen jetzt hier, wo auch die Eingabe entsteht. `pruefe_rollenkette`
# importiert sie zurueck, damit bestehende Aufrufe unveraendert bleiben.

DB = "data/tradinginfotool.db"


def bestand(symbol: str, db: str | None = None, instrument: str = "spot"):
    """Menge und wirksamer Einstand. NAEHERUNG bei historischen Faellen: der
    heutige Bestand, nicht der von damals - Bestandshistorie fuehren wir nicht.

    Liest BEIDE Einstandsspalten. Die manuelle geht vor - dieselbe Vorrangregel
    wie `database/models.py::effective_avg_buy_price_eur`. Ohne sie meldete die
    Kette 14 von 28 gehaltenen Positionen als "nicht im Bestand".

    DIE TABELLE FOLGT DEM INSTRUMENT (15.08.2026). Bis hierher stand hier
    IMMER `holdings` - die Spot-Tabelle. Im Hebel-Lauf ging damit der
    Spot-Bestand in den Prompt, und das Modell empfahl SCHLIESSEN fuer
    Positionen, die es nie gab: 25 von 270 Aufrufen des ersten
    Produktionsvormittags. Der Ausfuehrungspfad
    (`rollen_lauf._ein_asset`) traf die Unterscheidung seit dem 14.08. bereits
    richtig - nur die FAKTEN, auf die das Modell antwortet, taten es nicht.

    EINE HEBELPOSITION FUEHRT KEINEN EINSTAND JE STUECK. `hebel_positions` hat
    keine solche Spalte; der Buchwert steckt in `positionswert_eur`. Hier
    kommt deshalb `None` zurueck und nicht eine gerechnete Zahl - dieselbe
    Entscheidung wie im Ausfuehrungspfad, aus demselben Grund: eine erfundene
    Einstandszahl waere schlimmer als eine fehlende."""
    import sqlite3
    c = sqlite3.connect(f"file:{db or DB}?mode=ro", uri=True)
    try:
        if str(instrument) == "hebel":
            r = c.execute(
                "select positionsmenge from hebel_positions "
                "where symbol=? and status='offen' "
                "order by eroeffnet_am asc limit 1", (symbol,)).fetchone()
            return (r[0], None) if r else (None, None)
        r = c.execute(
            "select quantity, avg_buy_price_eur, avg_buy_price_manual_eur "
            "from holdings where symbol=?", (symbol,)).fetchone()
    except sqlite3.Error:
        # FEHLT DIE TABELLE, IST DAS KEINE AUSSAGE UEBER DEN BESTAND. Ein
        # leeres Ergebnis wuerde hier als "nicht im Bestand" gelesen - genau
        # die Falschaussage, gegen die `_bestand()` seit dem 11.08. drei
        # Zustaende fuehrt.
        return (None, None)
    if not r:
        return (None, None)
    menge, berechnet, manuell = r
    return (menge, manuell if manuell is not None else berechnet)


def gegenbestand_satz(symbol: str, db: str | None = None,
                      instrument: str = "spot") -> str | None:
    """Die ANDERE Seite desselben Assets - benannt, nicht verschwiegen.

    WARUM SIE INS URTEIL GEHOERT. Der Nutzer am 15.08.2026:

        "problem ist dass die trades unabhaengig sind und ich bin in einem
        hebel bei LINK - also eine Empfehlung und dann kommt ein spot verkauf
        rein."

    Beide Laeufe urteilen ueber dasselbe Asset und wussten nichts voneinander.
    Ein Urteil je Asset (statt je Instrument) waere die vollstaendige Loesung -
    der Nutzer hat sie am 15.08. als zu komplex zurueckgestellt, und das zu
    Recht, solange die Fakten noch nicht stimmen. Diese Zeile ist die kleine:
    das Urteil bleibt getrennt, aber es faellt nicht mehr blind.

    KEINE HANDLUNGSANWEISUNG. Der Satz stellt fest, was daneben liegt; was
    daraus folgt, entscheidet das Modell. Eine Formulierung wie "deshalb nicht
    kaufen" waere ein Regelwerk im Faktentext."""
    import sqlite3
    c = sqlite3.connect(f"file:{db or DB}?mode=ro", uri=True)
    try:
        if str(instrument) == "hebel":
            r = c.execute("select quantity from holdings where symbol=?",
                          (symbol,)).fetchone()
            if not r or not r[0]:
                return None
            return (f"Unabhaengig davon liegen {float(r[0]):.4f} Stueck "
                    f"{symbol} im Spot-Bestand. Das ist KEINE Hebelposition "
                    f"und wird getrennt beurteilt.")
        r = c.execute("select positionsmenge, hebel_effektiv, richtung "
                      "from hebel_positions where symbol=? and status='offen' "
                      "order by eroeffnet_am asc limit 1", (symbol,)).fetchone()
        if not r or not r[0]:
            return None
        richtung = f" ({r[2]})" if r[2] else ""
        hebel = f", Hebel {float(r[1]):.1f}" if r[1] else ""
        return (f"Unabhaengig davon ist in {symbol} eine Hebelposition offen"
                f"{richtung}: {float(r[0]):.4f} Stueck{hebel}. Sie wird "
                f"getrennt beurteilt.")
    except sqlite3.Error:
        return None


def kurs_eur(symbol: str, reihe, index: int, db: str | None = None):
    """EUR-Kurs am Ankertag.

    Liegt die REIHE bereits in EUR, wird NICHT umgerechnet - sonst waere es
    eine stille Doppelumrechnung um den Wechselkurs. Und `price_cache` ist eine
    Historie, kein Cache: ohne `order by` kaeme die aelteste Zeile."""
    import sqlite3
    from backtest_llm1_historisch import waehrung_je_symbol
    pfad = db or DB
    if waehrung_je_symbol(pfad).get(symbol) == "EUR":
        return float(reihe[index].close)
    c = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)
    r = c.execute("select price_usd, price_eur from price_cache where symbol=? "
                  "order by fetched_at desc limit 1", (symbol,)).fetchone()
    if not r or not r[0] or not r[1]:
        return float(reihe[index].close)
    return float(reihe[index].close) * (float(r[1]) / float(r[0]))


def fx_eur_je_usd(symbol: str, reihe, index: int, db: str | None = None) -> float:
    """Wieviel EUR ist ein USD dieser Reihe wert? 1,0, wenn die Reihe EUR ist.

    DIESELBE QUELLE wie `kurs_eur()` - sonst haetten wir zwei Umrechnungen, die
    auseinanderlaufen koennen. Hier steht sie einmal und wird von dort benutzt."""
    import sqlite3
    from backtest_llm1_historisch import waehrung_je_symbol
    pfad = db or DB
    if waehrung_je_symbol(pfad).get(symbol) == "EUR":
        return 1.0
    c = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)
    try:
        r = c.execute("select price_usd, price_eur from price_cache "
                      "where symbol=? order by fetched_at desc limit 1",
                      (symbol,)).fetchone()
    finally:
        c.close()
    if not r or not r[0] or not r[1]:
        return 1.0
    return float(r[1]) / float(r[0])


def atr_eur(symbol: str, reihe, index: int, db: str | None = None) -> float:
    """ATR in DERSELBEN Waehrung wie `kurs_eur()`.

    WOZU DIE ZWEITE FASSUNG - gefunden bei der Gegenpruefung zu Paket 7.
    `atr_bis()` rechnet aus der Kursreihe, und die liegt bei ALLEN 45 Symbolen
    in USD. `kurs_eur()` liefert dagegen EUR. Beide wurden bisher zusammen
    weitergereicht:

        `beschreibe_lage()`   RICHTIG - sie rechnet durchgehend in der
                              Quellwaehrung und rechnet nur die ANZEIGE um
        `leite_zonen_ab()`    FALSCH - die Spanne war 0,25 x ATR(USD) auf
                              EUR-Kurse. Gemessen an BTC: 882,85 statt 771,92
                              EUR, also 14,4 % zu breit

    Das Ziel war nie betroffen: es folgt CRV x Risiko und ist damit
    waehrungsfrei. Nur die Spanne stimmte nicht."""
    return atr_bis(reihe, index) * fx_eur_je_usd(symbol, reihe, index, db)


def atr_bis(reihe, index: int) -> float:
    """ATR aus `reihe[:index+1]` - streng kausal."""
    from indicators.calculations import atr_wilder, latest_value
    h = np.array([k.high for k in reihe[:index + 1]], dtype=float)
    l = np.array([k.low for k in reihe[:index + 1]], dtype=float)
    c = np.array([k.close for k in reihe[:index + 1]], dtype=float)
    return float(latest_value(atr_wilder(h, l, c)) or 0.0)


def baue_fall(*, symbol: str, reihe: list, index: int, reihen: dict,
              lagebild: dict | None = None, db: str | None = None,
              session=None, finanz_zwischenspeicher: dict | None = None,
              mit_finanzierung: bool = True,
              instrument: str = "spot", strategie: str = "einstieg",
              assetklasse: str | None = None,
              bloecke_ziel: dict | None = None) -> tuple[dict, dict]:
    """Beide Eingaben fuer EINEN Fall - die einzige Stelle, die das tut.

    Rueckgabe: (lagebild_eingabe, befund_eingabe). Wer das Lagebild schon hat,
    uebergibt es als `lagebild` und ignoriert den ersten Rueckgabewert.

    `mit_finanzierung=False` ist der Vergleichsarm fuer gepaarte Messungen -
    er darf nicht heimlich abweichen, deshalb steht er hier und nicht im
    Aufrufer.

    `instrument`/`strategie`/`assetklasse` (15.08.2026): DIE LUECKE, DIE DAS
    SCHLIESST. `baue_befund_eingabe()` kennt diese drei seit dem 12.08. und
    baut daraus den AUFTRAG-Block - den ersten des Prompts, weil was zuerst
    steht schwerer wiegt (R-T9). Diese Funktion nahm sie nicht entgegen, also
    griffen dort die Vorgabewerte, und im Faktensatz JEDES Laufs stand:

        "Gehandelt wird der Wert selbst, ohne Hebel und ohne laufende Kosten."

    Auch im Hebel-Lauf. Auch im Absicherungslauf. Die Rolle bekam ihre
    Anweisung getrennt und richtig (`rolle_trader.prompt_fuer(instrument, ...)`),
    die FAKTEN widersprachen ihr - und `handelsauftrag.beschreibe()` nennt sich
    selbst die BEDINGUNG, unter der alles Weitere zu lesen ist.

    Gemessen am ersten Produktionsvormittag: 13 Hebel-Eroeffnungen entstanden
    auf Fakten, die dem Modell sagten, es gebe keinen Hebel und keine
    laufenden Kosten."""
    datum = reihe[index].date
    menge, einstand = bestand(symbol, db, instrument)
    # DIE FINANZIERUNG WIRD NUR NOCH BEIM HEBEL GEHOLT (Phase I, Schritt 2).
    #
    # Der Satz entfaellt bei Spot ohnehin (`lagebeschreibung._finanzierung`),
    # aber der AUFRUF stand weiter drin: bei jedem Spot-Lauf 43 Anfragen an
    # Binance, bei Aktien, Rohstoffen und ETF elf weitere, die dort gar kein
    # Symbol haben und ins Leere liefen. Jeder dieser Aufrufe bucht seinen
    # Gesundheitsstand in `api_health_status`.
    #
    # FOLGE FUER GEPAARTE MESSUNGEN, ausdruecklich: `mit_finanzierung=False`
    # ist ab jetzt NUR bei `instrument='hebel'` ein echter Vergleichsarm. Auf
    # Spot erzeugen beide Arme denselben Prompt - eine Messung, die nichts
    # misst. Pruefung P-I-2 haelt das fest, damit es nicht still passiert.
    fin = (hole_finanzierung(symbol, datum, session, finanz_zwischenspeicher)
           if (mit_finanzierung and str(instrument) == "hebel") else None)
    # DER SEKTORBEZUG NUR FUER THEMEN-ETF.
    #
    # ⚠️ ERSTE FASSUNG PRUEFTE `== "etf"` UND HAETTE NIE GEGRIFFEN. Der
    # Aufrufer uebergibt die GRUPPE (`themen_etf`/`hedge`), nicht die
    # Assetklasse - siehe die ausfuehrliche Notiz in `baue_befund_eingabe()`.
    # Gefunden hat es `erhebe_prompts.py`: im gerenderten Faktensatz stand
    # kein Referenzsatz. Ein Code-Studium haette es nicht gezeigt, der
    # gerenderte Satz zeigt es sofort.
    #
    # BEIDE VOKABULARE, und `ist_hedge_instrument()` bleibt als zweite
    # Schranke stehen: kommt jemals wieder "etf" herein, muessen DBPK und 3QSS
    # trotzdem draussen bleiben. Sie nennen ihren Referenzindex in ihrem
    # eigenen Block (`absicherung_fakten.saetze()`); ein zweiter Bezug daneben
    # waere derselbe Fakt in zwei Formulierungen.
    ref = None
    if str(assetklasse or "").lower() in ("etf", "themen_etf"):
        try:
            from agent.hedge.pipeline import ist_hedge_instrument

            if not ist_hedge_instrument(symbol):
                ref = relative_staerke(reihe, index, db)
        except Exception:                                    # noqa: BLE001
            logger.info("Sektorbezug fuer %s nicht ermittelbar", symbol,
                        exc_info=True)
    return (
        baue_lagebild_eingabe(reihen, datum),
        baue_befund_eingabe(symbol=symbol, reihe=reihe, index=index,
                            kurs_eur=kurs_eur(symbol, reihe, index, db) or 0.0,
                            atr=atr_bis(reihe, index), menge=menge,
                            einstand_eur=einstand, finanzierung=fin,
                            lagebild=lagebild, instrument=instrument,
                            strategie=strategie, assetklasse=assetklasse,
                            gegenseite=gegenbestand_satz(symbol, db,
                                                         instrument),
                            referenz=ref,
                            bloecke_ziel=bloecke_ziel),
    )
