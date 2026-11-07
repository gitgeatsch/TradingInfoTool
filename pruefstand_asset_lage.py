"""Pruefstand G19 B2/B4 (E-171, 07.11.2026) - Fakt-Sammler ``agent/asset_lage.py`` und Job-Lauf, gegen NB-KOPIEN im Wegwerfpfad.

Voranalyse_G19_Dashboard_Bau_07_11.md §6 (Fassung 2, nach der Gegenpruefung):
- ⚠️ Am Desktop fehlen die Betriebsquellen. Ein Sammler, der "nie scheitert", bestuende jede Pruefung an leeren Karten -> hier
  laeuft alles auf der Pruefgrundlage ``Claude_Austauschordner/Pruefgrundlagen/asset_lage_2026-11-04`` (NB-Zustand 04./06.11.),
  und JE QUELLE muss mindestens ein echter Fakt (Zustand ``ok``) herauskommen.
- ⚠️ Seiteneffekt in DREI Armen, jeder mit eigener Gegenprobe: (1) Inhalt (SHA-256 jeder Datei), (2) Oeffnen (jede
  ``sqlite3.connect`` ohne ``mode=ro`` ausser der eigenen Ablage), (3) neue Dateien (Verzeichnisinhalt). Dazu: kein Zugriff
  ausserhalb des Wegwerfordners, kein Netz. Die Bedingungen stehen im HELFER (``Beobachter``), nicht in einer Textsuche.
- WAL: die Kopien der Pruefgrundlage sind Rollback-Journal-Dateien, die NB-Produktion ist WAL. Eine ``mode=ro``-Oeffnung kann
  Seitendateien (``-shm``/``-wal``) anlegen, wenn sie fehlen - deshalb wird jede Kopie VOR dem ersten Schnappschuss einmal ``mode=ro``
  geoeffnet. Der Fall "laufende WAL-Produktion mit offenem Schreiber" hat einen eigenen Pruefpunkt (Abschnitt 7, Fassung 2 nach der
  Code-Gegenpruefung 07.11.: Betriebsreihenfolge der Laeufe, getrennte Kurswege, Entfernen-Gegenprobe je Quelle, Sichten-Fall).

``pruefungen()`` liefert (Name, Bedingung, Detail) fuer ``pruefe_pakete.py --paket AssetLage``.
"""
from __future__ import annotations

import builtins
import hashlib
import os
import shutil
import socket
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta, timezone

import wegwerf  # noqa: F401  - legt tempfile unter D:\CLAUDE_Temp

GRUNDLAGE = "K:/My Drive/Claude_Austauschordner/Pruefgrundlagen/asset_lage_2026-11-04"
JETZT = datetime(2026, 11, 4, 16, 30, tzinfo=timezone.utc)
TERMINE = {"termine": [{"art": "fomc", "utc": "2026-11-05T19:00:00+00:00"}], "nicht_abgefragt": [], "geholt": "2026-11-04T06:45:00+00:00"}
PROJ = os.path.dirname(os.path.abspath(__file__))
_EIGEN = "asset_lage.db"


def _norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p))


def _unter(p: str, ordner: str) -> bool:
    a, b = _norm(p), _norm(ordner)
    return a == b or a.startswith(b.rstrip("\\/") + os.sep)


