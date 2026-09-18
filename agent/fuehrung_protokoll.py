# -*- coding: utf-8 -*-
"""Die FUEHRUNG bekommt eine Ablage (18.09.2026, Schritt 59 Phase 1, Paket 1.4).

⚠️⚠️ DER ANLASS, an einem Tag gezaehlt: Am 18.09. um 05:23 ging eine Mail mit
**116 Stop-Nachzieh-Empfehlungen** hinaus. In den Daten steht davon NICHTS.

Die Empfehlung ist vollstaendig ausgerechnet, bevor sie in die Mail geht -
Einstieg, bisheriger Stop, empfohlener Stop, gesicherte R, MFE, Begruendung -
und wird danach verworfen. Damit ist unmessbar, was die Fuehrung leistet: ob
ein nachgezogener Stop Gewinn sichert oder zu frueh ausstoppt, ob 116
Empfehlungen an einem Morgen zu viel sind, ob ihnen ueberhaupt gefolgt wird.

⚠️ ANDERS ALS BEIM POTENTIAL IST HIER NICHTS REKONSTRUIERBAR: die Empfehlung
haengt am Kursverlauf des Tages (2.458-archaeologie).

⚠️ AUCH DIE GEPRUEFTEN OHNE EMPFEHLUNG (Nutzerentscheidung B2). Ohne sie
fehlt der Vergleichsarm - man saehe nur die Faelle, in denen nachgezogen
wurde, und koennte nie sagen, ob Nachziehen besser war als Nichtstun. Das ist
genau der Fehler, den Befund 2.401 auf der Ausstiegsseite beschreibt.

⚠️ EIGENE TABELLE (B1), nicht `zellen_lauf`: die Fuehrung kommt NICHT aus dem
Kettenlauf, sondern aus einem eigenen taeglichen Job.

SIE ENTSCHEIDET NICHTS. Kein Filter, keine Mail, keine Sperre haengt daran.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

TABELLE = "fuehrung_lauf"


def migriere(conn) -> list[str]:
    """Additiv und idempotent, wie jede Migration hier."""
    getan = []
    vorhanden = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if TABELLE not in vorhanden:
        conn.execute(f"""CREATE TABLE {TABELLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            erfasst_am TEXT NOT NULL,
            art TEXT NOT NULL,
            symbol TEXT NOT NULL,
            signal_id INTEGER,
            tier TEXT,
            ist_hebel INTEGER,
            richtung TEXT,
            ur_aktion TEXT,
            seit TEXT,
            entry REAL,
            stop_bisher REAL,
            stop_empfohlen REAL,
            sichert_r REAL,
            mfe_r REAL,
            kurs_usd REAL,
            eur_je_usd REAL,
            ist_bestand INTEGER,
            begruendung TEXT)""")
        conn.execute(f"CREATE INDEX idx_fuehrung_zeit ON {TABELLE}(erfasst_am)")
        conn.execute(f"CREATE INDEX idx_fuehrung_signal ON {TABELLE}(signal_id)")
        getan.append(f"Tabelle {TABELLE} angelegt")
    conn.commit()
    return getan


def _zeile(e: dict, art: str, zeitpunkt: str) -> tuple:
    return (zeitpunkt, art, str(e.get("symbol") or ""), e.get("signal_id"),
            e.get("tier"), 1 if e.get("ist_hebel") else 0, e.get("richtung"),
            e.get("ur_aktion"), e.get("seit"), e.get("entry"),
            e.get("stop_bisher") if art == "empfehlung" else e.get("stop"),
            e.get("stop_empfohlen"), e.get("sichert_r"), e.get("mfe_r"),
            e.get("kurs_usd"), e.get("eur_je_usd"),
            1 if e.get("ist_bestand") else 0,
            (e.get("begruendung") or "")[:400] or None)


def schreibe(conn, ergebnis: dict, zeitpunkt: str) -> int:
    """Eine Zeile je GEPRUEFTER Position, Empfehlungen als solche gekennzeichnet.

    ⚠️ Der Aufrufer faengt breit: diese Ablage ist eine Messung, kein Signal -
    sie darf den Job und vor allem die Mail nicht verhindern."""
    migriere(conn)
    empfohlen = {(e.get("symbol"), e.get("signal_id"))
                 for e in (ergebnis.get("empfehlungen") or [])}
    zeilen = [_zeile(e, "empfehlung", zeitpunkt)
              for e in (ergebnis.get("empfehlungen") or [])]
    # Die geprueften OHNE Empfehlung - der Vergleichsarm (B2).
    zeilen += [_zeile(e, "geprueft", zeitpunkt)
               for e in (ergebnis.get("alle") or [])
               if (e.get("symbol"), e.get("signal_id")) not in empfohlen]
    if not zeilen:
        return 0
    conn.executemany(
        f"INSERT INTO {TABELLE} (erfasst_am, art, symbol, signal_id, tier, "
        f"ist_hebel, richtung, ur_aktion, seit, entry, stop_bisher, "
        f"stop_empfohlen, sichert_r, mfe_r, kurs_usd, eur_je_usd, "
        f"ist_bestand, begruendung) "
        f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", zeilen)
    conn.commit()
    return len(zeilen)
