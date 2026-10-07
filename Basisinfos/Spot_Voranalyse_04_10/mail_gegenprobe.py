"""Gegenprobe des Mailentwurfs (python Basisinfos/Spot_Voranalyse_04_10/mail_gegenprobe.py) - liest den ERZEUGTEN Text und rechnet aus SQL nach.

  G1 keine gesperrten Symbole in der Rangliste          G2 alle Krypto-Bestaende stehen im Bestand-Block
  G3 Klasse je Abschnitt gegen den Marktwert-Rang aus SQL (eigene Rechnung wie mk_gegenprobe)
  G4 Marke = max(0,65 x Hoch seit Kauf, 0,5 x Kauf), Kauf = Schluss am Folgetag des Stichtags - direkt aus SQL
  G5 Profilwerte (ausgegeben %, Gebuehren 365 T) direkt aus strukturprofil.db / gebuehren.db
  G6 Sprache: kein Kaufaufruf, keine e-Schreibweise, keine Dezimalpunkte bei Prozent/Mio./Mrd.
"""
import csv, os, re, sqlite3, sys
import numpy as np, pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TXT = open("Basisinfos/Spot_Voranalyse_04_10/mail_entwurf_beide_ebenen.md", encoding="utf-8").read()
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
ok_n = n = 0


def pruefe(name, ok, info=""):
    global ok_n, n
    n += 1; ok_n += bool(ok)
    print("%-6s %s %s" % (name, "gleich" if ok else "ABWEICHUNG", info))


rang = TXT.split("## Rangliste")[1].split("## Protokoll")[0]
bestand = TXT.split("## Dein Bestand")[1].split("## Rangliste")[0]
liste = re.findall(r"^- [★]+ \*\*([A-Z0-9]+)\*\*", rang, flags=re.M)
gesperrt = {r["binance"] for r in csv.DictReader(open("Basisinfos/symbol_zuordnung.csv", encoding="utf-8"), delimiter=";") if r["markt"] == "gesperrt"} | {"AUDIO", "MBL", "ONE"}
pruefe("G1", not (set(liste) & gesperrt), "Liste %d Coins, gesperrt darin: %s" % (len(liste), sorted(set(liste) & gesperrt)))
hb = [s for s, in sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True).execute("SELECT symbol FROM holdings WHERE quantity > 0")]
krypto = [s for s in hb if c.execute("SELECT 1 FROM price_history_ohlc WHERE assetklasse='krypto' AND symbol=? LIMIT 1", (s,)).fetchone() or s == "CANTON"]
fehlt = [s for s in krypto if "**%s**" % s not in bestand]
pruefe("G2", not fehlt, "Krypto-Bestand %d, fehlt im Block: %s" % (len(krypto), fehlt))

# G3 Klasse je Abschnitt
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import mk_messung as MK  # noqa: E402
t = MK.ENDE.replace(day=1)
abschnitte = {"H": rang.split("### Highcaps")[1].split("###")[0], "M": rang.split("### Midcaps")[1].split("###")[0], "S": rang.split("### Smallcaps")[1]}
out, _, _ = MK.klassen_mw(t)
for kl, txt in abschnitte.items():
    syms = re.findall(r"^- [★]+ \*\*([A-Z0-9]+)\*\*", txt, flags=re.M)
    falsch = [s for s in syms if out.get(s) != kl]
    pruefe("G3-%s" % kl, not falsch, "%d Coins, andere Klasse: %s" % (len(syms), falsch))

# G4 Marke direkt aus SQL
def kurse(s):
    return pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date>? ORDER BY date",
                       c, params=(s, t.date().isoformat())).close.dropna().values
def de2f(x):
    x = x.rstrip(",")
    return float(x.replace(".", "").replace(",", ".")) if "," in x else float(x)
for s in ["LTC", "NEO", "ONT", "DOT", "FIL", "UMA"]:
    m = re.search(r"\*\*%s\*\*.*?\*Marke:\* ([0-9,]+) \(Kurs am Folgetag des Stichtags ([0-9,]+)" % s, rang)
    if not m:
        pruefe("G4", False, "%s Marke nicht gefunden" % s); continue
    v = kurse(s)
    soll = max(0.65 * v.max(), 0.5 * v[0])
    ist = de2f(m.group(1)); kauf = de2f(m.group(2))
    pruefe("G4", abs(ist / soll - 1) < 0.002 and abs(kauf / v[0] - 1) < 0.002, "%s Marke Text %s / SQL %.6g · Kauf Text %s / SQL %.6g" % (s, m.group(1), soll, m.group(2), v[0]))

# G5 Profil und Gebuehren
p = sqlite3.connect("file:data/_spot/strukturprofil.db?mode=ro", uri=True)
for s in ["QNT", "LINK", "THETA"]:
    aus = p.execute("SELECT ausgegeben FROM profil WHERE symbol=?", (s,)).fetchone()[0]
    m = re.search(r"\*\*%s\*\*.*?fest; (\d+) %% sind ausgegeben" % s, TXT)
    pruefe("G5", m and int(m.group(1)) == round(100 * min(aus, 1)), "%s ausgegeben Text %s %% / DB %.1f %%" % (s, m.group(1) if m else "-", 100 * aus))
g = sqlite3.connect("file:data/_spot/gebuehren.db?mode=ro", uri=True)
for s in ["XLM", "ADA"]:
    v = g.execute("SELECT SUM(usd) FROM gebuehr WHERE symbol=? AND datum BETWEEN ? AND ?", (s, (t - pd.Timedelta(days=365)).date().isoformat(),
                                                                                          (t - pd.Timedelta(days=1)).date().isoformat())).fetchone()[0]
    m = re.search(r"\*\*%s\*\*.*?Nutzer zahlten in den letzten 12 Monaten ([0-9,]+) Mio\. \$" % s, TXT)
    pruefe("G5", m and abs(de2f(m.group(1)) - v / 1e6) < 0.6, "%s Gebuehren Text %s Mio / DB %.2f Mio" % (s, m.group(1) if m else "-", v / 1e6))

# G6 Sprache
roh = re.sub(r"kein Kaufsignal|Kauf am Folgetag|Kurs am Folgetag des Stichtags|Kaufkurses|seit dem Kauf", "", TXT)
pruefe("G6a", not re.search(r"\b(kaufen|Kaufsignal|jetzt einsteigen)\b", roh, flags=re.I), "kein Kaufaufruf")
pruefe("G6b", "e-0" not in TXT and "e+0" not in TXT, "keine e-Schreibweise")
pruefe("G6c", not re.search(r"\d\.\d+ ?(%|Mio|Mrd|Bio|-Fach|Jahren)", TXT), "keine Dezimalpunkte bei Prozent/Mio./Mrd./Jahren")
print("\n%d von %d gleich" % (ok_n, n))
