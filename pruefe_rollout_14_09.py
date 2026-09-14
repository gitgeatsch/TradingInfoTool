# -*- coding: utf-8 -*-
"""Nach dem Rollout vom 14.09.2026 AM NOTEBOOK: ist alles angekommen?

AUFRUF (am Notebook, fruehestens 30 Minuten nach dem Neustart):

    python pruefe_rollout_14_09.py

⚠️⚠️ NUR LESEND. `data/tradinginfotool.db` ist am Notebook die PRODUKTION -
jede Verbindung hier ist `mode=ro`. Das Skript startet keinen Job und ruft
keine Boerse auf.

WAS GEPRUEFT WIRD - je Punkt der Befund, der ihn traegt:

    1  Codestand: der erwartete Commit ist ausgecheckt und die neuen Module
       sind importierbar (sonst ModuleNotFoundError im Betrieb)
    2  Terminmarkt (Schritt 54, 2.452-gebaut): der eigene Job schreibt fuer
       rund 39 Kryptowerte, nicht aelter als 30 Minuten
    3  Lesegrenze: BTC bekommt frische Terminmarkt-Zahlen, keine ,veraltet'
    4  Umlaufmenge (2.453-turnover-gebaut): `externe_reihen` hat SplyCur fuer
       rund 61 Werte geholt, und `marktrang.umlaufmengen` findet sie
    5  Migration (Schritt 48): `signals.kurs_bei_empfehlung_eur` existiert
       (erst nach dem ersten Umlauf der Rollen-Kette)
    6  Datenfrische der beiden Quellen

Jede Zeile sagt OK, WARTEN (noch zu frueh) oder FEHLER - mit dem Grund.

⚠️ DIE AUSGABE LANDET ZUSAETZLICH IM AUSTAUSCHORDNER (Nutzervorgabe 14.09.):
`Claude_Austauschordner/Pruefungen/pruefe_rollout_14_09_<Geraet>.txt`. Der
Laufwerksbuchstabe ist je Geraet verschieden (Notebook G:, Desktop K:) - er
wird deshalb NICHT fest eingetragen, sondern ueber
`extract_notebook_diagnose._google_drive_wurzel()` gesucht, dieselbe Stelle,
die auch Export und Suite benutzen. Der Geraetename im Dateinamen verhindert,
dass ein Desktop-Lauf den Notebook-Lauf ueberschreibt.
"""
from __future__ import annotations

import io
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = "data/tradinginfotool.db"
ERGEBNIS: list[tuple[str, str, str]] = []


def zeile(urteil: str, was: str, grund: str = "") -> None:
    ERGEBNIS.append((urteil, was, grund))
    print(f"  {urteil:<7} {was}" + (f"\n          ({grund})" if grund else ""))


def ro():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def _zeit(t):
    z = datetime.fromisoformat(str(t))
    return z if z.tzinfo else z.replace(tzinfo=timezone.utc)


