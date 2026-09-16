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

CASH bleibt in diesem Schritt beim alten Abgleich (`sync_fiat_cash_from_bitpanda`);
die neue Cash-Logik ist Stufe 1.3.
"""
from __future__ import annotations

import logging
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
    sync_fiat_cash_from_bitpanda,
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

# Positionen unter diesem Wert heissen ,Staub' (Belohnungsreste wie SPACE mit
# 0,03 EUR) - sie stehen im Log, bekommen aber keine Mail.
STAUB_EUR = 1.0
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
    return ("%.2f EUR" % x).replace(".", ",")


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


def _asset_der_buchung(t: dict) -> str | None:
    return (t.get("asset_amount") or {}).get("asset_id") or t.get("asset_id")


# ---------------------------------------------------------------- Salden (E9)

def aktualisiere_wallet_salden(conn, api_key: str) -> tuple[dict, list[dict], bool]:
    """Neue Buchungen holen und den juengsten Saldo je Asset/Wallet ablegen.

    Rueckgabe: (alle Salden, die in diesem Lauf geholten Vorgaenge, vollstaendig).
    Der Stand fuer den naechsten Lauf rueckt nur vor, wenn der Abruf vollstaendig
    war."""
    stand = db.get_meta_wert(conn, META_BUCHUNGEN_STAND)
    seit = None
    if stand and _zeit(stand):
        seit = (_zeit(stand) - UEBERLAPPUNG).isoformat().replace("+00:00", "Z")
    vorgaenge, vollstaendig = BP.hole_buchungen_mit_stand(api_key, seit=seit)
    neu: dict = {}
    juengster = stand
    for o in vorgaenge:
        for t in o.get("transactions") or []:
            aid = _asset_der_buchung(t)
            zeit = t.get("credited_at")
            nach = t.get("asset_balance_after")
            if not aid or not zeit or nach is None:
                continue
            try:
                saldo = float(nach.get("value") if isinstance(nach, dict) else nach)
            except (TypeError, ValueError):
                continue
            key = (aid, t.get("wallet_owner") or "", t.get("wallet_id") or "")
            if key not in neu or zeit >= neu[key][1]:
                neu[key] = (saldo, zeit)
            if not juengster or zeit > juengster:
                juengster = zeit
    db.speichere_bitpanda_wallet_salden(conn, neu)
    if vollstaendig and juengster:
        db.set_meta_wert(conn, META_BUCHUNGEN_STAND, juengster)
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
    positionen = {p.asset_id: p for p in BP.hole_portfolio(api_key, kat)}
    fiat = BP.hole_fiat(api_key)
    salden, vorgaenge, vollstaendig = aktualisiere_wallet_salden(conn, api_key)
    bestand = bestand_je_asset(salden)
    antwort_vollstaendig = bool(fiat) and bool(positionen) and vollstaendig
    symbole, isin = watchlist_zuordnung(watchlist)
    alte = {h.symbol: h for h in db.get_all_holdings(conn)}
    gesehen: set = set()

    for aid in sorted(set(positionen) | {a for a, b in bestand.items() if abs(b["gesamt"]) > _EPS}):
        p = positionen.get(aid)
        b = bestand.get(aid, {"frei": 0.0, "gestakt": 0.0, "hebel": 0.0, "sonst": 0.0, "gesamt": 0.0})
        eintrag = kat.get(aid)
        name = ("%s (%s)" % (eintrag.name, eintrag.symbol)) if eintrag else "unbekanntes Asset %s" % aid
        bp_gesamt = p.menge_gesamt if p else 0.0

        # E9 - Gegenprobe je Asset: die Wallet-Summe muss die Portfolio-Menge treffen.
        # ⚠️ OFFEN GEMESSEN: ob `/portfolio` Hebel-Sicherheiten mitzaehlt, liess
        # sich am 15./16.09. nicht pruefen - es war keine Hebelposition offen.
        # Deshalb gelten BEIDE Lesarten; welche zutraf, steht im Log (Kontrolle
        # beim ersten offenen Hebel, Notebook-Kontrolle K10).
        mit_hebel = _stimmt(b["gesamt"], bp_gesamt)
        ohne_hebel = abs(b["hebel"]) > _EPS and _stimmt(b["gesamt"] - b["hebel"], bp_gesamt)
        if ohne_hebel and not mit_hebel:
            logger.info("Bitpanda-Bestand (neu): %s - Portfolio-Menge ohne Hebel-Wallet (%s) gezaehlt",
                        name, _menge(b["hebel"]))
        elif mit_hebel and abs(b["hebel"]) > _EPS:
            logger.info("Bitpanda-Bestand (neu): %s - Portfolio-Menge mit Hebel-Wallet (%s) gezaehlt",
                        name, _menge(b["hebel"]))
        if not (mit_hebel or ohne_hebel) or abs(b["sonst"]) > _EPS:
            text = ("%s: Buchungen ergeben %s, Bitpanda meldet %s%s - nicht uebernommen"
                    % (name, _menge(b["gesamt"]), _menge(bp_gesamt),
                       (", unbekannte Wallet-Art %s" % _menge(b["sonst"])) if abs(b["sonst"]) > _EPS else ""))
            result.warnings.append(text)
            logger.warning("Bitpanda-Bestand (neu): %s", text)
            meldungen.append(Meldung(
                schluessel="bestand_abweichung_%s" % aid, betreff="Bestand passt nicht zusammen: %s" % name,
                name=name, wert=_eur(p.wert_eur if p else None),
                status="Menge NICHT uebernommen - der letzte gute Stand bleibt im System (Buchungen %s, "
                       "Bitpanda %s)" % (_menge(b["gesamt"]), _menge(bp_gesamt)),
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
                "%s: frei %s -> %s, gestakt %s -> %s" % (intern, _menge(alt_frei), _menge(neu_frei),
                                                        _menge(alt_gestakt), _menge(neu_gestakt)))
            _signale(conn, result, intern, aid, alt_frei + alt_gestakt, neu_frei + neu_gestakt, vorgaenge)

    # E11 - verschwundene Positionen
    if antwort_vollstaendig:
        _verschwundene(conn, result, meldungen, alte, gesehen, bestand, kat, symbole, isin, vorgaenge)
    else:
        logger.info("Bitpanda-Bestand (neu): Antwort nicht vollstaendig - verschwundene Positionen "
                    "werden in diesem Lauf nicht auf 0 gesetzt")

    # Cash bleibt bis Stufe 1.3 beim alten Weg
    cash = sync_fiat_cash_from_bitpanda(conn, api_key)
    result.cash_reserve_updated, result.cash_reserve_old_eur, result.cash_reserve_new_eur = (
        cash.updated, cash.old_eur, cash.new_eur)

    db.set_bitpanda_holdings_synced_at(conn, datetime.now(timezone.utc).isoformat())
    for m in meldungen:
        if melden is not None:
            try:
                melden(m)
            except Exception:                                    # noqa: BLE001
                logger.exception("Meldung %s nicht verschickt", m.schluessel)
    result.meldungen = meldungen  # type: ignore[attr-defined]
    return result


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
