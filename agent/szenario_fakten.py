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
HORIZONT_KERZEN = 7


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
    """Wo liegt der aktuelle Wert in seiner eigenen Geschichte? 0 bis 100."""
    gueltig = [w for w in werte if isinstance(w, (int, float))]
    if len(gueltig) < 30 or aktuell is None:
        return None
    return int(round(100.0 * sum(1 for w in gueltig if w <= aktuell) / len(gueltig)))


def baue_szenario_fakten(
    *, symbol: str, assetklasse: str, kurs: float, atr: float,
    richtung: str, rsi: float | None = None,
    ema: dict | None = None, bollinger: dict | None = None,
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
