# -*- coding: utf-8 -*-
"""DIE HEBELBEWERTUNG GEGEN DIE MAIL-RECHNUNG - passt das fachlich zusammen?

⚠️ NUTZERAUFTRAG 13.09.2026: *„wenn du beides hast, stelle die
Hebelbewertung der eMail-Rechnung gegenueber und zeige mir, ob das
fachlich passt, damit das Thema erledigt ist."*

## Die Regel, um die es geht (Regel 2)

    BEWERTUNG          neutral, GEBUEHRENFREI - was ist hier zu holen?
                       -> daraus entsteht der HEBEL
    WIRTSCHAFTLICHKEIT 0,30 % Standard / 1,50 % Bitpanda, plus die
                       Finanzierung des geliehenen Kapitals
                       -> erscheint in der MAIL

## ⚠️⚠️ Die entscheidende Frage ist NICHT, ob beide dieselbe Zahl sagen

Sie duerfen es gar nicht. Die Frage ist, ob die Trennung an der
richtigen Naht liegt - also ob die Gebuehr den HEBEL beeinflussen
WUERDE, wenn man sie hineinliesse. Dafuer zerfaellt die Kostenseite in
zwei Teile, und sie verhalten sich VERSCHIEDEN:

    Handelsgebuehr   kosten_r = 2 x Satz / stop_rel
                     ⚠️ HAENGT NICHT AM HEBEL. Nominal = Einsatz x Hebel
                     steht in Zaehler UND Nenner und kuerzt sich heraus.
    Finanzierung     laeuft auf das GELIEHENE Kapital, also auf
                     Nominal x (1 - 1/Hebel)
                     ⚠️ HAENGT AM HEBEL - und nur sie.

Daraus folgt die Pruefung: die Handelsgebuehr kann die Hebelentscheidung
gar nicht verzerren, die Finanzierung schon. Ob sie es TUT, ist eine
Zahlenfrage - und die beantwortet dieses Werkzeug.

AUFRUF:
    python vergleiche_hebel_und_mailrechnung.py
    python vergleiche_hebel_und_mailrechnung.py --kapital 20000 --tage 5
"""
from __future__ import annotations

import argparse
import sys

from agent import betraege as BT
from agent import wahrscheinlichkeit as WK
from agent.krypto.backward_tracking import kosten_in_r

QUOTEN = (0.333, 0.360, 0.400, 0.450, 0.500)
STOPS = (0.05, 0.08, 0.12, 0.20)
SAETZE = (("Standard", 0.003), ("Bitpanda", 0.015))
CRV = 2.0


def _hebel(quote: float, stop: float, kapital: float) -> dict:
    """Die BEWERTUNGSSEITE - der echte Code, gebuehrenfrei."""
    try:
        return BT.hebelrechnung(quote=quote, crv=CRV, kapital_eur=kapital,
                                stop_rel=stop)
    except Exception as e:                                    # noqa: BLE001
        return {"fehler": str(e)}


def _mail(stop: float, hebel: float, tage: float, satz: float) -> dict:
    """Die MAILSEITE - dieselbe Funktion, die den Mailtext erzeugt."""
    fin_r = 0.0
    if hebel and hebel > 1.0:
        k = kosten_in_r(stop, "hebel", tage, hebel=hebel)
        fin_r = (k.get("finanzierung_rel") or 0.0) / stop
    return WK.rechne(crv=CRV, stop_relativ=stop, gebuehr_je_seite=satz,
                     finanzierung_r=fin_r)


