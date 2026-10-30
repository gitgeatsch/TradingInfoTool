# -*- coding: utf-8 -*-
"""Messplan W FASSUNG 4 (§14, vorab 1924c5b4, Nutzer 30.10.: „A2“) — Vorprüfung auf sechs Altcoins nach Regel, gepoolt.

Derselbe Rechenweg wie Fassung 3 (``p102_wale_basis``); neu ist nur das POOLEN über sechs Werte (``bewerte_gepoolt``: D = Mittel der
sechs D, Band über gemeinsame 15-T-Blöcke, dieselbe Vertauschung für alle). Bei EINEM Wert ist das bitgleich mit ``bewerte``
(geprüft 30.10. auf BTC Fassung 3, H1/H3/H7).

    --vorpruefung   Vollständigkeit, Rohdatei-Stichprobe (eigener Rechenweg), Kurse, Fallzahlen, Gleichlauf von E — OHNE Erträge
    --selbsttest    S1 Fehlalarm (AR(1) mit echtem Gleichlauf), S2 Ballung (Monatsregime GEMEINSAM), S3 Auflösung, Orakel
    --messung       nur nach bestandenem Selbsttest; fünf Punkte (§14)

    python -X utf8 Basisinfos/Rechenkern_02_10/p102_wale_f4.py --vorpruefung | --selbsttest [--welten 1000] | --messung
"""
import io
import json
import os
import socket
import sys
import zipfile
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p102_wale_basis as B  # noqa: E402
import wale_stichprobe as WS  # noqa: E402
import messnorm as N  # noqa: E402

B.fassung4()
AUS = os.path.join(B.HIER, "p102_wale_%s_f4.txt")
SELBSTTEST = os.path.join(B.HIER, "p102_wale_selbsttest_f4.json")
KS = (0.001, 0.0025, 0.005, 0.01, 0.02)
M = "spot"


def pp(x):
    return "%+.2f" % (100 * x) if np.isfinite(x) else "  –  "


def schreibe(name, z, vorher):
    z.append("\nSeiteneffekt: geschützte Datei unverändert: %s" % (vorher == B.fingerabdruck()))
    text = "\n".join(z)
    print(text)
    with open(AUS % name, "w", encoding="utf-8") as f:
        f.write(text + "\n")


def kopf(was, extra=""):
    return "%s Messplan W FASSUNG 4 (%s, %s) · %s · Urteil %s bis %s%s" % (
        was, socket.gethostname(), datetime.now().isoformat(timespec="seconds"), " ".join(s[:-4] for s in B.SYMBOLE), *B.URTEIL, extra)


# ── Vorprüfung ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def g_roh(df, q=B.Q_HAUPT):
    """EIGENER Rechenweg (pandas, nicht die Ablage): Sweeps = Läufe gleicher Zeit und Seite, Klassen Viertel-Dekaden, Grenzklasse ganz."""
    kauf = ~df["kaeufer_maker"]
    lauf = ((df["zeit"] != df["zeit"].shift()) | (kauf != kauf.shift())).cumsum()
    sw = (df.assign(usd=df["preis"] * df["menge"], kauf=kauf).groupby(lauf).agg(usd=("usd", "sum"), kauf=("kauf", "first")))
    sw["kl"] = np.clip(np.floor(4 * np.log10(np.maximum(sw["usd"], 1.0))), 0, 36).astype(int)
    sw["netto"] = np.where(sw["kauf"], sw["usd"], -sw["usd"])
    je = sw.groupby("kl").agg(usd=("usd", "sum"), netto=("netto", "sum")).sort_index(ascending=False)
    ges = je["usd"].sum()
    kum = je["usd"].cumsum()
    grenze = kum.index[np.argmax(kum.to_numpy() >= q * ges)]
    return float(je.loc[je.index >= grenze, "netto"].sum() / ges)


