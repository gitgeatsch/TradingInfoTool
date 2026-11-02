# -*- coding: utf-8 -*-
"""GDELT-PROBE AM NOTEBOOK — 14 Tage, viermal am Tag, die vier Nachrichtentöne (G7 §9.2 Bedingung 1, Voranalyse_Laufzeit §4.3/§7).

Nutzer 02.11.2026: *„ja, Skript bauen – prüfen, gegenprüfen und doku“*.

EIGENSTÄNDIG: nur Python-Standardbibliothek, KEIN Import aus dem Projekt, kein Pull, kein Betriebscode. Schreibt NUR die eigene
Datei ``gdelt_probe_<Rechner>.jsonl`` neben sich (Austauschordner) — nie ``tradinginfotool.db``, nie den Projektordner.

    python gdelt_probe.py                 # starten, Fenster offen lassen (Neustart setzt fort, Ende nach 14 Tagen von selbst)
    python gdelt_probe.py --stand         # was bisher geholt wurde
    python gdelt_probe.py --einmal --ausgabe <pfad>   # EINE Runde in eine Wegwerfdatei (Desktop-Prüfung)

Abfragen, Abstand zwischen zwei Abfragen (600 s), zweiter Versuch nach 120 s und Fenster (14 Tage bis heute 00:00 UTC) wie
``api/sichten_quellen.py --laufend`` — die Gleichheit prüft ``gdelt_probe_auswertung.py`` gegen den Quelltext (nicht abgeschrieben
geglaubt). Die Rohpunkte gehen UNVERÄNDERT in die Datei (auch die Uhrzeit), damit die Auswertung die Auflösung sieht.

Runden: zum Start, dann je Tag um 00:30, 06:30, 12:30, 18:30 UTC (01:30/07:30/13:30/19:30 MEZ). Eine verschlafene Runde wird bis
zur nächsten nachgeholt, danach zählt sie als ausgefallen — die Auswertung zählt das, nichts wird still übergangen.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

URL = "https://api.gdeltproject.org/api/v2/doc/doc"
H = {"User-Agent": "Mozilla/5.0 TradingInfoTool-Sichten"}
GDELT = {"krypto": "(bitcoin OR cryptocurrency) sourcelang:english", "fed": '"federal reserve" sourcelang:english',
         "aktien": '"stock market" sourcelang:english', "konflikt": "(war OR sanctions OR tariffs) sourcelang:english"}
GDELT_ABSTAND_S = 600
ZWEITER_VERSUCH_S = 120
LAUFEND_TAGE = 14
DAUER_TAGE = 14
SLOTS = ((0, 30), (6, 30), (12, 30), (18, 30))     # UTC
FASSUNG = "1 (02.11.2026)"

ORDNER = os.path.dirname(os.path.abspath(__file__))
RECHNER = os.environ.get("COMPUTERNAME") or socket.gethostname()


def jetzt() -> datetime:
    return datetime.now(timezone.utc)


def iso(t: datetime) -> str:
    return t.isoformat(timespec="seconds")


def ausgabe_pfad(a: list) -> str:
    p = a[a.index("--ausgabe") + 1] if "--ausgabe" in a else os.path.join(ORDNER, "gdelt_probe_%s.jsonl" % RECHNER)
    if not p.endswith(".jsonl") or os.path.basename(p).lower().startswith("tradinginfotool"):
        raise SystemExit("gdelt_probe schreibt NUR eine eigene .jsonl-Datei: %s" % p)
    return p


def schreibe(pfad: str, satz: dict) -> None:
    """Eine Zeile anhängen und sofort auf die Platte - ein Absturz verliert höchstens die laufende Abfrage."""
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps(satz, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def lies(pfad: str) -> list:
    if not os.path.exists(pfad):
        return []
    aus = []
    with open(pfad, encoding="utf-8") as f:
        for z in f:
            z = z.strip()
            if z:
                try:
                    aus.append(json.loads(z))
                except json.JSONDecodeError:      # halbe letzte Zeile nach einem Absturz: zählen, nicht abbrechen
                    aus.append({"art": "kaputt"})
    return aus


def slot_zeit(tag, h: int, m: int) -> datetime:
    return datetime(tag.year, tag.month, tag.day, h, m, tzinfo=timezone.utc)


def slots_zwischen(a: datetime, b: datetime) -> list:
    """Alle festen Rundenzeiten in [a, b)."""
    aus, tag = [], a.date()
    while tag <= b.date():
        for h, m in SLOTS:
            s = slot_zeit(tag, h, m)
            if a <= s < b:
                aus.append(s)
        tag += timedelta(days=1)
    return aus


def faellige_runde(t: datetime, erledigt: set, start: datetime) -> str | None:
    """Kennung der Runde, die jetzt laufen soll, oder None. Die Startrunde einmal; danach die jüngste feste Rundenzeit <= t, wenn
    sie noch nicht lief - eine ältere verschlafene ist damit vorbei (ausgefallen, die Auswertung zählt sie)."""
    if "start" not in erledigt:
        return "start"
    vorher = [s for s in slots_zwischen(start, t + timedelta(seconds=1))]
    if not vorher:
        return None
    k = iso(vorher[-1])
    return None if k in erledigt else k


def naechste_slotzeit(t: datetime) -> datetime:
    return slots_zwischen(t + timedelta(seconds=1), t + timedelta(days=1, seconds=1))[0]


def fenster(t: datetime) -> tuple:
    heute = t.date()
    return heute - timedelta(days=LAUFEND_TAGE), heute


def hole(abfrage: str, ab, bis) -> tuple:
    """(http, text, fehler). Ein Netzfehler ist http=None - nie still."""
    q = urllib.parse.urlencode({"query": abfrage, "mode": "timelinetone", "format": "json",
                                "startdatetime": ab.strftime("%Y%m%d") + "000000", "enddatetime": bis.strftime("%Y%m%d") + "000000"})
    try:
        with urllib.request.urlopen(urllib.request.Request(URL + "?" + q, headers=H), timeout=60) as r:
            return r.status, r.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300], "HTTP %d" % e.code
    except Exception as e:  # noqa: BLE001
        return None, "", "%s: %s" % (type(e).__name__, str(e)[:200])


def punkte(text: str) -> list | None:
    if not text.startswith("{"):
        return None
    try:
        tl = json.loads(text).get("timeline") or [{"data": []}]
        return [[x["date"], float(x["value"])] for x in tl[0]["data"]]
    except (ValueError, KeyError, IndexError, TypeError):
        return None


_LETZTE = [None]          # monotone Zeit der letzten Abfrage - der Abstand gilt auch ÜBER Runden (eine lange Runde läuft in die nächste)


def runde(pfad: str, kennung: str, warte=time.sleep, uhr=time.monotonic) -> int:
    """Die vier Töne nacheinander, 600 s Abstand zwischen ZWEI BELIEBIGEN Abfragen; je Ton höchstens zwei Versuche.
    -> Zahl der Töne mit Werten."""
    ok = 0
    for ton, abfrage in GDELT.items():
        for versuch in (1, 2):
            if _LETZTE[0] is not None and versuch == 1:
                warte(max(0.0, GDELT_ABSTAND_S - (uhr() - _LETZTE[0])))
            _LETZTE[0] = uhr()
            t0 = jetzt()
            ab, bis = fenster(t0)
            http, text, fehler = hole(abfrage, ab, bis)
            p = punkte(text) if http == 200 else None
            if http == 200 and p is None:
                fehler = "keine JSON-Zeitreihe: %s" % text[:120].replace("\n", " ")
            schreibe(pfad, {"art": "abruf", "runde": kennung, "ts": iso(t0), "ton": ton, "versuch": versuch, "http": http,
                            "fehler": fehler, "dauer_s": round((jetzt() - t0).total_seconds(), 1),
                            "fenster": [ab.isoformat(), bis.isoformat()], "punkte": p})
            print("  %s  %-8s Versuch %d: %s" % (iso(t0)[11:19], ton, versuch,
                                                 "%d Punkte" % len(p) if p is not None else (fehler or "?")), flush=True)
            if p is not None:
                ok += 1
                break
            if versuch == 1:
                warte(ZWEITER_VERSUCH_S)
    schreibe(pfad, {"art": "runde_ende", "runde": kennung, "ts": iso(jetzt()), "toene_ok": ok})
    return ok


def eigene_pruefsumme() -> str:
    with open(os.path.abspath(__file__), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def stand(pfad: str) -> None:
    z = lies(pfad)
    st = next((x for x in z if x.get("art") == "start"), None)
    print("Datei %s" % pfad)
    if not st:
        print("  noch nichts geholt")
        return
    ab = [x for x in z if x.get("art") == "abruf"]
    runden = [x for x in z if x.get("art") == "runde_ende"]
    print("  Start %s · Ende %s · Runden %d · Abrufe %d (davon mit Werten %d) · Neustarts %d · kaputte Zeilen %d" % (
        st["ts"], st["ende"], len(runden), len(ab), sum(1 for x in ab if x.get("punkte") is not None),
        sum(1 for x in z if x.get("art") == "neustart"), sum(1 for x in z if x.get("art") == "kaputt")))
    for ton in GDELT:
        a = [x for x in ab if x["ton"] == ton]
        print("  %-8s Versuche %3d · mit Werten %3d · 429: %d" % (ton, len(a), sum(1 for x in a if x.get("punkte") is not None),
                                                                sum(1 for x in a if x.get("http") == 429)))


def main(a: list) -> int:
    pfad = ausgabe_pfad(a)
    if "--stand" in a:
        stand(pfad)
        return 0
    z = lies(pfad)
    st = next((x for x in z if x.get("art") == "start"), None)
    t = jetzt()
    if st is None:
        st = {"art": "start", "ts": iso(t), "ende": iso(t + timedelta(days=DAUER_TAGE)), "rechner": RECHNER,
              "python": sys.version.split()[0], "fassung": FASSUNG, "pruefsumme": eigene_pruefsumme()}
        schreibe(pfad, st)
    else:
        schreibe(pfad, {"art": "neustart", "ts": iso(t), "rechner": RECHNER, "pruefsumme": eigene_pruefsumme()})
    start, ende = datetime.fromisoformat(st["ts"]), datetime.fromisoformat(st["ende"])
    erledigt = {x["runde"] for x in z if x.get("art") == "runde_ende"}
    print("GDELT-Probe %s · Rechner %s · Datei %s\n  läuft bis %s UTC — Fenster offen lassen, Ctrl+C beendet (Neustart setzt fort)"
          % (FASSUNG, RECHNER, pfad, st["ende"][:16].replace("T", " ")), flush=True)
    while True:
        t = jetzt()
        if t >= ende:
            schreibe(pfad, {"art": "fertig", "ts": iso(t)})
            print("Fertig: 14 Tage vorbei. Die Datei liegt im Austauschordner, der Desktop wertet sie aus.", flush=True)
            return 0
        k = faellige_runde(t, erledigt, start)
        if k:
            print("Runde %s" % k, flush=True)
            runde(pfad, k)
            erledigt.add(k)
            if "--einmal" in a:
                return 0
            continue
        n = naechste_slotzeit(t)
        print("  nächste Runde %s UTC" % iso(n)[:16].replace("T", " "), flush=True)
        while jetzt() < min(n, ende):                # in Minutenschritten: Ctrl+C greift, Ruhezustand verschiebt nichts
            time.sleep(60)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print("\nangehalten — Neustart mit demselben Befehl setzt fort.")
        sys.exit(0)
