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


def _englische_zahlen(text: str) -> list[str]:
    """Zahlen in englischer Schreibweise. Genau drei Ziffern nach dem Punkt
    gelten als Tausendergruppe (1.234,5) und zaehlen nicht."""
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
        if self.instrument == "hebel":
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


def _kopie(quelle: str) -> str:
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
    ziel = Path(tempfile.gettempdir()) / "simuliere_kette.db"
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--gruppe", default=None,
                   help="nur diese Gruppe, sonst alle")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    print("Cooldown in der Kopie um 30 Tage zurueckdatiert - sonst prueft "
          "die Simulation einen Produktionsstand statt der Kette.")

    reihen = lade_reihen_aus_db(db)
    gesamt = {"gruppen": 0, "signale": 0, "mails": 0, "fehler": [],
              "luecken": [], "gruppen_gelaufen": [],
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
        print(f"    Signale {len(e.get('signale') or [])}  "
              f"Mails {len(e.get('mails') or [])}  "
              f"Fehler {len(e.get('fehler') or [])}")
        d = e.get("durchlauf")
        if d is not None and hasattr(d, "bericht"):
            bericht = d.bericht()
            zeilen = bericht if isinstance(bericht, list) else str(bericht).splitlines()
            for zeile in zeilen[:16]:
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
            # SAMMELMAILS HABEN KEINE ASSET-BLOECKE. Sie fassen einen Lauf
            # zusammen; ein Verlauf- oder Gegenpruefungsblock waere dort
            # sinnlos. Meine erste Fassung hat sie mitgezaehlt und zwei
            # Luecken gemeldet, die keine sind.
            if str(eintrag.get("symbol") or "").lower().startswith("(sammel"):
                continue
            # ⚠️ JEDE MAIL, NICHT NUR DIE, DIE ICH GEBAUT HABE
            # (Nutzervorgabe 17.08.2026: "fuer alle eMail pruefen bitte").
            # Die Paketpruefung baut EINE Beispielrechnung; hier laufen die
            # echten Mails aller Gruppen durch - Spot wie Hebel, Einstieg
            # wie Bestand.
            _punkt = _englische_zahlen(text)
            if _punkt:
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {eintrag.get('symbol', '?')}: "
                    f"englische Zahlschreibweise {_punkt[:4]}")
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
                versand=None, config={"anlass": {"aktiv": True}})
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
