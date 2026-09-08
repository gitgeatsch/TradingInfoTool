# -*- coding: utf-8 -*-
"""KUENSTLICHE WELTEN MIT BEKANNTER WAHRHEIT — der Baukasten (08.09.2026)

## Wozu

Der Messstandard vom 08.09. macht die Urteile widerspruchsfrei. Ob die
Anlage **richtig** urteilt, ist damit nicht gesagt - dazu fehlt der
Selbsttest gegen bekannte Wahrheit:

    Fehlalarmquote   wie oft meldet sie TRAEGT, wo NICHTS ist?
    Fundquote        wie oft findet sie einen Effekt, der WIRKLICH da ist?

Dieses Modul baut die Welten. `selbsttest_messanlage.py` misst darauf.

## ⚠️⚠️ DIE ENTSCHEIDENDE ENTWURFSREGEL: NICHT `pflanze` BENUTZEN

Die Positivkontrolle der Norm pflanzt mit `pflanze=-s` in die
**gemischte** Welt. Wer damit auch die Testwelten baut, prueft den
Mechanismus mit sich selbst - und Befund 2.198 sagt gerade, dass genau
dieser Mechanismus verdaechtig ist.

> **Hier wird die Welt von Grund auf mit der Beziehung gebaut**, und die
> Norm bekommt sie als gewoehnliche `je_tag`-Struktur zu sehen. Sie kann
> nicht wissen, dass etwas darin steckt.

## Wie der Effekt entsteht

Die Kennzahl der Anlage ist `median(frei) - median(alle)`, wobei "frei"
die 80 % unterhalb `GRENZE` sind. Ein Effekt heisst also: **die oberen
20 % nach Kennzahl haben ein schlechteres Ergebnis.**

    in_r = tagesschock[t] + eigenrauschen - staerke * 1{rang >= 0,80}

⚠️ `staerke` ist NICHT die gemessene Wirkung. Werden 20 % um `staerke`
gesenkt, verschiebt sich der Median ALLER nur um einen Bruchteil davon.
**Deshalb misst `wahre_wirkung()` sie nach, statt sie anzunehmen** - die
Fundquote wird gegen die NACHGEMESSENE Groesse aufgetragen.

## ⚠️ Warum ein Tagesschock mit Gedaechtnis sein MUSS

Baute man unabhaengige Tage, braeuchte es keine Bloecke - und die
Fehlalarmquote fiele schmeichelhaft aus. Die echte Welt hat Marktphasen.
Der Schock ist deshalb AR(1); `wie_echt_ist_sie()` vergleicht die
Autokorrelation auf Blocklaenge mit der echten Messbasis.

    python selbsttest_welt.py            # Vorabtest, kein langer Lauf
"""
from __future__ import annotations

import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_regel_wirksamkeit as W                          # noqa: E402

# An der echten Messbasis abgelesen (08.09.2026, 536 Krypto-Reihen):
#   2.942 Tage · Median 313 Werte/Tag · in_r Median -0,391 · IQA 3,073
ECHT_IQA = 3.073
ECHT_MEDIAN = -0.391
TAGE = 1500          # >= 20 Bloecke bei Blocklaenge 60 (H20)
JE_TAG = 150         # bei 20 % bleiben 30 Anker - ueber MIND_ANKER = 12
PHI = 0.90           # Gedaechtnis des Tagesschocks (Marktphasen)
SCHOCK_ANTEIL = 0.40  # Anteil des Tagesschocks an der Gesamtstreuung


