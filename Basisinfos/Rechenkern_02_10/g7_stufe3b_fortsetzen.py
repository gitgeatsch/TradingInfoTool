"""G7 STUFE 3b — FORTSETZEN NACH EINER UNTERBRECHUNG (Nutzer 13.11.2026: *„sorge dafür, sollte es eine Unterbrechung geben,
dass wir sofort fortsetzen können“*)

⚠️ KEIN BLICK AUF URTEILE. Gezählt wird nur (Zeilen je Phase, lesbar ja/nein); kein Bedenken-Wert, kein Kurs.

    python Basisinfos/Rechenkern_02_10/g7_stufe3b_fortsetzen.py                 -> prüfen, bei Bedarf neu starten, sichern
    python Basisinfos/Rechenkern_02_10/g7_stufe3b_fortsetzen.py --nur-pruefen   -> nur berichten: nichts starten, nichts sichern

Regeln (vorab, 13.11.):
  1. 3b vollständig (2.058 Zeilen phase 3b)            -> nichts starten; Hinweis: prüfen, gegenprüfen, --messung GENAU EINMAL (Hand)
  2. ein Prozess „agent.finales_llm --lauf3b“ läuft    -> nichts starten (nie zwei Läufe gleichzeitig)
  3. die jüngste Fehlerdatei ist nicht leer            -> NICHT starten, melden: erst die Ursache (Memory: Neustart nur bei behebbarem Abbruch)
  4. sonst                                             -> sitzungsunabhängig per WMI neu starten, wie am 11.11. (eigene Prozessgruppe,
                                                          ohne Fenster), neues Protokollpaar data/_g7_stufe3b_lauf_<UTC>.txt / _err.txt.
                                                          `--lauf3b` prüft selbst: Vorprüfung WEITER, Eingaben 3a ungeändert; vorhandene
                                                          Urteile werden übersprungen (kein Doppelaufruf).
  5. Sicherung der Ablage höchstens alle 12 h (sqlite-Backup, konsistent auch bei laufendem Schreiber) nach data/_g7/sicherung/ und
     Y:\\Backup_TradingInfoTool\\G7_finales_llm\\ — je die letzten 3 Stände; nur Dateien dieses Musters werden entfernt.
Protokoll: data/_g7_stufe3b_fortsetzen.log (eine Zeile je Aufruf). Die Messung startet dieses Werkzeug NIE.
"""
import glob
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
DATA = os.path.join(PROJ, "data")
ABLAGE = os.path.join(DATA, "_g7", "finales_llm.db")
SOLL_3B = 2058
LOG = os.path.join(DATA, "_g7_stufe3b_fortsetzen.log")
SICHERUNG = [os.path.join(DATA, "_g7", "sicherung"), r"Y:\Backup_TradingInfoTool\G7_finales_llm"]
SICHERN_ALLE_H, BEHALTEN = 12, 3
PYTHON = r"D:\Python\python.exe"
OHNE_FENSTER = 0x08000000          # CREATE_NO_WINDOW: aus pythonw (Aufgabenplanung) kein aufblitzendes PowerShell-Fenster


def jetzt() -> datetime:
    return datetime.now(timezone.utc)


def zaehle() -> tuple[int, int]:
    """-> (Zeilen phase 3b, davon lesbar). Nur lesend."""
    c = sqlite3.connect("file:%s?mode=ro" % ABLAGE.replace("\\", "/"), uri=True)
    try:
        n, ok = c.execute("SELECT COUNT(*), COALESCE(SUM(form_ok), 0) FROM urteil WHERE phase='3b'").fetchone()
    finally:
        c.close()
    return int(n), int(ok)


def laeufe() -> list[tuple[int, str]]:
    """Laufende Prozesse mit 'agent.finales_llm' und '--lauf3b' in der Befehlszeile (python oder die cmd-Hülle)."""
    # nur python/cmd: die PowerShell-Abfrage selbst trägt beide Wörter in IHRER Befehlszeile (Test 13.11.: sie zählte sich mit)
    ps = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('python.exe','cmd.exe') -and $_.ProcessId -ne $PID -and "
          "$_.CommandLine -like '*agent.finales_llm*' -and $_.CommandLine -like '*--lauf3b*' } | "
          "ForEach-Object { '{0}|{1}' -f $_.ProcessId, $_.Name }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=120, creationflags=OHNE_FENSTER)
    if r.returncode != 0:
        raise RuntimeError("Prozessliste nicht lesbar: %s" % r.stderr.strip()[:200])
    aus = []
    for z in r.stdout.splitlines():
        if "|" in z:
            p, n = z.strip().split("|", 1)
            aus.append((int(p), n))
    return aus


