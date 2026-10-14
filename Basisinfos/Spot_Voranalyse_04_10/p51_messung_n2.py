"""P51 MESSUNG Makro-Umfeld, Nullwelt N2 (Spot §51.7) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p51_messung_n2.py

WARUM N2: Die Nullwelt N1 aus §51.5 (zirkulaere Zeitverschiebung, Rand 365 T) hat den eigenen Selbsttest NICHT bestanden
(p51_messung.txt: 9 von 200 Zufallsmerkmalen ueber Bonferroni, Soll 0,8). Ursache: bei traegen Reihen ist T(k) glatt in k; alle
Verschiebungen nahe dem Gipfel gelten gegen ihre ferne Vergleichsmenge als extrem -> die Quote waechst mit der Gipfelbreite.
Das ist ein Fehler meiner Eichung, nicht der Hypothese; das Urteil (Bonferroni, Epochen, Spiegelprobe) bleibt unveraendert.

N2 = Surrogat-Nullwelt fuer das MERKMAL: alle Kanalreihen werden GEMEINSAM phasen-randomisiert (gleiche Zufallsphasen fuer alle
Spalten, Prichard/Theiler 1994): Spektrum jeder Reihe UND Kreuzspektrum bleiben, der Bezug zum Ziel nicht. Danach exakt dieselbe
Einteilung (Drittel im 5-J-Fenster, Gesamt aus den Surrogat-Kanaelen). Die Einteilung ist rang-basiert, die Randverteilung
(Nicht-Normalitaet) spielt daher keine Rolle. Gemeinsamer Zeitraum ab 2006-04 (Dollar); fuer Stichtage ab 2011-04 sind die echten
Scores damit unveraendert (5-J-Fenster liegt ganz im Zeitraum).

Selbsttest N2 (a): ECHTE Kanaele gegen 200 synthetische Ziele (phasen-randomisierte Tagesertraege von BTC bzw. Korb/BTC; langsame
Zyklen bleiben im Spektrum), Fehlalarm je Stufe gegen das Soll aus der Stufung. (b) Pflanzung synth. Ziel + beta*sd*z(echter Kanal).
"""
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p51_vorpruefung as V   # noqa: E402

RNG = np.random.default_rng(20261053)
NZ, N_SELBST, N_PFL = 1000, 200, 60
A_KANAL, A_GESAMT = 0.025 / 9, 0.0125
STARK = np.log(1.2), np.log(0.8)
CACHE = os.path.join("data", "_spot", "p51_eingang.pkl")
ROLLE = {"T": "Urteil", "M": "Probe", "A": "Auskunft"}


# ══ Eingang ═════════════════════════════════════════════════════════════════════════════════════════════════════════════
def eingang():
    with open(CACHE, "rb") as f:
        D = pickle.load(f)
    if "preise" not in D:
        import s1_messung as S1
        s1 = S1.baue()
        D["preise"] = {"BTC": V.coinmetrics_btc(), "Korb/BTC": (s1["korb"] / s1["Bi"]).dropna()}
        with open(CACHE, "wb") as f:
            pickle.dump(D, f)
    return D


def spalten(K):
    """Die stetigen Kanalreihen als Matrix (Name -> Reihe, Vorzeichen); K5 kurz wird aus Kurve und 2 J abgeleitet."""
    sp = {}
    for n, (lg, vl, kz, vk) in K.items():
        sp[n + " lang"] = (lg, vl)
        if kz is not None:
            sp[n + " kurz"] = (kz, vk)
    return sp


def scores_aus(reihen, sp, idx):
    """reihen: dict Name -> pd.Series (echt oder Surrogat) auf idx. Gibt dict Score-Name -> pd.Series und die Gesamt-Varianten."""
    S = {n: V.score(reihen[n], sp[n][1]) for n in sp}
    kurve, zwei = reihen["K5 Kurve lang"], reihen["K4 Zinspfad 2J lang"]
    dk, d2 = kurve - kurve.shift(91), zwei - zwei.shift(91)
    k5 = pd.Series(np.where((dk > 0) & (d2 < 0), 1.0, np.where((dk > 0) & (d2 > 0), -1.0, 0.0)), index=idx)
    k5[dk.isna() | d2.isna()] = np.nan
    S["K5 Kurve kurz"] = k5
    kan = sorted({n.rsplit(" ", 1)[0] for n in S})
    for gname, end in (("Gesamt lang", "lang"), ("Gesamt kurz", "kurz")):
        teile = {k: S[k + " " + end] for k in kan if (k + " " + end) in S}
        M = pd.concat(teile, axis=1)
        S[gname] = V.score(M.sum(axis=1, min_count=6), +1)
        for k in teile:
            S["%s ohne %s" % (gname, k.split()[0])] = V.score(M.drop(columns=k).sum(axis=1, min_count=5), +1)
    return S


