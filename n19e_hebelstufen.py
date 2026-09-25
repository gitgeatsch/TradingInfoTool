# -*- coding: utf-8 -*-
"""N19-E: die HEBELSTUFEN direkt gegen die Barrieren-Quote (25.09.2026)

Vorabfestlegung: `Basisinfos/Vorabfestlegung_N19E_Hebelstufen_25_09.md`
N19-E ist eine **Nutzerentscheidung vom 06.09.2026, die nie umgesetzt
wurde**. Dieses Werkzeug holt sie nach.

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️⚠️ DER BRUCH, DEN ES BEHEBT - er steht in `rechne_kandidaten_beitrag`
═══════════════════════════════════════════════════════════════════════

    faktor = 1.0 / (1.0 + CRV)                        # = 0,3333
    punkte = 100.0 * (werte[k] - mittel) * faktor / 2.0

Die Werte kommen aus `bewegung_r` (Rendite in R) und werden mit einem
THEORETISCHEN Faktor in Quotenpunkte uebersetzt. Gemessen (2.580) sind die
tatsaechlichen Faktoren 0,30 / 0,35 / 0,90 - nicht einheitlich 0,3333. Die
Stufen sind dadurch 1,47x und 1,85x zu gross.

➤ HIER WIRD NICHT UEBERSETZT, SONDERN DIREKT GEMESSEN.

`messnorm.ZIELGROESSEN["barriere"]` gibt die Statistik vor: **mittel**. Bei
`barriere` ist y aus {+CRV, -1}, also

    q = (mittel + 1) / (1 + CRV)

Die Stufe entsteht damit UNMITTELBAR in Quotenpunkten - kein Faktor, keine
Uebersetzung, kein Bruch.

═══════════════════════════════════════════════════════════════════════
 ⚠️ AN `messnorm` GEBUNDEN, NICHT MIT EIGENEN KONSTANTEN
═══════════════════════════════════════════════════════════════════════

Vier meiner Werkzeuge vom 24./25.09. haben NULL `messnorm`-Verweise -
genau der Altbestandsfehler, der jeden Befund unter Vorbehalt stellt
(CLAUDE.md: *"ein Befund aus dieser Gruppe gilt nur mit Vorbehalt"*).
Hier kommen Nullpunkt, Perzentil, Staerken und Zielgroesse aus `messnorm`.

═══════════════════════════════════════════════════════════════════════
 WAS GEMESSEN WIRD
═══════════════════════════════════════════════════════════════════════

    Kandidaten   funding · oi_aenderung
                 ⛔ turnover NICHT - auf `barriere` untermaechtig
                   (+0,0073 gegen Nachweisgrenze 0,0094 bis 0,0180,
                   66 Symbole). Untermaechtig ist NICHT anders.
    Lage         hebel x einstieg, simuliert=True (Pflicht - es gab in
                 der neuen Kette NIE ein Hebelsignal)
    Zielgroesse  barriere   (aus messnorm.ZIELGROESSE_JE_LAGE)
    Horizont     3          (aus messnorm.HORIZONT_JE_LAGE)
    Menge        selektiert (Frageart `beitrag`, F-212)

    B5  Monotonie ueber ALLE fuenf Fuenftel
    B6  beide Historienhaelften
    ⭐  OUT-OF-SAMPLE: Stufen auf der ERSTEN Haelfte, Pruefung auf der
        ZWEITEN. B6 ist nicht dasselbe - es prueft Stabilitaet, nicht
        Ueberanpassung.

    python n19e_hebelstufen.py
    python n19e_hebelstufen.py --symbole 60      # Probelauf
"""
from __future__ import annotations

import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_beitrag_auf_auswahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402

# ⚠️ ALLES AUS DER NORM - keine eigenen Konstanten.
LAGE = N.Lage(instrument="hebel", strategie="einstieg", simuliert=True)
ZIELGROESSE = N.ZIELGROESSE_JE_LAGE[(LAGE.instrument, LAGE.strategie)]
HORIZONT = N.HORIZONT_JE_LAGE[(LAGE.instrument, LAGE.strategie)]
CRV = 2.0
# ⚠️⚠️ `zufall` IST PFLICHT, NICHT KUER. Vorabfestlegung 13 Paragraf 4
# nennt ihn als Negativkontrolle; mein erster Lauf hatte ihn vergessen.
# Eine Stufenleiter ohne Gegenprobe ist eine Zahlenreihe.
KANDIDATEN = ("oi_aenderung", "funding", "zufall")
MIND_JE_TAG = MA.MIND_ANKER          # 12 - dieselbe Grenze wie die Anlage


