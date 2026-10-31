# -*- coding: utf-8 -*-
"""G16 Wale URSACHENMESSUNG — Fassung 4 UNVERÄNDERT auf den neuen Werten (Messplan_Wale_29_10.md §18, vorab 4b3c4643, Nutzer 31.10.: „Ok a“).

Dieselbe Frage wie Fassung 4 (Einstieg 00:00 UTC t+1, Folgetag, oberstes minus unterstes Fünftel von E, gepoolt gleich gewichtet, roh),
nur auf den Werten aus Stufe 2 (ohne Kern, ohne die sechs aus Fassung 4, >= 365 Tage L und y im Urteilsfenster).

E und L aus ``p104_wale_s2.lade_alles`` (Zwischenspeicher der Stufe 2, E über ``p102_wale_basis``). Das Urteil folgt
``B.bewerte_gepoolt`` — mit EINER Abweichung, die erst bei vielen Werten auftritt: fehlt einem Wert in einer Vertauschung das obere
oder untere Fünftel (kurze Reihe, L auf Tage ohne y geschoben), fällt er in DIESER Vertauschung aus dem Mittel (nanmean), statt die
ganze Vertauschung zu verwerfen. Bei Fassung 4 (alle sechs voll) ist das dasselbe; ``--abgleich`` zeigt es auf den sechs.

    --abgleich      eigene Vertauschung gegen B.bewerte_gepoolt auf Fassung 4 (gesehene Daten, kein neuer Ertrag)
    --selbsttest    S1/S2 Fehlalarm, S3 Auflösung, Orakel — echte y der neuen Werte, künstliche L
    --messung       nur nach bestandenem Selbsttest; 5 Punkte (§18.1), danach Auskunft (§18.3)

    python -X utf8 Basisinfos/Rechenkern_02_10/p105_wale_f4_breit.py --abgleich | --selbsttest [--welten 1000] | --messung
"""
import json
import os
import socket
import sys
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p102_wale_basis as B  # noqa: E402
import p104_wale_s2 as S  # noqa: E402  (setzt B.START 2023-01-01, TG bis 2026-08-31)
import p103_wale_s2_voranalyse as V  # noqa: E402
import p64_lc_voranalyse as P  # noqa: E402
import messnorm as N  # noqa: E402

B.fassung4()                                           # PRUEFUNG perm, NULL_BLOCK 30, EINSEITIG, HYPOTHESEN 1
AUS = os.path.join(HIER, "p105_wale_f4_breit_%s.txt")
SELBSTTEST = os.path.join(HIER, "p105_wale_f4_breit_selbsttest.json")
TG = S.TG
URTEIL = (date(2024, 1, 1), date(2026, 8, 31))
W = B.maske(TG, URTEIL)
JAHRE = {"2024": (date(2024, 1, 1), date(2024, 12, 31)), "2025": (date(2025, 1, 1), date(2025, 12, 31)),
         "2026": (date(2026, 1, 1), date(2026, 8, 31))}
MIN_TAGE = 365
HORIZONTE = (1, 3, 7)
GRENZE = 0.05 + 2 * np.sqrt(0.05 * 0.95 / 1000)        # 6,4 %
STARTWERT_SELBST, STARTWERT_MESS = 20261107, 20261108
KS = (0.0005, 0.0010, 0.0015, 0.0025, 0.0050)          # 0,05 .. 0,50 Pp
CHUNK = 100


def kopf(was, extra=""):
    return "%s G16 URSACHE — Fassung 4 auf den neuen Werten (Messplan §18, %s, %s)%s" % (
        was, socket.gethostname(), datetime.now().isoformat(timespec="seconds"), extra)


def schreibe(name, z, vorher):
    z.append("\nSeiteneffekt: geschützte Datei unverändert: %s" % (vorher == B.fingerabdruck()))
    text = "\n".join(z)
    print(text)
    with open(AUS % name, "w", encoding="utf-8") as f:
        f.write(text + "\n")


pp = S.pp


