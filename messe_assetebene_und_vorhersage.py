# -*- coding: utf-8 -*-
"""Assetebene statt Marktebene - und sagt die Lage kurze hohe Anstiege voraus?

**27.09.2026.** Nutzerauftrag, woertlich:

> *"1. Messen, wo historisch die besten LAGEN und Risikobewertungen sind,
> haben wir schon gemacht - aber passt das? Das hast du auf MARKTEBENE
> durchgefuehrt? 2. auf ASSETEBENE umlegen und pruefen, ob diese bei
> KURZEN UND HOHEN ANSTIEGEN dies voraussagen koennen."*

═══════════════════════════════════════════════════════════════════════
 ⛔ DER BEFUND, DER DAZU GEFUEHRT HAT
═══════════════════════════════════════════════════════════════════════

Ja, es war Marktebene. `messe_inverse_achse.taeglich_beste` waehlt *je
Tag die besten 2 Prozent* - einen Querschnittsrang. **2.626** und
**2.628** stehen darauf.

⚠️⚠️ Und das widerspricht der Nutzerentscheidung vom SELBEN Tag
(2.608-2.610): *"Warum sprichst du von Rangfolge? Das System muss auch
bei nur 'Einem' Asset funktionieren und nicht besser oder schlechter
durch die Watchlist werden?!?!"*

➤ Ein Perzentil ist eine Aussage ueber die MENGE, keine ueber das ASSET.

═══════════════════════════════════════════════════════════════════════
 DIE ZWEI TEILE - und warum sie sich nicht verunreinigen
═══════════════════════════════════════════════════════════════════════

    TEIL 1   SAGT DIE LAGE KURZE HOHE ANSTIEGE VORAUS?
             Zielgroesse ist ein EREIGNIS (+X Prozent in Y Stunden),
             keine Handelsregel. ⭐ Damit braucht dieser Teil GAR KEINE
             Geometrie - kein Stop, kein Trailing, kein CRV. Er kann
             also nicht davon verunreinigt werden, dass Teil 2 die
             Geometrie noch sucht.
             Gerechnet JE SYMBOL, nicht ueber den Markt.

    TEIL 2   DIE ANORDNUNG AUF DER ABSOLUTEN SCHWELLE
             Dieselbe Gittersuche wie 2.628, aber die Auswahl ist eine
             ABSOLUTE Schwelle in ATR statt des Tagesrangs. Ergebnis ist
             eine MESSANORDNUNG (Modus `messen`), keine
             Systemeigenschaft.

⚠️⚠️ MODUS: `messen`. Hier wird NICHT kalibriert. Aus keinem Ergebnis
dieses Laufs folgt eine Hebelhoehe - das ist Modus `kalibrieren` und
kommt danach.

⚠️ NUR LESEN.  python messe_assetebene_und_vorhersage.py [--symbole N]
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
from messe_hebel_neudimension import (EMA_L, VORLAUF,           # noqa: E402
                                      trailing_mit_ausloeser)

# ⚠️⚠️ DER RIEGEL LAEUFT ZUERST. `taeglich_beste` steht seit heute auf
# der Verbotsliste - genau die Funktion, die 2.626/2.628 benutzt haben.
# Ein Aufruf hier wuerde abbrechen statt zu warnen.
pruefe_quellen("ema_abstand_atr", "momentum_kurz", "rsi")

# ── TEIL 1: die Ereignisse ──────────────────────────────────────────
# ⚠️ *kurze und hohe Anstiege* - die Groessen stammen aus 2.594, wo sie
# mit ihrer Haeufigkeit ausgewiesen sind: +10 % in 6 h kommt in 0,531 %
# der Anker vor, +15 % in 0,186 %. +20 % in 3 h waeren 0,087 % - nach
# der eigenen Vorabfestlegung zu selten fuer ein Geschaeft.
EREIGNISSE = ((0.10, 6), (0.10, 24), (0.15, 6), (0.05, 6))

# ⚠️ ABSOLUTE Schwellen in ATR - keine Perzentile. Dieselben wie 2.647,
# damit die Ergebnisse vergleichbar bleiben (R-R11).
SCHWELLEN = (-1.0, -1.2881, -1.5)

# ── TEIL 2: das Gitter ──────────────────────────────────────────────
FENSTER = (6, 12, 24, 48)
STOPS = (0.75, 1.00, 1.50, 2.00)
TRAIL_A, TRAIL_B = 1.5, 0.5     # aus 2.628; hier MESSWERKZEUG (Ebene B)

ZIEHUNGEN = 40
SAAT = 20260927
MIN_TREFFER = 30                # je Symbol
MIN_SYMBOLE = 20
MIN_JAHR = 100

# ⚠️⚠️⚠️ EINE QUOTE BRAUCHT EREIGNISSE, NICHT BEOBACHTUNGEN.
#
# ⛔ DER MANGEL, UND ICH HABE IHN NACH DEM ERGEBNIS GESEHEN - das gehoert
# dazugesagt: `MIN_JAHR` zaehlt ANKER. Bei einem Ereignis, das in 0,5 %
# der Anker vorkommt, sind 207 Anker rund EIN erwartetes Ereignis. Dort
# "Lift 0,000" zu messen ist keine Aussage, sondern eine leere Zelle -
# und genau daran sind im ersten Lauf beide Treffer gescheitert, jeweils
# am Jahr 2021. Das sind bei dieser Reihe VIER WOCHEN (sie beginnt am
# 01.12.2021).
#
# ✔ DIE REGEL IST NICHT NEU, SONDERN STEHT SCHON IM PROJEKT:
# `zaehle_kette._quote` gibt unter zehn Faellen einen Strich aus statt
# einer Prozentzahl (bewacht in `pruefe_pakete.py`, Paket Zaehlung:
# *unter zehn Faellen gibt es KEINE Quote*). Hier wird sie angewandt,
# nicht erfunden.
#
# ⚠️ Trotzdem werden BEIDE Zahlen ausgewiesen - mit und ohne die duennen
# Jahre. Wer eine Mindestmenge nach dem Ergebnis setzt, muss zeigen, was
# sie bewirkt.
MIN_EREIGNISSE = 10
# ⚠️ Die Spiegelprobe ist an einer Simulation GEEICHT (2.603): 1,717,
# nicht die urspruenglich registrierten 1,30. Kontrolle `zufall` 1,019.
SPIEGEL_SCHWELLE = 1.717

# ⚠️⚠️⚠️ DIE SPIEGELPROBE IST HIER GERICHTET - UND DAS WAR EIN FEHLER IN
# DER ERSTEN FASSUNG (27.09.2026, vor der Meldung gefunden).
#
# Die registrierte Regel aus 2.594 lautet *Staerke ist max(Lift, 1/Lift),
# das Nullband ist zweiseitig*. Sie ist richtig - fuer die Frage, ob ein
# Merkmal als BEITRAG etwas ordnet. Ein inverser Beitrag hat Wert.
#
# ⛔ HIER IST DIE FRAGE EINE ANDERE: *sagt die Lage kurze hohe ANSTIEGE
# voraus?* Ein Merkmal, das ABSTUERZE staerker vorhersagt als Anstiege,
# beantwortet sie mit NEIN - fuer einen Long-Einstieg ist es
# kontraindiziert, nicht "invers brauchbar".
#
# ⭐ Konkret gemessen: `ema_abstand_atr <= -1,0` hat Lift 2,671 nach oben
# und Spiegel 0,398, also Lift 6,71 nach UNTEN. Die erste Fassung gab
# dafuer ein Haeckchen. Richtig ist: diese Lage ist volatil in BEIDE
# Richtungen, mit Uebergewicht nach unten.
#
# ➤ Die Regel bleibt zweiseitig, das URTEIL wird gerichtet. Beide
#   Richtungen werden ausgewiesen - nur bestanden ist, was nach OBEN
#   zeigt.
RICHTUNG_GESUCHT = "hoch"


def merkmale(h, l, cc):
    """-> dict mit den drei Kandidaten. ALLE assetintern normiert.

    ⚠️⚠️ KEIN Querschnitt, kein Rang, kein Perzentil - jede Groesse ist
    aus der EIGENEN Reihe des Symbols gerechnet. Das ist die
    Nutzerentscheidung vom 26.09.: *muss auch bei nur EINEM Asset
    funktionieren*.
    """
    atr = atr_tag_relativ(h, l, cc)
    e = ema(cc, EMA_L)
    with np.errstate(divide="ignore", invalid="ignore"):
        w = (cc - e) / np.maximum(atr * cc, 1e-12)
        # momentum_kurz: 6-Stunden-Rendite in Einheiten der eigenen ATR
        vor = np.concatenate([np.full(6, np.nan), cc[:-6]])
        mom = (cc / vor - 1.0) / np.maximum(atr, 1e-12)
    # rsi(14) auf Stundenbasis
    d = np.diff(cc, prepend=cc[0])
    auf = np.where(d > 0, d, 0.0)
    ab = np.where(d < 0, -d, 0.0)
    k = 14
    ma_auf = np.convolve(auf, np.ones(k) / k, mode="full")[:len(cc)]
    ma_ab = np.convolve(ab, np.ones(k) / k, mode="full")[:len(cc)]
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = ma_auf / np.maximum(ma_ab, 1e-12)
        rsi = 100.0 - 100.0 / (1.0 + rs)
    return {"ema_abstand_atr": w, "momentum_kurz": mom, "rsi": rsi}, atr


def ereignis(h, l, cc, hoehe, fenster, runter=False):
    """-> bool je Anker: kommt in `fenster` Stunden ein Anstieg um `hoehe`?

    ⚠️⚠️ REGELFREI - kein Stop, kein Ziel, keine Reihenfolge. Es wird
    gefragt, ob der Kurs den Betrag ERREICHT, nicht ob ein Trade ihn
    mitgenommen haette. Genau deshalb braucht dieser Teil keine
    Geometrie.
    """
    n = len(cc)
    idx = np.arange(n)
    best = np.full(n, -np.inf) if not runter else np.full(n, np.inf)
    for s in range(1, fenster + 1):
        j = np.minimum(idx + s, n - 1)
        best = (np.minimum(best, l[j]) if runter
                else np.maximum(best, h[j]))
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = best / np.maximum(cc, 1e-12) - 1.0
    return (rel <= -hoehe) if runter else (rel >= hoehe)


def lade(grenze=None):
    """-> dict mit allen Reihen, je Symbol getrennt gehalten."""
    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle)
    sid = {s: i for i, s in enumerate(sl)}
    _dat = np.array([x[:10] for x in sl])
    _, tag_je_i = np.unique(_dat, return_inverse=True)
    jahr_je_i = np.array([int(x[:4]) for x in sl], np.int64)
    return kurse, sid, tag_je_i, jahr_je_i


def _lift_je_symbol(treffer, ereig, si, n_sym):
    """-> (lift_gewichtet, anteil_positiv, n_symbole) - JE SYMBOL.

    ⚠️⚠️ Lift = P(Ereignis | Lage, Symbol) / P(Ereignis | Symbol). Der
    Bezug ist das EIGENE Symbol, nicht der Markt - sonst misst die Zahl
    die Symbolauswahl (2.647).
    """
    lifte, gew = [], []
    for i in range(n_sym):
        m = si == i
        t = m & treffer
        k = int(t.sum())
        if k < MIN_TREFFER:
            continue
        basis = float(ereig[m].mean())
        if basis <= 0:
            continue
        lifte.append(float(ereig[t].mean()) / basis)
        gew.append(k)
    if not lifte:
        return np.nan, np.nan, 0
    lifte = np.array(lifte)
    gew = np.array(gew, float)
    return (float((lifte * gew).sum() / gew.sum()),
            100.0 * float((lifte > 1.0).mean()), len(lifte))


def _nullband_lift(treffer, ereig, tag, rng):
    """90. Perzentil des Lifts unter TAGESTREUER Mischung."""
    o = np.argsort(tag, kind="stable")
    ts, es, ms = tag[o], ereig[o], treffer[o]
    gr = np.flatnonzero(np.diff(ts)) + 1
    bloecke = np.split(np.arange(len(ts)), gr)
    basis = float(es.mean())
    if basis <= 0:
        return np.nan
    aus = []
    for _ in range(ZIEHUNGEN):
        s = k = 0
        for b in bloecke:
            z = int(ms[b].sum())
            if not z:
                continue
            s += float(es[rng.choice(b, size=z, replace=False)].sum())
            k += z
        aus.append((s / max(k, 1)) / basis)
    return float(np.percentile(aus, 90))


def main() -> int:
    grenze = (int(sys.argv[sys.argv.index("--symbole") + 1])
              if "--symbole" in sys.argv else None)

    print("=" * 104)
    print("ASSETEBENE STATT MARKTEBENE - und sagt die Lage kurze hohe "
          "Anstiege voraus?")
    print("=" * 104)
    print("  " + N.standardzeile())
    print("  ⚠️ MODUS: messen. Hier wird NICHT kalibriert - aus keinem")
    print("     Ergebnis folgt eine Hebelhoehe.")
    print("  ⚠️ AUSWAHL: ABSOLUTE Schwelle in ATR, KEIN Tagesrang")
    print("     (Nutzerentscheidung 26.09., 2.608-2.610)")
    print("  ⚠️ Ohne Gebuehren und Finanzierung (Regel 2)")
    print()

    kurse, sid, tag_je_i, jahr_je_i = lade(grenze)
    NAMEN = ("ema_abstand_atr", "momentum_kurz", "rsi")
    G, SI, namen = [], [], []
    MM = {k: [] for k in NAMEN}
    EV = {}          # (hoehe, fenster, runter) -> Liste
    ERT = []         # Teil 2 braucht Kurse - je Zelle neu gerechnet
    roh = []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        mk, atr = merkmale(h, l, cc)
        gu = np.isfinite(atr) & (atr > 0)
        for a in mk.values():
            gu &= np.isfinite(a)
        gu[:VORLAUF] = False
        gu[-max(FENSTER):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        i_sym = len(namen)
        namen.append(sym)
        G.append(gi[s2])
        SI.append(np.full(len(s2), i_sym, np.int64))
        for k in NAMEN:
            MM[k].append(mk[k][s2])
        for (ho, fe) in EREIGNISSE:
            for runter in (False, True):
                EV.setdefault((ho, fe, runter), []).append(
                    ereignis(h, l, cc, ho, fe, runter)[s2])
        roh.append((h, l, cc, atr, s2, gi[s2]))
    G = np.concatenate(G)
    SI = np.concatenate(SI)
    MM = {k: np.concatenate(v) for k, v in MM.items()}
    EV = {k: np.concatenate(v) for k, v in EV.items()}
    tag, jahr = tag_je_i[G], jahr_je_i[G]
    rng = np.random.default_rng(SAAT)
    print("  %d Anker · %d Tage · %d Symbole"
          % (len(G), len(np.unique(tag)), len(namen)), flush=True)
    print()

    # ══ TEIL 1 ═══════════════════════════════════════════════════════
    print("=" * 104)
    print("TEIL 1 - SAGT DIE LAGE KURZE HOHE ANSTIEGE VORAUS? (JE SYMBOL)")
    print("  ⭐ Zielgroesse ist ein EREIGNIS, keine Handelsregel - dieser")
    print("     Teil braucht KEINE Geometrie, keinen Stop, kein Trailing.")
    print("  Lift = P(Ereignis | Lage, Symbol) / P(Ereignis | Symbol)")
    print()
    befunde = {}
    for (ho, fe) in EREIGNISSE:
        ev = EV[(ho, fe, False)]
        ab = EV[(ho, fe, True)]
        print("  ── Ereignis: +%.0f %% in %d h · Haeufigkeit %.3f %% "
              "der Anker" % (100 * ho, fe, 100 * ev.mean()))
        print("     %-18s %9s %8s %9s %9s %9s %8s  %s"
              % ("Merkmal", "Schwelle", "Symbole", "Lift", "positiv",
                 "Nullband", "Spiegel", "Urteil"))
        for k in NAMEN:
            W = MM[k]
            # ⚠️ Fuer rsi und momentum ist NIEDRIG nicht automatisch die
            # gute Seite - die Richtung kommt aus den Daten, nicht aus
            # einer Annahme. Deshalb je Merkmal die eigenen Perzentile
            # als absolute Schwelle in EIGENEN Einheiten.
            if k == "ema_abstand_atr":
                grenzen = [(s, W <= s, "<=") for s in SCHWELLEN]
            else:
                qs = np.nanpercentile(W, [1, 5, 99])
                grenzen = [(qs[0], W <= qs[0], "<="),
                           (qs[1], W <= qs[1], "<="),
                           (qs[2], W >= qs[2], ">=")]
            for sw, tr, op in grenzen:
                lift, pos, nsym = _lift_je_symbol(tr, ev, SI, len(namen))
                if nsym < MIN_SYMBOLE:
                    print("     %-18s %s%7.3f %8d   zu wenige Symbole"
                          % (k, op, sw, nsym))
                    continue
                band = _nullband_lift(tr, ev, tag, rng)
                l_ab, _p2, _n2 = _lift_je_symbol(tr, ab, SI, len(namen))
                sp = (lift / l_ab) if l_ab and l_ab > 0 else np.nan
                # ⚠️⚠️ GERICHTET: nur nach OBEN zaehlt. Siehe
                # RICHTUNG_GESUCHT oben - `max(sp, 1/sp)` liess Merkmale
                # durch, die Abstuerze vorhersagen.
                hoch = bool(sp and sp >= SPIEGEL_SCHWELLE)
                runter = bool(sp and sp > 0 and 1.0 / sp >= SPIEGEL_SCHWELLE)
                ueber = bool(lift > band)
                gut = bool(ueber and pos >= 60.0 and hoch)
                befunde[(ho, fe, k, sw)] = (lift, pos, band, sp, gut)
                urteil = ("✔ Richtung HOCH" if gut else
                          "⛔ Richtung RUNTER" if runter else
                          "⚠ nur Bewegung" if ueber else "⛔")
                print("     %-18s %s%7.3f %8d %9.3f %8.1f%% %9.3f %8.3f  %s"
                      % (k, op, sw, nsym, lift, pos, band, sp, urteil))
        print()

    # ── MEHRFACHTESTEN: Bestes-von-N ueber ALLE Zellen ───────────────
    #
    # ⚠️⚠️⚠️ DIESER TEIL HAT IM ERSTEN LAUF GEFEHLT, und es ist GENAU der
    # Fehler, an dem 2.645 gefallen ist: dort war das Band je Kombination
    # EINZELN gerechnet, obwohl 32 durchsucht wurden - es war um Faktor
    # 1,9 zu lax. Hier wurden alle durchsucht (Merkmal x Schwelle x
    # Ereignis), also muss jede gegen das BESTE VON ALLEN zaehlen.
    #
    # ⭐ Die Ziehung ist billig zu machen: statt je Zelle zu ziehen, wird
    # der EREIGNISVEKTOR einmal je Ziehung INNERHALB der Tagesbloecke
    # gemischt. Das ist exakt dieselbe Nullhypothese (die Lage verliert
    # ihre Zuordnung, die Marktphase bleibt) und rechnet alle Zellen in
    # einem Durchgang.
    print("=" * 104)
    print("TEIL 1c - MEHRFACHTESTEN: Bestes-von-%d-Band" % len(befunde))
    print("  ⚠️ %d Zellen durchsucht - jede zaehlt gegen das BESTE von"
          % len(befunde))
    print("     allen, nicht gegen ihr eigenes Band (der Fehler von 2.645)")
    print()
    o = np.argsort(tag, kind="stable")
    gr = np.flatnonzero(np.diff(tag[o])) + 1
    bloecke = np.split(np.arange(len(tag)), gr)
    # Masken und Ereignisvektoren je Zelle einmal aufbauen
    zellen_m = []
    for (ho, fe, k, sw) in befunde:
        W = MM[k]
        zellen_m.append(((ho, fe), (W >= sw) if sw > 0 else (W <= sw)))
    maxima = []
    for _z in range(ZIEHUNGEN):
        # eine tagestreue Permutation, fuer ALLE Zellen dieselbe
        perm = np.arange(len(tag))
        for b in bloecke:
            perm[b] = rng.permutation(b)
        beste = 0.0
        for (schl, m) in zellen_m:
            ev_p = EV[(schl[0], schl[1], False)][o][perm]
            ms = m[o]
            basis = float(ev_p.mean())
            if basis <= 0 or not ms.any():
                continue
            beste = max(beste, float(ev_p[ms].mean()) / basis)
        maxima.append(beste)
    band_gesamt = float(np.percentile(maxima, 90))
    print("  ➤ Bestes-von-%d-Band (tagestreu, %d Ziehungen): %.4f"
          % (len(befunde), ZIEHUNGEN, band_gesamt))
    print()
    print("     %-18s %9s %8s %9s %11s  %s"
          % ("Merkmal", "Schwelle", "Ereignis", "Lift", "Band(%d)"
             % len(befunde), "Urteil"))
    ueberlebt = {}
    for schl, (lift, pos, band, sp, gut) in sorted(
            befunde.items(), key=lambda x: -x[1][0]):
        ho, fe, k, sw = schl
        haelt = bool(gut and lift > band_gesamt)
        if haelt:
            ueberlebt[schl] = (lift, pos, band, sp, True)
        if gut or lift > band_gesamt:
            print("     %-18s %9.4f %+5.0f%%/%dh %9.3f %11.4f  %s"
                  % (k, sw, 100 * ho, fe, lift, band_gesamt,
                     "✔" if haelt else
                     ("⛔ faellt am Mehrfachtesten" if gut
                      else "⛔ keine Richtung")))
    print()
    print("  ➤ %d von %d Zellen ueberleben BEIDES - Richtung UND "
          "Mehrfachtesten" % (len(ueberlebt), len(befunde)))
    print()
    befunde = ueberlebt

    # ── Die zwei fehlenden Pruefungen fuer die Treffer ───────────────
    #
    # ⚠️⚠️ Die erste Fassung hatte Nullwelt, je-Asset und Spiegelprobe -
    # aber NICHT Zeitstabilitaet und Weglassprobe. Nach der eigenen Regel
    # (die sechs Pruefungen, Paket `Hebelneubau`) darf daraus kein Befund
    # werden. Sie laufen deshalb NUR fuer das, was oben bestanden hat -
    # alles andere ist ohnehin erledigt.
    treffer = [(sl, k) for sl, (_l, _p, _b, _s, g) in befunde.items() if g]
    print("=" * 104)
    print("TEIL 1b - ZEITSTABILITAET UND WEGLASSPROBE fuer die %d Treffer"
          % len(treffer))
    print("  ⚠️ Ohne diese zwei ist es kein Befund (eigene Regel, Paket")
    print("     Hebelneubau). Sie liefen in der ersten Fassung nicht mit.")
    print()
    if not treffer:
        print("  ⛔ KEIN Treffer - nichts zu pruefen.")
    for (ho, fe, k, sw), _merkmal in treffer:
        ev = EV[(ho, fe, False)]
        W = MM[k]
        tr = (W >= sw) if sw > 0 else (W <= sw)
        basis_alle = float(ev.mean())
        js = np.unique(jahr)
        zs = ges = 0
        zs_alle = ges_alle = 0          # ohne Mindestmenge, zum Vergleich
        zeilen = []
        for j in js:
            jm = jahr == j
            n_j = int((jm & tr).sum())
            b_ = float(ev[jm].mean()) if jm.any() else 0.0
            if b_ <= 0 or not n_j:
                zeilen.append((int(j), n_j, 0.0, np.nan, "keine Basis"))
                continue
            a_ = float(ev[jm & tr].mean())
            lift = a_ / b_
            ok = lift > 1.0
            ges_alle += 1
            zs_alle += ok
            # ⚠️ Die Mindestmenge zaehlt ERWARTETE EREIGNISSE unter der
            # Nullhypothese, nicht Anker (siehe MIN_EREIGNISSE).
            erwartet = n_j * b_
            if n_j < MIN_JAHR or erwartet < MIN_EREIGNISSE:
                zeilen.append((int(j), n_j, lift, erwartet,
                               "zu duenn (%.1f erwartete Ereignisse)"
                               % erwartet))
                continue
            ges += 1
            zs += ok
            zeilen.append((int(j), n_j, lift, erwartet,
                           "✔" if ok else "⛔"))
        wl = wges = 0
        for j in list(js) + [None]:
            keep = np.ones(len(ev), bool) if j is None else (jahr != j)
            b_ = float(ev[keep].mean())
            if b_ <= 0 or not (keep & tr).any():
                continue
            wges += 1
            wl += (float(ev[keep & tr].mean()) / b_) > 1.0
        print("  %s %s %.4f  (Ereignis +%.0f %%/%d h, Basis %.3f %%)"
              % (k, ">=" if sw > 0 else "<=", sw, 100 * ho, fe,
                 100 * basis_alle))
        for j, n_j, lf, _b, mk in zeilen:
            print("      %d  %7d Anker  Lift %s  %s"
                  % (j, n_j, "%8.3f" % lf if np.isfinite(lf) else "       -",
                     mk))
        print("      ➤ Zeitstabil %d von %d (Jahre mit mindestens %d "
              "erwarteten Ereignissen)" % (zs, ges, MIN_EREIGNISSE))
        print("        ⚠️ OHNE die Mindestmenge waeren es %d von %d - die"
              % (zs_alle, ges_alle))
        print("           Regel wurde NACH dem Ergebnis angewandt, "
              "deshalb steht beides da.")
        print("      ➤ Weglassprobe %d von %d" % (wl, wges))
        print("      ➤ %s"
              % ("✔ ALLE SECHS PRUEFUNGEN" if (ges and zs == ges
                                               and wl == wges)
                 else "⛔ faellt"))
        print()

    # ══ TEIL 2 ═══════════════════════════════════════════════════════
    print("=" * 104)
    print("TEIL 2 - DIE MESSANORDNUNG AUF DER ABSOLUTEN SCHWELLE")
    print("  ⚠️ 2.628 hat dieses Gitter auf dem TAGESRANG gesucht (je Tag")
    print("     die besten 2 Prozent). Hier ist die Auswahl eine ABSOLUTE")
    print("     Schwelle - dieselbe Frage, die richtige Ebene.")
    print("  ⚠️⚠️ Das Ergebnis ist eine MESSANORDNUNG (Ebene B), KEINE")
    print("     Systemeigenschaft. Das Trailing gehoert in die")
    print("     Positionsfuehrung (T2), nicht in die Bewertung (T1).")
    print()
    ref = -1.2881
    print("  Auswahl: ema_abstand_atr <= %.4f · %d Zellen"
          % (ref, len(FENSTER) * len(STOPS)))
    print()
    print("     %6s %7s %10s %11s %11s  %s"
          % ("H", "Stop", "Signale", "Ertrag %", "Stopquote", "Zeitstabil"))
    m_sel = MM["ema_abstand_atr"] <= ref
    zellen = []
    for fe in FENSTER:
        for st in STOPS:
            E, R = [], []
            for (h, l, cc, atr, s2, _g) in roh:
                r, kp, _d = trailing_mit_ausloeser(
                    h, l, cc, atr, st, TRAIL_A, TRAIL_B, fe)
                E.append(kp[s2] * 100.0)
                R.append(r[s2])
            E = np.concatenate(E)
            R = np.concatenate(R)
            mm = m_sel & np.isfinite(E)
            if mm.sum() < 500:
                continue
            ertrag = float(E[mm].mean())
            # ⚠️ Der Stop ist erreicht, wenn R bei -1 landet (das
            # Anfangsrisiko ist der Nenner) - mit Toleranz, weil der
            # Trailing-Stop exakt dort schliesst.
            stopq = 100.0 * float((R[mm] <= -0.999).mean())
            js = np.unique(jahr[mm])
            tr = ges = 0
            for j in js:
                jm = (jahr == j)
                if int((jm & mm).sum()) < MIN_JAHR:
                    continue
                ges += 1
                tr += float(E[jm & mm].mean()) > float(E[jm & np.isfinite(E)].mean())
            zellen.append((fe, st, int(mm.sum()), ertrag, E, mm, tr, ges))
            print("     %6d %7.2f %10d %+11.4f %10.1f%%  %d von %d"
                  % (fe, st, int(mm.sum()), ertrag, stopq, tr, ges),
                  flush=True)
    if zellen:
        # ⚠️⚠️ BESTES-VON-N-BAND, TAGESTREU. Zwei Dinge, die die erste
        # Fassung falsch hatte:
        #   1. sie zog GLOBAL statt tagestreu - damit misst das Band die
        #      Marktphase mit und ist zu weit
        #   2. sie zog aus jeder Zelle einzeln und nahm das Maximum,
        #      aber ohne dieselbe Tagesstruktur
        # Der Standard verlangt tagestreu (2.216), und genau daran ist
        # 2.626 haengengeblieben.
        o = np.argsort(tag, kind="stable")
        gr = np.flatnonzero(np.diff(tag[o])) + 1
        bloecke = np.split(np.arange(len(tag)), gr)
        best = max(zellen, key=lambda z: z[3])
        bands = []
        for _ in range(ZIEHUNGEN):
            zieh = []
            for (_f, _s, _n, _e, Ez, mz, _t, _g) in zellen:
                ez, mzs = Ez[o], mz[o]
                s = k = 0.0
                for b in bloecke:
                    z = int(mzs[b].sum())
                    if not z:
                        continue
                    w = rng.choice(b, size=z, replace=False)
                    v = ez[w]
                    v = v[np.isfinite(v)]
                    s += float(v.sum())
                    k += len(v)
                zieh.append(s / max(k, 1.0))
            bands.append(max(zieh))
        band = float(np.percentile(bands, 90))
        print()
        print("  ➤ Beste Zelle: H%d / Stop %.2f mit %+.4f %% "
              "· TAGESTREUES Bestes-von-%d-Band %+.4f  %s"
              % (best[0], best[1], best[3], len(zellen), band,
                 "✔" if best[3] > band else "⛔ faellt"))
        print("     Zeitstabil %d von %d Jahren" % (best[6], best[7]))
        print("  ⚠️ Vergleich 2.628 (auf dem TAGESRANG): H24 / Stop 1,00")
        print("     mit +1,5196 %. Eine andere Auswahl, also eine andere")
        print("     Zahl - KEIN Widerspruch, sondern die andere Ebene.")
    print()
    print("=" * 104)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
