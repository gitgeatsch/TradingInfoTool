"""Wie haette das LLM in einer ANDEREN Marktphase entschieden? (2026-08-09)

DER AUFTRAG, woertlich (Nutzer, 09.08.): *"simuliere einfach eine andere
Marktphase aus der Historie und wie die LLMs damals reagiert haetten"*.

WARUM DAS DIE EINZIGE MOEGLICHE FORM DER FRAGE IST. Ausnahmslos jedes Signal
der Datenbank traegt `regime = "baer"` - 1.391 Hebel, 2.223 Spot, ueber die
ganze Historie (gemessen 06.08., `Konstruktion_Zeitskalen_06_08.md` V2). Aus
Produktionsdaten laesst sich deshalb NIE trennen, ob ein Befund am Modell oder
an der Marktphase liegt. Es gibt nur eine Phase. Wer den Vergleich will, muss
ihn simulieren - und das geht, weil die Kursreihen bis 2024-07 zurueckreichen
und dort alle drei Phasen vorkommen (bulle 35,1 %, baer 36,0 %, gemischt
28,8 % der Tage).

DIE KONKRETE FRAGE. Der Deadloop besteht aus zwei Beobachtungen: keine
LONG-/Kaufsignale, und fast nichts kommt durchs CRV-Gate (62,9 % der Signale
seit 01.08. scheitern an CRV < 2,0). Beides koennte eine Eigenschaft des
Systems sein - oder schlicht die richtige Antwort auf einen Baerenmarkt. Dieser
Lauf trennt das.

DIE ARME, vor dem Lauf festgelegt:

    BULLE        Anker aus Phasen mit EMA20 > EMA50 > EMA200, Label "bulle"
    SEITWAERTS   Anker aus gemischten Phasen, Label "seitwaerts"
    BAER         Anker aus Phasen mit EMA20 < EMA50 < EMA200, Label "baer"

Nur Anker aus STABILEN Bloecken (mindestens `MIN_BLOCK` aufeinanderfolgende
Tage derselben Phase) - die Rohklassifikation flackert an den Raendern
tagesweise, und ein Anker auf einem Flackertag misst nichts.

WICHTIG ZUM FAKTENSATZ. `baue_historische_fakten()` setzt `regime.wert` auf
"nicht rekonstruierbar". Das ist fuer diesen Lauf falsch und wird ueberschrieben:
eine "Unknown"-Option loest laut `regime.py` Abstention aus - genau der
Mechanismus, der die EROEFFNEN-Quote schon einmal von 93 % auf 3 % gedrueckt
hat. Ein Arm mit "unbekannt" wuerde also nicht die Marktphase messen, sondern
den Abstention-Reflex.

DIE PRIMAERGROESSEN, ebenfalls vorab festgelegt:

    1  EROEFFNEN-Quote      die Deadloop-Kennzahl
    2  LONG-Anteil          die "keine Kaufsignale"-Kennzahl
    3  Anteil CRV >= 2,0    die Gate-Kennzahl
    4  Stop-Abstand in %    Vergleichbarkeit mit der Produktion

Alle vier sind REINE VERHALTENSGROESSEN - sie haengen an dem, was das Modell
ausgibt, und nicht daran, wie wir den spaeteren Verlauf bewerten. Das ist
Absicht: das statische Halten bis zur Barriere wurde am 06.08. als falsches
Instrument verworfen (Median-Trade nach 1-2 Tagen entschieden, aber 26-45 %
erreichen ihren Bestwert erst nach Tag 5; live ist stattdessen der
Trailing-Stop ab +1R). Ergebnisgroessen (`ausgang`, `r`) werden deshalb
mitgeschrieben, aber NUR nachrangig ausgewertet und mit diesem Vorbehalt.

DIE GEGENPRUEFUNGEN, ohne die der Lauf nichts wert ist (stehende Nutzer-Vorgabe
09.08.: *"mach zu all deinen Pruefungen immer eine Gegenpruefung"*):

    CC1 REPRODUKTION    Der BAER-Arm muss die Produktion treffen: 82,7 % SHORT
                        und Stop-Median 8,25 % (n=568 seit 01.08.). Trifft er
                        das nicht, misst der Aufbau nicht das System, und alle
                        anderen Zahlen sind wertlos. Das ist ein ABBRUCH-
                        Kriterium, keine Randnotiz.
    CC2 LABEL/DATEN     BULLE-Anker ein zweites Mal, Marktdaten identisch, nur
                        das Label auf "baer" gezwungen. Trennt "andere Daten"
                        von "anderes Wort im Prompt". VORAB-ERWARTUNG: kein
                        messbarer Unterschied - am 06.08. reagierte das Modell
                        auf ein getauschtes Regime-Label nicht messbar
                        (Konfidenz 0,28x, Stop 0,10x des Eigenrauschens, n=29).
                        Zeigt CC2 doch einen Effekt, widerspricht das der
                        frueheren Messung und gehoert gemeldet, nicht verrechnet.
    CC3 RAUSCHBODEN     Dieselben Anker zweimal. `nemotron` dreht bei
                        IDENTISCHER Eingabe in ~12 % die Handelsrichtung
                        (Messung 09.08.). Ohne diesen Boden ist kein
                        Armunterschied interpretierbar.
    CC4 KONZENTRATION   Kein einzelnes Symbol darf einen Armunterschied tragen.

AUSGESCHLOSSEN: CAT - dokumentiert kaputte Kursreihe (Memory
project_z3_fx_ableitung_06_08).

    python messe_regimephasen_llm.py --je-arm 30 --trocken
    python messe_regimephasen_llm.py --je-arm 30 --ausgabe regimephasen.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import time
from collections import Counter, defaultdict

from backtest_llm1_historisch import (
    HORIZONT,
    VORLAUF_MIN,
    Kerze,
    baue_historische_fakten,
    lade_reihen,
)
from erzeuge_parameterdaten import _auswerten, _zonen

# Kaputte Kursreihe, dokumentiert - ein Anker darauf misst Datenmuell.
AUSGESCHLOSSEN = {"CAT"}

# Wie viele aufeinanderfolgende Tage derselben Phase, damit ein Block als
# stabil gilt. Die Rohklassifikation flackert an den Uebergaengen tageweise
# (gemessen: 2025-06-18 bis 2025-07-02 wechselt achtmal).
MIN_BLOCK = 10

# Ab wie vielen gemeinsamen Symbolen ein Cluster-Bootstrap tragfaehig ist.
# Cameron/Gelbach/Miller: cluster-robuste Verfahren ueber-verwerfen bei fuenf
# bis dreissig Clustern (10 % statt der nominellen 5 %). Darunter ist der
# Wild-Cluster-Test Pflicht, und selbst mit ihm bleibt ein Lauf mit sehr
# wenigen Clustern hypothesegenerierend. 12 ist die Untergrenze, unterhalb
# derer dieses Skript das ausdruecklich sagt statt es zu verschweigen.
MIN_CLUSTER = 12

# Produktion seit 2026-08-01, n=568 - die Messlatte fuer CC1.
PROD_SHORT_ANTEIL = 0.827
PROD_STOP_MEDIAN = 8.25

ARME = ("BULLE", "SEITWAERTS", "BAER")
LABEL = {"BULLE": "bulle", "SEITWAERTS": "seitwaerts", "BAER": "baer"}


def _ema(werte: list[float], n: int) -> list[float]:
    k = 2.0 / (n + 1)
    out = [werte[0]]
    for x in werte[1:]:
        out.append(x * k + out[-1] * (1 - k))
    return out


def btc_phasen(btc: list[Kerze]) -> dict[str, str]:
    """Datum -> BULLE / SEITWAERTS / BAER, nur aus Daten BIS zu diesem Tag.

    Dieselbe EMA-Ordnung, die `regime.py` fuer `btc_trend_label` verwendet.
    Bewusst NICHT die volle Regime-Logik: deren zweite Bedingung ist Fear &
    Greed, und den gibt es historisch nicht. Genau diese ODER-Bedingung ist
    ohnehin der Grund, warum das Live-Regime nie etwas anderes als "baer"
    sagt - die EMA-Ordnung allein variiert (35 / 29 / 36 % der Tage).
    """
    schluss = [k.close for k in btc]
    e20, e50, e200 = _ema(schluss, 20), _ema(schluss, 50), _ema(schluss, 200)
    phasen: dict[str, str] = {}
    for i in range(200, len(btc)):
        if e20[i] > e50[i] > e200[i]:
            phasen[btc[i].date] = "BULLE"
        elif e20[i] < e50[i] < e200[i]:
            phasen[btc[i].date] = "BAER"
        else:
            phasen[btc[i].date] = "SEITWAERTS"
    return phasen


def stabile_tage(phasen: dict[str, str]) -> dict[str, str]:
    """Nur Tage, die in einem Block von >= MIN_BLOCK gleichen Tagen liegen."""
    daten = sorted(phasen)
    fest: dict[str, str] = {}
    lauf: list[str] = []
    for tag in daten + [None]:
        if lauf and (tag is None or phasen[tag] != phasen[lauf[0]]):
            if len(lauf) >= MIN_BLOCK:
                for t in lauf:
                    fest[t] = phasen[t]
            lauf = []
        if tag is not None:
            lauf.append(tag)
    return fest


def waehle_anker(reihen: dict[str, list[Kerze]], fest: dict[str, str],
                 je_arm: int, je_symbol: int) -> dict[str, list[tuple[str, int]]]:
    """Je Arm gleich viele Anker, ueber Symbole UND Zeit gestreut.

    Die Streuung ist kein Schoenheitsdetail: liegen alle Anker eines Arms auf
    wenigen Tagen, misst der Armvergleich einen Kalendervergleich. Genau diese
    Falle hat am 09.08. schon einmal einen Anbietervergleich entwertet.
    """
    je_arm_anker: dict[str, list[tuple[str, int]]] = {a: [] for a in ARME}
    # Kandidaten JE SYMBOL sammeln, nicht in eine gemeinsame Liste. Die erste
    # Fassung sortierte alles nach (Datum, Symbol) und lief mit fester
    # Schrittweite darueber - bei mehreren Symbolen pro Tag trifft eine feste
    # Schrittweite dann systematisch immer dasselbe Symbol. Der Selbsttest
    # (teste_regimephasen.py, D1g) hat genau das gefunden: von zwei
    # gleichwertigen Symbolen kam nur eines je vor. Das waere im echten Lauf
    # eine stille Symbolverzerrung gewesen, und CC4 haette sie als
    # "Konzentration" gemeldet, ohne die Ursache zu zeigen.
    je_symbol_kand: dict[str, dict[str, list[int]]] = {
        a: defaultdict(list) for a in ARME}
    for sym, reihe in sorted(reihen.items()):
        if sym in AUSGESCHLOSSEN or len(reihe) < VORLAUF_MIN + HORIZONT + 5:
            continue
        for i in range(VORLAUF_MIN, len(reihe) - HORIZONT - 2):
            arm = fest.get(reihe[i].date)
            if arm:
                je_symbol_kand[arm][sym].append(i)
    for arm in ARME:
        # Aus JEDEM Symbol gleichmaessig ueber die Zeit gestreute Anker ziehen -
        # und dann REIHUM einsammeln, nicht der Reihe nach. Das Reihum ist der
        # Punkt: bei `je_arm` kleiner als (Symbole x je_symbol) wuerde jedes
        # andere Verfahren am Ende Symbole abschneiden, und genau die
        # Symbolabdeckung ist hier die knappe Groesse (nur 15 bis 19 Symbole je
        # Arm ueberhaupt vorhanden). Reihum heisst: erst bekommt jedes Symbol
        # einen Anker, dann jedes einen zweiten, und so fort.
        je_sym_gezogen: dict[str, list[int]] = {}
        for sym, indizes in sorted(je_symbol_kand[arm].items()):
            if not indizes:
                continue
            schritt = max(1, len(indizes) // je_symbol)
            je_sym_gezogen[sym] = indizes[::schritt][:je_symbol]
        gezogen: list[tuple[str, int]] = []
        for runde in range(je_symbol):
            for sym in sorted(je_sym_gezogen):
                if runde < len(je_sym_gezogen[sym]) and len(gezogen) < je_arm:
                    gezogen.append((sym, je_sym_gezogen[sym][runde]))
        je_arm_anker[arm] = gezogen
    return je_arm_anker


def vergleiche_arme(a: list[dict], b: list[dict], feld: str,
                    ist_anteil: bool = False) -> dict:
    """Armunterschied JE SYMBOL gepaart, mit Cluster-Bootstrap ueber Symbole.

    WARUM GEPAART JE SYMBOL. Die Arme sitzen zwangslaeufig auf verschiedenen
    Tagen - die Marktphase IST das Datum. Damit ist der Vergleich unpaariert,
    und jede Symbolungleichheit zwischen den Armen geht ungefiltert in den
    Unterschied ein. Ein Arm mit mehr volatilen Kleinwerten haette weitere
    Stops, ohne dass die Marktphase etwas damit zu tun haette.

    Der Ausweg: den Unterschied je Symbol bilden und nur Symbole verwenden, die
    in BEIDEN Armen vorkommen. Damit kuerzt sich die Symbolzusammensetzung
    heraus, und die Streuung ueber Symbole wird zur Fehlerquelle - genau das,
    was `_cluster_bootstrap` und der Wild-Cluster-Test behandeln.

    WARUM ZUSAETZLICH DER WILD-CLUSTER-TEST. Cameron/Gelbach/Miller: cluster-
    robuste Verfahren ueber-verwerfen bei fuenf bis dreissig Clustern. Wir
    liegen mit 15 bis 19 Symbolen mitten in diesem Bereich.
    """
    from bewerte_fakt_wirkung import _cluster_bootstrap, _wild_cluster_p_wert

    def je_symbol(zeilen: list[dict]) -> dict[str, float]:
        eimer: dict[str, list[float]] = defaultdict(list)
        for z in zeilen:
            w = z.get(feld)
            if ist_anteil:
                w = 1.0 if w else 0.0
            if w is None:
                continue
            eimer[z["symbol"]].append(float(w))
        return {s: statistics.fmean(v) for s, v in eimer.items() if v}

    ma, mb = je_symbol(a), je_symbol(b)
    gemeinsam = sorted(set(ma) & set(mb))
    if len(gemeinsam) < 2:
        return {"symbole_gemeinsam": len(gemeinsam), "wirkung": None}
    diffs = [mb[s] - ma[s] for s in gemeinsam]
    unten, oben = _cluster_bootstrap(diffs, gemeinsam)
    p = _wild_cluster_p_wert(diffs, gemeinsam)
    streu = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
    mittel = statistics.fmean(diffs)
    # Wie viele Symbole braeuchte es, um GENAU diesen Effekt nachzuweisen?
    # Dieselbe Formel wie in werte_regime_llm_aus.py - bewusst nicht neu
    # erfunden, damit zwei Messungen dieselbe Sprache sprechen.
    noetig = ((1.96 * streu / abs(mittel)) ** 2) if mittel else None
    return {"symbole_gemeinsam": len(gemeinsam), "wirkung": mittel,
            "ci_unten": unten, "ci_oben": oben, "wild_p": p,
            "streuung": streu, "noetige_symbole": noetig}


def _kennzahlen(zeilen: list[dict]) -> dict:
    """Die vier Primaergroessen plus Streuung. Reine Verhaltensgroessen."""
    mit_zonen = [z for z in zeilen if z.get("crv") is not None]
    eroeffnen = [z for z in zeilen if z.get("action") == "ERÖFFNEN"]
    n = len(zeilen)
    if not n:
        return {}
    stops = [z["stop_pct"] for z in mit_zonen if z.get("stop_pct")]
    crvs = [z["crv"] for z in mit_zonen]
    longs = [z for z in mit_zonen if z.get("richtung") == "LONG"]
    unbrauchbar = [z for z in zeilen if z.get("zonen_status") == "unbrauchbar"]
    mit_fazit = [z for z in zeilen if z.get("fazit_folgen")]
    ja = [z for z in mit_fazit if z["fazit_folgen"] == "ja"]
    nein = [z for z in mit_fazit if z["fazit_folgen"] == "nein"]
    return {
        "n": n,
        "n_mit_zonen": len(mit_zonen),
        "unbrauchbare_zonen_quote": len(unbrauchbar) / n,
        "eroeffnen_quote": len(eroeffnen) / n,
        # NAHT 2 der Kette: stimmt das Modell seiner eigenen Empfehlung zu?
        # Produktion zum Vergleich: ja 1,6 %, nein 7,0 %, Rest mit_vorbehalt.
        "selbst_ja_quote": (len(ja) / len(mit_fazit)) if mit_fazit else None,
        "selbst_nein_quote": (len(nein) / len(mit_fazit)) if mit_fazit else None,
        "long_anteil": (len(longs) / len(mit_zonen)) if mit_zonen else None,
        "crv_ab_2": (sum(1 for c in crvs if c >= 2.0) / len(crvs)) if crvs else None,
        "crv_median": statistics.median(crvs) if crvs else None,
        "stop_median": statistics.median(stops) if stops else None,
        "symbole": len({z["symbol"] for z in zeilen}),
    }


def _zeile(sym: str, reihe: list[Kerze], i: int, antwort: dict, arm: str,
           label: str) -> dict:
    """Eine Ergebniszeile - Verhaltensgroessen zuerst, Ergebnis nachrangig."""
    # `eigene_einschaetzung` ist die SELBSTZUSTIMMUNG - die zweite Naht der
    # Kette und nach der Produktionsmessung vom 09.08. die auffaelligste:
    # 18 von 1.134 "ja" (1,6 %), und alle 18 sind SHORT. 45 % der Vorbehalte
    # nennen als Grund das Regime - eine Groesse, die sich in der gesamten
    # Historie nie geaendert hat. Ohne dieses Feld waere genau der
    # interessanteste Uebergang im Messlauf nicht enthalten.
    selbst = antwort.get("eigene_einschaetzung") or {}
    satz = {
        "arm": arm, "label_im_prompt": label, "symbol": sym,
        "datum": reihe[i].date, "action": antwort.get("action"),
        "richtung": antwort.get("richtung"),
        "konfidenz": antwort.get("confidence_pct"),
        "modell": antwort.get("_modell"),
        "fazit_folgen": selbst.get("folgen"),
        "fazit_kurzfazit": selbst.get("kurzfazit"),
    }
    # WARUM DER STATUS UND NICHT NUR EIN STILLES WEGLASSEN. `_zonen()` folgt
    # exakt `_zonen_absolut()` aus dem Backward-Tracking: die Richtung wird aus
    # `take_profit < entry` abgeleitet, und widerspruechliche Zonensaetze
    # (z. B. deklariertes SHORT mit Ziel ueber dem Einstieg) ergeben None.
    # Die Produktion verwirft sie genauso - sie landen dort in der Kategorie
    # "keine Zonen erarbeitet", die ueber Wochen der groesste Einzelposten des
    # Deadloops war (23,9 %). Sie hier stillschweigend zu ueberspringen wuerde
    # also ausgerechnet die interessanteste Kategorie unsichtbar machen.
    z = _zonen(antwort)
    satz["zonen_status"] = "ok" if z else (
        "keine_zonen" if antwort.get("action") == "HALTEN" else "unbrauchbar")
    if z:
        # DIE ABSOLUTEN ZONENWERTE MITSCHREIBEN, nicht nur die relativen.
        # Ohne Entry/Stop/Ziel in Kurseinheiten laesst sich die live gefahrene
        # Ausstiegsregel (Trailing ab +1R) NACHTRAEGLICH nicht am Kursverlauf
        # entlangfahren - und damit waere die Frage "ist das geaenderte
        # Verhalten auch BESSER" aus diesem Lauf nicht beantwortbar. Ein Lauf,
        # der nur zeigt, dass ein Eingriff mehr Signale erzeugt, misst
        # Lockerung statt Qualitaet.
        satz["entry"] = z["entry"]
        satz["stop"] = z["stop"]
        satz["ziel"] = z["ziel"]
        satz["risiko"] = z["risiko"]
        satz["ist_short"] = z["ist_short"]
        satz["crv"] = round(z["crv"], 4)
        satz["stop_pct"] = round(z["risiko"] / z["entry"] * 100, 3)
        satz["ziel_pct"] = round(z["chance"] / z["entry"] * 100, 3)
        satz["richtung"] = "SHORT" if z["ist_short"] else "LONG"
        # NACHRANGIG, siehe Modul-Docstring: statische Barrieren sind nicht
        # das live gefahrene Modell (Trailing ab +1R seit 05.08.).
        satz["nachrangig_statisch"] = _auswerten(z, reihe, i)
        # DAS LIVE GEFAHRENE MODELL. Ohne diese Zeilen beantwortet der Lauf
        # nur "aendert der Eingriff das Verhalten" - nicht "ist das geaenderte
        # Verhalten BESSER". Ein Eingriff, der mehr Signale erzeugt, aber
        # schlechtere, waere Lockerung statt Qualitaet.
        from bewerte_dynamisch import bewerte_mit_trailing
        kerzen = reihe[i + 1:i + 1 + HORIZONT]
        dyn = bewerte_mit_trailing(z, kerzen, horizont=HORIZONT)
        if dyn:
            satz["dyn_ausgang"] = dyn.ausgang
            satz["dyn_r"] = round(dyn.r, 4)
            satz["dyn_mfe_r"] = round(dyn.mfe_r, 4)
            satz["dyn_tag"] = dyn.tag
        # Konservative Variante: Haltedauer auf 3 Tage gekappt - das P75 der
        # in der Produktion gemessenen Zeit bis zur Ueberholung (Median 0,7,
        # P75 2,9 Tage, n=43). Damit ist die Ueberholung nicht simuliert,
        # aber ihre Groessenordnung als BEKANNTE Abschneidung abgebildet.
        dyn3 = bewerte_mit_trailing(z, kerzen, horizont=HORIZONT, kappung_tage=3)
        if dyn3:
            satz["dyn3_ausgang"] = dyn3.ausgang
            satz["dyn3_r"] = round(dyn3.r, 4)
    return satz


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--je-arm", type=int, default=30)
    p.add_argument("--je-symbol", type=int, default=3)
    p.add_argument("--pause", type=float, default=1.0)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--cc2", type=int, default=15,
                   help="wie viele BULLE-Anker mit erzwungenem baer-Label")
    p.add_argument("--cc3", type=int, default=15,
                   help="wie viele Anker doppelt, fuer den Rauschboden")
    p.add_argument("--ausgabe", default="regimephasen.json")
    args = p.parse_args()

    reihen = lade_reihen()
    btc = reihen.get("BTC")
    if not btc:
        print("Keine BTC-Reihe - ohne sie ist keine Phase bestimmbar.")
        return 1
    phasen = btc_phasen(btc)
    fest = stabile_tage(phasen)
    verteilung = Counter(fest.values())
    print(f"BTC-Reihe: {len(btc)} Tage, {btc[0].date} .. {btc[-1].date}")
    print(f"Stabile Tage (Block >= {MIN_BLOCK}): {len(fest)} von {len(phasen)}")
    for a in ARME:
        print(f"   {a:12} {verteilung.get(a, 0):5} Tage")

    anker = waehle_anker(reihen, fest, args.je_arm, args.je_symbol)
    print()
    for a in ARME:
        tage = sorted({reihen[s][i].date for s, i in anker[a]})
        print(f"   {a:12} {len(anker[a]):4} Anker, "
              f"{len({s for s, _ in anker[a]})} Symbole, "
              f"{len(tage)} verschiedene Tage"
              + (f", {tage[0]} .. {tage[-1]}" if tage else ""))
    if any(len(anker[a]) < args.je_arm for a in ARME):
        print("\nWARNUNG: nicht jeder Arm ist voll besetzt - Armvergleich "
              "ungleichgewichtig.")

    # --- MINDESTANFORDERUNGEN, VOR dem Lauf geprueft ----------------------
    # Nicht die Ankerzahl ist die knappe Groesse, sondern die SYMBOLZAHL. Der
    # Armvergleich rechnet je Symbol gepaart (siehe vergleiche_arme), also ist
    # die Zahl der in beiden Armen vorkommenden Symbole die effektive
    # Stichprobe. Sie hier zu melden verhindert den teuersten Fehler dieses
    # Projekts: einen Lauf zu fahren, dessen Aussagekraft von vornherein zu
    # klein war, und das erst hinterher zu merken.
    print("\n=== MINDESTANFORDERUNGEN (vor dem Lauf) ===")
    sym_je_arm = {a: {s for s, _ in anker[a]} for a in ARME}
    genug = True
    for x, y in (("BULLE", "BAER"), ("SEITWAERTS", "BAER"), ("BULLE", "SEITWAERTS")):
        gemeinsam = sym_je_arm[x] & sym_je_arm[y]
        marke = "" if len(gemeinsam) >= MIN_CLUSTER else "   <-- UNTER MINIMUM"
        if len(gemeinsam) < MIN_CLUSTER:
            genug = False
        print(f"  {x:11} gegen {y:11} gemeinsame Symbole {len(gemeinsam):3}"
              f"  (Minimum {MIN_CLUSTER}){marke}")
    print(f"  Anker je Arm: " + ", ".join(f"{a}={len(anker[a])}" for a in ARME))
    print("  Nachweisbar ist ein Effekt ab etwa 1 Standardabweichung der")
    print("  Symbol-Differenzen geteilt durch Wurzel(gemeinsame Symbole) x 1,96.")
    print("  Die tatsaechlich noetige Symbolzahl steht nach dem Lauf je Groesse.")
    if not genug:
        print("  ACHTUNG: mindestens ein Armpaar liegt unter der Clusterzahl,")
        print("  ab der ein Cluster-Bootstrap tragfaehig ist. Der Lauf ist")
        print("  damit HYPOTHESEGENERIEREND, nicht nachweisend - und genau so")
        print("  gehoert er berichtet.")

    if args.trocken:
        # WARUM DIESER MOCK NICHT DETERMINISTISCH IST. Ein Mock, der immer
        # dasselbe antwortet, laesst CC3 mit einem Rauschboden von 0 % und CC1
        # mit 0 % SHORT durchlaufen - beide Waechter bestuenden bzw. schluegen
        # dann trivial an, ohne je geprueft zu haben, ob sie funktionieren.
        # Genau dieser degenerierte Selbsttest ist am 09.08. schon einmal
        # passiert (Nachweisrahmen, Rauschboden 0 -> "IM RAUSCHEN" bestand
        # sinnlos). Der Mock bildet deshalb beides nach: einen SHORT-Ueberhang
        # in der Groessenordnung der Produktion und eine Wiederholungs-
        # Instabilitaet in der Groessenordnung der gemessenen ~12 %.
        zaehler = [0]

        def frage(fakten, _label, _sym):
            zaehler[0] += 1
            preis = (fakten.get("preis") or {}).get("usd") or 100.0
            n = zaehler[0]
            streu = ((n * 2654435761) >> 16) % 100 / 100.0
            if n % 9 == 0:
                return {"action": "HALTEN", "_modell": "trocken"}
            # ~80 % SHORT wie in der Produktion (470 von 568)
            ist_short = (((n * 40503) >> 8) % 100) < 80
            stop_rel = 0.05 + streu * 0.06
            ziel_rel = stop_rel * (1.6 + streu * 1.2)
            richtung = -1.0 if ist_short else 1.0
            return {"action": "ERÖFFNEN",
                    "richtung": "SHORT" if ist_short else "LONG",
                    "_modell": "trocken",
                    "confidence_pct": 60 + int(streu * 20),
                    "entry": {"usd_von": preis, "usd_bis": preis},
                    "stop_loss": {"usd_von": preis * (1 - richtung * stop_rel),
                                  "usd_bis": preis * (1 - richtung * stop_rel)},
                    "take_profit": {"usd_von": preis * (1 + richtung * ziel_rel),
                                    "usd_bis": preis * (1 + richtung * ziel_rel)}}
    else:
        import os

        import config as config_module
        from agent import llm_schema
        from agent.krypto.hebel_analyst import SYSTEM_PROMPT, _validate_hebel
        from api.openrouter import OpenRouterClient
        config_module.load_env()
        schluessel = os.environ.get("OPENROUTER_API_KEY")
        if not schluessel:
            print("OPENROUTER_API_KEY fehlt.")
            return 1
        client = OpenRouterClient(schluessel)

        # DENSELBEN Weg gehen wie die Produktion, nicht einen aehnlichen.
        # OpenRouter ist der EINZIGE Anbieter, der das strikte Schema bekommt
        # (gemessen 09.08.: 2/38 und 2/20 Formfehler unter json_object, 0 unter
        # Schema). Ein Messlauf mit `json_object` wuerde also ausgerechnet die
        # schlechtere der beiden bekannten Konfigurationen vermessen und die
        # Formfehler dem Marktphasen-Arm zuschreiben.
        antwortformat = llm_schema.response_format_fuer(
            client, "agent.krypto.hebel_analyst")
        strikt = antwortformat.get("type") == "json_schema"
        print(f"\nAntwortformat: {antwortformat.get('type')}"
              + ("" if strikt else "   <-- NICHT strikt, siehe llm_schema.py"))
        if not strikt:
            print("ABBRUCH: fuer OpenRouter ist das strikte Schema die gemessen")
            print("bessere Konfiguration. Faellt es auf json_object zurueck,")
            print("liegt eine Schema-Luecke vor - die gehoert repariert, nicht")
            print("umgangen.")
            return 2

        def frage(fakten, _label, sym):
            time.sleep(args.pause)
            roh = client.chat(
                [{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": json.dumps(fakten, ensure_ascii=False)}],
                temperature=0.2, response_format=antwortformat)
            antwort = json.loads(roh)
            # Die ECHTE Validierung der Produktion. Ohne sie wuerde eine
            # formal kaputte Antwort als gueltiger Messpunkt gezaehlt.
            antwort = _validate_hebel(antwort, sym)
            modell = getattr(client, "letztes_modell", None)
            if modell:
                antwort["_modell"] = modell
            return antwort

    beginn_lauf = [time.time()]

    def lauf(paare: list[tuple[str, int]], arm: str, label: str,
             markierung: str) -> list[dict]:
        raus, fehler = [], Counter()
        beginn_lauf[0] = time.time()
        for nr, (sym, i) in enumerate(paare, 1):
            reihe = reihen[sym]
            fakten = baue_historische_fakten(sym, reihe, i, btc)
            if fakten is None:
                fehler["kein_faktensatz"] += 1
                continue
            # DAS ist die eigentliche Manipulation dieses Laufs - siehe
            # Modul-Docstring: "nicht rekonstruierbar" wuerde Abstention
            # ausloesen statt die Marktphase zu messen.
            fakten.setdefault("regime", {})
            fakten["regime"] = dict(fakten["regime"])
            fakten["regime"]["wert"] = label
            fakten["regime"]["quelle"] = ("historische EMA-Ordnung des BTC "
                                          "(EMA20/50/200) am Ankertag")
            try:
                antwort = frage(fakten, label, sym)
            except Exception as exc:  # noqa: BLE001
                fehler[type(exc).__name__] += 1
                continue
            raus.append(_zeile(sym, reihe, i, antwort, markierung, label))
            # ZWISCHENPRUEFUNG (Nutzer-Vorgabe 09.08.: waehrend des Laufs
            # pruefen, nicht erst danach). Ein Lauf ueber zwei Stunden, der am
            # Ende auffaellt, hat zwei Stunden gekostet. Gemeldet wird deshalb
            # laufend das, woran man einen Defekt frueh erkennt: Fehlerrate,
            # Modellrotation, unbrauchbare Zonen und die beiden Kennzahlen,
            # um die es geht.
            if nr % 10 == 0 or nr == len(paare):
                k = _kennzahlen(raus)
                modelle = {z.get("modell") for z in raus if z.get("modell")}
                rotiert = "" if len(modelle) <= 1 else f"  ROTATION {len(modelle)} Modelle"
                warnung = ""
                if k.get("unbrauchbare_zonen_quote", 0) > 0.5:
                    warnung = "  <-- ueber 50 % unbrauchbare Zonen"
                if fehler and sum(fehler.values()) > nr * 0.3:
                    warnung = "  <-- Fehlerrate ueber 30 %"
                verstrichen = time.time() - beginn_lauf[0]
                je_fall = verstrichen / max(1, nr)
                print(f"   {markierung:16} {nr:4}/{len(paare)}  "
                      f"gueltig {len(raus):4}  Fehler {sum(fehler.values()):3}  "
                      f"unbrauchb. Zonen {k.get('unbrauchbare_zonen_quote', 0):5.1%}  "
                      f"EROEFF {k.get('eroeffnen_quote', 0):5.1%}  "
                      f"selbst-ja {(k.get('selbst_ja_quote') or 0):5.1%}  "
                      f"{je_fall:4.1f} s/Fall{rotiert}{warnung}")
        if fehler:
            print(f"   {markierung:16} Fehler: {dict(fehler)}")
        return raus

    print("\n=== HAUPTARME ===")
    ergebnis: dict[str, list[dict]] = {}
    for a in ARME:
        ergebnis[a] = lauf(anker[a], a, LABEL[a], a)

    print("\n=== CC2: BULLE-Daten mit erzwungenem baer-Label ===")
    ergebnis["CC2_bulle_als_baer"] = lauf(
        anker["BULLE"][:args.cc2], "BULLE", "baer", "CC2_bulle_als_baer")

    print("\n=== CC3: Rauschboden (dieselben Anker ein zweites Mal) ===")
    cc3_paare = anker["BAER"][:args.cc3]
    ergebnis["CC3_wiederholung"] = lauf(
        cc3_paare, "BAER", LABEL["BAER"], "CC3_wiederholung")

    print("\n" + "=" * 78)
    print("KENNZAHLEN JE ARM (Primaergroessen, reines Modellverhalten)")
    print(f"{'Arm':22} {'n':>4} {'Sym':>4} {'EROEFF':>7} {'LONG':>7} "
          f"{'CRV>=2':>7} {'CRVmed':>7} {'Stopmed':>8} {'selbst-ja':>9} "
          f"{'o.Zonen':>8}")
    kz = {}
    for name, zeilen in ergebnis.items():
        k = _kennzahlen(zeilen)
        kz[name] = k
        if not k:
            print(f"{name:22} - keine Zeilen")
            continue
        def f(x, p=False):
            if x is None:
                return "   -"
            return f"{x:6.1%}" if p else f"{x:7.2f}"
        print(f"{name:22} {k['n']:4} {k['symbole']:4} "
              f"{f(k['eroeffnen_quote'], True):>7} {f(k['long_anteil'], True):>7} "
              f"{f(k['crv_ab_2'], True):>7} {f(k['crv_median']):>7} "
              f"{f(k['stop_median']):>8} {f(k['selbst_ja_quote'], True):>9} "
              f"{f(k['unbrauchbare_zonen_quote'], True):>8}")

    print()
    print("=== ARMVERGLEICH, je Symbol gepaart, Cluster-Bootstrap ueber Symbole ===")
    print("   (positive Wirkung = im erstgenannten Arm hoeher als im BAER-Arm)")
    print(f"{'Vergleich':26} {'Groesse':12} {'Sym':>4} {'Wirkung':>9} "
          f"{'Intervall':>22} {'wild p':>7} {'noetig Sym':>11}")
    vergleiche = {}
    for x in ("BULLE", "SEITWAERTS"):
        for feld, ist_anteil, name in (
                ("richtung", False, "LONG-Anteil"),
                ("crv", False, "CRV"),
                ("stop_pct", False, "Stop %"),
        ):
            if feld == "richtung":
                za = [{**z, "richtung": 1.0 if z.get("richtung") == "LONG" else 0.0}
                      for z in ergebnis["BAER"] if z.get("richtung")]
                zb = [{**z, "richtung": 1.0 if z.get("richtung") == "LONG" else 0.0}
                      for z in ergebnis[x] if z.get("richtung")]
            else:
                za, zb = ergebnis["BAER"], ergebnis[x]
            v = vergleiche_arme(za, zb, feld, ist_anteil)
            vergleiche[f"{x}_gegen_BAER_{feld}"] = v
            if v.get("wirkung") is None:
                print(f"{x + ' gegen BAER':26} {name:12} "
                      f"{v['symbole_gemeinsam']:4}   zu wenige gemeinsame Symbole")
                continue
            ci = (f"[{v['ci_unten']:+.3f}; {v['ci_oben']:+.3f}]"
                  if v["ci_unten"] is not None else "-")
            noetig = (f"{v['noetige_symbole']:11.0f}"
                      if v["noetige_symbole"] else "          -")
            print(f"{x + ' gegen BAER':26} {name:12} {v['symbole_gemeinsam']:4} "
                  f"{v['wirkung']:+9.3f} {ci:>22} "
                  f"{(v['wild_p'] if v['wild_p'] is not None else float('nan')):7.3f}"
                  f"{noetig}")
    print("  LESEART: enthaelt das Intervall die Null, ist es kein Nachweis.")
    print("  Steht unter 'noetig Sym' eine Zahl groesser als die vorhandene,")
    print("  war der Lauf fuer GENAU DIESEN Effekt zu klein - das ist eine")
    print("  Aussage ueber die Messung, nicht ueber die Welt.")

    print()
    print("=== CC1 REPRODUKTION: trifft der BAER-Arm die Produktion? ===")
    k = kz.get("BAER") or {}
    if k.get("long_anteil") is not None:
        short_anteil = 1 - k["long_anteil"]
        d_short = abs(short_anteil - PROD_SHORT_ANTEIL)
        d_stop = (abs(k["stop_median"] - PROD_STOP_MEDIAN)
                  if k.get("stop_median") else None)
        print(f"  SHORT-Anteil  Simulation {short_anteil:6.1%}   "
              f"Produktion {PROD_SHORT_ANTEIL:6.1%}   Abstand {d_short:5.1%}")
        if d_stop is not None:
            print(f"  Stop-Median   Simulation {k['stop_median']:6.2f} %  "
                  f"Produktion {PROD_STOP_MEDIAN:6.2f} %  "
                  f"Faktor {k['stop_median']/PROD_STOP_MEDIAN:5.2f}")
        streng = d_short <= 0.15 and (d_stop is None or
                                      k["stop_median"] <= PROD_STOP_MEDIAN * 1.5)
        print(f"  URTEIL: {'REPRODUZIERT' if streng else 'REPRODUZIERT NICHT'}")
        if not streng:
            print("  -> Der Aufbau bildet die Produktion nicht ab. Die Armvergleiche")
            print("     darunter sind damit NICHT auf das Live-System uebertragbar.")
            print("     Das ist ein Abbruchkriterium, keine Fussnote.")

    print()
    print("=== CC3 RAUSCHBODEN: dieselbe Eingabe, zweiter Lauf ===")
    erst = {(z["symbol"], z["datum"]): z for z in ergebnis["BAER"]}
    dreher = gleich = 0
    for z in ergebnis["CC3_wiederholung"]:
        a = erst.get((z["symbol"], z["datum"]))
        if not a or not a.get("richtung") or not z.get("richtung"):
            continue
        if a["richtung"] == z["richtung"]:
            gleich += 1
        else:
            dreher += 1
    if gleich + dreher:
        print(f"  Paare {gleich + dreher}, Richtung gedreht {dreher} "
              f"= {dreher/(gleich+dreher):.1%}")
        print("  Zum Vergleich: 09.08. an nemotron gemessen ~12 %.")
        print("  JEDER Armunterschied unterhalb dieses Bodens ist kein Befund.")
    else:
        print("  Keine vergleichbaren Paare.")

    print()
    print("=== CC4 KONZENTRATION: traegt ein einzelnes Symbol den Arm? ===")
    for a in ARME:
        je_sym = Counter(z["symbol"] for z in ergebnis[a]
                         if z.get("richtung") == "LONG")
        gesamt = sum(je_sym.values())
        if gesamt:
            top, anzahl = je_sym.most_common(1)[0]
            print(f"  {a:12} LONG-Signale {gesamt:3}, groesstes Symbol "
                  f"{top} mit {anzahl} = {anzahl/gesamt:5.1%}")
        else:
            print(f"  {a:12} keine LONG-Signale")

    pathlib.Path(args.ausgabe).write_text(
        json.dumps({"kennzahlen": kz, "zeilen": ergebnis,
                    "min_block": MIN_BLOCK, "ausgeschlossen": sorted(AUSGESCHLOSSEN)},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