def vorpruefung() -> int:
    vorher = B.fingerabdruck()
    con = B.ro()
    tg, aus = B.lade()
    z = [kopf("VORPRÜFUNG", " · Tage %s bis %s · OHNE Erträge" % (tg[0], tg[-1]))]
    ok = tg[-1] >= B.URTEIL[1]
    z.append("  Daten reichen bis %s (Soll >= %s) %s" % (tg[-1], B.URTEIL[1], "✔" if ok else "✖"))
    a, b = tg[0].isoformat(), tg[-1].isoformat()
    z.append("\n1 VOLLSTÄNDIGKEIT (Soll %d Tage je Reihe)" % len(tg))
    for s in B.SYMBOLE:
        n, lo, hi, ohne = con.execute("SELECT COUNT(*), MIN(umsatz_usd/kerze_usd), MAX(umsatz_usd/kerze_usd), SUM(kerze_usd IS NULL) "
                                      "FROM tag WHERE symbol=? AND markt=? AND datum BETWEEN ? AND ?", (s, M, a, b)).fetchone()
        ab = con.execute("SELECT COUNT(*) FROM tag WHERE symbol=? AND markt=? AND datum BETWEEN ? AND ? AND (ABS(umsatz_usd/kerze_usd-1) > 0.005 "
                         "OR substr(erste_utc,12,5) > '00:05' OR substr(letzte_utc,12,5) < '23:55')", (s, M, a, b)).fetchone()[0]
        sw = con.execute("SELECT COUNT(*) FROM (SELECT t.datum, ABS(SUM(st.usd)/t.umsatz_usd-1) a FROM tag t JOIN stunde st USING (symbol, markt, datum) "
                         "WHERE t.symbol=? AND t.markt=? AND t.datum BETWEEN ? AND ? GROUP BY t.datum HAVING a > 1e-6)", (s, M, a, b)).fetchone()[0]
        gut = n == len(tg) and not ohne and not sw
        ok &= gut
        z.append("  %-9s %4d Tage · Archiv/Kerze %.4f..%.4f · auffällig %d · Stunden≠Tag %d · %s" % (s, n, lo or 0, hi or 0, ab, sw, "✔" if gut else "✖"))
        if ab:
            for zeile in con.execute("SELECT datum, umsatz_usd/kerze_usd, erste_utc, letzte_utc FROM tag WHERE symbol=? AND markt=? AND datum BETWEEN ? AND ? "
                                     "AND (ABS(umsatz_usd/kerze_usd-1) > 0.005 OR substr(erste_utc,12,5) > '00:05' OR substr(letzte_utc,12,5) < '23:55')",
                                     (s, M, a, b)).fetchall()[:5]:
                z.append("            auffällig: %s Archiv/Kerze %.4f %s .. %s" % zeile)
    # 2 Stichprobe: je Wert 3 Tage NEU aus dem Archiv, G mit eigenem Rechenweg gegen die Ablage
    z.append("\n2 STICHPROBE Rohdatei (je Wert 3 Zufallstage im Urteilsfenster, neu geladen, G q 5 %% mit eigenem pandas-Rechenweg)")
    rng = np.random.default_rng(20261030)
    idx = {d.isoformat(): i for i, d in enumerate(tg)}
    fenster = [d for d in tg if B.URTEIL[0] <= d <= B.URTEIL[1]]
    for s in B.SYMBOLE:
        g = aus[s]["markt"][M][B.Q_HAUPT][0]
        abw = []
        for d in rng.choice(len(fenster), 3, replace=False):
            datum = fenster[int(d)].isoformat()
            df = WS.lies_tag(M, datum, s)
            abw.append(float("inf") if df is None else abs(g_roh(df) - g[idx[datum]]))
        gut = max(abw) < 1e-9
        ok &= gut
        z.append("  %-9s größte Abweichung G %.2e · %s" % (s, max(abw), "✔" if gut else "✖"))
    # 3 Kurse
    z.append("\n3 KURSE an den Einstiegszeitpunkten (00:00 Pflicht; 06:00 Verzugsprobe; Börsenausfall = fehlt bei allen)")
    jetzt = int(datetime.now().timestamp() * 1000) - 3600000
    pxs = {s: B.kurse(con, s) for s in B.SYMBOLE}
    fehlt = {s: {(d, st) for d in tg + [tg[-1] + timedelta(days=i) for i in range(1, 9)] for st in (0, 6)
                 if B._ms(d, st) not in pxs[s] and B._ms(d, st) < jetzt} for s in B.SYMBOLE}
    for s in B.SYMBOLE:
        null = sorted(x for x in fehlt[s] if x[1] == 0)
        sechs = sorted(x for x in fehlt[s] if x[1] == 6)
        boerse = [x for x in sechs if all(x in fehlt[t] for t in B.SYMBOLE)]
        gut = not null and len(boerse) == len(sechs)
        ok &= gut
        z.append("  %-9s fehlend 00:00 %d %s · 06:00 %d (Börsenausfall %d) · %s" % (s, len(null), null[:3] if null else "", len(sechs), len(boerse),
                                                                                "✔" if gut else "✖"))
    # 4 Fallzahlen, Gleichlauf
    w = B.maske(tg, B.URTEIL)
    z.append("\n4 FALLZAHLEN (q 5 %%) · Urteilsfenster %d Tage" % w.sum())
    for h in B.HORIZONTE:
        blk = N._block(h)
        z.append("  H%d: Block %d T -> %d gemeinsame Blöcke %s" % (h, blk, -(-int(w.sum()) // blk), "✔" if w.sum() / blk >= 20 else "✖ < 20"))
        ok &= w.sum() / blk >= 20
    es = {}
    for s in B.SYMBOLE:
        g, r, e, lab = aus[s]["markt"][M][B.Q_HAUPT]
        es[s] = e
        fin = np.isfinite(e[:-1]) & np.isfinite(e[1:])
        je = ["%d: %d/%d/%d" % (j, (lab[mj] == 1).sum(), (lab[mj] == 0).sum(), (lab[mj] == -1).sum())
              for j in (2024, 2025, 2026) for mj in [np.array([d.year == j for d in tg]) & w]]
        z.append("  %-9s Fünftel ab %s, AK(1) von E %+.3f · oben/mitte/unten %s" % (
            s, next((tg[i] for i in range(len(tg)) if np.isfinite(lab[i])), None), np.corrcoef(e[:-1][fin], e[1:][fin])[0, 1], " · ".join(je)))
    kor = [np.corrcoef(es[a][m], es[b][m])[0, 1] for i, a in enumerate(B.SYMBOLE) for b in B.SYMBOLE[i + 1:]
           for m in [np.isfinite(es[a]) & np.isfinite(es[b]) & w]]
    z.append("  Gleichlauf von E zwischen den Werten (paarweise Korrelation, 15 Paare): Mittel %+.3f, Spanne %+.3f .. %+.3f" % (
        np.mean(kor), min(kor), max(kor)))
    con.close()
    ok &= vorher == B.fingerabdruck()
    z.append("ERGEBNIS: %s" % ("BESTANDEN" if ok else "NICHT BESTANDEN"))
    schreibe("vorpruefung", z, vorher)
    return 0 if ok else 1


# ── Selbsttest ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def ar1(rng, n, phi):
    e = np.empty(n)
    e[0] = rng.standard_normal()
    zz = rng.standard_normal(n) * np.sqrt(max(1e-9, 1 - phi ** 2))
    for i in range(1, n):
        e[i] = phi * e[i - 1] + zz[i]
    return e


def traegt(r):
    return r["stufe"].startswith("TRAEGT (oberstes Fünftel HÖHER")


def selbsttest() -> int:
    welten = int(sys.argv[sys.argv.index("--welten") + 1]) if "--welten" in sys.argv else 1000
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(20261102 if B.PRUEFUNG == "perm" else 20261031)    # 4b: neuer Startwert, nicht der vom 4a-Lauf
    tg, aus = B.lade()
    w = B.maske(tg, B.URTEIL)
    n = len(tg)
    S = B.SYMBOLE
    es = {s: aus[s]["markt"][M][B.Q_HAUPT][2] for s in S}
    phis = {}
    for s in S:
        e = es[s]
        fin = np.isfinite(e[:-1]) & np.isfinite(e[1:])
        phis[s] = float(np.corrcoef(e[:-1][fin], e[1:][fin])[0, 1])
    kor = [np.corrcoef(es[a][m], es[b][m])[0, 1] for i, a in enumerate(S) for b in S[i + 1:] for m in [np.isfinite(es[a]) & np.isfinite(es[b])]]
    rho = max(0.0, float(np.mean(kor)))
    ys = {h: [aus[s]["y"][(h, 0)][w] for s in S] for h in B.HORIZONTE}
    monat = np.unique(np.array([d.year * 12 + d.month for d in tg]), return_inverse=True)[1]
    z = [kopf("SELBSTTEST", " · %d Welten · echte Erträge, künstliche Signale, KEIN echtes Ergebnis · EINSEITIG" % welten)]
    z.append("Soll: S1/S2 TRÄGT in <= 5 %% bei H1 (Hauptfrage; H3/H7 Auskunft) · Orakel H1 >= 190/200 · Nullwelt Block 15 T, gemeinsam · "
             "Urteil %s" % ("PERMUTATIONSTEST (Fassung 4b), %d Vertauschungen" % B.NULL_PERM if B.PRUEFUNG == "perm" else "t-Band"))
    z.append("Autokorrelation E: %s · Gleichlauf rho %.3f (Mittel der 15 Paare)" % (", ".join("%s %+.3f" % (s[:-4], p) for s, p in phis.items()), rho))

    def s1():
        c = ar1(rng, n, float(np.mean(list(phis.values()))))
        return [np.sqrt(rho) * c + np.sqrt(1 - rho) * ar1(rng, n, phis[s]) for s in S]

    def s2():                                                     # Monatsregime für ALLE sechs gleich (schärfste Ballung)
        m = rng.standard_normal(monat.max() + 1)[monat]
        return [m + 0.2 * rng.standard_normal(n) for _ in S]

    fehl = {}
    for name, welt in (("S1", s1), ("S2", s2)):
        tr = {h: 0 for h in B.HORIZONTE}
        for _ in range(welten):
            labs = [B.fuenftel(e)[w] for e in welt()]
            for h in B.HORIZONTE:
                tr[h] += traegt(B.bewerte_gepoolt(labs, ys[h], h, rng, mit_block=False))
        fehl[name] = {h: tr[h] / welten for h in B.HORIZONTE}
        print("  %s fertig" % name, flush=True)
    z.append("\nFEHLALARM (TRÄGT HÖHER) — H 1 / 3 / 7")
    for name in ("S1", "S2"):
        q = [fehl[name][h] for h in B.HORIZONTE]
        z.append("  %s  %s   H1 %s" % (name, "  ".join("%5.1f %%" % (100 * x) for x in q), "✔" if q[0] <= 0.05 else "✖ über 5 %"))
    halt = fehl["S1"][1] <= 0.05 and fehl["S2"][1] <= 0.05
    n3 = max(200, welten // 4)
    z.append("\nS3 AUFLÖSUNG (%d Welten je k, Signal wie S1) — k in Pp, D verschiebt um 2k" % n3)
    xs = {}
    for h in B.HORIZONTE:
        quote = []
        for k in KS:
            t = 0
            for _ in range(n3):
                labs = [B.fuenftel(e)[w] for e in s1()]
                yk = [y + k * np.where(np.isfinite(l), l, 0) for l, y in zip(labs, ys[h])]
                r = B.bewerte_gepoolt(labs, yk, h, rng, mit_block=False)
                t += traegt(r)
            quote.append(t / n3)
        x = next((k for k, qq in zip(KS, quote) if qq >= 0.8), None)
        xs[h] = x
        z.append("  H%d  %s  ->  X = %s" % (h, "  ".join("%.2f:%3.0f%%" % (100 * k, 100 * qq) for k, qq in zip(KS, quote)),
                                           ("%.2f Pp (D-Unterschied %.2f Pp)" % (100 * x, 200 * x)) if x else "über 2 Pp"))
    print("  S3 fertig", flush=True)
    z.append("\nORAKEL (200 Welten, E = y + Rauschen gleicher Streuung je Wert) — Soll H1 TRÄGT HÖHER >= 190")
    orakel = {}
    for h in B.HORIZONTE:
        t = 0
        yv = [aus[s]["y"][(h, 0)] for s in S]
        for _ in range(200):
            labs = [B.fuenftel(np.where(np.isfinite(y), y, 0) + np.nanstd(y) * rng.standard_normal(n))[w] for y in yv]
            t += traegt(B.bewerte_gepoolt(labs, ys[h], h, rng, mit_block=False))
        orakel[h] = t
        z.append("  H%d  %3d von 200 %s" % (h, t, "✔" if t >= 190 else "✖"))
    bestanden = bool(halt and orakel[1] >= 190)
    z.append("\nERGEBNIS: %s · Nullwelt block (gemeinsam) · X H1 %s" % ("BESTANDEN" if bestanden else "NICHT BESTANDEN",
                                                                   ("%.2f Pp" % (100 * xs[1])) if xs[1] else "über 2 Pp"))
    schreibe("selbsttest", z, vorher)
    if welten >= 1000:
        with open(SELBSTTEST, "w", encoding="utf-8") as f:
            json.dump({"bestanden": bestanden, "nullwelt": "block", "welten": welten, "rho": rho, "fehl": fehl,
                       "X": {str(h): v for h, v in xs.items()}, "orakel": orakel}, f, indent=1)
    return 0 if bestanden else 1


# ── Messung ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def messung() -> int:
    if not os.path.exists(SELBSTTEST) or not json.load(open(SELBSTTEST, encoding="utf-8")).get("bestanden"):
        print("✖ kein bestandener Selbsttest Fassung 4 (%s) - nicht messen" % SELBSTTEST)
        return 1
    st = json.load(open(SELBSTTEST, encoding="utf-8"))
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(20261101)
    tg, aus = B.lade()
    w = B.maske(tg, B.URTEIL)
    S = B.SYMBOLE
    z = [kopf("MESSUNG", " · einseitig (oberstes Fünftel HÖHER) · q 5 % · Log-Ertrag brutto, Pp")]
    labs = {s: aus[s]["markt"][M][B.Q_HAUPT][3] for s in S}

    def gepoolt(maske, h=1, verzug=0, lab=None):
        lab = lab or labs
        return B.differenz_gepoolt([lab[s][maske] for s in S], [aus[s]["y"][(h, verzug)][maske] for s in S])

    z.append("\n══ GEPOOLT (Mittel der sechs D) ══")
    haupt = {}
    for h in B.HORIZONTE:
        x = st["X"].get(str(h))
        r = B.bewerte_gepoolt([labs[s][w] for s in S], [aus[s]["y"][(h, 0)][w] for s in S], h, rng, aufloesung=2 * x if x else None)
        haupt[h] = r
        z.append("  H%d%s  D %s · Schwelle Permutation 95 %% %s (p %.3f) · Null %s · t-Band-Untergrenze %s · %s · %d/%d Wert-Tage oben/unten, "
                 "%d Bl., AK %.3f" % (h, "  (HAUPTFRAGE)" if h == 1 else "  (Auskunft)  ", pp(r["D"]), pp(r["schwelle"]), r["p"], pp(r["nullpunkt"]),
                                      pp(r["unten"]), r["stufe"], r["n_oben"], r["n_unten"], r["n_bloecke"], r["ak"]))
    jahre = {j: gepoolt(B.maske(tg, zr)) for j, zr in B.JAHRE.items()}
    verzug = gepoolt(w, 1, 6)
    leiter = {q: gepoolt(w, lab={s: aus[s]["markt"][M][q][3] for s in S}) for q in B.STUFEN}
    arm_g = gepoolt(w, lab={s: B.fuenftel(aus[s]["markt"][M][B.Q_HAUPT][0]) for s in S})
    arm_r = gepoolt(w, lab={s: B.fuenftel(aus[s]["markt"][M][B.Q_HAUPT][1]) for s in S})
    z.append("  H1 Jahre %s · Verzug 06:00 %s" % (" · ".join("%s %s" % (j, pp(v)) for j, v in jahre.items()), pp(verzug)))
    z.append("  Auskunft H1: q 1/5/10/20 %s · Vergleichsarme G roh %s, R roh %s" % (" ".join(pp(leiter[q]) for q in B.STUFEN), pp(arm_g), pp(arm_r)))
    z.append("\n══ JE WERT (H1; Untergrenze einseitig zur Auskunft, das Urteil ist gepoolt) ══")
    je = {}
    for s in S:
        y = aus[s]["y"][(1, 0)]
        r = B.bewerte(labs[s][w], y[w], 1, rng)
        je[s] = r["D"]
        jj = " ".join("%s %s" % (j, pp(B.differenz(labs[s][B.maske(tg, zr)], y[B.maske(tg, zr)]))) for j, zr in B.JAHRE.items())
        h37 = " ".join("H%d %s" % (h, pp(B.differenz(labs[s][w], aus[s]["y"][(h, 0)][w]))) for h in (3, 7))
        z.append("  %-9s D %s [%s] · %s · %s · Verzug %s" % (s, pp(r["D"]), pp(r["unten"]), jj, h37, pp(B.differenz(labs[s][w], aus[s]["y"][(1, 6)][w]))))
    h = haupt[1]
    p = [h["stufe"].startswith("TRAEGT (oberstes Fünftel HÖHER"),
         sum(v > 0 for v in je.values()) >= 4,
         sum(v > 0 for v in jahre.values()) >= 2,
         verzug > 0,
         bool(st["bestanden"])]
    z.append("\n══ URTEIL (§14, alle 5 Punkte) ══")
    z.append("  1 D über der Permutationsschwelle %s · 2 D>0 bei %d/6 %s · 3 Jahre positiv %d/3 %s · 4 Verzug %s · 5 Selbsttest %s" % (
        "✔" if p[0] else "✖", sum(v > 0 for v in je.values()), "✔" if p[1] else "✖", sum(v > 0 for v in jahre.values()), "✔" if p[2] else "✖",
        "✔" if p[3] else "✖", "✔" if p[4] else "✖"))
    z.append("  ->  %s" % ("TRÄGT AUSSERHALB DES KERNS -> Stufe 2 (eigener Messplan, keine Verschlechterung)" if all(p)
                          else "TRÄGT NICHT außerhalb des Kerns (Stufe H1: %s) -> Dashboard-Weg" % h["stufe"]))
    schreibe("messung", z, vorher)
    return 0


if __name__ == "__main__":
    if "--vorpruefung" in sys.argv:
        sys.exit(vorpruefung())
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    if "--messung" in sys.argv:
        sys.exit(messung())
    print(__doc__)
