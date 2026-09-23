# -*- coding: utf-8 -*-
"""TRAGEN DIE UNTEREN VIER FUENFTEL EINE ORDNUNG? Regler gegen Schalter.

⚠️⚠️⚠️ DIE VORABFESTLEGUNG STEHT IN
`Basisinfos/Vorabfestlegung_Funding_Abstufung_23_09.md` UND WIRD HIER
NICHT NACHVERHANDELT. Sie nennt Fragestellung, beide Tabellen samt
Herleitung und - das Entscheidende - was welches Ergebnis BEDEUTET,
geschrieben vor der Messung.

## Warum diese Frage und keine andere

Die registrierte Wirkung von `funding` (+0,0246 R) stammt aus
`messe_regel_wirksamkeit.py` - und das Werkzeug misst EINE SPERRE
(`GRENZE = 0.80`, "hohes Funding = ueberhitzt -> OBEN sperren"). Ein
SCHALTER. Fuenf Stufen sind nie gemessen worden; sie sind eine
IN-SAMPLE-Umrechnung aus `rechne_funding_beitrag.py`, deren eigene
Vorabfestlegung ("nutzbar nur wenn MONOTON") die erzeugte Tabelle
verletzt.

Beide Formen unterscheiden sich AUSSCHLIESSLICH in den unteren vier
Fuenfteln - Fuenftel 4 ist praktisch identisch, das Mittel ist in beiden
null. Damit misst der Vergleich die ORDNUNG und nicht die HAERTE
(`feedback_zwei_regeln_vergleichen_auswahlanteil_angleichen`).

## Der Messstandard gilt vollstaendig

⚠️ Gemessen wird auf der SELEKTIERTEN Menge - die stehende Vorbedingung
in `wahrscheinlichkeit.py:404`. Auf der FREIEN Menge gemessene
Gegenbefunde (N-56, N-58) sind genau daran gescheitert und wurden
zurueckgenommen.

Blocklaenge aus `messnorm._block(H20)`, Band ueber Blockbootstrap,
Entscheidung auf der GEPAARTEN Differenz je Tag, beide Historienhaelften
einzeln (R-R8 B6), Positivkontrolle mit gepflanzter Ordnung.

⚠️ NUR LESEND, gegen die Messbasis am Desktop.

    python phase4_funding_abstufung.py
    python phase4_funding_abstufung.py --quelle frei
"""
from __future__ import annotations

import sys

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_beitrag_auf_auswahl as A                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messnorm                                              # noqa: E402
import n67_schnitt_ueber_die_kette as N67                    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm_auswahl import MENGEN                          # noqa: E402

HORIZONT = 20
MENGE = "20%"           # die selektierte Menge - die Vorbedingung
DURCHLASS = 0.50        # die besten 50 % nach Punktsumme, JE FORM GLEICH
ZIEHUNGEN = 300

# ---- die beiden Tabellen, beide mit Mittel null (Vorabfestlegung Par. 2)
HEUTE = (+0.82, +1.30, +0.12, -0.54, -1.70)     # live, wahrscheinlichkeit.py
SCHALTER = (+0.43, +0.43, +0.43, +0.43, -1.72)  # hergeleitet, siehe Par. 2
# turnover bleibt in BEIDEN Formen unveraendert - sonst misst man zwei
# Aenderungen auf einmal.
TURNOVER = (+2.32, +0.50, +0.34, -0.11, -3.06)  # live, Stand 22.09. (S6)


def fuenftel(rang_0_1: np.ndarray) -> np.ndarray:
    """Rang in [0,1] -> Fach 0..4. Obergrenze 1.0 gehoert in Fach 4."""
    return np.minimum((rang_0_1 * 5).astype(int), 4)


