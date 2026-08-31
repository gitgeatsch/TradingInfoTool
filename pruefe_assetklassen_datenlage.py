# -*- coding: utf-8 -*-
"""Welche Datenlage haben Aktien, ETF und Rohstoffe? (30.08.2026)

Nutzerauftrag: andere Assetklassen konzeptionell mitdenken, pruefen ob Daten
da sind und die Umsetzbarkeit geklaert ist - mitbauen nur, wenn der Aufwand
gering ist.

Geprueft wird an der Quelle:
  1 wieviele Symbole je Klasse, und wieviel Kurshistorie
  2 gibt es die Krypto-Beitraege dort ueberhaupt (Funding? Turnover?)
  3 welche Entsprechungen waeren noetig
  4 ⚠️ JE INSTRUMENT UND STRATEGIE - die Achse, die am 31.08. fehlte

## Zu Abschnitt 4 (31.08.2026)

Nutzerkritik, woertlich: *"Du zeigst mir einen simplen Signale-Filter heute
und dann - keine Unterscheidung nach Krypto. Bei Krypto haben wir drei
Strategien aktuell: SPOT, Hebel und Akkumulation. ZIEL: nicht der Takt soll
die Empfehlung liefern, sondern nur jene, die qualitativ mit ausreichender
Wahrscheinlichkeit und Potential einen HANDEL begruenden - je Asset, je
Strategie, etc.!"*

Gemeldet hatte ich "174 -> 88 Signale/Tag". Eine Gesamtzahl beantwortet die
Frage nicht, sie verdeckt sie. Das Ziel verlangt eine Aussage JE ZELLE aus

    Klasse x Instrument x Strategie

⚠️ Und nicht jede Kombination ist erlaubt - `handelsauftrag.ERLAUBTE_PAARE`
schliesst aus (spot x swing ist seit dem 14.08. draussen). Eine Zelle, die
die Paar-Matrix erlaubt, kann trotzdem tot sein: `INSTRUMENTE_JE_GRUPPE`
entscheidet, ob die Gruppe im Betrieb ueberhaupt laeuft.

⚠️ NICHTS NEUES GEBAUT. Diese Achse gehoert hierher, nicht in ein zweites
Werkzeug - eine zweite Landkarte neben einer bestehenden ist derselbe
Schaden wie ein ueberholtes Bestandsdokument (Nutzervorgabe 31.08.:
*"was ist mit den alten landkarten - nichts neues bauen was wir schon haben"*).
"""
import sqlite3, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)

print("### 1. Symbole und Kurshistorie je Assetklasse ###")
try:
    for r in c.execute(
        "SELECT tier, COUNT(DISTINCT symbol) FROM watchlist GROUP BY tier"):
        print("  %-14s %d Symbole" % r)
except Exception as e:
    print("  watchlist: %s" % str(e)[:60])
print()
try:
    print("  Kurshistorie je Klasse (price_history_ohlc x watchlist):")
    for r in c.execute(
        "SELECT w.tier, COUNT(DISTINCT p.symbol), COUNT(*), MIN(p.date), MAX(p.date) "
        "FROM price_history_ohlc p JOIN watchlist w ON w.symbol = p.symbol "
        "GROUP BY w.tier"):
        print("    %-14s %3d Symbole, %7d Zeilen, %s .. %s"
              % (r[0], r[1], r[2], str(r[3])[:10], str(r[4])[:10]))
except Exception as e:
    print("    %s" % str(e)[:80])

print()
print("### 2. Messbasis messdaten.db — welche Klassen? ###")
m = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
for r in m.execute("SELECT assetklasse, COUNT(*) FROM messreihen GROUP BY assetklasse"):
    print("  %-14s %d Reihen" % r)

print()
print("### 3. Gibt es Nicht-Kurs-Daten fuer Aktien/ETF/Rohstoffe? ###")
for t in ("macro_snapshot", "open_interest_snapshot", "marktscan_candidates"):
    try:
        sp = [x[1] for x in c.execute("PRAGMA table_info(%s)" % t)]
        n = c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        print("  %-26s %6d Zeilen" % (t, n))
    except Exception:
        pass
print()
print("  Finnhub/SEC im Code angebunden - aber welche Tabelle speichert das?")
for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    if any(w in t.lower() for w in ("fundament", "finnhub", "sec_", "earnings",
                                     "bilanz", "kgv", "aktie")):
        n = c.execute("SELECT COUNT(*) FROM [%s]" % t).fetchone()[0]
        print("    %-30s %d" % (t, n))
print("    -> (keine Zeile oberhalb = es gibt keine Fundamentaldaten-Tabelle)")

print()
print("### 4. JE KLASSE x INSTRUMENT x STRATEGIE — wo steht eine Bewertung? ###")
sys.path.insert(0, ".")
from agent import assetklassen as AK
from agent import handelsauftrag as HA
from agent import potential as PT
from agent import wahrscheinlichkeit as WK

print("  Schwelle %.3f R. Eine Zelle ist nur dann eine BEWERTUNG, wenn dort"
      % PT.schwelle())
print("  ein tragender Beitrag registriert ist - sonst ist sie ein TAKT.")
print()
print("  %-11s %-12s %-13s %-7s %s"
      % ("Klasse", "Instrument", "Strategie", "laeuft", "was Stufe 11 tut"))
print("  " + "-" * 92)
_mit, _ohne = [], []
for _kl in sorted(AK.gruppiere()):
    _inst = AK.INSTRUMENTE_JE_GRUPPE.get(_kl) or ()
    for _i in HA.INSTRUMENTE:
        # ⚠️ ALLE Instrumente zeigen, nicht nur die laufenden - sonst
        # verschwindet genau die Luecke, um die es geht.
        _laeuft = _i in _inst
        for _st in HA.ERLAUBTE_PAARE.get(_i, ()):
            _v = WK.vermessen(_kl, _st)
            if not _laeuft:
                _tut = "-- keine Gruppe im Betrieb"
            elif _v:
                _tut = "ENTSCHEIDET (%d Beitraege)" % len(_v)
                _mit.append((_kl, _i, _st))
            else:
                _tut = "⚠️ winkt durch (Notiz) - nicht vermessen"
                _ohne.append((_kl, _i, _st))
            print("  %-11s %-12s %-13s %-7s %s"
                  % (_kl, _i, _st, "ja" if _laeuft else "nein", _tut))
print()
print("  Zellen mit echter Bewertung: %d   ohne: %d" % (len(_mit), len(_ohne)))
for _z in _mit:
    print("     ✔ %s x %s x %s" % _z)
for _z in _ohne:
    print("     ⚠️ %s x %s x %s" % _z)
if _ohne:
    print()
    print("  Fuer diese Zellen liefert das System eine Empfehlung, ohne dass")
    print("  eine Messung dahintersteht - genau der Zustand, den das")
    print("  uebergeordnete Ziel ausschliesst.")
