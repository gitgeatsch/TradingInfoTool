# -*- coding: utf-8 -*-
"""DIE ABRUFKETTE VON ANFANG BIS ENDE - simuliert, nicht geprueft (16.08.2026).

NUTZERVORGABE: *"die Abrufkette pruefen und simulieren bzw. testen - von Anfang
bis zum Ende."*

WAS DIESES SKRIPT KANN, WAS `pruefe_pakete.py` NICHT KANN. Die 853
Paketpruefungen sind statisch: sie lesen Quelltext und rufen einzelne
Funktionen. Sie haben heute dreimal etwas NICHT gefunden, das erst beim
Durchlaufen sichtbar wurde - die Abgrenzung des Sektorbezugs (`etf` statt
`themen_efp`), die Klassen-Einstufung, die bei zwei von fuenf Gruppen nie
ankam, und den zweiten Bloeckeaufruf mit dem falschen ATR.

    Eine Kette, die in jedem Einzelteil stimmt, kann als Ganzes reissen.

WAS SIMULIERT WIRD UND WAS ECHT IST:

    ECHT    Kursreihen, Bestaende, Fakten, Lagebeschreibung, Rechnung,
            Gate-Stufen, Anlassmessung, Signalabbildung, DB-Schreiben,
            Mailaufbau, Rolle-G-Zeilen
    ATTRAPPE die beiden Modellaufrufe (Rolle A, Rolle BC) und Z.ai

Die Attrappe antwortet DETERMINISTISCH und durchlaeuft je Gruppe alle
Aktionen des jeweiligen Vokabulars - `NICHTS_TUN` genauso wie `EROEFFNEN`.
Ein Testlauf, der nur den einfachen Fall nimmt, prueft den Zweig nicht, in dem
die Fehler sitzen.

⚠️ NIEMALS GEGEN DIE ECHTE DATENBANK. Die Kette SCHREIBT in `probe` - deshalb
wird die Datenbank zuerst in den Scratchpad kopiert und ausschliesslich die
Kopie benutzt. Der Pfad wird ausgegeben, damit er nachpruefbar ist.

BETRIEBSART `probe`, NICHT `trocken`. Der Trockenlauf ueberspringt genau die
Stufen, um die es hier geht: er schreibt nicht, misst den Anlass nicht und
ruft Rolle G nicht. Ein Trockenlauf haette am 15.08. schon einmal die
abgeschaltete Stufe geprueft und fuer gruen erklaert.

AUFRUF:  python simuliere_kette.py [--db PFAD] [--gruppe krypto]
"""
from __future__ import annotations

import argparse
import re as _re

from ui import formatting as _FORM

# ⚠️ EIN PUNKT ZWISCHEN ZIFFERN IST NUR ALS TAUSENDERPUNKT ERLAUBT.
# Meine erste Fassung war `\d+\.\d` und fand nur einstellige
# Nachkommastellen: "2.5" ja, "3.81" nein - das  scheitert an der
# zweiten Ziffer. Sie meldete sauber, wo es nicht sauber war.
_ENG_ZAHL = _re.compile(r"(?<![\d.])\d+\.(\d+)")


# ⚠️ EIN DEUTSCHES DATUM IST KEINE ENGLISCHE ZAHL (20.08.2026).
#
# Mit dem Terminkalender (93 D) stand erstmals ein Datum in der Mail:
# "FOMC-Sitzung (15.09.-16.09.2026)". Die Pruefung meldete daraufhin acht
# Luecken - "15.09" und "16.09" sahen fuer sie aus wie 15.09 in englischer
# Dezimalschreibweise. Der Fehler lag NICHT in der Mail.
#
# Datumsangaben werden deshalb vorher herausgeschnitten. Sie zu ignorieren
# ist richtig, sie zu erlauben waere falsch: "1.5" bleibt ein Fund.
_DATUM = _re.compile(r"\b\d{1,2}\.\d{1,2}\.(?:\d{2,4})?")


NUR_SYMBOLE: set = set()


def _echte_config() -> dict:
    """Die Konfiguration des BETRIEBS, nicht eine Minimalattrappe.

    ⚠️ GEFUNDEN AM 28.08.2026. Der zweite Lauf uebergab
    `config={"anlass": {"aktiv": True}}`, der erste gar nichts - beide fielen
    damit auf die CODE-Vorgaben zurueck statt auf `config.yaml`. Folge:

        Simulation   verlustanteil 15 %  ->  bei 5,23 % Stop Hebel 2,87
        Produktion   verlustanteil  6 %  ->  bei 5,23 % Stop Hebel 1,15

    Die Simulation zeigte also einen echten Hebel, wo der Betrieb keinen
    erzeugt. Sie prueft die KETTE zuverlaessig, aber sie prueft nicht die
    BETRAEGE des Produktionsstands - und genau die sind seit S5 die Frage.

    `anlass.aktiv` bleibt gesetzt: der Anlassfilter soll in der Simulation
    laufen, das war der Zweck der ursprfuenglichen Zeile."""
    import config as _C

    cfg = dict(_C.load_config() or {})
    cfg.setdefault("anlass", {})
    if isinstance(cfg["anlass"], dict):
        cfg["anlass"] = dict(cfg["anlass"])
        cfg["anlass"]["aktiv"] = True
    else:
        cfg["anlass"] = {"aktiv": True}
    return cfg


def _englische_zahlen(text: str) -> list[str]:
    """Zahlen in englischer Schreibweise. Genau drei Ziffern nach dem Punkt
    gelten als Tausendergruppe (1.234,5) und zaehlen nicht; Datumsangaben
    im Format 15.09. oder 16.09.2026 ebenso wenig."""
    text = _DATUM.sub(" ", text)
    return sorted({m.group(0) for m in _ENG_ZAHL.finditer(text)
                   if len(m.group(1)) != 3})

import json
import sqlite3
import sys
import tempfile
from pathlib import Path

# Die Aktionen, die eine Attrappe je Instrument durchspielen soll. Bewusst
# ALLE - der Verkaufszweig war am 14.08. der groesste Fund des Echtbetriebs,
# und er wurde von keinem Test beruehrt.
AKTIONEN_JE_INSTRUMENT = {
    "spot": ("KAUFEN", "NACHKAUFEN", "REDUZIEREN", "VERKAUFEN", "NICHTS_TUN"),
    "hebel": ("ERÖFFNEN", "NACHKAUFEN", "HEBEL_ERHÖHEN", "HEBEL_SENKEN",
              "TEILVERKAUF", "SCHLIESSEN", "HALTEN"),
    "absicherung": ("KAUFEN", "NACHKAUFEN", "REDUZIEREN", "VERKAUFEN",
                    "NICHTS_TUN"),
}


def _hat_eigene_grundlage(conn, symbol: str, assetklasse: str) -> bool:
    """Liegt zu DIESEM Wert eine symbolspezifische Grundlage vor?

    Der BTC-weite Boersenfluss zaehlt nicht - er sagt ueber ein einzelnes
    Symbol nichts, und genau daran haengt G5.

    ⚠️ DIE KLASSE WIRD DURCHGEREICHT, NICHT AUF "krypto" GESETZT
    (17.08.2026). Vorher stand hier fest `assetklasse="krypto"` - fuer
    eine Aktie wurden damit die Aktienquellen (Leerverkaeufer, Insider)
    gar nicht erst geholt, und die Antwort war immer False.

    Genau daran haengt die Pruefung unten: sie meldete jede Aktie mit
    Gegenpruefung als "urteilt OHNE Grundlage" - obwohl beide Aktien G1
    UND G2 erfuellen, seit FINRA und SEC am 16.08. dazugekommen sind.
    Das Kriterium beschrieb einen Zustand, den es nicht mehr gibt."""
    from agent import mindestkriterien as MK
    from agent import positionierung as PO

    try:
        lage = PO.lage(conn, str(symbol).upper(), assetklasse=assetklasse)
    except Exception:                                    # noqa: BLE001
        return False
    return any(q in MK.SYMBOLSPEZIFISCH_G for q in MK.quellen_g(lage))


class Attrappe:
    """Ein Modell-Client, der die Form der echten hat und nichts abruft.

    DIE FORM IST DER PUNKT. `rollen_lauf._frage()` haelt in seinem eigenen
    Docstring fest, dass eine frei erfundene Client-Schnittstelle erst beim
    ersten ECHTEN Aufruf auffliegt - mit verbrauchtem Kontingent. Diese
    Attrappe nimmt deshalb genau das entgegen, was dort uebergeben wird:
    eine Nachrichtenliste, `model`, `response_format`, `temperature`."""

    def __init__(self, instrument: str = "spot"):
        self.instrument = instrument
        self.aufrufe = 0
        self._zaehler = 0
        self.gesehen: list[dict] = []

    def chat(self, nachrichten, **kwargs):
        self.aufrufe += 1
        system = str(nachrichten[0].get("content") or "")
        eingabe = json.loads(nachrichten[1]["content"])
        self.gesehen.append({"system": system[:60], "eingabe": eingabe})
        if "Marktlage" in system or "Leitmaerkte" in system or \
                "marktlage" in eingabe:
            return json.dumps({
                "lage": "Die drei Leitmaerkte laufen auseinander: Krypto steht "
                        "37,6 % unter dem Vorjahresstand, der breite "
                        "US-Aktienmarkt 19,7 % darueber. Die Netto-Liquiditaet "
                        "liegt 3,2 % ueber dem Stand von vor 26 Wochen.",
                "klassen": [
                    {"klasse": "krypto", "einstufung": "unguenstig",
                     "warum": "37,6 % unter dem Stand von vor 250 Handelstagen"},
                    {"klasse": "aktien", "einstufung": "guenstig",
                     "warum": "1,9 % unter dem Hoch dieser 250 Handelstage"},
                    {"klasse": "rohstoffe", "einstufung": "gemischt",
                     "warum": "12,3 % ueber dem Stand von vor 250 Handelstagen"},
                ],
                "belege": ["Bitcoin schwankt taeglich um 2,7 % des Kurses, im "
                           "17. Perzentil der letzten 250 Handelstage"],
            }, ensure_ascii=False)

        aktionen = AKTIONEN_JE_INSTRUMENT.get(self.instrument, ("NICHTS_TUN",))
        aktion = aktionen[self._zaehler % len(aktionen)]
        self._zaehler += 1
        # Der Einstieg folgt dem echten Kurs aus den Fakten - eine erfundene
        # Zahl liefe sofort in die Stopabstands-Untergrenze und der Lauf
        # wuerde etwas anderes pruefen als gemeint.
        kurs = _kurs_aus_fakten(eingabe)
        antwort = {
            "belege": [
                {"fakt": "Der naechste Widerstand liegt 1,3 "
                         "Schwankungsbreiten hoeher", "richtung": "dagegen",
                 "gewicht": "mittel"},
                {"fakt": "Von den letzten 20 Tagen entfielen 42 % des "
                         "Umsatzes auf Aufwaertstage", "richtung": "dagegen",
                 "gewicht": "gering"},
                {"fakt": "Auf Sicht der letzten 17 Handelstage zeigt die "
                         "Marktstruktur hoehere Hochs", "richtung": "dafuer",
                 "gewicht": "hoch"},
            ],
            "unabhaengige_faktoren": 3,
            "aktion": aktion,
            "begruendung": "Die Struktur dreht, der Umsatz traegt sie noch "
                           "nicht.",
            "was_dagegen": "Der Umsatz liegt ueberwiegend auf Abwaertstagen.",
            "umgeworfen_durch": "Ein Schlusskurs unter der naechsten "
                                "Unterstuetzung",
            "umgeworfen_preis_eur": round(kurs * 0.93, 8),
            "umgeworfen_bis": None,
        }
        # ⚠️ S6c (22.08.2026): HING AM INSTRUMENT, WIE DER VERTRAG SELBST.
        #
        # Hier stand `if self.instrument == "hebel"`. Als S6c die
        # Richtungspflicht instrumentunabhaengig machte, lieferte diese
        # Attrappe fuer Spot weiter keine Richtung - und die Simulation
        # meldete 6 Fehler und NULL Signale. Das war kein Fehlalarm, sondern
        # genau die Auskunft, fuer die es sie gibt: wenn das Modell die
        # Richtung nicht nennt, kommt nichts mehr durch.
        #
        # DER PROMPT VERLANGT SIE SEIT S6a FUER BEIDE INSTRUMENTE ("Bei
        # KAUFEN und NACHKAUFEN nenne ZUSAETZLICH die Richtung"). Die
        # Attrappe bildet jetzt ab, was der Prompt fordert - nicht weniger.
        from agent.empfehlung_vertrag import BRAUCHT_RICHTUNG
        if aktion in BRAUCHT_RICHTUNG:
            antwort["richtung"] = "LONG"
        if aktion not in ("NICHTS_TUN", "HALTEN"):
            antwort["einstieg_eur"] = round(kurs, 8)
            antwort["stop_eur"] = round(kurs * 0.94, 8)
        return json.dumps(antwort, ensure_ascii=False)


