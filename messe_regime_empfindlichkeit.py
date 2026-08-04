"""Stufe 2: Reagiert das LLM ueberhaupt auf die Marktphase? (2026-08-04)

DIE FRAGE. Alle Kalibrierung stammt aus einer Baerenphase. Ob das LLM in einer
Aufwaertsphase anders urteilen wuerde, laesst sich nicht direkt pruefen - es
gibt keine Signale von dort. Aber: DIE PHASE IST EIN DETERMINISTISCHER FAKT,
den WIR liefern (agent/krypto/regime.py -> regime.wert im Fakten-JSON). Das
LLM leitet sie nicht her. Also laesst sie sich tauschen und die Reaktion
messen.

WAS DAS BEANTWORTET - und was nicht:

    beantwortbar:    Reagiert das LLM auf die Phase? Wie stark?
    NICHT:           Reagiert es in die RICHTIGE Richtung? Dafuer fehlen
                     Ergebnisse aus einer Aufwaertsphase.

Beide Ausgaenge sind verwertbar. Reagiert es NICHT, sind die 13 Regime-Fakten
totes Gewicht im Prompt - ein Befund fuer die Prompt-Inventur. Reagiert es
stark, ist das Risiko einer Fehlkalibrierung beziffert.

STUFE 2 STATT STUFE 1. Nur `regime.wert` umzuschalten erzeugt einen
widerspruechlichen Faktensatz: das Label saegt "bulle", waehrend btc_trend
weiter Baerenwerte traegt. Deshalb wird der BTC-Trend MIT getauscht - und zwar
gegen einen ECHTEN Wert aus einer realen Aufwaertsphase der Kurshistorie
(183 AUF-Tage vorhanden), nicht gegen einen erfundenen.

WAS AUCH STUFE 2 NICHT KANN: Fear&Greed, BTC-Dominanz und Dollar-Index werden
historisch nicht gespeichert. Sie bleiben auf Baerenwerten stehen. Der
Faktensatz ist also konsistenter als in Stufe 1, aber nicht vollstaendig
konsistent - das ist die benannte Grenze, keine uebersehene.
"""
from __future__ import annotations

import io
import json
import sys

from messe_prompt_nebeneffekte import (
    _sammle, _uneinigkeit, Befund, bericht,
)

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"

# Aus agent/krypto/regime.py: REGIME_STATES und die btc_trend_label-Texte.
# Woertlich uebernommen - ein abweichender Text waere fuer das LLM ein
# anderer Fakt und die Messung waere nicht das, was sie zu sein vorgibt.
AUFWAERTS = {
    "regime.wert": "bulle",
    "regime.btc_trend": "aufwärts (EMA20 > EMA50 > EMA200)",
}
ABWAERTS = {
    "regime.wert": "baer",
    "regime.btc_trend": "abwärts (EMA20 < EMA50 < EMA200)",
}


def _setze_pfad(fakten: dict, pfad: str, wert) -> None:
    knoten = fakten
    teile = pfad.split(".")
    for t in teile[:-1]:
        if not isinstance(knoten, dict) or t not in knoten:
            return
        knoten = knoten[t]
    if isinstance(knoten, dict) and teile[-1] in knoten:
        knoten[teile[-1]] = wert


def tausche(fakten: dict, ersetzungen: dict) -> dict:
    import copy
    kopie = copy.deepcopy(fakten)
    for pfad, wert in ersetzungen.items():
        _setze_pfad(kopie, pfad, wert)
    return kopie


def pruefe_aufwaertsphase_existiert() -> tuple[int, str, str] | None:
    """Belegt an der echten Kurshistorie, dass es Aufwaertsphasen GAB.

    Ohne diesen Nachweis waere der getauschte Wert eine Erfindung. Mit ihm ist
    er die Beschreibung eines real eingetretenen Marktzustands."""
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    # LAENGSTE Reihe nehmen, nicht die erste gefundene. Die erste Fassung
    # brach bei der ersten Quelle mit BTC ab - und die fuehrt nur den
    # Signalzeitraum. Gemeldet wurden dadurch 2 AUF-Tage statt 183, was den
    # Beleg wertlos aussehen liess. Der Fehler lag in der Pruefung, nicht in
    # den Daten.
    btc: list = []
    for q in ("preishistorie_signal_symbole", "preishistorie_ueberholte_symbole"):
        rr = ((d.get(q) or {}).get("preishistorie_je_symbol") or {}).get("BTC")
        if not rr:
            continue
        kand = sorted((p for p in rr if p.get("currency") == "USD"),
                      key=lambda p: str(p["date"])[:10])
        if len(kand) > len(btc):
            btc = kand
    if not btc:
        return None
    F, SCHWELLE = 30, 8.0
    auf = []
    for i in range(F, len(btc)):
        a, b = btc[i - F]["close"], btc[i]["close"]
        if a and b and (b / a - 1) * 100 > SCHWELLE:
            auf.append(str(btc[i]["date"])[:10])
    return (len(auf), min(auf), max(auf)) if auf else None


