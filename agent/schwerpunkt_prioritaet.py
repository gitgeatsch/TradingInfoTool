"""Manuelle Schwerpunkte vorziehen - gemeinsame Achse fuer alle Assetklassen.

WOZU DAS HIER STEHT UND NICHT IN EINER PIPELINE: es ist EINE Regel, und sie
soll fuer jede Assetklasse dieselbe sein, sobald eine Klasse sie braucht.
Dasselbe Muster wie `agent/provider_sperre.py` - zwei Kopien wuerden garantiert
auseinanderlaufen.

## Die Anforderung, im Wortlaut des Nutzers (07.08.)

> *"wenn z.B. ein Thema trendet, bekommen andere wichtige Bereiche keinen Raum,
> obwohl ich der Meinung bin, dass Energie aktuell unterbewertet ist und
> zukuenftig massiv steigen wird - und diese Trades werden vergessen bzw. gehen
> unter."*

Das dreht die uebliche Anforderung um: ein Mechanismus, der Aufmerksamkeit nach
TRENDSTAERKE verteilt, tut systematisch das Gegenteil dessen, was antizyklisches
Investieren braucht. Ein Themenfeld ist oft gerade dann interessant, WEIL
niemand hinsieht.

**Deshalb eine stabile Partition und KEIN Re-Sort.** Schwerpunkt-Assets nach
vorn, alle uebrigen behalten ihre bisherige Reihenfolge, und innerhalb beider
Gruppen aendert sich nichts. Wer hier nach Score oder Trendstaerke sortierte,
haette die Anforderung ins Gegenteil verkehrt.

## Reichweite heute: 13 von 57 Assets

Nur 7 ETF, 4 Rohstoffe und 2 Aktien tragen ueberhaupt eine `hauptgruppe` -
**kein einziges Krypto-Asset**. Aufgerufen wird diese Funktion deshalb bislang
nur von `agent/multi_asset_batch.py`.

## Warum die KRYPTO-KETTE sie NICHT aufruft - und wann sie es tun wuerde

Zwei Gruende, und der erste ist der wichtigere:

**1. Krypto hat bereits eine Achse, nur eine andere.** Der Budget-Allocator
sortiert Kandidaten nach `score_gesamt` und legt darueber die
SLA-Reservierung: ueberfaellige Kandidaten werden nach echter Wartezeit
vorgezogen, als GARANTIE statt als Score-Boost (ausdrueckliche
Nutzer-Entscheidung: *"kein Boost, sondern eine echte Garantie"*, siehe
`budget_allocator.py::_priorisiere_nach_wartezeit()`). Krypto fehlt also keine
Priorisierung - es fehlt eine THEMENBASIERTE, und die ist nur dann noetig, wenn
man Krypto nach Unterthemen steuern will.

**2. Es gibt keine Daten dafuer.** Die 44 Krypto-Assets haben weder
`hauptgruppe` noch `unterkategorie`. Ein Aufruf hier waere ein toter Aufruf -
`ist_manueller_schwerpunkt(None, None)` liefert immer False. Genau das ist die
stille Attrappe, die dieses Projekt schon zweimal in die Irre gefuehrt hat:
verdrahtet, aber wirkungslos, und niemand merkt es.

**Die Bedingung fuer den Anschluss ist deshalb inhaltlich, nicht technisch.**
Technisch ist es eine Zeile - dieselbe, die in `multi_asset_batch.py` steht.
Gebraucht wird eine Krypto-Taxonomie, und die bildet eine Anlagesicht ab, keine
Datenstruktur.

**Ausgangspunkt dafuer, falls es soweit kommt** (Nutzer-Hinweis 2026-08-09):
die Achse waeren die zugrundeliegenden NARRATIVE, mit **BTC gegen Altcoins als
Grundgruppe**. Erst danach feinere Narrative innerhalb der Altcoins. Bewusst
NICHT jetzt gebaut - der Nutzer hat das Thema als richtig bestaetigt und die
Umsetzung ausdruecklich vertagt.

## Was diese Funktion NICHT tut

Sie aendert nur die REIHENFOLGE, nie die AUSWAHL. Ob ein Deckel greift und wie
viele Kandidaten durchkommen, entscheidet allein die aufrufende Pipeline. In
`multi_asset_batch` gibt es gar keinen Stueckzahl-Deckel - spuerbar wird die
Prioritaet dort erst, wenn mitten im Lauf ein Anbieter-Tagesbudget auslaeuft
oder der Circuit Breaker zuschlaegt.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def ziehe_schwerpunkte_vor(assets: list, *, kontext: str = "") -> tuple[list, list]:
    """Stabile Partition: Schwerpunkt-Assets nach vorn, Rest unveraendert.

    Gibt `(neue_reihenfolge, bevorzugte)` zurueck. Ist kein Asset betroffen -
    etwa weil `schwerpunkte.manuell` leer ist oder die Klasse gar keine
    `hauptgruppe` fuehrt - kommt die Liste Zeichen fuer Zeichen unveraendert
    zurueck und `bevorzugte` ist leer. Der No-Op-Fall ist der Normalfall und
    ausdruecklich kein Sonderweg.

    `kontext` erscheint nur in der Log-Zeile (z.B. "Multi-Asset-Batch"), damit
    bei mehreren Aufrufern erkennbar bleibt, wessen Reihenfolge sich geaendert
    hat.
    """
    # Lokal importiert: `config` laedt beim Import die YAML, und dieses Modul
    # soll auch von Tests importierbar sein, die das gar nicht brauchen.
    import config

    # EINE Schleife statt zweier Listenfilter: `a not in bevorzugt` wuerde
    # Dataclass-Objekte ueber `==` vergleichen und bei wertgleichen Assets das
    # falsche Element aussortieren.
    bevorzugt: list = []
    uebrige: list = []
    for asset in assets:
        ziel = bevorzugt if config.ist_manueller_schwerpunkt(
            getattr(asset, "hauptgruppe", None),
            getattr(asset, "unterkategorie", None)) else uebrige
        ziel.append(asset)

    if not bevorzugt:
        return list(assets), []

    logger.info(
        "%sSchwerpunkt-Prioritaet: %d von %d Assets vorgezogen (%s).",
        f"{kontext}: " if kontext else "",
        len(bevorzugt), len(assets),
        ", ".join(getattr(a, "symbol", "?") for a in bevorzugt),
    )
    return bevorzugt + uebrige, bevorzugt
