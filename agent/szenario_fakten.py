# -*- coding: utf-8 -*-
"""Faktensatz und Zonen fuer den Szenario-Schaetzer - Stufe 0 (10.08.2026).

ZWEI REGELN, aus den Messungen desselben Tages abgeleitet:

1. KEINE WERTURTEILE. `einordnung: "unter der Basislinie"` kostete gemessen
   4,6 Konfidenzpunkte und 16 pp LONG-Anteil (Wild-Cluster-p 0,031), waehrend
   die Zahlen, aus denen dieses Urteil stammt, keinen messbaren Effekt hatten.
   Zahlen informieren, Text weist an. Hier stehen deshalb nur Zahlen - mit
   ihrem Bezug, damit sie einordenbar sind, aber ohne Einordnung.

2. JEDE ZAHL MIT BEZUG. Ein nackter RSI von 71,6 ist fuer ein Modell ohne
   Bezugsrahmen bedeutungslos; "71,6 bei einem Band von 30 bis 70" ist eine
   Aussage. Dasselbe gilt fuer Abstaende: nicht "3,20 USD unter dem EMA-200",
   sondern "0,8 ATR unter dem EMA-200" - das ist ueber alle Assetklassen
   vergleichbar, von BTC bis zu einem Rohstoff-ETC.

DIE ZONEN SETZT NICHT DAS MODELL. Sie werden hier deterministisch aus dem ATR
berechnet. Solange entry/stop/target aus der Modellantwort stammten, war jede
Frage nach "erreichst du dein Ziel" zirkulaer - ein enges Ziel gewinnt sie
trivial. Genau diese Sorte Zirkelschluss hat am 10.08. zweimal ein
Messergebnis wertlos gemacht.

WAS BEWUSST FEHLT und was das kostet: `regime` als Etikett. Es war auf allen
1.022 gemessenen Faellen konstant "baer" - ein Fakt ohne Varianz, der die
Richtungsableitung des Gegenpruefers praktisch determiniert hat (1 LONG in
1.022 Faellen). Stattdessen steht hier der ABSTAND zur Regimegrenze, sofern
bekannt: eine Zahl mit Varianz statt eines Etiketts ohne.
"""
from __future__ import annotations

# Die Zonen. Fest, damit sie ueber alle Assetklassen und alle Laeufe
# vergleichbar sind - und damit der Brier-Score etwas misst, das sich zwischen
# zwei Messungen nicht verschoben hat.
#
# CRV 2,0 ist bewusst der Wert, den das Risk-Gate ohnehin verlangt
# (CRV_MINIMUM = 2.0). Die Schaetzung wird damit direkt gegen die Schwelle
# gemessen, an der die Produktion entscheidet - und nicht gegen eine
# Hilfsgroesse, die sonst nirgends vorkommt.
STOP_IN_ATR = 1.5
ZIEL_IN_ATR = 3.0
# ZWANZIG, nicht sieben (Stufe-0-Trockenlauf, 10.08.). Bei sieben Kerzen
# erreichte in 60 echten Faellen KEIN EINZIGER das Ziel - die Basisrate fuer
# "ziel" waere 0 % gewesen und der Ausgang unschaetzbar. Ein Ziel in 3 ATR
# Entfernung braucht mehr als eine Woche.
#
# Die Wahl fiel ueber einen Rasterlauf (Stop 0,75/1,0/1,5 ATR x Horizont
# 7/14/20/30) auf die AUSGEWOGENSTE Ausgangsverteilung - 21 % Ziel, 49 % Stop,
# 30 % keines. Ausgewogen heisst hier: am schwersten durch blosses Raten der
# Basisrate zu schlagen, also der informativste Test. Getroffen wurde sie,
# BEVOR ein Modell gelaufen war; sie kann also kein Ergebnis beguenstigen.
HORIZONT_KERZEN = 20


def baue_zonen(kurs: float, atr: float, richtung: str) -> dict | None:
    """Einstieg, Stop und Ziel - deterministisch, richtungsneutral aufgebaut.

    `richtung` sagt nur, wohin das Ziel zeigt. Die Zonen selbst folgen immer
    demselben ATR-Vielfachen, damit LONG- und SHORT-Aufbauten dieselbe
    Schwierigkeit haben. Andernfalls waere ein Vergleich der Trefferquoten
    zwischen den Richtungen bedeutungslos."""
    if not kurs or not atr or atr <= 0 or richtung not in ("LONG", "SHORT"):
        return None
    vz = 1.0 if richtung == "LONG" else -1.0
    return {
        "richtung": richtung,
        "einstieg": round(kurs, 8),
        "stop": round(kurs - vz * STOP_IN_ATR * atr, 8),
        "ziel": round(kurs + vz * ZIEL_IN_ATR * atr, 8),
        "stop_abstand_atr": STOP_IN_ATR,
        "ziel_abstand_atr": ZIEL_IN_ATR,
        "crv": round(ZIEL_IN_ATR / STOP_IN_ATR, 2),
        "horizont_kerzen": HORIZONT_KERZEN,
        "hinweis": ("Einstieg, Stop und Ziel sind vorgegeben und aus der "
                    "aktuellen Schwankungsbreite berechnet - nicht zu aendern."),
    }


