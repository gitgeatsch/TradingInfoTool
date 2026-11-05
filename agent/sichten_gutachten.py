# -*- coding: utf-8 -*-
"""EBENE 2 — die SICHT-GUTACHTEN (G7 Stufe 1, Voranalyse_G7_Stufe1_04_11.md B1–B4; Nutzer 05.11.2026: *„ja hört sich vernünftig an
also deine Empfehlung“* = Umfang a, alle sechs Sichten in einem Lauf, S7 zuletzt).

Je Sicht und Stichtag EIN Gutachten nach der Ergebnisform von Datenbasis §3a (zustand, wirkung_krypto, horizont, neu_seit, eingepreist,
treiber ≤ 3, kippt_wenn, gegenargument). Die Eingabe ist genau das, was am Stichtag bekannt war: Zustände (``agent.zustaende``) und
Ereignisse (``agent.ereignisse``, A1). Jedes Gutachten wird von Prüfer v2 auf Faktentreue GEZÄHLT, nie verworfen (S1-7).

    python -m agent.sichten_gutachten --eingabe 2026-03-18 S1      # nur die Eingabe zeigen, ohne Netz
    python -m agent.sichten_gutachten --probe                      # B6: 3 Tage x 6 Sichten in eine EIGENE Ablage
    python -m agent.sichten_gutachten --lauf                       # der Rückspiel-Lauf, wiederaufnehmbar
    python -m agent.sichten_gutachten --stand

⚠️⚠️ Schreibt NUR in ``data/_g7/gutachten.db`` (oder ``--pfad``) — nie in die Produktions-DB, nie in ``sichten.db``.
⚠️ Stichtag T = 00:00 UTC des Tages, wie der Vergleichsarm (g7_stufe0 c): Zustände mit Stand ≤ T−1, Ereignisse mit bekannt_ab ≤ T.
⚠️ Kein Blick gegen KÜNFTIGE Kurse in diesem Modul — gemessen wird erst in Stufe 2, nach dem ganzen Lauf (Voranalyse §5.1).

S7 in zwei Armen (Voranalyse_G7_S7_Anlage_05_11.md §4a/§4b; Nutzer 05.11.2026: *„Ja, d + Wort-Arm“*):
  S7  (Form d, HAUPTARM)  das LLM sieht KEINEN Kurs, ``eingepreist`` = 'unbekannt'. Die Kursreaktion seit jeder Meldung (bis T, Fakt,
                          ``agent.kursreaktion``) wird je E-Nummer und Asset in die Ablage NEBEN das Urteil gelegt - für das finale LLM.
  S7w (Arm e)             dieselbe Eingabe, je Ereigniszeile zusätzlich nur das WORT (gestiegen / gefallen / unverändert, gegen BTC).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from agent import ereignisse as EV
from agent import gutachten_pruefer as GP
from agent import kursreaktion as KR
from agent import zustaende as Z

PROJ = Z.PROJ
ABLAGE = os.path.join(PROJ, "data", "_g7", "gutachten.db")
ABLAGE_PROBE = os.path.join(PROJ, "data", "_g7", "gutachten_probe.db")
MODELL = EV.MODELL                       # gemini-3.5-flash-lite: einziges Modell mit belegt >= 480 Aufrufen/Tag, sauber ab Dez. 2025
URL = EV.URL
SCHLUESSEL = EV.SCHLUESSEL               # GEMINI_API_KEY_2 - nie der NB-Schlüssel
ZEITRAUM = ("2025-12-01", "2026-10-31")  # 335 Tage, Voranalyse §0
REIHENFOLGE = ("S1", "S3", "S8", "S2", "S4", "S7", "S7w")   # §5.1: S7 zuletzt; S7w = Arm e (§4b)
BASIS = {"S7w": "S7"}                    # S7w liest dieselben Zustände und Ereignisse wie S7
MIT_KURS = ("S7", "S7w")                 # Kursreaktion als Fakt in der Ablage; im Text nur bei S7w (als Wort)
WDH_ANTEIL = 0.05                        # S1-6: Eigenrauschen
SAAT = 20261105
VERSUCHE = 3                             # Formfehler -> nachfassen, danach als unlesbar abgelegt
PROBE_TAGE = 3

ZUSTAND = {"normal": 0, "auffällig": 1, "kritisch": 2}
WIRKUNG = {"stützt": -1, "keine": 0, "belastet": 1}          # Vorabfestlegung §4: belastet = +1
HORIZONT = ("stunden", "tage", "wochen")
EINGEPREIST = ("ja", "teilweise", "nein", "unbekannt")
FELDER = ("zustand", "wirkung_krypto", "horizont", "horizont_t", "neu_seit", "eingepreist", "eingepreist_beleg", "treiber", "aussage",
          "kippt_wenn", "gegenargument", "assets")

# ══ B1 Fragen-Prompt je Sicht ═══════════════════════════════════════════════════════════════════════════════════════════════════
# Frage = Datenbasis §3a, Horizont nach Vorabfestlegung §4 eingesetzt (S1/S3 1–5 T: ein Zeitraum trägt nur H <= 5, G7-1).
SICHT = {
    "S1": ("Krypto gesamt", "Ist die Krypto-Gesamtlage ungewöhnlich (Hebel überdehnt, Stablecoin-Abfluss, Breite bricht weg), und erhöht das "
           "das Risiko eines breiten Einbruchs in den nächsten 1–5 Tagen?"),
    "S2": ("Liquidität und Zinsen USA", "Hat sich die Liquiditäts- oder Zinslage so verändert, dass Risikoanlagen in den nächsten Wochen "
           "belastet oder gestützt werden? Welcher Termin kann das kippen?"),
    "S3": ("Risikoappetit Weltmärkte", "Gibt es Stress an Aktien- oder Kreditmärkten, der in den nächsten 1–5 Tagen auf Krypto "
           "übergreifen kann?"),
    "S4": ("Dollar und Rohstoffe", "Bewegt sich Dollar, Gold, Öl oder Kupfer ungewöhnlich, und auf welchem Weg träfe das Krypto in den "
           "nächsten Wochen?"),
    "S7": ("Ereignisse je Asset, Konflikte", "Welche Meldung betrifft ein Asset direkt, und ist sie neu? "
           "Belastet oder stützt sie dieses Asset in den nächsten 1–5 Tagen? Dazu: verschärft die Konfliktlage (Krieg, Sanktionen, "
           "Zölle) das Risiko für Krypto insgesamt?"),
    "S7w": ("Ereignisse je Asset, Konflikte", "Welche Meldung betrifft ein Asset direkt, ist sie neu, und hat der Kurs schon reagiert? "
            "Belastet oder stützt sie dieses Asset in den nächsten 1–5 Tagen? Dazu: verschärft die Konfliktlage (Krieg, Sanktionen, "
            "Zölle) das Risiko für Krypto insgesamt?"),
    "S8": ("Termine", "Steht in den nächsten 1–3 Tagen ein Termin an, der nach seinem gemessenen Faktor die Schwankung erhöht, und in "
           "welche Richtung kann er kippen?"),
}


def basis(sicht: str) -> str:
    return BASIS.get(sicht, sicht)


_EINGEPREIST = ("- eingepreist: ob der Markt schon reagiert hat (ja / teilweise / nein); 'unbekannt', wenn die Eingabe dazu nichts zeigt. "
                "eingepreist_beleg: worauf du das stützt, ein kurzer Satz.\n")
_EINGEPREIST_S7 = ("- eingepreist: hier IMMER 'unbekannt' - du siehst keine Kurse; ob und wie der Kurs seit der Meldung reagiert hat, legt "
                   "das System als Fakt neben deine Einschätzung. eingepreist_beleg: leer.\n")
_EINGEPREIST_S7W = ("- eingepreist: ob der Kurs seit der Meldung schon reagiert hat (ja / teilweise / nein); die Angabe 'Kurs seit "
                    "Meldung' in der Ereigniszeile zeigt je Asset die Richtung (gestiegen / gefallen / unverändert, gegen BTC, gemessen "
                    "an der üblichen Schwankung des Assets). 'unbekannt' bei 'kein Kurs'. eingepreist_beleg: worauf du das stützt, ein "
                    "kurzer Satz.\n")


def prompt(sicht: str) -> str:
    name, frage = SICHT[sicht]
    s7 = (' "assets": [{"asset": "<Ticker>", "wirkung": "belastet|stützt|keine", "ereignis": "E<n>", "neu": true|false}],'
          if sicht == "S7" else
          ' "assets": [{"asset": "<Ticker>", "wirkung": "belastet|stützt|keine", "ereignis": "E<n>", "neu": true|false, '
          '"eingepreist": "ja|teilweise|nein|unbekannt"}],' if sicht == "S7w" else "")
    s7_regel = ("- assets: je Asset, das von einer Meldung DIREKT betroffen ist und bei dem du eine Wirkung siehst, ein Eintrag mit der "
                "Meldung (E-Nummer), auf die er sich stützt. Nicht genannte Assets gelten als 'keine'. Leere Liste, wenn nichts davon "
                "zutrifft.\n" if sicht in MIT_KURS else "")
    eing = {"S7": _EINGEPREIST_S7, "S7w": _EINGEPREIST_S7W}.get(sicht, _EINGEPREIST)
    return (
        "Du bist ein erfahrener, nüchterner Beobachter der Kryptomärkte. Du bekommst die Lage EINER Sicht (%s) an einem Stichtag. "
        "Alles in der Eingabe war zu diesem Zeitpunkt bekannt und ist ein FAKT über die Gegenwart. Deine Aufgabe ist die EINSCHÄTZUNG, "
        "was daraus für Krypto folgt.\n\n"
        "FRAGE: %s\n\n"
        "REGELN\n"
        "- Nur die Eingabe zählt. Du weißt nicht, was nach dem Stichtag geschah; nutze kein Wissen über spätere Ereignisse oder Kurse.\n"
        "- 'normal' ist der Regelfall. Ein ● heißt nur, dass ein Wert im eigenen 5-Jahres-Rang weit oben oder unten liegt - das ist "
        "noch keine ungewöhnliche Lage. 'auffällig' nur, wenn die Lage als Ganzes vom Normalen abweicht; 'kritisch' nur, wenn sie das "
        "deutlich tut und das Risiko für Krypto im Horizont der Frage erheblich erhöht.\n"
        "- wirkung_krypto: belastet / stützt / keine - die Richtung der Wirkung auf Krypto im Horizont der Frage.\n"
        "%s"
        "- treiber: höchstens 3, die deine Einschätzung tragen. Jeder in GENAU einer dieser Formen, Werte EXAKT wie in der Eingabe:\n"
        '    Zustand:  {"schluessel": "<der Text in den eckigen Klammern, OHNE die Klammern, z. B. S1.dvol.BTC>", '
        '"wert": <die erste Zahl der Zeile>, '
        '"rang": <die Zahl nach P>, "klasse": "sehr tief|tief|normal|hoch|sehr hoch" (das Wort nach dem = in der Zeile), '
        '"aussage": "..."}\n'
        '    Ereignis: {"ereignis": "E<n>", "typ": "<das Wort nach Typ: in der Zeile>", "aussage": "..."}\n'
        '    Termin:   {"termin": "fomc|cpi|nfp", "tag": "JJJJ-MM-TT", "aussage": "..."}\n'
        "- In ALLEN Texten (aussage, kippt_wenn, gegenargument, eingepreist_beleg und die aussage jedes Treibers) KEINE Zahlen - "
        "Werte und Ränge gehören in die Felder der Treiber. Erlaubt ist nur der Horizont in Tagen.\n"
        "- neu_seit: Datum (JJJJ-MM-TT), seit dem der wichtigste Treiber bekannt ist; leer, wenn nichts Besonderes vorliegt.\n"
        "- kippt_wenn: welcher Auslöser oder Termin die Einschätzung umstoßen würde. gegenargument: das stärkste Argument dagegen.\n"
        "%s"
        "- Keine Kauf- oder Verkaufsempfehlung, keine Gebühren, keine Kursziele.\n\n"
        "ANTWORT: genau ein JSON-Objekt, sonst nichts:\n"
        '{"zustand": "normal|auffällig|kritisch", "wirkung_krypto": "belastet|stützt|keine", "horizont": "stunden|tage|wochen", '
        '"horizont_t": <Tage als ganze Zahl>, "neu_seit": "JJJJ-MM-TT oder leer", "eingepreist": "ja|teilweise|nein|unbekannt", '
        '"eingepreist_beleg": "...", "treiber": [...],%s "aussage": "ein Satz", "kippt_wenn": "...", "gegenargument": "..."}'
        % (name, frage, eing, s7_regel, s7))


def prompt_sha(sicht: str) -> str:
    """Je Sicht eigene Prüfsumme: wird S7 nach seinem Selbsttest angepasst, bleiben S1–S4/S8 gültig (keine Doppelaufrufe)."""
    return hashlib.sha256(("%s\n%s" % (MODELL, prompt(sicht))).encode("utf-8")).hexdigest()[:12]


# ══ B2 Eingabe je Sicht und Tag ═════════════════════════════════════════════════════════════════════════════════════════════════
def _T(tag: str) -> str:
    return Z._T(tag)


def herkunft(e) -> str:
    """S1-4: Regel / Vorfilter / Weg b je Ereigniszeile, damit Stufe 2 Weg b getrennt ausweisen kann."""
    if e.quelle != "nachricht":
        return "boerse_%s" % e.methode
    if e.methode != "llm":
        return "nachricht_%s" % e.methode
    return "vorfilter" if EV.vorfilter(e.titel) else "weg_b"


class Quelle:
    """Zustände und Ereignisse einmal geladen (beides ``mode=ro``)."""

    def __init__(self, ablage: Z.Ablage | None = None, E: pd.DataFrame | None = None, kurse: KR.Kurse | None = None):
        self.ablage = ablage or Z.Ablage()
        self.E = EV.lade() if E is None else E
        self._tag: dict = {}
        self._kurse = kurse

    @property
    def kurse(self) -> KR.Kurse:
        """Nur für S7/S7w und erst beim ersten Gebrauch (S1–S4/S8 lesen nie einen Kurs)."""
        if self._kurse is None:
            self._kurse = KR.Kurse()
        return self._kurse

    def tag(self, tag: str):
        """-> (Zustände, Ereignisse am Stichtag) - je Tag einmal, für alle sechs Sichten."""
        if tag not in self._tag:
            T = _T(tag)
            self._tag = {tag: (Z.zustaende(T, self.ablage), EV.am(self.E, T, assets=EV.assets_am(T)))}
        return self._tag[tag]


def eingabe(q: Quelle, tag: str, sicht: str) -> dict:
    """-> {"text", "sha", "ereignisse" (E-Nr -> beleg, typ, herkunft), "pruef" (Prüfer-v2-Eingabe), "vorgriff" (Liste)}."""
    T = _T(tag)
    b = basis(sicht)
    liste, ev = q.tag(tag)
    zs = [z for z in liste if z.sicht == b]
    zeilen, vorgriff = [], []
    for z in zs:
        k = "termin %s" % z.symbol if z.quelle == "termin" else GP.schluessel(z)
        zeilen.append(("● " if z.auffaellig else "  ") + re.sub(r"^\[%s\]" % b, "[%s]" % k, z.satz))
        if z.quelle != "termin" and z.stand and z.stand[:10] >= tag:
            vorgriff.append("%s Stand %s" % (k, z.stand))
    x = ev[ev.sicht == b]
    evz = EV.zeilen(ev, b, T)
    gruppen = list(x.groupby(["typ", "assets"], sort=False))
    if len(gruppen) != len(evz):
        raise RuntimeError("Ereigniszeilen %d gegen Gruppen %d" % (len(evz), len(gruppen)))
    emap, ez = {}, []
    for i, ((typ, a_), g) in enumerate(gruppen):
        nr = "E%d" % (i + 1)
        emap[nr] = {"beleg": g.iloc[0].beleg, "typ": typ, "herkunft": sorted({herkunft(e) for e in g.itertuples()})}
        teil = re.sub(r"^\[%s\]" % b, "[%s]" % nr, evz[i]).split(" · ")
        # Probe 2 (05.11.): ohne Beschriftung übernahm das Modell den BEREICH (makro_usa) als Typ - Feld 1 = betrifft, Feld 2 = Typ
        teil[1], teil[2] = "betrifft: " + teil[1], "Typ: " + teil[2]
        if teil[2] != "Typ: " + typ:
            raise RuntimeError("Ereigniszeile %s: Typ %r statt %r" % (nr, teil[2], typ))
        if sicht in MIT_KURS:
            # Form d / Arm e: je Asset der Meldung die Kursreaktion seit Bekanntwerden bis T - Fakt, in die Ablage NEBEN das Urteil
            kr = [KR.reaktion(q.kurse, a, min(g.bekannt_ab), T) for a in json.loads(a_)]
            emap[nr]["kurs"] = kr
            vorgriff += ["%s Kurs %s bis %s" % (nr, r["asset"], r["bis"]) for r in kr if r["bis"] > T[:10] + " 00:00"]
            if sicht == "S7w" and kr:
                teil.insert(len(teil) - 1, "Kurs seit Meldung (gegen BTC; BTC selbst absolut): " +
                            ", ".join("%s %s" % (r["asset"], r["wort"]) for r in kr))
        ez.append(" · ".join(teil))
        vorgriff += ["%s bekannt %s" % (nr, x_) for x_ in g.bekannt_ab if x_ > T]
    teile = ["Stichtag: %s 00:00 UTC (alles unten war zu diesem Zeitpunkt bekannt)" % tag,
             "Sicht %s — %s" % (b, SICHT[sicht][0]), ""]
    if sicht == "S8":
        teile += ["TERMINE (Fakt, mit gemessenem Faktor):"] + zeilen
    else:
        teile += ["ZUSTÄNDE (Fakt; Rang über die letzten 5 Jahre; ● = Rang ≤ P20 oder ≥ P80):"] + (zeilen or ["  (keine)"])
        teile += ["", "EREIGNISSE (am Stichtag bekannt, höchstens %d Tage alt; Fakt):" % EV.FENSTER_T] + (ez or ["  (keine)"])
    text = "\n".join(teile)
    return {"text": text, "sha": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], "ereignisse": emap,
            "pruef": GP.eingabe(zs, x, b), "vorgriff": vorgriff}


# ══ Antwortleser ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _norm(s) -> str:
    t = str(s or "").strip().lower()
    return t.replace("ae", "ä").replace("ue", "ü") if t in ("auffaellig", "stuetzt") else t


def lies(roh: str, sicht: str, emap: dict) -> tuple[dict | None, list]:
    """-> (Felder, Formfehler). Felder None = unbrauchbar (nachfassen). Unbekannte Felder und zu viele Treiber werden GEZÄHLT."""
    fehler = []
    try:
        g = json.loads(roh[roh.index("{"):roh.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError) as e:
        return None, ["kein JSON-Objekt: %s" % str(e)[:80]]
    if not isinstance(g, dict):
        return None, ["kein Objekt"]
    zu, wi = _norm(g.get("zustand")), _norm(g.get("wirkung_krypto"))
    if zu not in ZUSTAND:
        return None, ["zustand %r" % g.get("zustand")]
    if wi not in WIRKUNG:
        return None, ["wirkung_krypto %r" % g.get("wirkung_krypto")]
    g["zustand"], g["wirkung_krypto"] = zu, wi
    fremd = sorted(set(g) - set(FELDER))
    if fremd:
        fehler.append("unbekannte Felder %s" % fremd)
    if _norm(g.get("horizont")) not in HORIZONT:
        fehler.append("horizont %r" % g.get("horizont"))
    if _norm(g.get("eingepreist")) not in EINGEPREIST:
        fehler.append("eingepreist %r" % g.get("eingepreist"))
    try:
        g["horizont_t"] = int(float(g.get("horizont_t")))
    except (TypeError, ValueError):
        fehler.append("horizont_t %r" % g.get("horizont_t"))
        g["horizont_t"] = None
    tr = g.get("treiber")
    if isinstance(tr, list):                                   # Probe 2: "[S1.dvol.BTC]" - Schreibweise, kein Faktenfehler
        for t in tr:
            if isinstance(t, dict) and isinstance(t.get("schluessel"), str):
                t["schluessel"] = t["schluessel"].strip().strip("[]").strip()
    if not isinstance(tr, list):
        fehler.append("treiber keine Liste")
        g["treiber"] = []
    elif len(tr) > 3:
        fehler.append("%d Treiber statt höchstens 3" % len(tr))
    if sicht == "S7" and _norm(g.get("eingepreist")) not in ("unbekannt", ""):
        fehler.append("eingepreist %r ohne Kurs (S7 sieht keinen)" % g.get("eingepreist"))
    if sicht in MIT_KURS:
        a = g.get("assets")
        if not isinstance(a, list):
            fehler.append("assets keine Liste")
            g["assets"] = []
        else:
            for i, e in enumerate(a):
                if not isinstance(e, dict) or _norm(e.get("wirkung")) not in WIRKUNG:
                    fehler.append("assets %d: Form/Wirkung" % (i + 1))
                elif e.get("ereignis") not in emap:
                    fehler.append("assets %d: Ereignis %r nicht in der Eingabe" % (i + 1, e.get("ereignis")))
    elif "assets" in g:
        fehler.append("assets bei %s" % sicht)
    return g, fehler


def fuer_pruefer(g: dict, emap: dict) -> dict:
    """Das Gutachten in der Form, die Prüfer v2 liest: E-Nummer -> Beleg; eingepreist_beleg als Freitext (``zustand_text``); die
    Ereignisse der S7-Assets als weitere Treiber (nur Beleg prüfen)."""
    def ev(t):
        if isinstance(t, dict) and "ereignis" in t:
            t = dict(t)
            t["ereignis"] = emap.get(t["ereignis"], {}).get("beleg", "unbekannt:%s" % t["ereignis"])
        return t
    tr = [ev(t) for t in (g.get("treiber") or [])]
    for e in (g.get("assets") or []) if isinstance(g.get("assets"), list) else []:
        if isinstance(e, dict) and "ereignis" in e:
            tr.append(ev({"ereignis": e["ereignis"]}))
    return {"horizont_t": g.get("horizont_t"), "treiber": tr, "aussage": g.get("aussage"), "kippt_wenn": g.get("kippt_wenn"),
            "gegenargument": g.get("gegenargument"), "zustand_text": g.get("eingepreist_beleg")}


WARTEN: dict = {}                        # Wartegründe seit Start (Statuscode -> [Zahl, Sekunden]) - fürs Protokoll, 05.11.: Lauf wurde langsamer


# ══ LLM ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def rufe(key: str, system: str, nutzer: str, http=None) -> tuple[str, int]:
    """Ein Aufruf; wartet geduldig auf Minuten- und Tageskontingent (Logik wie ``ereignisse.frage``)."""
    import requests
    http = http or requests
    body = {"model": MODELL, "temperature": 0, "reasoning_effort": "medium",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": nutzer}]}
    for _ in range(2000):
        try:
            r = http.post(URL, headers={"Authorization": "Bearer %s" % key}, json=body, timeout=240)
        except Exception:                                      # noqa: BLE001 - Netzaussetzer: warten statt abbrechen
            w_ = WARTEN.setdefault("netz", [0, 0.0])
            w_[0], w_[1] = w_[0] + 1, w_[1] + 60
            time.sleep(60)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            g = re.search(r'"retryDelay"\s*:\s*"([\d.]+)s"', r.text)
            warte = 900.0 if "PerDay" in r.text else float(g.group(1)) if g else float(r.headers.get("retry-after") or 30)
            w_ = WARTEN.setdefault("%d%s" % (r.status_code, "-Tag" if "PerDay" in r.text else ""), [0, 0.0])
            w_[0], w_[1] = w_[0] + 1, w_[1] + min(max(warte + 2, 5), 900)
            time.sleep(min(max(warte + 2, 5), 900))
            continue
        r.raise_for_status()
        j = r.json()
        return j["choices"][0]["message"].get("content") or "", int((j.get("usage") or {}).get("total_tokens") or 0)
    raise RuntimeError("LLM %s: keine Antwort" % MODELL)


# ══ B4 Ablage ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def verbinde(pfad: str = ABLAGE) -> sqlite3.Connection:
    if os.path.basename(pfad).lower() in ("tradinginfotool.db", "sichten.db"):
        raise SystemExit("sichten_gutachten schreibt NIE in %s" % os.path.basename(pfad))
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    c = sqlite3.connect(pfad, timeout=60)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS gutachten (
            tag TEXT, sicht TEXT, wdh INTEGER, modell TEXT, prompt_sha TEXT, eingabe_sha TEXT, eingabe TEXT, ereignisse TEXT,
            roh TEXT, versuche INTEGER, form_ok INTEGER, formfehler TEXT, zustand INTEGER, wirkung INTEGER, felder TEXT,
            treue_geprueft INTEGER, treue_verstoesse INTEGER, pruefung TEXT, tokens INTEGER, am TEXT,
            PRIMARY KEY (tag, sicht, wdh, modell, prompt_sha));""")
    return c


