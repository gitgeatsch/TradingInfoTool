# -*- coding: utf-8 -*-
"""K-1a — Tragen die Beitraege auf der A1-MENGE? (09.09.2026)

## Die Frage aus dem Kettenplan

> **Tragen die Beitraege auf der A1-Menge (top-k nach Jahresentwicklung)?
> Das ist die Menge, fuer die sie gedacht sind.**

⚠️ Vorhersage aus dem Plan: *„K-1a traegt (dafuer sind sie gebaut)."*

## ⚠️⚠️ Was N-96/N-97 daran geaendert haben (Befund 2.262)

Der Betriebsablauf ist ZWEISTUFIG, am Betriebscode nachgelesen:

    agent/marktrang.raenge    Rang ueber die MESSBASIS (536), fuer unsere
                              Symbole nur ABGELESEN
    agent/auswahl.waehle      k = 2 aus der Watchlist nach 250-Tage-
                              Entwicklung (`k_fuer`: K_GROSS=2 ab 10 Werten)

**Die A1-Menge sind ZWEI Werte pro Tag.** Genau so wird hier gemessen -
absolutes k, taeglich neu gewaehlt. Dafuer nimmt `sammle` seit heute eine
Menge JE TAG (`nur` als Mapping; Vorabtest auf Kunstdaten bestanden,
einschliesslich des Grenzfalls „Woerterbuch als Menge missbraucht").

⚠️ `momentum250` bildet dieselbe Groesse wie `auswahl.rangliste`:
`jetzt / frueher - 1` ueber 250 Zeilen. Nachgelesen, nicht angenommen.

## ⚠️⚠️⚠️ DIE NORM IST HIER NICHT ANWENDBAR - und das ist ein Befund

`messnorm_auswahl.pruefe_auswahl` misst unter der **Tagesklammer**:
`median(frei) - median(alle)` INNERHALB jedes Tages. Bei k=2 gibt es je
Tag nicht genug Zeilen fuer zwei Gruppen - gemessen: **0 verwertbare
Tage**.

> Das ist kein Datenmangel, sondern Bauart: **auf der Menge, auf der die
> Kette entscheidet, laesst sich das Beitragskriterium der Norm gar
> nicht anwenden.** Es steht neben A1 (Hebel: Band auf binaeren Daten)
> und A2 (Akkumulation: Blockregel bei H90) als dritte strukturelle
> Sperre.

Deshalb wird hier der GEPOOLTE Kennwert gemessen - so wie
`messe_beitrag_auf_auswahl` es seit dem 04.09. tut (Befund 2.109: „Die
Tagesklammer traegt hier nicht"):

    Kennzahl = median(frei) - median(ALLE)     ueber alle Tage zusammen

⚠️ ABER NICHT mit dessen Werkzeug: `messe_beitrag_auf_auswahl.urteil`
zieht die Tage EINZELN (`rng.integers(0, n, n)`) und laesst damit die
Serienabhaengigkeit unbehandelt - es ist Altbestand von vor der
Messnorm. Hier wird der gepoolte Kennwert nach dem **Messstandard**
gemessen:

    Band            Blockbootstrap ueber Kalendertage, Block = 3 x H
    Nullpunkt       40 Ziehungen mit gemischtem RANG, 90. Perzentil
    Bezug           `messnorm._bezug` - derselbe Nullbezug wie ueberall
    Trennschaerfe   gepflanzte Leiter 0,02 / 0,05 / 0,10 / 0,20 / 0,40
    Kontrolle       `zufall` bei jedem k

## Der Aufbau

    Rang        ueber den vollen Tagesquerschnitt (keine Momentum-Vorwahl)
    Verengung   NACH dem Rang, auf die A1-Auswahl des Tages
    k           2 (live) · 3 · 5 · 8 · 13 · 21 · alle (= K-1w-Obergrenze)

⚠️ ABWEICHUNG VON DER REGISTRIERUNGSBASIS, und sie ist Absicht: die
Kandidaten sind auf ihrer eigenen `menge` registriert
(`bestand.messbasis`); hier steht ueberall der volle Querschnitt PLUS
die A1-Verengung, denn **die A1-Menge IST die Frage**. Das Zeitfenster
der Registrierung wird uebernommen.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    k=2 traegt          -> die Beitraege wirken dort, wo entschieden wird
    k=2 traegt nicht,
    grosse k tragen     -> die Wirkung verduennt sich zur Auswahl hin -
                           ein Befund ueber die KETTE, nicht die Beitraege
    nichts traegt       -> zuerst Kontrolle und Ankerzahl ansehen

⚠️ Die Kurve ueber k ist die Aussage, nicht die einzelne Zelle.

    python k1a_beitrag_auf_der_a1_menge.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bestand as BE                                          # noqa: E402
import messe_beitrag_auf_auswahl as A                         # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messe_regel_wirksamkeit as W                           # noqa: E402
import messnorm as N                                          # noqa: E402
from k1w_beitrag_auf_der_watchlist import watchlist           # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402

KANDIDATEN = ("funding", "turnover", "oi_aenderung", "schnitt", "zufall")
K_WERTE = (2, 3, 5, 8, 13, 21, 0)      # 0 = die ganze Watchlist
SAAT = 20260909
ZIEH_BAND = 400
MIN_FREI, MIN_ALLE = 5, 10


def a1_menge_je_tag(mom: dict, wl: set, k: int) -> dict:
    """Die A1-Auswahl je Tag: top-k der Watchlist nach 250-Tage-Entwicklung.

    ⚠️ `k = 0` heisst „keine Auswahl" - dann ist die ganze Watchlist die
    Menge. Das ist die Obergrenze und zugleich die K-1w-Zeile.

    ⚠️⚠️ `k_fuer` deckelt in der Produktion mit `min(k, n - 1)`: k ist NIE
    gleich der Zahl der Werte, weil „Rang 2 von 2" keine Begruendung ist.
    Dieselbe Deckelung hier - sonst waere die schmalste Zelle in Wahrheit
    gar keine Auswahl.
    """
    aus = {}
    for tag, werte in mom.items():
        kand = {s: w for s, w in werte.items() if s.upper() in wl}
        if len(kand) < 2:
            continue
        if k <= 0:
            aus[tag] = set(kand)
            continue
        kk = min(k, len(kand) - 1)
        aus[tag] = {s for s, _ in
                    sorted(kand.items(), key=lambda p: -p[1])[:kk]}
    return aus


def tagesdaten(je_tag: dict, mengen: dict) -> tuple[list, dict]:
    """Je Tag einmal aufbereiten: Kennzahl, Ergebnis, A1-Masken je k.

    ⚠️ Der Grund fuer das Zwischenlager ist nicht Bequemlichkeit: die
    Nullkontrolle mischt 40-mal den RANG, und der Rang haengt NICHT von
    `k` ab. Wer je (k, Ziehung) neu einliest, rechnet dasselbe siebenmal.
    """
    tage, daten = [], {}
    for tag in sorted(je_tag):
        zeilen = je_tag[tag]
        if len(zeilen) < 12:
            continue
        syms = [z["sym"] for z in zeilen]
        masken = {}
        for k, m in mengen.items():
            erlaubt = m.get(tag)
            if not erlaubt:
                continue
            msk = np.array([s in erlaubt for s in syms])
            if msk.any():
                masken[k] = msk
        if not masken:
            continue
        tage.append(tag)
        daten[tag] = {
            "w": np.array([z["kennzahl"] for z in zeilen], float),
            "y": np.array([z["in_r"] for z in zeilen], float),
            "masken": masken}
    return tage, daten


def _oben_je_tag(tage, daten, mische=None) -> dict:
    """`oben` = oberstes Fuenftel nach dem Rang des vollen Querschnitts."""
    aus = {}
    for t in tage:
        r = W.rang(daten[t]["w"])
        if mische is not None:
            r = mische.permutation(r)
        aus[t] = r >= W.GRENZE
    return aus


def kennzahl(tage, daten, oben, k, pflanze=0.0) -> float:
    """GEPOOLT: median(frei) - median(ALLE) - die registrierte Definition.

    ⚠️ NICHT gegen die GESPERRTEN. `messe_regel_wirksamkeit.wirkung()`
    rechnet `median(frei) - median(alle)`; frei gegen gesperrt lag um
    Faktor 3,8 daneben (2.105).
    """
    frei, alle = [], []
    for t in tage:
        d = daten[t]
        msk = d["masken"].get(k)
        if msk is None:
            continue
        o = oben[t]
        y = d["y"]
        if pflanze:
            # ⚠️ Vorzeichen wie in `sammle`: die GESPERRTEN schlechter zu
            # machen laesst die Regel BESSER aussehen, die Kennzahl STEIGT.
            y = y.copy()
            y[o] = y[o] + pflanze
        sel = msk
        alle.append(y[sel])
        frei.append(y[sel & ~o])
    if not alle:
        return float("nan")
    f = np.concatenate(frei) if frei else np.array([])
    a = np.concatenate(alle)
    if f.size < MIN_FREI or a.size < MIN_ALLE:
        return float("nan")
    return float(np.median(f) - np.median(a))


def band(tage, daten, oben, k, block, rng, pflanze=0.0):
    """Blockbootstrap ueber Kalendertage - Block = 3 x Horizont.

    ⚠️ `messe_beitrag_auf_auswahl.urteil` zieht die Tage EINZELN und
    laesst die Serienabhaengigkeit stehen. Genau davor warnt 2.107 fuer
    Anker; fuer Tage gilt dasselbe eine Ebene hoeher.
    """
    bl = [tage[i:i + block] for i in range(0, len(tage), block)]
    bl = [b for b in bl if b]
    if len(bl) < 20:
        return None
    echt = kennzahl(tage, daten, oben, k, pflanze)
    if not np.isfinite(echt):
        return None
    n = len(bl)
    boot = []
    for _ in range(ZIEH_BAND):
        zieh = []
        for i in rng.integers(0, n, n):
            zieh.extend(bl[i])
        v = kennzahl(zieh, daten, oben, k, pflanze)
        if np.isfinite(v):
            boot.append(v)
    if len(boot) < 50:
        return None
    u, o = np.quantile(boot, [0.025, 0.975])
    anker = sum(int(daten[t]["masken"][k].sum())
                for t in tage if k in daten[t]["masken"])
    return {"mittel": echt, "unten": float(u), "oben": float(o),
            "bloecke": n, "anker": anker}


def main() -> int:
    t0 = time.time()
    wl = watchlist()
    reihen = B.lade()
    mom = A.momentum250(reihen)
    zus = zusatzquellen()
    block = N._block(HORIZONT)

    print("=" * 116)
    print("K-1a — tragen die Beitraege auf der A1-MENGE (top-k nach "
          "Jahresentwicklung)?")
    print("=" * 116)
    print("  %s" % N.standardzeile())
    print("  Watchlist %d Symbole, davon %d in der Messbasis · Block %d "
          "Tage" % (len(wl), len(wl & set(reihen)), block))
    print("  ⚠️⚠️ DIE NORM IST HIER NICHT ANWENDBAR: `pruefe_auswahl` "
          "misst unter der Tagesklammer,")
    print("     und bei k=2 bleiben 0 verwertbare Tage. Gemessen wird der "
          "GEPOOLTE Kennwert -")
    print("     aber nach Messstandard (Blockbootstrap, %d Nullziehungen, "
          "%.0f. Perzentil)."
          % (N.NULL_ZIEHUNGEN, N.NULL_PERZENTIL))

    mengen = {k: a1_menge_je_tag(mom, wl, k) for k in K_WERTE}
    print()
    print("  DIE MENGE, BEVOR GEMESSEN WIRD")
    print("     %-6s %8s %13s" % ("k", "Tage", "Symbole/Tag"))
    for k in K_WERTE:
        m = mengen[k]
        print("     %-6s %8d %13.1f"
              % (k or "alle", len(m),
                 float(np.mean([len(v) for v in m.values()])) if m else 0.0))

    erg = {}
    for kand in KANDIDATEN:
        try:
            _m, fenster = BE.messbasis(kand)
        except KeyError:
            fenster = ""
        je0 = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        if fenster and fenster != "voll":
            je0 = {t: z for t, z in je0.items() if str(t) >= fenster}
        tage, daten = tagesdaten(je0, mengen)
        if not tage:
            print("\n  %-14s -> keine verwertbaren Tage" % kand)
            continue

        # ⚠️ Der Rang haengt nicht von k ab - einmal je Ziehung rechnen.
        oben_echt = _oben_je_tag(tage, daten)
        oben_null = [_oben_je_tag(tage, daten,
                                  np.random.default_rng(SAAT + z))
                     for z in range(N.NULL_ZIEHUNGEN)]

        print()
        print("  %s   (%d Tage)" % (kand.upper(), len(tage)))
        print("     %-6s %9s %22s %10s %9s %8s  %s"
              % ("k", "Wirkung", "Band", "Nullpunkt", "Anker", "Trennsch",
                 "Urteil"))
        for k in K_WERTE:
            rng = np.random.default_rng(SAAT)
            h = band(tage, daten, oben_echt, k, block, rng)
            if h is None:
                print("     %-6s nicht messbar (zu wenige Bloecke oder "
                      "Anker)" % (k or "alle"))
                continue
            nw = [kennzahl(tage, daten, o, k) for o in oben_null]
            nw = [x for x in nw if np.isfinite(x)]
            if len(nw) < N.NULL_ZIEHUNGEN // 2:
                print("     %-6s Nullpunkt nicht bestimmbar" % (k or "alle"))
                continue
            null = {"mittel": float(np.percentile(nw, N.NULL_PERZENTIL)),
                    "oben": float(np.max(nw))}
            bez = N._bezug(null)
            traegt = h["unten"] > bez

            # ---- Trennschaerfe: die gepflanzte Leiter -------------------
            ts = None
            if not traegt:
                for s in N.STAERKEN:
                    r2 = np.random.default_rng(SAAT + 991)
                    hp = band(tage, daten, oben_echt, k, block, r2,
                              pflanze=-float(s))
                    if hp and hp["unten"] > bez:
                        ts = s
                        break
            urteil = ("TRAEGT" if traegt else
                      ("KEIN BEFUND (Leiter zu kurz)" if ts is None else
                       "traegt nicht bis %.2f" % ts))
            erg[(kand, k)] = (h, bez, traegt, ts)
            print("     %-6s %+9.4f [%+.4f .. %+.4f] %+10.4f %9d %8s  %s"
                  % (k or "alle", h["mittel"], h["unten"], h["oben"], bez,
                     h["anker"], ("-" if traegt else
                                  ("%.2f" % ts if ts else "keine")),
                     urteil), flush=True)

    # ---- Die Kontrolle zuerst -------------------------------------------
    print()
    print("=" * 116)
    print("ZUERST DIE KONTROLLE")
    print("=" * 116)
    laut = [k for (kd, k), v in erg.items() if kd == "zufall" and v[2]]
    if laut:
        print("  ⚠️⚠️⚠️ `zufall` TRAEGT bei k = %s - dort gilt der Lauf "
              "NICHT."
              % ", ".join(str(x or "alle") for x in laut))
    else:
        print("  ✔ `zufall` traegt bei KEINEM k - die Anlage erzeugt hier "
              "keine Scheinbefunde.")

    kopf = " ".join("%9s" % (k or "alle") for k in K_WERTE)
    print()
    print("  DIE KURVE UEBER k - sie ist die Aussage, nicht die einzelne "
          "Zelle")
    print("     %-14s %s" % ("Kandidat", kopf))
    for kand in KANDIDATEN:
        z = []
        for k in K_WERTE:
            v = erg.get((kand, k))
            z.append("%9s" % ("-" if v is None else "%+.4f" % v[0]["mittel"]))
        print("     %-14s %s" % (kand, " ".join(z)))
    print()
    print("     %-14s %s" % ("(traegt?)", kopf))
    for kand in KANDIDATEN:
        z = []
        for k in K_WERTE:
            v = erg.get((kand, k))
            z.append("%9s" % ("-" if v is None
                              else ("JA" if v[2] else "nein")))
        print("     %-14s %s" % (kand, " ".join(z)))

    print()
    print("  ⚠️ k = 2 ist die LIVE-Menge. Traegt es dort nicht, aber bei "
          "grossen k, verduennt")
    print("     sich die Wirkung zur Auswahl hin - ein Befund ueber die "
          "KETTE, nicht die Beitraege.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
