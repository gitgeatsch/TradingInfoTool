"""E-79 Datenquellen-Inventar fuer Ereignisse (Voranalyse_Schritt7 §23.22, E-75) - nur LESENDE Abrufe oeffentlicher Quellen ohne Schluessel,
nichts wird gespeichert ausser diesem Bericht. Je Quelle: erreichbar? Zeitstempel? wie weit zurueck? Asset zuordenbar? Ereignistyp?

    python Basisinfos/Rechenkern_02_10/e79_quellen_inventar.py
"""
import json
import re
from datetime import datetime, timezone

import requests

H = {"User-Agent": "Mozilla/5.0 TradingInfoTool-Inventar"}


def hole(url, **kw):
    try:
        r = requests.get(url, headers=H, timeout=30, **kw)
        return r.status_code, r
    except Exception as exc:                                   # noqa: BLE001
        return "Fehler %s" % type(exc).__name__, None


def ts(ms):
    return datetime.fromtimestamp(int(ms) / (1000 if int(ms) > 1e11 else 1), tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def binance():
    # Katalog 48 = neue Listings, 161 = Delisting (oeffentliche CMS-Schnittstelle der Website)
    for kat, name in ((48, "Listing"), (161, "Delisting")):
        st, r = hole("https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
                     params={"type": 1, "catalogId": kat, "pageNo": 1, "pageSize": 50})
        if r is None or st != 200:
            print("  Binance %-9s %s" % (name, st)); continue
        try:
            arts = r.json()["data"]["catalogs"][0]["articles"]
        except Exception:                                      # noqa: BLE001
            print("  Binance %-9s Antwort ohne erwartete Struktur: %s" % (name, r.text[:160])); continue
        t = [a.get("releaseDate") for a in arts if a.get("releaseDate")]
        print("  Binance %-9s %d Meldungen auf Seite 1, Zeitstempel %s .. %s, Beispiel: %s" % (
            name, len(arts), ts(min(t)) if t else "-", ts(max(t)) if t else "-", (arts[0].get("title") or "")[:110] if arts else "-"))
        tiefe = None
        for seite in (5, 20, 50):
            st2, r2 = hole("https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
                           params={"type": 1, "catalogId": kat, "pageNo": seite, "pageSize": 50})
            try:
                a2 = r2.json()["data"]["catalogs"][0]["articles"]
            except Exception:                                  # noqa: BLE001
                a2 = []
            if a2:
                tiefe = (seite, ts(min(a.get("releaseDate") for a in a2)))
        print("            Rueckreichweite: %s" % ("Seite %d reicht bis %s" % tiefe if tiefe else "nur Seite 1 abrufbar"))


def llama(pfad, name, zeit_feld, sym_feld):
    st, r = hole("https://api.llama.fi/" + pfad)
    if r is None or st != 200:
        print("  DefiLlama %-9s %s %s" % (name, st, (r.text[:120] if r is not None else ""))); return
    d = r.json()
    rows = d.get("raises") if isinstance(d, dict) and "raises" in d else d
    if not isinstance(rows, list):
        print("  DefiLlama %-9s Struktur %s" % (name, str(type(d)))); return
    t = [x.get(zeit_feld) for x in rows if isinstance(x, dict) and x.get(zeit_feld)]
    mit_sym = sum(1 for x in rows if isinstance(x, dict) and x.get(sym_feld))
    print("  DefiLlama %-9s %d Eintraege, %s .. %s, mit Zuordnung (%s) %d · Felder %s" % (
        name, len(rows), ts(min(t)) if t else "-", ts(max(t)) if t else "-", sym_feld, mit_sym, sorted(rows[0])[:14] if rows else "-"))


def rss(url, name):
    st, r = hole(url)
    if r is None or st != 200:
        print("  RSS %-12s %s" % (name, st)); return
    d = re.findall(r"<pubDate>([^<]+)</pubDate>", r.text)
    print("  RSS %-12s %d Eintraege, %s .. %s (nur die letzten Tage, kein Archiv; Asset nur aus dem Titel)" % (
        name, len(d), d[-1][:22] if d else "-", d[0][:22] if d else "-"))


def gdelt():
    st, r = hole("https://api.gdeltproject.org/api/v2/doc/doc", params={
        "query": '"binance" delisting', "mode": "artlist", "format": "json", "maxrecords": 5,
        "startdatetime": "20250101000000", "enddatetime": "20250301000000"})
    if r is None or st != 200:
        print("  GDELT        %s" % st); return
    try:
        a = r.json().get("articles", [])
        print("  GDELT        %d Artikel Jan-Feb 2025, Zeitstempel z. B. %s - Archiv rueckwirkend, aber allgemeine Presse, Asset nur aus dem Titel" % (
            len(a), a[0].get("seendate") if a else "-"))
    except Exception:                                          # noqa: BLE001
        print("  GDELT        Antwort: %s" % r.text[:160])


if __name__ == "__main__":
    print("E-79 Datenquellen-Inventar Ereignisse · %s UTC" % datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
    binance()
    llama("hacks", "Hacks", "date", "name")
    llama("raises", "Raises", "date", "name")
    llama("emissions", "Unlocks", "nextEvent", "token")
    rss("https://cointelegraph.com/rss", "Cointelegraph")
    rss("https://www.coindesk.com/arc/outboundfeeds/rss/", "CoinDesk")
    gdelt()