def _jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def vorhanden(c: sqlite3.Connection, tag: str, sicht: str, wdh: int) -> bool:
    return c.execute("SELECT 1 FROM gutachten WHERE tag=? AND sicht=? AND wdh=? AND modell=? AND prompt_sha=?",
                     (tag, sicht, wdh, MODELL, prompt_sha(sicht))).fetchone() is not None


def gutachten(c: sqlite3.Connection, q: Quelle, tag: str, sicht: str, key: str, wdh: int = 0, http=None) -> dict:
    """Ein Gutachten erzeugen, prüfen, ablegen. Bricht bei Vorgriff ab (der darf nie in einen Prompt)."""
    ein = eingabe(q, tag, sicht)
    if ein["vorgriff"]:
        raise RuntimeError("VORGRIFF %s %s: %s" % (tag, sicht, ein["vorgriff"][:3]))
    roh, tok, felder, fehler, n = "", 0, None, [], 0
    for n in range(1, VERSUCHE + 1):
        roh, t = rufe(key, prompt(sicht), ein["text"], http)
        tok += t
        felder, fehler = lies(roh, sicht, ein["ereignisse"])
        if felder is not None:
            break
    pr = GP.pruefe(fuer_pruefer(felder, ein["ereignisse"]), ein["pruef"]) if felder is not None else None
    c.execute("INSERT OR REPLACE INTO gutachten VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
        tag, sicht, wdh, MODELL, prompt_sha(sicht), ein["sha"], ein["text"], json.dumps(ein["ereignisse"], ensure_ascii=False),
        roh, n, int(felder is not None), json.dumps(fehler, ensure_ascii=False),
        None if felder is None else ZUSTAND[felder["zustand"]], None if felder is None else WIRKUNG[felder["wirkung_krypto"]],
        None if felder is None else json.dumps(felder, ensure_ascii=False),
        None if pr is None else pr["geprueft"], None if pr is None else len(pr["verstoesse"]),
        None if pr is None else GP.als_json(pr), tok, _jetzt()))
    c.commit()
    return {"tag": tag, "sicht": sicht, "wdh": wdh, "form_ok": felder is not None, "versuche": n, "formfehler": fehler,
            "zustand": None if felder is None else felder["zustand"], "pruefung": pr}


