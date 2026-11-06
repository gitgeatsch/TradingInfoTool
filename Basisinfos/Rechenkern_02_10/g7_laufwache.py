"""G7 STUFE 1 — LAUFWACHE: ist der Lauf gesund, und kann die Messung überhaupt noch etwas zeigen? (Nutzer 05.11.2026: *„kannst du
regelmäßig prüfen, damit wir rechtzeitig abbrechen können wenn schon feststeht dass die Messung nicht trägt bzw. problematisch ist“*)

⚠️⚠️ KEIN BLICK GEGEN KURSE. Gelesen wird nur die Ablage (mode=ro) und das Protokoll. Alles hier ist aus den Urteilen SELBST ablesbar:
  - Gesundheit: Rate, voraussichtliches Ende, Wartegründe, unlesbar, Treue-Beanstandungen
  - Messbarkeit (Vergeblichkeit OHNE Kurs): hat die Hauptgröße genug Abwechslung, über genug Blöcke? Sagt eine Sicht an 98 % der
    Tage dasselbe, kann sie nichts trennen - das steht fest, bevor ein Kurs angesehen wird.

    python Basisinfos/Rechenkern_02_10/g7_laufwache.py           -> Bildschirm + data/_g7_laufwache.txt
"""
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
from agent import sichten_gutachten as G      # noqa: E402

AUS = os.path.join(PROJ, "data", "_g7_laufwache.txt")
LOGS = [os.path.join(PROJ, "data", f) for f in ("_g7_stufe1_lauf7.txt", "_g7_stufe1_lauf6.txt", "_g7_stufe1_lauf5.txt", "_g7_stufe1_lauf4.txt", "_g7_stufe1_lauf3.txt", "_g7_stufe1_lauf2.txt", "_g7_stufe1_lauf.txt")]
BLOCK, MIN_BLOECKE = 15, 20
# Schwellen VORAB (05.11.), nicht nach Ansicht der Werte:
GRENZEN = {"unlesbar_rot": 0.05, "treue_gelb": 0.20, "anteil_min": 0.05, "anteil_max": 0.95, "urteile_je_tag_min": 0.5}
HAUPT = {"S1": "zustand", "S3": "zustand", "S8": "zustand", "S2": "wirkung", "S4": "wirkung", "S7": "assets", "S7w": "assets"}
FRIST = "2026-11-30"                      # Vorschlag 05.11.: liegt das voraussichtliche Ende danach -> Entscheidung, nicht weiterlaufen lassen


def lade():
    c = sqlite3.connect("file:%s?mode=ro" % G.ABLAGE.replace("\\", "/"), uri=True)
    sha = {s: G.prompt_sha(s) for s in G.REIHENFOLGE}
    d = pd.read_sql("SELECT tag, sicht, wdh, prompt_sha, form_ok, zustand, wirkung, felder, treue_verstoesse, am FROM gutachten", c)
    return d[d.apply(lambda r: sha.get(r.sicht) == r.prompt_sha, axis=1)]


