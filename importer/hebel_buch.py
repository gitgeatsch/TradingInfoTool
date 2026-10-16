# -*- coding: utf-8 -*-
"""P11b (16.10.2026) - DIE HEBELPOSITIONEN ALS BUCH JE SYMBOL aus der neuen Bitpanda-Schnittstelle (/v1/operations).

Bitpanda-Umstellung Stufe 3 (Basisinfos/Bitpanda_Umstellung_Inventur.md): *"auf /v1/operations (margin_trading_*), Tabelle
hebel_positions in Bedeutung unveraendert"*. Anlass (Nutzer 16.10.): falsche *LIQUIDATION NAHE ETH*, nachdem ETH am 15.10. ausgestoppt
und geschlossen war - der alte Importer (alte Schnittstelle, Befund 2.679) verkleinerte statt zu schliessen.

WIE BITPANDA BUCHT (Voranalyse Schritt7 §23.60, 1.242 Margin-Vorgaenge ab 22.09.2025, alle geprueft):

    open_long          Kredit-Wallet (EURCV) OUTGOING k · Margin-Wallet INCOMING q zum Kurs r
    close_long         Margin-Wallet: Gebuehr, Verkauf (Erloes = Tilgung), REST ALS COIN INS SPOT-WALLET (das Eigenkapital) ·
    liquidation_long   Kredit-Wallet INCOMING (Tilgung). EIN Topf je Symbol, Tilgung ANTEILIG zur Menge (282 von 282)

DAS BUCH: Menge = Saldo des Margin-Wallets, Kredit = Summe der Kreditbuchungen, Kosten = Menge x Kurs (bei Abgaengen anteilig).
Ein LEBENSZYKLUS reicht von Saldo 0 bis wieder 0 = EINE Zeile in ``hebel_positions``; Liquidation = der ausdrueckliche Vorgangstyp
(die alte Erkennung ueber eine Gebuehren-Anomalie fand 4 von 7).

ABLAUF ``sync`` (alle 15 min im ``hebel_screening_job`` ueber ``sync_hebel_positions``):
    1. neue Vorgaenge holen (beim ERSTEN Lauf die ganze Historie), Margin-Vorgaenge in ``hebel_buch_vorgang`` (idempotent)
    2. EINMALIG, nur nach vollstaendiger Historie: die alten Zeilen nach ``hebel_positions_alt_bis_16_10`` SICHERN, dann ersetzen
       (Regel *Ruecksprache vor dem Entfernen*: Nutzer-Ja 16.10.; geloescht wird nichts, was nicht gesichert ist)
    3. das ganze Buch neu durchrechnen (deterministisch, keine Zustandsfehler) und ``hebel_positions`` schreiben
    4. Stempel: ``hebel_buch_stand`` (juengste Buchung, ISO) und ``hebel_position_last_synced_unix`` (fuer P11c ``wallet_lage``)
Ist die Historie beim ersten Lauf unvollstaendig, wird NICHT umgestellt - dann laeuft der alte Weg weiter (kein Loch).
"""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone

from database.models import HebelPosition

logger = logging.getLogger(__name__)

TABELLE = "hebel_buch_vorgang"
ALT = "hebel_positions_alt_bis_16_10"
META_STAND = "hebel_buch_stand"
META_UMGESTELLT = "hebel_buch_umgestellt_am"
META_WASSER = "hebel_position_last_synced_unix"
UEBERLAPPUNG = timedelta(minutes=10)
TOL = 1e-9
SPALTEN = ("symbol", "richtung", "status", "eroeffnet_am", "geschlossen_am", "hebel_effektiv", "positionswert_eur", "kreditbetrag_eur",
           "eigenkapital_eur", "positionsmenge", "letzte_transaktion_unix_timestamp", "liquidationspreis_geschaetzt_eur",
           "liquidationspreis_berechnet_am", "quelle_tags_json")


def schema(conn) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS %s (operation_id TEXT PRIMARY KEY, zeit TEXT NOT NULL, typ TEXT NOT NULL, asset_id TEXT NOT NULL, "
                 "zugang REAL NOT NULL, abgang REAL NOT NULL, saldo_nach REAL NOT NULL, kredit_aenderung REAL NOT NULL, kurs REAL, "
                 "roh TEXT NOT NULL)" % TABELLE)


def _meta(conn, k):
    r = conn.execute("SELECT value FROM meta WHERE key=?", (k,)).fetchone()
    return r[0] if r else None


