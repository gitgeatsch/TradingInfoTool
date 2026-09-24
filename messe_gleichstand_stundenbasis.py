# -*- coding: utf-8 -*-
"""P-9 auf der STUNDENBASIS: was kostet die Gleichstandsregel?

Nutzerauftrag 24.09.2026: *„ja Stundenbasis zuerst - pruefen und gegenpruefen"*

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE - und warum sie am Hebel haengt
═══════════════════════════════════════════════════════════════════════

In `messe_zielregel.ergebnisse()` steht eine Zeile:

    if stop_tag <= ziel_tag and stop_tag < H:
        zeile[name] = -1.0          # Stop gewinnt bei Gleichstand

Werden Ziel UND Stop am SELBEN TAG beruehrt, zaehlt der Stop. Auf
TAGESdaten ist die Reihenfolge unbekannt - die Regel ist also die
vorsichtige Annahme und war richtig, solange es nur Tagesdaten gab.

⚠️⚠️ ABER SIE IST SYSTEMATISCH PESSIMISTISCH, und `q` - die
Barrieren-Trefferquote, aus der ueber Kelly der GANZE Hebel entsteht - ist
genau diese Zahl. Ein zu niedriges `q` heisst: zu wenig Hebel, oder gar
keiner. Die Kelly-Nullstelle liegt bei 0,3333, gemessen wurden 31,3 %.

    ⭐ DIE GEMESSENE QUOTE LIEGT 2,0 PUNKTE UNTER DER NULLSTELLE.
       Wenn die Gleichstandsregel davon einen Teil erklaert, ist das
       nicht irgendein Detail - es ist der Unterschied zwischen
       "kein Hebel" und "Hebel".

➤ Seit dem 24.09. liegen 3.244.186 STUNDENkerzen vor (116 Symbole,
2021-12 bis heute). Auf ihnen IST die Reihenfolge aufloesbar.

═══════════════════════════════════════════════════════════════════════
 ⚠️ CHIRURGISCH - was eindeutig ist, bleibt bitgleich
═══════════════════════════════════════════════════════════════════════

Nur die MEHRDEUTIGEN Anker werden stuendlich nachgerechnet. Alles andere
bleibt Zeichen fuer Zeichen die Tagesrechnung. Damit ist jede Aenderung
zuordenbar - und R-R11 bleibt gewahrt, statt nachtraeglich behauptet zu
werden.

═══════════════════════════════════════════════════════════════════════
 DIE ZWEI GEGENPRUEFUNGEN - sie laufen IMMER mit
═══════════════════════════════════════════════════════════════════════

A  DER SCHALTER IST UNSCHAEDLICH. `ergebnisse(reihen)` und
   `ergebnisse(reihen, mit_gleichstand=True)` muessen in JEDEM
   gemeinsamen Schluessel bitgleich sein. 44 Skripte rufen diese
   Funktion; ein Nachweis am Quelltext ("steht ja hinter einem if")
   waere genau die Sorte Beleg, die dieses Projekt schon zweimal
   getaeuscht hat.

B  DIE STUNDENRECHNUNG STIMMT. Fuer eine Stichprobe EINDEUTIGER Anker
   muss die stuendliche Aufloesung DASSELBE Ergebnis liefern wie die
   Tagesrechnung. Ohne diese Probe misst man den eigenen Fehler.

    python messe_gleichstand_stundenbasis.py
    python messe_gleichstand_stundenbasis.py --symbole 30   # Probelauf
"""
from __future__ import annotations

import os
import sqlite3
import sys
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_zielregel as ZR                                 # noqa: E402

STUNDEN_DB = os.path.join("data", "stundenkurse.db")
CRV = 2.0
NAME = "ZIEL 2,0"          # die Variante, aus der `q` entsteht
PROBE_B = 400              # Stichprobe fuer Gegenpruefung B


def _stunden(symbol: str) -> dict:
    """Alle Stundenkerzen eines Symbols, nach Kalendertag gebuendelt."""
    c = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    try:
        rows = c.execute(
            "SELECT stunde, high, low FROM stundenkurse "
            "WHERE symbol=? ORDER BY stunde", (symbol,)).fetchall()
    except sqlite3.Error:
        rows = []
    c.close()
    aus = defaultdict(list)
    for stunde, hi, lo in rows:
        aus[stunde[:10]].append((hi, lo))
    return aus


