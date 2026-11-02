# -*- coding: utf-8 -*-
"""AUSWERTUNG DER GDELT-PROBE AM NB (G7 §9.2 Bedingung 1) — am Desktop, liest nur.

    python -X utf8 Basisinfos/Rechenkern_02_10/gdelt_probe_auswertung.py [<probe.jsonl>]      -> gdelt_probe_auswertung.txt
    python -X utf8 Basisinfos/Rechenkern_02_10/gdelt_probe_auswertung.py --rueckspiel          # NACH dem Probeende: Rückspiel holen

⚠️⚠️ VORAB FESTGELEGT (02.11.2026, bevor es einen einzigen Probewert gab). Die Probe HÄLT, wenn alle drei erfüllt sind:

| K1 Abdeckung  | je Ton fehlt der Tageswert 24 h nach Tagesende an höchstens 10 % der Live-Tage                               |
| K2 Gleichheit | die KLASSE des Zustands (Tageswert und 7-T-Mittel, ``zustaende.klasse``) ist live = Rückspiel an mindestens   |
|               | 90 % der Ton-Tage, je Maß. Live = was um 07:00 UTC des Folgetags in der Probe stand (nach der 06:30-Runde);  |
|               | Rückspiel = derselbe Weg wie die Historie (``sichten_quellen.gdelt_ton``), NACH dem Probeende geholt         |
| K3 Form       | jeder erfolgreiche Abruf hat Tagesauflösung (ein Punkt je Tag)                                               |

Hält sie nicht, wird **c** (Ton auch aus dem Rückspiel nehmen, Ü8) neu vorgelegt — so in G7 §9.2. Nur Auskunft: Verzug bis zum
ersten Wert, Revision (erster gegen letzten Wert desselben Tages), die Fensterprobe (14-T-Fenster gegen die Jahresfenster der
Historie auf den gemeinsamen Tagen) und die Gleichheit der Probe mit dem Quelltext von ``api/sichten_quellen``.

⚠️ Während die Probe läuft, fragt der Desktop GDELT NICHT ab (``--rueckspiel`` verweigert sich vor dem Probeende): beide Rechner
stehen womöglich hinter derselben öffentlichen Adresse, und eine Sperre des einen wäre dann eine Lücke des anderen.
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import os
import re
import sqlite3
import sys
import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
from agent import zustaende as Z  # noqa: E402
from api import sichten_quellen as SQ  # noqa: E402

PROBE_SKRIPT = os.path.join(HIER, "gdelt_probe_nb.py")
PROBE_ORDNER = r"K:\My Drive\Claude_Austauschordner\GDELT_Probe"      # die Datei heißt nach dem Rechnernamen des NB
RUECKSPIEL = os.path.join(PROJ, "data", "_sichten", "gdelt_probe_rueckspiel.json")
AUS = os.path.join(HIER, "gdelt_probe_auswertung.txt")
K1_LUECKE_MAX = 0.10
K2_GLEICH_MIN = 0.90
ENTSCHEID_STUNDE = 7          # live = Stand um 07:00 UTC des Folgetags


def probe_modul(pfad: str = PROBE_SKRIPT):
    spec = importlib.util.spec_from_file_location("gdelt_probe", pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def gleichheit_quelltext(P=None) -> list:
    """(Merkmal, Probe, Quelle, gleich) - die Werte der Quelle aus dem QUELLTEXT abgeleitet, nicht abgeschrieben."""
    P = P or probe_modul()
    src = inspect.getsource(SQ._gdelt_fenster)
    url = re.search(r'"(https://api\.gdeltproject\.org[^"]+)"', src).group(1)
    vs = re.search(r"versuche=(\d+),\s*pause=(\d+)", src)
    parameter = re.findall(r'"(query|mode|format|startdatetime|enddatetime)"\s*:\s*("[^"]*"|\w+)', src)
    zeilen = [("Abfragen (4 Töne)", P.GDELT, SQ.GDELT), ("Abstand zwischen Abfragen (s)", P.GDELT_ABSTAND_S, SQ.GDELT_ABSTAND_S),
              ("Fenster --laufend (Tage)", P.LAUFEND_TAGE, SQ.LAUFEND_TAGE), ("Kopfzeile", P.H, SQ.H), ("Adresse", P.URL, url),
              ("Versuche je Abfrage", 2, int(vs.group(1))), ("Pause vor dem 2. Versuch (s)", P.ZWEITER_VERSUCH_S, int(vs.group(2))),
              ("mode", "timelinetone", dict(parameter).get("mode", "").strip('"')),
              ("format", "json", dict(parameter).get("format", "").strip('"'))]
    return [(k, a, b, a == b) for k, a, b in zeilen]


def lade_probe(pfad: str) -> tuple:
    P = probe_modul()
    z = P.lies(pfad)
    st = next((x for x in z if x.get("art") == "start"), None)
    if st is None:
        raise SystemExit("keine Startzeile in %s" % pfad)
    return st, z


def _tag(gdelt_datum: str) -> str:
    return "%s-%s-%s" % (gdelt_datum[:4], gdelt_datum[4:6], gdelt_datum[6:8])


def abrufe(z: list) -> pd.DataFrame:
    """Je erfolgreichem Abruf und Tag eine Zeile (ts, ton, tag, wert, tagesaufloesung)."""
    zeilen = []
    for x in z:
        if x.get("art") != "abruf" or x.get("punkte") is None:
            continue
        tage = [_tag(d) for d, _ in x["punkte"]]
        tages = len(tage) == len(set(tage))
        for (d, w), t in zip(x["punkte"], tage):
            zeilen.append((pd.Timestamp(x["ts"]), x["ton"], t, float(w), tages))
    return pd.DataFrame(zeilen, columns=["ts", "ton", "tag", "wert", "tagesaufloesung"])


def historie(pfad: str = SQ.ABLAGE) -> pd.DataFrame:
    c = sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)
    try:
        return pd.read_sql("SELECT symbol AS ton, datum AS tag, wert FROM reihe WHERE quelle='gdelt_ton'", c)
    finally:
        c.close()


def live_tage(st: dict, bis: datetime) -> list:
    """Tage d, deren Ende (d+1 00:00 UTC) in die Probe fällt und deren 24-h-Frist abgelaufen ist."""
    a, e = datetime.fromisoformat(st["ts"]), min(datetime.fromisoformat(st["ende"]), bis)
    d, aus = a.date(), []
    while True:
        ende_d = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(days=1)
        if ende_d + timedelta(days=1) > e:
            return aus
        if ende_d >= a:
            aus.append(d.isoformat())
        d += timedelta(days=1)


def verfuegbarkeit(A: pd.DataFrame, tage: list, toene) -> pd.DataFrame:
    zeilen = []
    for ton in toene:
        a = A[A.ton == ton]
        for d in tage:
            ende_d = pd.Timestamp(d, tz="UTC") + pd.Timedelta(days=1)
            x = a[(a.tag == d) & (a.ts >= ende_d)].sort_values("ts")
            erst = x.iloc[0] if len(x) else None
            zeilen.append((ton, d, None if erst is None else (erst.ts - ende_d).total_seconds() / 3600,
                           None if erst is None else erst.wert, None if x.empty else x.iloc[-1].wert, len(x)))
    return pd.DataFrame(zeilen, columns=["ton", "tag", "verzug_h", "erstwert", "letztwert", "abrufe"])


def stand_live(A: pd.DataFrame, ton: str, zeitpunkt: pd.Timestamp) -> dict:
    """Je Tag der Wert aus dem JÜNGSTEN erfolgreichen Abruf vor ``zeitpunkt`` - so stünde es live in der Ablage (INSERT OR REPLACE)."""
    a = A[(A.ton == ton) & (A.ts < zeitpunkt)].sort_values("ts")
    return a.groupby("tag").wert.last().to_dict()


def _ablage(werte: dict) -> Z.Ablage:
    """{ton: {tag: wert}} -> Ablage mit bekannt_ab = Folgetag 00:00 (wie sichten_quellen)."""
    rows = [("gdelt_ton", ton, d, w, SQ._folgetag(d), None) for ton, r in werte.items() for d, w in r.items()]
    return Z.Ablage(df=pd.DataFrame(rows, columns=["quelle", "symbol", "datum", "wert", "bekannt_ab", "bis"]))


def klassenvergleich(A: pd.DataFrame, H: pd.DataFrame, R: dict, tage: list, schnitt: str) -> pd.DataFrame:
    """Je Ton, Live-Tag und Maß: Klasse live gegen Rückspiel am Stichtag d+1. Die Historie zählt nur VOR ``schnitt`` (erster Tag
    im Fenster der Probe) - sonst füllte sie eine Lücke der Probe auf und versteckte sie."""
    defs = [d for d in Z.DEFINITIONEN if d[1] == "gdelt_ton"]
    zeilen = []
    for d in tage:
        T = SQ._folgetag(d)
        zp = pd.Timestamp(T) + pd.Timedelta(hours=ENTSCHEID_STUNDE)
        live, rueck = {}, {}
        for ton in R:
            h = H[(H.ton == ton) & (H.tag < schnitt)].set_index("tag").wert.to_dict()
            live[ton] = {**h, **stand_live(A, ton, zp)}
            rueck[ton] = {**h, **R[ton]}
        al, ar = _ablage(live), _ablage(rueck)
        for de in defs:
            ton = de[2].split("~")[0]
            if ton not in R or d not in R[ton]:
                continue
            zl, zr = Z.zustand(de, al, T), Z.zustand(de, ar, T)
            zeilen.append((ton, d, de[4], zl.klasse, zr.klasse, zl.rang, zr.rang, zl.stand, zr.stand))
    return pd.DataFrame(zeilen, columns=["ton", "tag", "mass", "klasse_live", "klasse_rueck", "rang_live", "rang_rueck",
                                         "stand_live", "stand_rueck"])


def lade_rueckspiel(pfad: str = RUECKSPIEL) -> dict | None:
    if not os.path.exists(pfad):
        return None
    with open(pfad, encoding="utf-8") as f:
        r = json.load(f)
    return {ton: dict(map(tuple, w)) for ton, w in r["werte"].items()}


def hole_rueckspiel(st: dict, pfad: str = RUECKSPIEL, trotzdem: bool = False) -> None:
    """Derselbe Weg wie die Historie (``SQ.gdelt_ton``), über die ganze Probezeit samt 14-T-Vorlauf - EINE Abfrage je Ton."""
    ende = datetime.fromisoformat(st["ende"])
    if datetime.now(timezone.utc) < ende and not trotzdem:
        raise SystemExit("Probe läuft bis %s - der Desktop fragt GDELT bis dahin NICHT ab (gemeinsame Adresse möglich)" % st["ende"])
    ab = (datetime.fromisoformat(st["ts"]).date() - timedelta(days=SQ.LAUFEND_TAGE)).isoformat()
    bis = (ende.date() + timedelta(days=1)).isoformat()
    werte = {}
    for i, (ton, q) in enumerate(SQ.GDELT.items()):
        if i:
            time.sleep(SQ.GDELT_ABSTAND_S)
        werte[ton] = [(d, w) for d, w, _, _ in SQ.gdelt_ton(q, ab, bis)]
        print("  %s: %d Tage" % (ton, len(werte[ton])), flush=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump({"geholt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "ab": ab, "bis": bis, "werte": werte}, f)


def auswerten(st: dict, z: list, H: pd.DataFrame, R: dict | None, bis: datetime | None = None) -> dict:
    P = probe_modul()
    bis = bis or datetime.now(timezone.utc)
    A = abrufe(z)
    ab = [x for x in z if x.get("art") == "abruf"]
    runden_ist = {x["runde"] for x in z if x.get("art") == "runde_ende"}
    a = datetime.fromisoformat(st["ts"])
    e = min(datetime.fromisoformat(st["ende"]), bis)
    soll = {P.iso(s) for s in P.slots_zwischen(a, e)} | {"start"}
    tage = live_tage(st, bis)
    V = verfuegbarkeit(A, tage, list(P.GDELT))
    r = {"st": st, "abrufe": len(ab), "mit_werten": sum(1 for x in ab if x.get("punkte") is not None),
         "http": pd.Series([str(x.get("http")) for x in ab]).value_counts().to_dict() if ab else {},
         "runden_soll": len(soll), "runden_ist": len(runden_ist & soll), "runden_fehlen": sorted(soll - runden_ist),
         "neustarts": sum(1 for x in z if x.get("art") == "neustart"), "kaputt": sum(1 for x in z if x.get("art") == "kaputt"),
         "tage": tage, "V": V, "A": A}
    # K1
    k1 = {}
    for ton, g in V.groupby("ton"):
        luecke = g.verzug_h.isna() | (g.verzug_h > 24)
        k1[ton] = (int(luecke.sum()), len(g), float(luecke.mean()) if len(g) else float("nan"))
    r["k1"] = k1
    r["k1_ok"] = bool(tage) and all(q <= K1_LUECKE_MAX for _, _, q in k1.values())
    # K3
    r["k3_abrufe_nicht_taeglich"] = int((~A.groupby("ts").tagesaufloesung.all()).sum()) if len(A) else 0
    r["k3_ok"] = len(A) > 0 and r["k3_abrufe_nicht_taeglich"] == 0
    # Fensterprobe: 14-T-Fenster gegen die Jahresfenster der Historie (gemeinsame Tage)
    m = A.merge(H, on=["ton", "tag"], suffixes=("", "_hist"))
    r["fensterprobe"] = (len(m), float((m.wert - m.wert_hist).abs().max()) if len(m) else float("nan"),
                         int(((m.wert - m.wert_hist).abs() > 1e-9).sum()))
    # Revision
    rv = V.dropna(subset=["erstwert"])
    r["revision"] = (len(rv), float((rv.letztwert - rv.erstwert).abs().max()) if len(rv) else float("nan"),
                     int(((rv.letztwert - rv.erstwert).abs() > 1e-9).sum()))
    # K2
    if R is None:
        r["k2"], r["k2_ok"] = None, None
    else:
        K = klassenvergleich(A, H, R, tage, (a.date() - timedelta(days=P.LAUFEND_TAGE)).isoformat())
        r["K"] = K
        r["k2"] = {mass: (int((g.klasse_live == g.klasse_rueck).sum()), len(g)) for mass, g in K.groupby("mass")}
        r["k2_ok"] = bool(r["k2"]) and all(n and g / n >= K2_GLEICH_MIN for g, n in r["k2"].values())
    r["haelt"] = None if r["k2_ok"] is None else (r["k1_ok"] and r["k2_ok"] and r["k3_ok"])
    return r


def bericht(r: dict, gl: list) -> str:
    st = r["st"]
    o = ["GDELT-PROBE AM NB — Auswertung %s" % datetime.now(timezone.utc).isoformat(timespec="minutes"),
         "Probe: Rechner %s · Python %s · Fassung %s · Prüfsumme %s · Start %s · Ende %s" % (
             st.get("rechner"), st.get("python"), st.get("fassung"), st.get("pruefsumme"), st["ts"], st["ende"]), "",
         "Gleichheit mit dem Quelltext von api/sichten_quellen (Ü8):"]
    o += ["  %s %-32s %s" % ("✔" if g else "✖", k, "" if g else "Probe %r · Quelle %r" % (a, b)) for k, a, b, g in gl]
    o += ["", "Runden: %d von %d (fehlen: %s) · Abrufe %d, davon mit Werten %d · HTTP %s · Neustarts %d · kaputte Zeilen %d" % (
        r["runden_ist"], r["runden_soll"], ", ".join(r["runden_fehlen"][:12]) or "keine", r["abrufe"], r["mit_werten"], r["http"],
        r["neustarts"], r["kaputt"]), ""]
    o.append("K1 Abdeckung (Wert spätestens 24 h nach Tagesende; Soll Lücken ≤ %d %%) — %d Live-Tage" % (K1_LUECKE_MAX * 100, len(r["tage"])))
    for ton, (n, m, q) in r["k1"].items():
        v = r["V"][r["V"].ton == ton].verzug_h.dropna()
        o.append("  %-8s Lücken %d von %d (%.0f %%) · Verzug bis zum ersten Wert: Median %.1f h, max %.1f h" % (
            ton, n, m, q * 100 if m else float("nan"), v.median() if len(v) else float("nan"), v.max() if len(v) else float("nan")))
    o.append("  → %s" % ("erfüllt" if r["k1_ok"] else "NICHT erfüllt" if r["tage"] else "noch keine Live-Tage"))
    o += ["", "K3 Form: Abrufe ohne Tagesauflösung %d → %s" % (
        r["k3_abrufe_nicht_taeglich"], "noch kein Abruf mit Werten" if not len(r["A"]) else "erfüllt" if r["k3_ok"] else "NICHT erfüllt"), ""]
    if r["k2"] is None:
        o.append("K2 Gleichheit: offen — Rückspiel erst nach dem Probeende holen (--rueckspiel)")
    else:
        o.append("K2 Gleichheit der Klasse live = Rückspiel (Soll ≥ %d %% je Maß):" % (K2_GLEICH_MIN * 100))
        for mass, (g, n) in r["k2"].items():
            o.append("  %-8s %d von %d gleich (%.0f %%)" % (mass, g, n, 100 * g / n if n else float("nan")))
        o.append("  → %s" % ("erfüllt" if r["k2_ok"] else "NICHT erfüllt"))
    n, mx, ab = r["fensterprobe"]
    o += ["", "Auskunft — Fensterprobe (14-T-Fenster der Probe gegen die Jahresfenster der Historie): %d gemeinsame Werte, "
          "abweichend %d, größte Abweichung %s" % (n, ab, "%.4f" % mx if n else "–")]
    n, mx, ab = r["revision"]
    o.append("Auskunft — Revision (erster gegen letzten Wert desselben Tages in der Probe): %d Ton-Tage, geändert %d, größte "
             "Änderung %s" % (n, ab, "%.4f" % mx if n else "–"))
    o += ["", "URTEIL: %s" % ("offen (K2 fehlt)" if r["haelt"] is None else "HÄLT — G8 baut den Abruf (a)" if r["haelt"]
                              else "HÄLT NICHT — c neu vorlegen (G7 §9.2)")]
    return "\n".join(o)


def main(a: list) -> int:
    pfad = next((x for x in a[1:] if x.endswith(".jsonl")), None)
    if pfad is None:
        gef = sorted(f for f in os.listdir(PROBE_ORDNER) if f.startswith("gdelt_probe_") and f.endswith(".jsonl"))
        if len(gef) != 1:
            raise SystemExit("in %s nicht genau eine Probedatei: %s - Pfad angeben" % (PROBE_ORDNER, gef))
        pfad = os.path.join(PROBE_ORDNER, gef[0])
    st, z = lade_probe(pfad)
    if "--rueckspiel" in a:
        hole_rueckspiel(st, trotzdem="--trotzdem" in a)
    r = auswerten(st, z, historie(), lade_rueckspiel())
    t = bericht(r, gleichheit_quelltext())
    print(t)
    with open(AUS, "w", encoding="utf-8") as f:
        f.write(t + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
