# -*- coding: utf-8 -*-
"""WIE LANGE MUESSTEN WIR SAMMELN, BIS ES ENTSCHIEDEN IST?

⚠️ Nutzerfrage 21.09.2026: *„analysiere wo die Messgrenze ist und wie
wir dennoch ein gemessenes Ergebnis erhalten zur Kalibrierung"*.

Die Mengenleiter hat gezeigt, WORAN es liegt: die WIRKUNG ist ueber
die ganze Leiter praktisch konstant (H2: +0,0073 bis +0,0097; H3:
+0,0129 bis +0,0203), nur das BAND wird enger, je mehr Anker je Tag
zusammenkommen. Es fehlt also keine Wirkung, sondern PRAEZISION.

Praezision kommt aus zwei Quellen, und nur eine davon ist verfuegbar:

    ANKER JE TAG   haengt an der Symbolzahl. 375 ist, was es gibt -
                   mehr waere nur mit einer breiteren Messmenge zu
                   haben, und die gibt es nicht
    BLOECKE        haengt an der FENSTERLAENGE. 365 Tage sind 24
                   Bloecke. Hier ist Luft - durch WARTEN

⚠️⚠️ DAS IST EINE AUSLEGUNGSRECHNUNG, KEIN BEFUND. Sie beantwortet
"wie lange muessten wir sammeln", nicht "was kaeme heraus". Zwei
Annahmen stehen darin, und beide koennen falsch sein:

    1 DIE WIRKUNG BLEIBT. Sie ist ueber die Mengenleiter stabil -
      aber ein laengeres Fenster ist ein ANDERES Fenster, und
      `zeitfenster-ab-2023` zeigt, dass Marktabschnitte verschieden
      sind. Ein zweites Jahr kann die Wirkung senken
    2 DAS BAND SKALIERT MIT 1/WURZEL(BLOECKE). Das ist die uebliche
      Annahme des Blockbootstraps und hier NICHT nachgemessen

⚠️ Und der Preis der Laenge ist gegengerechnet: ein laengeres Fenster
wirft junge Werte hinaus (Nutzerhinweis: *„Krypto ist jung und neue
Coins liefern keine Werte"*).

    python phase4_c_wie_lange_noch.py
"""
from __future__ import annotations

import datetime as dt
import math
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402
import messnorm as N                                       # noqa: E402

# ⚠️ Gemessen am 21.09.2026 (`phase4_c_wo_ist_die_messgrenze --ohne-c`
# Teil C). Eingetragen, nicht neu gerechnet - der Lauf dauert 7 Minuten
# und diese Rechnung soll in Sekunden nachvollziehbar sein.
# (Menge, H, Wirkung, unten, oben, Bezug, Bloecke)
GEMESSEN = (
    ("5%",   2, +0.0084, -0.0157, +0.0357, +0.0000, 23),
    ("10%",  2, +0.0097, -0.0020, +0.0292, +0.0002, 24),
    ("20%",  2, +0.0088, -0.0024, +0.0270, +0.0002, 24),
    ("50%",  2, +0.0073, +0.0009, +0.0187, +0.0000, 24),
    ("5%",   3, +0.0203, -0.0111, +0.0607, +0.0036, 23),
    ("10%",  3, +0.0194, +0.0012, +0.0498, +0.0000, 24),
    ("20%",  3, +0.0134, -0.0021, +0.0413, +0.0005, 24),
    ("50%",  3, +0.0131, +0.0030, +0.0299, +0.0000, 24),
    ("5%",   5, +0.0243, -0.0173, +0.0709, +0.0056, 23),
    ("10%",  5, +0.0285, -0.0041, +0.0641, +0.0000, 24),
    ("20%",  5, +0.0176, -0.0080, +0.0458, +0.0000, 24),
    ("50%",  5, +0.0144, -0.0040, +0.0363, +0.0000, 24),
)
HEUTE_TAGE = 365


