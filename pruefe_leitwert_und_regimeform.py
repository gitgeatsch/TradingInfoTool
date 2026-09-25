# -*- coding: utf-8 -*-
"""Vier Gegenpruefungen fuer den BTC-Leitwert und die Regime-Messform

**25.09.2026**, Nutzervorgabe: *"gut pruefen und gegenpruefen"*.

Die Regime-Messung (Schritt 3) steht auf vier Annahmen, die bisher nur
BEHAUPTET sind. Jede wird hier am Seiteneffekt geprueft, nicht am Docstring.

═══════════════════════════════════════════════════════════════════════
 P1  IST DER NEU GELADENE LEITWERT DERSELBE BTC?
═══════════════════════════════════════════════════════════════════════

    `btc_leitwert.db` wurde am 25.09. frisch von Binance geholt.
    `stundenkurse.db` hat BTC ab 2023-09. Im UEBERLAPPENDEN Zeitraum
    muessen beide BITGLEICH sein - gleiche Quelle, gleiches Symbol,
    gleiche Aufloesung.

    ⚠️ Waere das nicht so, waere jede Regime-Messung auf einer anderen
    BTC-Reihe gelaufen als die Messbasis - und niemand haette es gemerkt,
    weil beide fuer sich stimmig aussehen (vgl. die Grundgesamtheits-Regel).

═══════════════════════════════════════════════════════════════════════
 P2  IST `btc_trend` STRENG KAUSAL?
═══════════════════════════════════════════════════════════════════════

    Der Wert zur Stunde t darf nur Kurse <= t nutzen. Geprueft wird am
    SEITENEFFEKT: die Zukunft wird VERAENDERT, und der Wert bei t muss
    unveraendert bleiben. Ein Blick nach vorn wuerde sich sofort zeigen.

═══════════════════════════════════════════════════════════════════════
 P3  BRICHT DIE ZYKLISCHE VERSCHIEBUNG DEN ZUSAMMENHANG?
═══════════════════════════════════════════════════════════════════════

    Die Nullwelt verschiebt das Merkmal gegen die Ausgaenge. Wenn die
    Verschiebung zu klein ist, bleibt ein Restzusammenhang und das Band
    ist zu eng. Geprueft wird die Korrelation Original gegen verschoben
    ueber den tatsaechlich verwendeten Versatzbereich.

═══════════════════════════════════════════════════════════════════════
 P4  NUTZT DAS KAUSALE FUENFTEL WIRKLICH NUR VERGANGENHEIT?
═══════════════════════════════════════════════════════════════════════

    Selbstprobe mit BEKANNTER Wahrheit: bei einer streng monoton
    STEIGENDEN Reihe ist jeder neue Wert der hoechste bisher gesehene.
    Ein korrekt kausales Fuenftel muss deshalb fast immer 4 sein. Ein
    rueckschauendes Fuenftel waere dagegen gleichmaessig auf 0..4
    verteilt.

⚠️ NUR LESEN.

    python pruefe_leitwert_und_regimeform.py
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from messe_regime_rollierend import (                           # noqa: E402
    _tage_mittel, _fuenftel_kausal, _fuenftel_rueckschau,
    LEITWERT, MIND_VERSATZ)

MESSBASIS = os.path.join("data", "stundenkurse.db")
ROT: list = []


def _melde(nr: str, frage: str, ok: bool, text: str) -> None:
    print("  %-5s %-52s %s" % (nr, frage, "OK" if ok else "⛔ FEHL"))
    print("        %s" % text)
    if not ok:
        ROT.append(nr)


def p1_bitgleich() -> None:
    if not os.path.exists(LEITWERT):
        _melde("P1", "Leitwert gegen Messbasis bitgleich", False,
               "%s fehlt" % LEITWERT)
        return
    a = sqlite3.connect("file:%s?mode=ro" % LEITWERT, uri=True)
    b = sqlite3.connect("file:%s?mode=ro" % MESSBASIS, uri=True)
    la = dict((r[0], r[1:]) for r in a.execute(
        "SELECT stunde, open, high, low, close, volumen FROM leitwert "
        "WHERE symbol='BTC'"))
    lb = dict((r[0], r[1:]) for r in b.execute(
        "SELECT stunde, open, high, low, close, volumen FROM stundenkurse "
        "WHERE symbol='BTC'"))
    a.close(); b.close()
    gemeinsam = sorted(set(la) & set(lb))
    if not gemeinsam:
        _melde("P1", "Leitwert gegen Messbasis bitgleich", False,
               "kein ueberlappender Zeitraum")
        return
    # ⚠️⚠️ DIE LETZTE STUNDE DER MESSBASIS WIRD AUSGENOMMEN - und zwar
    # BEGRUENDET, nicht um die Pruefung gruen zu machen: `hole_stundenkurse`
    # speichert die LAUFENDE Stunde als abgeschlossene Kerze. Gemessen am
    # 25.09. fuer BTC 2026-09-24 15:00: `open` und `low` stimmen (83673,77 /
    # 83508,00), aber `high` 84100,01 gegen 84468,01 und das Volumen 481
    # gegen 1011 - die halbe Stunde. Dieselbe Kerze, zu verschiedenen
    # Zeitpunkten gelesen.
    #
    # ➤ Das ist ein eigener Befund und wird als P5 GEMESSEN, nicht hier
    # versteckt. Bliebe die Stunde drin, waere P1 dauerhaft rot und die
    # eigentliche Frage - ist es derselbe BTC? - unbeantwortbar.
    letzte_mb = max(lb)
    pruefmenge = [s for s in gemeinsam if s != letzte_mb]
    abweichend = [s for s in pruefmenge if la[s] != lb[s]]
    # ⚠️ Nicht nur die Zahl der Abweichungen, auch ihre GROESSE - eine
    # Rundung in der letzten Stelle ist etwas anderes als ein anderer Kurs.
    groesste = 0.0
    for s in abweichend:
        for x, y in zip(la[s], lb[s]):
            if x and y:
                groesste = max(groesste, abs(x - y) / max(abs(y), 1e-12))
    _melde("P1", "Leitwert gegen Messbasis bitgleich",
           not abweichend,
           "%d gemeinsame Stunden (%s bis %s), ohne die letzte "
           "(offene Kerze, siehe P5) · %d abweichend%s"
           % (len(pruefmenge), pruefmenge[0], pruefmenge[-1], len(abweichend),
              " · groesste relative Abweichung %.2e" % groesste
              if abweichend else ""))
    # Zusatzauskunft: wie viel bringt der Leitwert ueberhaupt?
    nur_leit = sorted(set(la) - set(lb))
    print("        ⭐ Der Leitwert bringt %d Stunden ZUSAETZLICH%s"
          % (len(nur_leit),
             " (%s bis %s)" % (nur_leit[0], nur_leit[-1]) if nur_leit else ""))


def p2_kausal() -> None:
    """Wird die Zukunft veraendert, darf der Wert bei t sich nicht ruehren."""
    rng = np.random.default_rng(7)
    x = 100.0 + np.cumsum(rng.standard_normal(3000))
    a = _tage_mittel(x, 30)
    y = x.copy()
    t = 2000
    y[t + 1:] *= 5.0                    # die Zukunft massiv veraendern
    b = _tage_mittel(y, 30)
    gleich = np.allclose(a[:t + 1], b[:t + 1], equal_nan=True)
    spaeter = not np.allclose(a[t + 1:], b[t + 1:], equal_nan=True)
    _melde("P2", "`_tage_mittel` ist streng kausal", gleich and spaeter,
           "bis t unveraendert: %s · nach t veraendert: %s "
           "(ohne das Zweite wuerde die Probe nichts pruefen)"
           % (gleich, spaeter))


def p3_verschiebung() -> None:
    """Bleibt nach dem Mindestversatz ein Restzusammenhang?"""
    rng = np.random.default_rng(11)
    T = 42000
    reihe = _tage_mittel(rng.standard_normal(T), 30)
    gut = np.isfinite(reihe)
    w = reihe[gut]
    korr = []
    for v in (24, 7 * 24, 30 * 24, MIND_VERSATZ, 180 * 24):
        r = np.roll(w, v % len(w))
        korr.append((v // 24, abs(float(np.corrcoef(w, r)[0, 1]))))
    bei_mind = dict(korr)[MIND_VERSATZ // 24]
    _melde("P3", "zyklische Verschiebung bricht den Zusammenhang",
           bei_mind < 0.10,
           "|Korrelation| je Versatz: %s · bei %d Tagen %.4f"
           % (" ".join("%dT=%.3f" % (t, k) for t, k in korr),
              MIND_VERSATZ // 24, bei_mind))


def p4_fuenftel() -> None:
    """Selbstprobe mit bekannter Wahrheit auf einer MONOTONEN Reihe."""
    n = 60000
    w = np.arange(n, dtype=float)               # streng monoton steigend
    stunde = np.arange(n, dtype=np.int64)
    f_k = _fuenftel_kausal(w, stunde)
    f_r = _fuenftel_rueckschau(w)
    gilt = f_k >= 0
    anteil4 = float((f_k[gilt] == 4).mean()) if gilt.any() else 0.0
    # Rueckschau muss dagegen gleichmaessig verteilt sein
    verteilt = np.bincount(f_r, minlength=5) / len(f_r)
    _melde("P4", "kausales Fuenftel sieht nur die Vergangenheit",
           anteil4 > 0.95 and abs(verteilt.max() - 0.2) < 0.02,
           "monoton steigende Reihe: kausal %.1f %% in Fuenftel 4 "
           "(muss ~100 %% sein) · Rueckschau %s (muss ~20 %% je Fuenftel sein)"
           % (100 * anteil4,
              "/".join("%.0f%%" % (100 * v) for v in verteilt)))


def p5_offene_kerze() -> None:
    """Ist die LETZTE Kerze je Symbol systematisch unvollstaendig?

    ⚠️ Der Grund, warum P1 die letzte Stunde ausnimmt - hier wird er
    gemessen statt vorausgesetzt. `hole_stundenkurse` schreibt die laufende
    Stunde als abgeschlossene Kerze, und weil die Wiederaufnahme bei
    `MAX(stunde)` ansetzt und `INSERT OR IGNORE` nutzt, wird sie NIE
    korrigiert.

    ⚠️⚠️ Fuer die MESSUNG ist das belanglos (`ausgaenge` schliesst die
    letzten Anker ohnehin aus). Fuer den BETRIEB ist es die WICHTIGSTE
    Kerze - die aktuelle Lage, auf der ein Signal entsteht.
    """
    if not os.path.exists(MESSBASIS):
        return
    c = sqlite3.connect("file:%s?mode=ro" % MESSBASIS, uri=True)
    quoten = []
    for (sym,) in c.execute("SELECT DISTINCT symbol FROM stundenkurse"):
        r = c.execute("SELECT volumen FROM stundenkurse WHERE symbol=? "
                      "ORDER BY stunde DESC LIMIT 101", (sym,)).fetchall()
        if len(r) < 50:
            continue
        letzte, rest = r[0][0], [x[0] for x in r[1:] if x[0]]
        if not rest or not letzte:
            continue
        quoten.append(letzte / float(np.median(rest)))
    c.close()
    if not quoten:
        return
    q = np.array(quoten)
    verd = int((q < 0.6).sum())
    # Diese Pruefung ist eine MELDUNG, kein Urteil: sie ist absichtlich so
    # gestellt, dass sie den Zustand beschreibt. Rot wird sie erst, wenn der
    # Median unter 0,5 faellt - dann ist mehr als die halbe letzte Stunde weg.
    _melde("P5", "letzte Kerze je Symbol ist vollstaendig",
           float(np.median(q)) >= 0.5,
           "%d von %d Symbolen unter 60 %% des Median-Volumens (%.0f %%) · "
           "Median der Quote %.3f (1,0 = vollstaendig) · Quartile %.2f/%.2f/%.2f"
           % (verd, len(q), 100.0 * verd / len(q), float(np.median(q)),
              *np.percentile(q, [25, 50, 75])))
    print("        ⚠ BETRIFFT DEN BETRIEB, nicht die Messung: `ausgaenge`")
    print("           schliesst die letzten Anker aus, aber im Betrieb ist die")
    print("           letzte Kerze die AKTUELLE Lage. Behebbar mit INSERT OR")
    print("           REPLACE fuer die jeweils letzte Stunde.")


def main() -> int:
    print("=" * 100)
    print("GEGENPRUEFUNG: BTC-Leitwert und Regime-Messform")
    print("=" * 100)
    p1_bitgleich()
    p2_kausal()
    p3_verschiebung()
    p4_fuenftel()
    p5_offene_kerze()
    print()
    print("=" * 100)
    if ROT:
        print("⛔ %d von 5 FEHLGESCHLAGEN: %s" % (len(ROT), ", ".join(ROT)))
        print("   ⚠️ Solange eine dieser Pruefungen rot ist, gilt KEIN")
        print("      Ergebnis der Regime-Messung.")
        return 1
    print("✔✔ alle 5 Gegenpruefungen bestanden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
