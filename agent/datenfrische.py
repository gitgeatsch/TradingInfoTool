# -*- coding: utf-8 -*-
"""Wie alt sind die Fakten, mit denen wir urteilen? (17.08.2026)

DER ANLASS - und er ist der teuerste Fehlertyp, den dieses Projekt kennt.

Rolle A traegt vier Aussagen, die NICHT aus einer Kursreihe stammen:
Netto-Liquiditaet, Zinskurve, Fear & Greed, und die lange Sicht. Am 17.08.
stellte sich heraus, dass DREI davon von einem Skript stammen, das ein
Mensch von Hand gestartet hat - und seither von keinem Job mehr:

    netto_liquiditaet_mrd   letzter Wert 2026-08-05   (12 Tage)
    rendite_10j_pct         letzter Wert 2026-08-11   ( 6 Tage)
    fear_greed_value        letzter Wert 2026-08-12   ( 5 Tage)
                            alle 3.111 Zeilen mit demselben
                            fetched_at: 2026-08-12T09:01

WARUM ES NIEMAND SAH. `marktlage.beschreibe_makro` nimmt den juengsten Wert
<= Ankertag - ohne Altersgrenze. Der Satz verschwindet also NICHT, wenn die
Reihe stehenbleibt. Er wird weiter erzeugt, weiter an das Modell gegeben,
weiter geglaubt - nur immer aelter. Ein fehlender Satz faellt auf; ein
alter Satz sieht aus wie ein frischer.

    Das ist "fail-soft ist fail-silent" in seiner unangenehmsten Form:
    hier faellt nicht einmal etwas aus. Es steht nur still.

DIE ZWEI ALTER. Jede Quelle wird an ZWEI Zeitpunkten gemessen, und die
Unterscheidung ist der ganze Trick:

    DATENSTAND    das juengste Datum IN der Reihe. Wie alt die Information
                  ist. Haengt am Anbieter: die CFTC veroeffentlicht
                  freitags, WALCL woechentlich, der CPI monatlich mit
                  Verzug. Ein hohes Datenalter kann voellig richtig sein.

    ABRUFSTAND    wann wir zuletzt ERFOLGREICH nachgesehen haben
                  (`geholt_am` / `fetched_at`). Das haengt an UNS, nicht am
                  Anbieter - und ist deshalb der eigentliche
                  Gesundheitswert. Alles hier wird taeglich angefasst; ist
                  der Abrufstand aelter als zwei Tage, laeuft kein Job.

Ein Anbieter, der nichts Neues hat, ist normal. Ein Job, der nicht laeuft,
ist es nie. Deshalb wird nur das Abrufalter als Fehler gewertet - das
Datenalter wird berichtet, mit einer grosszuegigen Obergrenze je Quelle.

WER DAS BENUTZT
    scheduler/background.py     nach jedem `lagebild_reihen_job` - loggt
                                jede veraltete Quelle als WARNUNG
    extract_notebook_diagnose   Abschnitt `datenfrische` im NB-Export
    pruefe_pakete.py            Selbsttest der Registratur

⚠️ NEUE QUELLE = NEUER EINTRAG. Dieselbe Falle wie bei
`SYMBOL_ZU_COT_ROHSTOFF` (Umbauplan 71.2): fehlt der Eintrag, wird die
Quelle nicht ueberwacht - still. `pruefe_pakete` vergleicht die Registratur
deshalb gegen `mindestkriterien.QUELLEN_G` und gegen die Quellen, die in
der Datenbank tatsaechlich vorkommen, und meldet jede, die hier fehlt.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

# Ab wann ein Abruf als ausgefallen gilt. Zwei Tage, nicht einer: die Jobs
# laufen morgens, und ein einzelner Fehlschlag (Anbieter kurz weg) soll
# nicht sofort Alarm sein. Drei waeren zu lang - dann steht ein Wochenende
# dazwischen und der Ausfall faellt erst am Dienstag auf.
MAX_ABRUFALTER_TAGE = 2

# Kennung einer Messquelle, die als reine Symbolliste uebertragen wurde
# (`baue_messbasis_paket.py`, Tabelle `_nur_symbolliste`) - siehe
# `_stand_datei`. Steht an der Stelle des Datenstands.
NUR_SYMBOLLISTE = "symbolliste"


@dataclass(frozen=True)
class Quelle:
    """Eine Faktenquelle, die in einen Prompt geht.

    `max_datenalter` ist die Obergrenze fuer den DATENSTAND und richtet
    sich nach dem Anbietertakt, nicht nach unserem. Sie ist bewusst
    grosszuegig: sie soll eine tote Reihe finden, keine langsame."""
    name: str
    rolle: str
    tabelle: str
    max_datenalter: int
    job: str
    zweck: str
    # ⚠️⚠️ EINE EIGENE DATEI (S-1, 11.09.2026). Bis hierher lagen ALLE
    # Quellen in der Betriebsdatenbank, und `conn` genuegte. Die drei
    # MESSquellen liegen in eigenen Dateien - `funding_historie.db`,
    # `terminmarkt_historie.db`, `onchain_historie.db`.
    #
    # WARUM SIE HIERHER GEHOEREN UND NICHT IN EINE ZWEITE REGISTRATUR:
    # zwei Registraturen fuer dieselbe Frage laufen auseinander - das
    # steht als Lehre schon im Projekt ("drei Kopien laufen garantiert
    # auseinander"). Die Frage ist dieselbe: wie alt ist das, worauf wir
    # uns stuetzen.
    datei: str = ""
    # ⚠️⚠️ WIE VIELE SYMBOLE EIN VOLLSTAENDIGER LAUF BERUEHRT (Schritt 50
    # Teil B, 13.09.2026). 0 heisst "keine Erwartung gesetzt" - dann wird
    # nur der Zeitstempel gemeldet wie bisher.
    #
    # ⚠️ DIE ZAHL GEHOERT ZUR MESSBASIS-DEFINITION, NICHT ZU EINER TABELLE.
    # Beim Bauen selbst hineingetappt: `terminmarkt_tag` hat 100 Symbole,
    # `terminmarkt` 122 - `MESSBASIS[oi]` ist die VEREINIGUNG und damit
    # 122. Und `funding_historie` fuehrt 302 Symbole, von denen 300 in
    # `messmenge.V1` liegen. Wer gegen eine Tabelle zaehlt, meldet einen
    # Fehlalarm.
    erwartet: int = 0
    # ⚠️⚠️ UEBER WELCHE TABELLEN DER VERMERK GEZAEHLT WIRD. Leer heisst
    # "die eine Tabelle oben". Der Terminmarkt braucht BEIDE: `MESSBASIS`
    # ist dort die VEREINIGUNG aus `terminmarkt` (stuendlich, 122) und
    # `terminmarkt_tag` (taeglich, 100). Wer nur die Tagestabelle zaehlt,
    # meldet 100 von 122 und damit einen Fehlalarm - mir beim Bauen
    # dieses Feldes selbst passiert, obwohl ich die Falle eine Zeile
    # darueber aufgeschrieben hatte.
    vermerk_tabellen: tuple = ()
    # Spalten, wenn die Tabelle keine `quelle`-Spalte hat: (Datum, Abruf).
    spalten: tuple = ()


# DIE REGISTRATUR. Je Zeile eine Quelle, die ein Modell tatsaechlich liest.
#
# Die Obergrenzen sind aus dem ANBIETERTAKT hergeleitet, nicht geschaetzt:
#
#   WALCL (Fed-Bilanz)      woechentlich, donnerstags      -> 21 Tage
#                           (drei versaeumte Veroeffentlichungen)
#   ^TNX/^IRX               jeder Handelstag               ->  6 Tage
#                           (Wochenende + zwei Feiertage)
#   Fear & Greed            taeglich, auch am Wochenende   ->  4 Tage
#   makro_historie_monat    monatlich, CPI mit ~2 Monaten
#                           Veroeffentlichungsverzug       -> 95 Tage
#   CFTC COT                woechentlich, freitags,
#                           Bericht vom Dienstag davor     -> 21 Tage
#   FINRA Leerverkaeufe     zweimal im Monat               -> 35 Tage
#   SEC Form 4              laufend, aber schubweise       -> 21 Tage
#   yfinance Fundamentals   quartalsweise                  -> 120 Tage
#   Boersenfluss/Stablecoin/
#   Optionsmarkt/ETF        taeglich                       ->  6 Tage
REGISTRATUR: tuple[Quelle, ...] = (
    Quelle("netto_liquiditaet", "A", "macro_snapshot", 21,
           "lagebild_reihen", "Geld im US-Finanzsystem"),
    Quelle("zinskurve", "A", "macro_snapshot", 6,
           "lagebild_reihen", "10 Jahre gegen kurzfristig"),
    Quelle("fear_greed", "A", "macro_snapshot", 4,
           "lagebild_reihen", "Stimmung"),
    Quelle("lange_sicht", "A", "makro_historie_monat", 95,
           "makro_analog", "99 Jahre Makrohistorie"),
    Quelle("coinmetrics", "G", "externe_reihe", 6,
           "externe_reihen", "Boersenfluesse auf der Kette"),
    # ⚠️ ROLLE "W" - KEINE PROMPTQUELLE, sondern der Nenner des Beitrags
    # turnover in der Wahrscheinlichkeit (Befund 2.453-turnover, 14.09.).
    # Taeglich wie die anderen Coin-Metrics-Reihen -> 6 Tage; der Leser
    # selbst nimmt nichts, was aelter als 21 Tage ist.
    Quelle("coinmetrics_splycur", "W", "externe_reihe", 6,
           "externe_reihen", "Umlaufmenge fuer turnover"),
    Quelle("defillama", "G", "externe_reihe", 6,
           "externe_reihen", "Stablecoin-Angebot"),
    Quelle("deribit", "G", "externe_reihe", 6,
           "externe_reihen", "Optionsmarkt (DVOL, Skew)"),
    Quelle("cftc_cot", "G", "externe_reihe", 21,
           "externe_reihen", "Terminmarkt-Positionierung Rohstoffe"),
    Quelle("etf_bestand", "G", "externe_reihe", 6,
           "externe_reihen", "hinterlegte Metallmenge"),
    Quelle("finra", "G", "externe_reihe", 35,
           "externe_reihen", "Leerverkaufsposition Aktien"),
    Quelle("sec_edgar", "G", "externe_reihe", 21,
           "externe_reihen", "Insidergeschaefte Aktien"),
    Quelle("yfinance", "BC", "externe_reihe", 120,
           "externe_reihen", "Gewinn- und Umsatzwachstum"),
    # DIE DREI, DIE NICHT IN `externe_reihe` STEHEN - und die groessten.
    #
    # Der Terminmarkt traegt Rolle G bei 43 Kryptowerten, also bei 93 %
    # aller Urteile; die Kerzenreihe traegt JEDEN Satz jeder Rolle; der
    # Bestand entscheidet, ob ein Urteil ueberhaupt ein Bestandsurteil ist.
    # Sie hier wegzulassen hiesse, die drei wichtigsten Quellen ausgerechnet
    # aus der Frischepruefung herauszuhalten - weil sie in einer anderen
    # Tabelle stehen.
    # Rolle BC UND G seit Schritt 5 (01.09.) - BC bekommt die Saetze in die
    # Faktenlage. Die feinere Frische (2 h Lese-, 6 h/24 h Meldegrenze) liegt
    # in `positionierung` und `terminmarkt_sammlung`; hier nur das tote Netz.
    Quelle("terminmarkt", "BC/G", "open_interest_snapshot", 2,
           "terminmarkt", "Open Interest, Funding, Long-Anteil"),
    Quelle("kursreihe", "A/BC/G", "price_history_ohlc", 4,
           "refresh_ohlc", "die Kerzen selbst"),
    # ⚠️ JOBNAME KORRIGIERT (14.09.2026, 2.453-bestand): die Scheduler-ID
    # heisst `bitpanda_holdings`, nicht `refresh_bitpanda_holdings` - die Mail
    # schickte den Leser zum Suchen nach einem Namen, der im Log nicht steht.
    Quelle("bestand", "BC", "holdings", 3,
           "bitpanda_holdings", "was tatsaechlich im Depot liegt"),
    # ⚠️⚠️ ROLLE "K" - DAS KAPITAL (H-1, 11.09.2026). Keine Promptquelle,
    # sondern die Bezugsgroesse fuer r x Kapital (P-5). Am Notebook stand
    # sie zehn Tage still, ohne dass es jemand erfuhr (2.341). Drei Tage:
    # der Job schreibt taeglich den Vortag.
    Quelle("kapital", "K", "portfolio_wert_historie", 3,
           "portfolio_wert", "Kapital fuer die Hebelrechnung (r x Kapital)"),
    # ⚠️⚠️ ROLLE "H" - DIE ECHTEN HEBELPOSITIONEN (15.09.2026, 2.453-hebelpos).
    # Keine Promptquelle, sondern der Bestand, auf dem Hebelfuehrung und
    # Aggregat-Deckel stehen. Die FEINE Frische (Mail ab 1 Stunde) liegt in
    # `hebel_abgleich` und laeuft im Job selbst; hier das TOTE NETZ, das auch
    # einen Job findet, der gar nicht mehr laeuft. Gelesen wird der Stempel
    # des letzten ERFOLGREICHEN Abgleichs, nicht die Tabelle - die aendert
    # sich nur, wenn gehandelt wird.
    Quelle("hebel_abgleich", "H", "hebel_positions", 1,
           "hebel_screening", "offene Hebelpositionen bei Bitpanda"),

    # ---- ⚠️⚠️⚠️ DIE DREI MESSQUELLEN (S-1, 11.09.2026) ----------------
    #
    # Nutzervorgabe: *"die API Abfragen und Datensammlungen am Notebook
    # muessen stabil umgesetzt werden, damit ein kurzer Ausfall so wie
    # heute keinen Schaden anrichten kann."*
    #
    # GEPRUEFT AM 11.09.: von 21 Scheduler-Jobs schreibt KEINER diese
    # drei. Sie werden von Hand gefuellt (`hole_fremdreihen.py`,
    # `hole_terminmarkt_historie.py`) - kein Misfire-Schutz, kein
    # Watchdog, kein Backoff, keine Meldung. Am Desktop hinkten sie 11
    # bis 13 Tage.
    #
    # ⚠️ ROLLE "M" - UND DAS IST DIE WICHTIGE UNTERSCHEIDUNG. A, BC und G
    # speisen PROMPTS: faellt dort etwas aus, urteilt das Modell auf
    # altem Stand. Diese drei speisen die MESSBASIS - die Symbolliste,
    # gegen die gerangt wird. Die laufenden WERTE kommen aus
    # Live-Abrufen (`marktrang._hole`), nicht von hier.
    #
    #     Fuer den BETRIEB      wenig kritisch - die Liste aendert sich
    #                           langsam
    #     Fuer MESSUNGEN und
    #     Kalibrierung          voll kritisch - jede Neumessung laeuft
    #                           auf diesem Stand
    #
    # Deshalb eigene Rolle: ein Ausfall hier ist eine MESS-Stoerung, kein
    # Betriebsausfall. Die Nutzervorgabe vom 10.09. gilt: *"Aenderungen
    # duerfen die Bewertung nicht blockieren - und schon gar nicht
    # still."* Blockieren tut hier nichts; das Schweigen faellt weg.
    #
    # ⚠️ 21 Tage Obergrenze, nicht 6: diese Reihen werden in Schueben
    # nachgeladen, nicht taeglich. Sie soll eine TOTE Quelle finden,
    # keine langsame - dieselbe Begruendung wie bei WALCL oben.
    Quelle("funding_reihe", "M", "funding", 21,
           "hole_fremdreihen.py (VON HAND)",
           "Messbasis des Funding-Rangs - 300 Symbole",
           datei="data/funding_historie.db", spalten=("datum", ""),
           # messmenge.ABDECKUNG[funding]
           erwartet=300),
    Quelle("terminmarkt_reihe", "M", "terminmarkt_tag", 21,
           "hole_terminmarkt_historie.py (VON HAND)",
           "Messbasis des Terminmarkt-Rangs - 122 Symbole",
           datei="data/terminmarkt_historie.db", spalten=("tag", ""),
           # MESSBASIS[oi] = Vereinigung beider Tabellen
           erwartet=122, vermerk_tabellen=("terminmarkt", "terminmarkt_tag")),
    Quelle("onchain_reihe", "M", "splycur", 21,
           # ⚠️ SEIT 13.09. GIBT ES DEN AUFRUF WIRKLICH (Befund 2.418).
           # Vorher stand hier "VON HAND" und meinte es woertlich: es gab
           # keinen, die Reihe war einmal manuell geholt worden. Genau
           # deshalb lief sie zwoelf Tage aus dem Takt, ohne aufzufallen.
           "hole_fremdreihen.py splycur (VON HAND)",
           "Umlaufmenge - Nenner des Turnover-Rangs, 66 Symbole",
           datei="data/onchain_historie.db", spalten=("datum", ""),
           # messmenge.ABDECKUNG[turnover]
           erwartet=66),
)

# Wie der Stand je Tabelle gelesen wird. Bewusst hier und nicht in der
# Registratur: drei Tabellen, zwoelf Quellen - die Abfrage gehoert zur
# Tabelle, nicht zur Zeile.
_SPALTE_MACRO = {
    "netto_liquiditaet": "netto_liquiditaet_mrd",
    "zinskurve": "rendite_10j_pct",
    "fear_greed": "fear_greed_value",
}

# {Tabelle: (Datumsspalte, Abrufspalte)}. `open_interest_snapshot` hat kein
# Datum - dort ist `fetched_at` beides.
_EINFACH = {
    "open_interest_snapshot": ("fetched_at", "fetched_at"),
    "price_history_ohlc": ("date", "fetched_at"),
    "holdings": ("updated_at", "updated_at"),
    "portfolio_wert_historie": ("datum", "berechnet_am"),
}


def _tage(stand: str | None, heute: date) -> int | None:
    """Alter in Tagen - oder None, wenn es keinen Stand gibt.

    Vertraegt beides: ein reines Datum ("2026-08-05") und einen vollen
    Zeitstempel ("2026-08-12T09:01:29+00:00"). Beide Formen kommen in
    denselben Spalten vor, je nachdem welcher Schreiber sie gefuellt hat -
    und ein `fromisoformat` auf der falschen Annahme waere genau die Sorte
    stiller Fehler, gegen die dieses Modul gebaut ist."""
    if not stand:
        return None
    try:
        return (heute - date.fromisoformat(str(stand)[:10])).days
    except ValueError:
        return None


def _stand_macro(conn, spalte: str) -> tuple[str | None, str | None, int]:
    try:
        zeile = conn.execute(
            f"SELECT MAX(date), MAX(fetched_at), COUNT(*) FROM macro_snapshot "
            f"WHERE {spalte} IS NOT NULL").fetchone()
    except Exception:                                        # noqa: BLE001
        return None, None, 0
    return (zeile[0], zeile[1], int(zeile[2] or 0)) if zeile else (None, None, 0)


def _stand_monat(conn) -> tuple[str | None, str | None, int]:
    """Die Monatstabelle fuehrt KEINEN Abrufstempel. Der Abrufstand kommt
    deshalb aus `job_laeufe` - was hier sogar genauer ist: die Tabelle
    aendert sich nur einmal im Monat, der Job laeuft taeglich."""
    try:
        monat, anzahl = conn.execute(
            "SELECT MAX(monat), COUNT(*) FROM makro_historie_monat").fetchone()
    except Exception:                                        # noqa: BLE001
        return None, None, 0
    abruf = None
    try:
        zeile = conn.execute(
            "SELECT zuletzt_am FROM job_laeufe WHERE job_id = 'makro_analog'"
        ).fetchone()
        abruf = zeile[0] if zeile else None
    except Exception:                                        # noqa: BLE001
        abruf = None
    # "2026-07" ist kein Datum - der erste des Monats ist die einzige
    # Lesart, die nicht in die Zukunft zeigt.
    return (f"{monat}-01" if monat else None, abruf, int(anzahl or 0))


def _stand_einfach(conn, tabelle: str, datum: str,
                   abruf: str) -> tuple[str | None, str | None, int]:
    """Fuer die drei Tabellen, die keine `quelle`-Spalte haben.

    `open_interest_snapshot` fuehrt ueberhaupt kein Datum, nur
    `fetched_at` - dort ist der Abrufzeitpunkt zugleich der Datenstand,
    und das ist richtig so: ein Open Interest gilt fuer den Moment, in dem
    er gemessen wurde."""
    try:
        zeile = conn.execute(
            f"SELECT MAX({datum}), MAX({abruf}), COUNT(*) FROM {tabelle}"
        ).fetchone()
    except Exception:                                        # noqa: BLE001
        return None, None, 0
    return (zeile[0], zeile[1], int(zeile[2] or 0)) if zeile else (None, None, 0)


# ⚠️⚠️⚠️ KURSREIHEN JE WERT (15.09.2026, Befunde 2.453-kursreihe, 2.453-spy).
#
# Bis hierher mass `kursreihe` die TABELLE: `MAX(fetched_at)` ueber ganz
# `price_history_ohlc`. Krypto wird taeglich geschrieben - und verdeckte damit
# alles andere. Die S&P-Referenz stand seit dem 13.08., Rohstoffe, Themen-ETF
# und Hedge liefen bis zu fuenf Tage hinterher; die Pruefung sagte ,frisch'.
# Dieselbe Blindstelle wie beim Terminmarkt (2.452).
#
# JETZT JE WERT: jedes Watchlist-Symbol (ohne Cash-Aequivalente) und jede
# Referenzreihe, die die Kette liest. Grenzen:
#
#   Krypto         2 Kalendertage   (`refresh_ohlc` taeglich, 24/7-Handel)
#   Wertpapiere    3 Handelstage    (Wochenenden zaehlen nicht; nachgeladen
#   und Referenzen                   wird seit 15.09. je Handelstag - 3 lassen
#                                    einen Feiertag und einen Aussetzer zu)
#
# ⚠️ EIN WERT OHNE JEDE REIHE WIRD NICHT GEMELDET, sondern unter `ohne_reihe`
# gefuehrt. Das ist Planpunkt A2 / 2.450-neu (Neuaufnahme), kein Ausfall - eine
# Meldung jeden Tag dafuer waere Rauschen.
KURS_GRENZE_KRYPTO_TAGE = 2
KURS_GRENZE_WERTPAPIER_HANDELSTAGE = 3
REFERENZ_SPY = "_THEMEN_ETF_BENCHMARK_SPY"


def _kursreihen_je_wert(conn, heute, watchlist=None) -> dict:
    """{geprueft, veraltet: [...], ohne_reihe: [...]} - fail-soft, nie werfend."""
    from staleness import handelstage_alter

    aus: dict = {"geprueft": 0, "veraltet": [], "ohne_reihe": []}
    try:
        if watchlist is None:
            import config as _cfg
            watchlist = _cfg.get_watchlist()
        from agent import assetklassen as _AK
    except Exception:                                        # noqa: BLE001
        return aus
    ziele: dict[str, tuple[str, str]] = {}       # symbol -> (art, job)
    for a in watchlist or []:
        if getattr(a, "ist_cash_aequivalent", False):
            continue
        try:
            g = _AK.gruppe(a)
        except Exception:                                    # noqa: BLE001
            continue
        sym = str(a.symbol).upper()
        if g == "krypto":
            ziele[sym] = ("krypto", "refresh_ohlc")
        else:
            ziele[sym] = ("wertpapier", "refresh_aktien_ohlc")
            if g in ("aktien", "themen_etf"):
                ziele[REFERENZ_SPY] = ("referenz", "refresh_aktien_ohlc")
            if str(getattr(a, "assetklasse", "")).lower() == "rohstoffe":
                ziele[f"_ROHSTOFF_FUTURES_{sym}"] = ("referenz", "refresh_aktien_ohlc")
            if g == "hedge":
                ziele[f"_HEDGE_INDEX_{sym}"] = ("referenz_optional", "refresh_aktien_ohlc")
    if not ziele:
        return aus
    try:
        platz = ",".join("?" * len(ziele))
        stand = {str(r[0]).upper(): r[1] for r in conn.execute(
            f"SELECT symbol, MAX(date) FROM price_history_ohlc "
            f"WHERE symbol IN ({platz}) GROUP BY symbol", list(ziele))}
    except Exception:                                        # noqa: BLE001
        return aus
    for sym, (art, job) in sorted(ziele.items()):
        letzt = stand.get(sym)
        if letzt is None:
            if art != "referenz_optional":
                aus["ohne_reihe"].append(sym)
            continue
        aus["geprueft"] += 1
        if art == "krypto":
            alter = _tage(str(letzt), heute)
            grenze, einheit = KURS_GRENZE_KRYPTO_TAGE, "Tage"
        else:
            alter = handelstage_alter(str(letzt), heute)
            grenze, einheit = KURS_GRENZE_WERTPAPIER_HANDELSTAGE, "Handelstage"
        if alter is not None and alter > grenze:
            aus["veraltet"].append({"symbol": sym, "stand": str(letzt)[:10],
                                    "alter": alter, "einheit": einheit,
                                    "grenze": grenze, "job": job})
    return aus


def _stand_bestand(conn) -> tuple[str | None, str | None, int]:
    """Der Bestand: Stand und Abruf = der letzte ERFOLGREICHE Abgleich.

    ⚠️⚠️ BEFUND 2.453-bestand (14.09.2026). Bis hierher las diese Quelle
    `holdings.updated_at` - geschrieben nur bei einer MENGENAENDERUNG. Ein
    ruhiger Bestand sah nach zwei Tagen aus wie ein toter Job, und die
    Pruefung mailte ,Handlungsbedarf' (14.09. 19:54, Abgleich lief alle 30
    Minuten). Ein Bestand gilt fuer den Moment, in dem nachgesehen wurde -
    deshalb ist der Abgleichszeitpunkt Datenstand UND Abrufstand.

    DREI STUFEN, in dieser Reihenfolge:
        1  `bitpanda_holdings_synced_at` - gesetzt am Ende jedes erfolgreichen
           Bestandsabgleichs
        2  `cash_reserve_synced_at` - der Cash-Abruf laeuft im selben
           Abgleich mit; nur der UEBERGANG bis zum ersten Lauf nach dem
           Einspielen, sonst meldete genau dieser Start wieder falsch
        3  `holdings.updated_at` - nur ohne jeden Bitpanda-Abgleich (von Hand
           gepflegter Bestand), das fruehere Verhalten"""
    try:
        anzahl = int(conn.execute("SELECT COUNT(*) FROM holdings").fetchone()[0] or 0)
    except Exception:                                        # noqa: BLE001
        return None, None, 0
    for schluessel in ("bitpanda_holdings_synced_at", "cash_reserve_synced_at"):
        try:
            zeile = conn.execute("SELECT value FROM meta WHERE key = ?",
                                 (schluessel,)).fetchone()
        except Exception:                                    # noqa: BLE001
            zeile = None
        if zeile and zeile[0]:
            return str(zeile[0]), str(zeile[0]), anzahl
    return _stand_einfach(conn, "holdings", *_EINFACH["holdings"])


def _abrufvermerk(c, q) -> str | None:
    """"X von Y Symbolen, zuletzt am ..." - oder None, wenn es ihn nicht gibt.

    ⚠️ Er ist ADDITIV eingefuehrt: solange kein Ladelauf ihn geschrieben
    hat, gibt es ihn nicht, und der Aufrufer bleibt bei der Dateizeit.
    Eine leere Tabelle als "0 von 300 beruehrt" zu melden waere ein
    Fehlalarm ueber die eigene Umstellung.
    """
    if not q.erwartet:
        return None
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                         "AND name='abruf_symbol'").fetchone():
            return None
        # ⚠️ DISTINCT: ein Symbol, das in BEIDEN Terminmarkt-Tabellen
        # steht, ist EIN Symbol der Messbasis, nicht zwei.
        tabs = q.vermerk_tabellen or (q.tabelle,)
        zeile = c.execute(
            "SELECT COUNT(DISTINCT symbol), MAX(zuletzt_ok) FROM abruf_symbol "
            "WHERE tabelle IN (%s)" % ",".join("?" * len(tabs)),
            tabs).fetchone()
    except Exception:                                        # noqa: BLE001
        return None
    n = int((zeile or (0,))[0] or 0)
    if not n:
        return None
    return "%s (%d von %d Symbolen)" % (
        str(zeile[1] or "")[:19], n, q.erwartet)


def _stand_datei(q) -> tuple[str | None, str | None, int]:
    """Eine Quelle in einer EIGENEN Datei (S-1, 11.09.2026).

    ## ⚠️⚠️ DER ABRUFSTAND KOMMT AUS DER DATEIZEIT — und warum das geht

    Keine der drei Messquellen fuehrt eine `fetched_at`-Spalte; sie haben
    nur `datum` bzw. `tag`. Damit waere der ABRUFSTAND nicht messbar - und
    genau der ist nach dem Kopf dieses Moduls *"der eigentliche
    Gesundheitswert"*, weil er an UNS haengt und nicht am Anbieter.

    **Die Aenderungszeit der Datei beantwortet dieselbe Frage.** Die
    Skripte (`hole_fremdreihen.py`, `hole_terminmarkt_historie.py`)
    schreiben die Datei; ihre mtime ist damit der Zeitpunkt des letzten
    erfolgreichen Schreibens.

    ⚠️ **Was daran ungenau ist, und es gehoert gesagt:** eine mtime
    aendert sich auch bei einem TEILWEISEN Schreiben. Sie beweist also
    nicht, dass der Abruf vollstaendig war - nur, dass ueberhaupt einer
    stattfand. Fuer die Frage *"laeuft der Job noch?"* genuegt das; fuer
    *"war er vollstaendig?"* nicht. Eine echte `fetched_at`-Spalte waere
    besser und ist der naechste Schritt, wenn die Quellen Jobs bekommen.
    """
    import os
    import sqlite3
    pfad = q.datei
    if not pfad or not os.path.exists(pfad):
        return None, None, 0
    try:
        abruf = datetime.fromtimestamp(
            os.stat(pfad).st_mtime, timezone.utc).isoformat(
                timespec="seconds")
    except OSError:
        abruf = None
    datum_spalte = (q.spalten or ("datum",))[0]
    try:
        c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
        # ⚠️⚠️ AM NOTEBOOK LIEGT NUR DIE SYMBOLLISTE (Gegenpruefung 11.09.).
        # `baue_messbasis_paket.py` uebertraegt die drei Dateien als reine
        # Symbollisten (wenige Kilobyte statt 176 MB) und markiert sie mit
        # der Tabelle `_nur_symbolliste`. Dort gibt es kein Datum - die
        # erste Fassung von S-1 las das als ,fehlt' und haette am Notebook
        # mit jedem Lauf Alarm geschlagen. Die Symbolliste IST dort der
        # Sollzustand; gemessen wird am Desktop.
        if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                     "AND name='_nur_symbolliste'").fetchone():
            anzahl = c.execute("SELECT COUNT(*) FROM %s"
                               % q.tabelle).fetchone()[0]
            c.close()
            return NUR_SYMBOLLISTE, abruf, int(anzahl or 0)
        zeile = c.execute(
            "SELECT MAX(%s), COUNT(*) FROM %s"
            % (datum_spalte, q.tabelle)).fetchone()
        # ---- ⚠️⚠️ DER ABRUFVERMERK schlaegt die Dateizeit ---------------
        #
        # Die mtime beweist, dass GESCHRIEBEN wurde - nicht, dass der
        # Abruf VOLLSTAENDIG war (2.359-abruf). `abruf_symbol` fuehrt je
        # Symbol den Zeitpunkt des letzten Erfolgs; daraus wird
        # "X von Y erwarteten Symbolen".
        #
        # ⚠️ FEHLT DIE TABELLE ODER IST SIE LEER, bleibt alles wie bisher.
        # Sie fuellt sich erst mit dem naechsten Ladelauf - eine leere
        # Tabelle als "0 von 300" zu melden waere ein Fehlalarm ueber
        # unsere eigene Umstellung.
        vermerk = _abrufvermerk(c, q)
        c.close()
        if vermerk:
            abruf = vermerk
    except Exception:                                        # noqa: BLE001
        return None, abruf, 0
    if not zeile:
        return None, abruf, 0
    return zeile[0], abruf, int(zeile[1] or 0)


def _stand_extern(conn, quelle: str) -> tuple[str | None, str | None, int]:
    try:
        zeile = conn.execute(
            "SELECT MAX(datum), MAX(geholt_am), COUNT(*) FROM externe_reihe "
            "WHERE quelle = ?", (quelle,)).fetchone()
    except Exception:                                        # noqa: BLE001
        return None, None, 0
    return (zeile[0], zeile[1], int(zeile[2] or 0)) if zeile else (None, None, 0)


def _stand_hebel_abgleich(conn) -> tuple[str | None, str | None, int]:
    """Der Hebel-Abgleich: Stand und Abruf = der letzte ERFOLGREICHE Abgleich.

    ZWEI STUFEN:
        1  `hebel_positions_synced_at` - gesetzt am Ende jedes erfolgreichen
           Hebel-Abgleichs (`hebel_abgleich.stempel_setzen`)
        2  `bitpanda_holdings_synced_at` - nur der UEBERGANG bis zum ersten
           Lauf nach dem Einspielen: derselbe Bitpanda-Zugang, derselbe
           Endpunkt. Ohne ihn meldete die Datenfrische beim ersten Start
           ,fehlt', weil ihr Lauf vor dem ersten Abgleich liegen kann.

    Ohne beide: kein Bitpanda-Abgleich je gelaufen -> ,fehlt'. Die Zeilenzahl
    ist die der Positionen, aber mindestens 1, sobald ein Stempel steht: wer nie
    mit Hebel gehandelt hat, hat eine leere Tabelle und trotzdem einen
    funktionierenden Abgleich."""
    try:
        anzahl = int(conn.execute("SELECT COUNT(*) FROM hebel_positions").fetchone()[0] or 0)
    except Exception:                                        # noqa: BLE001
        anzahl = 0
    for schluessel in ("hebel_positions_synced_at", "bitpanda_holdings_synced_at"):
        try:
            zeile = conn.execute("SELECT value FROM meta WHERE key = ?",
                                 (schluessel,)).fetchone()
        except Exception:                                    # noqa: BLE001
            zeile = None
        if zeile and zeile[0]:
            return str(zeile[0]), str(zeile[0]), max(anzahl, 1)
    return None, None, anzahl


def pruefe(conn, heute: date | None = None,
           mit_dateien: bool = True, watchlist=None) -> list[dict]:
    """Eine Zeile je Quelle - Stand, Alter, Urteil.

    `urteil` ist eines von vier Woertern, und die Reihenfolge ist die der
    Dringlichkeit:

        "fehlt"      die Quelle hat ueberhaupt keine Zeile. Entweder nie
                     gelaufen, oder die Tabelle gibt es nicht.
        "abruf"      wir sehen seit ueber zwei Tagen nicht mehr nach.
                     DAS IST DER JOBAUSFALL - unser Fehler.
        "daten"      wir fragen, aber der Anbieter liefert seit ueber
                     seiner eigenen Taktzeit nichts. Kann echt sein
                     (Feiertagswoche), kann eine tote Reihe sein.
        "frisch"     alles in Ordnung.

    FAIL-SOFT, ABER NICHT STILL: faellt eine einzelne Abfrage aus, steht
    "fehlt" in der Zeile - nicht nichts. Eine Pruefung, die bei einem
    Fehler ein leeres Ergebnis liefert, meldet "alles frisch"."""
    heute = heute or datetime.now(timezone.utc).date()
    aus: list[dict] = []
    for q in REGISTRATUR:
        # ⚠️⚠️ DATEIQUELLEN LESEN AN `conn` VORBEI (11.09.2026, von der
        # Pruefsuite gefangen). Sie oeffnen einen FESTEN Pfad unter
        # `data/`. Ein Test, der eine kuenstliche Datenbank uebergibt,
        # kann sie damit nicht umlenken - er baute alles frisch auf und
        # bekam trotzdem drei Befunde aus den echten Dateien.
        #
        # ⚠️ Der Fehler war MEINER, nicht der des Tests: wer eine Quelle
        # an einen festen Pfad bindet, nimmt ihr die Testbarkeit. Bis die
        # drei einen Job haben (und damit eine `fetched_at`-Spalte in der
        # Betriebs-DB), bleibt das so - `mit_dateien=False` ist die
        # ehrliche Zwischenloesung, nicht die schoene.
        #
        # Die Dateiquellen haben eigene Dauerpruefungen im Paket
        # "Terminmarkt" - sie sind nicht ungeprueft, nur anders.
        if q.datei and not mit_dateien:
            continue
        if q.datei:
            daten, abruf, anzahl = _stand_datei(q)
        elif q.tabelle == "macro_snapshot":
            daten, abruf, anzahl = _stand_macro(conn, _SPALTE_MACRO[q.name])
        elif q.tabelle == "makro_historie_monat":
            daten, abruf, anzahl = _stand_monat(conn)
        elif q.tabelle == "holdings":
            daten, abruf, anzahl = _stand_bestand(conn)
        elif q.tabelle == "hebel_positions":
            daten, abruf, anzahl = _stand_hebel_abgleich(conn)
        elif q.tabelle in _EINFACH:
            daten, abruf, anzahl = _stand_einfach(conn, q.tabelle,
                                                  *_EINFACH[q.tabelle])
        else:
            daten, abruf, anzahl = _stand_extern(conn, q.name)
        alter_daten, alter_abruf = _tage(daten, heute), _tage(abruf, heute)
        # ⚠️⚠️ ZWEI KORREKTUREN AUS DER GEGENPRUEFUNG VON S-1 (11.09.2026).
        # Beide haetten am Notebook ab dem ersten Lauf Alarm geschlagen:
        #
        # 1. Die SYMBOLLISTE ist dort der Sollzustand, kein Ausfall. Sie
        #    bekommt ein eigenes Urteil und wird nicht gemeldet - leer
        #    bleibt sie ein ,fehlt'.
        # 2. Die Messbasis wird VON HAND nachgeladen, sie hat keinen Job.
        #    Die Zwei-Tage-Grenze fuer den Abruf traf sie nach 48 Stunden,
        #    obwohl ihre Registratur ausdruecklich sagt, sie solle eine
        #    TOTE Quelle finden, keine langsame. Fuer Rolle M gilt deshalb
        #    die eigene Obergrenze auch fuer den Abruf.
        abrufgrenze = (q.max_datenalter if q.rolle == "M"
                       else MAX_ABRUFALTER_TAGE)
        if daten == NUR_SYMBOLLISTE:
            urteil = "liste" if anzahl else "fehlt"
            alter_daten = None
        elif not anzahl or alter_daten is None:
            urteil = "fehlt"
        elif alter_abruf is None or alter_abruf > abrufgrenze:
            urteil = "abruf"
        elif alter_daten > q.max_datenalter:
            urteil = "daten"
        else:
            urteil = "frisch"
        zeile = {
            "quelle": q.name, "rolle": q.rolle, "job": q.job,
            "zweck": q.zweck, "zeilen": anzahl,
            "datenstand": daten, "datenalter_tage": alter_daten,
            "abrufstand": abruf, "abrufalter_tage": alter_abruf,
            "max_datenalter_tage": q.max_datenalter, "urteil": urteil,
        }
        # KURSREIHEN JE WERT - eigenes Urteil ,werte', wenn die Tabelle lebt,
        # aber einzelne Werte stehen (Befund 2.453-kursreihe). Ein Tabellen-
        # ausfall (,fehlt'/,abruf') bleibt das staerkere Urteil.
        if q.name == "kursreihe":
            je_wert = _kursreihen_je_wert(conn, heute, watchlist)
            zeile["werte_geprueft"] = je_wert["geprueft"]
            zeile["veraltete_werte"] = je_wert["veraltet"]
            zeile["ohne_reihe"] = je_wert["ohne_reihe"]
            if je_wert["veraltet"] and urteil in ("frisch", "daten"):
                zeile["urteil"] = "werte"
        aus.append(zeile)
    return aus


def stillgelegt_hinweis(config: dict | None,
                        kandidaten: int = 0) -> str | None:
    """Sagt, wenn eine LEERE Liste an einer abgeschalteten Quelle liegt.

    ⚠️⚠️ SCHRITT 40, 12.09.2026 - der Kern von "Altbestand stilllegen".
    Nutzervorgabe: *"damit wir nicht laufend ueber Altbestaende stolpern,
    sollten wir diese sauber stilllegen"*.

    Seit dem 12.09. steht `hebel_screening.aktiv` auf false. Die
    Kandidatenliste im Hebel-Tab ist damit dauerhaft leer - und eine leere
    Liste sagt zwei voellig verschiedene Dinge:

        "es gibt gerade keinen Kandidaten"   ein Befund
        "hier schaut niemand mehr nach"      ein Zustand

    Ohne diesen Satz sind beide nicht zu unterscheiden, und der Nutzer sucht
    beim naechsten Mal wieder danach. Dieselbe Klasse wie 2.386 und
    2.389-log: ein abgesprochener Zustand, der aussieht wie ein Ausfall.

    ⚠️ SIE GIBT AUCH DANN EINEN SATZ, WENN NOCH KANDIDATEN DA SIND - dann
    ist er sogar wichtiger: Zeilen aus einer abgeschalteten Quelle sind
    Altbestand, egal wie frisch sie aussehen."""
    an = bool(((config or {}).get("hebel_screening") or {}).get("aktiv"))
    if an:
        return None
    if kandidaten:
        return ("⚠ %d Kandidat%s aus dem STILLGELEGTEN Screening - "
                "Altbestand, es kommen keine neuen dazu"
                % (kandidaten, "en" if kandidaten != 1 else ""))
    return ("Screening stillgelegt (hebel_screening.aktiv = false) - "
            "keine neuen Kandidaten, das ist kein Ausfall")


def auffaellig(zeilen: list[dict]) -> list[dict]:
    """Nur die Zeilen, die nicht frisch sind - fuer Log und Export.

    ⚠️ ,liste' ist nicht auffaellig: am Notebook ist die Symbolliste der
    Sollzustand der Messbasis (Gegenpruefung S-1, 11.09.2026)."""
    return [z for z in zeilen if z.get("urteil") not in ("frisch", "liste")]


def als_text(zeilen: list[dict]) -> list[str]:
    """Eine Zeile Klartext je Quelle - fuer das Log und die Konsole."""
    aus = []
    for z in zeilen:
        aus.append(
            # Datum auf zehn Zeichen: `open_interest_snapshot` fuehrt einen
            # vollen Zeitstempel, und der sprengt jede Spaltenbreite.
            f"{z['urteil']:>7s}  {z['quelle']:<18s} Rolle {z['rolle']:<8s} "
            f"Daten {str(z['datenstand'] or '-')[:10]:<12s} "
            f"({'-' if z['datenalter_tage'] is None else z['datenalter_tage']} T)  "
            f"Abruf {str(z['abrufstand'] or '-')[:10]:<12s} "
            f"({'-' if z['abrufalter_tage'] is None else z['abrufalter_tage']} T)  "
            f"{z['zeilen']} Zeilen")
    return aus
