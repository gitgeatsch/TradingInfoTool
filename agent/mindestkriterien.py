# -*- coding: utf-8 -*-
"""Hat diese Rolle genug, um zu urteilen? - R-R1 bis R-R3 als Code (16.08.2026).

DER ANLASS. Die Mindestgrundlagen standen seit heute frueh im
`Regelwerksmanual.md` - als TEXT. Nutzerfrage: *"sind die neuen
Mindestkriterien bereits implementiert und geprueft?"* Antwort war: nein.

UND GENAU DIESE LUECKE HAT AN DEMSELBEN TAG ZUGESCHLAGEN. Rolle A bekam in der
Produktion **12 statt 15 Aussagen** - es fehlten Netto-Liquiditaet, Zinskurve
und Anlegerstimmung, also die gesamte Makro-Dimension und die Stimmung. Der
Grund war eine Datenluecke auf dem Notebook, und niemand sah sie: `lade_makro()`
ist fail-soft, der Satz entfaellt lautlos.

    Eine Rolle, deren Mindestgrundlage niemand prueft, urteilt auch dann
    weiter, wenn ihr ein Drittel fehlt - und die Ausgabe sieht genauso aus.

MELDEN IST DIE VORGABE, SPERREN DIE AUSNAHME. Ein Modul, das beim blossen
Einspielen eine Rolle stilllegt, nimmt dem Nutzer die Entscheidung ab -
dieselbe Regel wie bei `rollen_kette.aktiv_fuer` und `anlass.aktiv`. Und hier
waere sie besonders teuer: Rolle G erfuellte ihre eigene Mindestgrundlage bei
Einfuehrung NICHT (eine Quelle statt zwei), ein scharfes Kriterium haette sie
sofort stillgelegt.

STAND 16.08. ABENDS: fuer KRYPTO ist G1 erfuellt - Terminmarkt und
Boersenzu-/-abfluesse sind zwei verschiedene Erhebungen mit verschiedenen
Fragen. Fuer Aktien, Rohstoffe und ETF steht es weiterhin bei NULL Quellen;
die Clients liegen fertig in `api/` (finra, sec_edgar, cftc_cot) und sind
nicht verdrahtet. `sperren` bleibt deshalb leer.

WAS HIER NICHT GEPRUEFT WIRD: ob die Kriterien die RICHTIGEN sind. Sie stammen
aus der Praxisrecherche (Umbauplan 33, 41, 42) und sind damit auf Rang 2 der
Eignungsleiter - "in der Praxis angewendet", nicht "bei uns gemessen". Dieses
Modul prueft die EINHALTUNG, nicht die Gueltigkeit.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# --- ROLLE A: die vier Dimensionen der Marktlage (Methodik 2.21.2) ---------
#
# Die BREITE fehlt hier absichtlich: sie ist am 12.08. ersatzlos gestrichen
# worden (Subjekt falsch, Bezugskorb wandert, Richtung gemessen invers). Sie
# als Kriterium zu fuehren hiesse, etwas zu verlangen, das wir bewusst
# entfernt haben.
#
# ERKANNT AM WORTLAUT, nicht an einem Feld. Die Saetze entstehen in
# `marktlage.py` und sind dort festgelegt; ein Feld daneben waere eine zweite
# Definition, die auseinanderlaufen kann. Wer eine Formulierung aendert, muss
# hier nachziehen - und merkt es sofort, weil die Dimension dann fehlt.
DIMENSIONEN_A = (
    ("Trend", ("steht", "Handelstagen")),
    ("Volatilitaet", ("schwankt taeglich",)),
    ("Liquiditaet", ("je gehandeltem Euro Umsatz",)),
    ("Makro", ("Netto-Liquiditaet", "zehnjaehriger")),
    ("Stimmung", ("Anlegerstimmung",)),
)

# --- ROLLE BC: was ohne Ausnahme dastehen muss ----------------------------
#
# NICHT die volle CSTI-Liste. Auslöser, Handelbarkeit und Katalysator fehlen
# strukturell (Umbauplan 42.2) - sie hier zu verlangen hiesse, bei JEDEM Urteil
# einen Mangel zu melden, den wir kennen und der eine eigene Phase hat. Eine
# Warnung, die immer kommt, liest niemand.
#
# Geprueft wird, was da sein MUSS und heute auch da ist: der Auftrag (unter
# welcher Bedingung zu lesen ist), der Bestand (der KAS-Fall) und die Lage
# selbst. Faellt eines davon aus, ist das ein Defekt, kein bekannter Mangel.
PFLICHT_BC = ("auftrag", "stand")
PFLICHT_BLOECKE_BC = ("bestand", "verlauf")

# --- ROLLE G: die Bedingung, nicht die Liste (R-R3) ------------------------
#
# Fuer "zweites Modell prueft erstes" gibt es keinen Praxismassstab. Die
# Debattenliteratur liefert stattdessen eine EIGENSCHAFT: die Pruefung traegt
# nur, wenn der Pruefer Information hat, die dem Urteilenden fehlt.
#
# G1 zaehlt QUELLEN, nicht Zahlen. Open Interest, Finanzierungsrate und
# Long-Konten stammen aus EINER Tabelle (`open_interest_snapshot`) und
# beschreiben dieselbe Menge Menschen auf derselben Boerse - drei Zahlen, eine
# Quelle. Das Regime ist die zweite, aber es kommt aus unserer eigenen
# Kursreihe und zaehlt deshalb nicht als fremde.
# DREI BOERSEN SIND EINE QUELLE. Seit dem 16.08. liest `positionierung.py`
# Binance, Bybit und OKX - das verbessert den Fakt, vermehrt aber die ART
# nicht. Offene Kontrakte bleiben offene Kontrakte. Hier nach Endpunkten zu
# zaehlen hiesse, G1 durch dreifaches Zaehlen derselben Groesse zu erfuellen.
QUELLEN_G = {
    "terminmarkt": ("oi_aenderung_pct", "funding_perzentil", "long_anteil_pct",
                    "divergenz"),
    # DIE ZWEITE ART, seit 16.08. verdrahtet (Umbauplan 58): gezaehlte
    # Muenzbewegungen auf der Kette, nicht Positionsstaende an einer Boerse.
    # ⚠️ BTC-WEIT, NICHT SYMBOLSPEZIFISCH - deckt G1 ab, NIE G2.
    "onchain": ("boersenfluss",),
    # Die naechsten, sobald verdrahtet - siehe Umbauplan 40.1.
    "cot": ("cot_perzentil",),
    "short_interest": ("short_interest_perzentil",),
    "insider": ("insider_kaeufe_90d",),
    "optionsmarkt": ("dvol", "skew"),
}

# WELCHE QUELLEN EINEN EINZELNEN WERT BESCHREIBEN. G2 verlangt genau das - und
# ohne diese Liste wuerde eine BTC-weite Groesse wie der Boersenfluss die
# Bedingung miterfuellen, obwohl sie ueber SEI nichts aussagt.
SYMBOLSPEZIFISCH_G = ("terminmarkt", "cot", "short_interest", "insider",
                      "optionsmarkt")
MINDEST_QUELLEN_G = 2


def konfig(config: dict | None = None) -> dict:
    """Was gemeldet und was gesperrt wird.

    `sperren` ist eine LISTE von Rollen ("A", "BC", "G") - leer heisst: nichts
    sperrt. Bewusst nicht ein Schalter fuer alle: die drei Rollen haben sehr
    verschiedene Luecken, und Rolle G erfuellt ihre Mindestgrundlage heute
    nicht."""
    roh = ((config or {}).get("mindestkriterien") or {}) if isinstance(config, dict) else {}
    return {"melden": bool(roh.get("melden", True)),
            "sperren": tuple(str(r).upper() for r in (roh.get("sperren") or ()))}


def pruefe_a(saetze: list) -> list[str]:
    """Welche der fuenf Dimensionen fehlen im Lagebild?"""
    text = " ".join(str(s) for s in (saetze or []))
    return [name for name, woerter in DIMENSIONEN_A
            if not any(w in text for w in woerter)]


def pruefe_bc(fakten: dict, bloecke: dict | None = None) -> list[str]:
    """Was fehlt dem Faktensatz von Rolle BC?

    `bloecke` ist der Ausgang von `lagebeschreibung.geteilt()`; fehlt er, wird
    nur der aeussere Aufbau geprueft. NICHT nachrechnen - eine zweite Rechnung
    waere die naechste Stelle zum Auseinanderlaufen."""
    fehlt = [k for k in PFLICHT_BC if not (fakten or {}).get(k)]
    if bloecke is not None:
        fehlt += [f"Block {b}" for b in PFLICHT_BLOECKE_BC if not bloecke.get(b)]
    return fehlt


def quellen_g(lage: dict) -> list[str]:
    """Welche UNABHAENGIGEN Quellen liegen fuer Rolle G vor?

    Das Regime zaehlt NICHT mit: es wird aus BTC-Kurs und Fear & Greed
    gerechnet, und beides sieht Rolle A bereits. Es steht bei Rolle G, weil sie
    sonst nur eine Quelle haette - aber es ist keine fremde."""
    return [name for name, felder in QUELLEN_G.items()
            if any((lage or {}).get(f) is not None for f in felder)]


def pruefe_g(lage: dict) -> list[str]:
    """Was fehlt Rolle G zu ihrer Mindestgrundlage (R-R3)?"""
    q = quellen_g(lage)
    fehlt = []
    if len(q) < MINDEST_QUELLEN_G:
        fehlt.append(f"G1: {len(q)} von {MINDEST_QUELLEN_G} unabhaengigen "
                     f"Quellen ({', '.join(q) or 'keine'})")
    # G2 GETRENNT GEPRUEFT, NICHT AUS G1 ABGELEITET (16.08.2026). Vorher stand
    # hier `if not q` - also "irgendeine Quelle reicht". Mit dem Boersenfluss
    # waere das falsch geworden: er ist BTC-weit, und ein Symbol ohne
    # Terminmarktdaten haette G2 durch eine Marktgroesse erfuellt, die ueber
    # dieses Symbol nichts sagt.
    if not [n for n in q if n in SYMBOLSPEZIFISCH_G]:
        fehlt.append("G2: keine symbolspezifische Quelle")
    return fehlt


def melde(rolle: str, fehlend: list, config: dict | None = None,
          bezug: str = "") -> bool:
    """Meldet die Luecke und sagt, ob gesperrt werden soll.

    RUECKGABE `True` HEISST SPERREN - und das passiert nur, wenn der Nutzer die
    Rolle ausdruecklich in `mindestkriterien.sperren` eingetragen hat.

    Die Meldung nennt die fehlenden Punkte BEIM NAMEN. "Mindestkriterien nicht
    erfuellt" waere eine Zahl ohne Ursache; genau daran ist die Makro-Luecke
    tagelang vorbeigelaufen."""
    if not fehlend:
        return False
    c = konfig(config)
    if c["melden"]:
        logger.warning("Rolle %s%s: Mindestgrundlage unvollstaendig - %s",
                       rolle, f" ({bezug})" if bezug else "",
                       "; ".join(str(f) for f in fehlend))
    return str(rolle).upper() in c["sperren"]
