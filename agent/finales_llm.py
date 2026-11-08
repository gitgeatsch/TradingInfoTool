# -*- coding: utf-8 -*-
"""EBENE 4 — das FINALE LLM je REGEL0-Einstieg (G7 Stufe 3; Voranalyse_G7_Stufe3_finales_LLM_08_11.md, E-174, E-175).

Je Einstieg EINE Bedenken-Stufe 0/1/2 auf die Frage aus Datenbasis §3a, mit zwei Gründen (je eine Kennung der Eingabe) und „was
umstimmt“. Das Urteil ENTSCHEIDET NICHT (Ü9); gemessen wird es in Stufe 3 (Messplan §11, zweistufig nach E-174).

Eingabe (E-175, Nutzer 08.11.: *„Ja, alle vier“*):
  Block 1  Handlung und Wette (ein Satz aus dem Code)
  Block 2  Kurs-Lage (Abstand 200-T-Schnitt) · REGEL0-Lage (v̂, Stufe, Signalstunde) · Hebel-Abstand — sonst nichts (Ü8)
  Block 3  Meldungen zum Asset (A1, ≤ 7 T) mit Kursreaktion als Fakt — OHNE Schwere-Texte (Vorgriff P-1); Asset-Zuordnung um
           Kürzel in Klammern ergänzt (Lücke 1-Zeichen-Kürzel/BTC/ETH, M1 §6.2) — ``agent/ereignisse.py`` bleibt unverändert
  Block 4  Sicht-Gutachten S1, S2, S3, S4, S8, S7 (Form d), nur das Schema, wdh 0, eingefrorene Prompt-SHAs
  NICHT    A4 Gegenanwalt, Block 5 Befund-Karte (Vorgriff), Verwässerung, Wal-Zustand, Bestand
  Zeit     EIN Informationszeitpunkt t = Signalstunde + 1 h (= Spalte ``stunde``) für ALLE Blöcke: Kurse bis t geschlossen,
           Meldungen bekannt_ab ≤ t, Gutachten vom Tag T erst ab T 02:00 UTC (sonst T−1). LIVE muss genau das gebaut werden
           (G8b: Sichten-Tageslauf bis 02:00 UTC, A1 am NB, vorläufige Stufe ausdrücklich übergeben) - heute gibt es es nur im Rückspiel
  Stufe    die VORLÄUFIGE (ATR der Signalstunde), wie in der Live-Mail beim Signal; v̂ der Einstiegsstunde wird nicht gezeigt

⚠️⚠️ Schreibt NUR in ``data/_g7/finales_llm*.db`` — nie in die Produktions-DB. Liest alles ``mode=ro``.
⚠️ ``--vorpruefung`` zeigt NUR Messbarkeit, p_b, p_a und WEITER/ENDE — keinen weiteren Blick gegen Kurse (E-174).

    python -m agent.finales_llm --eingabe SYMBOL "2026-03-04 20:00"   # Eingabe ohne Netz
    python -m agent.finales_llm --prompt
    python -m agent.finales_llm --vorgriff                           # alle 2.379 Eingaben ohne Netz prüfen
    python -m agent.finales_llm --probe                              # 5 Einstiege auf den Probe-2-Tagen, eigene Ablage
    python -m agent.finales_llm --lauf3a | --vorpruefung | --lauf3b | --stand
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from agent import ereignisse as EV
from agent import kursreaktion as KR
from agent import sichten_gutachten as SG

PROJ = SG.PROJ
RK = os.path.join(PROJ, "Basisinfos", "Rechenkern_02_10")
ABLAGE = os.path.join(PROJ, "data", "_g7", "finales_llm.db")
ABLAGE_PROBE = os.path.join(PROJ, "data", "_g7", "finales_llm_probe.db")
GUTACHTEN = SG.ABLAGE
GUTACHTEN_PROBE = os.path.join(PROJ, "data", "_g7", "gutachten_probe2.db")
MENGE = os.path.join(RK, "g7_stufe3_menge_b.csv")
MENGE_SHA = "62a0641aeb643b46"
VORAUSWAHL = os.path.join(RK, "g7_stufe3_vorauswahl_d3.csv")
VORAUSWAHL_SHA = "314c47c3d8e06077"
ZIELGROESSE = os.path.join(PROJ, "data", "_g7", "regel0", "stufe3_zielgroesse_b.csv")
STUFE_VORL = os.path.join(PROJ, "data", "_g7", "regel0", "stufe3_stufe_vorlaeufig.csv")   # g7_stufe3_stufe_vorlaeufig.py, Gegenprobe 2435/2435
STUFE_VORL_SHA = "f6bef1cefcd7367d"     # NB-Abgleich Okt. 2026: 199/199 vorläufig und endgültig gleich
ZIELGROESSE_SHA = "c9a0b0e6111f298b"
MODELL = SG.MODELL
SCHLUESSEL = SG.SCHLUESSEL
SICHTEN = ("S1", "S2", "S3", "S4", "S8", "S7")
GUTACHTEN_AB_H = 2                       # S3-5: live braucht der Tageslauf der Sichten nach 00:00 rund 7 Aufrufe
TAGE_200 = 200
MAX_TYPEN = 6                            # Block 3: höchstens 6 Meldungsarten (neueste zuerst), Token-Grenze
VERSUCHE = 3
HUERDE = 0.40                            # E-174, Selbsttest Fassung 2: D3, c = 0,40, ODER-Regel
VERKEHRT = 0.95
MESSBAR = (0.05, 0.95)
UNLESBAR_ROT = 0.05
PROBE_N = 5
PROMPT_EINGEFROREN = "a7d1c5048eb0"      # eingefroren 08.11. nach der Probe (5/5 lesbar, treu, Belege ohne Stelle 0); 3a/3b nur damit
SAAT = 20261108
BEDENKEN = {0: "wie geplant", 1: "vorsichtiger", 2: "nicht"}
KENNUNG_FEST = ("Handlung", "Kurs-Lage", "REGEL0-Lage", "Hebel-Abstand") + SICHTEN
KLAMMER = re.compile(r"\(([A-Z0-9]{1,12})\)")


def _sha(pfad: str) -> str:
    with open(pfad, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def _t(stunde: str) -> pd.Timestamp:
    """Informationszeitpunkt t (naiv, UTC) = Spalte ``stunde`` = Signalstunde + 1 h."""
    return KR._T(stunde)


def _iso(t: pd.Timestamp) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def gutachten_tag(t: pd.Timestamp) -> str:
    """S3-5: das Gutachten vom Tag T erst ab T 02:00 UTC, sonst das vom Vortag — live dieselbe Regel."""
    d = t.normalize() if t.hour >= GUTACHTEN_AB_H else t.normalize() - pd.Timedelta(days=1)
    return d.strftime("%Y-%m-%d")


def _zahl(x: float, nachkomma: int = 1) -> str:
    return ("%+.*f" % (nachkomma, x)).replace(".", ",").replace("-", "−")


# ══ Quelle ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
class Quelle:
    """Kurse, Meldungen und Gutachten einmal geladen (alles ``mode=ro``)."""

    def __init__(self, gutachten: str = GUTACHTEN, kurse: KR.Kurse | None = None, E: pd.DataFrame | None = None):
        self.kurse = kurse or KR.Kurse()
        E = EV.lade() if E is None else E
        E = E[E.ereignis == 1].copy()
        E["liste"] = [set(json.loads(a)) if isinstance(a, str) and a.startswith("[") else set() for a in E.assets]
        E["klammer"] = [set(KLAMMER.findall(t or "")) for t in E.titel]
        self.E = E.sort_values("bekannt_ab").reset_index(drop=True)
        self._g = sqlite3.connect("file:%s?mode=ro" % gutachten.replace("\\", "/"), uri=True)
        self._cache: dict = {}

    def gutachten(self, tag: str, sicht: str):
        k = (tag, sicht)
        if k not in self._cache:
            self._cache[k] = self._g.execute(
                "SELECT form_ok, felder, ereignisse FROM gutachten WHERE tag=? AND sicht=? AND wdh=0 AND modell=? AND prompt_sha=?",
                (tag, sicht, MODELL, SG.prompt_sha(sicht))).fetchone()
        return self._cache[k]


# ══ Eingabe ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def block1(r) -> str:
    # Wortlaut der Wette wie im Betrieb (regel0_llm.plan_text, P1 03.10.: ohne "Gegenbewegung nach einem Rückgang" beurteilten die
    # Rollen einen TRENDhandel und sagten bei 9 von 10 "dagegen"; Gegenprüfung 08.11. M2)
    return ("[Handlung] Geplant ist ein Kauf (LONG) von %s auf eine Gegenbewegung nach einem Rückgang, mit Hebel %d-fach: Einstieg zum "
            "Schlusskurs der nächsten Stunde, Ausstieg genau 24 Stunden danach. Zu beurteilen ist, ob die Gegenbewegung in diesen 24 "
            "Stunden trägt." % (r.symbol, int(r.stufe_vorlaeufig)))


def block2(q: Quelle, r, t: pd.Timestamp) -> tuple[list, list]:
    """Kurs-Lage, REGEL0-Lage, Hebel-Abstand — nur Kerzen, die bis t geschlossen sind (Index = Stundenbeginn, Schluss = Beginn + 1 h)."""
    zeilen, vorgriff = [], []
    s, _quelle = q.kurse.reihe(r.symbol)
    s = s[s.index <= t - pd.Timedelta(hours=1)] if s is not None else None
    if s is None or not len(s):
        zeilen.append("[Kurs-Lage] kein Kurs bis %s UTC" % t.strftime("%Y-%m-%d %H:00"))
        sig = None
    else:
        p_t, bei = float(s.iloc[-1]), s.index[-1]
        if bei + pd.Timedelta(hours=1) > t:
            vorgriff.append("Kurs %s" % bei)
        d = s[s.index < t.normalize()].resample("D").last().dropna()
        if len(d) >= TAGE_200:
            ab = p_t / float(d.iloc[-TAGE_200:].mean()) - 1
            zeilen.append("[Kurs-Lage] Kurs um %s UTC: %s %% %s dem 200-Tage-Schnitt der Tagesschlüsse (Fakt)" % (
                t.strftime("%Y-%m-%d %H:00"), ("%.1f" % abs(100 * ab)).replace(".", ","), "über" if ab >= 0 else "unter"))
        else:
            zeilen.append("[Kurs-Lage] 200-Tage-Schnitt: zu kurze Reihe (%d Tage) (Fakt)" % len(d))
        sig = KR._sigma(s, t)
    # v̂ wird NICHT gezeigt: die Mengendatei trägt v̂ der EINSTIEGSstunde (eine Stunde nach t, Vorgriff); zum Signal ist nur bekannt,
    # dass die Kurve die Schwelle erstmals überschritten hat. Stufe = VORLÄUFIGE (ATR der Signalstunde) wie in der Live-Mail (Ü8).
    st = int(r.stufe_vorlaeufig)
    if st <= 0:
        raise ValueError("vorläufige Stufe 0 - live kein Handel, kein Aufruf (%s %s)" % (r.symbol, r.stunde))
    zeilen.append("[REGEL0-Lage] Signal zur Stunde %s UTC: das Kurvenmodell hat die Schwelle 0,035 erstmals nach mindestens 48 Stunden "
                  "darunter überschritten; Hebelstufe %dx aus der eigenen Schwankung des Assets (ATR der Signalstunde) (Fakt)" % (
                      str(r.signalstunde)[:16], st))
    liq = 100.0 / st
    if sig:
        zeilen.append("[Hebel-Abstand] Bei %dx liegt die Liquidation rechnerisch rund %.0f %% unter dem Einstieg (ohne Gebühren und "
                      "Haltemarge); das sind %s übliche Tagesschwankungen des Assets (Schwankung der letzten 60 Tage: %s %% je Tag) (Fakt)"
                      % (st, liq, ("%.1f" % (liq / (100 * sig))).replace(".", ","), ("%.1f" % (100 * sig)).replace(".", ",")))
    else:
        zeilen.append("[Hebel-Abstand] Bei %dx liegt die Liquidation rechnerisch rund %.0f %% unter dem Einstieg; übliche Schwankung: "
                      "zu kurze Reihe (Fakt)" % (st, liq))
    return zeilen, vorgriff


def block3(q: Quelle, r, t: pd.Timestamp) -> tuple[list, list, dict]:
    """Meldungen zum Asset, bekannt_ab ≤ t, höchstens 7 Tage alt; je Typ eine Zeile (neueste zuerst), Kursreaktion bis t."""
    sym = str(r.symbol).upper()
    E = q.E
    x = E[(E.bekannt_ab <= _iso(t)) & (E.bekannt_ab > _iso(t - pd.Timedelta(days=EV.FENSTER_T)))]
    x = x[[sym in a or sym in k for a, k in zip(x.liste, x.klammer)]]
    zeilen, vorgriff, emap = [], [], {}
    gruppen = sorted(x.groupby("typ"), key=lambda kv: kv[1].bekannt_ab.max(), reverse=True)[:MAX_TYPEN]
    for i, (typ, g) in enumerate(gruppen):
        nr = "E%d" % (i + 1)
        e = g.sort_values("bekannt_ab").iloc[-1]
        h = (t - pd.Timestamp(e.bekannt_ab).tz_convert(None)).total_seconds() / 3600
        n = " (+%d weitere dieses Typs)" % (len(g) - 1) if len(g) > 1 else ""
        kr = KR.reaktion(q.kurse, sym, e.bekannt_ab, t)        # ab der GEZEIGTEN (neuesten) Meldung (Gegenprüfung 08.11. S1)
        if kr["bis"] > t.strftime("%Y-%m-%d %H:00"):
            vorgriff.append("%s Kurs bis %s" % (nr, kr["bis"]))
        vorgriff += ["%s bekannt %s" % (nr, b) for b in g.bekannt_ab if b > _iso(t)]
        titel = re.sub(r"\s+", " ", str(e.titel or "")).strip()[:160]
        zeilen.append("[%s] bekannt %s UTC · Quelle %s · Typ: %s · neu seit %s · %s%s (Fakt)" % (
            nr, e.bekannt_ab[:16].replace("T", " "), e.quelle, typ, ("%.0f h" % h) if h < 48 else ("%.1f T" % (h / 24)).replace(".", ","),
            titel, n))
        zeilen.append("      seit dieser Meldung: %s" % KR.satz(kr))
        emap[nr] = {"typ": typ, "beleg": e.beleg, "quelle": e.quelle}
    return zeilen, vorgriff, emap


def _gutachten_zeile(sicht: str, tag: str, row, sym: str) -> str:
    name = SG.SICHT[sicht][0]
    if row is None:
        return "[%s] %s: kein Gutachten für den %s" % (sicht, name, tag)
    if not row[0]:
        return "[%s] %s: Gutachten vom %s unlesbar" % (sicht, name, tag)
    f = json.loads(row[1])
    tr = []
    for x in f.get("treiber") or []:
        if not isinstance(x, dict):
            continue
        wer = x.get("schluessel") or ("Meldung Typ %s" % x.get("typ") if x.get("ereignis") else None) or \
            ("Termin %s %s" % (x.get("termin"), x.get("tag")) if x.get("termin") else "?")
        tr.append("%s: %s" % (wer, x.get("aussage") or ""))
    teile = ["[%s] %s (Gutachten vom %s 00:00 UTC): Zustand %s · Wirkung auf Krypto: %s · Horizont: %s (%s T) · neu seit: %s · "
             "eingepreist: %s" % (sicht, name, tag, f.get("zustand"), f.get("wirkung_krypto"), f.get("horizont"), f.get("horizont_t"),
                                  f.get("neu_seit") or "–", f.get("eingepreist"))]
    if tr:
        teile.append("Treiber: " + " · ".join(tr))
    teile.append("kippt, wenn: %s" % (f.get("kippt_wenn") or ""))
    teile.append("Gegenargument: %s" % (f.get("gegenargument") or ""))
    if sicht == "S7":
        em = json.loads(row[2] or "{}")
        eig = [a for a in (f.get("assets") or []) if isinstance(a, dict) and str(a.get("asset", "")).upper() == sym]
        teile.append("zu %s: %s" % (sym, "; ".join("%s (Meldung Typ %s)" % (a.get("wirkung"), em.get(a.get("ereignis"), {}).get("typ", "?"))
                                                  for a in eig) if eig else "nicht genannt"))
    return " | ".join(teile) + " (Einschätzung, ungeprüft)"


def block4(q: Quelle, r, t: pd.Timestamp) -> tuple[list, list, list]:
    tag = gutachten_tag(t)
    fehlt = []
    zeilen = []
    for s_ in SICHTEN:
        row = q.gutachten(tag, s_)
        if row is None:
            fehlt.append((tag, s_))
        zeilen.append(_gutachten_zeile(s_, tag, row, str(r.symbol).upper()))
    vorgriff = [] if pd.Timestamp(tag) + pd.Timedelta(hours=GUTACHTEN_AB_H if tag == t.strftime("%Y-%m-%d") else 0) <= t else \
        ["Gutachten %s vor %s" % (tag, t)]
    return zeilen, vorgriff, fehlt


def eingabe(q: Quelle, r) -> dict:
    t = _t(r.stunde)
    b2, v2 = block2(q, r, t)
    b3, v3, emap = block3(q, r, t)
    b4, v4, fehlt = block4(q, r, t)
    teile = ["Signalzeitpunkt: %s UTC (alles unten war zu diesem Zeitpunkt bekannt)" % t.strftime("%Y-%m-%d %H:00"), "",
             "HANDLUNG:", block1(r), "", "LAGE DES ASSETS:"] + b2 + ["", "MELDUNGEN ZUM ASSET (höchstens %d Tage alt):" % EV.FENSTER_T] + \
        (b3 or ["  (keine)"]) + ["", "SICHTEN AUF DEN MARKT (Einschätzungen anderer Gutachter, ungeprüft):"] + b4
    text = "\n".join(teile)
    b3t = "\n".join(b3)
    vorgriff = v2 + v3 + v4 + (["Schwere in Block 3"] if ("Schwere:" in b3t or any(w_ in b3t for w_ in EV.SCHWERE.values())) else [])
    return {"text": text, "sha": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], "ereignisse": emap,
            "kennungen": list(KENNUNG_FEST) + list(emap), "vorgriff": vorgriff, "fehlt": fehlt}


# ══ Prompt und Leser ════════════════════════════════════════════════════════════════════════════════════════════════════════════
def prompt() -> str:
    return (
        "Du bist ein erfahrener, nüchterner Trading-Experte für Kryptowährungen. Ein regelbasiertes System (REGEL0) hat ein "
        "Einstiegssignal gegeben. Du bekommst die Handlung mit ihrer Wette, die Lage des Assets, Meldungen zum Asset und die "
        "Einschätzungen von sechs Sichten auf den Markt. Alles in der Eingabe war zum Signalzeitpunkt bekannt.\n\n"
        "FRAGE: Spricht die Gesamtlage dafür, diese Handlung wie geplant, vorsichtiger (kleiner, kürzer, enger) oder nicht "
        "auszuführen? Nenne die zwei entscheidenden Gründe und was dich umstimmen würde.\n\n"
        "REGELN\n"
        "- Nur die Eingabe zählt. Du weißt nicht, was nach dem Signalzeitpunkt geschah; nutze kein Wissen über spätere Ereignisse "
        "oder Kurse.\n"
        "- Die Wette setzt gerade auf eine Gegenbewegung NACH einem Rückgang. Ein vorangegangener Rückgang oder ein Kurs unter dem "
        "Schnitt ist deshalb für sich allein kein Grund dagegen.\n"
        "- Wäge Gründe dafür und dagegen ab. bedenken 0 = wie geplant: in der Abwägung überwiegt nichts gegen die Wette in den "
        "nächsten 24 Stunden. bedenken 1 = vorsichtiger: die Abwägung ergibt ein erhöhtes Risiko für die Wette, ohne dass die Gründe "
        "dagegen überwiegen. bedenken 2 = nicht: die belegten Gründe gegen die Wette überwiegen deutlich.\n"
        "- Ein Zustand allein ist kein Grund. Sage, warum er in den nächsten 24 Stunden auf DIESE Wette wirkt.\n"
        "- Jeder Grund stützt sich auf GENAU eine Stelle der Eingabe. Nenne sie als beleg mit ihrer Kennung aus den eckigen Klammern, "
        "ohne die Klammern: Handlung, Kurs-Lage, REGEL0-Lage, Hebel-Abstand, S1, S2, S3, S4, S7, S8 oder E1, E2 ...\n"
        "- Die Sichten sind Einschätzungen anderer Gutachter, keine Fakten. Wäge sie, übernimm sie nicht ungeprüft.\n"
        "- Gebühren und Kosten spielen keine Rolle. Beurteile die Lage, nicht den Namen oder Ruf des Assets.\n"
        "- Keine Kursziele, keine Kauf- oder Verkaufsempfehlung über die Frage hinaus.\n\n"
        "ANTWORT: genau ein JSON-Objekt, sonst nichts:\n"
        '{"bedenken": 0|1|2, "handlung": "wie geplant|vorsichtiger|nicht", '
        '"gruende": [{"grund": "ein Satz", "beleg": "<Kennung>"}, {"grund": "ein Satz", "beleg": "<Kennung>"}], '
        '"umstimmen": "was dich umstimmen würde, ein Satz"}')


def prompt_sha() -> str:
    return hashlib.sha256(("%s\n%s" % (MODELL, prompt())).encode("utf-8")).hexdigest()[:12]


def lies(roh: str, kennungen: list) -> tuple[dict | None, list, int, int]:
    """-> (Felder oder None = unlesbar, Formfehler, Belege geprüft, Belege ohne Stelle in der Eingabe)."""
    try:
        g = json.loads(roh[roh.index("{"):roh.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError) as e:
        return None, ["kein JSON-Objekt: %s" % str(e)[:80]], 0, 0
    if not isinstance(g, dict):
        return None, ["kein Objekt"], 0, 0
    b = g.get("bedenken")
    if isinstance(b, str) and b.strip().isdigit():
        b = int(b.strip())
    if isinstance(b, bool) or not isinstance(b, int):
        return None, ["bedenken %r" % g.get("bedenken")], 0, 0
    if b not in BEDENKEN:
        return None, ["bedenken %r" % b], 0, 0
    if str(g.get("handlung") or "").strip().lower() != BEDENKEN[b]:
        return None, ["handlung %r passt nicht zu bedenken %d" % (g.get("handlung"), b)], 0, 0
    gr = g.get("gruende")
    if not isinstance(gr, list) or len(gr) != 2 or not all(isinstance(x, dict) and x.get("grund") for x in gr):
        return None, ["gruende: nicht genau zwei"], 0, 0
    if not str(g.get("umstimmen") or "").strip():
        return None, ["umstimmen fehlt"], 0, 0
    fehler = ["unbekannte Felder %s" % sorted(set(g) - {"bedenken", "handlung", "gruende", "umstimmen"})] \
        if set(g) - {"bedenken", "handlung", "gruende", "umstimmen"} else []
    ohne = 0
    for x in gr:
        x["beleg"] = str(x.get("beleg") or "").strip().strip("[]").strip()
        ohne += x["beleg"] not in kennungen
    if gr[0]["beleg"] == gr[1]["beleg"]:
        fehler.append("beide Gründe mit demselben Beleg %r" % gr[0]["beleg"])
    g["bedenken"] = b
    return g, fehler, len(gr), ohne


# ══ Ablage ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def verbinde(pfad: str = ABLAGE) -> sqlite3.Connection:
    if not os.path.basename(pfad).lower().startswith("finales_llm"):
        raise SystemExit("finales_llm schreibt NUR in finales_llm*.db, nie in %s" % os.path.basename(pfad))
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    c = sqlite3.connect(pfad, timeout=60)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS urteil (
            symbol TEXT, stunde TEXT, teil TEXT, phase TEXT, modell TEXT, prompt_sha TEXT, eingabe_sha TEXT, eingabe TEXT,
            ereignisse TEXT, roh TEXT, versuche INTEGER, form_ok INTEGER, formfehler TEXT, bedenken INTEGER, felder TEXT,
            belege INTEGER, belege_ohne_stelle INTEGER, tokens INTEGER, am TEXT, modell_antwort TEXT,
            PRIMARY KEY (symbol, stunde, modell, prompt_sha));
        CREATE TABLE IF NOT EXISTS vorpruefung (am TEXT, prompt_sha TEXT, n INTEGER, unlesbar INTEGER, anteil REAL, p_b REAL,
            p_a REAL, ergebnis TEXT, lesart TEXT);""")
    return c


