"""ABGEKAPSELT seit 28.08.2026 - kein aktiver Pfad erreicht dieses Modul.

⚠️ WER HIER LANDET, SUCHT VERMUTLICH ETWAS, DAS ES NICHT MEHR GIBT. Tranchen
sind durch die Strategie `akkumulation` ersetzt (Nutzerentscheidung 27.08.:
"nachdem wir keine Tranchen mehr haben"). Der Code bleibt stehen, weil ein
Rueckfall auf den alten Weg technisch moeglich ist - er ist nicht tot, sondern
STILLGELEGT.

DIE BEIDEN GATES, die ihn heute unerreichbar machen:

    scheduler/background.py:3376   Budget-Allocator      -> Rollen-Kette
    scheduler/background.py:3540   Multi-Asset-Batch     -> Rollen-Kette

Beide fragen `rollen_job.bedient_neue_kette()`. Solange `rollen_kette.aktiv_fuer`
alle Gruppen nennt, laeuft keiner der beiden - und `agent/rollen_lauf.py` kennt
das Wort "tranchen" an keiner Stelle.

⚠️ EIN RUECKFALL WAERE KEIN FEHLER, SONDERN EIN RUECKSCHRITT: der alte Weg kennt
`strategie` NULL Mal, also auch keine Akkumulation, keine Positionsfuehrung je
Symbol und keinen Cooldown je Strategie. Deshalb warnen beide Nahtstellen seit
dem 28.08. LAUT statt auf `info` - siehe `rollen_job.warne_alter_weg()` und
`VERLUST_IM_RUECKFALL`.

Wer dieses Modul wieder verdrahten will, aendert zuerst die Dauerpruefung
"Abkapselung" in `pruefe_pakete.py` - sie haelt den Zustand fest.

---

Gestaffelte Kauf-/Verkaufszonen (AZ-4) - gemeinsame Regel fuer alle Klassen.

WOZU ZENTRAL: die Pruefung ist rund vierzig Zeilen und war bis zum 2026-08-09
nur im Krypto-Spot-Analysten. Sie in vier weitere Dateien zu kopieren waeren
vier Gelegenheiten auseinanderzulaufen - dasselbe Argument wie bei
`agent/llm_schema.py` (Schemata ableiten statt schreiben) und
`agent/schwerpunkt_prioritaet.py`.

## Warum ein fehlerhafter Vorschlag das Signal NICHT scheitern laesst

Der Tranchen-Vorschlag ist bewusst unverbindlich: es gibt keine Moeglichkeit,
den tatsaechlichen Order-Status ueber die Bitpanda-API zu verfolgen (siehe
Regelwerksmanual Kap. 4). Ein kaputter Vorschlag wird deshalb VERWORFEN und
protokolliert, statt ein sonst valides Gesamtsignal mitzureissen. Das ist eine
bewusste Entscheidung aus der Krypto-Fassung und wird hier unveraendert
uebernommen.

## Die Bedingung, unter der ueberhaupt Tranchen erlaubt sind

Sie steht NICHT hier, sondern je Pipeline - weil sie sich unterscheidet:

    Krypto-Spot   Regime baer/krise_extrem/seitwaerts (BTC-basiert)
                  UND Symbol in BTC/ETH/SOL
                  UND per-Asset-Flag

    Multi-Asset   Aktien-Baermarkt ODER VIX gestresst/krise
                  UND per-Asset-Flag
    (2026-08-09)

**BTC wird fuer Multi-Asset ausdruecklich NICHT als Basis verwendet**
(Nutzer-Vorgabe 2026-08-09). Der BTC-Regime-Score gatet ueber R-5.10 zwar
faktisch schon die ganze Spot-Familie - das ist als M6 im Gesamtkonzept als
offene Konzeptfrage vermerkt und soll hier nicht weiter ausgebaut werden.
Stattdessen die Groessen, die im Regime-Block dieser Klassen ohnehin stehen:
`equities_baermarkt_aktiv` und `vix_label`.

Die Symbol-Whitelist entfaellt fuer Multi-Asset: ihre Krypto-Begruendung
("Tranchen sind fuer die groessten, liquidesten Positionen gedacht") wird dort
durch das per-Asset-Flag abgebildet, dessen Vorgabewert an den gehaltenen
Positionen haengt.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

MIN_TRANCHEN = 2
MAX_TRANCHEN = 5
# Summentoleranz: das Modell rechnet in ganzen Prozent, 33+33+34 ergibt 100,
# 33,3 dreimal aber 99,9. Eine harte Gleichheit haette gute Vorschlaege
# verworfen.
ANTEIL_SUMME_MIN = 99.5
ANTEIL_SUMME_MAX = 100.5

# Ab welchem VIX-Band sind fuer Nicht-Krypto Tranchen erlaubt (2026-08-09).
#
# BEWUSST "erhoeht" (VIX >= 20) UND NICHT "gestresst" (>= 30). Die
# Krypto-Bedingung ist sehr weit - sie erlaubt Tranchen bei baer, krise_extrem
# UND seitwaerts, also in fast jedem Zustand ausser einem klaren
# Aufwaertsmarkt. Eine Multi-Asset-Fassung, die erst ab VIX 30 greift, waere
# ohne Begruendung viel enger als ihr Vorbild. "erhoeht" ist die naechste
# Entsprechung zu "der Markt ist nicht ruhig aufwaerts".
#
# ZUM EINORDNEN: am 2026-08-08 stand der VIX bei 14,9, also "ruhig" - die
# Bedingung feuert heute NICHT, und das ist richtig so. Bei ruhigem Markt ist
# gestaffelter Einstieg nicht der Punkt. Dass die Funktion derzeit schlaeft,
# ist kein Zeichen fuer eine unfertige Verdrahtung; der Test treibt sie
# deshalb mit einem synthetischen Regime, statt auf einen Markteinbruch zu
# warten.
VIX_LABELS_MIT_TRANCHEN = ("erhöht", "gestresst", "krise")


def validiere_tranchen(data: dict, symbol: str = "") -> None:
    """Prueft `data["tranchen"]` an Ort und Stelle und setzt es bei Fehlern
    auf None. Wirft NIE - siehe Modul-Docstring.

    Normalisiert nebenbei: `anteil_prozent` und die Zonengrenzen werden zu
    float, damit nachgelagerte Rechnungen sich nicht mit Strings befassen
    muessen."""
    tranchen = data.get("tranchen")
    if tranchen is None:
        return
    try:
        if not isinstance(tranchen, list) or not (MIN_TRANCHEN <= len(tranchen) <= MAX_TRANCHEN):
            raise ValueError(
                f"tranchen muss {MIN_TRANCHEN}-{MAX_TRANCHEN} Eintraege enthalten: {tranchen!r}")
        ranks_seen: set = set()
        anteil_summe = 0.0
        for eintrag in tranchen:
            if not isinstance(eintrag, dict):
                raise ValueError(f"tranchen-Eintrag ist kein Objekt: {eintrag!r}")
            rang = eintrag.get("rang")
            if not isinstance(rang, int) or rang in ranks_seen:
                raise ValueError(f"tranchen.rang ungueltig oder doppelt: {rang!r}")
            ranks_seen.add(rang)
            anteil = float(eintrag.get("anteil_prozent"))
            anteil_summe += anteil
            eintrag["anteil_prozent"] = anteil
            zone = eintrag.get("zone")
            if not isinstance(zone, dict):
                raise ValueError(f"tranchen.zone fehlt/kein Objekt: {zone!r}")
            for currency in ("usd", "eur"):
                von, bis = zone.get(f"{currency}_von"), zone.get(f"{currency}_bis")
                if von is None or bis is None:
                    raise ValueError(f"tranchen.zone.{currency}_von/{currency}_bis fehlt")
                von, bis = float(von), float(bis)
                if von > bis:
                    raise ValueError(
                        f"tranchen.zone.{currency}_von > {currency}_bis ({von} > {bis})")
                zone[f"{currency}_von"], zone[f"{currency}_bis"] = von, bis
        if not (ANTEIL_SUMME_MIN <= anteil_summe <= ANTEIL_SUMME_MAX):
            raise ValueError(f"tranchen.anteil_prozent-Summe nicht ~100: {anteil_summe}")
    except (ValueError, TypeError) as exc:
        logger.warning(
            "tranchen-Vorschlag verworfen (fehlerhaft, kein Signal-Fehler)%s: %s",
            f" fuer {symbol}" if symbol else "", exc)
        data["tranchen"] = None


def multi_asset_tranchen_erlaubt(regime_result, dca_flag: bool) -> bool:
    """Duerfen fuer dieses Multi-Asset-Signal Tranchen vorgeschlagen werden?

    BEWUSST OHNE BTC (Nutzer-Vorgabe 2026-08-09). Genutzt werden die beiden
    Groessen, die im Regime-Block von Aktien/Rohstoffe/Themen-ETF/Hedge
    ohnehin schon stehen - es kommt also keine neue Datenquelle hinzu.

    Die Krypto-Fassung erlaubt Tranchen bei baer/krise_extrem/seitwaerts, also
    "kein klarer Aufwaertsmarkt". Das Gegenstueck hier: erklaerter
    Aktien-Baermarkt ODER ein VIX, der Stress anzeigt. `seitwaerts` hat kein
    Pendant und wird deshalb nicht nachgebildet statt geraten.

    HEDGE RUFT DIESE FUNKTION NICHT MEHR (12.08.2026, Umbauplan Paket 0 /
    E1a). Der Zweifel unten hat sich bestaetigt und ist entschieden:
    `agent/hedge/pipeline.py` setzt `tranchen_erlaubt = False`, mit
    Begruendung an der Aufrufstelle. Die drei uebrigen Multi-Asset-Pipelines
    (aktien, rohstoff, themen_etf) nutzen sie unveraendert.

    VORLAEUFIG, mit Revisit-Bedingung (Nutzer-Einordnung 2026-08-09): *"bei
    Multiassets haben wir noch nicht alles beisammen, aber die Indexwerte sind
    nicht falsch."* S&P-Baermarkt und VIX sind also eine tragfaehige, aber
    nicht endgueltige Referenz. Wiedervorlage zusammen mit M6 (eigenes
    Regime-Konzept je Nicht-Krypto-Klasse) - dort steht auch die Frage, ob
    Rohstoffe dieselbe Referenz brauchen wie Aktien. Fuer Hedge war sie
    potenziell invers: DBPK/3QSS sind Short-Produkte, fuer die ein Baermarkt
    das GUTE Umfeld ist - genau deshalb ist Hedge jetzt draussen.
    """
    if not dca_flag:
        return False
    baermarkt = bool(getattr(regime_result, "equities_baermarkt_aktiv", False))
    vix = getattr(regime_result, "vix_label", None)
    return baermarkt or vix in VIX_LABELS_MIT_TRANCHEN
