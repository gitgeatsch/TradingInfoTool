"""P51 MESSUNG Makro-Umfeld (Spot §51.5, Stufe 2) - nur lesend; Abrufe FRED fredgraph.csv, yfinance, CoinMetrics Community (frei).

    python Basisinfos/Spot_Voranalyse_04_10/p51_messung.py

Fester Plan §51.5 (vorab Commit 52bf0e00), Vorpruefung §51.6 (0d97b4dd). Kanaele, Einteilung und Zielgroessen kommen unveraendert
aus p51_vorpruefung.py. Hier dazu:
  1. Nullwelt 1.000 zirkulaere Verschiebungen (Rand 365 T), p je Seite nach der Stufung (c+1)/(n+1).
     Bonferroni: Kanal 0,025/9 je Seite, Gesamt lang/kurz 0,0125 je Seite.
  2. Vorzeichen in jeder Epoche E1/E2/E3 gleich (fehlt eine Epoche: nicht entscheidbar).
  3. Spiegelprobe: guenstiges Drittel mehr starke Anstiege (>= +20 %) UND weniger starke Rueckgaenge (<= -20 %) als das unguenstige.
  Selbsttest (a) 200 phasen-randomisierte Makroreihen gegen T1/T2 (Fehlalarm je Stufe gegen das Soll aus der Stufung),
            (b) Pflanzung Ziel + beta*z(Merkmal) als Aufloesungskurve (Fund = Rang ueber der Bonferroni-Schwelle, nicht das volle Urteil).
  Weglassprobe: Gesamt lang/kurz ohne je einen Kanal.
Zwischenstand der Eingangsdaten wird nach data/_spot/p51_eingang.pkl gelegt (gitignored), damit die Gegenprobe dieselben Rohdaten hat.
"""
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p51_vorpruefung as V   # noqa: E402  (setzt das Arbeitsverzeichnis auf die Projektwurzel)

RNG = np.random.default_rng(20261052)
NZ = 1000
RAND = 365
A_KANAL, A_GESAMT = 0.025 / 9, 0.0125
STARK = np.log(1.2), np.log(0.8)
IDX = V.IDX
CACHE = os.path.join("data", "_spot", "p51_eingang.pkl")
ROLLE = {"T": "Urteil", "M": "Probe", "A": "Auskunft"}


def eingang():
    K, k5k = V.kanaele()
    Z = V.ziele()
    S = {}
    for n, (lg, vl, kz, vk) in K.items():
        S[n + " lang"] = V.score(lg, vl)
        S[n + " kurz"] = k5k if kz is None else V.score(kz, vk)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "wb") as f:
        pickle.dump({"K": K, "k5k": k5k, "Z": Z, "IDX": IDX}, f)
    return K, S, Z


def gesamt(S, ohne=None):
    aus = {}
    for name, end in (("Gesamt lang", "lang"), ("Gesamt kurz", "kurz")):
        teile = [S[k] for k in S if k.endswith(end) and not k.startswith("Gesamt") and (ohne is None or not k.startswith(ohne))]
        aus[name] = V.score(pd.concat(teile, axis=1).sum(axis=1, min_count=6 if ohne is None else 5), +1)
    return aus


# ══ Kern: Abstand und Nullwelt auf den Stichtagen ═══════════════════════════════════════════════════════════════════════
def vorbereiten(s, y, ab):
    ok = s.notna().values & y.notna().values & (IDX >= pd.Timestamp(ab))
    pos = np.where(ok)[0]
    if len(pos) < 800:
        return None
    dts = IDX[pos]
    stich = np.where(dts.day == 1)[0]
    ep = np.array([V.epoche(d) for d in dts[stich]])
    return pos, stich, ep


