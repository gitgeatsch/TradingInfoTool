"""Watchdog + Tray-Monitor fuer TradingInfoTool (2026-07-13, siehe
Basisinfos/Regelwerksmanual.md Kap. 12). Bewusst ein SEPARATER Prozess statt in
main.py eingebettet: ein Tray-Icon im selben Prozess wie ein haengender/
unsichtbarer Tk-Mainloop waere im schlimmsten Fall selbst mitbetroffen -
Ausloeser war ein Vorfall am 24/7-Notebook, bei dem die GUI ueber Nacht
verschwand, waehrend Scheduler/Agent im Hintergrund unbeeindruckt weiterliefen
(kein Absturz, vermutlich ein eingefrorenes/unsichtbares Fenster). Startet
main.py als Kindprozess, erkennt ueber die Heartbeat-Datei (siehe
ui/app.py::HEARTBEAT_PATH) auch einen "Prozess lebt, aber GUI reagiert nicht
mehr"-Zustand, nicht nur einen echten Prozess-Tod.

Bewusst KEIN Windows-Service mit Auto-Restart (Nutzer-Entscheidung,
2026-07-13): ein kaputter Auto-Restart-Loop waere selbst ein stilles
Fehlerbild. Stattdessen sichtbarer Tray-Status + manueller Neustart-Klick."""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Direktstart als Skript (die Desktop-Verknuepfung ruft genau das auf) legt
# monitor/ statt dem Projekt-Root in sys.path[0] - ohne diesen Insert schlaegt
# "import config" fehl, sobald ueber die echte Verknuepfung gestartet wird
# (waehrend der Entwicklung per "python -m monitor.watchdog" aus dem
# Projekt-Root nicht sichtbar, da dort sys.path[0] bereits der Projekt-Root
# ist - ein klassischer "funktioniert nur beim Entwickler" Stolperstein).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
from remote.server import DEFAULT_PORT  # noqa: E402

import pystray  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

MAIN_PY = PROJECT_ROOT / "main.py"
DATA_DIR = PROJECT_ROOT / "data"
HEARTBEAT_PATH = DATA_DIR / "gui_heartbeat.txt"
CRASH_LOG_PATH = DATA_DIR / "watchdog_crash.log"
PID_PATH = DATA_DIR / "watchdog.pid"
# Neustart-Bruecke von der Remote-Steuer-Seite (2026-07-14, siehe
# remote/server.py::api_restart_app()) - main.py kann sich nicht selbst neu
# starten (ein haengender Tk-Mainloop kann sich nicht selbst beenden), deshalb
# nur eine Flag-Datei schreiben, die hier im ohnehin laufenden 5-Sek.-Takt
# aufgegriffen wird.
RESTART_FLAG_PATH = DATA_DIR / "watchdog_restart_requested.txt"

CHECK_INTERVAL_SECONDS = 5
STALE_THRESHOLD_SECONDS = 30
STARTUP_GRACE_SECONDS = 60
CRASH_LOG_MAX_BYTES = 2_000_000

_COLORS = {
    "starting": (150, 150, 150),
    "ok": (76, 175, 80),
    "stale": (224, 160, 48),
    "dead": (224, 96, 90),
}

_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _build_icon_image(state: str) -> Image.Image:
    color = _COLORS.get(state, _COLORS["dead"])
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((8, 8, 56, 56), fill=color)
    return img


_SW_RESTORE = 9


def _bring_gui_to_front() -> bool:
    """Sucht das Tk-Fenster ueber den exakten Fenstertitel (siehe
    ui/app.py::TradingInfoToolApp.__init__ -> self.title("TradingInfoTool"))
    und holt es in den Vordergrund. Gibt False zurueck, wenn kein passendes
    Fenster gefunden wurde (Aufrufer faellt dann auf einen echten Neustart
    zurueck)."""
    hwnd = ctypes.windll.user32.FindWindowW(None, "TradingInfoTool")
    if not hwnd:
        return False
    ctypes.windll.user32.ShowWindow(hwnd, _SW_RESTORE)
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    return True


def _pid_alive(pid: int) -> bool:
    """os.kill(pid, 0) ist unter Windows KEIN sicherer Existenz-Check - Python
    ruft dort intern TerminateProcess(handle, 0) auf, wuerde also einen
    tatsaechlich noch laufenden Prozess beenden statt ihn nur zu pruefen.
    OpenProcess (nur Abfrage-Rechte) + CloseHandle ist der sichere Weg."""
    handle = ctypes.windll.kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def _check_existing_instance() -> None:
    """Verhindert ein zweites main.py+Watchdog-Paar (streiten sich sonst um
    dieselbe SQLite-Datei und Port 8765). Zeigt eine Messagebox statt eines
    stillen Exits, damit ein erneuter Doppelklick auf die Verknuepfung nicht
    wie "nichts passiert" wirkt."""
    if PID_PATH.exists():
        try:
            old_pid = int(PID_PATH.read_text().strip())
        except (ValueError, OSError):
            old_pid = None
        if old_pid and _pid_alive(old_pid):
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "TradingInfoTool - Watchdog laeuft bereits",
                f"Ein Watchdog-Prozess laeuft offenbar schon (PID {old_pid}).\n\n"
                "Bitte zuerst ueber das Tray-Icon beenden, bevor ein zweiter "
                "gestartet wird.",
            )
            root.destroy()
            sys.exit(1)
    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")