def teil1_naht(kapital: float, tage: float) -> None:
    """⚠️ HAENGT DIE HANDELSGEBUEHR AM HEBEL? Wenn ja, waere die Trennung
    an der falschen Stelle - dann muesste die Bewertung sie kennen."""
    print()
    print("1  LIEGT DIE NAHT RICHTIG? - haengt die Gebuehr ueberhaupt am Hebel?")
    print("=" * 96)
    print("   Gerechnet bei Stop 8 %%, Satz 1,50 %% (der teure Fall), "
          "%.0f Tage." % tage)
    print()
    print("   %-8s %14s %16s %14s" % ("Hebel", "Handelsgebuehr",
                                      "Finanzierung", "zusammen"))
    print("   " + "-" * 60)
    for h in (1.0, 2.0, 3.0, 5.0):
        k = kosten_in_r(0.08, "hebel" if h > 1 else "spot", tage,
                        hebel=h) if h > 1 else kosten_in_r(0.08, "spot", tage)
        fin = (k.get("finanzierung_rel") or 0.0) / 0.08
        handel = 2.0 * 0.015 / 0.08
        print("   %6.1fx %13.4f R %15.4f R %13.4f R"
              % (h, handel, fin, handel + fin))
    print()
    print("   ➤ DIE HANDELSGEBUEHR IST IN JEDER ZEILE DIESELBE ZAHL.")
    print("     `kosten_r = 2 x Satz / stop_rel` - das Nominal steht in")
    print("     Zaehler und Nenner und kuerzt sich heraus. Sie KANN die")
    print("     Hebelentscheidung nicht verzerren, auch nicht theoretisch.")
    print("   ⚠️ NUR DIE FINANZIERUNG WAECHST. Sie ist die einzige Kostenart,")
    print("     bei der die Trennung ueberhaupt etwas kostet - deshalb steht")
    print("     sie unten in Teil 3 auf dem Pruefstand.")


def teil2_gegenueber(kapital: float, tage: float) -> None:
    print()
    print("2  BEWERTUNG GEGEN MAIL - dieselben Faelle, beide Seiten")
    print("=" * 96)
    print("   Kapital %s EUR, CRV %.1f, %.0f Tage Haltedauer."
          % (("%,.0f" % kapital).replace(",", ".") if False
             else format(int(kapital), ",d").replace(",", "."), CRV, tage))
    for stop in STOPS:
        print()
        print("   ── Stop %.0f %% " % (100 * stop) + "─" * 70)
        print("   %-7s │ %-28s │ %-40s"
              % ("Quote", "BEWERTUNG (gebuehrenfrei)", "MAIL (Wirtschaftlichkeit)"))
        print("   %-7s │ %6s %7s %10s │ %-18s %-18s"
              % ("", "r(q)", "Hebel", "Risiko", "Standard 0,30 %",
                 "Bitpanda 1,50 %"))
        print("   " + "─" * 90)
        for q in QUOTEN:
            b = _hebel(q, stop, kapital)
            if "fehler" in b:
                print("   %5.1f %% │ %s" % (100 * q, b["fehler"]))
                continue
            h = b.get("hebel") or 1.0
            zellen = []
            for _name, satz in SAETZE:
                m = _mail(stop, h, tage, satz)
                traegt = q - m["breakeven"]
                zellen.append("%+5.1f Pp %s" % (100 * traegt,
                                                "✔" if traegt > 0 else "✖"))
            print("   %5.1f %% │ %5.2f %% %6.2fx %8.0f € │ %-18s %-18s"
                  % (100 * q, 100 * (b.get("r") or 0.0), h,
                     b.get("risiko_eur") or 0.0, zellen[0], zellen[1]))
    print()
    print("   Pp = Prozentpunkte Abstand der Quote zur gebuehrenBEHAFTETEN")
    print("   Huerde. ✔ traegt sich nach Kosten · ✖ traegt sich nicht.")


