# -*- coding: utf-8 -*-
"""E2b: die BESTEN Lagen erheben - selten, optimal, hohe Wahrscheinlichkeit.

**27.09.2026.** Nutzervorgabe: *"wir suchen gute Signale, das bedeutet nicht
jede Kombination oder Messwert muss ins System - darum verwende ich OPTIMAL
und hohe Wahrscheinlichkeit - nicht die Anzahl der Signale, sondern nur jene,
wo es sich lohnen koennte, das Risiko einzugehen - und die Abstufungen waeren
die Hebelhoehe."* Und: *"nicht nur 24 h, sondern bis zu 72, wenn moeglich."*

WAS GEMESSEN WIRD
    Von den Ankern, die binnen H Stunden +5 % oder -5 % erreichen, wie viele
    gehen ZUERST nach oben?  p = auf5 / (auf5 + ab5)
    Bezug ist das EIGENE Asset: die erwartete Quote aus den Grundraten der
    ausgewaehlten Symbole im selben Zeitraum. Vorsprung = p - p_erwartet.
    Dazu Hoehe (mfe) und Risiko vor dem Hoechstpunkt (maevp), und wie oft
    +10 % vor -5 % kommt (auf10).

GEGEN UEBERANPASSUNG - die Kernregel dieses Werkzeugs
    SUCHE nur in 2021-12 bis 2024-12. Die Schwellen kommen aus DIESEM
    Zeitraum. PRUEFUNG unberuehrt in 2025 bis 2026, mit denselben Schwellen.
    Nur die besten 10 je Fenster gehen in die Pruefung, und nur ueber diese
    30 zaehlt das Mehrfachtesten (Bestes-von-30, symboltreue Nullwelt, 40
    Ziehungen). Was in der Pruefung nicht haelt, ist kein Befund.

KANDIDATEN (Richtungsspuren aus E2, dazu zwei Hoehen-Merkmale)
    hoch   ema_abstand_atr, rsi, momentum_kurz                 (>= P90/95/99)
    tief   konten_verh, top_konten_verh, top_summe_verh,
           funding_vortag                                      (<= P1/5/10)
    Hoehe  vola_kausal hoch, oi_je_umsatz tief
    einzeln und paarweise (verschiedene Merkmale), Fenster 6 / 24 / 72 h

BESTAETIGUNG (Nutzerhinweis: oft pruefen, Richtung bestaetigen): fuer die in
der Pruefung haltenden - Signal vor 1 bzw. 3 h UND Kurs seither gestiegen.

Daten und Merkmale: `messe_e2_beitraege.lade()` - dieselben Anker wie E2
(kausal, lueckenfrei, funding als Vortagswert). NUR LESEND. Kein Stop, kein
Trailing. Keine Gebuehren (Regel 2). Ebene B (2.641).
"""
from __future__ import annotations

import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402

