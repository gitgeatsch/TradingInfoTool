"""F5 / S7-6 (E-57, 05.10.2026): R-R11 AM NOTEBOOK - rechnet der Betrieb dieselben Signale wie die Nachrechnung am Desktop?

    python Basisinfos/Rechenkern_02_10/pruefe_f5_rr11_nb.py <Kopie regel0_signale.db> <Ordner mit Kopie der NB-Daten>
           [--modelle <Kopie data/regel0_modelle>] [--von "2026-10-05 06:00"] [--bis "2026-10-10 23:00"] [--prozesse 4]
    python Basisinfos/Rechenkern_02_10/pruefe_f5_rr11_nb.py --gegenprobe

Alle SIGNALE der Woche, nicht nur die gemailten: der Betrieb bewertet jede Stunde alle Assets (05.10.: 105 Signale, 4 mit Schalter).
Je Laufstunde t der NB-Ablage laeuft am Desktop DERSELBE Stundenlauf (`regel0_stundenlauf.betrieb_lauf`) auf der Datenkopie, in
Wegwerfordnern. Verglichen werden je (Symbol, Signalstunde): v-dach, vorlaeufige und endgueltige Stufe.

    mit --modelle   die Modellpakete des NB  -> prueft den RECHENKERN (Ergebnis muss zeilengleich sein)
    ohne            die Pakete trainiert der Desktop neu -> prueft zusaetzlich das TRAINING (numpy-Fassung kann abweichen, R-R11:
                    Massstab sind gleiche SIGNALE, nicht gleiche Bits)

⚠️ NUR LESEND auf den Kopien; die Datenkopie liegt NICHT unter data/ (die Sperre des Stundenlaufs gilt dort nicht, weil Ablage und Modelle
ausdruecklich Wegwerfordner sind). Kein Netz, keine Mail.
"""
import argparse
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
B0 = datetime(2020, 1, 1)
F = "%Y-%m-%d %H:%M"


