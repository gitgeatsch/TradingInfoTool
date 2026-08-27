# -*- coding: utf-8 -*-
"""EINE Position je Symbol - nicht je Signal (27.08.2026).

⚠️ NICHT ZU VERWECHSELN MIT `agent/positionierung.py`. Das ist Rolle G und
beschreibt den TERMINMARKT (Open Interest, Funding, Long-Konten) - also was
ANDERE halten. Dieses Modul beschreibt, was DER NUTZER haelt.

DIE NUTZERFESTLEGUNG, die das ausloest (26.08.2026):

    *"eine position bleibt eine Position - hier sollte auch der verlust
    sichtbar sein und somit ein break even"*

DER BEFUND, DER SIE NOETIG MACHT. Gemessen am NB-Stand vom 26.08. ueber die
offenen Spot-Signale:

    266 offene Signale auf 44 Symbole
    37 Symbole MEHRFACH gefuehrt
    222 ueberzaehlige Fuehrungen = 83 %

    BIO 21x | BTC 17x | KAIA 14x | LINK 14x | AVAX 13x | ETH 12x

⚠️ UND VIERZEHN SYMBOLE TRAGEN GLEICHZEITIG VERSCHIEDENE HANDLUNGEN. HYPE
stand am selben Tag auf NACHKAUFEN *und* REDUZIEREN. Das ist kein
Meinungsstreit des Modells, sondern eine Buchhaltungsfrage: es wurden zwei
verschiedene Signale beurteilt, nicht zweimal dieselbe Position.

DIE URSACHE steht in einer einzigen Zeile in `backward_tracking`:
*"Offene SIGNALE, bei denen der Trailing-Stop nachgezogen gehoert."* Die
Ausstiegspruefung laeuft ueber Signale. Jedes NACHKAUFEN erzeugt eine eigene
Fuehrung mit eigenem MFE und eigenem nachgezogenen Stop - fuer einen Bestand,
den der Nutzer als EINE Position haelt, mit EINEM Einstand.

## Was dieses Modul NICHT tut

Es greift NICHT ein. Keine Aenderung an `compute_ausstiegs_empfehlungen`,
keine Aenderung an der Mail, kein Gate. Es ist eine LESEFUNKTION, die den
Zustand so darstellt, wie der Nutzer ihn haelt - damit die Wirkung eines
Umbaus gerechnet werden kann, bevor er stattfindet (N-6).

## Woher die Zahlen kommen - keine zweite Quelle

    Menge und Einstand   `rollen_eingabe.bestand()`   (beide Einstandsspalten,
                         manuelle hat Vorrang, gestaktes additiv)
    Ergebnis in Euro     `verkaufsrechnung.rechne()`  (dieselbe Rechnung, die
                         die Verkaufsmail benutzt)

Beide existieren seit dem 14./15.08. ⚠️ EINE ZWEITE FASSUNG WAERE DIE NAECHSTE
STELLE, AN DER MAIL UND DATENBANK AUSEINANDERLAUFEN - dieselbe Begruendung wie
bei `handelsauftrag` und `tranchen`.

## Der Stop-Vorbehalt

Eine Spot-Position hat nach Nutzerangabe KEINEN Stop ("aktuell auch ohne
StopLoss"). Sie hat deshalb auch kein R und keinen sinnvollen Positions-MFE.
Was sie hat, ist ein Einstand - und daraus Gewinn/Verlust in Euro und Prozent.
Genau das gibt dieses Modul zurueck, und nichts darueber hinaus. Wer hier ein
R erfaende, damit eine Formel rechnet, baute den Fehler ein, den N-11
aufgedeckt hat.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Diese Aktionen halten ein Signal "offen" im Sinne der Positionsfuehrung.
# HALTEN/NICHTS_TUN erzeugen keine Position - sie sind Schattenbuchungen.
AKTIONEN_MIT_BESTANDSWIRKUNG = ("KAUFEN", "NACHKAUFEN", "REDUZIEREN",
                                "VERKAUFEN")


@dataclass
class Position:
    """Was der Nutzer in EINEM Symbol haelt - unabhaengig davon, aus wie
    vielen Signalen es entstanden ist."""

    symbol: str
    instrument: str = "spot"
    menge_frei: float = 0.0
    menge_gestakt: float = 0.0
    einstand_eur: float | None = None
    kurs_eur: float | None = None
    strategie: str | None = None
    signale: list = field(default_factory=list)

    @property
    def menge_gesamt(self) -> float:
        return float(self.menge_frei) + float(self.menge_gestakt)

    @property
    def im_bestand(self) -> bool:
        return self.menge_gesamt > 0

    @property
    def wert_eur(self) -> float | None:
        if not self.kurs_eur:
            return None
        return self.menge_gesamt * float(self.kurs_eur)

    @property
    def ergebnis_eur(self) -> float | None:
        """Gewinn/Verlust in Euro. `None`, wenn der Einstand fehlt.

        ⚠️ KEINE NAEHERUNG BEI FEHLENDEM EINSTAND. Ein geschaetzter Einstand
        saehe aus wie ein bekannter - dieselbe Klasse Fehler wie die zwei
        Alter der Datenfrische."""
        # ⚠️ OHNE BESTAND KEIN ERGEBNIS, und NICHT die Null. Ein Symbol mit
        # offenen Signalen, aber ohne Menge, ergab hier `0,00 EUR` - und das
        # liest sich wie "weder Gewinn noch Verlust" statt wie "nichts da".
        # Beim ersten Nachweis standen dadurch 44 Positionen als berechenbar,
        # obwohl nur 29 einen Bestand hatten.
        if not self.im_bestand:
            return None
        if self.einstand_eur is None or not self.kurs_eur:
            return None
        return (float(self.kurs_eur) - float(self.einstand_eur)) * self.menge_gesamt

    @property
    def ergebnis_prozent(self) -> float | None:
        if not self.einstand_eur or not self.kurs_eur:
            return None
        return 100.0 * (float(self.kurs_eur) / float(self.einstand_eur) - 1.0)

    @property
    def break_even_eur(self) -> float | None:
        """Der Kurs, bei dem die Position weder gewinnt noch verliert.

        Das IST der Durchschnittseinstand - die Eigenschaft existiert, weil
        der Nutzer nach dieser Groesse gefragt hat und `einstand_eur` nicht
        beschreibt, wozu sie dient."""
        return self.einstand_eur

    @property
    def anzahl_fuehrungen(self) -> int:
        """Wie viele Signale heute als eigene Position gefuehrt wuerden."""
        return len(self.signale)


def _kurs(conn, symbol: str) -> float | None:
    """Letzter bekannter EUR-Kurs. `None`, wenn keiner vorliegt."""
    try:
        r = conn.execute(
            "SELECT price_eur FROM price_cache WHERE symbol=? "
            "ORDER BY fetched_at DESC LIMIT 1", (symbol,)).fetchone()
        if r and r[0]:
            return float(r[0])
    except Exception as exc:                                 # noqa: BLE001
        logger.debug("Kurs fuer %s nicht lesbar: %s", symbol, exc)
    return None


def lade(conn, symbole=None, instrument: str = "spot",
         db: str | None = None) -> list:
    """Alle Positionen - eine je Symbol.

    Symbole ohne Bestand UND ohne offenes Signal kommen nicht vor: sie sind
    keine Position, sondern ein Kandidat.

    ⚠️ `conn` wird uebergeben, nie hier geoeffnet - dieselbe Regel wie in
    `rollen_lauf` ("ohne Verbindung kein Lauf")."""
    from agent import rollen_eingabe as RE

    tabelle = "hebel_signals" if instrument == "hebel" else "signals"
    platzhalter = ""
    parameter: list = []
    if symbole:
        platzhalter = f" AND symbol IN ({','.join('?' * len(symbole))})"
        parameter = list(symbole)

    # Offene Signale je Symbol sammeln. Sie werden NICHT zu Positionen -
    # sie sind die Vorgeschichte EINER Position.
    offen: dict = {}
    try:
        for r in conn.execute(
                f"SELECT symbol, action, created_at, strategie FROM {tabelle} "
                f"WHERE (outcome_status IS NULL OR outcome_status='offen')"
                f"{platzhalter} ORDER BY symbol, created_at", parameter):
            if str(r[1]) in AKTIONEN_MIT_BESTANDSWIRKUNG:
                offen.setdefault(str(r[0]), []).append(
                    {"aktion": str(r[1]), "zeit": str(r[2]),
                     "strategie": r[3]})
    except Exception as exc:                                 # noqa: BLE001
        logger.warning("Offene Signale nicht lesbar (%s)", exc)

    kandidaten = set(offen)
    if symbole:
        kandidaten |= {str(s) for s in symbole}

    aus = []
    for sym in sorted(kandidaten):
        menge = einstand = None
        try:
            menge, einstand = RE.bestand(sym, db=db, instrument=instrument)
        except Exception as exc:                             # noqa: BLE001
            logger.warning("Bestand fuer %s nicht lesbar (%s)", sym, exc)
        sig = offen.get(sym, [])
        # Die Strategie der Position ist die des JUENGSTEN Signals - sie
        # beschreibt, wie zuletzt gehandelt wurde. `None` bleibt `None`;
        # eine Vorgabe zu erfinden hiesse, die Luecke zu verstecken.
        strategie = sig[-1]["strategie"] if sig else None
        p = Position(symbol=sym, instrument=instrument,
                     menge_frei=float(menge or 0.0),
                     einstand_eur=float(einstand) if einstand else None,
                     kurs_eur=_kurs(conn, sym), strategie=strategie,
                     signale=sig)
        if p.im_bestand or sig:
            aus.append(p)
    return aus


def zeilen(p: Position) -> list:
    """Die Position als Text - fuer die Mail und fuer die Diagnose.

    ABSOLUTE ZAHLEN VOR RELATIVEN, wie ueberall sonst (Nutzervorgabe
    12.08.)."""
    from agent.schreibweise import de

    z = [f"{p.symbol} - eine Position"
         + (f" ({p.anzahl_fuehrungen} Signale)" if p.anzahl_fuehrungen > 1
            else "")]
    if not p.im_bestand:
        z.append("   nicht im Bestand")
        return z
    z.append(f"   Menge        {de(p.menge_gesamt, 6)}"
             + (f" (davon {de(p.menge_gestakt, 6)} gestakt)"
                if p.menge_gestakt else ""))
    if p.einstand_eur is None:
        z.append("   Einstand     unbekannt - Gewinn/Verlust nicht berechenbar")
        return z
    z.append(f"   Break-even   {de(p.einstand_eur, 4)} EUR")
    if p.wert_eur is not None:
        z.append(f"   Wert heute   {de(p.wert_eur, 2)} EUR")
    if p.ergebnis_eur is not None:
        z.append(f"   Ergebnis     {de(p.ergebnis_eur, 2)} EUR"
                 f"  ({de(p.ergebnis_prozent, 1)} %)")
    return z
