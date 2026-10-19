"""P66b Wissenshorizont der kostenfreien LLMs (19.10.2026, Schritt7 §23.73). Nur Testfragen, keine Messung.

    python Basisinfos/Rechenkern_02_10/p66_horizont.py

Je Modell eine erzwungene Schaetzung des BTC-Schlusskurses (Temperatur 0) an Stichtagen 2023-06 bis 2026-02. 'Kennt' = Fehler < 5 %;
zum Vergleich der Fehler, den ein Modell haette, das nur den Kurs 3 Monate vorher kennt (Fortschreibung) - liegt die Schaetzung deutlich
darunter, zeigt sie Wissen ueber den Stichtag. Modelllisten (Groq, Cerebras, Mistral) nur abgefragt, nicht benutzt.
"""
import json
import os
import re
import sqlite3
import sys
import time

import pandas as pd
import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
from dotenv import dotenv_values  # noqa: E402

K = dotenv_values(".env")
TAGE = ("2023-06-15", "2024-03-14", "2024-09-15", "2024-12-15", "2025-02-15", "2025-04-07", "2025-06-15", "2025-08-15", "2025-10-10",
        "2025-12-15", "2026-02-15")
cm = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
btc = pd.read_sql("SELECT tag, PriceUSD FROM tag WHERE asset='btc'", cm, parse_dates=["tag"]).set_index("tag").PriceUSD
cm.close()
ANBIETER = {"groq": ("https://api.groq.com/openai/v1", K.get("GROQ_API_KEY")),
            "cerebras": ("https://api.cerebras.ai/v1", K.get("CEREBRAS_API_KEY")),
            "mistral": ("https://api.mistral.ai/v1", K.get("MISTRAL_API_KEY"))}
print("P66b WISSENSHORIZONT\n")
for n, (url, key) in ANBIETER.items():
    try:
        r = requests.get(url + "/models", headers={"Authorization": "Bearer %s" % key}, timeout=60)
        ids = sorted(m["id"] for m in r.json().get("data", []))
        print("%-9s Modelle (%d): %s" % (n, len(ids), ", ".join(ids[:40])))
    except Exception as exc:  # noqa: BLE001
        print("%-9s Modellliste nicht abrufbar: %s" % (n, exc))


def frage(anb, modell, d):
    text = ("Schaetze den Bitcoin-Schlusskurs in USD am %s (UTC). Du MUSST eine Zahl nennen, auch wenn du unsicher bist. "
            "Antworte nur als JSON {\"btc_usd\": Zahl}." % d)
    if anb == "gemini":
        from api.gemini import GeminiClient
        a = GeminiClient(K.get("GEMINI_API_KEY")).chat([{"role": "user", "content": text}], model=modell, temperature=0.0)
    else:
        url, key = ANBIETER[anb]
        r = requests.post(url + "/chat/completions", headers={"Authorization": "Bearer %s" % key},
                          json={"model": modell, "messages": [{"role": "user", "content": text}], "temperature": 0.0}, timeout=120)
        j = r.json()
        if "choices" not in j:
            raise ValueError("Antwort ohne choices: %s" % str(j)[:120])
        a = j["choices"][0]["message"]["content"]
    return float(json.loads(re.search(r"\{.*?\}", a, re.S).group(0))["btc_usd"])


KANDIDATEN = [("gemini", "gemini-3.5-flash-lite"), ("groq", "openai/gpt-oss-120b"), ("groq", "qwen/qwen3.8-27b"), ("mistral", "ministral-8b-2512")]
if len(sys.argv) > 1 and sys.argv[1] == "--ohne-gemini":                 # Gemini ist im ersten Lauf schon gemessen (Kontingent schonen)
    KANDIDATEN = KANDIDATEN[1:]
for anb, modell in KANDIDATEN:
    print("\n%s / %s" % (anb, modell))
    for d in TAGE:
        echt = float(btc.asof(pd.Timestamp(d)))
        fort = float(btc.asof(pd.Timestamp(d) - pd.Timedelta(days=91)))
        try:
            g = frage(anb, modell, d)
            f = abs(g / echt - 1)
            print("   %s  echt %8.0f · Schaetzung %8.0f · Fehler %5.1f %% · Fortschreibung 3 M %5.1f %% · %s" % (
                d, echt, g, 100 * f, 100 * abs(fort / echt - 1), "KENNT" if f < 0.05 else ("naeher als Fortschreibung" if f < abs(fort / echt - 1) - 0.03 else "-")))
        except Exception as exc:  # noqa: BLE001
            print("   %s  keine Antwort (%s)" % (d, str(exc)[:90]))
        time.sleep(2)
