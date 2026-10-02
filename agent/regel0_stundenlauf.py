"""REGEL0.1-Stundenlauf im Betrieb (Schritt 7, S7-2b, 02.10.2026; Voranalyse_Schritt7_Betrieb_02_10.md Abschnitt 14).

Laeuft als EIGENER PROZESS, gestartet vom Stundenjob ``regel0_nachlader`` nach dem Nachladen (Speicher und Absturz bleiben
ausserhalb der App):

    1  fehlende Monatspakete trainieren (Monatsjob S7-3, nur aus den Daten zum Monatsbeginn) - data/regel0_modelle/
    2  bewerten (agent.regel0_rechnung.bewerte): Signale der juengsten abgeschlossenen Stunde, Frische je Asset
    3  ablegen in data/regel0_signale.db: neue Signale mit VORLAEUFIGER Stufe, eine Stunde spaeter die ENDGUELTIGE (B-9);
       dazu der Hebel-Schalter des Assets (aus der Produktion NUR GELESEN) und je Lauf die Frische

⚠️ SCHREIBT NUR in regel0_signale.db und die Modelldateien. Nichts geht an die Mail oder in die Produktion - das ist S7-4.
Der Rechenkern selbst (agent/regel0_rechnung.py) bleibt rein lesend.

    python -m agent.regel0_stundenlauf --betrieb                                  # ein Lauf zur aktuellen Stunde (NB)
    python -m agent.regel0_stundenlauf --betrieb --jetzt <h> --ablage <dir> --modelle <dir>   # Probe auf Wegwerfordnern
"""
from __future__ import annotations

import csv
import os
import sqlite3
import sys
from datetime import datetime, timezone

import numpy as np

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HIER not in sys.path:
    sys.path.insert(0, HIER)

from agent.regel0_rechnung import (DATEN_VORGABE, REGELVERSION, _ro, _stunde_txt, betriebs_zusatz, bewerte,   # noqa: E402
                                   lade_paket, monat_von, speichere_paket, trainiere_monat)


# ══ S7-2b═════════════════════════════════
ABLAGE_NAME = "regel0_signale.db"
MODELL_ORDNER = "regel0_modelle"
VERALTET_MELDEN_AB = 0.10          # Anteil veralteter aktiver Assets, ab dem der Lauf eine Meldung verlangt


