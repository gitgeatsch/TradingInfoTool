# -*- coding: utf-8 -*-
"""F-213 abschliessen: was sagt `gesperrt_bis()` an den ECHTEN Zeilen?
(05.09.2026)

## Der Stand aus F-213

Der Cooldown sperrt 94,1 % - der staerkste Filter der Kette. Trotzdem
stehen 67 % der Signale enger zusammen, als er erlaubt, und zwar
AUSSCHLIESSLICH im 15-Stunden-Zweig (85,5 % verletzt), waehrend der
3,5-Stunden-Zweig sauber ist (13,1 %).

Fuenf Verdaechtige sind ausgeschlossen: zweiter Schreibpfad,
`quelle_kette`, zeitliche Aenderung, Aufrufstelle, "3,5 h gilt fuer
alles".

## Was hier gemacht wird

Die Signale werden CHRONOLOGISCH in eine leere Kopie eingefuegt, und VOR
jedem Einfuegen wird die ECHTE Funktion `wiederholung.gesperrt_bis()`
gefragt - mit `jetzt=` auf den Zeitpunkt dieses Signals.

⚠️ **Genau daran ist F-174s erste Fassung gescheitert**: sie las das
juengste Signal der FERTIGEN Tabelle, in einer Historie oft eines NACH dem
betrachteten Zeitpunkt ("Signal 16.08., gesperrt bis 22.08."). Die leere
Kopie plus `jetzt=` schliesst das aus - die Tabelle enthaelt zu jedem
Zeitpunkt nur Zeilen, die es damals schon gab.

## Die Frage, scharf gestellt

    Fuer jedes Signal:  war es laut gesperrt_bis() gesperrt?
    Und:                war der Abstand kleiner als die Soll-Dauer?

    gesperrt=JA  & Abstand < Soll   -> die Funktion ist richtig, das
                                       Signal haette nicht entstehen duerfen
                                       -> der Fehler liegt NACH der Sperre
    gesperrt=NEIN & Abstand < Soll  -> die FUNKTION laesst durch
                                       -> der Fehler liegt IN der Sperre
"""
import sqlite3
import sys
import datetime as dt
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent import wiederholung as WH     # DIE ECHTE FUNKTION

SP = ("C:/Users/Geatsch/AppData/Local/Temp/claude/"
      "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
      "f018f847-7a7c-44fa-bab6-ff90785a7541/scratchpad/nb_0903.db")


def main():
    quelle = sqlite3.connect("file:%s?mode=ro" % SP, uri=True)
    schema = quelle.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='signals'"
    ).fetchone()[0]
    spalten = [r[1] for r in quelle.execute("PRAGMA table_info(signals)")]
    rows = list(quelle.execute(
        "SELECT %s FROM signals WHERE created_at >= '2026-08-14' "
        "ORDER BY created_at" % ", ".join(spalten)))
    quelle.close()
    print("Signale ab 14.08.: %d · Spalten: %d" % (len(rows), len(spalten)))

    # ⚠️ LEERE KOPIE im Speicher - kein Dateikopieren, keine Produktions-DB
    ziel = sqlite3.connect(":memory:")
    ziel.executescript(schema)
    i_sym = spalten.index("symbol")
    i_zeit = spalten.index("created_at")
    i_inst = spalten.index("instrument") if "instrument" in spalten else None
    i_str = spalten.index("strategie") if "strategie" in spalten else None
    i_heb = spalten.index("hebel") if "hebel" in spalten else None
    platz = ",".join("?" * len(spalten))

    i_akt = spalten.index("action") if "action" in spalten else None
    nach_aktion = Counter()
    gesamt_aktion = Counter()
    letzt = {}
    z = Counter()
    beispiele = []
    for r in rows:
        sym = r[i_sym]
        zeit = r[i_zeit]
        inst = (r[i_inst] if i_inst is not None else "spot") or "spot"
        strat = r[i_str] if i_str is not None else None
        # ---- DIE ECHTE FUNKTION, auf dem Stand VOR diesem Signal ----
        sperre = WH.gesperrt_bis(ziel, sym, str(inst).lower(),
                                 gruppe="krypto", strategie=strat,
                                 jetzt=zeit)
        key = (str(sym).upper(), str(inst).lower())
        eng = None
        if key in letzt:
            vt, vh = letzt[key]
            h = (dt.datetime.fromisoformat(zeit) - vt).total_seconds() / 3600.0
            soll = WH.stunden(str(inst).lower(), None, gruppe="krypto",
                              strategie=strat, hebel_zuletzt=vh)
            eng = h < soll
            if eng and not sperre and len(beispiele) < 5:
                beispiele.append((sym, inst, vt.isoformat()[:16],
                                  zeit[:16], h, soll, vh))
        z[(bool(sperre), eng)] += 1
        if bool(sperre) and eng:
            nach_aktion[str(r[i_akt]).upper() if i_akt is not None else "?"] += 1
        if eng:
            gesamt_aktion[str(r[i_akt]).upper() if i_akt is not None else "?"] += 1
        letzt[key] = (dt.datetime.fromisoformat(zeit),
                      r[i_heb] if i_heb is not None else None)
        ziel.execute("INSERT INTO signals VALUES (%s)" % platz, r)
    ziel.commit()

    print()
    print("=" * 88)
    print("WAS SAGT `gesperrt_bis()` AN DEN ECHTEN ZEILEN?")
    print("=" * 88)
    print("  %-22s %-16s %8s" % ("gesperrt_bis sagt", "Abstand", "Anzahl"))
    for (gesperrt, eng), n in sorted(z.items(), key=lambda x: -x[1]):
        lab = "zu eng" if eng else ("weit genug" if eng is False else "erstes Signal")
        print("  %-22s %-16s %8d" % ("GESPERRT" if gesperrt else "frei", lab, n))

    zu_eng_frei = z[(False, True)]
    zu_eng_gesperrt = z[(True, True)]
    print()
    print("  " + "-" * 84)
    if zu_eng_frei > zu_eng_gesperrt:
        print("  ⚠️⚠️ DER FEHLER LIEGT IN DER SPERRE: %d Signale standen zu eng"
              % zu_eng_frei)
        print("     und `gesperrt_bis()` gab sie trotzdem frei.")
    elif zu_eng_gesperrt > 0:
        print("  ⚠️⚠️ DIE FUNKTION IST RICHTIG: %d zu enge Signale waren"
              % zu_eng_gesperrt)
        print("     laut Sperre GESPERRT - sie sind trotzdem entstanden.")
        print("     Der Fehler liegt also NACH der Sperre, nicht in ihr.")
    print()
    print("  " + "-" * 84)
    print("  WELCHE AKTIONEN entstehen trotz Sperre?")
    print("  %-16s %10s %10s %8s" % ("action","zu eng","davon gesperrt","%"))
    for a, n in gesamt_aktion.most_common():
        g = nach_aktion.get(a, 0)
        print("  %-16s %10d %10d %9.1f%%" % (a, n, g, 100*g/max(n,1)))
    if beispiele:
        print()
        print("  Beispiele (zu eng, aber freigegeben):")
        for s, i, vt, nt, h, soll, vh in beispiele:
            print("    %-10s %-5s %s -> %s  %.1f h (soll %.1f, Hebel zuvor %s)"
                  % (s, i, vt, nt, h, soll, vh))
    return 0


if __name__ == "__main__":
    sys.exit(main())
