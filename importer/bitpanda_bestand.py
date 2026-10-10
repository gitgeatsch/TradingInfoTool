# -*- coding: utf-8 -*-
"""BESTANDSABGLEICH UEBER DIE NEUE BITPANDA-SCHNITTSTELLE (Schritt 61, Stufe 1.2).

⚠️⚠️⚠️ WARUM ES IHN GIBT. Der alte Abgleich (`importer/bitpanda_sync.py`) las
den freien Bestand aus den alten Wallets und rekonstruierte das Gestakte aus
Transfer-Markierungen. Das hat ab 16.07. die gestakten Mengen verdoppelt und
die Belohnungen verloren (Befunde 2.455-bestand-gestakt,
2.455-bitpanda-staking-ursache) - Kapital rund 2.560 EUR zu hoch. Die neue
Schnittstelle liefert den Saldo je Wallet direkt.

DIE FELDBEDEUTUNG BLEIBT (Voranalyse 16.09.): `quantity` = frei,
`staked_quantity` = gestakt, additiv. 20 Leser rechnen `quantity +
staked_quantity` - keiner muss sich aendern.

DIE ENTSCHEIDUNGEN DES NUTZERS (16.09.2026), und wo sie im Code stehen:

  E1  `quantity` = Spot + Boersenhandel + Advanced Trading, `staked_quantity` =
      Staking; Hebel-Wallets bleiben draussen (gehoeren zu `hebel_positions`)
      -> `SPOT_WALLETS`, `STAKING_WALLETS`, `HEBEL_WALLETS`
  E2  Ausfall -> der letzte gute Stand bleibt, die Datenfrische meldet
      -> jede Ausnahme vor dem ersten Schreiben laesst `holdings` unberuehrt
  E9  Aufteilung je Wallet aus `asset_balance_after` der Buchungen, `/portfolio`
      als Gegenprobe -> `aktualisiere_wallet_salden`, `_stimmt`
  E10 ein offenes VERKAUFEN/REDUZIEREN gilt nur als umgesetzt, wenn ein ECHTER
      Verkauf dieses Coins NACH dem Signal in den Buchungen steht
      -> `_echter_verkauf_seit`. ⚠️ Ohne diese Regel haette der erste Lauf die
      Staking-Korrektur (ETH, SOL, SUI, TAO, NEAR, AVAX, HYPE, BNB) als Verkauf
      gelesen und offene Signale faelschlich bestaetigt.
  E11 fehlt eine Position in einer VOLLSTAENDIGEN Antwort UND zeigen die
      Buchungen Saldo 0, wird sie auf 0 gesetzt -> `_verschwundene`
  E12 der alte Abgleich bleibt als Rueckweg; Schalter `bitpanda.bestand_quelle`
      in `config.yaml` (fehlt = neu) -> `bestandsabgleich`
  E13 Positionen ohne Watchlist-Eintrag und andere Auffaelligkeiten kommen als
      Mail MIT NAME, WERT, STATUS UND ERFORDERLICHER AKTION -> `Meldung`

CASH (Stufe 1.3, Nutzerentscheidungen F1-F4 vom 16.09.2026) -> `cash_abgleich`:
  F1  der HEBEL rechnet weiter mit dem Kapital OHNE Cash (P-5 vom 11.09.); Cash
      wirkt auf die Einsatzgrenze und die Mailzeile, dazu die Anzeige
  F2  `cash_reserve_fiat_eur` behaelt seine Bedeutung VERFUEGBAR (so hat ihn der
      alte Abgleich schon befuellt: 659,99 EUR = available) - keiner seiner Leser
      wird umgedeutet; NEU daneben gesamt, gebunden, Orders, aelteste Order
  F3  den gebundenen BETRAG liefert die Public API (gesamt - verfuegbar); Anzahl,
      Kaufbetrag und aelteste Order kommen aus Fusion (`FUSION_API_KEY`) - faellt
      Fusion aus, bleibt der Betrag richtig und nur die Details fehlen
  F4  die Mailzeile unterscheidet drei Faelle (`entscheidungsrechnung.saetze`)

PROTOKOLL (F6, Befund 2.455-bestand-protokoll): jede Aenderung, jeder
Schutzhinweis und die Cash-Lage stehen im Log - am Notebook war nach dem ersten
Lauf nicht nachzulesen, ob E10 gegriffen hatte.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import api.bitpanda_public as BP
import database.db as db
from importer.bitpanda_sync import (
    SOURCE_BITPANDA_SYNC,
    BitpandaSyncResult,
    PlausibleSignalMatch,
    _KAUF_AKTIONEN,
    _VERKAUF_AKTIONEN,
)

logger = logging.getLogger(__name__)

QUELLE_NEU = "neu"
QUELLE_ALT = "alt"

SPOT_WALLETS = (BP.WALLET_SPOT, BP.WALLET_BOERSE, BP.WALLET_ADVANCED)
STAKING_WALLETS = (BP.WALLET_STAKING,)
HEBEL_WALLETS = BP.WALLET_HEBEL

# E10 - was ein ECHTER Verkauf ist, live gemessen am 16.09.2026 ueber die volle
# Historie (ausgehende Coin-Anteile): sell 320, swap 682, dust_swap 49,
# stock_exchange_sell 21. NICHT: stake/unstake (Wallet-Wechsel), margin_trading_*
# (Hebel), withdrawal (Auszahlung), merger_crypto, reclaim, *_reserve (Order
# reserviert, noch nicht verkauft) und alle Gebuehren-Anteile.
VERKAUFS_VORGAENGE = frozenset({"sell", "swap", "dust_swap", "stock_exchange_sell"})

# Katalogsymbol -> Watchlist-Symbol, wo beide auseinanderlaufen (Befund
# 2.455-bitpanda-zuordnung). Zusaetzlich greift die ISIN aus `yfinance_symbol`.
SYMBOL_ALIAS = {"CC": "CANTON", "VST-US": "VST", "IS0C": "ISOC"}

# Wie weit der inkrementelle Abruf vor den letzten Stand zurueckgreift. Salden
# sind absolut, Ueberlappung schadet nicht - verspaetet gebuchte Vorgaenge
# (`credited_at` in der Vergangenheit) werden so noch erfasst.
UEBERLAPPUNG = timedelta(hours=1)
META_BUCHUNGEN_STAND = "bitpanda_buchungen_stand"
# K-BP-3 (10.10.2026, Schritt7 Par. 23.36/23.37): Bitpanda schreibt `credited_at` mal MIT, mal OHNE Millisekunden
# (`...08:29:58Z` beim Kauf, `...08:29:58.380Z` bei der Hebel-Eroeffnung 380 ms spaeter). Als TEXT verglichen ist `58Z` GROESSER
# als `58.380Z` (`Z` > `.`) - der aeltere Zwischenstand gewann (EURCV 696,04 statt 296,04). Seit Fassung 2 werden Zeitpunkte
# einheitlich mit Millisekunden abgelegt, im Abruf als Zeit verglichen (Gleichstand: hoehere `order_id`), und EINMAL werden die
# gespeicherten Zeitpunkte vereinheitlicht und alle Buchungen neu gelesen (der inkrementelle Lauf holte den 09.10. nie wieder).
META_SALDEN_FASSUNG = "bitpanda_wallet_salden_fassung"
SALDEN_FASSUNG = "2"

# Positionen unter diesem Wert heissen ,Staub' (Belohnungsreste wie SPACE mit
# 0,03 EUR) - sie stehen im Log, bekommen aber keine Mail.
STAUB_EUR = 1.0
# F2/F3 - die neuen Cash-Schluessel neben `cash_reserve_fiat_eur` (= verfuegbar).
META_CASH_GESAMT = "cash_gesamt_eur"
META_CASH_GEBUNDEN = "cash_gebunden_eur"
META_CASH_ORDERS = "cash_orders_anzahl"
META_CASH_ORDERS_EUR = "cash_orders_kauf_eur"
META_CASH_AELTESTE = "cash_aelteste_order"
META_CASH_DETAILS = "cash_details_quelle"      # fusion | differenz
_ISIN = re.compile(r"^([A-Z]{2}[A-Z0-9]{9}[0-9])(\.|$)")
_EPS = 1e-9


@dataclass
class Meldung:
    """E13: eine Mail, die ohne Nachfragen verstaendlich ist."""
    schluessel: str
    betreff: str
    name: str
    wert: str
    status: str
    aktion: str
    cooldown_stunden: float = 24.0

    def text(self) -> str:
        return ("%s\n\nWert:    %s\nStatus:  %s\nAktion:  %s"
                % (self.name, self.wert, self.status, self.aktion))


def _eur(x: float | None) -> str:
    if x is None:
        return "unbekannt"
    return ("{:,.2f} EUR".format(x)).replace(",", "_").replace(".", ",").replace("_", ".")


def _menge(x: float) -> str:
    return ("%.8g" % x).replace(".", ",")


def _zeit(text: str | None) -> datetime | None:
    if not text:
        return None
    try:
        z = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return z if z.tzinfo else z.replace(tzinfo=timezone.utc)


def zeit_einheitlich(text: str | None) -> str | None:
    """`credited_at` in EINER Schreibweise (UTC, Millisekunden, `Z`) - damit auch der Textvergleich in SQL stimmt (K-BP-3)."""
    z = _zeit(text)
    if z is None:
        return None
    z = z.astimezone(timezone.utc)
    return z.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (z.microsecond // 1000)


def _reihenfolge(t: dict, zeit: str) -> tuple:
    """Sortierschluessel einer Buchung: die Zeit, bei Gleichstand die `order_id` (innerhalb eines Vorgangs fortlaufend 1, 2, ...)."""
    try:
        nr = int(t.get("order_id") or 0)
    except (TypeError, ValueError):
        nr = 0
    return (zeit, nr)


def _asset_der_buchung(t: dict) -> str | None:
    return (t.get("asset_amount") or {}).get("asset_id") or t.get("asset_id")


# ---------------------------------------------------------------- Salden (E9)

def aktualisiere_wallet_salden(conn, api_key: str) -> tuple[dict, list[dict], bool]:
    """Neue Buchungen holen und den juengsten Saldo je Asset/Wallet ablegen.

    Rueckgabe: (alle Salden, die in diesem Lauf geholten Vorgaenge, vollstaendig).
    Der Stand fuer den naechsten Lauf rueckt nur vor, wenn der Abruf vollstaendig
    war."""
    stand = db.get_meta_wert(conn, META_BUCHUNGEN_STAND)
    neu_lesen = db.get_meta_wert(conn, META_SALDEN_FASSUNG) != SALDEN_FASSUNG
    seit = None
    if neu_lesen:
        # K-BP-3: EINMAL alle Buchungen, und vorher die gespeicherten Zeitpunkte in die einheitliche Schreibweise
        n = db.vereinheitliche_bitpanda_wallet_zeitpunkte(conn, zeit_einheitlich)
        logger.info("Bitpanda-Bestand (neu): Wallet-Salden Fassung %s - %d Zeitpunkte vereinheitlicht, alle Buchungen werden neu gelesen",
                    SALDEN_FASSUNG, n)
    elif stand and _zeit(stand):
        seit = (_zeit(stand) - UEBERLAPPUNG).isoformat().replace("+00:00", "Z")
    vorgaenge, vollstaendig = BP.hole_buchungen_mit_stand(api_key, seit=seit)
    neu: dict = {}
    rang: dict = {}
    juengster = zeit_einheitlich(stand) if stand else None
    for o in vorgaenge:
        for t in o.get("transactions") or []:
            aid = _asset_der_buchung(t)
            zeit = zeit_einheitlich(t.get("credited_at"))
            nach = t.get("asset_balance_after")
            if not aid or not zeit or nach is None:
                continue
            try:
                saldo = float(nach.get("value") if isinstance(nach, dict) else nach)
            except (TypeError, ValueError):
                continue
            key = (aid, t.get("wallet_owner") or "", t.get("wallet_id") or "")
            r = _reihenfolge(t, zeit)
            if key not in neu or r >= rang[key]:
                neu[key] = (saldo, zeit)
                rang[key] = r
            if not juengster or zeit > juengster:
                juengster = zeit
    db.speichere_bitpanda_wallet_salden(conn, neu)
    if vollstaendig and juengster:
        db.set_meta_wert(conn, META_BUCHUNGEN_STAND, juengster)
    if vollstaendig and neu_lesen:
        db.set_meta_wert(conn, META_SALDEN_FASSUNG, SALDEN_FASSUNG)
    return db.lade_bitpanda_wallet_salden(conn), vorgaenge, vollstaendig


def bestand_je_asset(salden: dict) -> dict:
    """asset_id -> {frei, gestakt, hebel, gesamt} aus den Wallet-Salden (E1)."""
    aus: dict = {}
    for (aid, owner, _wid), (saldo, _zeit_) in salden.items():
        b = aus.setdefault(aid, {"frei": 0.0, "gestakt": 0.0, "hebel": 0.0, "sonst": 0.0})
        if owner in SPOT_WALLETS:
            b["frei"] += saldo
        elif owner in STAKING_WALLETS:
            b["gestakt"] += saldo
        elif owner in HEBEL_WALLETS:
            b["hebel"] += saldo
        else:
            # Eine Wallet-Art, die bisher nie vorkam - nicht raten, sondern
            # ausweisen (sie macht die Gegenprobe gegen `/portfolio` rot).
            b["sonst"] += saldo
    for b in aus.values():
        b["gesamt"] = b["frei"] + b["gestakt"] + b["hebel"] + b["sonst"]
    return aus


def _stimmt(a: float, b: float) -> bool:
    return abs(a - b) <= max(1e-8, 1e-6 * max(abs(a), abs(b)))


def spot_zeile(zeilen: list, b: dict):
    """K-BP-1 (09.10.2026, Schritt7 Par. 23.31/23.32): welche `/portfolio`-Zeile ist die SPOT-Zeile? -> (Zeile oder None, passt, Lesart)

    ⚠️ GEMESSEN am 09.10. an der Rohantwort (`nb_bitpanda_portfolio_roh.py`): bei offenem Hebel fuehrt `/portfolio` je Asset ZWEI
    Zeilen - Spot (frei + gestakt) und Hebel (margin-trading bzw. der Kredit margin-trading-credit) -, OHNE Kennzeichen und in
    WECHSELNDER Reihenfolge (BTC Spot zuerst, ETH Hebel zuerst). Vorher baute `abgleich_neu` `{asset_id: Zeile}` und behielt die
    LETZTE: BTC meldete den Hebelteil, EURCV den Kredit -> Fehlalarm alle 6 h, EURCV blieb veraltet. *"verfuegbar = 0"* kennzeichnet
    den Hebel NICHT - ein ganz gestakter Spot-Wert sieht genauso aus.

    DIE TRENNUNG laeuft deshalb ueber die MENGE der Wallets (Spot = frei + gestakt, Hebel = Hebel-Wallets), ohne Raten:
      * keine Zeile      - passt nur, wenn die Wallets zusammen 0 ergeben
      * eine Zeile       - Spot allein, Spot + Hebel in einer Zeile (beide Lesarten aus E9) oder nur der Hebel bei Spot 0
      * zwei Zeilen      - eine trifft Spot, die andere Hebel, gleich in welcher Reihenfolge
      * mehr als zwei    - unbekannt -> passt nicht (Meldung wie bisher)
    Eine unbekannte Wallet-Art (`sonst`) passt nie. Der Hebel-Teil kommt nie nach `holdings` (E1) - das regelt der Aufrufer."""
    spot, hebel = b["frei"] + b["gestakt"], b["hebel"]
    if abs(b.get("sonst", 0.0)) > _EPS:
        return None, False, "unbekannte Wallet-Art"
    if not zeilen:
        return None, abs(spot) <= _EPS and abs(hebel) <= _EPS, "keine Zeile"
    if len(zeilen) == 1:
        z = zeilen[0]
        if abs(hebel) <= _EPS:
            return z, _stimmt(z.menge_gesamt, spot), "Spot"
        if abs(spot) <= _EPS and _stimmt(z.menge_gesamt, hebel):
            return None, True, "nur Hebel"              # VOR "mit Hebel": bei Spot 0 sind beide Mengen gleich, die Zeile ist Hebel
        if _stimmt(z.menge_gesamt, spot):
            return z, True, "ohne Hebel-Wallet"
        if _stimmt(z.menge_gesamt, spot + hebel):
            return z, True, "mit Hebel-Wallet"
        return z, False, "eine Zeile passt weder zu Spot noch zu Spot + Hebel"
    if len(zeilen) == 2:
        z0, z1 = zeilen
        if _stimmt(z0.menge_gesamt, spot) and _stimmt(z1.menge_gesamt, hebel):
            return z0, True, "Spot- und Hebel-Zeile getrennt"
        if _stimmt(z1.menge_gesamt, spot) and _stimmt(z0.menge_gesamt, hebel):
            return z1, True, "Spot- und Hebel-Zeile getrennt"
        return None, False, "zwei Zeilen passen nicht zu Spot und Hebel"
    return None, False, "%d Zeilen" % len(zeilen)


# ------------------------------------------------------------ Zuordnung (E8)

def watchlist_zuordnung(watchlist) -> tuple[set, dict]:
    """(Watchlist-Symbole, ISIN -> Symbol aus `yfinance_symbol`)."""
    symbole = {str(a.symbol).upper() for a in watchlist or []}
    isin = {}
    for a in watchlist or []:
        m = _ISIN.match(str(getattr(a, "yfinance_symbol", "") or ""))
        if m:
            isin[m.group(1)] = str(a.symbol).upper()
    return symbole, isin


def zuordnen(eintrag, symbole: set, isin: dict) -> str | None:
    """Katalogeintrag -> Watchlist-Symbol: ISIN, Symbol, Alias - sonst None."""
    if eintrag is None:
        return None
    if eintrag.isin and eintrag.isin in isin:
        return isin[eintrag.isin]
    s = str(eintrag.symbol or "").upper()
    if s in symbole:
        return s
    alias = SYMBOL_ALIAS.get(s)
    if alias and alias in symbole:
        return alias
    return None


# --------------------------------------------------------- Signale (E10)

def _echter_verkauf_seit(vorgaenge: list[dict], asset_id: str, seit: datetime | None) -> bool:
    for o in vorgaenge:
        if o.get("operation_type") not in VERKAUFS_VORGAENGE:
            continue
        for t in o.get("transactions") or []:
            if (_asset_der_buchung(t) == asset_id and t.get("flow") == "OUTGOING"
                    and t.get("wallet_owner") in SPOT_WALLETS
                    and t.get("transaction_type") in ("sell", None)):
                z = _zeit(t.get("credited_at"))
                if z and (seit is None or z > seit):
                    return True
    return False


def _offenes_signal(conn, symbol: str, aktionen: set):
    s = db.get_latest_signal(conn, symbol)
    if s is not None and s.umgesetzt is None and s.action in aktionen:
        return s
    return None


# ------------------------------------------------------------- Abgleich

def abgleich_neu(conn, api_key: str, watchlist=None, melden=None) -> BitpandaSyncResult:
    """Ein voller Abgleich ueber die neue Schnittstelle.

    Reihenfolge mit Absicht: ALLE Netzabrufe zuerst (Katalog, Portfolio, Fiat,
    Buchungen), dann geschrieben. Faellt ein Abruf aus, wirft die Funktion,
    bevor `holdings` beruehrt wird (E2). `melden(Meldung)` verschickt Mails
    (Job) - ohne sie stehen die Meldungen nur im Ergebnis (GUI)."""
    import config as _cfg

    watchlist = watchlist if watchlist is not None else _cfg.get_watchlist()
    result = BitpandaSyncResult(staking_verified=True)
    meldungen: list[Meldung] = []

    kat = BP.katalog(conn, api_key)
    zeilen_je: dict = {}
    for z in BP.hole_portfolio(api_key, kat):
        zeilen_je.setdefault(z.asset_id, []).append(z)        # K-BP-1: ALLE Zeilen je Asset, nicht nur die letzte
    fiat = BP.hole_fiat(api_key)
    salden, vorgaenge, vollstaendig = aktualisiere_wallet_salden(conn, api_key)
    bestand = bestand_je_asset(salden)
    antwort_vollstaendig = bool(fiat) and bool(zeilen_je) and vollstaendig
    symbole, isin = watchlist_zuordnung(watchlist)
    alte = {h.symbol: h for h in db.get_all_holdings(conn)}
    gesehen: set = set()

    for aid in sorted(set(zeilen_je) | {a for a, b in bestand.items() if abs(b["gesamt"]) > _EPS}):
        zeilen = zeilen_je.get(aid, [])
        b = bestand.get(aid, {"frei": 0.0, "gestakt": 0.0, "hebel": 0.0, "sonst": 0.0, "gesamt": 0.0})
        eintrag = kat.get(aid)
        name = ("%s (%s)" % (eintrag.name, eintrag.symbol)) if eintrag else "unbekanntes Asset %s" % aid

        # E9 - Gegenprobe je Asset: die Wallets muessen die Portfolio-Zeilen treffen - SPOT gegen SPOT, HEBEL gegen HEBEL
        # (K-BP-1, `spot_zeile`). K10 ist seit 09.10. beantwortet: `/portfolio` fuehrt den Hebel als EIGENE Zeile.
        p, passt, lesart = spot_zeile(zeilen, b)
        bp_gesamt = (b["frei"] + b["gestakt"]) if passt else (p.menge_gesamt if p else 0.0)
        if passt and abs(b["hebel"]) > _EPS:
            logger.info("Bitpanda-Bestand (neu): %s - %s (Spot %s, Hebel %s)",
                        name, lesart, _menge(b["frei"] + b["gestakt"]), _menge(b["hebel"]))
        if not passt:
            gemeldet = " + ".join(_menge(z.menge_gesamt) for z in zeilen) or "0"
            text = ("%s: Buchungen ergeben Spot %s / Hebel %s, Bitpanda meldet %s%s - nicht uebernommen"
                    % (name, _menge(b["frei"] + b["gestakt"]), _menge(b["hebel"]), gemeldet,
                       (", unbekannte Wallet-Art %s" % _menge(b["sonst"])) if abs(b["sonst"]) > _EPS else ""))
            result.warnings.append(text)
            logger.warning("Bitpanda-Bestand (neu): %s", text)
            meldungen.append(Meldung(
                schluessel="bestand_abweichung_%s" % aid, betreff="Bestand passt nicht zusammen: %s" % name,
                name=name, wert=_eur(sum(z.wert_eur or 0.0 for z in zeilen) if zeilen else None),
                status="Menge NICHT uebernommen - der letzte gute Stand bleibt im System (Buchungen Spot %s / "
                       "Hebel %s, Bitpanda %s; %s)" % (_menge(b["frei"] + b["gestakt"]), _menge(b["hebel"]),
                                                      gemeldet, lesart),
                aktion="Keine sofort noetig. Kommt die Meldung beim naechsten Lauf wieder, bitte einen "
                       "Export ziehen - dann fehlt eine Buchung oder eine neue Wallet-Art.",
                cooldown_stunden=6.0))
            continue

        intern = zuordnen(eintrag, symbole, isin)
        if intern is None:
            if abs(bp_gesamt) <= _EPS:
                continue
            wert = p.wert_eur if p else None
            zeile = "%s: %s Stueck, %s" % (name, _menge(bp_gesamt), _eur(wert))
            result.unmatched_bitpanda_symbols.append(zeile)
            if wert is not None and wert < STAUB_EUR:
                logger.info("Bitpanda-Bestand (neu): Staub ohne Watchlist-Eintrag - %s", zeile)
                continue
            logger.warning("Bitpanda-Bestand (neu): Position ohne Watchlist-Eintrag - %s", zeile)
            meldungen.append(Meldung(
                schluessel="ohne_watchlist_%s" % aid, betreff="Position ohne Watchlist-Eintrag: %s" % name,
                name="%s%s" % (name, (", ISIN %s" % eintrag.isin) if eintrag and eintrag.isin else ""),
                wert="%s (%s Stueck)" % (_eur(wert), _menge(bp_gesamt)),
                status="NICHT im Bestand und NICHT im Kapital - das System kennt diesen Wert nicht und "
                       "bewertet ihn nicht",
                aktion="In der Oberflaeche ueber ,Asset hinzufuegen' aufnehmen (Assetklasse und "
                       "Kursquelle angeben). Ist die Position gewollt ausserhalb der Beobachtung, "
                       "diese Mail ignorieren - sie wiederholt sich hoechstens einmal am Tag."))
            continue

        gesehen.add(intern)
        h = alte.get(intern)
        alt_frei = (h.quantity or 0.0) if h else 0.0
        alt_gestakt = (h.staked_quantity or 0.0) if h else 0.0
        neu_frei, neu_gestakt = b["frei"], b["gestakt"]
        if not (_stimmt(alt_frei, neu_frei) and _stimmt(alt_gestakt, neu_gestakt)):
            db.upsert_holding(conn, intern, neu_frei, source=SOURCE_BITPANDA_SYNC)
            db.update_holding_staked_quantity(conn, intern, neu_gestakt)
            result.synced_count += 1
            result.updated_holdings.append(
                "%s: frei %s -> %s, gestakt %s -> %s (%s)"
                % (intern, _menge(alt_frei), _menge(neu_frei), _menge(alt_gestakt), _menge(neu_gestakt),
                   _art(alt_frei, neu_frei, alt_gestakt, neu_gestakt)))
            _signale(conn, result, intern, aid, alt_frei + alt_gestakt, neu_frei + neu_gestakt, vorgaenge)

    # E11 - verschwundene Positionen
    if antwort_vollstaendig:
        _verschwundene(conn, result, meldungen, alte, gesehen, bestand, kat, symbole, isin, vorgaenge)
    else:
        logger.info("Bitpanda-Bestand (neu): Antwort nicht vollstaendig - verschwundene Positionen "
                    "werden in diesem Lauf nicht auf 0 gesetzt")

    # Cash (Stufe 1.3, F1-F4)
    cash = cash_abgleich(conn, fiat, _fusion_schluessel())
    result.cash_reserve_updated = cash["geaendert"]
    result.cash_reserve_old_eur, result.cash_reserve_new_eur = cash["alt_verfuegbar"], cash["verfuegbar"]
    result.cash = cash  # type: ignore[attr-defined]

    db.set_bitpanda_holdings_synced_at(conn, datetime.now(timezone.utc).isoformat())
    _protokoll(result, cash)
    for m in meldungen:
        if melden is not None:
            try:
                melden(m)
            except Exception:                                    # noqa: BLE001
                logger.exception("Meldung %s nicht verschickt", m.schluessel)
    result.meldungen = meldungen  # type: ignore[attr-defined]
    return result


def _art(alt_frei, neu_frei, alt_gestakt, neu_gestakt) -> str:
    """F6: WAS sich geaendert hat - der alte Abgleich nannte jede Aenderung ,Zuwachs'."""
    summe = (neu_frei + neu_gestakt) - (alt_frei + alt_gestakt)
    if _stimmt(alt_frei + alt_gestakt, neu_frei + neu_gestakt):
        return "Umbuchung frei/gestakt"
    if _stimmt(alt_frei, neu_frei):
        return "gestakt %s" % ("Zuwachs" if summe > 0 else "Rueckgang")
    return "Zuwachs" if summe > 0 else "Rueckgang"


