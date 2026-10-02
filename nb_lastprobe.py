"""Lastprobe fuer Schritt 7 (Basisinfos/Voranalyse_Schritt7_Betrieb_02_10.md) - misst, ob ein Geraet die REGEL0-Rechnung traegt.

NUR LESEN, KEINE DATEN: rechnet auf ZUFALLSREIHEN dieselben Bausteine, die der Betrieb braucht, und misst Zeit und Arbeitsspeicher:

    B1  stuendliche Kurse fuer 650 Assets x 1 Jahr (Zufallsreihen) erzeugen
    B2  rsi 14 und ATR (24 h) je Asset            - die Stundenrechnung
    B3  eigenes Normal (+5 % vor -5 % binnen 24 h, gleitend ueber 365 Tage) - das Teuerste je Stunde
    B4  Monatstraining: logistische Kurve mit Daempfung, 4 Zeitbloecke x 6 Stufen auf 250.000 Ankern (scipy.optimize)
    B5  eine Stunde bewerten: alle Assets, letzte Stunde, mit dem trainierten Modell

Kein Zugriff auf Projektdatenbanken, kein Netz. Ergebnis auf den Bildschirm und in den Austauschordner
(Notebook_Analysedaten/nb_lastprobe_<GERAET>.txt), wie nb_teilexport_betriebsdaten.py. Laeuft am Desktop UND am Notebook;
das Verhaeltnis der beiden Laufzeiten rechnet die echten Desktop-Messungen auf das Notebook um.

    python nb_lastprobe.py
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as w
import os
import platform
import sys
import time
from datetime import datetime

HIER = os.path.dirname(os.path.abspath(__file__))


class _PMC(ctypes.Structure):
    _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("a", ctypes.c_size_t), ("b", ctypes.c_size_t),
                ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("e", ctypes.c_size_t), ("f", ctypes.c_size_t)]


class _MEM(ctypes.Structure):
    _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong),
                ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong), ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong),
                ("x", ctypes.c_ulonglong)]


def _spitze_gb():
    try:
        p = _PMC(); p.cb = ctypes.sizeof(_PMC)
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = w.HANDLE
        k.K32GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.POINTER(_PMC), w.DWORD]
        return p.PeakWorkingSetSize / 1e9 if k.K32GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(p), p.cb) else float("nan")
    except Exception:                                         # noqa: BLE001
        return float("nan")


def _ram():
    try:
        m = _MEM(); m.l = ctypes.sizeof(_MEM)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.t / 1e9, m.a / 1e9
    except Exception:                                         # noqa: BLE001
        return float("nan"), float("nan")


def _drive():
    for b in ("G", "K", "H", "E", "F"):
        for o in ("My Drive", "Meine Ablage"):
            if os.path.isdir("%s:/%s" % (b, o)):
                return "%s:/%s" % (b, o)
    return None


class _Zwei:
    def __init__(self, a):
        self.a, self.teile = a, []

    def write(self, s):
        self.teile.append(s)
        return self.a.write(s)

    def flush(self):
        self.a.flush()


def _inhalt() -> int:
    import numpy as np
    import pandas as pd
    from scipy.optimize import minimize
    from scipy.special import expit
    gt, fr = _ram()
    print("=" * 100)
    print("LASTPROBE REGEL0 (Schritt 7, nur Zufallsreihen) - %s - Geraet %s - Python %s · numpy %s · scipy %s" % (
        datetime.now().strftime("%Y-%m-%d %H:%M"), platform.node(), sys.version.split()[0], np.__version__,
        __import__("scipy").__version__))
    print("Prozessor %s · %d logische Kerne · Arbeitsspeicher gesamt %.1f GB, frei %.1f GB" % (
        platform.processor(), os.cpu_count() or 0, gt, fr))
    print("=" * 100)
    zeiten = {}
    rng = np.random.default_rng(20261002)
    N, T = 650, 365 * 24
    t0 = time.time()
    lr = rng.normal(0, 0.012, size=(N, T)).astype(np.float64)
    cc = 100.0 * np.exp(np.cumsum(lr, axis=1))
    sp = np.abs(rng.normal(0, 0.008, size=(N, T)))
    hh, ll = cc * (1 + sp), cc * (1 - sp)
    zeiten["B1 Kurse 650 x 8760 h"] = time.time() - t0
    t0 = time.time()
    d = np.diff(cc, axis=1, prepend=cc[:, :1])
    auf = pd.DataFrame(np.where(d > 0, d, 0.0).T).rolling(14, min_periods=14).sum().to_numpy().T / 14
    ab = pd.DataFrame(np.where(d < 0, -d, 0.0).T).rolling(14, min_periods=14).sum().to_numpy().T / 14
    with np.errstate(divide="ignore", invalid="ignore"):
        rsi = 100 - 100 / (1 + auf / ab)
    atr = pd.DataFrame(((hh - ll) / cc).T).rolling(24, min_periods=24).mean().to_numpy().T * np.sqrt(24.0)
    zeiten["B2 rsi + ATR"] = time.time() - t0
    t0 = time.time()
    ziel = np.zeros((N, T), np.int8)                 # +5 % vor -5 % binnen 24 h (vereinfacht ueber das Hoch/Tief der Folgestunden)
    for s in range(1, 25):
        z = np.roll(cc, -s, axis=1) / cc
        ziel = np.where((ziel == 0) & (z >= 1.05), 1, np.where((ziel == 0) & (z <= 0.95), -1, ziel))
    treffer = (ziel == 1).astype(np.float64)
    normal = pd.DataFrame(treffer.T).rolling(24 * 365, min_periods=240).mean().to_numpy().T
    zeiten["B3 eigenes Normal (24 h voraus, 365 Tage gleitend)"] = time.time() - t0
    t0 = time.time()
    n_a = 250_000
    ix = rng.integers(0, N * T, n_a)
    X = np.column_stack([np.ones(n_a), np.nan_to_num(rsi.ravel()[ix], nan=50) / 100.0, (np.nan_to_num(rsi.ravel()[ix], nan=50) / 100.0) ** 2])
    y = treffer.ravel()[ix]
    blk = np.minimum((np.arange(n_a) * 4) // n_a, 3)

    def fit(lam, m):
        f = lambda b: float(np.sum(np.logaddexp(0, X[m] @ b) - y[m] * (X[m] @ b)) + lam * np.sum(b[1:] ** 2))
        return minimize(f, np.zeros(3), method="L-BFGS-B").x
    for lam in (20.0, 200.0, 2000.0, 20000.0, 200000.0, 2000000.0):
        for b in range(4):
            fit(lam, blk != b)
    beta = fit(2000.0, np.ones(n_a, bool))
    zeiten["B4 Monatstraining (6 Stufen x 4 Bloecke, 250.000 Anker)"] = time.time() - t0
    t0 = time.time()
    r_letzt = np.nan_to_num(rsi[:, -1], nan=50) / 100.0
    v = expit(beta[0] + beta[1] * r_letzt + beta[2] * r_letzt ** 2) - np.nan_to_num(normal[:, -1], nan=0.2)
    zeiten["B5 eine Stunde bewerten (650 Assets)"] = time.time() - t0
    for k, s in zeiten.items():
        print("  %-58s %8.2f s" % (k, s))
    print("  %-58s %8.2f s" % ("SUMME", sum(zeiten.values())))
    print("  Spitze Arbeitsspeicher dieses Laufs: %.2f GB · Ergebnis-Pruefsumme %.6f (muss auf beiden Geraeten gleich sein)" % (
        _spitze_gb(), float(np.nansum(v))))
    print("SCHLUSS: vollstaendig")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    zw = _Zwei(sys.stdout)
    sys.stdout = zw
    try:
        rc = _inhalt()
    finally:
        sys.stdout = zw.a
        w_ = _drive()
        if w_:
            ziel = os.path.join(w_, "Claude_Austauschordner", "Notebook_Analysedaten")
            os.makedirs(ziel, exist_ok=True)
            pf = os.path.join(ziel, "nb_lastprobe_%s.txt" % platform.node())
            with open(pf, "w", encoding="utf-8") as f:
                f.write("".join(zw.teile))
            print("➤ geschrieben nach %s" % pf)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