def _in_atr(wert: float | None, bezug: float | None, atr: float | None):
    """Abstand in ATR-Vielfachen - die einzige ueber Assetklassen vergleichbare
    Einheit. Prozent taugt nicht: 1 % bedeutet bei BTC etwas anderes als bei
    einem Kleinstwert mit 12 % Tagesschwankung."""
    if wert is None or bezug is None or not atr or atr <= 0:
        return None
    return round((wert - bezug) / atr, 2)


def _perzentil(werte, aktuell) -> int | None:
    """Wo liegt der aktuelle Wert in seiner eigenen Geschichte? 0 bis 100.

    DER WERTEBEREICH MUSS PASSEN, und das wird hier geprueft. Beim ersten Bau
    (10.08.) wurde die KURSREIHE als RSI-Historie hereingereicht - ein RSI von
    55 gegen Kurse um 65.000 verglichen. Ergebnis: 0 fuer jedes Asset ueber
    100, 100 fuer jedes darunter. Ein Feld, das wie ein Perzentil aussieht und
    in Wahrheit eine Konstante je Asset ist - genau der Defekt, den wir am
    selben Tag bei `regime` und `optionsmarkt_skew` nachgewiesen haben.

    Die Pruefung ist grob und soll es sein: liegt der aktuelle Wert weit
    ausserhalb der Spannweite der Historie, passen die Reihen nicht zusammen,
    und ein Perzentil waere eine Scheinaussage."""
    gueltig = [w for w in werte if isinstance(w, (int, float))]
    if len(gueltig) < 30 or aktuell is None:
        return None
    tief, hoch = min(gueltig), max(gueltig)
    if aktuell < tief or aktuell > hoch:
        return None          # Reihen passen nicht zusammen - lieber nichts
    return int(round(100.0 * sum(1 for w in gueltig if w <= aktuell) / len(gueltig)))


def baue_szenario_fakten(
    *, symbol: str, assetklasse: str, kurs: float, atr: float,
    richtung: str, rsi: float | None = None,
    ema: dict | None = None, sma: dict | None = None,
    bollinger: dict | None = None,
    konfluenz: dict | None = None, atr_perzentil: int | None = None,
    atr_relativ_prozent: float | None = None,
    rsi_historie: list | None = None,
    relativstaerke: dict | None = None, makro_analoge: dict | None = None,
    kosten: dict | None = None, position: dict | None = None,
    regime_abstand: float | None = None, nicht_verfuegbar: list | None = None,
) -> dict | None:
    """Der Faktensatz. Eine Form fuer alle sechs Assetklassen.

    Alle Argumente ausser den ersten fuenf sind optional - eine Assetklasse,
    die kein Funding und keinen Optionsmarkt hat, laesst sie weg, statt
    Platzhalter zu senden. Was fehlt, steht in `nicht_verfuegbar`: das Modell
    soll wissen, dass dort nichts steht, statt es zu raten (bestehendes Muster
    aus `backtest_llm1_historisch.baue_historische_fakten()`).
    """
    zonen = baue_zonen(kurs, atr, richtung)
    if zonen is None:
        return None

    technik: dict = {}
    if rsi is not None:
        technik["rsi_14"] = {
            "wert": round(rsi, 1), "band": [30, 70],
            "perzentil_eigene_historie": _perzentil(rsi_historie or [], rsi),
        }
    for name, wert in (ema or {}).items():
        technik.setdefault("abstand_in_atr", {})[f"ema_{name}"] = _in_atr(kurs, wert, atr)
    for name, wert in (sma or {}).items():
        technik.setdefault("abstand_in_atr", {})[f"sma_{name}"] = _in_atr(kurs, wert, atr)
    for name, wert in (bollinger or {}).items():
        technik.setdefault("abstand_in_atr", {})[f"bollinger_{name}"] = _in_atr(kurs, wert, atr)
    if konfluenz:
        # Die Zaehlung, nicht die Gesamttendenz: "gemischt" waere ein Urteil.
        technik["konfluenz"] = {
            "pro_aufwaerts": konfluenz.get("bullish"),
            "pro_abwaerts": konfluenz.get("bearish"),
            "neutral": konfluenz.get("neutral"),
            "gesamt": sum(v for v in (konfluenz.get("bullish"),
                                      konfluenz.get("bearish"),
                                      konfluenz.get("neutral")) if v),
        }
    if atr_perzentil is not None or atr_relativ_prozent is not None:
        technik["schwankungsbreite"] = {
            "atr_relativ_prozent": atr_relativ_prozent,
            "perzentil_eigene_historie": atr_perzentil,
        }

    fakten = {
        "asset": {"symbol": symbol, "assetklasse": assetklasse},
        "aufbau": zonen,
        "technik": technik,
    }
    if regime_abstand is not None:
        # ABSTAND statt Etikett - siehe Modul-Docstring.
        fakten["marktlage"] = {"abstand_zur_regimegrenze_std": regime_abstand}
    if relativstaerke:
        fakten.setdefault("marktlage", {})["relativstaerke"] = relativstaerke
    if makro_analoge:
        # Die einzige Kategorie im Satz, die NICHT aus der Kursreihe dieses
        # Assets stammt - historische Vergleichsmonate mit ihren tatsaechlichen
        # Vorwaertsrenditen. Genau deshalb steht sie hier.
        fakten["historische_analoge"] = makro_analoge
    if kosten:
        fakten["ausfuehrung"] = dict(kosten)
    if position:
        fakten.setdefault("ausfuehrung", {})["bestand"] = position
    if nicht_verfuegbar:
        fakten["nicht_verfuegbar"] = list(nicht_verfuegbar)
    return fakten


