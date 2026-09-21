# -*- coding: utf-8 -*-
"""WIE GROSS IST DIE turnover-ABDECKUNG - JE BEZUGSMENGE.

⚠️⚠️ WARUM ES DIESES WERKZEUG GIBT (21.09.2026). Nutzerfrage, woertlich:

    *„woher kommen die 59 Symbole das reicht für keine Abdeckung"*
    *„laut deiner Aussage ca. 80 Prozent abdeckung, gesamt oder unser
    Portfolio"*

Beide Male zurecht. Ich hatte vier verschiedene Abdeckungszahlen (99,
91, 19, 12 Prozent) ohne ihre Bezugsmenge genannt - eine davon war
schlicht falsch (Audit 21.09., Schritt 66).

⚠️ DIE LEHRE STEHT IM MEMORY: eine nackte Prozentzahl ist kein Befund.
Eine Abdeckung wird als „X von Y <was>" genannt oder gar nicht.

## Was hier beantwortet wird

    1  WOHER kommen die Symbole der laufenden Quelle - und warum so
       wenige
    2  Wie gross ist die Abdeckung je Bezugsmenge, die den Nutzer
       interessiert: Messmenge, eigener Bestand, Signale, HEBELsignale
    3  Was die Alternative (CoinGecko Free Float) daran aendern wuerde

## ⚠️ NUR LESEND

Alle Datenbanken mit `mode=ro`. Kein Netzabruf, kein Projektmodul, das
ueber `api_health` schreiben koennte.
"""
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                                # noqa: E402

# ⚠️⚠️ KEINE VORGABE. Das Werkzeug verlangt eine SICHERUNG - am
# Notebook waere `data/tradinginfotool.db` die Produktion, und ein
# Werkzeug mit dieser Vorgabe wuerde sie dort anfassen, sobald es
# jemand ohne Flagge ruft. Dieselbe Bedingung wie in
# `phase4_c_turnover_luecke.py`.
def _pfad(flagge, vorgabe=""):
    a = sys.argv[1:]
    return a[a.index(flagge) + 1] if flagge in a else vorgabe


BETRIEB = _pfad("--db")
if not BETRIEB or not os.path.exists(BETRIEB):
    raise SystemExit("Sicherung nicht gefunden - mit --db "
                     "<sicherung.db> setzen (NIE die Standard-DB)")
MESS = "data/messdaten.db"
SPLY = "data/onchain_historie.db"
FREI = "data/umlaufmenge_cg.db"


def ro(pfad):
    return sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)


print("=" * 104)
print("DIE turnover-ABDECKUNG - JE BEZUGSMENGE")
print("=" * 104)

# ------------------------------------------------------------------
# 1  DIE BEIDEN QUELLEN
# ------------------------------------------------------------------
sply_alle = {r[0].upper() for r in
             ro(SPLY).execute("SELECT DISTINCT symbol FROM splycur")}
# genau der Betriebsweg, einschliesslich Frischegrenze und Nennersperre
betrieb = set(MR.umlaufmengen(db_pfad="data/_gibt_es_nicht_.db",
                              datei=SPLY))
frei = {r[0].upper() for r in ro(FREI).execute(
    "SELECT DISTINCT u.symbol FROM umlaufmenge u "
    "  JOIN abruf_symbol a ON a.symbol = u.symbol "
    " WHERE a.urteil = 'ok'")}

print()
print("1  DIE LAUFENDE QUELLE: Coin Metrics Community API, Metrik `SplyCur`")
print("   " + "-" * 98)
print("   Angefragt wird fuer die EINGEFRORENE MESSMENGE V1, nicht fuer")
print("   den Markt  (`hole_fremdreihen.py splycur` -> `B.lade()`).")
print()
print("   %-52s %5d" % ("Symbole, fuer die Coin Metrics einen Wert hat:",
                        len(sply_alle)))
print("   %-52s %5d" % ("davon frisch (Grenze %d Tage) und nicht gesperrt:"
                        % MR.SPLYCUR_FRISCHE_TAGE, len(betrieb)))
print()
print("   ➤ DAS IST DIE ANTWORT AUF ,WOHER KOMMEN DIE 59`: es ist die")
print("     GRATIS-ABDECKUNG von Coin Metrics, keine Auswahl von uns.")
print()
print("2  DIE ALTERNATIVE: CoinGecko, Marktkapitalisierung / Preis")
print("   " + "-" * 98)
print("   %-52s %5d" % ("Symbole mit brauchbarer Reihe:", len(frei)))
print("   %-52s %5d" % ("davon AUCH in der laufenden Quelle:",
                        len(frei & betrieb)))