def juengste_fehlerdatei() -> tuple[str, int] | None:
    f = sorted(glob.glob(os.path.join(DATA, "_g7_stufe3b_lauf*_err.txt")), key=os.path.getmtime)
    return (f[-1], os.path.getsize(f[-1])) if f else None


def starte(befehl: str | None = None) -> str:
    """befehl nur für den Prüfstand (harmloser Ersatz); im Betrieb immer der 3b-Lauf."""
    marke = jetzt().strftime("%Y%m%dT%H%MZ")
    aus, err = "data\\_g7_stufe3b_lauf_%s.txt" % marke, "data\\_g7_stufe3b_lauf_%s_err.txt" % marke
    cmd = befehl or 'cmd /c "set PYTHONIOENCODING=utf-8&& %s -m agent.finales_llm --lauf3b > %s 2> %s"' % (PYTHON, aus, err)
    ps = ("$su = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{CreateFlags=[uint32](0x08000000 -bor "
          "0x00000200); ShowWindow=[uint16]0}; $r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments "
          "@{CommandLine='%s'; CurrentDirectory='%s'; ProcessStartupInformation=$su}; '{0}|{1}' -f $r.ReturnValue, $r.ProcessId"
          % (cmd.replace("'", "''"), PROJ.replace("'", "''")))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=120, creationflags=OHNE_FENSTER)
    rv, pid = (r.stdout.strip().split("|") + ["?", "?"])[:2]
    if rv != "0":
        raise RuntimeError("WMI-Start fehlgeschlagen (ReturnValue %s): %s" % (rv, r.stderr.strip()[:200]))
    return "gestartet (cmd-PID %s), Protokoll %s" % (pid, aus)


def sichere() -> str:
    """sqlite-Backup, höchstens alle 12 h, je Ziel die letzten 3 Stände."""
    teile = []
    for ziel in SICHERUNG:
        try:
            os.makedirs(ziel, exist_ok=True)
            alt = sorted(glob.glob(os.path.join(ziel, "finales_llm_*.db")))
            if alt and (jetzt().timestamp() - os.path.getmtime(alt[-1])) < SICHERN_ALLE_H * 3600:
                teile.append("%s: jung genug" % ziel)
                continue
            dst = os.path.join(ziel, "finales_llm_%s.db" % jetzt().strftime("%Y%m%dT%H%MZ"))
            q = sqlite3.connect("file:%s?mode=ro" % ABLAGE.replace("\\", "/"), uri=True)
            d = sqlite3.connect(dst)
            q.backup(d)
            ok = d.execute("PRAGMA integrity_check").fetchone()[0]
            n = d.execute("SELECT COUNT(*) FROM urteil").fetchone()[0]
            d.close()
            q.close()
            for f in sorted(glob.glob(os.path.join(ziel, "finales_llm_*.db")))[:-BEHALTEN]:
                os.remove(f)
            teile.append("%s: %s (%s, %d Urteile)" % (ziel, os.path.basename(dst), ok, n))
        except Exception as e:                                          # noqa: BLE001
            teile.append("%s: FEHLER %s" % (ziel, e))
    return " · ".join(teile)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                                   # noqa: BLE001
        pass
    nur = "--nur-pruefen" in sys.argv
    n, ok = zaehle()
    L = laeufe()
    fe = juengste_fehlerdatei()
    lage = "3b %d/%d (lesbar %d) · Läufe %s · Fehlerdatei %s" % (
        n, SOLL_3B, ok, [p for p, _ in L] or "keiner", ("%s %d B" % (os.path.basename(fe[0]), fe[1])) if fe else "keine")
    if n >= SOLL_3B:
        tat = "FERTIG - nicht starten; nächster Schritt von Hand: prüfen, gegenprüfen, --messung GENAU EINMAL"
    elif L:
        tat = "läuft - nichts zu tun"
    elif fe and fe[1] > 0:
        tat = "NICHT gestartet: jüngste Fehlerdatei nicht leer - erst die Ursache ansehen"
    elif nur:
        tat = "würde neu starten (--nur-pruefen)"
    else:
        tat = starte()
    if not nur:
        tat += " · Sicherung: " + sichere()
    zeile = "%s · %s · %s" % (jetzt().strftime("%Y-%m-%dT%H:%M:%SZ"), lage, tat)
    if not nur:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(zeile + "\n")
    if sys.stdout is not None:                     # pythonw (Aufgabenplanung, ohne Fenster) hat keine Konsole
        print(zeile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
