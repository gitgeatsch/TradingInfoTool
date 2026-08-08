"""Nur LESEN: Kontostatus + aktueller Free-Katalog von OpenRouter.
Keine DB, keine Schreibzugriffe, keine Chat-Calls."""
import os, json
from dotenv import load_dotenv
load_dotenv()
import requests

key = os.environ["OPENROUTER_API_KEY"]
h = {"Authorization": f"Bearer {key}"}

k = requests.get("https://openrouter.ai/api/v1/key", headers=h, timeout=30).json()["data"]
print("KONTO")
for f in ("is_free_tier", "usage", "limit", "limit_remaining", "rate_limit"):
    print(f"  {f:<16} {k.get(f)}")

m = requests.get("https://openrouter.ai/api/v1/models", timeout=30).json()["data"]
frei = [x for x in m if float(x["pricing"]["prompt"]) == 0 and float(x["pricing"]["completion"]) == 0]
print(f"\nKATALOG: {len(m)} Modelle gesamt, {len(frei)} mit Preis 0")
frei.sort(key=lambda x: -x.get("context_length", 0))
for x in frei:
    print(f"  {x['id']:<52} {x.get('context_length',0):>9,} Kontext")
json.dump([x["id"] for x in frei], open("free_ids.json", "w"))
