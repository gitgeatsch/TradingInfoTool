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
# ⚠️ S6b (22.08.2026): EIN LAUF JE ASSET, NICHT ZWEI.
#
# Bis heute bekam Krypto zwei Urteile je Symbol - eines mit Spot-Etikett,
# eines mit Hebel-Etikett. Seit S5 produzierte der Hebel-Lauf in 76 % der
# Faelle Spot-Trades (Kapitel 129), und seit S6a stellten beide Laeufe
# WOERTLICH DIESELBE FRAGE. Zwei identische Fragen sind eine zu viel.
#
# DAS INSTRUMENT IST SEIT KAPITEL 88 EIN ERGEBNIS, KEINE KATEGORIE:
#
#     hebel = verlustanteil / stop_rel     Etikett "hebel", wenn > 1
#
# ⚠️ UND ES GIBT KEINEN ZIRKELBEZUG. `hebel_noetig` haengt an Verlustanteil
# und Stopabstand - nicht am Einsatz, nicht am Topf. Der Verlustanteil ist
# fuer Spot und Hebel derselbe (6 %). Das Etikett steht also fest, BEVOR ein
# Topf gebraucht wird; `rollen_lauf` leitet ihn danach daraus ab.
#
# DIE HANDELBARKEIT BLEIBT EINE EIGENSCHAFT DER GRUPPE - siehe
# `hebel_handelbar()` darunter. Sie war bis heute im Lauf-Etikett versteckt.
INSTRUMENTE_JE_GRUPPE = {
    "krypto": ("spot",),
    "aktien": ("spot",),
    "rohstoffe": ("spot",),
    "themen_etf": ("spot",),
    "hedge": ("absicherung",),
}

# Wo laesst sich ein Hebel ueberhaupt handeln? Bei Bitpanda nur Krypto.
#
# ⚠️ FUER DIE UEBRIGEN RECHNET DIE FORMEL ZWAR EINEN HEBEL AUS, handelbar ist
# er nicht (Umbauplan 88.3). Dort wirkt das Ergebnis als Betragsbegrenzung,
# nicht als Etikett - genau das tut `dimensioniere(hebel_handelbar=False)`.
HEBEL_HANDELBAR_JE_GRUPPE = {"krypto": True}


def hebel_handelbar(gruppe: str) -> bool:
    """Darf diese Gruppe gehebelt handeln?

    ⚠️ BIS S6b STAND DIESE FRAGE NIRGENDS. Sie steckte in
    `hebel_handelbar=(instrument == "hebel")` - also in der Frage, welcher
    LAUF gerade dran ist. Damit war die Handelbarkeit eine Eigenschaft des
    Ablaufs statt des Assets, und mit dem Wegfall des zweiten Laufs waere sie
    ersatzlos verschwunden."""
    return bool(HEBEL_HANDELBAR_JE_GRUPPE.get(
        str(gruppe or "").strip().lower(), False))


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


