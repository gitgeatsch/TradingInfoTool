"""P101 Selbsttest zu Messplan H-1 Fassung 2 §6 - VOR dem ersten Blick. Nur lesend; gibt KEIN echtes Ergebnis aus.

    python -X utf8 Basisinfos/Rechenkern_02_10/p101_h1_selbsttest.py

Echte Renditen 2025-26, KUENSTLICHE Zustaende (der echte Zustand wird nur fuer seinen Anteil gelesen):
  S1 Fehlalarm   Zustand zufaellig je Einstieg (Anteil wie echt)                         Soll: TRAEGT <= 5 %
  S2 Ballung     Anteil je 15-T-Block 10 % oder 50 % (Regime), je Einstieg gezogen        Soll: TRAEGT <= 5 %
  S3 Aufloesung  S1-Zustand, gepflanzt Delta += k fuer Zustand 1, k = 0,1/0,25/0,5/1/2 %  -> Fundquote, X = kleinstes k >= 80 %
  D  Orakel      Zustand := Delta > 0 (Zukunftswissen)                                    Soll: TRAEGT (hoeher) in 100 %
H-1b: Deltas D72/D120/DF mit Anteil von a; H-1c: D6/D72 mit Anteil von extrem. Band nach Bonferroni (3 bzw. 2 Hypothesen).
Ausgabe: Quoten je Menge; X je Menge und Hypothese nach data/_h1/aufloesung.json (fuer die Messung, Stufe TRAEGT NICHT BIS X).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p101_h1_basis as B  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

N_S1, N_S2, N_S3, N_D = 1000, 1000, 50, 20   # Fehlalarm mit 1.000 Ziehungen (Projektstandard 11.10., Lehre B4)
KS = (0.001, 0.0025, 0.005, 0.01, 0.02)


def ALPHA_H(nh):
    """Nennniveau je Hypothese (zweiseitig, Bonferroni) - erwartete Fehlalarmquote."""
    return B.ALPHA / nh


def quote(tag, deltas, hyp, welt, n, rng, k=0.0, richtung=+1):
    """Anteil der Welten mit TRAEGT (richtung=+1: nur 'HOEHER' zaehlt bei Pflanzung; 0: beide Richtungen)."""
    t = 0
    for _ in range(n):
        z = welt(rng)
        d = deltas + k * z
        st = B.bewerte(tag, z, d, rng, hyp)["stufe"]
        if st.startswith("TRAEGT (") and (richtung == 0 or "HOEHER" in st):
            t += 1
    return t / n


def main():
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(20261028)
    print("P101 SELBSTTEST H-1 (Fassung 4: Log-Differenz, t-Band ueber Bloecke) · echte Renditen 2025-26, kuenstliche Zustaende · KEIN echtes Ergebnis\n")
    X = {}
    durch = []
    for menge in B.MENGEN:
        D = B.tabelle(menge)
        U = D[D.jahr >= 2025].reset_index(drop=True)
        tag = U.tag.to_numpy()
        bl = (tag - tag.min()) // B.N._block(5)
        X[menge] = {}
        print("=" * 104)
        print(menge)
        for teil, hyps, zst in (("H-1b", B.H1B, "a"), ("H-1c", B.H1C, "extrem")):
            p = float(U[zst].mean())
            nh = len(hyps)
            for name, lang, kurz in hyps:
                d = B.delta(U, lang, kurz)
                ok = np.isfinite(d)
                tg, dd, bb = tag[ok], d[ok], bl[ok]
                n = len(tg)
                s1 = lambda r: (r.random(n) < p).astype(float)                                  # noqa: E731

                def s2(r, bb=bb, n=n):
                    ub = np.unique(bb)
                    pb = dict(zip(ub, np.where(r.random(len(ub)) < 0.5, 0.10, 0.50)))
                    return (r.random(n) < np.array([pb[x] for x in bb])).astype(float)
                q1 = quote(tg, dd, nh, s1, N_S1, rng, richtung=0)
                q2 = quote(tg, dd, nh, s2, N_S2, rng, richtung=0)
                fund = {k: quote(tg, dd, nh, s1, N_S3, rng, k=k) for k in KS}
                xk = next((k for k in KS if fund[k] >= 0.8), None)
                qd = quote(tg, dd, nh, lambda r, dd=dd: (dd > 0).astype(float), N_D, rng)
                X[menge]["%s_%s" % (teil, name)] = xk
                fehler = []
                if q1 > 0.05:
                    fehler.append("S1")
                if q2 > 0.05:
                    fehler.append("S2")
                if qd < 1.0:
                    fehler.append("D")
                if xk is None:
                    fehler.append("S3 ohne Aufloesung")
                durch += ["%s %s %s %s" % (menge, teil, name, f) for f in fehler]
                streng = ALPHA_H(nh) + 2 * np.sqrt(ALPHA_H(nh) * (1 - ALPHA_H(nh)) / N_S1)
                print("   %s %-5s Anteil %4.1f %% · S1 Fehlalarm %4.1f %% · S2 Ballung %4.1f %% (Soll <= 5 %%; Stufung streng <= %.1f %%: %s) · "
                      "D Orakel %3.0f %% · S3 Fundquote %s -> X = %s  %s" % (
                          teil, name, 100 * p, 100 * q1, 100 * q2, 100 * streng, "✔" if max(q1, q2) <= streng else "ueber", 100 * qd,
                          " ".join("%.2f:%.0f%%" % (100 * k, 100 * v) for k, v in fund.items()),
                          "%.2f Pp" % (100 * xk) if xk else "keine", "✔" if not fehler else "✖ " + ",".join(fehler)))
    os.makedirs(B.ABLAGE, exist_ok=True)
    with open(os.path.join(B.ABLAGE, "aufloesung.json"), "w", encoding="utf-8") as f:
        json.dump(X, f, indent=1)
    nachher = B.fingerabdruck()
    print("\nSeiteneffekt Produktionsdatei: %s" % ("✔ unveraendert" if vorher == nachher else "✖ VERAENDERT"))
    print("SELBSTTEST: %s" % ("✔ BESTANDEN - Messung darf laufen" if not durch else "✖ NICHT BESTANDEN: " + "; ".join(durch)))
    return 1 if (durch or vorher != nachher) else 0


if __name__ == "__main__":
    sys.exit(main())