def sammle(w, mom, anteil, pflanze: float = 0.0):
    """Je Kalendertag: (Fuenftel funding, Fuenftel turnover, Bewegung).

    ⚠️ Die AUSWAHL laeuft zuerst - genau wie im Betrieb und wie in F-212.
    Erst auf der so entstandenen Menge werden die Raenge gebildet; ein
    Rang ueber die freie Menge waere eine andere Groesse.

    `pflanze` ist die POSITIVKONTROLLE: sie legt eine echte Ordnung ueber
    die unteren vier Fuenftel, absteigend von Fach 0 nach Fach 3. Findet
    die Anlage sie nicht, ist ein Nullergebnis nicht deutbar
    (`feedback_nichtverwerfen_ist_kein_haken`).
    """
    aus = {}
    for tag, zeilen in w["funding"].items():
        if len(zeilen) < 12:
            continue
        syms = [x["sym"] for x in zeilen]
        y = np.array([x["in_r"] for x in zeilen], float)
        m = A._auswahl_maske(zeilen, mom.get(tag) or {}, anteil, None)
        if m is None or m.sum() < 8:
            continue
        faecher = {}
        for art in ("funding", "turnover"):
            zt = {x["sym"]: x["kennzahl"] for x in w[art].get(tag, [])}
            kz = np.array([zt.get(s, np.nan) for s in syms], float)
            ok = np.isfinite(kz) & m
            if ok.sum() < 8:
                faecher = None
                break
            r = np.full(len(syms), np.nan)
            r[ok] = np.argsort(np.argsort(kz[ok])) / max(int(ok.sum()) - 1, 1)
            f = np.full(len(syms), -1)
            f[ok] = fuenftel(r[ok])
            faecher[art] = f
        if not faecher:
            continue
        gilt = m & (faecher["funding"] >= 0) & (faecher["turnover"] >= 0)
        if gilt.sum() < 8:
            continue
        ff, tt, yy = faecher["funding"][gilt], faecher["turnover"][gilt], y[gilt]
        if pflanze:
            # ⚠️ ZENTRIERT pflanzen (feedback_trennschaerfe_zentriert_pflanzen):
            # die vier unteren Faecher bekommen eine absteigende Leiter mit
            # Mittelwert null. Fach 4 bleibt unberuehrt - es ist in beiden
            # Formen gleich und darf den Vergleich nicht tragen.
            leiter = np.array([+1.5, +0.5, -0.5, -1.5, 0.0]) * pflanze
            yy = yy + leiter[ff]
        aus[tag] = (ff, tt, yy)
    return aus


def ertrag(daten, tabelle, tage) -> dict:
    """Je Tag: Median der Bewegung der DURCHGELASSENEN.

    Durchgelassen sind die besten `DURCHLASS` nach Punktsumme - die Zahl
    ist je Form DIESELBE, damit der Auswahlanteil nicht mitmisst.
    """
    tab = np.asarray(tabelle, float)
    tur = np.asarray(TURNOVER, float)
    aus = {}
    for t in tage:
        ff, tt, yy = daten[t]
        punkte = tab[ff] + tur[tt]
        k = max(1, int(round(len(yy) * DURCHLASS)))
        # ⚠️ Bindungen: `argsort` ist stabil, die Reihenfolge bei gleichen
        # Punkten ist damit die Ladereihenfolge - fuer BEIDE Formen
        # dieselbe. Ein Bindungsunterschied kann den Vergleich also nicht
        # in eine Richtung ziehen (die Falle aus 2.551).
        idx = np.argsort(-punkte, kind="stable")[:k]
        aus[t] = float(np.median(yy[idx]))
    return aus


def gepaart(daten, tage):
    """HEUTE minus SCHALTER je Tag - auf DENSELBEN Ankern."""
    a = ertrag(daten, HEUTE, tage)
    b = ertrag(daten, SCHALTER, tage)
    return {t: a[t] - b[t] for t in tage}


def band(diff: dict, tage: list, rng):
    """Blockbootstrap auf die gepaarte Differenz."""
    block = messnorm._block(HORIZONT)
    werte = np.array([diff[t] for t in tage], float)
    starts = np.arange(max(1, len(tage) - block + 1))
    anzahl = int(np.ceil(len(tage) / block))
    zieh = []
    for _ in range(ZIEHUNGEN):
        idx = rng.choice(starts, anzahl)
        g = np.concatenate([werte[s:s + block] for s in idx])[:len(werte)]
        zieh.append(float(g.mean()))
    z = np.array(zieh)
    return float(werte.mean()), float(np.percentile(z, 5)), \
        float(np.percentile(z, 95))