class ZaiAttrappe:
    """Rolle G. Antwortet abwechselnd mit und ohne Einwand, damit BEIDE
    Mailzweige durchlaufen - der Bestaetigungszweig ist erst seit dem 16.08.
    ueberhaupt sichtbar."""

    def __init__(self):
        self.aufrufe = 0

    def chat(self, nachrichten, **kwargs):
        self.aufrufe += 1
        ja = self.aufrufe % 2 == 1
        return json.dumps(
            {"einwand": "ja" if ja else "nein",
             "grund": ("die Finanzierungsrate steht im 96. Perzentil"
                       if ja else "Funding im gewohnten Bereich")},
            ensure_ascii=False)


def _kurs_aus_fakten(eingabe: dict) -> float:
    """Den Kurs aus dem Bestand- oder Markenblock fischen.

    Rueckfall 1.0, wenn nichts gefunden wird - dann prueft der Lauf immer noch
    die Verdrahtung, nur nicht die Groessenordnungen."""
    import re

    for satz in (eingabe.get("stand") or []):
        m = re.search(r"bei ([\d.,]+) EUR", str(satz))
        if m:
            try:
                return float(m.group(1).replace(",", "."))
            except ValueError:
                pass
    return 1.0


def _kopie(quelle: str, name: str = "simuliere_kette.db") -> str:
    """Die Datenbank in den Scratchpad kopieren - ueber SQLites eigene
    Sicherung, nicht ueber das Dateisystem.

    ⚠️ HIER STAND EINE DATEIKOPIE, UND SIE IST AM 17.08. GEBROCHEN.

    Die Fassung davor kopierte drei Dateien einzeln (`.db`, `-wal`, `-shm`)
    und begruendete das richtig: ohne das WAL fehlt der juengste Stand. Nur
    ist das ZIEL dasselbe, jeden Lauf. Steht dort noch ein WAL von 08:19
    (102 MB) und die Quelle hat inzwischen eingecheckt (0 Byte), passen
    Hauptdatei und Beileger nicht mehr zusammen:

        sqlite3.DatabaseError: database disk image is malformed

    Genau so ist die Simulation heute gescheitert - und das ist der
    freundliche Ausgang. Ein WAL, das zufaellig noch LESBAR ist, haette
    keinen Fehler geworfen, sondern die Kette gegen einen alten Stand
    laufen lassen, und niemand haette es gesehen.

    `Connection.backup()` loest beides: es liest ueber SQLite (das WAL ist
    also automatisch drin), schreibt EINE in sich stimmige Datei, und
    braucht danach keine Beileger mehr. Die Quelle wird `mode=ro`
    geoeffnet - gelesen, nie geschrieben."""
    ziel = Path(tempfile.gettempdir()) / name
    # Erst die Reste des letzten Laufs weg. Ohne das liegt neben der frisch
    # gesicherten Datei weiter das alte WAL - und genau daran ist es
    # gescheitert.
    for endung in ("", "-wal", "-shm"):
        alt = Path(str(ziel) + endung)
        if alt.exists():
            alt.unlink()
    quell_conn = sqlite3.connect(f"file:{quelle}?mode=ro", uri=True)
    try:
        ziel_conn = sqlite3.connect(str(ziel))
        try:
            quell_conn.backup(ziel_conn)
            # Derselbe Massstab wie beim NB-Export: die Kopie wird geprueft,
            # bevor jemand ihr glaubt. Sonst ersetzt eine Vermutung
            # ("backup() wird schon stimmen") die alte Vermutung, die eben
            # gebrochen ist.
            befund = ziel_conn.execute(
                "PRAGMA integrity_check").fetchone()[0]
            if befund != "ok":
                raise SystemExit(f"[ABBRUCH] Die Kopie ist beschaedigt: "
                                 f"{befund[:200]}")
        finally:
            ziel_conn.close()
    finally:
        quell_conn.close()
    return str(ziel)


def _verbindung(pfad: str) -> sqlite3.Connection:
    """Eine Verbindung, die sich verhaelt wie die der Produktion.

    ⚠️ DAS IST KEIN DETAIL, ES WAR DER ERSTE FUND DIESER SIMULATION. Ohne
    `row_factory = sqlite3.Row` scheitern `db.get_latest_prices()` und
    `db.get_all_holdings()` mit

        TypeError: tuple indices must be integers or slices, not str

    und beide Aufrufe stehen hinter einem breiten `except`. Im Lauf sah das aus
    wie zwei echte Defekte: *"Kurse fuer die Ausstiegspruefung nicht ladbar"*
    und *"VVMX: Bestand nicht lesbar"*. Beides waere ein Fehlalarm gewesen -
    `database/db.py::get_connection()` setzt die Zeilenfabrik, die Produktion
    ist in Ordnung.

    ES BLEIBT TROTZDEM EIN BEFUND, nur ein anderer: derselbe Fehler hat heute
    frueh die Regime-Dauer der Rolle G still gekostet, weil `rolle_g` seine
    eigene Verbindung oeffnet. Wer eine Verbindung selbst aufmacht, erbt diese
    Einstellung NICHT - und der breite Fehlerfang macht daraus einen
    Halbsatz, der fehlt.

    Deshalb wird hier nicht nur gesetzt, sondern GEPRUEFT: weicht die
    Produktion je davon ab, faellt es hier auf und nicht im Betrieb."""
    from database import db as DBM
    import inspect

    quelle = inspect.getsource(DBM.get_connection)
    if "row_factory = sqlite3.Row" not in quelle:
        raise SystemExit(
            "db.get_connection() setzt keine Zeilenfabrik mehr - diese "
            "Simulation bildet die Produktion dann nicht mehr ab. Erst dort "
            "nachsehen, dann hier nachziehen.")
    conn = sqlite3.connect(pfad)
    conn.row_factory = sqlite3.Row
    return conn



