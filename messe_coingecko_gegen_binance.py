# -*- coding: utf-8 -*-
"""Liefert CoinGecko dieselben Kurse wie Binance? - und traegt BTC die Bewertung?

**26.09.2026**, Nutzerauftrag: *"dann CoinGecko gegen Binance messen"*.

═══════════════════════════════════════════════════════════════════════
 WARUM DIESE MESSUNG VOR JEDEM EINSATZ KOMMT
═══════════════════════════════════════════════════════════════════════

2.616 hat die Fallback-Stufen gemessen - aber an Kerzen, die aus den
EIGENEN Binance-Stundenkursen AGGREGIERT wurden. Der Unterschied war dort
rein die AUFLOESUNG. Ob CoinGecko dieselben Werte liefert, ist damit NICHT
gezeigt:

    Stufe 2 (67 %) und Stufe 3 (65 %) sind ANNAHMEN, solange diese
    Messung nicht gelaufen ist.

⭐ Gemessen wird an den Symbolen, die BEIDE Quellen haben - nur dort ist
ein Vergleich ueberhaupt moeglich.

═══════════════════════════════════════════════════════════════════════
 DIE DREI FRAGEN
═══════════════════════════════════════════════════════════════════════

    F1  Stimmen die SCHLUSSKURSE der stuendlichen Preisreihe ueberein?
        (Stufe 3 steht und faellt damit)

    F2  Stimmen die 4-h-OHLC-Kerzen mit den aggregierten ueberein -
        und zwar in HIGH und LOW, nicht nur im Schluss?
        (Stufe 2 braucht die Spanne, nicht den Punkt)

    F3  Ergibt die daraus gerechnete ATR dieselben Werte?
        (das ist die Groesse, die am Ende zaehlt)

⚠️ EIN UNTERSCHIED IST NICHT AUTOMATISCH EIN FEHLER: CoinGecko mittelt
ueber Boersen, Binance ist eine einzelne. Erwartet wird deshalb keine
Bitgleichheit, sondern ein Unterschied, der KLEIN GEGEN DEN EFFEKT ist -
und genau das ist die Pruefgroesse.

═══════════════════════════════════════════════════════════════════════
 UND NEBENBEI: TRAEGT DIE BEWERTUNG AUF BTC?
═══════════════════════════════════════════════════════════════════════

BTC ist aus NEUN Messwerkzeugen ausgeschlossen, steht aber im Betrieb auf
`hebel_pruefung_erlaubt=1`, wird gehalten und hat 30 Signale. Der Befund
2.608 gilt fuer BTC also NICHT - es war nie in der Menge.

⚠️ Das ist KEINE Entscheidungsfrage, sondern eine Messung. Sie laeuft hier
mit, damit die Antwort vorliegt statt zur Abstimmung zu stehen.

⚠️ NUR LESEN. Braucht `COINGECKO_API_KEY` aus der .env (100 Anfragen je
Minute statt 30 - ohne Key laeuft man in HTTP 429).

    python messe_coingecko_gegen_binance.py [--symbole N]
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import sys
import time
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema, trailing            # noqa: E402
from messe_aufloesung_und_fallback import (                     # noqa: E402
    atr_grob, atr_aus_schluessen)

BETRIEB_DB = os.path.join("data", "tradinginfotool.db")
EMA_L, VORLAUF, H, TW, SW = 48, 240, 72, 1.0, 1.0
PAUSE = 0.7                      # mit Demo-Key sind 100/Minute erlaubt
SAAT = 20260926


def schluessel():
    p = ".env"
    if not os.path.exists(p):
        return None
    for z in open(p, encoding="utf-8", errors="ignore"):
        if z.strip().startswith("COINGECKO_API_KEY"):
            return z.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def hol(url, key):
    kopf = {"User-Agent": "TradingInfoTool"}
    if key:
        kopf["x-cg-demo-api-key"] = key
    try:
        r = urllib.request.Request(url, headers=kopf)
        return json.loads(urllib.request.urlopen(r, timeout=30).read())
    except Exception as e:                                   # noqa: BLE001
        return {"__f": str(e)[:60]}


def cg_ids():
    c = sqlite3.connect("file:%s?mode=ro" % BETRIEB_DB, uri=True)
    try:
        return {r[0]: r[1] for r in c.execute(
            "SELECT symbol, coingecko_id FROM price_cache "
            "WHERE coingecko_id IS NOT NULL")}
    finally:
        c.close()


def stunde_aus_ms(ms):
    """CoinGecko-Zeitstempel (ms) -> Schluessel wie in `stundenkurse.db`.

    ⚠️ Das Format dort ist `2026-09-16 00:00` - Leerzeichen und Minuten,
    NICHT ISO mit `T`. Im Probelauf gefunden: mit `%Y-%m-%dT%H` gab es
    NULL gemeinsame Stunden, und der Lauf haette leise nichts gemessen.
    """
    return dt.datetime.fromtimestamp(ms / 1000.0, dt.UTC).strftime(
        "%Y-%m-%d %H:00")


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    key = schluessel()
    print("=" * 100)
    print("LIEFERT COINGECKO DIESELBEN KURSE WIE BINANCE?")
    print("=" * 100)
    print("  Demo-Key: %s" % ("ja (100/Minute)" if key else
                              "NEIN - Lauf bricht bei HTTP 429 ab"))
    print("  ⚠️ 2.616 mass AGGREGIERTE Binance-Kerzen. Stufe 2 (67 %) und")
    print("     Stufe 3 (65 %) sind ANNAHMEN, bis diese Messung laeuft.")
    print()

    ids = cg_ids()
    kurse = lade_kurse(None)
    gemeinsam = sorted(s for s in kurse if s in ids)
    if grenze:
        gemeinsam = gemeinsam[:grenze]
    print("  %d Symbole haben BEIDE Quellen" % len(gemeinsam), flush=True)
    print()

    # ══ F1/F2/F3 je Symbol ══════════════════════════════════════════
    print("  %-8s %7s %10s %10s %10s %10s %10s"
          % ("Symbol", "Stunden", "Kurs-Abw.", "Korr.", "High-Abw.",
             "Low-Abw.", "ATR-Verh."))
    zeilen = []
    for sym in gemeinsam:
        st, h, l, cc, v = kurse[sym]
        binance = {st[i]: cc[i] for i in range(len(st))}
        bh = {st[i]: h[i] for i in range(len(st))}
        bl = {st[i]: l[i] for i in range(len(st))}
        cid = ids[sym]
        d = hol("https://api.coingecko.com/api/v3/coins/%s/market_chart"
                "?vs_currency=usd&days=90" % cid, key)
        time.sleep(PAUSE)
        if "__f" in d:
            print("  %-8s ⛔ %s" % (sym, d["__f"]))
            continue
        # ── F1: Schlusskurse ─────────────────────────────────────────
        paare = []
        for ms, px in (d.get("prices") or []):
            s = stunde_aus_ms(ms)
            if s in binance and px:
                paare.append((binance[s], float(px)))
        if len(paare) < 100:
            print("  %-8s (nur %d gemeinsame Stunden)" % (sym, len(paare)))
            continue
        a = np.array([x[0] for x in paare]); b = np.array([x[1] for x in paare])
        abw = float(np.median(np.abs(b - a) / np.maximum(a, 1e-12))) * 100
        korr = float(np.corrcoef(a, b)[0, 1])
        # ── F2: 4-h-OHLC gegen aggregiert ────────────────────────────
        o = hol("https://api.coingecko.com/api/v3/coins/%s/ohlc"
                "?vs_currency=usd&days=30" % cid, key)
        time.sleep(PAUSE)
        habw = labw = float("nan")
        if isinstance(o, list) and len(o) > 20:
            hh, ll = [], []
            for ms, op, hi, lo, cl in o:
                s0 = dt.datetime.fromtimestamp(ms / 1000.0, dt.UTC)
                fenster = [(s0 + dt.timedelta(hours=k)).strftime("%Y-%m-%d %H:00")
                           for k in range(4)]
                bhs = [bh[x] for x in fenster if x in bh]
                bls = [bl[x] for x in fenster if x in bl]
                if len(bhs) == 4 and hi:
                    hh.append((max(bhs), float(hi)))
                if len(bls) == 4 and lo:
                    ll.append((min(bls), float(lo)))
            if len(hh) > 20:
                ah = np.array([x[0] for x in hh]); bhx = np.array([x[1] for x in hh])
                habw = float(np.median(np.abs(bhx - ah) / np.maximum(ah, 1e-12))) * 100
            if len(ll) > 20:
                al = np.array([x[0] for x in ll]); blx = np.array([x[1] for x in ll])
                labw = float(np.median(np.abs(blx - al) / np.maximum(al, 1e-12))) * 100
        # ── F3: ATR aus der CoinGecko-Preisreihe gegen Binance-ATR ───
        gem = sorted({stunde_aus_ms(ms) for ms, _p in (d.get("prices") or [])}
                     & set(st))
        atr_v = float("nan")
        if len(gem) > 300:
            cgp = {stunde_aus_ms(ms): float(px)
                   for ms, px in (d.get("prices") or []) if px}
            reihe = np.array([cgp[x] for x in gem])
            pos = {x: i for i, x in enumerate(st)}
            idx = np.array([pos[x] for x in gem])
            # ⚠️⚠️ DERSELBE SCHAETZER AUF BEIDEN SEITEN. Im Probelauf stand
            # hier `atr_aus_schluessen(CoinGecko)` gegen
            # `atr_tag_relativ(Binance)` - das Verhaeltnis 0,46 mischte
            # dann den QUELLEN-Unterschied mit der bekannten
            # Skalendifferenz der Methode (0,48x laut 2.616) und war
            # nicht lesbar. Jetzt: Renditeschaetzer gegen Renditeschaetzer,
            # damit nur die QUELLE uebrig bleibt.
            atr_cg = atr_aus_schluessen(reihe)
            atr_bn_gleich = atr_aus_schluessen(cc[idx])
            mb = np.nanmedian(atr_bn_gleich); mc = np.nanmedian(atr_cg)
            if mb and np.isfinite(mb) and np.isfinite(mc):
                atr_v = float(mc / mb)
        print("  %-8s %7d %9.3f%% %10.5f %9.3f%% %9.3f%% %10.3f"
              % (sym, len(paare), abw, korr, habw, labw, atr_v), flush=True)
        zeilen.append((sym, abw, korr, habw, labw, atr_v))

    if not zeilen:
        print("  keine Daten")
        return 1
    print()
    print("  ZUSAMMENFASSUNG ueber %d Symbole (Median)" % len(zeilen))
    for i, name in ((1, "Schlusskurs-Abweichung"), (2, "Korrelation"),
                    (3, "High-Abweichung"), (4, "Low-Abweichung"),
                    (5, "ATR-Verh. CG/BN, GLEICHER Schaetzer")):
        w = np.array([z[i] for z in zeilen], float)
        w = w[np.isfinite(w)]
        if not len(w):
            continue
        einheit = "" if i in (2, 5) else " %"
        print("    %-30s %8.4f%s   (Spanne %.4f bis %.4f)"
              % (name, float(np.median(w)), einheit, float(w.min()),
                 float(w.max())))
    print()
    print("  ⚠️ Ein Unterschied ist kein Fehler: CoinGecko mittelt ueber")
    print("     Boersen, Binance ist eine einzelne. Die Frage ist, ob er")
    print("     KLEIN GEGEN DEN EFFEKT ist.")

    # ══ BTC - traegt die Bewertung dort? ════════════════════════════
    print()
    print("=" * 100)
    print("TRAEGT DIE BEWERTUNG AUF BTC? (aus 9 Messwerkzeugen "
          "ausgeschlossen, im Betrieb freigegeben)")
    if "BTC" not in kurse:
        print("  BTC nicht in der Messbasis")
        return 0
    st, h, l, cc, v = kurse["BTC"]
    atr = atr_tag_relativ(h, l, cc)
    e = ema(cc, EMA_L)
    with np.errstate(divide="ignore", invalid="ignore"):
        w = (cc - e) / np.maximum(atr * cc, 1e-12)
    gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
    gu[:VORLAUF] = False
    gu[max(0, len(cc) - H):] = False
    sel = np.flatnonzero(gu)
    r = trailing(h, l, cc, atr, TW, H)[sel]
    p = r * TW * atr[sel]
    ww = w[sel]
    sig = ww >= SW
    print("  %d Anker · %d Signale (%.1f %% der Anker)"
          % (len(sel), int(sig.sum()), 100 * sig.mean()))
    if sig.sum() >= 50:
        rng = np.random.default_rng(SAAT)
        k = int(sig.sum())
        nb = [float(p[rng.choice(len(p), size=k, replace=False)].mean())
              for _ in range(N.NULL_ZIEHUNGEN)]
        b90 = float(np.percentile(np.array(nb), N.NULL_PERZENTIL)) * 100
        print("  ALLE Anker      : %+.4f %%" % (100 * float(p.mean())))
        print("  SIGNALE         : %+.4f %%  (E[R] %+.4f)"
              % (100 * float(p[sig].mean()), float(r[sig].mean())))
        print("  Nullband 90     : %+.4f %%" % b90)
        print("  ➤ %s" % ("✔ die Bewertung traegt auch auf BTC"
                          if 100 * float(p[sig].mean()) > b90 else
                          "⛔ auf BTC traegt sie NICHT"))
        print("  ⚠️ EIN Symbol - das Band ist breit, und ein Symbol ist")
        print("     keine Menge. Der Befund gilt fuer BTC, sonst nichts.")
    else:
        print("  zu wenige Signale (%d)" % int(sig.sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
