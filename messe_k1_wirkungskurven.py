# -*- coding: utf-8 -*-
"""K1 Schritt 1: die WIRKUNGSKURVEN je Beitrag - roh und selbstbezogen, 12 Stufen, gegen die Phase.

**28.09.2026.** Voranalyse `Basisinfos/Voranalyse_K1_Wirkungskurven_28_09.md`,
A1-A4 abgestimmt. Nutzer: *"ja, A1 bis A4 wie empfohlen ... dann laden und
messen - zu A4: wichtig zu unterscheiden, wie weit gestiegen - nur
'bestaetigte' Bewegung, also positiv, oder die Bewegung ist bereits gelaufen.
Nicht so einfach, sonst wird es ein Blocker."*

VORAB FESTGELEGT (W1-W13 der Voranalyse)
    Merkmale     --gruppe voll: funding_vortag, kaeufer_1h/6h/24h/rel,
                 premium_jetzt/24h, momentum_kurz, rsi, ema_abstand_atr,
                 bandenge (11) · --gruppe termin: konten_verh, top_konten_verh,
                 taker_verh, oi_aenderung (4, nach Teil B)
    Formen       roh und selbstbezogen (Wert minus Median der eigenen letzten
                 720 h, nur Vergangenheit) - je Merkmal zwei Kurven
    Stufen       12: < P1, P1-P10, P10-P20 ... P80-P90, P90-P99, > P99; Grenzen
                 aus der SUCHE, gepoolt, absolute Werte
    Lehrer       q5 (+5 vor -5 %, 24 h) urteilt
    Bezug        Phase (eigenes Asset, letzte 12 Monate, bekannte Ausgaenge);
                 Kontrollen Moment (Monat) und Tag (alle Assets am selben Tag)
    Anker        feste Tagesanker 00/06/12/18 UTC
    Nullwelt     Zeitverschiebung JE ASSET: die Merkmalsreihe des Assets
                 kreisfoermig um >= 60 Tage (1.440 Stunden-Anker) verschoben,
                 40 Ziehungen
    Kennzahl     S = Summe ueber die Stufen von (Anker x Dq^2); z gegen die
                 Nullwelt; Grenze Bestes-von-N (N Kurven), 90. Perzentil
    TRAEGT       z(S) > Grenze (Suche) UND Rangkorrelation des Profils Suche
                 gegen Pruefung >= 0,5 UND beide Randstufen mit gleichem
                 Vorzeichen in der Pruefung UND >= 3 von 4 Jahren mit positiver
                 Profilkorrelation zur Suche UND >= 60 % der Assets mit
                 positiver Profilkorrelation
    Teilung      schrumpft S gegen die Tages-Kontrolle auf weniger als die
                 Haelfte -> Hinweis: in _markt / _eigen teilen (W11)
    A4 / W12     je tragender Kurve: Randstufen-Dq je bisherigem Anstieg der
                 letzten 24 h in eigener ATR (< 0, 0-0,5, 0,5-1, 1-2, 2-3, > 3);
                 BESTAETIGT = Bereich, in dem die Lage noch positiv traegt,
                 GELAUFEN = wo sie kippt - die Grenze wird gemessen
    Pflicht      G1 Vorgriff im Normal · G4 Positivkontrolle (lineare Kurve
                 bekannter Staerke gepflanzt) · G7 Korrelationsmatrix ·
                 Altersachse (Merkmal 6/12/24 h alt)

    python messe_k1_wirkungskurven.py --menge unverzerrt:1 --gruppe voll

NUR LESEND (`mode=ro`). Kein Stop, kein Trailing, keine Gebuehren (Regel 2).
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
import messe_e2f_richtungsdaten as F2                             # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402

B0 = datetime(2020, 1, 1)
GRUPPEN = {"voll": ("funding_vortag", "kaeufer_1h", "kaeufer_6h", "kaeufer_24h", "kaeufer_rel",
                    "premium_jetzt", "premium_24h", "momentum_kurz", "rsi", "ema_abstand_atr",
                    "bandenge"),
           "termin": ("konten_verh", "top_konten_verh", "taker_verh", "oi_aenderung"),
           # W11 (Voranalyse K1): gegen die Tages-Kontrolle blieb von funding 3 %,
           # von premium_24h 8 % - Teilung in Markt (Median aller Assets zur
           # Stunde, ein KONTEXT) und eigen (Asset minus Markt, ein BEITRAG)
           "teilung": ("funding_vortag", "premium_jetzt", "premium_24h")}
PERZ = (1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99)
GITTER = (0, 6, 12, 18)
JAHR_H = 8760
SELBST_H = 720
ZIEHUNGEN, SAAT = 40, 20261007
MIN_VERSATZ = 1440
ANSTIEG = (-np.inf, 0.0, 0.5, 1.0, 2.0, 3.0, np.inf)


def _h(d):
    return int((d - B0).total_seconds() // 3600)


SUCHE = (_h(datetime(2023, 1, 1)), _h(datetime(2025, 1, 1)))
PRUEF = (_h(datetime(2025, 1, 1)), _h(datetime(2026, 9, 1)))


def spearman(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 5:
        return np.nan
    rx = pd.Series(x[ok]).rank().to_numpy(); ry = pd.Series(y[ok]).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    E2.menge_aus_argv()
    gruppe = sys.argv[sys.argv.index("--gruppe") + 1] if "--gruppe" in sys.argv else "voll"
    MERK = GRUPPEN[gruppe]
    print("=" * 120)
    print("K1 SCHRITT 1 - WIRKUNGSKURVEN · MENGE %s · GRUPPE %s%s" % (
        E2.MENGE, gruppe, " · NULLWELT GEMEINSAM (Kontext-Methode)" if "--gemeinsam" in sys.argv else ""))
    print("=" * 120)
    # hmax 72: der Lader rechnet die Kontrollfenster 6/72 h immer mit
    D = E2.lade(hmax=72, erste=(("u5", 1.05, True), ("d5", 0.95, False)), mit_atr=True)
    SYM, STD, syms = D["SYM"], D["STD"], D["syms"]
    A = ((D["T"]["u5"] <= 24) & (D["T"]["u5"] < D["T"]["d5"])).astype(np.float32)
    B = ((D["T"]["d5"] <= 24) & (D["T"]["d5"] <= D["T"]["u5"])).astype(np.float32)
    VOR24 = D["X"]["vor24"]; ATR = D["ATR"]
    FV = {m: D["F"][m].astype(np.float32) for m in E2.MERKMALE if m in MERK}
    del D
    n = len(SYM)
    MON = monat_von(STD); JAHR = (MON // 12).astype(np.int16)
    rng = np.random.default_rng(SAAT)

    # Richtungsdaten (Kaeuferanteil, Premium) - Bestand + Eingestellte
    brauche = [m for m in MERK if m.startswith(("kaeufer", "premium"))]
    if brauche:
        cr = sqlite3.connect("file:%s?mode=ro" % F2.RICHTUNG_DB, uri=True)
        cr2 = (sqlite3.connect("file:%s?mode=ro" % E2.EINGESTELLT_DB, uri=True)
               if E2.MENGE != "bestand" else None)
        for m in brauche:
            FV[m] = np.full(n, np.nan, np.float32)
        for si in np.unique(SYM):
            r = F2.richtungsmerkmale(syms[si], cr, cr2)
            if r is None:
                continue
            h0, M = r
            mk = SYM == si
            pos = STD[mk] - h0
            ok = (pos >= 0) & (pos < len(M["kaeufer_1h"]))
            for m in brauche:
                w = np.full(mk.sum(), np.nan, np.float32)
                w[ok] = M[m][pos[ok]]
                FV[m][mk] = w

    if gruppe == "teilung":
        # Markt = Median aller Assets zur selben Stunde (Bestand + Eingestellte der
        # Menge); eigen = Asset minus Markt. Beide werden als eigene Merkmale
        # gefuehrt (roh und selbstbezogen wie alle anderen)
        for m in list(MERK):
            v = pd.Series(FV[m].astype(float))
            mk = v.groupby(STD).transform("median").to_numpy()
            FV[m + "_markt"] = mk.astype(np.float32)
            FV[m + "_eigen"] = (FV[m] - mk).astype(np.float32)
            del FV[m]
        teil_t = ("_markt",) if "--nur-markt" in sys.argv else ("_markt", "_eigen")
        MERK = tuple(m + t for m in MERK for t in teil_t)
        for m in list(FV):
            if m not in MERK:
                del FV[m]
    # je Asset sortiert (lade liefert je Symbol zeitlich geordnet)
    ordnung = np.lexsort((STD, SYM))
    teile = np.split(ordnung, np.flatnonzero(np.diff(SYM[ordnung])) + 1)

    # selbstbezogene Form: Wert minus Median der eigenen letzten 720 h (nur Vergangenheit)
    KURVEN = {}
    for m in MERK:
        v = FV[m]
        s = np.full(n, np.nan, np.float32)
        for tl in teile:
            ser = pd.Series(v[tl].astype(float),
                            index=pd.to_datetime(STD[tl].astype("int64") * 3600, unit="s"))
            med = ser.rolling("%dh" % SELBST_H, closed="left", min_periods=240).median().to_numpy()
            s[tl] = v[tl] - med
        KURVEN[m + " roh"] = v
        KURVEN[m + " selbst"] = s
    namen = list(KURVEN)

    # Phasen-Normal (wie K3)
    def normal(a, b, W, vorgriff=False):
        na, nb = np.full(n, np.nan, np.float32), np.full(n, np.nan, np.float32)
        for tl in teile:
            st = STD[tl]
            ca = np.concatenate([[0.0], np.cumsum(a[tl])]); cb = np.concatenate([[0.0], np.cumsum(b[tl])])
            lo = np.searchsorted(st, st - JAHR_H, "left")
            hi = np.searchsorted(st, st, "left") if vorgriff else np.searchsorted(st, st - W, "right")
            k = hi - lo
            gut = (st - st[0] >= JAHR_H) & (k > 1000)
            na[tl] = np.where(gut, (ca[hi] - ca[lo]) / np.maximum(k, 1), np.nan)
            nb[tl] = np.where(gut, (cb[hi] - cb[lo]) / np.maximum(k, 1), np.nan)
        return na, nb

    NA, NB = normal(A, B, 24)
    gitter = np.isin(STD % 24, GITTER) & np.isfinite(NA)
    such = gitter & (STD >= SUCHE[0]) & (STD < SUCHE[1])
    pruef = gitter & (STD >= PRUEF[0]) & (STD < PRUEF[1])
    # Moment- und Tages-Bezug
    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    _u, smi = np.unique(SM, return_inverse=True)
    smn = np.maximum(np.bincount(smi), 1)
    MA = (np.bincount(smi, weights=A) / smn)[smi]; MB = (np.bincount(smi, weights=B) / smn)[smi]
    TAG = STD // 24
    _u, ti = np.unique(TAG, return_inverse=True)
    tn = np.maximum(np.bincount(ti), 1)
    TA = (np.bincount(ti, weights=A) / tn)[ti]; TB = (np.bincount(ti, weights=B) / tn)[ti]
    print("  Tagesanker mit Phase: Suche %d · Pruefung %d · Symbole %d · Kurven %d"
          % (such.sum(), pruef.sum(), len(np.unique(SYM[such | pruef])), len(namen)))

    GRENZEN = {k: np.nanpercentile(KURVEN[k][such & np.isfinite(KURVEN[k])], PERZ) for k in namen}

    def stufen(v, g):
        st = np.full(n, -1, np.int8)
        ok = np.isfinite(v)
        st[ok] = np.searchsorted(g, v[ok])
        return st

    def profil(st, sel, a=A, b=B, na=NA, nb=NB, minn=30):
        idx = np.flatnonzero(sel & (st >= 0))
        k = st[idx]
        sa = np.bincount(k, weights=a[idx], minlength=12); sb = np.bincount(k, weights=b[idx], minlength=12)
        sna = np.bincount(k, weights=na[idx], minlength=12); snb = np.bincount(k, weights=nb[idx], minlength=12)
        cnt = np.bincount(k, minlength=12)
        d = sa / np.maximum(sa + sb, 1e-12) - sna / np.maximum(sna + snb, 1e-12)
        return np.where(cnt >= minn, d, np.nan), cnt

    def S(d, cnt):
        return float(np.nansum(cnt * d ** 2))

    ST = {k: stufen(KURVEN[k], GRENZEN[k]) for k in namen}
    wert = {k: profil(ST[k], such) for k in namen}
    s_wert = {k: S(*wert[k]) for k in namen}

    # Nullwelt: Zeitverschiebung je Asset - oder, mit --gemeinsam, fuer ALLE
    # Assets um DENSELBEN Versatz (K3-Methode). ⚠️ Fuer Marktmerkmale (_markt,
    # zur selben Stunde fuer alle gleich) ist nur die gemeinsame Verschiebung
    # richtig: die Verschiebung je Asset zerstoert die Gleichzeitigkeit und
    # macht z zu gross (W11-Lauf 28.09.: z bis 118 bei Tag/Phase 0,03)
    GEMEINSAM = "--gemeinsam" in sys.argv
    H0 = STD - STD.min()
    LH = int(H0.max()) + 1

    def verschiebe(v):
        if GEMEINSAM:
            # Wert je Stunde (Median ueber die Assets - bei _markt identisch)
            # und fuer alle um denselben Versatz verschoben
            je_h = np.full(LH, np.nan)
            ok = np.isfinite(v)
            je_h[H0[ok]] = v[ok]
            r = int(rng.integers(60 * 24, LH - 60 * 24))
            return np.roll(je_h, r)[H0].astype(np.float32)
        aus = np.empty_like(v)
        for tl in teile:
            L = len(tl)
            r = int(rng.integers(MIN_VERSATZ, max(MIN_VERSATZ + 1, L - MIN_VERSATZ))) if L > 2 * MIN_VERSATZ else 0
            aus[tl] = np.roll(v[tl], r)
        return aus
    s_null = {k: np.zeros(ZIEHUNGEN) for k in namen}
    for zi in range(ZIEHUNGEN):
        for k in namen:
            st = stufen(verschiebe(KURVEN[k]), GRENZEN[k])
            s_null[k][zi] = S(*profil(st, such))
    mu = {k: s_null[k].mean() for k in namen}
    sd = {k: max(s_null[k].std(ddof=1), 1e-12) for k in namen}
    maxz = np.max(np.stack([(s_null[k] - mu[k]) / sd[k] for k in namen], axis=1), axis=1)
    grenze = float(np.percentile(maxz, 90))
    print("  Grenze Bestes-von-%d (Zeitverschiebung %s, %d Ziehungen): z %.2f" % (
        len(namen), "GEMEINSAM fuer alle Assets" if GEMEINSAM else "je Asset", ZIEHUNGEN, grenze))
    print()
    print("  %-22s %6s %6s | %5s %5s | %5s %6s | %6s %6s | %s | %s" % (
        "Kurve", "S", "z", "Form", "Rand", "Jahre", "Asset", "Tag/Ph", "Mo/Ph", "Dq je Stufe (Suche, <P1 ... >P99)", "Urteil"))
    traeger = []
    for k in namen:
        d, cnt = wert[k]
        z = (s_wert[k] - mu[k]) / sd[k]
        dp, _c = profil(ST[k], pruef)
        form = spearman(d, dp)
        rand = (np.sign(d[0]) == np.sign(dp[0])) and (np.sign(d[11]) == np.sign(dp[11]))
        jahre = []
        for y in (2023, 2024, 2025, 2026):
            dy, _c = profil(ST[k], gitter & (JAHR == y), minn=20)
            jahre.append(spearman(d, dy))
        j_ok = sum(1 for x in jahre if np.isfinite(x) and x > 0)
        # je Asset: Profil je (Asset, Stufe) ueber gruppierte Summen
        ix = np.flatnonzero((such | pruef) & (ST[k] >= 0))
        key = SYM[ix].astype(np.int64) * 12 + ST[k][ix]
        nsy = int(SYM.max()) + 1
        ga = np.bincount(key, weights=A[ix], minlength=nsy * 12).reshape(nsy, 12)
        gb = np.bincount(key, weights=B[ix], minlength=nsy * 12).reshape(nsy, 12)
        gna = np.bincount(key, weights=NA[ix], minlength=nsy * 12).reshape(nsy, 12)
        gnb = np.bincount(key, weights=NB[ix], minlength=nsy * 12).reshape(nsy, 12)
        gc = np.bincount(key, minlength=nsy * 12).reshape(nsy, 12)
        with np.errstate(divide="ignore", invalid="ignore"):
            gd = ga / (ga + gb) - gna / (gna + gnb)
        gd = np.where(gc >= 20, gd, np.nan)
        je = [spearman(d, gd[i]) for i in range(nsy) if np.isfinite(gd[i]).sum() >= 6]
        asset = float(np.mean([x > 0 for x in je if np.isfinite(x)])) if je else np.nan
        st_tag = S(*profil(ST[k], such, na=TA, nb=TB))
        st_mo = S(*profil(ST[k], such, na=MA, nb=MB))
        traegt = (z > grenze and np.isfinite(form) and form >= 0.5 and rand and j_ok >= 3
                  and np.isfinite(asset) and asset >= 0.6)
        if traegt:
            traeger.append(k)
        print("  %-22s %6.2f %+6.2f | %+5.2f %5s | %d/4 %5.0f%% | %6.2f %6.2f | %s | %s" % (
            k, s_wert[k], z, form, "ja" if rand else "nein", j_ok, 100 * asset if np.isfinite(asset) else float("nan"),
            st_tag / max(s_wert[k], 1e-12), st_mo / max(s_wert[k], 1e-12),
            " ".join("%+.3f" % x if np.isfinite(x) else "  -  " for x in d),
            ("✔ TRAEGT" + (" · TEILEN (Tag < 1/2)" if st_tag < 0.5 * s_wert[k] else "")) if traegt else "· nein"))
    print()
    print("  Tag/Ph, Mo/Ph = S gegen Tages- bzw. Monatsbezug geteilt durch S gegen die Phase (W11: < 0,5 -> teilen)")

    # A4 / W12: Randstufen je bisherigem Anstieg in ATR, fuer die tragenden Kurven
    print()
    print("=" * 120)
    print("A4 - BESTAETIGT ODER GELAUFEN: Dq der Randstufen (hoch = P90-P99 und > P99, tief = < P1 und P1-P10) "
          "je Anstieg der letzten 24 h in eigener ATR, Suche+Pruefung")
    with np.errstate(divide="ignore", invalid="ignore"):
        anst = VOR24 / np.maximum(ATR, 1e-12)
    ab_ = np.searchsorted(np.array(ANSTIEG[1:-1]), anst)
    ab_[~np.isfinite(anst)] = -1
    namen_a = ("< 0", "0-0,5", "0,5-1", "1-2", "2-3", "> 3")
    for k in (traeger or namen[:0]):
        zeile_h, zeile_t = [], []
        for j in range(6):
            sel = (such | pruef) & (ab_ == j)
            d, cnt = profil(ST[k], sel, minn=30)
            def rand(sl):
                ok = np.isfinite(d[sl]) & (cnt[sl] > 0)
                return (float(np.sum(d[sl][ok] * cnt[sl][ok]) / cnt[sl][ok].sum()), int(cnt[sl][ok].sum())) if ok.any() else (np.nan, 0)
            hoch, nh = rand(slice(10, 12)); tief, nt = rand(slice(0, 2))
            # ⚠️ ein leerer Bereich ist KEIN Wert (1. Lauf zeigte ihn als +0,000)
            zeile_h.append("%s %s" % (namen_a[j], ("%+.3f (%d)" % (hoch, nh)) if nh else "  -  "))
            zeile_t.append("%s %s" % (namen_a[j], ("%+.3f (%d)" % (tief, nt)) if nt else "  -  "))
        print("  %-22s hoch: %s" % (k, " · ".join(zeile_h)))
        print("  %-22s tief: %s" % ("", " · ".join(zeile_t)))
    if not traeger:
        print("  (keine tragende Kurve)")

    # Altersachse fuer die tragenden
    print()
    print("ALTERSACHSE (Merkmal L Stunden alt): S und Randstufen, Suche")
    for k in traeger:
        teile_s = []
        for L in (6, 12, 24):
            v = np.full(n, np.nan, np.float32)
            for tl in teile:
                vv = KURVEN[k][tl]
                ss = STD[tl]
                vorher = np.searchsorted(ss, ss - L)
                gut = (vorher < len(ss)) & (ss[np.minimum(vorher, len(ss) - 1)] == ss - L)
                w = np.full(len(tl), np.nan, np.float32); w[gut] = vv[vorher[gut]]
                v[tl] = w
            d, cnt = profil(stufen(v, GRENZEN[k]), such)
            teile_s.append("%dh: S %.2f (%.0f%%) Rand %+.3f/%+.3f" % (L, S(d, cnt), 100 * S(d, cnt) / max(s_wert[k], 1e-12), d[0], d[11]))
        print("  %-22s %s" % (k, " · ".join(teile_s)))

    # Pflichtproben
    print()
    print("=" * 120)
    print("PFLICHTPROBEN")
    VNA, VNB = normal(A, B, 24, vorgriff=True)
    diff = [abs(S(*profil(ST[k], such, na=VNA, nb=VNB)) - s_wert[k]) / max(s_wert[k], 1e-12) for k in namen]
    print("  G1 Vorgriff im Normal: groesste relative Aenderung von S %.3f" % max(diff))
    # ⚠️ In eine WIRKUNGSLOSE Reihe pflanzen - eine zeitverschobene Kopie des
    # Merkmals. Der 1. Lauf pflanzte in funding_vortag roh (z 27,9 schon ohne
    # Pflanzung) und meldete deshalb *gefunden* bei jeder Staerke - wertlos.
    k0 = "ema_abstand_atr selbst" if "ema_abstand_atr selbst" in namen else namen[0]
    v0 = verschiebe(KURVEN[k0])
    st0 = stufen(v0, GRENZEN[k0])
    s0 = np.array([S(*profil(stufen(verschiebe(KURVEN[k0]), GRENZEN[k0]), such)) for _ in range(ZIEHUNGEN)])
    mu0, sd0 = s0.mean(), max(s0.std(ddof=1), 1e-12)
    print("  G4 Positivkontrolle: lineare Kurve von -d bis +d ueber die 12 Stufen einer ZEITVERSCHOBENEN "
          "(wirkungslosen) Kopie von %s gepflanzt, gegen deren eigene Nullwelt und die Grenze %.2f:" % (k0, grenze))
    print("     ohne Pflanzung: z %+.2f" % ((S(*profil(st0, such)) - mu0) / sd0))
    for dd in (0.005, 0.01, 0.02, 0.04):
        gef = 0
        for _ in range(5):
            a = A.copy(); b = B.copy()
            for j in range(12):
                ziel = -dd + 2 * dd * j / 11
                sel = such & (st0 == j)
                treffer = np.flatnonzero(sel & ((a + b) > 0))
                m = int(round(abs(ziel) * len(treffer)))
                if ziel > 0:
                    pool = treffer[b[treffer] == 1]
                    w = rng.choice(pool, size=min(m, len(pool)), replace=False); a[w], b[w] = 1, 0
                elif ziel < 0:
                    pool = treffer[a[treffer] == 1]
                    w = rng.choice(pool, size=min(m, len(pool)), replace=False); a[w], b[w] = 0, 1
            s_pf = S(*profil(st0, such, a=a, b=b))
            gef += int((s_pf - mu0) / sd0 > grenze)
        print("     d = %.3f: gefunden %d von 5" % (dd, gef))
    print("  G7 Korrelationsmatrix (Rang, Suche, Tagesanker) - |rho| >= 0,5:")
    idx = np.flatnonzero(such)[::7]
    rk = {k: pd.Series(KURVEN[k][idx]).rank().to_numpy() for k in namen}
    for i, k1 in enumerate(namen):
        for k2 in namen[i + 1:]:
            ok = np.isfinite(rk[k1]) & np.isfinite(rk[k2])
            if ok.sum() > 1000:
                r = np.corrcoef(rk[k1][ok], rk[k2][ok])[0, 1]
                if abs(r) >= 0.5:
                    print("     %-22s ~ %-22s %+.2f" % (k1, k2, r))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
