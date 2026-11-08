"""G18 M0 — Erfolgsmessung REGEL0 im Betrieb (Vorabfestlegung_G18_M0_Erfolgsmessung_07_11.md; Nutzer 07.11.2026: *„ja G18 Beginnen“*).

    python -X utf8 Basisinfos/Rechenkern_02_10/g18_m0_erfolgsmessung.py <regel0_signale-Kopie> [<tradinginfotool-Sicherung .db.gz>]
        -> g18_m0_erfolgsmessung.txt (bei der Prüfstand-Kopie vom 04.11.: g18_m0_erfolgsmessung_pruefstand.txt)

Rechnung wie ``agent/regel0_messstand`` (Kennzahl, Spanne 99 % über TAGE, Befund gegen die Referenz) - dieselben Funktionen, nicht
nachgebaut. ⚠️ Nur lesend: die Kopien (mode=ro), die Kurs-Arbeitskopie data/_g7/kurse, die G7-Einstiegsdateien. Die Sicherung wird in
einen Wegwerf-Ordner auf D: entpackt und danach gelöscht.
"""
import gzip
import os
import shutil
import sqlite3
import sys
import tempfile
import time

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
import wegwerf  # noqa: E402,F401  (tempfile-Ordner auf D:)
from agent import regel0_messstand as MS  # noqa: E402

KOPIE_KURSE = os.path.join(PROJ, "data", "_g7", "kurse")
G7 = os.path.join(PROJ, "data", "_g7", "regel0")
E138_AB = "2026-10-25"
E138_GRENZE = 20
TXT = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    TXT.append(s)


def ro(pfad):
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)


def pp(x):
    return "%+.2f %%" % (100 * x) if x == x else "–"


def kz_zeile(name, rows, befund=True):
    k = MS._kennzahl(rows)
    if not k.get("n"):
        p("  %-34s keine" % name)
        return k
    p("  %-34s n %5d · Tage %3d · Mittel %s · Spanne 99 %% [%s; %s] · A24 %.1f %% · B24 %.1f %%%s" % (
        name, k["n"], k["tage"], pp(k["mittel"]), pp(k["mittel"] - k["halb"]), pp(k["mittel"] + k["halb"]), 100 * k["a24"],
        100 * k["b24"], (" · " + MS._befund(k)) if befund else ""))
    return k


# ══ Kurse der Arbeitskopie (D3 Drift, D5 rückwärts) ══════════════════════════════════════════════════════════════════════════════
def schluesse(ab="2026-08-25"):
    teile = []
    for db in ("stundenkurse.db", "stundenkurse_alle.db"):                 # die erste Datei gewinnt (wie regel0_messstand)
        c = ro(os.path.join(KOPIE_KURSE, db))
        teile.append(pd.read_sql("SELECT symbol, stunde, close FROM stundenkurse WHERE stunde >= ?", c, params=(ab,)))
        c.close()
    d = pd.concat(teile).drop_duplicates(["symbol", "stunde"], keep="first")
    S = d.pivot_table(index="stunde", columns="symbol", values="close")
    S.index = pd.to_datetime(S.index)
    return S.sort_index()


def e24_aus(S, symbol, stunde):
    t = pd.Timestamp(stunde)
    try:
        a, b = S.at[t, symbol], S.at[t + pd.Timedelta(hours=24), symbol]
    except KeyError:
        return np.nan
    return b / a - 1 if a and a == a and b == b else np.nan


