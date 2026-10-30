# -*- coding: utf-8 -*-
"""DESKTOP-NACHWEIS für ``api/sichten_quellen.py`` (G4, Weg A, 29.10.2026) — erst danach darf derselbe Abrufer an den NB.

Regel *Desktop zuerst* (Gesamtplan §6, Nutzer 09.08. und 29.10.). Geprüft wird die FUNKTION, nicht der Wert einer Sicht:

    N1  Vollständigkeit   jede Quelle aus ``auftraege`` hat Zeilen, beginnt ab 2023 und ist aktuell (Frist je Takt)
    N2  Lücken            Krypto-Tagesreihen ohne fehlenden Tag; Börsenreihen ohne Lücke > 5 Tage
    N3  Kein Vorgriff     jede Zeile ist erst NACH ihrem Beobachtungstag bekannt (Börse: frühestens 22:00 UTC am Tag)
    N4  Jahrgänge         ALFRED liefert Revisionen als eigene Zeilen (sonst wäre das Rückspiel vom heutigen Stand gefärbt)
    N5  Ü8 live = Rückspiel   ``--laufend`` in eine WEGWERF-Datei; auf gemeinsamen Zeilen dieselben Werte
    N6  Feeds             alle 9 liefern Meldungen, Felder wie im Archiv ``data/_lc/nachrichten.db``
    N7  Seiteneffekt      ``data/tradinginfotool.db`` unverändert (Größe und Änderungszeit), die Historie nur gelesen

    python -X utf8 Basisinfos/Rechenkern_02_10/g4_nachweis_sichtenquellen.py
"""
import os
import sqlite3
import sys
import tempfile
from datetime import date, timedelta

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
import wegwerf  # noqa: E402  (Wegwerf auf D:, laut aufräumen)
from api import sichten_quellen as SQ  # noqa: E402

PROD = os.path.join(PROJ, "data", "tradinginfotool.db")
FRIST = {"yfinance": 6, "coinbase_praemie": 3, "basis_quartal": 3, "gdelt_ton": 3,
         "fred:M2SL": 75, "fred:WALCL": 14, "fred:WTREGEN": 14, "fred:NFCI": 14}   # Tage bis zum letzten Wert; FRED täglich: 7
# Quellseitige Grenze, belegt und im Gesamtplan G4 benannt: FRED fuehrt die ICE-Reihen (Lizenz) nur rund drei Jahre rueckwirkend
SPAETER_BEGINN = {"fred:BAMLH0A0HYM2": "ICE-Lizenz: FRED fuehrt nur ~3 Jahre (HY ab 10/2023, G4)"}
ERGEBNIS = []


def urteil(nr, ok, text):
    ERGEBNIS.append(ok)
    print("%s %s  %s" % ("✔" if ok else "✖", nr, text))


