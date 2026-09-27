# -*- coding: utf-8 -*-
"""E2c: welche Lagen gingen den GROSSEN Bewegungen voraus - +20 / +30 % vor -10 %?

**27.09.2026.** Nutzervorgaben: *"5 Prozent finde ich eher als geringen
Anstieg"* und, mit zwei Bildern (Woche: fast alles gruen, +15 bis +157 %;
Tag: einzelne Ausreisser wie QNT +52,7 %), *"so etwas muessen wir erkennen
koennen und einsteigen"*. Dazu: *"nicht die Anzahl der Signale, sondern nur
jene, wo es sich lohnen koennte"* - Hebel 0 bis 5 Tage.

ZIELE je Einstieg (Lehrer-Fenster 24 h fuer den Tagesausreisser, 120 h fuer
den Schub ueber mehrere Tage):
    g20   +20 % wird erreicht, BEVOR -10 % eintritt
    g30   +30 % wird erreicht, BEVOR -10 % eintritt
    k10   -10 % zuerst (die Gefahr)
    Gleichstand in einer Stunde = -10 % zuerst (2.583). Kein Stop, kein
    Trailing - nur der Verlauf.

EPISODEN, NICHT STUNDEN: gezaehlt wird der Einstieg, wenn eine Lage
ERSCHEINT (in der Stunde davor war sie nicht erfuellt) - nicht jede Stunde,
in der sie besteht. Das korrigiert die Anker-Stunden-Zaehlung aus E2b.

BEZUG: das EIGENE Asset. Lift = Treffer / erwartete Treffer aus der
Grundrate des jeweiligen Symbols im selben Zeitraum.

GEGEN UEBERANPASSUNG: Suche 2021-12 bis 2024-12, Schwellen aus der Suche,
Pruefung unberuehrt 2025-2026; "haelt" nur, wenn BEIDE Pruefjahre ueber 1
liegen, gegen ein Bestes-von-N-Band der symboltreuen Nullwelt (40 Ziehungen)
ueber alle geprueften Kandidaten.

KANDIDATEN
    Asset   ema_abstand_atr, rsi, momentum_kurz, vola_kausal, volumenschub,
            oi_aenderung, eigene Rendite 24 h / 120 h            (hoch)
            konten_verh, top_konten_verh, top_summe_verh,
            funding_vortag, oi_je_umsatz                         (tief)
    Markt   BTC-Rendite 24 h / 120 h, BTC ueber seinem 48-h-EMA (in ATR),
            Breite = Anteil der Assets mit positiver 24-h-Rendite (hoch)
    einzeln und paarweise; Schwellen P90/95/99 bzw. P1/5/10

BESTAETIGUNG fuer die haltenden: Einstieg 1 bzw. 3 h nach dem Erscheinen,
wenn der Kurs seither gestiegen ist.

Daten: `messe_e2_beitraege.lade(hmax=120, ...)` - kausal, lueckenfrei,
funding als Vortagswert. NUR LESEND. Keine Gebuehren (Regel 2). Ebene B.
"""
from __future__ import annotations

import itertools
import os
import sqlite3
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402

FENSTER = (24, 120)
ZIELE = ("g20", "g30")
SUCHE_BIS = 2024
MIN_ERWARTET_SUCHE = 15.0
MIN_ERWARTET_JAHR = 3.0
TOP_K = 10
ZIEHUNGEN, SAAT = 40, 20260929
HOCH = ("ema_abstand_atr", "rsi", "momentum_kurz", "vola_kausal",
        "volumenschub", "oi_aenderung", "vor24", "vor120",
        "btc_24h", "btc_120h", "btc_ueber_ema", "breite_24h")
TIEF = ("konten_verh", "top_konten_verh", "top_summe_verh", "funding_vortag",
        "oi_je_umsatz")


