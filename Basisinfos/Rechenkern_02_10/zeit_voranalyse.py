"""Voranalyse LAUFZEIT verkürzen (Nutzer 02.11.: *„Ja bitte prüfen für eine saubere verkürzung der Zeit. Vor allem finde ich es seltsam
dass wir hier auf die alte Groq Schiene setzen müssen.“*) — Voranalyse_Laufzeit_02_11.md.

Nur lesend gegen Projektdaten; die LLM-Antworten gehen in eine EIGENE Ablage ``data/_a1/a1_stichprobe_llm_gemini.db`` (nie sichten.db,
nie die Produktion). Schlüssel: GEMINI_API_KEY_2 (eigener Desktop-Topf, 500/Tag je Modell), nie der NB-Schlüssel.

  w  WISSENSSTAND je Gemini-2.5-Modell über 2025 (erzwungene BTC-Schätzung je Monat, wie g7_stufe0 d) — ist 2025 damit sauber?
  a  A1 PROMPT 3 AUF GEMINI gegen die festgeschriebene Handeinordnung der Stichprobe 3 (dieselben 60 Titel, auf denen gpt-oss-120b
     gemessen ist: Fehlalarm 2, Verlust 4, Sicht relevant 90 %, Typ gleich bei Wiederholung 100 %)
  r  Auswertung von a ohne Netz

VORAB FESTGELEGT (02.11., vor dem ersten Aufruf):
  a  Ein Gemini-Modell TAUGT für A1, wenn auf Stichprobe 3: Fehlalarm <= 3 UND Verlust <= 5 (gpt-oss + 1) UND bei Wiederholung
     >= 95 % gleicher Typ. Sonst bleibt A1 auf gpt-oss-120b
  w  Ein Modell ist für einen Monat SAUBER, wenn sein Schätzfehler dort >= 10 % ist, OBWOHL die Kontrolltage (2023/24) < 10 % sind.
     Sauber ab = erster Testmonat, ab dem alle folgenden >= 10 % sind. Die Kursprobe ist eine UNTERGRENZE des Wissens (ein Modell kann
     Ereignisse kennen, ohne den Kurs zu kennen) — daher nur zusammen mit einem Sicherheitsabstand zu verwenden

    python zeit_voranalyse.py w | a | r
"""
import json
import os
import re
import sqlite3
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)
from agent import ereignisse as E  # noqa: E402

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DB = os.path.join(PROJ, "data", "_a1", "a1_stichprobe_llm_gemini.db")
A1_MODELLE = ("gemini-3.5-flash", "gemini-3.6-flash")
W_MODELLE = ("gemini-2.5-flash", "gemini-2.5-flash-lite")
AUS = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    AUS.append(s)


def _env():
    from dotenv import dotenv_values
    return dotenv_values(os.path.join(PROJ, ".env"))


def teil_w():
    import requests
    import g7_stufe0 as G
    key = _env().get("GEMINI_API_KEY_2")
    btc = G.kurs_btc()
    tage = [("K", "2023-06-15"), ("K", "2024-03-14"), ("K", "2024-08-12")] + [("T", "2025-%02d-15" % m) for m in range(1, 13)] + \
           [("T", "2026-03-16")]
    p("w  WISSENSSTAND (erzwungene BTC-Schätzung, Schlüssel 2) · K = Kontrolle, T = Test · Fehler < 10 %% = Modell kennt den Kurs")
    for m in W_MODELLE:
        zeile = []
        for k, d in tage:
            echt = float(btc.asof(pd.Timestamp(d)))
            t = ("Schätze den Bitcoin-Schlusskurs in USD am %s (UTC). Du MUSST eine Zahl nennen, auch wenn du unsicher bist. "
                 "Antworte nur als JSON {\"btc_usd\": Zahl}." % d)
            f = None
            for _ in range(6):
                x = requests.post(GEMINI_URL, headers={"Authorization": "Bearer %s" % key}, timeout=120,
                                  json={"model": m, "temperature": 0, "messages": [{"role": "user", "content": t}]})
                if x.status_code == 429 or x.status_code >= 500:
                    time.sleep(30)
                    continue
                try:
                    txt = x.json()["choices"][0]["message"].get("content") or ""
                    f = abs(float(json.loads(re.search(r"\{.*?\}", txt, re.S).group(0))["btc_usd"]) / echt - 1)
                except Exception:  # noqa: BLE001
                    f = None
                break
            zeile.append((k, d, f))
            time.sleep(4)
        p("   %-24s %s" % (m, " · ".join("%s%s %s" % (k, d[2:7], ("%.0f%%" % (100 * f)) if f is not None else "–") for k, d, f in zeile)))
        ktl = [f for k, d, f in zeile if k == "K" and f is not None]
        test = [(d, f) for k, d, f in zeile if k == "T"]
        ab = None
        for i, (d, f) in enumerate(test):
            if all(g is not None and g >= 0.10 for _d, g in test[i:]):
                ab = d[:7]
                break
        p("      Kontrolle %s · sauber ab (Kursprobe) %s" % ("ok" if ktl and max(ktl) < 0.10 else "⚠ taugt nicht", ab or "–"))