def h_von(txt):
    return int((datetime.strptime(txt[:16], F) - B0).total_seconds() // 3600)


def h_txt(h):
    return (B0 + timedelta(hours=h)).strftime(F)


def lies(ablage: str) -> tuple:
    c = sqlite3.connect("file:%s?mode=ro" % ablage.replace("\\", "/"), uri=True)
    laeufe = [r[0] for r in c.execute("SELECT jetzt FROM lauf ORDER BY jetzt")]
    sig = {(r[0], r[1]): (r[2], r[3], r[4]) for r in c.execute("SELECT symbol, signalstunde, vh, stufe_vorlaeufig, stufe FROM signal")}
    c.close()
    return laeufe, sig


def _block(arg):
    """Ein Prozess: die Laufstunden [a-1, b+1] nacheinander - behalten wird jede Signalstunde sh mit sh+1 in [a, b]
    (ihr NEU-Lauf liegt im Block, ihr ENDGUELTIG-Lauf sh+2 auch, dank des Ueberhangs)."""
    a, b, daten, modelle = arg
    import agent.regel0_stundenlauf as SL
    abl = tempfile.mkdtemp(prefix="r0_f5_")
    try:
        for t in range(a - 1, b + 2):
            SL.betrieb_lauf(daten, t, abl, modelle, ausgabe=lambda *x, **k: None)
        _l, sig = lies(os.path.join(abl, "regel0_signale.db"))
        return {k: v for k, v in sig.items() if a <= h_von(k[1]) + 1 <= b}
    finally:
        shutil.rmtree(abl, ignore_errors=True)


def nachrechnen(daten: str, modelle: str, von: int, bis: int, prozesse: int = 4) -> dict:
    stunden = list(range(von, bis + 1))
    n = max(1, min(prozesse, len(stunden)))
    gr = -(-len(stunden) // n)
    bloecke = [(stunden[i], stunden[min(i + gr, len(stunden)) - 1], daten, modelle) for i in range(0, len(stunden), gr)]
    # die Modellpakete EINMAL vorab (sonst traenieren vier Prozesse dasselbe Paket gleichzeitig)
    import agent.regel0_stundenlauf as SL
    vor = tempfile.mkdtemp(prefix="r0_f5v_")
    try:
        SL.betrieb_lauf(daten, von, vor, modelle, ausgabe=print)
    finally:
        shutil.rmtree(vor, ignore_errors=True)
    erg = {}
    if n == 1:
        for bl in bloecke:
            erg.update(_block(bl))
    else:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(n) as pool:
            for teil in pool.imap_unordered(_block, bloecke):
                erg.update(teil)
    return erg


def vergleiche(nb: dict, desk: dict, von: int, bis: int) -> dict:
    """Signalstunden sh mit sh+1 in [von, bis]. Stufe nur verglichen, wo BEIDE eine haben (die juengste Stunde ist im NB vorlaeufig)."""
    def drin(k):
        return von <= h_von(k[1]) + 1 <= bis
    a = {k: v for k, v in nb.items() if drin(k)}
    d = {k: v for k, v in desk.items() if drin(k)}
    nur_nb, nur_desk = sorted(set(a) - set(d)), sorted(set(d) - set(a))
    vh, vorl, endg = [], [], []
    for k in sorted(set(a) & set(d)):
        (va, pa, sa), (vd, pd, sd) = a[k], d[k]
        if va is None or vd is None or abs(va - vd) > 1e-9:
            vh.append((k, va, vd))
        if pa is not None and pd is not None and int(pa) != int(pd):
            vorl.append((k, pa, pd))
        if sa is not None and sd is not None and int(sa) != int(sd):
            endg.append((k, sa, sd))
    return dict(n_nb=len(a), n_desk=len(d), gleich=len(set(a) & set(d)) - len({x[0] for x in vh + vorl + endg}),
                nur_nb=nur_nb, nur_desk=nur_desk, vh=vh, vorl=vorl, endg=endg,
                ok=not (nur_nb or nur_desk or vh or vorl or endg))


def bericht(e: dict, titel: str) -> bool:
    print("%s: NB %d Signale, Desktop %d, gleich %d" % (titel, e["n_nb"], e["n_desk"], e["gleich"]))
    for name, liste in (("nur im NB", e["nur_nb"]), ("nur am Desktop", e["nur_desk"]), ("v-dach anders", e["vh"]),
                        ("vorlaeufige Stufe anders", e["vorl"]), ("endgueltige Stufe anders", e["endg"])):
        print("  %s %-26s %d%s" % ("✔" if not liste else "⛔", name, len(liste), ("  z. B. " + "; ".join(str(x) for x in liste[:4])) if liste else ""))
    print("SCHLUSS F5: %s" % ("zeilengleich" if e["ok"] else "NICHT zeilengleich"))
    return e["ok"]


def gegenprobe() -> int:
    """Eine Ablage wird so erzeugt, wie das NB sie schreibt (Stundenlaeufe nacheinander auf den Desktop-Daten) - dann muss das
    Werkzeug mit seinen parallelen Bloecken ZEILENGLEICH sein, und je ein eingebauter Fehler muss genau seine Zeile rot machen."""
    import agent.regel0_stundenlauf as SL
    mod = os.environ.get("F5_MODELLE") or tempfile.mkdtemp(prefix="r0_f5m_")
    von, bis = h_von("2026-08-19 13:00"), h_von("2026-08-19 21:00")
    abl = tempfile.mkdtemp(prefix="r0_f5nb_")
    for t in range(von - 1, bis + 2):
        SL.betrieb_lauf("data", t, abl, mod, ausgabe=lambda *x, **k: None)
    pf = os.path.join(abl, "regel0_signale.db")
    _l, nb = lies(pf)
    desk = nachrechnen("data", mod, von, bis, prozesse=3)
    ok = []
    e = vergleiche(nb, desk, von, bis)
    ok.append(e["ok"] and e["n_nb"] > 20)
    print("  %s  parallele Bloecke = Stundenlauf nacheinander (%d Signale)" % ("OK  " if ok[-1] else "FEHL", e["n_nb"]))
    k0 = sorted(k for k in nb if von <= h_von(k[1]) + 1 <= bis)
    for name, mut, feld in (("v-dach", lambda d: d.__setitem__(k0[0], (d[k0[0]][0] + 1e-6, d[k0[0]][1], d[k0[0]][2])), "vh"),
                            ("endgueltige Stufe", lambda d: d.__setitem__(k0[1], (d[k0[1]][0], d[k0[1]][1], 99)), "endg"),
                            ("fehlendes Signal", lambda d: d.pop(k0[2]), "nur_desk"),
                            ("erfundenes Signal", lambda d: d.__setitem__(("ERFUNDEN", k0[3][1]), (0.05, 3, 3)), "nur_nb")):
        m = dict(nb)
        mut(m)
        e = vergleiche(m, desk, von, bis)
        rot = [x for x in ("nur_nb", "nur_desk", "vh", "vorl", "endg") if e[x]]
        ok.append(rot == [feld])
        print("  %s  eingebauter Fehler *%s* -> genau %s rot (%s)" % ("OK  " if ok[-1] else "FEHL", name, feld, rot))
    shutil.rmtree(abl, ignore_errors=True)
    print("%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ablage", nargs="?")
    ap.add_argument("daten", nargs="?")
    ap.add_argument("--modelle")
    ap.add_argument("--von")
    ap.add_argument("--bis")
    ap.add_argument("--prozesse", type=int, default=4)
    ap.add_argument("--gegenprobe", action="store_true")
    a = ap.parse_args(argv)
    if a.gegenprobe:
        return gegenprobe()
    laeufe, nb = lies(a.ablage)
    von = h_von(a.von) if a.von else h_von(laeufe[0])
    bis = h_von(a.bis) if a.bis else h_von(laeufe[-1])
    mod = a.modelle
    if mod:                                            # die NB-Pakete als KOPIE - der Lauf darf dort nichts anlegen oder aendern
        k = tempfile.mkdtemp(prefix="r0_f5mk_")
        for f in os.listdir(mod):
            shutil.copy2(os.path.join(mod, f), k)
        mod = k
    else:
        mod = tempfile.mkdtemp(prefix="r0_f5mt_")
    print("F5 R-R11 am NB: Laufstunden %s bis %s (%d), Modelle %s" % (h_txt(von), h_txt(bis), bis - von + 1,
                                                                       "des NB" if a.modelle else "am Desktop neu trainiert"))
    desk = nachrechnen(a.daten, mod, von, bis, a.prozesse)
    return 0 if bericht(vergleiche(nb, desk, von, bis), "Signale") else 1


if __name__ == "__main__":
    sys.exit(main())
