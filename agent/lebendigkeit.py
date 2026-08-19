# -*- coding: utf-8 -*-
"""Lebt das Projekt noch - und in welche RICHTUNG? (Umbauplan 93 C, 19.08.2026)

⚠️ EINE RICHTUNG, KEIN ZUSTAND - UND KEIN GATE.

Der erste Entwurf lautete "kein Spot, egal wie der Chart aussieht". Das waere
ein statisches Qualitaetsgate gewesen - die Bauform, die den Deadloop erzeugt
hat - und es haette ausgerechnet den wertvollsten Fall gesperrt: den Coin,
der stirbt und dreht. Ein langfristiger Abwaertstrend, der in einen
Aufwaertstrend uebergeht, ist die groesste Chance.

Deshalb misst dieses Modul nicht "lebt / lebt nicht", sondern "wird
schwaecher / stabilisiert sich / wird staerker". DER UEBERGANG IST DAS
SIGNAL, NICHT DER PEGEL. Und es urteilt nicht: die Zahlen gehen als Merkmal
in die Mail, sie unterdruecken nichts.

⚠️ OHNE HISTORIE KEIN UEBERGANG - DESHALB BEGINNT DAS SAMMELN HEUTE.

CoinGecko liefert `developer_data` nur als AKTUELLEN Stand, keine Reihe.
DefiLlama liefert TVL ebenfalls als Momentaufnahme. Die Reihe muss also
selbst aufgebaut werden, und sie ist fruehestens in Wochen auswertbar. Wer
heute nicht anfaengt, hat in drei Monaten dieselbe Luecke.

BIS DAHIN STEHT DER WERT MIT WARNHINWEIS IN DER MAIL (Nutzerwunsch
19.08.2026). Er verschwindet von selbst, sobald die Reihe lang genug ist -
niemand muss daran denken.

ZWEI QUELLEN, ZWEI TAKTE - UND DER GRUND IST DAS KONTINGENT:

    DefiLlama     TVL       ZWEI Sammelabrufe fuer ALLE Symbole, kein
                            Kontingent. Deckt 25 von 44 Kryptowerten.
    CoinGecko     Commits   EIN Abruf JE SYMBOL. Das Monatskontingent lag am
                            19.08. bei 3.521 von 10.000; taeglich 41 Abrufe
                            waeren +1.230/Monat und braechten uns nahe an
                            die 80-%-Warnschwelle.

DESHALB CoinGecko WOECHENTLICH. Das ist nicht nur billiger, sondern richtig:
`commit_count_4_weeks` misst ein VIER-WOCHEN-Fenster. Es taeglich abzufragen
liefert 28-fach ueberlappende Messwerte - viel Kontingent fuer fast keine
zusaetzliche Information.

⚠️ DREI ZUSTAENDE, DIE NIE VERSCHMELZEN (Lehre vom 19.08., als 429er als
"kein Repository" gezaehlt wurden und "0 von 43" ergaben, waehrend BTC zwei
Minuten zuvor 73.168 Sterne gemeldet hatte):

    wert          eine Zahl kam an
    keine_quelle  die Antwort kam an und sagt: dazu gibt es hier nichts
    fehler        wir haben es NICHT erfahren (Netz, 429, unerwartete Form)

Der dritte ist der wichtige. Wer ihn mit dem zweiten verrechnet, erklaert
lebendige Ketten fuer tot - und "unbekannt" darf nie wie "tot" aussehen.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

DEFILLAMA_PROTOKOLLE = "https://api.llama.fi/protocols"
DEFILLAMA_CHAINS = "https://api.llama.fi/v2/chains"
COINGECKO_COIN = "https://api.coingecko.com/api/v3/coins/{}"

# Wie viele Beobachtungen braucht eine Richtungsaussage? Nicht geraten,
# sondern aus dem Messfenster der Kennzahl abgeleitet:
#
#   tvl         taeglich erhoben; ein Monat ist die kuerzeste Spanne, in der
#               ein Trend nicht nur die Kursbewegung derselben Woche ist.
#   entwickler  woechentlich erhoben, misst selbst 4 Wochen. Zwei
#               unabhaengige Fenster sind das Minimum, drei sind ehrlich -
#               bei Wochentakt also 12 Beobachtungen.
MINDESTREIHE = {"tvl": 30, "entwickler": 12}

# Ab welcher Aenderung heisst es "staerker" statt "unveraendert"? Unter zehn
# Prozent ist bei TVL das taegliche Rauschen des Kurses selbst, nicht die
# Nutzung - und bei Commits sind es einzelne Arbeitstage.
SCHWELLE_RELATIV = 0.10

ZUSTAENDE = ("wert", "keine_quelle", "fehler")


class QuelleUnbekannt(RuntimeError):
    """Wir haben es NICHT erfahren - das ist kein Nein."""


def _tabelle(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS lebendigkeit_beobachtung (
                   id INTEGER PRIMARY KEY,
                   erfasst_am TEXT NOT NULL,
                   symbol TEXT NOT NULL,
                   quelle TEXT NOT NULL,
                   zustand TEXT NOT NULL,
                   wert REAL,
                   kennzahlen_json TEXT,
                   grund TEXT)""")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_lebendigkeit_symbol "
            "ON lebendigkeit_beobachtung (symbol, quelle, erfasst_am)")
        return True
    except sqlite3.Error as exc:
        logger.info("Lebendigkeits-Tabelle nicht anlegbar: %s", exc)
        return False