def zeile(name, d, u, o, n):
    zeichen = "✔ Null aus" if (u > 0 or o < 0) else "⚠ Null ein"
    print("     %-26s %+.5f R  [%+.5f .. %+.5f]  %5d Tage  %s"
          % (name, d, u, o, n, zeichen))
    return u > 0 or o < 0


def main() -> int:
    quelle = N67._quelle_aus_argv()
    print("=" * 100)
    print("FUNDING - TRAGEN DIE UNTEREN VIER FUENFTEL EINE ORDNUNG?")
    print("=" * 100)
    print("  Vorabfestlegung: "
          "Basisinfos/Vorabfestlegung_Funding_Abstufung_23_09.md")
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Menge %s (SELEKTIERT) · Durchlass %d %% · Quelle %s"
          % (MENGE, round(DURCHLASS * 100), quelle))
    print("     HEUTE    " + "  ".join("%+.2f" % x for x in HEUTE))
    print("     SCHALTER " + "  ".join("%+.2f" % x for x in SCHALTER))

    print("\n  Laden ...")
    reihen = B.lade()
    w = N67.welten(reihen, quelle)
    mom = momentum250(reihen)
    daten = sammle(w, mom, MENGEN[MENGE])
    tage = sorted(daten)
    if len(tage) < 200:
        print("  ⛔ zu wenige Tage (%d) - keine Aussage" % len(tage))
        return 1
    m = len(tage) // 2
    print("  %d Kalendertage, %s bis %s" % (len(tage), tage[0], tage[-1]))

    rng = np.random.default_rng(messnorm.SAAT)
    print("\n" + "-" * 100)
    print("  DER VERGLEICH - gepaart je Tag, Blocklaenge %d"
          % messnorm._block(HORIZONT))
    print("-" * 100)
    diff = gepaart(daten, tage)
    d, u, o = band(diff, tage, rng)
    traegt = zeile("HEUTE minus SCHALTER", d, u, o, len(tage))

    print("\n  B6 - BEIDE HISTORIENHAELFTEN (R-R8)")
    haelften = {}
    for nm, tg in (("1. Haelfte", tage[:m]), ("2. Haelfte", tage[m:])):
        dh, uh, oh = band(diff, tg, np.random.default_rng(messnorm.SAAT))
        haelften[nm] = (dh, uh, oh, zeile(nm, dh, uh, oh, len(tg)))

    # ---- DIE POSITIVKONTROLLE ---------------------------------------
    # ⚠️ OHNE SIE IST EIN NULLERGEBNIS NICHT DEUTBAR. Gepflanzt wird eine
    # echte, zentrierte Ordnung ueber die unteren vier Faecher; die
    # Anlage MUSS sie als Vorteil von HEUTE erkennen.
    print("\n" + "-" * 100)
    print("  POSITIVKONTROLLE - gepflanzte Ordnung ueber die unteren vier")
    print("-" * 100)
    gefunden = 0
    staerken = (0.02, 0.05, 0.10, 0.20, 0.40)      # bis 0,40 R, Messstandard
    for p in staerken:
        dk = sammle(w, mom, MENGEN[MENGE], pflanze=p)
        tk = sorted(dk)
        dfk = gepaart(dk, tk)
        pd, pu, po = band(dfk, tk, np.random.default_rng(messnorm.SAAT))
        ok = pu > 0
        gefunden += int(ok)
        print("     Staerke %.2f R            %+.5f R  [%+.5f .. %+.5f]  %s"
              % (p, pd, pu, po, "✔ gefunden" if ok else "✖ NICHT gefunden"))
    print("     ➤ %d von %d Staerken gefunden" % (gefunden, len(staerken)))

    # ---- ⚠️⚠️⚠️ DIE ENTSCHEIDENDE KONTROLLE ---------------------------
    # EIGENER FEHLER, gefunden am 23.09. VOR dem Ergebnis: die Grenze
    # "3 von 5 Staerken" oben ist WILLKUERLICH. Sie sagt, dass die Anlage
    # IRGENDEINEN Effekt findet - nicht, dass sie DEN findet, um den es
    # geht.
    #
    # Richtig ist die Frage: findet die Anlage genau die Ordnung, die die
    # LIVE-TABELLE BEHAUPTET? Findet sie die nicht, sagt ein
    # Messgleichstand ueberhaupt nichts - er ist dann nur die Aussage
    # "der Effekt liegt unter der Nachweisgrenze".
    #
    # Umrechnung Punkte -> R, die Gegenrichtung von
    # `rechne_funding_beitrag.py`:  dR = Punkte * 2 * 1/(1+CRV) / 100
    print("\n  ⚠️ DIE ENTSCHEIDENDE KONTROLLE - die BEHAUPTETE Ordnung")
    beh = np.array([x * 0.06 for x in HEUTE])
    beh = beh - beh[:4].mean()
    beh[4] = 0.0                      # Fach 4 ist in beiden Formen gleich
    print("     %s   Spanne der unteren vier %.4f R"
          % ("  ".join("%d:%+.4f" % (k, beh[k]) for k in range(4)),
             beh[:4].max() - beh[:4].min()))
    dk = {t: (ff, tt, yy + beh[ff]) for t, (ff, tt, yy) in daten.items()}
    tk = sorted(dk)
    bd, bu, bo = band(gepaart(dk, tk), tk,
                      np.random.default_rng(messnorm.SAAT))
    kontrolle_ok = bu > 0
    print("     eingepflanzt und gemessen  %+.5f R  [%+.5f .. %+.5f]  %s"
          % (bd, bu, bo, "✔ GEFUNDEN" if kontrolle_ok else
             "✖ NICHT GEFUNDEN - ein Gleichstand sagt hier NICHTS"))

    # ---- DIE ENTSCHEIDUNG NACH DER VORABFESTLEGUNG -------------------
    print("\n" + "=" * 100)
    print("  ENTSCHEIDUNG nach Vorabfestlegung 4, Paragraf 4")
    print("=" * 100)
    h1, h2 = haelften["1. Haelfte"], haelften["2. Haelfte"]
    beide_oben = h1[1] > 0 and h2[1] > 0
    beide_unten = h1[2] < 0 and h2[2] < 0
    widerspruch = (h1[1] > 0 and h2[2] < 0) or (h1[2] < 0 and h2[1] > 0)

    if widerspruch:
        print("     ⛔ DIE HAELFTEN WIDERSPRECHEN SICH - B6 verletzt.")
        print("       Nichts aendern (wie 2.553).")
    elif traegt and d > 0 and beide_oben:
        print("     ✔ DIE ABSTUFUNG TRAEGT - der Regler bleibt.")
        print("       Die Live-Tabelle ist gerechtfertigt, 2.552 geschlossen.")
    elif traegt and d < 0 and beide_unten:
        print("     ⛔ DIE ABSTUFUNG SCHADET - UMBAU AUF SCHALTER.")
        print("       Danach Schwelle nach R-R9 neu kalibrieren.")
    elif not kontrolle_ok:
        print("     ⛔ NICHTS ENTSCHIEDEN - die Positivkontrolle faellt.")
        print("       Die Anlage findet die BEHAUPTETE Ordnung nicht,")
        print("       also sagt der Gleichstand nichts ueber sie aus.")
        print()
        print("       ➤ WAS DAMIT TROTZDEM BELEGT IST, und es ist der")
        print("       eigentliche Befund: die Live-Tabelle behauptet einen")
        print("       Effekt UNTERHALB DER NACHWEISGRENZE. Er laesst sich")
        print("       mit dieser Datenlage weder bestaetigen noch")
        print("       widerlegen - auch nicht, wenn man ihn EINPFLANZT.")
        print("       Die Form ist damit keine MESSfrage mehr.")
    else:
        print("     ➤ MESSGLEICHSTAND - die Abstufung traegt NICHTS.")
        print("       Die Positivkontrolle haelt, die Anlage ist also")
        print("       empfindlich genug. Damit ist belegt: die Unterschiede")
        print("       zwischen den unteren vier Fuenfteln sind RAUSCHEN.")
        print()
        print("       ⚠️ DAS IST KEINE MESSENTSCHEIDUNG FUER DEN UMBAU.")
        print("       Fuer den Schalter spricht die Sparsamkeit - eine")
        print("       unbelegte Behauptung weniger. Gegen ihn, dass kein")
        print("       GEWINN belegt ist. ➤ NUTZERENTSCHEIDUNG.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