# ══ B3 Lauf ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def tage(a: str = ZEITRAUM[0], b: str = ZEITRAUM[1]) -> list[str]:
    return [t.strftime("%Y-%m-%d") for t in pd.date_range(a, b, freq="D")]


def wdh_tage(alle: list[str] | None = None) -> list[str]:
    """S1-6: 5 % der Tage, fest ausgelost mit Saat - je alle sechs Sichten ein zweites Mal."""
    alle = alle or tage()
    n = int(round(len(alle) * WDH_ANTEIL))
    return sorted(np.random.default_rng(SAAT).choice(alle, n, replace=False).tolist())


def probe_tage() -> list[str]:
    """B6: 3 Tage, ausgelost mit eigener Saat - nicht ausgesucht (sonst wählt man 'interessante' Tage)."""
    return sorted(np.random.default_rng(SAAT + 6).choice(tage(), PROBE_TAGE, replace=False).tolist())


def plan(probe: bool = False) -> list[tuple[str, str, int]]:
    """Reihenfolge: je Sicht (S1, S3, S8, S2, S4, S7) erst alle Tage, dann ihre Wiederholungen."""
    if probe:
        return [(t, s, 0) for s in REIHENFOLGE for t in probe_tage()]
    w = wdh_tage()
    return [x for s in REIHENFOLGE for x in [(t, s, 0) for t in tage()] + [(t, s, 1) for t in w]]


