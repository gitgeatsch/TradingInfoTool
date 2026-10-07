"""N4 - Rueckspiel des LLM-Pruefblocks (Trader 0.1e) auf der Entwicklungsmenge (Voranalyse_Schritt7 §23; Nutzer 05.10.2026:
*N4-1 nur Kern, N4-2 Ja - bauen, pruefen und gegenpruefen. Wenn die Messung abbricht oder der Rechner neu startet, muss alles wieder
funktionieren und es darf nichts verloren gehen*).

    python Basisinfos/Rechenkern_02_10/n4_rueckspiel.py lauf            # startet oder setzt fort; endet, wenn fertig oder Kontingent leer
    python Basisinfos/Rechenkern_02_10/n4_rueckspiel.py stand           # Fortschritt, Kontingent, Fehler - OHNE Trennzahlen (kein Zwischenblick)
    python Basisinfos/Rechenkern_02_10/n4_rueckspiel.py lauf --platzhalter zufall|orakel   # Probelauf ohne Gemini (Pruefung)

NACH EINEM NEUSTART DES RECHNERS: Doppelklick auf `n4_start.cmd` (Nutzer 05.10.: keine Windows-Aufgabe). Stand: `n4_stand.cmd`.

WIEDERANLAUF (die Kernforderung):
  - Ablage `data/_n4/n4_ablage.db` (nicht im Temp-Ordner, nicht die Standard-DB), SQLite mit synchronous=FULL.
  - JEDE Stimme wird sofort geschrieben (eigene Transaktion). Ein Abbruch verliert hoechstens den einen Aufruf, der gerade lief;
    er wird beim Fortsetzen wiederholt. Doppelte gibt es nicht (Primaerschluessel teil/pos/stimme).
  - Die EINGABEN werden beim ersten Start eingefroren (Tabelle eingabe). Das Fortsetzen nimmt genau diese, auch wenn sich Daten aendern.
  - Die FASSUNG (Prompt, Bausteine, Modell, Temperatur, Stimmen) wird als Pruefsumme festgehalten; weicht sie ab, verweigert der Laeufer.
  - Sperre ueber einen HERZSCHLAG in der Ablage: ein zweiter Laeufer startet nicht; ist der Herzschlag aelter als 10 min, gilt der
    alte Laeufer als tot (Absturz, Neustart des Rechners) und wird uebernommen.
  - Kontingent je SCHLUESSEL und Pazifik-Tag in der Ablage gezaehlt (vor dem Aufruf gebucht). Ist alles leer, wartet der Laeufer bis
    zum naechsten Pazifik-Tag (oder endet mit --kein-warten).

ABLAUF (vorab, §23): K_a Raten (50 Anker, 1 Aufruf) -> T Trader (Anker 0-99) -> K_b benannt (Anker 0-99) -> Entscheid K (P2b) ->
T (100-999) mit ZWISCHENENTSCHEIDEN nach 250/500/750 -> R_w Wiederholung und R_v vertauschte Reihenfolge (je Anker 0-99).
Schluessel: GEMINI_API_KEY_2 (Deckel 480/Tag), GEMINI_API_KEY (Deckel 300/Tag; der NB-Pruefblock braucht hoechstens 150).
Die Werte der Schluessel werden nie ausgegeben.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sqlite3
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)
os.chdir(PROJ)

ANKER_DATEI = os.path.join(HIER, "n4_anker_entwicklung.csv")
BEST_DATEI = os.path.join(HIER, "n4_anker_bestaetigung.csv")
BELEG = os.path.join(HIER, "n4_anker_beleg.txt")
ABLAGE_VORGABE = os.path.join(PROJ, "data", "_n4", "n4_ablage.db")
B0 = datetime(2020, 1, 1, tzinfo=timezone.utc)
SAAT = 20261005
STIMMEN = 5
N_KA, N_KB, N_R = 50, 100, 100
BLICKE = (250, 500, 750)
DECKEL = {2: int(os.environ.get("N4_DECKEL_2", "480")), 1: int(os.environ.get("N4_DECKEL_1", "300"))}
REIHENFOLGE_SCHLUESSEL = (2, 1)
HERZSCHLAG_TOT_S = int(os.environ.get("N4_HERZ_TOT", "600"))   # Pruefung setzt ihn kurz
RATEN_PROMPT = ("Du bekommst die Kurs- und Volumenlage eines Werts ohne Namen und ohne Datum. Rate trotzdem: um welchen Wert (Kuerzel) "
                "und um welchen Monat und welches Jahr handelt es sich? Antworte AUSSCHLIESSLICH mit JSON: "
                '{"kuerzel": "<Kuerzel>", "monat": "<MM>", "jahr": "<JJJJ>"}')


# ---------------------------------------------------------------------------- Anker
def _sha(p: str) -> str:
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def lade_anker(datei: str = ANKER_DATEI):
    """Die eingefrorene Entwicklungsmenge - nur, wenn die Pruefsumme dem Beleg entspricht und KEIN Anker der Bestaetigungsmenge darin ist."""
    import pandas as pd
    soll = None
    for z in open(BELEG, encoding="utf-8"):
        if z.startswith(os.path.basename(datei)) and "SHA-256" in z:
            soll = z.split("SHA-256")[1].strip().split()[0]
    if datei == ANKER_DATEI and _sha(datei) != soll:
        raise SystemExit("Anker-Datei weicht vom Beleg ab (SHA-256) - Abbruch")
    a = pd.read_csv(datei, sep=";", dtype={"symbol": str})
    best = {(r["symbol"], int(r["std"])) for r in csv.DictReader(open(BEST_DATEI, encoding="utf-8"), delimiter=";")}
    if any((s, int(t)) in best for s, t in zip(a["symbol"], a["std"])):
        raise SystemExit("Anker der BESTAETIGUNGSMENGE in der Liste - Abbruch (die Bestaetigung bleibt unberuehrt)")
    return a


def reihenfolge(a):
    """Feste Reihenfolge: je Jahr gemischt (Saat), dann abwechselnd 2025/2026 - jeder Zwischenblick sieht beide Jahre gleich stark."""
    import pandas as pd
    rng = random.Random(SAAT)
    toepfe = {}
    for j in sorted(a["jahr"].unique()):
        idx = list(a.index[a["jahr"] == j])
        rng.shuffle(idx)
        toepfe[j] = idx
    out = []
    while any(toepfe.values()):
        for j in sorted(toepfe):
            if toepfe[j]:
                out.append(toepfe[j].pop(0))
    return a.loc[out].reset_index(drop=True)


def anker_dict(z) -> dict:
    sig = B0 + timedelta(hours=int(z["std"]))
    return dict(symbol=z["symbol"], bitpanda=None, signalstunde=sig.strftime("%Y-%m-%d %H:%M"),
                einstieg=(sig + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"), ausstieg=(sig + timedelta(hours=25)).strftime("%Y-%m-%d %H:%M"),
                stufe=int(z["stufe"]), kurs=None)


# ---------------------------------------------------------------------------- Ablage
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS eingabe (pos INTEGER PRIMARY KEY, symbol TEXT, std INTEGER, jahr INTEGER, signalstunde TEXT, stufe INTEGER,
                                    eingabe TEXT, summe TEXT);
CREATE TABLE IF NOT EXISTS stimme (teil TEXT, pos INTEGER, stimme INTEGER, schluessel INTEGER, modell TEXT, urteil TEXT, gueltig INTEGER,
                                   roh TEXT, fehler TEXT, sekunden REAL, zeit TEXT, PRIMARY KEY (teil, pos, stimme));
CREATE TABLE IF NOT EXISTS kontingent (schluessel INTEGER, tag TEXT, n INTEGER, erschoepft INTEGER DEFAULT 0, PRIMARY KEY (schluessel, tag));
CREATE TABLE IF NOT EXISTS entscheid (name TEXT PRIMARY KEY, zeit TEXT, ergebnis TEXT, kennzahlen TEXT);
CREATE TABLE IF NOT EXISTS herz (id INTEGER PRIMARY KEY CHECK (id = 1), pid INTEGER, zeit REAL, start TEXT);
CREATE TABLE IF NOT EXISTS ereignis (zeit TEXT, art TEXT, text TEXT);
"""


