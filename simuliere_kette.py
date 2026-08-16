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
import json
import shutil
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
    """Die Datenbank in den Scratchpad kopieren - MIT den WAL-Dateien.

    Ohne sie fehlt der juengste, noch nicht eingecheckte Stand, und die Kopie
    sieht aelter aus als das Original. Dass WAL-Dateien im Projekt schon
    einmal versehentlich eingecheckt wurden, macht sie nicht unwichtig."""
    ziel = Path(tempfile.gettempdir()) / "simuliere_kette.db"
    for endung in ("", "-wal", "-shm"):
        q = Path(str(quelle) + endung)
        if q.exists():
            shutil.copy2(q, str(ziel) + endung)
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
            hat_g = "GEGENPRUEFUNG" in text
            if gruppe == "krypto" and not hat_g:
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {eintrag.get('symbol', '?')}: "
                    f"Rolle G fehlt, obwohl Positionierungsdaten vorliegen")
            if gruppe != "krypto" and hat_g:
                gesamt["luecken"].append(
                    f"{gruppe}/{instrument} {eintrag.get('symbol', '?')}: "
                    f"Rolle G urteilt OHNE Grundlage (R-R3/G5)")
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