def enthaelt_werturteile(fakten: dict) -> list[str]:
    """Waechter: findet Felder, die ein URTEIL statt einer Zahl tragen.

    Er sucht nach den Namensmustern, mit denen wir Werturteile gebaut haben -
    `*einordnung*`, `*hinweis*`, `*bewertung*`, `*_label` - und meldet jedes
    Vorkommen mit seinem Pfad.

    AUSNAHME `aufbau.hinweis`: das ist eine Anweisung an das Modell ("die
    Zonen sind vorgegeben"), kein Urteil ueber die Marktlage. Sie steht
    absichtlich dort und ist der einzige zugelassene Freitext im Faktensatz.

    Der Waechter laeuft im Trockenlauf ueber alle sechs Assetklassen. Ohne ihn
    wandert beim naechsten Umbau wieder ein Urteil hinein, und wir merken es
    erst an einer verschobenen Richtungswahl."""
    MUSTER = ("einordnung", "hinweis", "bewertung", "_label", "lesehilfe",
              "wie_du_das_nutzt", "tendenz")
    ERLAUBT = ("aufbau.hinweis",)
    treffer: list[str] = []

    def geh(knoten, pfad=""):
        if isinstance(knoten, dict):
            for k, v in knoten.items():
                p = f"{pfad}.{k}" if pfad else k
                if any(m in str(k).lower() for m in MUSTER) and p not in ERLAUBT:
                    treffer.append(p)
                geh(v, p)
        elif isinstance(knoten, list):
            for i, v in enumerate(knoten):
                geh(v, f"{pfad}[{i}]")

    geh(fakten)
    return treffer


# --- Die Wahrheit ----------------------------------------------------------
def finde_konstanten(faktensaetze: list, mindestens: int = 20) -> list[str]:
    """Waechter: findet Felder, die ueber ALLE Faelle denselben Wert tragen.

    WARUM ES DEN BRAUCHT. Drei Konstanten haben uns Wochen gekostet, und keine
    war im Einzelfall zu sehen:

      * `regime` war auf allen 1.022 Faellen "baer" - der Gegenpruefer las
        eine Konstante mit Richtungsaussage und kam deshalb 1 von 1.022 Mal
        auf LONG.
      * `optionsmarkt_skew` war auf allen 1.022 Faellen negativ, weil dort ein
        BTC-weiter Wert stand statt des Wertes des jeweiligen Assets.
      * `perzentil_eigene_historie` war je Asset konstant, weil dem Perzentil
        die Kursreihe statt der RSI-Reihe gereicht wurde.

    Ein konstantes Feld ist schlimmer als ein fehlendes. Es kostet Platz im
    Prompt, sieht nach Information aus, und wenn es eine Richtung nahelegt,
    schiebt es JEDE Antwort in dieselbe Richtung. Fehlt es dagegen, steht das
    in `nicht_verfuegbar` und das Modell weiss es.

    ERLAUBT sind Konstruktionsparameter - die Zonengeometrie ist per
    Definition fest, das RSI-Band ist [30, 70], und wer nur eine Assetklasse
    misst, hat sie zwangslaeufig ueberall gleich. Alles andere ist ein Befund.

    Er gehoert VOR die Modellaufrufe. Heute haetten wir sonst einen ganzen
    Messlauf an einem toten Feld verbraucht - Kontingent, das nicht
    zurueckkommt."""
    # Die Namen stammen aus baue_zonen() - beim ersten Anlauf hatte ich sie
    # geraten ("stop_in_atr" statt "stop_abstand_atr"), und der Waechter
    # meldete prompt seine eigene Erlaubt-Liste als Befund.
    ERLAUBT_PRAEFIX = ("aufbau.stop_abstand_atr", "aufbau.ziel_abstand_atr",
                       "aufbau.crv", "aufbau.horizont_kerzen",
                       "aufbau.richtung", "aufbau.hinweis",
                       "asset.assetklasse", "technik.rsi_14.band",
                       "nicht_verfuegbar")
    saetze = [f for f in faktensaetze if isinstance(f, dict)]
    if len(saetze) < mindestens:
        return []

    def flach(knoten, pfad="", aus=None):
        aus = {} if aus is None else aus
        if isinstance(knoten, dict):
            for k, v in knoten.items():
                flach(v, f"{pfad}.{k}" if pfad else str(k), aus)
        elif isinstance(knoten, list):
            aus[pfad] = repr(knoten)
        else:
            aus[pfad] = repr(knoten)
        return aus

    gesehen: dict[str, set] = {}
    for f in saetze:
        for pfad, wert in flach(f).items():
            gesehen.setdefault(pfad, set()).add(wert)

    treffer = []
    for pfad, werte in sorted(gesehen.items()):
        if len(werte) != 1 or pfad.startswith(ERLAUBT_PRAEFIX):
            continue
        # Ein Feld, das nur in wenigen Saetzen ueberhaupt vorkommt, ist nicht
        # konstant - es ist selten. Der Unterschied ist wesentlich: Seltenheit
        # ist erlaubt, Konstanz ueber die volle Stichprobe nicht.
        vorkommen = sum(1 for f in saetze if pfad in flach(f))
        if vorkommen < len(saetze):
            continue
        treffer.append(f"{pfad} = {next(iter(werte))} (alle {vorkommen} Faelle)")
    return treffer


