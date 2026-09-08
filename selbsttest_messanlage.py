# -*- coding: utf-8 -*-
"""DER SELBSTTEST DER MESSANLAGE — gegen bekannte Wahrheit (08.09.2026)

## Warum es ihn gibt

Nutzerfrage 08.09.: *„Bist du dir sicher, dass wir mit diesem Schritt eine
stabile Basis haben oder ist das Risiko noch hoch, dass noch Fehler
vorliegen?"*

Die ehrliche Antwort war: nein. Der Messstandard macht die Urteile
**widerspruchsfrei**, nicht **richtig**. Was eine Aussage ueber
Stabilitaet rechtfertigen wuerde, sind zwei Quoten gegen bekannte
Wahrheit - und die gab es fuer die Anlage als Ganzes nie.

    Fehlalarmquote   wie oft meldet sie TRAEGT, wo NICHTS ist?
    Fundquote        wie oft findet sie einen Effekt, der WIRKLICH da ist?

## ⚠️ Der Sollwert steht VOR dem Lauf fest

`messe_bewertungskennzahl.urteil_tage` bildet ein **95-%-Band**
(`quantile [0,025 · 0,975]`). Einseitig sind das **2,5 %** Fehlalarme.
`Befund.traegt` verlangt zusaetzlich `unten > null_oben`, ist also noch
strenger.

    Fehlalarmquote deutlich UEBER 2,5 %   -> die Anlage ist unzuverlaessig
    Fehlalarmquote weit UNTER 2,5 %       -> sie ist uebervorsichtig, und
                                             das erklaert, warum so wenig
                                             traegt
    dazwischen                            -> sie haelt, was sie verspricht

⚠️ **Beide Ausgaenge sind Befunde.** Wer nur den ersten fuer einen Fehler
haelt, hat die zweite Haelfte der Frage nicht gestellt.

## Was gemessen wird

| | |
|---|---|
| Stufe 1 | `staerke = 0` - reine Nullwelten. Jedes TRAEGT ist ein Fehlalarm |
| Stufe 2 | `staerke > 0` - die Fundquote gegen die **nachgemessene** Wirkung |
| Stufe 3 | die AUSGEWIESENE Trennschaerfe gegen die tatsaechliche Fundquote |

⚠️ Stufe 3 ist die eigentliche Pruefung des Standards: die Anlage
behauptet in jedem Befund eine Trennschaerfe. Stimmt diese Behauptung mit
dem, was sie tatsaechlich findet?

## ⚠️⚠️ Warum die Welten NICHT mit `pflanze` gebaut werden

Siehe `selbsttest_welt.py`: die Positivkontrolle der Norm pflanzt mit
`pflanze=-s`. Wer damit auch die Testwelten baut, prueft den Mechanismus
mit sich selbst. Die Welten hier tragen die Beziehung von Grund auf.

## Der Umfang, und was er an Genauigkeit hergibt

    Stufe 1   50 Welten   -> bei wahren 2,5 % ein Standardfehler von 2,2 pp
    Stufe 2   20 je Stufe -> genug fuer "findet sie es ueberhaupt", nicht
                            fuer eine Quote auf zwei Stellen
    Stufe 3   12 Welten

⚠️ Die Leiter der Stufe 2 wurde nach dem Kurzlauf VERFEINERT. Er zeigte
den Sprung zwischen gemessen +0,019 (0 %) und +0,039 (100 %) - eine
Leiter ohne Stufe dazwischen kann die Aufloesung nicht beziffern,
sondern nur sagen "irgendwo dazwischen".

⚠️ Das reicht, um 2,5 % von 25 % zu unterscheiden - nicht, um 2,5 % von
4 % zu unterscheiden. Die Zahl steht in der Ausgabe daneben.

    python selbsttest_messanlage.py [--menge 20%] [--klein]
"""
from __future__ import annotations

import argparse
import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
import selbsttest_welt as SW                                 # noqa: E402

HORIZONT = 20
# ⚠️ EINE Staerke fuer die Quotenlaeufe - die Positivkontrolle kostet je
# Staerke fuenf Ziehungen und wird fuer `traegt` nicht gebraucht. Stufe 3
# laeuft dann mit der vollen Leiter.
SPAR_LEITER = (0.02,)
STAERKEN = (0.05, 0.10, 0.14, 0.18, 0.22, 0.30)