def btc_merkmale():
    """-> {stunde: (btc_24h, btc_120h, btc_ueber_ema)} - kausal, aus den Stundenkursen."""
    c = sqlite3.connect("file:%s?mode=ro" % E2.STUNDEN_DB, uri=True)
    rows = c.execute("SELECT stunde, high, low, close, volumen FROM stundenkurse "
                     "WHERE symbol='BTC' ORDER BY stunde").fetchall()
    c.close()
    basis = datetime(2020, 1, 1)
    st = np.array([int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - basis)
                       .total_seconds() // 3600) for r in rows], np.int64)
    h = np.array([r[1] for r in rows], float)
    l = np.array([r[2] for r in rows], float)
    cc = np.array([r[3] for r in rows], float)
    vol = np.array([(r[4] or 0.0) for r in rows], float)
    km = E2.kursmerkmale(h, l, cc, vol)
    aus = {}
    pos = {int(s): i for i, s in enumerate(st)}
    for i, s in enumerate(st):
        j24, j120 = pos.get(int(s) - 24), pos.get(int(s) - 120)
        aus[int(s)] = (cc[i] / cc[j24] - 1.0 if j24 is not None else np.nan,
                       cc[i] / cc[j120] - 1.0 if j120 is not None else np.nan,
                       km["ema_abstand_atr"][i])
    return aus


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 124)
    print("E2c - WELCHE LAGEN GINGEN DEN GROSSEN BEWEGUNGEN VORAUS? "
          "(+20 / +30 %% vor -10 %%, Fenster 24 und 120 h)")
    print("=" * 124)
    print("  Episoden statt Stunden · Bezug: das eigene Asset · Suche bis %d, "
          "Pruefung ab %d · kein Stop, kein Trailing" % (SUCHE_BIS, SUCHE_BIS + 1))
    print()
    D = E2.lade(hmax=120, erste=(("up20", 1.20, True), ("up30", 1.30, True),
                                 ("dn10", 0.90, False)))
    F, T, X = D["F"], D["T"], D["X"]
    SYM, JAHR, STD, CC, TAG = D["SYM"], D["JAHR"], D["STD"], D["CC"], D["TAG"]
    n = D["n"]
    nsym = int(SYM.max()) + 1

    # Marktmerkmale
    B = btc_merkmale()
    leer = (np.nan, np.nan, np.nan)
    bt = np.array([B.get(int(s), leer) for s in STD])
    F = dict(F)
    F["btc_24h"], F["btc_120h"], F["btc_ueber_ema"] = bt[:, 0], bt[:, 1], bt[:, 2]
    F["vor24"], F["vor120"] = X["vor24"], X["vor120"]
    pos_plus = np.isfinite(X["vor24"]) & (X["vor24"] > 0)
    us, inv = np.unique(STD, return_inverse=True)
    breite = np.bincount(inv, weights=pos_plus) / np.maximum(np.bincount(inv), 1)
    F["breite_24h"] = breite[inv]

    # Ziele
    Zt = {}
    for W in FENSTER:
        Zt[("g20", W)] = ((T["up20"] <= W) & (T["up20"] < T["dn10"])).astype(float)
        Zt[("g30", W)] = ((T["up30"] <= W) & (T["up30"] < T["dn10"])).astype(float)
        Zt[("k10", W)] = ((T["dn10"] <= W) & (T["dn10"] <= T["up20"])).astype(float)
    suche, pruef = JAHR <= SUCHE_BIS, JAHR > SUCHE_BIS
    print("  %d Anker · %d Symbole · Suche %d · Pruefung %d · %d Anker wegen "
          "Luecken ausgeschlossen" % (n, len(np.unique(SYM)), int(suche.sum()),
                                      int(pruef.sum()), D["ausgeschlossen"]))
    print("  GRUNDRATEN je Anker:  " + " · ".join(
        "%s/%dh %.3f%%" % (z, W, 100 * Zt[(z, W)].mean())
        for W in FENSTER for z in ("g20", "g30", "k10")))
    print()

    # Grundrate je Symbol und Zeitraum
    def gr(zr, key):
        k = np.maximum(np.bincount(SYM[zr], minlength=nsym), 1)
        return np.bincount(SYM[zr], weights=Zt[key][zr], minlength=nsym) / k
    GR = {(zn, key): gr(zr, key) for zn, zr in (("s", suche), ("p", pruef))
          for key in Zt}

    # Episodenbeginn: Lage erfuellt, in der Stunde davor (selbes Symbol) nicht
    ordnung = np.lexsort((STD, SYM))
    vorher = np.full(n, -1, np.int64)
    gl = (SYM[ordnung][1:] == SYM[ordnung][:-1]) & (np.diff(STD[ordnung]) == 1)
    vorher[ordnung[1:][gl]] = ordnung[:-1][gl]

    def beginn(maske):
        v = vorher
        war = np.zeros(n, bool)
        ok = v >= 0
        war[ok] = maske[v[ok]]
        return maske & ~war

    def lift(maske, key, zn):
        treffer = Zt[key][maske].sum()
        erwartet = GR[(zn, key)][SYM[maske]].sum()
        return treffer / max(erwartet, 1e-12), treffer, erwartet

    # Schwellen aus der Suche
    bed = []
    for m in HOCH:
        v = F[m][suche]
        for q in (90, 95, 99):
            bed.append((m, ">=", q, float(np.nanpercentile(v, q))))
    for m in TIEF:
        v = F[m][suche]
        for q in (1, 5, 10):
            bed.append((m, "<=", q, float(np.nanpercentile(v, q))))
    BM = {}
    for m, op, q, sw in bed:
        v = F[m]
        with np.errstate(invalid="ignore"):
            BM[(m, q)] = np.isfinite(v) & ((v >= sw) if op == ">=" else (v <= sw))
    schw = {(m, q): (op, sw) for m, op, q, sw in bed}
    kand = [((m, q),) for m, _o, q, _s in bed]
    kand += [((a[0], a[2]), (b[0], b[2])) for a, b in itertools.combinations(bed, 2)
             if a[0] != b[0]]
    print("  %d Bedingungen · %d Kandidaten (einzeln und paarweise)"
          % (len(bed), len(kand)))
    print()

    def name(k):
        return " & ".join("%s %s%d" % (m, "hoch P" if schw[(m, q)][0] == ">="
                                       else "tief P", q) for m, q in k)

    # ⚠️ KEIN Masken-Cache: 1.275 Masken x 3,1 Mio Anker waeren ~4 GB -
    # dieselbe Falle wie 2.651. Jede Maske wird bei Bedarf neu gebildet.
    def maske(k):
        mm = BM[k[0]].copy()
        for x in k[1:]:
            mm &= BM[x]
        return beginn(mm)

    jahr_s = {j: suche & (JAHR == j) for j in (2022, 2023, 2024)}

    # ══ SUCHE - jede Maske EINMAL, ausgewertet fuer alle vier Ziele ══
    listen = {(z, W): [] for W in FENSTER for z in ZIELE}
    for k in kand:
        ms = maske(k) & suche
        if not ms.any():
            continue
        for W in FENSTER:
            for z in ZIELE:
                key = (z, W)
                lf, tr, er = lift(ms, key, "s")
                if er < MIN_ERWARTET_SUCHE:
                    continue
                jj = []
                for j, mj in jahr_s.items():
                    lj, _t, ej = lift(ms & mj, key, "s")
                    if ej >= MIN_ERWARTET_JAHR:
                        jj.append(lj > 1)
                if len(jj) < 2 or not all(jj):
                    continue
                gef, _tg, _eg = lift(ms, ("k10", W), "s")
                listen[key].append((lf, tr, er, gef, int(ms.sum()), k))
    auswahl = []
    for W in FENSTER:
        for z in ZIELE:
            key = (z, W)
            liste = listen[key]
            liste.sort(key=lambda x: -x[0])
            top = liste[:TOP_K]
            auswahl += [(key,) + x for x in top]
            print("=" * 124)
            print("SUCHE %s binnen %d h - die besten %d von %d (alle Suchjahre "
                  "ueber 1, mind. %.0f erwartete Treffer)"
                  % (z, W, len(top), len(liste), MIN_ERWARTET_SUCHE))
            print("     %-66s %7s %7s %7s %7s %8s" % ("Lage", "Einst.", "Treffer",
                                                   "erwart.", "Lift", "Gefahr"))
            for lf, tr, er, gef, ne, k in top:
                print("     %-66s %7d %7.0f %7.1f %7.2f %8.2f"
                      % (name(k), ne, tr, er, lf, gef))
            print()

    # ══ PRUEFUNG ════════════════════════════════════════════════════
    rng = np.random.default_rng(SAAT)
    ids = np.flatnonzero(pruef)
    o = ids[np.argsort(SYM[ids], kind="stable")]
    so = SYM[o]
    start = np.searchsorted(so, np.arange(nsym), "left")
    laenge = np.searchsorted(so, np.arange(nsym), "right") - start

    def ziehe(mm):
        s = SYM[mm]
        r = (rng.random(len(s)) * np.maximum(laenge[s], 1)).astype(np.int64)
        return o[start[s] + r]

    null = np.zeros((ZIEHUNGEN, len(auswahl)))
    for i, (key, *_r, k) in enumerate(auswahl):
        mp = maske(k) & pruef
        for zi in range(ZIEHUNGEN):
            idx = ziehe(mp)
            null[zi, i] = (Zt[key][idx].sum() /
                           max(GR[("p", key)][SYM[idx]].sum(), 1e-12))
    mu = null.mean(axis=0)
    sd = np.maximum(null.std(axis=0, ddof=1), 1e-12)
    zgr = float(np.percentile(np.max((null - mu) / sd, axis=1), 90))
    tage = len(np.unique(TAG[pruef]))
    print("=" * 124)
    print("PRUEFUNG 2025-2026 - dieselben Schwellen, Einstiege beim Erscheinen "
          "der Lage, Bestes-von-%d (z-Grenze %.2f)" % (len(auswahl), zgr))
    print("  ⚠️ Lift allein zeigt auch MEHR BEWEGUNG. Entscheidend ist q = "
          "P(Ziel zuerst) / (P(Ziel zuerst) + P(-10 %% zuerst)) gegen q des")
    print("     eigenen Assets (q_erw) - und P absolut. Bei +20 %% gegen -10 %% "
          "liegt die Gewinnschwelle bei q = 1/3, bei +30 %% bei q = 1/4.")
    print("     %-12s %-58s %6s %6s %6s %6s %6s %6s %6s %6s %6s %6s %6s  %s"
          % ("Ziel", "Lage", "Einst.", "Lift", "z", "2025", "2026", "Gefahr",
             "P_Ziel", "P_-10", "q", "q_erw", "Ein/T", "Urteil"))
    haelt = []
    for i, (key, lf_s, *_r, k) in enumerate(auswahl):
        mp = maske(k) & pruef
        lf, tr, er = lift(mp, key, "p")
        z = (lf - mu[i]) / sd[i]
        jt = []
        for j in (2025, 2026):
            lj, _t, ej = lift(mp & (JAHR == j), key, "p")
            jt.append((lj, ej))
        beide = all(ej >= MIN_ERWARTET_JAHR and lj > 1 for lj, ej in jt)
        gef, _t, _e = lift(mp, ("k10", key[1]), "p")
        ok = lf > 1 and z > zgr and beide
        urteil = ("✔ HAELT" if ok else "· zu wenig" if er < MIN_ERWARTET_JAHR * 2
                  else "✖ haelt nicht")
        if ok:
            haelt.append((key, k, mp))
        jtxt = ["%6.2f" % lj if ej >= MIN_ERWARTET_JAHR else "  -   " for lj, ej in jt]
        kk_ = ("k10", key[1])
        p_z = Zt[key][mp].mean() if mp.sum() else np.nan
        p_k = Zt[kk_][mp].mean() if mp.sum() else np.nan
        e_z = GR[("p", key)][SYM[mp]].mean() if mp.sum() else np.nan
        e_k = GR[("p", kk_)][SYM[mp]].mean() if mp.sum() else np.nan
        q = p_z / max(p_z + p_k, 1e-12)
        q_e = e_z / max(e_z + e_k, 1e-12)
        print("     %-12s %-58s %6d %6.2f %6.2f %s %s %6.2f %5.1f%% %5.1f%% %6.3f %6.3f %6.2f  %s"
              % ("%s/%dh" % key, name(k), int(mp.sum()), lf, z,
                 jtxt[0], jtxt[1], gef, 100 * p_z, 100 * p_k, q, q_e,
                 mp.sum() / max(tage, 1), urteil))
    print()

    # ══ BESTAETIGUNG ════════════════════════════════════════════════
    print("=" * 124)
    print("BESTAETIGUNG fuer die haltenden: Einstieg k Stunden NACH dem "
          "Erscheinen, wenn der Kurs seither gestiegen ist (Pruefzeitraum)")
    if not haelt:
        print("  keine Lage haelt - nichts zu bestaetigen")
    nachher = {}
    for kk in (1, 3):
        o2 = ordnung
        g2 = (SYM[o2][kk:] == SYM[o2][:-kk]) & (STD[o2][kk:] - STD[o2][:-kk] == kk)
        nachher[kk] = (o2[:-kk][g2], o2[kk:][g2])
    for key, k, mp in haelt:
        lf, tr, er = lift(mp, key, "p")
        print("  %s/%dh %s" % (key[0], key[1], name(k)))
        kk_ = ("k10", key[1])

        def q_von(mm):
            pz, pk = Zt[key][mm].mean(), Zt[kk_][mm].mean()
            return pz, pk, pz / max(pz + pk, 1e-12)
        print("     %-34s %7s %7s %7s %7s %7s %7s %7s" % ("", "Einst.", "Treffer",
                                                  "erwart.", "Lift", "P_Ziel",
                                                  "P_-10", "q"))
        pz, pk, q = q_von(mp)
        print("     %-34s %7d %7.0f %7.1f %7.2f %6.1f%% %6.1f%% %7.3f"
              % ("beim Erscheinen", int(mp.sum()), tr, er, lf, 100 * pz, 100 * pk, q))
        for kk in (1, 3):
            fr, sp = nachher[kk]
            for txt, bed_ in (("%d h spaeter, seither gestiegen" % kk, True),
                              ("%d h spaeter, NICHT gestiegen" % kk, False)):
                mm = np.zeros(n, bool)
                wahl = mp[fr] & ((CC[sp] > CC[fr]) == bed_)
                mm[sp[wahl]] = True
                l2, t2, e2 = lift(mm, key, "p")
                pz, pk, q = q_von(mm) if mm.any() else (np.nan, np.nan, np.nan)
                print("     %-34s %7d %7.0f %7.1f %7.2f %6.1f%% %6.1f%% %7.3f"
                      % (txt, int(mm.sum()), t2, e2, l2, 100 * pz, 100 * pk, q))
        print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
