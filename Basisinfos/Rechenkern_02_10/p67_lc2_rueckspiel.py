"""P67 L-C2 RUECKSPIEL (19.10.2026, Schritt7 §23.74, vorab fa3aac7e): gpt-oss-120b bewertet je Einstiegstag das Risiko eines breiten Kursrutsches
aus den Schlagzeilen des VORTAGS. Nur Abfragen und Ablage; die Auswertung steht in p67_auswertung.py.

    python Basisinfos/Rechenkern_02_10/p67_lc2_rueckspiel.py [--tage 2025-03-06,2025-05-23] [--ablage <pfad>]

Wiederaufnehmbar (geladene Tage werden uebersprungen). Groq kostenfrei: 8.000 Tokens/Minute -> Drossel ueber die Antwort-Kopfzeilen,
bei 429 Wartezeit aus der Antwort. Je Abfrage wird geprueft: keine Meldung mit Zeitpunkt >= d 00:00, kein Datum in der Eingabe (sonst Abbruch).
"""
import hashlib
import json
import os
import re
import sqlite3
import sys
import time

import pandas as pd
import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
from dotenv import dotenv_values  # noqa: E402

MODELL = "openai/gpt-oss-120b"
URL = "https://api.groq.com/openai/v1/chat/completions"
N_MAX = 60
MONATE = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
DATUM = [re.compile(r"\b20(?:24|25|26)\b"), re.compile(r"\b%s\s+\d{1,2}(?:st|nd|rd|th)?\b" % MONATE, re.I), re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+%s\b" % MONATE, re.I),
         re.compile(r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I), re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b"),
         re.compile(r"\bQ[1-4]\b")]
PLAN = ("Kontext: Ein Handelssystem kauft Altcoins NACH einem Rueckgang und wettet auf eine Gegenbewegung binnen 24 Stunden. "
        "Die Gefahr fuer diesen Handel ist ein BREITER Kursrutsch am Kryptomarkt, der viele Altcoins zugleich um 10 % und mehr fallen laesst. "
        "Unten stehen die Krypto-Schlagzeilen der letzten 24 Stunden (ohne Datum). Beurteile allein daraus das Risiko eines solchen breiten "
        "Kursrutsches in den NAECHSTEN 24 Stunden. Antworte nur als JSON {\"risiko\": \"niedrig\" | \"mittel\" | \"hoch\", \"grund\": \"ein Satz\"}.")


def ohne_datum(t):
    for m in DATUM:
        t = m.sub("", t)
    return re.sub(r"\s{2,}", " ", t).strip(" ,;:-")


def meldungen():
    c = sqlite3.connect("file:data/_lc/nachrichten.db?mode=ro", uri=True)
    M = pd.read_sql("SELECT titel, pub_utc, aufnahme_ts FROM meldung WHERE pub_utc IS NOT NULL", c, parse_dates=["pub_utc"])
    c.close()
    M["zeit"] = M[["pub_utc"]].join(pd.to_datetime(M.aufnahme_ts.str[:14], format="%Y%m%d%H%M%S").rename("auf")).min(axis=1)
    M["schl"] = M.titel.fillna("").str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.strip()
    M = M.sort_values("zeit").drop_duplicates("schl")
    return M[(M.zeit >= "2024-12-01") & (M.schl != "")]


def eingabe(M, d):
    a, e = pd.Timestamp(d) - pd.Timedelta(days=1), pd.Timestamp(d)
    X = M[(M.zeit >= a) & (M.zeit < e)].sort_values("zeit").tail(N_MAX)
    zeilen = [ohne_datum(t) for t in X.titel]
    zeilen = [z for z in zeilen if z]
    text = "\n".join("- " + z for z in zeilen) if zeilen else "keine Meldungen"
    return text, len(zeilen), (X.zeit.max() if len(X) else None)


def pruefe_eingabe(text, juengst, d):
    if juengst is not None and juengst >= pd.Timestamp(d):
        raise RuntimeError("VORGRIFF: Meldung mit Zeitpunkt %s >= %s" % (juengst, d))
    for m in DATUM:
        if m.search(text):
            raise RuntimeError("DATUM in der Eingabe fuer %s: %r" % (d, m.search(text).group(0)))