def _jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _rufe(key: str, system: str, nutzer: str, http=None) -> tuple[str, int, str]:
    """Wie ``sichten_gutachten.rufe`` (dieselbe Warte-Logik, dasselbe Anfragebuch), gibt aber zusätzlich die MODELLKENNUNG der Antwort
    zurück (Voranalyse §1: zwischen 3a und 3b liegen Tage). Eigene Kopie, weil ``rufe`` im laufenden Stufe-1-Lauf steckt."""
    import time
    import requests
    http = http or requests
    body = {"model": MODELL, "temperature": 0, "reasoning_effort": "medium",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": nutzer}]}
    folge503 = 0
    echt = http is requests
    for _ in range(2000):
        try:
            r = http.post(SG.URL, headers={"Authorization": "Bearer %s" % key}, json=body, timeout=240)
        except Exception:                                      # noqa: BLE001
            if echt:
                SG._buche("netz")
            time.sleep(60)
            continue
        if echt:
            SG._buche("%d%s" % (r.status_code, "-Tag" if r.status_code == 429 and "PerDay" in r.text else ""))
        if r.status_code == 429 or r.status_code >= 500:
            g = re.search(r'"retryDelay"\s*:\s*"([\d.]+)s"', r.text)
            warte = 900.0 if "PerDay" in r.text else float(g.group(1)) if g else float(r.headers.get("retry-after") or 30)
            if r.status_code >= 500:
                folge503 += 1
                warte = max(warte, min(30 * 2 ** (folge503 - 1), 600))
            time.sleep(min(max(warte + 2, 5), 900))
            continue
        if r.status_code in (401, 403):
            r.raise_for_status()
        if r.status_code >= 400:
            raise SG.HttpDauerfehler("HTTP %d: %s" % (r.status_code, r.text[:200]))
        j = r.json()
        try:
            inhalt = j["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError, TypeError):
            inhalt = ""
        return inhalt, int((j.get("usage") or {}).get("total_tokens") or 0), str(j.get("model") or "")
    raise RuntimeError("LLM %s: keine Antwort" % MODELL)


def eingaben_geaendert(c: sqlite3.Connection, q: "Quelle", phasen=("3a",)) -> list:
    """Gegenprüfung 08.11. M1 (wie ``sichten_gutachten.veraltet``): abgelegte Urteile, deren EINGABE heute anders aussieht
    (geänderter Code, nachgetragene Meldungen, überschriebene Gutachten). Dann ist es eine NEUE Messung (R-R11) -> Abbruch."""
    M = menge().set_index(["symbol", "stunde"])
    aus = []
    sql = ("SELECT symbol, stunde, eingabe_sha FROM urteil WHERE modell=? AND prompt_sha=? AND phase IN (%s)"
           % ",".join("?" * len(phasen)))
    for sym, st_, h in c.execute(sql, (MODELL, prompt_sha(), *phasen)).fetchall():
        r = type("R", (), dict(M.loc[(sym, st_)].to_dict(), symbol=sym, stunde=st_))
        if eingabe(q, r)["sha"] != h:
            aus.append((sym, st_))
    return aus


def urteil(c: sqlite3.Connection, q: Quelle, r, key: str, phase: str, http=None) -> dict:
    ein = eingabe(q, r)
    if ein["vorgriff"]:
        raise RuntimeError("VORGRIFF %s %s: %s" % (r.symbol, r.stunde, ein["vorgriff"][:3]))
    if ein["fehlt"]:
        raise RuntimeError("Gutachten fehlen %s %s: %s" % (r.symbol, r.stunde, ein["fehlt"]))
    roh, tok, g, fehler, n, gepr, ohne, m_ant = "", 0, None, [], 0, 0, 0, ""
    for n in range(1, VERSUCHE + 1):
        try:
            roh, t_, m_ant = _rufe(key, prompt(), ein["text"], http)
        except SG.HttpDauerfehler as e:
            roh, g, fehler = "", None, [str(e)[:200]]
            break
        tok += t_
        g, fehler, gepr, ohne = lies(roh, ein["kennungen"])
        if g is not None:
            break
    c.execute("INSERT OR REPLACE INTO urteil VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
        r.symbol, r.stunde, getattr(r, "teil", ""), phase, MODELL, prompt_sha(), ein["sha"], ein["text"],
        json.dumps(ein["ereignisse"], ensure_ascii=False), roh, n, int(g is not None), json.dumps(fehler, ensure_ascii=False),
        None if g is None else g["bedenken"], None if g is None else json.dumps(g, ensure_ascii=False), gepr, ohne, tok, _jetzt(),
        m_ant))
    c.commit()
    return {"form_ok": g is not None, "bedenken": None if g is None else g["bedenken"], "formfehler": fehler, "ohne": ohne}


def _vorhanden(c, symbol, stunde) -> bool:
    return c.execute("SELECT 1 FROM urteil WHERE symbol=? AND stunde=? AND modell=? AND prompt_sha=?",
                     (symbol, stunde, MODELL, prompt_sha())).fetchone() is not None


# ══ Mengen ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def menge() -> pd.DataFrame:
    if _sha(MENGE) != MENGE_SHA:
        raise SystemExit("Menge b geändert (Prüfsumme) - festgeschrieben 02.11.")
    for f_, h_ in ((STUFE_VORL, STUFE_VORL_SHA), (ZIELGROESSE, ZIELGROESSE_SHA)):
        if _sha(f_) != h_:
            raise SystemExit("%s geändert (Prüfsumme) - festgeschrieben 08.11." % os.path.basename(f_))
    M = pd.read_csv(MENGE, sep=";")
    Z = pd.read_csv(ZIELGROESSE, sep=";")[["symbol", "stunde", "ertrag_s"]]
    S = pd.read_csv(STUFE_VORL, sep=";")[["symbol", "stunde", "stufe_vorlaeufig", "stufe_menge"]]
    M = M.merge(S, on=["symbol", "stunde"], how="left", validate="1:1")
    if M.stufe_vorlaeufig.isna().any() or (M.stufe_menge != M.stufe).any():
        raise SystemExit("vorläufige Stufe fehlt oder passt nicht zur Menge (g7_stufe3_stufe_vorlaeufig.py)")
    return M.merge(Z, on=["symbol", "stunde"], how="left").dropna(subset=["ertrag_s"]).sort_values(["stunde", "symbol"]) \
        .reset_index(drop=True)


def vorauswahl() -> pd.DataFrame:
    if _sha(VORAUSWAHL) != VORAUSWAHL_SHA:
        raise SystemExit("Vorauswahl geändert (Prüfsumme) - festgeschrieben 08.11. (E-174)")
    V = pd.read_csv(VORAUSWAHL, sep=";")[["symbol", "stunde"]]
    return menge().merge(V, on=["symbol", "stunde"], how="inner").sort_values(["stunde", "symbol"]).reset_index(drop=True)


def probe_menge() -> pd.DataFrame:
    """B3: 5 Einstiege der Menge b an den Probe-2-Tagen (dort liegen alle Sichten in den eingefrorenen Fassungen), NICHT aus der
    Vorauswahl; ausgelost, nicht ausgesucht."""
    c = sqlite3.connect("file:%s?mode=ro" % GUTACHTEN_PROBE.replace("\\", "/"), uri=True)
    tage = {t for (t,) in c.execute("SELECT DISTINCT tag FROM gutachten")}
    c.close()
    M = menge()
    V = set(zip(*[pd.read_csv(VORAUSWAHL, sep=";")[k] for k in ("symbol", "stunde")]))
    M = M[[gutachten_tag(_t(s)) in tage and (y, s) not in V for y, s in zip(M.symbol, M.stunde)]]
    return M.sample(min(PROBE_N, len(M)), random_state=SAAT).sort_values(["stunde", "symbol"]).reset_index(drop=True)


# ══ Lauf und Vorprüfung ═════════════════════════════════════════════════════════════════════════════════════════════════════════
def lauf(c, q: Quelle, rows: pd.DataFrame, key: str, phase: str, protokoll=print, http=None) -> dict:
    if phase != "probe" and prompt_sha() != PROMPT_EINGEFROREN:
        raise SystemExit("Prompt-SHA %s ist nicht der eingefrorene %s - 3a/3b nur mit dem eingefrorenen Prompt" % (prompt_sha(), PROMPT_EINGEFROREN))
    offen = [r for r in rows.itertuples() if not _vorhanden(c, r.symbol, r.stunde)]
    fehlt =sorted({f for r in offen for f in eingabe(q, r)["fehlt"]})
    if fehlt:
        raise SystemExit("Block 4 unvollständig: %d Gutachten fehlen, z. B. %s - erst nach Stufe 1" % (len(fehlt), fehlt[:4]))
    protokoll("Lauf %s: %d offen von %d · Prompt-SHA %s · Modell %s" % (phase, len(offen), len(rows), prompt_sha(), MODELL))
    z = {"neu": 0, "unlesbar": 0}
    for i, r in enumerate(offen):
        e = urteil(c, q, r, key, phase, http)
        z["neu"] += 1
        z["unlesbar"] += not e["form_ok"]
        if i % 25 == 0 or not e["form_ok"] or phase == "probe":
            protokoll("%s %s %s · %s · Belege ohne Stelle %d · %s" % (_jetzt()[:19], r.symbol, r.stunde,
                                                                      "lesbar" if e["form_ok"] else "UNLESBAR", e["ohne"],
                                                                      e["formfehler"] or "Form ok"))
    return z


def _p(Zs: pd.DataFrame, u: np.ndarray) -> float:
    """Dieselbe Statistik wie Selbsttest Fassung 2 (pw) und Messanlage: Arm HANDEL, Tagesbahn, einseitig unten."""
    sys.path.insert(0, RK)
    import g7_stufe3_anlage as A                                       # noqa: E402
    if len(Zs) < 3 or u.sum() in (0, len(u)):
        return float("nan")
    s, null = A.arm_handel_tage(u, Zs.ertrag_s.to_numpy(), A.bahn_tage(Zs.assign(tag=Zs.stunde.str[:10])))
    return float((null <= s).mean()) if np.isfinite(s) and len(null) else float("nan")


def vorpruefung(c, q: "Quelle | None" = None) -> dict:
    """E-174: zeigt NUR Messbarkeit, p_b, p_a und WEITER/ENDE."""
    if c.execute("SELECT 1 FROM vorpruefung WHERE prompt_sha=?", (prompt_sha(),)).fetchone():
        raise SystemExit("Vorprüfung für diesen Prompt-SHA ist schon gelaufen - E-174: genau EINE Vorprüfung")
    if q is not None:
        ge = eingaben_geaendert(c, q, ("3a",))
        if ge:
            raise SystemExit("Eingaben seit dem Ablegen geändert (%d, z. B. %s) - neue Messung (R-R11)" % (len(ge), ge[:3]))
    V = vorauswahl()
    U = pd.read_sql("SELECT symbol, stunde, form_ok, bedenken FROM urteil WHERE modell=? AND prompt_sha=? AND phase='3a'", c,
                    params=(MODELL, prompt_sha()))
    X = V.merge(U, on=["symbol", "stunde"], how="left")
    if X.form_ok.isna().any():
        raise SystemExit("Vorprüfung erst, wenn alle %d Urteile vorliegen (fehlen %d)" % (len(X), int(X.form_ok.isna().sum())))
    unl = int((X.form_ok == 0).sum())
    L = X[X.form_ok == 1].sort_values(["stunde", "symbol"]).reset_index(drop=True)
    u = (L.bedenken >= 1).to_numpy().astype(float)
    anteil = float(u.mean()) if len(u) else float("nan")
    aus = {"n": len(X), "unlesbar": unl, "anteil": anteil, "p_b": float("nan"), "p_a": float("nan")}
    if unl / len(X) > UNLESBAR_ROT:
        aus.update(ergebnis="ENDE", lesart="technisch Rot (> 5 % unlesbar)")
    elif not (MESSBAR[0] <= anteil <= MESSBAR[1]):
        aus.update(ergebnis="ENDE", lesart="nicht messbar (KEIN BEFUND, Scheideweg Fall 5)")
    else:
        aus["p_b"] = _p(L, u)
        ia = (L.teil == "a_gemailt").to_numpy()
        aus["p_a"] = _p(L[ia].reset_index(drop=True), u[ia])
        pb, pa = np.nan_to_num(aus["p_b"], nan=1.0), np.nan_to_num(aus["p_a"], nan=1.0)
        if pb <= HUERDE or pa <= HUERDE:
            aus.update(ergebnis="WEITER", lesart="Hürde genommen - 3b läuft; ausgewertet wird auf allen 2.379")
        elif max(aus["p_b"] if np.isfinite(aus["p_b"]) else 0, aus["p_a"] if np.isfinite(aus["p_a"]) else 0) >= VERKEHRT:
            aus.update(ergebnis="ENDE", lesart="verkehrt, Hinweis aus 3a (Scheideweg Fall 4)")
        else:
            aus.update(ergebnis="ENDE", lesart="nicht trennbar (Scheideweg Fall 4)")
    c.execute("INSERT INTO vorpruefung VALUES (?,?,?,?,?,?,?,?,?)", (_jetzt(), prompt_sha(), aus["n"], unl, anteil, aus["p_b"],
                                                                     aus["p_a"], aus["ergebnis"], aus["lesart"]))
    c.commit()
    return aus


def vorgriff_alle(q: Quelle | None = None) -> dict:
    """Ohne Netz: alle Eingaben der Menge b bauen — Vorgriff, Schwere, fehlende Gutachten, Länge."""
    q = q or Quelle()
    M = menge()
    v, fehlt, laenge, ohne_meldung = [], 0, [], 0
    for r in M.itertuples():
        e = eingabe(q, r)
        v += [(r.symbol, r.stunde, x) for x in e["vorgriff"]]
        fehlt += bool(e["fehlt"])
        laenge.append(len(e["text"]))
        ohne_meldung += not e["ereignisse"]
    return {"eingaben": len(M), "vorgriff": len(v), "beispiele": v[:5], "mit_fehlenden_gutachten": fehlt,
            "zeichen_median": int(np.median(laenge)), "zeichen_max": int(max(laenge)), "ohne_meldung": ohne_meldung}


def darf_3b(c) -> tuple[bool, str]:
    """E-174: 3b nur nach der (einzigen, ersten) Vorprüfung dieses Prompt-SHA mit WEITER."""
    v = c.execute("SELECT ergebnis FROM vorpruefung WHERE prompt_sha=? ORDER BY am ASC LIMIT 1", (prompt_sha(),)).fetchone()
    return (bool(v) and v[0] == "WEITER"), (v[0] if v else "keine Vorprüfung")


def stand(c) -> pd.DataFrame:
    return pd.read_sql("SELECT phase, teil, prompt_sha, COUNT(*) n, SUM(form_ok) lesbar, SUM(belege_ohne_stelle > 0) beleg_fehlt, "
                       "SUM(tokens) tokens, MAX(am) zuletzt FROM urteil GROUP BY 1, 2, 3 ORDER BY 1, 2", c)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                          # noqa: BLE001
        pass
    p = argparse.ArgumentParser()
    p.add_argument("--eingabe", nargs=2, metavar=("SYMBOL", "STUNDE"))
    p.add_argument("--prompt", action="store_true")
    p.add_argument("--vorgriff", action="store_true")
    p.add_argument("--probe", action="store_true")
    p.add_argument("--lauf3a", action="store_true")
    p.add_argument("--vorpruefung", action="store_true")
    p.add_argument("--lauf3b", action="store_true")
    p.add_argument("--stand", action="store_true")
    o = p.parse_args()
    if o.prompt:
        print(prompt(), "\n\nSHA", prompt_sha())
        return 0
    if o.eingabe:
        M = menge()
        r = M[(M.symbol == o.eingabe[0]) & (M.stunde == o.eingabe[1])]
        if not len(r):
            raise SystemExit("nicht in Menge b")
        e = eingabe(Quelle(), next(r.itertuples()))
        print(e["text"], "\n\nSHA", e["sha"], "· Vorgriff", e["vorgriff"] or "keiner", "· fehlt", e["fehlt"] or "nichts")
        return 0
    if o.vorgriff:
        print(vorgriff_alle())
        return 0
    probe = o.probe
    c = verbinde(ABLAGE_PROBE if probe else ABLAGE)
    if probe or o.lauf3a or o.lauf3b:
        from dotenv import dotenv_values
        key = dotenv_values(os.path.join(PROJ, ".env")).get(SCHLUESSEL)
        if probe:
            q = Quelle(gutachten=GUTACHTEN_PROBE)
            print(lauf(c, q, probe_menge(), key, "probe", protokoll=lambda s: print(s, flush=True)))
        elif o.lauf3a:
            print(lauf(c, Quelle(), vorauswahl(), key, "3a", protokoll=lambda s: print(s, flush=True)))
        else:
            ok_, stand_ = darf_3b(c)
            if not ok_:
                raise SystemExit("3b nur nach Vorprüfung WEITER (E-174) - Stand: %s" % stand_)
            q = Quelle()
            ge = eingaben_geaendert(c, q, ("3a",))
            if ge:
                raise SystemExit("Eingaben von 3a seit dem Ablegen geändert (%d) - neue Messung (R-R11)" % len(ge))
            M = menge()
            V = set(zip(vorauswahl().symbol, vorauswahl().stunde))
            print(lauf(c, q, M[[(y, s) not in V for y, s in zip(M.symbol, M.stunde)]], key, "3b",
                       protokoll=lambda s: print(s, flush=True)))
    if o.vorpruefung:
        a = vorpruefung(c, Quelle())
        print("VORPRÜFUNG 3a: %d Urteile · unlesbar %d · Anteil Bedenken ≥ 1 %.1f %% · p_b %.3f · p_a %.3f → %s (%s)" % (
            a["n"], a["unlesbar"], 100 * a["anteil"], a["p_b"], a["p_a"], a["ergebnis"], a["lesart"]))
    print(stand(c).to_string())
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