def abstand_v(sv, yv):
    """sv (..., m) Scores, yv (m,) Ziel -> mittleres Ziel +1 minus -1 (NaN bei < 5 je Klasse)."""
    p, m = sv == 1, sv == -1
    np_, nm = p.sum(-1), m.sum(-1)
    a = (p * yv).sum(-1) / np.maximum(np_, 1) - (m * yv).sum(-1) / np.maximum(nm, 1)
    return np.where((np_ >= 5) & (nm >= 5), a, np.nan)


def pruefe(s, y, ab, verschiebungen=None):
    v = vorbereiten(s, y, ab)
    if v is None:
        return None
    pos, stich, ep = v
    ss, yy = s.values[pos], y.values[pos]
    sv, yv = ss[stich], yy[stich]
    a = float(abstand_v(sv, yv))
    eps = {e: float(abstand_v(sv[ep == e], yv[ep == e])) if (ep == e).any() else np.nan for e in ("E1", "E2", "E3")}
    n = len(pos)
    k = verschiebungen if verschiebungen is not None else RNG.integers(RAND, n - RAND, NZ)
    k = k[k < n - RAND]
    null = abstand_v(ss[(stich[None, :] - k[:, None]) % n], yv)
    null = null[~np.isnan(null)]
    p_hoch = (np.sum(null >= a) + 1) / (len(null) + 1)
    p_tief = (np.sum(null <= a) + 1) / (len(null) + 1)
    plus, minus = yv[sv == 1], yv[sv == -1]
    spiegel = (np.mean(plus >= STARK[0]), np.mean(minus >= STARK[0]), np.mean(plus <= STARK[1]), np.mean(minus <= STARK[1]))
    return dict(a=a, ep=eps, p_hoch=p_hoch, p_tief=p_tief, n_p=int((sv == 1).sum()), n_m=int((sv == -1).sum()), spiegel=spiegel,
                null_sd=float(np.std(null)), nnull=len(null))


def urteil(r, alpha):
    if r is None or r["a"] != r["a"]:
        return "zu wenig Daten"
    richt = +1 if r["p_hoch"] <= alpha else (-1 if r["p_tief"] <= alpha else 0)
    if richt == 0:
        return "nicht entscheidbar (Nullwelt)"
    fehlt = [e for e in ("E1", "E2", "E3") if r["ep"][e] != r["ep"][e]]
    if fehlt:
        return "nicht entscheidbar (%s nicht pruefbar)" % "/".join(fehlt)
    if any(np.sign(r["ep"][e]) != richt for e in ("E1", "E2", "E3")):
        return "nicht entscheidbar (Vorzeichen kippt)"
    hp, hm, tp, tm = r["spiegel"]
    sp = (hp > hm and tp < tm) if richt > 0 else (hp < hm and tp > tm)
    if not sp:
        return "nicht entscheidbar (Spiegelprobe)"
    return "TRAEGT" if richt > 0 else "SCHADET"


def zeile(name, r, alpha, rolle):
    if r is None:
        return "  %-28s zu wenig Daten" % name
    e = " ".join("%s %s" % (k, "%+6.1f" % (100 * r["ep"][k]) if r["ep"][k] == r["ep"][k] else "   -  ") for k in ("E1", "E2", "E3"))
    hp, hm, tp, tm = r["spiegel"]
    u = urteil(r, alpha) if rolle == "Urteil" else "(%s) %s" % (rolle, urteil(r, alpha))
    return "  %-28s n+ %3d n- %3d · %+7.1f %% · %s · p hoch %.4f tief %.4f · Spiegel auf %2.0f/%2.0f ab %2.0f/%2.0f %% · %s" % (
        name, r["n_p"], r["n_m"], 100 * r["a"], e, r["p_hoch"], r["p_tief"], 100 * hp, 100 * hm, 100 * tp, 100 * tm, u)