FENSTER = (6, 24, 72)
SUCHE_BIS = 2024
MIN_AUFGELOEST_SUCHE = 300
MIN_AUFGELOEST_PRUEF = 100
TOP_K = 10
ZIEHUNGEN, SAAT = 40, 20260928
HOCH = ("ema_abstand_atr", "rsi", "momentum_kurz", "vola_kausal")
TIEF = ("konten_verh", "top_konten_verh", "top_summe_verh", "funding_vortag",
        "oi_je_umsatz")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 120)
    print("E2b - DIE BESTEN LAGEN: selten, optimal, hohe Wahrscheinlichkeit "
          "(Suche bis %d, Pruefung ab %d)" % (SUCHE_BIS, SUCHE_BIS + 1))
    print("=" * 120)
    print("  p = Anteil 'zuerst +5 %%' unter den Ankern, die binnen H +5 %% "
          "oder -5 %% erreichen · Bezug: das eigene Asset im selben Zeitraum")
    print("  kein Stop, kein Trailing · ohne Gebuehren (Regel 2)")
    print()
    D = E2.lade()
    F, Z, SYM, JAHR, STD, CC, TAG = (D[k] for k in ("F", "Z", "SYM", "JAHR",
                                                    "STD", "CC", "TAG"))
    n = D["n"]
    nsym = int(SYM.max()) + 1
    suche = JAHR <= SUCHE_BIS
    pruef = ~suche
    rng = np.random.default_rng(SAAT)
    print("  %d Anker · Suche %d · Pruefung %d" % (n, int(suche.sum()),
                                                  int(pruef.sum())))
    print()

    # Grundraten je Symbol, getrennt nach Zeitraum und Fenster
    def grundrate(zeitraum, f):
        a = np.bincount(SYM[zeitraum], weights=Z[f]["auf5"][zeitraum], minlength=nsym)
        b = np.bincount(SYM[zeitraum], weights=Z[f]["ab5"][zeitraum], minlength=nsym)
        k = np.maximum(np.bincount(SYM[zeitraum], minlength=nsym), 1)
        return a / k, b / k

    GR = {(z, f): grundrate(m, f) for z, m in (("s", suche), ("p", pruef))
          for f in FENSTER}

    def kennzahlen(maske, f, zr):
        ra, rb = GR[(zr, f)]
        up = Z[f]["auf5"][maske].sum()
        dn = Z[f]["ab5"][maske].sum()
        eu = ra[SYM[maske]].sum()
        ed = rb[SYM[maske]].sum()
        p = up / max(up + dn, 1e-12)
        pe = eu / max(eu + ed, 1e-12)
        return p, pe, int(up + dn)

    # Schwellen AUS DEM SUCHZEITRAUM
    bedingungen = []
    for m in HOCH:
        v = F[m][suche]
        for q in (90, 95, 99):
            bedingungen.append((m, ">=", q, float(np.nanpercentile(v, q))))
    for m in TIEF:
        v = F[m][suche]
        for q in (1, 5, 10):
            bedingungen.append((m, "<=", q, float(np.nanpercentile(v, q))))
    B = {}
    for m, op, q, sw in bedingungen:
        v = F[m]
        with np.errstate(invalid="ignore"):
            B[(m, q)] = np.isfinite(v) & ((v >= sw) if op == ">=" else (v <= sw))
    kandidaten = [((m, q),) for m, _op, q, _sw in bedingungen]
    for (a, b) in itertools.combinations(bedingungen, 2):
        if a[0] != b[0]:
            kandidaten.append(((a[0], a[2]), (b[0], b[2])))
    schwelle = {(m, q): (op, sw) for m, op, q, sw in bedingungen}
    print("  %d Bedingungen · %d Kandidaten (einzeln und paarweise) je "
          "Fenster" % (len(bedingungen), len(kandidaten)))
    print()

    def maske_von(k):
        m = B[k[0]].copy()
        for x in k[1:]:
            m &= B[x]
        return m

    def name(k):
        return " & ".join("%s %s%s" % (m, "hoch P" if schwelle[(m, q)][0] == ">="
                                       else "tief P", q) for m, q in k)

    # ══ SUCHE ═══════════════════════════════════════════════════════
    auswahl = []
    for f in FENSTER:
        liste = []
        for k in kandidaten:
            m = maske_von(k)
            ms = m & suche
            p, pe, nres = kennzahlen(ms, f, "s")
            if nres < MIN_AUFGELOEST_SUCHE:
                continue
            # Jahre im Suchzeitraum: Vorsprung positiv?
            jj = [kennzahlen(ms & (JAHR == j), f, "s") for j in (2022, 2023, 2024)]
            j_ok = sum(1 for pj, pej, nj in jj if nj >= 30 and pj > pej)
            j_n = sum(1 for _pj, _pej, nj in jj if nj >= 30)
            liste.append((p - pe, p, pe, nres, j_ok, j_n, k))
        liste.sort(key=lambda x: -x[0])
        gewaehlt = [x for x in liste if x[5] >= 2 and x[4] == x[5]][:TOP_K]
        auswahl += [(f,) + x for x in gewaehlt]
        print("=" * 120)
        print("SUCHE H%d - die besten %d (Vorsprung, alle Suchjahre positiv), "
              "von %d mit genug Faellen" % (f, len(gewaehlt), len(liste)))
        print("     %-62s %7s %6s %6s %6s %6s" % ("Lage", "aufgel.", "p",
                                                "p_erw", "Vorspr", "Jahre"))
        for (v, p, pe, nres, jo, jn, k) in gewaehlt:
            print("     %-62s %7d %6.3f %6.3f %+6.3f %4d/%d"
                  % (name(k), nres, p, pe, v, jo, jn))
        print()

    # ══ PRUEFUNG ════════════════════════════════════════════════════
    print("=" * 120)
    print("PRUEFUNG 2025-2026 - dieselben Schwellen, unberuehrt, "
          "Bestes-von-%d gegen die symboltreue Nullwelt" % len(auswahl))
    pool_ids = np.flatnonzero(pruef)

    def ziehe_sym(maske):
        # je Auswahlanker ein Zufallsanker desselben Symbols aus dem
        # Pruefzeitraum
        ids = pool_ids
        o = ids[np.argsort(SYM[ids], kind="stable")]
        s = SYM[o]
        start = np.searchsorted(s, np.arange(nsym), "left")
        laenge = np.searchsorted(s, np.arange(nsym), "right") - start
        ss = SYM[maske]
        r = (rng.random(len(ss)) * np.maximum(laenge[ss], 1)).astype(np.int64)
        return o[start[ss] + r]

    zeilen = []
    null = np.zeros((ZIEHUNGEN, len(auswahl)))
    for i, (f, *_r, k) in enumerate(auswahl):
        mp = maske_von(k) & pruef
        for zi in range(ZIEHUNGEN):
            idx = ziehe_sym(mp)
            mm = np.zeros(n, bool)
            mm[idx] = True
            up = Z[f]["auf5"][idx].sum()
            dn = Z[f]["ab5"][idx].sum()
            ra, rb = GR[("p", f)]
            eu, ed = ra[SYM[idx]].sum(), rb[SYM[idx]].sum()
            null[zi, i] = up / max(up + dn, 1e-12) - eu / max(eu + ed, 1e-12)
    mu = null.mean(axis=0)
    sd = np.maximum(null.std(axis=0, ddof=1), 1e-12)
    zgrenze = float(np.percentile(np.max((null - mu) / sd, axis=1), 90))
    print("  z-Grenze (Bestes-von-%d): %.2f" % (len(auswahl), zgrenze))
    print()
    print("     %-4s %-60s %6s %6s %6s %7s %6s %6s %6s %6s %6s %6s  %s"
          % ("H", "Lage", "aufg.", "p", "p_erw", "Vorspr", "z", "2025", "2026",
             "Asset", "Sig/T", "auf10", "Urteil"))
    haelt = []
    tage_pruef = len(np.unique(TAG[pruef]))
    for i, (f, v_s, p_s, pe_s, n_s, jo, jn, k) in enumerate(auswahl):
        mp = maske_von(k) & pruef
        p, pe, nres = kennzahlen(mp, f, "p")
        vor = p - pe
        z = (vor - mu[i]) / sd[i]
        jahr_txt = []
        for j in (2025, 2026):
            pj, pej, nj = kennzahlen(mp & (JAHR == j), f, "p")
            jahr_txt.append("%+.3f" % (pj - pej) if nj >= 30 else "  -  ")
        ra, rb = GR[("p", f)]
        up_s = np.bincount(SYM[mp], weights=Z[f]["auf5"][mp], minlength=nsym)
        dn_s = np.bincount(SYM[mp], weights=Z[f]["ab5"][mp], minlength=nsym)
        gueltig = (up_s + dn_s) >= 10
        base = ra / np.maximum(ra + rb, 1e-12)
        asset = (np.mean((up_s[gueltig] / (up_s[gueltig] + dn_s[gueltig]))
                         > base[gueltig]) if gueltig.any() else np.nan)
        sig_tag = mp.sum() / max(tage_pruef, 1)
        auf10 = Z[f]["auf10"][mp].mean() if mp.sum() else np.nan
        ok = (nres >= MIN_AUFGELOEST_PRUEF and z > zgrenze and vor > 0
              and (not np.isfinite(asset) or asset >= 0.6))
        urteil = ("✔ HAELT" if ok else
                  "· zu duenn" if nres < MIN_AUFGELOEST_PRUEF else "✖ haelt nicht")
        if ok:
            haelt.append((f, k, mp))
        print("     H%-3d %-60s %6d %6.3f %6.3f %+7.3f %6.2f %6s %6s %5.0f%% %6.2f %6.3f  %s"
              % (f, name(k), nres, p, pe, vor, z, jahr_txt[0], jahr_txt[1],
                 100 * asset if np.isfinite(asset) else float("nan"),
                 sig_tag, auf10, urteil))
    print()
    print("  Suche zum Vergleich: die Vorspruenge oben lagen bei %s"
          % ", ".join("%+.3f" % x[1] for x in auswahl[:5]) + " …")
    print()

    # ══ BESTAETIGUNG ════════════════════════════════════════════════
    print("=" * 120)
    print("BESTAETIGUNG (nur fuer die haltenden, im Pruefzeitraum): Signal vor "
          "k h UND Kurs seither gestiegen, Einstieg jetzt")
    if not haelt:
        print("  keine Lage haelt in der Pruefung - nichts zu bestaetigen")
    ordnung = np.lexsort((STD, SYM))
    for f, k, mp in haelt:
        p, pe, nres = kennzahlen(mp, f, "p")
        print("  H%d %s" % (f, name(k)))
        print("     %-36s %7s %6s %6s %7s" % ("", "aufg.", "p", "p_erw", "Vorspr"))
        print("     %-36s %7d %6.3f %6.3f %+7.3f" % ("Signal jetzt", nres, p, pe, p - pe))
        signal = maske_von(k)
        for kk in (1, 3):
            o = ordnung
            gleich = (SYM[o][kk:] == SYM[o][:-kk]) & (STD[o][kk:] - STD[o][:-kk] == kk)
            spaeter, frueher = o[kk:][gleich], o[:-kk][gleich]
            for txt, bed in (("vor %dh, seither gestiegen" % kk, True),
                             ("vor %dh, seither NICHT gestiegen" % kk, False)):
                mm = np.zeros(n, bool)
                treffer = signal[frueher] & ((CC[spaeter] > CC[frueher]) == bed)
                mm[spaeter[treffer]] = True
                mm &= pruef
                pb, peb, nb = kennzahlen(mm, f, "p")
                if nb < 30:
                    print("     %-36s %7d  (zu duenn)" % (txt, nb))
                    continue
                print("     %-36s %7d %6.3f %6.3f %+7.3f" % (txt, nb, pb, peb, pb - peb))
        print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
