"""Kopie der REGEL0-Dateien vom Notebook fuer die Pruefungen am Desktop (F5 / S7-6, E-57; Nutzer 05.10.2026).

    python nb_kopie_regel0.py <Zielordner, z. B. E:\\regel0_kopie>            Ablage, Modelle UND Stundenkurse (~1,3 GB)
    python nb_kopie_regel0.py <Zielordner> --ohne-kurse                        nur Ablage und Modelle (klein, z. B. fuer den Austauschordner)

NUR LESEND an der Quelle: jede Datenbank wird mit mode=ro geoeffnet und ueber die SQLite-Sicherungsfunktion in EINEM Schritt kopiert -
das ist ein in sich stimmiger Stand, auch wenn gerade ein Stundenlauf schreibt (die Sicherung liest unter einer Lesetransaktion).
Am Notebook wird nichts veraendert: kein Schreibzugriff in data/, keine Mail, kein Netz. Geschrieben wird NUR in den Zielordner:
die Kopien, der Modellordner und die Begleitdatei KOPIE_INFO.txt (Groesse, Pruefsumme, Kennzahlen, Integritaetspruefung).

⚠️ Der Zielordner darf nicht im Projekt liegen (schon gar nicht in data/) - das Skript verweigert es.
"""
import hashlib
import os
import platform
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone

PROJEKT = os.path.dirname(os.path.abspath(__file__))
DATEN = os.path.join(PROJEKT, "data")
ABLAGE = "regel0_signale.db"
KURSE = ("stundenkurse.db", "stundenkurse_alle.db")
MODELLE = "regel0_modelle"


def _sha(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for teil in iter(lambda: f.read(1 << 20), b""):
            h.update(teil)
    return h.hexdigest()


def ziel_erlaubt(ziel: str, projekt: str = PROJEKT) -> tuple:
    z = os.path.normcase(os.path.realpath(os.path.abspath(ziel)))
    p = os.path.normcase(os.path.realpath(projekt))
    if z == p or z.startswith(p + os.sep):
        return False, "Zielordner liegt im Projekt (%s) - verweigert, damit nie etwas neben der Produktion entsteht" % projekt
    return True, ""


def sichere(quelle: str, ziel: str) -> dict:
    """Eine Datenbank nur lesend sichern -> {zeilen je Tabelle, quick_check}."""
    src = sqlite3.connect("file:%s?mode=ro" % quelle.replace("\\", "/"), uri=True, timeout=60)
    try:
        dst = sqlite3.connect(ziel)
        try:
            src.backup(dst, pages=-1)                   # EIN Schritt: der ganze Stand unter einer Lesetransaktion
        finally:
            dst.close()
    finally:
        src.close()
    c = sqlite3.connect("file:%s?mode=ro" % ziel.replace("\\", "/"), uri=True)
    try:
        qc = c.execute("PRAGMA quick_check").fetchone()[0]
        tab = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        zeilen = {t: c.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for t in tab}
        extra = {}
        if "lauf" in tab:
            extra["letzter_lauf"] = c.execute("SELECT MAX(jetzt) FROM lauf").fetchone()[0]
        if "stundenkurse" in tab:
            extra["letzte_stunde"] = c.execute("SELECT MAX(stunde) FROM stundenkurse").fetchone()[0]
    finally:
        c.close()
    return dict(quick_check=qc, zeilen=zeilen, **extra)


def kopiere(ziel: str, ohne_kurse: bool = False, daten: str = DATEN, projekt: str = PROJEKT, ausgabe=print) -> int:
    ok, grund = ziel_erlaubt(ziel, projekt)
    if not ok:
        ausgabe("⛔ " + grund)
        return 3
    os.makedirs(ziel, exist_ok=True)
    t0 = time.time()
    info = ["REGEL0-KOPIE vom %s (%s), Geraet %s" % (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                                                     datetime.now().astimezone().strftime("%H:%M Ortszeit"), platform.node()),
            "Quelle: %s (nur lesend)" % daten, ""]
    fehler = 0
    for name in (ABLAGE,) + (() if ohne_kurse else KURSE):
        q, z = os.path.join(daten, name), os.path.join(ziel, name)
        if not os.path.exists(q):
            info.append("⛔ %-22s fehlt an der Quelle" % name)
            fehler += 1
            continue
        if os.path.exists(z):
            os.remove(z)
        t1 = time.time()
        k = sichere(q, z)
        ok_ = k["quick_check"] == "ok"
        fehler += 0 if ok_ else 1
        info.append("%s %-22s %8.1f MB  %5.0f s  quick_check %s  SHA-256 %s" % (
            "✔" if ok_ else "⛔", name, os.path.getsize(z) / 1e6, time.time() - t1, k["quick_check"], _sha(z)[:16]))
        for kk in ("letzter_lauf", "letzte_stunde"):
            if kk in k:
                info.append("      %s: %s" % (kk.replace("_", " "), k[kk]))
        info.append("      Zeilen: " + ", ".join("%s %d" % (t, n) for t, n in k["zeilen"].items() if not t.startswith("sqlite_")))
    qm = os.path.join(daten, MODELLE)
    if os.path.isdir(qm):
        zm = os.path.join(ziel, MODELLE)
        os.makedirs(zm, exist_ok=True)
        for f in sorted(os.listdir(qm)):
            shutil.copy2(os.path.join(qm, f), os.path.join(zm, f))
            gleich = _sha(os.path.join(qm, f)) == _sha(os.path.join(zm, f))
            fehler += 0 if gleich else 1
            info.append("%s %s/%s  SHA-256 %s%s" % ("✔" if gleich else "⛔", MODELLE, f, _sha(os.path.join(zm, f))[:16],
                                                    "" if gleich else "  ABWEICHUNG zur Quelle"))
    else:
        info.append("⛔ %s/ fehlt an der Quelle" % MODELLE)
        fehler += 1
    info += ["", "SCHLUSS: %s (%.0f s)" % ("vollstaendig" if not fehler else "%d FEHLER" % fehler, time.time() - t0)]
    with open(os.path.join(ziel, "KOPIE_INFO.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(info) + "\n")
    for z in info:
        ausgabe(z)
    return 0 if not fehler else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    if not a or a[0].startswith("-"):
        print(__doc__)
        return 2
    return kopiere(a[0], ohne_kurse="--ohne-kurse" in a)


if __name__ == "__main__":
    sys.exit(main())