def _sha(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _eigen(name: str) -> bool:
    return name == _EIGEN or name.startswith(_EIGEN + "-")


class Beobachter:
    """Zeichnet waehrend des Blocks auf: Inhalt, Oeffnungen, neue Dateien, Zugriffe ausserhalb, Netz."""

    def __init__(self, ordner: str):
        self.ordner = ordner
        self.nicht_ro, self.aussen, self.netz = [], [], []

    def _stand(self) -> dict:
        aus = {}
        for w, _, fs in os.walk(self.ordner):
            for f in fs:
                p = os.path.join(w, f)
                aus[os.path.relpath(p, self.ordner)] = _sha(p)
        return aus

    def __enter__(self):
        self.vorher = self._stand()
        self._connect, self._open, self._sock, self._dns = sqlite3.connect, builtins.open, socket.socket.connect, socket.getaddrinfo
        b = self

        def connect(ziel, *a, **k):
            s = str(ziel)
            pfad = s[5:].split("?")[0] if s.startswith("file:") else s
            ro = "mode=ro" in s
            if pfad not in (":memory:", ""):
                if not _unter(pfad, b.ordner):
                    b.aussen.append(pfad)
                elif not ro and not _eigen(os.path.basename(pfad)):
                    b.nicht_ro.append(pfad)
            return b._connect(ziel, *a, **k)

        def oeffne(datei, *a, **k):
            if isinstance(datei, (str, os.PathLike)):
                p = os.fspath(datei)
                if _unter(p, os.path.join(PROJ, "data")) or (p.lower().endswith((".db", ".json", ".sqlite")) and not _unter(p, b.ordner)):
                    b.aussen.append(p)
            return b._open(datei, *a, **k)

        def sock(selbst, adresse, *a, **k):
            b.netz.append(str(adresse))
            raise OSError("Pruefstand: Netz gesperrt")

        def dns(host, *a, **k):
            b.netz.append("dns:%s" % host)
            raise OSError("Pruefstand: Netz gesperrt")

        sqlite3.connect, builtins.open, socket.socket.connect, socket.getaddrinfo = connect, oeffne, sock, dns
        return self

    def __exit__(self, *exc):
        sqlite3.connect, builtins.open, socket.socket.connect, socket.getaddrinfo = self._connect, self._open, self._sock, self._dns
        nachher = self._stand()
        self.geaendert = [n for n, h in self.vorher.items() if n in nachher and nachher[n] != h and not _eigen(os.path.basename(n))]
        self.neu = [n for n in nachher if n not in self.vorher and not _eigen(os.path.basename(n))]
        self.weg = [n for n in self.vorher if n not in nachher]
        return False

    def sauber(self) -> tuple[bool, str]:
        teile = [("Inhalt", self.geaendert), ("ohne mode=ro", self.nicht_ro), ("neu", self.neu), ("weg", self.weg),
                 ("ausserhalb", self.aussen), ("Netz", self.netz)]
        schmutz = ["%s: %s" % (n, ", ".join(map(str, x[:3]))) for n, x in teile if x]
        return not schmutz, " · ".join(schmutz) or "0 Schreibzugriffe, 0 neue Dateien, 0 Zugriffe ausserhalb, 0 Netz"


def _vorbereiten(ziel: str, voll_umlauf: bool = False) -> str:
    for f in ("tradinginfotool.db", "regel0_signale.db", "spot_betrieb.db", "makro_lage.json"):
        shutil.copy2(os.path.join(GRUNDLAGE, f), os.path.join(ziel, f))
    shutil.copy2(os.path.join(GRUNDLAGE, "umlaufmenge_cg_voll_desktop.db" if voll_umlauf else "umlaufmenge_cg.db"),
                 os.path.join(ziel, "umlaufmenge_cg.db"))
    for f in os.listdir(ziel):                                  # WAL-Seitendateien vorab (Modul-Docstring)
        if f.endswith(".db"):
            sqlite3.connect("file:%s?mode=ro" % os.path.join(ziel, f).replace("\\", "/"), uri=True).close()
    return ziel


def _neu(T: str, name: str) -> str:
    p = os.path.join(T, name)
    os.makedirs(p)
    return p


def _ok(erg, quelle) -> int:
    return (erg["zustaende"].get(quelle) or {}).get("ok", 0)


def pruefungen() -> list:
    from agent import asset_lage as AL

    R = []
    da = os.path.isdir(GRUNDLAGE)
    R.append(("Pruefgrundlage %s vorhanden (NB-Kopien, nicht in der Rotation)" % os.path.basename(GRUNDLAGE), da, GRUNDLAGE))
    if not da:
        return R
    T = tempfile.mkdtemp(prefix="g19_")
    try:
        A = _vorbereiten(_neu(T, "a"))
        # ── 1 Sammeln: nebenwirkungsfrei ───────────────────────────────────────────────────────────────────────────────
        with Beobachter(A) as b:
            erg = AL.sammle(A, JETZT, termine=TERMINE, mit_sichten=False)
        s, d = b.sauber()
        R.append(("⚠️⚠️ Sammler auf NB-Kopien: kein Schreiben, keine neue Datei, kein Zugriff ausserhalb, kein Netz", s, d))
        # ── 2 je Quelle ein echter Fakt ────────────────────────────────────────────────────────────────────────────────
        quellen = ("kurs", "kurs:signal", "bestand", "regel0_signal", "hebel", "ankuendigung", "season", "makro", "gesamtmarkt", "termine")
        leer = [q for q in quellen if not _ok(erg, q)]
        R.append(("⚠️⚠️ je Betriebsquelle mindestens ein echter Fakt (ok), EUR-Kurs und Signalkurs GETRENNT - %d Karten" % len(erg["karten"]),
                  not leer, "ohne ok: %s" % ", ".join(leer) if leer else " · ".join("%s %d" % (q, _ok(erg, q)) for q in quellen)))
        # Gegenprobe je Quelle: Datei entfernen -> ihre Angaben verlieren jedes 'ok' (sonst waere die Zeile oben blind)
        datei_quellen = {"tradinginfotool.db": ("kurs", "bestand", "hebel"), "regel0_signale.db": ("regel0_signal", "ankuendigung", "kurs:signal"),
                         "spot_betrieb.db": ("season",), "makro_lage.json": ("makro", "gesamtmarkt")}
        blind = []
        for datei, qs in datei_quellen.items():
            E = _vorbereiten(_neu(T, "e_" + datei.split(".")[0]))
            os.remove(os.path.join(E, datei))
            for rest in (datei + "-wal", datei + "-shm"):
                if os.path.exists(os.path.join(E, rest)):
                    os.remove(os.path.join(E, rest))
            ee = AL.sammle(E, JETZT, termine=TERMINE, mit_sichten=False)
            blind += ["%s (ohne %s)" % (q, datei) for q in qs if _ok(ee, q)]
            if datei == "tradinginfotool.db":
                nicht = (ee["zustaende"].get("bestand") or {}).get("nicht abgefragt", 0)
                if not nicht:
                    blind.append("bestand nicht 'nicht abgefragt'")
        R.append(("Gegenprobe je Quelle: ohne ihre Datei kein 'ok' mehr (Produktion, Signale, Spot-Ablage, Makro)", not blind, ", ".join(blind)))
        # Upbit: ein gepflanzter Fall (die Kopie hat keinen) - an einem L-Bestand (Krypto ohne Kern und Stablecoins)
        bs = [k for k in erg["karten"] if "bestand" in k["anlass"]]
        lb = [k for k in bs for f in k["fakten"] if f["schluessel"] == "upbit" and f["zustand"] == "leer"]
        c = sqlite3.connect(os.path.join(A, "spot_betrieb.db"))
        c.execute("INSERT INTO upbit_fall VALUES (?,?,?,?,?,?,?)", (999999, lb[0]["bitpanda"], lb[0]["bitpanda"], "2026-11-04 10:00", "faellig", 1.0, None))
        c.commit()
        c.close()
        e2 = AL.sammle(A, JETZT, termine=TERMINE, mit_sichten=False)
        kreis_falsch = [k["bitpanda"] for k in e2["karten"] for f in k["fakten"] if f["schluessel"] == "upbit" and f["zustand"] != "nicht abgefragt"
                        and (k["bitpanda"] in ("BTC", "ETH", "SOL", "EURCV") or "bestand" not in k["anlass"])]
        R.append(("Upbit: gepflanzter Fall = ok; Kern, Stablecoin und Nicht-Bestand = 'nicht abgefragt' (nicht im Prüfkreis)",
                  _ok(e2, "upbit") == 1 and not kreis_falsch, "upbit %s · falsch im Kreis %s" % (e2["zustaende"].get("upbit"), kreis_falsch[:5])))
        nk = [k["bitpanda"] for k in bs for f in k["fakten"] if f["schluessel"] == "ankuendigung" and f["zustand"] == "leer"
              and k["bitpanda"] in ("3QSS", "CEBS", "GOOGL", "OD7C")]
        R.append(("Ankündigungen: Nicht-Krypto (ETF, Aktie) = 'nicht abgefragt', nie 'leer'", not nk, str(nk)))
        # Verwaesserung: Desktop-Messbasis, Stichtag mit 90 T Historie
        V = _vorbereiten(_neu(T, "v"), voll_umlauf=True)
        e3 = AL.sammle(V, datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc), termine=TERMINE, mit_sichten=False)
        R.append(("Verwässerung: mit 90 T Mengenhistorie (Desktop-Messbasis, 20.09.) entstehen Fakten (ok)", _ok(e3, "verwaesserung") > 0,
                  "verwaesserung %s" % e3["zustaende"].get("verwaesserung")))
        # ── 3 Inhalt der Fakten ────────────────────────────────────────────────────────────────────────────────────────
        h = {r[0]: (r[1] or 0) + (r[2] or 0) for r in sqlite3.connect("file:%s?mode=ro" % os.path.join(A, "tradinginfotool.db").replace("\\", "/"),
                                                                        uri=True).execute("SELECT symbol, quantity, staked_quantity FROM holdings")}
        falsch = [k["bitpanda"] for k in bs for f in k["fakten"] if f["schluessel"] == "bestand" and f["zustand"] == "ok"
                  and abs(f["wert"]["menge"] - h.get(k["bitpanda"], -1)) > 1e-9]
        gestakt = sum(1 for k in bs for f in k["fakten"] if f["schluessel"] == "bestand" and f["zustand"] == "ok" and f["wert"]["gestakt"] > 0)
        R.append(("Bestand = frei + gestakt je Karte (wie holdings)", not falsch and gestakt > 0,
                  "abweichend %s · Karten mit Gestaktem %d" % (falsch[:5], gestakt)))
        hb = [f for k in erg["karten"] for f in k["fakten"] if f["schluessel"] == "hebel" and f["zustand"] == "ok"]
        stopp = [f["satz"] for f in hb if "stop" in (str(f["wert"]) + f["satz"]).lower() or "empfehl" in (str(f["wert"]) + f["satz"]).lower()]
        R.append(("Hebel: nur Liquidation/Abstand/Stufe/Haltedauer - kein Stop, keine Empfehlung der angehaltenen Kette", hb and not stopp,
                  "%d Hebel-Fakten, mit Stop/Empfehlung %d" % (len(hb), len(stopp))))
        realisiert = [f["satz"] for k in erg["karten"] for f in k["fakten"] if "realisiert" in f["satz"].lower()]
        R.append(("Ergebnis heisst nie 'realisiert'", not realisiert, "; ".join(realisiert[:2])))
        gemessen = [f["satz"][:80] for f in erg["markt"] + [y for k in erg["karten"] for y in k["fakten"]]
                    if any(w in f["satz"] for w in ("im Mittel", "geprüft an", "trennt ", "lag in", "Tendenz"))]
        R.append(("keine gemessenen Sätze unter dem Kennzeichen Fakt (Befunde kommen mit B3)", not gemessen, "; ".join(gemessen[:3])))
        vorg = sum(1 for f in erg["markt"] + [y for k in erg["karten"] for y in k["fakten"]] if (f["alter_h"] or 0) < -0.05)
        R.append(("(Auskunft) Angaben mit Stand NACH der Prüfzeit - nur auf der späteren Kopie möglich, im Betrieb nie", True,
                  "%d Angaben (Bitpanda-Abgleich 06.11., Makro 07.11. gegen Prüfzeit 04.11. 16:30)" % vorg))
        zuk = [s["signalstunde"] for k in erg["karten"] for s in k["signale"]
               if datetime.strptime(s["signalstunde"], AL.FMT).replace(tzinfo=timezone.utc) + timedelta(hours=1) > JETZT]
        R.append(("kein Signal, dessen Stunde nach der Kartenzeit schliesst (kein Vorgriff auf der späteren Kopie)", not zuk, ", ".join(zuk[:3])))
        # ── 4 drei Zustaende / anderes Geraet ──────────────────────────────────────────────────────────────────────────
        L = os.path.join(T, "leer")
        os.makedirs(L)
        with Beobachter(L) as b:
            e0 = AL.sammle(L, JETZT, mit_sichten=True)
        s, d = b.sauber()
        alle_nicht = all(set(z) == {"nicht abgefragt"} for q, z in e0["zustaende"].items())
        R.append(("ohne jede Betriebsquelle: alle Angaben 'nicht abgefragt' (sichtbar), keine Datei angelegt", s and alle_nicht and not os.listdir(L),
                  "%s · %s" % (e0["zustaende"], d)))
        tf = AL.termin_fakt
        z3 = (tf(None, JETZT)["zustand"], tf({"termine": [], "nicht_abgefragt": []}, JETZT)["zustand"],
              tf({"termine": [], "nicht_abgefragt": ["cpi", "nfp", "fomc"]}, JETZT)["zustand"])
        R.append(("Termine: drei Zustände getrennt (nicht übergeben / kein Termin / nicht abgefragt)",
                  z3 == ("nicht abgefragt", "leer", "nicht abgefragt"), str(z3)))
        # ── 5 Job-Lauf: nur die eigene Ablage, jedes Signal genau eine Karte ───────────────────────────────────────────
        J = _vorbereiten(_neu(T, "j"))
        t0 = datetime(2026, 11, 4, 0, 35, tzinfo=timezone.utc)
        n_laeufe = 0
        with Beobachter(J) as b:                                 # BETRIEBSREIHENFOLGE: Stundenlaeufe 00:35-06:35, Tag 06:45, Stunden 07:35-16:35
            for st in range(0, 17):
                if st == 6:
                    AL.lauf(J, "signal", t0 + timedelta(hours=6))
                    AL.lauf(J, "tag", datetime(2026, 11, 4, 6, 45, tzinfo=timezone.utc), termine=TERMINE)
                    n_laeufe += 2
                    continue
                AL.lauf(J, "signal", t0 + timedelta(hours=st))
                n_laeufe += 1
        s, d = b.sauber()
        R.append(("⚠️⚠️ Job-Lauf in Betriebsreihenfolge (Stunden vor und nach dem Tageslauf): schreibt NUR asset_lage.db",
                  s and os.path.exists(os.path.join(J, _EIGEN)), d))
        ca = sqlite3.connect("file:%s?mode=ro" % os.path.join(J, _EIGEN).replace("\\", "/"), uri=True)
        doppelt = ca.execute("SELECT COUNT(*) FROM (SELECT symbol, signalstunde FROM karte WHERE signalstunde IS NOT NULL "
                             "GROUP BY 1, 2 HAVING COUNT(*) > 1)").fetchone()[0]
        mit = {tuple(r) for r in ca.execute("SELECT symbol, signalstunde FROM karte WHERE signalstunde IS NOT NULL")}
        ca.close()
        ende = datetime(2026, 11, 4, 16, 35, tzinfo=timezone.utc)
        cs = sqlite3.connect("file:%s?mode=ro" % os.path.join(J, "regel0_signale.db").replace("\\", "/"), uri=True)
        soll = set()
        for tg in ("2026-11-03", "2026-11-04"):
            soll |= {(s["symbol"], s["signalstunde"]) for s in AL.signale_am(cs, tg, bis=ende)}
        cs.close()
        R.append(("jedes Signal (03./04.11. bis 16:35) hat genau EINE Karte", not doppelt and soll == mit,
                  "Soll %d · Karten %d · doppelt %d · fehlend %d" % (len(soll), len(mit), doppelt, len(soll - mit))))
        ca = sqlite3.connect("file:%s?mode=ro" % os.path.join(J, _EIGEN).replace("\\", "/"), uri=True)
        tagkarten = {r[0] for r in ca.execute("SELECT k.bitpanda FROM karte k JOIN lauf l ON l.id = k.lauf WHERE l.art='tag'")}
        fremd = ca.execute("SELECT COUNT(*) FROM fakt f JOIN karte k ON k.id = f.karte WHERE f.schluessel='regel0_signal' "
                           "AND (k.signalstunde IS NULL OR json_extract(f.wert, '$.signalstunde') != k.signalstunde)").fetchone()[0]
        ca.close()
        ohne = [k["bitpanda"] for k in bs if k["bitpanda"] not in tagkarten]
        R.append(("Tageslauf nach Stundenläufen: jeder Bestand hat eine Tageskarte, kein Signal steht auf einer fremden Karte",
                  not ohne and not fremd, "Bestände ohne Tageskarte %s · fremde Signalangaben %d" % (ohne[:5], fremd)))
        st = AL.stand(J, ende)
        R.append(("Diagnose stand(): JEDER Lauf protokolliert (auch 0 Karten), Verzug der Signalkarten ausgewiesen",
                  st.get("laeufe") == n_laeufe and "tag" in st and "signal" in st and "signalkarte_verzug_min" in st,
                  "Läufe %s von %d · %s" % (st.get("laeufe"), n_laeufe, {k: st.get(k) for k in ("karten_gesamt", "signalkarten_nachgeholt",
                                                                                                 "signalkarte_verzug_min")})))
        # ein Fehler im Lauf: protokolliert (lauf.fehler), kein Abbruch, als Fehler im Ergebnis
        F = _vorbereiten(_neu(T, "f"))
        alt_s = AL.sammle
        AL.sammle = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("gepflanzt"))
        try:
            rf = AL.lauf(F, "tag", JETZT, termine=TERMINE)
        finally:
            AL.sammle = alt_s
        sf = AL.stand(F, JETZT)
        R.append(("Fehler im Lauf: steht in lauf.fehler und im Ergebnis, die Diagnose zählt ihn", "gepflanzt" in (rf.get("fehler") or "")
                  and sf.get("fehler_24h") == 1 and "gepflanzt" in (sf.get("tag", {}).get("fehler") or ""), "%s · fehler_24h %s" % (rf.get("fehler"), sf.get("fehler_24h"))))
        # Sperre: Signale nicht lesbar -> nichts als erledigt vermerkt, der naechste Lauf holt nach
        K = _vorbereiten(_neu(T, "k"))
        sperre = sqlite3.connect(os.path.join(K, "regel0_signale.db"), timeout=1)
        sperre.execute("BEGIN EXCLUSIVE")
        r1 = AL.lauf(K, "signal", datetime(2026, 11, 4, 12, 35, tzinfo=timezone.utc))
        sperre.rollback()
        sperre.close()
        r2 = AL.lauf(K, "signal", datetime(2026, 11, 4, 12, 36, tzinfo=timezone.utc))
        R.append(("Sperre auf den Signalen: Lauf vermerkt nichts, der nächste holt nach", r1.get("karten") == 0 and "nicht lesbar" in r1.get("grund", "")
                  and r2.get("karten", 0) > 0, "gesperrt: %s · danach: %s Karten" % (r1.get("grund"), r2.get("karten"))))
        # Job-Huelle: Schalter aus / falsches Geraet -> laeuft nicht
        import scheduler.background as BG
        import agent.regel0_groesse as G
        alt = G.asset_lage_aktiv
        try:
            G.asset_lage_aktiv = lambda werte=None: False         # ausdruecklich - die echte yaml kann spaeter 'true' tragen
            j1 = BG.asset_lage_job("tag", ordner=K)
            G.asset_lage_aktiv = lambda werte=None: True
            j2 = BG.asset_lage_job("tag", ordner=K)
        finally:
            G.asset_lage_aktiv = alt
        R.append(("Job: Schalter aus -> läuft nicht; Schalter an, aber kein Betriebsgerät -> läuft nicht", not j1["gelaufen"] and not j2["gelaufen"]
                  and "terminmarkt" in (j2.get("grund") or ""), "%s | %s" % (j1.get("grund"), j2.get("grund"))))
        # ── 6 Gegenproben: jeder Arm des Beobachters schlaegt an ──────────────────────────────────────────────────────
        G0 = _vorbereiten(_neu(T, "g"))
        with open(os.path.join(G0, "gegenprobe.bin"), "wb") as f:
            f.write(b"0" * 64)
        from agent import regel0_ablage as RA
        gp = {}
        with Beobachter(G0) as b:                                # Arm 1: Inhalt
            with open(os.path.join(G0, "gegenprobe.bin"), "r+b") as f:
                f.write(b"1")
        gp["Inhalt"] = bool(b.geaendert)
        with Beobachter(G0) as b:                                # Arm 2: Oeffnen ohne mode=ro (CREATE IF NOT EXISTS laesst den Inhalt gleich)
            RA.oeffne(G0).close()
        gp["ohne mode=ro"] = bool(b.nicht_ro)
        with Beobachter(G0) as b:                                # Arm 3: neue Datei
            with open(os.path.join(G0, "neu.db"), "w") as f:
                f.write("x")
        gp["neue Datei"] = bool(b.neu)
        with Beobachter(G0) as b:                                # ausserhalb: Leser mit festem Pfad
            from agent import makro_lage as ML
            ML.lade()
        gp["ausserhalb"] = bool(b.aussen)
        from database import db as _DB                          # Netz: der FRED-Weg direkt. ⚠️ track_api_health schreibt den Fehlschlag
        alt_pfad = _DB.DB_PATH                                    # in die Standard-DB -> DB_PATH auf eine Wegwerfdatei (CLAUDE.md, Paket StandardDB)
        _DB.DB_PATH = __import__("pathlib").Path(os.path.join(T, "gesundheit.db"))
        try:
            with Beobachter(G0) as b:
                from agent import termin_fakt as TFM
                TFM._SPEICHER.clear()
                TFM.termine(JETZT, JETZT + timedelta(days=7), "x" * 32)
        finally:
            _DB.DB_PATH = alt_pfad
        gp["Netz"] = bool(b.netz)
        R.append(("Gegenproben: jeder Arm schlägt an (Inhalt, ohne mode=ro, neue Datei, ausserhalb, Netz)", all(gp.values()),
                  " · ".join("%s %s" % (k, "rot" if v else "BLIND") for k, v in gp.items())))
        # FRED-Fehlschlag des Jobs bleibt NICHT im Tagesspeicher von termin_fakt (den nutzt auch die REGEL0-Mail)
        alt_pfad = _DB.DB_PATH
        _DB.DB_PATH = __import__("pathlib").Path(os.path.join(T, "gesundheit.db"))
        try:
            with Beobachter(G0):
                TFM._SPEICHER.clear()
                AL.termine_holen(JETZT, "x" * 32)
            rest = [k for k, v in TFM._SPEICHER.items() if not v[1]]
        finally:
            _DB.DB_PATH = alt_pfad
        R.append(("FRED-Fehlschlag des Jobs bleibt nicht im Tagesspeicher (REGEL0-Mail fragt selbst neu)", not rest, str(rest)))
        # ── 7 Sichten-Fall (Desktop-sichten.db) und laufende WAL-Produktion ───────────────────────────────────────────
        quelle_s = os.path.join(PROJ, "data", "_sichten", "sichten.db")
        if os.path.isfile(quelle_s):
            S = _vorbereiten(_neu(T, "s"))
            os.makedirs(os.path.join(S, "_sichten"))
            shutil.copy2(quelle_s, os.path.join(S, "_sichten", "sichten.db"))
            es = AL.sammle(S, datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc), termine=TERMINE, mit_sichten=True)
            sz = [f for f in es["markt"] if f["schluessel"].startswith("sicht:")]
            doppelt_s = [f["satz"][:30] for f in sz if f["satz"].lstrip("● ").count("[S") > 1]
            R.append(("Sicht-Zustände (Desktop-sichten.db, 15.10.): gelesen, Satz ohne doppelte Sichtmarke", len(sz) > 20 and not doppelt_s,
                      "%d Zustände · ok %d · doppelt %s" % (len(sz), sum(f["zustand"] == "ok" for f in sz), doppelt_s[:2])))
        W = _vorbereiten(_neu(T, "w"))
        pw = os.path.join(W, "tradinginfotool.db")
        cw = sqlite3.connect(pw)
        cw.execute("PRAGMA journal_mode=WAL")
        cw.close()
        import subprocess
        import sys as _sys
        schreiber = subprocess.Popen([_sys.executable, "-c", "import sqlite3,time;c=sqlite3.connect(r'%s');c.execute('BEGIN IMMEDIATE');"
                                      "c.execute(\"INSERT INTO meta VALUES ('g19_schreiber','1')\");time.sleep(4);c.commit();print('ok')" % pw],
                                     stdout=subprocess.PIPE, text=True)
        time.sleep(1.0)
        tw = time.time()
        ew = AL.sammle(W, JETZT, termine=TERMINE, mit_sichten=False)
        dauer = time.time() - tw
        aus_s = schreiber.communicate(timeout=30)[0].strip()
        R.append(("laufende WAL-Produktion: Lesen mit mode=ro neben einem offenen Schreiber - Bestand gelesen, Schreiber nicht blockiert",
                  _ok(ew, "bestand") > 0 and aus_s == "ok" and dauer < 3.5, "bestand ok %d · Schreiber %r · Lesedauer %.1f s"
                  % (_ok(ew, "bestand"), aus_s, dauer)))
    finally:
        wegwerf.aufraeumen(T)
    return R


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for n, ok, d in pruefungen():
        print("  %s  %s\n        %s" % ("OK  " if ok else "FEHL", n, d))