def main() -> int:
    vorher = (os.path.getsize(PROD), os.path.getmtime(PROD)) if os.path.exists(PROD) else None
    h = sqlite3.connect("file:%s?mode=ro" % SQ.ABLAGE.replace("\\", "/"), uri=True)
    heute = date.today()

    # N1
    soll = [(q, s) for q, s, _ in SQ.auftraege("x")]
    fehlt, alt, spaet = [], [], []
    for q, s in soll:
        lo, hi, n = h.execute("SELECT MIN(datum), MAX(datum), COUNT(*) FROM reihe WHERE quelle=? AND symbol=?", (q, s)).fetchone()
        if not n:
            fehlt.append("%s:%s" % (q, s))
            continue
        if lo > "2023-01-10" and "%s:%s" % (q, s) not in SPAETER_BEGINN:
            spaet.append("%s:%s ab %s" % (q, s, lo))
        frist = FRIST.get("%s:%s" % (q, s), FRIST.get(q, 7))
        if (heute - date.fromisoformat(hi)).days > frist:
            alt.append("%s:%s bis %s" % (q, s, hi))
    urteil("N1", not (fehlt or alt or spaet), "%d Quellen · fehlen %s · beginnen spät %s · veraltet %s"
           % (len(soll), fehlt or "–", spaet or "–", alt or "–"))

    # N2
    # GDELT: eine Luecke, die in ALLEN Abfragen am selben Tag liegt, ist ein Ausfall der QUELLE (die Abfragen sind unabhaengig) -
    # sie wird ausgewiesen, nicht verschwiegen. Eine Luecke nur in einer Abfrage waere ein Fehler des Abrufers.
    gd = [set(d for (d,) in h.execute("SELECT datum FROM reihe WHERE quelle='gdelt_ton' AND symbol=?", (k,))) for k in SQ.GDELT]
    alle_tage = set().union(*gd)
    erste, letzte = min(alle_tage), max(alle_tage)
    kalender = {(date.fromisoformat(erste) + timedelta(days=i)).isoformat() for i in range((date.fromisoformat(letzte) - date.fromisoformat(erste)).days + 1)}
    quellausfall = sorted(kalender - alle_tage)
    nur_einzeln = sorted(alle_tage - set.intersection(*gd))
    luecken = ["gdelt_ton: %d Tage nur in einzelnen Abfragen %s" % (len(nur_einzeln), nur_einzeln[:5])] if nur_einzeln else []
    for q, s in soll:
        if q == "gdelt_ton":
            continue
        tage = sorted({date.fromisoformat(d) for (d,) in h.execute("SELECT DISTINCT datum FROM reihe WHERE quelle=? AND symbol=?"
                                                                    " AND datum >= '2023-01-01'", (q, s))})
        if len(tage) < 2:
            continue
        gross = max((b - a).days for a, b in zip(tage, tage[1:]))
        grenze = 1 if q in ("coinbase_praemie", "basis_quartal", "gdelt_ton") else (5 if q == "yfinance" else None)
        if grenze and gross > grenze:
            luecken.append("%s:%s größte Lücke %d T" % (q, s, gross))
    urteil("N2", not luecken, "Krypto lückenlos, Börse ≤ 5 T, GDELT in allen Abfragen gleich · %s · GDELT-Quellausfall %d Tage %s"
           % (luecken or "keine Lücke", len(quellausfall), quellausfall[:3] + (["…"] if len(quellausfall) > 3 else [])))

    # N3
    v = h.execute("SELECT quelle, COUNT(*) FROM reihe WHERE (quelle='yfinance' AND bekannt_ab < datum || 'T22:00') OR "
                  "(quelle<>'yfinance' AND substr(bekannt_ab,1,10) <= datum) GROUP BY quelle").fetchall()
    urteil("N3", not v, "Zeilen vor ihrem Bekanntwerden: %s" % (v or "keine"))

    # N4
    rev = h.execute("SELECT symbol, COUNT(*) FROM (SELECT symbol, datum FROM reihe WHERE quelle='fred' GROUP BY symbol, datum "
                    "HAVING COUNT(DISTINCT wert) > 1) GROUP BY symbol").fetchall()
    urteil("N4", any(s == "M2SL" for s, _ in rev), "Beobachtungen mit mehreren Jahrgängen: %s" % (dict(rev) or "keine"))

    if "--nur-bestand" in sys.argv:                          # N5/N6 rufen die Quellen ab (GDELT: nicht waehrend einer Sperre)
        h.close()
        print("\n%d von %d Nachweisen bestanden (nur Bestand N1-N4)" % (sum(ERGEBNIS), len(ERGEBNIS)))
        return 0 if all(ERGEBNIS) else 1
    # N5 + N6 in einer Wegwerf-Datei
    T = tempfile.mkdtemp(prefix="g4_")
    try:
        w = os.path.join(T, "sichten_laufend.db")
        e = SQ.lade((heute - timedelta(days=SQ.LAUFEND_TAGE)).isoformat(), w, mit_feeds=True)
        gescheitert = [k for k, n in e.items() if n is None]
        c = sqlite3.connect("file:%s" % w.replace("\\", "/"), uri=True)   # ⚠️ sonst nimmt ATTACH die URI (mode=ro) nicht an
        c.execute("ATTACH ? AS h", ("file:%s?mode=ro" % SQ.ABLAGE.replace("\\", "/"),))
        je = c.execute("""SELECT quelle, symbol, COUNT(*), SUM(ABS(l.wert - x.wert) > 1e-9 * MAX(1, ABS(x.wert))) FROM reihe l JOIN h.reihe x
                          USING (quelle, symbol, datum, bekannt_ab) GROUP BY quelle, symbol""").fetchall()
        gem, anders = sum(r[2] for r in je), sum(r[3] or 0 for r in je)
        bsp = c.execute("""SELECT l.quelle, l.symbol, l.datum, x.wert, l.wert FROM reihe l JOIN h.reihe x USING (quelle, symbol, datum, bekannt_ab)
                           WHERE ABS(l.wert - x.wert) > 1e-9 * MAX(1, ABS(x.wert)) LIMIT 5""").fetchall()
        # Nutzer 30.10. (a): GDELT gilt als abgeglichen, wenn MINDESTENS EINE Abfrage gemeinsame Zeilen ohne Abweichung hat (die vier
        # laufen durch dieselbe Funktion); eine gesperrte Abfrage ist ein ausgewiesener QUELLAUSFALL. Jede andere Quelle muss laufen.
        gd_ok = [s for q, s, n, a in je if q == "gdelt_ton" and n > 0 and not a]
        gd_aus = [s for q, s in gescheitert if q == "gdelt_ton"]
        sonst = [k for k in gescheitert if k[0] != "gdelt_ton"]
        fehlt_quelle = sorted({q for q, _, _ in SQ.auftraege("x")} - {"gdelt_ton"} - {q for q, _, n, _ in je if n > 0})
        urteil("N5", not sonst and not fehlt_quelle and gd_ok and gem > 100 and not anders,
               "laufend gegen Historie: %d gemeinsame Zeilen, %d abweichend %s · gescheitert %s · Quellen ohne Abgleich %s · GDELT abgeglichen %s, "
               "Quellausfall %s" % (gem, anders, bsp or "", sonst or "–", fehlt_quelle or "–", gd_ok or "KEINE", gd_aus or "–"))
        for q in sorted({r[0] for r in je}):
            print("      %-17s %s" % (q, " · ".join("%s %d/%d" % (s, n - (a or 0), n) for qq, s, n, a in je if qq == q)))
        feeds = dict(c.execute("SELECT feed, COUNT(*) FROM meldung GROUP BY feed").fetchall())
        leer = c.execute("SELECT COUNT(*) FROM meldung WHERE pub_utc IS NULL OR titel = ''").fetchone()[0]
        arch = sqlite3.connect("file:%s?mode=ro" % os.path.join(PROJ, "data", "_lc", "nachrichten.db").replace("\\", "/"), uri=True)
        gleich = [r[1] for r in arch.execute("PRAGMA table_info(meldung)")] == [r[1] for r in c.execute("PRAGMA table_info(meldung)")]
        arch.close()
        urteil("N6", len(feeds) == 9 and leer == 0 and gleich,
               "%d von 9 Feeds, %d Meldungen, ohne Zeit/Titel %d, Felder wie Archiv: %s" % (len(feeds), sum(feeds.values()), leer, gleich))
        c.close()
    finally:
        wegwerf.aufraeumen(T)

    h.close()
    nachher = (os.path.getsize(PROD), os.path.getmtime(PROD)) if os.path.exists(PROD) else None
    urteil("N7", vorher == nachher, "Produktions-DB unverändert: %s" % (vorher == nachher))
    print("\n%d von %d Nachweisen bestanden" % (sum(ERGEBNIS), len(ERGEBNIS)))
    return 0 if all(ERGEBNIS) else 1


if __name__ == "__main__":
    sys.exit(main())