def _schluessel_wache(was: str, conn, kennung: str) -> None:
    """1.7: Schluesselzustand melden - fail-soft, der Abgleich geht vor."""
    try:
        from agent import schluessel_wache as SW
        getattr(SW, was)(conn, kennung)
    except Exception:                                        # noqa: BLE001
        logger.exception("Schluesselueberwachung (%s, %s) fehlgeschlagen", was, kennung)


def _fusion_schluessel() -> str | None:
    """Der Fusion-Leseschluessel aus der Umgebung (main.py laedt die .env)."""
    return os.environ.get("FUSION_API_KEY") or None


def cash_abgleich(conn, fiat: dict, fusion_key: str | None = None) -> dict:
    """F1-F3: Cash gesamt, verfuegbar und gebunden speichern.

    Fehlt die EUR-Zeile, wird NICHTS geschrieben (E2 - der letzte gute Stand
    bleibt) und ein Hinweis zurueckgegeben."""
    aus = {"geaendert": False, "alt_verfuegbar": db.get_cash_reserve_fiat_eur(conn),
           "verfuegbar": None, "gesamt": None, "gebunden": None, "orders": None,
           "orders_eur": None, "aelteste": None, "details": None, "hinweis": None}
    eur = (fiat or {}).get(BP.EUR_WAEHRUNG_ID)
    if not eur:
        aus["hinweis"] = "keine EUR-Zeile in der Antwort - Cash nicht aktualisiert"
        logger.warning("Bitpanda-Cash (neu): %s", aus["hinweis"])
        return aus
    gesamt, verfuegbar = float(eur[0]), float(eur[1])
    gebunden = round(max(0.0, gesamt - verfuegbar), 2)
    aus.update(gesamt=round(gesamt, 2), verfuegbar=round(verfuegbar, 2), gebunden=gebunden)
    aus["geaendert"] = not _stimmt(aus["alt_verfuegbar"] or 0.0, verfuegbar)
    jetzt = datetime.now(timezone.utc).isoformat()
    db.set_cash_reserve_fiat_eur(conn, round(verfuegbar, 2))
    db.set_cash_reserve_synced_at(conn, jetzt)
    db.set_meta_wert(conn, META_CASH_GESAMT, "%.2f" % gesamt)
    db.set_meta_wert(conn, META_CASH_GEBUNDEN, "%.2f" % gebunden)
    details = "differenz"
    orders = orders_eur = aelteste = None
    if fusion_key and gebunden > 0:
        try:
            from api.bitpanda_fusion import offene_orders
            o = offene_orders(fusion_key)
            orders, orders_eur, aelteste, details = o.anzahl, o.kauf_eur, o.aelteste, "fusion"
            _schluessel_wache("wieder_in_ordnung", conn, "fusion")
        except Exception as exc:                                 # noqa: BLE001
            logger.warning("Bitpanda-Cash (neu): Fusion-Orders nicht lesbar - Betrag aus der "
                           "Public API, ohne Details: %s", exc)
            if getattr(exc, "schluessel_abgelehnt", False):
                # 1.7 (G1): war bis 16.09. nur diese WARNING - still
                _schluessel_wache("abgelehnt", conn, "fusion")
    elif gebunden > 0:
        logger.info("Bitpanda-Cash (neu): kein FUSION_API_KEY - gebundener Betrag ohne Orderdetails")
    for key, wert in ((META_CASH_ORDERS, orders), (META_CASH_ORDERS_EUR, orders_eur),
                      (META_CASH_AELTESTE, aelteste)):
        db.set_meta_wert(conn, key, "" if wert is None else str(wert))
    db.set_meta_wert(conn, META_CASH_DETAILS, details)
    aus.update(orders=orders, orders_eur=orders_eur, aelteste=aelteste, details=details)
    return aus


