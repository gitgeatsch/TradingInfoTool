r"""P59 VORPRUEFUNG (Stufe 1): Hat ein bekannter Makro-Termin einen WERT fuer den Hebeltrade? (15.10.2026)

    python Basisinfos/Rechenkern_02_10/p59_termin_vorpruefung.py > Basisinfos/Rechenkern_02_10/p59_termin_vorpruefung.txt

Nur lesend (stundenkurse.db mode=ro, data/_vergleich/kern48jbz_einstiege_bestand.csv, data/_termine/termine.json aus
p59_termine_inventur.py). Schreibt nichts ausser der Ausgabe.

MESSPLAN - VOR DEM LAUF FESTGELEGT, ZWEISEITIG (keine fachliche Richtung vorab angenommen):

  Termine   CPI und Arbeitsmarkt (FRED release 10/50, 08:30 New York), FOMC-Erklaerung (Fed-Kalender, 14:00 New York,
            nur planmaessige Sitzungen). Ausgeschlossen, weil keine Monatsveroeffentlichung: CPI 2024-02-09
            (Saisonfaktoren), NFP 2024-01-10 und 2024-08-21 (Revisionen). Terminstunde = die UTC-Stunde, in der
            die Veroeffentlichung liegt.

  F1 PRAEMISSE  Ist BTC in den 2 Stunden ab Termin unruhiger als zur selben Uhrzeit an Werktagen ohne Termin
            (+-1 Tag Abstand zu jedem Termin)? Groesse: mittlere |log-Rendite| ueber 2 h, Verhaeltnis Termin/Ohne.
            Nullwelt: 10.000 Ziehungen gleich vieler Ersatztage (Werktag, selbe Uhrzeit, ohne Termin). p zweiseitig.

  F2 HAUPTFRAGE  REGEL0-Einstiege (Referenz Fassung 0.1, 2024-2026), deren 24-h-Fenster (Stunde+1 bis +24, wie die
            Barrierenrechnung E2.ergebnisse) einen Termin enthaelt, gegen die uebrigen:
              B24  -5 % zuerst binnen 24 h (Stop-/Liquidationsseite)       \  Hauptgroessen, Bonferroni
              A24  +5 % zuerst binnen 24 h (das Ereignis q5 der REGEL0)    /  alpha 0,05/2 je Groesse
              D24  -5 % beruehrt binnen 24 h, egal in welcher Reihenfolge (Auskunft: Hebel-Gefahr)
            Wirksame Stichprobe = Zahl der TERMINE, nicht der Einstiege (Einstiege am selben Tag haengen zusammen).
            Deshalb Nullwelt: die Termine werden durch Ersatzzeitpunkte ersetzt (Werktag, selbe Uhrzeit, gleiche
            Zahl je Art, ohne echten Termin im Abstand +-1 Tag), 2.000 Ziehungen; die Einstiege bleiben, wie sie sind.
            Je Art und je Jahr: Auskunft, keine Entscheidung.

  SELBSTTEST  200 Laeufe mit Ersatzterminen ALS "echte" Termine: Anteil p < 0,05 muss bei rund 5 % liegen (Sollband
            1-10 %). Aufloesung: Pflanzung +d auf B24 bei Einstiegen im Fenster (d = 0,02/0,04/0,06/0,08), Fundquote
            bei p < 0,025 aus 50 Laeufen je d.

  F3 AUSKUNFT  BTC-Rendite 2 h ab CPI gegen die Tagesaenderung der 2-jaehrigen Rendite (DGS2) am CPI-Tag, je Jahr
            Rangkorrelation - wie empfindlich reagiert Krypto auf die Ueberraschung (n ~ 12 je Jahr: nur Auskunft).

  ENTSCHEIDUNG  F1 bestaetigt -> der Termin traegt als RISIKO-Fakt. F2 belegt (B24 oder A24 p < 0,025, Selbsttest im
            Band) -> Voranalyse fuer ein Gewicht (Hebel/Zeitpunkt) im REGEL0-Betrieb. F2 nicht belegt -> nur Fakt.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.stdout.reconfigure(encoding="utf-8")

B0 = datetime(2020, 1, 1)
NY, UTC = ZoneInfo("America/New_York"), ZoneInfo("UTC")
RNG = np.random.default_rng(59)
AUS = {"cpi": {"2024-02-09"}, "nfp": {"2024-01-10", "2024-08-21"}}
FOMC = ["2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
        "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
        "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09"]


def stunde(tag, uhr):
    t = datetime.fromisoformat("%s %s" % (tag, uhr)).replace(tzinfo=NY).astimezone(UTC).replace(tzinfo=None)
    return int((t - B0).total_seconds() // 3600)


T = json.load(open(os.path.join("data", "_termine", "termine.json"), encoding="utf-8"))
TERM = {"cpi": [stunde(z["tag"], "08:30") for z in T["cpi"] if z["tag"] not in AUS["cpi"]],
        "nfp": [stunde(z["tag"], "08:30") for z in T["nfp"] if z["tag"] not in AUS["nfp"]],
        "fomc": [stunde(d, "14:00") for d in FOMC]}
alle_tage = {(B0 + timedelta(hours=h)).date() for v in TERM.values() for h in v}

# BTC stuendlich
c = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
k = pd.read_sql("select stunde, close from stundenkurse where symbol='BTC' order by stunde", c)
c.close()
k["h"] = ((pd.to_datetime(k.stunde) - pd.Timestamp(B0)).dt.total_seconds() // 3600).astype(int)
close = pd.Series(k.close.values, index=k.h.values)
H0, H1 = int(close.index.min()), int(close.index.max())
lc = np.log(close.reindex(range(H0, H1 + 1)).values)


def bew2(h):
    """|log-Rendite| von der Schlusskurs-Stunde VOR dem Termin bis 2 h danach (Balken h und h+1)."""
    i = h - H0
    if i - 1 < 0 or i + 1 >= len(lc):
        return np.nan
    return abs(lc[i + 1] - lc[i - 1])


def ersatz(h, n, rng):
    """n Ersatzzeitpunkte zur selben UTC-Uhrzeit wie h, an Werktagen, +-1 Tag ohne Termin, im Datenbereich."""
    tag0 = B0 + timedelta(hours=h)
    kand = []
    for d in range(-400, 401):
        t = tag0 + timedelta(days=d)
        if t.weekday() >= 5 or d == 0:
            continue
        if any((t.date() + timedelta(days=x)) in alle_tage for x in (-1, 0, 1)):
            continue
        kand.append(h + 24 * d)
    kand = np.array(kand)
    return rng.choice(kand, size=n, replace=True)


print("P59 VORPRUEFUNG · Makro-Termine und Hebeltrade (Stufe 1)\n")
print("Termine: " + " · ".join("%s %d" % (a, len(v)) for a, v in TERM.items()))
print("BTC stuendlich %s bis %s\n" % (B0 + timedelta(hours=H0), B0 + timedelta(hours=H1)))

# ---------------- F1 Praemisse
print("F1 PRAEMISSE: BTC |Rendite| 2 h ab Termin gegen selbe Uhrzeit ohne Termin (10.000 Ziehungen)")
for art in ("cpi", "nfp", "fomc", "alle"):
    hs = [h for a in (TERM if art == "alle" else {art: TERM[art]}) for h in TERM[a] if H0 < h < H1 - 2]
    echt = np.nanmean([bew2(h) for h in hs])
    # Ersatzpool je Termin einmal, dann ziehen
    pool = [ersatz(h, 400, RNG) for h in hs]
    pw = np.array([[bew2(x) for x in p if H0 < x < H1 - 2][:300] for p in pool], dtype=object)
    ziehung = []
    for _ in range(10000):
        ziehung.append(np.nanmean([p[RNG.integers(len(p))] for p in pw]))
    ziehung = np.array(ziehung)
    p = 2 * min((ziehung >= echt).mean(), (ziehung <= echt).mean())
    print("   %-5s n %3d · Termin %.3f %% · ohne %.3f %% · Verhaeltnis %.2f · p %.4f"
          % (art, len(hs), 100 * echt, 100 * ziehung.mean(), echt / ziehung.mean(), max(p, 1e-4)))

# ---------------- F2 Hauptfrage
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
s = E.stunde.values.astype(np.int64)
B24 = ((E.t_d <= 24) & (E.t_d <= E.t_u)).values.astype(float)
A24 = ((E.t_u <= 24) & (E.t_u < E.t_d)).values.astype(float)
D24 = (E.t_d <= 24).values.astype(float)
JAHR = E.jahr.values
print("\nF2 HAUPTFRAGE: %d REGEL0-Einstiege %s · Basis B24 %.1f %% · A24 %.1f %% · D24 %.1f %%"
      % (len(E), dict(E.jahr.value_counts().sort_index()), 100 * B24.mean(), 100 * A24.mean(), 100 * D24.mean()))


def im_fenster(termine):
    t = np.sort(np.asarray(termine, np.int64))
    lo = np.searchsorted(t, s + 1, "left")
    hi = np.searchsorted(t, s + 25, "left")
    return hi > lo


def diff(maske, y):
    return y[maske].mean() - y[~maske].mean()


POOL = [ersatz(h, 2000, np.random.default_rng(590 + i)) for i, h in enumerate(h for a in TERM for h in TERM[a])]


def ersatz_termine(rng):
    """Je echtem Termin ein Ersatzzeitpunkt (Kandidaten je Termin einmal vorberechnet - selbe Uhrzeit, Werktag, ohne Termin)."""
    return [p[rng.integers(len(p))] for p in POOL]


def nullwelt(y, n, rng, pflanze=0.0):
    out = []
    for _ in range(n):
        m = im_fenster(ersatz_termine(rng))
        yy = y
        if pflanze:
            yy = y.copy()
            z = m & (yy == 0)
            yy[z & (rng.random(len(yy)) < pflanze / max(1e-9, 1 - y[m].mean()))] = 1.0
        out.append(diff(m, yy))
    return np.array(out)


ECHT = im_fenster([h for v in TERM.values() for h in v])
NULL = {}
for name, y in (("B24", B24), ("A24", A24), ("D24", D24)):
    d = diff(ECHT, y)
    nw = nullwelt(y, 2000, RNG)
    NULL[name] = nw
    p = 2 * min((nw >= d).mean(), (nw <= d).mean())
    print("   %s  im Fenster %.1f %% (n %d) · ohne %.1f %% · Unterschied %+.2f Pp · Nullband 5/95 %+.2f/%+.2f · p %.4f%s"
          % (name, 100 * y[ECHT].mean(), ECHT.sum(), 100 * y[~ECHT].mean(), 100 * d, 100 * np.percentile(nw, 5),
             100 * np.percentile(nw, 95), max(p, 5e-4), "" if name != "D24" else "  (Auskunft)"))

print("\n   je Art (Auskunft):")
for art in TERM:
    m = im_fenster(TERM[art])
    print("     %-5s Einstiege im Fenster %4d · B24 %+.2f Pp · A24 %+.2f Pp · D24 %+.2f Pp"
          % (art, m.sum(), 100 * diff(m, B24), 100 * diff(m, A24), 100 * diff(m, D24)))
print("   je Jahr (Auskunft, alle Termine):")
for j in (2024, 2025, 2026):
    w = JAHR == j
    m = ECHT[w]
    print("     %d  im Fenster %4d von %5d · B24 %+.2f Pp · A24 %+.2f Pp · D24 %+.2f Pp"
          % (j, m.sum(), w.sum(), 100 * diff(m, B24[w]), 100 * diff(m, A24[w]), 100 * diff(m, D24[w])))

# ---------------- Selbsttest
print("\nSELBSTTEST (Ersatztermine als 'echt', 200 Laeufe gegen je 300 Nullziehungen):")
for name, y in (("B24", B24), ("A24", A24)):
    treffer = 0
    for _ in range(200):
        d = diff(im_fenster(ersatz_termine(RNG)), y)
        nw = NULL[name][RNG.choice(len(NULL[name]), 300, replace=False)]
        p = 2 * min((nw >= d).mean(), (nw <= d).mean())
        treffer += p < 0.05
    print("   %s  Anteil p < 0,05: %.1f %% (Sollband 1-10 %%)" % (name, 100 * treffer / 200))
print("   Aufloesung B24 (Fundquote bei p < 0,025, 50 Laeufe je d):")
for dd in (0.02, 0.04, 0.06, 0.08):
    fund = 0
    for _ in range(50):
        m = im_fenster(ersatz_termine(RNG))
        yy = B24.copy()
        z = m & (yy == 0)
        yy[z & (RNG.random(len(yy)) < dd / max(1e-9, 1 - B24[m].mean()))] = 1.0
        d = diff(m, yy)
        p = 2 * min((NULL["B24"] >= d).mean(), (NULL["B24"] <= d).mean())
        fund += p < 0.025
    print("     +%.0f Pp  Fundquote %d %%" % (100 * dd, 2 * fund))

# ---------------- F3 Auskunft
print("\nF3 AUSKUNFT: BTC 2 h ab CPI gegen Tagesaenderung DGS2 am CPI-Tag (Rangkorrelation, Vorzeichen: Rendite hoch = Ueberraschung inflationaer)")
dg = pd.Series({d: v for d, v in T["dgs2"]})
dg.index = pd.to_datetime(dg.index)
ddg = dg.diff()
zeilen = []
for h in TERM["cpi"]:
    tag = pd.Timestamp((B0 + timedelta(hours=h)).date())
    if tag in ddg.index and H0 < h < H1 - 2:
        i = h - H0
        zeilen.append((tag.year, lc[i + 1] - lc[i - 1], ddg[tag]))
Z = pd.DataFrame(zeilen, columns=["jahr", "btc", "ddgs2"]).dropna()
for j, g in Z.groupby("jahr"):
    r = spearmanr(g.btc, g.ddgs2).correlation if len(g) > 3 else np.nan
    print("   %d  n %2d · rho %+.2f · mittlere |BTC 2 h| %.2f %% · mittlere |dDGS2| %.3f Pp"
          % (j, len(g), r, 100 * g.btc.abs().mean(), g.ddgs2.abs().mean()))
r = spearmanr(Z.btc, Z.ddgs2).correlation
print("   alle n %d · rho %+.2f" % (len(Z), r))
last = Z.tail(3)
print("   letzte CPI-Tage im Datenbestand: " + " · ".join("BTC %+.2f %% / DGS2 %+.3f" % (100 * a, b) for a, b in zip(last.btc, last.ddgs2)))
