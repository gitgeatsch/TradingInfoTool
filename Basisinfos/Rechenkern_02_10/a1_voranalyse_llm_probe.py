"""Voranalyse A1: Probelauf gpt-oss-120b (Groq) auf 2 x 25 Nachrichtentiteln - Token, Zeit, Formtreue. Nur lesend; Ausgabe in den Scratchpad."""
import json
import os
import sqlite3
import time

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.env")
TYPEN = ["delisting", "listing", "hack_exploit", "depeg", "regulierung_klage", "etf_fonds", "makro_zentralbank", "unternehmen_kauf",
         "netz_upgrade", "token_freigabe", "partnerschaft", "marktbericht_kurs", "meinung_analyse", "sonstiges"]
SYSTEM = ("Du ordnest Krypto-Nachrichten ein. Fuer JEDE nummerierte Meldung genau ein JSON-Objekt: "
          '{"nr": n, "typ": einer aus %s, "assets": [Ticker, nur wenn die Meldung ein bestimmtes Asset BETRIFFT], '
          '"bereich": "asset"|"krypto_gesamt"|"makro_usa"|"aktien_kredit"|"asien"|"sonstiges", "ereignis": true|false '
          '(false = Kursbericht, Meinung, Prognose, Werbung - kein neues Geschehen)}. Keine Bewertung, keine Prognose. '
          'Antwort: ein JSON-Array, sonst nichts.' % TYPEN)
n = pd.read_sql("SELECT feed, titel, pub_utc FROM meldung WHERE pub_utc >= '2025-12-01' AND pub_utc < '2026-10-17'",
                sqlite3.connect("file:D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool/data/_lc/nachrichten.db?mode=ro", uri=True))
probe = n.sample(50, random_state=11).reset_index(drop=True)
aus, stat = [], []
for teil in (probe.iloc[:25], probe.iloc[25:]):
    text = "\n".join("%d. %s" % (i + 1, t) for i, t in enumerate(teil.titel))
    t0 = time.time()
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]},
                      json={"model": "openai/gpt-oss-120b", "temperature": 0, "messages": [
                          {"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]}, timeout=120)
    j = r.json()
    inhalt = j["choices"][0]["message"]["content"] if r.status_code == 200 else ""
    try:
        erg = json.loads(inhalt[inhalt.index("["):inhalt.rindex("]") + 1])
        ok = len(erg) == len(teil) and all(e.get("typ") in TYPEN for e in erg)
    except Exception:  # noqa: BLE001
        erg, ok = [], False
    stat.append((r.status_code, j.get("usage", {}), round(time.time() - t0, 1), ok, len(erg)))
    for t, e in zip(teil.titel, erg):
        aus.append((t[:80], e.get("typ"), e.get("ereignis"), e.get("bereich"), e.get("assets")))
for s in stat:
    print("HTTP %s · Token %s · %.1f s · Form gueltig %s (%d Objekte)" % s)
d = pd.DataFrame(aus, columns=["titel", "typ", "ereignis", "bereich", "assets"])
print(d.typ.value_counts().to_dict(), "· ereignis=true:", int(d.ereignis.sum()))
d.to_csv(r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\Basisinfos\Rechenkern_02_10\a1_voranalyse_llm_probe_standard.csv", index=False)
print(d.head(50).to_string())