def main() -> int:
    jetzt = datetime.now(timezone.utc)
    print("=" * 76)
    print("ROLLOUT 14.09.2026 - KONTROLLE AM NOTEBOOK (nur lesend)")
    print("=" * 76)

    # 1 CODESTAND
    try:
        kopf = subprocess.run(["git", "log", "-1", "--format=%h %s"],
                              capture_output=True, text=True).stdout.strip()
    except Exception as exc:                                 # noqa: BLE001
        kopf = f"unbekannt ({exc})"
    print(f"\n  Commit: {kopf}")
    try:
        import agent.signal_ansicht  # noqa: F401
        import agent.terminmarkt_sammlung  # noqa: F401
        from api.onchain import get_splycur_history  # noqa: F401
        zeile("OK", "neue Module importierbar")
    except Exception as exc:                                 # noqa: BLE001
        zeile("FEHLER", "neue Module importierbar",
              f"{type(exc).__name__}: {exc} - Pull unvollstaendig?")
        return 1

    c = ro()
    try:
        # 2 TERMINMARKT
        grenze = (jetzt - timedelta(minutes=30)).isoformat()
        n = c.execute("SELECT COUNT(DISTINCT symbol) FROM open_interest_snapshot "
                      "WHERE fetched_at >= ?", (grenze,)).fetchone()[0]
        juengst = c.execute("SELECT MAX(fetched_at) FROM open_interest_snapshot").fetchone()[0]
        if n >= 35:
            zeile("OK", f"Terminmarkt: {n} Werte in den letzten 30 Minuten")
        elif n > 0:
            zeile("WARTEN", f"Terminmarkt: erst {n} Werte in 30 Minuten",
                  "ein Durchlauf dauert rund 2,5 Minuten - in 15 Minuten wiederholen")
        else:
            zeile("FEHLER", "Terminmarkt: KEINE neue Zeile in 30 Minuten",
                  f"juengste Zeile {juengst} - im Log nach "
                  "'Terminmarkt-Sammlung' suchen")

        # 3 LESEGRENZE
        from agent import positionierung as PO
        lage = PO.lage(c, "BTC")
        if lage.get("veraltet"):
            zeile("FEHLER" if n else "WARTEN", "BTC-Terminmarkt noch ,veraltet'",
                  str(lage["veraltet"][:1]))
        elif lage.get("oi_jetzt") is not None:
            zusatz = ("" if lage.get("oi_aenderung_pct") is not None else
                      " - OI-Aenderung erst nach 8 Stunden (erwartet)")
            zeile("OK", "BTC bekommt frische Terminmarkt-Zahlen" + zusatz)
        else:
            zeile("FEHLER", "BTC ohne Terminmarkt", str(lage.get("fehlt")))

        # 4 UMLAUFMENGE
        from agent import marktrang as MR
        z = c.execute("SELECT COUNT(DISTINCT schluessel), MAX(datum), MAX(geholt_am) "
                      "FROM externe_reihe WHERE quelle = ?",
                      (MR.SPLYCUR_QUELLE,)).fetchone()
        if (z[0] or 0) >= 55:
            zeile("OK", f"Umlaufmenge: {z[0]} Werte, Datenstand {z[1]}, geholt {str(z[2])[:16]}")
        else:
            zeile("FEHLER", f"Umlaufmenge: nur {z[0] or 0} Werte",
                  "externe_reihen laeuft beim Start - im Log nach 'Umlaufmenge' suchen")
        menge = MR.umlaufmengen(db_pfad=DB)
        zeile("OK" if len(menge) >= 55 else "FEHLER",
              f"marktrang.umlaufmengen findet {len(menge)} Werte",
              "" if len(menge) >= 55 else "turnover faellt sonst aus (2.453-turnover)")

        # 5 MIGRATION
        spalten = {r[1] for r in c.execute("PRAGMA table_info(signals)")}
        if "kurs_bei_empfehlung_eur" in spalten:
            zeile("OK", "signals.kurs_bei_empfehlung_eur angelegt")
        else:
            zeile("WARTEN", "signals.kurs_bei_empfehlung_eur noch nicht da",
                  "entsteht beim ersten Umlauf der Rollen-Kette (15-Minuten-Takt)")

        # 6 DATENFRISCHE
        from agent import datenfrische as DF
        for zz in DF.pruefe(c):
            if zz["quelle"] in ("terminmarkt", MR.SPLYCUR_QUELLE):
                zeile("OK" if zz["urteil"] == "frisch" else "FEHLER",
                      f"Datenfrische {zz['quelle']}: {zz['urteil']}",
                      f"Datenstand {zz['datenstand']}, Abruf {zz['abrufstand']}")
    finally:
        c.close()

    fehler = [e for e in ERGEBNIS if e[0] == "FEHLER"]
    warten = [e for e in ERGEBNIS if e[0] == "WARTEN"]
    print("\n" + "=" * 76)
    print(f"{len(ERGEBNIS)} Punkte: {len(fehler)} FEHLER, {len(warten)} WARTEN")
    return 1 if fehler else 0


class _Mitschrift(io.StringIO):
    """Schreibt auf die Konsole UND merkt sich den Text."""

    def __init__(self, konsole):
        super().__init__()
        self._konsole = konsole

    def write(self, text):
        self._konsole.write(text)
        return super().write(text)

    def flush(self):
        self._konsole.flush()


def _in_austauschordner(text: str) -> None:
    """Best effort - ein fehlendes Laufwerk bricht die Kontrolle nicht ab."""
    try:
        import platform
        from extract_notebook_diagnose import _google_drive_wurzel
        ziel = _google_drive_wurzel() / "Claude_Austauschordner" / "Pruefungen"
        ziel.mkdir(parents=True, exist_ok=True)
        geraet = (platform.node() or "unbekannt").strip() or "unbekannt"
        pfad = ziel / f"pruefe_rollout_14_09_{geraet}.txt"
        zeitpunkt = datetime.now(timezone.utc).isoformat(timespec="seconds")
        kopf = f"# Geraet: {geraet}\n# Geschrieben: {zeitpunkt}\n\n"
        pfad.write_text(kopf + text, encoding="utf-8")
        print(f"\n(Volltext geschrieben nach {pfad})")
    except Exception as exc:                                 # noqa: BLE001
        print(f"\n(Konnte die Ausgabe nicht in den Austauschordner schreiben: {exc})")


if __name__ == "__main__":
    _konsole = sys.stdout
    _mit = _Mitschrift(_konsole)
    sys.stdout = _mit
    try:
        _code = main()
    finally:
        sys.stdout = _konsole
    _in_austauschordner(_mit.getvalue())
    raise SystemExit(_code)
