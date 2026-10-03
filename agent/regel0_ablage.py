"""Ablage der REGEL0-Signale (Schritt 7, S7-2b/S7-4) - die EINE Stelle, die ``data/regel0_signale.db`` oeffnet.

Leicht (nur sqlite3), damit sie im Prozess der App laufen kann: der Stundenlauf (eigener Prozess) schreibt die Signale,
der Stundenjob der App liest sie und vermerkt die versandten Mails.

⚠️ SCHREIBT NUR in ``regel0_signale.db`` - der Dateiname steht hier fest und ist von aussen nicht waehlbar (nie die Produktion).
"""
from __future__ import annotations

import os
import sqlite3

ABLAGE_NAME = "regel0_signale.db"

_SIGNAL_SPALTEN = (
    ("symbol", "TEXT"), ("signalstunde", "TEXT"), ("einstieg", "TEXT"), ("ausstieg", "TEXT"), ("vh", "REAL"),
    ("stufe_vorlaeufig", "INTEGER"), ("stufe", "INTEGER"), ("p2", "REAL"), ("p3", "REAL"), ("p5", "REAL"),
    ("hebel_schalter", "INTEGER"), ("bitpanda", "TEXT"), ("zusatz", "INTEGER"), ("btc", "INTEGER"), ("version", "TEXT"),
    ("erfasst_am", "TEXT"), ("endgueltig_am", "TEXT"),
    # S7-4 (03.10.2026)
    ("kurs", "REAL"), ("kurs_markt", "TEXT"),
    ("mail_signal_am", "TEXT"), ("mail_signal_stufe", "INTEGER"), ("mail_korrektur_am", "TEXT"), ("mail_erinnerung_am", "TEXT"),
    # S7-5b (03.10.2026): Preisabgleich Bitpanda gegen Binance vor der Signalmail
    ("paar", "TEXT"), ("faktor", "REAL"), ("abgleich", "TEXT"), ("mail_gesperrt_am", "TEXT"),
)


def oeffne(ordner: str) -> sqlite3.Connection:
    """Verbindung zur Ablage in ``ordner`` (legt sie an, ergaenzt fehlende Spalten)."""
    p = os.path.join(ordner, ABLAGE_NAME)
    c = sqlite3.connect(p, timeout=30)
    c.execute("CREATE TABLE IF NOT EXISTS lauf (jetzt TEXT PRIMARY KEY, gerechnet_am TEXT, sekunden REAL, pakete TEXT, aktiv INTEGER, "
              "frisch INTEGER, veraltet INTEGER, veraltet_liste TEXT, nicht_im_handel INTEGER, neu INTEGER, endgueltig INTEGER, meldung TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS signal (%s, PRIMARY KEY (symbol, signalstunde))"
              % ", ".join("%s %s" % sp for sp in _SIGNAL_SPALTEN[:17]))
    # E-52 (03.10.2026): die Urteile der LLM-Rollen je Signal und Rolle - Fassung, Pruefsummen, Eingabe, Antwort, Laufzeit, Fehler
    c.execute("CREATE TABLE IF NOT EXISTS pruefung (symbol TEXT, signalstunde TEXT, rolle TEXT, fassung TEXT, modell TEXT, "
              "prompt_pruefsumme TEXT, eingabe_pruefsumme TEXT, eingabe TEXT, antwort TEXT, urteil TEXT, ergebnis TEXT, sekunden REAL, "
              "fehler TEXT, ungedeckt TEXT, am TEXT, gefragt INTEGER, tag_pazifik TEXT, PRIMARY KEY (symbol, signalstunde, rolle, fassung))")
    da = {r[1] for r in c.execute("PRAGMA table_info(signal)")}
    for name, typ in _SIGNAL_SPALTEN:
        if name not in da:
            c.execute("ALTER TABLE signal ADD COLUMN %s %s" % (name, typ))
    c.commit()
    return c