AUSGAENGE = ("ziel", "stop", "keines")


def loese_auf(reihe, idx: int, zonen: dict,
              horizont: int = HORIZONT_KERZEN) -> str | None:
    """Was wurde ZUERST erreicht - Ziel, Stop, oder keines im Horizont?

    Die Gegenprobe zur Schaetzung. Sie liest ausschliesslich die Kursreihe und
    kennt weder Modell noch Empfehlung - deshalb ist sie als Wahrheit
    brauchbar, anders als das gespeicherte Handelsergebnis, das an den vom
    Modell selbst gesetzten Zonen haengt.

    INNERHALB EINER KERZE laesst sich die Reihenfolge nicht aufloesen: Hoch und
    Tief stehen ohne Zeitstempel nebeneinander. Wird in derselben Kerze beides
    beruehrt, gilt der STOP als zuerst erreicht - die pessimistische Annahme.
    Andernfalls wuerde jeder volatile Tag als Gewinn gezaehlt, und die
    Trefferquote waere systematisch zu hoch. Dieselbe Konvention verwendet das
    Backward-Tracking.

    Gibt None zurueck, wenn der Horizont ueber das Ende der Reihe hinausragt -
    dann ist der Fall (noch) nicht auswertbar und darf nicht mitzaehlen.
    """
    if idx + horizont >= len(reihe) or not zonen:
        return None
    long = zonen["richtung"] == "LONG"
    ziel, stop = zonen["ziel"], zonen["stop"]
    for k in reihe[idx + 1: idx + 1 + horizont]:
        hoch, tief = getattr(k, "high", None), getattr(k, "low", None)
        if hoch is None or tief is None:
            continue
        stop_beruehrt = (tief <= stop) if long else (hoch >= stop)
        ziel_beruehrt = (hoch >= ziel) if long else (tief <= ziel)
        if stop_beruehrt:
            return "stop"          # auch wenn beides - siehe Docstring
        if ziel_beruehrt:
            return "ziel"
    return "keines"


def brier(verteilung: dict, eingetreten: str) -> float | None:
    """Brier-Score fuer drei sich ausschliessende Ausgaenge. 0 ist perfekt.

    Summe der quadrierten Abweichungen zwischen geschaetzter Wahrscheinlichkeit
    und Eintreten (1 oder 0). Wertebereich 0 bis 2. Der Standardmassstab fuer
    Wahrscheinlichkeitsprognosen seit Brier 1950 - bewusst nicht selbst
    erfunden, damit unsere Zahlen mit der Literatur vergleichbar bleiben.
    """
    if eingetreten not in AUSGAENGE or not verteilung:
        return None
    summe = 0.0
    for name, schluessel in zip(AUSGAENGE,
                                ("ziel_zuerst_pct", "stop_zuerst_pct", "keines_pct")):
        p = verteilung.get(schluessel)
        if p is None:
            return None
        summe += (float(p) / 100.0 - (1.0 if name == eingetreten else 0.0)) ** 2
    return round(summe, 4)