def messe_regime(provider, fakten_je_signal: list[dict],
                 wiederholungen: int = 5) -> Befund:
    """Drei Arme wie bei messe_prompt_nebeneffekte, aber TAUSCH statt Entfernen.

        A1  Regime auf Baer (unveraendert)
        A2  Regime auf Baer (identisch)  -> Rauschboden
        B   Regime auf Bulle             -> Wirkung
    """
    import statistics
    a_r, a_w, k_r, k_w = [], [], [], []
    for fakten in fakten_je_signal:
        baer = tausche(fakten, ABWAERTS)
        bulle = tausche(fakten, AUFWAERTS)
        a1 = _sammle(provider, baer, wiederholungen)
        a2 = _sammle(provider, baer, wiederholungen)
        b = _sammle(provider, bulle, wiederholungen)
        a_r.append(_uneinigkeit(a1.actions, a2.actions))
        a_w.append(_uneinigkeit(a1.actions, b.actions))
        if a1.konfidenzen and a2.konfidenzen and b.konfidenzen:
            m1, m2, mb = (statistics.fmean(x.konfidenzen) for x in (a1, a2, b))
            k_r.append(abs(m1 - m2))
            k_w.append(abs(m1 - mb))
    ar = statistics.fmean(a_r) if a_r else 0.0
    aw = statistics.fmean(a_w) if a_w else 0.0
    kr = statistics.fmean(k_r) if k_r else 0.0
    kw = statistics.fmean(k_w) if k_w else 0.0
    srv_a = (aw / ar) if ar > 1e-9 else None
    srv_k = (kw / kr) if kr > 1e-9 else None
    kand = [x for x in (srv_a, srv_k) if x is not None]
    srv = max(kand) if kand else None
    if srv is None:
        urteil = "unbestimmt (kein Rauschen messbar)"
    elif srv < 1.0:
        urteil = ("KEINE Reaktion auf die Marktphase - die Regime-Fakten "
                  "bewegen weniger als zwei identische Laeufe")
    elif srv < 2.0:
        urteil = "schwache Reaktion im Rauschbereich - nicht belastbar"
    else:
        urteil = f"REAKTION nachweisbar ({srv:.1f}-faches Eigenrauschen)"
    return Befund("regime (baer -> bulle, Stufe 2)", len(fakten_je_signal),
                  wiederholungen, ar, aw, kr, kw, srv, urteil)


def selbsttest() -> int:
    """Prueft den Tauschmechanismus, bevor Kontingent fliesst."""
    import random
    rng = random.Random(20260805)
    fehler = []

    print("=== Beleg: gab es reale Aufwaertsphasen? ===")
    nachweis = pruefe_aufwaertsphase_existiert()
    if nachweis:
        n, von, bis = nachweis
        print(f"  {n} AUF-Tage in der BTC-Historie, {von} .. {bis}")
        print("  -> der getauschte btc_trend beschreibt einen real")
        print("     eingetretenen Zustand, keine Erfindung")
    else:
        print("  FEHL  keine Aufwaertsphase nachweisbar")
        fehler.append("Aufwaertsphase")

    def fakten(i):
        return {"asset": {"symbol": f"T{i}"},
                "regime": {"wert": "baer", "quelle": "test",
                           "btc_trend": "abwärts (EMA20 < EMA50 < EMA200)"},
                "preis": {"usd": 100.0}}

    def antwort(k):
        return {"action": "ERÖFFNEN" if k >= 60 else "HALTEN",
                "confidence_pct": k,
                "entry": {"usd_von": 99.0, "usd_bis": 101.0},
                "stop_loss": {"usd_von": 95.0},
                "take_profit": {"usd_von": 110.0}}

    def blind(f):
        return antwort(62.0 + rng.gauss(0, 4))

    def phasenbewusst(f):
        bulle = (f.get("regime") or {}).get("wert") == "bulle"
        return antwort((74.0 if bulle else 58.0) + rng.gauss(0, 4))

    print()
    print("=== Tausch greift? ===")
    probe = tausche(fakten(0), AUFWAERTS)
    ok = probe["regime"]["wert"] == "bulle" and "aufwärts" in probe["regime"]["btc_trend"]
    print(f"  {'OK  ' if ok else 'FEHL'}  regime.wert und btc_trend getauscht")
    print(f"        {probe['regime']['wert']} / {probe['regime']['btc_trend']}")
    if not ok:
        fehler.append("Tausch")
    unberuehrt = probe["asset"]["symbol"] == "T0" and probe["preis"]["usd"] == 100.0
    print(f"  {'OK  ' if unberuehrt else 'FEHL'}  uebrige Fakten unveraendert")
    if not unberuehrt:
        fehler.append("Seiteneffekt")

    signale = [fakten(i) for i in range(6)]
    print()
    for name, prov, erwartet in (("blind (ignoriert die Phase)", blind, False),
                                 ("phasenbewusst", phasenbewusst, True)):
        b = messe_regime(prov, signale, wiederholungen=12)
        print(f"--- {name} ---")
        print(bericht(b))
        hat = b.signal_rausch_verhaeltnis is not None and b.signal_rausch_verhaeltnis >= 2.0
        gut = hat == erwartet
        print(f"  {'OK  ' if gut else 'FEHL'}  erwartet: "
              f"{'Reaktion' if erwartet else 'keine Reaktion'}")
        print()
        if not gut:
            fehler.append(name)

    if fehler:
        print(f"FEHLGESCHLAGEN: {fehler}")
        return 1
    print("Stufe 2 bereit. Der echte Lauf braucht die Schluessel (Notebook).")
    return 0


if __name__ == "__main__":
    raise SystemExit(selbsttest())