def bloecke(tage) -> int:
    t0 = pd.Timestamp(G.ZEITRAUM[0])
    return len({(pd.Timestamp(t) - t0).days // BLOCK for t in tage})


def messbarkeit(x: pd.DataFrame, sicht: str) -> tuple[str, str]:
    """-> (Ampel, Satz). Nur aus den Urteilen, ohne Kurs."""
    x = x[(x.wdh == 0) & (x.form_ok == 1)]
    if not len(x):
        return "–", "noch keine Urteile"
    if HAUPT[sicht] == "zustand":
        ja = x[x.zustand >= 1]
        a = len(ja) / len(x)
        bj, bn = bloecke(ja.tag), bloecke(x[x.zustand == 0].tag)
        s = "auffällig an %.0f %% der Tage · Blöcke mit auffällig %d, mit normal %d" % (100 * a, bj, bn)
    elif HAUPT[sicht] == "wirkung":
        ja = x[x.wirkung != 0]
        a = len(ja) / len(x)
        bj, bn = bloecke(ja.tag), bloecke(x[x.wirkung == 0].tag)
        s = "Wirkung ≠ keine an %.0f %% der Tage (belastet %d / stützt %d) · nur Auskunft" % (
            100 * a, (x.wirkung == 1).sum(), (x.wirkung == -1).sum())
    else:
        n_st = n_bel = 0
        tage = set()
        for t, f in zip(x.tag, x.felder):
            for e in (json.loads(f).get("assets") or []):
                w = str(e.get("wirkung", "")).lower() if isinstance(e, dict) else ""
                n_st += w in ("stützt", "stuetzt")
                n_bel += w == "belastet"
                if w in ("stützt", "stuetzt", "belastet"):
                    tage.add(t)
        je_tag = (n_st + n_bel) / len(x)
        bj = bloecke(tage)
        s = "Urteile je Tag %.1f (stützt %d / belastet %d) · Blöcke mit Urteil %d" % (je_tag, n_st, n_bel, bj)
        ampel = "grün" if je_tag >= GRENZEN["urteile_je_tag_min"] and min(n_st, n_bel) >= 30 else "gelb"
        return ampel, s
    if not (GRENZEN["anteil_min"] <= a <= GRENZEN["anteil_max"]):
        return "rot", s + " → zu wenig Abwechslung, die Hauptgröße kann so nichts trennen"
    return ("grün" if min(bj, bn) >= MIN_BLOECKE or len(x) < len(G.tage()) else "rot"), s


def wartegruende() -> str:
    for f in LOGS:
        if os.path.exists(f):
            w = re.findall(r"Warten (\{.*\}|keins)", open(f, encoding="utf-8", errors="replace").read())
            if w:
                return w[-1]
    return "–"


def anfragebuch(jetzt) -> list[str]:
    """Echte Anfragen je Kontingenttag (Pazifik) aus ``data/_g7/anfragen.csv`` (seit 05.11. abends): zählen 503 mit?"""
    if not os.path.exists(G.ANFRAGEN):
        return ["Anfragebuch: noch leer"]
    b = pd.read_csv(G.ANFRAGEN, sep=";", dtype=str)
    z = []
    for tag in sorted(b.kontingent_tag.unique())[-2:]:
        x = b[b.kontingent_tag == tag]
        n = x.art.value_counts().to_dict()
        z.append("Anfragen Kontingenttag %s (%s): %d gesamt · %s" % (
            tag, "heute" if tag == G.kontingent_tag(jetzt) else "Vortag", len(x),
            " · ".join("%s %d" % (k, v) for k, v in sorted(n.items()))))
        if "429-Tag" in n:
            vor = x[x.zeit_utc < x[x.art == "429-Tag"].zeit_utc.min()]
            z.append("   -> Tagesgrenze erreicht nach %d Anfragen, davon %d erfolgreich (200) und %d Fehlversuche 5xx" % (
                len(vor), (vor.art == "200").sum(), vor.art.str.startswith("5").sum()))
    return z


def main():
    jetzt = datetime.now(timezone.utc)
    d = lade()
    plan = G.plan()
    offen = len(plan) - len(d)
    am = pd.to_datetime(d.am)
    r6 = (am > pd.Timestamp(jetzt) - pd.Timedelta(hours=3)).sum() / 3
    r24 = (am > pd.Timestamp(jetzt) - pd.Timedelta(hours=24)).sum() / 24
    rate = max(min(r6, r24) if r24 > 0 else r6, 0.1)              # vorsichtig: die langsamere der beiden Raten
    ende = pd.Timestamp(jetzt) + pd.Timedelta(hours=offen / rate)
    z = ["G7 LAUFWACHE · %s UTC · KEIN Blick gegen Kurse" % jetzt.strftime("%Y-%m-%d %H:%M"),
         "Fortschritt %d von %d · offen %d · Rate letzte 3 h %.1f/h, 24 h %.1f/h · letztes Gutachten %s" % (
             len(d), len(plan), offen, r6, r24, d.am.max()),
         "voraussichtliches Ende bei der langsameren Rate: %s %s · Wartegründe seit Neustart %s" % (
             ende.strftime("%Y-%m-%d"), "⚠ NACH DER FRIST %s" % FRIST if ende.strftime("%Y-%m-%d") > FRIST else "(vor der Frist %s)" % FRIST,
             wartegruende()),
         ]
    haupt = [p_ for p_ in plan if p_[1] not in ("S2", "S4")]
    erledigt = set(zip(d.tag, d.sicht, d.wdh))
    offen_h = sum(1 for p_ in haupt if (p_[0], p_[1], p_[2]) not in erledigt)
    ende_h = pd.Timestamp(jetzt) + pd.Timedelta(hours=offen_h / rate)
    z.append("Haupttests (ohne S2/S4) offen %d -> voraussichtlich fertig %s" % (offen_h, ende_h.strftime("%Y-%m-%d")))
    z += anfragebuch(jetzt) + [""]
    ampeln = []
    for s in G.REIHENFOLGE:
        x = d[d.sicht == s]
        n0 = (x.wdh == 0).sum()
        unl = 1 - x.form_ok.mean() if len(x) else 0
        tr = (x.treue_verstoesse > 0).mean() if len(x) else 0
        a, satz = messbarkeit(x, s)
        gesund = "rot" if unl > GRENZEN["unlesbar_rot"] else "gelb" if tr > GRENZEN["treue_gelb"] else "grün"
        ampeln += [a, gesund]
        z.append("%-4s %3d/%d Tage · unlesbar %.0f %% · Treue beanstandet %.0f %% [%s] · Messbarkeit [%s] %s" % (
            s, n0, len(G.tage()), 100 * unl, 100 * tr, gesund, a, satz))
    if ende.strftime("%Y-%m-%d") > FRIST:
        ampeln.append("gelb")
        z.append("⚠ voraussichtliches Ende nach der Frist %s -> gelb (bei ROT über mehrere Tage: Entscheidung)" % FRIST)
    if "429-Tag" in wartegruende():
        z.append("⚠ Tageskontingent erreicht (429 PerDay) - Rücksetzen 09:00 MEZ")
    z += ["", "Gesamt: %s" % ("ROT - Entscheidung nötig" if "rot" in ampeln else "GELB - beobachten" if "gelb" in ampeln
                                 else "grün")]
    print("\n".join(z))
    open(AUS, "w", encoding="utf-8").write("\n".join(z) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                  # noqa: BLE001
        pass
    main()