def _protokoll(result, cash: dict) -> None:
    """F6: der Lauf steht vollstaendig im Log - Zusammenfassung, jede Aenderung,
    jede bestaetigte oder geschuetzte Signal-Umsetzung, die Cash-Lage."""
    logger.info(
        "Bitpanda-Bestandsabgleich (neu): %d Aenderung(en), %d Signal(e) als umgesetzt bestaetigt, "
        "%d Hinweis(e), %d Position(en) ohne Watchlist, %d unklar",
        result.synced_count, len(result.auto_confirmed_decreases), len(result.warnings),
        len(result.unmatched_bitpanda_symbols), len(result.stale_bitpanda_sync_symbols))
    for z in result.updated_holdings:
        logger.info("Bitpanda-Bestand (neu): Aenderung %s", z)
    for z in result.auto_confirmed_decreases:
        logger.info("Bitpanda-Bestand (neu): Signal bestaetigt - %s", z)
    for z in result.warnings:
        if "NICHT als umgesetzt" in z:
            logger.info("Bitpanda-Bestand (neu): Schutz E10 - %s", z)
    for z in result.stale_bitpanda_sync_symbols:
        logger.info("Bitpanda-Bestand (neu): unklar - %s", z)
    if cash.get("verfuegbar") is not None:
        logger.info(
            "Bitpanda-Cash (neu): verfuegbar %s, gesamt %s, gebunden %s%s",
            _eur(cash["verfuegbar"]), _eur(cash["gesamt"]), _eur(cash["gebunden"]),
            (" in %s Orders (Kauf %s, aelteste %s)" % (cash["orders"], _eur(cash["orders_eur"]),
                                                       str(cash["aelteste"] or "-")[:10])
             if cash.get("details") == "fusion" else " (ohne Orderdetails)"))