# ══ Selbsttest ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def phasen_zufall(x):
    """Gleiches Spektrum, zufaellige Phasen (Theiler 1992) auf dem zusammenhaengenden Teil der Reihe."""
    a, b = x.first_valid_index(), x.last_valid_index()
    t = x.loc[a:b].ffill()
    v = t.values - t.values.mean()
    f = np.fft.rfft(v)
    ph = RNG.uniform(0, 2 * np.pi, len(f))
    ph[0] = 0.0
    if len(v) % 2 == 0:
        ph[-1] = 0.0
    r = np.fft.irfft(np.abs(f) * np.exp(1j * ph), n=len(v)) + t.values.mean()
    return pd.Series(r, index=t.index).reindex(IDX)


def selbsttest(K, Z, n_merk=200):
    roh = [(n + " lang", lg) for n, (lg, _, _, _) in K.items()] + [(n + " kurz", kz) for n, (_, _, kz, _) in K.items() if kz is not None]
    ziele = [z for z in Z if z.startswith("T")]
    stufen = {"Bonferroni Kanal": A_KANAL, "0,025 je Seite": 0.025, "0,05 je Seite": 0.05}
    zaehl = {z: {s: 0 for s in stufen} for z in ziele}
    voll = {z: 0 for z in ziele}
    gueltig = {z: 0 for z in ziele}
    for i in range(n_merk):
        _, x = roh[int(RNG.integers(len(roh)))]
        s = V.score(phasen_zufall(x), +1)
        for z in ziele:
            y, ab = Z[z]
            r = pruefe(s, y, ab)
            if r is None or r["a"] != r["a"]:
                continue
            gueltig[z] += 1
            for st, al in stufen.items():
                zaehl[z][st] += int(min(r["p_hoch"], r["p_tief"]) <= al)
            voll[z] += int(urteil(r, A_KANAL) in ("TRAEGT", "SCHADET"))
    print("\nSELBSTTEST (a): %d phasen-randomisierte Makroreihen (gleiches Spektrum, kein Zusammenhang mit dem Ziel)" % n_merk)
    ergebnis = True
    for z in ziele:
        g = gueltig[z]
        teile = []
        for st, al in stufen.items():
            soll = 2 * (np.floor(al * (NZ + 1) - 1) + 1) / (NZ + 1)
            grenze = g * soll + 2 * np.sqrt(g * soll * (1 - soll))
            ok = zaehl[z][st] <= grenze
            ergebnis &= ok
            teile.append("%s %d (Soll %.1f, Grenze %.1f) %s" % (st, zaehl[z][st], g * soll, grenze, "ok" if ok else "UEBER"))
        print("  %-22s gueltig %3d · %s · volles Urteil %d" % (z, g, " · ".join(teile), voll[z]))
    print("  => Selbsttest (a) %s" % ("BESTANDEN" if ergebnis else "NICHT bestanden"))
    return ergebnis


def aufloesung(K, Z, n_merk=60, betas=(0.0, 0.05, 0.1, 0.2, 0.3, 0.5)):
    roh = [(n + " lang", lg) for n, (lg, _, _, _) in K.items()] + [(n + " kurz", kz) for n, (_, _, kz, _) in K.items() if kz is not None]
    print("\nSELBSTTEST (b): Pflanzung Ziel + beta * sd(Ziel) * z(Merkmal), je Staerke %d Merkmale; Fund = p <= Bonferroni (Kanal)" % n_merk)
    for z in [z for z in Z if z.startswith("T")]:
        y, ab = Z[z]
        sd = float(y[IDX >= pd.Timestamp(ab)].std())
        merk = []
        for i in range(n_merk):
            _, x = roh[int(RNG.integers(len(roh)))]
            merk.append(phasen_zufall(x))
        teile = []
        for b in betas:
            fund, abst, fund_ep = 0, [], 0
            for x in merk:
                zx = (x - x.mean()) / x.std()
                yp = y + b * sd * zx
                r = pruefe(V.score(x, +1), yp, ab)
                if r is None or r["a"] != r["a"]:
                    continue
                abst.append(r["a"])
                f = r["p_hoch"] <= A_KANAL
                fund += int(f)
                fund_ep += int(f and all(r["ep"][e] == r["ep"][e] and r["ep"][e] > 0 for e in ("E1", "E2", "E3")))
            teile.append("beta %.2f: Abstand %+5.1f %% Fund %3.0f %% (mit Epochen %3.0f %%)" % (
                b, 100 * np.median(abst), 100 * fund / max(len(abst), 1), 100 * fund_ep / max(len(abst), 1)))
        print("  %s (sd %.3f)\n    %s" % (z, sd, "\n    ".join(teile)))


