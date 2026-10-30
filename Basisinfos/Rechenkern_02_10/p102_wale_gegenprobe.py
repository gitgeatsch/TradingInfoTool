# -*- coding: utf-8 -*-
"""GEGENPROBE Messplan W §7 — ZWEITER Rechenweg, ohne ``p102_wale_basis``-Rechnung (nur dessen Konstanten und Datei-Pfad).

    E       je Tag eigene Schleife: G/R aus den Klassen absteigend, OLS über die Normalgleichungen (3x3, eigene Summen)
    L       Perzentile von Hand (lineare Interpolation, Typ 7) statt np.quantile
    D       Schleife über die Tage
    Band    Block-BOOTSTRAP (2.000 Ziehungen, Perzentile) statt t-Band — andere Methode, ähnliche Breite erwartet
    Vorgriff  zwei Mutationen (OLS mit Tag t im Fenster; Rang mit Tag t im Fenster) müssen von der Messung ABWEICHEN

    python -X utf8 Basisinfos/Rechenkern_02_10/p102_wale_gegenprobe.py
"""
import math
import os
import socket
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p102_wale_basis as B  # noqa: E402  (nur Konstanten, Pfade, und zum Vergleich die Ergebnisse)

AUSGABE = os.path.join(B.HIER, "p102_wale_gegenprobe.txt")


def g_r_schleife(con, symbol, markt, tg, q):
    g, r = [], []
    for d in tg:
        z = con.execute("SELECT klasse, SUM(CASE WHEN seite='kauf' THEN usd ELSE 0 END), SUM(CASE WHEN seite='verkauf' THEN usd ELSE 0 END)"
                        " FROM verteilung WHERE symbol=? AND markt=? AND datum=? AND einheit='sweep' GROUP BY klasse ORDER BY klasse DESC",
                        (symbol, markt, d.isoformat())).fetchall()
        if not z:
            g.append(float("nan")); r.append(float("nan")); continue
        ges = sum(k + v for _, k, v in z)
        netto = sum(k - v for _, k, v in z)
        kum = gross = 0.0
        for _, k, v in z:
            kum += k + v
            gross += k - v
            if kum >= q * ges:
                break
        g.append(gross / ges); r.append((netto - gross) / ges)
    return g, r


def kurs(con, symbol, d, stunde):
    t = int(datetime(d.year, d.month, d.day, stunde, tzinfo=timezone.utc).timestamp() * 1000)
    x = con.execute("SELECT eroeffnung FROM kurs WHERE symbol=? AND ts=?", (symbol, t)).fetchone()
    return x[0] if x else None


def ols3(zeilen):
    """b aus den Normalgleichungen; zeilen = [(1, R, r, G)]."""
    A = [[0.0] * 3 for _ in range(3)]
    c = [0.0] * 3
    for x0, x1, x2, yy in zeilen:
        x = (x0, x1, x2)
        for i in range(3):
            c[i] += x[i] * yy
            for j in range(3):
                A[i][j] += x[i] * x[j]
    return np.linalg.solve(np.array(A), np.array(c))


def perzentil(werte, p):
    v = sorted(werte)
    h = (len(v) - 1) * p
    lo = math.floor(h)
    return v[lo] + (h - lo) * (v[min(lo + 1, len(v) - 1)] - v[lo])


def e_und_l(g, r, bew, mutation=None):
    n = len(g)
    e = [float("nan")] * n
    for t in range(n):
        if not all(math.isfinite(v) for v in (g[t], r[t], bew[t])):
            continue
        hi = t + 1 if mutation == "ols" else t                     # Mutation: Tag t im eigenen Schätzfenster (Vorgriff)
        zeilen = [(1.0, r[i], bew[i], g[i]) for i in range(max(0, t - B.FENSTER_B), hi)
                  if all(math.isfinite(v) for v in (g[i], r[i], bew[i]))]
        if len(zeilen) < B.MIN_BEOB:
            continue
        b = ols3(zeilen)
        e[t] = g[t] - (b[0] + b[1] * r[t] + b[2] * bew[t])
    lab = [float("nan")] * n
    for t in range(n):
        if not math.isfinite(e[t]):
            continue
        hi = t + 1 if mutation == "rang" else t
        v = [x for x in e[max(0, t - B.FENSTER_RANG):hi] if math.isfinite(x)]
        if len(v) < B.MIN_BEOB:
            continue
        lo_, hi_ = perzentil(v, 0.2), perzentil(v, 0.8)
        lab[t] = 1.0 if e[t] > hi_ else (-1.0 if e[t] < lo_ else 0.0)
    return e, lab


