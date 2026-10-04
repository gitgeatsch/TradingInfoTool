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

import agent.regel0_ablage as _AB                                  # noqa: E402
from agent.regel0_rechnung import (DATEN_VORGABE, REGELVERSION, _ro, _stunde_txt, betriebs_zusatz, bewerte,   # noqa: E402
                                   lade_paket, monat_von, speichere_paket, trainiere_monat)


# ══ S7-2b═════════════════════════════════
ABLAGE_NAME = _AB.ABLAGE_NAME
MODELL_ORDNER = "regel0_modelle"
NACHHOLEN_H = 3                    # N-1 (E-57): verpasste Signalstunden bis so weit zurueck nachrechnen (Nutzer 04.10.: *bis 3 h*)


def verpasste_stunden(ablage_pfad: str, jetzt: int) -> list:
    """N-1: Signalstunden zwischen jetzt-2-NACHHOLEN_H und jetzt-3, die KEIN frueherer Lauf abgelegt hat. Ein Lauf zur Stunde t legt
    t-1 (neu) und t-2 (endgueltig) ab. Ohne jeden Lauf in den letzten 24 h wird nichts nachgeholt (Erststart, kein Ausfall)."""
    import sqlite3 as _sq
    if not os.path.exists(ablage_pfad):
        return []
    c = _sq.connect("file:%s?mode=ro" % ablage_pfad.replace("\\", "/"), uri=True)
    try:
        lt = {int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - datetime(2020, 1, 1)).total_seconds() // 3600)
              for r in c.execute("SELECT jetzt FROM lauf WHERE jetzt >= ?", (_stunde_txt(jetzt - 24),))}
        schon = {r[0] for r in c.execute("SELECT signalstunde FROM nachgeholt")} if c.execute(
            "SELECT 1 FROM sqlite_master WHERE name='nachgeholt'").fetchone() else set()
        # Zeilen OHNE endgueltige Stufe (der Lauf sh+2 fiel aus): R-R11 am 04.10. (19.08./24.08.) - die Stunde VOR einem Ausfall
        # hatte nur die vorlaeufige Stufe, das Nachholen sah sie nicht, weil sie schon eine Zeile hatte
        ohne_stufe = {int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - datetime(2020, 1, 1)).total_seconds() // 3600)
                      for r in c.execute("SELECT DISTINCT signalstunde FROM signal WHERE stufe IS NULL AND signalstunde >= ? AND signalstunde <= ?",
                                         (_stunde_txt(jetzt - 24), _stunde_txt(jetzt - 3)))}
    finally:
        c.close()
    if not lt:
        return []
    gedeckt = {t - 1 for t in lt} | {t - 2 for t in lt}
    fehlend = {sh for sh in range(jetzt - 2 - NACHHOLEN_H, jetzt - 2) if sh not in gedeckt and _stunde_txt(sh) not in schon}
    # die endgueltige Stufe ergaenzen, wo der Lauf sh+2 fehlte (der Lauf sh+1 legte nur die vorlaeufige ab) - bis 24 h zurueck
    ohne_endg = {sh for sh in ohne_stufe if (sh + 2) not in lt}
    return sorted(fehlend | ohne_endg)
VERALTET_MELDEN_AB = 0.10          # Anteil veralteter aktiver Assets, ab dem der Lauf eine Meldung verlangt