def main(kopie, sicherung=None):
    t0 = time.time()
    pruefstand = "2026-11-04" in kopie.replace("\\", "/") or "asset_lage_2026-11-04" in kopie.replace("\\", "/")
    c = ro(kopie)
    stich = c.execute("SELECT MAX(berechnet_am) FROM ausgang").fetchone()[0]
    rows = c.execute("SELECT a.symbol, a.signalstunde, a.einstieg, a.e24, a.q, s.hebel_schalter, s.stufe, s.mail_signal_am "
                     "FROM ausgang a JOIN signal s ON s.symbol=a.symbol AND s.signalstunde=a.signalstunde "
                     "WHERE a.status='ok' AND a.signalstunde >= ? ORDER BY a.signalstunde", (MS.START,)).fetchall()
    offen = c.execute("SELECT COUNT(*) FROM signal s WHERE s.signalstunde >= ? AND NOT EXISTS (SELECT 1 FROM ausgang a WHERE "
                      "a.symbol=s.symbol AND a.signalstunde=s.signalstunde AND a.status='ok')", (MS.START,)).fetchone()[0]
    c.close()
    D = pd.DataFrame(rows, columns=["symbol", "signalstunde", "einstieg", "e24", "q", "schalter", "stufe", "mail"])
    D["tag"] = D.signalstunde.str[:10]
    p("G18 M0 ERFOLGSMESSUNG REGEL0 · %s · %s" % (time.strftime("%Y-%m-%d %H:%M"), "PRÜFSTAND (Kopie 04.11., nur Form)" if pruefstand
                                                     else "Messung"))
    p("Kopie %s · Stand der Ausgänge %s · abgeschlossen %d · ohne abgeschlossenen Ausgang %d · Referenz %s · Kosten %s (nachgelagert)"
      % (os.path.basename(kopie), stich, len(D), offen, pp(MS.REF_MITTEL), pp(MS.KOSTEN)))

    z = lambda d: list(zip(d.tag, d.e24, d.q))  # noqa: E731
    p("")
    p("D1 Niveau gegen die Referenz (brutto, 24 h, Spanne über Tage)")
    k_alle = kz_zeile("alle", z(D))
    kz_zeile("gemailt", z(D[D.mail.notna()]))
    for st in sorted(D.stufe.dropna().unique()):
        kz_zeile("Stufe %d" % st, z(D[D.stufe == st]))
    if k_alle.get("n"):
        p("  netto nach Kosten (nachgelagert): alle %s je Signal" % pp(k_alle["mittel"] - MS.KOSTEN))

    p("")
    p("D2 E-138-Spur ab %s: Tage mit > %d Signalen gegen ≤ %d (nur Beschreibung, kein Befund)" % (E138_AB, E138_GRENZE, E138_GRENZE))
    d2 = D[D.tag >= E138_AB].copy()
    je_tag = d2.groupby("tag").size()
    d2["breit"] = d2.tag.map(je_tag) > E138_GRENZE
    p("  Tage: marktweit %d · ruhig %d" % ((je_tag > E138_GRENZE).sum(), (je_tag <= E138_GRENZE).sum()))
    kz_zeile("marktweit (> %d je Tag)" % E138_GRENZE, z(d2[d2.breit]), befund=False)
    kz_zeile("ruhig (≤ %d je Tag)" % E138_GRENZE, z(d2[~d2.breit]), befund=False)

    p("")
    p("D3 Vorsprung gegen die Drift (Auskunft, Kurse der Arbeitskopie bis 02.11.): 24-h-Ertrag minus Mittel der Breite-Menge")
    S = schluesse()
    breite = sorted(set(pd.read_csv(os.path.join(PROJ, "data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";").symbol))
    B = S[[s for s in breite if s in S.columns]]
    drift = (B.shift(-24) / B - 1).mean(axis=1)
    D["drift"] = pd.to_datetime(D.einstieg).map(drift)
    d3 = D[D.drift.notna()]
    p("  Signale mit Drift %d von %d (bis %s)" % (len(d3), len(D), d3.tag.max() if len(d3) else "–"))
    kz_zeile("Drift der Breite-Menge", list(zip(d3.tag, d3.drift, d3.q)), befund=False)
    kz_zeile("Vorsprung alle", list(zip(d3.tag, d3.e24 - d3.drift, d3.q)), befund=False)
    g3 = d3[d3.mail.notna()]                       # ⚠️ pandas trägt NaN, nicht None (Prüfstand 07.11.: 'gemailt' war = 'alle')
    kz_zeile("Vorsprung gemailt", list(zip(g3.tag, g3.e24 - g3.drift, g3.q)), befund=False)

    p("")
    p("D4 echte Hebel-Trades seit %s (Ergebnis zum Schlusskurs, nie 'realisiert')" % MS.START[:10])
    if sicherung:
        T = tempfile.mkdtemp(prefix="g18m0_")
        try:
            prod = os.path.join(T, "tradinginfotool.db")
            with gzip.open(sicherung, "rb") as f, open(prod, "wb") as g:
                shutil.copyfileobj(f, g)
            ordner = os.path.join(T, "ablage")
            os.makedirs(ordner)
            shutil.copyfile(kopie, os.path.join(ordner, "regel0_signale.db"))
            cp = ro(prod)
            tr = MS.trades(cp, ordner)
            cp.close()
            ok = [t for t in tr if t["ergebnis"] is not None]
            p("  Sicherung %s · Trades %d (offen %d, ohne Rechnung %d) · Eigenkapital %.2f € · Ergebnis %+.2f € · Gebühren %.2f €" % (
                os.path.basename(sicherung), len(tr), sum(t["status"] == "offen" for t in tr), len(tr) - len(ok),
                sum(t["eigenkapital"] for t in ok), sum(t["ergebnis"] for t in ok), sum(t["kosten"] or 0 for t in ok)))
            for t in tr:
                p("   %-6s auf %s zu %s %-11s %5.0f h · Signal %s · EK %8.2f € · Ergebnis %s" % (
                    t["symbol"], t["auf"], t["zu"] or "–", t["status"], t["dauer_h"], t["signal"] or "eigene Entscheidung",
                    t["eigenkapital"], ("%+.2f €" % t["ergebnis"]) if t["ergebnis"] is not None else "–"))
        finally:
            wegwerf.aufraeumen(T)
    else:
        p("  keine Sicherung angegeben")

    p("")
    p("D5 rückwärts Sep./Okt. 2026 (Betriebsrechnung G7 §10, 24 h aus der Kurs-Arbeitskopie) — Auskunft, stößt E-139 nicht um")
    F = pd.read_csv(os.path.join(G7, "f_einstiege_betrieb_mit_stufe_schalter.csv"), sep=";")
    F = F[(F.tag >= "2026-09-01") & (F.tag <= "2026-10-31")].copy()
    F["e24"] = [e24_aus(S, s, h) for s, h in zip(F.symbol, F.stunde)]
    F["q"] = F.a24.astype(int) - F.b24.astype(int)
    F = F[F.e24.notna()]
    for name, sub in (("alle", F), ("Schalter-Werte", F[F.schalter.astype(str) == "True"])):
        for mon in ("2026-09", "2026-10"):
            kz_zeile("%s %s" % (name, mon), z(sub[sub.tag.str[:7] == mon]))
    p("")
    p("fertig %.0f s" % (time.time() - t0))
    aus = os.path.join(HIER, "g18_m0_erfolgsmessung%s.txt" % ("_pruefstand" if pruefstand else ""))
    open(aus, "w", encoding="utf-8").write("\n".join(TXT) + "\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
