# -*- coding: utf-8 -*-
"""H-3: die Totzone — UND die Suche nach einer tragenden H-Nutzung (30.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Der Auftrag, woertlich

Nutzer 30.08.: *"mach H-3 — die Totzone 0,5 ATR prüfen. Zur bisherigen
Messung eine Anmerkung: du legst mir dasselbe Ergebnis vor — H auf null oder
falsch nutzen. Das war nicht der Auftrag. Nach H-3 ist eine H-Nutzung oder
Kombination zu finden."*

⚠️ BERECHTIGT. Zweimal wurde derselbe Schluss vorgelegt, statt zu suchen.
Dieses Werkzeug sucht deshalb - und zwar systematisch statt anekdotisch.

## Teil 1 — H-3: die Totzone

`lagebeschreibung.NIVEAU_MIN_ABSTAND_ATR = 0.5` entscheidet, ab welchem
Abstand ein Kursniveau ueberhaupt als Marke gilt. Sie ist die letzte der
vier nie geprueften Annahmen (K1) und die einzige, die **beide** H-Baender
gleichzeitig verschiebt.

⚠️ EIN LAUF REICHT FUER ALLE TOTZONEN. `LB._cluster_mit_art` - der teure
Teil - ist von der Totzone unabhaengig; sie wirkt erst bei der Zuordnung
nach oben/unten. Der Lauf holt die Niveaus deshalb mit `totzone=0.0` und
filtert danach selbst. Fuenf Laeufe waeren fuenfmal dieselbe Arbeit.

## Teil 2 — die Suche, und warum sie NICHT aus dem Bauch kommt

⚠️ EIN ERSTER ENTWURF PRUEFTE 21 ZELLEN AUS DEM BAUCH (Funding, Volatilitaet,
Marktphase, Totzone). Nutzereinwand 30.08.: *"bist du dir sicher, dass du
ohne weitere Recherche jetzt H in einer Nebenpruefung messen kannst?"* -
berechtigt. Haette davon eine getroffen, waere es Data-Mining gewesen, keine
Hypothese. Die Zellen kommen deshalb jetzt aus der Lehrmeinung und aus einer
Luecke im eigenen Bestand.

### Was die Recherche als WIRKSAM belegt (30.08.2026)

    ANZAHL BERUEHRUNGEN   1 = kaum Bedeutung · 2 = "potential, requires
                          further confirmation" · 3+ = "strong and reliable"
                          · 4+ = "very strong"
    VOLUMEN an der Marke  hochvolumige Zonen deutlich stabiler, geringere
                          Bruchwahrscheinlichkeit
    ALTER                 "the influence of a zone decays over time"
    TRENDFILTER           Signale sperren, wenn der uebergeordnete Trend
                          nicht mitgeht

### ⚠️ DIE LUECKE IM EIGENEN BESTAND - und sie ist der Kern dieser Messung

`MIN_BERUEHRUNGEN = 2`. Unser H baut also auf genau der Stufe auf, die die
Lehrmeinung als BESTAETIGUNGSBEDUERFTIG einstuft.

Kapitel 112 hat Staerke, Alter und "gefegt" geprueft - aber mit dieser
ausdruecklichen Einschraenkung im eigenen Kopf:

    "NUR B LAESST SICH ANREICHERN, NICHT A. A ist eine ABWESENHEIT - an
     einer Marke, die es nicht gibt, ist kein Merkmal zu messen."

⚠️ DIE ANREICHERUNG WURDE AM WIRKUNGSLOSEN TEIL GEPRUEFT. Heute ist gemessen:
B ist zu 86,75 % wahr und traegt nichts; A ist der wirksame Teil (H und A
stimmen bei 98,27 % ueberein).

Und die Begruendung von damals enthaelt einen Denkfehler: A laesst sich sehr
wohl anreichern - nicht am OBJEKT, sondern an der DEFINITION.
`MIN_BERUEHRUNGEN` entscheidet, welche Niveaus ueberhaupt als Widerstand
gelten. Mit 3 statt 2 ist A nicht nur haeufiger, sondern ANDERS
ZUSAMMENGESETZT. Das ist nie gemessen worden.

### Die Zellen - zwei Achsen, beide begruendet

    TOTZONE          0,25 / 0,5 / 1,0 / 1,5 / 2,0 ATR
                     -> K1, die letzte der vier ungepruesften Annahmen
    BERUEHRUNGEN     2 / 3 / 4
                     -> aus der Lehrmeinung, und die Luecke aus Kapitel 112

Das sind 15 Zellen je Bauform. Gerechnet werden zwei Bauformen (H = A UND B,
sowie nur A), also 30 Zellen. Dazu drei Alters-Zellen als dritte belegte
Groesse.

## Vorab festgelegt

  FUND          eine Zelle schlaegt das Zellen-Maximum des Placebos UND hat
                in beiden Historienhaelften dasselbe Vorzeichen
  kein Fund     sonst - und dann wird das ausdruecklich als "gesucht und
                nicht gefunden" berichtet, mit der Angabe, wie gross ein
                Effekt haette sein muessen

    python messe_h3_totzone_und_kombination.py
"""
from __future__ import annotations

