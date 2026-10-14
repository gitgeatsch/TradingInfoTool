"""Wegwerf-Ordner fuer Pruefstaende, Gegenproben und die Suite - auf D:, mit einem Aufraeumen, das NICHT still scheitert (15.10.2026).

Nutzer 15.10.: *"Analysiere warum meine C-Partition vollaeuft"* -> 48 liegengebliebene Wegwerf-Ordner (16 GB) in %TEMP%.
Ursache: ``shutil.rmtree(T, ignore_errors=True)`` am Ende der Pruefstaende. Unter Windows laesst sich eine SQLite-Datei nicht
loeschen, solange eine Verbindung offen ist - und ``ignore_errors`` hat genau das verschwiegen. Jede Kopie (~0,7 GB) blieb liegen.

Nutzer: *"temporaere Dateien loeschen, wenn nicht mehr benoetigt - kannst du nicht auf D arbeiten?"* -> ja, dieses Modul:

    import wegwerf                     # ab jetzt liegen ALLE tempfile-Ordner dieses Prozesses unter BASIS (D:)
    T = tempfile.mkdtemp(prefix="p22_")
    ...
    wegwerf.aufraeumen(T)              # schliesst offene SQLite-Verbindungen in T, loescht mit Wiederholung, meldet laut, was bleibt

Beim Import werden Reste frueherer Laeufe (aelter als ALT_STUNDEN) unter BASIS entfernt - auch die eines abgebrochenen Laufs.
⚠️ Nur unter BASIS wird geloescht, nie anderswo. Am NB laeuft das nicht (die Suite laeuft dort nicht); ohne Laufwerk D: faellt
BASIS auf den System-Temp zurueck. ``TIT_WEGWERF`` (Umgebung) setzt einen anderen Ort.
"""
from __future__ import annotations

import atexit
import gc
import logging
import os
import shutil
import sqlite3
import stat
import sys
import tempfile
import time

ALT_STUNDEN = 12
_D = "D:\\"
BASIS = os.environ.get("TIT_WEGWERF") or (os.path.join(_D, "CLAUDE_Temp", "TradingInfoTool") if os.path.isdir(_D)
                                          else os.path.join(tempfile.gettempdir(), "TradingInfoTool"))
os.makedirs(BASIS, exist_ok=True)
tempfile.tempdir = BASIS


def _unter(datei: str, ordner: str) -> bool:
    try:
        a, b = os.path.normcase(os.path.abspath(datei)), os.path.normcase(os.path.abspath(ordner))
    except (TypeError, ValueError):
        return False
    return a == b or a.startswith(b.rstrip("\\/") + os.sep)


def _schliesse_verbindungen(ordner: str) -> int:
    """Schliesst jede noch offene SQLite-Verbindung und jeden Log-Handler, deren Datei unter ``ordner`` liegt. -> Anzahl."""
    n = 0
    gc.collect()
    for o in gc.get_objects():
        if isinstance(o, sqlite3.Connection):
            try:
                for _, _, f in o.execute("PRAGMA database_list").fetchall():
                    if f and _unter(f, ordner):
                        o.close()
                        n += 1
                        break
            except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                pass                      # schon geschlossen oder in einem anderen Thread angelegt
    for lg in [logging.getLogger()] + [logging.getLogger(x) for x in list(logging.root.manager.loggerDict)]:
        for h in list(getattr(lg, "handlers", [])):
            if isinstance(h, logging.FileHandler) and _unter(h.baseFilename, ordner):
                h.close()
                lg.removeHandler(h)
                n += 1
    gc.collect()
    return n


def _groesse_mb(ordner: str) -> float:
    s = 0
    for wurzel, _, dateien in os.walk(ordner):
        for d in dateien:
            try:
                s += os.path.getsize(os.path.join(wurzel, d))
            except OSError:
                pass
    return s / 1024 ** 2


def aufraeumen(ordner: str, versuche: int = 4) -> bool:
    """Loescht ``ordner`` (nur unter BASIS oder dem System-Temp). True = weg. False = laut gemeldet, was bleibt."""
    if not ordner or not os.path.exists(ordner):
        return True
    if not (_unter(ordner, BASIS) or _unter(ordner, tempfile.gettempdir()) or _unter(ordner, os.environ.get("TEMP", "") or BASIS)):
        print("⚠⚠ wegwerf.aufraeumen: %s liegt nicht unter %s - NICHT geloescht" % (ordner, BASIS), file=sys.stderr)
        return False
    _schliesse_verbindungen(ordner)

    def _schreibbar(func, pfad, *_):
        # schreibgeschuetzte Dateien (z. B. Git-Objekte in einem Wegwerf-Repo) loescht Windows erst nach chmod
        os.chmod(pfad, stat.S_IWRITE)
        func(pfad)
    for i in range(versuche):
        try:
            if sys.version_info >= (3, 12):
                shutil.rmtree(ordner, onexc=_schreibbar)
            else:
                shutil.rmtree(ordner, onerror=_schreibbar)
            return True
        except OSError:
            time.sleep(0.5 * (i + 1))
            _schliesse_verbindungen(ordner)
    print("⚠⚠⚠ WEGWERF-ORDNER NICHT GELOESCHT: %s (%.0f MB) - eine Datei ist noch offen. Er wird beim naechsten Lauf "
          "(aelter als %d h) entfernt." % (ordner, _groesse_mb(ordner), ALT_STUNDEN), file=sys.stderr)
    return False


def alte_reste(stunden: float = ALT_STUNDEN) -> list:
    """Entfernt Ordner unter BASIS, die aelter als ``stunden`` sind (Reste abgebrochener Laeufe). -> Liste der entfernten."""
    weg = []
    jetzt = time.time()
    for name in os.listdir(BASIS):
        p = os.path.join(BASIS, name)
        try:
            if jetzt - os.path.getmtime(p) > stunden * 3600:
                if os.path.isdir(p):
                    shutil.rmtree(p)
                else:
                    os.remove(p)              # auch einzelne Wegwerf-Dateien (mkstemp, NamedTemporaryFile)
                weg.append(name)
        except OSError:
            pass
    return weg


_REST = alte_reste()

# ── Aufraeumen beim Programmende fuer ALLES, was dieser Prozess per tempfile angelegt hat (auch TemporaryDirectory) ─────────────
# Anlass (Suite-Lauf 15.10.): viele Pakete legen Wegwerf-Ordner an und loeschen sie nie (r0_tw_*, aufn_*, ...). Statt jede Stelle
# einzeln zu suchen, merkt sich das Modul jeden angelegten Ordner und raeumt ihn am Ende auf - laut, wenn es nicht geht.
_ANGELEGT: list = []
_mkdtemp_original = tempfile.mkdtemp


def _mkdtemp(*a, **k):
    p = _mkdtemp_original(*a, **k)
    _ANGELEGT.append(p)
    return p


tempfile.mkdtemp = _mkdtemp


@atexit.register
def _am_ende() -> None:
    for p in reversed(_ANGELEGT):
        if os.path.exists(p):
            aufraeumen(p)
