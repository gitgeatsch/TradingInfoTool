# -*- coding: utf-8 -*-
"""WELCHE Werte werden heute ueberhaupt beurteilt? (A1, 23.08.2026)

DIE NUTZERVORGABE, DIE DAS AUSLOEST:

    "Wir messen immer im breiten Bereich und die Signale kommen im breiten
     Bereich - HYPE zehnmal kaufen am Tag, LINK zehnmal - aber nie selektiv
     auf Assetebene. Der HANDEL passiert aber auf Assetebene."

Und der Grundsatz darueber:

    "JEDE Entscheidung zu einem Trade soll eine BEGRUENDUNG haben. Der Grund
     'das Asset ist in der Zeitschleife dran' ist keine."

⚠️ GENAU DAS WAR DER ZUSTAND. Bis heute waehlte die UHR: der Cooldown liess
durch, wer lange genug nicht gefragt worden war. Von 41 Symbolen passierten 30
den Fingerabdruck und NULL den Cooldown - die einzige wirksame Auswahl war eine
Zeitregel ohne jeden Beleg.

WAS HIER STATTDESSEN AUSWAEHLT, und es ist gemessen (messe_auswahl.py, 40
Symbole, 3.290 Tage, barrierenfrei und brutto, Newey-West ueber 1.874 Termine):

    k=1   Horizont  5: +0,73 % (t 1,93)    Horizont 20: +4,55 % (t 4,21)
    k=2   Horizont  5: +0,79 % (t 3,29)    Horizont 20: +2,74 % (t 4,52)
    k=3   Horizont  5: +0,43 % (t 2,22)    Horizont 20: +1,11 % (t 2,37)
    k=5   Horizont  5: +0,17 % (t 1,22)    Horizont 20: +0,46 % (t 1,15)

⚠️ AB k=5 IST NICHTS MEHR DA. Der urspruengliche Vorschlag "die besten k" mit
einem Fuenftel (8 von 40) haette GENAU NICHTS ausgewaehlt. Deshalb k = 2.

⚠️ UND DIE UHR IST NICHT ABGESCHAFFT, SIE IST ENTMACHTET. Der Cooldown bleibt
als MINDESTABSTAND stehen - sonst wuerde dieselbe Auswahl alle fuenfzehn
Minuten neu befragt, und aus einer Auswahl waere eine neue Flut. Er waehlt nur
nicht mehr aus; er verhindert nur noch die Wiederholung derselben Frage.

DER MARKTZUSTAND IST HIER SCHATTEN, KEINE SCHRANKE (A1b). Gemessen:

    BTC ueber seinem 200-Schnitt   Auswahl +1,45 %  Markt +0,53 %  t  3,58
    BTC unter seinem 200-Schnitt   Auswahl +0,08 %  Markt +0,17 %  t -0,46

Im Mittel eindeutig - je Jahr aber gemischt (2024 trennt gar nicht, 2025 trennt
und verliert trotzdem absolut). Ein Waechter, der selbst verwirft, macht seine
eigene Wirkung unsichtbar; deshalb rechnet er mit, steht in der Mail und sperrt
NICHTS. Genau so ist H seit dem 22.08. gebaut.

WAS AUSDRUECKLICH NICHT GEBAUT IST: der absolute Trendfilter am Einzelwert
(Lehrbuch-Dual-Momentum). Gemessen sperrt er 228 von 1.874 Terminen und
verbessert nichts - die besten zwei nach Jahresentwicklung sind ohnehin fast
immer gestiegen.

⚠️ DUENNE GRUPPEN (Nutzerentscheidung 23.08.: "vorlaeufig so anwenden, wichtig
die Assets sollten dennoch handelbar sein und eine Auswahl ist zu finden"):
unter zehn Symbolen ist k=2 keine Auswahl mehr, sondern eine Aufzaehlung.
Deshalb dort k=1 - bei zwei Werten also 'der bessere von beiden'. Bei EINEM
Wert gibt es nichts zu waehlen; dann waehlt diese Stufe NICHT und laesst alle
durch, statt eine Auswahl vorzutaeuschen.

⚠️ UND k IST NIE GLEICH n. 'Rang 2 von 2' waere eine Begruendung, die keine
ist - genau die Sorte Satz, die dieses Projekt vermeiden will.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Der Rueckblick ist der EINZIGE, der die Placebo-Schwelle gehalten hat
# (messe_drift 19.08.: 250/5 mit t = 3,20 bei empirischer Schwelle 3,05).
# Eine andere Zahl waere ein Wert ohne Befund daneben.
RUECKBLICK_TAGE = 250

K_GROSS = 2                 # ab MINDEST_FUER_K2 Symbolen - gemessene Stelle
K_KLEIN = 1                 # darunter: zwei von vier waeren keine Auswahl
MINDEST_FUER_K2 = 10
MINDEST_FUER_AUSWAHL = 2    # bei einem einzigen Wert gibt es nichts zu
                            # waehlen; ab zwei ist 'der bessere von
                            # beiden' eine Auswahl (Nutzerentscheidung
                            # 23.08.: 'eine Auswahl ist zu finden').
                            # ⚠️ Bei n=2 ist der Rangplatz allerdings
                            # kaum mehr als ein Muenzwurf - er halbiert
                            # die Aufrufe und traegt keinen Beleg.

SMA_MARKT = 200             # fuer den Marktzustand (Schatten)

GEMESSEN = {"k": 2, "abstand_h5": 0.0079, "t_h5": 3.29,
            "abstand_h20": 0.0274, "t_h20": 4.52,
            "schwelle": 3.05, "termine": 1874, "stand": "2026-08-23"}


def k_fuer(anzahl: int) -> int:
    """Wieviele passieren? 0 heisst: diese Stufe waehlt hier nicht aus.

    ⚠️ NIE ALLE. Waere k gleich der Zahl der Werte, stuende in der Mail eine
    Begruendung ("Rang 2 von 2"), die keine ist."""
    n = int(anzahl or 0)
    if n < MINDEST_FUER_AUSWAHL:
        return 0
    k = K_GROSS if n >= MINDEST_FUER_K2 else K_KLEIN
    return min(k, n - 1)


def rangliste(reihen: dict, symbole=None,
              rueckblick: int = RUECKBLICK_TAGE) -> list[tuple[str, float]]:
    """Symbole nach der Entwicklung ueber `rueckblick` Tage, bester zuerst.

    ⚠️ NUR WERTE MIT GENUG HISTORIE. Wer erst seit hundert Tagen dabei ist,
    hat keine Jahresentwicklung; ihn mit null zu fuehren waere eine erfundene
    Zahl - und wuerde ihn ans Ende setzen, wo er ueber die Auswahl mitbestimmt.
    Dieselbe Regel wie in `drift.rang()`."""
    erlaubt = ({str(s).upper() for s in symbole} if symbole is not None
               else None)
    aus = []
    for sym, kerzen in (reihen or {}).items():
        if erlaubt is not None and str(sym).upper() not in erlaubt:
            continue
        if not kerzen or len(kerzen) <= rueckblick:
            continue
        try:
            frueher = float(kerzen[-1 - rueckblick].close)
            jetzt = float(kerzen[-1].close)
        except (AttributeError, IndexError, TypeError, ValueError):
            continue
        if frueher > 0 and jetzt > 0:
            aus.append((sym, jetzt / frueher - 1.0))
    return sorted(aus, key=lambda p: p[1], reverse=True)


def waehle(reihen: dict, symbole=None,
           rueckblick: int = RUECKBLICK_TAGE) -> dict:
    """Die Auswahl fuer EINEN Lauf - einmal je Lauf, nicht je Asset.

    Gibt `{"aktiv": bool, "k": int, "von": int, "gewaehlt": set,
           "platz": {symbol: (platz, von)}, "ohne_historie": [...]}`.

    `aktiv=False` heisst: hier wird nicht ausgewaehlt (zu wenige Werte mit
    Historie). Dann passieren ALLE - eine Stufe, die nichts entscheiden kann,
    darf nicht sperren."""
    liste = rangliste(reihen, symbole, rueckblick)
    n = len(liste)
    k = k_fuer(n)
    platz = {sym: (i + 1, n) for i, (sym, _e) in enumerate(liste)}
    ohne = []
    if symbole is not None:
        haben = {s for s, _ in liste}
        ohne = [s for s in symbole if s not in haben]
    return {"aktiv": k > 0, "k": k, "von": n,
            "gewaehlt": {sym for sym, _e in liste[:k]},
            "platz": platz, "entwicklung": dict(liste), "ohne_historie": ohne}


def grund(auswahl: dict, symbol: str) -> str:
    """Die Begruendung je Symbol - fuer die Mail UND fuer den Trichter.

    ⚠️ SIE NENNT IMMER BEIDE ZAHLEN. "Rang 17" allein ist keine Auskunft;
    erst "von 40" macht daraus eine."""
    if not (auswahl or {}).get("aktiv"):
        return "keine Auswahl moeglich - zu wenige Werte mit Jahreshistorie"
    p = (auswahl.get("platz") or {}).get(symbol)
    if not p:
        return (f"keine Jahresentwicklung - weniger als {RUECKBLICK_TAGE} "
                f"Handelstage Historie")
    return (f"Rang {p[0]} von {p[1]} nach der Entwicklung der letzten "
            f"{RUECKBLICK_TAGE} Handelstage")


def marktzustand(reihen: dict, klasse: str) -> dict | None:
    """A1b - der Marktzustand als STETIGE Groesse. Schatten, keine Schranke.

    ⚠️ KEIN ETIKETT "steigend/fallend". Ein Etikett ist erst hinterher bekannt
    (die Rendite des Zeitraums), der Abstand zum eigenen Schnitt schon vorher.
    Das ist der Unterschied zwischen einer Beschreibung und einer Groesse, mit
    der man arbeiten kann."""
    try:
        from agent.marktlage import BENCHMARK, BENCHMARK_NAME
    except Exception:                                        # noqa: BLE001
        return None
    sym = BENCHMARK.get(str(klasse or "").strip().lower())
    kerzen = (reihen or {}).get(sym)
    if not sym or not kerzen or len(kerzen) < SMA_MARKT:
        return None
    try:
        schluss = [float(k.close) for k in kerzen[-SMA_MARKT:]]
        jetzt = float(kerzen[-1].close)
    except (AttributeError, TypeError, ValueError):
        return None
    mittel = sum(schluss) / len(schluss)
    if mittel <= 0:
        return None
    return {"symbol": sym, "name": BENCHMARK_NAME.get(sym, sym),
            "abstand": jetzt / mittel - 1.0, "fenster": SMA_MARKT}


def saetze(auswahl: dict, symbol: str, zustand: dict | None = None) -> list:
    """Die Zeilen fuer die Mail. SPERREN NICHTS - das steht auch da."""
    if not (auswahl or {}).get("aktiv"):
        return []
    zeilen = [grund(auswahl, symbol) + "."]
    if symbol in (auswahl.get("gewaehlt") or set()):
        zeilen.append(
            f"Beurteilt werden je Durchgang die besten {auswahl['k']} dieser "
            f"Gruppe. Gemessen ueber {GEMESSEN['termine']} Termine lagen sie "
            f"auf {20} Handelstage {100 * GEMESSEN['abstand_h20']:.1f} "
            f"Prozentpunkte vor dem Gruppenschnitt.")
    if zustand:
        wie = ("ueber" if zustand["abstand"] > 0 else "unter")
        zeilen.append(
            f"{zustand['name']} steht {abs(100 * zustand['abstand']):.1f} % "
            f"{wie} seinem eigenen Schnitt der letzten {zustand['fenster']} "
            f"Handelstage. Diese Angabe sperrt nichts - sie wird "
            f"mitgeschrieben, um sie spaeter an Ergebnissen zu pruefen.")
    return zeilen