def _signale(conn, result, intern, aid, alt_summe, neu_summe, vorgaenge) -> None:
    """Rueckgang -> offenes Verkaufssignal nur bei echtem Verkauf (E10);
    Zuwachs -> offenes Kaufsignal als ,plausibel' fuer die Oberflaeche."""
    if neu_summe < alt_summe - _EPS:
        s = _offenes_signal(conn, intern, _VERKAUF_AKTIONEN)
        if s is None:
            return
        if _echter_verkauf_seit(vorgaenge, aid, _zeit(s.created_at)):
            db.update_signal_umsetzung(conn, s.id, True, umgesetzt_menge=neu_summe)
            result.auto_confirmed_decreases.append(
                "%s: %s -> %s (%s-Signal vom %s bestaetigt - Verkauf in den Buchungen)"
                % (intern, _menge(alt_summe), _menge(neu_summe), s.action, str(s.created_at)[:10]))
        else:
            result.warnings.append(
                "%s: Rueckgang %s -> %s ohne Verkaufsvorgang (Staking-Korrektur, Auszahlung, Hebel) - "
                "%s-Signal vom %s NICHT als umgesetzt markiert"
                % (intern, _menge(alt_summe), _menge(neu_summe), s.action, str(s.created_at)[:10]))
    elif neu_summe > alt_summe + _EPS:
        s = _offenes_signal(conn, intern, _KAUF_AKTIONEN)
        if s is not None:
            result.plausible_signal_matches.append(PlausibleSignalMatch(
                signal_id=s.id, symbol=intern, action=s.action, alt_menge=alt_summe,
                neu_menge=neu_summe, signal_datum=s.created_at))