def _monat_txt(h: int) -> str:
    m_ = int(monat_von(np.array([h]))[0])
    return "%04d-%02d" % (m_ // 12, m_ % 12 + 1)


def benoetigte_pakete(jetzt: int) -> list:
    """Die Monatspakete, die ein Lauf zur Stunde ``jetzt`` braucht: rsi aus den Monaten der Signalstunden (jetzt-2, jetzt-1),
    ATR aus den Monaten der Einstiegsstunden (jetzt-1, jetzt). An der Monatsgrenze sind das zwei."""
    return sorted({_monat_txt(h) for h in (jetzt - 2, jetzt - 1, jetzt)})


def _ablage(ordner_ablage: str):
    """Verbindung zur Signalablage - ueber die EINE Stelle (agent/regel0_ablage.py), schreibt nur ``regel0_signale.db``."""
    return _AB.oeffne(ordner_ablage)


def _kurs_markt(ordner: str) -> dict:
    """{Symbol: 'spot'|'futures'} der Zusatz-Assets (stundenkurse_alle.db, Tabelle _quelle) - fuer den Vermerk *Kurs aus Futures*."""
    p = os.path.join(ordner, "stundenkurse_alle.db")
    if not os.path.exists(p):
        return {}
    c = _ro(p)
    try:
        return {r[0]: r[1] for r in c.execute("SELECT symbol, markt FROM _quelle")}
    except sqlite3.Error:
        return {}
    finally:
        c.close()


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


def _binance_zu_bitpanda() -> tuple:
    """-> ({Binance-Symbol: Bitpanda-Symbol oder None}, {Binance-Symbol: Faktor}) aus Basisinfos/symbol_zuordnung.csv.

    ⚠️ S7-5c (N-2, 03.10.2026): ein GESPERRTES Kuerzel (Bitpanda fuehrt darunter einen ANDEREN Coin) bekommt KEINEN Bitpanda-Namen -
    fuer JEDE Menge, auch die Messbasis (ZK liegt dort; Kurs Binance gegen Bitpanda +101,6 %). Ohne Namen kein Schalter, keine Mail.
    Faktor: Kurs des Binance-Paars je Bitpanda-Stueck (CAT -> 1000CAT: 1000)."""
    pz = os.path.join(HIER, "Basisinfos", "symbol_zuordnung.csv")
    aus, fak = {}, {}
    if os.path.exists(pz):
        with open(pz, encoding="utf-8") as f_:
            for r in csv.DictReader(f_, delimiter=";"):
                if r.get("markt") == "gesperrt":
                    aus[r["binance"]] = None
                    aus.setdefault(r["bitpanda"], None)
                else:
                    aus[r["binance"]] = r["bitpanda"]
                    try:
                        fak[r["binance"]] = float(r.get("faktor") or 1)
                    except ValueError:
                        fak[r["binance"]] = 1.0
    return aus, fak


def _kurs_paar(ordner: str) -> dict:
    """{Symbol: Binance-Paar} der Zusatz-Assets (stundenkurse_alle.db, _quelle); die Messbasis handelt <SYMBOL>USDT am Spot."""
    p = os.path.join(ordner, "stundenkurse_alle.db")
    if not os.path.exists(p):
        return {}
    c = _ro(p)
    try:
        return {r[0]: r[1] for r in c.execute("SELECT symbol, paar FROM _quelle")}
    except sqlite3.Error:
        return {}
    finally:
        c.close()


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
    nachholen = verpasste_stunden(os.path.join(ordner_ablage, _AB.ABLAGE_NAME), jetzt)
    for sh in nachholen:                       # die Modellpakete der verpassten Stunden (Monatsgrenze) - nur laden, nie trainieren
        for mt in benoetigte_pakete(sh + 1):
            pf = os.path.join(ordner_modelle, "regel0_modell_%s.pkl" % mt)
            if mt not in pakete and os.path.exists(pf):
                pakete[mt] = lade_paket(pf)
    B = bewerte(ordner, pakete, jetzt, zusatz=zus, nachholen=tuple(nachholen))
    fr = B["frische"]
    schalter = _hebel_schalter(ordner)
    zu_bp, fak = _binance_zu_bitpanda()
    markt = _kurs_markt(ordner)
    paare = _kurs_paar(ordner)
    meldung = ""
    if fr["aktiv"] and len(fr["veraltet"]) / fr["aktiv"] > VERALTET_MELDEN_AB:
        meldung = "%d von %d aktiven Assets ohne die Stunde %s - Datenbasis veraltet (Nachlader?)" % (
            len(fr["veraltet"]), fr["aktiv"], _stunde_txt(jetzt - 1))
    c = _ablage(ordner_ablage)
    try:
        jetzt_txt = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")
        for x in B["neu"]:
            bp = zu_bp.get(x["symbol"], x["symbol"])
            sch = schalter.get(bp.upper()) if bp else None
            c.execute("INSERT OR IGNORE INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, stufe_vorlaeufig, p2, p3, p5, hebel_schalter, "
                      "bitpanda, zusatz, btc, version, erfasst_am, kurs, kurs_markt, paar, faktor) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (x["symbol"], x["signalstunde"], x["einstieg"], x["ausstieg"], x["vh"], x["stufe"], x["p2"], x["p3"], x["p5"],
                       None if sch is None else int(sch), bp, int(x["zusatz"]), int(x["btc"]), REGELVERSION, jetzt_txt,
                       x.get("kurs"), markt.get(x["symbol"], "spot"), paare.get(x["symbol"], x["symbol"] + "USDT"), fak.get(x["symbol"], 1.0)))
        # endgueltig (jetzt-2) und nachgeholt (N-1): fehlt die Zeile, wird sie VOLLSTAENDIG angelegt (mit Kurs, Markt, Paar, Faktor -
        # bis 04.10. fehlten diese bei der aufgefangenen Stunde, die Mail konnte dann den Preis nicht gegenpruefen)
        for x in B["endgueltig"] + B.get("nachgeholt", []):
            bp = zu_bp.get(x["symbol"], x["symbol"])
            sch = schalter.get(bp.upper()) if bp else None
            c.execute("INSERT OR IGNORE INTO signal (symbol, signalstunde, einstieg, ausstieg, vh, stufe_vorlaeufig, hebel_schalter, bitpanda, "
                      "zusatz, btc, version, erfasst_am, kurs, kurs_markt, paar, faktor) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (x["symbol"], x["signalstunde"], x["einstieg"], x["ausstieg"], x["vh"], x["stufe"], None if sch is None else int(sch),
                       bp, int(x["zusatz"]), int(x["btc"]), REGELVERSION, jetzt_txt, x.get("kurs"), markt.get(x["symbol"], "spot"),
                       paare.get(x["symbol"], x["symbol"] + "USDT"), fak.get(x["symbol"], 1.0)))
            c.execute("UPDATE signal SET stufe=?, p2=?, p3=?, p5=?, endgueltig_am=? WHERE symbol=? AND signalstunde=?",
                      (x["stufe"], x["p2"], x["p3"], x["p5"], jetzt_txt, x["symbol"], x["signalstunde"]))
        for sh_txt in B.get("nachgeholt_stunden", []):
            c.execute("INSERT OR REPLACE INTO nachgeholt VALUES (?,?,?)",
                      (sh_txt, _stunde_txt(jetzt), sum(1 for x in B["nachgeholt"] if x["signalstunde"] == sh_txt)))
        if B.get("nachgeholt_stunden") or B.get("nachholen_ausgelassen"):
            meldung = (meldung + " · " if meldung else "") + "nachgeholt: %s%s" % (
                ", ".join(B.get("nachgeholt_stunden") or []) or "-",
                (" · NICHT nachholbar (Modellpaket fehlt): " + ", ".join(B["nachholen_ausgelassen"])) if B.get("nachholen_ausgelassen") else "")
        c.execute("INSERT OR REPLACE INTO lauf VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (_stunde_txt(jetzt), jetzt_txt, round(time.time() - t0, 1), ",".join(sorted(pakete)), fr["aktiv"], fr["frisch"],
                   len(fr["veraltet"]), ",".join(fr["veraltet"][:50]), fr["nicht_im_handel"], len(B["neu"]), len(B["endgueltig"]), meldung))
        c.commit()
    finally:
        c.close()
    zus_ = dict(jetzt=_stunde_txt(jetzt), sekunden=round(time.time() - t0, 1), neu=len(B["neu"]), endgueltig=len(B["endgueltig"]),
                nachgeholt=B.get("nachgeholt_stunden") or [],
                neu_schalter_an=sum(1 for x in B["neu"] if (zu_bp.get(x["symbol"], x["symbol"]) or "") and
                                    schalter.get(zu_bp.get(x["symbol"], x["symbol"]).upper())),
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
