"""A1 zweiter Weg (04.11.): flash-lite gegen gpt-oss-120b auf denselben Titeln, Prompt 3. Nur lesend (mode=ro), ohne Netz.
Reproduziert zuerst den 02.11.-Stand (Nachrichten 84 %, Binance-Rest 83 % Sicht relevant gleich), dann der volle Überschnitt."""
import json, os, sqlite3, sys
from collections import Counter
PROJ = r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool"
sys.path.insert(0, PROJ)
import pandas as pd
from agent import ereignisse as E

c = sqlite3.connect("file:%s?mode=ro" % E.ABLAGE.replace("\\", "/"), uri=True)
L = pd.read_sql("SELECT quelle, meldung, modell, typ, assets, bereich, am AS geholt FROM llm_antwort WHERE lauf=1 AND prompt_sha=?", c,
                params=(E.PROMPT_SHA,))
print("Prompt", E.PROMPT_SHA, "| Antworten je Modell:", L.groupby("modell").size().to_dict())
W, A = E.welt(), E.alias()
M = E.llm_offen(W, alle=True).set_index(["quelle", "meldung"])
M = M[~M.index.duplicated()]

def bewerte(r):
    if r.typ == "unlesbar":
        return None
    t = M.titel.get((r.quelle, r.meldung), "")
    a = E.assets_pruefen(json.loads(r.assets), t, W, A)
    b = r.bereich if not (a and r.bereich == "sonstiges") else "asset"
    s = E.sicht(a, b) if r.typ not in E.KEIN_EREIGNIS else None
    return (r.typ, s, tuple(sorted(a)))

L["wert"] = [bewerte(r) for r in L.itertuples(index=False)]
G = L[L.modell == "openai/gpt-oss-120b"].set_index(["quelle", "meldung"])
F = L[L.modell == E.MODELL].set_index(["quelle", "meldung"])
gem = G.index.intersection(F.index)
print("gemeinsame Titel", len(gem), "| gpt-oss unlesbar", int(G.typ.eq("unlesbar").sum()), "| flash-lite unlesbar auf gem.",
      int(F.loc[gem].typ.eq("unlesbar").sum()))

def teil(name, idx):
    z = Counter()
    for k in idx:
        g, f = G.wert[k], F.wert[k]
        if g is None or f is None:
            z["unlesbar"] += 1; continue
        z["n"] += 1
        rg, rf = g[1] is not None, f[1] is not None
        z["rel_gleich"] += rg == rf
        z["nur_gemini"] += rf and not rg
        z["nur_gptoss"] += rg and not rf
        z["beide_rel"] += rg and rf
        z["beide_rel_sicht_gleich"] += rg and rf and g[1] == f[1]
        z["typ_gleich"] += g[0] == f[0]
        z["asset_gleich_bei_beide_rel"] += rg and rf and g[2] == f[2]
    n = z["n"] or 1
    print("%-26s n %5d (unlesbar %d) | Sicht relevant gleich %5.1f %% | nur Gemini %4d | nur gpt-oss %4d | beide relevant %4d, "
          "gleiche Sicht %5.1f %%, gleiche Assets %5.1f %% | Typ gleich %5.1f %%" % (
              name, z["n"], z["unlesbar"], 100 * z["rel_gleich"] / n, z["nur_gemini"], z["nur_gptoss"], z["beide_rel"],
              100 * z["beide_rel_sicht_gleich"] / max(z["beide_rel"], 1), 100 * z["asset_gleich_bei_beide_rel"] / max(z["beide_rel"], 1),
              100 * z["typ_gleich"] / n))
    return z

# R-R11: 02.11.-Stand nachbilden = die flash-lite-Antworten, die bis zur Gegenprobe am 02.11. vorlagen
print("\n-- 1. Reproduktion 02.11. (flash-lite geholt am 02.11.) --")
frueh = [k for k in gem if str(F.geholt[k]) < "2026-11-03"]
for q in ("nachricht", "binance"):
    teil("02.11. " + q, [k for k in frueh if k[0] == q])
print("\n-- 2. voller Ueberschnitt --")
for q in sorted({k[0] for k in gem}):
    teil(q, [k for k in gem if k[0] == q])
teil("ALLE", list(gem))
# Zuordnung nach Teil (Boersen-Rest / Vorfilter / uebrige Nachrichten)
vf = {k: E.vorfilter(M.titel.get(k, "")) for k in gem if k[0] == "nachricht"}
print("\n-- 3. Nachrichten nach Vorfilter --")
teil("Vorfilter-Treffer", [k for k, v in vf.items() if v])
teil("uebrige", [k for k, v in vf.items() if not v])

print("\n-- 4. Reproduktion 02.11. eng: die ersten 250 Nachrichten-Antworten von flash-lite --")
fn = F.loc[[k for k in gem if k[0] == "nachricht"]].sort_values("geholt")
teil("erste 250 Nachrichten", list(fn.index[:250]))
print("flash-lite Antworten gesamt nach Teil:", Counter("boerse" if k[0] != "nachricht" else ("vorfilter" if E.vorfilter(M.titel.get(k, "")) else "uebrige") for k in F.index))
rel = Counter()
for k in F.index:
    w = F.wert[k]
    if w is None: continue
    t = "boerse" if k[0] != "nachricht" else ("vorfilter" if E.vorfilter(M.titel.get(k, "")) else "uebrige")
    rel[(t, w[1] is not None)] += 1
print("flash-lite relevant je Teil:", dict(rel))