def einmal(rng, staerke, menge, staerken, je_tag_n, ak=0.0):
    """Eine Welt bauen und mit der ECHTEN Norm messen."""
    je, mom = SW.welt(rng, staerke=staerke, je_tag_n=je_tag_n,
                      kennzahl_ak=ak)
    return MA.pruefe_auswahl(
        "selbsttest", je, mom,
        lage=N.Lage(instrument="spot", strategie="einstieg"),
        menge=menge, rng=np.random.default_rng(int(rng.integers(1, 10 ** 9))),
        horizont=HORIZONT, staerken=staerken,
        hypothese="Selbsttest gegen bekannte Wahrheit", verwendung="Beitrag")


def quote(treffer: int, n: int) -> str:
    """Quote MIT Standardfehler — die Ziehungszahl gehoert in die Ausgabe."""
    p = treffer / max(1, n)
    se = (p * (1.0 - p) / max(1, n)) ** 0.5
    return "%2d/%2d = %5.1f %% (± %.1f pp)" % (treffer, n, 100 * p, 100 * se)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--menge", default="20%")
    ap.add_argument("--klein", action="store_true",
                    help="Kurzlauf zum Pruefen des Aufbaus, keine Aussage")
    # ⚠️ DIE BEHARRLICHKEIT DER KENNZAHL (08.09., nachgemessen):
    #     zufall -0,001 · funding +0,608 · schnitt +0,985
    # Ohne diese Achse sagt der Selbsttest ueber die beiden TRAGENDEN
    # Beitraege nichts - beide sind stark beharrlich.
    ap.add_argument("--ak", type=float, default=0.0,
                    help="Autokorrelation der Kennzahl je Symbol")
    ap.add_argument("--nur-stufe1", action="store_true",
                    dest="nur1", help="nur die Fehlalarmquote")
    a = ap.parse_args()
    n1, n2, n3 = (8, 5, 3) if a.klein else (50, 20, 12)
    je_tag_n = SW.JE_TAG
    t0 = time.time()

    print("=" * 100)
    print("SELBSTTEST DER MESSANLAGE — Menge %s, Horizont %d" % (a.menge, HORIZONT))
    print("=" * 100)
    print("  %s" % N.standardzeile())
    print("  Sollwert: das Band ist ein 95-%-Band -> einseitig 2,5 % "
          "Fehlalarme.")
    print("  `traegt` prueft zusaetzlich gegen `null_oben`, ist also strenger.")
    print("  Beharrlichkeit der Kennzahl: %.3f  (echt: zufall -0,001 · "
          "funding +0,608 · schnitt +0,985)" % a.ak)
    if a.klein:
        print("  ⚠️ KURZLAUF - prueft nur den Aufbau, liefert KEINE Aussage.")

    # ---- Stufe 1: die Fehlalarmquote ------------------------------------
    print()
    print("  STUFE 1 — Nullwelten: jedes TRAEGT ist ein Fehlalarm")
    fehl, wirkungen = 0, []
    for i in range(n1):
        b = einmal(np.random.default_rng(50000 + i), 0.0, a.menge,
                   SPAR_LEITER, je_tag_n, a.ak)
        fehl += bool(b.traegt)
        wirkungen.append(b.wirkung)
        if (i + 1) % 10 == 0 or i + 1 == n1:
            print("     %2d Welten: %s" % (i + 1, quote(fehl, i + 1)),
                  flush=True)
    p_fehl = fehl / max(1, n1)
    print("     Wirkung der Nullwelten: Mittel %+.4f · Streuung %.4f"
          % (float(np.mean(wirkungen)), float(np.std(wirkungen))))

    # ---- Stufe 2: die Fundquote -----------------------------------------
    print()
    if a.nur1:
        print()
        print("  (Stufe 2 und 3 uebersprungen - nur die Fehlalarmquote)")
        print("  Fehlalarmquote: %s   Sollwert <= 2,5 %%" % quote(fehl, n1))
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 0
    print("  STUFE 2 — Welten MIT Effekt: findet die Anlage ihn?")
    print("     %8s %14s %10s   %s"
          % ("gepflanzt", "wahre Wirkung", "gemessen", "Fundquote"))
    kurve = []
    for s in STAERKEN:
        tr, w = 0, []
        for i in range(n2):
            b = einmal(np.random.default_rng(60000 + int(s * 1000) * 97 + i),
                       s, a.menge, SPAR_LEITER, je_tag_n, a.ak)
            tr += bool(b.traegt)
            w.append(b.wirkung)
        wahr = SW.wahre_wirkung(s, ziehungen=4)
        kurve.append((s, wahr, float(np.mean(w)), tr, n2))
        print("     %8.2f %+14.4f %+10.4f   %s"
              % (s, wahr, float(np.mean(w)), quote(tr, n2)), flush=True)

    # ---- Stufe 3: stimmt die AUSGEWIESENE Trennschaerfe? ----------------
    print()
    print("  STUFE 3 — was die Anlage ueber sich selbst behauptet")
    ts, ts_r = [], []
    for i in range(n3):
        b = einmal(np.random.default_rng(70000 + i), 0.0, a.menge,
                   N.STAERKEN, je_tag_n, a.ak)
        if b.trennschaerfe is not None:
            ts.append(b.trennschaerfe)
            ts_r.append(b.trennschaerfe_in_r)
    if ts:
        print("     ausgewiesene Trennschaerfe (gemessene Skala): "
              "Median %+.4f  [%+.4f .. %+.4f]"
              % (float(np.median(ts)), min(ts), max(ts)))
        print("     dahinter gepflanzt: %s"
              % ", ".join("%.2f" % v for v in sorted(set(ts_r))))
    else:
        print("     ⚠️ keine einzige Welt lieferte eine Trennschaerfe")

    # ---- Das Urteil ueber die Anlage ------------------------------------
    print()
    print("=" * 100)
    print("WAS DAS UEBER DIE ANLAGE SAGT")
    print("=" * 100)
    print("  Fehlalarmquote: %s   Sollwert <= 2,5 %%" % quote(fehl, n1))
    if p_fehl > 0.10:
        print("  ⚠️⚠️ DEUTLICH ZU HOCH - die Anlage meldet Befunde, wo "
              "nichts ist.")
    elif p_fehl > 0.025:
        print("  ⚠️ ueber dem Sollwert, aber in der Groessenordnung - "
              "gegen die Ziehungszahl pruefen.")
    else:
        print("  ✔ innerhalb des Sollwerts.")
    if ts and kurve:
        beh = float(np.median(ts))
        # Wo faengt die Anlage tatsaechlich an, zuverlaessig zu finden?
        gefunden = [(w, t / n) for _s, _wa, w, t, n in kurve if n]
        treffend = [w for w, q in gefunden if q >= 0.80]
        print()
        print("  Sie behauptet eine Trennschaerfe von %+.4f." % beh)
        if treffend:
            print("  Tatsaechlich findet sie ab einer Wirkung von etwa "
                  "%+.4f in >= 80 %% der Faelle." % min(treffend))
            if min(treffend) > beh * 1.5:
                print("  ⚠️⚠️ Sie ist SCHLECHTER als behauptet - die "
                      "ausgewiesene Trennschaerfe ist zu optimistisch.")
            elif min(treffend) < beh * 0.67:
                print("  ⚠️ Sie ist BESSER als behauptet - die "
                      "ausgewiesene Trennschaerfe ist zu pessimistisch, "
                      "und Nullbefunde wirken schwaecher als sie sind.")
            else:
                print("  ✔ Behauptung und Wirklichkeit stimmen ueberein.")
        else:
            print("  ⚠️⚠️ In KEINER gemessenen Stufe erreicht sie 80 %% "
                  "Fundquote - die Leiter reicht nicht weit genug, um "
                  "ihre eigene Behauptung zu pruefen.")
    print()
    se = (0.025 * 0.975 / max(1, n1)) ** 0.5
    print("  ⚠️ Genauigkeit: bei %d Welten und einer wahren Quote von "
          "2,5 %% betraegt der Standardfehler %.1f pp. Diese Zahlen "
          "unterscheiden 2,5 %% von 25 %%, nicht von 4 %%."
          % (n1, 100 * se))
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
