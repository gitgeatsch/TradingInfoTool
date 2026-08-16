# -*- coding: utf-8 -*-
"""Die Schalter, die der Nutzer je Asset in der GUI setzt (14.08.2026).

GEFUNDEN IN DER QUERPRUEFUNG GUI/Einstellungen/Assets, auf Nutzerwunsch: drei
Schalter, die es in der Oberflaeche gibt, die die alten Pipelines lesen - und
die die Rollen-Kette komplett ignoriert hat.

    asset_dca_settings.dca_erlaubt          je Asset: darf akkumuliert werden?
    asset_hebel_settings.hebel_pruefung_erlaubt  je Asset: Hebel pruefen?
    asset_bitpanda_override.bitpanda_gelistet_override  handelbar trotz
                                            fehlendem Listing-Eintrag?

DIE NUTZERVORGABE DAZU STEHT WOERTLICH IM ALTEN CODE (12.08.):

    "ich moechte selbst entscheiden, bei welchen Assets die Strategie
     angewendet wird - ueberall moeglich, aber nur dort Signale erzeugen, wo
     ich das selektiv moechte."

Eine Kette, die diese Schalter uebergeht, tut genau das Gegenteil: sie erzeugt
Signale, wo der Nutzer ausdruecklich keine wollte. Das ist schlimmer als ein
fehlendes Merkmal - es ist eine ueberstimmte Entscheidung.

WARUM DAS EIN KOSTENFILTER IST UND KEIN QUALITAETSFILTER, und deshalb hier
erlaubt: die Schalter sagen nichts ueber Marktlagen oder Erfolgsaussichten. Sie
sagen, was der NUTZER handeln will. Ein Asset, fuer das er keinen Hebel will,
braucht kein Hebel-Urteil - nicht weil es schlecht waere, sondern weil er es
nicht ausfuehren wuerde. Der Deadloop entstand aus Filtern, die dem Modell
widersprachen; dieser hier setzt nur um, was der Nutzer gesagt hat.

FAIL-OPEN, NICHT FAIL-CLOSED. Ist ein Schalter nicht lesbar, gilt "erlaubt".
Ein Lesefehler darf nicht dazu fuehren, dass die Kette stumm nichts mehr tut -
das waere der Deadloop durch die Hintertuer.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _ist_cash_aequivalent(symbol: str, watchlist=None) -> bool:
    """Ist das ein Stablecoin oder eine andere Cash-Vertretung?

    DIE OBERFLAECHE WEISS DAS LAENGST, die Kette wusste es nicht (15.08.2026).
    `ui/app.py` baut die Spalte "Hebel-Pruefung" ausdruecklich nur fuer
    `a.assetklasse == "krypto" and not a.ist_cash_aequivalent` - EURCV steht
    dort mit "-", also "kommt gar nicht in Frage".

    `darf_analysiert_werden()` kannte diese Bedingung nicht und fragte nur den
    Schalter. Der hat fuer EURCV keine Zeile und liefert damit "erlaubt".
    Anzeige und Verhalten sagten Gegenteiliges: in der GUI ein Strich, in der
    Kette ein Hebel-Kandidat.

    NUR EIN DATENMANGEL HAT DAS AUFGEHALTEN. EURCV hat keine Tageskerzen und
    fiel deshalb schon an der Faktenstufe heraus - das ist Zufall, keine
    Regel. Ein gehebelter Stablecoin ist kein Trade, sondern ein Denkfehler mit
    laufenden Kosten."""
    import config as config_module

    try:
        if watchlist is None:
            watchlist = config_module.get_watchlist()
        sym = str(symbol or "").strip().upper()
        for a in watchlist:
            if str(a.symbol).strip().upper() == sym:
                return bool(getattr(a, "ist_cash_aequivalent", False))
    except Exception:                                        # noqa: BLE001
        logger.debug("Cash-Aequivalenz nicht lesbar fuer %s", symbol)
    return False


def darf_analysiert_werden(conn, symbol: str, instrument: str,
                           strategie: str, watchlist=None
                           ) -> tuple[bool, str | None]:
    """Will der Nutzer fuer DIESES Paar ueberhaupt ein Urteil?

    Gibt `(erlaubt, grund)` zurueck. `grund` ist nur gesetzt, wenn abgelehnt -
    er landet in der Durchlaessigkeitstabelle, damit sichtbar bleibt, dass hier
    eine NUTZERENTSCHEIDUNG gewirkt hat und nicht die Marktlage.

    Die Pruefung sitzt VOR dem Modellaufruf: ein Asset, das der Nutzer nicht
    handeln will, soll kein Kontingent kosten."""
    import database.db as db

    sym = str(symbol or "").strip().upper()
    i = str(instrument or "").strip().lower()
    s = str(strategie or "").strip().lower()

    if i == "hebel":
        # DIESELBE BEDINGUNG WIE DIE OBERFLAECHE, und sie steht VOR dem
        # Schalter: wo die GUI "-" anzeigt, gibt es keine Entscheidung zu
        # lesen. Der Schalter beantwortet "will der Nutzer das?", diese Zeile
        # beantwortet "kann man das ueberhaupt fragen?".
        if _ist_cash_aequivalent(sym, watchlist):
            return False, "Cash-Aequivalent - kein Hebel-Kandidat"
        # ⚠️ EIN LESEFEHLER HEISST NICHT "ERLAUBT" (16.08.2026).
        #
        # Hier stand ein `logger.debug` und danach ging es weiter - ein
        # nicht lesbarer Schalter liess das Asset also DURCH. Nachgestellt:
        # ohne `conn.row_factory = sqlite3.Row` wirft
        # `get_hebel_pruefung_erlaubt` einen TypeError, und ein
        # ausdruecklich ABGESCHALTETES Asset wurde trotzdem beurteilt.
        #
        # Die Vorgabe des Nutzers laesst das nicht zu: *"ueberall moeglich,
        # aber nur dort Signale erzeugen, wo ich das selektiv moechte."*
        # Wer nicht lesen kann, was gewollt ist, darf es nicht annehmen.
        #
        # UND DIE MELDUNG GEHT AUF WARNUNG. Auf `debug` erschien sie in
        # keinem Log - dieselbe Klasse wie die Regime-Dauer, die aus genau
        # demselben Grund (fehlende Zeilenfabrik) tagelang fehlte.
        try:
            if not db.get_hebel_pruefung_erlaubt(conn, sym):
                return False, "Hebel-Pruefung fuer dieses Asset abgeschaltet"
        except Exception as exc:                             # noqa: BLE001
            logger.warning("Hebel-Schalter fuer %s nicht lesbar (%s) - "
                           "Asset wird NICHT beurteilt", sym, exc)
            return False, "Hebel-Schalter nicht lesbar"

    if s == "akkumulation":
        # Dieselbe Regel wie beim Hebelschalter darueber.
        try:
            if not db.get_dca_erlaubt(conn, sym):
                return False, "DCA fuer dieses Asset abgeschaltet"
        except Exception as exc:                             # noqa: BLE001
            logger.warning("DCA-Schalter fuer %s nicht lesbar (%s) - "
                           "Asset wird NICHT beurteilt", sym, exc)
            return False, "DCA-Schalter nicht lesbar"

    return True, None


def mail_richtung_erlaubt(richtung: str | None, config: dict | None = None) -> bool:
    """Darf ein Hebel-Signal DIESER Richtung per E-Mail hinaus?

    HIERHER GEZOGEN AM 15.08.2026, aus `scheduler/background.py`. Die
    Rollen-Kette verschickt ueber ihr eigenes `versand` und lief an der
    Funktion vorbei - ein SHORT der neuen Kette waere trotz `nur_long`
    verschickt worden. Statt die Pruefung dort nachzubauen (die Kopierfalle,
    die dieses Projekt mehrfach erwischt hat), steht sie jetzt bei den anderen
    Nutzerschaltern, und BEIDE Ketten fragen dieselbe Stelle.

    DIE VORGABE DES NUTZERS, woertlich vom 05.08.2026:

        der Schalter soll "NULL Einfluss auf die Funktionsweise im
        Hintergrund" haben - SHORTs sollen lediglich nicht per E-Mail kommen
        und nicht in der GUI erscheinen.

    UND DER GRUND IST MESSHYGIENE, nicht Ertrag. Bis zum 05.08. sass der Filter
    VOR der Verarbeitung: zwei Vorfilter im Budget-Allocator warfen
    SHORT-Kandidaten schon vor dem Modellaufruf weg, ein Veto im Risk-Gate
    drehte `action` nachtraeglich auf HALTEN. Folge: **313 SHORT-Vorschlaege
    lagen als "HALTEN" in der Datenbank** und haben bei der Ursachensuche zum
    31.07.-Bruch wiederholt Populationen vermischt. Jede Auswertung ueber
    Richtungen war strukturell verzerrt.

    KEIN VETO, KEINE ZUSTANDSAENDERUNG. Diese Funktion entscheidet nur ueber
    den Versand. Das Signal wird geschrieben, das Gate zaehlt es als
    durchgekommen, der Ausgang wird normal verfolgt und gemessen - mit seiner
    echten `richtung` und seiner echten `action`.

    WER SIE AN EINER ANDEREN STELLE ALS DEM VERSAND AUFRUFT, baut den Fehler
    von 2026-07-28 nach."""
    import config as config_module

    try:
        cfg = config if config is not None else config_module.load_config()
        modus = (cfg.get("budget_allocator", {})
                 .get("hebel_richtung_modus", "beide"))
    except Exception:                                        # noqa: BLE001
        # FAIL-OPEN wie die uebrigen Schalter: ein Lesefehler darf keine
        # Nachricht verschlucken.
        return True
    if modus != "nur_long":
        return True
    return str(richtung or "").upper() != "SHORT"


def ist_handelbar(conn, symbol: str, bitpanda_gelistet=None) -> bool:
    """Kann der Nutzer das Asset ueberhaupt kaufen?

    DER OVERRIDE SCHLAEGT DAS LISTING, nicht umgekehrt - so macht es die alte
    Kette (`krypto/pipeline.py:690`), und der Grund ist praktisch: die
    Listing-Abfrage kennt nicht jeden Sonderfall, der Nutzer schon.

    `None` als Listing heisst "nicht abgefragt" und gilt als handelbar. Eine
    Empfehlung wegen einer fehlgeschlagenen API-Abfrage zu unterdruecken waere
    ein stiller Ausfall."""
    import database.db as db

    if bitpanda_gelistet:
        return True
    try:
        if db.get_bitpanda_gelistet_override(conn, str(symbol).strip().upper()):
            return True
    except Exception:                                        # noqa: BLE001
        pass
    return bitpanda_gelistet is None
