"""Gegenpruefung der Bauumfang-Vorlage Spot §39 - jede Behauptung gegen ihre Quelle, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/sb39_pruefung.py

  V1 Code-Anschluesse existieren (Datei, Funktion, Konstante, Schalter)
  V2 Datenlage am NB laut Teilexport T440 (vorhanden / fehlt)
  V3 jede zitierte Messzahl steht so in ihrer Ergebnisdatei
  V4 jede Zeile der Vorlage nennt Grundlage oder NB-Stand (keine leeren Pflichtspalten)
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "ok" if gut else "FEHLT/FALSCH", info))


def lies(p):
    return io.open(os.path.join(PROJ, p), encoding="utf-8").read()


def enthaelt(p, muster):
    return re.search(muster, lies(p), re.M) is not None


# V1
for datei, muster, was in [
    ("agent/positionsfuehrung.py", r"^def lade\(", "Positionsfuehrung je Symbol (B1/B2)"),
    ("agent/binance_ankuendigungen.py", r"^KATALOGE = \(161, 49\)", "O29 laedt 161/49, nicht 48 (D2)"),
    ("agent/binance_ankuendigungen.py", r"^def hole\(", "O29-Abruf (B3)"),
    ("scheduler/background.py", r"^def ausstiegs_job\(", "Stop-Nachzieh-Mail je Signal (A6/O19)"),
    ("scheduler/background.py", r"get_stablecoin_supply\(\)", "Stablecoins nur Momentanwert (D1)"),
    ("scheduler/background.py", r"^def lagebild_reihen_job\(", "FRED/WALCL-Job (C1-Kontext)"),
    ("api/macro.py", r'"m2_geldmenge": "M2SL"', "M2 aus FRED (C1/B2)"),
    ("agent/regel0_groesse.py", r"^def spot_kette_angehalten\(", "Schalter alte Spot-Kette (A5)"),
    ("Basisinfos/regel0_betrieb.yaml", r"^spot_kette_angehalten: true", "alte Spot-Kette angehalten (A5 erledigt)"),
    ("database/db.py", r"avg_buy_price_eur", "Einstand in holdings (B2)"),
]:
    pruefe("V1", enthaelt(datei, muster), "%s: %s" % (was, datei))
db = lies("database/db.py")
m = re.search(r"CREATE TABLE IF NOT EXISTS holdings \((.*?)\);", db, re.S)
pruefe("V1", m and "rolle" not in m.group(1).lower() and "starttag" not in m.group(1).lower(), "holdings OHNE Rolle/Starttag (A1 ist Neubau)")

# V2
nb = io.open(r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/nb_betriebsdaten_T440.txt", encoding="utf-8").read()
for tab in ("holdings", "price_cache", "bitpanda_katalog", "bitpanda_wallet_saldo", "externe_reihe", "macro_snapshot", "stundenkurse", "umlaufmenge", "price_history_ohlc"):
    pruefe("V2", re.search(r"^  %s +~\d+ Zeilen" % tab, nb, re.M) is not None, "NB hat %s" % tab)
pruefe("V2", "richtung_historie" not in nb, "NB hat KEINE richtung_historie (BTCDOM fehlt -> D1)")

# V3
S = "Basisinfos/Spot_Voranalyse_04_10/"
for datei, muster, was in [
    (S + "fb_messung.txt", r"URTEIL ab 2024 Z1 x3: .*Korb \+5\.50 Pp .*TRAEGT", "B1 Mitnahme x3 +5,5 Pp, traegt"),
    (S + "am_kalibrierung.txt", r"3 von 3: .*Season-Tage +26\.0 %", "C1 3/3 -> 26 % Season-Tage"),
    (S + "am_kalibrierung.txt", r"BTC \+ M2, Stablecoins fehlen +Tage +0 ", "C1 heutiges Muster nie dagewesen"),
    (S + "c2_messung.txt", r"C2-b Upbit-Listing ab 2024: .*Korb -9\.97 Pp .*SCHADET", "B3 Upbit -10 Pp, schadet"),
    (S + "c2_messung.txt", r"verpasst \(Meldung bis \+4 h\) Median \+12\.0 %", "B3 Upbit erste 4 h +12 %"),
    (S + "c2_messung.txt", r"\+4 h / 30 T: -20\.1 Pp", "B3 Futures-Start 30 T -20 Pp"),
    (S + "v32_vorpruefung.txt", r"H +Kauf .*halbe Spanne 0\.36 %", "D6 Kosten H 0,36 %"),
    (S + "v32_vorpruefung.txt", r"M +Kauf .*halbe Spanne 0\.88 %", "D6 Kosten M 0,88 %"),
    (S + "v32_vorpruefung.txt", r"S +Kauf .*halbe Spanne 3\.20 %", "D6 Kosten S 3,20 %"),
    (S + "e33_analyse.txt", r"halten 45 % · mit Mitnahme x3 42 %", "B2 L-Preis -45 %/Jahr"),
    (S + "e33_analyse.txt", r"Dominanz-Spitze 44 % \(Lift 1\.65\)", "C3 Dominanz-Spitze Lift 1,65"),
    (S + "k37_messung.txt", r"K-H1-H ab 2024: .*TRAEGT NICHT", "A4 Momentum H traegt nicht"),
    (S + "k37_messung.txt", r"Dominanz-Spitze \+6\.3 Pp \(n 71\)", "A4 Schatten-Hypothese +6,3 Pp n 71"),
]:
    pruefe("V3", enthaelt(datei, muster), "%s (%s)" % (was, os.path.basename(datei)))

# V4
doc = lies("Basisinfos/Voranalyse_Spot_Neubau_04_10.md")
teil = doc.split("## 39. Bauumfang Spot")[1]
zeilen = [z for z in teil.splitlines() if re.match(r"\| \*\*[A-D]\d\*\* \|", z)]
leer = [z[:20] for z in zeilen if any(c.strip() == "" for c in z.strip("|").split("|"))]
pruefe("V4", len(zeilen) >= 20 and not leer, "%d Punkte, davon mit leerer Pflichtspalte %d %s" % (len(zeilen), len(leer), leer))
print("\n%d von %d bestaetigt" % (ok, n))
