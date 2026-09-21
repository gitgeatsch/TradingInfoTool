# -*- coding: utf-8 -*-
"""WO IST DIE MESSGRENZE - UND WIE KOMMEN WIR TROTZDEM ZU EINEM URTEIL?

⚠️ Nutzerfrage 21.09.2026: *„dann gibt es offenbar ein problem mit der
Menge bzw Zeitfaktor? analysiere wo die Messgrenze ist und wie wir
dennoch ein gemessenes Ergebnis erhalten zur Kalibrierung - Hinweis:
Krypto ist jung und neue Coins liefern keine Werte."*

Der Hinweis trifft den Kern: ZEIT und MENGE sind nicht unabhaengig. Ein
laengeres Fenster wirft automatisch die jungen Werte hinaus - und in
Krypto sind das viele. Bisher habe ich beide Achsen einzeln beklagt,
aber ihren ZUSAMMENHANG nie gemessen.

## Die drei Fragen, getrennt

    A ZEIT    wie viele Symbole ueberleben welches Fenster? Das ist
              der Preis der Laenge, und er ist aus den KURSEN
              messbar - unabhaengig von jeder Mengenquelle
    B BLOCK   was VERLANGT die Norm je Horizont? `_block(H) =
              max(15, 3H)`, 20 Bloecke. Daraus folgt eine harte
              Mindestlaenge je Horizont
    C MENGE   das Urteil ueber die ganze Mengenleiter statt auf
              EINEM Wert (`pruefung-auf-einem-parameterwert`). Bei
              NEU-VOLL wich das Urteil zwischen 5 und 50 Prozent ab -
              eine Leiter zeigt, ob das eine Kante oder ein Verlauf ist

⚠️⚠️ DER ENTSCHEIDENDE PUNKT, den A und B zusammen ergeben: fuer H2
bis H5 verlangt die Norm 300 Ankertage - die HABEN wir (360). Die Zeit
ist dort NICHT der Engpass. Sie wird es erst bei H20 (1.200 Tage). Der
Engpass bei H2 bis H5 ist die BANDBREITE, und die haengt an den Ankern
JE TAG - also an der Menge, nicht an der Laenge.

⚠️ NUR LESEND, kein Netz. Teil C ruft die echte Messung und dauert.

    python phase4_c_wo_ist_die_messgrenze.py
    python phase4_c_wo_ist_die_messgrenze.py --ohne-c
"""
from __future__ import annotations

import datetime as dt
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402
import messnorm as N                                       # noqa: E402

FENSTER = (365, 500, 730, 1000, 1200, 1500, 2000, 2600)
HORIZONTE = (1, 2, 3, 5, 10, 20)


