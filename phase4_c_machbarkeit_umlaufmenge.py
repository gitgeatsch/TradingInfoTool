# -*- coding: utf-8 -*-
"""MACHBARKEIT: traegt CoinGecko als Quelle fuer den `turnover`-Nenner?

⚠️ VOR dem Vollabruf (rund 18 Minuten fuer 537 Symbole). Nutzerauftrag
20.09.2026: *„vorher sauber machbarkeit pruefen, ob unser portfolio
ausreichend abgedeckt ist, Quelle sauber pruefen, etc."*

## Der Weg, der geprueft wird

    1  /exchanges/binance/tickers        Paar -> coin_id, EINDEUTIG
    2  /coins/{id}/market_chart?days=365 Marktkapitalisierung + Preis
    3  Menge = Marktkapitalisierung / Preis   -> FREE FLOAT

## Was hier geprueft wird - und warum jedes einzeln

    ABDECKUNG    wie viele der 537 Messmengen-Symbole bekommen eine
                 coin_id? Und wie viele der gehaltenen Positionen? Eine
                 Quelle, die das Portfolio nicht deckt, loest nichts.
    VOLLSTAENDIG bekommt jede Stichprobe 366 Punkte, oder gibt es
                 Luecken? Eine Reihe mit Loechern kann nicht ranken.
    RICHTIG      stimmt Marktkapitalisierung/Preis mit dem direkt
                 gemeldeten `circulating_supply` ueberein? Wenn nicht,
                 rechnen wir etwas anderes aus, als wir glauben.
    STETIG       ⚠️ SPRUENGE in der Menge sind der bekannte Datenfehler
                 (Token-Umstellungen, `datenfehler-tokenumstellungen`).
                 Ein Sprung im NENNER verschiebt den Rang, ohne dass am
                 Markt etwas passiert ist.
    GEGEN ALT    fuer Symbole mit `SplyCur`-Reihe: wie weit laufen die
                 beiden Historien auseinander?

⚠️ STICHPROBE, nicht Vollabruf - und die Auswahl ist vorab benannt:
die groessten Bestandswerte, zwei tote, zwei kleine. Wer nur die
Grossen prueft, prueft den einfachen Fall.

⚠️ Eigener Abruf, NICHT ueber api/* (das bucht ueber `api_health` in die
Produktionsdatenbank). NUR LESEND.

    python phase4_c_machbarkeit_umlaufmenge.py --db <sicherung.db>
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CG = "https://api.coingecko.com/api/v3"
# ⚠️ Vorab benannt: gross / klein / tot - nicht nach dem Ergebnis gewaehlt.
STICHPROBE = ("BTC", "ETH", "LINK", "SOL", "TAO", "SUI", "MORPHO",
              "BEAMX", "SUPRA", "FTT", "SRM", "XLM")


def _pfad(flagge: str, vorgabe: str) -> str:
    a = sys.argv[1:]
    return a[a.index(flagge) + 1] if flagge in a else vorgabe


def hole(url: str, versuche: int = 4):
    """401/403 = Verbot, 429 = Drosselung - getrennt, mit Nachwartezeit."""
    for i in range(versuche):
        try:
            r = urllib.request.Request(
                url, headers={"User-Agent": "TIT-Machbarkeit"})
            with urllib.request.urlopen(r, timeout=45) as a:
                return a.status, json.loads(a.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < versuche - 1:
                time.sleep(25 * (i + 1))
                continue
            return e.code, None
        except Exception as exc:                             # noqa: BLE001
            return str(exc)[:60], None
    return "?", None


def binance_karte() -> dict:
    """Paar -> coin_id, ueber die Boersen-Ticker (eindeutig)."""
    karte, seite = {}, 1
    while seite <= 12:
        st, d = hole("%s/exchanges/binance/tickers?page=%d" % (CG, seite))
        tk = (d or {}).get("tickers") or [] if isinstance(d, dict) else []
        if not tk:
            break
        for t in tk:
            if (t.get("target") or "").upper() == "USDT" and t.get("coin_id"):
                karte[(t.get("base") or "").upper()] = t["coin_id"]
        seite += 1
        time.sleep(2.5)
    return karte


def main() -> int:
    db = _pfad("--db", "")
    if not db or not os.path.exists(db):
        raise SystemExit("Sicherung nicht gefunden - mit --db "
                         "<sicherung.db> setzen (NIE die Standard-DB)")
    print("=" * 104)
    print("MACHBARKEIT: COINGECKO ALS QUELLE FUER DEN `turnover`-NENNER")
    print("=" * 104)

    # ---- Messmenge und Bestand ---------------------------------------
    import agent.marktrang as MR
    datei, sql = MR.MESSBASIS["schnitt"]
    v1 = {r[0].upper() for r in sqlite3.connect(
        "file:%s?mode=ro" % datei, uri=True).execute(sql)}
    o = sqlite3.connect("file:data/onchain_historie.db?mode=ro", uri=True)
    alt = {r[0].upper() for r in o.execute(
        "SELECT DISTINCT symbol FROM splycur")}
    p = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    bestand = {}
    for sym, q, s in p.execute(
            "SELECT symbol, COALESCE(quantity,0), COALESCE(staked_quantity,0)"
            "  FROM holdings"):
        if (q or 0) + (s or 0) > 0:
            bestand[sym.upper()] = (q or 0) + (s or 0)
    kurse = {}
    for sym, pe in p.execute(
            "SELECT symbol, price_eur FROM price_cache pc WHERE fetched_at = "
            "(SELECT MAX(fetched_at) FROM price_cache x "
            "  WHERE x.symbol = pc.symbol)"):
        if pe:
            kurse[sym.upper()] = pe

    print("  Messmenge V1: %d · `SplyCur` heute: %d · Bestandspositionen: %d"
          % (len(v1), len(alt), len(bestand)))
    print("  Binance-Ticker holen ...")
    karte = binance_karte()
    print("  -> %d USDT-Paare mit eindeutiger coin_id" % len(karte))
    print()

    # ---- 1  ABDECKUNG -------------------------------------------------
    print("-" * 104)
    print("  1) ABDECKUNG")
    print("-" * 104)
    neu_v1 = sorted(v1 & set(karte))
    print("     Messmenge V1:  %d von %d = %.0f %%   (heute mit `SplyCur`: "
          "%d = %.0f %%)"
          % (len(neu_v1), len(v1), 100.0 * len(neu_v1) / len(v1),
             len(v1 & alt), 100.0 * len(v1 & alt) / len(v1)))
    kry = [s for s in bestand if s in karte or s in alt or s in v1]
    deck_neu = [s for s in kry if s in karte]
    deck_alt = [s for s in kry if s in alt]
    wert = sum(bestand[s] * kurse.get(s, 0.0) for s in kry)
    wert_neu = sum(bestand[s] * kurse.get(s, 0.0) for s in deck_neu)
    wert_alt = sum(bestand[s] * kurse.get(s, 0.0) for s in deck_alt)
    print("     BESTAND (Krypto): %d Positionen, %.0f EUR" % (len(kry), wert))
    print("       mit NEUER Quelle: %2d Positionen = %.0f %% · nach Wert "
          "%.0f EUR = %.1f %%"
          % (len(deck_neu), 100.0 * len(deck_neu) / len(kry) if kry else 0,
             wert_neu, 100.0 * wert_neu / wert if wert else 0))
    print("       mit ALTER Quelle: %2d Positionen = %.0f %% · nach Wert "
          "%.0f EUR = %.1f %%"
          % (len(deck_alt), 100.0 * len(deck_alt) / len(kry) if kry else 0,
             wert_alt, 100.0 * wert_alt / wert if wert else 0))
    fehlt = sorted(set(kry) - set(deck_neu))
    if fehlt:
        print("     ⚠️ Bestand OHNE neue Quelle: %s" % ", ".join(fehlt))
    print()

    # ---- 2 bis 5  DIE STICHPROBE --------------------------------------
    print("-" * 104)
    print("  2) STICHPROBE - Vollstaendigkeit, Richtigkeit, Stetigkeit")
    print("-" * 104)
    print("     %-8s %6s %6s %8s %10s %10s %9s"
          % ("Symbol", "Punkte", "Nullen", "Luecken", "Menge heute",
             "cg supply", "Abw."))
    probleme = []
    for sym in STICHPROBE:
        cid = karte.get(sym)
        if not cid:
            print("     %-8s -> keine coin_id ueber Binance-Ticker" % sym)
            probleme.append((sym, "keine id"))
            continue
        st, d = hole("%s/coins/%s/market_chart?vs_currency=usd&days=365"
                     "&interval=daily" % (CG, cid))
        mc = (d or {}).get("market_caps") or [] if isinstance(d, dict) else []
        pr = (d or {}).get("prices") or [] if isinstance(d, dict) else []
        if not mc:
            print("     %-8s -> Status %s, keine Daten" % (sym, st))
            probleme.append((sym, "Status %s" % st))
            time.sleep(2.5)
            continue
        mengen = []
        nullen = 0
        for (t1, m), (t2, k) in zip(mc, pr):
            if not k or not m:
                nullen += 1
                mengen.append(None)
            else:
                mengen.append(m / k)
        gueltig = [x for x in mengen if x]
        # Luecken im Tagesraster
        luecken = 0
        for a, b in zip(mc, mc[1:]):
            if (b[0] - a[0]) > 1.6 * 86400000:
                luecken += 1
        # aktueller Wert zum Vergleich
        st2, d2 = hole("%s/coins/markets?vs_currency=usd&ids=%s" % (CG, cid))
        cs = None
        if isinstance(d2, list) and d2:
            cs = d2[0].get("circulating_supply")
        heute = gueltig[-1] if gueltig else None
        abw = (100.0 * (heute - cs) / cs) if (heute and cs) else None
        print("     %-8s %6d %6d %8d %10s %10s %8s"
              % (sym, len(mc), nullen, luecken,
                 ("%.3g" % heute) if heute else "-",
                 ("%.3g" % cs) if cs else "-",
                 ("%+.1f %%" % abw) if abw is not None else "-"))
        if abw is not None and abs(abw) > 2.0:
            probleme.append((sym, "Menge weicht %+.1f %% vom "
                                  "circulating_supply ab" % abw))
        if luecken:
            probleme.append((sym, "%d Luecken im Tagesraster" % luecken))
        if nullen:
            probleme.append((sym, "%d Punkte ohne Wert" % nullen))
        # Spruenge: groesster Tageswechsel der MENGE
        spr = 0.0
        for a, b in zip(gueltig, gueltig[1:]):
            if a > 0:
                spr = max(spr, abs(b - a) / a)
        if spr > 0.10:
            probleme.append((sym, "Mengensprung von %.0f %% an einem Tag"
                             % (100 * spr)))
        time.sleep(3)
    print()
    print("-" * 104)
    print("  3) BEFUND")
    print("-" * 104)
    if probleme:
        print("     ⚠️ %d Auffaelligkeiten:" % len(probleme))
        for s, w in probleme:
            print("        %-8s %s" % (s, w))
    else:
        print("     ✔ keine Auffaelligkeit in der Stichprobe")
    print()
    print("     ⚠️ Eine Stichprobe von %d Werten belegt keine "
          "Vollstaendigkeit - sie kann nur" % len(STICHPROBE))
    print("        Probleme FINDEN. Findet sie keine, ist der Vollabruf "
          "vertretbar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