def teil_a():
    import a1_validierung3 as V
    key = _env().get("GEMINI_API_KEY_2")
    S = V.stichprobe3()
    S["quelle"], S["meldung"] = V.QUELLE, S.nr.astype(str)
    M = S[["quelle", "meldung", "titel"]]
    c = E.verbinde(DB)
    alt = (E.URL, E.MODELL)
    try:
        E.URL = GEMINI_URL
        for m in A1_MODELLE:
            E.MODELL = m
            for lauf in (21, 22):
                print(m, "Lauf", lauf, E.llm_lauf(c, M, key, lauf=lauf), flush=True)
    finally:
        E.URL, E.MODELL = alt
        c.close()


def teil_r():
    import a1_validierung3 as V
    V.p = p
    W, A = E.welt(), E.alias()
    S = V.stichprobe3()
    S["h_ereignis"] = ~S.typ.isin(E.KEIN_EREIGNIS)
    S["h_assets_w"] = [None if x.strip() == "?" else json.dumps(sorted({k for k in x.split() if k in W})) for x in S.assets]
    S["h_sicht"] = pd.Series([E.sicht(json.loads(a) if a else [], b) if (e and b != "sonstiges") else None
                              for a, b, e in zip(S.h_assets_w.fillna("[]"), S.bereich, S.h_ereignis)], index=S.index)
    p("a  A1 PROMPT 3 (%s) AUF GEMINI · Stichprobe 3 (60, Hand vorher festgeschrieben) · Vergleich gpt-oss-120b: Fehlalarm 2, Verlust 4, "
      "Sicht relevant 90 %%, Wiederholung 100 %%" % E.PROMPT_SHA)
    c = sqlite3.connect("file:%s?mode=ro" % DB.replace("\\", "/"), uri=True)

    def antw(m, lauf):
        L = pd.read_sql("SELECT meldung, typ, assets, bereich FROM llm_antwort WHERE quelle=? AND lauf=? AND modell=? AND prompt_sha=?", c,
                        params=(V.QUELLE, lauf, m, E.PROMPT_SHA))
        return L.set_index("meldung") if len(L) == 60 else None
    for m in A1_MODELLE:
        L1, L2 = antw(m, 21), antw(m, 22)
        if L1 is None or L2 is None:
            p("\n%s: unvollständig — nicht bewertet" % m)
            continue
        un = int((L1.typ == "unlesbar").sum())
        R, fa, ve = V.bewerte(S, L1, W, A, "%s (Lauf 21; unlesbar %d)" % (m, un))
        gl = sum(R.typ[i] == L2.loc[str(n)].typ for i, n in zip(S.index, S.nr))
        z = ~S.notiz.str.startswith("zweifelhaft")
        p("  Wiederholung (Lauf 22): gleicher Typ %s · ohne die %d zweifelhaften Handfälle: Sicht relevant gleich %s · Fehlalarm %d · Verlust %d" % (
            V.fmt(gl, 60), int((~z).sum()), V.fmt(int(R.ok[z].sum()), int(z.sum())), int((S.h_sicht.isna() & R.sicht.notna())[z].sum()),
            int((S.h_sicht.notna() & R.sicht.isna())[z].sum())))
        ja = fa <= 3 and ve <= 5 and gl >= 57
        p("  ENTSCHEIDUNG (vorab): Fehlalarm %d (≤ 3) · Verlust %d (≤ 5) · Wiederholung %d/60 (≥ 57) => %s" % (
            fa, ve, gl, "TAUGT FÜR A1" if ja else "taugt NICHT"))
    c.close()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    t = sys.argv[1]
    {"w": teil_w, "a": teil_a, "r": teil_r}[t]()
    if t != "a":
        open(os.path.join(HIER, "zeit_voranalyse_%s.txt" % t), "w", encoding="utf-8").write("\n".join(AUS) + "\n")


if __name__ == "__main__":
    main()
