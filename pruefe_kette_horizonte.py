# -*- coding: utf-8 -*-
"""Auf welchem Horizont ist jede Stufe begruendet - und worauf wirkt sie?
(03.09.2026)

## Der Anlass

Nutzerauftrag nach der Hebel-Bestandsaufnahme: *„pruefe die bestehende
Kette - beruecksichtige dabei deine Erkenntnisse, damit wir nicht einfach
punktuell aendern und an anderer Stelle Fehler erzeugen."*

Die Erkenntnis aus F-185 ist eine **Brille**, keine Einzelstelle: die
Beitraege sind auf **H20** kalibriert. Diese Datei fragt sie fuer die
ganze Kette ab.

## ⚠️ Die Frage, praezise gestellt

Nicht *„wie lange haelt der Nutzer eine Position"* - die Kette handelt
nicht, und eine Bestandshistorie gibt es nicht (F-183). Sondern:

> **Wie lange dauert es, bis ein Signal an einer seiner beiden Barrieren
> entschieden ist?** Das ist der Zeitraum, ueber den die Bewertung eine
> Aussage machen muesste.

⚠️ **Und der Zeitraum ist eine FOLGE der Geometrie, keine unabhaengige
Groesse.** Ein enger Stop endet frueher. Die Kette waehlt ueber den Stop
also implizit ihren Horizont - und bewertet dann mit Groessen, die auf
einem anderen gemessen sind.

## ⚠️ Was diese Messung NICHT sagt

Die Beitragsmessung ist **barrierefrei** (Ertrag nach H Tagen), die Kette
hat **TP und SL**. Ein barrierefreier H20-Ertrag und ein Trade, der nach
zwei Tagen an einer Barriere endet, sind nicht dasselbe. Die Zahl hier
belegt, dass der WIRKUNGSZEITRAUM kurz ist - sie ersetzt nicht die
Messung der Beitraege auf kurzen Horizonten. Die liegt seit dem 31.08.
vor und steht unten zum Vergleich.

    python pruefe_kette_horizonte.py [--db PFAD]
"""
import argparse
import statistics as st
import sys
from datetime import date

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Die am 31.08. gemessene Wirkung je Horizont (`messe_kandidaten_als_regel.py
# --horizonte 1,2,3,5,10,20`, 523 Reihen). ⚠️ ABGESCHRIEBEN, nicht gerechnet -
# deshalb steht die Quelle dabei und die Suite prueft sie nicht auf
# Aktualitaet. Wer sie neu misst, traegt sie hier nach.
WIRKUNG_JE_HORIZONT = {1: (0.0019, 0.0044), 2: (0.0026, 0.0107),
                       20: (0.0246, 0.0616)}

# Worauf jede Stufe begruendet ist. Aus dem Code und den Messdokumenten
# zusammengetragen, mit Fundstelle - damit die Tabelle nachpruefbar ist.
STUFEN = [
    ("auftrag", "Instrument/Strategie-Paar", "—", "keine Messgroesse"),
    ("fakten", "Datenlage vorhanden", "—", "keine Messgroesse"),
    ("lagebild", "Marktlage (LLM)", "—", "keine Messgroesse"),
    ("anlass", "Alter des Faktensatzes in Stunden", "—",
     "Mengenregel, kein Horizont - ⚠️ und ein FAKT, keine Bewertung"),
    ("auswahl", "Rang nach 250-Handelstage-Entwicklung", "H5 und H20",
     "auswahl.GEMESSEN: H5 +0,79 % (t 3,29) · H20 +2,74 % (t 4,52)"),
    ("terminmarkt", "OI-Aufbau, oberstes Fuenftel", "H20",
     "F-168 - ⚠️ greift im Betrieb ohnehin nie (F-180)"),
    ("wiederholung", "Cooldown in Stunden", "—",
     "⚠️ NIE gegen Ergebnisse gemessen - Mengenbremse ohne Qualitaetsaussage"),
    ("urteil", "Modellurteil", "—", "keine Messgroesse"),
    ("aktion", "Handlung gegen Bestand plausibel", "—", "Konsistenzregel"),
    ("geometrie", "Stop und CRV", "—",
     "⚠️ bestimmt die HALTEDAUER und damit den Horizont"),
    ("risikoschicht", "Risikobetrag", "—", "Kapitalregel"),
    ("entscheider", "Potential gegen Schwelle", "H20",
     "⚠️⚠️ Beitraege H20-kalibriert, Schwelle fuer H20 gesetzt"),
]


