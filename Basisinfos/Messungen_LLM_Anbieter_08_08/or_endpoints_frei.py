"""KORREKTUR zum vorigen Lauf: die Endpunkte muessen MIT `:free`-Suffix
abgefragt werden. Ohne Suffix antwortet die BEZAHLTE Variante - dort stehen
bis zu 17 Upstream-Anbieter, was den Eindruck erweckt, es gaebe eine
Routing-Wahl. Fuer die freien Varianten gilt das nicht.

Nur LESEN, keine Chat-Calls.
"""
import json

import requests

frei = [i for i in json.load(open("free_ids.json")) if i.endswith(":free")]
print(f'{"Modell":<50}{"Upstream":<20}{"Kontext":>9}{"max_out":>9}{"up30m":>7}  rf')
gesamt = {}
for mid in frei:
    try:
        d = requests.get(f"https://openrouter.ai/api/v1/models/{mid}/endpoints",
                         timeout=30).json().get("data") or {}
    except Exception as exc:  # noqa: BLE001
        print(f"{mid:<50}FEHLER {exc}")
        continue
    eps = d.get("endpoints", [])
    gesamt[mid] = [(e.get("provider_name"), e.get("uptime_last_30m")) for e in eps]
    for e in eps:
        rf = "ja" if "response_format" in (e.get("supported_parameters") or []) else "NEIN"
        up = e.get("uptime_last_30m")
        print(f'{mid:<50}{str(e.get("provider_name")):<20}'
              f'{(e.get("context_length") or 0):>9,}{(e.get("max_completion_tokens") or 0):>9,}'
              f'{(f"{up:.0f}" if isinstance(up,(int,float)) else "-"):>7}  {rf}')

anzahl = {m: len(v) for m, v in gesamt.items()}
print(f"\nEndpunkte je freiem Modell: {sorted(set(anzahl.values()))}")
print(f"Modelle mit mehr als einem Endpunkt: "
      f"{[m for m, n in anzahl.items() if n > 1] or 'KEINES'}")
json.dump(gesamt, open("endpoints_frei.json", "w"), ensure_ascii=False, indent=1)
