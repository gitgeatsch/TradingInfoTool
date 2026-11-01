# -*- coding: utf-8 -*-
"""A1 — der EREIGNIS-LESER (G9, Fütterung §3/§6 Schritt 4; Voranalyse_A1_Ereignisleser_01_11.md, Nutzer 01.11.: *„a, bauen – prüfen,
gegenprüfen und doku“*).

Macht aus MELDUNGEN (Binance-, Upbit-Ankündigungen, Nachrichten) EREIGNISSE: Zeit · Asset oder Bereich · Typ · Schwere · Beleg — als
FAKT, nie als Urteil (Ü2, Regel 4). Die Sichten bekommen nie Rohmeldungen (Fütterung §3), nur diese Zeilen.

EIN Rechenweg live und Rückspiel (Ü8):
  * Börsen REGELBASIERT (A1-1): erste passende Regel gewinnt. Für die drei Mail-Arten dieselben Meldungen wie
    ``binance_ankuendigungen.art`` (A1-2, Prüfpaket) und dieselben Kürzel (``binance_ankuendigungen.kuerzel``)
  * Nachrichten: VORFILTER auf Risiko-Stichwörter (Nutzer 01.11. „a“), nur die Treffer liest das LLM. Ob der Filter echte Ereignisse
    verliert, misst die Stichprobe (P1/P2) — ist es mehr als vernachlässigbar, geht es auf b (alle Nachrichten)
  * der REST der Börsen und die Vorfilter-Treffer: gpt-oss-120b (Groq), Stapel zu 25, Temperatur 0, Typ-Definitionen im Prompt (A1-6).
    Jede Antwort steht in ``llm_antwort`` (Eingabe-Prüfsumme, Rohtext, Token) — ein zweiter Lauf liest sie, statt neu zu fragen
  * SCHWERE nur aus dem Register (A1-8): die gemessene Wirkung mit Befund, sonst „ungemessen“
  * ``bekannt_ab`` (A1-5): Börsen Veröffentlichung + 1 h (stündlicher Abruf); Nachrichten min(Archivaufnahme, Veröffentlichung + 1 h)

⚠️ Ablage ``data/_sichten/sichten.db``, Tabellen ``ereignis`` und ``llm_antwort``. NIE die Produktion. Kein Betrieb, kein NB, keine Mail.

    python -m agent.ereignisse --regeln            # Börsen-Ereignisse nach Regeln (ohne Netz)
    python -m agent.ereignisse --llm               # Rest + Vorfilter-Treffer per LLM (wiederaufnehmbar, wartet auf das Kontingent)
    python -m agent.ereignisse --stand
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

import pandas as pd

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEN = os.path.join(PROJ, "data")
ABLAGE = os.path.join(DATEN, "_sichten", "sichten.db")
QUELLEN = {"binance": os.path.join(DATEN, "_a1", "binance_ankuendigungen_alle.db"),
           "upbit": os.path.join(DATEN, "_c2", "ankuendigungen.db"),
           "nachricht": os.path.join(DATEN, "_lc", "nachrichten.db")}
MODELL = "openai/gpt-oss-120b"
URL = "https://api.groq.com/openai/v1/chat/completions"
STAPEL = 25
LESEVERZUG_H = 1                        # A1-5: live würde stündlich gelesen
FENSTER_T = 7                           # Takt §5: ein Gutachten gilt höchstens 7 Tage - so weit zurück reicht „neu seit“
NACHRICHT_AB = "2025-12-01"             # Rückspielfenster (G7); das Archiv reicht bis 01/2025 zurück, gelesen wird ab hier
# ⚠️ WEG b (Nutzerregel 01.11.: „ist das mehr als vernachlässigbar, geht es auf b“): der Vorfilter erfasste in der Stichprobe nur ~55 %
# der relevanten Risiko-Ereignisse (a1_nachweis.txt) -> ALLE Nachrichten gehen ans LLM. Der Vorfilter bleibt nur als REIHENFOLGE.
WEG = "b"

# ══ Typkatalog (Voranalyse §3) — die Definition steht im Prompt (A1-6) ══════════════════════════════════════════════════════════
TYPEN = {
    "delisting_token": "eine Börse beendet den Handel eines Tokens ganz",
    "delisting_futures": "eine Börse schließt einen Terminkontrakt (Futures/Perpetual)",
    "delisting_margin": "eine Börse beendet Margin-Handel oder entfernt Margin-Paare",
    "paar_entfernt": "eine Börse entfernt einzelne Spot-Handelspaare, der Token bleibt handelbar",
    "monitoring": "eine Börse setzt ein Beobachtungs-/Warnkennzeichen auf einen Token",
    "monitoring_ende": "eine Börse nimmt ein solches Kennzeichen zurück",
    "listing_spot": "eine Börse nimmt einen Token neu in den Spot-Handel oder in einen neuen Markt (z. B. KRW)",
    "listing_futures": "eine Börse startet einen neuen Terminkontrakt",
    "listing_alpha": "Aufnahme in Binance Alpha oder eine ähnliche Vorstufe",
    "alpha_entfernt": "Binance Alpha oder eine ähnliche Vorstufe entfernt einen Token",
    "margin_neu": "eine Börse nimmt einen Token in den Margin-Handel auf",
    "verschoben": "ein angekündigter Termin (Listing, Delisting, Upgrade) wird verschoben oder vorgezogen",
    "depeg_aussetzung": "ein Stablecoin verliert seine Bindung, oder Einzahlung/Auszahlung/Handel/ein Netz wird ausgesetzt oder fällt aus",
    "hack_exploit": "Diebstahl, Hack, Exploit, Rug Pull, abgezogene Mittel",
    "regulierung_klage": "Gesetz oder Gesetzesschritt (Abstimmung, Beschluss), Behördenentscheid, Ermittlung, Klage, Anklage, Urteil, "
                         "Vergleich, Verbot, Lizenz, Sanktion, Beschlagnahme. NICHT: Forderung, Kritik, Treffen, Erwägung, Meinung "
                         "(das ist marktbericht_meinung)",
    "etf_fonds": "Antrag, Zulassung, Start, Ablehnung eines ETF oder Fonds (tägliche Zu-/Abflüsse sind marktbericht_meinung)",
    "makro_zentralbank": "Zinsentscheid, Zentralbank, Inflation, Arbeitsmarkt, Zölle, Staatshaushalt, Konjunkturdaten",
    "unternehmen": "Firmenkauf, Fusion, Umstrukturierung, Insolvenz, Finanzierungsrunde, Börsengang; eine Firma, Stiftung oder ein "
                   "Staat kauft oder verkauft Krypto in großem Umfang (gemeldeter Kauf/Verkauf, keine Prognose)",
    "netz_upgrade": "Netz-Upgrade, Hard Fork, Token-Migration oder -Tausch, Umbenennung, Änderung der Tokenomics, Burn",
    "token_freigabe": "NUR Unlock/Vesting: bisher gesperrte Token werden frei",
    "airdrop": "Airdrop, Gratis-Verteilung von Token",
    "aktion": "Werbung, Wettbewerb, Rabatt, Belohnung, Veranstaltung",
    "produkt": "neues Produkt, Funktion, Gebühr, Wartung, Programm einer Firma oder Börse (ohne Handelsbeginn/-ende eines Tokens)",
    "marktbericht_meinung": "Kursbericht, Zu-/Abflüsse, Analyse, Prognose, Meinung, Interview, Erklärstück — kein neues Geschehen",
    "sonstiges": "neues Geschehen, das in keinen anderen Typ passt",
}
KEIN_EREIGNIS = ("aktion", "produkt", "marktbericht_meinung")   # abgelegt, aber nicht an die Sichten (Voranalyse §3)
# Prompt 1 (35eb32461b60) nannte die Bereiche nur - das LLM legte 39 von 90 Nachrichten unter "sonstiges", darunter Krypto-Hacks und
# Krypto-Klagen, die so an KEINE Sicht gingen (a1_nachweis.txt). Prompt 2 definiert sie.
BEREICHE = {
    "asset": "die Meldung betrifft ein oder mehrere bestimmte Krypto-Assets (dann stehen sie in assets)",
    "krypto_gesamt": "Krypto allgemein ohne ein bestimmtes Asset: Börsen, DeFi, Wallets, Stablecoins, Krypto-Firmen, Krypto-Kriminalität, "
                     "Krypto-Gesetze und -Regulierung (in jedem Land)",
    "makro_usa": "US-Wirtschaft und Fed: Zinsen, Inflation, Arbeitsmarkt, Konjunktur, Zölle, Staatshaushalt (nicht: Krypto-Gesetze)",
    "aktien_kredit": "Aktien, Anleihen, Banken, Kredit - ohne Krypto-Bezug",
    "asien": "Wirtschaft und Märkte Asiens - ohne Krypto-Bezug",
    "sonstiges": "NUR wenn die Meldung weder Krypto noch Wirtschaft oder Finanzmärkte betrifft",
}
SICHT_JE_BEREICH = {"asset": "S7", "krypto_gesamt": "S1", "makro_usa": "S2", "aktien_kredit": "S3", "asien": "S5"}
# Gleichheit mit dem Betrieb (A1-2, P3): Typ hier -> ``binance_ankuendigungen.art``
BETRIEB_ART = {"delisting_token": "token_delist", "delisting_futures": "futures_delist", "monitoring": "monitoring"}

# ══ Regeln je Börse — erste passende gewinnt, Reihenfolge = Vorrang (A1-1, beim Bau nachgeschärft) ═══════════════════════════════
# Die ersten fünf stehen UNVERÄNDERT wie in der Voranalyse - sie tragen die Gleichheit mit dem Betrieb (59/19/32).
B_REGELN = [
    ("monitoring_ende", r"(?i)remove .*monitoring tag|monitoring tag.*remov"),
    ("monitoring", r"(?i)monitoring tag"),
    ("delisting_futures", r"(?i)futures will (delist|close)|delist .*perpetual"),
    ("delisting_margin", r"(?i)margin will delist|removal of (isolated |cross )?margin trading pairs"),
    ("delisting_token", r"(?i)^binance will delist|will cease trading"),
    ("paar_entfernt", r"(?i)removal of (spot )?trading pairs"),          # A1-3: auch der alte Titel ohne „Spot“ (2023)
    ("alpha_entfernt", r"(?i)alpha will remove"),
    ("depeg_aussetzung", r"(?i)depeg|price deviation|suspend(s|ed)? (deposits|withdrawals|trading)|\bhalt"),
    ("verschoben", r"(?i)postpone|delay|will be advanced"),
    ("listing_futures", r"(?i)futures will launch|perpetual contract"),
    ("listing_spot", r"(?i)^binance will list|adds .* trading pairs?|on binance (launchpool|hodler airdrops|megadrop)|will be available on binance"),
    ("listing_alpha", r"(?i)binance alpha"),
    ("margin_neu", r"(?i)margin will add|margin adds|adds .* on (cross|isolated) margin"),
    ("netz_upgrade", r"(?i)network upgrade|hard fork|wallet maintenance|token (swap|merge|migration)|redenomination|rebrand|contract swap"
                     r"|mainnet swap|tokenomics|completes? (the )?integration|cease support for deposits"),
    ("airdrop", r"(?i)airdrop"),
    ("aktion", r"(?i)competition|rewards?|share|prize|promotion|campaign|giveaway|quiz|voucher|learn & earn|earn |exclusive|contest|discount"
               r"|bonus|refer|up for grabs|\bwin\b|celebrat|trip to|award"),
    ("produkt", r"(?i)convert|tick size|leverage|margin tiers|options|\bapi\b|copy trading|trading bots?|earn|simple earn|loan|pay|card|launch"
                r"|introduc|program|fee|maintenance|system upgrade|collateral|wallet|p2p|vip|update"),
]
U_REGELN = [
    ("monitoring_ende", r"유의 ?종목 ?(지정 )?해제|유의 촉구 해제"),
    ("monitoring", r"유의 ?종목|투자 ?유의|유의 촉구"),
    ("paar_entfernt", r"(BTC|ETH|USDT|비트렉스)( 마켓|/[A-Z]+ 마켓) 거래 ?지원 ?(종료|일시 ?중단)|페어 제거"),
    ("delisting_token", r"거래 ?지원 ?종료|사업 종료"),
    ("listing_spot", r"상장|신규 ?거래 ?지원|디지털 자산 추가|마켓 (오픈|추가)|거래 ?지원 예정|코인 추가"),
    ("netz_upgrade", r"네트워크 업그레이드|하드포크|입출금|스왑|리브랜딩|토큰 변경|메인넷|티커 변경"),
    ("airdrop", r"에어드랍"),
]
# ══ Vorfilter Nachrichten (Weg a): Risiko-Stichwörter ══════════════════════════════════════════════════════════════════════════
# ⚠️ Die Voranalyse zählte 14,8 % mit einem nicht abgelegten Muster; dieses hier ist das gebaute und gilt (Wert in der Doku).
VORFILTER = re.compile(r"(?i)\bhack|exploit|\bdrain(ed|s)?\b|stolen|theft|breach|attack|de-?peg|delist|\bhalt|suspend|outage|frozen|freez"
                       r"|lawsuit|\bsues?\b|\bsued\b|charge[ds]?\b|indict|regulat|\bban(s|ned)?\b|sanction|\bprobe\b|investigat|settle"
                       r"|bankrupt|insolven|collapse|liquidat|unlock|vesting")
VORFILTER_GROSS = re.compile(r"\b(SEC|CFTC|DOJ)\b")       # Behördenkürzel nur in Großschrift (sonst „sec“ in „second“)

# ══ Schwere — NUR aus dem Register (A1-8); Schlüssel (Quelle, Typ[, Markt]) ═══════════════════════════════════════════════════
_E1 = "E-1 (Schritt7 §23.23)"
SCHWERE = {
    ("binance", "delisting_token"): "gemessen: Merkmal SCHWER 24 h −0,95 bis −1,46 % in den unverzerrten Mengen, nach der Vorabregel "
                                    "NICHT getragen; Token-Delisting allein −0,9 bis −6,1 % (unter der Mindestzahl) · " + _E1,
    ("binance", "delisting_futures"): "gemessen: Merkmal SCHWER 24 h −0,95 bis −1,46 %, nach der Vorabregel NICHT getragen; "
                                      "Futures-Delisting allein zu wenige (≤ 8) · " + _E1,
    ("binance", "monitoring"): "gemessen: Merkmal SCHWER 24 h −0,95 bis −1,46 %, nach der Vorabregel NICHT getragen; Monitoring "
                               "allein −1,0 bis −1,6 % · " + _E1,
    ("binance", "paar_entfernt"): "gemessen: ohne Effekt (der Token bleibt handelbar) · " + _E1 + " ⚠ Menge ohne 27 Entfernungen 2023 (A1-3)",
    ("binance", "delisting_margin"): "gemessen: ohne Effekt (der Token bleibt handelbar) · " + _E1,
    ("binance", "listing_futures"): "gemessen: 7 T −6,2 Pp gegen BTC, Rang gegen Zufall 0,00 — TRÄGT NICHT · C2-a (Spot §38.4)",
    ("binance", "listing_spot"): "Auskunft (kein Urteil): 7 T Mittel −8,4 %, Median −16,9 % · C2-c (Spot §38.4)",
    ("upbit", "listing_spot", "KRW"): "gemessen: 7 T −10,0 Pp gegen BTC, erste 4 h Median +12 % — SCHADET · C2-b (Spot §38.4)",
}
UNGEMESSEN = "ungemessen"

# ══ Assets — Universum und Alias-Tabelle (A1-4) ════════════════════════════════════════════════════════════════════════════════
# Kürzel, die zugleich gewöhnliche Wörter sind: nur mit Namen im Titel oder in Klammern/als Paar (Kennzeichen der Börse)
MEHRDEUTIG = {"S", "CAT", "ONE", "GAS", "AI", "HIGH", "FUN", "MOVE", "ME", "PEOPLE", "SUN", "BOND", "GO", "LINK", "OM", "ID", "MAGIC",
              "BANANA", "DOGS", "PORTAL", "OPEN", "USUAL", "NOT", "TRUMP", "WIN", "BEL", "GLM", "HOT", "KEY", "ALT", "ACE", "MASK",
              "SAFE", "JUP", "FORM", "RARE", "LIT", "PUNDIX", "PHA", "AUDIO", "STORJ", "CHESS", "ARK", "TRU", "VIC", "ZK", "T", "G", "W",
              "A", "C", "U", "NEW", "BIG", "CHEX", "NFP", "API", "CEO", "IPO", "ETF", "USA", "EU", "UK", "FED", "SEC", "CPI", "GDP"}
ALIAS_ZUSATZ = {"bitcoin": "BTC", "ether": "ETH", "ethereum": "ETH", "solana": "SOL", "ripple": "XRP", "dogecoin": "DOGE",
                "cardano": "ADA", "sonic": "S", "chainlink": "LINK", "tether": "USDT", "binance coin": "BNB", "polkadot": "DOT",
                "avalanche": "AVAX", "hyperliquid": "HYPE", "toncoin": "TON", "litecoin": "LTC", "tron": "TRX", "sui": "SUI",
                "aptos": "APT", "arbitrum": "ARB", "optimism": "OP", "celestia": "TIA", "near protocol": "NEAR", "pepe": "PEPE"}


def welt() -> set:
    """Asset-Universum: Binance-Stundenreihen inkl. eingestellter (wie ``binance_ankuendigungen.welt``) + Watchlist."""
    from agent import binance_ankuendigungen as BA
    s = set(BA.welt(DATEN))
    try:
        import config as C
        s |= {w.symbol.upper() for w in C.get_watchlist() if w.assetklasse == "krypto"}
    except Exception:                                          # noqa: BLE001
        pass
    return s


def alias() -> dict:
    """Name (klein) -> Kürzel: Watchlist-Namen + Zusatz."""
    a = dict(ALIAS_ZUSATZ)
    try:
        import config as C
        for w in C.get_watchlist():
            if w.assetklasse == "krypto" and w.name and len(w.name) >= 3:
                a.setdefault(w.name.lower(), w.symbol.upper())
    except Exception:                                          # noqa: BLE001
        pass
    return a


def _wort(t: str, w: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(w), t, re.I) is not None


def assets_pruefen(kandidaten, titel: str, W: set, A: dict) -> list:
    """Kürzel aus dem LLM oder dem Titel gegen Universum und Alias-Tabelle: ein mehrdeutiges gilt nur mit seinem Namen im Titel."""
    namen_je = {}
    for n, k in A.items():
        namen_je.setdefault(k, []).append(n)
    aus = set()
    for k in kandidaten or []:
        k = str(k).upper().strip().lstrip("$")
        if not k or k not in W:
            continue
        if k in MEHRDEUTIG and not any(_wort(titel, n) for n in namen_je.get(k, [])):
            continue
        aus.add(k)
    for n, k in A.items():                                    # Name ohne Kürzel („Solana“) zählt auch
        if k in W and _wort(titel, n):
            aus.add(k)
    return sorted(aus)


# ══ Regeln ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def regel(titel: str, regeln) -> str | None:
    for typ, m in regeln:
        if re.search(m, titel or ""):
            return typ
    return None


def binance_assets(typ: str, titel: str, text: str, W: set) -> list:
    """Für die Mail-Arten GENAU die Kürzel des Betriebs (E-1); sonst Klammer, Kontrakt (XYZUSDT) und Großwörter im Titel."""
    from agent import binance_ankuendigungen as BA
    if typ in BETRIEB_ART:
        return sorted(BA.kuerzel(BETRIEB_ART[typ], titel, text or "", W))
    k = set(re.findall(r"\(([A-Z0-9]{2,15})\)", titel)) | {BA.basis(x) for x in re.findall(r"\b([A-Z0-9]{2,20})USDT\b", titel)}
    k |= {x for x in re.findall(r"(?<![A-Za-z0-9])([A-Z0-9]{2,12})(?![A-Za-z0-9])", titel) if x not in MEHRDEUTIG}
    if typ in ("paar_entfernt", "delisting_margin"):
        k |= set(re.findall(r"\b([A-Z0-9]{2,15})/[A-Z0-9]{2,6}\b", text or ""))
    return sorted(x for x in k if x in W and x not in BA.QUOTE)


def upbit_assets(titel: str, W: set) -> list:
    from agent import binance_ankuendigungen as BA
    t = re.sub(r"\b(KRW|BTC|ETH|USDT)(?=\s*(,|마켓|/|\)))", " ", titel)      # Marktnamen, keine Assets
    t = re.sub(r"/(KRW|BTC|ETH|USDT)\b", " ", t)
    k = set(re.findall(r"(?<![A-Za-z0-9])([A-Z0-9]{2,12})(?![A-Za-z0-9])", t))
    return sorted(x for x in k if x in W and x not in BA.QUOTE)


def upbit_markt(titel: str) -> str:
    return "KRW" if re.search(r"KRW|원화", titel) else ""


def schwere(quelle: str, typ: str, markt: str = "") -> str:
    return SCHWERE.get((quelle, typ, markt)) or SCHWERE.get((quelle, typ)) or UNGEMESSEN


def sicht(assets: list, bereich: str) -> str | None:
    return "S7" if assets else SICHT_JE_BEREICH.get(bereich)


# ══ Zeit ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _iso(t: pd.Timestamp) -> str:
    return t.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%S+00:00")


def bekannt_boerse(zeit: pd.Timestamp) -> str:
    return _iso(zeit + pd.Timedelta(hours=LESEVERZUG_H))


def bekannt_nachricht(pub: pd.Timestamp, aufnahme: pd.Timestamp | None) -> str:
    """A1-5: min(Archivaufnahme, Veröffentlichung + 1 h) - nie früher als belegt."""
    k = pub + pd.Timedelta(hours=LESEVERZUG_H)
    if aufnahme is not None and not pd.isna(aufnahme):
        k = min(k, aufnahme)
    return _iso(k)


# ══ Meldungen laden (nur lesend) ═══════════════════════════════════════════════════════════════════════════════════════════════
def _ro(pfad: str) -> sqlite3.Connection:
    if os.path.basename(pfad) == "tradinginfotool.db":
        raise SystemExit("ereignisse liest NIE die Produktions-DB")
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)


def meldungen(quelle: str, pfad: str | None = None) -> pd.DataFrame:
    """Einheitlich: quelle, meldung, zeit (UTC), titel, text, beleg, aufnahme, katalog."""
    c = _ro(pfad or QUELLEN[quelle])
    try:
        if quelle == "binance":
            d = pd.read_sql("SELECT code, katalog, titel, release_ms, text FROM meldung", c)
            from agent import binance_ankuendigungen as BA
            return pd.DataFrame({"quelle": "binance", "meldung": d.code, "zeit": pd.to_datetime(d.release_ms, unit="ms", utc=True),
                                 "titel": d.titel, "text": d.text, "beleg": [BA.LINK % x for x in d.code], "aufnahme": pd.NaT,
                                 "katalog": d.katalog})
        if quelle == "upbit":
            d = pd.read_sql("SELECT id, titel, utc FROM upbit", c)
            return pd.DataFrame({"quelle": "upbit", "meldung": d.id.astype(str), "zeit": pd.to_datetime(d.utc, utc=True), "titel": d.titel,
                                 "text": "", "beleg": ["https://upbit.com/service_center/notice?id=%d" % i for i in d.id],
                                 "aufnahme": pd.NaT, "katalog": 0})
        d = pd.read_sql("SELECT feed, schluessel, titel, link, pub_utc, aufnahme_ts FROM meldung", c)
        return pd.DataFrame({"quelle": "nachricht", "meldung": d.feed + "|" + d.schluessel,
                             "zeit": pd.to_datetime(d.pub_utc, utc=True, errors="coerce"), "titel": d.titel.fillna(""), "text": "",
                             "beleg": d.link, "aufnahme": pd.to_datetime(d.aufnahme_ts, format="%Y%m%d%H%M%S", utc=True, errors="coerce"),
                             "katalog": 0})
    finally:
        c.close()


def vorfilter(titel: str) -> bool:
    return bool(VORFILTER.search(titel or "") or VORFILTER_GROSS.search(titel or ""))


# ══ LLM ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def prompt() -> str:
    defs = "\n".join("- %s: %s" % (k, v) for k, v in TYPEN.items())
    bdefs = "\n".join("- %s: %s" % (k, v) for k, v in BEREICHE.items())
    return ("Du ordnest Krypto- und Wirtschaftsmeldungen ein. Jede nummerierte Meldung FÜR SICH - die anderen Meldungen nicht heranziehen. "
            "Typen (genau einer):\n%s\n"
            "Für JEDE Meldung ein JSON-Objekt {\"nr\": n, \"typ\": \"...\", \"assets\": [Ticker], \"bereich\": \"...\"}. "
            "assets: nur Krypto-Ticker, die die Meldung BETRIFFT (nicht bloß erwähnt; Bitcoin als Beute oder Zahlungsmittel "
            "betrifft BTC nicht), sonst []. "
            "bereich (genau einer):\n%s\n"
            "Keine Bewertung, keine Prognose. Antwort: ein JSON-Array, sonst nichts." % (defs, bdefs))


PROMPT_SHA = hashlib.sha256(prompt().encode("utf-8")).hexdigest()[:12]


def _eingabe(titel: list) -> str:
    return "\n".join("%d. %s" % (i + 1, re.sub(r"\s+", " ", t or "").strip()[:300]) for i, t in enumerate(titel))


def lies_antwort(roh: str, n: int) -> list:
    """Antwort -> n Einträge (typ, assets, bereich); wirft bei falscher Form."""
    j = json.loads(roh[roh.index("["):roh.rindex("]") + 1])
    je = {int(e["nr"]): e for e in j if isinstance(e, dict) and "nr" in e}
    if sorted(je) != list(range(1, n + 1)):
        raise ValueError("nr %s statt 1..%d" % (sorted(je)[:30], n))
    aus = []
    for i in range(1, n + 1):
        e = je[i]
        typ = str(e.get("typ", "")).strip()
        if typ not in TYPEN:
            raise ValueError("typ %r" % typ)
        b = str(e.get("bereich", "sonstiges")).strip()
        aus.append((typ, [str(x) for x in (e.get("assets") or []) if isinstance(x, (str, int))], b if b in BEREICHE else "sonstiges"))
    return aus


def frage(key: str, titel: list, http=None) -> tuple[str, int]:
    """Ein Stapel an Groq; wartet geduldig auf Minuten- und Tageskontingent (wie p67)."""
    import requests
    http = http or requests
    body = {"model": MODELL, "temperature": 0, "reasoning_effort": "low",
            "messages": [{"role": "system", "content": prompt()}, {"role": "user", "content": _eingabe(titel)}]}
    for _ in range(2000):
        try:
            r = http.post(URL, headers={"Authorization": "Bearer %s" % key}, json=body, timeout=180)
        except Exception:                                      # noqa: BLE001 - Netzaussetzer: warten statt abbrechen
            time.sleep(60)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            m = re.search(r"try again in (?:(\d+)h)?(?:(\d+)m)?([\d.]+)s", r.text)
            warte = (int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + float(m.group(3))) if m else \
                float(r.headers.get("retry-after") or 30)
            time.sleep(min(max(warte + 2, 5), 900))
            continue
        r.raise_for_status()
        j = r.json()
        if int(r.headers.get("x-ratelimit-remaining-tokens") or 8000) < 3500:
            time.sleep(20)
        return j["choices"][0]["message"].get("content") or "", int((j.get("usage") or {}).get("total_tokens") or 0)
    raise RuntimeError("Groq: keine Antwort")


# ══ Ablage ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def verbinde(pfad: str = ABLAGE) -> sqlite3.Connection:
    if os.path.basename(pfad) == "tradinginfotool.db":
        raise SystemExit("ereignisse schreibt NIE in die Produktions-DB")
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    c = sqlite3.connect(pfad, timeout=60)
    c.executescript("""
        CREATE TABLE IF NOT EXISTS ereignis (quelle TEXT, meldung TEXT, zeit TEXT, bekannt_ab TEXT, typ TEXT, ereignis INTEGER,
                                             assets TEXT, bereich TEXT, sicht TEXT, schwere TEXT, beleg TEXT, titel TEXT, methode TEXT,
                                             modell TEXT, geholt TEXT, PRIMARY KEY (quelle, meldung));
        CREATE TABLE IF NOT EXISTS llm_antwort (quelle TEXT, meldung TEXT, lauf INTEGER, modell TEXT, prompt_sha TEXT, stapel TEXT,
                                                nr INTEGER, typ TEXT, assets TEXT, bereich TEXT, tokens INTEGER, roh TEXT, am TEXT,
                                                PRIMARY KEY (quelle, meldung, lauf, modell, prompt_sha));""")
    return c


def _jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _zeile(m, typ, assets, bereich, markt, methode, modell=""):
    return (m.quelle, m.meldung, _iso(m.zeit), bekannt_nachricht(m.zeit, m.aufnahme) if m.quelle == "nachricht" else bekannt_boerse(m.zeit),
            typ, int(typ not in KEIN_EREIGNIS), json.dumps(assets), bereich, sicht(assets, bereich), schwere(m.quelle, typ, markt),
            m.beleg, m.titel, methode, modell, _jetzt())


def regel_ereignisse(W: set | None = None) -> tuple[list, pd.DataFrame]:
    """Börsen nach Regeln -> (Zeilen, Rest ohne Regel). Ohne Netz."""
    W = W if W is not None else welt()
    zeilen, rest = [], []
    for q, regeln in (("binance", B_REGELN), ("upbit", U_REGELN)):
        M = meldungen(q)
        for m in M.itertuples(index=False):
            typ = regel(m.titel, regeln)
            if typ is None:
                rest.append(m)
                continue
            a = binance_assets(typ, m.titel, m.text, W) if q == "binance" else upbit_assets(m.titel, W)
            zeilen.append(_zeile(m, typ, a, "asset" if a else "krypto_gesamt", upbit_markt(m.titel) if q == "upbit" else "", "regel"))
    return zeilen, pd.DataFrame(rest)


def schreibe(c: sqlite3.Connection, zeilen: list) -> int:
    c.executemany("INSERT OR REPLACE INTO ereignis VALUES (%s)" % ",".join("?" * 15), zeilen)
    c.commit()
    return len(zeilen)


def llm_offen(W: set | None = None, alle: bool = False, ab: str = NACHRICHT_AB) -> pd.DataFrame:
    """Was das LLM lesen soll, in dieser Reihenfolge: Börsen-Rest · Vorfilter-Treffer (Weg a) · mit ``alle`` die übrigen Nachrichten
    (Weg b). Je Teil zeitlich geordnet - so steht Weg a vollständig, bevor b beginnt."""
    _, rest = regel_ereignisse(W)
    N = meldungen("nachricht")
    N = N[N.zeit.notna() & (N.zeit >= ab)]
    vf = N.titel.map(vorfilter)
    teile = [rest.sort_values("zeit"), N[vf].sort_values("zeit")] + ([N[~vf].sort_values("zeit")] if alle else [])
    return pd.concat(teile, ignore_index=True)


def llm_lauf(c: sqlite3.Connection, M: pd.DataFrame, key: str, lauf: int = 1, stapel: int = STAPEL, protokoll=print) -> dict:
    """Je Quelle zeitlich geordnet in Stapeln; bereits beantwortete (gleicher Lauf, Modell, Prompt) werden übersprungen."""
    da = {(q, m) for q, m in c.execute("SELECT quelle, meldung FROM llm_antwort WHERE lauf=? AND modell=? AND prompt_sha=?",
                                        (lauf, MODELL, PROMPT_SHA))}
    offen = M[[(q, m) not in da for q, m in zip(M.quelle, M.meldung)]]
    tok = fehl = 0
    for q, G in offen.groupby("quelle", sort=False):
        for i in range(0, len(G), stapel):
            T = G.iloc[i:i + stapel]
            sid = hashlib.sha256(_eingabe(list(T.titel)).encode("utf-8")).hexdigest()[:12]
            for versuch in range(3):
                roh, t = frage(key, list(T.titel))
                tok += t
                try:
                    aus = lies_antwort(roh, len(T))
                    break
                except Exception as e:                         # noqa: BLE001
                    fehl += 1
                    protokoll("  Form ungültig (%s), Versuch %d" % (str(e)[:80], versuch + 1))
            else:
                aus = [("unlesbar", [], "sonstiges")] * len(T)
            c.executemany("INSERT OR REPLACE INTO llm_antwort VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          [(m.quelle, m.meldung, lauf, MODELL, PROMPT_SHA, sid, k + 1, a[0], json.dumps(a[1]), a[2], t, roh, _jetzt())
                           for k, (m, a) in enumerate(zip(T.itertuples(index=False), aus))])
            c.commit()
            protokoll("%s %s Stapel %d/%d · %d Token" % (_jetzt()[:19], q, i // stapel + 1, (len(G) + stapel - 1) // stapel, t))
    return {"gefragt": len(offen), "token": tok, "formfehler": fehl}


def llm_ereignisse(c: sqlite3.Connection, M: pd.DataFrame, W: set | None = None, lauf: int = 1) -> list:
    """Antworten aus ``llm_antwort`` -> Ereigniszeilen (Assets gegen Universum/Alias)."""
    W = W if W is not None else welt()
    A = alias()
    L = pd.read_sql("SELECT quelle, meldung, typ, assets, bereich FROM llm_antwort WHERE lauf=? AND modell=? AND prompt_sha=?", c,
                    params=(lauf, MODELL, PROMPT_SHA)).set_index(["quelle", "meldung"])
    zeilen = []
    for m in M.itertuples(index=False):
        if (m.quelle, m.meldung) not in L.index:
            continue
        r = L.loc[(m.quelle, m.meldung)]
        a = assets_pruefen(json.loads(r.assets), m.titel, W, A)
        b = r.bereich if not (a and r.bereich == "sonstiges") else "asset"
        zeilen.append(_zeile(m, r.typ, a, b, upbit_markt(m.titel) if m.quelle == "upbit" else "", "llm", MODELL))
    return zeilen


# ══ Lesen am Stichtag (für die Sichten) ═══════════════════════════════════════════════════════════════════════════════════════
def lade(pfad: str = ABLAGE) -> pd.DataFrame:
    c = _ro(pfad)
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='ereignis'").fetchone():
            return pd.DataFrame(columns=["quelle", "meldung", "zeit", "bekannt_ab", "typ", "ereignis", "assets", "bereich", "sicht",
                                         "schwere", "beleg", "titel", "methode", "modell"])
        return pd.read_sql("SELECT * FROM ereignis", c)
    finally:
        c.close()


def am(E: pd.DataFrame, T: str, tage: int = FENSTER_T, assets=None) -> pd.DataFrame:
    """Ereignisse, die am Stichtag T BEKANNT sind (``bekannt_ab ≤ T``, P5) und höchstens ``tage`` alt; nur echte Ereignisse.
    Mit ``assets`` (z. B. Watchlist): ein BÖRSEN-Ereignis gilt nur für beobachtete Assets (S7) - ein Listing oder Delisting fremder Werte
    ist für die Marktsicht Rauschen und entfällt. Ein Nachrichten-Ereignis zu einem fremden Asset geht an S1 (Krypto allgemein)."""
    t = pd.Timestamp(T)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    ab = _iso(t - pd.Timedelta(days=tage))
    x = E[(E.bekannt_ab <= _iso(t)) & (E.bekannt_ab > ab) & (E.ereignis == 1)].copy()
    x["assets_alle"] = x.assets
    if assets is not None:
        s = {a.upper() for a in assets}
        x["assets"] = [json.dumps([a for a in json.loads(v) if a in s]) for v in x.assets]
        x["sicht"] = [("S7" if json.loads(a) else None if q != "nachricht" else
                       SICHT_JE_BEREICH.get("krypto_gesamt" if b == "asset" else b)) for a, b, q in zip(x.assets, x.bereich, x.quelle)]
    return x[x.sicht.notna()].sort_values("bekannt_ab")


def zeilen(x: pd.DataFrame, sicht_: str, T: str) -> list[str]:
    """Fütterung §3: Zeit · Asset oder Bereich · Typ · Schwere · neu seit · Beleg · Ereignis. Gleiches (Typ, Assets) nur einmal, mit Zahl."""
    t = pd.Timestamp(T)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    aus = []
    for (typ, a), g in x[x.sicht == sicht_].groupby(["typ", "assets"], sort=False):
        e = g.iloc[0]
        h = (t - pd.Timestamp(e.bekannt_ab)).total_seconds() / 3600
        wer = ", ".join(json.loads(a)) or ", ".join(json.loads(e.assets_alle)) or e.bereich
        n = " (%d Meldungen)" % len(g) if len(g) > 1 else ""
        aus.append("[%s] %s UTC · %s · %s · Schwere: %s · neu seit %s · %s%s · Ereignis" % (
            sicht_, e.zeit[:16].replace("T", " "), wer, typ, e.schwere, ("%.0f h" % h) if h < 48 else ("%.1f T" % (h / 24)), e.beleg, n))
    return aus


# ══ Ablauf ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                          # noqa: BLE001
        pass
    p = argparse.ArgumentParser()
    p.add_argument("--regeln", action="store_true")
    p.add_argument("--llm", action="store_true")
    p.add_argument("--schreibe", action="store_true", help="nur die vorhandenen LLM-Antworten als Ereignisse schreiben (ohne Netz)")
    p.add_argument("--stand", action="store_true")
    p.add_argument("--pfad", default=ABLAGE)
    o = p.parse_args()
    c = verbinde(o.pfad)
    W = welt()
    if o.regeln:
        z, rest = regel_ereignisse(W)
        print("Regeln: %d Ereignisse geschrieben, Rest für das LLM %d" % (schreibe(c, z), len(rest)))
    if o.llm or o.schreibe:
        M = llm_offen(W, alle=(WEG == "b"))
        print("LLM: %d Meldungen (Börsen-Rest, Vorfilter-Treffer%s), Prompt %s" % (len(M), ", übrige Nachrichten" * (WEG == "b"),
                                                                                 PROMPT_SHA))
        if o.llm:
            from dotenv import dotenv_values
            key = dotenv_values(os.path.join(PROJ, ".env")).get("GROQ_API_KEY")
            print(llm_lauf(c, M, key, protokoll=lambda s: print(s, flush=True)))
        print("LLM: %d Ereignisse geschrieben" % schreibe(c, llm_ereignisse(c, M, W)))
    if o.stand or not (o.regeln or o.llm or o.schreibe):
        print(pd.read_sql("SELECT quelle, methode, typ, COUNT(*) n FROM ereignis GROUP BY 1,2,3 ORDER BY 1,2,4 DESC", c).to_string())
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
