"""Was wuergt die Selbstzustimmung ab? 2x2-faktoriell mit Rauschboden (09.08.)

DIE ZWEI THESEN (Nutzer-Formulierung 09.08.):

    A  DEFENSIVMODUS      Vorsicht gegenueber der eigenen Bewertung -
                          UNGERICHTET, alle Signale gleichermassen.
    B  REGIME ERSCHLAEGT  Die Bewertung laeuft nicht ueber die Vorgaben,
                          sondern wird vom Regime abgewuergt - GERICHTET.

BEOBACHTUNGSLAGE aus der Produktion (09.08., n=1.134 mit Fazit):

    LONG    452:  ja  0 (0,0 %)   nein 76 (16,8 %)
    SHORT   682:  ja 18 (2,6 %)   nein  3 (0,4 %)

    59 LONG mit Konfidenz >= 70 - davon 0 mit "ja". Das staerkste stand bei 78.
    Keine hohe Schwelle (dann kaemen die Besten durch), sondern eine DECKE.
    Innerhalb SHORT trennt die Konfidenz "ja" von "mit_vorbehalt" gar nicht
    (68 gegen 68) - Signatur eines UNKONDITIONIERTEN Vorbehalts.

DER MECHANISMUS STEHT IN UNSEREM PROMPT, nicht im Modell:

    Regel 2   macht den Regime-Konflikt zu einem von NUR ZWEI Faellen, fuer die
              eine Daempfung von *Konfidenz UND Hebel-Vorschlag* ausdruecklich
              verlangt wird - mit Erlaubnis, die 75-%-Untergrenze zu
              unterschreiten.
    Regel 26  sagt woertlich, ein "bereits laufender Regime-Konflikt" koenne
              fuer ein negatives Selbsturteil ausreichen, "selbst wenn
              confidence_pct hoch ist".
    Der Flag  entsteht deterministisch in unserem Code:
                  (regime=="baer" and trigger=="LONG")
               or (regime=="bulle" and trigger=="SHORT")
              Da `regime` in der GESAMTEN Historie "baer" war, ist das eine
              permanente Strafe auf genau eine Handelsrichtung.

WARUM ADDITIV STATT SUBTRAKTIV - der Fund, der Stunden Muell verhindert hat.
Der historische Faktensatz enthaelt WEDER `systemguete` NOCH
`richtungs_konflikt_mit_trigger` (geprueft 09.08.). Ein Arm, der sie
ENTFERNT, haette nichts entfernt und nach zwei Stunden garantiert einen
Nulleffekt gemeldet, der wie ein Befund aussieht. Deshalb wird der verdaechtige
Mechanismus HINZUGEFUEGT und geprueft, ob der Effekt ERSCHEINT - eine
Positivkontrolle, die staerker ist als eine Entfernung.

DIE FUENF ARME, alle auf DENSELBEN Ankern, gepaart je Anker:

    A1    Grundlinie
    A2    identisch zu A1  ->  RAUSCHBODEN. Ohne ihn ist kein Effekt lesbar;
          `nemotron` dreht bei identischer Eingabe in ~12 % die Richtung.
    E1    + systemguete (echte, negative Produktionszahlen)
    E2    + Regime-Flag samt Hinweistext
    E12   beides  ->  Wechselwirkung und zugleich der produktionsnaechste Arm

EIN DETAIL, DAS DEN ARM SONST VERDORBEN HAETTE. Der historische Faktensatz
fuehrt `historische_erfolgsquote` in `nicht_verfuegbar`. Speist man
`systemguete` ein, ohne diesen Eintrag zu entfernen, widerspricht sich der
Faktensatz - er behauptet gleichzeitig, die Erfolgsquote sei nicht verfuegbar,
und liefert sie mit. Und genau die Erfolgsquote nennt das Modell in der
Produktion als Vorbehaltsgrund. E1/E12 raeumen den Eintrag deshalb mit ab.

DIE MESSGROESSEN - STETIG ZUERST. Die kategoriale `ja`-Quote ist das
Phaenomen, aber mit 1,6 % ein schwaches Messinstrument. Die Regeln selbst
nennen zwei STETIGE Groessen, die gedaempft werden sollen, und eine dritte als
Vermittler:

    confidence_pct        Regel 2 verlangt Daempfung
    hebel_vorschlag       Regel 2 verlangt Daempfung - zweites explizites Ziel
    gegenszenario_pct     Regel 2: "eine hohe Gegenszenario-Wahrscheinlichkeit
                          (Bear bei LONG, Bull bei SHORT) sollte Konfidenz und
                          Hebel-Vorschlag daempfen" - der Vermittler
    long_anteil, crv, stop_pct, fazit ja/nein

VORHERSAGEN, VOR dem Lauf festgelegt:

    Gilt B:  E2 senkt LONG-Anteil und/oder LONG-Konfidenz und -Hebel deutlich,
             SHORT bleibt weitgehend unberuehrt.
    Gilt A:  E1 senkt die ja-Quote und die Konfidenz in BEIDEN Richtungen.
    Gilt beides: E12 zeigt beide Muster; die Wechselwirkung sagt, ob sie sich
             verstaerken oder nur addieren.
    Gilt keins: alle Effekte liegen im A1/A2-Rauschboden.

GEGENKONTROLLE zu E2, ohne die der Befund nichts wert ist: SHORT darf sich
NICHT wesentlich aendern. Bricht SHORT mit ein, ist der Flag ein genereller
Daempfer und kein Richtungsfilter - dann ist die Deutung falsch, egal wie gut
die LONG-Zahl aussieht.

WAS DIESER LAUF NEBENBEI KORRIGIERT. `teste_regime_llm.py` lieferte am 06.08.
einen Nullbefund fuer das Regime - es tauscht aber NUR `regime.wert` und
`regime_profil` und laesst `richtungs_konflikt_mit_trigger` unberuehrt. Die
Regeln 2 und 26 haengen am FLAG, nicht am Label. Der Nullbefund misst also das
Wort, nicht den Mechanismus.

    python messe_kettennaht_eingriffe.py --je-arm 40 --trocken
    python messe_kettennaht_eingriffe.py --je-arm 40 --ausgabe kettennaht.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import time
from collections import Counter, defaultdict

from backtest_llm1_historisch import baue_historische_fakten, lade_reihen
import messe_regimephasen_llm as M

# Die ECHTEN Produktionszahlen (Systemguete Hebel/real, Stand 09.08.). Eine
# erfundene Zahl wuerde eine andere Frage beantworten als "wirkt das, was wir
# taeglich einspeisen".
SYSTEMGUETE_ECHT = {
    "anzahl_ausgewerteter_trades": 142,
    "erwartungswert_r": -0.176,
    "sqn": -3.07,
    "sqn_einordnung": "kaum handelbar",
    "profit_factor": 0.74,
    "lesehilfe": (
        "Erwartungswert in R = durchschnittliches Ergebnis je Signal, gemessen "
        "an den bisher aufgeloesten Signalen dieses Systems."
    ),
}

# Wortgleich aus agent/krypto/hebel_analyst.py::facts() - ein umformulierter
# Hinweis waere ein anderer Reiz und damit ein anderer Versuch.
REGIME_FLAG_HINWEIS = (
    "Der Screening-Kandidat schlaegt eine Richtung vor, die dem aktuellen "
    "Regime entgegensteht (Gegen-Trend-Wette MIT Hebel - staerker verstaerktes "
    "Risiko als ohne Hebel). Wird nachtraeglich zusaetzlich deterministisch "
    "gedeckelt (siehe hebel_kontext), aber bereits hier in deiner eigenen "
    "Einschaetzung explizit gegenrechnen, nicht nur an kurzfristiger Technik "
    "festmachen."
)

# SO kommt die Trefferquote heute beim Modell an - abgefragt aus der
# Produktionskopie ueber `compute_win_rate_fact(conn, "hebel")`, nicht
# nachgebaut. Regel 14 weist das Modell an, sie "grob in die confidence_pct-
# Kalibrierung" einzubeziehen und dabei den `hinweis` zu lesen.
ERFOLGSQUOTE_ROH = {
    "anzahl_ausgewertete_signale": 94,
    "trefferquote_pct": 16.0,
    "treffer": 15,
    "fehlschlaege": 79,
    "hinweis": "Basiert auf 94 bisher ausgewerteten Signalen.",
}

# E4 - DER REPARATURKANDIDAT. Gleiche Zahlen, ergaenzter Bezugsrahmen.
#
# WARUM DAS UEBERHAUPT EINE FRAGE IST: Regel 32 (CRV-Baender) sagt woertlich,
# dort stuenden "bewusst KEINE absoluten Trefferquoten", weil die absolute
# Quote mit steigendem CRV ZWANGSLAEUFIG faellt - das Ziel liegt CRV-mal weiter
# als der Stop. Regel 14 speist dann genau eine absolute Quote ein. Das ist ein
# Widerspruch im eigenen Regelwerk: das Modell liest "16 %" ohne zu wissen, dass
# der Breakeven bei der Pflichtgrenze CRV 2,0 nicht bei 50 %, sondern bei
# 33,3 % liegt.
#
# DER EINGRIFF SITZT IM `hinweis`, NICHT IM PROMPT. Regel 14 weist an, den
# Hinweis zu lesen - der Wirkungspfad existiert also bereits. Damit bleibt E4
# eine FAKTEN-Aenderung und ist mit den uebrigen Armen vergleichbar; eine
# Prompt-Aenderung waere ein anderer Eingriffstyp und nicht mehr gepaart
# auswertbar.
#
# KONTEXT LIEFERN, URTEIL OFFENLASSEN: der Text nennt Bezugsgroesse und
# Zaehlregel, aber KEINE Handlungsanweisung. Dieselbe Linie wie beim
# systemguete-Fakt, dessen Docstring ausdruecklich davor warnt, ein
# "sei deshalb vorsichtiger" anzuhaengen.
ERFOLGSQUOTE_MIT_BEZUG = {
    **ERFOLGSQUOTE_ROH,
    "breakeven_trefferquote_pct": {"crv_2_0": 33.3, "crv_3_0": 25.0},
    "hinweis": (
        "Basiert auf 94 bisher ausgewerteten Signalen. Zur Einordnung: diese "
        "Quote ist nicht mit 50 % zu vergleichen, sondern mit dem Breakeven "
        "der eigenen Zielsetzung - bei einem CRV von 2,0 liegt er bei 33,3 %, "
        "bei 3,0 bei 25,0 % (1/(1+CRV)). Als Treffer zaehlt ausschliesslich das "
        "vollstaendige Erreichen des Take-Profit; Signale, die vorher durch "
        "eine neuere Analyse ersetzt wurden (43 Faelle), sind weder als Treffer "
        "noch als Fehlschlag enthalten."
    ),
}

ARME = ("A1", "A2", "E1_systemguete", "E2_regimeflag",
        "E3_quote_roh", "E4_quote_bezug", "E12_produktionsnah")
MIT_GUETE = {"E1_systemguete", "E12_produktionsnah"}
MIT_FLAG = {"E2_regimeflag", "E12_produktionsnah"}
# Nur diese Arme liefern die Quote WIRKLICH mit - und nur sie duerfen deshalb
# `historische_erfolgsquote` aus `nicht_verfuegbar` streichen. Der frueher
# gebaute Zustand (streichen, ohne zu liefern) haette dem Modell gesagt, die
# Quote sei verfuegbar, und dann keine geliefert - schlimmer als beides.
MIT_QUOTE = {"E3_quote_roh": ERFOLGSQUOTE_ROH,
             "E4_quote_bezug": ERFOLGSQUOTE_MIT_BEZUG,
             "E12_produktionsnah": ERFOLGSQUOTE_ROH}

# Stetige Messgroessen. Reihenfolge ist Absicht: die beiden, deren Daempfung
# Regel 2 ausdruecklich verlangt, zuerst.
STETIG = (
    ("konfidenz", "Konfidenz"),
    ("hebel", "Hebel-Vorschlag"),
    ("gegenszenario_pct", "Gegenszenario %"),
    ("crv", "CRV"),
    ("stop_pct", "Stop %"),
)


def baue_arm(fakten: dict, arm: str, label: str) -> dict:
    """Faktensatz je Arm. Gibt IMMER eine tiefe Kopie zurueck.

    Die tiefe Kopie ist Pflicht, nicht Stil: liefe ein Arm auf dem Objekt des
    vorherigen, waeren spaetere Arme stillschweigend kumulativ manipuliert -
    und der Vergleich waere zerstoert, ohne dass irgendwo ein Fehler auftaucht.
    """
    neu = json.loads(json.dumps(fakten))
    neu["regime"] = dict(neu.get("regime") or {})
    neu["regime"]["wert"] = label
    neu["regime"]["quelle"] = "historische EMA-Ordnung des BTC am Ankertag"
    if arm in MIT_GUETE:
        # NUR die Systemguete - `historische_erfolgsquote` bleibt hier
        # ausdruecklich in `nicht_verfuegbar` stehen. Es sind ZWEI Fakten:
        # `systemguete` ist Erwartungswert/SQN/Profitfaktor (Regel 31 Teil 2),
        # `historische_erfolgsquote` ist die Trefferquote (Regel 14). Sie zu
        # vermengen wuerde den Arm unlesbar machen - man wuesste hinterher
        # nicht, welcher der beiden gewirkt hat.
        neu["systemguete"] = dict(SYSTEMGUETE_ECHT)
    if arm in MIT_QUOTE:
        neu["historische_erfolgsquote"] = dict(MIT_QUOTE[arm])
        # Erst JETZT darf der Eintrag weg - weil die Zahl jetzt wirklich
        # mitgeliefert wird. Sonst behauptete der Faktensatz gleichzeitig,
        # sie sei nicht verfuegbar, und lieferte sie mit.
        neu["nicht_verfuegbar"] = [
            x for x in (neu.get("nicht_verfuegbar") or [])
            if x != "historische_erfolgsquote"]
    if arm in MIT_FLAG:
        neu["regime"]["richtungs_konflikt_mit_trigger"] = True
        neu["regime"]["richtungs_konflikt_hinweis"] = REGIME_FLAG_HINWEIS
    return neu


def pruefe_eingriffe(basis: dict, label: str) -> list[tuple[str, bool, str]]:
    """Kommt jeder Eingriff an - und NUR er? Der wichtigste Waechter der Datei.

    Ein Arm, dessen Manipulation nicht landet, laeuft stundenlang und liefert
    garantiert einen Nulleffekt, der wie ein Befund aussieht. Genau das ist am
    09.08. zweimal passiert (Textersetzung ohne assert; 200 Anker gegen ein
    erschoepftes Tageskontingent).
    """
    aus = []
    a1 = baue_arm(basis, "A1", label)
    a2 = baue_arm(basis, "A2", label)
    aus.append(("A1 gegen A2 bitgleich (Rauschboden misst nur das Modell)",
                json.dumps(a1, sort_keys=True) == json.dumps(a2, sort_keys=True),
                ""))
    aus.append(("A1 hat KEINE systemguete", "systemguete" not in a1, ""))
    aus.append(("A1 hat KEIN Regime-Flag",
                "richtungs_konflikt_mit_trigger" not in (a1.get("regime") or {}),
                ""))
    aus.append(("A1 fuehrt 'historische_erfolgsquote' als nicht verfuegbar",
                "historische_erfolgsquote" in (a1.get("nicht_verfuegbar") or []),
                str(a1.get("nicht_verfuegbar"))))
    for arm in ARME[2:]:
        b = baue_arm(basis, arm, label)
        anders = json.dumps(a1, sort_keys=True) != json.dumps(b, sort_keys=True)
        aus.append((f"{arm}: Faktensatz veraendert", anders, ""))
        aus.append((f"{arm}: systemguete "
                    + ("gesetzt" if arm in MIT_GUETE else "NICHT gesetzt"),
                    ("systemguete" in b) == (arm in MIT_GUETE), ""))
        aus.append((f"{arm}: Regime-Flag "
                    + ("true" if arm in MIT_FLAG else "abwesend"),
                    (b["regime"].get("richtungs_konflikt_mit_trigger") is True)
                    == (arm in MIT_FLAG), ""))
        # Die Quote und ihr Verfuegbarkeitsvermerk MUESSEN zusammenpassen -
        # genau hier lag der Konstruktionsfehler, den der Nutzer gefunden hat.
        hat_quote = "historische_erfolgsquote" in b
        soll = arm in MIT_QUOTE
        aus.append((f"{arm}: Trefferquote "
                    + ("mitgeliefert" if soll else "NICHT mitgeliefert"),
                    hat_quote == soll, ""))
        vermerkt = "historische_erfolgsquote" in (b.get("nicht_verfuegbar") or [])
        aus.append((f"{arm}: 'nicht_verfuegbar' passt zur Lieferung",
                    vermerkt == (not soll),
                    f"geliefert={hat_quote}, als fehlend vermerkt={vermerkt}"))
    # E3 und E4 duerfen sich AUSSCHLIESSLICH im Hinweis/Bezug unterscheiden -
    # gleiche Zahlen. Sonst misst der Vergleich nicht den Bezugsrahmen,
    # sondern eine andere Quote.
    e3 = baue_arm(basis, "E3_quote_roh", label)["historische_erfolgsquote"]
    e4 = baue_arm(basis, "E4_quote_bezug", label)["historische_erfolgsquote"]
    aus.append(("E3 und E4 tragen DIESELBEN Zahlen (nur Bezug unterscheidet)",
                all(e3[k] == e4[k] for k in
                    ("trefferquote_pct", "treffer", "fehlschlaege",
                     "anzahl_ausgewertete_signale")),
                f"E3 {e3['trefferquote_pct']} gegen E4 {e4['trefferquote_pct']}"))
    aus.append(("E4 nennt den Breakeven, E3 nicht",
                ("33,3" in e4["hinweis"] or "33.3" in e4["hinweis"])
                and "33" not in e3["hinweis"], ""))
    return aus


def _messwerte(antwort: dict, sym: str, reihe, i: int, arm: str,
               label: str) -> dict:
    """Alle Messgroessen einer Antwort - stetige zuerst."""
    z = M._zeile(sym, reihe, i, antwort, arm, label)
    z["hebel"] = antwort.get("hebel_vorschlag")
    z["gegenargument_laenge"] = len(antwort.get("gegenargument") or "")
    z["anzahl_key_risks"] = len(antwort.get("key_risks") or [])
    # Gegenszenario RICHTUNGSBEWUSST: fuer ein LONG ist das Bear-Szenario das
    # Gegenszenario, fuer ein SHORT das Bull-Szenario. Ohne diese Unterscheidung
    # misst man bei gemischten Richtungen Unsinn.
    fc = antwort.get("forecast") or {}
    ri = z.get("richtung")
    gegen = fc.get("bear") if ri == "LONG" else fc.get("bull")
    if isinstance(gegen, dict):
        z["gegenszenario_pct"] = gegen.get("probability_pct")
    return z


def _gepaart(a: list[dict], b: list[dict], feld: str) -> tuple[list, list]:
    """Differenzen je (Symbol, Datum) - und die Symbole dazu, fuer Clustern."""
    idx = {(z["symbol"], z["datum"]): z for z in a}
    diffs, symbole = [], []
    for z in b:
        v = idx.get((z["symbol"], z["datum"]))
        if not v:
            continue
        x, y = v.get(feld), z.get(feld)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            diffs.append(float(y) - float(x))
            symbole.append(z["symbol"])
    return diffs, symbole


def _vergleich(a: list[dict], b: list[dict], feld: str) -> dict | None:
    from bewerte_fakt_wirkung import _cluster_bootstrap, _wild_cluster_p_wert
    diffs, symbole = _gepaart(a, b, feld)
    if len(diffs) < 3:
        return None
    unten, oben = _cluster_bootstrap(diffs, symbole)
    return {"n": len(diffs), "symbole": len(set(symbole)),
            "wirkung": statistics.fmean(diffs),
            "ci_unten": unten, "ci_oben": oben,
            "wild_p": _wild_cluster_p_wert(diffs, symbole)}


def _je_richtung(zeilen: list[dict]) -> dict:
    """Kennzahlen GETRENNT nach Richtung - die Gegenkontrolle zu E2 lebt davon.

    Ein Gesamtmittel liesse einen reinen LONG-Einbruch und einen allgemeinen
    Daempfer gleich aussehen. Genau die sollen hier unterschieden werden.
    """
    aus = {}
    for ri in ("LONG", "SHORT"):
        g = [z for z in zeilen if z.get("richtung") == ri]
        mf = [z for z in g if z.get("fazit_folgen")]
        def med(feld):
            w = [z[feld] for z in g if isinstance(z.get(feld), (int, float))]
            return statistics.median(w) if w else None
        aus[ri] = {
            "n": len(g),
            "ja": sum(1 for z in mf if z["fazit_folgen"] == "ja"),
            "nein": sum(1 for z in mf if z["fazit_folgen"] == "nein"),
            "ja_quote": (sum(1 for z in mf if z["fazit_folgen"] == "ja") / len(mf))
                        if mf else None,
            "konfidenz": med("konfidenz"), "hebel": med("hebel"),
            "gegenszenario_pct": med("gegenszenario_pct"), "crv": med("crv"),
        }
    g = [z for z in zeilen if z.get("richtung")]
    aus["LONG_ANTEIL"] = (sum(1 for z in g if z["richtung"] == "LONG") / len(g)
                          ) if g else None
    aus["n"] = len(zeilen)
    return aus


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--je-arm", type=int, default=40)
    p.add_argument("--je-symbol", type=int, default=5)
    p.add_argument("--pause", type=float, default=1.0)
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--anbieter", choices=("gemini", "openrouter"),
                   default="gemini",
                   help="gemini (Vorgabe - traegt die Produktion seit 07.08. allein) oder openrouter (nur Gegenpruefungsrolle)")
    p.add_argument("--pruefpunkt", type=int, default=8)
    p.add_argument("--label", default="auto",
                   help="auto = tatsaechliche Marktphase des Ankers (Vorgabe). Ein fester Wert (baer/bulle/seitwaerts) erzwingt dieselbe Lage fuer alle Anker.")
    p.add_argument("--ausgabe", default="kettennaht_eingriffe.json")
    args = p.parse_args()

    reihen = lade_reihen()
    btc = reihen.get("BTC")
    if not btc:
        print("Keine BTC-Reihe.")
        return 1
    fest = M.stabile_tage(M.btc_phasen(btc))
    je_phase = M.waehle_anker(reihen, fest, args.je_arm, args.je_symbol)
    # DAS LABEL FOLGT DER TATSAECHLICHEN MARKTPHASE DES ANKERS.
    #
    # Nutzer-Vorgabe 09.08.: *"du hast es in der Hand die richtigen
    # Informationen zu uebergeben - also auch dem LLM die richtige Marktphase
    # der jeweiligen Messung"*. Einem Anker aus einer nachweislichen
    # Bullenphase `regime = "baer"` zu uebergeben hiesse, dem Modell etwas
    # Falsches zu erzaehlen - und dann zu messen, wie es auf eine Luege
    # reagiert. Eine erste Fassung dieses Skripts tat genau das.
    #
    # DER KONFLIKT-FLAG BLEIBT DABEI KOHAERENT: er sagt "die Richtung des
    # Kandidaten steht dem Regime entgegen" - eine sinnvolle Aussage in JEDEM
    # Regime, nicht nur im Baer. Produktiv entsteht er aus
    # (baer und LONG) oder (bulle und SHORT); dass er dort faktisch immer
    # LONG trifft, liegt allein daran, dass das Regime nie etwas anderes war.
    # Genau diese Einseitigkeit wird hier aufgebrochen: mit variierendem Label
    # zeigt sich, ob der Flag eine RICHTUNG bestraft oder die jeweils
    # trendabgewandte Seite.
    #
    # `--label` erzwingt bei Bedarf ein festes Label (z. B. um die reine
    # Produktionslage nachzustellen); Vorgabe ist "auto".
    anker = []
    for phase in M.ARME:
        for sym, i in je_phase[phase]:
            label = M.LABEL[phase] if args.label == "auto" else args.label
            anker.append((phase, label, sym, i))
    anker.sort(key=lambda x: (reihen[x[2]][x[3]].date, x[2]))
    if args.je_arm and len(anker) > args.je_arm:
        schritt = max(1, len(anker) // args.je_arm)
        anker = anker[::schritt][:args.je_arm]

    print(f"Anker {len(anker)}, {len({a[2] for a in anker})} Symbole, "
          f"{len({reihen[a[2]][a[3]].date for a in anker})} Tage")
    print(f"Phasen: {dict(Counter(a[0] for a in anker))}")
    print(f"{len(ARME)} Arme  ->  {len(anker) * len(ARME)} Aufrufe")

    print("\n=== ENTSCHEIDUNGSREGEL, VOR dem Lauf festgelegt ===")
    print("  Jeder Effekt wird am A1/A2-Rauschboden derselben Groesse gemessen.")
    print("  These B: E2 senkt LONG-Konfidenz/-Hebel/-Anteil ueber den Boden,")
    print("           SHORT bleibt darunter.")
    print("  These A: E1 senkt Konfidenz und ja-Quote in BEIDEN Richtungen.")
    print("  Ein Effekt unter dem Rauschboden zaehlt NICHT, egal wie er aussieht.")

    print("\n=== EINGRIFFSKONTROLLE (vor dem ersten Aufruf) ===")
    probe = baue_historische_fakten(anker[0][2], reihen[anker[0][2]],
                                    anker[0][3], btc)
    if probe is None:
        print("  Kein Faktensatz baubar - Abbruch.")
        return 1
    alles = True
    for name, ok, detail in pruefe_eingriffe(probe, anker[0][1]):
        print(f"  {'[ok]    ' if ok else '[FEHLER]'} {name}"
              + (f"   {detail}" if detail and not ok else ""))
        alles &= ok
    from agent.krypto.hebel_analyst import SYSTEM_PROMPT
    for feld in ("systemguete", "richtungs_konflikt_mit_trigger",
                 "hebel_vorschlag", "forecast"):
        drin = feld in SYSTEM_PROMPT
        print(f"  {'[ok]    ' if drin else '[FEHLER]'} Prompt nennt {feld}")
        alles &= drin
    if not alles:
        print("\n  ABBRUCH: ein Eingriff kommt nicht an oder hat keinen")
        print("  Wirkungspfad im Prompt. Ein Lauf darauf ist Zeitverlust.")
        return 2

    if args.trocken:
        zaehler = [0]

        def frage(fakten, sym):
            zaehler[0] += 1
            n = zaehler[0]
            preis = (fakten.get("preis") or {}).get("usd") or 100.0
            streu = ((n * 2654435761) >> 16) % 100 / 100.0
            flag = bool((fakten.get("regime") or {}).get(
                "richtungs_konflikt_mit_trigger"))
            guete = "systemguete" in fakten
            # Der Mock BILDET DIE VERMUTETE WIRKUNG NACH, damit Auswertung und
            # Waechter an einem Fall mit BEKANNTER Antwort geprueft werden -
            # inklusive eines Eigenrauschens, sonst besteht der Rauschboden
            # trivial mit 0.
            rausch = (((n * 2246822519) >> 13) % 7) - 3
            ist_short = (((n * 40503) >> 8) % 100) < (92 if flag else 70)
            konf = 68 + rausch - (6 if flag and not ist_short else 0) - (2 if guete else 0)
            hebel = 3.0 - (1.0 if flag and not ist_short else 0.0)
            folgen = "ja" if (not guete and not flag and streu > 0.55) else "mit_vorbehalt"
            r = -1.0 if ist_short else 1.0
            stop_rel = 0.05 + streu * 0.05
            return {"action": "ERÖFFNEN",
                    "richtung": "SHORT" if ist_short else "LONG",
                    "_modell": "trocken", "confidence_pct": konf,
                    "hebel_vorschlag": hebel,
                    "gegenargument": "x" * (40 + int(streu * 20)),
                    "key_risks": ["a", "b"],
                    "forecast": {"bull": {"scenario": "b", "probability_pct": 25 + rausch},
                                 "base": {"scenario": "b", "probability_pct": 50},
                                 "bear": {"scenario": "b", "probability_pct": 25 - rausch}},
                    "eigene_einschaetzung": {"folgen": folgen, "kurzfazit": "Attrappe"},
                    "entry": {"usd_von": preis, "usd_bis": preis},
                    "stop_loss": {"usd_von": preis * (1 - r * stop_rel),
                                  "usd_bis": preis * (1 - r * stop_rel)},
                    "take_profit": {"usd_von": preis * (1 + r * stop_rel * 2.2),
                                    "usd_bis": preis * (1 + r * stop_rel * 2.2)}}
    else:
        import os

        import config as config_module
        from agent import llm_schema
        from agent.krypto.hebel_analyst import _validate_hebel
        config_module.load_env()

        # ANBIETERWAHL - und warum GEMINI die Vorgabe ist (gemessen 09.08.):
        #
        #   1. Gemini traegt die Produktion SEIT DEM 07.08. ALLEIN (166 und 65
        #      Signale, kein Mistral mehr - der wurde kostenpflichtig).
        #      `nemotron` ueber OpenRouter entscheidet in der Produktion GAR
        #      NICHT; der Client ist laut eigenem Docstring "ausschliesslich
        #      fuer die Gegenpruefung". Ein Eingriffslauf darauf misst ein
        #      Modell, dessen Ergebnis nicht uebertraegt.
        #   2. Der Anbietereffekt auf genau die hier gemessene Groesse ist
        #      RIESIG: `ja`-Quote mistral 0,1 % (n=829) gegen gemini 5,6 %
        #      (n=305) - Faktor 56. Wer den Anbieter wechselt, misst den
        #      Anbieter.
        #   3. Gemini ist ~6x schneller (4,1 s gegen 32,1 s) und streute in der
        #      Vorprobe 0,00 auf der Konfidenz - bei null Eigenrauschen ist
        #      jeder Effekt lesbar.
        #
        # Der Anbietereffekt selbst stoert diesen Lauf nicht: alle Arme laufen
        # auf DEMSELBEN Anbieter und denselben Ankern, gepaart. Er kuerzt sich
        # heraus. Er wuerde nur stoeren, wenn man das Ergebnis auf einen
        # anderen Anbieter uebertragen wollte - und genau das tun wir nicht.
        if args.anbieter == "openrouter":
            from api.openrouter import OpenRouterClient
            schluessel = os.environ.get("OPENROUTER_API_KEY")
            if not schluessel:
                print("OPENROUTER_API_KEY fehlt.")
                return 1
            client = OpenRouterClient(schluessel)
        else:
            from api.gemini import GeminiClient
            schluessel = os.environ.get("GEMINI_API_KEY")
            if not schluessel:
                print("GEMINI_API_KEY fehlt.")
                return 1
            client = GeminiClient(schluessel)
        # JEDER bekommt das Format, das FUER IHN entschieden wurde - Gemini
        # `json_object`, OpenRouter striktes Schema. Ein einheitliches Format
        # waere ein Laborvergleich, den wir im Betrieb nie fahren.
        fmt = llm_schema.response_format_fuer(client, "agent.krypto.hebel_analyst")
        print(f"\nAnbieter: {args.anbieter}, Antwortformat: {fmt.get('type')}")
        if args.anbieter == "openrouter" and fmt.get("type") != "json_schema":
            print("ABBRUCH: striktes Schema nicht verfuegbar (siehe llm_schema.py).")
            return 2

        def frage(fakten, sym):
            # WIEDERHOLUNG BEI FORMFEHLER. Gemini scheiterte in der Vorprobe an
            # 2 von 15 Antworten an der JSON-Form (13 %) - das ist der bekannte
            # Preis von `json_object`. Ohne Wiederholung verloere ein 210er-Lauf
            # rund 27 Faelle, und zwar NICHT zufaellig ueber die Arme verteilt,
            # sondern moeglicherweise gehaeuft dort, wo der Faktensatz laenger
            # ist - also ausgerechnet in den Eingriffsarmen. Das waere ein
            # stiller Selektionsfehler.
            letzter = None
            for versuch in range(3):
                time.sleep(args.pause)
                try:
                    roh = client.chat(
                        [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user",
                          "content": json.dumps(fakten, ensure_ascii=False)}],
                        temperature=0.2, response_format=fmt)
                    antwort = _validate_hebel(json.loads(roh), sym)
                    antwort["_versuche"] = versuch + 1
                    modell = getattr(client, "letztes_modell", None)
                    if modell:
                        antwort["_modell"] = modell
                    return antwort
                except (json.JSONDecodeError, ValueError) as exc:
                    letzter = exc
                    continue
            raise letzter if letzter else RuntimeError("unbekannt")

    ergebnis: dict[str, list[dict]] = {a: [] for a in ARME}
    fehler: dict[str, Counter] = {a: Counter() for a in ARME}
    beginn = time.time()

    # ARMWEISE VERSCHRAENKT statt Arm nach Arm: bricht der Lauf ab, liegen von
    # jedem Arm gleich viele Faelle vor und der Vergleich bleibt auswertbar.
    # Nacheinander waere der letzte Arm bei einem Abbruch leer.
    for nr, (phase, label, sym, i) in enumerate(anker, 1):
        basis = baue_historische_fakten(sym, reihen[sym], i, btc)
        if basis is None:
            continue
        for arm in ARME:
            try:
                antwort = frage(baue_arm(basis, arm, label), sym)
            except Exception as exc:  # noqa: BLE001
                fehler[arm][type(exc).__name__] += 1
                continue
            z = _messwerte(antwort, sym, reihen[sym], i, arm, label)
            z["phase"] = phase
            ergebnis[arm].append(z)
        if nr % 5 == 0 or nr == len(anker):
            je = (time.time() - beginn) / max(1, nr)
            rest = (len(anker) - nr) * je / 60
            stand = " ".join(f"{a.split('_')[0]}{len(ergebnis[a]):3}" for a in ARME)
            print(f"  Anker {nr:3}/{len(anker)}  {stand}  "
                  f"Fehler {sum(sum(f.values()) for f in fehler.values()):3}  "
                  f"{je:5.1f} s/Anker  Rest ~{rest:4.0f} min")

        if nr == args.pruefpunkt:
            gesamt = sum(len(ergebnis[a]) for a in ARME)
            ohne = sum(1 for a in ARME for z in ergebnis[a]
                       if not z.get("fazit_folgen"))
            ohne_hebel = sum(1 for a in ARME for z in ergebnis[a]
                             if z.get("hebel") is None)
            print(f"\n  --- PRUEFPUNKT nach {nr} Ankern: {gesamt} Zeilen, "
                  f"{ohne} ohne Fazit, {ohne_hebel} ohne Hebel")
            if gesamt == 0:
                print("  ABBRUCH: keine verwertbare Zeile."); return 3
            leer = [a for a in ARME if not ergebnis[a]]
            if leer:
                print(f"  ABBRUCH: Arme ohne Zeilen: {leer}"); return 3
            if ohne / gesamt > 0.5:
                print("  ABBRUCH: ueber die Haelfte ohne Selbsteinschaetzung -")
                print("  genau das Feld, an dem die Fragestellung haengt.")
                return 3
            # Rauschboden schon hier grob pruefen: sind A1 und A2 IDENTISCH,
            # ist entweder das Modell deterministisch (dann ist der Boden 0 und
            # jeder Effekt zaehlt) oder - wahrscheinlicher - ein Verdrahtungs-
            # fehler laesst beide Arme dieselbe Antwort benutzen.
            d, _ = _gepaart(ergebnis["A1"], ergebnis["A2"], "konfidenz")
            if d and all(abs(x) < 1e-9 for x in d):
                print("  WARNUNG: A1 und A2 liefern bitgleiche Konfidenz.")
                print("  Entweder echt deterministisch - oder ein Verdrahtungs-")
                print("  fehler. Vor der Deutung klaeren.")
            print("  --- verwertbar, Lauf geht weiter\n")

    # ---------------------------------------------------------------- Auswertung
    print("\n" + "=" * 92)
    print("KENNZAHLEN je Arm, getrennt nach Richtung (Mediane)")
    print(f"{'Arm':16} {'LONG%':>6} | {'L n':>4} {'ja%':>6} {'Konf':>5} {'Heb':>5} "
          f"{'Geg%':>5} | {'S n':>4} {'ja%':>6} {'Konf':>5} {'Heb':>5} {'Geg%':>5}")
    kz = {}
    for a in ARME:
        k = _je_richtung(ergebnis[a]); kz[a] = k
        L, S = k["LONG"], k["SHORT"]
        def q(x): return f"{x:5.1%}" if x is not None else "    -"
        def m(x): return f"{x:5.1f}" if x is not None else "    -"
        print(f"{a:16} {q(k['LONG_ANTEIL']):>6} | {L['n']:4} {q(L['ja_quote']):>6} "
              f"{m(L['konfidenz'])} {m(L['hebel'])} {m(L['gegenszenario_pct'])} | "
              f"{S['n']:4} {q(S['ja_quote']):>6} {m(S['konfidenz'])} "
              f"{m(S['hebel'])} {m(S['gegenszenario_pct'])}")

    print("\nRAUSCHBODEN (A1 gegen A2, identische Eingabe) und EFFEKTE")
    print(f"{'Groesse':18} {'Rauschboden':>12} | " +
          " | ".join(f"{a:>22}" for a in ARME[2:]))
    vergleiche = {}
    for feld, name in STETIG:
        boden = _vergleich(ergebnis["A1"], ergebnis["A2"], feld)
        zeile = f"{name:18} "
        zeile += (f"{boden['wirkung']:+7.3f} n={boden['n']:<3}" if boden
                  else "          -  ")
        for a in ARME[2:]:
            v = _vergleich(ergebnis["A1"], ergebnis[a], feld)
            vergleiche[f"{a}:{feld}"] = v
            if not v:
                zeile += " | " + " " * 22
                continue
            ci = (f"[{v['ci_unten']:+.2f};{v['ci_oben']:+.2f}]"
                  if v["ci_unten"] is not None else "")
            marke = "*" if (v["ci_unten"] is not None
                            and (v["ci_unten"] > 0 or v["ci_oben"] < 0)) else " "
            zeile += f" | {v['wirkung']:+6.2f}{marke}{ci:>15}"
        print(zeile)
    print("  * = Bootstrap-Intervall schliesst die Null aus. Ohne Stern kein Nachweis.")

    print("\nEFFEKTE GETRENNT NACH RICHTUNG - hier entscheidet sich A gegen B")
    for a in ARME[2:]:
        for ri in ("LONG", "SHORT"):
            teil_a = [z for z in ergebnis["A1"] if z.get("richtung") == ri]
            teil_b = [z for z in ergebnis[a] if z.get("richtung") == ri]
            v = _vergleich(teil_a, teil_b, "konfidenz")
            h = _vergleich(teil_a, teil_b, "hebel")
            if v:
                print(f"  {a:16} {ri:6} Konfidenz {v['wirkung']:+6.2f} "
                      f"(n={v['n']}, {v['symbole']} Symbole)"
                      + (f"   Hebel {h['wirkung']:+5.2f}" if h else ""))
            else:
                print(f"  {a:16} {ri:6} zu wenige gepaarte Faelle")

    print("\n=== URTEIL nach der vorab festgelegten Regel ===")
    boden_konf = _vergleich(ergebnis["A1"], ergebnis["A2"], "konfidenz")
    schwelle = abs(boden_konf["wirkung"]) if boden_konf else 0.0
    print(f"  Rauschboden Konfidenz: {schwelle:.2f} Punkte")
    for a in ARME[2:]:
        aussagen = []
        for ri in ("LONG", "SHORT"):
            ta = [z for z in ergebnis["A1"] if z.get("richtung") == ri]
            tb = [z for z in ergebnis[a] if z.get("richtung") == ri]
            v = _vergleich(ta, tb, "konfidenz")
            if v:
                ueber = abs(v["wirkung"]) > max(schwelle, 1.0)
                aussagen.append(f"{ri} {v['wirkung']:+.2f}"
                                + (" (ueber Boden)" if ueber else " (im Rauschen)"))
        print(f"  {a:16} " + "   ".join(aussagen))
    print("  These B braucht: E2 LONG ueber Boden UND SHORT im Rauschen.")
    print("  These A braucht: E1 in BEIDEN Richtungen ueber Boden.")

    fb = {a: dict(f) for a, f in fehler.items() if f}
    if fb:
        print(f"\nFehler je Arm: {fb}")
    pathlib.Path(args.ausgabe).write_text(
        json.dumps({"kennzahlen": kz, "vergleiche": vergleiche,
                    "zeilen": ergebnis, "fehler": fb,
                    "systemguete_eingespeist": SYSTEMGUETE_ECHT},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
