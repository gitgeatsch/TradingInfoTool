"""P66c Kontamination ueber EREIGNISWISSEN (19.10.2026, Schritt7 §23.73) - fuer ein Nachrichten-Rueckspiel zaehlt, ob ein Modell die
Ereignisse kennt, nicht nur Kurse (gpt-oss verweigert Kursangaben grundsaetzlich).

    python Basisinfos/Rechenkern_02_10/p66_ereignis_probe.py

7 Fragen (2 Kontrollen 2024, 5 Tests 2025-26) an 4 kostenfreie Modelle, Temperatur 0. Die richtige Antwort wird NICHT aus meinem Gedaechtnis
vorgegeben, sondern je Frage mit den Schlagzeilen des eigenen Archivs (data/_lc/nachrichten.db) im Fenster belegt (Kontrollen 2024:
Archiv beginnt 12/2024 - dort gilt die allgemein belegte Tatsache). Bewertung von Hand in der Doku.
"""
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
FRAGEN = [
    ("Kontrolle", "An welchem Datum genehmigte die US-SEC die ersten Spot-Bitcoin-ETFs?", None, None, None),
    ("Kontrolle", "In welchem Monat und Jahr fand das vierte Bitcoin-Halving statt?", None, None, None),
    ("Test", "Welche Kryptoboerse wurde im Februar 2025 um rund 1,5 Milliarden US-Dollar gehackt?", "2025-02-20", "2025-02-24", r"hack|exploit"),
    ("Test", "Was loeste Anfang April 2025 den starken Kursrutsch an Aktien- und Kryptomaerkten aus?", "2025-04-02", "2025-04-08", r"tariff|crash|plunge"),
    ("Test", "Was geschah am 10. und 11. Oktober 2025 am Kryptomarkt, und was war der Ausloeser?", "2025-10-10", "2025-10-12", r"liquidat|crash|tariff"),
    ("Test", "Was geschah Mitte Dezember 2025 am Kryptomarkt?", "2025-12-12", "2025-12-18", r"crash|plunge|fall|drop|liquidat|fed|rate"),
    ("Test", "Was geschah am 3. und 4. Juni 2026 am Kryptomarkt?", "2026-06-03", "2026-06-05", r"crash|plunge|fall|drop|liquidat|tumble|sell"),
]
MODELLE = [("gemini", "gemini-3.5-flash-lite"), ("groq", "openai/gpt-oss-120b"), ("groq", "qwen/qwen3.8-27b"), ("mistral", "ministral-8b-2512")]
URL = {"groq": ("https://api.groq.com/openai/v1", K.get("GROQ_API_KEY")), "mistral": ("https://api.mistral.ai/v1", K.get("MISTRAL_API_KEY"))}
c = sqlite3.connect("file:data/_lc/nachrichten.db?mode=ro", uri=True)
M = pd.read_sql("SELECT titel, pub_utc FROM meldung WHERE pub_utc IS NOT NULL", c, parse_dates=["pub_utc"]).drop_duplicates("titel")
c.close()
print("P66c EREIGNIS-PROBE\n")


def frage(anb, modell, text):
    msg = [{"role": "user", "content": text + " Antworte in hoechstens zwei Saetzen. Wenn du es nicht weisst, sage nur 'unbekannt'."}]
    if anb == "gemini":
        from api.gemini import GeminiClient
        return GeminiClient(K.get("GEMINI_API_KEY")).chat(msg, model=modell, temperature=0.0)
    u, key = URL[anb]
    j = requests.post(u + "/chat/completions", headers={"Authorization": "Bearer %s" % key}, json={"model": modell, "messages": msg, "temperature": 0.0},
                      timeout=120).json()
    return j["choices"][0]["message"].get("content") if "choices" in j else "FEHLER %s" % str(j)[:100]


for art, text, a, e, muster in FRAGEN:
    print("=" * 110)
    print("%s: %s" % (art, text))
    if a:
        X = M[(M.pub_utc >= a) & (M.pub_utc < e)]
        X = X[X.titel.str.contains(muster, case=False, regex=True, na=False)]
        print("   ARCHIV %s..%s (%d passende Titel), Beispiele:" % (a, e, len(X)))
        for t in X.titel.head(5):
            print("     - %s" % t[:130])
    for anb, modell in MODELLE:
        try:
            ant = frage(anb, modell, text)
        except Exception as exc:  # noqa: BLE001
            ant = "FEHLER %s" % exc
        print("   %-24s %s" % (modell[:24], re.sub(r"\s+", " ", str(ant))[:260]))
        time.sleep(2)