class Watchdog:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._proc: subprocess.Popen | None = None
        self._started_at: float = 0.0
        self._crash_log_fh = self._open_crash_log()

    def _open_crash_log(self):
        # Einfache Groessenbremse statt echter Rotation - dieses Log ist ein
        # selten beschriebenes Sicherheitsnetz (nur Prozess-Start/-Crash-
        # Ausgaben), keine hochfrequente Log-Datei wie tradinginfotool.log.
        try:
            if CRASH_LOG_PATH.exists() and CRASH_LOG_PATH.stat().st_size > CRASH_LOG_MAX_BYTES:
                CRASH_LOG_PATH.unlink()
        except OSError:
            pass
        return open(CRASH_LOG_PATH, "a", encoding="utf-8", errors="replace")

    def start_main_process(self) -> None:
        self._crash_log_fh.write(f"\n===== Start {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        self._crash_log_fh.flush()
        self._proc = subprocess.Popen(
            [sys.executable, str(MAIN_PY)],
            cwd=str(PROJECT_ROOT),
            stdout=self._crash_log_fh,
            stderr=self._crash_log_fh,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        self._started_at = time.monotonic()

    def _terminate_main_process(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    def _heartbeat_age_seconds(self) -> float | None:
        try:
            mtime = HEARTBEAT_PATH.stat().st_mtime
        except OSError:
            return None
        return time.time() - mtime

    def _current_state(self) -> tuple[str, str]:
        if self._proc is None or self._proc.poll() is not None:
            return "dead", "TradingInfoTool: Prozess beendet"

        since_start = time.monotonic() - self._started_at
        age = self._heartbeat_age_seconds()

        if age is None or age > STALE_THRESHOLD_SECONDS:
            if since_start < STARTUP_GRACE_SECONDS:
                return "starting", "TradingInfoTool: startet..."
            if age is None:
                return "stale", "TradingInfoTool: keine Heartbeat-Datei gefunden"
            return "stale", f"TradingInfoTool: GUI reagiert seit {age:.0f}s nicht"

        return "ok", "TradingInfoTool: laeuft"

    def _check_remote_restart_request(self, icon: pystray.Icon) -> None:
        """Siehe RESTART_FLAG_PATH oben - Fund wird sofort verarbeitet UND die
        Datei geloescht, damit derselbe Request nicht bei jedem Poll-Tick erneut
        einen Neustart ausloest."""
        if not RESTART_FLAG_PATH.exists():
            return
        try:
            RESTART_FLAG_PATH.unlink()
        except OSError:
            pass
        self.on_restart(icon, None)

    def _monitor_loop(self, icon: pystray.Icon) -> None:
        icon.visible = True
        while icon.visible:
            self._check_remote_restart_request(icon)
            state, tooltip = self._current_state()
            icon.icon = _build_icon_image(state)
            icon.title = tooltip
            time.sleep(CHECK_INTERVAL_SECONDS)

    def on_show_window(self, icon: pystray.Icon, item) -> None:
        """Leichtgewichtige Alternative zu 'Neu starten': holt das bestehende
        Fenster nur in den Vordergrund (minimiert/verschoben/hinter anderen
        Fenstern), OHNE main.py neu zu starten und damit den laufenden
        Zustand zu verwerfen - passt besser zum urspruenglichen Notebook-
        Vorfall (Fenster unsichtbar, Prozess aber quicklebendig) als ein
        harter Neustart. Findet kein Fenster-Handle (z.B. Prozess tatsaechlich
        tot/so verhangen, dass gar kein Fenster mehr existiert), faellt es
        auf den harten Neustart zurueck."""
        if not _bring_gui_to_front():
            self.on_restart(icon, item)

    def on_restart(self, icon: pystray.Icon, item) -> None:
        self._terminate_main_process()
        self.start_main_process()

    def on_open_status(self, icon: pystray.Icon, item) -> None:
        config.load_env()
        token = os.environ.get("REMOTE_ACCESS_TOKEN", "")
        webbrowser.open(f"http://127.0.0.1:{DEFAULT_PORT}/?token={token}")

    def on_stop(self, icon: pystray.Icon, item) -> None:
        self._terminate_main_process()
        icon.stop()

    def run(self) -> None:
        self.start_main_process()
        menu = pystray.Menu(
            pystray.MenuItem("Fenster anzeigen", self.on_show_window),
            pystray.MenuItem("Status-Details", self.on_open_status),
            pystray.MenuItem("Neu starten", self.on_restart),
            pystray.MenuItem("Beenden", self.on_stop),
        )
        icon = pystray.Icon("TradingInfoTool", _build_icon_image("starting"), "TradingInfoTool: startet...", menu)
        try:
            icon.run(setup=self._monitor_loop)
        finally:
            self._terminate_main_process()
            self._crash_log_fh.close()
            try:
                PID_PATH.unlink()
            except OSError:
                pass


def main() -> None:
    _check_existing_instance()
    Watchdog().run()


if __name__ == "__main__":
    main()