def lauf(c: sqlite3.Connection, key: str, probe: bool = False, protokoll=print, http=None, q: Quelle | None = None) -> dict:
    """Wiederaufnehmbar: was mit diesem Modell und dieser Prompt-SHA schon abgelegt ist, wird nicht noch einmal gefragt."""
    q = q or Quelle()
    offen = [(t, s, w) for t, s, w in plan(probe) if not vorhanden(c, t, s, w)]
    protokoll("Lauf %s: %d offen von %d · Prompt-SHA %s" % ("PROBE" if probe else "voll", len(offen), len(plan(probe)),
                                                          {s: prompt_sha(s) for s in REIHENFOLGE}))
    z = {"neu": 0, "unlesbar": 0, "treue_beanstandet": 0}
    for i, (t, s, w) in enumerate(offen):
        r = gutachten(c, q, t, s, key, w, http)
        z["neu"] += 1
        z["unlesbar"] += not r["form_ok"]
        z["treue_beanstandet"] += bool(r["pruefung"] and not r["pruefung"]["ok"])
        if i % 25 == 0 or not r["form_ok"] or probe:
            protokoll("%s %s %s wdh %d · %s · %s · %s · Warten %s" % (
                _jetzt()[:19], t, s, w, r["zustand"] or "UNLESBAR", GP.satz(r["pruefung"]) if r["pruefung"] else r["formfehler"],
                "Formfehler %s" % r["formfehler"] if r["formfehler"] else "Form ok",
                {k_: "%d x / %.0f min" % (v_[0], v_[1] / 60) for k_, v_ in WARTEN.items()} or "keins"))
    return z