def main() -> int:
    print("=" * 100)
    print("WIE LANGE MUESSTEN WIR SAMMELN? - eine AUSLEGUNGSRECHNUNG")
    print("=" * 100)
    print("  ⚠️ KEIN BEFUND. Zwei Annahmen: die Wirkung bleibt, und das "
          "Band skaliert")
    print("     mit 1/Wurzel(Bloecke). Beide koennen falsch sein - die "
          "erste besonders,")
    print("     weil ein laengeres Fenster ein ANDERES Fenster ist "
          "(`zeitfenster-ab-2023`).")
    print()
    print("  %6s %3s %9s %11s %9s %11s %10s   %s"
          % ("Menge", "H", "Wirkung", "Abstand", "Faktor", "Bloecke",
             "Tage", "ab wann"))
    heute = dt.date.today()
    for menge, h, w, unten, _oben, bezug, bl in GEMESSEN:
        # Abstand, der noch fehlt: `unten` muss ueber `bezug`
        fehlt = bezug - unten
        halb = w - unten                      # halbe Bandbreite nach unten
        if fehlt <= 0:
            print("  %6s %3d %+9.4f %11s %9s %11d %10d   ✔ TRAEGT SCHON"
                  % (menge, h, w, "-", "-", bl, HEUTE_TAGE))
            continue
        # noetige Verengung: neue Halbbreite muss < (w - bezug) sein
        ziel = w - bezug
        if ziel <= 0:
            print("  %6s %3d %+9.4f %11s %9s %11d %10s   ⛔ Wirkung unter "
                  "dem Nullpunkt - Warten hilft nicht"
                  % (menge, h, w, "-", "-", bl, "-"))
            continue
        faktor = halb / ziel                  # so viel enger muss es werden
        noetig_bl = bl * faktor ** 2
        noetig_tage = noetig_bl * N._block(h)
        jahre = (noetig_tage - HEUTE_TAGE) / 365.25
        wann = heute + dt.timedelta(days=max(0.0, noetig_tage -
                                             HEUTE_TAGE))
        print("  %6s %3d %+9.4f %11.4f %9.2f %11.0f %10.0f   %s"
              % (menge, h, w, fehlt, faktor, noetig_bl, noetig_tage,
                 ("%s (+%.1f Jahre)" % (wann.isoformat(), jahre))
                 if jahre > 0 else "jetzt"))

    # ---- was kostet die Laenge an Symbolen? --------------------------
    datei, sql = MR.MESSBASIS["schnitt"]
    v1 = {r[0].upper() for r in sqlite3.connect(
        "file:%s?mode=ro" % datei, uri=True).execute(sql)}
    m = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    erst = {}
    for sym, a in m.execute("SELECT symbol, MIN(date) "
                            "  FROM price_history_ohlc GROUP BY symbol"):
        try:
            erst[sym.upper()] = dt.date.fromisoformat(str(a)[:10])
        except Exception:                                  # noqa: BLE001
            pass
    print()
    print("  ⚠️ GEGENRECHNUNG - was kostet das WARTEN an Symbolen?")
    print("     Nach VORNE zu sammeln kostet keine jungen Werte - das "
          "Fenster waechst")
    print("     am neuen Ende. Es kostet aber die, die EINGESTELLT "
          "werden. Wie viele")
    print("     das sind, ist nicht zu schaetzen, sondern aus der "
          "Vergangenheit zu")
    print("     ZAEHLEN: wie viele der damals Handelbaren handeln heute "
          "noch?")
    letzt = {}
    for sym, b in m.execute("SELECT symbol, MAX(date) "
                            "  FROM price_history_ohlc GROUP BY symbol"):
        try:
            letzt[sym.upper()] = dt.date.fromisoformat(str(b)[:10])
        except Exception:                                  # noqa: BLE001
            pass
    print("     %12s %10s %12s %10s"
          % ("Stichtag", "handelbar", "heute noch", "Schwund"))
    for zurueck in (365, 730, 1095, 1460):
        stichtag = heute - dt.timedelta(days=zurueck)
        # damals handelbar: erster Kurs davor, letzter Kurs danach
        damals = [s for s in v1 if s in erst and erst[s] <= stichtag
                  and s in letzt and letzt[s] >= stichtag]
        # heute noch: letzter Kurs juenger als 30 Tage
        noch = [s for s in damals if (heute - letzt[s]).days <= 30]
        if damals:
            weg = 100.0 * (len(damals) - len(noch)) / len(damals)
            print("     %s %10d %12d %9.0f %%  (%.1f %%/Jahr)"
                  % (stichtag.isoformat(), len(damals), len(noch), weg,
                     weg / (zurueck / 365.25)))
    print("     ⚠️ DER SCHWUND IST DER PREIS DES WARTENS - und er trifft "
          "nicht zufaellig:")
    print("        eingestellt wird, was klein und illiquide ist. Wer "
          "wartet, misst am")
    print("        Ende auf einer Menge, aus der der Boden der "
          "Verteilung herausgefallen")
    print("        ist - genau die Verzerrung, die der Nachzug gerade "
          "behoben hat.")
    print("        ➤ GEGENMITTEL: die Reihe eines eingestellten Symbols "
          "STEHEN LASSEN,")
    print("          nicht loeschen. Dann waechst das Fenster, ohne "
          "dass die Menge")
    print("          schrumpft.")
    print()
    print("=" * 100)
    print("  ➤ DER PUNKT: nach vorne zu sammeln ist der EINZIGE Weg, der "
          "die Abdeckung")
    print("     NICHT kostet. Eine rueckwaertige Verlaengerung gibt es "
          "bei dieser Quelle")
    print("     ohnehin nicht (365 Tage sind das Maximum ohne "
          "Schluessel).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
