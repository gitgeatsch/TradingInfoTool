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
    Quelle("terminmarkt", "G", "open_interest_snapshot", 2,
           "hebel_screening", "Open Interest, Funding, Long-Anteil"),
    Quelle("kursreihe", "A/BC/G", "price_history_ohlc", 4,
           "refresh_ohlc", "die Kerzen selbst"),
    Quelle("bestand", "BC", "holdings", 3,
           "refresh_bitpanda_holdings", "was tatsaechlich im Depot liegt"),
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


def _stand_extern(conn, quelle: str) -> tuple[str | None, str | None, int]:
    try:
        zeile = conn.execute(
            "SELECT MAX(datum), MAX(geholt_am), COUNT(*) FROM externe_reihe "
            "WHERE quelle = ?", (quelle,)).fetchone()
    except Exception:                                        # noqa: BLE001
        return None, None, 0
    return (zeile[0], zeile[1], int(zeile[2] or 0)) if zeile else (None, None, 0)


def pruefe(conn, heute: date | None = None) -> list[dict]:
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
        if q.tabelle == "macro_snapshot":
            daten, abruf, anzahl = _stand_macro(conn, _SPALTE_MACRO[q.name])
        elif q.tabelle == "makro_historie_monat":
            daten, abruf, anzahl = _stand_monat(conn)
        elif q.tabelle in _EINFACH:
            daten, abruf, anzahl = _stand_einfach(conn, q.tabelle,
                                                  *_EINFACH[q.tabelle])
        else:
            daten, abruf, anzahl = _stand_extern(conn, q.name)
        alter_daten, alter_abruf = _tage(daten, heute), _tage(abruf, heute)
        if not anzahl or alter_daten is None:
            urteil = "fehlt"
        elif alter_abruf is None or alter_abruf > MAX_ABRUFALTER_TAGE:
            urteil = "abruf"
        elif alter_daten > q.max_datenalter:
            urteil = "daten"
        else:
            urteil = "frisch"
        aus.append({
            "quelle": q.name, "rolle": q.rolle, "job": q.job,
            "zweck": q.zweck, "zeilen": anzahl,
            "datenstand": daten, "datenalter_tage": alter_daten,
            "abrufstand": abruf, "abrufalter_tage": alter_abruf,
            "max_datenalter_tage": q.max_datenalter, "urteil": urteil,
        })
    return aus


def auffaellig(zeilen: list[dict]) -> list[dict]:
    """Nur die Zeilen, die nicht frisch sind - fuer Log und Export."""
    return [z for z in zeilen if z.get("urteil") != "frisch"]


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