def stand(c: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql("SELECT sicht, wdh, prompt_sha, COUNT(*) n, SUM(form_ok) lesbar, SUM(treue_verstoesse > 0) beanstandet, "
                       "SUM(zustand = 1) auffaellig, SUM(zustand = 2) kritisch, SUM(tokens) tokens, MAX(am) zuletzt "
                       "FROM gutachten GROUP BY 1, 2, 3 ORDER BY 1, 2", c)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                          # noqa: BLE001
        pass
    p = argparse.ArgumentParser()
    p.add_argument("--eingabe", nargs=2, metavar=("TAG", "SICHT"))
    p.add_argument("--prompt", metavar="SICHT")
    p.add_argument("--probe", action="store_true")
    p.add_argument("--lauf", action="store_true")
    p.add_argument("--stand", action="store_true")
    p.add_argument("--pfad", default=None)
    o = p.parse_args()
    if o.prompt:
        print(prompt(o.prompt), "\n\nSHA", prompt_sha(o.prompt))
        return 0
    if o.eingabe:
        e = eingabe(Quelle(), o.eingabe[0], o.eingabe[1])
        print(e["text"], "\n\nSHA", e["sha"], "· Vorgriff", e["vorgriff"] or "keiner")
        print(json.dumps(e["ereignisse"], ensure_ascii=False)[:2000])
        return 0
    pfad = o.pfad or (ABLAGE_PROBE if o.probe else ABLAGE)
    c = verbinde(pfad)
    if o.probe or o.lauf:
        from dotenv import dotenv_values
        key = dotenv_values(os.path.join(PROJ, ".env")).get(SCHLUESSEL)
        print(lauf(c, key, probe=o.probe, protokoll=lambda s: print(s, flush=True)))
    print(stand(c).to_string())
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