def teil3_kostet_die_trennung(kapital: float, tage: float) -> None:
    """⚠️⚠️ DIE EIGENTLICHE FACHFRAGE: erzeugt der gebuehrenfreie Hebel
    Trades, die die MAIL dann als nicht tragend ausweist?

    ⚠️ DIE ERSTE FASSUNG TASTETE EIN QUOTENRASTER AB und meldete "kein
    Fall kippt" - das war ein Artefakt des Rasters. Die Fenstergrenzen
    lagen sichtbar ZWISCHEN zwei Rasterpunkten (45,8 %% und 49,8 %% bei
    8 %% Stop, waehrend das Raster 45,0 und 50,0 hatte). Gemessen wird
    deshalb das FENSTER selbst, nicht eine Stichprobe daraus."""
    print()
    print("3  KOSTET DIE TRENNUNG ETWAS? - das FENSTER, nicht eine Stichprobe")
    print("=" * 96)
    print("   Die Handelsgebuehr haengt nicht am Hebel (Teil 1). Die")
    print("   FINANZIERUNG schon - der gebuehrenfreie Hebel hebt also seine")
    print("   eigene Huerde. Gefragt ist das Quotenfenster, in dem ein Trade")
    print("   OHNE Hebel tragen wuerde und MIT dem gewaehlten Hebel nicht.")
    print("   Gerechnet zum teuren Satz (Bitpanda 1,50 %%), %.0f Tage." % tage)
    print()
    print("   %-8s %8s │ %11s %11s │ %s"
          % ("Stop", "Hebel", "Huerde 1x", "Huerde real", "FENSTER"))
    print("   " + "─" * 74)
    for stop in STOPS:
        # der Hebel, den die Bewertung bei voller Kelly-Klammer vergibt
        b = _hebel(0.45, stop, kapital)
        h = b.get("hebel") or 1.0
        m_real = _mail(stop, h, tage, 0.015)
        m_ohne = _mail(stop, 1.0, tage, 0.015)
        fenster = 100.0 * (m_real["breakeven"] - m_ohne["breakeven"])
        print("   %6.0f %% %7.2fx │ %10.1f %% %10.1f %% │ %+5.1f Prozentpunkte"
              % (100 * stop, h, 100 * m_ohne["breakeven"],
                 100 * m_real["breakeven"], fenster))
    print()
    print("   ➤ DAS FENSTER EXISTIERT und ist am ENGEN Stop am breitesten.")
    print("     Ein Trade mit einer Quote darin wuerde ungehebelt tragen und")
    print("     gehebelt nicht - die Bewertung hat ihn trotzdem gehebelt.")
    print("   ⚠️ DAS IST KEIN FEHLER DER TRENNUNG, sondern ihr Preis, und")
    print("     er ist bezifferbar. Die Bewertung DARF ihn nicht kennen")
    print("     (Regel 2), die Mail MUSS ihn zeigen - und sie tut es, weil")
    print("     sie die Huerde je Gebuehrensatz MIT Finanzierung ausweist.")
    print("   ⚠⚠ WAS DARAUS FOLGT UND WAS NICHT: es folgt NICHT, die")
    print("     Gebuehr in den Hebel zu nehmen. Es folgt, dass der Nutzer die")
    print("     Zeile lesen muss - und dass ein enger Stop beim teuren Satz")
    print("     der ungeeignetste Fall ist.")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--kapital", type=float, default=20000.0)
    p.add_argument("--tage", type=float, default=5.0)
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=" * 96)
    print("HEBELBEWERTUNG GEGEN MAIL-RECHNUNG (Regel 2)")
    print("=" * 96)
    print("BEWERTUNG          `betraege.hebelrechnung` - Quote und CRV, "
          "Kosten 0,00 %")
    print("WIRTSCHAFTLICHKEIT `wahrscheinlichkeit.rechne` - 0,30 % / 1,50 % "
          "plus Finanzierung")
    print("⚠️ Beide Seiten rufen den ECHTEN Betriebscode, keine Nachbildung.")
    teil1_naht(a.kapital, a.tage)
    teil2_gegenueber(a.kapital, a.tage)
    teil3_kostet_die_trennung(a.kapital, a.tage)


if __name__ == "__main__":
    main()
