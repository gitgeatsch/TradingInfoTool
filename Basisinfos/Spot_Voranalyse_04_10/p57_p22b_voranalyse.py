"""P57 VORANALYSE P22b - Mengenreihe fuer Coins ausserhalb der Binance-Messmenge (Spot §56/§57; Nutzer 15.10.: "Voranalyse P22b
vorbereiten, pruefen und gegenpruefen"). Nur lesend auf Projektdaten; Abrufe frei (CoinGecko market_chart, Binance exchangeInfo);
alles Geschriebene liegt im Wegwerf-Ordner (D:).

    python Basisinfos/Spot_Voranalyse_04_10/p57_p22b_voranalyse.py <Prod-Sicherung .db.gz>

TEIL 1  Binance-Spot: welche der Kandidaten haben ein USDT-Paar (TRADING)? -> die kaemen in Variante A in die turnover-Messbasis
TEIL 2  Abruf und Abdeckung: 365 T market_chart je CoinGecko-ID, dieselbe Zerlegung wie der Vollabruf (hole_umlaufmenge_cg.zerlege,
        Buendelfaktor), Urteil nach MIND_PUNKTE; BIO: warum verworfen?
TEIL 3  Grundgesamtheit B4 (stehende Regel): Stichtag 01.09.2026 in NB-Lage (wie p22-Pruefstand) - HEUTE gegen Variante A (neue
        Coins in derselben Mengendatei). Wie viele Coins wechseln Klasse und Fuenftel - im ganzen Universum und im Bestand?
        Variante B (eigene Zusatztabelle, nur die Verwaesserung liest sie) laesst B4 per Bau unberuehrt; geprueft wird das hier mit.
TEIL 4  turnover: Wer liest ihn heute (raenge -> nur die angehaltene Rollen-Kette)? Wie viele Symbole kaemen dazu?
TEIL 5  Vorschau: Verwaesserung 90 T und Freigabe-Rhythmus der neuen Coins zum letzten Datentag
"""
import gzip
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import date

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
import wegwerf  # noqa: E402,F401

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

import agent.spot_abbau as SA  # noqa: E402
import agent.verwaesserung as VW  # noqa: E402
import config as C  # noqa: E402
import hole_umlaufmenge_cg as HU  # noqa: E402

