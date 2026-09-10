# -*- coding: utf-8 -*-
"""V7 — KRITERIUM 3: traegt die Groesse noch, wenn `funding` FESTGEHALTEN wird?

## Das letzte fehlende der vier Kriterien

    1  ABDECKUNG    ✔ gemessen (Vierfachtest, 2.293)
    2  STABILITAET  ✔ gemessen (Vierfachtest)
    3  UNABHAENGIG  ⚠️ DIESER LAUF - bei KEINEM Kandidaten gemessen
    4  REGEL 3      ✔ gemessen (V1, 2.297)

## Was „festgehalten" heisst - und wie es hier gebaut wird

Die Frage ist nicht *„korrelieren die beiden?"*, sondern *„bleibt etwas
uebrig, wenn man `funding` konstant haelt?"*. Also: **innerhalb** einer
Funding-Schicht messen.

⚠️ Dafuer braucht es KEIN neues Werkzeug. Ein Funding-Fuenftel ist eine
SYMBOLMENGE JE TAG - und genau die nimmt der `nur`-Parameter von
`sammle`, der am 10.09. um eine Tagesvariante erweitert und auf
Kunstdaten geprueft wurde (0 %% gemeinsame Mitglieder bei korrelierter
Auswahl, Grenzfall „Woerterbuch als Menge" abgedeckt).

    nur = {tag: {Symbole im Funding-Fuenftel k}}

Damit laeuft die Messung durch die **gewohnte Norm** - Tagesklammer,
Blockbootstrap, 40 Nullziehungen, Trennschaerfeleiter. Kein Sonderpfad.

## ⚠️⚠️ DIE GEGENKONTROLLE IST HIER DER KERN, NICHT DIE ZUGABE

`pruefe_n1_schichtung_gegen_partner` hat den Punkt schon benannt:

> Zwei Deutungen, und sie sind zu trennen:
>   **A** `funding` erklaert die Groesse mit  -> Redundanz
>   **B** die Schichtung an sich kostet Schaerfe -> ein Messproblem

**Die Kontrolle: dieselbe Schichtung, aber mit GEMISCHTEM Funding.** Die
Faecher sind dann genauso klein, tragen aber keine Information.

    faellt ECHT, GEMISCHT nicht   ->  `funding` erklaert es  (A)
    fallen BEIDE gleich           ->  die Schichtung kostet  (B)

⚠️ **Ohne diese Kontrolle waere jedes „traegt nicht mehr" wertlos** - es
koennte allein daher kommen, dass ein Fuenftel ein Fuenftel der Anker
hat. Nach dem heutigen Tag ist das keine theoretische Sorge.

## Wer gemessen wird

    schnitt, vola, schnitt50     die Kandidaten
    turnover, oi_aenderung       ⚠️ der BESTAND - kein zweierlei Mass (N-2)
    zufall                       Kontrolle, darf nirgends tragen

⚠️ `funding` selbst fehlt: eine Groesse gegen sich selbst festzuhalten
ist keine Frage. `amihud` fehlt auch - er traegt auf KEINER Menge
(0 von 3, 2.293) und ist zu 70,7 %% eine Asset-Eigenschaft.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    schnitt        traegt weiter - seine Momentum-Korrelation ist gering,
                   und `funding` ist eine ganz andere Quelle
    turnover       offen; 92 %% additiv zu Funding laut Registrierung,
                   also sollte er ueberleben
    zufall         traegt nirgends
    GEMISCHT       ⚠️ die entscheidende Zeile. Liegt sie beim selben Wert
                   wie ECHT, sagt der Lauf ueber Redundanz NICHTS

    python n104_v7_kriterium3.py
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
import messe_regel_wirksamkeit as W                           # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                 # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250             # noqa: E402

# ⚠️⚠️ `schnitt50` WAR HERAUSGENOMMEN - AUS LAUFZEITGRUENDEN, UND DAS
# WAR FALSCH (Nutzereinwand 10.09.: „Warum hast du schnitt50 einfach
# herausgenommen, macht es keinen Sinn diesen zu messen?").
#
# Sachlich steht er gut da: 100 % Abdeckung, **6,9 % Asset-Anteil** - der
# zweitbeste Wert ueberhaupt, nur `oi_aenderung` liegt tiefer - stabil,
# und laut 2.222 die EINZIGE monotone Form. Genau das zaehlt beim
# Schritt FORM.
#
# ⚠️ Eine Kuerzung aus Laufzeitgruenden ist eine stille Verengung. Sie im
# Skriptkopf zu vermerken ist nicht dasselbe wie sie zu begruenden.
KANDIDATEN = ("schnitt", "schnitt50", "vola", "turnover",
              "oi_aenderung", "zufall")
SCHICHTEN = 5
SAAT = 20260910


def funding_schichten(je_funding: dict, mische: bool = False,
                      saat: int = SAAT) -> list:
    """Je Fuenftel eine Menge JE TAG: `[{tag: {sym}}, ...]`.

    ⚠️ Der Rang entsteht ueber den vollen Tagesquerschnitt, wie
    `marktrang` in der Produktion.

    ⚠️⚠️ `mische=True` ist die GEGENKONTROLLE: die Funding-Werte werden je
    Tag ueber die Symbole vertauscht. Die Faecher bleiben gleich gross,
    tragen aber keine Information mehr. Ohne diesen Arm ist ein „traegt
    nicht mehr" nicht von den Kosten der Schichtung zu unterscheiden.
    """
    rng = np.random.default_rng(saat)
    aus = [dict() for _ in range(SCHICHTEN)]
    for tag, zeilen in je_funding.items():
        if len(zeilen) < SCHICHTEN * 4:
            continue
        syms = [x["sym"] for x in zeilen]
        werte = np.array([x["kennzahl"] for x in zeilen], float)
        if mische:
            werte = rng.permutation(werte)
        r = W.rang(werte)
        for i, s in enumerate(syms):
            k = min(int(r[i] * SCHICHTEN), SCHICHTEN - 1)
            aus[k].setdefault(tag, set()).add(s)
    return aus


def miss(kand, je, mom, lage, menge, nur=None):
    """Ein Befund unter der gewohnten Norm - mit oder ohne Schichtung."""
    try:
        return MA.pruefe_auswahl(
            kand, je, mom, lage=lage, menge=menge,
            rng=np.random.default_rng(SAAT), horizont=HORIZONT,
            hypothese="V7 Kriterium 3", verwendung="Beitrag", nur=nur)
    except Exception as exc:                                  # noqa: BLE001
        return str(exc)[:52]


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    lage = N.Lage(instrument="spot", strategie="einstieg")

    je_fu = K.baue(reihen, "funding", zus.get("funding"), horizont=HORIZONT)
    echt = funding_schichten(je_fu)
    gemischt = funding_schichten(je_fu, mische=True)

    print("=" * 112)
    print("V7 — KRITERIUM 3: traegt die Groesse noch, wenn `funding` "
          "FESTGEHALTEN wird?")
    print("=" * 112)
    print("  %s" % messmenge.zeile())
    print("  %s" % N.standardzeile())
    print("  Schichtung in %d Funding-Fuenftel, je Tag - ueber den "
          "`nur`-Parameter (Tagesvariante)." % SCHICHTEN)
    print("  ⚠️⚠️ Die Zeile GEMISCHT ist der Kern: dieselbe Schichtung "
          "ohne Information.")
    print("     Faellt ECHT und GEMISCHT gleich, kostet die SCHICHTUNG - "
          "dann sagt der Lauf")
    print("     ueber Redundanz NICHTS.")
    print("  Faechergroesse: %.1f Symbole je Tag und Fuenftel"
          % (np.mean([len(v) for v in echt[0].values()]) if echt[0] else 0))

    erg = {}
    for kand in KANDIDATEN:
        try:
            je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        except Exception as exc:                              # noqa: BLE001
            print("\n  %-14s -> %s" % (kand, str(exc)[:60]))
            continue
        try:
            menge, fenster = BE.messbasis(kand)
        except KeyError:
            menge, fenster = "", ""
        # ⚠️⚠️ DIE MENGE IST NICHT STILLSCHWEIGEND `frei`.
        #
        # Fuer die REGISTRIERTEN Beitraege (`turnover`, `oi_aenderung`) ist
        # `frei` die Registrierungsbasis - dort ist es richtig.
        #
        # Fuer KANDIDATEN ohne Basis (`schnitt`, `schnitt50`, `vola`) ist
        # `frei` dagegen die MARKT-Frage (P6), nicht die Beitragsfrage.
        # Der Vierfachtest hat `schnitt` gerade deshalb ueber 10/20/50 %
        # gemessen - und auf `frei` war er auch dort „nicht trennbar".
        #
        # ⚠️ Hier wird es BENANNT statt behoben: eine Momentum-Menge UND
        # ein Funding-Fuenftel zugleich liesse zu wenige Anker uebrig
        # (30 je Fuenftel mal 20 % waeren 6). Der Vorbehalt gehoert in
        # die Auswertung, nicht in eine Zahl, die es nicht hergibt.
        ohne_basis = not menge
        menge = menge or "frei"
        if fenster and fenster != "voll":
            je = {t: z for t, z in je.items() if str(t) >= fenster}

        print()
        print("  %s   (Menge %s%s)"
              % (kand.upper(), menge,
                 " ⚠️ keine registrierte Basis - das ist die "
                 "MARKT-Frage" if ohne_basis else ""))
        b0 = miss(kand, je, mom, lage, menge)
        if isinstance(b0, str):
            print("     ohne Schichtung  -> %s" % b0)
            continue
        print("     %-18s %+9.4f [%+.4f .. %+.4f]  %s"
              % ("ohne Schichtung", b0.wirkung, b0.unten, b0.oben,
                 b0.urteil.split(" (")[0][:38]), flush=True)

        for wie, schichten in (("echt", echt), ("GEMISCHT", gemischt)):
            traeger, werte = 0, []
            for k in range(SCHICHTEN):
                b = miss(kand, je, mom, lage, menge, nur=schichten[k])
                if isinstance(b, str):
                    continue
                werte.append(b.wirkung)
                if b.traegt:
                    traeger += 1
            if not werte:
                print("     in funding %-8s nicht messbar" % wie)
                continue
            erg[(kand, wie)] = (float(np.mean(werte)), traeger, len(werte))
            print("     in funding %-7s %+9.4f (Mittel ueber %d Fuenftel) "
                  " traegt in %d von %d"
                  % (wie, float(np.mean(werte)), len(werte), traeger,
                     len(werte)), flush=True)
        erg[(kand, "ohne")] = (b0.wirkung, 1 if b0.traegt else 0, 1)

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 112)
    print("DIE ABNAHME — erklaert `funding` es, oder kostet die "
          "Schichtung?")
    print("=" * 112)
    zf = erg.get(("zufall", "echt"))
    if zf and zf[1]:
        print("  ⚠️⚠️⚠️ `zufall` traegt in %d von %d Fuenfteln - der Lauf "
              "gilt NICHT." % (zf[1], zf[2]))
    elif zf:
        print("  ✔ `zufall` traegt in keinem Fuenftel.")
    print()
    print("  ⚠️ Massgeblich ist die ZAHL DER FUENFTEL, in denen die "
          "Groesse traegt - nicht das")
    print("     Mittel der Wirkung. Bei fuenf schmalen Faechern ist ein "
          "Mittelwert leicht gross")
    print("     und trotzdem nirgends trennbar (der Vorabtest zeigte "
          "genau das bei `zufall`).")
    print()
    print("     %-14s %10s %10s %10s  %s"
          % ("Kandidat", "ohne", "echt", "GEMISCHT", "Lesart"))
    for kand in KANDIDATEN:
        o = erg.get((kand, "ohne"))
        e = erg.get((kand, "echt"))
        g = erg.get((kand, "GEMISCHT"))
        if not (o and e and g):
            continue
        # ⚠️⚠️ ZUERST DIE VORFRAGE: traegt die Groesse UEBERHAUPT?
        #
        # Der Vorabtest hat genau hier einen Fehler gefunden: `zufall`
        # bekam „✔ unabhaengig von `funding`", obwohl er in 0 von 5
        # Fuenfteln traegt. Eine Regel, die nur Betraege vergleicht,
        # bescheinigt einer Groesse ohne Wirkung Unabhaengigkeit - und
        # das ist dieselbe Verwechslung wie „Eigenschaft statt Urteil"
        # (Fehler 4 vom 08.09.).
        if not o[1]:
            lesart = "— traegt schon ohne Schichtung nicht, keine Aussage"
        elif not e[1] and not g[1]:
            lesart = ("⚠️ traegt in KEINEM Fuenftel, auch nicht gemischt - "
                      "die SCHICHTUNG kostet")
        # ⚠️ Der Vergleich ist ECHT gegen GEMISCHT, nicht ECHT gegen OHNE.
        # Nur so ist der Verlust durch die Schichtung herausgerechnet.
        # ⚠️⚠️⚠️ DIE AUFLOESUNG: bei fuenf Faechern ist die feinste
        # unterscheidbare Einheit EIN Fach. Ein Unterschied von einem
        # Fuenftel ist damit KEIN Unterschied, sondern die Grenze.
        #
        # Der erste Entwurf las „2 gegen 3" als „`funding` erklaert einen
        # Teil mit". Das ist dieselbe Ueberdeutung wie beim Gleichstand in
        # N-46b - dort hat der Vorabtest sie gefangen, hier erst das
        # Ergebnis.
        elif abs(e[1] - g[1]) <= 1:
            lesart = ("— %d gegen %d Fuenftel: EIN Fach Unterschied ist "
                      "die Aufloesungsgrenze, keine Aussage"
                      % (e[1], g[1]))
        elif e[1] < g[1]:
            lesart = ("⚠️⚠️ `funding` erklaert einen Teil mit (%d gegen %d "
                      "Fuenftel)" % (e[1], g[1]))
        else:
            lesart = ("✔ unabhaengig von `funding` (%d gegen %d Fuenftel)"
                      % (e[1], g[1]))
        print("     %-14s %+10.4f %+10.4f %+10.4f  %s"
              % (kand, o[0], e[0], g[0], lesart))
    print()
    print("  ⚠️ Der Vergleich ist ECHT gegen GEMISCHT - NICHT echt gegen "
          "ohne. Nur so ist der")
    print("     Verlust herausgerechnet, den die kleineren Faecher "
          "ohnehin verursachen.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