def dauern(db):
    """Tage von der Erstellung bis TP/SL, je Ausgang.

    ⚠️ `outcome_entschieden_am` ist ein TAGESdatum, `created_at` ein
    Zeitstempel mit Zone. Die Differenz wird deshalb auf Tagesebene
    gebildet - `0` heisst "noch am selben Tag". Meine erste Fassung zog
    die Zeitstempel direkt voneinander ab und bekam bei jedem Wert eine
    Ausnahme (naiv gegen zonenbehaftet), die im Sammelfang verschwand:
    das Ergebnis war "keine entschiedenen Trades" bei 239 vorhandenen.
    """
    import sqlite3
    aus = {}
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    for lab, status in (("Take Profit", "take_profit_erreicht"),
                        ("Stop Loss", "stop_loss_erreicht")):
        w = []
        for a, b in c.execute(
                "SELECT created_at, outcome_entschieden_am FROM signals "
                "WHERE quelle_kette='rollen' AND outcome_status=?",
                (status,)):
            try:
                t = (date.fromisoformat(str(b)[:10])
                     - date.fromisoformat(str(a)[:10])).days
            except Exception:                                # noqa: BLE001
                continue
            if 0 <= t < 400:
                w.append(t)
        if w:
            aus[lab] = sorted(w)
    return aus


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    a = p.parse_args()

    print("=" * 78)
    print("1) WORAUF JEDE STUFE BEGRUENDET IST")
    print("=" * 78)
    print("  %-14s %-34s %-9s" % ("Stufe", "Groesse", "Horizont"))
    for name, groesse, hor, quelle in STUFEN:
        print("  %-14s %-34s %-9s" % (name, groesse[:34], hor))
        if quelle and not quelle.startswith("keine"):
            print("  %-14s   %s" % ("", quelle))

    print()
    print("=" * 78)
    print("2) WIE LANGE LAEUFT EIN SIGNAL WIRKLICH?")
    print("=" * 78)
    d = dauern(a.db)
    if not d:
        print("  ⚠️ keine entschiedenen Trades in %s" % a.db)
        print("     (am Desktop erwartet - die Produktions-DB liegt am NB)")
        return 0
    alle = sorted(x for w in d.values() for x in w)
    for lab, w in d.items():
        print("  %-12s n=%3d · Median %4.1f Tage · Mittel %4.1f · max %d"
              % (lab, len(w), st.median(w), st.mean(w), w[-1]))
    print("  %-12s n=%3d · Median %4.1f Tage · Mittel %4.1f"
          % ("ZUSAMMEN", len(alle), st.median(alle), st.mean(alle)))
    print()
    for g in (1, 2, 3, 5, 10, 20):
        k = sum(1 for x in alle if x <= g)
        print("     entschieden binnen %2d Tagen: %3.0f %%  (%d von %d)"
              % (g, 100 * k / len(alle), k, len(alle)))

    print()
    print("=" * 78)
    print("3) DER ABGLEICH — kalibriert gegen wirksam")
    print("=" * 78)
    med = st.median(alle)
    print("  Die Beitraege sind auf H20 kalibriert. Gemessen am 31.08.:")
    print("     %-6s %-12s %-12s" % ("H", "Funding", "Turnover"))
    for h in sorted(WIRKUNG_JE_HORIZONT):
        f, t = WIRKUNG_JE_HORIZONT[h]
        marke = "  <- hier wirkt sie" if h <= med + 0.5 else ""
        print("     %-6d %+.4f      %+.4f%s" % (h, f, t, marke))
    f20, t20 = WIRKUNG_JE_HORIZONT[20]
    nah = min(WIRKUNG_JE_HORIZONT, key=lambda h: abs(h - med))
    f_n, t_n = WIRKUNG_JE_HORIZONT[nah]
    print()
    print("  Median-Dauer %.1f Tage -> naechster gemessener Horizont H%d"
          % (med, nah))
    print("  Funding  H%-2d %+.4f gegen H20 %+.4f  =  Faktor %.1f"
          % (nah, f_n, f20, f20 / f_n if f_n else float("inf")))
    print("  Turnover H%-2d %+.4f gegen H20 %+.4f  =  Faktor %.1f"
          % (nah, t_n, t20, t20 / t_n if t_n else float("inf")))
    print()
    print("  ⚠️⚠️ Die Kette entscheidet ihre Signale auf einem Horizont, auf")
    print("     dem die Bewertung ein Bruchteil ihrer kalibrierten Wirkung")
    print("     hat - und die Schwelle stammt aus der H20-Welt (R-R9).")
    print()
    print("  ⚠️ KEIN Vorwurf an eine einzelne Stufe. Der Horizont ist eine")
    print("     FOLGE der Geometrie: ein enger Stop endet frueher. Wer die")
    print("     Schwelle allein anfasst, verschiebt das Problem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