def _quote_je_fuenftel(je_tag: dict, mom: dict, anteil: float,
                       tage: set | None = None) -> tuple:
    """Je Fuenftel die Barrieren-Trefferquote `q` - die Stufe selbst.

    ⚠️ DIE TAGESKLAMMER IST PFLICHT: Fuenftel werden INNERHALB eines Tages
    gebildet, damit die Marktlage festgehalten ist. Ohne sie misst man die
    Marktbewegung und nennt sie Beitrag.

    ⚠️⚠️ `q` KOMMT AUS DEM MITTELWERT, nicht aus einer eigenen Zaehlung:
    `messnorm.ZIELGROESSEN["barriere"]["statistik"]` = "mittel", und bei
    y aus {+CRV, -1} gilt q = (mittel + 1) / (1 + CRV). Wer stattdessen
    Treffer zaehlt, baut eine zweite Definition derselben Groesse.
    """
    sammel: dict = {k: [] for k in range(5)}
    n_tage = 0
    for tag, z in je_tag.items():
        if tage is not None and tag not in tage:
            continue
        if len(z) < MIND_JE_TAG:
            continue
        m = MB._auswahl_maske(z, mom.get(tag) or {}, anteil, None)
        if m is None or m.sum() < 8:
            continue
        gewaehlt = [x for x, keep in zip(z, m) if keep]
        w = np.array([x["kennzahl"] for x in gewaehlt], float)
        y = np.array([x["in_r"] for x in gewaehlt], float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        treffer = 0
        for k in range(5):
            sel = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if sel.sum() >= 2:
                sammel[k].append(float(np.mean(y[sel])))
                treffer += 1
        if treffer == 5:
            n_tage += 1
    if any(len(sammel[k]) < 30 for k in range(5)):
        return None, None, 0
    mittel = [float(np.mean(sammel[k])) for k in range(5)]
    # ⭐ DIE UMRECHNUNG - aus der Definition, nicht aus einem Faktor
    q = [(m + 1.0) / (1.0 + CRV) for m in mittel]
    q_alle = float(np.mean(q))
    punkte = [round(100.0 * (x - q_alle), 3) for x in q]
    return q, punkte, n_tage


def _nullpunkt_spanne(je_tag: dict, mom: dict, anteil: float, rng,
                      ziehungen: int) -> np.ndarray:
    """Die SPANNE q0-q4 in Welten OHNE Zuordnung - der Bezug.

    ⚠️⚠️ OHNE DIESEN BEZUG IST DIE STUFENLEITER EINE ZAHLENREIHE. Fuenf
    Mittelwerte streuen immer; ob 1,2 Punkte Spanne viel sind, sagt erst
    der Vergleich mit einer Welt, in der es nichts zu finden gibt.
    Mein erster Lauf hatte ihn vergessen.

    ⚠️ Gemischt wird die Kennzahl INNERHALB des Tages - die Marktlage
    bleibt, nur die Zuordnung faellt weg. Dieselbe Neutralisierung wie
    in `messnorm_auswahl`.
    """
    aus = []
    for _ in range(ziehungen):
        sammel: dict = {k: [] for k in range(5)}
        for tag, z in je_tag.items():
            if len(z) < MIND_JE_TAG:
                continue
            m = MB._auswahl_maske(z, mom.get(tag) or {}, anteil, None)
            if m is None or m.sum() < 8:
                continue
            g = [x for x, keep in zip(z, m) if keep]
            y = np.array([x["in_r"] for x in g], float)
            r = rng.permutation(len(g)) / max(len(g) - 1, 1)
            for k in range(5):
                sel = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
                if sel.sum() >= 2:
                    sammel[k].append(float(np.mean(y[sel])))
        if all(len(sammel[k]) >= 30 for k in range(5)):
            q = [(float(np.mean(sammel[k])) + 1.0) / (1.0 + CRV)
                 for k in range(5)]
            aus.append(abs(q[0] - q[4]))
    return np.array(aus)


def _trennschaerfe(je_tag: dict, mom: dict, anteil: float, rng,
                   p90: float, staerken) -> list:
    """Ab welcher gepflanzten Leiter findet die Anlage etwas?

    ⚠️⚠️ GEPFLANZT WIRD IN EINE NEUTRALISIERTE WELT - die Zuordnung wird
    zuerst gemischt, dann die Leiter aufgepraegt. Wer in die ECHTEN Daten
    pflanzt, misst Effekt PLUS Pflanzung und bekommt bei Staerke null
    schon einen Treffer. Genau dieser Fehler ist mir am 24.09. in
    `messe_hebel_nachpruefung` passiert.

    ⚠️ ZENTRIERT: Fuenftel 0..4 bekommen -2s..+2s, die Summe ist null -
    der Gesamtmittelwert verschiebt sich NICHT (Messstandard).

    ⚠️ Gepflanzt wird in R (die Einheit von `in_r`), gemessen wird die
    Spanne in q - dieselbe Groesse wie im Hauptlauf.
    """
    aus = []
    for s in staerken:
        treffer, n = 0, 0
        for _ in range(10):
            sammel: dict = {k: [] for k in range(5)}
            for tag, z in je_tag.items():
                if len(z) < MIND_JE_TAG:
                    continue
                m = MB._auswahl_maske(z, mom.get(tag) or {}, anteil, None)
                if m is None or m.sum() < 8:
                    continue
                g = [x for x, keep in zip(z, m) if keep]
                y = np.array([x["in_r"] for x in g], float)
                r = rng.permutation(len(g)) / max(len(g) - 1, 1)
                for k in range(5):
                    sel = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
                    if sel.sum() >= 2:
                        # zentrierte Leiter, in R aufgepraegt
                        sammel[k].append(float(np.mean(y[sel]))
                                         + (k - 2.0) * (s / 2.0))
            if all(len(sammel[k]) >= 30 for k in range(5)):
                q = [(float(np.mean(sammel[k])) + 1.0) / (1.0 + CRV)
                     for k in range(5)]
                n += 1
                if abs(q[0] - q[4]) > p90:
                    treffer += 1
        aus.append((s, treffer / n if n else float("nan"), n))
    return aus


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("N19-E — DIE HEBELSTUFEN DIREKT GEGEN DIE BARRIEREN-QUOTE")
    print("=" * 100)
    print("  Lage %s x %s%s · Zielgroesse %s · Horizont %d · CRV %.1f"
          % (LAGE.instrument, LAGE.strategie,
             "  ⚠️ SIMULIERT" if LAGE.simuliert else "",
             ZIELGROESSE, HORIZONT, CRV))
    print("  ⚠️ Nullpunkt/Perzentil/Staerken aus `messnorm`: %d Ziehungen, "
          "%.0f. Perzentil" % (N.NULL_ZIEHUNGEN, N.NULL_PERZENTIL))

    rng = np.random.default_rng(20260925)
    reihen = B.lade()
    if grenze:
        reihen = {k: reihen[k] for k in list(reihen)[:grenze]}
    mom = MB.momentum250(reihen)
    tm = K.lade_terminmarkt()
    zus = {"oi_aenderung": tm["oi_aenderung"], "funding": F.lade_funding()}

    for kand in KANDIDATEN:
        print()
        print("=" * 100)
        print("  %s" % kand)
        print("=" * 100)
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        if not je:
            print("    leere Welt")
            continue
        zul = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
        print("    %d Tage · zulaessige Mengen: %s"
              % (len(je), ", ".join(zul) or "⚠️ KEINE"), flush=True)
        if not zul:
            continue

        for menge in zul:
            anteil = MA.MENGEN[menge]
            q, punkte, n = _quote_je_fuenftel(je, mom, anteil)
            if q is None:
                print("    %-6s zu duenn" % menge)
                continue
            print()
            print("    ── MENGE %s  (%d Tage mit allen fuenf Fuenfteln)"
                  % (menge, n))
            print("       %-10s %8s %8s %8s %8s %8s"
                  % ("Fuenftel", "0", "1", "2", "3", "4"))
            print("       %-10s %s" % ("q",
                  " ".join("%8.4f" % x for x in q)))
            print("       %-10s %s" % ("Punkte",
                  " ".join("%8.3f" % x for x in punkte)))

            # ── B5: Monotonie ueber ALLE fuenf ────────────────────────
            auf = all(q[i] <= q[i + 1] for i in range(4))
            ab = all(q[i] >= q[i + 1] for i in range(4))
            print("       B5 Monotonie: %s"
                  % ("steigend ✔" if auf else "fallend ✔" if ab
                     else "⚠️ NICHT monoton"))

            # ── ⭐ DER NULLPUNKT - die Spanne gegen eine Welt ohne Effekt ──
            spanne = abs(q[0] - q[4])
            null = _nullpunkt_spanne(je, mom, anteil, rng, N.NULL_ZIEHUNGEN)
            if len(null) >= 10:
                p90 = float(np.percentile(null, N.NULL_PERZENTIL))
                print("       ⭐ Spanne q0-q4 %.4f · Nullpunkt %.4f "
                      "(%.0f. Perz %.4f) · %s"
                      % (spanne, float(null.mean()), N.NULL_PERZENTIL, p90,
                         "UEBER dem Nullpunkt" if spanne > p90
                         else "⛔ IM RAUSCHEN"))
                # ── ⭐ TRENNSCHAERFE - nur wo der Nullpunkt steht ──────
                ts = _trennschaerfe(je, mom, anteil, rng, p90, N.STAERKEN)
                gefunden = next((s for s, qu, _n in ts if qu >= 0.8), None)
                print("       ⭐ Trennschaerfe (neutralisiert, 10 Ziehungen):")
                print("          %s" % "  ".join(
                    "%.2f:%.0f%%" % (s, 100 * qu) for s, qu, _n in ts))
                print("          zuverlaessig (80 %%) ab: %s"
                      % ("%.2f R" % gefunden if gefunden else "keiner"))
                if gefunden:
                    # ⚠️⚠️ EINHEITEN: die Spanne steht in q, die gepflanzte
                    # Staerke in R. Ein direkter Vergleich waere falsch.
                    # Eine Leiter der Staerke s laeuft von -s bis +s, also
                    # 2s in R; ueber q = (mittel+1)/(1+CRV) sind das
                    # 2s/(1+CRV) in q.
                    gef_q = 2.0 * gefunden / (1.0 + CRV)
                    print("          ⚠️ Aufloesung %.2f R = %.4f in q"
                          % (gefunden, gef_q))
                    print("          ⚠️ gemessene Spanne %.4f -> %s"
                          % (spanne,
                             "UEBER der Aufloesung" if spanne > gef_q
                             else "⛔ UNTER der Aufloesung (Grauzone)"))
            else:
                print("       ⭐ Nullpunkt: zu wenige Welten (%d)" % len(null))

            # ── Die Spanne gegen die Kelly-Nullstelle ─────────────────
            null = 1.0 / (1.0 + CRV)
            ueber = [i for i, x in enumerate(q) if x > null]
            print("       Kelly-Nullstelle %.4f · Fuenftel darueber: %s"
                  % (null, ueber or "⛔ KEINES"))

            # ── B6: beide Haelften ────────────────────────────────────
            alle = sorted(je)
            mitte = len(alle) // 2
            for txt, tset in (("1. Haelfte", set(alle[:mitte])),
                              ("2. Haelfte", set(alle[mitte:]))):
                q2, p2, n2 = _quote_je_fuenftel(je, mom, anteil, tset)
                if q2 is None:
                    print("       B6 %s: zu duenn" % txt)
                    continue
                a2 = all(q2[i] <= q2[i + 1] for i in range(4))
                b2 = all(q2[i] >= q2[i + 1] for i in range(4))
                print("       B6 %-11s q4-q0 %+.4f  %s  (%d Tage)"
                      % (txt, q2[4] - q2[0],
                         "monoton" if (a2 or b2) else "⚠️ nicht monoton", n2))

            # ── ⭐ OUT-OF-SAMPLE ──────────────────────────────────────
            # ⚠️ B6 prueft STABILITAET, das hier prueft UEBERANPASSUNG.
            # Die Stufen werden auf der ersten Haelfte geschaetzt und auf
            # der zweiten ANGEWANDT - wer beide getrennt schaetzt, hat
            # zweimal in-sample gemessen.
            q_in, p_in, _ = _quote_je_fuenftel(je, mom, anteil,
                                               set(alle[:mitte]))
            q_out, p_out, _ = _quote_je_fuenftel(je, mom, anteil,
                                                 set(alle[mitte:]))
            if q_in and q_out:
                r = float(np.corrcoef(p_in, p_out)[0, 1])
                print("       ⭐ out-of-sample: Rangtreue der Stufen r %+.3f"
                      % r)
                print("          in  %s" % " ".join("%+.2f" % x for x in p_in))
                print("          out %s" % " ".join("%+.2f" % x for x in p_out))
                print("          %s" % ("✔ die Ordnung haelt" if r > 0.5
                                        else "⚠️ die Ordnung haelt NICHT"))
    print()
    print("=" * 100)
    print("  ⚠️ DIE ENTSCHEIDUNGSREGEL steht in Vorabfestlegung 13 Paragraf 5:")
    print("     monoton + out-of-sample stabil + Kontrolle sauber -> Stufen")
    print("     nicht monoton -> SCHALTER statt Regler, keine Leiter")
    print("     nur in-sample -> Ueberanpassung, kein Befund")
    print()
    print("  ⚠️ UND DIE GRENZE, VORAB BENANNT (Paragraf 5.1): die Wirkungen")
    print("     liegen bei +0,005 bis +0,011, die Nachweisgrenze bei 0,009")
    print("     bis 0,021. Kleine Stufen und breite Baender sind ERWARTET.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