def _wer_zuerst(kerzen: list, stop: float, ziel: float):
    """Welche Barriere kommt zuerst? 'ziel' | 'stop' | 'unklar' | None.

    ⚠️ `unklar` bleibt uebrig: beruehrt EINE STUNDE beide Schwellen, ist
    die Reihenfolge auch hier unbekannt. Diese Faelle werden AUSGEWIESEN,
    nicht stillschweigend einer Seite zugeschlagen - sonst ersetzt man
    eine Annahme durch eine andere und nennt es Messung.
    """
    for hi, lo in kerzen:
        traf_z, traf_s = hi >= ziel, lo <= stop
        if traf_z and traf_s:
            return "unklar"
        if traf_z:
            return "ziel"
        if traf_s:
            return "stop"
    return None                      # der Tag beruehrt gar nichts


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 92)
    print("P-9 AUF DER STUNDENBASIS - was kostet die Gleichstandsregel?")
    print("=" * 92)
    reihen = B.lade()
    if grenze:
        reihen = {k: reihen[k] for k in list(reihen)[:grenze]}
    print("  %d Krypto-Reihen · CRV %.1f · Horizont %d Tage"
          % (len(reihen), CRV, ZR.HORIZONT))

    print("\n  Barrieren rechnen (mit Gleichstandsmeldung)...", flush=True)
    mit = ZR.ergebnisse(reihen, mit_gleichstand=True)
    print("  Barrieren rechnen (Vorgabe, fuer Gegenpruefung A)...", flush=True)
    ohne = ZR.ergebnisse(reihen)

    # ───────────────────────── GEGENPRUEFUNG A ─────────────────────────
    print()
    print("─" * 92)
    print("GEGENPRUEFUNG A - ist der Schalter unschaedlich?")
    print("─" * 92)
    if len(mit) != len(ohne):
        print("  ⛔ ROT: %d Zeilen gegen %d - der Schalter aendert die MENGE"
              % (len(mit), len(ohne)))
        return 1
    neu = {"gleichstand", "anker_tag", "entscheid_tag", "stop_kurs",
           "ziel_kurs", "erwartet"}
    abw = 0
    for a, b in zip(mit, ohne):
        for k, v in b.items():
            if a.get(k) != v:
                abw += 1
    extra = set(mit[0]) - set(ohne[0]) if mit else set()
    print("  %d Zeilen · %d Abweichung(en) in den gemeinsamen Schluesseln"
          % (len(mit), abw))
    print("  zusaetzliche Schluessel: %s" % (sorted(extra) or "keine"))
    if abw or extra - neu:
        print("  ⛔ ROT - die Vorgabe ist NICHT bitgleich")
        return 1
    print("  ✔ GRUEN - die Vorgabe rechnet bitgleich weiter (R-R11)")

    # ───────────────────────── DER UMFANG ──────────────────────────────
    print()
    print("─" * 92)
    print("1) WIE GROSS IST DAS PROBLEM?")
    print("─" * 92)
    gl = [z for z in mit if z.get("gleichstand")]
    entschieden = [z for z in mit if z[NAME] in (-1.0, CRV)]
    print("  Anker gesamt            %s" % f"{len(mit):,}".replace(",", "."))
    print("  davon ENTSCHIEDEN       %s" % f"{len(entschieden):,}".replace(",", "."))
    print("  davon GLEICHSTAND       %s   (%.2f %% aller entschiedenen)"
          % (f"{len(gl):,}".replace(",", "."),
             100.0 * len(gl) / max(1, len(entschieden))))
    q_alt = sum(1 for z in entschieden if z[NAME] == CRV) / max(1, len(entschieden))
    print("  Quote HEUTE (q)         %.4f   (%.2f %%)" % (q_alt, 100 * q_alt))
    print("  Kelly-Nullstelle        %.4f   (%.2f %%)" % (1 / (1 + CRV),
                                                          100 / (1 + CRV)))
    if not gl:
        print("\n  Kein Gleichstand - die Regel kostet nichts. Ende.")
        return 0

    # ───────────────────── DIE STUNDENAUFLOESUNG ───────────────────────
    print()
    print("─" * 92)
    print("2) DIE MEHRDEUTIGEN STUENDLICH AUFGELOEST")
    print("─" * 92)
    je_sym = defaultdict(list)
    for z in gl:
        je_sym[z["sym"]].append(z)
    # ⚠️ Gegenpruefung B: eindeutige Anker, an denen die Stundenrechnung
    # dasselbe liefern MUSS wie die Tagesrechnung.
    rng = np.random.default_rng(20260924)
    eindeutig = [z for z in entschieden if not z.get("gleichstand")
                 and z.get("entscheid_tag") is not None]
    probe = ([eindeutig[i] for i in
              rng.choice(len(eindeutig), min(PROBE_B, len(eindeutig)),
                         replace=False)] if eindeutig else [])
    for z in probe:
        je_sym[z["sym"]].append(z)

    zaehl = {"ziel": 0, "stop": 0, "unklar": 0, "leer": 0, "ohne_daten": 0}
    b_ok = b_fehl = 0
    _abw: list = []
    for sym, liste in sorted(je_sym.items()):
        tage = _stunden(sym)
        if not tage:
            for z in liste:
                if z.get("gleichstand"):
                    zaehl["ohne_daten"] += 1
            continue
        for z in liste:
            k = tage.get(str(z["entscheid_tag"])[:10])
            if z.get("gleichstand"):
                if not k:
                    zaehl["ohne_daten"] += 1
                    continue
                w = _wer_zuerst(k, z["stop_kurs"], z["ziel_kurs"])
                zaehl[w if w else "leer"] += 1
            else:
                # ⚠️ GEGENPRUEFUNG B am ENTSCHEIDUNGStag, nicht am Ankertag:
                # der Einstieg ist der SCHLUSSkurs des Ankertags, und die
                # Kerzen davor koennen die Schwelle laengst beruehrt haben.
                if not k:
                    continue
                w = _wer_zuerst(k, z["stop_kurs"], z["ziel_kurs"])
                if w == z.get("erwartet"):
                    b_ok += 1
                else:
                    b_fehl += 1
                    if b_fehl <= 3:
                        _abw.append("%s %s: Tag sagt %s, Stunde sagt %s"
                                    % (sym, z["entscheid_tag"],
                                       z.get("erwartet"), w))

    n_gl = sum(zaehl[k] for k in ("ziel", "stop", "unklar", "leer"))
    print("  %-26s %8s %8s" % ("", "Anzahl", "Anteil"))
    for k, text in (("ziel", "ZIEL zuerst"), ("stop", "STOP zuerst"),
                    ("unklar", "⚠️ auch stuendlich unklar"),
                    ("leer", "keine Beruehrung (Datenlage)")):
        print("  %-26s %8d %7.1f %%"
              % (text, zaehl[k], 100.0 * zaehl[k] / max(1, n_gl)))
    if zaehl["ohne_daten"]:
        print("  %-26s %8d          (nicht bewertbar)"
              % ("ohne Stundendaten", zaehl["ohne_daten"]))

    print()
    print("─" * 92)
    print("GEGENPRUEFUNG B - stimmt die Stundenrechnung?")
    print("─" * 92)
    print("  %d eindeutige Anker geprueft: %d wie erwartet, %d abweichend"
          % (b_ok + b_fehl, b_ok, b_fehl))
    if b_fehl == 0:
        print("  ✔ GRUEN - Stunde und Tag stimmen an eindeutigen Ankern ueberein")
    else:
        print("  ⛔ ROT - die Stundenrechnung widerspricht der Tagesrechnung")
        for z in _abw:
            print("      %s" % z)

    # ───────────────────────── DIE WIRKUNG ─────────────────────────────
    print()
    print("─" * 92)
    print("3) WAS DAS FUER `q` UND DEN HEBEL BEDEUTET")
    print("─" * 92)
    # Heute zaehlen ALLE Gleichstaende als Stop. Neu: nur die, die es sind.
    treffer_alt = sum(1 for z in entschieden if z[NAME] == CRV)
    gewinnt_neu = zaehl["ziel"]
    q_neu = (treffer_alt + gewinnt_neu) / max(1, len(entschieden))
    null = 1.0 / (1.0 + CRV)
    print("  q heute (Gleichstand = Stop)      %.4f" % q_alt)
    print("  q stuendlich aufgeloest           %.4f   (%+.4f)"
          % (q_neu, q_neu - q_alt))
    print("  Kelly-Nullstelle                  %.4f" % null)
    print()
    for text, q in (("heute", q_alt), ("stuendlich", q_neu)):
        kelly = (q * (1.0 + CRV) - 1.0) / CRV
        print("  Kelly %-12s %+.5f   %s"
              % (text, kelly, "→ HEBEL" if kelly > 0 else "→ kein Hebel"))
    print()
    if zaehl["unklar"]:
        print("  ⚠️ %d Faelle bleiben auch stuendlich unklar (%.1f %%) - sie"
              % (zaehl["unklar"], 100.0 * zaehl["unklar"] / max(1, n_gl)))
        print("     zaehlen oben WIE HEUTE als Stop, nicht als Ziel.")
    print("  ⚠️ Das ist die WIRKUNG DER REGEL, kein Kalibrierungsbefund -")
    print("     ob `q` die Trefferquote TRIFFT, misst `messe_bewertung_")
    print("     kalibrierung.py`. Diese Messung sagt nur, auf welcher Zahl")
    print("     jene aufsetzt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
