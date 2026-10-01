# -*- coding: utf-8 -*-
"""Was haben unsere ECHTEN Signale gebracht? (22.08.2026, Umbauplan 126)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

DER ANLASS KAM VOM NUTZER: *"eigentlich sollten wir auch eine Messung der
bisherigen Signale durchfuehren inkl. der LLM Bewertungen - diese sollten auch
bereits ein Ergebnis zeigen oder? ... also auch die Schatten meine ich inkl.
der Rolle G ZAI."*

Er hat recht, und die Daten liegen seit Wochen im NB-Export. Alle bisherigen
Kapitel (99-125) haben auf FREMDEN Binance-Reihen gemessen. Hier wird zum
ersten Mal gefragt, was UNSER System an UNSEREN Signalen erreicht hat.

DIE FRAGEN, VORAB FESTGELEGT - UND DER MASSSTAB IST FUER ALLE DERSELBE:

    F1  Schlaegt ein Anbieter die Basisrate seiner eigenen Geometrie?
    F2  Sagt Z.ais Gegenpruefung ("konsistent"/"widerspruch") den Ausgang
        vorher?
    F3  Sagt Z.ais Richtungsurteil ("uebereinstimmung"/"abweichung") den
        Ausgang vorher?
    F4  Was haetten die Schatten gebracht - Veto-Schatten und
        selbst gewaehltes HALTEN?

DER MASSSTAB (Kapitel 119): Trefferquote gegen `1/(1+CRV)`, und der Abstand
zum Breakeven `(1+Kosten_R)/(1+CRV)` bei BEIDEN Gebuehrensaetzen. Eine
Trefferquote ohne ihren Breakeven ist keine Aussage (Methodik 2.53).

⚠️ VIER VORBEHALTE, DIE ZUM ERGEBNIS GEHOEREN - SIE STEHEN HIER, WEIL SIE
SPAETER NICHT MEHR AUFFALLEN WUERDEN:

  1. DIESE DATEN STAMMEN GROSSTEILS AUS DER ALTEN KETTE. Die Rollen-Kette
     laeuft erst seit dem 15.08.2026; `created_at` der Gegenpruefungen
     beginnt am 26.07. Was hier gemessen wird, ist zum groessten Teil das
     VORGAENGERSYSTEM. Das entwertet die Messung nicht - es benennt sie.
  2. DAS REGIME WAR DURCHGEHEND "BAER". Ein Anbieter, der ueberwiegend LONG
     vorschlaegt, misst hier die Marktrichtung mit - die Quoten sind also
     nicht der Verdienst des Modells allein.
  2b. DIE TREFFERQUOTE UND DAS REALISIERTE R KOENNEN SICH WIDERSPRECHEN, und
     dann gilt das R. Der Breakeven unterstellt, dass jeder Treffer das
     volle CRV zahlt; wird frueher verkauft oder das Ziel verfehlt, ist die
     Quote schoen und das Ergebnis null. Dieser Fall wird ausdruecklich
     GEMELDET, nicht ueberlesen.
  3. `nur_long` FILTERT SEIT DEM 05.08. NUR NOCH DEN VERSAND. Aeltere
     SHORT-Vorschlaege wurden davor als HALTEN gebucht (313 Faelle) - wer
     ueber Richtungen auswertet, mischt zwei Populationen.
  4. UEBERLEBENSVERZERRUNG DER AUFLOESUNG: ein Signal zaehlt erst, wenn es
     aufgeloest ist. Laufende Positionen fehlen, und offene Verlierer laufen
     laenger als offene Gewinner.
  5. ⚠️ DIE HAEUFUNG - der schwerste. 1.118 Gegenpruefungen verteilen sich
     auf 192 (Symbol, Tag) und 22 Symbole; VIRTUAL bekam an EINEM Tag 48
     Bewertungen. Die Intervalle werden deshalb auf die EFFEKTIVE
     Stichprobe gerechnet (Faktor 5,82), nicht auf die rohe Fallzahl.
     Siehe `HAEUFUNG_GEMESSEN`.

DIE ABBRUCHREGEL JE FRAGE:

    weniger als 30 aufgeloeste Faelle  -> "nicht entscheidbar", KEINE Zahl
    Vertrauensintervall enthaelt die   -> "nicht unterscheidbar"
    Basisrate
    sonst                              -> Befund MIT Breakeven-Abstand

⚠️ ES WIRD NICHTS PERMUTIERT. Diese Messung vergleicht nicht zwei Arme
derselben Grundgesamtheit, sondern eine beobachtete Quote gegen eine
ARITHMETISCHE Erwartung. Das richtige Werkzeug ist das Vertrauensintervall
der Quote, nicht ein Zufallsarm - eine Permutation haette hier nichts zu
vertauschen (dieselbe Lehre wie Methodik 2.55).

    python messe_signalbilanz.py [--export PFAD]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys

sys.path.insert(0, ".")
from simuliere_bremse import SAETZE_ZUM_BERICHTEN              # noqa: E402

MINDEST_FAELLE = 30
# Der Stopabstand, mit dem der Breakeven gerechnet wird. Median ueber die
# echten Signale waere besser - er steht im Export aber nicht je Fall, also
# wird der gemessene Median aus Kapitel 120 genommen und AUSGEWIESEN.
STOP_RELATIV = 0.20

# ⚠️ DAS GEPLANTE CRV, NICHT DAS REALISIERTE (Korrektur 22.08.2026).
#
# Meine erste Fassung nahm `avg_realisiertes_crv` als Nenner der Basisrate.
# Das ist zirkulaer und liefert Unsinn: fuer mistral/krypto stand dort 0,03,
# also eine "Basisrate" von 97 % und ein Breakeven von 100,1 %. Der
# realisierte CRV ist das ERGEBNIS, die Basisrate haengt an der GEOMETRIE.
#
# Gerechnet wird deshalb mit dem geplanten CRV des Systems; der realisierte
# steht als eigene Spalte daneben, wo er hingehoert.
CRV_GEPLANT = 2.0

# ⚠️ DIE HAEUFUNG - UND SIE IST DER GROESSTE EINZELNE FEHLER DIESER MESSUNG
# GEWESEN (Korrektur 22.08.2026, auf Nutzerfrage).
#
# Nutzerfrage woertlich: *"wie wir diese korrekt zaehlen wenn z.B. Hype 5 mal
# am Tag eine Bewertung erhalten hat, ist das abgrenzbar?"*
#
# JA, UND ES IST GRAVIEREND. Gemessen an den 1.118 Gegenpruefungen:
#
#     Eintraege                    1.118
#     verschiedene Symbole            22
#     verschiedene (Symbol, Tag)     192
#     Hoechstzahl an einem Tag        48   (VIRTUAL am 31.07.)
#
# Das sind KEINE 1.118 unabhaengigen Beobachtungen. Fuenf Bewertungen
# desselben Symbols am selben Tag schauen auf dieselbe Zukunft - sie sind
# EINE Beobachtung mit fuenf Meinungen, nicht fuenf Beobachtungen.
#
# Methodik 2.19.1 kennt das seit dem 10.08. ("jede kuenftige Messung dieser
# Bauart braucht die Gewichtung") - meine erste Fassung hat es trotzdem
# uebersehen und Wilson-Intervalle auf die rohen Fallzahlen gerechnet.
#
# ⚠️ DIE ZAEHLEINHEIT IST DER ANLASS, NICHT DAS SIGNAL. `agent/anlass.py`
# definiert sie bereits: derselbe Fingerabdruck binnen 24 Stunden ist
# DIESELBE Frage. (Symbol, Tag) ist die grobe, konservative Naeherung davon -
# genauer waere der Fingerabdruck, aber der steht im Export nicht je Fall.
HAEUFUNG_GEMESSEN = 5.82
HAEUFUNG_QUELLE = "1.118 Gegenpruefungen -> 192 (Symbol, Tag), 22 Symbole"


def _wilson(treffer: int, n: int) -> tuple:
    """Vertrauensintervall einer Quote (Wilson, 95 %).

    ⚠️ NICHT DIE NORMALNAEHERUNG. Bei kleinen Fallzahlen und Quoten nahe 0
    oder 1 liefert sie Grenzen ausserhalb [0,1] - genau der Bereich, in dem
    hier gemessen wird."""
    if n <= 0:
        return (float("nan"), float("nan"))
    z = 1.959964
    p = treffer / n
    nenner = 1 + z * z / n
    mitte = (p + z * z / (2 * n)) / nenner
    rand = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / nenner
    return (max(0.0, mitte - rand), min(1.0, mitte + rand))


def _breakeven(crv: float, satz: float, stop_relativ: float) -> float:
    return (1.0 + 2.0 * satz / stop_relativ) / (1.0 + crv)


def _urteil(treffer: int, n: int, crv: float,
            haeufung: float = HAEUFUNG_GEMESSEN) -> tuple:
    """(Text, Quote, Intervall) - oder 'nicht entscheidbar'.

    ⚠️ DAS INTERVALL WIRD AUF DIE EFFEKTIVE STICHPROBE GERECHNET, nicht auf
    die rohe Fallzahl. Die Quote selbst bleibt, wie sie ist - gehaeufte
    Beobachtungen verzerren sie nicht, sie machen sie nur unsicherer."""
    # Die Untergrenze gilt fuer die EFFEKTIVE Stichprobe: 30 gehaeufte
    # Faelle sind bei Faktor 5,8 nur fuenf unabhaengige.
    n_eff = max(1, int(round(n / max(haeufung, 1.0))))
    if n_eff < MINDEST_FAELLE:
        return (f"nicht entscheidbar ({n} Faelle = {n_eff} unabhaengige, "
                f"noetig {MINDEST_FAELLE})", None, None)
    q = treffer / n
    unten, oben = _wilson(int(round(q * n_eff)), n_eff)
    basis = 1.0 / (1.0 + crv)
    if unten <= basis <= oben:
        return ("nicht unterscheidbar von der Basisrate", q, (unten, oben))
    return ("BESSER" if q > basis else "SCHLECHTER", q, (unten, oben))


def _lade(pfad: str) -> dict:
    roh = io.open(pfad, encoding="utf-8").read()
    dec = json.JSONDecoder()
    aus = {}
    for name in ("gesamt_signalqualitaet", "provider_performance",
                 "zai_gegenpruefung_verlauf", "zai_richtung_performance",
                 "veto_schatten_performance",
                 "selbst_gewaehltes_halten_performance"):
        m = re.search(r'"%s"\s*:\s*' % re.escape(name), roh)
        aus[name] = dec.raw_decode(roh, m.end())[0] if m else None
    return aus


def _zeile(name: str, treffer: int, n: int, crv: float,
           zusatz: str = "", realisiert: float | None = None) -> None:
    text, q, iv = _urteil(treffer, n, crv)
    if q is None:
        print(f"  {name:22}{n:>7}   {text}")
        return
    print(f"  {name:22}{n:>7}{100 * q:8.1f} %"
          f"  [{100 * iv[0]:4.1f}; {100 * iv[1]:4.1f}]  {zusatz:20} {text}")
    for bez, satz in SAETZE_ZUM_BERICHTEN:
        be = _breakeven(crv, satz, STOP_RELATIV)
        print(f"  {'':22}{'':7}{'':10}  {bez}: noetig "
              f"{100 * be:.1f} % -> {100 * (q - be):+.1f} Punkte")
    # ⚠️ DER WIDERSPRUCH, DER SONST UNTERGEHT. Eine Quote ueber dem
    # Breakeven bei einem realisierten R um null heisst: die Treffer zahlen
    # das unterstellte CRV NICHT. Dann ist die Quote schoen und das
    # Ergebnis keins - und das R gilt, nicht die Quote.
    if realisiert is not None and q > _breakeven(
            crv, SAETZE_ZUM_BERICHTEN[0][1], STOP_RELATIV)             and realisiert <= 0.0:
        print(f"  {'':22}{'':7}{'':10}  ⚠️ WIDERSPRUCH: Quote ueber dem "
              f"Breakeven, realisiert aber {realisiert:+.2f} R -")
        print(f"  {'':22}{'':7}{'':10}     die Treffer zahlen das "
              f"unterstellte CRV {crv:.1f} nicht. Es gilt das R.")


def anbieter(daten: dict) -> None:
    print("\n" + "=" * 78)
    print("F1  SCHLAEGT EIN ANBIETER SEINE EIGENE BASISRATE?")
    print("=" * 78)
    q = daten.get("gesamt_signalqualitaet") or {}
    if not q:
        print("  Abschnitt fehlt im Export")
        return
    for gruppe, je_anbieter in sorted(q.items()):
        print(f"\n  --- {gruppe} ---")
        print(f"  {'Anbieter':22}{'n':>7}{'Quote':>10}"
              f"{'  95-%-Intervall':>18}  {'realisiert':20} Urteil")
        for name, w in sorted((je_anbieter or {}).items()):
            n = int(w.get("anzahl_resolved") or 0)
            tp = int(w.get("take_profit_count") or 0)
            rcrv = w.get("avg_realisiertes_crv")
            _zeile(f"{name}", tp, n, CRV_GEPLANT,
                   f"realisiert {float(rcrv):+.2f} R"
                   if rcrv is not None else "",
                   None if rcrv is None else float(rcrv))


def gegenpruefung(daten: dict) -> None:
    print("\n" + "=" * 78)
    print("F2/F3  SAGT ROLLE G (Z.ai) DEN AUSGANG VORHER?")
    print("=" * 78)
    v = daten.get("zai_gegenpruefung_verlauf") or {}
    eintraege = v.get("eintraege") or []
    print(f"  {v.get('anzahl_gesamt', 0)} Gegenpruefungen insgesamt, "
          f"{len(eintraege)} im Export enthalten")

    # ⚠️ DER GRUND, WARUM FAST NICHTS AUSWERTBAR IST - und er ist ein
    # BETRIEBSBEFUND, keine Messgrenze (gefunden 22.08.2026).
    #
    # Die Aufschluesselung nach `action` zeigt es sofort: Rolle G laeuft
    # ueberwiegend auf HALTEN, und HALTEN bekommt per Konstruktion nie einen
    # Ausgang. Ohne diese Zeilen sieht es aus, als sei die Verknuepfung
    # kaputt - sie ist es nicht, es gibt schlicht nichts zu verknuepfen.
    import collections as _c

    kreuz = _c.Counter(
        (str(x.get("action")), str(x.get("outcome_status")))
        for x in eintraege)
    akt = _c.Counter(str(x.get("action")) for x in eintraege)
    print(f"\n  {'action':16}{'n':>7}{'mit Ausgang':>14}{'Anteil':>10}")
    for aktion, n in akt.most_common():
        mit = sum(w for (a, st), w in kreuz.items()
                  if a == aktion
                  and st not in ("nicht_anwendbar", "None", "offen"))
        print(f"  {aktion:16}{n:>7}{mit:>14}{100 * mit / n:9.1f} %")
    eroeffnen = akt.get("ERÖFFNEN", 0)
    if eroeffnen and len(eintraege):
        print(f"\n  ⚠️ {100 * (1 - eroeffnen / len(eintraege)):.1f} % der "
              f"Aufrufe entfallen auf HALTEN.")
        # ⚠️ UND HALTEN IST NICHT GRUNDSAETZLICH UNAUSWERTBAR - das war mein
        # erster Schluss und er war zur Haelfte falsch. Ein selbst
        # gewaehltes HALTEN mit gesetzten Zonen wird sehr wohl aufgeloest,
        # nur in `selbst_halten_outcome_*`. Die Exportabfrage las bis zum
        # 22.08. nur `outcome_*`.
        if not any("selbst_halten_outcome_status" in x for x in eintraege[:1]):
            print("     ⚠️ DIESER EXPORT KENNT DIE SCHATTENSPALTEN NOCH "
                  "NICHT - der Ausgang eines")
            print("        selbst gewaehlten HALTEN steht in "
                  "`selbst_halten_outcome_*`, und die")
            print("        Abfrage las bis zum 22.08. nur `outcome_*`. Nach "
                  "Pull und neuem")
            print("        Export werden diese Faelle auswertbar - vorher "
                  "nicht.")
    # ⚠️ NUR AUFGELOESTE FAELLE. `outcome_status` "nicht_anwendbar" heisst,
    # dass es nie einen Ausgang gab - sie mitzuzaehlen waere ein Nenner aus
    # Faellen, die die Frage gar nicht beantworten koennen.
    # ⚠️ BEIDE SPALTEN, NICHT NUR EINE (Korrektur 22.08.2026). Ein selbst
    # gewaehltes HALTEN mit gesetzten Zonen wird aufgeloest - aber in
    # `selbst_halten_outcome_realisiertes_crv`, nicht in `outcome_*`. Wer
    # nur die erste liest, haelt 1.046 auswertbare Faelle fuer unauswertbar.
    def _ergebnis(e):
        for feld in ("outcome_realisiertes_crv",
                     "selbst_halten_outcome_realisiertes_crv"):
            if e.get(feld) is not None:
                return float(e[feld])
        return None

    auf = [e for e in eintraege if _ergebnis(e) is not None]
    aus_schatten = sum(
        1 for e in auf if e.get("outcome_realisiertes_crv") is None)
    if aus_schatten:
        print(f"  davon aus dem HALTEN-Schatten: {aus_schatten}")
    print(f"  davon mit Ausgang: {len(auf)}")
    if not auf:
        print("  ⚠️ KEIN einziger Eintrag traegt einen Ausgang - die Frage")
        print("     ist mit diesem Export nicht beantwortbar.")
        return
    for feld, name in (("zai_gegenpruefung_urteil", "F2 Gegenpruefung"),
                       ("zai_uebereinstimmung", "F3 Richtungsurteil")):
        gruppen: dict = {}
        for e in auf:
            wert = e.get(feld)
            if wert is None:
                continue
            gruppen.setdefault(str(wert), []).append(_ergebnis(e))
        print(f"\n  --- {name} ---")
        if not gruppen:
            print("     kein Eintrag traegt dieses Feld")
            continue
        print(f"  {'Urteil':34}{'n':>7}{'Anteil > 0':>12}{'mittleres CRV':>16}")
        for wert, crvs in sorted(gruppen.items()):
            besser = sum(1 for c in crvs if c > 0)
            print(f"  {wert:34}{len(crvs):>7}{100 * besser / len(crvs):11.1f} %"
                  f"{sum(crvs) / len(crvs):+16.3f}")
        if len(gruppen) >= 2:
            namen = sorted(gruppen)
            a, b = gruppen[namen[0]], gruppen[namen[1]]
            if min(len(a), len(b)) >= MINDEST_FAELLE:
                d = (sum(a) / len(a)) - (sum(b) / len(b))
                print(f"  Unterschied {namen[0]} gegen {namen[1]}: "
                      f"{d:+.3f} R im mittleren CRV")
            else:
                print(f"  ⚠️ nicht entscheidbar - kleinste Gruppe hat "
                      f"{min(len(a), len(b))} Faelle")


def schatten(daten: dict) -> None:
    print("\n" + "=" * 78)
    print("F4  WAS HAETTEN DIE SCHATTEN GEBRACHT?")
    print("=" * 78)
    for schluessel, titel in (
            ("veto_schatten_performance", "Veto-Schatten (vetote Trades)"),
            ("selbst_gewaehltes_halten_performance",
             "selbst gewaehltes HALTEN")):
        print(f"\n  --- {titel} ---")
        d = daten.get(schluessel) or {}
        if not d:
            print("     Abschnitt fehlt im Export")
            continue
        print(f"  {'Gruppe / Anbieter':22}{'n':>7}{'Quote':>10}"
              f"{'  95-%-Intervall':>18}  {'realisiert':20} Urteil")
        for gruppe, je in sorted(d.items()):
            for name, w in sorted((je or {}).items()):
                n = int(w.get("anzahl_resolved") or 0)
                tp = int(w.get("take_profit_count") or 0)
                rcrv = w.get("avg_realisiertes_crv")
                _zeile(f"{gruppe}/{name}", tp, n, CRV_GEPLANT,
                       f"realisiert {float(rcrv):+.2f} R"
                       if rcrv is not None else "",
                       None if rcrv is None else float(rcrv))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", default=None)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    pfad = a.export
    if not pfad:
        from extract_notebook_diagnose import _google_drive_wurzel
        import os
        pfad = os.path.join(_google_drive_wurzel(), "Claude_Austauschordner",
                            "Notebook_Analysedaten", "notebook_diagnose.json")
    print("=" * 78)
    print("WAS HABEN UNSERE ECHTEN SIGNALE GEBRACHT?")
    print(f"  Quelle: {pfad}")
    print("  ⚠️ Grossteils ALTE KETTE - die Rollen-Kette laeuft erst seit")
    print("     dem 15.08.2026. Regime durchgehend 'baer'.")
    print(f"  Breakeven gerechnet mit Stopabstand {100 * STOP_RELATIV:.0f} % "
          f"(Median aus Kapitel 120)")
    print("=" * 78)
    daten = _lade(pfad)
    anbieter(daten)
    gegenpruefung(daten)
    schatten(daten)
    print("\n" + "=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
