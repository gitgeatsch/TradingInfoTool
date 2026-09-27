# -*- coding: utf-8 -*-
"""Schritt 2: die Achse `ema_abstand_atr` an BEIDEN Enden, gegen SIEBEN Zielgroessen.

**27.09.2026.** Nutzerauftrag: *"Werkzeug bauen und Schritt 2 messen - dann
eine Bewertung des Ergebnisses gemeinsam abstimmen, schrittweise."* Und
davor: *"Zielgroesse ist zu MESSEN."*

WOZU
    2.626/2.631/2.647 sagen: das UNTERE Ende (weit unter dem eigenen
    48-h-EMA, in eigener ATR) traegt. 2.648 sagt: auf einem PROZENT-
    Ereignis zeigt dieselbe Lage mehr Abstuerze als Anstiege. 2.643 hat
    daraus OHNE Messung die ganze Achse zur Risikosperre erklaert. Dieses
    Werkzeug misst beide Enden auf DENSELBEN Ankern gegen alle
    Zielgroessen, damit der Widerspruch eine Zahl bekommt.

⛔ KEIN TRAILING. Nutzervorgabe 27.09.: *"Trailing ist hier falsch und
gehoert zur Positionsfuehrung, die spaeter kommt."* 2.626/2.631/2.647
haben den Ertrag MIT Trailing gemessen (Stop wird ab +1,5 R 0,5 R unter
den Hoechstkurs nachgezogen) - also Lage UND Fuehrungsregel zusammen.
Hier wird die LAGE gemessen: regelfrei (MFE, MAE, Ereignisse) und mit
FESTEN Barrieren (Stop und Ziel, ohne Nachziehen) als Messwerkzeug.

WIE
    TEIL 0  Selbstprobe: dieselben ANKER wie 2.631 (Signalzahlen je
            Schwelle) - sonst Abbruch.
    TEIL 1  sechs Auswahlen (W <= -1,0 / -1,2881 / -1,5 und W >= +1,0 /
            +1,2881 / +1,5) x sieben Zielgroessen, je gegen
              - den MARKT (alle Anker)
              - die tagestreue NULLWELT (je Tag so viele Zufallsanker wie
                die Auswahl, 40 Ziehungen), Urteil gegen ein
                BESTES-VON-6-Band je Zielgroesse (Mehrfachtesten)
              - das EIGENE SYMBOL (Anteil des Effekts, der symbolintern
                bleibt)
              - jedes KALENDERJAHR (aus dem Datum)
    TEIL 2  ATR-Kontrolle fuer das untere Ende
    TEIL 3  Positivkontrolle: ein gepflanzter Effekt auf Zufallsankern mit
            der Tagesverteilung der Auswahl muss gefunden werden

DIE SIEBEN ZIELGROESSEN (Messfenster H24; Prozent-Ereignisse H6 wie 2.648)
    ziel_vor_stop  feste Barrieren +1 / -1 ATR: 1, wenn das Ziel ZUERST
                   erreicht wird (Gleichstand in einer Stunde = Stop, 2.583)
    mfe_atr        groesster Anstieg in ATR - CHANCE, regelfrei
    mae_atr        groesster Rueckgang in ATR - RISIKO (niedriger = besser)
    ev_auf_pct     +15 % innerhalb 6 h erreicht (Rate)
    ev_ab_pct      -10 % innerhalb 6 h erreicht (Rate, niedriger = besser)
    ev_auf_atr     +1 ATR innerhalb 24 h erreicht (Rate)
    ev_ab_atr      -1 ATR innerhalb 24 h erreicht (Rate, niedriger = besser)

NUR LESEND: `stundenkurse.db` mit `mode=ro`. Keine Gebuehren (Regel 2).
Ebene B (Erfolgsmessung, 2.641).
⚠️ Die Kopfzeile von `messnorm` gilt hier NICHT (2.653); die Pruefform
steht oben.
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from hebel_neubau import pruefe_quellen                         # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema                      # noqa: E402

pruefe_quellen("ema_abstand_atr")

STUNDEN_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "data", "stundenkurse.db")
EMA_L, VORLAUF = 48, 240          # 2.606 / messe_hebel_neudimension
HZ, BARRIERE = 24, 1.00           # Messfenster 2.642, Barriere wie 2.644
H_EV = 6                          # Prozent-Ereignisse wie 2.648
SAAT = 20260927
ZIEHUNGEN = N.NULL_ZIEHUNGEN      # 40

AUSWAHLEN = (("unten -1,0", "<=", -1.0), ("unten -1,2881", "<=", -1.2881),
             ("unten -1,5", "<=", -1.5), ("oben +1,0", ">=", 1.0),
             ("oben +1,2881", ">=", 1.2881), ("oben +1,5", ">=", 1.5))
# (Name, hoeher ist besser?, Einheit)
ZIELE = (("ziel_vor_stop", True, "Rate"),
         ("mfe_atr", True, "ATR"), ("mae_atr", False, "ATR"),
         ("ev_auf_pct", True, "Rate"), ("ev_ab_pct", False, "Rate"),
         ("ev_auf_atr", True, "Rate"), ("ev_ab_atr", False, "Rate"))

# 2.631 TEIL 1, registriert 26.09.2026 - die Selbstprobe der ANKER
REGISTRIERT_2631 = {-1.5: 3372, -1.2: 16940, -1.0: 46713}


def lade_kurse():
    """Wie `messe_reverse_scharfe_anstiege.lade_kurse` - dieselbe Menge."""
    c = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    syms = [r[0] for r in c.execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol "
        "HAVING COUNT(*) > 2000 ORDER BY COUNT(*) DESC")]
    aus = {}
    for s in syms:
        rows = c.execute(
            "SELECT stunde, high, low, close FROM stundenkurse "
            "WHERE symbol=? ORDER BY stunde", (s,)).fetchall()
        if len(rows) < 500:
            continue
        aus[s] = ([r[0] for r in rows],
                  np.array([r[1] for r in rows], float),
                  np.array([r[2] for r in rows], float),
                  np.array([r[3] for r in rows], float))
    c.close()
    return aus


def extreme(high, low, H):
    """-> (max high, min low) ueber die Stunden t+1 .. t+H."""
    n = len(high)
    idx = np.arange(n)
    mx = np.full(n, -np.inf)
    mn = np.full(n, np.inf)
    for s in range(1, H + 1):
        j = np.minimum(idx + s, n - 1)
        mx = np.maximum(mx, high[j])
        mn = np.minimum(mn, low[j])
    return mx, mn


def ziel_vor_stop(high, low, close, einheit):
    """-> 1.0, wenn +BARRIERE vor -BARRIERE erreicht wird, sonst 0.0.

    Feste Barrieren, KEIN Nachziehen. Gleichstand in derselben Stunde
    zaehlt als Stop (2.583) - konservativ.
    """
    n = len(close)
    idx = np.arange(n)
    ziel = close + BARRIERE * einheit
    stop = close - BARRIERE * einheit
    fertig = np.zeros(n, bool)
    treffer = np.zeros(n)
    for s in range(1, HZ + 1):
        j = np.minimum(idx + s, n - 1)
        raus = ~fertig & (low[j] <= stop)
        fertig |= raus
        rein = ~fertig & (high[j] >= ziel)
        treffer[rein] = 1.0
        fertig |= rein
    return treffer


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 110)
    print("SCHRITT 2 - DIE ACHSE AN BEIDEN ENDEN, GEGEN SIEBEN ZIELGROESSEN")
    print("=" * 110)
    print("  Messfenster H%d; feste Barrieren +/-%.2f ATR ohne Nachziehen; "
          "Prozent-Ereignisse H%d wie 2.648" % (HZ, BARRIERE, H_EV))
    print("  ⛔ KEIN TRAILING - Positionsfuehrung kommt spaeter "
          "(Nutzervorgabe 27.09.)")
    print("  Nullwelt tagestreu, %d Ziehungen; Bestes-von-6 je Zielgroesse; "
          "ohne Gebuehren (Regel 2)" % ZIEHUNGEN)
    print()

    kurse = lade_kurse()
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle)
    sid = {s: i for i, s in enumerate(sl)}
    jahr_je_stunde = np.array([int(x[:4]) for x in sl], np.int64)

    SP = {k: [] for k in ("G", "W", "SYM", "ATR")}
    Z = {k: [] for k, _b, _e in ZIELE}
    for si, (sym, (st, h, l, cc)) in enumerate(kurse.items()):
        if sym.upper() == "BTC":
            continue
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - HZ):] = False
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        einheit = np.maximum(atr * cc, 1e-12)
        mx24, mn24 = extreme(h, l, HZ)
        mx6, mn6 = extreme(h, l, H_EV)
        zvs = ziel_vor_stop(h, l, cc, einheit)
        SP["G"].append(np.array([sid[x] for x in st], np.int64)[sel])
        SP["W"].append(w[sel])
        SP["SYM"].append(np.full(len(sel), si, np.int64))
        SP["ATR"].append(atr[sel])
        Z["ziel_vor_stop"].append(zvs[sel])
        Z["mfe_atr"].append(((mx24 - cc) / einheit)[sel])
        Z["mae_atr"].append(((cc - mn24) / einheit)[sel])
        Z["ev_auf_pct"].append((mx6 >= cc * 1.15)[sel].astype(float))
        Z["ev_ab_pct"].append((mn6 <= cc * 0.90)[sel].astype(float))
        Z["ev_auf_atr"].append((mx24 >= cc + einheit)[sel].astype(float))
        Z["ev_ab_atr"].append((mn24 <= cc - einheit)[sel].astype(float))
    G = np.concatenate(SP["G"])
    W = np.concatenate(SP["W"])
    SYM = np.concatenate(SP["SYM"])
    ATR = np.concatenate(SP["ATR"])
    Z = {k: np.concatenate(v) for k, v in Z.items()}
    tag = G // 24
    jahr = jahr_je_stunde[G]
    n = len(G)
    print("  %d Anker · %d Tage · %d Symbole (BTC ausgenommen)"
          % (n, len(np.unique(tag)), len(np.unique(SYM))), flush=True)
    print()

    # ══ TEIL 0: SELBSTPROBE DER ANKER ═══════════════════════════════
    print("=" * 110)
    print("TEIL 0 - SELBSTPROBE: dieselben ANKER wie 2.631")
    ok0 = True
    for sw, k_reg in sorted(REGISTRIERT_2631.items()):
        k = int((W <= sw).sum())
        ok0 &= k == k_reg
        print("  W <= %-5.1f  Signale %6d (reg. %6d)  %s"
              % (sw, k, k_reg, "✔" if k == k_reg else "⛔ ABWEICHUNG"))
    if not ok0:
        print()
        print("  ⛔ ABBRUCH - die Ankermenge ist nicht die von 2.631.")
        return 1
    print("  ✔ dieselben Anker - alles Weitere steht auf derselben Menge")
    print()

    # ══ Nullwelt: tagestreu ═════════════════════════════════════════
    rng = np.random.default_rng(SAAT)
    reihenfolge = np.argsort(tag, kind="stable")
    t_sort = tag[reihenfolge]
    grenzen = np.flatnonzero(np.diff(t_sort)) + 1
    starts = np.concatenate([[0], grenzen])
    enden = np.concatenate([grenzen, [n]])
    pool = {int(t_sort[a]): reihenfolge[a:b] for a, b in zip(starts, enden)}

    def ziehe(maske):
        je = dict(zip(*np.unique(tag[maske], return_counts=True)))
        a = [rng.choice(pool[int(t)], size=min(int(c), len(pool[int(t)])),
                        replace=False) for t, c in je.items()]
        return np.concatenate(a)

    markt = {k: float(v.mean()) for k, v in Z.items()}
    nsym = int(SYM.max()) + 1
    zaehl = np.maximum(np.bincount(SYM, minlength=nsym), 1)
    sym_mittel = {k: np.bincount(SYM, weights=v, minlength=nsym) / zaehl
                  for k, v in Z.items()}

    masken = [(W <= sw) if op_ == "<=" else (W >= sw)
              for _name, op_, sw in AUSWAHLEN]
    null = {k: np.zeros((ZIEHUNGEN, len(AUSWAHLEN))) for k, *_ in ZIELE}
    for z in range(ZIEHUNGEN):
        for ai, m in enumerate(masken):
            idx = ziehe(m)
            for k, *_ in ZIELE:
                null[k][z, ai] = Z[k][idx].mean()

    # ══ TEIL 1 ══════════════════════════════════════════════════════
    print("=" * 110)
    print("TEIL 1 - SECHS AUSWAHLEN x SIEBEN ZIELGROESSEN")
    print("  besser = in Richtung GUT (hoeher bei Chance, NIEDRIGER bei "
          "Risiko und Absturz)")
    print("  Null-Mitte = Mittel der tagestreuen Nullwelt; z gegen sie; "
          "Urteil gegen die Bestes-von-6-Grenze (90. Perzentil)")
    print("  intern = Anteil des Unterschieds zum Markt, der gegen das "
          "EIGENE Symbol bleibt · Jahre = besser als der Markt desselben "
          "Jahres")
    print()
    for k, besser_hoch, einheit in ZIELE:
        nm = null[k]
        mu = nm.mean(axis=0)
        sd = np.maximum(nm.std(axis=0, ddof=1), 1e-12)
        vz = 1.0 if besser_hoch else -1.0
        zmax = np.max(vz * (nm - mu) / sd, axis=1)
        zgrenze = float(np.percentile(zmax, 90))
        print("  ── %s (%s, %s ist besser) · Markt %.4f · z-Grenze %.2f"
              % (k, einheit, "hoeher" if besser_hoch else "niedriger",
                 markt[k], zgrenze))
        print("     %-14s %8s %9s %10s %10s %8s %7s %7s  %s"
              % ("Auswahl", "Signale", "Wert", "Null-Mitte", "gg. Markt",
                 "z", "intern", "Jahre", "Urteil"))
        for ai, (name, _op, _sw) in enumerate(AUSWAHLEN):
            m = masken[ai]
            wert = float(Z[k][m].mean())
            z = vz * (wert - mu[ai]) / sd[ai]
            d_markt = wert - markt[k]
            d_int = float((Z[k][m] - sym_mittel[k][SYM[m]]).mean())
            intern = d_int / d_markt if abs(d_markt) > 1e-12 else float("nan")
            gut_j, n_j = 0, 0
            for j_ in np.unique(jahr[m]):
                mj = m & (jahr == j_)
                if mj.sum() < 30:
                    continue
                n_j += 1
                d_j = Z[k][mj].mean() - Z[k][jahr == j_].mean()
                gut_j += int(vz * d_j > 0)
            urteil = ("✔ besser" if z > zgrenze else
                      "⛔ schlechter" if -z > zgrenze else "· im Band")
            print("     %-14s %8d %9.4f %10.4f %+10.4f %8.2f %7.2f %4d/%-2d  %s"
                  % (name, int(m.sum()), wert, mu[ai], d_markt, z, intern,
                     gut_j, n_j, urteil))
        print()

    # ══ TEIL 2: ATR-KONTROLLE ═══════════════════════════════════════
    print("=" * 110)
    print("TEIL 2 - ATR-KONTROLLE: das untere Ende (W <= -1,2881) innerhalb "
          "jedes ATR-Fuenftels aller Anker")
    grenzen_atr = np.percentile(ATR, [20, 40, 60, 80])
    fuenftel = np.searchsorted(grenzen_atr, ATR)
    m_u = W <= -1.2881
    a = Z["mfe_atr"] - Z["mae_atr"]
    print("     %-8s %9s %12s %10s %10s %10s"
          % ("Fuenftel", "Signale", "zielvorstop", "alle", "mfe-mae", "alle"))
    for f in range(5):
        mf = fuenftel == f
        ms = mf & m_u
        if ms.sum() < 30:
            print("     %-8d %9d  (zu duenn)" % (f + 1, int(ms.sum())))
            continue
        print("     %-8d %9d %12.4f %10.4f %+10.4f %+10.4f"
              % (f + 1, int(ms.sum()), Z["ziel_vor_stop"][ms].mean(),
                 Z["ziel_vor_stop"][mf].mean(), a[ms].mean(), a[mf].mean()))
    print("  ATR der Auswahl / Median aller: %.2f"
          % (float(np.median(ATR[m_u])) / float(np.median(ATR))))
    print()

    # ══ TEIL 3: POSITIVKONTROLLE ════════════════════════════════════
    print("=" * 110)
    print("TEIL 3 - POSITIVKONTROLLE: Zufallsanker mit der Tagesverteilung "
          "von W <= -1,2881, auf mfe_atr ein Effekt gepflanzt")
    band = float(np.percentile(null["mfe_atr"][:, 1], 90))
    for delta in (0.01, 0.03, 0.05, 0.10):
        gefunden = 0
        for _ in range(5):
            idx = ziehe(m_u)
            gefunden += int(float(Z["mfe_atr"][idx].mean()) + delta > band)
        print("  gepflanzt %+.2f ATR  gefunden %d von 5 (Band %.4f)"
              % (delta, gefunden, band))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