print("   %-52s %5d" % ("nur in der laufenden Quelle:",
                        len(betrieb - frei)))

# ------------------------------------------------------------------
# 2  DIE BEZUGSMENGEN
# ------------------------------------------------------------------
m = ro(MESS)
v1 = {r[0].upper() for r in m.execute(
    "SELECT DISTINCT symbol FROM price_history_ohlc "
    " WHERE assetklasse = 'krypto'")}
# „handelbar im Fenster": hat im letzten Jahr der Messbasis Volumen
letzter = m.execute("SELECT MAX(date) FROM price_history_ohlc "
                    " WHERE assetklasse = 'krypto'").fetchone()[0]
handelbar = {r[0].upper() for r in m.execute(
    "SELECT DISTINCT symbol FROM price_history_ohlc "
    " WHERE assetklasse = 'krypto' AND volume > 0 "
    "   AND date >= date(?, '-365 day')", (letzter,))}

# ---- ⚠️⚠️ DIE ASSETKLASSE, UND WARUM SIE HIER STEHEN MUSS ---------
#
# Der erste Lauf meldete "unser Bestand: 5 von 33 (15 %)". Die Zahl war
# IRREFUEHREND: von den 33 gehaltenen Werten sind 16 gar kein Krypto -
# ETFs, Aktien und Rohstoffe (OD7C, OD7H, OD7L, OD7N, EXH3, G2X, CEBS,
# DBPK, ROL, VVMX, X136, VST, BW, 3QSS, ISOC).
#
# ⚠️ EURCV gehoert NICHT dazu: der Stablecoin ist in der
# Watchlist als `krypto` gefuehrt, und die Watchlist ist hier die
# massgebliche Quelle - nicht mein Augenschein.
#
# `turnover` ist eine KRYPTO-Groesse (Coin Metrics und Binance fuehren
# nichts anderes). Eine Abdeckung gegen eine Menge zu rechnen, die zur
# Haelfte aus ETFs besteht, meldet zuverlaessig eine zu niedrige Zahl -
# und sie waere nicht falsch, sondern SINNLOS.
#
# Die Klasse kommt aus `config.get_watchlist()`, der Quelle, die auch
# der Betrieb benutzt (`rollen_lauf`: `elif assetklasse == "krypto"`).
# ⚠️ Sie liest nur `config.yaml` - kein Schreibweg, kein Netzabruf.
import config as CFG                                        # noqa: E402

_wl = CFG.get_watchlist()
wl_krypto = {a.symbol.upper() for a in _wl if a.assetklasse == "krypto"}
# ⚠️⚠️ NICHT `beobachtungsstatus == "TRADING"` - DEN GIBT ES HIER
# NICHT. Die erste Fassung fragte danach und meldete "0 von 0"; in
# `config.yaml` stehen ALLE 60 Eintraege auf `beobachtung`. Das
# TRADING aus 2.487-grundgesamtheit ist der BINANCE-Symbolstatus, eine
# ganz andere Groesse - ein Namensschatten.
#
# ⚠️ Die echte Untergliederung der Watchlist ist die ROLLE. `core`
# sind die Werte, bei denen eine fehlende Bewertung laut Nutzervorgabe
# NICHT unkritisch ist (Suite: "kein KERNWERT ohne jeden Beitrag").
wl_krypto_core = {a.symbol.upper() for a in _wl
                  if a.assetklasse == "krypto" and a.rolle == "core"}

b = ro(BETRIEB)
# ⚠️⚠️⚠️ `staked_quantity` GEHOERT DAZU - VOM NUTZER GEFUNDEN.
# Die erste Fassung fragte nur `quantity > 0` und meldete 18 Krypto-
# Positionen. Der Nutzer widersprach: *„unser Bestand in Krypto ist
# hoeher als 18"*. Er hatte recht: ACHT Positionen sind VOLLSTAENDIG
# gestaked und stehen mit `quantity = 0` in der Tabelle - AVAX, BNB,
# HYPE, NEAR, SEI, SOL, SUI, VSN. Richtig sind 26.
#
# ⚠️⚠️ UND ES IST NICHT NUR EINE ZAHL: NEAR und SOL sind genau
# Werte, bei denen HEBELSIGNALE entstanden sind. Eine Bestandsfrage,
# die sie uebersieht, uebersieht den halben Anlass.
#
# ⚠️ Eine gestakte Position ist eine GEHALTENE Position. Dass die
# Menge in einer zweiten Spalte steht, ist eine Eigenheit der
# Bitpanda-Anbindung, kein Unterschied in der Sache.
bestand_alle = {str(r[0]).upper() for r in b.execute(
    "SELECT DISTINCT symbol FROM holdings "
    " WHERE COALESCE(quantity, 0) > 0 "
    "    OR COALESCE(staked_quantity, 0) > 0")}