import io
import json
import os
import statistics as st
import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from messe_marken import (CRV, MIN_BERUEHRUNGEN, K, MAX_TAGE,     # noqa: E402
                          _niveaus_schnell, _SwingSpeicher)
from simuliere_bremse import _reihen_roh, klassen_aus_db          # noqa: E402

CACHE = "anker_h3_2026_08_30.json"
HORIZONT = 20
MINDESTALTER = 250
BRUCH = 5.0
BLOCK = 120
MIND_JE_GRUPPE = 30
PLACEBO_LAEUFE = 40
TOTZONEN = (0.25, 0.5, 1.0, 1.5, 2.0)     # 0,5 ist der Produktionswert
BERUEHRUNGEN = (2, 3, 4)                  # 2 ist der Produktionswert
ZELLEN_ANGEKUENDIGT = 33


def _ausgang(c, h, l, i, stop, ziel):
    for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
        if l[j] <= stop:
            return "stop"
        if h[j] >= ziel:
            return "ziel"
    return "abgelaufen"


def laufe(db="data/messdaten.db", klasse="krypto"):
    """Ein Lauf, alle Totzonen. Niveaus einmal, Zuordnung fuenfmal."""
    from messe_funding_niveau import lade_funding
    try:
        funding = lade_funding()
        print("Funding geladen: %d Symbole" % len(funding), flush=True)
    except Exception as exc:                                 # noqa: BLE001
        print("⚠️ Funding nicht ladbar (%s) - N4 faellt aus" % exc, flush=True)
        funding = {}

    roh = _reihen_roh(db, klasse, klassen_aus_db(db))
    aus = []
    t0 = letzte = time.time()
    for nr, (sym, (c, h, l, v, a, off, d)) in enumerate(roh.items(), 1):
        del v
        sp = _SwingSpeicher(h, l)
        f_sym = funding.get(sym.upper(), {})
        cc = np.asarray(c, dtype=float)
        verh = cc[1:] / np.maximum(cc[:-1], 1e-12)
        bruch = (verh > BRUCH) | (verh < 1.0 / BRUCH)
        for i in range(off + 1 + MINDESTALTER, len(c) - HORIZONT - 1):
            atr, kurs = float(a[i - off]), float(c[i])
            if not (atr > 0 and kurs > 0):
                continue
            if bruch[i:i + HORIZONT].any():
                continue
            # ⚠️ TOTZONE 0 - ALLE Niveaus. Gefiltert wird gleich selbst.
            n = _niveaus_schnell(sp, c, h, l, i, atr, totzone=0.0)
            # ⚠️ ABSTAND *UND* BERUEHRUNGSZAHL - beide Achsen bleiben offen.
            # Wer hier schon nach MIN_BERUEHRUNGEN filtert, hat die zweite
            # Achse verworfen, bevor sie gemessen wurde. Genau so entstand
            # die Luecke in Kapitel 112.
            oben = [((m["preis"] - kurs) / atr, m["beruehrungen"], m["alter"])
                    for m in n["oben"]]
            unten = [((kurs - m["preis"]) / atr, m["beruehrungen"], m["alter"])
                     for m in n["unten"]]
            stop_atr = K                       # Stop liegt K ATR unter Kurs
            ziel_atr = CRV * K                 # Ziel CRV x Stopabstand darueber
            satz = {"sym": sym, "datum": d[i], "atr_rel": atr / kurs,
                    "phase": None,
                    "funding": f_sym.get(d[i]),
                    "in_r": (float(c[i + HORIZONT]) - kurs) / (K * atr)}
            ag = _ausgang(c, h, l, i, kurs - K * atr, kurs + CRV * K * atr)
            satz["ziel"] = (1.0 if ag == "ziel"
                            else 0.0 if ag == "stop" else None)
            for tz in TOTZONEN:
                for mb in BERUEHRUNGEN:
                    o = [x for x in oben if x[0] >= tz and x[1] >= mb]
                    u = [x for x in unten if x[0] >= tz and x[1] >= mb]
                    frei = not any(x[0] < ziel_atr for x in o)
                    gedeckt = any(x[0] < stop_atr for x in u)
                    schl = "%g_%d" % (tz, mb)
                    satz["frei_" + schl] = frei
                    satz["ged_" + schl] = gedeckt
                    satz["h_" + schl] = bool(frei and gedeckt)
            # ALTER der naechsten Marke im Weg - dritte belegte Groesse
            # ("the influence of a zone decays over time"). Genommen wird
            # die naechste ueber dem Kurs beim PRODUKTIONSWERT 0,5/2.
            nah = [x for x in oben if x[0] >= 0.5 and x[1] >= 2]
            satz["alter_oben"] = (min(nah)[2] if nah else None)
            aus.append(satz)
        if time.time() - letzte >= 60:
            letzte = time.time()
            print("  [%4.1f min] Reihe %d/%d - %d Anker"
                  % ((letzte - t0) / 60, nr, len(roh), len(aus)), flush=True)
    return aus


