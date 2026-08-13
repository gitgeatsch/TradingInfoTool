# -*- coding: utf-8 -*-
"""Der Betriebsaufruf der Rollen-Kette - der Schnitt (14.08.2026).

NUTZERENTSCHEIDUNG 13.08.: *"ich finde das System ist zu komplex als mit
mehreren Varianten zu fahren - das ist der glatte Schnitt - altes bzw. falsches
raus oder stillegen."*

DER SCHNITT IST JE ASSETKLASSE, NICHT JE ZEITPUNKT. Fuer ein Asset gibt es
immer genau EINE Kette; das heisst nicht, dass alle Klassen am selben Tag
wechseln muessen. `AKTIV_FUER` sagt, welche Klassen die neue Kette bedient -
und der alte Weg ueberspringt genau diese.

    Krypto Spot + Hebel   fertig, kann sofort
    Aktien, Rohstoffe,    Kapitel 17: Kursquelle je Klasse fehlt noch
    Themen-ETF
    Hedge                 Paket 14 zuerst bauen

WARUM EIN EIGENES MODUL UND KEINE OPERATION AM OFFENEN HERZEN. Die alte Kette
haengt an `hebel_screening_job()` - einer Funktion von ueber zweihundert Zeilen
mit Positions-Sync, Auto-Add und Allocator. Die neue dort hineinzuoperieren
hiesse, beide Wege in einer Funktion zu haben, und genau das ist der Zustand,
den der Nutzer abgelehnt hat.

DER SCHALTER STEHT IN DER KONFIGURATION, nicht im Code. Wer umstellt, aendert
eine Zeile in `config.yaml` und startet neu - er braucht kein Deployment und
keine Codeaenderung, und er kann zurueck. Das ist der Unterschied zwischen
einem Schnitt und einem Sprung.

WAS DIESES MODUL NICHT TUT: es entscheidet nichts. Die Kette liegt in
`agent/rollen_lauf.py`; hier steht nur, WOMIT sie gefuettert wird und WOHIN das
Ergebnis geht.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Welche Assetklassen die NEUE Kette bedient. Leer heisst: keine - dann laeuft
# alles wie bisher. Ueberschreibbar unter `rollen_kette.aktiv_fuer`.
#
# BEWUSST LEER ALS VORGABE. Ein Modul, das beim blossen Einspielen die
# Produktion umstellt, nimmt dem Nutzer die Entscheidung ab, die er treffen
# wollte.
VORGABE_AKTIV_FUER: tuple[str, ...] = ()


def aktiv_fuer(config: dict | None = None) -> tuple[str, ...]:
    """Die Assetklassen, die die neue Kette bedient."""
    wert = ((config or {}).get("rollen_kette") or {}).get("aktiv_fuer")
    if wert is None:
        return VORGABE_AKTIV_FUER
    return tuple(str(k).strip().lower() for k in wert if str(k).strip())


def bedient_neue_kette(assetklasse: str, config: dict | None = None) -> bool:
    """Laeuft diese Klasse ueber die neue Kette?

    DIE EINE FRAGE, die der alte Weg stellen muss, bevor er etwas tut. Wer sie
    nicht stellt, erzeugt fuer dasselbe Asset zwei Empfehlungen - und der
    Nutzer muesste entscheiden, welcher er glaubt. Das ist schlechter als jede
    der beiden allein."""
    return str(assetklasse or "").strip().lower() in aktiv_fuer(config)


def fuehre_krypto_lauf(
    *, conn_factory, config, client, zai_client=None, versand=None,
    instrument: str = "spot", strategie: str = "einstieg",
    betriebsart: str = "probe", db: str = "data/tradinginfotool.db",
) -> dict | None:
    """Ein Durchgang der Rollen-Kette ueber die Krypto-Watchlist.

    GIBT `None` ZURUECK, WENN DIE KLASSE NICHT UMGESTELLT IST - der Aufrufer
    laesst dann den alten Weg laufen. Kein Fehler, kein Log-Rauschen: das ist
    der Normalzustand, solange der Schalter nicht gesetzt ist.

    DIE VERBINDUNG WIRD HIER GEOEFFNET UND GESCHLOSSEN, nicht in der Kette.
    `rollen_lauf` bekommt sie uebergeben und oeffnet grundsaetzlich keine -
    darum muss es an DIESER Stelle geschehen, wo auch klar ist, welche
    Datenbank gemeint ist.

    `betriebsart` steht bewusst auf `probe`: die Mail wird gebaut, aber nicht
    verschickt. Wer sie verschicken will, sagt es ausdruecklich."""
    from agent import rollen_lauf as RL

    if not bedient_neue_kette("krypto", config):
        return None

    from backtest_llm1_historisch import lade_reihen_aus_db

    reihen = lade_reihen_aus_db(db)
    # NUR ECHTE SYMBOLE. Die Reihen enthalten auch Sammelposten
    # (`_ROHSTOFF_FUTURES_*`), die kein handelbares Asset sind.
    symbole = [s for s in sorted(reihen) if not s.startswith("_")]
    if not symbole:
        logger.warning("Rollen-Kette: keine Symbole - Lauf entfaellt")
        return None

    conn = conn_factory()
    try:
        ergebnis = RL.fuehre_lauf(
            conn=conn, reihen=reihen, symbole=symbole, betriebsart=betriebsart,
            instrument=instrument, strategie=strategie, client=client,
            zai_client=zai_client, versand=versand, config=config, db=db,
            assetklasse="krypto")
    finally:
        conn.close()

    d = ergebnis.get("durchlauf")
    anker = ergebnis.get("ankertag") or {}
    logger.info(
        "Rollen-Kette %s/%s (%s): Ankertag %s (%s von %s gedeckt), "
        "%s Signale, %s Mails, %s Fehler",
        instrument, strategie, betriebsart, anker.get("tag"),
        anker.get("gedeckt"), anker.get("gesamt"), len(ergebnis["signale"]),
        len(ergebnis["mails"]), len(ergebnis["fehler"]))
    if d is not None:
        # DIE DURCHLAESSIGKEIT INS LOG, nicht nur in die Tabelle. Wer morgens
        # nachsieht, warum nichts kam, soll es an einer Zeile erkennen.
        logger.info("Rollen-Kette Durchlaessigkeit: %s",
                    {st: (d.bestanden_je_stufe[st], d.verloren_je_stufe[st])
                     for st, _ in __import__(
                         "agent.rollen_gate", fromlist=["STUFEN"]).STUFEN})
    for fehler in ergebnis["fehler"][:5]:
        logger.warning("Rollen-Kette: %s", fehler)
    return ergebnis