bestand = bestand_alle & wl_krypto
# ⚠️ `quantity`, NICHT `amount` - am Schema geprueft, bevor das
# Werkzeug lief. Eine falsche Spalte haette hier keine Ausnahme
# geworfen, sondern eine LEERE Menge geliefert und damit eine
# Abdeckung von 0 Prozent gemeldet (feedback_null_ergebnis_gegen_schema_pruefen).
sig_alle = {str(r[0]).upper() for r in b.execute(
    "SELECT DISTINCT symbol FROM signals")}
hebel_zeilen = list(b.execute(
    "SELECT symbol, substr(created_at,1,10) FROM signals "
    " WHERE instrument = 'hebel' AND hebel IS NOT NULL "
    "   AND verlust_am_stop_eur IS NOT NULL ORDER BY created_at"))
hebel_sym = {str(s).upper() for s, _t in hebel_zeilen}

MENGEN = (
    ("Messmenge V1 (eingefroren, krypto)", v1,
     "worueber der Beitrag GEMESSEN wurde"),
    ("davon handelbar im letzten Jahr", handelbar,
     "Volumen > 0 in den letzten 365 Tagen der Messbasis"),
    ("unsere WATCHLIST, krypto", wl_krypto,
     "was wir beobachten (config.yaml)"),
    ("davon Rolle `core`", wl_krypto_core,
     "⚠️ Kernwerte - hier ist eine fehlende Bewertung NICHT unkritisch"),
    ("unser BESTAND, nur krypto", bestand,
     "⚠️ was wir halten - OHNE die %d ETF/Aktien-Positionen"
     % len(bestand_alle - wl_krypto)),
    ("Symbole mit irgendeinem Signal", sig_alle,
     "worueber die Kette je entschieden hat"),
    ("SYMBOLE mit HEBELsignal", hebel_sym,
     "⚠️ die Menge, um die es beim Hebel geht"),
)

print()
print("3  DIE ABDECKUNG JE BEZUGSMENGE")
print("   " + "-" * 98)
print("   %-38s %6s | %13s | %13s" % ("Bezugsmenge", "Werte",
                                      "LAUFEND", "Alternative"))
print("   %-38s %6s | %13s | %13s" % ("", "", "Coin Metrics", "CoinGecko"))
print("   " + "-" * 98)
for name, menge, _warum in MENGEN:
    n = len(menge)
    a, f = len(menge & betrieb), len(menge & frei)
    print("   %-38s %6d | %4d  %6.1f%% | %4d  %6.1f%%"
          % (name, n, a, 100.0 * a / n if n else 0.0,
             f, 100.0 * f / n if n else 0.0))
print("   " + "-" * 98)
for name, _menge, warum in MENGEN:
    print("   %-38s %s" % (name, warum))

# ------------------------------------------------------------------
# 3  DIE HEBELSIGNALE IM EINZELNEN
# ------------------------------------------------------------------
print()
print("4  DIE HEBELSIGNALE IM EINZELNEN - hier faellt die Entscheidung")
print("   " + "-" * 98)
print("   %-10s %-12s %10s %12s" % ("Symbol", "Tag", "Betrieb", "Alternative"))
print("   " + "-" * 98)
tr_a = tr_f = 0
for sym, tag in hebel_zeilen:
    s = str(sym).upper()
    ja_a, ja_f = s in betrieb, s in frei
    tr_a += ja_a
    tr_f += ja_f
    print("   %-10s %-12s %10s %12s"
          % (s, tag, "WERT" if ja_a else "-- fehlt",
             "WERT" if ja_f else "-- fehlt"))
print("   " + "-" * 98)
n = len(hebel_zeilen)
print("   %-23s %10d von %d  (%.0f %%)"
      % ("LAUFEND mit Wert:", tr_a, n, 100.0 * tr_a / n if n else 0))
print("   %-23s %10d von %d  (%.0f %%)"
      % ("mit der Alternative:", tr_f, n, 100.0 * tr_f / n if n else 0))
print()
print("   ⚠️ Diese Signale stammen aus der DESKTOP-Kopie der")
print("      Betriebsdatenbank. Sie hat nicht den Stand des Notebooks -")
print("      die Zahl kann dort groesser sein, das Verhaeltnis nicht")
print("      zwangslaeufig gleich.")
print()
print("=" * 104)
