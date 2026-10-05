"""N4 (05.10.2026, Nutzer: *wenn sich bereits ein eindeutiges Ergebnis abzeichnet, Zeit in Anpassungen stecken statt weiter zu messen*):
die ZWISCHENENTSCHEIDE vorab festlegen und gegen BEKANNTE WAHRHEIT eichen, bevor ein Aufruf faellt.

    python Basisinfos/Rechenkern_02_10/n4_sequenz_selbsttest.py

Echte Anker der Entwicklungsmenge in der Reihenfolge des Laeufers (n4_rueckspiel.reihenfolge), echte 24-h-Ertraege, SIMULIERTE Urteile
(stuetzt 10 %, neutral 45 %, spricht dagegen 45 %, gepflanzte Staerke k). Blicke nach 250, 500, 750 und 1.000 Ankern (je Jahr die Haelfte).

Je Jahr: z = (Unterschied stuetzt - dagegen  -  Mittel der Nullwelt) / Streuung der Nullwelt, Nullwelt = Vertauschen innerhalb des Tages
(R1, wie die Hauptregel). Gepoolt: z_p = (z_2025 + z_2026) / sqrt(2).

Regeln (Kandidaten, je Blick):
  ABBRUCH-ANPASSEN  z_p <= Grenze(Blick)  -> der Trader trennt erkennbar nicht: Zeit in Anpassungen
  ABBRUCH-TRAEGT    p < 0,001 in BEIDEN Jahren (Haybittle-Peto) -> weiter zur Bestaetigung
  sonst WEITER; nach 1.000 gilt die Hauptregel R1 (je Jahr ueber dem 95. Perzentil)
Geeicht wird: P(ABBRUCH-ANPASSEN | k = 0,3) <= 5 % (ein Effekt, den N4 sicher finden kann, darf nicht verworfen werden),
und P(ABBRUCH-ANPASSEN | k = 0) moeglichst gross (Zeit sparen).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from n4_rueckspiel import lade_anker, reihenfolge          # noqa: E402

RNG = np.random.default_rng(20261006)
WELTEN, PERM = int(os.environ.get("N4_SEQ_WELTEN", "300")), 200
NUR = os.environ.get("N4_SEQ_NUR")                          # Nachpruefung eines Kandidaten bei einer Staerke, z. B. "A:0.3"
BLICKE = (250, 500, 750, 1000)
KANDIDATEN = {"A (-0,5 / 0,0 / 0,5)": (-0.5, 0.0, 0.5), "B (-1,0 / -0,5 / 0,0)": (-1.0, -0.5, 0.0), "C (0,0 / 0,5 / 1,0)": (0.0, 0.5, 1.0),
              "D (-1,0 / 0,0 / 0,5)": (-1.0, 0.0, 0.5)}   # D nach der Nachpruefung von A (A: 5,3 % bei 1.000 Welten, Risiko nur bei Blick 250)

a = reihenfolge(lade_anker())
s = pd.read_csv("data/_vergleich/b0_spur_bestand.csv", sep=";")[["symbol", "std", "spot"]]
a = a.merge(s, on=["symbol", "std"], how="left")
assert a["spot"].notna().all()
a["tag"] = pd.to_datetime(a["signalstunde_utc"]).dt.date.astype(str)
R = a["spot"].values
J = a["jahr"].values
T = a["tag"].values


def z_jahr(r, lab, tage):
    def st(l):
        a1, a2 = r[l == 1], r[l == -1]
        return a1.mean() - a2.mean() if len(a1) > 1 and len(a2) > 1 else 0.0
    s0 = st(lab)
    gr = [np.where(tage == t)[0] for t in np.unique(tage)]
    nul = []
    for _ in range(PERM):
        p = np.arange(len(r))
        for ix in gr:
            if len(ix) > 1:
                p[ix] = RNG.permutation(ix)
        nul.append(st(lab[p]))
    nul = np.array(nul)
    sd = nul.std() or 1e-9
    return (s0 - nul.mean()) / sd, float(np.mean(nul >= s0))


def welt(k):
    z = (R - R.mean()) / R.std()
    lat = k * z + RNG.standard_normal(len(R))
    out = np.zeros(len(R), int)
    for j in np.unique(J):                                   # Quote je Jahr wie in der Kalibrierung
        m = J == j
        q90, q45 = np.quantile(lat[m], [0.90, 0.45])
        out[m] = np.where(lat[m] >= q90, 1, np.where(lat[m] <= q45, -1, 0))
    return out


def lauf(k, grenzen):
    lab = welt(k)
    for b, g in zip(BLICKE, list(grenzen) + [None]):
        zs, ps = [], []
        for j in np.unique(J):
            m = (J[:b] == j)
            z, p = z_jahr(R[:b][m], lab[:b][m], T[:b][m])
            zs.append(z); ps.append(p)
        zp = sum(zs) / np.sqrt(len(zs))
        if b < 1000:
            if max(ps) < 0.001:
                return "traegt_frueh", b
            if zp <= g:
                return "anpassen", b
        else:
            return ("traegt" if max(ps) < 0.05 else "traegt_nicht"), b


print("N4 Zwischenentscheide - Eichung gegen bekannte Wahrheit (%d Welten je Stärke, %d Vertauschungen, Blicke %s)" % (WELTEN, PERM, BLICKE))
for name, gr in KANDIDATEN.items():
    if NUR and not name.startswith(NUR.split(":")[0]):
        continue
    print("\nKandidat %s" % name)
    print("  k     | Abbruch ANPASSEN (Blick 250/500/750) | Abbruch TRAEGT frueh | am Ende traegt | am Ende traegt nicht | mittlere Anker")
    for k in ((float(NUR.split(":")[1]),) if NUR and ":" in NUR else (0.0, 0.1, 0.2, 0.3)):
        erg = [lauf(k, gr) for _ in range(WELTEN)]
        an = [b for e, b in erg if e == "anpassen"]
        print("  %.1f   | %5.1f %%  (%3.0f / %3.0f / %3.0f %%)           | %6.1f %%            | %6.1f %%        | %6.1f %%              | %4.0f" % (
            k, 100 * len(an) / WELTEN, *(100 * sum(1 for b in an if b == x) / WELTEN for x in BLICKE[:3]),
            100 * sum(1 for e, _ in erg if e == "traegt_frueh") / WELTEN, 100 * sum(1 for e, _ in erg if e == "traegt") / WELTEN,
            100 * sum(1 for e, _ in erg if e == "traegt_nicht") / WELTEN, np.mean([b for _, b in erg])))
