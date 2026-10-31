# -*- coding: utf-8 -*-
"""G16 Wale STUFE 2 — VORANALYSE (31.10.2026, Nutzer: *„a, Voranalyse Stufe 2 starten prüfen und gegenprüfen“*).

Frage der Stufe 2 (Messplan W §14, Zeile „trägt“): hebt der Spot-Großfluss E die REGEL0, ohne sie irgendwo zu verschlechtern?
Diese Voranalyse misst nur, was VOR einem Messplan feststehen muss — sie sieht E auf keinem REGEL0-Einstieg an:

    A  Einstiege je Menge, Symbole, Jahre, Überschneidung mit dem schon Gesehenen (Kern, die sechs aus Fassung 4)
    B  Binance-Spotmarkt je Symbol (nur dort gibt es Wal-Daten), Monat für Monat per HEAD — kein Download
    C  Abdeckung: welche Einstiege bekämen ein E (Vorlauf 180 T Schätzfenster + 120 T Rang, Verzug)
    D  Download-Umfang (zip) für die noch fehlenden Symbole
    E  Betrieb: wann liegt die Tagesdatei vor (Last-Modified der letzten Tage)

    python -X utf8 Basisinfos/Rechenkern_02_10/p103_wale_s2_voranalyse.py            # A-E, Ausgabe .txt daneben

Nur lesend: Einstiegsdateien und HEAD-Anfragen; Produktions-DB nicht berührt (hier gibt es sie nicht, Desktop).
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
B0 = pd.Timestamp("2020-01-01")                      # Stundenzähler der Einstiegsdateien (wie p64/p71)
KERN = ("BTC", "ETH", "SOL")
F4 = ("BNB", "ADA", "TRX", "AVAX", "LINK", "NEAR")   # Fassung 4: auf denselben Tagen schon gesehen
GELADEN = KERN + F4                                  # liegt in data/_wale/wale_voll.db
START = date(2023, 1, 1)                             # wie Fassung 4
ENDE = date(2026, 8, 31)                             # letzter Einstieg der Referenz (Stunde 58436)
VORLAUF = 180 + 120                                  # Schätzfenster + Mindestzahl für den Rang (Messplan W Fassung 2)
CACHE = os.path.join("data", "_wale", "s2_head.csv")
URL_M = "https://data.binance.vision/data/spot/monthly/aggTrades/{p}/{p}-aggTrades-{j:04d}-{m:02d}.zip"
URL_D = "https://data.binance.vision/data/spot/daily/aggTrades/{p}/{p}-aggTrades-{d}.zip"
H = {"User-Agent": "Mozilla/5.0 (TradingInfoTool Forschung)"}
AUS = []


def zeige(s=""):
    print(s, flush=True)
    AUS.append(s)


def einstiege():
    E = {}
    for m in MENGEN:
        e = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % m), sep=";")
        e["zeit"] = B0 + pd.to_timedelta(e.stunde, unit="h")
        e["ein"] = e.zeit + pd.Timedelta(hours=1)      # Einstiegskurs = SCHLUSS der Einstiegsstunde (p71: C[stunde])
        E[m] = e
    return E


def monate():
    j, m, out = START.year, START.month, []
    while (j, m) <= (ENDE.year, ENDE.month):
        out.append((j, m))
        j, m = (j + 1, 1) if m == 12 else (j, m + 1)
    return out


def head(url):
    for v in range(4):
        try:
            r = requests.head(url, headers=H, timeout=30, allow_redirects=True)
            if r.status_code == 200:
                return int(r.headers.get("Content-Length", 0)), r.headers.get("Last-Modified", "")
            if r.status_code == 404:
                return -1, ""
        except requests.RequestException:
            pass
        time.sleep(2 * (v + 1))
    return None, ""


def kandidaten(sym):
    k = [sym + "USDT"]
    if sym.startswith("1000"):
        k.append(sym[4:] + "USDT")
    return k


def spot_tabelle(symbole):
    """Je Symbol und Monat: Größe der Monatsdatei (Byte), -1 = keine Datei. Zwischenspeicher, weil 8.000 HEAD-Anfragen."""
    if os.path.exists(CACHE):
        T = pd.read_csv(CACHE)
        if set(symbole) <= set(T.symbol):
            return T
    auftraege = [(s, p, j, m) for s in symbole for p in kandidaten(s) for (j, m) in monate()]
    with ThreadPoolExecutor(16) as ex:
        erg = list(ex.map(lambda a: head(URL_M.format(p=a[1], j=a[2], m=a[3]))[0], auftraege))
    T = pd.DataFrame([(s, p, "%04d-%02d" % (j, m), b) for (s, p, j, m), b in zip(auftraege, erg)],
                     columns=["symbol", "paar", "monat", "bytes"])
    T.to_csv(CACHE, index=False)
    return T


def abdeckung(E, T):
    """Je Menge: Maske 'Einstieg bekäme ein E' (E des Vortags braucht Daten bis t-1 und VORLAUF Tage davor; eingestellte Paare:
    Daten bis zum Ende des letzten Archivmonats). Dazu das Spotpaar, Beginn und Ende je Symbol."""
    vorh = T[T.bytes > 0]
    paar = vorh.groupby("symbol").paar.agg(lambda x: x.value_counts().index[0])
    erst = vorh.groupby(["symbol", "paar"]).monat.min()
    letzt = vorh.groupby(["symbol", "paar"]).monat.max()
    beginn = {s: max(pd.Timestamp(START), pd.Timestamp(erst[(s, p)] + "-01")) for s, p in paar.items()}
    ende = {s: pd.Timestamp(letzt[(s, paar[s])] + "-01") + pd.offsets.MonthEnd(0) for s in paar.index}
    M = {}
    for m, e in E.items():
        vortag = e.ein.dt.normalize() - pd.Timedelta(days=1)
        b, n = e.symbol.map(beginn), e.symbol.map(ende)
        M[m] = (b.notna() & (vortag >= b + pd.Timedelta(days=VORLAUF)) & (vortag <= n)).to_numpy()
    return M, paar, erst, letzt


def main():
    zeige("VORANALYSE G16 STUFE 2 (Gerät %s, %s) · Einstiege kern48jbz_<Menge> · Spot-Archiv data.binance.vision"
          % (os.environ.get("COMPUTERNAME", "?"), datetime.now().isoformat(timespec="seconds")))
    E = einstiege()

    # ── A ──
    zeige("\n══ A  EINSTIEGE ══")
    alle = set()
    for m, e in E.items():
        alle |= set(e.symbol)
        j = e.jahr.value_counts().sort_index()
        zeige("  %-13s %6d Einstiege · %3d Symbole · %s · %s .. %s" % (
            m, len(e), e.symbol.nunique(), " ".join("%d %d" % (a, b) for a, b in j.items()),
            e.zeit.min().date(), e.zeit.max().date()))
        k = e.symbol.isin(KERN).sum()
        f = e.symbol.isin(F4).sum()
        zeige("                davon Kern %d (%.1f %%) · Fassung-4-Werte %d (%.1f %%) · übrige %d" % (
            k, 100 * k / len(e), f, 100 * f / len(e), len(e) - k - f))
    zeige("  Vereinigung der vier Mengen: %d Symbole" % len(alle))
    tage = {m: e.zeit.dt.normalize().value_counts() for m, e in E.items()}
    for m, t in tage.items():
        zeige("  %-13s Einstiegstage %d · je Tag Median %d, 90. Perzentil %d, Höchstwert %d" % (
            m, len(t), t.median(), t.quantile(0.9), t.max()))

    # ── B ──
    zeige("\n══ B  BINANCE-SPOTMARKT JE SYMBOL (Monatsdateien %s .. %s, HEAD) ══" % (START, ENDE))
    T = spot_tabelle(sorted(alle))
    if T.bytes.isna().any():
        zeige("  ⚠ %d HEAD-Anfragen ohne Antwort — Ergebnis unvollständig" % T.bytes.isna().sum())
    vorh = T[T.bytes > 0]
    MASKE, paar, erst, letzt = abdeckung(E, T)
    ohne = sorted(alle - set(paar.index))
    zeige("  mit Spotmarkt: %d von %d Symbolen · ohne: %d" % (len(paar), len(alle), len(ohne)))
    zeige("  ohne Spotmarkt (nur Terminmarkt oder anderer Name): %s" % " ".join(ohne))
    weg = sorted(s for s in paar.index if letzt[(s, paar[s])] < "%04d-%02d" % (ENDE.year, ENDE.month))
    zeige("  davon eingestellt vor %04d-%02d (Archiv endet früher; gehören zur Grundgesamtheit): %d · %s" % (
        ENDE.year, ENDE.month, len(weg), " ".join(weg)))
    for m, e in E.items():
        zeige("    %-13s Einstiege mit E auf eingestellten Paaren: %d" % (m, (MASKE[m] & e.symbol.isin(weg).to_numpy()).sum()))
    umbenannt = {s: p for s, p in paar.items() if p != s + "USDT"}
    if umbenannt:
        zeige("  anderer Spotname: %s" % ", ".join("%s→%s" % kv for kv in umbenannt.items()))

    # ── C ──
    zeige("\n══ C  ABDECKUNG: welcher Einstieg bekäme ein E (Daten ab %s bzw. ab Spotbeginn, Vorlauf %d T, E des Vortags) ══"
          % (START, VORLAUF))
    for m, e in E.items():
        hat_spot = e.symbol.isin(paar.index)
        ok = pd.Series(MASKE[m], index=e.index)
        zeige("  %-13s %6d von %6d Einstiegen mit E (%.1f %%) · ohne Spotmarkt %d · zu jung/zu früh %d" % (
            m, ok.sum(), len(e), 100 * ok.mean(), (~hat_spot).sum(), (hat_spot & ~ok).sum()))
        for j in (2024, 2025, 2026):
            s = e.jahr == j
            zeige("                %d: %5d von %5d (%.1f %%)" % (j, (ok & s).sum(), s.sum(), 100 * (ok & s).mean() / max(s.mean(), 1e-9)))
        neu = ok & ~e.symbol.isin(GELADEN)
        zeige("                davon UNGESEHEN (ohne Kern und Fassung-4-Werte): %d Einstiege, %d Symbole" % (
            neu.sum(), e.symbol[neu].nunique()))
        e["mit_e"] = ok

    # ── D ──
    zeige("\n══ D  DOWNLOAD-UMFANG (zip, %s .. %s; Kern und Fassung-4-Werte liegen schon vor) ══" % (START, ENDE))
    noetig = [s for s in paar.index if s not in GELADEN]
    G = vorh[vorh.symbol.isin(noetig) & (vorh.paar == vorh.symbol.map(paar))]
    gb = G.bytes.sum() / 1e9
    je = G.groupby("symbol").bytes.sum().sort_values(ascending=False) / 1e9
    zeige("  %d Symbole · %.1f GB zip · %d Monatsdateien" % (len(noetig), gb, len(G)))
    zeige("  größte: %s" % " · ".join("%s %.1f" % kv for kv in je.head(12).items()))
    zeige("  kleinste: %s" % " · ".join("%s %.2f" % kv for kv in je.tail(6).items()))
    zeige("  Verteilung je Symbol (GB): Median %.2f · 90. Perzentil %.2f · Summe der 10 größten %.1f (%.0f %%)" % (
        je.median(), je.quantile(0.9), je.head(10).sum(), 100 * je.head(10).sum() / gb))
    # nur die Symbole, die tatsächlich Einstiege mit E liefern
    mit_e = set().union(*[set(e.symbol[e.mit_e]) for e in E.values()]) - set(GELADEN)
    gb2 = G[G.symbol.isin(mit_e)].bytes.sum() / 1e9
    zeige("  davon Symbole, die Einstiege mit E liefern: %d · %.1f GB" % (len(mit_e), gb2))

    # ── E ──
    zeige("\n══ E  BETRIEB: Erscheinungszeit der Tagesdatei (Last-Modified, letzte 10 Tage) ══")
    heute = datetime.now(timezone.utc).date()
    probe = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT"]
    zeilen = []
    for p in probe:
        for k in range(1, 11):
            d = (heute - timedelta(days=k)).isoformat()
            b, lm = head(URL_D.format(p=p, d=d))
            if b and b > 0 and lm:
                t = pd.Timestamp(lm).tz_convert("UTC")
                zeilen.append((p, d, (t - pd.Timestamp(d, tz="UTC") - pd.Timedelta(days=1)) / pd.Timedelta(hours=1), b))
    Z = pd.DataFrame(zeilen, columns=["paar", "tag", "std_nach_tagesende", "bytes"])
    if len(Z):
        zeige("  %d Dateien · Stunden nach Tagesende (00:00 UTC): Median %.1f · Höchstwert %.1f · Mindestwert %.1f" % (
            len(Z), Z.std_nach_tagesende.median(), Z.std_nach_tagesende.max(), Z.std_nach_tagesende.min()))
        for p, g in Z.groupby("paar"):
            zeige("    %-9s %s" % (p, " ".join("%.1f" % x for x in g.std_nach_tagesende)))
        zeige("  Größe je Tag (MB, zip): %s" % " · ".join("%s %.1f" % (p, g.bytes.median() / 1e6) for p, g in Z.groupby("paar")))
    else:
        zeige("  ⚠ keine Tagesdatei der letzten 10 Tage abrufbar")

    with open(os.path.join(HIER, "p103_wale_s2_voranalyse.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(AUS) + "\n")


if __name__ == "__main__":
    main()
