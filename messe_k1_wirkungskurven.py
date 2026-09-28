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

    RANDKRITERIUM - VORAB FESTGELEGT 28.09.2026, VOR jeder Randrechnung
    (Nutzer: *"Randkriterium fuer naechste Messungen ja ... so festlegen und
    neu rechnen"*):
        Rand      oben = Stufen P90-P99 und > P99, unten = < P1 und P1-P10
        Kennzahl  Dq des Rands gegen die Phase (Anker-gewichtet)
        Nullwelt  dieselbe wie fuer die Kurve (je Asset, bzw. --gemeinsam);
                  Grenze Bestes-von-(2 x Kurven), zweiseitig, 90. Perzentil
        TRAEGT    jenseits der Grenze (Suche) UND gleiches Vorzeichen in der
                  Pruefung UND >= 3 von 4 Jahren UND >= 60 % der Assets
                  gleiches Vorzeichen UND gleiches Vorzeichen 2022 (Moment-
                  Bezug, von der Kurvenmessung unberuehrt)
        Rolle     positiv -> Einstieg (nur mit Altersachse und A4
                  *bestaetigt*), negativ -> Sperre
    --nur-eigen: bei den Teilungsgruppen nur die _eigen-Kurven (die _markt-
    Kurven werden nur mit --nur-markt --gemeinsam beurteilt)

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
           "teilung": ("funding_vortag", "premium_jetzt", "premium_24h"),
           # W11 fuer den Terminmarkt (28.09.): konten_verh und top_konten_verh
           # behielten gegen die Tages-Kontrolle nur 5 bis 20 Prozent
           "termin_teilung": ("konten_verh", "top_konten_verh"),
           # REGELTEST (Nutzer 28.09.: *die Regel muss auch in unseren Tests
           # funktionieren*): Zufallsmerkmale - das Randkriterium darf fast
           # nie *traegt* melden; dazu gepflanzte Raender (--gruppe regeltest)
           "regeltest": ("ema_abstand_atr",),
           # ALTERSACHSE fein (Voranalyse K1 Abschnitt 10, B1-B4 abgestimmt
           # 28.09.): die Familie *oben gestreckt*, dazu zwei Zufallsmerkmale
           "altersachse": ("rsi", "momentum_kurz", "ema_abstand_atr")}
# B2: die Alter der feinen Altersachse, in Stunden
ALTER_FEIN = (0, 1, 2, 3, 6, 9, 12, 18, 24, 36, 48)
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


