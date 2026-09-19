# -*- coding: utf-8 -*-
"""WIE VIELE FRAGEN KAEMEN BEIM MODELL AN? (19.09.2026, Schritt 59)

Die Anlass-Schwelle senkt das Volumen um 60 bis 89 % (2.465-volumen). Die
Frage, an der die Entscheidung haengt, ist aber eine andere:

    ⚠️ WIE VIELE ZELLEN ERREICHEN DAS MODELL, wenn die Wiederholungssperre
       entfaellt - und passt das unter das Tageskontingent von 500?

Zwischen `anlass` und dem Modellaufruf liegen `auswahl` und `terminmarkt`.

## ⚠️⚠️ EIN GESCHEITERTER ERSTER VERSUCH, UND WARUM ER HIER STEHT

Die erste Fassung wollte die Auswahlstufe NACHBAUEN (oberste 20 % nach
250-Tage-Momentum, wie in `phase3_kette`) und daraus je Zelle rechnen. Die
Probe gegen den Betrieb ist durchgefallen:

    nachgebaut  23,7 % kaemen durch
    beobachtet  60,6 % kamen durch

Der Nachbau war falsch, nicht der Betrieb. Zwei Gruende, beide im Code
nachgelesen:

    1. `agent/auswahl.py` waehlt **k = 2** (`GEMESSEN k:2`), nicht 20 %.
    2. Ein Wert MIT BESTAND passiert die Auswahl IMMER - dort steht die
       Verkaufsfrage an, und die haengt nicht am Rang.

⚠️ Nach der eigenen Regel ("ein Nachbau, der die beobachteten Zahlen nicht
trifft, darf nichts hochrechnen", R-R11) ist diese Spalte gestrichen. Was
bleibt, ist der DREISATZ mit den beobachteten Quoten - und die Annahme, die
er macht, wird geprueft statt geglaubt:

    ⚠️ HAENGT DIE ZAHL DER BEWEGTEN BLOECKE MIT DEM MOMENTUM-RANG ZUSAMMEN?
       Wenn nicht, siebt die Anlass-Schwelle QUER zur Auswahl, und die
       Durchlassquote bleibt fuer die kleinere Menge dieselbe.

⚠️ `terminmarkt` verwirft im gemessenen Fenster NICHTS (die Quelle ist seit
02.09. eingefroren, 2.452) - die Stufe wird als durchlaessig gefuehrt und
das ausgewiesen, nicht stillschweigend weggelassen.

⚠️ Nur lesend gegen die Tagessicherung. Kein LLM.
"""
from __future__ import annotations

import collections
import json
import sys
import time

import numpy as np

import phase3_anlass as PA
import phase3_takt as T
from messe_beitrag_auf_auswahl import momentum250

def _kontingent() -> int:
    """Das TAGESKONTINGENT der Rollen-Kette - aus der echten Leiter gerechnet.

    ⚠️⚠️ HIER STAND `500`, UND DAS WAR FALSCH (korrigiert 19.09.2026, noch am
    selben Tag). 500 ist der ERSTE Topf (`gemini-3.1-flash-lite`); die Kette
    hat vier, und sie nutzt jeden bis 90 % seiner Grenze:

        gemini-3.1-flash-lite   500 ->  450
        gemini-3.5-flash-lite   500 ->  450
        openrouter            1.000 ->  900
        groq                     83 ->   74
                                      -----
                                       1.874

    Mit der falschen Zahl stand in der ersten Fassung ,das Vierfache des
    Kontingents` - tatsaechlich ist es das 1,2-Fache. Die Empfehlung, die
    daraus folgte, waere eine andere gewesen.

    ⚠️ GERECHNET, NICHT ABGESCHRIEBEN: die Leiter kommt aus
    `scheduler.rollen_job`. Eine Kopie hier waere die naechste Stelle zum
    Auseinanderlaufen - genau der Fehler, den diese Korrektur behebt."""
    from scheduler.rollen_job import KETTE, RESERVE_ANTEIL
    return sum(int(b * (1.0 - RESERVE_ANTEIL)) for _q, _m, b in KETTE)


KONTINGENT = _kontingent()
QUER_GRENZE = 0.05        # ab hier gilt die Siebung nicht mehr als quer
VORBEHALT = ("HOCHRECHNUNG, KEINE MESSUNG: beobachtete Quoten aus 8 Tagen auf "
             "eine kleinere Menge uebertragen - und `terminmarkt` verwirft im "
             "Fenster nichts (eingefrorene Quelle, 2.452)")


def beobachtete_quoten(con) -> dict:
    """Was der Betrieb je Stufe wirklich durchgelassen hat (8 Tage)."""
    best = collections.Counter()
    verl = collections.Counter()
    for (roh,) in con.execute(
            "SELECT daten_json FROM gate_durchlaessigkeit"
            " WHERE erfasst_am >= '2026-09-11' AND lauf = 'rollen'"):
        try:
            d = json.loads(roh)
        except Exception:
            continue
        for k, v in (d.get("bestanden") or {}).items():
            best[k] += int(v or 0)
        for k, v in (d.get("verloren") or {}).items():
            verl[k] += int(v or 0)
    aus = {}
    for stufe in ("anlass", "auswahl", "terminmarkt", "wiederholung"):
        hinein = best.get(stufe, 0) + verl.get(stufe, 0)
        aus[stufe] = {"hinein": hinein, "bestanden": best.get(stufe, 0),
                      "quote": (best.get(stufe, 0) / hinein) if hinein else 0.0}
    return aus