# ── Urteil (wie B.bewerte_gepoolt, Vertauschung vektorisiert, nanmean über die Werte) ─────────────────────────────────────
def d_werte(L, Y):
    """D je Wert, L und Y (..., Werte, Tage), bereits gegenseitig maskiert. NaN, wo oben oder unten fehlt."""
    f = np.isfinite(Y)
    o, u = (L == 1) & f, (L == -1) & f
    yo = np.where(o, Y, 0.0)
    yu = np.where(u, Y, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return yo.sum(-1) / o.sum(-1) - yu.sum(-1) / u.sum(-1)


def pooled(dv):
    with np.errstate(invalid="ignore"):
        n = np.isfinite(dv).sum(-1)
        return np.where(n > 0, np.nansum(dv, -1) / np.maximum(n, 1), np.nan)


def maskiere(L, Y):
    L = np.where(np.isfinite(L) & np.isfinite(Y), L, np.nan)
    return L, np.where(np.isfinite(L), Y, np.nan)


def null_verteilung(L, Y, rng, n=B.NULL_PERM):
    """Wie ``B.nullpunkt_gepoolt``: Blöcke B.NULL_BLOCK ab dem ersten Tag, für alle Werte dieselbe Vertauschung, gleicher Zufallsstrom."""
    lang = L.shape[1]
    bl = [np.arange(i * B.NULL_BLOCK, min((i + 1) * B.NULL_BLOCK, lang)) for i in range(-(-lang // B.NULL_BLOCK))]
    idx = np.array([np.concatenate([bl[i] for i in rng.permutation(len(bl))]) for _ in range(n)])
    w = np.concatenate([pooled(d_werte(L[:, idx[a:a + CHUNK]].transpose(1, 0, 2), Y[None, :, :])) for a in range(0, n, CHUNK)])
    return w[np.isfinite(w)]


def urteil(L, Y, rng, mit_block=False):
    """-> dict D, schwelle, p, null_mittel, p1 (H1, einseitig). ``mit_block``: dazu t-Band-Blöcke und Block-AK wie bewerte_gepoolt."""
    L, Y = maskiere(L, Y)
    dv = d_werte(L, Y)
    d = float(pooled(dv))
    null = null_verteilung(L, Y, rng)
    aus = {"D": d, "dv": dv, "schwelle": float(np.quantile(null, 1 - B.ALPHA / B.HYPOTHESEN)), "null_mittel": float(null.mean()),
           "p": float((1 + (null >= d).sum()) / (1 + len(null))), "n_null": len(null)}
    nb, block_ok, ak = 99, True, float("nan")
    if mit_block:
        blk = N._block(1)
        _u, _o, nb = B.band_gepoolt(list(L), list(Y), blk, B.ALPHA / B.HYPOTHESEN, B.EINSEITIG)
        je_tag = {}
        for i in range(L.shape[1]):
            v = [L[k, i] * Y[k, i] for k in range(L.shape[0]) if np.isfinite(L[k, i]) and L[k, i] != 0]
            if v:
                je_tag[i] = float(np.mean(v))
        pb = N.pruefe_block(je_tag, blk)
        ak, block_ok = pb["ak"], pb["ok"] or not np.isfinite(pb["ak"])
    aus.update(nb=nb, block_ok=block_ok, ak=ak, p1=bool(np.isfinite(d) and nb >= 20 and block_ok and d > aus["schwelle"]))
    return aus


# ── Daten ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
def lade():
    """-> dict: sym (neue Werte), E, LAB [Wert, Tag über TG], y {(h, verzug): [Wert, Tag]}, umsatz, eingestellt."""
    sym, E, LAB, _vp = S.lade_alles()
    m, eingestellt = S.paare()
    con = B.ro(S.S2)
    neu = [i for i, s in enumerate(sym) if s not in V.GELADEN]
    ys = {(h, v): [] for h in HORIZONTE for v in (0, 6)}
    for i in neu:
        s = sym[i]
        px = B.kurse(con, m[s])
        for h in HORIZONTE:
            ys[(h, 0)].append(B.ertrag(px, TG, h, 0))
        x = P.reihe(s)
        for h in HORIZONTE:
            if x is None:
                ys[(h, 6)].append(np.full(len(TG), np.nan))
                continue
            a, _L, C = x

            def preis(tage_vor):                       # P(06:00 am Tag t+tage_vor) = Schluss der Stunde 05:00-06:00
                k = np.array([int((pd.Timestamp(d + timedelta(days=tage_vor)) - P.B0) / pd.Timedelta(hours=1)) + 5 - a for d in TG])
                ok = (k >= 0) & (k < len(C))
                return np.where(ok, C[np.clip(k, 0, len(C) - 1)], np.nan)
            with np.errstate(invalid="ignore", divide="ignore"):
                ys[(h, 6)].append(np.log(preis(1 + h) / preis(1)))
    ys = {k: np.array(v) for k, v in ys.items()}
    E, LAB = E[neu], LAB[neu]
    sym = [sym[i] for i in neu]
    tage = (np.isfinite(LAB[:, W]) & np.isfinite(ys[(1, 0)][:, W])).sum(1)
    nimm = tage >= MIN_TAGE
    a, b = URTEIL[0].isoformat(), URTEIL[1].isoformat()
    ums = {s: con.execute("SELECT COALESCE(SUM(umsatz_usd), 0) FROM tag WHERE symbol=? AND markt='spot' AND datum BETWEEN ? AND ?",
                          (m[s], a, b)).fetchone()[0] for s in sym}
    con.close()
    return {"sym": [s for s, k in zip(sym, nimm) if k], "E": E[nimm], "LAB": LAB[nimm], "y": {k: v[nimm] for k, v in ys.items()},
            "umsatz": np.array([ums[s] for s, k in zip(sym, nimm) if k]), "eingestellt": eingestellt, "alle_neu": len(sym),
            "tage": tage[nimm]}


# ── Abgleich gegen B.bewerte_gepoolt (Fassung 4, gesehene Daten) ─────────────────────────────────────────────────────────
def abgleich() -> int:
    vorher = B.fingerabdruck()
    tg, aus = B.lade()
    w = B.maske(tg, B.URTEIL)
    z = [kopf("ABGLEICH", " · eigene Vertauschung gegen B.bewerte_gepoolt auf Fassung 4 (sechs Werte, gesehen, KEIN neuer Ertrag)")]
    ok = True
    for h in (1, 3):
        labs = np.array([aus[s]["markt"]["spot"][B.Q_HAUPT][3][w] for s in B.SYMBOLE])
        ys = np.array([aus[s]["y"][(h, 0)][w] for s in B.SYMBOLE])
        for start in (1, 2, 3):
            r0 = B.bewerte_gepoolt(list(labs), list(ys), h, np.random.default_rng(start), mit_block=False)
            r1 = urteil(labs, ys, np.random.default_rng(start))
            a = (abs(r0["D"] - r1["D"]), abs(r0["schwelle"] - r1["schwelle"]), r0["p"] == r1["p"])
            gut = a[0] < 1e-15 and a[1] < 1e-15 and a[2]
            ok &= gut
            z.append("  H%d Startwert %d: D %s / %s · Schwelle %s / %s · p %.3f / %.3f · Abweichung D %.1e, Schwelle %.1e %s"
                     % (h, start, pp(r0["D"]), pp(r1["D"]), pp(r0["schwelle"]), pp(r1["schwelle"]), r0["p"], r1["p"], a[0], a[1], "✔" if gut else "✖"))
    # künstliche Welt mit kurzen Reihen: nanmean statt Verwerfen — nur Auskunft, wie oft ein Wert ausfällt
    z.append("\nERGEBNIS: %s" % ("BITGLEICH (bis 1e-15, p identisch)" if ok else "ABWEICHUNG"))
    schreibe("abgleich", z, vorher)
    return 0 if ok else 1


# ── Selbsttest ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def selbsttest() -> int:
    welten = int(sys.argv[sys.argv.index("--welten") + 1]) if "--welten" in sys.argv else 1000
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(STARTWERT_SELBST)
    d = lade()
    vp = json.load(open(S.VP, encoding="utf-8"))
    phi, rho = vp["phi"], max(0.0, vp["rho"])
    E, Y = d["E"], d["y"][(1, 0)]
    maske = np.isfinite(E)
    nv, nd = E.shape
    Yw = Y[:, W]
    monat = np.unique(np.array([t.year * 12 + t.month for t in TG]), return_inverse=True)[1]
    s1f = np.sqrt(max(1e-9, 1 - phi ** 2))
    z = [kopf("SELBSTTEST", " · %d Welten · echte y (H1, 00:00) der neuen Werte, künstliche L · EINSEITIG · Startwert %d" % (welten, STARTWERT_SELBST))]
    z.append("Werte %d (von %d neuen, >= %d Tage L und y) · Urteil %s bis %s · phi %.3f · rho %.3f · Nullwelt %d T gemeinsam, %d Vertauschungen"
             % (nv, d["alle_neu"], MIN_TAGE, *URTEIL, phi, rho, B.NULL_BLOCK, B.NULL_PERM))
    z.append("Soll: Fehlalarm H1 S1/S2 <= %.1f %% · Orakel >= 190/200" % (100 * GRENZE))

    def s1():
        c = np.empty(nd)
        e = np.empty((nv, nd))
        c[0], e[:, 0] = rng.standard_normal(), rng.standard_normal(nv)
        for t in range(1, nd):
            c[t] = phi * c[t - 1] + s1f * rng.standard_normal()
            e[:, t] = phi * e[:, t - 1] + s1f * rng.standard_normal(nv)
        return np.where(maske, np.sqrt(rho) * c[None, :] + np.sqrt(1 - rho) * e, np.nan)

    def s2():
        mm = rng.standard_normal(monat.max() + 1)[monat]
        return np.where(maske, mm[None, :] + 0.2 * rng.standard_normal((nv, nd)), np.nan)

    fehl, ausfall = {}, []
    for name, welt in (("S1", s1), ("S2", s2)):
        t = 0
        for i in range(welten):
            r = urteil(S.fuenftel_matrix(welt())[:, W], Yw, rng)
            t += r["p1"]
            ausfall.append(B.NULL_PERM - r["n_null"])
            if (i + 1) % 100 == 0:
                print("  %s %d/%d · %.1f %%" % (name, i + 1, welten, 100 * t / (i + 1)), flush=True)
        fehl[name] = t / welten
    halt = all(f <= GRENZE for f in fehl.values())
    z.append("\nFEHLALARM H1 (TRÄGT HÖHER, Punkt 1)")
    for name, f in fehl.items():
        z.append("  %s %5.1f %% %s" % (name, 100 * f, "✔" if f <= GRENZE else "✖ über %.1f %%" % (100 * GRENZE)))
    z.append("  verworfene Vertauschungen (kein Wert mit oben UND unten): höchstens %d je Welt" % max(ausfall))
    n3 = 250 if welten >= 1000 else welten
    z.append("\nS3 AUFLÖSUNG (%d Welten je k, Signal wie S1, Pflanzung y + k·L) — k in Pp, D verschiebt um 2k" % n3)
    quote = []
    for k in KS:
        t = 0
        for _ in range(n3):
            lw = S.fuenftel_matrix(s1())[:, W]
            t += urteil(lw, Yw + k * np.where(np.isfinite(lw), lw, 0), rng)["p1"]
        quote.append(t / n3)
        print("  S3 k %.2f Pp: %.0f %%" % (100 * k, 100 * quote[-1]), flush=True)
    x = next((k for k, q in zip(KS, quote) if q >= 0.8), None)
    z.append("  %s  ->  X = %s" % ("  ".join("%.2f:%3.0f%%" % (100 * k, 100 * q) for k, q in zip(KS, quote)),
                                    ("%.2f Pp (D-Unterschied %.2f Pp)" % (100 * x, 200 * x)) if x else "über 0,50 Pp"))
    z.append("\nORAKEL (200 Welten, E = y + Rauschen gleicher Streuung je Wert, NaN-Muster des echten E)")
    sd = np.nanstd(Y, axis=1)[:, None]
    y0 = np.where(np.isfinite(Y), Y, 0.0)
    orakel = 0
    for _ in range(200):
        lw = S.fuenftel_matrix(np.where(maske, y0 + sd * rng.standard_normal((nv, nd)), np.nan))[:, W]
        orakel += urteil(lw, Yw, rng)["p1"]
    z.append("  %d von 200 %s" % (orakel, "✔" if orakel >= 190 else "✖"))
    bestanden = bool(halt and orakel >= 190)
    z.append("\nERGEBNIS: %s · X %s" % ("BESTANDEN" if bestanden else "NICHT BESTANDEN", ("%.2f Pp" % (100 * x)) if x else "über 0,50 Pp"))
    schreibe("selbsttest", z, vorher)
    if welten >= 1000:
        with open(SELBSTTEST, "w", encoding="utf-8") as f:
            json.dump({"bestanden": bestanden, "null_block": B.NULL_BLOCK, "welten": welten, "grenze": GRENZE, "fehl": fehl, "X": x,
                       "quote": dict(zip(map(str, KS), quote)), "orakel": orakel, "startwert": STARTWERT_SELBST, "werte": nv}, f, indent=1)
    return 0 if bestanden else 1


# ── Messung ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def messung() -> int:
    st = json.load(open(SELBSTTEST, encoding="utf-8")) if os.path.exists(SELBSTTEST) else {}
    if not st.get("bestanden") or st.get("null_block") != B.NULL_BLOCK or st.get("welten", 0) < 1000:
        print("✖ kein bestandener Selbsttest (1.000 Welten, Block %d) - nicht messen" % B.NULL_BLOCK)
        return 1
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(STARTWERT_MESS)
    d = lade()
    sym, LAB, y = d["sym"], d["LAB"], d["y"]
    X = st["X"]
    z = [kopf("MESSUNG", " · einseitig (oberstes Fünftel HÖHER) · q 5 % · Einstieg 00:00 UTC t+1 · Log brutto, roh, Pp")]
    z.append("Selbsttest ✔ (S1 %.1f %%, S2 %.1f %%, Orakel %d/200, X %s) · Werte %d von %d neuen (>= %d Tage) · Urteil %s bis %s"
             % (100 * st["fehl"]["S1"], 100 * st["fehl"]["S2"], st["orakel"], ("%.2f Pp" % (100 * X)) if X else "über 0,50 Pp",
                len(sym), d["alle_neu"], MIN_TAGE, *URTEIL))

    def dd(maske, h=1, v=0, zeilen=None):
        zeilen = np.arange(len(sym)) if zeilen is None else zeilen
        L, Y = maskiere(LAB[zeilen][:, maske], y[(h, v)][zeilen][:, maske])
        return float(pooled(d_werte(L, Y)))

    r = urteil(LAB[:, W], y[(1, 0)][:, W], rng, mit_block=True)
    dv = r["dv"]
    jahre = {j: dd(B.maske(TG, zr)) for j, zr in JAHRE.items()}
    verzug = dd(W, 1, 6)
    n_pos, n_fin = int((dv > 0).sum()), int(np.isfinite(dv).sum())
    p = [r["p1"], n_pos > n_fin / 2, sum(v > 0 for v in jahre.values()) >= 2, verzug > 0, True]
    obergrenze = r["D"] + r["schwelle"] - r["null_mittel"]
    z.append("\n══ URTEIL H1 (§18.1, alle 5 Punkte) ══")
    z.append("  D %s Pp · Schwelle Permutation 95 %% %s (p %.3f) · Null %s · einseitige Obergrenze %s · Blöcke (15 T) %d · AK %.3f"
             % (pp(r["D"]), pp(r["schwelle"]), r["p"], pp(r["null_mittel"]), pp(obergrenze), r["nb"], r["ak"]))
    z.append("  1 Test %s · 2 D>0 bei %d/%d %s · 3 Jahre %s %s · 4 Verzug 06:00 %s %s · 5 Selbsttest ✔" % (
        "✔" if p[0] else "✖", n_pos, n_fin, "✔" if p[1] else "✖", " ".join("%s %s" % (j, pp(v)) for j, v in jahre.items()),
        "✔" if p[2] else "✖", pp(verzug), "✔" if p[3] else "✖"))
    traegt = all(p)
    stufe = "TRÄGT AUF DEN NEUEN WERTEN" if traegt else ("TRÄGT NICHT BIS %.2f Pp" % (200 * X) if X and obergrenze < 2 * X else "NICHT TRENNBAR")
    z.append("  ->  %s" % stufe)
    # ── Auskunft (§18.3) ──
    z.append("\n══ AUSKUNFT (§18.3) — nach dem Urteil, NICHT Teil davon ══")
    z.append("  H3 %s · H7 %s · Verzug H3 %s" % (pp(dd(W, 3)), pp(dd(W, 7)), pp(dd(W, 3, 6))))
    ordnung = np.argsort(-d["umsatz"])
    drittel = np.array_split(ordnung, 3)
    aus_dr = {}
    for nr, zl in enumerate(drittel, 1):
        rr = urteil(LAB[zl][:, W], y[(1, 0)][zl][:, W], rng)
        aus_dr[nr] = rr
        z.append("  Liquidität Drittel %d (%d Werte, Spot-Umsatz %.2f..%.2f Mrd. USD): D %s · Schwelle %s · p %.3f · D>0 bei %d/%d"
                 % (nr, len(zl), d["umsatz"][zl].min() / 1e9, d["umsatz"][zl].max() / 1e9, pp(rr["D"]), pp(rr["schwelle"]), rr["p"],
                    int((rr["dv"] > 0).sum()), int(np.isfinite(rr["dv"]).sum())))
    handelnd = [i for i in ordnung if sym[i] not in d["eingestellt"]][:6]
    r6 = urteil(LAB[handelnd][:, W], y[(1, 0)][handelnd][:, W], rng)
    z.append("  Fassung-4-Regel auf den neuen Werten (Top 6 Umsatz, handelnd: %s): D %s · Schwelle %s · p %.3f · je Wert %s"
             % (" ".join(sym[i] for i in handelnd), pp(r6["D"]), pp(r6["schwelle"]), r6["p"], " ".join(pp(v) for v in r6["dv"])))
    ein = [i for i, s in enumerate(sym) if s in d["eingestellt"]]
    if ein:
        z.append("  eingestellte Paare (%d): D %s · übrige: %s" % (len(ein), pp(dd(W, zeilen=np.array(ein))),
                                                                 pp(dd(W, zeilen=np.array([i for i in range(len(sym)) if i not in ein])))))
    schreibe("messung", z, vorher)
    with open(AUS % "messung" + ".json", "w", encoding="utf-8") as f:
        json.dump({"traegt": traegt, "stufe": stufe, "D": r["D"], "schwelle": r["schwelle"], "p": r["p"], "punkte": p, "jahre": jahre,
                   "verzug": verzug, "n_pos": n_pos, "n_fin": n_fin, "werte": sym, "dv": [float(v) for v in dv],
                   "drittel": {k: {"D": v["D"], "p": v["p"]} for k, v in aus_dr.items()}, "top6": {"sym": [sym[i] for i in handelnd], "D": r6["D"], "p": r6["p"]}},
                  f, indent=1, default=float)
    return 0


if __name__ == "__main__":
    if "--abgleich" in sys.argv:
        sys.exit(abgleich())
    if "--selbsttest" in sys.argv:
        sys.exit(selbsttest())
    if "--messung" in sys.argv:
        sys.exit(messung())
    print(__doc__)