def altersachse_fein(namen, KURVEN, GRENZEN, teile, STD, JAHR, A, B, NA, NB, MA, MB,
                     such, pruef, gitter22, verschiebe) -> None:
    """ALTERSACHSE FEIN - vorab festgelegt 28.09.2026 (Voranalyse K1 Abschnitt 10).

    B1 Rand     derselbe wie im Randkriterium: oben Stufen 10+11, unten 0+1,
                Anker-gewichtet; die Stufen 10 und 11 einzeln als Auskunft.
                ⛔ Anlass: die alte Altersachse druckte nur d[0]/d[11] und wurde
                gegen den Zweistufen-Rand gelesen - Einzelstufe gegen Rand.
    B2 Alter    ALTER_FEIN, 0 bis 48 h. Der L Stunden alte Wert desselben Assets
                (exakt STD - L), die Stufengrenzen des AKTUELLEN Merkmals.
    B3 Kurven   rsi, momentum_kurz, ema_abstand_atr je roh/selbst + 2 Zufall.
    B4 Pruefung je Alter Suche und Pruefzeit getrennt; Nullwelt Zeitverschiebung
                (je Ziehung EINE Verschiebung je Kurve, fuer alle Alter dieselbe),
                40 Ziehungen; Grenze Bestes-von-(Alter x echte Kurven x 2 Raender);
                Pruefzeit gegen den Versatz der Zufallsraender (E-11); 2022 mit
                Moment-Bezug als Auskunft.
    Gueltigkeit (10c): eine UMKEHR ist ein Alter, in dem der Rand jenseits der
    Grenze das Gegenzeichen des Alters 0 hat UND die Pruefzeit (minus Versatz)
    ebenfalls. ⭐ Kein Blocker: das Ergebnis ist ein VERLAUF, der in K1 Schritt 2
    als Gewicht eingeht - keine Schwelle *erst ab X Stunden*.
    """
    anker = such | pruef | gitter22
    idx_l, src = [], {L: [] for L in ALTER_FEIN}
    for tl in teile:
        ss = STD[tl]
        ai = np.flatnonzero(anker[tl])
        if not len(ai):
            continue
        idx_l.append(tl[ai])
        for L in ALTER_FEIN:
            j = np.searchsorted(ss, ss[ai] - L)
            jj = np.minimum(j, len(ss) - 1)
            ok = (j < len(ss)) & (ss[jj] == ss[ai] - L)
            src[L].append(np.where(ok, tl[jj], -1))
    IDX = np.concatenate(idx_l)
    SRC = {L: np.concatenate(src[L]) for L in ALTER_FEIN}
    sA, sB = A[IDX], B[IDX]
    sNA, sNB, sMA, sMB = NA[IDX], NB[IDX], MA[IDX], MB[IDX]
    m_such, m_pruef, m_22 = such[IDX], pruef[IDX], gitter22[IDX]

    def gealtert(v, L):
        s_ = SRC[L]
        out = np.full(len(s_), np.nan, np.float32)
        ok = s_ >= 0
        out[ok] = v[s_[ok]]
        return out

    def stufe(w, g):
        st = np.full(len(w), -1, np.int64)
        ok = np.isfinite(w)
        st[ok] = np.searchsorted(g, w[ok])
        return st

    def rand_dq(st, sel, na, nb, minn=30):
        """-> (unten, oben, Dq Stufe 10, Dq Stufe 11, Anker oben) - wie raender()"""
        ix = np.flatnonzero(sel & (st >= 0))
        k_ = st[ix]
        sa = np.bincount(k_, weights=sA[ix], minlength=12)
        sb = np.bincount(k_, weights=sB[ix], minlength=12)
        sna = np.bincount(k_, weights=na[ix], minlength=12)
        snb = np.bincount(k_, weights=nb[ix], minlength=12)
        cnt = np.bincount(k_, minlength=12)
        d = sa / np.maximum(sa + sb, 1e-12) - sna / np.maximum(sna + snb, 1e-12)
        d = np.where(cnt >= minn, d, np.nan)
        aus = []
        for sl in (slice(0, 2), slice(10, 12)):
            ok = np.isfinite(d[sl]) & (cnt[sl] > 0)
            aus.append(float(np.sum(d[sl][ok] * cnt[sl][ok]) / cnt[sl][ok].sum()) if ok.any() else np.nan)
        return aus[0], aus[1], float(d[10]), float(d[11]), int(cnt[10:12].sum())

    echt = [k for k in namen if not k.startswith("zufall")]
    zuf = [k for k in namen if k.startswith("zufall")]
    nL = len(ALTER_FEIN)
    rn = {k: np.full((ZIEHUNGEN, nL, 2), np.nan) for k in namen}
    for zi in range(ZIEHUNGEN):
        for k in namen:
            v_sh = verschiebe(KURVEN[k])
            for li, L in enumerate(ALTER_FEIN):
                u, o, _a, _b, _n = rand_dq(stufe(gealtert(v_sh, L), GRENZEN[k]), m_such, sNA, sNB)
                rn[k][zi, li] = (u, o)
    mu = {k: np.nanmean(rn[k], axis=0) for k in namen}
    sd = {k: np.maximum(np.nanstd(rn[k], axis=0, ddof=1), 1e-9) for k in namen}
    zmax = np.nanmax(np.concatenate([np.abs((rn[k] - mu[k]) / sd[k]).reshape(ZIEHUNGEN, -1)
                                     for k in echt], axis=1), axis=1)
    grenze = float(np.nanpercentile(zmax, 90))

    werte = {}
    for k in namen:
        zeilen = []
        for L in ALTER_FEIN:
            st = stufe(gealtert(KURVEN[k], L), GRENZEN[k])
            zeilen.append((rand_dq(st, m_such, sNA, sNB), rand_dq(st, m_pruef, sNA, sNB),
                           rand_dq(st, m_22, sMA, sMB, minn=20)))
        werte[k] = zeilen
    vz = np.array([werte[k][li][1][ri] for k in zuf for li in range(nL) for ri in (0, 1)], float)
    vers, vers_sd = float(np.nanmean(vz)), float(np.nanstd(vz, ddof=1))

    print()
    print("=" * 120)
    print("ALTERSACHSE FEIN (vorab 28.09., Voranalyse K1 Abschnitt 10, B1-B4) - Rand wie im Randkriterium, "
          "Stufengrenzen des aktuellen Merkmals")
    print("  Grenze Bestes-von-%d (%d Alter x %d Kurven x 2 Raender): |z| %.2f · Pruefzeit-Versatz der "
          "Zufallsraender %+.4f (sd %.4f, %d Werte)" % (nL * len(echt) * 2, nL, len(echt), grenze, vers, vers_sd,
                                                         np.isfinite(vz).sum()))
    for k in namen:
        for ri, rname in ((1, "oben"), (0, "unten")):
            print("  %-24s %-5s  %s" % (k, rname, "  ".join("%3dh" % L for L in ALTER_FEIN)))
            zs = [(werte[k][li][0][ri] - mu[k][li, ri]) / sd[k][li, ri] for li in range(nL)]
            reihen = (("Dq Suche", [werte[k][li][0][ri] for li in range(nL)], "%+.3f"),
                      ("z Suche", zs, "%+5.1f "),
                      ("Pruef-Vers", [werte[k][li][1][ri] - vers for li in range(nL)], "%+.3f"),
                      ("2022", [werte[k][li][2][ri] for li in range(nL)], "%+.3f"))
            if ri == 1:
                reihen += (("P90-99", [werte[k][li][0][2] for li in range(nL)], "%+.3f"),
                           (">P99", [werte[k][li][0][3] for li in range(nL)], "%+.3f"))
            for nm, xs, f in reihen:
                print("    %-12s %s" % (nm, " ".join((f % x) if np.isfinite(x) else "  -   " for x in xs)))
            v0 = np.sign(werte[k][0][0][ri])
            umkehr = [L for li, L in enumerate(ALTER_FEIN)
                      if np.isfinite(zs[li]) and abs(zs[li]) > grenze and np.sign(werte[k][li][0][ri]) == -v0
                      and np.sign(werte[k][li][1][ri] - vers) == -v0]
            jenseits = [L for li, L in enumerate(ALTER_FEIN) if np.isfinite(zs[li]) and abs(zs[li]) > grenze]
            print("    %s" % (("⛔ UMKEHR bei %s h" % umkehr) if umkehr else
                              "✔ keine Umkehr (jenseits der Grenze bei %s h)" % (jenseits or "keinem Alter")))
    fa = sum(1 for k in zuf for li in range(nL) for ri in (0, 1)
             if abs((werte[k][li][0][ri] - mu[k][li, ri]) / sd[k][li, ri]) > grenze)
    print("  REGELTEST: Zufallsraender jenseits der Grenze: %d von %d (Soll: fast keiner)" % (fa, len(zuf) * nL * 2))
    print("  Pruef-Vers = Dq der Pruefzeit minus Versatz (E-11) · 2022 mit Moment-Bezug · Umkehr = jenseits der "
          "Grenze mit Gegenzeichen zu 0 h UND Pruefzeit ebenso (Abschnitt 10c)")

    # ══ GEGENPRUEFUNG TAGESZEIT (nachtraeglich 28.09., aendert kein Urteil) ══
    stunde = (STD[IDX] % 24).astype(np.int64)

    def dq(ix, na=sNA, nb=sNB):
        return (sA[ix].sum() / max(sA[ix].sum() + sB[ix].sum(), 1e-12)
                - na[ix].sum() / max(na[ix].sum() + nb[ix].sum(), 1e-12))

    print()
    print("=" * 120)
    print("GEGENPRUEFUNG TAGESZEIT (nachtraeglich 28.09., aendert kein vorab festgelegtes Urteil): misst der Rand "
          "die UHRZEIT der festen Anker?")
    for nm, sel in (("Suche", m_such), ("Pruef", m_pruef)):
        print("  T1 Dq aller Anker je Ankerstunde, %s: %s" % (nm, " · ".join(
            "%02d h %+.4f (%d)" % (h, dq(np.flatnonzero(sel & (stunde == h))), int((sel & (stunde == h)).sum()))
            for h in GITTER)))

    def rand_tb(st, sel, sl):
        tot, nn = 0.0, 0
        for h in GITTER:
            ia = np.flatnonzero(sel & (stunde == h) & (st >= 0))
            ie = ia[np.isin(st[ia], sl)]
            if len(ie) < 30:
                continue
            tot += len(ie) * (dq(ie) - dq(ia))
            nn += len(ie)
        return tot / nn if nn else np.nan

    rng_t = np.random.default_rng(SAAT + 24)

    def verschiebe_tage(v):
        aus = np.empty_like(v)
        for tl in teile:
            Lt = len(tl)
            if Lt > 2 * MIN_VERSATZ:
                r = 24 * int(rng_t.integers(MIN_VERSATZ // 24, (Lt - MIN_VERSATZ) // 24))
            else:
                r = 0
            aus[tl] = np.roll(v[tl], r)
        return aus

    print("  T2 Anteil der Randanker (oben, 0 h, Suche) je Ankerstunde 00/06/12/18 - gleichverteilt waeren je 25 %")
    for k in namen:
        st0 = stufe(gealtert(KURVEN[k], 0), GRENZEN[k])
        ie = np.flatnonzero(m_such & np.isin(st0, (10, 11)))
        anteil = [100.0 * np.mean(stunde[ie] == h) for h in GITTER]
        print("     %-24s %s" % (k, "  ".join("%02d h %4.1f %%" % (h, a) for h, a in zip(GITTER, anteil))))
    tn = {k: np.full((ZIEHUNGEN, nL), np.nan) for k in namen}
    for zi in range(ZIEHUNGEN):
        for k in namen:
            v_sh = verschiebe_tage(KURVEN[k])
            for li, L in enumerate(ALTER_FEIN):
                tn[k][zi, li] = rand_dq(stufe(gealtert(v_sh, L), GRENZEN[k]), m_such, sNA, sNB)[1]
    print("  T3/T4 oberer Rand: tagesbereinigt (Suche, Pruefzeit) und z gegen die TAGESGLEICHE Nullwelt")
    print("  %-24s %-9s %s" % ("", "", "  ".join("%3dh" % L for L in ALTER_FEIN)))
    for k in namen:
        tb_s, tb_p, zt = [], [], []
        for li, L in enumerate(ALTER_FEIN):
            st = stufe(gealtert(KURVEN[k], L), GRENZEN[k])
            tb_s.append(rand_tb(st, m_such, (10, 11)))
            tb_p.append(rand_tb(st, m_pruef, (10, 11)))
            m_, s_ = np.nanmean(tn[k][:, li]), max(np.nanstd(tn[k][:, li], ddof=1), 1e-9)
            zt.append((werte[k][li][0][1] - m_) / s_)
        print("  %-24s %-9s %s" % (k, "roh", " ".join("%+.3f" % werte[k][li][0][1] for li in range(nL))))
        print("  %-24s %-9s %s" % ("", "tb Such", " ".join("%+.3f" % x if np.isfinite(x) else "  -   " for x in tb_s)))
        print("  %-24s %-9s %s" % ("", "tb Pruef", " ".join("%+.3f" % x if np.isfinite(x) else "  -   " for x in tb_p)))
        print("  %-24s %-9s %s" % ("", "z Tag", " ".join("%+5.1f " % x if np.isfinite(x) else "  -   " for x in zt)))
    print("  tb = je Ankerstunde Dq(Rand) minus Dq(alle Anker dieser Stunde), mit den Randankern gewichtet; "
          "z Tag = gegen Verschiebungen um ganze Tage (Uhrzeit bleibt erhalten)")


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

    if gruppe in ("teilung", "termin_teilung"):
        # Markt = Median aller Assets zur selben Stunde (Bestand + Eingestellte der
        # Menge); eigen = Asset minus Markt. Beide werden als eigene Merkmale
        # gefuehrt (roh und selbstbezogen wie alle anderen)
        for m in list(MERK):
            v = pd.Series(FV[m].astype(float))
            mk = v.groupby(STD).transform("median").to_numpy()
            FV[m + "_markt"] = mk.astype(np.float32)
            FV[m + "_eigen"] = (FV[m] - mk).astype(np.float32)
            del FV[m]
        teil_t = (("_markt",) if "--nur-markt" in sys.argv else
                  ("_eigen",) if "--nur-eigen" in sys.argv else ("_markt", "_eigen"))
        MERK = tuple(m + t for m in MERK for t in teil_t)
        for m in list(FV):
            if m not in MERK:
                del FV[m]
    if gruppe == "regeltest":
        o_ = np.lexsort((STD, SYM))
        gr_ = np.flatnonzero(np.diff(SYM[o_])) + 1
        for glatt in (1, 6, 24, 72, 168):
            for saat in (1, 2):
                r_ = np.random.default_rng(3000 * glatt + saat)
                if "--nur-markt" in sys.argv:
                    # Zufalls-MARKTreihe: ein Wert je Stunde, fuer alle Assets
                    # gleich - prueft die Regel dort, wo _markt-Urteile stehen
                    # (mit --gemeinsam: gemeinsame Zeitverschiebung)
                    h_ = (STD - STD.min()).astype(np.int64)
                    x_ = r_.standard_normal(int(h_.max()) + 1)
                    c_ = np.concatenate([[0.0], np.cumsum(x_)])
                    kk = np.arange(1, len(x_) + 1)
                    lo_ = np.maximum(0, kk - glatt)
                    FV["zufall_markt_g%d_s%d" % (glatt, saat)] = ((c_[kk] - c_[lo_]) / (kk - lo_))[h_].astype(np.float32)
                    continue
                x_ = r_.standard_normal(n)
                v_ = np.empty(n, np.float32)
                for tl_ in np.split(o_, gr_):
                    c_ = np.concatenate([[0.0], np.cumsum(x_[tl_])])
                    kk = np.arange(1, len(tl_) + 1)
                    lo_ = np.maximum(0, kk - glatt)
                    v_[tl_] = (c_[kk] - c_[lo_]) / (kk - lo_)
                FV["zufall_g%d_s%d" % (glatt, saat)] = v_
        MERK = tuple(m for m in FV if m.startswith("zufall"))
        del FV["ema_abstand_atr"]
    if gruppe == "altersachse":
        # B3: zwei Zufallsmerkmale durch dieselbe Rechnung - zeigen sie ueber
        # das Alter ein Muster, ist es die Rechnung, nicht der Markt
        o_ = np.lexsort((STD, SYM))
        gr_ = np.flatnonzero(np.diff(SYM[o_])) + 1
        for glatt, saat in ((6, 1), (24, 1)):
            r_ = np.random.default_rng(3000 * glatt + saat)
            x_ = r_.standard_normal(n)
            v_ = np.empty(n, np.float32)
            for tl_ in np.split(o_, gr_):
                c_ = np.concatenate([[0.0], np.cumsum(x_[tl_])])
                kk = np.arange(1, len(tl_) + 1)
                lo_ = np.maximum(0, kk - glatt)
                v_[tl_] = (c_[kk] - c_[lo_]) / (kk - lo_)
            FV["zufall_g%d_s%d" % (glatt, saat)] = v_
        MERK = tuple(MERK) + ("zufall_g6_s1", "zufall_g24_s1")
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
    def raender(d, cnt):
        """-> (unten, oben): Anker-gewichtetes Dq der Randstufen (0,1 bzw. 10,11)."""
        aus = []
        for sl in (slice(0, 2), slice(10, 12)):
            ok = np.isfinite(d[sl]) & (cnt[sl] > 0)
            aus.append(float(np.sum(d[sl][ok] * cnt[sl][ok]) / cnt[sl][ok].sum()) if ok.any() else np.nan)
        return aus

    s_null = {k: np.zeros(ZIEHUNGEN) for k in namen}
    r_null = {k: np.zeros((ZIEHUNGEN, 2)) for k in namen}
    for zi in range(ZIEHUNGEN):
        for k in namen:
            st = stufen(verschiebe(KURVEN[k]), GRENZEN[k])
            dn, cn = profil(st, such)
            s_null[k][zi] = S(dn, cn)
            r_null[k][zi] = raender(dn, cn)
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

    # ══ RANDKRITERIUM (vorab 28.09.) ══════════════════════════════════
    rmu = {k: np.nanmean(r_null[k], axis=0) for k in namen}
    rsd = {k: np.maximum(np.nanstd(r_null[k], axis=0, ddof=1), 1e-9) for k in namen}
    rz = np.stack([np.abs((r_null[k] - rmu[k]) / rsd[k]) for k in namen], axis=1).reshape(ZIEHUNGEN, -1)
    rgrenze = float(np.nanpercentile(np.nanmax(rz, axis=1), 90))
    gitter22 = np.isin(STD % 24, GITTER) & (JAHR == 2022)
    print()
    print("=" * 120)
    print("RANDKRITERIUM (vorab 28.09.) - Grenze Bestes-von-%d Raendern: |z| %.2f" % (2 * len(namen), rgrenze))
    print("  %-26s %-5s %8s %6s | %8s | %5s | %6s | %8s %6s | %s" % (
        "Kurve", "Rand", "Dq Such", "z", "Dq Pruef", "Jahre", "Asset", "Dq 2022", "Anker", "Urteil"))
    rand_traeger = []
    nsy = int(SYM.max()) + 1
    for k in namen:
        d, cnt = wert[k]
        ru = raender(d, cnt)
        dp, cp = profil(ST[k], pruef)
        rp = raender(dp, cp)
        d22, c22 = profil(ST[k], gitter22, na=MA, nb=MB, minn=20)
        r22 = raender(d22, c22)
        jahre = []
        for y in (2023, 2024, 2025, 2026):
            dy, cy = profil(ST[k], gitter & (JAHR == y), minn=20)
            jahre.append(raender(dy, cy))
        ix = np.flatnonzero((such | pruef) & (ST[k] >= 0))
        for ri, (sl, name) in enumerate(((slice(0, 2), "unten"), (slice(10, 12), "oben"))):
            w = ru[ri]
            z = (w - rmu[k][ri]) / rsd[k][ri] if np.isfinite(w) else np.nan
            vz = np.sign(w)
            j_ok = sum(1 for y in jahre if np.isfinite(y[ri]) and np.sign(y[ri]) == vz)
            # je Asset: Rand-Dq je Asset (mind. 20 Anker im Rand)
            im = ix[np.isin(ST[k][ix], (0, 1) if ri == 0 else (10, 11))]
            sa = np.bincount(SYM[im], weights=A[im], minlength=nsy); sb = np.bincount(SYM[im], weights=B[im], minlength=nsy)
            sna = np.bincount(SYM[im], weights=NA[im], minlength=nsy); snb = np.bincount(SYM[im], weights=NB[im], minlength=nsy)
            sc = np.bincount(SYM[im], minlength=nsy)
            with np.errstate(divide="ignore", invalid="ignore"):
                da = sa / (sa + sb) - sna / (sna + snb)
            ok = (sc >= 20) & np.isfinite(da)
            asset = float(np.mean(np.sign(da[ok]) == vz)) if ok.any() else np.nan
            n22 = int(c22[sl].sum())
            traegt = (np.isfinite(z) and abs(z) > rgrenze and np.sign(rp[ri]) == vz and j_ok >= 3
                      and np.isfinite(asset) and asset >= 0.6 and np.isfinite(r22[ri]) and np.sign(r22[ri]) == vz)
            rolle = ("✔ EINSTIEG (Alter/A4 pruefen)" if vz > 0 else "⛔ SPERRE") if traegt else "· nein"
            if traegt:
                rand_traeger.append((k, name, vz))
            print("  %-26s %-5s %+8.4f %+6.2f | %+8.4f | %d/4   | %5.0f%% | %+8.4f %6d | %s" % (
                k, name, w, z, rp[ri], j_ok, 100 * asset if np.isfinite(asset) else float("nan"),
                r22[ri], n22, rolle))
    print("  Dq 2022: Moment-Bezug (Asset im selben Monat) - 2022 hat noch kein 12-Monats-Normal; unberuehrt von der Kurvenmessung")
    traeger = sorted(set(traeger) | {k for k, _n, v in rand_traeger if v > 0})
    if gruppe == "regeltest":
        print()
        print("  REGELTEST ZUFALL: %d von %d Raendern *tragen* (Soll: fast keiner)" % (
            len(rand_traeger), 2 * len(namen)))
        print("  REGELTEST PFLANZUNG: oberer Rand um +d gehoben (Suche, Pruefung UND 2022), in einer "
              "zeitverschobenen Kopie der ersten Zufallskurve - gefunden, wenn alle Randbedingungen gelten:")
        k0 = namen[0]
        for dd in (0.01, 0.02, 0.04, 0.08):
            gef = 0
            for _ in range(5):
                st0 = stufen(verschiebe(KURVEN[k0]), GRENZEN[k0])
                a = A.copy(); b = B.copy()
                oben = np.isin(st0, (10, 11)) & np.isin(STD % 24, GITTER)
                tr = np.flatnonzero(oben & ((a + b) > 0) & (b == 1))
                m_ = int(round(dd * (oben & ((a + b) > 0)).sum()))
                w_ = rng.choice(tr, size=min(m_, len(tr)), replace=False)
                a[w_], b[w_] = 1, 0
                d_, c_ = profil(st0, such, a=a, b=b); ro = raender(d_, c_)[1]
                z_ = (ro - rmu[k0][1]) / rsd[k0][1]
                dp_, cp_ = profil(st0, pruef, a=a, b=b); rp_ = raender(dp_, cp_)[1]
                d22_, c22_ = profil(st0, gitter22, a=a, b=b, na=MA, nb=MB, minn=20); r22_ = raender(d22_, c22_)[1]
                jj = 0
                for y in (2023, 2024, 2025, 2026):
                    dy_, cy_ = profil(st0, gitter & (JAHR == y), a=a, b=b, minn=20)
                    ry = raender(dy_, cy_)[1]
                    jj += int(np.isfinite(ry) and ry > 0)
                gef += int(z_ > rgrenze and rp_ > 0 and r22_ > 0 and jj >= 3)
            print("     d = +%.2f: gefunden %d von 5" % (dd, gef))

    if gruppe == "altersachse":
        altersachse_fein(namen, KURVEN, GRENZEN, teile, STD, JAHR, A, B, NA, NB, MA, MB,
                         such, pruef, gitter22, verschiebe)

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
    # ⛔ Bis 28.09. druckte dieser Abschnitt als *Rand* nur d[0]/d[11] (die
    # aeusserste Einzelstufe) - und wurde gegen den Zweistufen-Rand des
    # Randkriteriums gelesen (2.675 -> 2.676). Jetzt derselbe Rand; die feine
    # Achse steht in `altersachse_fein` (--gruppe altersachse)
    print("ALTERSACHSE (Merkmal L Stunden alt): S und RAND wie im Randkriterium (unten 0+1 / oben 10+11), Suche")
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
            ru_, ro_ = raender(d, cnt)
            teile_s.append("%dh: S %.2f (%.0f%%) Rand %+.3f/%+.3f" % (L, S(d, cnt), 100 * S(d, cnt) / max(s_wert[k], 1e-12), ru_, ro_))
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
