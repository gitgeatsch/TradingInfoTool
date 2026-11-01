"""Voranalyse A1: Regelentwurf auf Binance (6.276), Upbit (785) und Nachrichten (39.929) - Abdeckung, Rest fuer das LLM, Token. Nur lesend."""
import re
import sqlite3
import pandas as pd

P = "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool/data/"
B_REGELN = [  # (typ, muster) - erste passende gewinnt; Reihenfolge = Vorrang
    ("monitoring_ende", r"(?i)remove .*monitoring tag|monitoring tag.*remov"),
    ("monitoring", r"(?i)monitoring tag"),
    ("delisting_futures", r"(?i)futures will (delist|close)|delist .*perpetual"),
    ("delisting_margin", r"(?i)margin will delist"),
    ("delisting_token", r"(?i)^binance will delist|will cease trading"),
    ("paar_entfernt", r"(?i)removal of (spot )?trading pairs"),
    ("alpha_entfernt", r"(?i)alpha will remove"),
    ("depeg_warnung", r"(?i)depeg|price deviation|suspend(s|ed)? (deposits|withdrawals|trading)|halt"),
    ("verschoben", r"(?i)postpone|delay"),
    ("listing_futures", r"(?i)futures will launch|perpetual contract"),
    ("listing_spot", r"(?i)^binance will list|adds .* trading pairs?|on binance (launchpool|hodler airdrops|megadrop)|will be available on binance"),
    ("listing_alpha", r"(?i)binance alpha"),
    ("margin_neu", r"(?i)margin will add|margin adds"),
    ("netz_upgrade", r"(?i)network upgrade|hard fork|wallet maintenance|token (swap|merge|migration)|redenomination|rebrand|contract swap"),
    ("airdrop", r"(?i)airdrop"),
    ("aktion", r"(?i)competition|rewards?|share|prize|promotion|campaign|giveaway|quiz|voucher|learn & earn|earn "),
    ("produkt", r"(?i)convert|tick size|leverage|margin tiers|options|api|copy trading|trading bots?|earn|simple earn|loan|pay|card|launch"),
]
U_REGELN = [
    ("delisting_token", r"거래지원 종료"),
    ("monitoring_ende", r"유의 종목 지정 해제|유의 촉구 해제"),
    ("monitoring", r"유의 종목 지정|투자 유의|유의 촉구"),
    ("listing_spot", r"신규 거래지원|디지털 자산 추가|마켓 (오픈|추가)|코인 추가"),
    ("netz_upgrade", r"네트워크 업그레이드|하드포크|입출금|스왑|리브랜딩|토큰 변경|메인넷"),
    ("airdrop", r"에어드랍"),
]


def regel(titel, regeln):
    for typ, m in regeln:
        if re.search(m, titel):
            return typ
    return "rest"


c = sqlite3.connect("file:%s_a1/binance_ankuendigungen_alle.db?mode=ro" % P, uri=True)
b = pd.read_sql("SELECT katalog, titel, release_ms FROM meldung", c)
b["typ"] = [regel(t, B_REGELN) for t in b.titel]
print("BINANCE %d Meldungen - Typ je Katalog:" % len(b))
print(pd.crosstab(b.typ, b.katalog, margins=True).to_string())
print("Rest-Beispiele:", b[b.typ == "rest"].titel.sample(min(10, (b.typ == "rest").sum()), random_state=1).str[:90].tolist())
u = pd.read_sql("SELECT titel, utc FROM upbit", sqlite3.connect("file:%s_c2/ankuendigungen.db?mode=ro" % P, uri=True))
u["typ"] = [regel(t, U_REGELN) for t in u.titel]
print("\nUPBIT %d Meldungen:" % len(u), u.typ.value_counts().to_dict())
print("Rest-Beispiele:", u[u.typ == "rest"].titel.sample(min(8, (u.typ == "rest").sum()), random_state=1).str[:60].tolist())
n = pd.read_sql("SELECT feed, titel, beschreibung, pub_utc FROM meldung", sqlite3.connect("file:%s_lc/nachrichten.db?mode=ro" % P, uri=True))
n["pub"] = pd.to_datetime(n.pub_utc, utc=True, errors="coerce")
r = n[(n.pub >= "2025-12-01") & (n.pub < "2026-10-17")].copy()
r["zeichen"] = r.titel.fillna("").str.len() + r.beschreibung.fillna("").str.len()
print("\nNACHRICHTEN Rueckspielfenster 01.12.2025-16.10.2026: %d Meldungen, %d je Tag (Median), Zeichen je Meldung Median %d, P90 %d"
      % (len(r), r.groupby(r.pub.dt.date).size().median(), r.zeichen.median(), r.zeichen.quantile(0.9)))
r["norm"] = r.titel.fillna("").str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.split().str[:8].str.join(" ")
print("gleicher Titelanfang (8 Woerter) in mehreren Feeds: %d Dubletten" % (len(r) - r.norm.nunique()))
tok = r.zeichen.sum() / 3.75 + len(r) * 120          # +120 Token Anweisung/Antwort je Meldung, wenn einzeln
print("LLM alles einzeln: ~%.1f Mio Token = %.0f Tage bei 200.000 Token/Tag (Groq)" % (tok / 1e6, tok / 200000))
print("Typ-Regeln auf Nachrichtentitel (Binance-Muster, nur zur Groesse):", pd.Series([regel(t, B_REGELN) for t in r.titel.fillna("")]).value_counts().head(8).to_dict())