def frage(key, text):
    body = {"model": MODELL, "temperature": 0.0, "messages": [{"role": "user", "content": PLAN + "\n\nSchlagzeilen:\n" + text}]}
    # 19.10.2026: Groq-Tagesgrenze 200.000 Tokens (TPD) und Netzaussetzer - geduldig warten statt abbrechen (nur Fehlerbehandlung,
    # Modell/Eingabe/Einstellung unveraendert)
    for v in range(400):
        try:
            r = requests.post(URL, headers={"Authorization": "Bearer %s" % key}, json=body, timeout=180)
        except requests.RequestException:
            time.sleep(60)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            m = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", r.text)
            warte = (int(m.group(1) or 0) * 60 + float(m.group(2))) if m else float(r.headers.get("retry-after") or 30)
            time.sleep(min(max(warte + 2, 5), 600))
            continue
        r.raise_for_status()
        j = r.json()
        rest = int(r.headers.get("x-ratelimit-remaining-tokens") or 8000)
        if rest < 3000:
            time.sleep(20)
        return j["choices"][0]["message"].get("content") or "", (j.get("usage") or {}).get("total_tokens")
    raise RuntimeError("Groq: 400 Versuche ohne Antwort")


def lies(roh):
    m = re.search(r"\{.*\}", roh or "", re.S)
    j = json.loads(m.group(0))
    r = str(j.get("risiko", "")).strip().lower()
    if r not in ("niedrig", "mittel", "hoch"):
        raise ValueError("risiko %r" % r)
    return r, str(j.get("grund", ""))[:300]


def main():
    ablage = sys.argv[sys.argv.index("--ablage") + 1] if "--ablage" in sys.argv else os.path.join("data", "_lc", "p67_rueckspiel.db")
    key = dotenv_values(".env").get("GROQ_API_KEY")
    E = pd.read_csv(os.path.join("data", "_lc", "p65_einstiege.csv"), sep=";", parse_dates=["zeit"])
    tage = sorted({str(z.date()) for z in E.zeit})
    if "--tage" in sys.argv:
        tage = sys.argv[sys.argv.index("--tage") + 1].split(",")
    M = meldungen()
    c = sqlite3.connect(ablage)
    c.execute("CREATE TABLE IF NOT EXISTS urteil (tag TEXT PRIMARY KEY, modell TEXT, n_meldungen INTEGER, juengst TEXT, eingabe_sha TEXT, roh TEXT, "
              "risiko TEXT, grund TEXT, versuche INTEGER, tokens INTEGER, am TEXT)")
    da = {r[0] for r in c.execute("SELECT tag FROM urteil WHERE risiko IS NOT NULL")}
    neu = 0
    for d in tage:
        if d in da:
            continue
        text, n, juengst = eingabe(M, d)
        pruefe_eingabe(text, juengst, d)
        risiko, grund, roh, tok, v = None, None, None, None, 0
        for v in range(1, 4):
            try:
                roh, tok = frage(key, text)
                risiko, grund = lies(roh)
                break
            except (ValueError, AttributeError, json.JSONDecodeError):
                time.sleep(3)
        c.execute("INSERT OR REPLACE INTO urteil VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (d, MODELL, n, str(juengst) if juengst is not None else None, hashlib.sha256(text.encode()).hexdigest()[:16], roh,
                   risiko or "fehlt", grund, v, tok, time.strftime("%Y-%m-%d %H:%M:%S")))
        c.commit()
        neu += 1
        if neu % 25 == 0:
            z = dict(c.execute("SELECT risiko, COUNT(*) FROM urteil GROUP BY risiko").fetchall())
            print("  %s: %d neu · Stand %s" % (d, neu, z), flush=True)
        time.sleep(1)
    z = dict(c.execute("SELECT risiko, COUNT(*) FROM urteil GROUP BY risiko").fetchall())
    print("RUECKSPIEL %s: %d Tage in der Ablage, neu %d · %s" % (MODELL, sum(z.values()), neu, z), flush=True)
    c.close()


if __name__ == "__main__":
    main()