def nachweis_n14(db: str) -> int:
    """N-14 NACHWEISEN: die OI-Sperre im ECHTEN Lauf, nicht in der Suite.

    Stehende Regel: *eine Stufe gilt erst als gebaut, wenn die
    Kettensimulation sie nachweist.* Die Suite prueft Eigenschaften des
    Codes; ob die Stufe im Lauf ueberhaupt erreicht wird und ob sie dort
    das Richtige tut, sagt sie nicht. Genau daran ist G-6 am 31.08.
    vorbeigelaufen: 1828 Pruefungen gruen, echte Produktion 0 Signale.

    SECHS FAELLE, jeder mit eigenem Haken:

        A  Fuenftel 4, einstieg, kein Bestand   -> GESPERRT
        B  Fuenftel 1, einstieg                 -> durch, ohne Notiz
        C  kein Rang,  einstieg                 -> NOTIZ, durch
        D  Fuenftel 4, MIT Bestand              -> NOTIZ, durch
        E  Fuenftel 4, akkumulation             -> NOTIZ, durch
        F  gesperrt wird NUR, wer Fuenftel 4 ohne Bestand hatte

    ⚠️⚠️ JE FALL EIN EIGENER LAUF - und das ist die Lehre aus fuenf
    verworfenen Fassungen.

    Der Grund steht in `auswahl.k_fuer`: bei zehn und mehr Werten
    passieren genau **zwei**. Werte MIT Bestand sind davon ausgenommen und
    kommen immer durch. In einer Kopie, die ueberwiegend Bestand fuehrt,
    erreichen die Stufe also fast nur Bestandswerte - und die Faelle A, B
    und C, die alle einen BESTANDSFREIEN Wert brauchen, konkurrieren um
    zwei Plaetze. Drei Rollen auf zwei Plaetzen: der Nachweis konnte in
    einem gemeinsamen Lauf gar nicht vollstaendig werden.

    Mit EINEM Symbol je Lauf ist `k_fuer(1) = 0` und die Auswahlstufe
    entscheidet nicht (`aktiv=False`, "eine Stufe, die nichts entscheiden
    kann, darf nicht sperren"). Damit erreicht jeder Fall die Stufe, die
    er pruefen soll.

    ⚠️ Was dieser Aufbau NICHT zeigt: das Zusammenspiel mit der
    Auswahlstufe. Das ist Absicht - dafuer ist der normale Lauf der
    Simulation da, und dort steht die Stufe seit heute in der
    Trichtertabelle.
    """
    from agent import rollen_lauf as RL
    from agent import rollen_eingabe as _RE_probe
    from backtest_llm1_historisch import lade_reihen_aus_db

    reihen = lade_reihen_aus_db(db)
    kandidaten = [s for s in reihen
                  if len(reihen.get(s) or ()) > 60 and not s.startswith("_")]
    mit, ohne = [], []
    for s in kandidaten:
        try:
            _m, _e = _RE_probe.bestand(s, db, "spot")
            (mit if (_m and float(_m) > 0) else ohne).append(s)
        except Exception:                                    # noqa: BLE001
            ohne.append(s)
    print()
    print("=" * 76)
    print("N-14 NACHWEIS — die OI-Sperre im Lauf")
    print("=" * 76)
    print("  %d Reihen in der Kopie: %d mit Bestand, %d ohne"
          % (len(kandidaten), len(mit), len(ohne)))
    if not ohne or not mit:
        print("N-14: die Kopie hat nicht beide Sorten - Nachweis nicht "
              "moeglich")
        return 1

    def _lauf(strategie, syms, raenge):
        conn = _verbindung(db)
        try:
            e = RL.fuehre_lauf(
                conn=conn, reihen=reihen, symbole=list(syms),
                betriebsart="probe", instrument="spot",
                strategie=strategie, client=Attrappe("spot"),
                modell="attrappe", config=_echte_config(), db=db,
                zai_client=ZaiAttrappe(), assetklasse="krypto",
                versand=None, antworten={"marktraenge": raenge})
        finally:
            conn.commit()
            conn.close()
        tr = e.get("durchlauf")
        return {"gruende": tr.gruende.get("terminmarkt") or {},
                "notizen": tr.notizen.get("terminmarkt") or {},
                "verloren": tr.verloren_je_stufe.get("terminmarkt", 0),
                "bestanden": tr.bestanden_je_stufe.get("terminmarkt", 0),
                "durchlauf": tr}

    HOCH = {"oi_fuenftel": 4, "querschnitt_oi": 122,
            "funding_fuenftel": 1, "turnover_fuenftel": 1}
    TIEF = {"oi_fuenftel": 1, "querschnitt_oi": 122,
            "funding_fuenftel": 1, "turnover_fuenftel": 1}
    KEIN = {"funding_fuenftel": 1, "turnover_fuenftel": 1}

    def _erster_der_ankommt(sorte, rang, strategie="einstieg", grenze=6):
        """Der erste Wert dieser Sorte, der die Stufe wirklich erreicht.

        ⚠️ NOETIG, WEIL EINZELNE REIHEN VORHER AUSSCHEIDEN - vier Werte
        der Kopie haben keine Daten ab dem 19.08. und fallen an `fakten`.
        Ein einzelner Bewerber machte den Nachweis von der Reihenfolge
        des Zufalls abhaengig; hier wird bis zu `grenze` Mal versucht,
        und wenn keiner ankommt, ist das ein ehrliches "nicht gezeigt".
        """
        for s in sorte[:grenze]:
            # ⚠️ IMMER EIN GESTELLTER EINTRAG, auch fuer "kein Rang".
            # Ein LEERES Woerterbuch gilt in `fuehre_lauf` als "nichts
            # gestellt" (`if _gestellt:`) - dann holt der Lauf die echten
            # Raenge aus dem Netz, und Fall C prueft, was Binance heute
            # sagt, statt was gestellt war. Genau daran ist Fassung 7
            # gescheitert: das Symbol kam mit einem echten Rang an und
            # lief wortlos durch.
            #
            # "Kein Rang" heisst deshalb: ein Eintrag OHNE den Schluessel
            # `oi_fuenftel`, nicht ein fehlender Eintrag.
            r = _lauf(strategie, [s], {s: dict(rang)})
            if r["verloren"] + r["bestanden"]:
                r["symbol"] = s
                return r
        return None

    a = _erster_der_ankommt(ohne, HOCH)
    b = _erster_der_ankommt(ohne, TIEF)
    c = _erster_der_ankommt(ohne, KEIN)
    d = _erster_der_ankommt(mit, HOCH)
    kern = [s for s in ("ETH", "SOL", "BTC") if s in reihen]
    e_ = _erster_der_ankommt(kern or mit, HOCH, strategie="akkumulation")

    for name, r in (("A", a), ("B", b), ("C", c), ("D", d), ("E", e_)):
        if r is None:
            print("  %s  kein Bewerber hat die Stufe erreicht" % name)
            continue
        print("  %s  %-10s gesperrt %d · durch %d%s"
              % (name, r["symbol"], r["verloren"], r["bestanden"],
                 "".join("\n         %s: %s" % ("gesperrt" if k == "g"
                                                else "Notiz", t)
                         for k, d2 in (("g", r["gruende"]),
                                       ("n", r["notizen"]))
                         for t in d2)))

    faelle = [
        ("A  Fuenftel 4 wird gesperrt",
         bool(a) and any("hoechsten Fuenftel" in g for g in a["gruende"]),
         "kein bestandsfreier Wert mit Fuenftel 4 hat die Stufe erreicht"),
        ("B  darunter wird durchgelassen, ohne Notiz",
         bool(b) and b["bestanden"] > 0 and b["verloren"] == 0
         and not b["notizen"],
         "erwartet: durch und wortlos"),
        ("C  ohne Rang: Notiz statt Sperre",
         bool(c) and c["verloren"] == 0
         and any("kein OI-Rang" in g for g in c["notizen"]),
         "erwartet: Notiz 'kein OI-Rang' und keine Sperre"),
        ("D  mit Bestand: Notiz statt Sperre",
         bool(d) and d["verloren"] == 0
         and any("Bestand" in g for g in d["notizen"]),
         "erwartet: Notiz 'Bestand' und keine Sperre - sonst wuerde die "
         "Ausstiegsfrage unterdrueckt"),
        ("E  Akkumulationslauf ohne Sperre",
         bool(e_) and e_["verloren"] == 0,
         "erwartet: keine Sperre - die Messung ankert auf einem EINSTIEG"),
        ("F  nur Fuenftel 4 wird gesperrt",
         all(r is None or r["verloren"] == 0 for r in (b, c, d, e_)),
         "ein Wert ohne Fuenftel 4 wurde gesperrt"),
    ]
    print()
    print("  " + "-" * 72)
    offen = 0
    for name, erfuellt, hinweis in faelle:
        print("  %s  %s%s" % ("✔" if erfuellt else "✖", name,
                              "" if erfuellt else "   <- %s" % hinweis))
        offen += 0 if erfuellt else 1
    # ---- E2: DER STRATEGIE-ZWEIG - und warum er hier NICHT faellt ------
    #
    # ⚠️ FALL E ZEIGT WENIGER, ALS SEIN NAME VERSPRICHT, und das gehoert
    # gesagt. Gepruefte Eigenschaft ist "im Akkumulationslauf wird nicht
    # gesperrt". Die Notiz, die dabei erscheint, lautet aber "Bestand
    # vorhanden" - es greift also die BESTANDSausnahme, nicht die
    # Strategieausnahme.
    #
    # Der Grund ist strukturell und in dieser Kopie nicht zu umgehen:
    # Kern-Assets sind genau die, die gehalten werden (ETH, SOL, BTC
    # haben alle Bestand). Und die zweite Zelle eines Assets faellt
    # ohnehin an `anlass` - die Einstiegszelle hat denselben Faktensatz
    # schon verbraucht ("nur 0 zaehlende Blockaenderungen"). Die
    # Akkumulationszelle erreicht die Stufe damit gar nicht.
    #
    # Statt das als Erfolg zu buchen, wird es BENANNT. Den Zweig selbst
    # deckt das Suite-Paket "Terminmarkt" ueber den Syntaxbaum ab.
    _strategiezweig = bool(e_) and any(
        "Messung gilt nur fuer den Einstieg" in g for g in e_["notizen"])
    print("  %s  E2 der Strategie-Zweig selbst%s"
          % ("✔" if _strategiezweig else "○",
             "" if _strategiezweig else
             "   <- in dieser Kopie nicht erreichbar: alle Kern-Assets "
             "haben Bestand (die Bestandsausnahme greift zuerst), und die "
             "zweite Zelle faellt an `anlass`. Strukturell geprueft im "
             "Suite-Paket 'Terminmarkt'"))

    print("  " + "-" * 72)
    if offen:
        print("  ✖ NICHT VOLLSTAENDIG NACHGEWIESEN - %d von 6 Faellen offen."
              % offen)
        print("    Ein offener Fall heisst NICHT 'falsch', sondern 'in "
              "diesem Lauf nicht gezeigt'. Beides darf nicht verschwimmen.")
        print("=" * 76)
        return 1
    print("  ✔ VOLLSTAENDIG NACHGEWIESEN - alle sechs Faelle gezeigt.")
    print("=" * 76)
    return 0