def schreibe(conn, *, symbol: str, quelle: str, zustand: str,
             wert: float | None = None, kennzahlen: dict | None = None,
             grund: str = "", jetzt: str | None = None) -> bool:
    """Eine Beobachtung. SCHREIBT AUCH FEHLER - sonst sieht eine Luecke
    spaeter aus wie ein Wert von null."""
    if zustand not in ZUSTAENDE:
        raise ValueError(f"Zustand {zustand!r} unbekannt - {ZUSTAENDE}")
    if conn is None or not _tabelle(conn):
        return False
    try:
        conn.execute(
            "INSERT INTO lebendigkeit_beobachtung (erfasst_am, symbol, "
            "quelle, zustand, wert, kennzahlen_json, grund) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (jetzt or datetime.now(timezone.utc).isoformat(),
             str(symbol).upper(), str(quelle), zustand,
             float(wert) if wert is not None else None,
             json.dumps(kennzahlen or {}, ensure_ascii=False),
             str(grund or "")))
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.info("Lebendigkeit %s/%s nicht schreibbar: %s",
                    symbol, quelle, exc)
        return False


def reihe(conn, symbol: str, quelle: str, tage: int = 400) -> list[tuple]:
    """(erfasst_am, wert) der Beobachtungen MIT Wert, aelteste zuerst.

    Fehler und fehlende Quellen bleiben draussen - sie sind keine Nullen."""
    if conn is None:
        return []
    try:
        grenze = (datetime.now(timezone.utc)
                  - timedelta(days=int(tage))).isoformat()
        return [(r[0], float(r[1])) for r in conn.execute(
            "SELECT erfasst_am, wert FROM lebendigkeit_beobachtung "
            "WHERE symbol = ? AND quelle = ? AND zustand = 'wert' "
            "AND wert IS NOT NULL AND erfasst_am >= ? ORDER BY erfasst_am",
            (str(symbol).upper(), str(quelle), grenze)).fetchall()]
    except sqlite3.Error:
        return []