def d_schleife(lab, y):
    so = su = 0.0
    no = nu = 0
    for a, b in zip(lab, y):
        if not (math.isfinite(a) and math.isfinite(b)):
            continue
        if a == 1:
            so += b; no += 1
        elif a == -1:
            su += b; nu += 1
    return so / no - su / nu if no and nu else float("nan")


def bootstrap(lab, y, block, alpha, rng, n=2000):
    bl = {}
    for i, (a, b) in enumerate(zip(lab, y)):
        if math.isfinite(a) and math.isfinite(b) and a != 0:
            bl.setdefault(i // block, []).append((a, b))
    keys = list(bl)
    w = []
    for _ in range(n):
        z = [x for k in rng.choice(len(keys), len(keys)) for x in bl[keys[k]]]
        o = [b for a, b in z if a == 1]; u = [b for a, b in z if a == -1]
        if o and u:
            w.append(sum(o) / len(o) - sum(u) / len(u))
    return float(np.quantile(w, alpha / 2)), float(np.quantile(w, 1 - alpha / 2))


def main() -> int:
    global AUSGABE
    if "--fassung3" in sys.argv:                                  # Messplan W Fassung 3 (vorab d5df61fb)
        B.fassung3()
        AUSGABE = AUSGABE.replace(".txt", "_f3.txt")
    elif "--fassung4" in sys.argv:                                # Fassung 4 (vorab 1924c5b4): sechs Altcoins, gepoolt
        B.fassung4()
        AUSGABE = AUSGABE.replace(".txt", "_f4.txt")
    pool = {}                                                     # h -> [(lab im Fenster, y im Fenster)] je Wert, zweiter Weg
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(7)
    tg, aus = B.lade()
    con = B.ro()
    z = ["GEGENPROBE Messplan W%s (%s, %s) — zweiter Rechenweg, q 5 %%, Urteilsfenster je Wert"
         % (" FASSUNG 3" if B.EINSEITIG else "", socket.gethostname(), datetime.now().isoformat(timespec="seconds"))]
    ok = True
    for s in B.SYMBOLE:
        w = [B.urteil(s)[0] <= d <= B.urteil(s)[1] for d in tg]
        px0 = [kurs(con, s, d, 0) for d in tg + [tg[-1] + timedelta(days=i) for i in range(1, 10)]]
        bew = [math.log(px0[i + 1] / px0[i]) if px0[i] and px0[i + 1] else float("nan") for i in range(len(tg))]
        for m in B.MAERKTE:
            g, r = g_r_schleife(con, s, m, tg, B.Q_HAUPT)
            e, lab = e_und_l(g, r, bew)
            _, _, e_v, lab_v = aus[s]["markt"][m][B.Q_HAUPT]
            fe = np.isfinite(e_v) & np.isfinite(np.array(e))
            de = float(np.max(np.abs(e_v[fe] - np.array(e)[fe]))) if fe.any() else float("nan")
            gleich = float(np.mean([(a == b) or (math.isnan(a) and math.isnan(b)) for a, b in zip(lab, lab_v)]))
            gut = de < 1e-9 and gleich == 1.0 and (np.isnan(e_v) == np.isnan(np.array(e))).all()
            z.append("\n%s %-7s E: größte Abweichung %.1e · Fünftel gleich %.4f · %s" % (s, m, de, gleich, "✔" if gut else "✖"))
            ok &= gut
            for mut in ("ols", "rang"):
                _, lab_m = e_und_l(g, r, bew, mut)
                anders = sum(1 for a, b in zip(lab_m, lab_v) if not ((a == b) or (math.isnan(a) and math.isnan(b))))
                z.append("   Vorgriff-Mutation %-4s: %d Tage mit anderem Fünftel %s" % (mut, anders, "✔ erkannt" if anders else "✖ NICHT erkannt"))
                ok &= anders > 0
            for h in B.HORIZONTE:
                y = [math.log(px0[i + 1 + h] / px0[i + 1]) if px0[i + 1] and px0[i + 1 + h] else float("nan") for i in range(len(tg))]
                lw = [lab[i] for i in range(len(tg)) if w[i]]
                yw = [y[i] for i in range(len(tg)) if w[i]]
                d = d_schleife(lw, yw)
                d_v = B.differenz(lab_v[np.array(w)], aus[s]["y"][(h, 0)][np.array(w)])
                u_v, o_v, nb = B.band(lab_v[np.array(w)], aus[s]["y"][(h, 0)][np.array(w)], B.N._block(h), B.ALPHA / B.HYPOTHESEN)
                bu, bo = bootstrap(lw, yw, B.N._block(h), B.ALPHA / B.HYPOTHESEN, rng)
                gut = abs(d - d_v) < 1e-12
                ok &= gut
                pool.setdefault(h, []).append((lw, yw))
                z.append("   H%d  D Schleife %+.4f Pp · Messung %+.4f Pp %s · t-Band Breite %.3f Pp · Bootstrap %.3f Pp (Verhältnis %.2f)"
                         % (h, 100 * d, 100 * d_v, "✔" if gut else "✖", 100 * (o_v - u_v), 100 * (bo - bu), (bo - bu) / (o_v - u_v)))
    if len(B.SYMBOLE) > 1 and B.EINSEITIG and B.HYPOTHESEN == 1:   # Fassung 4: GEPOOLT (Mittel der D, gemeinsame Blöcke)
        z.append("
GEPOOLT (%d Werte) — D als Mittel der Schleifen-D · Bootstrap über GEMEINSAME Blöcke gegen das t-Band" % len(B.SYMBOLE))
        for h, teile in sorted(pool.items()):
            d = sum(d_schleife(l, y) for l, y in teile) / len(teile)
            w = np.array([B.urteil(B.SYMBOLE[0])[0] <= x <= B.urteil(B.SYMBOLE[0])[1] for x in tg])
            labs_v = [aus[s]["markt"]["spot"][B.Q_HAUPT][3][w] for s in B.SYMBOLE]
            ys_v = [aus[s]["y"][(h, 0)][w] for s in B.SYMBOLE]
            d_v = B.differenz_gepoolt(labs_v, ys_v)
            u_v, o_v, _ = B.band_gepoolt(labs_v, ys_v, B.N._block(h), B.ALPHA)
            blk = B.N._block(h)
            nbl = -(-len(teile[0][0]) // blk)
            ws = []
            for _ in range(2000):
                zieh = rng.choice(nbl, nbl)
                je = []
                for l, y in teile:
                    lz = [l[i] for k in zieh for i in range(k * blk, min((k + 1) * blk, len(l)))]
                    yz = [y[i] for k in zieh for i in range(k * blk, min((k + 1) * blk, len(y)))]
                    je.append(d_schleife(lz, yz))
                if all(math.isfinite(x) for x in je):
                    ws.append(sum(je) / len(je))
            bu, bo = float(np.quantile(ws, B.ALPHA / 2)), float(np.quantile(ws, 1 - B.ALPHA / 2))
            gut = abs(d - d_v) < 1e-12
            ok &= gut
            z.append("   H%d  D Schleife %+.4f Pp · Messung %+.4f Pp %s · t-Band (zweiseitig) Breite %.3f Pp · Bootstrap %.3f Pp (Verhältnis %.2f)"
                     % (h, 100 * d, 100 * d_v, "✔" if gut else "✖", 100 * (o_v - u_v), 100 * (bo - bu), (bo - bu) / (o_v - u_v)))
    con.close()
    nachher = B.fingerabdruck()
    ok &= vorher == nachher
    z.append("\nSeiteneffekt: geschützte Datei unverändert: %s" % (vorher == nachher))
    z.append("ERGEBNIS: %s" % ("BESTANDEN" if ok else "NICHT BESTANDEN"))
    text = "\n".join(z)
    print(text)
    with open(AUSGABE, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