# ------------------------------------------------------------- Auswertung
def je_block(anker, schluessel, feld="in_r", bedingung=None, block=BLOCK):
    """Traeger gegen Nicht-Traeger, JE ZEITBLOCK - ohne Komposition."""
    lage = (lambda x: float(np.mean(x))) if feld == "ziel" else st.median
    teil = [a for a in anker if bedingung is None or bedingung(a)]
    tage = sorted({a["datum"] for a in teil})
    if len(tage) < 2 * block:
        return None
    zu = {t: i // block for i, t in enumerate(tage)}
    eimer = {}
    for a in teil:
        if a.get(feld) is None:
            continue
        k = schluessel(a)
        if k is None:
            continue
        eimer.setdefault(zu[a["datum"]], ([], []))[0 if k else 1] \
            .append(float(a[feld]))
    w = [lage(m) - lage(o) for m, o in eimer.values()
         if len(m) >= MIND_JE_GRUPPE and len(o) >= MIND_JE_GRUPPE]
    return w if len(w) >= 5 else None


def mittel(w):
    return None if w is None else float(np.mean(w))


def zeile(titel, w, huerde, einzug=2):
    if w is None:
        print("%s%-44s zu wenige Bloecke" % (" " * einzug, titel))
        return None
    m = float(np.mean(w))
    fund = abs(m) > huerde
    print("%s%-44s %+.4f R  %2d/%2d Bloecke +   %s"
          % (" " * einzug, titel, m, int((np.array(w) > 0).sum()), len(w),
             "⚠️ SCHLAEGT DIE HUERDE" if fund else "unter der Huerde"))
    return m


def main():
    if os.path.exists(CACHE):
        anker = json.loads(io.open(CACHE, encoding="utf-8").read())
        print("%d Anker aus dem Zwischenspeicher." % len(anker))
    else:
        print("Lade Anker (523 Reihen, alle Totzonen) - das dauert...",
              flush=True)
        anker = laufe()
        io.open(CACHE, "w", encoding="utf-8").write(json.dumps(anker))
        print("Zwischengespeichert -> %s" % CACHE)
    rng = np.random.default_rng(20260830)
    n = len(anker)
    mit_f = sum(1 for a in anker if a.get("funding") is not None)

    print()
    print("=" * 104)
    print("H-3 — DIE TOTZONE, UND DIE SUCHE NACH EINER TRAGENDEN NUTZUNG")
    print("=" * 104)
    print("%d Anker, %d Symbole, %s .. %s"
          % (n, len({a["sym"] for a in anker}),
             min(a["datum"] for a in anker), max(a["datum"] for a in anker)))
    print("mit Funding-Wert: %d (%.1f %%)" % (mit_f, 100 * mit_f / n))
    print("Produktionswert der Totzone: 0,5 ATR")

    # ---- DIE HUERDE ZUERST, aus dem Placebo ueber ALLE Zellen -----------
    print()
    print("-" * 104)
    print("  ⚠️ DIE HUERDE — Placebo-Maximum ueber alle %d angekuendigten Zellen"
          % ZELLEN_ANGEKUENDIGT)
    print("-" * 104)
    print("  Bei 33 Zellen findet der Zufall allein schon deutliche Werte.")
    print("  Die Huerde ist deshalb das MAXIMUM des Placebos ueber alle Zellen")
    print("  eines Laufs, nicht das Band einer einzelnen (Methodik 2.57).")
    je_sym = {}
    for a in anker:
        je_sym.setdefault(a["sym"], []).append(a)
    sortiert = {s: sorted(z, key=lambda x: x["datum"]) for s, z in je_sym.items()}
    schluessel = ["h_%g_%d" % (tz, mb) for tz in TOTZONEN for mb in BERUEHRUNGEN]
    schluessel += ["frei_%g_%d" % (tz, mb) for tz in TOTZONEN for mb in BERUEHRUNGEN]
    maxima = []
    for _ in range(PLACEBO_LAEUFE):
        versetzt = []
        for z in sortiert.values():
            v = int(rng.integers(0, max(len(z), 1)))
            umlauf = z[v:] + z[:v]
            for x, y in zip(z, umlauf):
                # ⚠️ ALLE Marken-Felder gemeinsam versetzen, sonst zerfaellt
                # der Zusammenhang zwischen den Zellen und das Maximum
                # faellt zu klein aus.
                neu_ = dict(x)
                for k in schluessel:
                    neu_[k] = y[k]
                versetzt.append(neu_)
        werte = []
        for k in schluessel:
            w = je_block(versetzt, lambda a, kk=k: a[kk])
            if w:
                werte.append(abs(float(np.mean(w))))
        if werte:
            maxima.append(max(werte))
    huerde = float(np.quantile(maxima, 0.95))
    print("  Placebo-Maximum je Lauf: Median %.4f, 95%%-Quantil %.4f R"
          % (float(np.median(maxima)), huerde))
    print("  -> Eine Zelle gilt nur als Fund, wenn |Wirkung| > %.4f R" % huerde)

    ergebnisse = {}

    for bauform, praefix, klar in (
            ("H = A UND B", "h_", "H — wie heute gebaut"),
            ("nur A", "frei_", "H-1 — nur A, B faellt weg")):
        print()
        print("=" * 104)
        print("  %s   (Zeilen = Totzone, Spalten = Mindestberuehrungen)" % klar)
        print("=" * 104)
        print("  %-14s %26s %26s %26s"
              % ("Totzone", "2 Beruehrungen", "3 Beruehrungen", "4 Beruehrungen"))
        for tz in TOTZONEN:
            zeile_ = "  %-14s" % ("%.2f ATR%s" % (tz, " *" if tz == 0.5 else ""))
            for mb in BERUEHRUNGEN:
                k = "%s%g_%d" % (praefix, tz, mb)
                q = 100 * sum(1 for a in anker if a[k]) / n
                w = je_block(anker, lambda a, kk=k: a[kk])
                if w is None:
                    zeile_ += "%26s" % "zu wenige Bloecke"
                    continue
                m = float(np.mean(w))
                ergebnisse["%s tz%.2f mb%d" % (bauform, tz, mb)] = m
                zeile_ += "%18s" % ("%+.4f R %s" % (m, "⚠️" if abs(m) > huerde else "  "))
                zeile_ += "%8s" % ("(%.1f%%)" % q)
            print(zeile_)
        print("  * = Produktionswert")

    print()
    print("=" * 104)
    print("  DAS ALTER DER NAECHSTEN MARKE — 'the influence decays over time'")
    print("=" * 104)
    mit_alter = [a for a in anker if a.get("alter_oben") is not None]
    if len(mit_alter) > 10000:
        q3 = np.quantile([a["alter_oben"] for a in mit_alter], [1 / 3, 2 / 3])
        print("  Alter der naechsten Marke oberhalb, in Handelstagen:")
        print("  Drittelgrenzen %.0f / %.0f" % (q3[0], q3[1]))
        for name, bed in (
                ("frisch (< %.0f Tage)" % q3[0],
                 lambda a: a["alter_oben"] < q3[0]),
                ("mittel", lambda a: q3[0] <= a["alter_oben"] < q3[1]),
                ("alt    (>= %.0f Tage)" % q3[1],
                 lambda a: a["alter_oben"] >= q3[1])):
            w = je_block(mit_alter, lambda a: a["h_0.5_2"], bedingung=bed)
            m = zeile("H bei Marke %s" % name, w, huerde, 4)
            ergebnisse["Alter " + name] = m
    else:
        print("  zu wenige Anker mit Altersangabe")

    # ---------------------------------------------------------- Das Fazit
    print()
    print("=" * 104)
    print("ERGEBNIS DER SUCHE")
    print("=" * 104)
    gueltig = {k: v for k, v in ergebnisse.items() if v is not None}
    treffer = {k: v for k, v in gueltig.items() if abs(v) > huerde}
    print("  %d Zellen gerechnet, Huerde %.4f R" % (len(gueltig), huerde))
    if not treffer:
        groesst = max((abs(v) for v in gueltig.values()), default=0.0)
        print()
        print("  ⚠️ KEIN FUND. Groesster Betrag %.4f R, noetig waeren %.4f R."
              % (groesst, huerde))
        print("  Das heisst NICHT 'H ist wertlos' - es heisst: unter diesen")
        print("  vorab benannten, aus der Lehrmeinung abgeleiteten Formen ist")
        print("  keine, die den Zufall bei dieser Zellenzahl schlaegt.")
        print()
        print("  Die fuenf groessten Betraege - zur Einordnung, NICHT als Befund:")
        for k, v in sorted(gueltig.items(), key=lambda x: -abs(x[1]))[:5]:
            print("     %-32s %+.4f R" % (k, v))
        return
    print()
    print("  ⚠️ %d ZELLE(N) SCHLAGEN DIE HUERDE:" % len(treffer))
    for k, v in sorted(treffer.items(), key=lambda x: -abs(x[1])):
        print("     %-32s %+.4f R" % (k, v))

    print()
    print("=" * 104)
    print("  ⚠️ PFLICHTPRUEFUNG DER TREFFER — beide Historienhaelften")
    print("=" * 104)
    print("  Ein Treffer, dessen Vorzeichen zwischen den Haelften dreht, ist")
    print("  kein Fund, sondern eine Episode.")
    tage = sorted({a["datum"] for a in anker})
    mitte = tage[len(tage) // 2]
    for k in sorted(treffer, key=lambda x: -abs(treffer[x])):
        teile = k.split()
        if len(teile) < 3 or not teile[-1].startswith("mb"):
            continue
        praefix = "h_" if k.startswith("H = A UND B") else "frei_"
        # ⚠️ `%g` IM LAUF, `%.2f` IM NAMEN - der erste Lauf brach hier mit
        # KeyError 'h_1.00_4', weil die Felder 'h_1_4' heissen. Der Wert
        # muss zurueck durch dieselbe Formatierung, nicht durch die des
        # Anzeigenamens.
        feld = "%s%g_%s" % (praefix, float(teile[-2][2:]), teile[-1][2:])
        print()
        print("  %s" % k)
        werte = []
        for name, bed in (("erste Haelfte", lambda a: a["datum"] < mitte),
                          ("zweite Haelfte", lambda a: a["datum"] >= mitte)):
            w = je_block(anker, lambda a, f=feld: a[f], bedingung=bed)
            werte.append(zeile(name, w, huerde, 4))
        if all(x is not None for x in werte):
            gleich = (werte[0] > 0) == (werte[1] > 0)
            print("    -> %s" % ("gleiches Vorzeichen - der Fund haelt" if gleich
                                 else "⚠️ VORZEICHEN DREHT - eine Episode, kein Fund"))


if __name__ == "__main__":
    main()
