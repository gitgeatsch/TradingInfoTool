"""Phase 1: Erreichbarkeit aller :free-Modelle unter den AKTUELLEN Privacy-
Schaltern. Reproduziert die Messung vom 07.08. abends - kurze Frage, damit der
Befund vergleichbar ist. Keine DB, kein Schreibzugriff."""
import json, os, time
from dotenv import load_dotenv
load_dotenv()
import requests

key = os.environ["OPENROUTER_API_KEY"]
ids = [i for i in json.load(open("free_ids.json")) if i.endswith(":free")]
h = {"Authorization": f"Bearer {key}", "HTTP-Referer": "https://github.com/gitgeatsch/TradingInfoTool", "X-Title": "TradingInfoTool"}
frage = [{"role": "user", "content": "Antworte mit genau einem Wort: wie viel ist 2+2?"}]

print(f"{len(ids)} Modelle mit :free-Suffix\n")
res = {}
for i in ids:
    t = time.monotonic()
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          json={"model": i, "messages": frage, "temperature": 0.3},
                          headers=h, timeout=60)
        d = time.monotonic() - t
        if r.status_code == 200:
            txt = r.json()["choices"][0]["message"]["content"][:30].replace("\n", " ")
            res[i] = ("OK", d, txt)
        else:
            grund = r.json().get("error", {}).get("message", r.text)[:90]
            res[i] = (str(r.status_code), d, grund)
    except Exception as e:
        res[i] = ("EXC", time.monotonic() - t, str(e)[:90])
    st, d, info = res[i]
    print(f"  {st:<5} {d:>6.1f}s  {i:<52} {info}")
    time.sleep(3)

json.dump({k: v[0] for k, v in res.items()}, open("probe1.json", "w"))
print("\nZUSAMMENFASSUNG")
for st in sorted({v[0] for v in res.values()}):
    treffer = [k for k, v in res.items() if v[0] == st]
    print(f"  {st:<5} {len(treffer):>2}x  {', '.join(t.split('/')[-1] for t in treffer)}")