def _verschwundene(conn, result, meldungen, alte, gesehen, bestand, kat, symbole, isin, vorgaenge) -> None:
    """E11: gehaltene Watchlist-Werte, die in der Antwort fehlen. Auf 0 nur, wenn
    ein Bitpanda-Asset zu ihnen gehoert und dessen Buchungen Saldo 0 zeigen."""
    je_symbol: dict = {}
    for aid, eintrag in kat.items():
        intern = zuordnen(eintrag, symbole, isin)
        if intern and aid in bestand:
            je_symbol.setdefault(intern, []).append(aid)
    for symbol, h in alte.items():
        menge = (h.quantity or 0.0) + (h.staked_quantity or 0.0)
        if symbol in gesehen or menge <= _EPS or symbol not in symbole:
            continue
        aids = je_symbol.get(symbol, [])
        if not aids:
            result.stale_bitpanda_sync_symbols.append(
                "%s (%s) - keinem Bitpanda-Asset mit Buchungen zuzuordnen, NICHT auf 0 gesetzt"
                % (symbol, _menge(menge)))
            continue
        if all(abs(bestand[a]["frei"] + bestand[a]["gestakt"]) <= _EPS for a in aids):
            alt_summe = menge
            db.upsert_holding(conn, symbol, 0.0, source=SOURCE_BITPANDA_SYNC)
            db.update_holding_staked_quantity(conn, symbol, 0.0)
            result.synced_count += 1
            result.updated_holdings.append("%s: %s -> 0 (bei Bitpanda nicht mehr vorhanden)"
                                           % (symbol, _menge(alt_summe)))
            _signale(conn, result, symbol, aids[0], alt_summe, 0.0, vorgaenge)
            meldungen.append(Meldung(
                schluessel="verschwunden_%s" % symbol, betreff="Position auf 0 gesetzt: %s" % symbol,
                name=symbol, wert="vorher %s Stueck" % _menge(alt_summe),
                status="Bei Bitpanda nicht mehr vorhanden (Buchungen Saldo 0) - im System auf 0 gesetzt",
                aktion="Keine, wenn die Position verkauft oder uebertragen wurde. Falls unerwartet: "
                       "bei Bitpanda pruefen.", cooldown_stunden=24.0))


def bestandsabgleich(conn, api_key: str, listed_assets_holen=None, melden=None, watchlist=None):
    """E12: der EINE Einstieg fuer Job und Oberflaeche - waehlt die Quelle.

    `bitpanda.bestand_quelle` in `config.yaml`: fehlt oder `neu` -> neuer
    Abgleich; `alt` -> der bisherige (Rueckweg ohne Code-Aenderung)."""
    import config as _cfg

    quelle = _cfg.bitpanda_bestand_quelle()
    if quelle == QUELLE_ALT:
        from importer.bitpanda_sync import sync_from_bitpanda
        listed = listed_assets_holen() if listed_assets_holen else []
        logger.info("Bitpanda-Bestand: ALTER Abgleich (config bitpanda.bestand_quelle = alt)")
        return sync_from_bitpanda(conn, api_key, listed)
    return abgleich_neu(conn, api_key, watchlist=watchlist, melden=melden)
