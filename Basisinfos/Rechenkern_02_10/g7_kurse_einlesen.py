"""Desktop-Gegenstück zu ``nb_auszug_kurse.py`` (G7 Stufe 0e): den NB-Auszug aus dem Austauschordner PRÜFEN und in eine ARBEITSKOPIE
einlesen. Die Messbasis-Dateien am Desktop bleiben UNBERÜHRT (``data/stundenkurse.db`` trägt ``_nur_messbasis``).

  1  GEGENPROBE auf der Überlappung (ab 2026-08-01 bis zum Desktop-Ende): je Symbol und Stunde dieselben Kurse? Abweichungen werden
     gezählt und gezeigt — Betrieb (NB) und Messbasis (Desktop) müssen dieselbe Reihe sein, sonst ist das Anhängen falsch
     (CLAUDE.md: Betrieb und Messung brauchen dieselbe Grundgesamtheit). AUSNAHME: die LETZTE Desktop-Stunde je Symbol — die Kerze
     war beim Kopieren noch offen (02.11.: alle 451 Abweichungen genau dort, 01.10. 16/17 Uhr); dort gilt die NB-Kerze (ersetzt)
  2  ARBEITSKOPIE ``data/_g7/kurse/`` = Desktop-Datei + NB-Zeilen NACH dem jeweiligen Desktop-Ende je Symbol; Marke ``_g7_rueckspiel``.
     Nur wenn 1 sauber ist (oder mit ``--trotzdem``)

    python g7_kurse_einlesen.py [<pfad zum auszug>] [--trotzdem] [--nur-pruefen]
"""
import glob
import os
import shutil
import sqlite3
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
ORDNER = r"K:\My Drive\Claude_Austauschordner\G7_Kurse"
ZIEL = os.path.join(PROJ, "data", "_g7", "kurse")
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db")


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    pf = arg[0] if arg else max(glob.glob(os.path.join(ORDNER, "kurse_auszug_*.db")), default=None)
    if not pf:
        sys.exit("kein Auszug in %s" % ORDNER)
    a = ro(pf)
    meta = dict(a.execute("SELECT schluessel, wert FROM _meta").fetchall())
    print("Auszug %s · Rechner %s · geholt %s" % (os.path.basename(pf), meta.get("rechner"), meta.get("geholt_utc")))
    sauber = True
    neu = {}
    for f in DATEIEN:
        tab = "kurse_" + f.replace(".db", "")
        N = pd.read_sql("SELECT symbol, stunde, open, high, low, close FROM %s" % tab, a)
        d = ro(os.path.join(PROJ, "data", f))
        D = pd.read_sql("SELECT symbol, stunde, open, high, low, close FROM stundenkurse WHERE stunde >= ?", d, params=(meta["ab"],))
        ende = pd.read_sql("SELECT symbol, MAX(stunde) bis FROM stundenkurse GROUP BY symbol", d).set_index("symbol").bis
        d.close()
        m = N.merge(D, on=["symbol", "stunde"], suffixes=("_nb", "_d"))
        abw = m[(abs(m.close_nb / m.close_d - 1) > 1e-9) | (abs(m.high_nb / m.high_d - 1) > 1e-9) | (abs(m.low_nb / m.low_d - 1) > 1e-9)]
        nur_d = len(D.merge(N, on=["symbol", "stunde"], how="left", indicator=True).query("_merge == 'left_only'"))
        sym_nb, sym_d = set(N.symbol), set(D.symbol)
        print("%-22s Überlappung %d Stunden · abweichend %d · nur am Desktop %d · Symbole NB %d / Desktop %d (nur NB %d, nur Desktop %d)" % (
            f, len(m), len(abw), nur_d, len(sym_nb), len(sym_d), len(sym_nb - sym_d), len(sym_d - sym_nb)))
        offen = abw[abw.stunde.values == ende.reindex(abw.symbol).values]
        abw = abw.drop(offen.index)
        print("   davon letzte Desktop-Stunde (Kerze offen, NB ersetzt): %d · sonst abweichend: %d" % (len(offen), len(abw)))
        if len(abw):
            print(abw.groupby("symbol").size().sort_values(ascending=False).head(10).to_string())
            sauber = False
        x = N.merge(ende.rename("bis").reset_index(), on="symbol", how="left")
        neu[f] = pd.concat([x[x.bis.isna() | (x.stunde > x.bis)], x.merge(offen[["symbol", "stunde"]], on=["symbol", "stunde"])])
        print("   anzuhängen: %d Stunden, %d Symbole, bis %s" % (len(neu[f]), neu[f].symbol.nunique(), neu[f].stunde.max()))
    if "--nur-pruefen" in sys.argv:
        return
    if not sauber and "--trotzdem" not in sys.argv:
        sys.exit("⚠ Überlappung NICHT gleich - keine Arbeitskopie (Ursache klären; --trotzdem nur mit Begründung)")
    os.makedirs(ZIEL, exist_ok=True)
    for f in DATEIEN:
        z = os.path.join(ZIEL, f)
        shutil.copyfile(os.path.join(PROJ, "data", f), z)
        c = sqlite3.connect(z)
        spalten = [r[1] for r in c.execute("PRAGMA table_info(stundenkurse)")]
        tab = "kurse_" + f.replace(".db", "")
        X = pd.read_sql("SELECT %s FROM %s" % (",".join(spalten), tab), a)
        X = X.merge(neu[f][["symbol", "stunde"]], on=["symbol", "stunde"])
        c.executemany("INSERT OR REPLACE INTO stundenkurse (%s) VALUES (%s)" % (",".join(spalten), ",".join("?" * len(spalten))),
                      X.itertuples(index=False, name=None))
        c.execute("CREATE TABLE IF NOT EXISTS _g7_rueckspiel (hinweis TEXT)")
        c.execute("INSERT INTO _g7_rueckspiel VALUES (?)", ("Arbeitskopie G7: Desktop-Messbasis + NB-Auszug %s (%s) - NICHT die Messbasis"
                                                            % (os.path.basename(pf), meta.get("geholt_utc")),))
        c.commit()
        print("Arbeitskopie %s: +%d Zeilen, bis %s" % (z, len(X), c.execute("SELECT MAX(stunde) FROM stundenkurse").fetchone()[0]))
        c.close()
    a.close()


if __name__ == "__main__":
    main()