def zellen(watchlist=None, conn=None) -> list[dict]:
    """⚠️⚠️ DAS ZELLENMODELL — Schritt 3, 01.09.2026. NOCH OHNE AUFRUFER.

    Nutzervorgabe 31.08., woertlich: *„Asset z. B. LINK kommt in die
    Bewertung - entweder es kommt nur eine Strategie in Frage, weil dies die
    Bewertung ergibt, oder u. U. beides, Akkumulation und Hebel, aber nur
    wenn die Bewertung dies zulaesst."*

    ## Was eine ZELLE ist

    Eine Zelle ist ein Paar aus Instrument und Strategie fuer EIN Asset:

        (BTC, spot,  einstieg)      immer zulaessig
        (BTC, spot,  akkumulation)  nur wenn `dca_erlaubt`
        (BTC, hebel, einstieg)      nur wenn `hebel_pruefung_erlaubt`

    `laeufe()` liefert dagegen (Gruppe, Instrument, alle Symbole) - eine
    Zeile je Gruppe, und die Strategie kommt laufweit von aussen. Genau das
    war der zweite gescheiterte Anlauf: *„zuerst eigene Aufrufe je Strategie,
    dann ueber Spot pseudo-Hebel generiert"*.

    ## ⚠️ DREI QUELLEN, KEINE ZWEITE LISTE

        INSTRUMENTE_JE_GRUPPE      welche Instrumente die Gruppe fuehrt
        handelsauftrag.ERLAUBTE_PAARE   welche Strategie zu welchem
                                        Instrument passt (spot x swing ist
                                        seit 14.08. gestrichen)
        die Schalter des Nutzers   `asset_hebel_settings.hebel_pruefung_-
                                   erlaubt` (24 Assets) und
                                   `asset_dca_settings.dca_erlaubt`
                                   (Vorgabe BTC/ETH/SOL)

    Wer hier eine eigene Liste baute, baute die naechste, die einen Schalter
    vergisst - dieselbe Begruendung wie im Kopf von `laeufe()`.

    ## ⚠️ WAS DIESE FUNKTION NICHT TUT

    Sie entscheidet NICHT, ob eine Zelle ein Signal bekommt. Das ist die
    Bewertung (Stufe 11), und sie kommt in Schritt 4. Diese Funktion sagt
    nur, welche Fragen fuer ein Asset ueberhaupt GESTELLT werden duerfen.

    ⚠️ UND SIE HAT NOCH KEINEN AUFRUFER. Schritt 3 ist bewusst folgenlos:
    er erzeugt die Liste, damit sie geprueft werden kann, bevor Schritt 4
    den Ablauf umbaut. Ein Umbau, dessen Grundlage nicht geprueft ist, ist
    der dritte Anlauf, der scheitert.

    Rueckgabe: je Zelle ein dict mit `symbol`, `gruppe`, `instrument`,
    `strategie` und `warum` - der Grund, warum sie zulaessig ist. Der Grund
    steht dabei, weil eine Liste ohne Begruendung beim naechsten Zweifel
    nachgerechnet werden muss.
    """
    from agent import handelsauftrag as HA

    nach_gruppe = gruppiere(watchlist)
    hebel_erlaubt, dca_erlaubt = _schalter(conn)
    aus = []
    for gruppe, symbole in nach_gruppe.items():
        gefuehrt = INSTRUMENTE_JE_GRUPPE.get(gruppe, ("spot",))
        # ⚠️ HEBEL IST EIN INSTRUMENT DER GRUPPE, AUCH WENN `laeufe()` es
        # nicht fuehrt. S6b hat ihn aus dem LAUF genommen (Kapitel 88,
        # "Hebel als Ergebnis statt als Kategorie") - nicht aus der Frage,
        # ob er handelbar ist. Dafuer gibt es HEBEL_HANDELBAR_JE_GRUPPE.
        moeglich = set(gefuehrt)
        if HEBEL_HANDELBAR_JE_GRUPPE.get(gruppe):
            moeglich.add("hebel")
        for symbol in symbole:
            sym = str(symbol).upper()
            for instrument in sorted(moeglich):
                if instrument == "hebel" and sym not in hebel_erlaubt:
                    continue
                for strategie in HA.ERLAUBTE_PAARE.get(instrument, ()):
                    if strategie == "akkumulation" and sym not in dca_erlaubt:
                        continue
                    # ⚠️ SWING IST AKTUELL KEIN THEMA (Nutzerentscheidung
                    # 31.08.: *"nur Einstieg reicht, Swing aktuell kein
                    # Thema"*). Die Paar-Matrix kennt es weiter - hier
                    # faellt es raus, an EINER Stelle und mit Begruendung.
                    if strategie == "swing":
                        continue
                    aus.append({
                        "symbol": sym, "gruppe": gruppe,
                        "instrument": instrument, "strategie": strategie,
                        "warum": _warum(instrument, strategie, gefuehrt)})
    return aus


def _warum(instrument: str, strategie: str, gefuehrt) -> str:
    """Warum ist diese Zelle zulaessig? Steht in der Liste, nicht im Kopf."""
    if instrument == "hebel" and instrument not in gefuehrt:
        return ("Hebel ist fuer diese Gruppe handelbar und fuer dieses Asset "
                "freigeschaltet - `laeufe()` fuehrt ihn seit S6b nicht mehr")
    if strategie == "akkumulation":
        return "Akkumulation ist fuer dieses Asset freigeschaltet (dca_erlaubt)"
    return "Grundfall: das Instrument der Gruppe mit Einstieg"


def _schalter(conn=None) -> tuple[set, set]:
    """Die beiden Schalter des Nutzers - aus der Datenbank, nicht geraten.

    ⚠️ OHNE VERBINDUNG DIE VORGABEN. `database.db.get_dca_erlaubt` faellt
    ohne Zeile auf `{BTC, ETH, SOL}` zurueck; der Hebelschalter hat keine
    Vorgabe - ohne Datenbank ist er fuer NIEMANDEN an. Das ist die
    vorsichtige Richtung: lieber keine Hebelzelle als eine erfundene.
    """
    hebel, dca = set(), set()
    if conn is None:
        try:
            import database.db as _db
            return set(), set(getattr(_db, "_DCA_ERLAUBT_DEFAULT_SYMBOLS",
                                      {"BTC", "ETH", "SOL"}))
        except Exception:                                    # noqa: BLE001
            return set(), {"BTC", "ETH", "SOL"}
    try:
        for zeile in conn.execute(
                "SELECT symbol FROM asset_hebel_settings "
                "WHERE hebel_pruefung_erlaubt=1"):
            hebel.add(str(zeile[0]).upper())
    except Exception:                                        # noqa: BLE001
        pass
    try:
        import database.db as _db
        vorgabe = set(getattr(_db, "_DCA_ERLAUBT_DEFAULT_SYMBOLS",
                              {"BTC", "ETH", "SOL"}))
        gesetzt = {str(s).upper(): int(w or 0) for s, w in conn.execute(
            "SELECT symbol, dca_erlaubt FROM asset_dca_settings")}
        for sym in vorgabe:
            if gesetzt.get(sym, 1):
                dca.add(sym)
        for sym, wert in gesetzt.items():
            if wert:
                dca.add(sym)
    except Exception:                                        # noqa: BLE001
        dca = {"BTC", "ETH", "SOL"}
    return hebel, dca


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