# ══ Hauptlauf ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    K, S, Z = eingang()
    S.update(gesamt(S))
    print("P51 MESSUNG Makro-Umfeld (§51.5, Stufe 2) · Daten bis %s · Nullwelt %d zirkulaere Verschiebungen · Bonferroni Kanal %.4f, Gesamt %.4f je Seite\n"
          % (IDX[-1].date(), NZ, A_KANAL, A_GESAMT))
    print("Spalten: n je Klasse · Abstand guenstig-unguenstig (log-Ertrag) · je Epoche · p je Seite (Stufung) · Spiegel: Anteil >= +20 %% guenstig/unguenstig, <= -20 %% guenstig/unguenstig")
    urteile = []
    for zn, (y, ab) in Z.items():
        rolle = ROLLE[zn[0]]
        print("=" * 170)
        print("%s  [%s]" % (zn, rolle))
        for sn, s in S.items():
            alpha = A_GESAMT if sn.startswith("Gesamt") else A_KANAL
            r = pruefe(s, y, ab)
            print(zeile(sn, r, alpha, rolle))
            if rolle == "Urteil" and r is not None:
                u = urteil(r, alpha)
                urteile.append((zn, sn, u, r))
    print("\n" + "=" * 170)
    print("URTEILE KRYPTO (Plan §51.5):")
    for zn, sn, u, r in urteile:
        if u in ("TRAEGT", "SCHADET") or min(r["p_hoch"], r["p_tief"]) <= 0.025:
            print("  %-20s %-28s %+6.1f %%  p %.4f  -> %s" % (zn, sn, 100 * r["a"], min(r["p_hoch"], r["p_tief"]), u))
    n_t = sum(u == "TRAEGT" for *_, u, _ in [(a, b, c, d) for a, b, c, d in urteile])
    n_s = sum(u == "SCHADET" for *_, u, _ in [(a, b, c, d) for a, b, c, d in urteile])
    print("  => TRAEGT %d · SCHADET %d · von %d Pruefungen" % (n_t, n_s, len(urteile)))

    print("\nWEGLASSPROBE (Gesamt ohne je einen Kanal; Krypto):")
    for zn in [z for z in Z if z.startswith("T")]:
        y, ab = Z[zn]
        for gname in ("Gesamt lang", "Gesamt kurz"):
            basis = pruefe(S[gname], y, ab)
            teile = []
            for kn in K:
                g = gesamt({k: v for k, v in S.items() if not k.startswith("Gesamt")}, ohne=kn)[gname]
                r = pruefe(g, y, ab)
                teile.append("%s %+5.1f (p %.3f)" % (kn.split()[0], 100 * r["a"], min(r["p_hoch"], r["p_tief"])) if r and r["a"] == r["a"] else kn.split()[0] + " -")
            print("  %-20s %-11s alle %+5.1f %% (p %.4f) · ohne: %s" % (zn, gname, 100 * basis["a"], min(basis["p_hoch"], basis["p_tief"]), " · ".join(teile)))

    selbsttest(K, Z)
    aufloesung(K, Z)

    print("\nSTAND HEUTE (%s): %s" % (IDX[-1].date(), " · ".join("%s %s" % (k, {1.0: "+", -1.0: "-", 0.0: "0"}.get(v.dropna().iloc[-1], "?") if v.notna().any() else "?")
                                                         for k, v in S.items())))
    print("Laufzeit %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