def main() -> int:
    print("=" * 100)
    print("WO IST DIE MESSGRENZE?")
    print("=" * 100)

    # ---- A  Der Preis der Fensterlaenge -------------------------------
    datei, sql = MR.MESSBASIS["schnitt"]
    v1 = {r[0].upper() for r in sqlite3.connect(
        "file:%s?mode=ro" % datei, uri=True).execute(sql)}
    m = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    spanne = {}
    for sym, a, b, n in m.execute(
            "SELECT symbol, MIN(date), MAX(date), COUNT(*) "
            "  FROM price_history_ohlc GROUP BY symbol"):
        try:
            spanne[sym.upper()] = (dt.date.fromisoformat(str(a)[:10]),
                                   dt.date.fromisoformat(str(b)[:10]), n)
        except Exception:                                  # noqa: BLE001
            pass
    heute = dt.date.today()
    print()
    print("-" * 100)
    print("  A) DER PREIS DER FENSTERLAENGE - Krypto ist jung")
    print("-" * 100)
    print("     %8s %10s %10s %10s   %s"
          % ("Fenster", "Symbole", "Anteil", "davon tot", "Bemerkung"))
    je_fenster = {}
    for tage in FENSTER:
        ab = heute - dt.timedelta(days=tage)
        drin = [s for s in v1 if s in spanne and spanne[s][0] <= ab]
        # "tot" = letzter Kurs liegt vor heute minus 30 Tage
        tot = sum(1 for s in drin
                  if (heute - spanne[s][1]).days > 30)
        je_fenster[tage] = len(drin)
        bem = ""
        if tage == 365:
            bem = "das Fenster der neuen Quelle"
        elif tage == 1200:
            bem = "⚠️ was H20 braucht"
        elif tage == 2600:
            bem = "die lange Historie der registrierten Tabelle"
        print("     %6d d %10d %9.0f %% %10d   %s"
              % (tage, len(drin), 100.0 * len(drin) / len(v1), tot, bem))
    print()
    print("     ⚠️ GELESEN: ein Symbol zaehlt, wenn sein ERSTER Kurs vor "
          "dem Fensterbeginn")
    print("        liegt - sonst hat es im Fenster Loecher und kann "
          "nicht durchgaengig")
    print("        ranken. Der Verlust von %d auf %d Symbole zwischen 365 "
          "und 1.200 Tagen"
          % (je_fenster[365], je_fenster[1200]))
    print("        ist der Preis, den H20 kostet - und er ist nicht "
          "verhandelbar.")

    # ---- B  Was die Norm verlangt -------------------------------------
    print()
    print("-" * 100)
    print("  B) WAS DIE NORM VERLANGT - harte Mindestlaenge je Horizont")
    print("-" * 100)
    print("     %4s %8s %12s %14s   %s"
          % ("H", "Block", "20 Bloecke", "haben wir?", "Symbole dort"))
    for h in HORIZONTE:
        b = N._block(h)
        noetig = 20 * b
        ok = noetig <= 360
        # welches Fenster deckt das?
        passend = min((t for t in FENSTER if t >= noetig), default=None)
        print("     %4d %8d %12d %14s   %s"
              % (h, b, noetig,
                 "JA (365 d)" if ok else "nein",
                 ("%d bei %d d" % (je_fenster[passend], passend))
                 if passend else "-"))
    print()
    print("     ⚠️⚠️ DAS IST DER KERN: fuer H2 bis H5 reichen 365 Tage. "
          "Die ZEIT ist dort")
    print("        NICHT der Engpass - sie wird es erst ab H10. Wer bei "
          "H2 ,zu kurzes")
    print("        Fenster` sagt, nennt den falschen Grund.")
    print()
    print("     ⚠️ Der Engpass bei H2 bis H5 ist die BANDBREITE. Sie "
          "haengt an den")
    print("        Ankern JE TAG mal der Zahl der Bloecke - also an der "
          "MENGE.")
    print("        Genau deshalb traegt NEU-VOLL bei 50 Prozent (187 "
          "Anker/Tag) und")
    print("        nicht bei 5 Prozent (19 Anker/Tag), obwohl beide "
          "dieselben 24 Bloecke")
    print("        haben.")

    # ---- C  Die Mengenleiter -----------------------------------------
    if "--ohne-c" in sys.argv[1:]:
        print()
        print("  C) MENGENLEITER - uebersprungen (--ohne-c)")
        return 0
    print()
    print("-" * 100)
    print("  C) DIE MENGENLEITER - ein Urteil auf EINEM Parameterwert "
          "ist keins")
    print("-" * 100)
    import numpy as np
    import messe_eigenschaft_beitrag as B
    import messe_kandidaten_als_regel as K
    import messnorm_auswahl as MA
    from messe_beitrag_auf_auswahl import momentum250
    import phase4_c_kalibrierung_freefloat as C

    neu, weg, ges = C.menge_neu(C.MENGE_DB, True)
    tage_neu = sorted({t for d in neu.values() for t in d})
    ab = tage_neu[0]
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    leiter = ("5%", "10%", "20%", "50%", "frei")
    print("     %6s %4s %6s %8s %9s %20s %9s %7s  %s"
          % ("Menge", "H", "Syms", "Anker/T", "Wirkung", "Band", "Bezug",
             "Blöcke", "Urteil"))
    for H in (2, 3, 5):
        je0 = K.baue(reihen, "turnover", neu, horizont=H)
        je = C.beschneiden(je0, None, ab)
        for mg in leiter:
            try:
                b = MA.pruefe_auswahl(
                    "turnover", je, mom, lage=lage, menge=mg,
                    rng=np.random.default_rng(C.SAAT), horizont=H,
                    hypothese="C Mengenleiter", verwendung="Beitrag",
                    zielgroesse="bewegung_r")
            except Exception as exc:                       # noqa: BLE001
                print("     %6s %4d -> %s" % (mg, H, str(exc)[:62]))
                continue
            print("     %6s %4d %6d %8.1f %+9.4f [%+.4f..%+.4f] %+9.4f "
                  "%7d  %s"
                  % (mg, H, b.abdeckung_symbole,
                     b.n_anker / b.n_tage if getattr(b, "n_anker", 0)
                     and b.n_tage else 0.0,
                     b.wirkung, b.unten, b.oben, b.bezugswert,
                     b.n_bloecke, C.kurz(b.urteil)), flush=True)
        print()
    print("     ⚠️ LESEART: traegt es auf MEHREREN benachbarten "
          "Mengenstufen, ist es")
    print("        ein Verlauf. Traegt es auf genau einer, ist es eine "
          "Kante - und eine")
    print("        Kante ist ein Hinweis, kein Befund (2.208-n86, "
          "sinngemaess auf die")
    print("        Mengenachse).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