def _setze(conn, k, v) -> None:
    conn.execute("INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, str(v)))


def _iso(text: str) -> str:
    """'2026-10-09T04:38:53.123Z' -> '2026-10-09T04:38:53+00:00' (die Schreibweise der bisherigen Zeilen)."""
    d = datetime.fromisoformat(str(text).replace("Z", "+00:00")).astimezone(timezone.utc)
    return d.replace(microsecond=0).isoformat()


def aus_vorgang(o: dict) -> dict | None:
    """Ein Margin-Vorgang der neuen Schnittstelle -> eine Buchzeile, oder None (kein Margin-Vorgang / kein Margin-Wallet)."""
    typ = str(o.get("operation_type") or "")
    if not typ.startswith("margin_trading_"):
        return None
    tx = o.get("transactions") or []
    marg = [t for t in tx if t.get("wallet_owner") == "margin-trading"]
    if not marg or not marg[0].get("asset_id"):
        return None
    zu = sum(float(t["asset_amount"]["value"]) for t in marg if t.get("flow") == "INCOMING")
    ab = sum(float(t["asset_amount"]["value"]) for t in marg if t.get("flow") == "OUTGOING")
    salden = [float(t["asset_balance_after"]["value"]) for t in marg if t.get("asset_balance_after")]
    kr = [t for t in tx if t.get("wallet_owner") == "margin-trading-credit"]
    dk = sum(float(t["asset_amount"]["value"]) * (1 if t.get("flow") == "OUTGOING" else -1) for t in kr)
    kurs = next((float(t["trade"]["rate"]) for t in marg if t.get("trade") and t.get("flow") == "INCOMING"), None)
    zeit = min(t["credited_at"] for t in tx if t.get("credited_at"))
    return {"operation_id": o["operation_id"], "zeit": zeit, "typ": typ, "asset_id": marg[0]["asset_id"], "zugang": zu, "abgang": ab,
            "saldo_nach": min(salden) if typ != "margin_trading_open_long" and salden else (max(salden) if salden else 0.0),
            "kredit_aenderung": dk, "kurs": kurs, "roh": json.dumps(o, ensure_ascii=False, separators=(",", ":"))}


def speichere(conn, vorgaenge: list) -> int:
    schema(conn)
    n = 0
    for o in vorgaenge:
        z = aus_vorgang(o)
        if z is None:
            continue
        cur = conn.execute("INSERT OR IGNORE INTO %s (%s) VALUES (%s)" % (TABELLE, ",".join(z), ",".join("?" * len(z))), list(z.values()))
        n += cur.rowcount
    return n


def lebenszyklen(conn) -> list[dict]:
    """Das ganze Buch durchrechnen - je Symbol Lebenszyklen von Saldo 0 bis wieder 0 (der letzte ggf. offen)."""
    schema(conn)
    sym = {}
    for aid, s in conn.execute("SELECT asset_id, symbol FROM bitpanda_katalog"):
        sym.setdefault(aid, s)
    stand: dict = {}
    aus = []
    for oid, zeit, typ, aid, zu, ab, kd, kurs in conn.execute(
            "SELECT operation_id, zeit, typ, asset_id, zugang, abgang, kredit_aenderung, kurs FROM %s ORDER BY zeit, operation_id" % TABELLE):
        s = sym.get(aid)
        if not s:
            logger.warning("Hebel-Buch: Asset %s nicht im Bitpanda-Katalog - Vorgang %s uebergangen", aid, oid)
            continue
        if "short" in typ:
            logger.warning("Hebel-Buch: SHORT-Vorgang %s (%s) - Bitpanda bietet kein Short; nicht im Buch", oid, typ)
            continue
        b = stand.get(s)
        if b is None or b["menge"] <= TOL:
            if typ != "margin_trading_open_long":
                logger.warning("Hebel-Buch: %s %s ohne offene Position - uebergangen", s, typ)
                continue
            b = stand[s] = {"symbol": s, "menge": 0.0, "kredit": 0.0, "kosten": 0.0, "auf": zeit, "zu": None, "liquidiert": False,
                            "vorgaenge": 0, "eroeffnungen": 0, "abgaenge": 0, "letzte": zeit, "spitze": None}
        vor = b["menge"]
        nach = max(vor + zu - ab, 0.0)
        if typ == "margin_trading_open_long":
            b["kosten"] += zu * (kurs or 0.0)
            b["eroeffnungen"] += 1
        else:
            b["spitze"] = {"menge": vor, "kredit": b["kredit"], "kosten": b["kosten"]}       # Stand VOR dem Abgang (fuer die Abschlusszeile)
            b["kosten"] *= (nach / vor) if vor > TOL else 0.0
            b["abgaenge"] += 1
        b["kredit"] += kd
        b["menge"] = nach
        b["vorgaenge"] += 1
        b["letzte"] = zeit
        if typ != "margin_trading_open_long" and nach <= TOL:
            b.update(zu=zeit, liquidiert=(typ == "margin_trading_liquidation_long"))
            aus.append(b)
            stand[s] = None
    aus += [b for b in stand.values() if b and b["menge"] > TOL]
    return aus


def als_position(z: dict) -> HebelPosition:
    offen = z["zu"] is None
    w = z if offen else (z.get("spitze") or z)
    kosten, kredit, menge = w["kosten"], w["kredit"], w["menge"]
    ek = kosten - kredit
    return HebelPosition(
        symbol=z["symbol"], richtung="LONG",
        status="offen" if offen else ("liquidiert" if z["liquidiert"] else "geschlossen"),
        eroeffnet_am=_iso(z["auf"]), geschlossen_am=None if offen else _iso(z["zu"]),
        hebel_effektiv=(kosten / ek) if ek > 0 else None, positionswert_eur=kosten, kreditbetrag_eur=kredit, eigenkapital_eur=ek,
        positionsmenge=menge, letzte_transaktion_unix_timestamp=int(datetime.fromisoformat(z["letzte"].replace("Z", "+00:00")).timestamp()),
        quelle_tags_json=json.dumps({"quelle": "bitpanda_operations", "vorgaenge": z["vorgaenge"], "eroeffnungen": z["eroeffnungen"],
                                     "abgaenge": z["abgaenge"], "liquidation": z["liquidiert"],
                                     "werte": "aktuell" if offen else "vor dem letzten Abgang"}))


def _schreibe(conn, positionen: list) -> None:
    upd = ", ".join("%s = excluded.%s" % (c, c) for c in SPALTEN if c not in ("symbol", "eroeffnet_am", "liquidationspreis_geschaetzt_eur",
                                                                                "liquidationspreis_berechnet_am"))
    conn.executemany("INSERT INTO hebel_positions (%s) VALUES (%s) ON CONFLICT(symbol, eroeffnet_am) DO UPDATE SET %s"
                     % (", ".join(SPALTEN), ", ".join("?" * len(SPALTEN)), upd),
                     [[getattr(p, c) for c in SPALTEN] for p in positionen])


def umgestellt(conn) -> bool:
    return bool(_meta(conn, META_UMGESTELLT))


def _umstellen(conn) -> int:
    """EINMALIG: die alten Zeilen sichern, dann leeren - in derselben Transaktion wie das erste Schreiben des Buchs."""
    n = conn.execute("SELECT COUNT(*) FROM hebel_positions").fetchone()[0]
    conn.execute("CREATE TABLE IF NOT EXISTS %s AS SELECT * FROM hebel_positions WHERE 0" % ALT)
    conn.execute("INSERT INTO %s SELECT * FROM hebel_positions" % ALT)
    gesichert = conn.execute("SELECT COUNT(*) FROM %s" % ALT).fetchone()[0]
    if gesichert < n:
        raise RuntimeError("Sicherung unvollstaendig (%d von %d) - nicht umgestellt" % (gesichert, n))
    conn.execute("DELETE FROM hebel_positions")
    return n


def sync(conn, api_key: str, hole=None) -> dict:
    """Ein Lauf. ``hole`` (Pruefstand): Ersatz fuer api.bitpanda_public.hole_buchungen_mit_stand(api_key, seit=...) -> (vorgaenge, vollst.).
    -> {'geladen', 'neu_im_buch', 'umgestellt', 'gesichert', 'offen', 'geschlossen_neu', 'positionen', 'vollstaendig'}"""
    if hole is None:
        from api.bitpanda_public import hole_buchungen_mit_stand as hole
    schema(conn)
    stand = _meta(conn, META_STAND)
    seit = None
    if stand:
        seit = (datetime.fromisoformat(stand.replace("Z", "+00:00")) - UEBERLAPPUNG).isoformat().replace("+00:00", "Z")
    vorgaenge, vollstaendig = hole(api_key, seit=seit)                   # Netz ZUERST - vorher kein Schreiben
    vorher_offen = {r[0] for r in conn.execute("SELECT symbol FROM hebel_positions WHERE status='offen'")}
    aus = {"geladen": len(vorgaenge), "vollstaendig": vollstaendig, "umgestellt": False, "gesichert": 0}
    try:
        aus["neu_im_buch"] = speichere(conn, vorgaenge)
        if not umgestellt(conn):
            if stand is None and not vollstaendig:
                conn.rollback()
                logger.warning("Hebel-Buch: erste Historie unvollstaendig (%d Vorgaenge) - NICHT umgestellt, der alte Weg bleibt",
                               len(vorgaenge))
                aus.update(positionen=[], offen=sorted(vorher_offen), geschlossen_neu=0)
                return aus
            aus["gesichert"] = _umstellen(conn)
            _setze(conn, META_UMGESTELLT, datetime.now(timezone.utc).isoformat(timespec="seconds"))
            aus["umgestellt"] = True
        pos = [als_position(z) for z in lebenszyklen(conn)]
        _schreibe(conn, pos)
        juengst = conn.execute("SELECT MAX(zeit) FROM %s" % TABELLE).fetchone()[0]
        if vollstaendig:
            zeiten = [t.get("credited_at") for o in vorgaenge for t in o.get("transactions") or [] if t.get("credited_at")]
            if zeiten:
                neu_stand = max(zeiten + ([stand] if stand else []))
                _setze(conn, META_STAND, neu_stand)
        if juengst:
            _setze(conn, META_WASSER, int(datetime.fromisoformat(juengst.replace("Z", "+00:00")).timestamp()))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    jetzt_offen = {p.symbol for p in pos if p.status == "offen"}
    aus.update(positionen=sorted(jetzt_offen | (vorher_offen - jetzt_offen)), offen=sorted(jetzt_offen),
               geschlossen_neu=len(vorher_offen - jetzt_offen))
    return aus
