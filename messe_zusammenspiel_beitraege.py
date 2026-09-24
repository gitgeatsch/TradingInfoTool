# -*- coding: utf-8 -*-
"""Spielen `funding` und `turnover` korrekt zusammen? (24.09.2026)

Nutzerfrage: *„wir haben zwei Beitraege fuer die Hebelerstellung? es muessen
beide korrekt angewendet werden oder? und auch wie diese korrekt
zusammenspielen oder?"*

═══════════════════════════════════════════════════════════════════════
 DIE DREI TEILFRAGEN
═══════════════════════════════════════════════════════════════════════

1  WERDEN SIE ANGEWENDET?   Am Code beantwortet: `funding_fuenftel` und
   `turnover_fuenftel` tragen `instrumente=("spot",)`. Fuer
   `instrument="hebel"` gilt KEINER von beiden - die Quote steht dort
   konstant auf der Basisrate 0,3333, also exakt der Kelly-Nullstelle.

2  MESSEN SIE DASSELBE?     Wenn ja, ist die Addition eine Doppelzaehlung.
   Gemessen wird die Rangkorrelation ueber die gemeinsamen (Tag, Symbol).

3  ⭐ IST DIE ADDITION ZULAESSIG?  Das ist die eigentliche Frage. Die
   Rechnung lautet `q = basisrate + (f_punkte + t_punkte)/100` - eine
   REINE SUMME. Sie unterstellt, dass die Wirkung beider zusammen die
   Summe ihrer Einzelwirkungen ist.

   ➤ GEMESSEN WIRD DAS AN DER TATSAECHLICHEN QUOTE je Feld der
     5x5-Tafel: was die Formel vorhersagt gegen das, was eintritt.

⚠️ Das ist KEINE Beitragsmessung - es wird nicht gefragt, ob die beiden
tragen (das ist registriert). Gefragt wird, ob ihre VERKNUEPFUNG stimmt.

⚠️⚠️ NICHTS WIRD GEAENDERT. Reine Messung gegen die live registrierten
Stufen aus `wahrscheinlichkeit.BEITRAEGE`.

⚠️⚠️ DIE TURNOVER-QUELLE STEHT HIER FEST AUF `frei` - und das wird
benannt, weil eine fest gesetzte Quelle die gefaehrlichere Haelfte ist:
sie steht in keinem Aufruf und ist nur durch Codelesen zu finden.

    `_R3._zusatz("turnover", "frei")`  =  `umschlag_frei`

Es gibt hier also KEIN `--quelle` als Schalter - die Quelle ist fest, und
genau deshalb steht sie hier. Wer sie umstellen will, aendert diese Zeile
und liest zuerst den Absatz darunter.

`frei` ist seit dem 22.09. die LIVE-Groesse (S6, Nennerwechsel). Die
Vorgabe in `messe_bewertung_kalibrierung` bleibt dagegen `gesamt`, damit
der registrierte Befund reproduzierbar ist (R-R11) - hier wird aber die
LAUFENDE Verknuepfung geprueft, nicht ein alter Befund. Wer das aendert,
misst den abgeschalteten Nenner.

    python messe_zusammenspiel_beitraege.py
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertung_kalibrierung as MK                    # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_zielregel as ZR                                 # noqa: E402
from agent import wahrscheinlichkeit as W                    # noqa: E402

CRV = 2.0
NAME = "ZIEL 2,0"
MIND_FELD = 300          # weniger ist kein Feld, sondern ein Einzelfall


def _stufen(merkmal: str):
    for b in W.BEITRAEGE:
        if b.merkmal == merkmal and b.stufen:
            return tuple(b.stufen)
    return None


def main() -> int:
    print("=" * 96)
    print("SPIELEN `funding` UND `turnover` KORREKT ZUSAMMEN?")
    print("=" * 96)
    st_f, st_t = _stufen("funding_fuenftel"), _stufen("turnover_fuenftel")
    print("  funding_fuenftel  %s" % (st_f,))
    print("  turnover_fuenftel %s" % (st_t,))
    print("  Basisrate %.4f  ·  Kelly-Nullstelle %.4f"
          % (W.basisrate(CRV), 1.0 / (1.0 + CRV)))

    print()
    print("─" * 96)
    print("FRAGE 1 - WERDEN SIE UEBERHAUPT ANGEWENDET?")
    print("─" * 96)
    for inst in ("spot", "hebel"):
        r0 = W.rechne(crv=CRV, stop_relativ=0.06, gebuehr_je_seite=0.0015,
                      klasse="krypto", strategie="einstieg", richtung="LONG",
                      instrument=inst,
                      merkmale={"funding_fuenftel": 0, "turnover_fuenftel": 0})
        r4 = W.rechne(crv=CRV, stop_relativ=0.06, gebuehr_je_seite=0.0015,
                      klasse="krypto", strategie="einstieg", richtung="LONG",
                      instrument=inst,
                      merkmale={"funding_fuenftel": 4, "turnover_fuenftel": 4})
        spanne = r0["quote"] - r4["quote"]
        print("  %-6s bestes %.4f · schlechtestes %.4f · SPANNE %.4f  %s"
              % (inst, r0["quote"], r4["quote"], spanne,
                 "⛔ KEINE WIRKUNG" if abs(spanne) < 1e-9 else ""))

    print()
    print("  Daten laden...", flush=True)
    reihen = B.lade()
    zeilen = ZR.ergebnisse(reihen, mit_gleichstand=True, horizont=20)
    import phase3_reproduktion as _R3
    fu_roh = K.baue(reihen, "funding", F.lade_funding(), horizont=20)
    tu_roh = K.baue(reihen, "turnover", _R3._zusatz("turnover", "frei"),
                    horizont=20)
    fu5 = MK._fuenftel_je_tag(fu_roh)
    tu5 = MK._fuenftel_je_tag(tu_roh)

    # ---- die 5x5-Tafel: tatsaechliche Quote je Feld --------------------
    tafel = defaultdict(list)
    paare_f, paare_t = [], []
    for z in zeilen:
        if z[NAME] not in (-1.0, CRV):
            continue
        tag, sym = str(z["anker_tag"])[:10], z["sym"]
        f = (fu5.get(tag) or {}).get(sym)
        t = (tu5.get(tag) or {}).get(sym)
        if f is None or t is None:
            continue
        tafel[(f, t)].append(1 if z[NAME] == CRV else 0)
        paare_f.append(f)
        paare_t.append(t)

    print()
    print("─" * 96)
    print("FRAGE 2 - MESSEN SIE DASSELBE?")
    print("─" * 96)
    if len(paare_f) < 100:
        print("  ⛔ zu wenige gemeinsame Punkte (%d)" % len(paare_f))
        return 1
    r = float(np.corrcoef(paare_f, paare_t)[0, 1])
    print("  %s gemeinsame (Tag, Symbol)-Punkte"
          % f"{len(paare_f):,}".replace(",", "."))
    print("  Rangkorrelation der Fuenftel: r = %+.4f" % r)
    print("  %s" % ("⚠️ STARK korreliert - die Addition zaehlt doppelt"
                    if abs(r) > 0.5 else
                    "⚠️ maessig korreliert - Additivitaet ist zu pruefen"
                    if abs(r) > 0.25 else
                    "✔ weitgehend unabhaengig - die Addition ist plausibel"))

    # ---- Frage 3: stimmt die Vorhersage? -------------------------------
    print()
    print("─" * 96)
    print("FRAGE 3 - IST DIE ADDITION ZULAESSIG? (die 5x5-Tafel)")
    print("─" * 96)
    basis = W.basisrate(CRV)
    print("  f\\t      %s" % "".join("%14s" % ("t=%d" % t) for t in range(5)))
    fehler, gewicht = [], []
    for f in range(5):
        zeile = "  f=%d " % f
        for t in range(5):
            w = tafel.get((f, t)) or []
            if len(w) < MIND_FELD:
                zeile += "%14s" % "-"
                continue
            ist = float(np.mean(w))
            soll = basis + (st_f[f] + st_t[t]) / 100.0
            zeile += "%14s" % ("%.3f/%.3f" % (ist, soll))
            fehler.append(ist - soll)
            gewicht.append(len(w))
        print(zeile)
    print("  (IST / SOLL je Feld · Felder unter %d Ankern ausgelassen)"
          % MIND_FELD)

    if not fehler:
        print("  ⛔ kein Feld hat genug Anker")
        return 1
    fehler = np.array(fehler)
    gewicht = np.array(gewicht, float)
    mittel = float(np.average(fehler, weights=gewicht))
    print()
    print("  Felder mit genug Ankern: %d von 25" % len(fehler))
    print("  mittlerer Fehler (gewichtet)  %+.4f  (%+.2f Prozentpunkte)"
          % (mittel, 100 * mittel))
    print("  groesster Einzelfehler        %+.4f" % fehler[np.argmax(np.abs(fehler))])
    print("  Streuung der Fehler           %.4f" % fehler.std())

    # ⚠️⚠️ DIE SPREIZUNG IST DIE EIGENTLICHE PRUEFGROESSE, NICHT DER
    # MITTELWERT.
    #
    # Meine erste Fassung urteilte allein am mittleren Fehler mit der
    # Schwelle 0,02 - und haette einen Versatz von 1,74 Punkten als "✔"
    # ausgewiesen, obwohl die Formel die SPREIZUNG um Faktor 2 ueberschaetzt.
    # Ein Mittelwert kann stimmen, waehrend jede einzelne Vorhersage falsch
    # ist; genau das misst die Spreizung.
    ist_alle = np.array([float(np.mean(tafel[(f, t)]))
                         for f in range(5) for t in range(5)
                         if len(tafel.get((f, t)) or []) >= MIND_FELD])
    soll_alle = np.array([basis + (st_f[f] + st_t[t]) / 100.0
                          for f in range(5) for t in range(5)
                          if len(tafel.get((f, t)) or []) >= MIND_FELD])
    sp_ist = float(ist_alle.max() - ist_alle.min())
    sp_soll = float(soll_alle.max() - soll_alle.min())
    pos = int((fehler > 0).sum())
    print()
    print("  %d von %d Feldern liegen UEBER der Vorhersage" % (pos, len(fehler)))
    print()
    print("  SPREIZUNG ueber die Tafel")
    print("    tatsaechlich  %.4f  (%.1f Prozentpunkte)" % (sp_ist, 100 * sp_ist))
    print("    vorhergesagt  %.4f  (%.1f Prozentpunkte)" % (sp_soll, 100 * sp_soll))
    print("    Verhaeltnis   %.2f" % (sp_soll / max(1e-9, sp_ist)))
    # ⚠️ Die Ordnung getrennt von der Hoehe - eine Formel kann richtig
    # ordnen und trotzdem die falsche Zahl nennen (2.580).
    ordnung = float(np.corrcoef(ist_alle, soll_alle)[0, 1])
    print("    Ordnung (r)   %+.3f" % ordnung)
    print()
    if sp_soll / max(1e-9, sp_ist) > 1.5:
        print("  ⛔ DIE FORMEL UEBERSCHAETZT DIE SPREIZUNG um Faktor %.2f"
              % (sp_soll / sp_ist))
        print("     Die Stufen sind zu gross - dasselbe Bild wie 2.580")
        print("     (Ueberschaetzung Faktor 3) und wie die Kalibrierung")
        print("     (+0,040 statt +0,333).")
    elif abs(mittel) > 0.02:
        print("  ⛔ die Formel liegt im Mittel um mehr als 2 Punkte daneben")
    elif fehler.std() > 0.05:
        print("  ⚠️ im MITTEL richtig, je Feld aber stark streuend")
    else:
        print("  ✔ die Addition trifft die tatsaechliche Quote")
    if abs(mittel) > 0.01:
        print("  ⚠️ ZUSAETZLICH ein systematischer Versatz von %+.2f Punkten"
              % (100 * mittel))
    print()
    print("  ⚠️ Das prueft die VERKNUEPFUNG, nicht ob die Beitraege tragen.")
    print("     Und es gilt fuer SPOT - beim Hebel greift keiner von beiden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