def surrogat_matrix(X):
    """Gemeinsame Phasen-Randomisierung der Spalten von X (T x m, ohne Luecken)."""
    mu = X.mean(axis=0)
    F = np.fft.rfft(X - mu, axis=0)
    ph = RNG.uniform(0, 2 * np.pi, F.shape[0])
    ph[0] = 0.0
    if X.shape[0] % 2 == 0:
        ph[-1] = 0.0
    return np.fft.irfft(F * np.exp(1j * ph)[:, None], n=X.shape[0], axis=0) + mu


def phasen_reihe(v):
    mu = v.mean()
    F = np.fft.rfft(v - mu)
    ph = RNG.uniform(0, 2 * np.pi, len(F))
    ph[0] = 0.0
    if len(v) % 2 == 0:
        ph[-1] = 0.0
    return np.fft.irfft(np.abs(F) * np.exp(1j * (np.angle(F) + ph)), n=len(v)) + mu


# ══ Statistik ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
def abstand_v(sv, yv):
    p, m = sv == 1, sv == -1
    np_, nm = p.sum(-1), m.sum(-1)
    a = (p * yv).sum(-1) / np.maximum(np_, 1) - (m * yv).sum(-1) / np.maximum(nm, 1)
    return np.where((np_ >= 5) & (nm >= 5), a, np.nan)


def pruefe(sv, yv, ep, bank):
    """sv (m,) echter Score, yv (m,) Ziel, ep (m,) Epoche, bank (NZ, m) Surrogat-Scores - alle auf denselben Stichtagen."""
    ok = ~np.isnan(sv) & ~np.isnan(yv)
    if ok.sum() < 30:
        return None
    s, y, e = sv[ok], yv[ok], ep[ok]
    a = float(abstand_v(s, y))
    eps = {k: float(abstand_v(s[e == k], y[e == k])) if (e == k).any() else np.nan for k in ("E1", "E2", "E3")}
    b = bank[:, ok]
    b = np.where(np.isnan(b), 0.0, b)      # Surrogat ohne Score an einem Tag zaehlt als Mitte (selten, nur am Rand)
    null = abstand_v(b, y)
    null = null[~np.isnan(null)]
    p_hoch = (np.sum(null >= a) + 1) / (len(null) + 1)
    p_tief = (np.sum(null <= a) + 1) / (len(null) + 1)
    plus, minus = y[s == 1], y[s == -1]
    sp = (np.mean(plus >= STARK[0]), np.mean(minus >= STARK[0]), np.mean(plus <= STARK[1]), np.mean(minus <= STARK[1])) if len(plus) and len(minus) else (np.nan,) * 4
    return dict(a=a, ep=eps, p_hoch=p_hoch, p_tief=p_tief, n_p=int((s == 1).sum()), n_m=int((s == -1).sum()), spiegel=sp, nnull=len(null))


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
    if not ((hp > hm and tp < tm) if richt > 0 else (hp < hm and tp > tm)):
        return "nicht entscheidbar (Spiegelprobe)"
    return "TRAEGT" if richt > 0 else "SCHADET"


def zeile(name, r, alpha, rolle):
    if r is None:
        return "  %-30s zu wenig Daten" % name
    e = " ".join("%s %s" % (k, "%+6.1f" % (100 * r["ep"][k]) if r["ep"][k] == r["ep"][k] else "   -  ") for k in ("E1", "E2", "E3"))
    hp, hm, tp, tm = r["spiegel"]
    u = urteil(r, alpha)
    return "  %-30s n+ %3d n- %3d | %+7.1f %% | %s | p hoch %.4f tief %.4f | Spiegel auf %2.0f/%2.0f ab %2.0f/%2.0f %% | %s%s" % (
        name, r["n_p"], r["n_m"], 100 * r["a"], e, r["p_hoch"], r["p_tief"], 100 * hp, 100 * hm, 100 * tp, 100 * tm,
        "" if rolle == "Urteil" else "(%s) " % rolle, u)


def ziel_aus_preis(p, h, idx):
    pd_ = p.reindex(p.index.union(idx)).ffill().reindex(idx)
    return np.log(pd_.shift(-(1 + h)) / pd_.shift(-1))


