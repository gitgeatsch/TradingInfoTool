"""P82 GEGENPROBE (24.10.2026): die drei tragenden Aussagen der Voranalyse Robustheit auf einem zweiten Weg.

    python -X utf8 Basisinfos/Rechenkern_02_10/p82_gegenprobe.py

G1  tau2 = 0 in der Referenz in allen Monaten, lang nicht: aus der EIGENEN Ausgabe des Erzeugers (Kommandozeile, 'Schrumpfung kausal')
G2  Rauschen anders gerechnet: Bootstrap ueber EINZELNE Tage (statt 7-Tage-Bloecke) und t-Test der Tagesdifferenz auf gemeinsamen Tagen
G3  Gruppe c (ohne fruehere Kurse): ihre Stundenkurse sind in data/ und data/_hist zeilengleich (dann kommen ihre geaenderten
    Einstiege aus dem Querschnitt - Modell, Schrumpfung - und nicht aus der eigenen Reihe)
"""
import hashlib
import os
import re
import sqlite3
import subprocess
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
import p79_f1_fg_gier as P79  # noqa: E402

GR = os.path.join("data", "_vergleich", "kern48jbz_gruppe_bestand.csv")


def g1():
    import tempfile
    import wegwerf
    T = tempfile.mkdtemp(prefix="p82g_")
    out = {}
    for name, ordner in (("Referenz", "data"), ("lang", os.path.join("data", "_hist"))):
        z = os.path.join(T, "%s.csv" % name)
        r = subprocess.run([sys.executable, "-X", "utf8", "-m", "agent.regel0_rechnung", "--nachrechnung", "--ordner", ordner,
                            "--zusatz-aus", GR, "--ziel", z], capture_output=True, text=True)
        m = re.search(r"tau2 = 0 in (\d+) von (\d+) Monaten", r.stdout)
        out[name] = (int(m.group(1)), int(m.group(2))) if m else None
    wegwerf.aufraeumen(T)
    ok = out["Referenz"] and out["Referenz"][0] == out["Referenz"][1] and out["lang"] and out["lang"][0] < out["lang"][1]
    print("G1 tau2 = 0 (Erzeuger-Ausgabe): Referenz %s von %s · lang %s von %s -> %s" % (
        *(out["Referenz"] or ("?", "?")), *(out["lang"] or ("?", "?")), "ok" if ok else "NICHT OK"))
    return bool(ok)


def g2():
    tage = pd.date_range("2024-01-01", "2026-08-31", freq="D")
    P79.TAGE = tage
    a = pd.read_csv(os.path.join("data", "_hist", "einstiege_A.csv"), sep=";")
    b = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
    sr, nr, _ = P79.tagesreihe(b)
    sl, nl, _ = P79.tagesreihe(a)
    rng = np.random.default_rng(821)
    z = np.empty((2000, 2))
    for i in range(2000):
        ix = rng.integers(0, len(tage), len(tage))
        z[i] = sr[ix].sum() / nr[ix].sum(), sl[ix].sum() / nl[ix].sum() - sr[ix].sum() / nr[ix].sum()
    gem = (nr > 0) & (nl > 0)
    d = sl[gem] / nl[gem] - sr[gem] / nr[gem]
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    lo_r, hi_r = np.percentile(z[:, 0], [2.5, 97.5])
    lo_d, hi_d = np.percentile(z[:, 1], [2.5, 97.5])
    ok = lo_r < 0 < hi_r and hi_d < 0 and t < -2
    print("G2 Einzeltag-Bootstrap: Referenz [%+.3f; %+.3f] %% (schliesst 0 ein) · Differenz [%+.3f; %+.3f] %% · t-Test Tagesdifferenz "
          "(gleich gewichtete Tage, %d gemeinsame) Mittel %+.3f %%, t = %.2f -> %s" % (
              100 * lo_r, 100 * hi_r, 100 * lo_d, 100 * hi_d, gem.sum(), 100 * d.mean(), t, "ok" if ok else "NICHT OK"))
    return bool(ok)


def g3():
    ca = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
    cb = sqlite3.connect("file:data/_hist/stundenkurse.db?mode=ro", uri=True)
    erst = dict(ca.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol").fetchall())
    lang = dict(cb.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol").fetchall())
    c = [s for s in erst if lang[s] == erst[s]]
    abw = []
    for s in c:
        h = []
        for con in (ca, cb):
            m = hashlib.sha256()
            for r in con.execute("SELECT stunde, open, high, low, close FROM stundenkurse WHERE symbol=? ORDER BY stunde", (s,)):
                m.update(repr(r).encode())
            h.append(m.hexdigest())
        if h[0] != h[1]:
            abw.append(s)
    print("G3 Symbole ohne fruehere Kurse (Datenbeginn gleich): %d · Kursreihe zeilengleich in beiden Dateien: %d · abweichend: %s -> %s" % (
        len(c), len(c) - len(abw), abw or "keine", "ok" if not abw else "NICHT OK"))
    return not abw


def main():
    print("P82 GEGENPROBE Voranalyse Robustheit REGEL0")
    e = [g1(), g2(), g3()]
    print("ERGEBNIS %d von 3" % sum(e))


if __name__ == "__main__":
    main()
