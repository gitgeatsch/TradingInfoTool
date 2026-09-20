# -*- coding: utf-8 -*-
"""Phase 4, Punkt 2b — WELCHES FENSTER? Ein PROFIL, kein Einzelurteil.

## Die Frage, im Wortlaut des Nutzers

*„Ein Handel mit Hebel und erhöhtem Risiko 2-5 wird durch die bestehende
hohe Wahrscheinlichkeit **eines kurzen starken Anstiegs** dynamisch
erzeugt. Meist sogar kleiner als 2 Tage aber **das kannst du erheben
welches Fenster (Horizont) das beste ist**."*

⚠️ Die „2 Tage" sind KEINE Vorgabe (Klarstellung 20.09.): sie sind
**F-202**, eine eigene Messung der medianen Dauer bis zur Entscheidung.
Der Horizont wird hier erhoben, nicht gesetzt.

## ⚠️⚠️ WARUM EIN PROFIL UND KEINE VORAB GEWAEHLTE HAUPTZELLE

Der erste Entwurf war 5 Horizonte x 5 Zielhoehen = 25 Zellen. Bei 25
Zellen liegt der familienweite Fehlalarm bei 47 Prozent
(`phase3_stufen.familienfehler`) — irgendeine traegt immer. Mein Ausweg
war, EINE Hauptzelle vorab zu benennen. **Das war der schlechtere Weg,
und der Nutzer hat danach gefragt** (*„ist das ueberhaupt eine
Entscheidung?"*).

Der bessere Weg steht im Bestand:

> **2.208-n86 (gilt):** *„auf der 20-%-Menge traegt er bei FUENF von
> sechs Horizonten, **mit monoton wachsender Wirkung** (+0,0130 H1 ->
> +0,0418 H5 -> +0,1858 H20). Die Ausnahme H10 ist eine **Enthaltung,
> kein Widerspruch**."*

Benachbarte Horizonte teilen dieselben Anker und ueberlappende Fenster;
sie sind stark korreliert. **Ein Zufallstreffer springt nicht als glatte
Kurve durch sechs Zellen.** Nach genau dieser Logik wird hier auch ueber
Stufen geurteilt — Monotonie gegen Buckel (2.158).

⚠️ Und eine Hauptzelle haette geschadet: traegt H2 und die Nachbarn
nicht, ist das **N2** (*„Warum traegt `schnitt50` bei H5, aber nicht bei
H2 und H20?"*) — eine Einzelzelle ohne Form, seit Wochen ungeklaert.

    6 Zellen -> familienweiter Fehlalarm rund 14 % (statt 53 % bei 30)

## ⚠️⚠️⚠️ ZWEI KANAELE, WEIL SIE GEGENEINANDER LAUFEN KOENNEN

    RICHTUNG   P(Ziel | aufgeloest)   ungeloeste Anker fallen HERAUS
    QUOTE      P(Ziel)                ungeloeste zaehlen als verfehlt

> **2.139-quote (gilt):** *„Richtung besser, Quote schlechter — und `q`
> in der Potentialformel IST die Quote."*
> **2.136 (gilt):** `turnover` traegt Richtung (+0,00512), auf der Quote
> nicht, weil sein Aufloesungskanal (-0,00218) dagegenlaeuft.

Bei H20 sind 95 % aufgeloest, beide Masse fallen fast zusammen. **Bei H1
sind es 21 %** — dort ist der Unterschied die halbe Frage. Der 2a-Lauf
mass NUR die Richtung; das steht als Einschraenkung in 2.490-kanal.

## Was die ZAEHLUNG vorab schon weiss (Machbarkeit, 20.09.)

    H      aufgeloest   P(Z|auf)   P(Ziel)   EW/aufgeloest   Bloecke
     1        20,9 %      0,204     0,043       -0,389          90
     2        38,3 %      0,241     0,092       -0,278          90
     3        51,3 %      0,266     0,137       -0,201          90
     5        68,3 %      0,295     0,201       -0,116          90
     7        78,0 %      0,311     0,242       -0,068          64
    20        95,1 %      0,332     0,316       -0,003          22

⚠️ **Bei symmetrischem Ziel (1,0 R) ist der EW auf JEDEM Horizont fair**
(-0,016 bis -0,025). Die Kosten kommen aus der **Asymmetrie**: der Stop
liegt bei 1 R, das Ziel bei 2 R — der naehere Rand wird frueher
getroffen. Wer kurz misst, sieht ueberproportional frueh aufgeloeste
Faelle, also ueberproportional Stops.

⚠️ **Das ist kein Verlust, den jemand erleidet** — das Fenster ist ein
MESSfenster, keine Zwangsschliessung. Es heisst: bei kurzem H wird eine
**stop-verzerrte Teilmenge** gemessen, und das Urteil muss das tragen.

⚠️ Bloecke sind bei H1 bis H5 KEIN Engpass (90 gegen 22 bei H20) —
`_block(H)` ist 3 x H.

## Wie geurteilt wird — vorab festgelegt

| | |
|---|---|
| **TRAEGT** | das Band schliesst den Nullpunkt aus (Messstandard) |
| **FORM** | traegt ein Kandidat auf mehreren BENACHBARTEN Horizonten mit gleichgerichteter Wirkung? Eine Einzelzelle ohne Nachbarn ist ein **Hinweis**, kein Befund |
| **KONTROLLE** | `zufall` muss auf JEDEM Horizont still sein. Traegt er irgendwo, gilt diese Zelle nicht (2.237) |
| **MENGE** | je Kandidat und Horizont nach `menge_nach_datenlage` (F-212) |
| **FENSTER** | ab 2023 (ZEITFENSTER-AB-2023) |

⚠️ Die Zielhoehe bleibt hier auf **2,0 R** — der laufenden Regel Z-2
(`config.yaml risiko.crv_minimum`). Die Zielhoehen-Achse ist eine ZWEITE
Frage und wird erst gestellt, wenn dieses Profil etwas zeigt; sie ist
dann **bedingt** und das gehoert ausgewiesen.

⚠️ NUR LESEND. Kein DB-Schreibzugriff, kein API-Abruf.

    python phase4_2b_horizontprofil.py
    python phase4_2b_horizontprofil.py --horizonte 2,3 --kanal quote
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import k1c_hebel_barriere as K1                          # noqa: E402
import messe_eigenschaft_beitrag as B                    # noqa: E402
import messe_kandidaten_als_regel as K                   # noqa: E402
import messmenge                                          # noqa: E402
import messnorm as N                                      # noqa: E402
import messnorm_auswahl as MA                            # noqa: E402
import phase3_stufen as ST                                # noqa: E402
from messe_alle_kandidaten import zusatzquellen          # noqa: E402
from messe_beitrag_auf_auswahl import momentum250        # noqa: E402

HORIZONTE = (1, 2, 3, 5, 7, 20)
ZIELHOEHE = 2.0
AB = "2023-01-01"
SAAT = 20260920
# ⚠️ Dieselbe Liste wie K-1c, damit die H20-Spalte gegen 2a vergleichbar
# ist. `zufall` ist die Kontrolle und MUSS stumm bleiben.
KANDIDATEN = K1.KANDIDATEN

# ⚠️ Die Barrierenreihen haengen NUR an (H, Zielhoehe, Kanal) - nicht am
# Kandidaten. Ohne diesen Zwischenspeicher wird dieselbe Rechnung fuenfmal
# je Zelle wiederholt (in K-1c ist das so, dort mit EINEM Horizont
# vertretbar; hier waere es das Sechsfache davon).
_SPEICHER: dict = {}


def _barrieren(reihen: dict, H: int, ungeloest):
    schluessel = (H, ZIELHOEHE, ungeloest)
    if schluessel not in _SPEICHER:
        _SPEICHER[schluessel] = {
            s: K1.barriere_je_reihe(v, H, ZIELHOEHE, ungeloest)
            for s, v in reihen.items()}
    return _SPEICHER[schluessel]


def je_tag_umrechnen(je_tag: dict, je_sym: dict):
    """Wie `K1.barriere_je_tag`, aber mit vorgerechneten Reihen.

    ⚠️ Bewusst dieselbe Mechanik: Mindestbesetzung 12 je Tag, Anteil
    ausgewiesen. Wer hier abweicht, misst etwas anderes als 2a."""
    neu, drin, gesamt = {}, 0, 0
    for tag, zeilen in je_tag.items():
        if str(tag)[:10] < AB:
            continue
        z = []
        for x in zeilen:
            gesamt += 1
            b = (je_sym.get(x["sym"]) or {}).get(tag)
            if b is None:
                continue
            drin += 1
            z.append({"sym": x["sym"], "kennzahl": x["kennzahl"],
                      "in_r": float(b)})
        if len(z) >= 12:
            neu[tag] = z
    return neu, (drin / gesamt if gesamt else 0.0)


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:26]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    horizonte = HORIZONTE
    if "--horizonte" in args:
        horizonte = tuple(int(x) for x in
                          args[args.index("--horizonte") + 1].split(","))
    kanaele = ("richtung", "quote")
    if "--kanal" in args:
        kanaele = (args[args.index("--kanal") + 1],)
    # ⚠️ SAATPROBE (Methodik 2.477). Vorgabe ist die des Erstlaufs; ein
    # Urteil darf nicht an einer Ziehung haengen - erst recht kein
    # NULLBEFUND und keine VORZEICHENDREHUNG.
    saat = SAAT
    if "--saat" in args:
        saat = int(args[args.index("--saat") + 1])
    for k in kanaele:
        if k not in ("richtung", "quote"):
            print("unbekannter Kanal %r - erlaubt: richtung, quote" % k)
            return 2

    t0 = time.time()
    print("=" * 112)
    print("PHASE 4 · PUNKT 2b - WELCHES FENSTER? Ein PROFIL ueber die "
          "Horizonte")
    print("=" * 112)
    print("  " + N.standardzeile())
    print("  " + messmenge.zeile())
    print("  Zielhoehe %.1f R (Regel Z-2) · Fenster ab %s · Menge je "
          "Kandidat nach Datenlage" % (ZIELHOEHE, AB))
    print("  ⚠️ %d Zellen je Kanal - familienweiter Fehlalarm rund %.0f %%. "
          "Geurteilt wird nach FORM" % (len(horizonte),
                                        100 * ST.familienfehler(
                                            len(horizonte))))
    print("     ueber benachbarte Horizonte, nicht nach einer Einzelzelle "
          "(2.208-n86).")
    print()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    lage = N.Lage(instrument="hebel", strategie="einstieg", simuliert=True)

    for kanal in kanaele:
        ungeloest = None if kanal == "richtung" else 0.0
        print("-" * 112)
        print("  KANAL: %s" % (
            "RICHTUNG - P(Ziel | aufgeloest), ungeloeste Anker fallen heraus"
            if kanal == "richtung" else
            "QUOTE - P(Ziel), ungeloeste zaehlen als verfehlt. ⚠️ DAS IST "
            "`q` DER POTENTIALFORMEL"))
        print("-" * 112)
        print("  %-14s %3s %6s %9s %20s %9s %7s  %s"
              % ("Kandidat", "H", "Menge", "Wirkung", "Band", "Bezug",
                 "Bloecke", "Urteil"))
        profil: dict = {}
        # ⚠️ HORIZONT AUSSEN, KANDIDAT INNEN - und das ist kein Geschmack:
        # so lebt immer nur EIN Satz Barrierenreihen im Speicher (rund
        # 512.000 Anker). Andersherum haengen alle sechs Horizonte
        # gleichzeitig darin. Die FORM wird unten ohnehin aus `profil`
        # gebildet, nicht aus der Reihenfolge der Ausgabe.
        for H in horizonte:
            _SPEICHER.clear()
            for kand in KANDIDATEN:
                try:
                    je0 = K.baue(reihen, kand, zus.get(kand), horizont=H)
                except Exception as exc:                   # noqa: BLE001
                    print("  %-14s %3d -> %s" % (kand, H, str(exc)[:56]))
                    continue
                je, _anteil = je_tag_umrechnen(
                    je0, _barrieren(reihen, H, ungeloest))
                if not je:
                    print("  %-14s %3d -> leere Welt" % (kand, H))
                    continue
                menge = MA.menge_nach_datenlage(je, mom, horizont=H)
                if menge is None:
                    print("  %-14s %3d %6s -> KEINE Menge haelt Anker UND "
                          "Bloecke" % (kand, H, "-"))
                    continue
                try:
                    b = MA.pruefe_auswahl(
                        kand, je, mom, lage=lage, menge=menge,
                        rng=np.random.default_rng(saat), horizont=H,
                        hypothese="2b Horizontprofil",
                        verwendung="Beitrag", zielgroesse="barriere")
                except Exception as exc:                   # noqa: BLE001
                    print("  %-14s %3d -> %s" % (kand, H, str(exc)[:60]))
                    continue
                profil.setdefault(kand, {})[H] = b
                print("  %-14s %3d %6s %+9.4f [%+.4f..%+.4f] %+9.4f %7d  %s"
                      % (kand, H, menge, b.wirkung, b.unten, b.oben,
                         b.bezugswert, b.n_bloecke, kurz(b.urteil)),
                      flush=True)
            print()

        # ---- Die FORM, und zwar ausgewiesen ------------------------------
        print("  FORM je Kandidat (die Frage ist nicht ,wo traegt er`, "
              "sondern ,hat es eine Gestalt`):")
        zf = profil.get("zufall", {})
        zf_traegt = sorted(h for h, b in zf.items() if b.traegt)
        for kand, je_h in profil.items():
            traegt = sorted(h for h, b in je_h.items() if b.traegt)
            reihe = " ".join("H%d:%+.4f%s" % (h, je_h[h].wirkung,
                                              "*" if je_h[h].traegt else "")
                             for h in sorted(je_h))
            print("    %-14s %s" % (kand, reihe))
            if kand != "zufall":
                print("      traegt bei %s%s"
                      % (("H" + ", H".join(str(h) for h in traegt))
                         if traegt else "KEINEM Horizont",
                         "" if len(traegt) < 2 else
                         "  (mehrere BENACHBARTE - das ist eine Form)"))
        print()
        if zf_traegt:
            print("  ⚠️⚠️ DIE KONTROLLE `zufall` TRAEGT bei H%s - diese "
                  "Zellen gelten NICHT (2.237)."
                  % ", H".join(str(h) for h in zf_traegt))
        else:
            print("  ✔ Die Kontrolle `zufall` ist auf allen Horizonten "
                  "still - die Zellen sind gueltig.")
        print()

    print("  ⚠️ `hebel` hat in der Produktion NULL Signale - jede Aussage "
          "hier ist SIMULIERT.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