def synth_preis(p):
    """Phasen-randomisierte Tages-log-Ertraege (gleiches Spektrum inkl. langsamer Zyklen), wieder aufsummiert."""
    p = p.dropna().sort_index()
    p = p.reindex(pd.date_range(p.index[0], p.index[-1], freq="D")).ffill()
    r = np.diff(np.log(p.values))
    rs = phasen_reihe(r)
    return pd.Series(np.exp(np.concatenate([[0.0], np.cumsum(rs)])) * p.values[0], index=p.index)


# ══ Hauptlauf ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    D = eingang()
    K, Z, IDX0 = D["K"], D["Z"], D["IDX"]
    sp = spalten(K)
    start = max(r.first_valid_index() for r, _ in sp.values())
    idx = IDX0[IDX0 >= start]
    X = pd.DataFrame({n: r.reindex(idx).ffill() for n, (r, _) in sp.items()})
    assert not X.isna().any().any(), "Luecke im gemeinsamen Zeitraum"
    echt = scores_aus({n: X[n] for n in X}, sp, idx)
    namen = list(echt)
    stich = np.where(idx.day == 1)[0]
    sd = idx[stich]
    ep = np.array([V.epoche(d) for d in sd])
    print("P51 MESSUNG N2 (Surrogat-Nullwelt, §51.7) · Zeitraum %s bis %s · %d Stichtage · %d gemeinsame Surrogate · Bonferroni Kanal %.4f, Gesamt %.4f je Seite"
          % (idx[0].date(), idx[-1].date(), len(stich), NZ, A_KANAL, A_GESAMT))
    # Bank: NZ x Score x Stichtag
    bank = np.full((NZ, len(namen), len(stich)), np.nan, dtype=np.float32)
    for i in range(NZ):
        Xs = surrogat_matrix(X.values)
        Ss = scores_aus({n: pd.Series(Xs[:, j], index=idx) for j, n in enumerate(X.columns)}, sp, idx)
        for j, n in enumerate(namen):
            bank[i, j] = Ss[n].values[stich]
        if (i + 1) % 200 == 0:
            print("  ... %d Surrogate (%.0f s)" % (i + 1, time.time() - t0), flush=True)
    E = np.array([echt[n].values[stich] for n in namen])
    with open(os.path.join("data", "_spot", "p51_bank_n2.pkl"), "wb") as f:
        pickle.dump({"namen": namen, "stich": sd, "bank": bank, "echt": E}, f)

    haupt = [n for n in namen if " ohne " not in n]
    urteile = []
    print("\nSpalten: n je Klasse | Abstand guenstig-unguenstig (log) | je Epoche | p je Seite (Stufung) | Spiegel >= +20 %% / <= -20 %% guenstig/unguenstig")
    for zn, (y, ab) in Z.items():
        rolle = ROLLE[zn[0]]
        yv = y.reindex(sd).values.astype(float)
        yv[sd < pd.Timestamp(ab)] = np.nan
        print("=" * 175)
        print("%s  [%s]" % (zn, rolle))
        for n in haupt:
            j = namen.index(n)
            alpha = A_GESAMT if n.startswith("Gesamt") else A_KANAL
            r = pruefe(E[j], yv, ep, bank[:, j])
            print(zeile(n, r, alpha, rolle))
            if rolle == "Urteil" and r is not None:
                urteile.append((zn, n, urteil(r, alpha), r))
    print("\n" + "=" * 175)
    print("URTEILE KRYPTO (Plan §51.5, Nullwelt N2):")
    for zn, n, u, r in urteile:
        if u in ("TRAEGT", "SCHADET") or min(r["p_hoch"], r["p_tief"]) <= 0.05:
            print("  %-20s %-28s %+6.1f %%  p %.4f  -> %s" % (zn, n, 100 * r["a"], min(r["p_hoch"], r["p_tief"]), u))
    print("  => TRAEGT %d · SCHADET %d · von %d Pruefungen" % (sum(u == "TRAEGT" for _, _, u, _ in urteile), sum(u == "SCHADET" for _, _, u, _ in urteile), len(urteile)))

    print("\nWEGLASSPROBE (Gesamt ohne je einen Kanal, Krypto, p gegen N2):")
    for zn in [z for z in Z if z.startswith("T")]:
        y, ab = Z[zn]
        yv = y.reindex(sd).values.astype(float)
        yv[sd < pd.Timestamp(ab)] = np.nan
        for g in ("Gesamt lang", "Gesamt kurz"):
            rb = pruefe(E[namen.index(g)], yv, ep, bank[:, namen.index(g)])
            teile = []
            for n in [n for n in namen if n.startswith(g + " ohne")]:
                r = pruefe(E[namen.index(n)], yv, ep, bank[:, namen.index(n)])
                teile.append("%s %+5.1f (p %.3f)" % (n.split()[-1], 100 * r["a"], min(r["p_hoch"], r["p_tief"])) if r and r["a"] == r["a"] else n.split()[-1] + " -")
            print("  %-20s %-11s alle %+5.1f %% (p %.4f) | ohne: %s" % (zn, g, 100 * rb["a"], min(rb["p_hoch"], rb["p_tief"]), " · ".join(teile)))

    # Selbsttest (a): echte Kanaele gegen synthetische Ziele
    print("\nSELBSTTEST N2 (a): echte Kanaele gegen %d synthetische Ziele (phasen-randomisierte Tagesertraege)" % N_SELBST)
    stufen = {"Bonferroni Kanal": A_KANAL, "0,025 je Seite": 0.025, "0,05 je Seite": 0.05}
    ziele_t = {"T1 BTC 90T": ("BTC", 90, "2013-01-01"), "T1 BTC 180T": ("BTC", 180, "2013-01-01"), "T2 Altkorb/BTC 90T": ("Korb/BTC", 90, "2019-01-01")}
    gesamt_ok = True
    synth = {zn: [] for zn in ziele_t}
    for zn, (pn, h, ab) in ziele_t.items():
        zaehl, n_t, voll = {s: 0 for s in stufen}, 0, 0
        for i in range(N_SELBST):
            yv = ziel_aus_preis(synth_preis(D["preise"][pn]), h, idx).reindex(sd).values.astype(float)
            yv[sd < pd.Timestamp(ab)] = np.nan
            if i < N_PFL:
                synth[zn].append(yv)
            for n in haupt:
                j = namen.index(n)
                r = pruefe(E[j], yv, ep, bank[:, j])
                if r is None or r["a"] != r["a"]:
                    continue
                n_t += 1
                for s, al in stufen.items():
                    zaehl[s] += int(min(r["p_hoch"], r["p_tief"]) <= al)
                voll += int(urteil(r, A_GESAMT if n.startswith("Gesamt") else A_KANAL) in ("TRAEGT", "SCHADET"))
        teile = []
        for s, al in stufen.items():
            soll = 2 * (np.floor(al * (NZ + 1) - 1) + 1) / (NZ + 1)
            grenze = n_t * soll + 2 * np.sqrt(n_t * soll * (1 - soll))
            ok = zaehl[s] <= grenze
            gesamt_ok &= ok
            teile.append("%s %d (Soll %.1f, Grenze %.1f) %s" % (s, zaehl[s], n_t * soll, grenze, "ok" if ok else "UEBER"))
        print("  %-20s Pruefungen %4d | %s | volles Urteil %d" % (zn, n_t, " | ".join(teile), voll))
    print("  => Selbsttest N2 (a) %s" % ("BESTANDEN" if gesamt_ok else "NICHT bestanden"))

    # Selbsttest (b): Pflanzung in synthetische Ziele mit echtem Kanal
    print("\nSELBSTTEST N2 (b): Pflanzung synth. Ziel + beta*sd*z(echte Kanalreihe), %d Paare je Staerke; Fund = p hoch <= Bonferroni Kanal" % N_PFL)
    kanal_namen = [n for n in sp]
    for zn in ziele_t:
        teile = []
        for b in (0.0, 0.1, 0.2, 0.3, 0.5):
            fund, fund_ep, ab_l = 0, 0, []
            for i, yv in enumerate(synth[zn]):
                n = kanal_namen[int(RNG.integers(len(kanal_namen)))]
                x = X[n].values[stich] * sp[n][1]
                zx = (x - np.nanmean(x)) / np.nanstd(x)
                sdy = np.nanstd(yv)
                r = pruefe(E[namen.index(n)], yv + b * sdy * zx, ep, bank[:, namen.index(n)])
                if r is None or r["a"] != r["a"]:
                    continue
                ab_l.append(r["a"])
                f = r["p_hoch"] <= A_KANAL
                fund += int(f)
                fund_ep += int(f and all(r["ep"][e] == r["ep"][e] and r["ep"][e] > 0 for e in ("E1", "E2", "E3")))
            m = max(len(ab_l), 1)
            teile.append("beta %.1f: Abstand %+5.1f %% | Fund %3.0f %% | mit Epochen %3.0f %%" % (b, 100 * np.median(ab_l), 100 * fund / m, 100 * fund_ep / m))
        print("  %s\n    %s" % (zn, "\n    ".join(teile)))

    print("\nSTAND HEUTE (%s): %s" % (idx[-1].date(), " · ".join("%s %s" % (n, {1.0: "+", -1.0: "-", 0.0: "0"}.get(echt[n].dropna().iloc[-1], "?"))
                                                         for n in haupt)))
    print("Laufzeit %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
