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
        python nb_teilexport_betriebsdaten.py --mit-kurse E:\regel0_kopie     dazu die Stundenkurse (~1,3 GB) auf den USB-Stick

KOPIE FUER DIE PRUEFUNGEN AM DESKTOP (F5/S7-6 und Testwoche, E-57; Nutzer 05.10.: *in ein bestehendes integrieren*): bei jedem Lauf
gehen die REGEL0-Ablage und die Modellpakete (zusammen ~0,1 MB) als KOPIE nach
        <Google Drive>/Claude_Austauschordner/Notebook_Analysedaten/regel0_kopie_<GERAET>/
- nur lesend ueber die SQLite-Sicherung (``nb_kopie_regel0.py``), mit KOPIE_INFO.txt (Pruefsummen, Integritaet). Die grossen
Stundenkurse nur mit ``--mit-kurse <Ordner>`` (USB), nie in den Drive.
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
        _kopie_fuer_pruefungen()
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


def _kopie_fuer_pruefungen() -> None:
    """Ablage + Modelle (klein) in den Austauschordner; mit --mit-kurse dazu die Stundenkurse in den angegebenen Ordner (USB)."""
    print()
    print("-" * 100)
    if not os.path.exists(os.path.join(DATEN, "regel0_signale.db")):
        print("REGEL0-KOPIE: keine REGEL0-Ablage auf diesem Geraet - uebersprungen")
        return
    import nb_kopie_regel0 as K
    w = _drive_wurzel()
    if w is None:
        print("REGEL0-KOPIE: Google Drive nicht gefunden - uebersprungen")
    else:
        ziel = os.path.join(w, "Claude_Austauschordner", "Notebook_Analysedaten", "regel0_kopie_%s" % platform.node())
        zeilen = []
        rc = K.kopiere(ziel, ohne_kurse=True, daten=DATEN, ausgabe=zeilen.append)
        print("REGEL0-KOPIE (Ablage + Modelle) %s -> %s" % ("vollstaendig" if rc == 0 else "MIT FEHLER (rc %d)" % rc, ziel))
        for z in zeilen[3:]:
            if z:
                print("    " + z)
    if "--mit-kurse" in sys.argv:
        i = sys.argv.index("--mit-kurse")
        if i + 1 >= len(sys.argv):
            print("⛔ --mit-kurse ohne Zielordner")
            return
        print("REGEL0-KOPIE MIT STUNDENKURSEN -> %s (dauert 1-2 min)" % sys.argv[i + 1])
        K.kopiere(sys.argv[i + 1], ohne_kurse=False, daten=DATEN, ausgabe=lambda z: print("    " + z) if z else None)


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
    # Schritt 7, O15: die LAUFENDEN Werte der Groessen-Deckel aus der config.yaml DIESES Geraets (die Desktop-Kopie kann abweichen) -
    # gesucht nach Schluesselnamen, damit die Pfade nicht aufgezaehlt werden muessen
    print()
    print("-" * 100)
    try:
        import yaml
        cfg = yaml.safe_load(open(os.path.join(HIER, "Basisinfos", "config.yaml"), encoding="utf-8")) or {}
        such = ("hebel_aus_quote", "cooldown_stunden_wenn_gehebelt", "stop_min_atr", "verlustanteil", "toepfe_deckel_eur",
                "cash_reserve_min_fixed_eur", "hebel_richtung_modus", "aktiv_fuer", "betriebsart")
        gef = []

        def lauf(d, pfad):
            if isinstance(d, dict):
                for k, v in d.items():
                    if k in such:
                        gef.append((("%s.%s" % (pfad, k)).strip("."), v))
                    lauf(v, "%s.%s" % (pfad, k))
        lauf(cfg, "")
        print("DECKEL UND GROESSEN (config.yaml dieses Geraets):")
        for k, v in gef:
            print("    %-55s %s" % (k, v))
    except Exception as ex:                                      # noqa: BLE001
        print("  ⛔ Deckel nicht lesbar: %s" % ex.__class__.__name__)
    # Schritt 7, O15 Positionsgroesse (E-43 Punkt 3): Altbestand der Hebelpositionen und Kontowert - nur lesen.
    # P9 (10.10.2026): die ABFRAGEN stehen in agent/betriebslage.py (eine Quelle mit der Statusseite); hier nur die Ausgabe -
    # zeilengleich zur Fassung davor nachgewiesen (Basisinfos/Rechenkern_02_10/p9_teilexport_vergleich.py).
    import agent.betriebslage as BL
    if os.path.exists(prod):
        print()
        print("-" * 100)
        try:
            c = ro(prod)
            hp = BL.hebel_positionen(c)
            print("HEBEL-POSITIONEN je Status: " + " · ".join("%s %d" % (s, n) for s, n in hp["je_status"]))
            offen = hp["offen"]
            print("OFFEN (geschlossen_am leer): %d · Positionswert %.0f EUR · Eigenkapital %.0f EUR · Kredit %.0f EUR" % (
                len(offen), hp["summe_wert"], hp["summe_ek"], hp["summe_kredit"]))
            for r in offen:
                print("    %-8s %-5s %-10s Hebel %4.1f · Wert %8.0f · Eigenkapital %7.0f · seit %s · Liq. geschaetzt %s" % (
                    r[0], r[1], r[2], r[3] or 0, r[4] or 0, r[5] or 0, str(r[7])[:16], r[8]))
            # H15 (09.10.2026): was die Hebelfuehrung gemeldet hat (Schluessel hebelfuehrung:<id>:<Empfehlung>:<Stufe>:<Tag>)
            try:
                hf = BL.hebelfuehrung_gemeldet(c, 8)
                print("HEBELFUEHRUNG (H15) gemeldet: %d Zustaende%s" % (len(hf), "".join("\n    %s · %s" % (j, str(z)[:16]) for j, z in hf)))
            except sqlite3.Error as ex:
                print("  ⛔ Hebelfuehrung nicht lesbar: %s" % ex)
            pw = BL.portfoliowert(c, 3)
            print("PORTFOLIOWERT (letzte 3 Tage): " + " · ".join("%s %.0f EUR (Cash %.0f)" % (d, w or 0, ca or 0) for d, w, ca in pw))
            c.close()
        except sqlite3.Error as ex:
            print("  ⛔ Positionen nicht lesbar: %s" % ex)
    # Schritt 7, S7-1b: laeuft der Stundenjob `regel0_nachlader`? Je Datei der Stand, wie viele Symbole ihn erreichen, die letzten Laeufe
    print()
    print("-" * 100)
    try:
        nl = BL.nachlader(DATEN)
        print("REGEL0-DATENBASIS (Stundenjob regel0_nachlader): %s - %s" % ("schreibt" if nl["schreibt"] else "schreibt NICHT", nl["grund"]))
        for e in nl["dateien"]:
            if e["fehlt"]:
                print("    %-24s FEHLT" % e["datei"])
                continue
            print("    %-24s Stand %s · %d von %d Symbolen auf Stand (der Rest: nicht mehr im Handel oder Rueckstand)" % (
                e["datei"], e["stand"], e["aktuell"], e["gesamt"]))
            if e["laeufe"] is not None:
                for r in e["laeufe"]:
                    print("        Lauf %s · neu %d · ersetzt %d · nicht im Handel %d · Fehler %d" % r)
            else:
                print("        noch kein Lauf des Nachladers")
    except Exception as ex:                                      # noqa: BLE001
        print("  ⛔ REGEL0-Datenbasis nicht lesbar: %s %s" % (ex.__class__.__name__, ex))
    # Schritt 7, S7-2b: der Rechenkern im Betrieb - Modelldateien, letzte Laeufe, Signale (nur lesen)
    print()
    print("-" * 100)
    try:
        rr = BL.regel0_rechnung(DATEN)
        print("REGEL0-RECHNUNG: Modelldateien %d - %s" % (len(rr["modelle"]), ", ".join(
            "%s (%s)" % (n_, sha or "ohne Pruefsumme") for n_, sha in rr["modelle"]) or "-"))
        if not rr["ablage"]:
            print("    regel0_signale.db fehlt - noch kein Lauf")
        else:
            for r in rr["laeufe"]:
                print("    Lauf %s · %.0f s · Pakete %s · frisch %d/%d · veraltet %d · nicht im Handel %d · neu %d · endgueltig %d%s" % (
                    r[0], r[1] or 0, r[2], r[4], r[3], r[5], r[6], r[7], r[8], (" · ⚠️ " + r[9]) if r[9] else ""))
            print("    Signale gesamt %d, davon Hebel-Schalter an %d" % (rr["signale_gesamt"], rr["schalter_an"]))
            mail_ = rr["mail_spalten"]
            if mail_:
                print("    Mails (S7-4): Signal %d · Korrektur %d · Erinnerung %d" % rr["mails"])
                if "verpasst" in rr:
                    # N-1 (E-57): nach einem Ausfall nachgerechnet, Einstieg schon vorbei - keine Signalmail
                    nh_ = rr["nachgeholt"]
                    print("    Nachgeholt (N-1): %d Signalstunden%s · verpasste Signale (keine Mail): %d" % (
                        nh_[0] or 0, (" - " + nh_[1]) if nh_[1] else "", rr["verpasst"]))
                for e_ in rr.get("entfallen") or []:
                    # 04.10.2026: Ausstiegserinnerung nur bei offener Hebelposition - die entfallenen mit Grund
                    print("      Erinnerung entfallen: %s (Ausstieg %s) am %s - %s" % (e_[0] or e_[1], e_[2], e_[3], e_[4]))
            for r in rr["juengste"]:
                print("      %-9s (%s) Signal %s · Einstieg %s · v %.4f · Stufe vorl. %s / endg. %s · p5 %s · Schalter %s%s" % (
                    r[0], r[1], r[2], r[3], r[4] or 0, r[5], r[6], "%.4f" % r[7] if r[7] is not None else "-",
                    {1: "an", 0: "aus"}.get(r[8], "?"),
                    (" · Mail %s%s%s" % (r[9] or "-", " · Korr. %s" % r[10] if r[10] else "", " · Erinn. %s" % r[11] if r[11] else "")) if mail_ else ""))
    except Exception as ex:                                      # noqa: BLE001
        print("  ⛔ REGEL0-Rechnung nicht lesbar: %s %s" % (ex.__class__.__name__, ex))
    # E-52 (03.10.2026): die LLM-Sofortfassung - Aufrufe je Tag, Urteile je Rolle, Ausfaelle, Laufzeit (nur lesen)
    print()
    print("-" * 100)
    try:
        pb = BL.pruefblock(DATEN)
        if not pb["lauf"]:
            print("REGEL0-PRUEFUNG (LLM): noch kein Lauf")
        else:
            # die Kopfzeile IMMER - ein leerer Abschnitt sah am 03.10. aus wie ein fehlender (Tabelle da, noch kein Signal geprueft)
            n_p = pb["zeilen"]
            print("REGEL0-PRUEFUNG (LLM): %d Zeilen%s" % (n_p, " - noch kein Signal geprueft (Schatten wartet auf ein Signal mit Hebel-Schalter an)"
                                                         if not n_p else ""))
            # ⚠️ 04.10.: bis dahin zaehlte diese Zeile ZEILEN statt Aufrufe (5 statt 25 bei 5 Stimmen) - jetzt die Spalte `aufrufe`
            for r in pb["je_tag"]:
                print("REGEL0-PRUEFUNG (LLM) %s · Aufrufe %d · gefragte Rollen %d" % r)
            for r in pb["je_rolle"]:
                print("    %-11s Fassung %s · Zeilen %d · mit Urteil %d · ohne (Fehler/Sperre) %d · Laufzeit im Mittel %s s" % r)
            for r in pb["urteile"]:
                print("      %-11s %-16s %d" % r)
            for r in pb["fehler"]:
                print("      ⚠️ %s · %d" % (str(r[0])[:90], r[1]))
            for r in pb["juengste"]:
                print("      %-9s %s %-11s %s" % (r[0], r[1], r[2], r[3] or ("(%s)" % str(r[4])[:60])))
    except Exception as ex:                                      # noqa: BLE001
        print("  ⛔ REGEL0-Pruefung nicht lesbar: %s %s" % (ex.__class__.__name__, ex))
    # O29 (08.10.2026): Binance-Ankuendigungen - Schalter, letzter Abruf, Fehler, Zuordnungen, Vorwaertsprotokoll (nur lesen; K-ANK-1)
    print()
    print("-" * 100)
    try:
        an = BL.ankuendigungen(DATEN)
        if not an["lauf"]:
            print("BINANCE-ANKUENDIGUNGEN: Schalter %s · noch kein Lauf" % ("AN" if an["an"] else "aus"))
        else:
            print("BINANCE-ANKUENDIGUNGEN: Schalter %s · Laeufe %d, davon fehlerfrei %d" % ("AN" if an["an"] else "aus", an["laeufe"], an["fehlerfrei"]))
            for r in an["letzte"]:
                print("    Lauf %s · %s · neu %d · Zuordnungen %d · protokolliert %d · %s s%s" % (
                    r[0], "ok" if r[1] else "FEHLER", r[2], r[3], r[4], r[6], (" · " + str(r[5])[:90]) if r[5] else ""))
            print("    Meldungen %d · Zuordnungen %d · je Art: %s" % (an["meldungen"], an["zuordnungen"], ", ".join("%s %d" % r for r in an["je_art"])))
            if "protokoll" in an:
                print("    Vorwaertsprotokoll: Signale %d · mit Ereignis %d · noch ohne Eintrag %d" % an["protokoll"])
                for r in an["mit_ereignis"]:
                    print("      %-9s %s %s" % r)
    except Exception as ex:                                      # noqa: BLE001
        print("  ⛔ Binance-Ankuendigungen nicht lesbar: %s %s" % (ex.__class__.__name__, ex))
    # S7-5d (03.10.2026): taeglicher Abgleich als Auskunft - Neuaufnahme, gesperrte Mails, Hebel-Schalter-Assets ohne Daten (nur lesen)
    print()
    print("-" * 100)
    try:
        na = BL.neuaufnahme_und_abgleich(DATEN, prod)
        if na["neuaufnahme"] is not None:
            if na["neuaufnahme"]:
                for r in na["neuaufnahme"]:
                    print("REGEL0-NEUAUFNAHME %s · Regel %d · Datei %d · neu: %s%s" % (r[0], r[1], r[2], r[3] or "-", (" · ⚠️ " + r[4]) if r[4] else ""))
            else:
                print("REGEL0-NEUAUFNAHME: noch kein Lauf")
        if na["gesperrt"] is not None:
            g = na["gesperrt"]
            print("REGEL0 Signale NICHT gemailt wegen Zuordnung: %d%s" % (len(g), "".join(chr(10) + "    %s (%s) %s · %s" % x for x in g)))
        if na["ohne_daten"] is not None:
            ohne = na["ohne_daten"]
            print("Hebel-Schalter AN, aber OHNE REGEL0-Daten (kein Signal moeglich): %d - %s" % (len(ohne), ", ".join(ohne) or "-"))
    except Exception as ex:                                      # noqa: BLE001
        print("  ⛔ REGEL0-Abgleich nicht lesbar: %s %s" % (ex.__class__.__name__, ex))
    # P9 (10.10.2026, G-O): die NB-Kontrollen aus Basisinfos/nb_kontrollen.yaml - automatische live ausgewertet, dieselbe Quelle wie
    # die Statusseite (Karte "Offene NB-Kontrollen"). Nur die offenen; die Historie steht in der Datei.
    print()
    print("-" * 100)
    try:
        c = ro(prod) if os.path.exists(prod) else None
        try:
            ko = BL.kontrollen(c, DATEN)
        finally:
            if c is not None:
                c.close()
        if ko.get("fehlt"):
            print("NB-KONTROLLEN: Basisinfos/nb_kontrollen.yaml FEHLT")
        else:
            print("NB-KONTROLLEN (Stand %s): offen %d · ueberfaellig %d" % (ko.get("stand"), ko["offen"], ko["ueberfaellig"]))
            for e in ko["eintraege"]:
                if e.get("status") != "offen":
                    continue
                zustand = e.get("status_live") or ("UEBERFAELLIG" if e["ueberfaellig"] else "offen")
                print("    %-10s %-24s %-11s bis %-10s %s" % (e.get("id"), zustand, e.get("art"), e.get("faellig_bis") or "-",
                                                         str(e.get("titel"))[:90]))
                if e.get("auto_beleg"):
                    print("        automatisch: %s" % e["auto_beleg"])
    except Exception as ex:                                      # noqa: BLE001
        print("  ⛔ NB-Kontrollen nicht lesbar: %s %s" % (ex.__class__.__name__, ex))
    print()
    print("SCHLUSS: vollstaendig")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
