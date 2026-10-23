"""P69 MESSPLAN M-L FASSUNG 1b (Voranalyse_REGEL0_Kosten_23_10.md §7/§7.1, vorab e6e30261; Selbsttest einseitig): Limit-Einstieg fuer REGEL0 auf Bitpanda/Fusion.

    python Basisinfos/Rechenkern_02_10/p69_ml_limit.py

Ablauf: (1) SELBSTTEST (Zufallspfad brutto ~0, Positivkontrolle Rueckkehr > 0) - sonst Abbruch; (2) Wahl der Tiefe auf 2024 je Kostenbasis
nach Gesamtertrag je Signal; (3) Bestaetigung 2025 und 2026 getrennt, vier Mengen, Nullwelt (zufaellige Stunden derselben Coins im selben Jahr).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import p64_lc_voranalyse as P  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
TIEFEN = (0.005, 0.01, 0.015, 0.02)
GUELTIG = 4
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
UNV = MENGEN[1:]
BASEN = {"H": 0.0048, "H+Schlupf": 0.0058, "S": 0.0050}
ZIEH = 200
KAT = set(pd.read_csv(os.path.join("data", "_spot", "bitpanda_katalog_krypto_2026-10-08.csv"), sep=";").symbol.str.upper())


# ── (1) Selbsttest ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def kunst(n, rueck, saat):
    """n Pfade: 28 Stunden zu je 60 Teilschritten, Preis-Martingal (Zufallspfad) oder Rueckkehr zur Mitte (OU auf dem Log-Kurs)."""
    rng = np.random.default_rng(saat)
    s = 0.005 / np.sqrt(60)
    z = rng.standard_t(4, (n, 28 * 60)) / np.sqrt(2.0) * s
    if not rueck:
        p = np.cumprod(1 + z, axis=1)
    else:
        lp = np.zeros((n, 28 * 60))
        for t in range(1, 28 * 60):
            lp[:, t] = lp[:, t - 1] * (1 - 1 / (12 * 60)) + z[:, t]
        p = np.exp(lp)
    h = p.reshape(n, 28, 60)
    return h[:, :, -1], h.min(axis=2)          # Stundenschluss, Stundentief (Stunde 0 = Einstiegsstunde)


def limit_brutto(C, L, x, w=GUELTIG):
    lim = C[:, 0] * (1 - x)
    g = L[:, 1:w + 1].min(axis=1) <= lim
    return (C[g, 24] / lim[g] - 1).mean(), g.mean()


def selbsttest():
    C, L = kunst(200000, False, 1)
    Cr, Lr = kunst(60000, True, 2)
    ok = True
    for x in TIEFEN:
        m, f = limit_brutto(C, L, x)
        mr, fr = limit_brutto(Cr, Lr, x)
        ok &= m < 0.0003 and mr > 0      # Fassung 1b (§7.1): einseitig - das Minus ist das echte Ueberschiessen unter das Limit
        print("  Selbsttest Tiefe %.1f %%: Zufallspfad brutto %+.4f %% (gefuellt %.0f %%) · Rueckkehr %+.4f %% (gefuellt %.0f %%)"
              % (100 * x, 100 * m, 100 * f, 100 * mr, 100 * fr))
    print("  SELBSTTEST %s\n" % ("BESTANDEN" if ok else "NICHT BESTANDEN"))
    return ok


# ── (2)/(3) Messung ─────────────────────────────────────────────────────────────────────────────────────────────────────────
_r = {}


def reihe(s):
    if s not in _r:
        x = P.reihe(s)
        if x is None:
            _r[s] = None
        else:
            a, L, C = x
            n = len(C)
            fmin = np.full(n, np.nan)
            if n > GUELTIG + 1:
                from numpy.lib.stride_tricks import sliding_window_view
                w = sliding_window_view(L[1:], GUELTIG)
                fmin[:len(w)] = np.where(np.isfinite(w).all(axis=1), w.min(axis=1), np.nan)
            c24 = np.full(n, np.nan)
            c24[:n - 24] = C[24:]
            jahr = (P.B0 + pd.to_timedelta(np.arange(n) + a, unit="h")).year.to_numpy()
            ok = np.isfinite(C) & np.isfinite(fmin) & np.isfinite(c24)
            _r[s] = (a, C, fmin, c24, jahr, ok)
    return _r[s]


def einstiege(menge):
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    z = []
    for s, st, j in zip(E.symbol, E.stunde, E.jahr):
        x = reihe(s)
        if x is None:
            continue
        a, C, fmin, c24, jahr, ok = x
        i = int(st) - a
        if 0 <= i < len(C) and ok[i]:
            z.append((s, int(j), C[i], fmin[i], c24[i]))
    return pd.DataFrame(z, columns=["symbol", "jahr", "c0", "fmin", "c24"])


def netto(D, x, kosten):
    lim = D.c0 * (1 - x)
    g = D.fmin <= lim
    r = (D.c24 / lim - 1 - kosten).where(g)
    return r


def nullwelt(D, x, kosten, saat):
    """je Signal eine Zufallsstunde desselben Coins im selben Jahr; Rueckgabe: Netto je gefuelltem Handel je Ziehung (ZIEH Werte)."""
    rng = np.random.default_rng(saat)
    werte = np.zeros(ZIEH)
    anz = np.zeros(ZIEH)
    for (s, j), grp in D.groupby(["symbol", "jahr"]):
        a, C, fmin, c24, jahr, ok = reihe(s)
        kand = np.flatnonzero(ok & (jahr == j))
        if len(kand) == 0:
            continue
        idx = rng.choice(kand, (ZIEH, len(grp)))
        lim = C[idx] * (1 - x)
        g = fmin[idx] <= lim
        r = np.where(g, c24[idx] / lim - 1 - kosten, 0.0)
        werte += r.sum(axis=1)
        anz += g.sum(axis=1)
    return werte / np.maximum(anz, 1)


def main():
    print("P69 M-L LIMIT-EINSTIEG · Tiefen %s · Gueltigkeit %d h · Kostenbasen %s\n" % (TIEFEN, GUELTIG, BASEN))
    if not selbsttest():
        print("Selbsttest nicht bestanden - es wird NICHT gemessen (§7).")
        return
    E = {m: einstiege(m) for m in MENGEN}
    for m in MENGEN:
        print("  %s: %d Einstiege mit vollem Fenster (2024 %d · 2025 %d · 2026 %d)" % (m, len(E[m]), *(int((E[m].jahr == j).sum()) for j in (2024, 2025, 2026))))
    print()
    for basis, kosten in BASEN.items():
        Eb = {m: (E[m][E[m].symbol.isin(KAT)] if basis == "S" else E[m]) for m in MENGEN}
        # Wahl 2024
        ges = {}
        for x in TIEFEN:
            ges[x] = np.mean([netto(Eb[m][Eb[m].jahr == 2024], x, kosten).fillna(0).mean() for m in MENGEN])
        wahl = max(ges, key=ges.get)
        print("=== Basis %s (Kosten %.2f %%) · WAHL 2024 nach Gesamtertrag je Signal: %s -> gewaehlt %.1f %%"
              % (basis, 100 * kosten, " · ".join("%.1f %% %+.3f" % (100 * x, 100 * v) for x, v in ges.items()), 100 * wahl))
        traegt = True
        for j in (2025, 2026):
            for m in MENGEN:
                D = Eb[m][Eb[m].jahr == j]
                r = netto(D, wahl, kosten)
                nw = nullwelt(D, wahl, kosten, saat=hash((basis, m, j)) % 2 ** 32)
                rang = float(np.mean(nw < r.mean()))
                ohne = (D.c24 / D.c0 - 1 - kosten).mean()
                if m in UNV:
                    traegt &= (r.mean() > 0) and (rang >= 0.90)
                print("  %d %-13s netto je gefuelltem Handel %+.3f %% (gefuellt %.0f %%, ohne Limit %+.3f) · Gesamtertrag je Signal %+.3f · Nullwelt %+.3f [P10 %+.3f; P90 %+.3f] · Rang %.2f"
                      % (j, m, 100 * r.mean(), 100 * r.notna().mean(), 100 * ohne, 100 * r.fillna(0).mean(), 100 * nw.mean(),
                         100 * np.percentile(nw, 10), 100 * np.percentile(nw, 90), rang))
        print("  URTEIL Basis %s: %s\n" % (basis, "TRAEGT" if traegt else "TRAEGT NICHT"))
    print("Auskunft Gueltigkeit (Basis H, Tiefe 1 %, unverzerrt_1, alle Jahre) - siehe p69_gegenprobe.py")


if __name__ == "__main__":
    main()