def _monat_txt(h: int) -> str:
    m_ = int(monat_von(np.array([h]))[0])
    return "%04d-%02d" % (m_ // 12, m_ % 12 + 1)


def benoetigte_pakete(jetzt: int) -> list:
    """Die Monatspakete, die ein Lauf zur Stunde ``jetzt`` braucht: rsi aus den Monaten der Signalstunden (jetzt-2, jetzt-1),
    ATR aus den Monaten der Einstiegsstunden (jetzt-1, jetzt). An der Monatsgrenze sind das zwei."""
    return sorted({_monat_txt(h) for h in (jetzt - 2, jetzt - 1, jetzt)})


def _ablage(ordner_ablage: str):
    """Verbindung zur Signalablage - SCHREIBT NUR in ``regel0_signale.db`` (nie in die Produktion)."""
    p = os.path.join(ordner_ablage, ABLAGE_NAME)
    if os.path.basename(p) != ABLAGE_NAME or os.path.basename(p).lower() == "tradinginfotool.db":
        raise SystemExit("⛔ verweigert: %s" % p)
    c = sqlite3.connect(p, timeout=30)
    c.execute("CREATE TABLE IF NOT EXISTS lauf (jetzt TEXT PRIMARY KEY, gerechnet_am TEXT, sekunden REAL, pakete TEXT, aktiv INTEGER, "
              "frisch INTEGER, veraltet INTEGER, veraltet_liste TEXT, nicht_im_handel INTEGER, neu INTEGER, endgueltig INTEGER, meldung TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS signal (symbol TEXT, signalstunde TEXT, einstieg TEXT, ausstieg TEXT, vh REAL, "
              "stufe_vorlaeufig INTEGER, stufe INTEGER, p2 REAL, p3 REAL, p5 REAL, hebel_schalter INTEGER, bitpanda TEXT, "
              "zusatz INTEGER, btc INTEGER, version TEXT, erfasst_am TEXT, endgueltig_am TEXT, PRIMARY KEY (symbol, signalstunde))")
    return c


def _hebel_schalter(ordner: str) -> dict:
    """{Bitpanda-Symbol: an?} aus der Produktion - NUR LESEN (mode=ro). Fehlt die Datei oder Tabelle: leer (dann *unbekannt*)."""
    p = os.path.join(ordner, "tradinginfotool.db")
    if not os.path.exists(p):
        return {}
    try:
        c = _ro(p)
        try:
            return {str(r[0]).upper(): bool(r[1]) for r in c.execute("SELECT symbol, hebel_pruefung_erlaubt FROM asset_hebel_settings")}
        finally:
            c.close()
    except sqlite3.Error:
        return {}


def _binance_zu_bitpanda() -> dict:
    pz = os.path.join(HIER, "Basisinfos", "symbol_zuordnung.csv")
    aus = {}
    if os.path.exists(pz):
        with open(pz, encoding="utf-8") as f_:
            for r in csv.DictReader(f_, delimiter=";"):
                if r.get("markt") != "gesperrt":
                    aus[r["binance"]] = r["bitpanda"]
    return aus


def betrieb_lauf(ordner: str, jetzt: int | None = None, ordner_ablage: str | None = None, ordner_modelle: str | None = None,
                 ausgabe=print) -> dict:
    """Ein Stundenlauf im Betrieb: fehlende Monatspakete trainieren (Monatsjob), bewerten, Signale und Lauf ablegen.

    Neue Signale kommen mit der VORLAEUFIGEN Stufe in die Ablage, eine Stunde spaeter bekommen sie die ENDGUELTIGE (B-9).
    Nichts geht an die Mail oder in die Produktion - das ist S7-4."""
    import json
    import time
    t0 = time.time()
    ordner_ablage = ordner_ablage or ordner
    ordner_modelle = ordner_modelle or os.path.join(ordner, MODELL_ORDNER)
    os.makedirs(ordner_modelle, exist_ok=True)
    if jetzt is None:
        jetzt = int((datetime.now(timezone.utc).replace(tzinfo=None) - datetime(2020, 1, 1)).total_seconds() // 3600)
    zus = betriebs_zusatz(ordner)
    pakete, neu_trainiert = {}, []
    for mt in benoetigte_pakete(jetzt):
        pf = os.path.join(ordner_modelle, "regel0_modell_%s.pkl" % mt)
        if not os.path.exists(pf):
            t1 = time.time()
            j_, m_ = int(mt[:4]), int(mt[5:])
            RK_pk = trainiere_monat(ordner, j_, m_, zusatz=zus)
            sha = speichere_paket(RK_pk, pf)
            neu_trainiert.append(mt)
            ausgabe("REGEL0-Rechnung: Monatspaket %s trainiert in %.0f s (%d Assets, Pruefsumme %s)" % (mt, time.time() - t1, RK_pk["assets"], sha[:12]))
        pakete[mt] = lade_paket(pf)
    B = bewerte(ordner, pakete, jetzt, zusatz=zus)
    fr = B["frische"]
    schalter = _hebel_schalter(ordner)
    zu_bp = _binance_zu_bitpanda()
    meldung = ""
    if fr["aktiv"] and len(fr["veraltet"]) / fr["aktiv"] > VERALTET_MELDEN_AB:
        meldung = "%d von %d aktiven Assets ohne die Stunde %s - Datenbasis veraltet (Nachlader?)" % (
            len(fr["veraltet"]), fr["aktiv"], _stunde_txt(jetzt - 1))
    c = _ablage(ordner_ablage)
    try:
        jetzt_txt = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")
        for x in B["neu"]:
            bp = zu_bp.get(x["symbol"], x["symbol"])
            sch = schalter.get(bp.upper())
            c.execute("INSERT OR IGNORE INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, stufe_vorlaeufig, p2, p3, p5, hebel_schalter, "
                      "bitpanda, zusatz, btc, version, erfasst_am) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (x["symbol"], x["signalstunde"], x["einstieg"], x["ausstieg"], x["vh"], x["stufe"], x["p2"], x["p3"], x["p5"],
                       None if sch is None else int(sch), bp, int(x["zusatz"]), int(x["btc"]), REGELVERSION, jetzt_txt))
        for x in B["endgueltig"]:
            bp = zu_bp.get(x["symbol"], x["symbol"])
            sch = schalter.get(bp.upper())
            c.execute("INSERT OR IGNORE INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, hebel_schalter, bitpanda, zusatz, btc, version, "
                      "erfasst_am) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                      (x["symbol"], x["signalstunde"], x["einstieg"], x["ausstieg"], x["vh"], None if sch is None else int(sch), bp,
                       int(x["zusatz"]), int(x["btc"]), REGELVERSION, jetzt_txt))
            c.execute("UPDATE signal SET stufe=?, p2=?, p3=?, p5=?, endgueltig_am=? WHERE symbol=? AND signalstunde=?",
                      (x["stufe"], x["p2"], x["p3"], x["p5"], jetzt_txt, x["symbol"], x["signalstunde"]))
        c.execute("INSERT OR REPLACE INTO lauf VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (_stunde_txt(jetzt), jetzt_txt, round(time.time() - t0, 1), ",".join(sorted(pakete)), fr["aktiv"], fr["frisch"],
                   len(fr["veraltet"]), ",".join(fr["veraltet"][:50]), fr["nicht_im_handel"], len(B["neu"]), len(B["endgueltig"]), meldung))
        c.commit()
    finally:
        c.close()
    zus_ = dict(jetzt=_stunde_txt(jetzt), sekunden=round(time.time() - t0, 1), neu=len(B["neu"]), endgueltig=len(B["endgueltig"]),
                neu_schalter_an=sum(1 for x in B["neu"] if schalter.get(zu_bp.get(x["symbol"], x["symbol"]).upper())),
                aktiv=fr["aktiv"], frisch=fr["frisch"], veraltet=len(fr["veraltet"]), trainiert=neu_trainiert, meldung=meldung)
    ausgabe("REGEL0-ERGEBNIS " + json.dumps(zus_, ensure_ascii=False))
    return zus_


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    a = sys.argv
    if "--betrieb" not in a:
        print(__doc__)
        return 2
    ordner = a[a.index("--ordner") + 1] if "--ordner" in a else DATEN_VORGABE
    jetzt = int(a[a.index("--jetzt") + 1]) if "--jetzt" in a else None
    abl = a[a.index("--ablage") + 1] if "--ablage" in a else None
    mod = a[a.index("--modelle") + 1] if "--modelle" in a else None
    # ⚠️⚠️ NUR AM BETRIEBSGERAET in den Datenordner schreiben (02.10.: eine Pruefung der Suite hatte am Desktop einen echten
    # Lauf ausgeloest - Ablage und Modellpaket landeten in data/). Dieselbe Sperre wie der Nachlader (Datenzustand, kein
    # Geraetename). Eine Probe gibt Ablage UND Modelle ausdruecklich als Wegwerfordner an.
    if abl is None or mod is None:
        import agent.regel0_nachlader as _NL
        ok, grund = _NL.betrieb_erlaubt(ordner)
        if not ok:
            print("REGEL0-Rechnung: verweigert - %s (Probe: --ablage und --modelle angeben)" % grund)
            return 3
    betrieb_lauf(ordner, jetzt, abl, mod)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