def oeffne(pfad: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    c = sqlite3.connect(pfad, timeout=60)
    c.execute("PRAGMA journal_mode=DELETE")
    c.execute("PRAGMA synchronous=FULL")
    c.executescript(SCHEMA)
    return c


def jetzt_txt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


LOG = {"pfad": None}


def ereignis(c, art: str, text: str) -> None:
    c.execute("INSERT INTO ereignis VALUES (?,?,?)", (jetzt_txt(), art, text[:2000]))
    c.commit()
    zeile = "%s %-10s %s" % (jetzt_txt(), art, text)
    if sys.stdout is not None:                                 # unter pythonw (Windows-Aufgabe) gibt es keine Konsole
        print(zeile, flush=True)
    if LOG["pfad"]:
        try:
            with open(LOG["pfad"], "a", encoding="utf-8") as f:
                f.write(zeile + "\n")
        except OSError:
            pass


def pazifik_tag() -> str:
    if os.environ.get("N4_TAG"):                              # nur fuer die Pruefung
        return os.environ["N4_TAG"]
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")


def sekunden_bis_neuer_tag() -> float:
    from zoneinfo import ZoneInfo
    jetzt = datetime.now(ZoneInfo("America/Los_Angeles"))
    morgen = (jetzt + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    return (morgen - jetzt).total_seconds()


# ---------------------------------------------------------------------------- Fassung
def fassung(K: dict) -> str:
    import agent.regel0_llm as L
    teile = [L.system_fuer("trader", K), json.dumps(K["rollen"]["trader"].get("bausteine") or [], ensure_ascii=False), K["modell"],
             str(K.get("temperatur") or 0.0), str(STIMMEN), RATEN_PROMPT]
    return hashlib.sha256("\x1f".join(teile).encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------- Vorflug: Eingaben einfrieren
def friere_eingaben(c, K) -> int:
    import agent.regel0_llm as L
    if c.execute("SELECT 1 FROM meta WHERE k='eingaben_fertig'").fetchone():
        return c.execute("SELECT COUNT(*) FROM eingabe").fetchone()[0]
    # SCHRITTWEISE (05.10., Pruefung P3): das Einfrieren dauert ~80 s; ein Abbruch darin soll nur Sekunden kosten, nicht alles.
    # Je 25 Anker ein Commit; beim Fortsetzen werden nur die fehlenden gerechnet. Erst 'eingaben_fertig' gibt den Plan frei.
    schon = {r[0] for r in c.execute("SELECT pos FROM eingabe")}
    a = reihenfolge(lade_anker())
    zeilen, fehlt = [], []
    for pos, z in a.iterrows():
        if pos in schon:
            continue
        r = anker_dict(z)
        e = L.trader_eingabe(r, "data", K)
        if e is not None and L.anonym_verletzt(e, r):
            fehlt.append((pos, z["symbol"], "nicht anonym"))
            continue
        # Zu junge Assets (unter 30 Tageskerzen): im BETRIEB bekommt der Trader keine Eingabe ("fehlt"). N4 bildet das nach -
        # kein Aufruf, die Zeile bleibt mit leerer Eingabe stehen und zaehlt in der Auswertung als *fehlt* (Vorflug 05.10.: 3 Anker).
        t = json.dumps(e, ensure_ascii=False, sort_keys=True) if e is not None else None
        zeilen.append((pos, z["symbol"], int(z["std"]), int(z["jahr"]), r["signalstunde"], int(z["stufe"]), t,
                       hashlib.sha256(t.encode("utf-8")).hexdigest()[:12] if t else None))
        if len(zeilen) >= 25:
            c.executemany("INSERT OR IGNORE INTO eingabe VALUES (?,?,?,?,?,?,?,?)", zeilen); c.commit(); zeilen = []
    if fehlt:
        raise SystemExit("Vorflug: %d Anker NICHT ANONYM %s - Abbruch" % (len(fehlt), fehlt[:5]))
    c.executemany("INSERT OR IGNORE INTO eingabe VALUES (?,?,?,?,?,?,?,?)", zeilen)
    n = c.execute("SELECT COUNT(*) FROM eingabe").fetchone()[0]
    if n != len(a):
        raise SystemExit("Einfrieren unvollstaendig: %d von %d" % (n, len(a)))
    c.execute("INSERT OR REPLACE INTO meta VALUES ('eingaben_fertig', ?)", (jetzt_txt(),))
    c.commit()
    return n


def variante(teil: str, e: dict, zeile) -> dict:
    if teil == "K_b":                                         # benannt (Kontaminationsprobe b)
        return dict(e, wert=zeile["symbol"], zeitpunkt=zeile["signalstunde"])
    if teil == "R_v":                                         # vertauschte Reihenfolge der Saetze
        return dict(e, lage_des_werts=list(reversed(e["lage_des_werts"])))
    return e


# ---------------------------------------------------------------------------- Plan
def plan(c) -> list:
    """Die Aufgaben in fester Reihenfolge: (teil, pos, stimmen). Was erledigt ist, wird uebersprungen."""
    n = c.execute("SELECT COUNT(*) FROM eingabe").fetchone()[0]
    p = [("K_a", i, 1) for i in range(min(N_KA, n))]
    p += [("T", i, STIMMEN) for i in range(min(100, n))]
    p += [("K_b", i, STIMMEN) for i in range(min(N_KB, n))]
    p += [("ENTSCHEID_K", None, 0)]
    for i in range(100, n):
        if i in BLICKE:
            p.append(("ENTSCHEID_T%d" % i, None, 0))
        p.append(("T", i, STIMMEN))
    p += [("R_w", i, STIMMEN) for i in range(min(N_R, n))]
    p += [("R_v", i, STIMMEN) for i in range(min(N_R, n))]
    return p


def ohne_eingabe(c) -> set:
    return {r[0] for r in c.execute("SELECT pos FROM eingabe WHERE eingabe IS NULL")}


def erledigt(c, teil, pos) -> int:
    return c.execute("SELECT COUNT(*) FROM stimme WHERE teil=? AND pos=?", (teil, pos)).fetchone()[0]


# ---------------------------------------------------------------------------- Clients
class Platzhalter:
    """Probe-Client ohne Gemini: 'zufall' (Urteile unabhaengig vom Ausgang) oder 'orakel' (Urteil folgt dem echten 24-h-Ertrag).
    Fehler auf Wunsch: N4_PH_NETZ (Anteil Netzfehler), N4_PH_UNGUELTIG (Anteil Formfehler), N4_PH_LEER_NACH (Tagesbudget je Schluessel)."""

    def __init__(self, modus: str, schluessel: int):
        self.modus, self.schluessel = modus, schluessel
        self.rng = random.Random(SAAT + schluessel + int(time.time() * 1000) % 100000)
        self.spot = None
        self.anker = None

    def chat(self, messages, model=None, temperature=0.0, response_format=None):
        from api.gemini import TageskontingentErschoepft
        import requests
        leer = int(os.environ.get("N4_PH_LEER_NACH", "0") or 0)
        if leer and _ph_zaehler(self.schluessel) >= leer:
            raise TageskontingentErschoepft("Platzhalter: Tagesbudget leer", model)
        _ph_zaehler(self.schluessel, +1)
        if os.environ.get("N4_PH_PAUSE"):
            time.sleep(float(os.environ["N4_PH_PAUSE"]))
        if self.rng.random() < float(os.environ.get("N4_PH_NETZ", "0") or 0):
            raise requests.ConnectionError("Platzhalter: Netzfehler")
        if self.rng.random() < float(os.environ.get("N4_PH_UNGUELTIG", "0") or 0):
            return "das ist kein JSON"
        if "Rate trotzdem" in messages[0]["content"]:
            return json.dumps({"kuerzel": "XYZ", "monat": "%02d" % self.rng.randint(1, 12), "jahr": str(self.rng.choice((2023, 2024)))})
        if self.modus == "orakel" and self.anker is not None:
            r = self.spot.get(self.anker, 0.0)
            u = "stuetzt" if r > 0.03 else ("spricht_dagegen" if r < 0.0 else "neutral")
            if self.rng.random() < 0.2:
                u = self.rng.choice(("stuetzt", "neutral", "spricht_dagegen"))
        else:
            u = self.rng.choices(("stuetzt", "neutral", "spricht_dagegen"), (0.1, 0.45, 0.45))[0]
        return json.dumps({"urteil": u, "begruendung": "Platzhalter", "gegengrund": "Platzhalter",
                           "belege": [{"fakt": "Platzhalter", "richtung": "neutral"}]})


_PH = {}


def _ph_zaehler(s, plus=0):
    tag = pazifik_tag()
    _PH[(s, tag)] = _PH.get((s, tag), 0) + plus
    return _PH[(s, tag)]


def baue_clients(platzhalter: str | None) -> dict:
    if platzhalter:
        return {s: Platzhalter(platzhalter, s) for s in REIHENFOLGE_SCHLUESSEL}
    from dotenv import dotenv_values
    from api.gemini import GeminiClient
    v = dotenv_values(os.path.join(PROJ, ".env"))
    out = {}
    for s, name in ((2, "GEMINI_API_KEY_2"), (1, "GEMINI_API_KEY")):
        if v.get(name):
            out[s] = GeminiClient(api_key=v[name], tagesbudget=10 ** 6, reserve=0)   # gezaehlt wird in der N4-Ablage je Schluessel
    if 2 not in out:
        raise SystemExit("GEMINI_API_KEY_2 fehlt in .env - Abbruch")
    return out


# ---------------------------------------------------------------------------- Kontingent
def frei(c, s) -> int:
    z = c.execute("SELECT n, erschoepft FROM kontingent WHERE schluessel=? AND tag=?", (s, pazifik_tag())).fetchone()
    if z and z[1]:
        return 0
    return max(0, DECKEL[s] - (z[0] if z else 0))


def buche(c, s) -> None:
    c.execute("INSERT INTO kontingent (schluessel, tag, n) VALUES (?,?,1) ON CONFLICT(schluessel, tag) DO UPDATE SET n=n+1",
              (s, pazifik_tag()))
    c.commit()


def erschoepft(c, s) -> None:
    c.execute("INSERT INTO kontingent (schluessel, tag, n, erschoepft) VALUES (?,?,0,1) ON CONFLICT(schluessel, tag) DO UPDATE SET erschoepft=1",
              (s, pazifik_tag()))
    c.commit()


# ---------------------------------------------------------------------------- Herzschlag-Sperre
def nimm_sperre(c) -> bool:
    z = c.execute("SELECT pid, zeit FROM herz WHERE id=1").fetchone()
    if z and z[0] != os.getpid() and time.time() - z[1] < HERZSCHLAG_TOT_S:
        return False
    c.execute("INSERT OR REPLACE INTO herz VALUES (1, ?, ?, ?)", (os.getpid(), time.time(), jetzt_txt()))
    c.commit()
    return True


def herzschlag(c) -> None:
    c.execute("UPDATE herz SET zeit=? WHERE id=1 AND pid=?", (time.time(), os.getpid()))
    c.commit()


def gib_sperre(c) -> None:
    c.execute("DELETE FROM herz WHERE id=1 AND pid=?", (os.getpid(),))
    c.commit()


# ---------------------------------------------------------------------------- ein Aufruf
def eine_stimme(c, clients, K, teil, pos, nr, zeile, spot) -> str:
    """'ok' | 'leer' (kein Kontingent mehr heute) | 'fehler' (Netz/Server, nicht gespeichert, wird wiederholt)."""
    import agent.regel0_llm as L
    import requests
    from api.gemini import TageskontingentErschoepft
    e = json.loads(zeile["eingabe"])
    for s in REIHENFOLGE_SCHLUESSEL:
        if s not in clients or frei(c, s) <= 0:
            continue
        cl = clients[s]
        if isinstance(cl, Platzhalter):
            cl.spot, cl.anker = spot, (zeile["symbol"], zeile["std"])
        buche(c, s)                                            # VOR dem Aufruf: ein Abbruch kostet hoechstens Kontingent, nie Daten
        t0 = time.time()
        try:
            if teil == "K_a":
                roh = L.frage(cl, K["modell"], RATEN_PROMPT, e, 0.0)
                urteil, gueltig, fehler = None, 1, None
            else:
                roh = L.frage(cl, K["modell"], L.system_fuer("trader", K), variante(teil, e, zeile), float(K.get("temperatur") or 0.0))
                try:
                    urteil, gueltig, fehler = L.validiere("trader", roh)["urteil"], 1, None
                except L.AntwortUngueltig as exc:
                    urteil, gueltig, fehler = None, 0, "ungueltig: %s" % str(exc)[:200]
        except L.AntwortUngueltig as exc:                       # keine JSON-Struktur - zaehlt wie im Betrieb als ungueltige Stimme
            roh, urteil, gueltig, fehler = None, None, 0, "ungueltig: %s" % str(exc)[:200]
        except TageskontingentErschoepft:
            erschoepft(c, s)
            ereignis(c, "KONTINGENT", "Schluessel %d heute erschoepft (Pazifik-Tag %s)" % (s, pazifik_tag()))
            continue
        except (requests.RequestException, OSError, ValueError) as exc:
            if "429" in str(exc):
                ereignis(c, "DROSSEL", "Schluessel %d: %s" % (s, str(exc)[:160]))
            else:
                ereignis(c, "FEHLER", "Schluessel %d %s %s/%d: %s" % (s, teil, pos, nr, str(exc)[:200]))
            return "fehler"
        c.execute("INSERT OR IGNORE INTO stimme VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (teil, pos, nr, s, K["modell"], urteil, gueltig, json.dumps(roh, ensure_ascii=False)[:4000] if roh is not None else None,
                   fehler, round(time.time() - t0, 2), jetzt_txt()))
        c.commit()
        return "ok"
    return "leer"


# ---------------------------------------------------------------------------- Lauf
def lauf(ablage: str, platzhalter: str | None, kein_warten: bool, max_aufrufe: int | None) -> int:
    import agent.regel0_llm as L
    import database.db as db
    from pathlib import Path
    db.DB_PATH = Path(os.path.dirname(ablage)) / "client_zaehler.db"   # der Gemini-Client schreibt hierhin, NIE in die Standard-DB
    os.makedirs(os.path.dirname(ablage), exist_ok=True)
    cz = sqlite3.connect(db.DB_PATH); cz.row_factory = sqlite3.Row; db.init_db(cz); cz.close()
    std = os.path.join(PROJ, "data", "tradinginfotool.db")
    std_vorher = os.path.getmtime(std) if os.path.exists(std) else None
    LOG["pfad"] = os.path.join(os.path.dirname(ablage), "n4_lauf.log")
    c = oeffne(ablage)
    ende = c.execute("SELECT v FROM meta WHERE k='ende'").fetchone()
    if ende:                                                   # fertig oder nach P2b beendet: still beenden (Aufgabe alle 15 min)
        print("N4 ist beendet (%s) - nichts zu tun." % ende[0])
        c.close()
        return 0
    if not nimm_sperre(c):
        print("Ein anderer Laeufer ist aktiv (Herzschlag juenger als %d s) - nichts zu tun." % HERZSCHLAG_TOT_S)
        return 0
    try:
        # 07.10.2026: der Betrieb ist auf Fassung 0.2 (regel0_llm.yaml); N4 bleibt auf der EINGEFRORENEN 0.1e (Fingerabdruck)
        K = L.lade(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "regel0_llm_0_1e_n4.yaml"))
        K = dict(K, stimmen=STIMMEN)
        f = fassung(K)
        alt = c.execute("SELECT v FROM meta WHERE k='fassung'").fetchone()
        if alt and alt[0] != f:
            raise SystemExit("FASSUNG GEAENDERT (%s statt %s) - eine geaenderte Fassung ist ein NEUER Versuch in einer neuen Ablage" % (f, alt[0]))
        if not alt:
            c.executemany("INSERT INTO meta VALUES (?,?)", [("fassung", f), ("anker_sha", _sha(ANKER_DATEI)), ("start", jetzt_txt()),
                                                            ("modell", K["modell"]), ("platzhalter", platzhalter or "nein")])
            c.commit()
        ph = c.execute("SELECT v FROM meta WHERE k='platzhalter'").fetchone()[0]
        if (ph != "nein") != bool(platzhalter):
            raise SystemExit("Ablage gehoert zu einem %s-Lauf - nicht mischen" % ("Platzhalter" if ph != "nein" else "echten"))
        n = friere_eingaben(c, K)
        ereignis(c, "START", "pid %d · Fassung %s · %d Anker eingefroren · %s" % (os.getpid(), f, n, "PLATZHALTER " + platzhalter if platzhalter else "Gemini"))
        clients = baue_clients(platzhalter)
        import pandas as pd
        spot = {(r.symbol, int(r.std)): float(r.spot) for r in pd.read_csv("data/_vergleich/b0_spur_bestand.csv", sep=";").itertuples()}
        zeilen = {r[0]: dict(zip(("pos", "symbol", "std", "jahr", "signalstunde", "stufe", "eingabe", "summe"), r))
                  for r in c.execute("SELECT * FROM eingabe")}
        import n4_auswertung as A
        gesamt, fehler_folge = 0, 0
        leer_e = ohne_eingabe(c)
        if leer_e:
            ereignis(c, "HINWEIS", "%d Anker ohne Eingabe (zu junge Assets) - wie im Betrieb *fehlt*, kein Aufruf: %s" % (
                len(leer_e), ", ".join(zeilen[p_]["symbol"] for p_ in sorted(leer_e))))
        for teil, pos, k in plan(c):
            if pos in leer_e:
                continue
            if teil.startswith("ENTSCHEID_T") and c.execute("SELECT 1 FROM meta WHERE k='t_gestoppt'").fetchone():
                continue                                       # T ist schon beendet: spaetere Blicke entfallen
            if teil.startswith("ENTSCHEID"):
                if c.execute("SELECT 1 FROM entscheid WHERE name=?", (teil,)).fetchone():
                    e = c.execute("SELECT ergebnis FROM entscheid WHERE name=?", (teil,)).fetchone()[0]
                else:
                    e = A.entscheide(c, teil)
                    c.execute("INSERT INTO entscheid VALUES (?,?,?,?)", (teil, jetzt_txt(), e["ergebnis"], json.dumps(e.get("kennzahlen"))))
                    c.commit()
                    e = e["ergebnis"]
                    ereignis(c, "ENTSCHEID", "%s: %s" % (teil, e))
                if e.startswith("STOP"):
                    if teil.startswith("ENTSCHEID_T") and not c.execute("SELECT 1 FROM meta WHERE k='t_gestoppt'").fetchone():
                        c.execute("INSERT INTO meta VALUES ('t_gestoppt', ?)", (teil,)); c.commit()
                    if teil == "ENTSCHEID_K":
                        ereignis(c, "ENDE", "Kontaminationsprobe nicht bestanden (P2b) - nur noch vorwaerts messen, T wird nicht fortgesetzt")
                        c.execute("INSERT OR REPLACE INTO meta VALUES ('ende', ?)", ("P2b " + jetzt_txt(),)); c.commit()
                        return 0
                continue
            if teil == "T" and c.execute("SELECT 1 FROM meta WHERE k='t_gestoppt'").fetchone():
                continue                                       # T wurde am Zwischenentscheid beendet: weiter mit R
            while erledigt(c, teil, pos) < k:
                nr = erledigt(c, teil, pos)                    # Stimmen sind lueckenlos 0..k-1
                if max_aufrufe is not None and gesamt >= max_aufrufe:
                    ereignis(c, "HALT", "max_aufrufe %d erreicht (Pruefung)" % max_aufrufe)
                    return 0
                erg = eine_stimme(c, clients, K, teil, pos, nr, zeilen[pos], spot)
                herzschlag(c)
                if erg == "ok":
                    gesamt += 1
                    fehler_folge = 0
                elif erg == "fehler":
                    fehler_folge += 1
                    time.sleep(0 if platzhalter else min(600, 15 * 2 ** min(fehler_folge, 5)))
                    if fehler_folge >= 20:
                        ereignis(c, "PAUSE", "20 Fehler in Folge - 30 min Pause")
                        time.sleep(0 if platzhalter else 1800)
                        fehler_folge = 0
                else:
                    if kein_warten:
                        ereignis(c, "LEER", "Kontingent aller Schluessel fuer heute verbraucht - Ende (--kein-warten)")
                        return 0
                    w = sekunden_bis_neuer_tag()
                    ereignis(c, "WARTEN", "Kontingent leer - warte %.1f h bis zum naechsten Pazifik-Tag" % (w / 3600))
                    ende = time.time() + w
                    while time.time() < ende:
                        time.sleep(min(300, max(1, ende - time.time())))
                        herzschlag(c)
        ereignis(c, "FERTIG", "alle Teile erledigt · Aufrufe dieses Laufs %d" % gesamt)
        c.execute("INSERT OR REPLACE INTO meta VALUES ('ende', ?)", ("fertig " + jetzt_txt(),)); c.commit()
        return 0
    except SystemExit as exc:
        ereignis(c, "ABBRUCH", str(exc))
        raise
    except BaseException as exc:                               # auch Strg+C: Grund festhalten, Daten sind schon geschrieben
        ereignis(c, "ABBRUCH", "%s: %s %s" % (type(exc).__name__, exc, traceback.format_exc()[-600:]))
        raise
    finally:
        try:
            gib_sperre(c)
            if std_vorher is not None and os.path.getmtime(std) != std_vorher:
                ereignis(c, "WARNUNG", "Standard-DB wurde waehrend des Laufs veraendert - von wem? (N4 schreibt nie hinein)")
        finally:
            c.close()


def stand(ablage: str) -> int:
    if not os.path.exists(ablage):
        print("noch keine Ablage:", ablage)
        return 0
    c = sqlite3.connect("file:%s?mode=ro" % ablage.replace("\\", "/"), uri=True)
    print("N4-Stand %s (Ablage %s)" % (jetzt_txt(), ablage))
    for k, v in c.execute("SELECT k, v FROM meta"):
        print("  %-12s %s" % (k, v))
    n = c.execute("SELECT COUNT(*) FROM eingabe").fetchone()[0]
    leer = {r[0] for r in c.execute("SELECT pos FROM eingabe WHERE eingabe IS NULL")}
    soll = {"K_a": N_KA, "T": n, "K_b": N_KB, "R_w": N_R, "R_v": N_R}
    soll = {t: min(m, n) - sum(1 for p in leer if p < m) for t, m in soll.items()}
    for teil, st in (("K_a", 1), ("T", STIMMEN), ("K_b", STIMMEN), ("R_w", STIMMEN), ("R_v", STIMMEN)):
        fertig = c.execute("SELECT COUNT(*) FROM (SELECT pos FROM stimme WHERE teil=? GROUP BY pos HAVING COUNT(*)>=?)", (teil, st)).fetchone()[0]
        ung = c.execute("SELECT COUNT(*) FROM stimme WHERE teil=? AND gueltig=0", (teil,)).fetchone()[0]
        print("  %-4s %4d von %4d Ankern fertig · ungueltige Stimmen %d" % (teil, fertig, soll[teil], ung))
    for s, tag, nn, er in c.execute("SELECT schluessel, tag, n, erschoepft FROM kontingent ORDER BY tag DESC, schluessel LIMIT 6"):
        print("  Kontingent Schluessel %d am %s: %d von %d%s" % (s, tag, nn, DECKEL[s], " (erschoepft gemeldet)" if er else ""))
    for name, zeit, erg in c.execute("SELECT name, zeit, ergebnis FROM entscheid ORDER BY zeit"):
        print("  Entscheid %-14s %s  %s" % (name, zeit, erg))          # nur das Ergebnis, keine Trennzahlen
    h = c.execute("SELECT pid, zeit, start FROM herz WHERE id=1").fetchone()
    print("  Laeufer: %s" % ("aktiv, pid %d, letzter Herzschlag vor %.0f s" % (h[0], time.time() - h[1]) if h else "keiner aktiv"))
    for z in c.execute("SELECT zeit, art, text FROM ereignis ORDER BY rowid DESC LIMIT 8"):
        print("  %s %-10s %s" % (z[0], z[1], z[2][:150]))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("befehl", choices=("lauf", "stand"))
    ap.add_argument("--ablage", default=ABLAGE_VORGABE)
    ap.add_argument("--platzhalter", choices=("zufall", "orakel"))
    ap.add_argument("--kein-warten", action="store_true")
    ap.add_argument("--max-aufrufe", type=int)
    x = ap.parse_args()
    if x.platzhalter and os.path.abspath(x.ablage) == os.path.abspath(ABLAGE_VORGABE):
        raise SystemExit("Platzhalter-Laeufe nie in die echte Ablage - bitte --ablage <Wegwerfpfad>")
    sys.exit(lauf(x.ablage, x.platzhalter, x.kein_warten, x.max_aufrufe) if x.befehl == "lauf" else stand(x.ablage))