KANDIDATEN = ["HYPE", "XDC", "KAS", "ASTER", "AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "SUPRA", "CANTON", "MON", "VSN", "BIO"]
AUS = {"EURCV": "Stablecoin"}
UEBERNOMMEN = ["AIOZ", "AKT", "BRETT", "CAT", "GRIFFAIN", "HYPE", "KAS", "MORPHO", "PLUME", "SUPRA"]
HEUTE_B4 = date(2026, 9, 5)
STICH = "2026-09-01"


def main():
    T = tempfile.mkdtemp(prefix="p57_")
    cfg = yaml.safe_load(open("Basisinfos/config.yaml", encoding="utf-8"))
    ids = {e["symbol"]: e.get("coingecko_id") for e in cfg["watchlist"] if e.get("symbol") in KANDIDATEN}
    print("P57 VORANALYSE P22b · Kandidaten %d (ohne %s) · Wegwerf %s\n" % (len(KANDIDATEN), ", ".join("%s: %s" % kv for kv in AUS.items()), T))

    # ══ TEIL 1 Binance-Spot ══════════════════════════════════════════════════════════════════════════════════════════════════
    st, info = HU.hole(HU.BINANCE_INFO)
    status = {s["baseAsset"].upper(): s.get("status") for s in (info or {}).get("symbols", []) if s.get("quoteAsset") == "USDT"}
    print("TEIL 1  Binance-Spot (USDT-Paar): %s" % " · ".join("%s %s" % (s, status.get(s, "-")) for s in KANDIDATEN))
    mit_paar = [s for s in KANDIDATEN if status.get(s) == "TRADING"]
    m = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
    in_mess = {r[0] for r in m.execute("SELECT DISTINCT symbol FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'")}
    m.close()
    print("        mit TRADING-Paar: %s · davon schon in der Messbasis (Kurse): %s\n" % (", ".join(mit_paar) or "-", ", ".join(s for s in mit_paar if s in in_mess) or "-"))

    # ══ TEIL 2 Abruf und Abdeckung ═══════════════════════════════════════════════════════════════════════════════════════════
    c = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    bio = c.execute("SELECT * FROM abruf_symbol WHERE symbol='BIO'").fetchone()
    c.close()
    zus = os.path.join(T, "zusatz.db")
    z = sqlite3.connect(zus)
    z.execute("CREATE TABLE umlaufmenge (symbol TEXT, datum TEXT, wert REAL, PRIMARY KEY (symbol, datum))")
    erg2 = {}
    for s in KANDIDATEN:
        cid = ids.get(s)
        if not cid:
            erg2[s] = ("keine ID", 0, 0, 0, 0.0)
            continue
        stc, d = HU.hole("%s/coins/%s/market_chart?vs_currency=usd&days=%d&interval=daily" % (HU.CG, cid, HU.TAGE))
        if not isinstance(d, dict):
            erg2[s] = ("Abruf %s" % stc, 0, 0, 0, 0.0)
        else:
            f, _ = HU.vervielfacher(s)
            reihe, weg, spr, gr = HU.zerlege(s, d, f)
            urteil = "ok" if len(reihe) >= HU.MIND_PUNKTE else "verworfen"
            if urteil == "ok":
                z.executemany("INSERT OR REPLACE INTO umlaufmenge VALUES (?,?,?)", reihe)
            erg2[s] = (urteil, len(reihe), weg, spr, gr)
        time.sleep(HU._PAUSE[0])
    z.commit()
    z.close()
    print("TEIL 2  Abruf CoinGecko market_chart 365 T (Zerlegung wie der Vollabruf, Mindestpunkte %d):" % HU.MIND_PUNKTE)
    for s, (u, n, weg, spr, gr) in erg2.items():
        print("        %-9s %-10s Punkte %3d · ohne Wert %3d · Spruenge >=10 %% %2d · groesster %5.1f %%  (%s)" % (s, u, n, weg, spr, 100 * gr, ids.get(s)))
    print("        BIO im Vollabruf 21.09.: %s\n" % (bio,))

    # ══ TEIL 3 Grundgesamtheit B4 ════════════════════════════════════════════════════════════════════════════════════════════
    prod_q = os.path.join(T, "prod.db")
    with gzip.open(sys.argv[1], "rb") as f, open(prod_q, "wb") as g:
        shutil.copyfileobj(f, g)
    kop = os.path.join(T, "kopie.db")
    q = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
    k = sqlite3.connect(kop)
    k.execute("CREATE TABLE price_history_ohlc (symbol TEXT, assetklasse TEXT, currency TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, "
              "volume REAL, fetched_at TEXT, quelle TEXT, PRIMARY KEY (symbol, currency, date))")
    for s, letzt in q.execute("SELECT symbol, MAX(date) FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' GROUP BY symbol").fetchall():
        if s in UEBERNOMMEN:
            continue
        ab = (pd.Timestamp(letzt) - pd.Timedelta(days=499)).date().isoformat()
        k.executemany("INSERT INTO price_history_ohlc VALUES (?,?,?,?,?,?,?,?,?,?,?)", q.execute(
            "SELECT symbol, assetklasse, currency, date, open, high, low, close, volume, fetched_at, quelle FROM price_history_ohlc "
            "WHERE symbol=? AND assetklasse='krypto' AND currency='USD' AND date >= ?", (s, ab)).fetchall())
    k.commit()
    k.close()

    def http(sym):
        return [(dd[:10], cc) for dd, cc in q.execute("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' AND "
                                                       "currency='USD' ORDER BY date", (sym,))]

    def lauf(name, mit_zusatz):
        o = os.path.join(T, name)
        os.makedirs(o)
        shutil.copy(kop, os.path.join(o, SA.KOPIE))
        shutil.copy("data/umlaufmenge_cg.db", os.path.join(o, SA.UMLAUF))
        if mit_zusatz:
            u = sqlite3.connect(os.path.join(o, SA.UMLAUF))
            u.execute("ATTACH DATABASE ? AS z", (zus,))
            u.execute("INSERT OR IGNORE INTO umlaufmenge SELECT symbol, datum, wert FROM z.umlaufmenge")
            u.commit()
            u.execute("DETACH DATABASE z")
            u.close()
        shutil.copy(prod_q, os.path.join(o, "prod.db"))
        cp = sqlite3.connect(os.path.join(o, "prod.db"))
        cp.row_factory = sqlite3.Row
        try:
            e = SA.lauf(cp, o, C.get_watchlist(), HEUTE_B4, http, mit_tabelle=True)
        finally:
            cp.close()
        a = sqlite3.connect(os.path.join(o, SA.ABLAGE))
        vu = {r[0]: r[1:] for r in a.execute("SELECT symbol, klasse, verw90, fuenftel FROM verw_universum WHERE stichtag=?", (STICH,))}
        bf = {r[0]: r[1:] for r in a.execute("SELECT symbol, reihe, klasse, fuenftel FROM abbau_fuenftel WHERE stichtag=?", (STICH,))}
        a.close()
        return e, e["_tabelle"].set_index("sym"), vu, bf

    e0, z0, v0, b0 = lauf("heute", False)
    eA, zA, vA, bA = lauf("variante_A", True)
    q.close()
    gem = z0.index.intersection(zA.index)
    kl_w = [s for s in gem if z0.kl[s] != zA.kl[s]]
    q_w = [s for s in gem if z0.q[s] == z0.q[s] and zA.q[s] == zA.q[s] and z0.q[s] != zA.q[s]]
    b_w = [s for s in b0 if b0[s][2] != bA.get(s, (None,) * 3)[2]]   # KORREKTUR: Zeile = (reihe, klasse, fuenftel)
    vq_w = [s for s in v0 if (v0[s][2] or 0) != (vA.get(s, (None, None, None))[2] or 0)]
    print("TEIL 3  Grundgesamtheit B4, Stichtag %s, NB-Lage (Universum heute %d, Variante A %d):" % (STICH, len(z0), len(zA)))
    print("        Variante A - Klasse gewechselt: %d (%s)" % (len(kl_w), ", ".join("%s %s->%s" % (s, z0.kl[s], zA.kl[s]) for s in kl_w[:12])))
    print("        Variante A - B4-Fuenftel gewechselt: %d von %d (%.1f %%) · im BESTAND: %d (%s)" % (
        len(q_w), len(gem), 100 * len(q_w) / max(len(gem), 1), len(b_w),
        ", ".join("%s %s->%s" % (s, b0[s][2], bA.get(s, (None,) * 3)[2]) for s in b_w) or "-"))
    print("        Variante A - Verwaesserungs-Fuenftel gewechselt: %d · B4 unteres Fuenftel heute %s / Variante A %s" % (
        len(vq_w), ",".join(e0["unten"]), ",".join(eA["unten"])))
    print("        Variante B (Zusatztabelle, B4 liest sie nicht): B4 bitgleich zu heute PER BAU - Klassen der neuen Coins bleiben die "
          "Umsatz-Klasse")
    neu_im_uni = [s for s in KANDIDATEN if s in z0.index]
    print("        Kandidaten im B4-Universum: %s (Klasse heute %s)\n" % (", ".join(neu_im_uni) or "-",
                                                                        ", ".join("%s %s" % (s, z0.kl[s]) for s in neu_im_uni)))

    # ══ TEIL 4 turnover ══════════════════════════════════════════════════════════════════════════════════════════════════════
    import agent.marktrang as MR
    print("TEIL 4  turnover: live_groesse %s · Leser von raenge(): nur agent/rollen_lauf.py (Rollen-Kette, angehalten seit 05.10., E-67)" % MR.live_groesse())
    print("        Variante A: Messbasis turnover = Symbolliste der Mengendatei -> + %d Symbole mit Binance-USDT-Paar (%s) - aendert die Raenge "
          "ALLER Coins, sobald die Kette wieder laeuft\n" % (len([s for s in mit_paar if erg2.get(s, ("",))[0] == "ok"]),
                                                            ", ".join(s for s in mit_paar if erg2.get(s, ("",))[0] == "ok") or "-"))

    # ══ TEIL 5 Vorschau ══════════════════════════════════════════════════════════════════════════════════════════════════════
    zz = sqlite3.connect(zus)
    d = pd.read_sql("SELECT symbol, datum, wert FROM umlaufmenge", zz)
    zz.close()
    d["datum"] = pd.to_datetime(d.datum.str[:10])
    R = {s: g.set_index("datum").wert.sort_index() for s, g in d.groupby("symbol")}
    letzt = d.datum.max()
    print("TEIL 5  Vorschau zum %s (Verwaesserung 90 T · Freigabe-Rhythmus):" % letzt.date())
    for s in KANDIDATEN:
        r = R.get(s)
        v = VW.wert(r, letzt) if r is not None else None
        rt = VW.rhythmus_text(VW.rhythmus(r, letzt)) if r is not None else None
        print("        %-9s %s%s" % (s, ("%+.1f %%" % (100 * np.expm1(v))) if v is not None else "-", (" · " + rt[:110]) if rt else ""))
    wegwerf.aufraeumen(T)


if __name__ == "__main__":
    main()
