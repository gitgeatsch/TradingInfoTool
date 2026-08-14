# -*- coding: utf-8 -*-
"""Welches Asset gehoert in welchen Lauf (14.08.2026, Multi-Asset-Umstieg).

DIE FALLE, DIE DIESES MODUL VERHINDERT, ist am 06.08. schon einmal
zugeschnappt. `agent/hedge/pipeline.py` beschreibt sie:

    "Hedge ist KEINE Assetklasse - die Watchlist kennt nur `aktien`,
     `rohstoffe`, `krypto` und `etf`. DBPK und 3QSS stehen als `etf` darin und
     sind nur ueber ihre Mitgliedschaft in SYMBOL_ZU_HEBEL_FAKTOR erkennbar.
     Diese Pruefung stand bisher als `asset.symbol in SYMBOL_ZU_HEBEL_FAKTOR`
     an sechs verstreuten Stellen; eine siebte hat sie am 06.08. schlicht
     vergessen (der neue OHLC-Refresh filterte auf eine Assetklasse 'hedge',
     die es nicht gibt, und liess die beiden Instrumente aus)."

**Und mein `rollen_lauf.KLASSEN` hat genau diesen Fehler wiederholt** - es
fuehrte "hedge" als Assetklasse. Ein Lauf danach haette null Symbole gefunden
und wie ein ruhiger Tag ausgesehen.

DREI BEGRIFFE, DIE MAN AUSEINANDERHALTEN MUSS:

    Assetklasse   was in der Watchlist steht: krypto | aktien | rohstoffe | etf
    Bereich       wonach der Faktenblock seine Zusatzinfo waehlt:
                  krypto_spot | krypto_hebel | aktien | rohstoffe |
                  themen_etf | hedge
    Instrument    spot | hebel | absicherung - WIE gehandelt wird

Sie sehen sich aehnlich und sind es nicht. `etf` zerfaellt in zwei Bereiche
(hedge und themen_etf), `krypto` in zwei (nach Instrument), und `absicherung`
ist ein Instrument, kein Ort.

WOHER DIE WATCHLIST KOMMT: aus `config.yaml`, nicht aus der Datenbank
(`config.get_watchlist()`). Das ist der zweite Punkt, den ich falsch
dokumentiert hatte - die Tabelle `watchlist` gibt es gar nicht.
"""
from __future__ import annotations

# Was die Watchlist wirklich kennt. NICHT erweitern, ohne `config.yaml`
# anzufassen - eine Klasse, die dort niemand vergibt, findet null Symbole.
ASSETKLASSEN = ("krypto", "aktien", "rohstoffe", "etf")

# Welches Instrument fuer welche Gruppe sinnvoll ist. Krypto ist die einzige
# Klasse mit zwei - Hebel gibt es bei Bitpanda nur dort.
INSTRUMENTE_JE_GRUPPE = {
    "krypto": ("spot", "hebel"),
    "aktien": ("spot",),
    "rohstoffe": ("spot",),
    "themen_etf": ("spot",),
    "hedge": ("absicherung",),
}


def gruppe(asset) -> str:
    """Der BEREICH dieses Assets - nicht seine Assetklasse.

    Der Unterschied ist genau ein Fall: ein `etf`, der ein Absicherungs-
    instrument ist, gehoert in die Gruppe `hedge`, alle uebrigen in
    `themen_etf`. Die Erkennung kommt aus `hedge/pipeline.ist_hedge_instrument`
    - der EINEN Stelle, an der sie steht, seit sie an sieben verstreuten
    Stellen einmal zu wenig stand."""
    from agent.hedge.pipeline import ist_hedge_instrument

    klasse = str(getattr(asset, "assetklasse", "") or "").strip().lower()
    if klasse == "etf":
        try:
            return "hedge" if ist_hedge_instrument(asset) else "themen_etf"
        except Exception:                                    # noqa: BLE001
            return "themen_etf"
    return klasse if klasse in ASSETKLASSEN else "krypto"


def gruppiere(watchlist=None) -> dict[str, list[str]]:
    """Alle Symbole nach Gruppe. Cash-Aequivalente fallen heraus.

    EIN STABLECOIN IST KEIN HANDELSKANDIDAT. `ist_cash_aequivalent` markiert
    ihn; ihn zu beurteilen kostet einen Aufruf fuer eine Frage, die sich nicht
    stellt. Dieselbe Zeile steht in `hebel_screening.py:332` - hier ist sie
    keine Kopie, sondern dieselbe Eigenschaft am selben Objekt."""
    import config as config_module

    if watchlist is None:
        watchlist = config_module.get_watchlist()
    aus: dict[str, list[str]] = {}
    for a in watchlist:
        if getattr(a, "ist_cash_aequivalent", False):
            continue
        aus.setdefault(gruppe(a), []).append(a.symbol)
    return {k: sorted(v) for k, v in sorted(aus.items())}


def laeufe(watchlist=None) -> list[tuple[str, str, list[str]]]:
    """Alle (Gruppe, Instrument, Symbole) fuer einen vollstaendigen Umlauf.

    DIE EINE STELLE, an der steht, was ein Durchgang ueber ALLE Assets
    bedeutet. Wer sie umgeht, baut die naechste Liste, die eine Gruppe
    vergisst - so wie der OHLC-Refresh am 06.08. die Absicherung vergass."""
    nach_gruppe = gruppiere(watchlist)
    aus = []
    for g, symbole in nach_gruppe.items():
        for instrument in INSTRUMENTE_JE_GRUPPE.get(g, ("spot",)):
            aus.append((g, instrument, symbole))
    return aus


def kern_symbole(watchlist=None) -> set:
    """Die `core`-Assets der Watchlist - der Vorrang in der Warteschlange.

    KORREKTUR MEINER EIGENEN DOKUMENTATION (14.08.): ich hatte geschrieben, die
    Stufe "vorgemerkt" sei leer, weil die Tabelle `watchlist` keine Spalten
    habe. Die Watchlist ist keine Tabelle - sie steht in `config.yaml`, und
    jedes Asset traegt dort eine `rolle`. Dreizehn davon sind `core`, und der
    alte Budget-Allocator benutzt genau dieses Merkmal
    (`budget_allocator.py:348`)."""
    import config as config_module

    if watchlist is None:
        watchlist = config_module.get_watchlist()
    return {str(a.symbol).upper() for a in watchlist
            if str(getattr(a, "rolle", "") or "").strip().lower() == "core"}
