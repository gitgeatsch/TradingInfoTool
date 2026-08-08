"""Endpunkt-Ebene aller freien Modelle. Nur LESEN, keine Chat-Calls.

Warum das die bisher fehlende Ebene ist: /api/v1/models liefert das MODELL
(Kontextfenster, Preis). Hinter einem Modell stehen aber ein oder mehrere
UPSTREAM-ANBIETER, und deren Eigenschaften entscheiden ueber Tempo, Limits und
Datenpolitik. Genau dort muessten die 404 ("data policy") und die 24-s-Timeouts
sichtbar werden.
"""
import json

import requests

frei = [i for i in json.load(open("free_ids.json"))]
zeilen = []
for mid in frei:
    slug = mid.split(":")[0]
    try:
        r = requests.get(f"https://openrouter.ai/api/v1/models/{slug}/endpoints", timeout=30)
        d = r.json().get("data") or {}
    except Exception as exc:  # noqa: BLE001
        print(f"{mid}: FEHLER {exc}")
        continue
    for e in d.get("endpoints", []):
        zeilen.append({
            "modell": mid,
            "anbieter": e.get("provider_name"),
            "kontext": e.get("context_length"),
            "max_out": e.get("max_completion_tokens"),
            "quantisierung": e.get("quantization"),
            "uptime": (e.get("uptime_last_30m") if e.get("uptime_last_30m") is not None
                       else e.get("stats", {}).get("uptime")),
            "status": e.get("status"),
            "params": e.get("supported_parameters") or [],
        })

json.dump(zeilen, open("endpoints.json", "w"), ensure_ascii=False, indent=1)
print(f"{len(zeilen)} Endpunkte ueber {len(frei)} Modelle\n")
print(f'{"Modell":<50}{"Upstream":<20}{"Kontext":>9}{"max_out":>9}{"up%":>7}  rf')
for z in sorted(zeilen, key=lambda x: (-(x["kontext"] or 0))):
    rf = "ja" if "response_format" in z["params"] else "NEIN"
    up = f'{z["uptime"]:.0f}' if isinstance(z["uptime"], (int, float)) else "-"
    print(f'{z["modell"]:<50}{str(z["anbieter"]):<20}{(z["kontext"] or 0):>9,}'
          f'{(z["max_out"] or 0):>9,}{up:>7}  {rf}')