def rangplatz_je_tag(reihen: dict) -> dict:
    """tag -> {symbol: Rangplatz 0..1}, 0 ist der beste.

    ⚠️ DIESELBE GROESSE WIE IN DER KETTE (`momentum250`), nur als PLATZ
    statt als Menge - hier geht es nicht darum, wer gewinnt, sondern ob die
    beiden Siebe ueberhaupt dieselbe Richtung kennen."""
    aus = {}
    for tag, werte in momentum250(reihen).items():
        if len(werte) < 5:
            continue
        sortiert = sorted(werte.items(), key=lambda x: -x[1])
        n = len(sortiert)
        aus[tag] = {s: i / (n - 1) for i, (s, _w) in enumerate(sortiert)}
    return aus


def quer(beob: list, rang: dict) -> tuple:
    """Siebt die Anlass-Schwelle quer zur Auswahl? (Korrelation, Paare)."""
    paare = [(len(b["geaenderte_bloecke"]),
              (rang.get(b["zeit"].date().isoformat()) or {}).get(b["symbol"]))
             for b in beob]
    paare = [(a, r) for a, r in paare if r is not None]
    if len(paare) < 500:
        return None, paare
    x = np.array([p[0] for p in paare], float)
    y = np.array([p[1] for p in paare], float)
    return float(np.corrcoef(x, y)[0, 1]), paare


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("HOCHRECHNUNG BIS ZUM MODELL - passt es unter das Kontingent?")
    print("=" * 100)
    print("  ⚠️ %s" % VORBEHALT)
    con = T._oeffne_sicherung()

    q = beobachtete_quoten(con)
    print("\n  DIE BEOBACHTETEN QUOTEN (8 Tage Betrieb)")
    print("     %-14s %9s %11s %9s" % ("Stufe", "hinein", "bestanden", "Quote"))
    for stufe in ("anlass", "auswahl", "terminmarkt", "wiederholung"):
        d = q[stufe]
        print("     %-14s %9d %11d %8.1f %%"
              % (stufe, d["hinein"], d["bestanden"], 100.0 * d["quote"]))

    beob = PA.lade_beobachtungen(con)
    tage = len({b["zeit"].date() for b in beob})
    print("\n  %d Beobachtungen ueber %d Tage" % (len(beob), tage))

    # ---- DIE ANNAHME, AUF DER DER DREISATZ STEHT -------------------------
    print("\n  DIE ANNAHME - siebt der Anlass QUER zur Auswahl?")
    import messe_eigenschaft_beitrag as B
    rang = rangplatz_je_tag(B.lade("krypto", "V1"))
    r, paare = quer(beob, rang)
    if r is None:
        print("     zu wenige Paare (%d) - die Annahme bleibt UNGEPRUEFT"
              % len(paare))
    else:
        x = np.array([p[0] for p in paare], float)
        y = np.array([p[1] for p in paare], float)
        print("     %d Paare (bewegte Bloecke gegen Rangplatz 0..1)" % len(paare))
        for schwelle in (1, 2, 3):
            m = x >= schwelle
            if m.sum() > 100 and (~m).sum() > 100:
                print("        ab %d Bloecken: mittlerer Rangplatz %.3f gegen"
                      " %.3f darunter"
                      % (schwelle, float(y[m].mean()), float(y[~m].mean())))
        print("     Korrelation %+.4f  ->  %s"
              % (r, "QUER, der Dreisatz haelt" if abs(r) < QUER_GRENZE
                 else "⚠️ NICHT quer - der Dreisatz verschiebt sich"))

    # ---- DER DREISATZ ----------------------------------------------------
    print("\n  WIE VIELE ZELLEN ERREICHEN DAS MODELL - OHNE WIEDERHOLUNGSSPERRE")
    print("     %-34s %12s %13s %11s"
          % ("Einstellung", "Fragen/Tag", "beim Modell", "Kontingent"))
    for name, ign, mind in PA.VARIANTEN:
        frei = ~PA.sperrt_maske(beob, ign, mind)
        je_tag = int(frei.sum()) / max(tage, 1)
        beim_modell = je_tag * q["auswahl"]["quote"] * q["terminmarkt"]["quote"]
        print("     %-34s %12.0f %13.0f %11s"
              % (name, je_tag, beim_modell,
                 "passt" if beim_modell <= KONTINGENT else "⚠️ zu viel"))
    from scheduler.rollen_job import KETTE as _K, RESERVE_ANTEIL as _R
    print("\n     Kontingent: %d nutzbare Modellaufrufe je Tag ueber VIER Toepfe"
          % KONTINGENT)
    print("        " + " · ".join("%s %d" % (m or q, int(b * (1.0 - _R)))
                                  for q, m, b in _K))
    print("     Heute mit Sperre: %.0f je Tag (Quote der Sperre %.1f %%)"
          % (q["wiederholung"]["bestanden"] / 8.0,
             100.0 * q["wiederholung"]["quote"]))

    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 100)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
