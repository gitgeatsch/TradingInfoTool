"""Teilexport fuer Schritt 4 (Betriebspruefung REGEL0 am Notebook) - NUR LESEN, keine Netzabfrage.

Zweck (Plan_Hebel_fuenf_Phasen_27_09.md, Abschnitt PLAN UND VORGEHEN, Betriebspruefung B1-B9; E-35 *Labor-only ist FAIL*):
feststellen, welche Daten die REGEL0 am Notebook VORFINDET - welche Datenbanken und Tabellen, welche Zeitaufloesung und
Historie, welche Symbole (Grundgesamtheit), die aktuelle Hebel-Liste, Python-Pakete fuer das Monatstraining.

⚠️ Regeln (CLAUDE.md):
  - jede Datenbank nur mit ``mode=ro`` - kein Schreibzugriff, auch nicht auf die Produktion ``tradinginfotool.db``
  - keine Netzabfrage, kein Import von Projektmodulen mit Seiteneffekten
  - leichtgewichtig: Zeilenzahlen ueber ``max(rowid)`` (Schaetzung, keine Vollzaehlung), Symbole nur bei kleinen Tabellen
  - Ausgabe auf stdout UND direkt in den Austauschordner (Nutzer 01.10.: *das Ergebnis direkt in den Austauschordner*):
        <Google Drive>/Claude_Austauschordner/Notebook_Analysedaten/nb_betriebsdaten_<GERAET>.txt
    Der Geraetename steht im Dateinamen, damit ein Desktop-Testlauf (9900K) das Notebook-Ergebnis (T440) NIE
    ueberschreibt (Lehre 24.08., Pruefungen-Ordner). Der Drive-Buchstabe wird gesucht, nicht geraten (G, K, H, E, F x
    "My Drive"/"Meine Ablage", wie ``extract_notebook_diagnose._google_drive_wurzel`` - hier nachgebaut, um keine
    Projektmodule mit Seiteneffekten zu importieren). Die Datei wird auch bei einem Abbruch geschrieben; fehlt die
    Zeile ``SCHLUSS: vollstaendig``, ist der Lauf abgebrochen.

Aufruf am Notebook nach ``git pull``:
        python nb_teilexport_betriebsdaten.py
Am Desktop zum Test unschaedlich (dieselben Regeln, eigene Datei ``..._9900K.txt``). ``--ohne-ablage``: nur stdout.
"""
from __future__ import annotations

import os
import platform
import sqlite3
import sys
from datetime import datetime

HIER = os.path.dirname(os.path.abspath(__file__))
DATEN = os.path.join(HIER, "data")
# Spalten, an denen eine Zeitreihe erkannt wird (Stunde oder Tag)
ZEIT = ("stunde", "datum", "tag", "timestamp", "zeit", "date")


def ro(pfad):
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True, timeout=5)


def tabellen(c):
    return [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]


def spalten(c, t):
    return [r[1] for r in c.execute('PRAGMA table_info("%s")' % t)]


def _drive_wurzel():
    for b in ("G", "K", "H", "E", "F"):
        for o in ("My Drive", "Meine Ablage"):
            k = "%s:/%s" % (b, o)
            if os.path.isdir(k):
                return k
    return None


class _Zwei:
    """stdout UND Puffer - der Puffer geht am Ende in den Austauschordner."""

    def __init__(self, a):
        self.a, self.teile = a, []

    def write(self, s):
        self.teile.append(s)
        return self.a.write(s)

    def flush(self):
        self.a.flush()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                            # noqa: BLE001
        pass
    if "--ohne-ablage" in sys.argv:
        return _inhalt()
    zw = _Zwei(sys.stdout)
    sys.stdout = zw
    rc = 1
    try:
        rc = _inhalt()
    finally:
        sys.stdout = zw.a
        w = _drive_wurzel()
        if w is None:
            print("⚠️ Google Drive nicht gefunden (G/K/H/E/F) - Ergebnis nur oben auf dem Bildschirm")
        else:
            ziel = os.path.join(w, "Claude_Austauschordner", "Notebook_Analysedaten")
            os.makedirs(ziel, exist_ok=True)
            pf = os.path.join(ziel, "nb_betriebsdaten_%s.txt" % platform.node())
            with open(pf, "w", encoding="utf-8") as f:
                f.write("".join(zw.teile))
            print("➤ geschrieben nach %s" % pf)
    return rc


