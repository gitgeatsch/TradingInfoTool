# -*- coding: utf-8 -*-
"""Cooldown - wann darf dasselbe Asset wieder ein Signal bekommen (13.08.2026).

DER GRUND STEHT IN DEN EIGENEN MESSDATEN dieses Projekts:

    Die Verlustquelle war die Wiederholung - fuenf Symbole trugen 102 % des
    Minus.

Die alte Kette hat daraus Konsequenzen gezogen und fuehrt acht
Cooldown-Einstellungen. **Die Rollen-Kette las keine einzige davon.** Sie lief
bei jedem Durchgang ueber alle Symbole und durfte jedes Mal dasselbe Asset
empfehlen - bei zwei Laeufen am Tag und 250 EUR je Tranche waeren das 500 EUR
taeglich in dasselbe Asset, solange das Modell es mag.

Gefunden bei der vollstaendigen Pruefung der alten Kette am 13.08. (Umbauplan
Kap. 16.4), ausgeloest durch die Nutzerfrage nach den Betraegen.

WARUM HIER UND NICHT IM GATE. Das Gate zaehlt, wo Signale verlorengehen - es
entscheidet nicht, warum. Die Frage "ist dieses Asset gerade gesperrt" ist eine
eigene, und sie braucht die Datenbank; das Gate braucht sie sonst nirgends.

WAS DIESE DATEI NICHT TUT: sie kennt keine Sonderfaelle der alten Kette
(ausgemustert, Re-Evaluierung, Position). Die Rollen-Kette hat diese Zustaende
nicht - sie hier nachzubilden hiesse, Begriffe zu uebernehmen, die zu ihr nicht
gehoeren. Wenn sie gebraucht werden, kommen sie mit einer Begruendung dazu.
"""
from __future__ import annotations

# Die Werte der alten Kette, als Vorgabe. Ueberschreibbar unter
# `budget_allocator.*` - DENSELBEN Schluesseln, damit es nicht zwei Wahrheiten
# gibt (die Kopierfalle, die dieses Projekt schon dreimal erwischt hat).
VORGABE_STUNDEN: dict[str, float] = {
    "spot": 15.0,          # budget_allocator.spot_cooldown_stunden
    "hebel": 3.5,          # budget_allocator.cooldown_stunden
    "absicherung": 15.0,   # kein eigener Wert in der alten Kette - wie Spot,
                           # weil eine Absicherung eher laenger traegt als ein
                           # Hebel-Trade, nicht kuerzer
}

_SCHLUESSEL = {"spot": "spot_cooldown_stunden", "hebel": "cooldown_stunden"}


def stunden(instrument: str, config: dict | None = None) -> float:
    """Wie lange dasselbe Asset nach einem Signal gesperrt ist."""
    i = str(instrument or "").strip().lower()
    ba = (config or {}).get("budget_allocator") or {}
    schluessel = _SCHLUESSEL.get(i)
    wert = ba.get(schluessel) if schluessel else None
    return float(wert if wert is not None else VORGABE_STUNDEN.get(i, 15.0))


def gesperrt_bis(conn, symbol: str, instrument: str, *,
                 config: dict | None = None,
                 jetzt: str | None = None) -> str | None:
    """Bis wann ist `symbol` gesperrt? `None` heisst: frei.

    ZAEHLT NUR SIGNALE DER EIGENEN KETTE. Die Altsignale stammen aus einer
    anderen Logik mit anderem Vokabular; sie hier mitzuzaehlen hiesse, die neue
    Kette fuer Entscheidungen zu sperren, die sie nie getroffen hat.

    NUR EINSTIEGE SPERREN. Ein NICHTS_TUN erzeugt keine Position und damit auch
    keine Wiederholungsgefahr - es zu sperren wuerde die Kette daran hindern,
    ihre Meinung zu aendern.

    Fail-soft: fehlt die Spalte (aeltere Datei), gibt es keine Sperre. Ein
    Cooldown, der wegen eines Schemafehlers ALLES sperrt, waere schlimmer als
    keiner."""
    from datetime import datetime, timedelta, timezone

    try:
        spalten = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
        if "quelle_kette" not in spalten:
            return None
        zeile = conn.execute(
            "SELECT MAX(created_at) FROM signals WHERE symbol = ? "
            "AND quelle_kette = 'rollen' AND action NOT IN ('HALTEN', 'VERKAUFEN')",
            (symbol,)).fetchone()
    except Exception:                                        # noqa: BLE001
        return None
    if not zeile or not zeile[0]:
        return None
    try:
        zuletzt = datetime.fromisoformat(str(zeile[0]))
        if zuletzt.tzinfo is None:
            zuletzt = zuletzt.replace(tzinfo=timezone.utc)
        frei_ab = zuletzt + timedelta(hours=stunden(instrument, config))
        nun = (datetime.fromisoformat(jetzt) if jetzt
               else datetime.now(timezone.utc))
        if nun.tzinfo is None:
            nun = nun.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return frei_ab.isoformat() if frei_ab > nun else None