def nachweis_paket_b(quelle: str) -> int:
    """SCHRITT 23 - PAKET B VON ANFANG BIS ENDE, mit einem GEZIELT erzeugten
    Hebelgeschaeft (11.09.2026).

    Befund 2.371: bis zum 11.09. ist NIE ein Hebelgeschaeft durch die Kette
    gelaufen - weder im Betrieb (Schalter aus) noch in dieser Simulation. Die
    Suite prueft H-2, H-4, H-5 und S-4 einzeln; ob sie im Lauf zusammen die
    richtige Mail, Zeile, Sperre und Summe ergeben, sagt sie nicht.

    STEUERBAR IST DIE ATTRAPPE UEBER DIE MARKTRAENGE - dieselben Fuenftel, aus
    denen `potential.rechne()` die Quote bildet (gerechnet 11.09.):

        Funding 0 + Turnover 0   Quote 0,373 -> r 1,25 %  -> Hebel (bis 5x)
        ohne Beitrag             Quote 0,333 -> r 0       -> Spot

    ZWEI KOPIEN, beide im Temp-Verzeichnis, nie die Quelle:

        A  Schalter AN   Hebelgeschaeft · Hebelfuehrung · Deckel ausgeschoepft
        B  Schalter AUS  derselbe Spot-Trade als Vergleich (N-38) · Akkumulation

    Warum zwei: die Anlass-Sperre laesst denselben Faktensatz nur einmal
    durch. Ein Vergleichslauf in derselben Kopie hinge an ihr, nicht am
    Schalter.

    ⚠️ DIE KUENSTLICHEN POSITIONEN LIEGEN AUF SYMBOLEN OHNE KURSREIHE (ZZPLAN,
    ZZOHNESTOP, ZZVOLL). Sie fallen an `fakten`, bevor ein Modell gefragt
    wird - Hebelfuehrung und Deckel lesen aber `hebel_positions`, nicht die
    Kursreihen. Geschrieben wird ueber die ECHTEN Schreiber
    (`felder_aus_entscheidung`, `schreibe_signal`, `upsert_hebel_position`):
    eine von Hand gesetzte Zeile hat H-4 schon einmal verdeckt (Befund
    2.379-instrument-korrektur). Und sie entstehen NACH dem Zurueckdatieren -
    der erste H-4-Lauf verlor die Zuordnung genau daran.
    """
    from datetime import datetime, timedelta, timezone

    from agent import assetklassen as AK
    from agent import hebel_aggregat as HAG
    from agent import portfolio_historie as PH
    from agent import rollen_eingabe as RE
    from agent import rollen_lauf as RL
    from agent import signal_abbildung as SA
    from agent import toepfe as TO
    from agent import wiederholung as WH
    from agent.betraege import hebel_aus_quote_einstellungen
    from agent.schreibweise import de
    from backtest_llm1_historisch import lade_reihen_aus_db
    from database import db as DBM
    from database.models import HebelPosition

    HEBEL = {"funding_fuenftel": 0, "turnover_fuenftel": 0,
             "oi_fuenftel": 1, "querschnitt_oi": 122}
    OHNE = {"oi_fuenftel": 1, "querschnitt_oi": 122}
    ablage = Path(tempfile.gettempdir()) / "simuliere_kette_mails"
    ablage.mkdir(exist_ok=True)
    faelle: list = []

    def fall(name, erfuellt, beleg=""):
        faelle.append((name, bool(erfuellt)))
        print("  %s  %s" % ("✔" if erfuellt else "✖", name))
        for z in [x for x in str(beleg or "").splitlines() if x.strip()][:14]:
            print("         " + z)

    def konfig(aktiv: bool) -> dict:
        c = _echte_config()
        rk = dict(c.get("rollen_kette") or {})
        rk["hebel_aus_quote"] = {**dict(rk.get("hebel_aus_quote") or {}),
                                 "aktiv": aktiv}
        c["rollen_kette"] = rk
        return c

    def vorbereiten(name: str) -> str:
        db = _kopie(quelle, name)
        # Derselbe Grund wie in `main`: sonst prueft der Lauf den Cooldown der
        # Produktion statt der Kette.
        with _verbindung(db) as c0:
            for tabelle in ("signals", "hebel_signals"):
                try:
                    c0.execute(f"UPDATE {tabelle} SET created_at = "
                               f"datetime(created_at, '-30 days')")
                except sqlite3.Error:
                    pass
            c0.commit()
        return db

    def einfuegen(c, tabelle, werte):
        spalten = list(c.execute(f"PRAGMA table_info({tabelle})"))
        w = dict(werte)
        for s in spalten:
            if s[1] not in w and s[3] and s[4] is None and not s[5]:
                w[s[1]] = 0 if any(t in (s[2] or "").upper()
                                   for t in ("INT", "REAL")) else "x"
        cols = [k for k in w if k in {s[1] for s in spalten}]
        c.execute("INSERT OR REPLACE INTO %s (%s) VALUES (%s)" % (
            tabelle, ",".join(cols), ",".join("?" * len(cols))),
            [w[k] for k in cols])

    def position(c, symbol, *, auf, hebel, ek, kurs=None, einstand=100.0):
        pw = hebel * ek
        DBM.upsert_hebel_position(c, HebelPosition(
            symbol=symbol, richtung="LONG", status="offen",
            eroeffnet_am=auf.isoformat(),
            letzte_transaktion_unix_timestamp=int(auf.timestamp()),
            hebel_effektiv=hebel, positionswert_eur=pw,
            kreditbetrag_eur=pw - ek, eigenkapital_eur=ek,
            positionsmenge=pw / einstand))
        if kurs is not None:
            einfuegen(c, "price_cache", {"symbol": symbol, "price_eur": kurs,
                                         "price_usd": kurs / 0.9,
                                         "fetched_at": jetzt.isoformat()})
        c.commit()

    def lauf(db, symbole, raenge, cfg, strategie="einstieg"):
        modell = Attrappe("spot")
        conn = _verbindung(db)
        try:
            e = RL.fuehre_lauf(
                conn=conn, reihen=reihen, symbole=list(symbole),
                betriebsart="probe", instrument="spot", strategie=strategie,
                client=modell, modell="attrappe", config=cfg, db=db,
                zai_client=ZaiAttrappe(), assetklasse="krypto", versand=None,
                antworten={"marktraenge": raenge})
        finally:
            conn.commit()
            conn.close()
        e["_aufrufe"] = modell.aufrufe
        return e

    def ablegen(eintrag, name):
        if not eintrag:
            return
        (ablage / ("paket_b_%s.txt" % name)).write_text(
            str(eintrag.get("text") or ""), encoding="utf-8")
        for nr, b in enumerate(eintrag.get("bilder") or []):
            if b.get("png"):
                (ablage / ("paket_b_%s_%d.png" % (name, nr))).write_bytes(b["png"])

    def mail_zu(e, symbol):
        return next((m for m in e.get("mails") or []
                     if m.get("symbol") == symbol), None)

    def betrag(text):
        m = _re.search(r"^Betrag\s+([\d.,]+) EUR - (.+)$", text or "", _re.M)
        return (m.group(1), m.group(2).strip()) if m else (None, None)

    def gruende(e, stufe):
        tr = e.get("durchlauf")
        return [str(g) for g in ((getattr(tr, "gruende", {}) or {}).get(stufe)
                                 or {})]

    def verluste(e):
        tr = e.get("durchlauf")
        return {k: v for k, v in (getattr(tr, "verloren_je_stufe", {})
                                  or {}).items() if v}

    def signal_von(e, symbol):
        return next((s for s in e.get("signale") or []
                     if s.get("symbol") == symbol and s.get("id")), None)

    def zeile(db, sid):
        c = _verbindung(db)
        try:
            r = c.execute("SELECT * FROM signals WHERE id = ?", (sid,)).fetchone()
            return dict(r) if r else {}
        finally:
            c.close()

    def toepfe(db):
        c = _verbindung(db)
        try:
            return TO.belegt_eur(c, "hebel"), TO.belegt_eur(c, "spot")
        finally:
            c.close()

    def sperre_stunden(db, symbol, erzeugt, cfg):
        c = _verbindung(db)
        try:
            bis = WH.gesperrt_bis(c, symbol, "spot", config=cfg, gruppe="krypto")
        finally:
            c.close()
        if not bis:
            return None
        a0 = datetime.fromisoformat(str(erzeugt).replace("Z", "+00:00"))
        a0 = a0 if a0.tzinfo else a0.replace(tzinfo=timezone.utc)
        return (datetime.fromisoformat(bis) - a0).total_seconds() / 3600.0

    def mit(text, *worte):
        return "\n".join(z for z in str(text or "").splitlines()
                         if any(w in z for w in worte))

    print("=" * 76)
    print("SCHRITT 23 - PAKET B VON ANFANG BIS ENDE")
    print("=" * 76)
    dbA = vorbereiten("paket_b_schalter_an.db")
    print("Quelle  : %s" % quelle)
    print("KOPIE A : %s   (Schalter an)" % dbA)
    reihen = lade_reihen_aus_db(dbA)
    AN, AUS = konfig(True), konfig(False)
    ein = hebel_aus_quote_einstellungen(AN)
    jetzt = datetime.now(timezone.utc).replace(microsecond=0)
    c = _verbindung(dbA)
    try:
        kap = PH.aktuelles_kapital(c)
        erlaubt = {r[0] for r in c.execute(
            "SELECT symbol FROM asset_hebel_settings "
            "WHERE hebel_pruefung_erlaubt = 1")}
    finally:
        c.close()
    if not kap.get("verwendbar"):
        print("✖ ABBRUCH - Kapital nicht verwendbar: %s" % kap.get("satz"))
        return 1
    K = float(kap["wert_eur"])
    deckel = float(ein["aggregat_anteil"]) * K
    print("Kapital : %s EUR (%s) - Aggregat-Deckel %s EUR"
          % (de(K, 0), kap.get("zustand"), de(deckel, 2)))
    krypto = next((list(s) for g, i, s in AK.laeufe() if g == "krypto"), [])
    kandidaten = []
    for s in krypto:
        if len(reihen.get(s) or ()) <= 60 or s not in erlaubt:
            continue
        try:
            menge, _ = RE.bestand(s, dbA, "spot")
        except Exception:                                    # noqa: BLE001
            menge = None
        if not (menge and float(menge) > 0):
            kandidaten.append(s)
    kandidaten.sort(key=lambda s: (s != "ONDO", s))
    print("Kandidaten (Hebel erlaubt, kein Bestand): %s" % ", ".join(kandidaten[:12]))

    # ---- DIE POSITIONEN - nach dem Zurueckdatieren, ueber die echten Schreiber
    c = _verbindung(dbA)
    auf1 = jetzt - timedelta(days=3.5)
    _rech = {"etikett": "hebel", "hebel": 5.0, "verlust_am_stop_eur": 57.5,
             "hebel_aus_quote": {"ist_hebel": True},
             "einstieg_von_eur": 99.5, "einstieg_bis_eur": 100.5,
             "stop_eur": 88.5, "ziel_von_eur": 123.0, "ziel_bis_eur": 125.0}
    plan_id = SA.schreibe_signal(c, SA.felder_aus_entscheidung(
        {"aktion": "KAUFEN", "richtung": "LONG",
         "begruendung": "E2E Paket B - der Plan der Position"},
        fakten={}, rechnung=_rech, instrument="spot", strategie="einstieg",
        eur_je_usd=0.9, modell="attrappe"),
        symbol="ZZPLAN", erstellt_am=(auf1 - timedelta(hours=2)).isoformat())
    position(c, "ZZPLAN", auf=auf1, hebel=5.0, ek=100.0, kurs=100.0)
    position(c, "ZZOHNESTOP", auf=jetzt - timedelta(hours=5), hebel=4.0, ek=150.0)
    c.close()
    print("Positionen: ZZPLAN 5x seit 3,5 Tagen, Plan-Signal %s (Stop 11,5 %%) · "
          "ZZOHNESTOP 4x ohne Signal und ohne Kurs" % plan_id)

    # ================================================================ A1
    print("\n--- A1  DAS HEBELGESCHAEFT ---")
    S1 = e1 = None
    for s in kandidaten[:6]:
        vor = toepfe(dbA)
        e = lauf(dbA, [s, "ZZPLAN", "ZZOHNESTOP"], {s: HEBEL}, AN)
        sg = signal_von(e, s)
        if sg and (sg.get("felder") or {}).get("instrument") == "hebel":
            S1, e1, vor1 = s, e, vor
            break
        print("  %s: kein Hebelsignal - %d Signale, Verluste %r"
              % (s, len(e.get("signale") or []), verluste(e)))
    if not S1:
        fall("A1 ein Hebelgeschaeft entsteht", False,
             "kein Kandidat kam als Hebel durch - Nachweis nicht moeglich")
        return 1
    z1 = zeile(dbA, signal_von(e1, S1)["id"])
    print("  Wert %s - Signal %s" % (S1, z1.get("id")))
    fall("H1 die Signalzeile ist ein HEBELgeschaeft: instrument 'hebel', "
         "Hebel 2 bis 5x, Verlust am Stop gesetzt",
         z1.get("instrument") == "hebel"
         and 2.0 <= float(z1.get("hebel") or 0) <= float(ein["hebel_grenze"]) + 1e-9
         and float(z1.get("verlust_am_stop_eur") or 0) > 0,
         "instrument %r · hebel %r · verlust_am_stop_eur %r · action %r"
         % (z1.get("instrument"), z1.get("hebel"),
            z1.get("verlust_am_stop_eur"), z1.get("action")))
    m1 = mail_zu(e1, S1)
    ablegen(m1, "1_hebelgeschaeft")
    t1 = str((m1 or {}).get("text") or "")
    b1 = betrag(t1)
    fall("H2 die Mail: Betrag MIT Hebel, Hebelrechnung samt Aggregat-Satz, "
         "Liquidation, Anhang C",
         bool(m1) and str(b1[1] or "").startswith("Hebel")
         and "Aggregat-Deckel:" in t1 and "Zwangsaufloesung" in t1,
         "Betreff: %s\n" % (m1 or {}).get("betreff")
         + mit(t1, "Betrag  ", "Aggregat-Deckel", "Liquidation", "Zwangsaufloesung",
               "Hebel aus der", "r(q)"))
    png = [b for b in (m1 or {}).get("bilder") or []
           if (b.get("png") or b"")[:4] == b"\x89PNG"]
    fall("H3 der Chart zur Mail entsteht", bool(png),
         "%d PNG - abgelegt unter %s" % (len(png), ablage))
    nach1 = toepfe(dbA)
    _ts = float(z1.get("position_size_eur") or 0.0)
    fall("H4 Hebeltopf: das Signal belegt den HEBEL-Topf, der Spot-Topf bleibt",
         _ts > 0 and abs((nach1[0] - vor1[0]) - _ts) < 1e-6
         and abs(nach1[1] - vor1[1]) < 1e-6,
         "Hebeltopf %s -> %s EUR · Spot-Topf %s -> %s EUR · Tranche %s EUR"
         % (de(vor1[0], 0), de(nach1[0], 0), de(vor1[1], 0), de(nach1[1], 0),
            de(_ts, 0)))
    _std1 = sperre_stunden(dbA, S1, z1.get("created_at"), AN)
    _soll_h = WH.stunden("spot", AN, "krypto", strategie="einstieg",
                         hebel_zuletzt=float(z1.get("hebel") or 0))
    _soll_s = WH.stunden("spot", AN, "krypto", strategie="einstieg",
                         hebel_zuletzt=1.2)
    fall("H5 Cooldown: der kurze Takt fuer Hebel (%s h statt %s h)"
         % (de(_soll_h, 1), de(_soll_s, 1)),
         _std1 is not None and abs(_std1 - _soll_h) < 0.02 and _soll_h < _soll_s,
         "gesperrt fuer %s Stunden ab dem Signal" % (de(_std1, 2) if _std1 else "-"))
    ha1 = e1.get("hebel_aggregat") or {}
    fall("H6 Aggregat-Deckel im Lauf: ZZPLAN Liquidation vor dem Stop = "
         "Eigenkapital 100 + ZZOHNESTOP 11,7 % von 600 = 70,20 -> offen 170,20",
         abs(float(ha1.get("offen_eur") or -1) - 170.2) < 0.01
         and abs(float(ha1.get("deckel_eur") or 0) - deckel) < 0.01,
         ha1.get("satz"))
    c = _verbindung(dbA)
    agg1 = HAG.aggregat(c, kapital_eur=K, anteil=float(ein["aggregat_anteil"]),
                        hebelnenner_eur=float(ein["hebelnenner_eur"]))
    c.close()
    fall("H7 danach zaehlt das neue Signal mit seinem Verlust am Stop - und "
         "r(q) nahm nicht mehr als frei war",
         abs(agg1["offen_eur"] - (170.2 + float(z1["verlust_am_stop_eur"]))) < 0.01
         and float(z1["verlust_am_stop_eur"]) <= float(ha1.get("frei_eur") or 0) + 0.01,
         "\n".join("%-8s %-10s %8s EUR  %s" % (p["art"], p["symbol"],
                                              de(p["risiko_eur"], 2), p["grund"])
                   for p in agg1["posten"]))
    hf = e1.get("hebelfuehrung") or {}
    mh = next((m for m in e1.get("mails") or []
               if m.get("seite") == "hebelfuehrung"), None)
    ablegen(mh, "1_hebelfuehrung")
    th = str((mh or {}).get("text") or "")
    fall("H8 Hebelfuehrung: beide Positionen gefuehrt, ZZPLAN mit SEINEM Signal "
         "- HEBEL SENKEN",
         hf.get("offen") == 2 and ("Plan         Signal %s vom" % plan_id) in th
         and "ZZPLAN - Hebel 5,0x LONG" in th and "HEBEL SENKEN" in th,
         "Betreff: %s\n%s" % ((mh or {}).get("betreff"),
                              mit(th, "ZZPLAN", "Plan ", "Nachschuss",
                                  "hoechstens", "Im Deckel")))
    fall("H9 ZZOHNESTOP: KURS FEHLT - Stop unbekannt, angenommen 11,7 %, im "
         "Deckel 70,20 EUR",
         "ZZOHNESTOP" in th and "KURS FEHLT" in th
         and "Stop unbekannt - im Aggregat-Deckel angenommen 11,7 %" in th
         and "Im Deckel    70,20 EUR" in th,
         mit(th, "ZZOHNESTOP", "Stop unbekannt", "Im Deckel    70"))
    e1b = lauf(dbA, [S1], {S1: HEBEL}, AN)
    _ga, _gw = gruende(e1b, "anlass"), gruende(e1b, "wiederholung")
    fall("H10 derselbe Wert gleich danach: kein Signal, kein Modellaufruf",
         not signal_von(e1b, S1) and e1b["_aufrufe"] == 0 and bool(_ga or _gw),
         "Anlass: %r · Cooldown: %r" % (_ga[:2], _gw[:2]))

    # ================================================================ A2
    print("\n--- A2  DER DECKEL IST FAST AUSGESCHOEPFT ---")
    c = _verbindung(dbA)
    _offen = HAG.aggregat(c, kapital_eur=K, anteil=float(ein["aggregat_anteil"]),
                          hebelnenner_eur=float(ein["hebelnenner_eur"]))["offen_eur"]
    _luecke = deckel - _offen - 30.0
    # ⚠️ NUR AUFFUELLEN, WO NOCH MEHR ALS 30 EUR FREI SIND. Beim ersten Lauf
    # (Kapital der Kopie 9.942 EUR, Deckel 298) liess das ONDO-Signal nur noch
    # 3 EUR - die Pruefung erwartete trotzdem 30 und meldete einen Fehler,
    # den es nicht gab.
    _frei_soll = 30.0 if _luecke > 0 else max(0.0, deckel - _offen)
    if _luecke > 0:
        position(c, "ZZVOLL", auf=jetzt - timedelta(hours=2), hebel=3.0,
                 ek=_luecke / (HAG.STOP_ANGENOMMEN * 3.0), kurs=100.0)
    c.close()
    print("  offen %s EUR von %s - ZZVOLL belegt %s EUR, frei bleiben %s EUR"
          % (de(_offen, 2), de(deckel, 2), de(max(0.0, _luecke), 2),
             de(_frei_soll, 2)))
    S2 = e2 = None
    for s in [k for k in kandidaten if k != S1][:6]:
        e = lauf(dbA, [s], {s: HEBEL}, AN)
        if signal_von(e, s):
            S2, e2 = s, e
            break
        print("  %s: kein Signal - Verluste %r" % (s, verluste(e)))
    if not S2:
        fall("D0 ein zweiter Hebelkandidat erreicht die Rechnung", False,
             "kein Kandidat kam durch")
    else:
        z2 = zeile(dbA, signal_von(e2, S2)["id"])
        m2 = mail_zu(e2, S2)
        ablegen(m2, "2_deckel_ausgeschoepft")
        t2 = str((m2 or {}).get("text") or "")
        b2 = betrag(t2)
        ha2 = e2.get("hebel_aggregat") or {}
        print("  Wert %s - Signal %s" % (S2, z2.get("id")))
        fall("D1 der Lauf sieht frei %s EUR" % de(_frei_soll, 2),
             abs(float(ha2.get("frei_eur") or -1) - _frei_soll) < 0.05,
             ha2.get("satz"))
        fall("D2 derselbe Hebelkandidat wird SPOT: instrument 'spot', keine "
             "Hebelspalte, Betrag ohne Hebel",
             z2.get("instrument") == "spot" and z2.get("hebel") is None
             and b2[1] == "kein Hebel",
             "instrument %r · hebel %r · Betrag %s EUR - %s"
             % (z2.get("instrument"), z2.get("hebel"), b2[0], b2[1]))
        fall("D3 die Mail sagt warum",
             "nach dem Aggregat-Deckel unter 2,0x" in t2,
             mit(t2, "Aggregat-Deckel", "traegt", "unter 2,0x"))
        _std2 = sperre_stunden(dbA, S2, z2.get("created_at"), AN)
        fall("D4 und der Cooldown ist der lange Takt fuer Spot (%s h)"
             % de(_soll_s, 1),
             _std2 is not None and abs(_std2 - _soll_s) < 0.02,
             "gesperrt fuer %s Stunden" % (de(_std2, 2) if _std2 else "-"))

    # ================================================================ B
    print("\n--- B  SCHALTER AUS: SPOT UNVERAENDERT · AKKUMULATION ---")
    dbB = vorbereiten("paket_b_schalter_aus.db")
    print("KOPIE B : %s   (Schalter aus)" % dbB)
    if S2:
        eB = lauf(dbB, [S2], {S2: HEBEL}, AUS)
        mB = mail_zu(eB, S2)
        ablegen(mB, "3_vergleich_schalter_aus")
        bB = betrag(str((mB or {}).get("text") or ""))
        fall("N1 Spot unveraendert (N-38): derselbe Trade mit Schalter AUS hat "
             "denselben Betrag",
             bB[0] is not None and bB[0] == b2[0],
             "Schalter an: %s EUR - %s · Schalter aus: %s EUR - %s"
             % (b2[0], b2[1], bB[0], bB[1]))
    kern = next((s for s in ("BTC", "ETH", "SOL") if reihen.get(s)), None)
    if kern:
        eK = lauf(dbB, [kern], {kern: OHNE}, AN)
        z8 = eK.get("zellen") or {}
        print("  Kernwert %s - Zellen %r - Verluste %r"
              % (kern, (z8.get("je_symbol") or {}).get(kern), verluste(eK)))
        fall("K1 der Kernwert laeuft mit zwei Zellen (Akkumulation + taktisch)",
             (z8.get("paare") or 0) > (z8.get("symbole") or 0),
             "paare %r · symbole %r" % (z8.get("paare"), z8.get("symbole")))
        fall("K2 mit der Betriebskonfiguration entsteht kein Akkumulationssignal",
             not any(str((s.get("felder") or {}).get("strategie")) == "akkumulation"
                     for s in eK.get("signale") or []))
        # ⚠️ BEFUND, KEIN HAKEN (erster Lauf 11.09.): die Akkumulationszelle
        # erreicht die Sperre im Betrieb gar nicht. `anlass.beobachte` ist je
        # Symbol und Instrument verschluesselt, nicht je Strategie - die
        # Einstiegszelle laeuft zuerst (`_REIHENFOLGE`) und verbraucht den
        # Faktensatz, die zweite Zelle sieht "0 Blockaenderungen". Dazu kommt
        # der Cooldown je Symbol (2.380-akku-cooldown). Beides gehoert zu
        # Schritt 26. Es wird GEZEIGT, nicht als bestanden gezaehlt.
        _gAn = gruende(eK, "anlass")
        print("  ○  BEFUND (Schritt 26): die Akkumulationszelle faellt an "
              "`anlass`, nicht an der Sperre - %r" % _gAn[:2])
        # ⚠️ DIE SPERRE SELBST IST IM LAUF NICHT ERREICHBAR - und das ist der
        # zweite Teil des Befunds, kein Mangel dieser Simulation. Zweiter
        # Lauf am 11.09. mit Anlass-Sperre aus (nur in der Kopie): beide
        # Zellen fielen an `wiederholung` - der erste Lauf hatte fuer BTC eine
        # Zeile geschrieben. `zellen()` laesst (spot, einstieg) IMMER zu, ein
        # Kernwert hat also stets zwei Zellen, und beide Sperren gelten dem
        # SYMBOL. Die Verdrahtung der Sperre belegt die Suite (Paket B,
        # `lage_gesperrt` an der Entscheiderstufe); im Lauf wird sie erst
        # sichtbar, wenn Schritt 26 Anlass und Cooldown je Zelle fuehrt.
        _ohne_anlass = konfig(True)
        _ohne_anlass["anlass"] = {**dict(_ohne_anlass.get("anlass") or {}),
                                  "aktiv": False}
        eK2 = lauf(dbB, [kern], {kern: OHNE}, _ohne_anlass)
        print("  ○  BEFUND (Schritt 26): auch ohne Anlass-Sperre erreicht die "
              "Akkumulationszelle den Entscheider nicht - Verluste %r, "
              "Entscheider %r" % (verluste(eK2), gruende(eK2, "entscheider")[:2]))

    print("\n" + "=" * 76)
    offen = [n for n, ok in faelle if not ok]
    print("%d Faelle, %d gezeigt, %d offen" % (len(faelle), len(faelle) - len(offen),
                                              len(offen)))
    for n in offen:
        print("  ✖ " + n)
    print("Mails und Charts: %s (paket_b_*)" % ablage)
    print("=" * 76)
    return 1 if offen else 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--symbole", default=None,
                   help="nur diese Symbole (Komma), umgeht die Auswahlstufe")
    p.add_argument("--gruppe", default=None,
                   help="nur diese Gruppe, sonst alle")
    p.add_argument("--nachweis-n14", action="store_true",
                   help="nur den N-14-Nachweis (OI-Sperre), ohne Netzabruf")
    p.add_argument("--nachweis-paket-b", action="store_true",
                   help="Schritt 23: Paket B mit gezielt erzeugtem Hebelgeschaeft")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    global NUR_SYMBOLE
    NUR_SYMBOLE = {s.strip().upper() for s in (a.symbole or "").split(",")
                   if s.strip()}
    if NUR_SYMBOLE:
        # ⚠️ BERICHTIGT 11.09.2026: hier stand "die Auswahlstufe wird
        # umgangen". Umgangen wird nur die VORAUSWAHL dieser Simulation
        # (welche Werte in den Lauf gehen). Die Stufe "beste k" der KETTE
        # greift weiter - im Lauf gegen die NB-Sicherung fielen dort trotz
        # `--symbole` zwei von fuenf heraus, und der alte Text liess das
        # wie einen Fehler aussehen.
        print("NUR DIESE SYMBOLE: %s - umgangen wird die Vorauswahl der "
              "Simulation; die Stufe 'beste k' der Kette greift weiter"
              % ", ".join(sorted(NUR_SYMBOLE)))

    if getattr(a, "nachweis_n14", False):
        return nachweis_n14(a.db)
    if getattr(a, "nachweis_paket_b", False):
        return nachweis_paket_b(a.db)

    from agent import assetklassen as AK
    from agent import rollen_lauf as RL
    from backtest_llm1_historisch import lade_reihen_aus_db

    db = _kopie(a.db)
    print("=" * 76)
    print("SIMULATION DER ABRUFKETTE - Anfang bis Ende")
    print("=" * 76)
    print(f"Quelle : {a.db}")
    print(f"KOPIE  : {db}   <- hierhin wird geschrieben, nie in die Quelle")

    # --- DEN PRODUKTIONS-COOLDOWN IN DER KOPIE ZURUECKDATIEREN -----------
    #
    # NOETIG, SEIT DIE SIMULATION GEGEN DAS NB-BACKUP LAEUFT. Dort stehen
    # echte Signale von heute - der Cooldown sperrt dann JEDES Symbol, und die
    # Simulation prueft nicht mehr die Kette, sondern einen Produktionsstand.
    # Gemessen beim ersten Lauf: hedge und themen_etf kamen mit "0 Aufrufe"
    # durch, weil beide Symbole bis zum 17.08. gesperrt waren.
    #
    # ZURUECKDATIERT, NICHT GELOESCHT: die Zeilen werden fuer Bestand,
    # Trefferbilanz und Ausstiegsfuehrung gebraucht. Nur ihr Alter aendert
    # sich - und zwar NUR in der Kopie.
    with _verbindung(db) as c0:
        for tabelle in ("signals", "hebel_signals"):
            try:
                c0.execute(f"UPDATE {tabelle} SET created_at = "
                           f"datetime(created_at, '-30 days')")
            except sqlite3.Error:
                pass
        c0.commit()
    # ---- SCHRITT 3+4: EIN KERN-ASSET MUSS DABEI SEIN (01.09.2026) -------
    #
    # ⚠️ OHNE DAS BEWEIST DIESE SIMULATION DEN UMBAU NICHT. Der erste Lauf
    # nach Schritt 3 meldete "krypto/spot 5 Symbole, hinein 5" - also fuenf
    # Zellen aus fuenf Symbolen. Kein Asset hatte zwei Zellen, und damit lief
    # der neue Pfad ueberhaupt nicht durch.
    #
    # Die Projektregel dazu ist unmissverstaendlich: *eine Stufe gilt erst
    # als gebaut, wenn `simuliere_kette.py` sie in der fertigen Mail
    # nachweist.* Eine gruene Suite ist kein Wirkungsnachweis.
    #
    # Geschaltet wird ausschliesslich in der KOPIE, wie das Zurueckdatieren
    # darueber - die Produktionsdatenbank wird nicht angefasst.
    _kern = None
    with _verbindung(db) as c0:
        try:
            import database.db as _dbk
            # ⚠️ `price_history_ohlc`, nicht `ohlc_daily` - meine erste
            # Fassung riet den Tabellennamen und bekam einen
            # OperationalError, den der Fehlerfang als "kein Kern-Asset"
            # meldete. Die Simulation sagte daraufhin brav, sie weise den
            # Pfad nicht nach - richtig gemeldet, falsche Ursache.
            _tab = "price_history_ohlc"
            for _s in [r[0] for r in c0.execute(
                    "SELECT DISTINCT symbol FROM %s ORDER BY symbol" % _tab)]:
                if str(_s).upper() in ("BTC", "ETH", "SOL"):
                    _dbk.set_dca_erlaubt(c0, str(_s).upper(), True)
                    _kern = str(_s).upper()
                    break
            c0.commit()
        except Exception as _exc:                            # noqa: BLE001
            print("⚠️ Kern-Asset nicht schaltbar (%s) - der Zellen-Pfad "
                  "wird in diesem Lauf NICHT nachgewiesen" % type(_exc).__name__)
    if _kern:
        print("Kern-Asset %s in der Kopie auf Akkumulation geschaltet - es "
              "bekommt damit ZWEI Zellen (Akkumulation + taktisch)." % _kern)
    else:
        print("⚠️ KEIN Kern-Asset im Bestand - der Zellen-Pfad laeuft in "
              "diesem Lauf nicht durch.")

    print("Cooldown in der Kopie um 30 Tage zurueckdatiert - sonst prueft "
          "die Simulation einen Produktionsstand statt der Kette.")

    # 93 C: EINEN MESSPUNKT IN DIE KOPIE SAMMELN (19.08.2026).
    #
    # Ohne Beobachtung gibt es keine Lebendigkeitszeile, und die Simulation
    # koennte nicht zeigen, dass sie ankommt - "gebaut und nicht verdrahtet"
    # waere unbemerkt geblieben. Zwei Sammelabrufe bei DefiLlama, KEIN
    # CoinGecko-Kontingent, und geschrieben wird ausschliesslich in die
    # KOPIE.
    try:
        import config as _C

        from agent import lebendigkeit as _LB
        with sqlite3.connect(db) as _c1:
            _z = _LB.job(_c1, _C.get_watchlist(), mit_entwickler=False)
        print(f"Lebendigkeit in die Kopie gesammelt: {_z['tvl']}")
    except Exception as _exc:                                # noqa: BLE001
        print(f"Lebendigkeit nicht sammelbar ({type(_exc).__name__}) - die "
              f"Mailzeile fehlt dann, das ist KEIN Kettenfehler")

    reihen = lade_reihen_aus_db(db)
    gesamt = {"gruppen": 0, "signale": 0, "mails": 0, "fehler": [],
              "luecken": [], "gruppen_gelaufen": [],
              "lebendigkeit_gesehen": False, "mehrzellig_gesehen": False,

              "vorfilter_gesehen": False,
              "gruppen_uebersprungen": []}

    for gruppe, instrument, symbole in AK.laeufe():
        if a.gruppe and gruppe != a.gruppe:
            continue
        vorhanden = [s for s in symbole if reihen.get(s)]
        if not vorhanden:
            gesamt["gruppen_uebersprungen"].append(
                f"{gruppe}/{instrument} (keine Kursreihe im Bestand)")
            print(f"\n### {gruppe}/{instrument}: keine Kursreihe - "
                  f"uebersprungen")
            continue
        # Genug Symbole, damit die Attrappe JEDE Aktion einmal durchspielt.
        auswahl = vorhanden[:len(AKTIONEN_JE_INSTRUMENT.get(instrument, ()))]
        # ⚠️ GEZIELT PRUEFBAR (28.08.2026). Ohne `--symbole` nimmt die
        # Simulation die ersten Werte mit Kursreihe - und genau die Stufe
        # "gehoert zu den besten k der Gruppe" warf am 28.08. BTC, ETH und SOL
        # heraus. Damit lief die neue Akkumulations-Lagezeile in KEINER
        # simulierten Mail, obwohl der Lauf grün meldete.
        #
        # Eine Simulation, die den geaenderten Pfad nicht betritt, weist ihn
        # nicht nach - dieselbe Luecke wie bei Rolle G, die vier Wochen als
        # gebaut galt und nie lief.
        if NUR_SYMBOLE:
            gewuenscht = [s for s in vorhanden if s.upper() in NUR_SYMBOLE]
            if gewuenscht:
                auswahl = gewuenscht
        # ⚠️⚠️ DAS KERN-ASSET MUSS IN DEN LAUF (Schritt 3+4, 01.09.2026).
        #
        # Ohne das betritt die Simulation den neuen Pfad nicht: die ersten
        # fuenf Krypto-Werte mit Kursreihe sind alphabetisch AIOZ, AKT,
        # ALGO, APT, ASTER - kein einziger mit `dca_erlaubt`. Der Lauf
        # meldete "5 Symbole, hinein 5", also fuenf Zellen aus fuenf
        # Symbolen, und der Zellen-Pfad lief GAR NICHT.
        #
        # ⚠️ Genau die Luecke, die der Kommentar zwei Absaetze weiter oben
        # schon einmal beschrieben hat: *„Eine Simulation, die den
        # geaenderten Pfad nicht betritt, weist ihn nicht nach."* Sie ist
        # mir trotzdem noch einmal passiert - deshalb steht die Aufnahme
        # jetzt im Code und nicht in der Hoffnung.
        if not NUR_SYMBOLE and _kern and _kern in vorhanden                 and _kern not in auswahl:
            auswahl = [_kern] + list(auswahl)[:-1] if auswahl else [_kern]

        # ⚠️ DEN HEBELSCHALTER IN DER KOPIE EINSCHALTEN.
        #
        # Ohne das prueft dieser Lauf den GROESSTEN Korb gar nicht: seit dem
        # 15.08. ist `get_hebel_pruefung_erlaubt` standardmaessig FALSE, also
        # fallen im Entwicklungsbestand alle Hebel-Symbole an der
        # Auftragsstufe heraus. Der erste Durchgang meldete dafuer brav
        # "0 Fehler" - und hatte 77 % der Produktionsaufrufe nie beruehrt.
        #
        # Das ist genau die Falle, vor der der Kopf dieses Skripts warnt:
        # ein Testlauf, der stillschweigend weniger prueft, als er behauptet.
        # In der KOPIE ist das Umschalten harmlos; die Quelle bleibt
        # unberuehrt.
        if instrument == "hebel":
            with _verbindung(db) as c0:
                for s in auswahl:
                    c0.execute(
                        "INSERT INTO asset_hebel_settings (symbol, "
                        "hebel_pruefung_erlaubt) VALUES (?, 1) "
                        "ON CONFLICT(symbol) DO UPDATE SET "
                        "hebel_pruefung_erlaubt = 1", (s,))
                c0.commit()
        modell = Attrappe(instrument)
        zai = ZaiAttrappe()
        conn = _verbindung(db)
        try:
            e = RL.fuehre_lauf(
                conn=conn, reihen=reihen, symbole=auswahl,
                betriebsart="probe", instrument=instrument,
                strategie="einstieg", client=modell, modell="attrappe",
                config=_echte_config(),
                db=db, zai_client=zai, assetklasse=gruppe, versand=None)
        except Exception as exc:                             # noqa: BLE001
            gesamt["fehler"].append(f"{gruppe}/{instrument}: "
                                    f"{type(exc).__name__}: {exc}")
            print(f"\n### {gruppe}/{instrument}: ABGEBROCHEN - "
                  f"{type(exc).__name__}: {str(exc)[:110]}")
            conn.close()
            continue
        conn.commit()
        conn.close()

        gesamt["gruppen"] += 1
        gesamt["signale"] += len(e.get("signale") or [])
        gesamt["mails"] += len(e.get("mails") or [])
        gesamt["fehler"] += [f"{gruppe}/{instrument}: {f}"
                             for f in (e.get("fehler") or [])]
        print(f"\n### {gruppe}/{instrument}   {len(auswahl)} Symbole, "
              f"{modell.aufrufe} Modellaufrufe, {zai.aufrufe} Rolle-G-Aufrufe")
        # ⚠️ SCHRITT 3+4 NACHWEISEN: der Lauf meldet seine Zellen in
        # `ergebnis["zellen"]["je_symbol"]`. Sobald ein Symbol dort mehr
        # als eine Strategie hat, ist der neue Pfad wirklich gelaufen -
        # nicht nur in der Suite. ⚠️ Meine erste Fassung las das aus
        # einem MAIL-Eintrag; dort steht es nicht, und die Simulation
        # meldete zu Recht "nicht nachgewiesen".
        # ⚠️⚠️ NACHGESCHAERFT (01.09.2026): `je_symbol` fuehrt ALLE Assets
        # der Watchlist, nicht nur die des Laufs. Steht BTC dort mit zwei
        # Strategien, war diese Zeile gruen - AUCH WENN BTC im Lauf gar
        # nicht vorkam. Der Nachweis galt der LISTE, nicht dem LAUF.
        #
        # Aufgefallen an einer Zahl, die nicht zusammenpasste: "krypto/spot
        # 5 Symbole, hinein 5" - fuenf Zellen aus fuenf Symbolen, also kein
        # Mehrzellen-Asset, und trotzdem meldete die Simulation den
        # Nachweis als erbracht.
        #
        # ⚠️ Jetzt zaehlt, was der Lauf WIRKLICH durchlaufen hat: mehr
        # PAARE als Symbole heisst, dass mindestens ein Asset zwei Zellen
        # bekam. Dieselbe Zahl steht im Trichter als `hinein`.
        _z8 = e.get("zellen") or {}
        if (_z8.get("paare") or 0) > (_z8.get("symbole") or 0):
            gesamt["mehrzellig_gesehen"] = True
        # ⚠️ SCHRITT 7 NACHWEISEN - JE LAUF, NICHT JE MAIL.
        #
        # Mein erster Anlauf zaehlte die gefuehrten Positionen INNERHALB der
        # Mail-Schleife. Produziert eine Gruppe keine Mail (der Krypto-Lauf
        # der Simulation liefert 0 Signale), laeuft die Schleife nie - und
        # die Simulation meldete "KEINE Position gefuehrt", obwohl der Lauf
        # welche gefuehrt hatte. Die Meldung war richtig formuliert und zeigte
        # auf die falsche Ursache.
        #
        # ⚠️ Zweite Instanz derselben Falle an einem Tag: die Zellen hatte ich
        # zuerst genauso falsch gezaehlt. Ein Zaehler gehoert dorthin, wo die
        # gezaehlte Sache ENTSTEHT - nicht dorthin, wo sie angezeigt wird.
        # ⚠️ SCHRITT 5 SICHTBAR MACHEN. Ohne diese Zeile laesst sich nicht
        # unterscheiden, ob der Terminmarkt ankommt oder ob die Kopie keine
        # OI-Daten hat - beides sieht im Lauf gleich aus. Dieselbe Lehre wie
        # bei Schritt 7: eine Verdrahtung, die man nicht sehen kann, ist
        # nicht nachgewiesen.
        _tm5 = e.get("terminmarkt") or []
        if _tm5:
            gesamt["terminmarkt_gesehen"] = (
                gesamt.get("terminmarkt_gesehen", 0) + len(_tm5))
        print("    Terminmarkt (Schritt 5): %d von %d Symbolen mit "
              "Faktenlage%s" % (len(_tm5), len(auswahl),
                                (" - " + ", ".join(_tm5[:4])) if _tm5 else ""))
        _pf = e.get("positionsfuehrung") or {}
        print("    Positionsfuehrung: %s gefuehrt, %s im Bestand · "
              "Ausstiege %d · Sammelmail %s"
              % (_pf.get("gefuehrt", "-"), _pf.get("im_bestand", "-"),
                 len(e.get("ausstiege") or []),
                 "ja" if any(m.get("symbol") == "(Sammel)"
                             for m in (e.get("mails") or [])) else "NEIN"))
        if _pf.get("im_bestand"):
            gesamt["positionen_gefuehrt"] = (
                gesamt.get("positionen_gefuehrt", 0) + _pf["im_bestand"])
        print(f"    Signale {len(e.get('signale') or [])}  "
              f"Mails {len(e.get('mails') or [])}  "
              f"Fehler {len(e.get('fehler') or [])}")
        d = e.get("durchlauf")
        if d is not None and hasattr(d, "bericht"):
            bericht = d.bericht()
            zeilen = bericht if isinstance(bericht, list) else str(bericht).splitlines()
            # ⚠️⚠️ NICHT KAPPEN (11.09.2026). Hier stand `zeilen[:16]`.
            # Beim ersten Lauf gegen die NB-Sicherung hatte der Krypto-
            # Trichter viele Begruendungszeilen - die letzten Stufen
            # (Toepfe, Trefferquote) und die Zeile `heraus` fielen aus der
            # ANZEIGE. Es sah aus wie ein stiller Verlust in der Kette:
            # 1 Kandidat nach "Zonen rechenbar", 0 Signale, und keine
            # Stufe nannte den Verlust. Der Trichter ist genau die
            # Tabelle, die sagt, WO die Kette verliert - wer ihr Ende
            # abschneidet, schneidet die Antwort ab.
            for zeile in zeilen:
                print(f"    {zeile}")
        for f in (e.get("fehler") or [])[:6]:
            print(f"    FEHLER: {f[:110]}")

        # --- KOMMT AM ENDE AN, WAS AM ANFANG ENTSTAND? -------------------
        #
        # Der eigentliche Ende-zu-Ende-Test. Ein Lauf ohne Fehler beweist,
        # dass nichts abgestuerzt ist - nicht, dass die Saetze angekommen
        # sind. Genau diese Luecke hat gestern die Mail mit dem falschen ATR
        # ueberlebt: sie war fehlerfrei und zeigte andere Zahlen als der
        # Prompt.
        for eintrag in (e.get("mails") or [])[:99]:
            text = str(eintrag.get("text") or "")
            # ⚠️ DIE FERTIGE MAIL ABLEGEN (11.09.2026). Bis hierher wurde
            # der Text nur im Speicher geprueft und nirgends geschrieben -
            # ob eine Zeile WIRKLICH in der Mail steht, war danach nicht
            # mehr nachsehbar. Der Projektgrundsatz verlangt aber den
            # Nachweis IN DER FERTIGEN MAIL, und der Nutzer will die
            # Mails durchsehen. Geschrieben wird nur ins Temp-Verzeichnis.
            try:
                _ablage = Path(tempfile.gettempdir()) / "simuliere_kette_mails"
                _ablage.mkdir(exist_ok=True)
                (_ablage / ("%s_%s_%s.txt" % (gruppe, instrument,
                    eintrag.get("symbol", "unbekannt")))).write_text(
                        text, encoding="utf-8")
                # DAS BILD GEHOERT ZUR MAIL (Nutzerhinweis 11.09.: "das
                # eMail generiert auch einen Chart - nicht vergessen und
                # pruefen"). Bis dahin wurde es gebaut, aber nie abgelegt -
                # ob es entsteht und was darauf steht, war nicht nachsehbar.
                for _nr, _bild in enumerate(eintrag.get("bilder") or []):
                    if _bild.get("png"):
                        (_ablage / ("%s_%s_%s_%d.png" % (gruppe, instrument,
                            eintrag.get("symbol", "unbekannt"), _nr))
                         ).write_bytes(_bild["png"])
            except OSError:
                pass
            # SAMMELMAILS HABEN KEINE ASSET-BLOECKE. Sie fassen einen Lauf
            # zusammen; ein Verlauf- oder Gegenpruefungsblock waere dort
            # sinnlos. Meine erste Fassung hat sie mitgezaehlt und zwei
            # Luecken gemeldet, die keine sind.
            # ⚠️⚠️ SCHRITT 7 WIRD HIER GEPRUEFT - VOR DEM UEBERSPRINGEN.
            #
            # Die Positionsfuehrung steht ausschliesslich in der SAMMELMAIL,
            # und die wird zwei Zeilen weiter uebersprungen ("Sammelmails
            # haben keine Asset-Bloecke"). Mein erster Haken sass DAHINTER
            # und sah die Sammelmail nie - die Simulation meldete deshalb
            # "keine Mail nennt sie", obwohl die Mail sie nannte.
            #
            # ⚠️ DRITTE INSTANZ DERSELBEN FALLE AN EINEM TAG: der Zaehler
            # stand erst in der Mail-Schleife statt am Lauf, die Zellen
            # ebenso, und jetzt dieser Haken hinter einem `continue`.
            # Merksatz: bevor eine Pruefung "nicht gefunden" meldet, ist zu
            # klaeren, ob sie ueberhaupt HINSEHEN konnte.
            if "WAS SIE HALTEN" in text:
                gesamt["positionen_gesehen"] = True
                if not gesamt.get("_pf_gezeigt"):
                    # ⚠️ DER BELEG, EINMAL JE LAUF: der Abschnitt so, wie er in der
                    # fertigen Mail steht. Eine Pruefung, die nur "gefunden" meldet,
                    # laesst offen, WAS sie gefunden hat.
                    gesamt["_pf_gezeigt"] = True
                    _ab = text[text.index("WAS SIE HALTEN"):]
                    print("")
                    print("    --- SCHRITT 7 IN DER FERTIGEN MAIL ---")
                    for _z in _ab.split(chr(10))[:9]:
                        print("    " + _z)
            # H-4 (11.09.2026): DIE HEBELFUEHRUNG IST EBENFALLS EINE
            # SAMMELMAIL - sie handelt von offenen Positionen, nicht von einem
            # Asset, und traegt deshalb keinen Verlauf-Block. Der erste Lauf
            # meldete genau das als Luecke ("(Hebel): Verlauf-Block fehlt").
            # Gezaehlt wird, dass sie ankommt; der Beleg steht einmal im Lauf.
            if eintrag.get("seite") == "hebelfuehrung":
                if not gesamt.get("hebelfuehrung_gesehen"):
                    print("")
                    print("    --- H-4 HEBELFUEHRUNG IN DER FERTIGEN MAIL ---")
                    for _z in text.split(chr(10))[:16]:
                        print("    " + _z)
                gesamt["hebelfuehrung_gesehen"] = True
                continue
            if str(eintrag.get("symbol") or "").lower().startswith("(sammel"):
                continue
            # ⚠️ JEDE MAIL, NICHT NUR DIE, DIE ICH GEBAUT HABE
            # (Nutzervorgabe 17.08.2026: "fuer alle eMail pruefen bitte").
            # Die Paketpruefung baut EINE Beispielrechnung; hier laufen die
            # echten Mails aller Gruppen durch - Spot wie Hebel, Einstieg
            # wie Bestand.
            # ⚠️ DIE ZWEI GEBUEHRENSAETZE MUESSEN IN JEDER EINSTIEGSMAIL
            # STEHEN (01.09.2026, Nutzervorgabe: *"getrennt fuer 0,3
            # Standard und 1,5 BP"*).
            #
            # Geprueft wird hier und nicht nur in `pruefe_pakete`, weil die
            # Paketpruefung `trefferbilanz.satz()` DIREKT aufruft. Ob die
            # Zeilen auch in der zusammengesetzten Mail ankommen, entscheidet
            # die Naht in `rollen_lauf` - und genau solche Nahtstellen sind
            # im Projekt schon zweimal still ausgefallen (Rolle G, marktrang).
            #
            # ⚠️ NUR BEI EINSTIEGEN. Eine Ausstiegsmail fuehrt keinen neuen
            # Stop und keine neue Position - dort waere die Kostenrechnung
            # eine Zahl ohne Bezug.
            from agent.krypto.backward_tracking import (
                SAETZE_JE_SEITE_MAILTEXT as _saetze_pflicht)
            if "Ihr Stop liegt" in text:
                _fehlende = [s[0] for s in _saetze_pflicht if s[0] not in text]
                if _fehlende:
                    gesamt["luecken"].append(
                        f"{gruppe}/{instrument} {eintrag.get('symbol','?')}: "
                        f"Gebuehrensatz fehlt in der Mail: {_fehlende}")
            _punkt = _englische_zahlen(text)
            if _punkt:
                # ⚠️ DIE ZEILE MITNENNEN, nicht nur die Zahl (11.09.2026).
                # Beim Lauf gegen die NB-Sicherung meldete die Simulation
                # "englische Zahlschreibweise ['11.5']" - und weil der
                # Mailtext nirgends gespeichert wird, war danach nicht mehr
                # feststellbar, WELCHE Zeile ihn traegt. Eine Luecke, die
                # man nicht findet, kann man nicht beheben.
                _wo = [z.strip() for z in text.splitlines()
                       if any(x in _DATUM.sub(" ", z) for x in _punkt)]
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {eintrag.get('symbol', '?')}: "
                    f"englische Zahlschreibweise {_punkt[:4]} - in: "
                    f"{(_wo[0] if _wo else '?')[:110]}")
            # Und die sechs Handelsparameter muessen den Fett-Schwarz-Griff
            # bekommen - geprueft am gerenderten HTML, weil dazwischen die
            # Reihenfolge der Formatregeln liegt.
            _hat = {z.split(" ", 1)[0].rstrip(":")
                    for z in text.splitlines() if z.strip()
                    } & _FORM.HANDELSPARAMETER
            if _hat:
                _html = _FORM.render_detail_html(text)
                _fett = _re.findall(
                    r"font-weight:bold;color:#000000;\">([^< ]+)", _html)
                _fehlt = _hat - {w.rstrip(":") for w in _fett}
                if _fehlt:
                    gesamt["luecken"].append(
                        f"{gruppe}/{instrument} "
                        f"{eintrag.get('symbol', '?')}: nicht fett "
                        f"hervorgehoben {sorted(_fehlt)}")
            # DER TRICHTER GEHOERT IN JEDE MAIL MIT EINSTIEGSZONE (93 A).
            # Wo eine Zone gerechnet wurde, lagen Kurs UND ATR vor - dann
            # gibt es keinen Grund, warum die Spanne fehlen duerfte.
            if "Einstiegszone" in text and "Uebliche Kursbewegung" not in text:
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {eintrag.get('symbol', '?')}: "
                    f"Trichter fehlt trotz Einstiegszone")
            # 93 C: die Lebendigkeitszeile gehoert in jede KRYPTO-Mail zu
            # einem Symbol, zu dem eine Quelle etwas liefert. Wo DefiLlama
            # nichts kennt (LINK etwa ist ein Orakel), fehlt sie zu Recht -
            # deshalb wird nicht je Mail geprueft, sondern ob die Zeile
            # UEBERHAUPT ankommt.
            if gruppe == "krypto" and "Lebendigkeit des Projekts" in text:
                gesamt["lebendigkeit_gesehen"] = True
            # V1: der Vorfilter-Schatten gehoert in JEDE Mail - anders als
            # die Lebendigkeit haengt er an keiner Fremdquelle. Steht er
            # nicht da, ist die Schattenmessung stumm.
            if "Vorfilter H" in text:
                gesamt["vorfilter_gesehen"] = True
            if "Marktstruktur" not in text:
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {eintrag.get('symbol', '?')}: "
                    f"Verlauf-Block fehlt in der Mail")
            # ROLLE G NUR BEI KRYPTO - und das ist kein Zugestaendnis, sondern
            # die Regel R-R3/G5: liegt zu einem Wert keine eigene Grundlage
            # vor, wird NICHT gefragt. Aktien, Rohstoffe und ETF haben keine
            # Terminmarktdaten.
            #
            # Meine erste Fassung verlangte den Abschnitt ueberall und meldete
            # vier Luecken, die Regelkonformitaet waren. Umgekehrt gilt aber
            # auch: bei Krypto MUSS er da sein, und bei den uebrigen darf er
            # NICHT erscheinen - beides wird geprueft.
            # ⚠️ "KRYPTO" REICHT ALS BEDINGUNG NICHT MEHR (17.08.2026).
            # Seit dem Boersenfluss dazugekommen ist, hat JEDES
            # Kryptosymbol Positionierungssaetze - auch eines ganz ohne
            # Terminmarktdaten. Rolle G ueberspringt es dann zu Recht
            # (G5: ueber nichts wird nicht gefragt), und diese Pruefung
            # meldete es als Luecke. AIOZ hat es gezeigt: kein Open
            # Interest, keine Finanzierungsrate, kein Long-Anteil - nur
            # der BTC-weite Fluss, der ueber AIOZ nichts aussagt.
            #
            # GEFRAGT WIRD JETZT NACH SYMBOLSPEZIFISCHEN Daten, also nach
            # derselben Bedingung, die `mindestkriterien.SYMBOLSPEZIFISCH_G`
            # fuehrt. Ein Kriterium, das eine korrekte Entscheidung als
            # Fehler meldet, wird nach dem dritten Mal ignoriert.
            # ⚠️ NACH DER GRUNDLAGE FRAGEN, NICHT NACH DER GRUPPE
            # (17.08.2026). Hier stand `gruppe != "krypto"` - eine
            # Abkuerzung aus der Zeit, als ausser Krypto nichts eine
            # Positionierung hatte. Seit dem 16.08. erfuellen beide
            # Aktien G1 und G2 (Leerverkaeufer + Insider), und die
            # Simulation meldete sie als "urteilt OHNE Grundlage".
            #
            # Ein Kriterium, das eine korrekte Entscheidung als Fehler
            # meldet, wird nach dem dritten Mal ignoriert.
            hat_g = "GEGENPRUEFUNG" in text
            _sym = str(eintrag.get("symbol") or "")
            _grundlage = _hat_eigene_grundlage(conn, _sym, gruppe)
            if _grundlage and not hat_g:
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {_sym}: Rolle G fehlt, obwohl "
                    f"SYMBOLSPEZIFISCHE Positionierungsdaten vorliegen")
            # ⚠️ EINE EINSTELLUNG IST KEINE LUECKE (17.08.2026). Rolle G
            # urteilt bei AIOZ und ASTER allein auf dem BTC-weiten
            # Boersenfluss - G2 ist nicht erfuellt, und `mindestkriterien`
            # MELDET das auch. Gesperrt wird nur, wenn der Nutzer "G" in
            # `mindestkriterien.sperren` eintraegt.
            #
            # Solange er das nicht tut, ist der Zustand gewollt. Ihn als
            # Luecke zu zaehlen hiesse, jeden Lauf rot zu faerben fuer eine
            # Entscheidung, die getroffen wurde.
            if hat_g and not _grundlage:
                from agent import mindestkriterien as _MK9

                if "G" in (_MK9.konfig().get("sperren") or ()):
                    gesamt["luecken"].append(
                        f"{gruppe}/{instrument} {_sym}: Rolle G urteilt "
                        f"OHNE Grundlage, obwohl G gesperrt sein sollte")
                else:
                    gesamt.setdefault("hinweise", []).append(
                        f"{gruppe}/{instrument} {_sym}: Rolle G urteilt auf "
                        f"BTC-weiter Grundlage (G2 offen, nicht gesperrt)")
            # UND DIE KONSISTENZZEILE DARF NICHT ZURUECKKOMMEN.
            if "nennt die Begruendung" in text:
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {eintrag.get('symbol', '?')}: "
                    f"Konsistenzzeile wieder in der Mail - sie wurde am "
                    f"17.08. entfernt")
            if instrument == "hebel" and "Zwangsaufloesung" not in text:
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {eintrag.get('symbol', '?')}: "
                    f"Liquidationsabstand fehlt in der Mail")
        gesamt["gruppen_gelaufen"].append(f"{gruppe}/{instrument}")

        # --- DERSELBE LAUF NOCH EINMAL, MIT AKTIVER ANLASS-SPERRE ---------
        #
        # DER EIGENTLICHE ENDE-ZU-ENDE-BEWEIS. Die Kursreihen sind dieselben,
        # der Faktensatz also bitgleich - genau der Fall, den die Sperre
        # entfernen soll. Kaeme hier auch nur ein Signal heraus, sperrte sie
        # nicht; kaeme im ERSTEN Lauf keines, prueften wir gegen nichts.
        #
        # Die Attrappe wird NEU gebaut: sonst zaehlte sie im Aktionsvokabular
        # weiter und der zweite Lauf bekaeme andere Antworten - der Test
        # wuerde dann die Attrappe messen statt die Sperre.
        modell2 = Attrappe(instrument)
        conn = _verbindung(db)
        try:
            e2 = RL.fuehre_lauf(
                conn=conn, reihen=reihen, symbole=auswahl,
                betriebsart="probe", instrument=instrument,
                strategie="einstieg", client=modell2, modell="attrappe",
                db=db, zai_client=ZaiAttrappe(), assetklasse=gruppe,
                versand=None, config=_echte_config())
            conn.commit()
        finally:
            conn.close()
        n2 = len(e2.get("signale") or [])
        a2 = modell2.aufrufe
        print(f"    zweiter Lauf MIT Sperre: {n2} Signale, "
              f"{a2} Modellaufrufe (vorher {len(e.get('signale') or [])} / "
              f"{modell.aufrufe})")
        if n2:
            gesamt["luecken"].append(
                f"{gruppe}/{instrument}: Sperre wirkungslos - {n2} Signale "
                f"auf identischem Faktensatz")
        if a2 > 1:
            gesamt["luecken"].append(
                f"{gruppe}/{instrument}: Sperre kam ZU SPAET - {a2} "
                f"Modellaufrufe trotz identischer Fakten")

    # --- Was ist in der Datenbank angekommen? -----------------------------
    print("\n" + "=" * 76)
    print("WAS IN DER DATENBANK ANGEKOMMEN IST")
    # 93 C: gesammelt UND angekommen? Beides, sonst ist es halb gebaut.
    # ⚠️ SCHRITT 3+4: hat ein Asset ueberhaupt ZWEI Zellen durchlaufen?
    # Ohne diesen Nachweis ist der Umbau nur in der Suite belegt, nicht im
    # Betrieb - genau die Unterscheidung, die das Projekt seit Rolle G macht.
    # ⚠️ SCHRITT 5: kam der Terminmarkt ueberhaupt irgendwo an?
    if not gesamt.get("terminmarkt_gesehen"):
        gesamt["luecken"].append(
            "Schritt 5: KEIN Symbol bekam Terminmarkt-Fakten - entweder "
            "fehlen die OI-Daten in der Kopie, oder die Einspeisung greift "
            "nicht. Der Anlass kann sich dann nicht am Terminmarkt aendern")

    # ⚠️ SCHRITT 7: gefuehrt, aber nicht gezeigt = die halbe Verdrahtung.
    if gesamt.get("positionen_gefuehrt") and not gesamt.get("positionen_gesehen"):
        gesamt["luecken"].append(
            "Schritt 7: %d Positionen gefuehrt, aber KEINE Mail nennt sie - "
            "die Positionsfuehrung erreicht den Leser nicht"
            % gesamt["positionen_gefuehrt"])
    elif not gesamt.get("positionen_gefuehrt"):
        gesamt["luecken"].append(
            "Schritt 7: in diesem Lauf wurde KEINE Position gefuehrt - der "
            "Nachweis steht aus (kein Bestand in der Kopie, oder keine "
            "Sammelmail, weil keine Ausstiege anfielen)")
    if _kern and not gesamt.get("mehrzellig_gesehen"):
        gesamt["luecken"].append(
            "Schritt 3+4: KEIN Asset lief mit zwei Zellen durch - der "
            "Zellen-Pfad ist in dieser Simulation nicht nachgewiesen "
            "(Kern-Asset war %s)" % _kern)
    if not gesamt["lebendigkeit_gesehen"]:
        gesamt["luecken"].append(
            "Lebendigkeit (93 C): in KEINER Kryptomail angekommen - "
            "gesammelt wurde, angezeigt nicht")
    if not gesamt["vorfilter_gesehen"]:
        gesamt["luecken"].append(
            "Vorfilter H (V1): in KEINER Mail angekommen - die "
            "Schattenmessung laeuft dann ins Leere")
    print("=" * 76)
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    for tabelle, spalte in (("signals", "quelle_kette"),
                            ("anlass_beobachtung", None)):
        try:
            if spalte:
                n = c.execute(f"SELECT COUNT(*) FROM {tabelle} "
                              f"WHERE {spalte}='rollen'").fetchone()[0]
                print(f"  {tabelle:22} {n:>5} Zeilen aus der Rollen-Kette")
                for r in c.execute(
                        "SELECT action, COUNT(*) FROM signals "
                        "WHERE quelle_kette='rollen' GROUP BY 1 ORDER BY 2 DESC"):
                    print(f"      {r[0]:18} {r[1]}")
            else:
                n = c.execute(f"SELECT COUNT(*) FROM {tabelle}").fetchone()[0]
                print(f"  {tabelle:22} {n:>5} Zeilen")
        except sqlite3.Error as exc:
            print(f"  {tabelle:22} nicht lesbar: {exc}")
    c.close()

    # --- ABDECKUNG: was wurde NICHT geprueft? ----------------------------
    #
    # Diese Zeilen sind wichtiger als die Fehlerzahl. Ein Lauf, der die
    # Haelfte der Koerbe ueberspringt und "0 Fehler" meldet, ist die
    # gefaehrlichste Sorte gruen - und genau das war der erste Durchgang:
    # Hebel, Rohstoffe und Absicherung liefen nie, gemeldet wurde "in Ordnung".
    print("\n" + "=" * 76)
    print("ABDECKUNG")
    print("=" * 76)
    for g in gesamt["gruppen_gelaufen"]:
        print(f"  gelaufen       {g}")
    for g in gesamt["gruppen_uebersprungen"]:
        print(f"  UEBERSPRUNGEN  {g}")
    if gesamt["luecken"]:
        print("\nWAS IN DER MAIL NICHT ANKAM:")
        for z in gesamt["luecken"]:
            print(f"  {z}")

    # BEKANNT UND NICHT GESPERRT - sichtbar, aber nicht als Fehler.
    if gesamt.get("hinweise"):
        print("")
        print("BEKANNTE ZUSTAENDE (gemeldet, nicht gesperrt):")
        for z in sorted(set(gesamt["hinweise"])):
            print(f"  {z}")

    print("\n" + "=" * 76)
    print(f"{gesamt['gruppen']} Gruppen durchlaufen, {gesamt['signale']} "
          f"Signale, {gesamt['mails']} Mails, {len(gesamt['fehler'])} Fehler, "
          f"{len(gesamt['luecken'])} Luecken")
    if gesamt["fehler"]:
        print("\nALLE FEHLER:")
        for f in gesamt["fehler"]:
            print(f"  {f[:140]}")
    print("=" * 76)
    return 1 if (gesamt["fehler"] or gesamt["luecken"]
                 or not gesamt["gruppen"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