def _inhalt() -> int:
    print("=" * 100)
    print("NB-TEILEXPORT BETRIEBSDATEN (Schritt 4, nur lesen) - %s - Geraet %s - Python %s" % (
        datetime.now().strftime("%Y-%m-%d %H:%M"), platform.node(), sys.version.split()[0]))
    print("Projekt: %s" % HIER)
    print("=" * 100)
    # Pakete fuer das Monatstraining (B2/B3)
    for mod in ("numpy", "pandas", "scipy"):
        try:
            m = __import__(mod)
            print("  Paket %-7s %s" % (mod, getattr(m, "__version__", "?")))
        except Exception as ex:                                  # noqa: BLE001
            print("  Paket %-7s FEHLT (%s)" % (mod, ex.__class__.__name__))
    try:
        import shutil
        fr = shutil.disk_usage(HIER).free / 1e9
        print("  freier Speicher am Projektlaufwerk: %.1f GB" % fr)
    except Exception:                                            # noqa: BLE001
        pass
    if not os.path.isdir(DATEN):
        print("⛔ data/ fehlt")
        return 1
    dbs = sorted(f for f in os.listdir(DATEN) if f.endswith(".db"))
    print()
    print("DATENBANKEN in data/ (%d):" % len(dbs))
    for f in dbs:
        p = os.path.join(DATEN, f)
        st = os.stat(p)
        print("  %-45s %10.1f MB  geaendert %s" % (f, st.st_size / 1e6, datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")))
    for f in dbs:
        p = os.path.join(DATEN, f)
        if os.path.getsize(p) == 0:
            continue
        print()
        print("-" * 100)
        print("%s" % f)
        try:
            c = ro(p)
            for t in tabellen(c):
                sp = spalten(c, t)
                try:
                    n = c.execute('SELECT max(rowid) FROM "%s"' % t).fetchone()[0]
                except sqlite3.Error:
                    n = None
                zeile = "  %-32s ~%s Zeilen · Spalten %s" % (t, n if n is not None else "?", ", ".join(sp[:10]) + (" …" if len(sp) > 10 else ""))
                print(zeile)
                zs = [s for s in sp if s.lower() in ZEIT]
                if zs and n:
                    z = zs[0]
                    try:
                        lo, hi = c.execute('SELECT min("%s"), max("%s") FROM "%s"' % (z, z, t)).fetchone()
                        print("      Zeitraum %s: %s .. %s" % (z, lo, hi))
                    except sqlite3.Error:
                        pass
                if "symbol" in sp and n and n <= 3_000_000:
                    try:
                        ns = c.execute('SELECT COUNT(DISTINCT symbol) FROM "%s"' % t).fetchone()[0]
                        print("      Symbole: %d" % ns)
                    except sqlite3.Error:
                        pass
                    # Aufloesung: Abstand der ersten zwei Zeitpunkte eines Symbols
                    if zs:
                        try:
                            s0 = c.execute('SELECT symbol FROM "%s" LIMIT 1' % t).fetchone()[0]
                            zz = [r[0] for r in c.execute('SELECT "%s" FROM "%s" WHERE symbol=? ORDER BY "%s" LIMIT 3' % (zs[0], t, zs[0]), (s0,))]
                            print("      Beispiel %s: %s" % (s0, " | ".join(str(x) for x in zz)))
                        except sqlite3.Error:
                            pass
            c.close()
        except sqlite3.Error as ex:
            print("  ⛔ nicht lesbar: %s" % ex)
    # die aktuelle Hebel-Liste (B5/B6, Schritt 5)
    prod = os.path.join(DATEN, "tradinginfotool.db")
    if os.path.exists(prod):
        print()
        print("-" * 100)
        try:
            c = ro(prod)
            if "asset_hebel_settings" in tabellen(c):
                rows = c.execute("SELECT symbol, hebel_pruefung_erlaubt FROM asset_hebel_settings ORDER BY symbol").fetchall()
                an = [r[0] for r in rows if r[1]]
                print("HEBEL-LISTE (asset_hebel_settings, erlaubt): %d - %s" % (len(an), ", ".join(an)))
            c.close()
        except sqlite3.Error as ex:
            print("  ⛔ Hebel-Liste nicht lesbar: %s" % ex)
    # Watchlist (Krypto) und Bestand - nur SYMBOLE, keine Mengen (Signalbilanz je Asset, Nutzer 01.10.)
    print()
    print("-" * 100)
    try:
        import yaml
        cfg = yaml.safe_load(open(os.path.join(HIER, "Basisinfos", "config.yaml"), encoding="utf-8")) or {}
        wl = cfg.get("watchlist") or []
        kr = sorted(str(e.get("symbol")) for e in wl if (e.get("assetklasse") or "krypto") == "krypto")
        print("WATCHLIST krypto (config.yaml): %d - %s" % (len(kr), ", ".join(kr)))
    except Exception as ex:                                      # noqa: BLE001
        print("  ⛔ Watchlist nicht lesbar: %s" % ex.__class__.__name__)
    if os.path.exists(prod):
        try:
            c = ro(prod)
            rows = c.execute("SELECT symbol FROM holdings WHERE COALESCE(quantity, 0) > 0 ORDER BY symbol").fetchall()
            print("BESTAND (holdings, Menge > 0, nur Symbole): %d - %s" % (len(rows), ", ".join(r[0] for r in rows)))
            c.close()
        except sqlite3.Error as ex:
            print("  ⛔ Bestand nicht lesbar: %s" % ex)
    print()
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