def richtung(werte: list[tuple], quelle: str) -> dict:
    """Wird es staerker, schwaecher oder bleibt es? UND OB WIR DAS DUERFEN.

    `trag faehig` ist der ganze Punkt dieses Moduls: solange die Reihe zu
    kurz ist, gibt es KEINE Richtungsaussage - nur den aktuellen Wert und
    einen Hinweis, wie weit die Reihe ist."""
    noetig = MINDESTREIHE.get(quelle, 30)
    n = len(werte)
    aus = {"quelle": quelle, "beobachtungen": n, "noetig": noetig,
           "tragfaehig": n >= noetig, "jetzt": werte[-1][1] if werte else None,
           "richtung": None, "aenderung_relativ": None}
    if n < 2:
        return aus
    # Erste und letzte HAELFTE mitteln, nicht erster gegen letzter Punkt -
    # ein einzelner Ausreisser am Rand wuerde sonst die Richtung bestimmen.
    h = max(1, n // 2)
    frueh = sum(w for _, w in werte[:h]) / h
    spaet = sum(w for _, w in werte[-h:]) / h
    if frueh <= 0:
        return aus
    d = (spaet - frueh) / frueh
    aus["aenderung_relativ"] = d
    if aus["tragfaehig"]:
        aus["richtung"] = ("staerker" if d > SCHWELLE_RELATIV else
                           "schwaecher" if d < -SCHWELLE_RELATIV else
                           "unveraendert")
    return aus


def saetze(conn, symbol: str, assetklasse: str = "") -> list[str]:
    """Die Zeilen fuer die Mail - mit Warnhinweis, solange die Reihe kurz ist.

    ⚠️ KEIN URTEIL. Diese Zeilen sperren nichts und empfehlen nichts. Sie
    sagen, was an Nutzung und Entwicklung messbar ist und ob sich das bewegt.
    """
    from agent.schreibweise import de

    if str(assetklasse or "").strip().lower() != "krypto":
        return []
    teile = []
    for quelle, name, einheit in (
            ("tvl", "Im Protokoll hinterlegtes Kapital", " USD"),
            ("entwickler", "Commits in vier Wochen", "")):
        r = richtung(reihe(conn, symbol, quelle), quelle)
        if r["jetzt"] is None:
            continue
        wert = de(r["jetzt"], 0) + einheit
        if r["tragfaehig"] and r["richtung"]:
            teile.append(
                f"   {name}: {wert} - {r['richtung']} "
                f"({de(100 * r['aenderung_relativ'], 0)} % gegenueber dem "
                f"Beginn der Reihe, {de(r['beobachtungen'], 0)} Messungen).")
        else:
            teile.append(
                f"   {name}: {wert}. ⚠️ NOCH KEINE RICHTUNGSAUSSAGE - die "
                f"eigene Reihe hat erst {de(r['beobachtungen'], 0)} von "
                f"{de(r['noetig'], 0)} noetigen Messungen.")
    if not teile:
        return []
    return (["Lebendigkeit des Projekts (Merkmal, kein Urteil):"] + teile
            + ["   Ein Projekt kann verkuemmern und der Kurs trotzdem "
               "steigen - und umgekehrt. Diese Zeilen sperren nichts."])


# ---------------------------------------------------------------------------
# DIE SAMMLER. Sie urteilen nicht und rechnen nicht - sie holen und schreiben.
# ---------------------------------------------------------------------------

def sammle_tvl(conn, symbole, sitzung=None, jetzt: str | None = None) -> dict:
    """DefiLlama: ZWEI Abrufe fuer ALLE Symbole, kein Kontingent.

    ⚠️ Faellt der Abruf aus, wird fuer JEDES Symbol ein `fehler` geschrieben -
    nicht nichts. Eine Luecke ohne Eintrag sieht spaeter aus wie ein Tag, an
    dem es das Projekt nicht gab."""
    import requests

    s = sitzung or requests.Session()
    gesucht = {str(x).upper() for x in symbole}
    summe: dict[str, float] = {}
    try:
        for antwort, feld in ((s.get(DEFILLAMA_PROTOKOLLE, timeout=45),
                               "symbol"),
                              (s.get(DEFILLAMA_CHAINS, timeout=45),
                               "tokenSymbol")):
            antwort.raise_for_status()
            for e in antwort.json():
                sym = str(e.get(feld) or "").upper()
                tvl = e.get("tvl")
                if sym in gesucht and tvl:
                    # Ein Symbol kann mehrere Protokolle haben - sie gehoeren
                    # addiert, sonst zaehlt zufaellig das erstgefundene.
                    summe[sym] = summe.get(sym, 0.0) + float(tvl)
    except Exception as exc:                                 # noqa: BLE001
        for sym in sorted(gesucht):
            schreibe(conn, symbol=sym, quelle="tvl", zustand="fehler",
                     grund=type(exc).__name__, jetzt=jetzt)
        return {"fehler": len(gesucht), "wert": 0, "keine_quelle": 0}

    zaehl = {"wert": 0, "keine_quelle": 0, "fehler": 0}
    for sym in sorted(gesucht):
        if sym in summe:
            schreibe(conn, symbol=sym, quelle="tvl", zustand="wert",
                     wert=summe[sym], jetzt=jetzt)
            zaehl["wert"] += 1
        else:
            # DEFILLAMA HAT GEANTWORTET und kennt zu diesem Symbol nichts.
            # Das ist eine Auskunft, kein Ausfall - LINK etwa ist ein Orakel
            # und hat schlicht kein hinterlegtes Kapital.
            schreibe(conn, symbol=sym, quelle="tvl", zustand="keine_quelle",
                     grund="kein Protokoll und keine Chain mit TVL",
                     jetzt=jetzt)
            zaehl["keine_quelle"] += 1
    return zaehl


def sammle_entwickler(conn, paare, sitzung=None, abstand_s: float = 5.0,
                      jetzt: str | None = None) -> dict:
    """CoinGecko: EIN Abruf je Symbol - deshalb WOECHENTLICH, nicht taeglich.

    `paare` ist [(symbol, coingecko_id), ...]."""
    import time

    import requests

    s = sitzung or requests.Session()
    zaehl = {"wert": 0, "keine_quelle": 0, "fehler": 0}
    liste = [(a, b) for a, b in paare if b]
    for i, (sym, cid) in enumerate(liste):
        zustand, wert, kenn, grund = "fehler", None, {}, "unerreichbar"
        try:
            r = s.get(COINGECKO_COIN.format(cid), timeout=30, params={
                "localization": "false", "tickers": "false",
                "market_data": "false", "community_data": "false",
                "developer_data": "true", "sparkline": "false"})
            if r.status_code != 200:
                grund = f"HTTP {r.status_code}"
            else:
                d = r.json()
                if "developer_data" not in d:
                    # ⚠️ NICHT als "kein Repo" werten - eine Antwort ohne das
                    # Feld ist eine unerwartete Form, vielleicht ein
                    # Fehlerkoerper mit Status 200.
                    grund = "Feld developer_data fehlt"
                else:
                    dev = d.get("developer_data") or {}
                    kenn = {k: dev.get(k) for k in
                            ("stars", "forks", "subscribers",
                             "commit_count_4_weeks", "total_issues")}
                    hat = any(bool(kenn.get(k)) for k in
                              ("stars", "forks", "subscribers",
                               "total_issues"))
                    if hat:
                        zustand, wert = "wert", float(
                            kenn.get("commit_count_4_weeks") or 0)
                    else:
                        # ⚠️ "0 COMMITS" IST NICHT "TOT". Kein hinterlegtes
                        # Repository ist ein fehlender Link, kein
                        # eingestelltes Projekt.
                        zustand, grund = ("keine_quelle",
                                          "kein Repository hinterlegt")
        except Exception as exc:                             # noqa: BLE001
            grund = type(exc).__name__
        schreibe(conn, symbol=sym, quelle="entwickler", zustand=zustand,
                 wert=wert, kennzahlen=kenn, grund=grund, jetzt=jetzt)
        zaehl[zustand] += 1
        if i < len(liste) - 1:
            time.sleep(abstand_s)
    return zaehl


def job(conn, watchlist, *, mit_entwickler: bool, jetzt=None) -> dict:
    """Ein Sammellauf. URTEILT NICHT, SPERRT NICHT, MELDET NUR.

    `mit_entwickler` trennt den Wochen- vom Tagestakt: TVL kostet zwei
    Abrufe, die Entwicklerdaten einen JE SYMBOL (siehe Modul-Docstring)."""
    krypto = [x for x in (watchlist or [])
              if str(getattr(x, "assetklasse", "") or "").lower() == "krypto"
              and not getattr(x, "ist_cash_aequivalent", False)]
    aus = {"symbole": len(krypto), "tvl": {}, "entwickler": {}}
    if not krypto:
        return aus
    aus["tvl"] = sammle_tvl(conn, [x.symbol for x in krypto], jetzt=jetzt)
    if mit_entwickler:
        aus["entwickler"] = sammle_entwickler(
            conn, [(x.symbol, getattr(x, "coingecko_id", None))
                   for x in krypto], jetzt=jetzt)
    logger.info("Lebendigkeit gesammelt: %s", aus)
    return aus