def welt(rng, *, staerke: float = 0.0, tage: int = TAGE,
         je_tag_n: int = JE_TAG, phi: float = PHI,
         kennzahl_ak: float = 0.0) -> tuple[dict, dict]:
    """Eine Welt mit bekannter Wahrheit -> (je_tag, mom).

    `staerke = 0` heisst: die Kennzahl sagt NICHTS ueber das Ergebnis.
    Alles andere ist Fehlalarm.

    ## ⚠️⚠️ `kennzahl_ak` — die BEHARRLICHKEIT der Kennzahl

    Die erste Fassung zog die Kennzahl jeden Tag neu (AK = 0). An den
    echten Daten gemessen (08.09.2026, Autokorrelation je Symbol von Tag
    zu Tag, Median ueber alle Symbole mit >= 200 Tagen):

        zufall    -0,001     <- so war der Pruefstand gebaut
        funding   +0,608
        schnitt   +0,985

    Bei `schnitt` stehen an fast allen Tagen DIESELBEN Symbole in der
    gesperrten Gruppe. Ein Pruefstand ohne Beharrlichkeit sagt ueber
    genau die beiden tragenden Beitraege NICHTS - und faellt vermutlich
    zu schmeichelhaft aus, weil er mehr unabhaengige Beobachtungen
    vortaeuscht, als es gibt.

    ⚠️ Die Vorgabe bleibt 0, damit frueher gemessene Zahlen reproduzierbar
    bleiben. Die beharrlichen Faelle laufen ausdruecklich mit
    `kennzahl_ak=0.61` bzw. `0.985`.
    """
    syms = ["S%03d" % i for i in range(je_tag_n)]

    # ---- Tagesschock mit Gedaechtnis ------------------------------------
    schock = np.zeros(tage, float)
    for t in range(1, tage):
        schock[t] = phi * schock[t - 1] + rng.normal(0.0, 1.0)
    if schock.std() > 0:
        schock = schock / schock.std()

    # Streuung so aufteilen, dass die Summe der echten IQA entspricht.
    # t(4) hat IQA 1,482 - erst messen, dann skalieren (keine Konstante
    # aus dem Kopf).
    probe = rng.standard_t(4, size=200000)
    iqa_t = float(np.percentile(probe, 75) - np.percentile(probe, 25))
    s_eigen = ECHT_IQA * (1.0 - SCHOCK_ANTEIL) / iqa_t
    s_schock = ECHT_IQA * SCHOCK_ANTEIL / 1.349   # IQA einer N(0,1)

    # ⚠️ Beharrliche Kennzahl als AR(1) je Symbol: `kz_t = a*kz_{t-1} +
    # sqrt(1-a^2)*Rauschen` hat Einheitsstreuung und exakt die
    # Autokorrelation `a` - so ist die eingestellte Zahl auch die
    # gemessene, ohne Nachkalibrierung.
    a = float(kennzahl_ak)
    kz = rng.normal(0.0, 1.0, je_tag_n)
    rest = (1.0 - a * a) ** 0.5

    je_tag, mom = {}, {}
    for t in range(tage):
        tag = "T%05d" % t
        if a:
            kz = a * kz + rest * rng.normal(0.0, 1.0, je_tag_n)
        else:
            kz = rng.normal(0.0, 1.0, je_tag_n)
        # ⚠️ DIE ECHTE Rangfunktion, keine Nachbildung - sonst weicht die
        # gepflanzte Grenze von der gemessenen ab.
        oben = W.rang(kz) >= W.GRENZE
        y = (ECHT_MEDIAN + schock[t] * s_schock
             + rng.standard_t(4, size=je_tag_n) * s_eigen)
        if staerke:
            y = y - float(staerke) * oben
        je_tag[tag] = [{"sym": syms[i], "kennzahl": float(kz[i]),
                        "in_r": float(y[i])} for i in range(je_tag_n)]
        # Die AUSWAHL ist unabhaengig vom Effekt - der saubere Grundfall.
        mom[tag] = {syms[i]: float(v)
                    for i, v in enumerate(rng.normal(0.0, 1.0, je_tag_n))}
    return je_tag, mom


def wahre_wirkung(staerke: float, ziehungen: int = 12,
                  saat: int = 4711) -> float:
    """Die TATSAECHLICHE Wirkung dieser Staerke — nachgemessen.

    ⚠️ Sie ist deutlich kleiner als `staerke`: gesenkt werden nur 20 %,
    und der Median ALLER verschiebt sich dadurch nur anteilig. Wer die
    Fundquote gegen `staerke` auftraegt, liest die Anlage zu streng.

    Gerechnet auf der VOLLEN Welt (`anteil = 1`), damit die Zahl nicht
    von der Auswahl abhaengt.
    """
    from messe_beitrag_auf_auswahl import sammle
    werte = []
    for z in range(ziehungen):
        je, mom = welt(np.random.default_rng(saat + z), staerke=staerke)
        g = sammle(je, mom, 1.0)
        frei = np.concatenate([y[~o] for o, y in g.values()])
        alle = np.concatenate([y for _o, y in g.values()])
        werte.append(float(np.median(frei) - np.median(alle)))
    return float(np.mean(werte))


