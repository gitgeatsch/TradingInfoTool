# -*- coding: utf-8 -*-
"""DER VIERFACHTEST — nach dem Messstandard neu gebaut (10.09.2026)

## Der Maßstab, seit dem 05.09. festgelegt

Ein neuer Beitrag braucht **alle vier**, nicht eines davon:

    1  ABDECKUNG      fuer wie viele Symbole liegt die Groesse vor?  (F-218)
    2  STABILITAET    haelt die Ordnung ueber die Bloecke?           (F-217)
    3  UNABHAENGIG    traegt sie noch, wenn `funding` festgehalten wird?
    4  REGEL 3        trennt sie auch LAENGS, im eigenen Symbol?     (N-43c)

## ⚠️⚠️⚠️ Warum er NEU gebaut wird und nicht nur neu gelaufen

Die Werkzeuge, aus denen die 05.09.-Zahlen stammen -
`pruefe_kandidaten_abdeckung_stabilitaet.py` und
`pruefe_kandidaten_untereinander.py` - tragen **beide** seit dem 06.09.
einen Sperrkopf:

> ⛔⛔ UEBERHOLT AM 06.09.2026 — NICHT MEHR BENUTZEN. Dieses Werkzeug
> misst auf der ZIELGROESSE „Ziel vor Stop" und/oder auf der FREIEN statt
> der SELEKTIERTEN Menge. Beides ist als falsch nachgewiesen.

**Damit stehen `vola`s vier Haken auf ueberholtem Grund** - Abdeckung
516/516, Stabilitaet +0,647, Regel 3 laengs 5,37. Sie werden hier NICHT
uebernommen, sondern neu erhoben. Dasselbe Muster wie beim
Kalibrierungsfaktor (2.279).

## ⚠️ Und Kriterium 4 war bis heute gar nicht messbar

N-46 hat es blockiert. **N-46b hat den Laengs-Nullpunkt entschieden**
(Tagesmischung, Fehlalarm 1,0 %% / 4,0 %% gegen Soll 2,5 %%) - erst
seither ist Kriterium 4 ueberhaupt pruefbar.

⚠️⚠️ **Mit einem benannten Vorbehalt (A9, Befund 2.283):** bei hoher
Beharrlichkeit loest die Laengs-Achse erst ab **0,08 R** auf - 0,03 R
findet sie in 20 %%, 0,05 R in 50 %% der Faelle. **Die echten Kandidaten
liegen bei 0,02 bis 0,05 R.** Ein „traegt nicht laengs" ist dort
UNTERMACHT, kein Nullbefund, und wird hier auch so ausgewiesen.

## Die Kandidaten

    vola           aus Kursdaten, volle Abdeckung erwartet
    schnitt50      aus Kursdaten, die einzige monotone Form (2.222)
    amihud         aus Kursdaten, unabhaengig von allem
    volumenanteil  ⚠️ NICHT registriert, Befund unter Vorbehalt (A6:
                   Negativkontrolle mit EINER Ziehung) - aber der einzige
                   Kandidat mit VOLLER Abdeckung aus vorhandenen Daten
    schnitt        laeuft als MASSSTAB mit - er traegt bei der
                   Akkumulation (2.286-schnitt)
    zufall         Kontrolle, darf nirgends bestehen

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    Abdeckung      vola, amihud, schnitt50, volumenanteil ~ voll;
                   sie kommen alle aus der eigenen Kursreihe
    Stabilitaet    offen - genau daran ist `turnover` gefallen
    Unabhaengig    offen
    Regel 3        ⚠️ vermutlich UNTERMACHT bei allen - siehe A9

⚠️ **Wenn Kriterium 4 durchgaengig KEIN BEFUND liefert, ist das kein
Ergebnis ueber die Kandidaten, sondern ueber die Anlage** - und dann ist
der Vierfachtest in seiner heutigen Form nicht erfuellbar. Das waere ein
Befund, kein Rueckschlag.

    python n102_vierfachtest.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bestand as BE                                          # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                 # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250             # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n68_zeitstabilitaet import (entzerrte_reihe,          # noqa: E402
                                 stabilitaetsurteil)
from n75_quer_gegen_laengs import laengs_rang, wirkung        # noqa: E402
from n91_rangkorrelation_form import band                     # noqa: E402

# ⚠️ `volumenanteil` FEHLT hier - `messe_kandidaten_als_regel.baue`
# kennt ihn nicht, und seine relative Form braucht eine
# QUERSCHNITTSrechnung (Anteil am Tagesgesamtumsatz), die `baue`
# je Symbol gar nicht sehen kann. Das ist ein eigener Bauschritt
# und wird NICHT nebenbei erledigt - er ist der Kandidat mit der
# besten Abdeckung und hat eine saubere Messung verdient.
KANDIDATEN = ("vola", "schnitt50", "amihud",
              "schnitt", "zufall")
SAAT = 20260910
NULL_ZIEH = 20
# ⚠️ Aus A9 (2.283): unterhalb dieser Groesse ist ein Laengs-Nullbefund
# UNTERMACHT. Gemessen an Nullwelten mit der Beharrlichkeit von `schnitt`.
LAENGS_AUFLOESUNG = 0.08


def abdeckung(je_tag: dict) -> tuple:
    """Wie viele Symbole traegt die Groesse - und wie viele Anker je Tag?"""
    syms, anker = set(), []
    for zeilen in je_tag.values():
        anker.append(len(zeilen))
        for x in zeilen:
            syms.add(x["sym"])
    return len(syms), (float(np.mean(anker)) if anker else 0.0)


def stabilitaet(je_tag, mom, menge, block):
    """⚠️⚠️⚠️ KORRIGIERT 10.09.2026 - die alte Fassung war fehlerhaft.

    Sie entschied allein ueber `d["unten"] <= 0.0 <= d["oben"]`, also
    ,das Band schliesst die Null ein'. Das ist ein NICHT-Verwerfen, als
    Haken ausgegeben - **je breiter das Band, desto sicherer das ✔**.
    `schnitt`, dessen Baender sechsmal breiter sind als `funding`s,
    bestand damit, weil er unruhig ist. Richtig gemessen faellt er.

    Das Urteil steht jetzt in `n68_zeitstabilitaet.stabilitaetsurteil`
    (vier Urteile, mit Trennschaerfe auf die zentrierte Reihe).

    ⚠️ ZWEITER FEHLER, gleiche Stelle: der Aufrufer gibt EINE `menge`,
    waehrend Kriterium 1 zehn Zeilen darueber ueber ALLE zulaessigen
    laeuft. N-73 war hier nie angewandt - und `schnitt`s
    Haelftenunterschied dreht mit der Menge (−0,0805 bei 10 %, +0,1973
    bei 20 %). Wer eine Menge waehlt, waehlt das Urteil.
    Vollstaendig ueber alle Mengen: `n110_kriterium2_mit_trennschaerfe.py`.
    """
    e = entzerrte_reihe(je_tag, mom, MENGEN[menge])
    return stabilitaetsurteil(e, block)


def laengs(je_tag, mom, block):
    """Kriterium 4 - trennt die Groesse auch INNERHALB des Symbols?

    ⚠️ Nullmodell ist die TAGESMISCHUNG. Sie ist am 10.09. gegen bekannte
    Wahrheit entschieden worden (2.282): Fehlalarm 1,0 % bzw. 4,0 % gegen
    ein Soll von 2,5 %, und auf sechs von acht Sprossen fuendiger als der
    zirkulaere Verschub.
    """
    lr = laengs_rang(je_tag)
    if not lr:
        return None
    echt, _ = wirkung(je_tag, mom, 1.0, "laengs", lr)
    b = band(echt, block)
    if b is None:
        return None
    nw = []
    for z in range(NULL_ZIEH):
        w, _ = wirkung(je_tag, mom, 1.0, "laengs", lr,
                       mische=np.random.default_rng(SAAT + z))
        nb = band(w, block, zieh=300, saat=SAAT + z)
        if nb:
            nw.append(nb[0])
    if len(nw) < NULL_ZIEH // 2:
        return None
    bez = max(0.0, float(np.percentile(nw, N.NULL_PERZENTIL)))
    traegt = b[1] > bez
    # ⚠️ A9: unterhalb der Aufloesung ist ein Nullbefund UNTERMACHT.
    untermacht = (not traegt) and abs(b[0]) < LAENGS_AUFLOESUNG
    return {"wert": b[0], "unten": b[1], "oben": b[2], "bezug": bez,
            "traegt": traegt, "untermacht": untermacht}


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = _block(HORIZONT)
    lage = N.Lage(instrument="spot", strategie="einstieg")

    print("=" * 116)
    print("DER VIERFACHTEST — nach dem Messstandard neu gebaut")
    print("=" * 116)
    print("  %s" % messmenge.zeile())
    print("  %s" % N.standardzeile())
    print("  ⚠️ Die 05.09.-Zahlen stammen aus zwei am 06.09. GESPERRTEN "
          "Werkzeugen - sie werden")
    print("     NICHT uebernommen, sondern neu erhoben.")
    print("  ⚠️⚠️ Kriterium 4 (Regel 3 laengs) ist erst seit N-46b "
          "(10.09.) ueberhaupt pruefbar -")
    print("     mit dem Vorbehalt A9: unterhalb %.2f R ist ein "
          "Nullbefund UNTERMACHT." % LAENGS_AUFLOESUNG)

    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                              # noqa: BLE001
            print()
            print("  %-14s -> nicht baubar: %s" % (kand, str(exc)[:60]))
            continue
        try:
            menge, fenster = BE.messbasis(kand)
        except KeyError:
            menge, fenster = "frei", ""
        menge = menge or "frei"
        if fenster and fenster != "voll":
            je = {t: z for t, z in je.items() if str(t) >= fenster}

        n_sym, je_tag_anker = abdeckung(je)
        print()
        print("  %s   (Basis: Menge %s%s)"
              % (kand.upper(), menge,
                 ", ab %s" % fenster if fenster and fenster != "voll" else ""))

        # ---- 1 ABDECKUNG -------------------------------------------------
        anteil = 100.0 * n_sym / len(messmenge.V1)
        print("     1 ABDECKUNG    %d von %d Symbolen (%.1f %%), %.1f "
              "Anker je Tag" % (n_sym, len(messmenge.V1), anteil,
                                je_tag_anker), flush=True)

        # ---- Die WIRKUNG ueber ALLE ZULAESSIGEN MENGEN --------------------
        #
        # ⚠️⚠️ NICHT auf einer Menge, und NICHT auf `frei`. N-73 haelt
        # fest: die schmalste zulaessige Menge ist zugleich die
        # rauschendste, und `schnitt` bekam bei 10 % und 20 % fast
        # denselben Punktschaetzer, aber verschiedene Urteile.
        #
        # > „Das URTEIL sollte ueber ALLE zulaessigen Mengen halten. Ein
        # > Kandidat, der nur auf einer von ihnen traegt, ist nicht
        # > robust - und das ist ein Befund ueber ihn, kein Grund, sich
        # > die passende Menge auszusuchen."
        #
        # ⚠️ `frei` beantwortet die MARKT-Frage (P6) und zaehlt als
        # Vergleichsbasis, nicht als Beitragsurteil.
        try:
            zul = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
        except Exception as exc:                              # noqa: BLE001
            zul = []
            print("       Wirkung     Mengenwahl gescheitert: %s"
                  % str(exc)[:46])
        traegt_quer = None
        if zul:
            traeger, gepruef = [], []
            for m in zul:
                try:
                    b = MA.pruefe_auswahl(
                        kand, je, mom, lage=lage, menge=m,
                        rng=np.random.default_rng(SAAT), horizont=HORIZONT,
                        hypothese="Vierfachtest", verwendung=(
                            "Markt" if m == "frei" else "Beitrag"))
                except Exception as exc:                      # noqa: BLE001
                    print("       Wirkung  %-5s nicht messbar: %s"
                          % (m, str(exc)[:44]))
                    continue
                print("       Wirkung  %-5s %+.4f [%+.4f .. %+.4f]  %s"
                      % (m, b.wirkung, b.unten, b.oben,
                         b.urteil.split(" (")[0][:40]), flush=True)
                if m == "frei":
                    continue
                gepruef.append(m)
                if b.traegt:
                    traeger.append(m)
            if gepruef:
                traegt_quer = (len(traeger) == len(gepruef))
                print("       -> traegt auf %d von %d Beitragsmengen%s"
                      % (len(traeger), len(gepruef),
                         "  ✔ robust" if traegt_quer else
                         "  ⚠️ NICHT robust (N-73)"))

        # ---- 2 STABILITAET -----------------------------------------------
        st = stabilitaet(je, mom, menge, block)
        if st is None:
            print("     2 STABILITAET  nicht messbar (zu wenige Bloecke)")
        else:
            # ⚠️ Das volle Urteil, nicht nur ja/nein - ,nicht trennbar'
            # ist KEINE Stabilitaet, und genau das hat die alte Fassung
            # als ✔ ausgegeben.
            print("     2 STABILITAET  Diff %+.4f [%+.4f .. %+.4f] "
                  "Trennsch %s  %s"
                  % (st["diff"], st["unten"], st["oben"],
                     ("%.2f" % st["ts"]) if st["ts"] else "KEINE",
                     st["urteil"]), flush=True)
            print("       ⚠️ NUR DIESE EINE MENGE (%s). N-73 gilt hier "
                  "nicht - `schnitt`s" % menge)
            print("          Haelftenunterschied dreht mit ihr (−0,0805 "
                  "bei 10 %, +0,1973 bei 20 %).")
            print("          Vollstaendig: "
                  "n110_kriterium2_mit_trennschaerfe.py")

        # ---- 4 REGEL 3 LAENGS --------------------------------------------
        lg = laengs(je, mom, block)
        if lg is None:
            print("     4 REGEL 3      nicht messbar")
        else:
            wort = ("✔ trennt laengs" if lg["traegt"] else
                    ("⚠️⚠️ UNTERMACHT (unter %.2f R)" % LAENGS_AUFLOESUNG
                     if lg["untermacht"] else "trennt nicht"))
            print("     4 REGEL 3      %+.4f [%+.4f .. %+.4f] gegen %+.4f "
                  "  %s" % (lg["wert"], lg["unten"], lg["oben"],
                            lg["bezug"], wort), flush=True)
        erg[kand] = (n_sym, anteil, traegt_quer, st, lg)

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 116)
    print("DIE ABNAHME — alle vier, nicht eines")
    print("=" * 116)
    zf = erg.get("zufall")
    if zf and (zf[2] or (zf[4] and zf[4]["traegt"])):
        print("  ⚠️⚠️⚠️ DIE KONTROLLE `zufall` besteht ein Kriterium - "
              "der Lauf gilt NICHT.")
    elif zf:
        print("  ✔ `zufall` besteht kein Kriterium.")
    print()
    print("     %-14s %10s %10s %10s %14s" % ("Kandidat", "1 Abdeck.",
                                              "Wirkung", "2 Stabil.",
                                              "4 Regel 3"))
    for kand in KANDIDATEN:
        v = erg.get(kand)
        if not v:
            continue
        n_sym, anteil, tq, st, lg = v
        print("     %-14s %9.1f %% %10s %10s %14s"
              % (kand, anteil,
                 "-" if tq is None else ("JA" if tq else "nein"),
                 "-" if st is None else ("ja" if st["stabil"] else "NEIN"),
                 "-" if lg is None else
                 ("JA" if lg["traegt"] else
                  ("untermacht" if lg["untermacht"] else "nein"))))
    print()
    print("  ⚠️ Kriterium 3 (unabhaengig von `funding`) fehlt hier noch - "
          "es braucht eine")
    print("     bedingte Messung je Funding-Fuenftel und ist ein eigener "
          "Schritt.")
    print("  ⚠️⚠️ Liefert Kriterium 4 durchgaengig UNTERMACHT, ist das ein "
          "Befund ueber die")
    print("     ANLAGE, nicht ueber die Kandidaten - dann ist der "
          "Vierfachtest so nicht erfuellbar.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
