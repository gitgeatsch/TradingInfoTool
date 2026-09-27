# -*- coding: utf-8 -*-
"""Die Lage VOR der Bewegung - das Optimum, nicht die Fortsetzung.

**27.09.2026.** Nutzerdefinition, woertlich:

> *"OPTIMUM ist: wir kennen die Bewertungen und die LAGE VOR DER
> BEWEGUNG. Das ist das Ziel, und ist fuer mich auch eine
> Wahrscheinlichkeit. Die Bewertung eines BEREITS GESTIEGENEN Assets ist
> weder das Ziel noch ist es ein Optimum - dazu brauche ich kein System,
> das sehe ich am Kurs, und dann steige ich ein und RATE, ob er noch
> weiter steigt."*

═══════════════════════════════════════════════════════════════════════
 ⛔ WAS DIESE MESSUNG AN DER VORIGEN KORRIGIERT
═══════════════════════════════════════════════════════════════════════

2.648 hat `momentum_kurz >= 0,8509` gemessen - woertlich *in den letzten
6 Stunden stark gestiegen* - und einen Lift von 6,931 auf *+15 Prozent in
den NAECHSTEN 6 Stunden* gefunden. Das ist zu einem guten Teil die
FORTSETZUNG einer laufenden Bewegung.

⚠️ Der Befund bleibt richtig. Was fehlte, ist die Frage, ob er FRUEH
GENUG ist.

═══════════════════════════════════════════════════════════════════════
 DIE ZWEI ACHSEN, DIE DAS TRENNEN
═══════════════════════════════════════════════════════════════════════

    KARENZ k      Die Lage bei t, das Ereignisfenster erst ab t+k.
                  ⭐ Bricht der Lift mit wachsendem k ein, war er
                  FORTSETZUNG. Haelt er, war die Lage VORHER erkennbar -
                  und genau das ist das Optimum.

    VORLAUF v     Wie weit ist das Asset in den letzten 24 Stunden schon
                  gelaufen, in eigenen ATR? Nutzerbeispiel: *wenn das
                  Asset bereits 50 Prozent gestiegen ist, ist das Risiko
                  einer Korrektur eher gegeben.*
                  ⚠️ Als eigene ACHSE, nicht als Sperre - so ist
                  ablesbar, WIE der Lift mit dem Vorlauf variiert, statt
                  eine Grenze zu setzen, die niemand begruenden kann.

⭐⭐ UND DIE KANDIDATEN SIND ANDERE. Gesucht sind Merkmale, die RUHE
beschreiben, nicht Bewegung:

    bandenge        der Squeeze - enge Baender vor dem Ausbruch. Rolle B
                    im Neubauplan, und bis heute NIE gemessen (in 2.645
                    lief es mit, aber gegen `E[R]` - das ist die A-Frage)
    vola_tief       niedrige Schwankung
    ema_abstand_atr die Lage zum eigenen Schnitt (Rolle C, laeuft als
                    Vergleich mit)
    oi_aenderung    Terminmarkt: baut sich Position auf, BEVOR der Kurs
                    reagiert? Rohgroesse, seit E-3 frei
    funding         dito

⚠️ `momentum_kurz` und `rsi` laufen MIT - als Kontrolle. Sie MUESSEN mit
wachsender Karenz einbrechen; tun sie es nicht, ist die Messung falsch.

⚠️ MODUS: `messen`. Keine Kalibrierung, keine Hebelhoehe.
⚠️ NUR LESEN.  python messe_lage_vor_der_bewegung.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from hebel_neubau import pruefe_quellen                         # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema                      # noqa: E402
from messe_hebel_neudimension import EMA_L, VORLAUF             # noqa: E402
from messe_assetebene_und_vorhersage import (ereignis,          # noqa: E402
                                             _lift_je_symbol,
                                             MIN_TREFFER, MIN_SYMBOLE,
                                             MIN_EREIGNISSE)

pruefe_quellen("bandenge", "vola", "ema_abstand_atr", "oi_aenderung",
               "funding", "momentum_kurz", "rsi")

HOEHE, FENSTER = 0.15, 6        # das Ereignis aus 2.648
KARENZEN = (0, 3, 6, 12, 24)    # Stunden Luecke zwischen Lage und Fenster
ZIEHUNGEN = 40
SAAT = 20260927
# ⚠️ Vorlaufschwellen ABSOLUT in eigener ATR, keine Perzentile (2.649).
VORLAUF_GRENZEN = (-1.0, 0.0, 1.0, 2.0)


def merkmale(h, l, cc):
    """-> dict. RUHE-Merkmale zuerst, die zwei Bewegungsmasse als Kontrolle."""
    atr = atr_tag_relativ(h, l, cc)
    e = ema(cc, EMA_L)
    n = len(cc)
    with np.errstate(divide="ignore", invalid="ignore"):
        w = (cc - e) / np.maximum(atr * cc, 1e-12)
        vor6 = np.concatenate([np.full(6, np.nan), cc[:-6]])
        mom = (cc / vor6 - 1.0) / np.maximum(atr, 1e-12)
        vor24 = np.concatenate([np.full(24, np.nan), cc[:-24]])
        vorlauf = (cc / vor24 - 1.0) / np.maximum(atr, 1e-12)
    # bandenge: Breite des 2-Sigma-Bands um den EMA, in eigener ATR.
    # ⚠️ Gleitende Standardabweichung ueber 48 Stunden - dasselbe Fenster
    # wie der EMA, damit beide dieselbe Lage beschreiben.
    k = EMA_L
    c2 = np.concatenate([[0.0], np.cumsum(cc)])
    c2q = np.concatenate([[0.0], np.cumsum(cc * cc)])
    idx = np.arange(n)
    a0 = np.maximum(0, idx - k + 1)
    anz = (idx - a0 + 1).astype(float)
    mit = (c2[idx + 1] - c2[a0]) / anz
    mq = (c2q[idx + 1] - c2q[a0]) / anz
    with np.errstate(invalid="ignore"):
        sd = np.sqrt(np.maximum(mq - mit * mit, 0.0))
        bandenge = (4.0 * sd) / np.maximum(atr * cc, 1e-12)
        # vola_tief: die ATR selbst, relativ zum eigenen Median
        vola = atr / np.maximum(np.nanmedian(atr), 1e-12)
    return ({"bandenge": bandenge, "vola": vola, "ema_abstand_atr": w,
             "momentum_kurz": mom, "rsi_platzhalter": None},
            atr, vorlauf)


def rsi14(cc):
    d = np.diff(cc, prepend=cc[0])
    auf = np.where(d > 0, d, 0.0)
    ab = np.where(d < 0, -d, 0.0)
    k = 14
    ma_a = np.convolve(auf, np.ones(k) / k, mode="full")[:len(cc)]
    ma_b = np.convolve(ab, np.ones(k) / k, mode="full")[:len(cc)]
    with np.errstate(divide="ignore", invalid="ignore"):
        return 100.0 - 100.0 / (1.0 + ma_a / np.maximum(ma_b, 1e-12))


def ereignis_mit_karenz(h, l, cc, hoehe, fenster, karenz, runter=False):
    """Das Ereignis im Fenster [t+karenz+1, t+karenz+fenster].

    ⚠️⚠️ DER BEZUG BLEIBT DER KURS BEI t, NICHT BEI t+karenz. Sonst
    misst man die Bewegung AB der Karenz und verliert genau die Frage -
    ein Einstieg findet bei t statt, und was zaehlt, ist der Gewinn ab
    DORT.
    """
    n = len(cc)
    idx = np.arange(n)
    best = np.full(n, np.inf if runter else -np.inf)
    for s in range(karenz + 1, karenz + fenster + 1):
        j = np.minimum(idx + s, n - 1)
        best = (np.minimum(best, l[j]) if runter
                else np.maximum(best, h[j]))
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = best / np.maximum(cc, 1e-12) - 1.0
    return (rel <= -hoehe) if runter else (rel >= hoehe)


def main() -> int:
    grenze = (int(sys.argv[sys.argv.index("--symbole") + 1])
              if "--symbole" in sys.argv else None)
    print("=" * 106)
    print("DIE LAGE VOR DER BEWEGUNG - Optimum statt Fortsetzung")
    print("=" * 106)
    print("  " + N.standardzeile())
    print("  Ereignis +%.0f %% in %d h · Karenzen %s"
          % (100 * HOEHE, FENSTER, ", ".join(str(k) for k in KARENZEN)))
    print("  ⚠️ MODUS: messen. Keine Kalibrierung, keine Hebelhoehe.")
    print("  ⚠️ Ohne Gebuehren und Finanzierung (Regel 2)")
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle)
    sid = {s: i for i, s in enumerate(sl)}
    _dat = np.array([x[:10] for x in sl])
    _, tag_je_i = np.unique(_dat, return_inverse=True)
    jahr_je_i = np.array([int(x[:4]) for x in sl], np.int64)

    NAMEN = ("bandenge", "vola", "ema_abstand_atr", "momentum_kurz", "rsi")
    G, SI, VL, namen = [], [], [], []
    MM = {k: [] for k in NAMEN}
    EV = {k: [] for k in KARENZEN}
    EVAB = {k: [] for k in KARENZEN}
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        mk, atr, vorlauf = merkmale(h, l, cc)
        mk["rsi"] = rsi14(cc)
        mk.pop("rsi_platzhalter", None)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(vorlauf)
        for k in NAMEN:
            gu &= np.isfinite(mk[k])
        gu[:VORLAUF] = False
        gu[-(max(KARENZEN) + FENSTER + 1):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        namen.append(sym)
        G.append(np.array([sid[x] for x in st], np.int64)[s2])
        SI.append(np.full(len(s2), len(namen) - 1, np.int64))
        VL.append(vorlauf[s2])
        for k in NAMEN:
            MM[k].append(mk[k][s2])
        for kar in KARENZEN:
            EV[kar].append(ereignis_mit_karenz(h, l, cc, HOEHE, FENSTER,
                                               kar)[s2])
            EVAB[kar].append(ereignis_mit_karenz(h, l, cc, HOEHE, FENSTER,
                                                 kar, True)[s2])
    G = np.concatenate(G)
    SI = np.concatenate(SI)
    VL = np.concatenate(VL)
    MM = {k: np.concatenate(v) for k, v in MM.items()}
    EV = {k: np.concatenate(v) for k, v in EV.items()}
    EVAB = {k: np.concatenate(v) for k, v in EVAB.items()}
    tag, jahr = tag_je_i[G], jahr_je_i[G]
    rng = np.random.default_rng(SAAT)
    print("  %d Anker · %d Tage · %d Symbole"
          % (len(G), len(np.unique(tag)), len(namen)), flush=True)
    print()

    # ══ TEIL 1: DIE KARENZ ═══════════════════════════════════════════
    print("=" * 106)
    print("TEIL 1 - DIE KARENZPROBE: bricht der Lift ein, wenn die Lage")
    print("         weiter VOR dem Ereignis liegt?")
    print("  ⭐ Ein Merkmal, das nur die FORTSETZUNG misst, verliert mit")
    print("     wachsendem k. Eines, das die Lage VORHER kennt, haelt.")
    print("  ⚠️ momentum_kurz und rsi laufen als KONTROLLE mit - sie")
    print("     MUESSEN einbrechen. Tun sie es nicht, ist die Messung falsch.")
    print()
    # Schwellen: absolut bzw. eigene Perzentile, KEIN Tagesrang
    grenzen = {}
    for k in NAMEN:
        W = MM[k]
        if k == "ema_abstand_atr":
            grenzen[k] = [("<=", -1.2881)]
        elif k in ("bandenge", "vola"):
            # RUHE = niedrige Werte; beide Raender pruefen
            q = np.nanpercentile(W, [5, 20, 80, 95])
            grenzen[k] = [("<=", q[0]), ("<=", q[1]),
                          (">=", q[2]), (">=", q[3])]
        else:
            q = np.nanpercentile(W, [99])
            grenzen[k] = [(">=", q[0])]
    print("  %-16s %10s %s" % ("Merkmal", "Schwelle",
                               " ".join("%9s" % ("k=%dh" % k)
                                        for k in KARENZEN)))
    verlauf = {}
    for k in NAMEN:
        for op, sw in grenzen[k]:
            tr = (MM[k] >= sw) if op == ">=" else (MM[k] <= sw)
            reihe = []
            for kar in KARENZEN:
                lf, pos, nsym = _lift_je_symbol(tr, EV[kar], SI, len(namen))
                reihe.append(lf if nsym >= MIN_SYMBOLE else np.nan)
            verlauf[(k, op, sw)] = reihe
            print("  %-16s %s%9.3f %s"
                  % (k, op, sw,
                     " ".join("%9.3f" % x if np.isfinite(x) else "        -"
                              for x in reihe)), flush=True)
    print()
    print("  ➤ ABLESEN: Verhaeltnis k=24h zu k=0h")
    print("  %-16s %10s %10s  %s" % ("Merkmal", "Schwelle", "Haltequote",
                                     "Deutung"))
    for (k, op, sw), reihe in verlauf.items():
        if not (np.isfinite(reihe[0]) and np.isfinite(reihe[-1])
                and reihe[0] > 0):
            continue
        q = reihe[-1] / reihe[0]
        print("  %-16s %s%9.3f %10.2f  %s"
              % (k, op, sw, q,
                 "⭐ haelt - Lage war VORHER da" if q >= 0.8 else
                 "⚠ faellt teilweise" if q >= 0.5 else
                 "⛔ bricht ein - war FORTSETZUNG"))
    print()

    # ══ TEIL 2: DER VORLAUF ══════════════════════════════════════════
    print("=" * 106)
    print("TEIL 2 - DER VORLAUF: wie wirkt es, wenn das Asset schon")
    print("         gelaufen ist?")
    print("  Nutzerbeispiel: *wenn das Asset bereits 50 Prozent gestiegen")
    print("  ist, ist das Risiko einer Korrektur eher gegeben*")
    print("  Vorlauf = Anstieg der letzten 24 h in eigener ATR")
    print()
    faecher = []
    letzte = -np.inf
    for g in VORLAUF_GRENZEN:
        faecher.append((letzte, g))
        letzte = g
    faecher.append((letzte, np.inf))
    print("  %-16s %10s %s" % ("Merkmal", "Schwelle",
                               " ".join("%12s" % ("%.0f..%.0f ATR" % (a, b)
                                                  if np.isfinite(a)
                                                  and np.isfinite(b)
                                                  else ("<%.0f" % b
                                                        if not np.isfinite(a)
                                                        else ">%.0f" % a))
                                        for a, b in faecher)))
    for k in NAMEN:
        for op, sw in grenzen[k]:
            tr = (MM[k] >= sw) if op == ">=" else (MM[k] <= sw)
            reihe = []
            for a, b in faecher:
                m = tr & (VL > a) & (VL <= b)
                ev = EV[0]
                lf, _p, nsym = _lift_je_symbol(m, ev, SI, len(namen))
                reihe.append(lf if nsym >= MIN_SYMBOLE else np.nan)
            print("  %-16s %s%9.3f %s"
                  % (k, op, sw,
                     " ".join("%12.3f" % x if np.isfinite(x)
                              else "           -" for x in reihe)),
                  flush=True)
    print()
    print("  ⚠️ Eine Zeile, die im LINKEN Fach (wenig gelaufen) genauso")
    print("     traegt wie rechts, ist das OPTIMUM. Eine, die nur rechts")
    print("     traegt, ist Fortsetzung.")
    print()

    # ══ TEIL 3: DIE SECHS PRUEFUNGEN ═════════════════════════════════
    #
    # ⚠️⚠️⚠️ TEIL 1 UND 2 SIND DIAGNOSE, KEIN URTEIL. Sie zeigen einen
    # Verlauf; ob eine Zelle TRAEGT, entscheidet sich hier. In der ersten
    # Fassung fehlte dieser Teil ganz - und `vola >= 2,126` haette mit
    # Lift 13 bis 22 wie ein grosser Fund ausgesehen. Genau davor warnt
    # 2.594: `vola` hatte dort den hoechsten Lift von allen und war NUR
    # BEWEGUNG.
    print("=" * 106)
    print("TEIL 3 - DIE SECHS PRUEFUNGEN, je KARENZ")
    print("  ⚠️ Teil 1 und 2 sind DIAGNOSE. Hier wird geurteilt.")
    print("  ⭐⭐ UND ZWAR JE KARENZ, nicht nur bei der strengsten.")
    print("     Die erste Fassung urteilte nur bei k=24h - damit war")
    print("     ablesbar, OB etwas haelt, aber nicht, WO die Grenze liegt.")
    print("     Genau das ist die Frage nach dem OPTIMUM.")
    print()
    for kar in KARENZEN:
      ev, evab = EV[kar], EVAB[kar]
      print("-" * 106)
      print("  KARENZ k=%dh - zwischen Bewertung und Ereignisfenster" % kar)
      print()
      zellen = [(k, op, sw) for k in NAMEN for op, sw in grenzen[k]]

      # Mehrfachtesten: tagestreue Permutation, Bestes-von-N ueber ALLE Zellen
      o = np.argsort(tag, kind="stable")
      gr = np.flatnonzero(np.diff(tag[o])) + 1
      bloecke = np.split(np.arange(len(tag)), gr)
      masken = []
      for (k, op, sw) in zellen:
          masken.append((MM[k] >= sw) if op == ">=" else (MM[k] <= sw))
      maxima, einzel = [], {i: [] for i in range(len(zellen))}
      for _z in range(ZIEHUNGEN):
          perm = np.arange(len(tag))
          for b in bloecke:
              perm[b] = rng.permutation(b)
          ev_p = ev[o][perm]
          basis = float(ev_p.mean())
          beste = 0.0
          for i, m in enumerate(masken):
              ms = m[o]
              if basis <= 0 or not ms.any():
                  continue
              lf = float(ev_p[ms].mean()) / basis
              einzel[i].append(lf)
              beste = max(beste, lf)
          maxima.append(beste)
      band_n = float(np.percentile(maxima, 90))
      print("  ➤ Bestes-von-%d-Band (tagestreu, %d Ziehungen): %.4f"
            % (len(zellen), ZIEHUNGEN, band_n))
      print()
      print("  %-16s %9s %8s %9s %9s %8s  %s"
            % ("Merkmal", "Schwelle", "Symbole", "Lift", "Einzelband",
               "Spiegel", "Urteil"))
      ueberlebt = []
      for i, (k, op, sw) in enumerate(zellen):
          m = masken[i]
          lf, pos, nsym = _lift_je_symbol(m, ev, SI, len(namen))
          if nsym < MIN_SYMBOLE or not np.isfinite(lf):
              print("  %-16s %s%8.3f %8d   zu duenn" % (k, op, sw, nsym))
              continue
          band_e = (float(np.percentile(einzel[i], 90)) if einzel[i]
                    else np.nan)
          lf_ab, _p, _n = _lift_je_symbol(m, evab, SI, len(namen))
          sp = (lf / lf_ab) if lf_ab and lf_ab > 0 else np.nan
          hoch = bool(sp and sp >= 1.717)
          haelt = bool(lf > band_n and pos >= 60.0 and hoch)
          if haelt:
              ueberlebt.append((k, op, sw, m, lf, pos, sp))
          print("  %-16s %s%8.3f %8d %9.3f %9.3f %8.3f  %s"
                % (k, op, sw, nsym, lf, band_e, sp,
                   "✔" if haelt else
                   "⛔ Richtung RUNTER" if sp and sp > 0 and 1 / sp >= 1.717
                   else "⚠ nur Bewegung" if lf > band_n
                   else "⛔ unter dem Band"))
      print()
      print("  ➤ %d von %d Zellen ueberleben Nullband, Mehrfachtesten, "
            "Richtung und je-Asset" % (len(ueberlebt), len(zellen)))
      print()

      # Zeitstabilitaet und Weglassprobe nur fuer die Ueberlebenden
      if not ueberlebt:
          print("  ⛔ Nichts zu pruefen - keine Zelle haelt.")
      js = np.unique(jahr)
      for (k, op, sw, m, lf, _pos, _sp) in ueberlebt:
          print("  %s %s %.4f  (Lift %.3f bei Karenz %dh)" % (k, op, sw, lf, kar))
          zs = ges = 0
          for j in js:
              jm = jahr == j
              n_j = int((jm & m).sum())
              b_ = float(ev[jm].mean()) if jm.any() else 0.0
              if b_ <= 0 or not n_j:
                  continue
              erw = n_j * b_
              l_j = float(ev[jm & m].mean()) / b_
              if erw < MIN_EREIGNISSE:
                  print("      %d  %7d Anker  Lift %8.3f  zu duenn (%.1f "
                        "erwartete Ereignisse)" % (j, n_j, l_j, erw))
                  continue
              ges += 1
              zs += l_j > 1.0
              print("      %d  %7d Anker  Lift %8.3f  %s"
                    % (j, n_j, l_j, "✔" if l_j > 1.0 else "⛔"))
          wl = wges = 0
          for j in list(js) + [None]:
              keep = np.ones(len(ev), bool) if j is None else (jahr != j)
              b_ = float(ev[keep].mean())
              if b_ <= 0 or not (keep & m).any():
                  continue
              wges += 1
              wl += (float(ev[keep & m].mean()) / b_) > 1.0
          print("      ➤ Zeitstabil %d von %d · Weglassprobe %d von %d  %s"
                % (zs, ges, wl, wges,
                   "✔ ALLE SECHS PRUEFUNGEN" if (ges and zs == ges
                                                 and wl == wges)
                   else "⛔ faellt"))
          print()
    print("=" * 106)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