def wie_echt_ist_sie() -> None:
    """⚠️ VORABTEST — taugt die Welt ueberhaupt als Pruefstand?

    Drei Fragen, und jede kann den ganzen Selbsttest entwerten:

        1. Ist bei `staerke = 0` wirklich NICHTS drin?
        2. Wie gross ist die Wirkung einer Staerke TATSAECHLICH?
        3. Sieht die Abhaengigkeit ueber die Tage aus wie die echte?
    """
    from messnorm import _block, pruefe_block
    from messe_beitrag_auf_auswahl import sammle
    from pruefe_n31_tagesklammer import je_tag_wirkung

    print("=" * 92)
    print("VORABTEST DES PRUEFSTANDES — bevor irgendetwas Langes laeuft")
    print("=" * 92)

    # ---- 1) Bei staerke = 0 darf NICHTS drin sein ----------------------
    print()
    print("  1) Ist die Nullwelt wirklich leer?")
    null = [wahre_wirkung(0.0, ziehungen=1, saat=9000 + i) for i in range(8)]
    print("     8 Welten: %s"
          % "  ".join("%+.4f" % v for v in null))
    m, sd = float(np.mean(null)), float(np.std(null))
    print("     Mittel %+.4f · Streuung %.4f  ->  %s"
          % (m, sd, "OK, leer" if abs(m) < 2 * sd / np.sqrt(len(null)) + 0.003
             else "⚠️ DIE NULLWELT IST NICHT LEER - Generator fehlerhaft"))

    # ---- 2) Was ist eine Staerke WERT? ---------------------------------
    print()
    print("  2) Was ist eine gepflanzte Staerke tatsaechlich wert?")
    print("     %10s %14s %10s" % ("Staerke", "wahre Wirkung", "Anteil"))
    for s in (0.05, 0.10, 0.20, 0.40, 0.80):
        w = wahre_wirkung(s, ziehungen=6)
        print("     %10.2f %+14.4f %9.1f %%" % (s, w, 100.0 * w / s))
    print("     ⚠️ Die Anlage misst NICHT die gepflanzte Zahl. Deshalb")
    print("        traegt der Selbsttest gegen die WAHRE Wirkung auf.")

    # ---- 2b) Trifft die eingestellte Beharrlichkeit? -------------------
    print()
    print("  2b) Kommt die eingestellte Beharrlichkeit auch heraus?")
    print("     %10s %14s   %s" % ("eingestellt", "gemessen", "Urteil"))
    for a_soll in (0.0, 0.61, 0.985):
        je, _m = welt(np.random.default_rng(555), staerke=0.0,
                      kennzahl_ak=a_soll, tage=600)
        folgen = {}
        for t in sorted(je):
            for x in je[t]:
                folgen.setdefault(x["sym"], []).append(x["kennzahl"])
        aks = []
        for v in folgen.values():
            v = np.array(v, float)
            if len(v) > 100 and v.std() > 0:
                aks.append(float(np.corrcoef(v[:-1], v[1:])[0, 1]))
        ist = float(np.median(aks))
        print("     %10.3f %14.3f   %s"
              % (a_soll, ist,
                 "OK" if abs(ist - a_soll) < 0.03
                 else "⚠️ WEICHT AB - der Generator tut nicht, was er sagt"))

    # ---- 3) Sieht die Abhaengigkeit echt aus? --------------------------
    print()
    print("  3) Autokorrelation auf Blocklaenge — kuenstlich gegen echt")
    block = _block(20)
    je, mom = welt(np.random.default_rng(1234), staerke=0.0)
    d = je_tag_wirkung(sammle(je, mom, 1.0))
    bp = pruefe_block(d, block)
    print("     kuenstlich: %d Tage · Block %d · AK %+.3f · %s"
          % (len(d), block, bp["ak"], bp["grund"]))
    try:
        import messe_eigenschaft_beitrag as B
        import messe_kandidaten_als_regel as K
        from messe_beitrag_auf_auswahl import momentum250
        r = B.lade()
        jr = K.baue(r, "zufall", None, horizont=20)
        dr = je_tag_wirkung(sammle(jr, momentum250(r), 1.0))
        br = pruefe_block(dr, block)
        print("     echt:       %d Tage · Block %d · AK %+.3f · %s"
              % (len(dr), block, br["ak"], br["grund"]))
        print("     -> %s"
              % ("beide unter der Grenze 0,15 - vergleichbar"
                 if bp["ok"] and br["ok"] else
                 "⚠️ die Bloecke verhalten sich UNTERSCHIEDLICH"))
    except Exception as exc:                                 # noqa: BLE001
        print("     echte Basis nicht ladbar: %s" % str(exc)[:60])


if __name__ == "__main__":
    wie_echt_ist_sie()
