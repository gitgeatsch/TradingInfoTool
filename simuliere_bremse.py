"""Soll die Bremse angewandt werden? (20.08.2026, Umbauplan 99)

DIE FRAGE DES NUTZERS, woertlich: *"diese Bremse ist nicht nur zu messen bzw.
rechnen, sondern wir muessen ueber historische Daten detailliert simulieren,
ob wir den Filter anwenden - vor allem in den von uns verwendeten Bereichen
SPOT und Hebel. Krypto vorerst, andere Assetklassen danach."*

Und die Vorgabe dazu: *"Die 106 Mails sollen NICHT zusammengefasst werden,
sondern die Mailanzahl muss sich durch das System regulieren - geringere
Anzahl an Signalen durch optimierte Signalgenerierung und Bewertung."*

DIE BREMSE IST KEIN NEUES URTEIL. Sie steht seit jeher in jeder Mail:

    --> Traegt sich NICHT: 34 erreichen das Ziel, noetig waeren 42.

`trefferbilanz.bewerte()` rechnet das aus zwei Zahlen: der Trefferquote der
eigenen Vergangenheit fuer DIESE Konstellation und dem Breakeven aus Kosten
und CRV. Beide sind Arithmetik, keine Prognose. Bisher wird die Zeile nur
gedruckt; die Bremse waere, danach zu handeln.

⚠️ WARUM SIE HEUTE NICHTS DURCHLIESSE - UND WORAN DAS LIEGT.

Die Trefferquote je Konstellation kommt aus den EIGENEN Signalen, und davon
gibt es je Zelle fast keine. `geschrumpft()` zieht sie deshalb auf die
Basisrate zusammen, und die liegt per Konstruktion UNTER dem Breakeven:

    Basisrate  1/(1+CRV)        Breakeven  (1+Kosten)/(1+CRV)

Derselbe Nenner, also liegt die Huerde bei Kosten ueber null IMMER darueber.
Solange die Zelle leer ist, ist die Antwort deshalb rechnerisch immer NEIN -
und ein Filter, der immer nein sagt, ist der Deadloop.

DESHALB SIMULIERT DIESES WERKZEUG DIE TABELLE AUS DER HISTORIE. Nicht aus
unseren 118 Signalen, sondern aus zehntausenden Ankern der eigenen
Kursreihen. Erst dann steht in jeder Zelle eine Zahl, die etwas traegt - und
erst dann ist die Frage "anwenden oder nicht" ueberhaupt beantwortbar.

⚠️ DIESELBEN FUNKTIONEN WIE DER BETRIEB. `merkmale()`, `geschrumpft()`,
`breakeven()` und `basisrate_fuer()` werden IMPORTIERT, nicht nachgebaut.
Eine zweite Fassung waere die Sorte Kopie, die still veraltet - und dann
simulierte man eine Bremse, die es nicht gibt.

⚠️ WALK-FORWARD. Die Tabelle fuer einen Anker wird NUR aus Faellen gebaut,
die davor abgeschlossen waren. Wer die ganze Historie nimmt, laesst den
Filter in die Zukunft sehen und misst sich selbst.

    python simuliere_bremse.py [--instrument spot|hebel] [--klasse krypto]
"""
from __future__ import annotations

import argparse
import io
import json
import sys

import math

import numpy as np

sys.path.insert(0, ".")
from agent import trefferbilanz as TB                        # noqa: E402
from messe_drift import _reihen                              # noqa: E402

# Unsere Zeitfenster, aus dem Betrieb uebernommen und NICHT neu gewaehlt:
# `entscheidungsrechnung.GRENZEN["tage_max"]` deckelt die Haltedauer.
MAX_TAGE = 120
# Der Rauschboden aus config.yaml (rollen_kette.stop_min_atr, S1/Kapitel 90).
STOP_ATR = 2.0
# Das Ziel folgt dem CRV der Trefferbilanz - dieselbe Zahl, damit Basisrate
# und Geometrie nicht auseinanderlaufen (der Fund vom 12.08.).
CRV = TB.CRV
# Fenster fuer die Perzentile, die in den Schluessel gehen.
FENSTER = 250
# Ab wann eine Zelle ueberhaupt etwas sagt. Unter dieser Zahl greift die
# Schrumpfung ohnehin fast vollstaendig.
MIN_ZELLE = 20

# ⚠️ SPOT UND HEBEL UNTERSCHEIDEN SICH IN DEN KOSTEN, NICHT IN DER GEOMETRIE
# (Kapitel 90: `Hebel = Verlustanteil / Stopabstand` - Stop und Ziel sind
# dieselben). Beim Hebel kommt die Finanzierung dazu, und sie laeuft mit der
# Haltedauer. Deshalb ist der Breakeven dort hoeher, und deshalb muessen die
# beiden getrennt simuliert werden - eine gemeinsame Zahl waere fuer beide
# falsch.
#
# Der Satz ist der uebliche Bereich fuer Krypto-Dauerpositionen; er steht
# hier als Annahme, weil unsere eigene Reihe dafuer zu kurz ist.
FINANZIERUNG_JE_TAG = {"spot": 0.0, "hebel": 0.0003}

# Die Marktphase am Ankertag - aus dem Markt selbst, nicht aus einem Etikett.
# Gemessen am Mittel aller Symbole ueber 250 Tage; die Schwellen sind die
# gaengigen +/-20 %.
PHASE_FENSTER = 250
PHASE_SCHWELLE = 0.20


def _atr(h, l, c, fenster: int = 14):
    tr = np.maximum(h[1:] - l[1:],
                    np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    return np.array([tr[max(0, i - fenster + 1):i + 1].mean()
                     for i in range(fenster - 1, len(tr))])


def _rang(reihe, i: int, fenster: int = FENSTER):
    """Perzentil des heutigen Werts im eigenen Fenster - wie im Betrieb."""
    ab = max(0, i - fenster)
    v = reihe[ab:i]
    v = v[np.isfinite(v)]
    if len(v) < 30:
        return None
    return int(round(100.0 * float((v < reihe[i]).mean())))


def _reihen_roh(db: str, klasse: str, klassen: dict | None = None) -> dict:
    """Symbol -> (close, high, low, volumen, atr, offset).

    ⚠️ DIE ANLAGEKLASSE STEHT NICHT IN DER DATENBANK, sondern in der
    Watchlist. Eine Messdatenbank mit eigenen Symbolen haette dort keinen
    Eintrag - jede Reihe waere STILL uebersprungen worden, und die Messung
    haette wie gewohnt ausgesehen, nur mit den alten 24 Reihen (Umbauplan
    107).

    `klassen` ist deshalb ein optionaler Ersatz fuer diese Zuordnung. Ohne
    Angabe bleibt alles exakt wie bisher - die Produktion sieht keinen
    Unterschied."""
    import config as C
    from backtest_llm1_historisch import lade_reihen_aus_db

    kl = klassen if klassen is not None else {
        x.symbol: str(getattr(x, "assetklasse", "") or "").lower()
        for x in C.get_watchlist()}
    aus = {}
    for sym, kerzen in lade_reihen_aus_db(db).items():
        if sym.startswith("_") or kl.get(sym) != klasse or len(kerzen) < 400:
            continue
        c = np.array([float(k.close) for k in kerzen])
        h = np.array([float(k.high) for k in kerzen])
        l = np.array([float(k.low) for k in kerzen])
        v = np.array([float(k.volume or 0) or np.nan for k in kerzen])
        d = [str(k.date)[:10] for k in kerzen]
        a = _atr(h, l, c)
        aus[sym] = (c, h, l, v, a, len(c) - len(a), d)
    return aus



def klassen_aus_db(db: str) -> dict | None:
    """Die Anlageklassen, die eine MESSdatenbank selbst mitbringt.

    ⚠️ Gibt None zurueck, wenn es die Tabelle nicht gibt - dann gilt die
    Watchlist wie bisher. Ein Rueckfall auf ein leeres Woerterbuch waere der
    schlimmste Fall: er wuerde JEDE Reihe verwerfen, und die Messung liefe
    ohne eine einzige Zeile durch (Umbauplan 107)."""
    import sqlite3
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
            return {s: k for s, k in
                    c.execute("SELECT symbol, assetklasse FROM messreihen")}
    except sqlite3.Error:
        return None


# ⚠️ ZWEI SAETZE, ZWEI FRAGEN (Umbauplan 119, Nutzerentscheidung 20.08.).
#
#   REFERENZ  0,30 % je Seite - beantwortet "IST DAS EIN GUTER TRADE?".
#             Boersenunabhaengig, weil sonst nicht der Markt gemessen wird,
#             sondern das Preismodell eines Anbieters. Hergeleitet aus
#             veroeffentlichten Taker-Gebuehren der Grundstufe:
#             Bitpanda Pro 0,15 % · Bitvavo 0,25 % · Kraken 0,40 %
#             -> Mittel 0,27 %, plus rund 0,03 % Slippage.
#             ⚠️ Ein Mischsatz gilt nur ueber VERGLEICHBARE Modelle. Der
#             Bitpanda-Brokersatz (Spread) gehoert nicht hinein - Spread und
#             Orderbuch sind zwei Geschaeftsmodelle, kein Kontinuum.
#
#   BETRIEB   1,50 % je Seite - beantwortet "RECHNET SICH DAS FUER MICH?".
#             Bitpandas Brokerspread, 0,99 % (BTC) bis 2,49 % (Altcoins).
#             Bleibt fuer die Produktion und fuer die Portfoliorechnung in
#             den Mails unveraendert massgeblich.
#
# ⚠️ JEDES MESSERGEBNIS WIRD ZWEISPALTIG BERICHTET - Referenz UND Betrieb
# nebeneinander. Ein Ergebnis ohne sein reales Gegenstueck laedt zur
# Fehldeutung ein; laufen die beiden auseinander, IST das die Aussage.
REFERENZ_JE_SEITE = 0.003
SAETZE_ZUM_BERICHTEN = (("Referenz 0,30 %", 0.003), ("Betrieb 1,50 %", 0.015))


def gebuehr_je_seite(klasse: str, satz: float | None = None) -> float:
    """Der Gebuehrensatz je Seite - und ein LAUTES Nein fuer alles andere.

    ⚠️ HIER STAND EIN STILLER RUECKFALL. Alle Messwerkzeuge lasen
    `TB.KOSTEN_JE_SEITE.get(klasse, 0.015)`. Fuer 'aktien' und 'etf' gibt es
    dort keinen Schluessel - sie bekamen also kommentarlos die KRYPTO-Gebuehr
    und haetten eine Messung ausgegeben, die niemand als falsch erkannt
    haette.

    An der Boerse sind die Kosten eine FIXGEBUEHR je Seite plus Spread. Die
    Fixgebuehr haengt an der Positionsgroesse und kuerzt sich aus
    `2 * Gebuehr / Stopabstand` nicht heraus - ein einzelner Prozentsatz kann
    sie gar nicht ausdruecken. Die Produktion rechnet das richtig
    (`TB.kosten_r_aus_stop`); diese Simulationen kennen keine
    Positionsgroesse.

    Deshalb wird hier abgebrochen statt geschaetzt. Wer die Messungen auf
    Boersenklassen ausweiten will, muss ihnen zuerst eine Positionsgroesse
    geben - siehe Umbauplan 106."""
    if satz is not None:
        return float(satz)
    satz = TB.KOSTEN_JE_SEITE.get(klasse)
    if satz is None:
        raise SystemExit(
            f"Anlageklasse '{klasse}' hat keinen Gebuehrensatz je Seite. "
            f"Boersenklassen rechnen mit Fixgebuehr + Spread und brauchen "
            f"eine Positionsgroesse (TB.kosten_r_aus_stop). Ein stiller "
            f"Rueckfall auf den Krypto-Satz waere eine falsche Messung.")
    return float(satz)

def _marktphase(roh: dict, fenster: int = PHASE_FENSTER,
                schwelle: float | None = None) -> dict:
    """Datum -> "bulle" / "seitwaerts" / "baer".

    ⚠️ AUS DEM MARKT SELBST, NICHT AUS EINEM ETIKETT. Das Projekt hat sich
    verboten, "Modell oder Markt?" zu fragen - hier wird der Markt deshalb
    gemessen: gleichgewichteter Index aus allen Reihen, seine eigene
    250-Tage-Bewegung, Schwellen bei +/-20 %.

    WARUM ES SEIN MUSS: bis heute lief JEDE Messung dieses Projekts auf einem
    einzigen Regime (Memory: "Regime war IMMER baer"). Eine Bremse, die nur
    im Baermarkt geprueft wurde, ist keine geprueffte Bremse."""
    reihen = {}
    for sym, (c, _h, _l, _v, _a, _off, d) in roh.items():
        for j, tag in enumerate(d):
            reihen.setdefault(tag, []).append(c[j] / c[0])
    tage = sorted(reihen)
    index = np.array([float(np.mean(reihen[t])) for t in tage])
    # ⚠️ DIE SCHWELLE MUSS ZUM FENSTER PASSEN. +/-20 % sind fuer 250 Tage die
    # gaengige Zahl; auf 20 Tagen waeren sie fast nie erreicht - dann hiesse
    # jeder Zeitpunkt "seitwaerts" und die Messung vergliche nichts.
    # Skaliert wird mit der Wurzel des Fensters, wie es fuer einen zufaelligen
    # Pfad zu erwarten ist. Ohne Angabe bleibt es bei der alten Zahl.
    s = (PHASE_SCHWELLE if schwelle is None
         else schwelle * math.sqrt(fenster / PHASE_FENSTER))
    aus = {}
    for j, tag in enumerate(tage):
        if j < fenster or index[j - fenster] <= 0:
            aus[tag] = "unbekannt"
            continue
        r = index[j] / index[j - fenster] - 1.0
        aus[tag] = ("bulle" if r > s else
                    "baer" if r < -s else "seitwaerts")
    return aus


def baue_anker(db: str, klasse: str, instrument: str) -> list[dict]:
    faelle = []
    roh = _reihen_roh(db, klasse)
    phase = _marktphase(roh)
    for sym, (c, h, l, v, a, off, d) in roh.items():
        # Tagesrenditen fuer das Schwankungs-Perzentil.
        rend = np.full(len(c), np.nan)
        rend[1:] = np.abs(np.diff(c) / c[:-1])
        for i in range(off + FENSTER, len(c) - 1):
            atr = a[i - off]
            einstieg = c[i]
            if not (atr > 0 and einstieg > 0):
                continue
            stop = einstieg - STOP_ATR * atr
            if stop <= 0:
                continue
            risiko = einstieg - stop
            ziel = einstieg + CRV * risiko
            ausgang, tage = "abgelaufen", MAX_TAGE
            for j in range(i + 1, min(i + 1 + MAX_TAGE, len(c))):
                # ⚠️ STOP ZUERST. Faellt beides in dieselbe Kerze, weiss
                # niemand, was zuerst kam - die vorsichtige Lesart zaehlt.
                if l[j] <= stop:
                    ausgang, tage = "stop", j - i
                    break
                if h[j] >= ziel:
                    ausgang, tage = "ziel", j - i
                    break
            schluessel = TB.merkmale(
                vola_perzentil=_rang(rend, i),
                spanne_perzentil=_rang(np.abs(
                    np.concatenate(([np.nan] * 20,
                                    c[20:] / c[:-20] - 1.0))), i),
                gleichlauf=_rang(v, i))
            faelle.append({"symbol": sym, "datum": d[i], "i": i,
                           "schluessel": schluessel, "ausgang": ausgang,
                           "tage": tage, "phase": phase.get(d[i], "unbekannt"),
                           "stop_relativ": float(risiko / einstieg)})
    faelle.sort(key=lambda x: x["datum"])
    return faelle


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--klasse", default="krypto")
    p.add_argument("--instrument", default="spot", choices=("spot", "hebel"))
    p.add_argument("--datei", default="messwerte_bremse.json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print(f"SOLL DIE BREMSE ANGEWANDT WERDEN? - {a.klasse}/{a.instrument}")
    print("=" * 78)
    faelle = baue_anker(a.db, a.klasse, a.instrument)
    print(f"  {len(faelle)} Anker aus den eigenen Kursreihen")
    if not faelle:
        print("  keine Anker - KEIN URTEIL")
        return 1

    ausg = {}
    for f in faelle:
        ausg[f["ausgang"]] = ausg.get(f["ausgang"], 0) + 1
    n_ent = ausg.get("ziel", 0) + ausg.get("stop", 0)
    print(f"  Ausgang: Ziel {ausg.get('ziel', 0)}, Stop "
          f"{ausg.get('stop', 0)}, abgelaufen {ausg.get('abgelaufen', 0)} "
          f"({100 * ausg.get('abgelaufen', 0) / len(faelle):.0f} %)")
    print(f"  Trefferquote ueber ALLE entschiedenen Faelle: "
          f"{100 * ausg.get('ziel', 0) / max(1, n_ent):.1f} %")

    # Kosten je Trade in R - dieselbe Rechnung wie im Betrieb.
    kosten_je_seite = gebuehr_je_seite(a.klasse)
    schnitt_stop = float(np.median([f["stop_relativ"] for f in faelle]))
    # Beim Hebel laeuft die Finanzierung mit der Haltedauer mit - gerechnet
    # mit der MEDIAN-Haltedauer der entschiedenen Faelle, nicht mit dem
    # Deckel: 120 Tage waeren die Ausnahme, nicht der Fall.
    _dauer = [f["tage"] for f in faelle if f["ausgang"] in ("ziel", "stop")]
    median_tage = float(np.median(_dauer)) if _dauer else 20.0
    finanzierung = (FINANZIERUNG_JE_TAG[a.instrument] * median_tage
                    / schnitt_stop)
    kosten_r = 2 * kosten_je_seite / schnitt_stop + finanzierung
    schwelle = TB.breakeven(kosten_r, CRV)
    print(f"  Median-Stopabstand {100 * schnitt_stop:.1f} %, "
          f"Median-Haltedauer {median_tage:.0f} Handelstage")
    print(f"  Kosten {kosten_r:.2f} R"
          + (f" (davon {finanzierung:.2f} R Finanzierung)"
             if finanzierung else "")
          + f"  ->  Breakeven {100 * schwelle:.1f} %")
    print(f"  Basisrate zu CRV {CRV}: "
          f"{100 * TB.basisrate_fuer(CRV):.1f} %")

    # --- WALK-FORWARD: die Tabelle nur aus der Vergangenheit --------------
    print("\n" + "-" * 78)
    print("WALK-FORWARD - die Tabelle wird je Anker NUR aus abgeschlossenen")
    print("Faellen davor gebaut. Nichts sieht in die Zukunft.")
    print("-" * 78)
    tabelle: dict = {}
    durch, blockiert = [], []
    # Faelle nach Abschlussdatum einsortieren, damit nur Bekanntes zaehlt.
    for f in faelle:
        e = tabelle.get(f["schluessel"]) or {"treffer": 0, "faelle": 0}
        p_zelle = TB.geschrumpft(e["treffer"], e["faelle"],
                                 basisrate=TB.basisrate_fuer(CRV))
        (durch if p_zelle > schwelle else blockiert).append(f)
        # ERST DANACH einbuchen - der eigene Fall darf sein eigenes Urteil
        # nicht beeinflussen.
        if f["ausgang"] in ("ziel", "stop"):
            e["faelle"] += 1
            e["treffer"] += 1 if f["ausgang"] == "ziel" else 0
            tabelle[f["schluessel"]] = e

    def quote(liste):
        n = sum(1 for x in liste if x["ausgang"] in ("ziel", "stop"))
        t = sum(1 for x in liste if x["ausgang"] == "ziel")
        return n, (100.0 * t / n if n else 0.0)

    n_d, q_d = quote(durch)
    n_b, q_b = quote(blockiert)
    print(f"  DURCHGELASSEN {len(durch):6} Anker ({100 * len(durch) / len(faelle):4.1f} %)"
          f"   Trefferquote {q_d:5.1f} %  auf {n_d} entschiedenen")
    print(f"  BLOCKIERT     {len(blockiert):6} Anker ({100 * len(blockiert) / len(faelle):4.1f} %)"
          f"   Trefferquote {q_b:5.1f} %  auf {n_b} entschiedenen")
    print(f"  Breakeven {100 * schwelle:.1f} % - "
          + ("die Durchgelassenen liegen DARUEBER"
             if q_d > 100 * schwelle else
             "auch die Durchgelassenen liegen DARUNTER"))

    # --- JE MARKTPHASE ----------------------------------------------------
    print("\n" + "-" * 78)
    print("JE MARKTPHASE - eine Bremse, die nur im Baermarkt geprueft wurde,")
    print("ist keine geprueffte Bremse.")
    print("-" * 78)
    _durch_ids = {id(x) for x in durch}
    je_phase: dict = {}
    for f in faelle:
        e = je_phase.setdefault(f["phase"], {"durch": [], "block": []})
        e["durch" if id(f) in _durch_ids else "block"].append(f)
    print(f"  {'Phase':12}{'Anker':>8}{'durch':>8}{'Quote durch':>14}"
          f"{'Quote blockiert':>18}")
    for ph in ("bulle", "seitwaerts", "baer", "unbekannt"):
        e = je_phase.get(ph)
        if not e:
            continue
        n = len(e["durch"]) + len(e["block"])
        nd, qd = quote(e["durch"])
        nb, qb = quote(e["block"])
        print(f"  {ph:12}{n:8}{len(e['durch']):8}"
              + (f"{qd:13.1f} %" if nd >= 30 else f"{'zu wenig':>14}")
              + (f"{qb:17.1f} %" if nb >= 30 else f"{'zu wenig':>18}"))

    # --- JE ASSET ---------------------------------------------------------
    print("\n" + "-" * 78)
    print("JE ASSET - traegt der Filter ueberall oder nur bei wenigen?")
    print("-" * 78)
    je_sym: dict = {}
    for f in faelle:
        e = je_sym.setdefault(f["symbol"], {"durch": [], "block": []})
        e["durch" if id(f) in _durch_ids else "block"].append(f)
    zeilen = []
    for sym, e in je_sym.items():
        nd, qd = quote(e["durch"])
        if nd >= 30:
            zeilen.append((sym, len(e["durch"]), qd))
    ueber = [z for z in zeilen if z[2] > 100 * schwelle]
    print(f"  {len(zeilen)} Symbole mit mindestens 30 entschiedenen "
          f"Durchlaessen, davon {len(ueber)} ueber dem Breakeven "
          f"({100 * schwelle:.1f} %)")
    for sym, n, q in sorted(zeilen, key=lambda x: -x[2])[:5]:
        print(f"    {sym:10} {n:6} durch   {q:5.1f} %")
    if len(zeilen) > 5:
        print("    ...")
        for sym, n, q in sorted(zeilen, key=lambda x: x[2])[:3]:
            print(f"    {sym:10} {n:6} durch   {q:5.1f} %")

    print("\n" + "-" * 78)
    print("ZELLEN - wo steht die Quote ueber dem Breakeven?")
    print("-" * 78)
    stark = []
    for k, e in tabelle.items():
        if e["faelle"] < MIN_ZELLE:
            continue
        pz = TB.geschrumpft(e["treffer"], e["faelle"],
                            basisrate=TB.basisrate_fuer(CRV))
        if pz > schwelle:
            stark.append((k, e["faelle"], pz))
    print(f"  {len(tabelle)} Zellen belegt, "
          f"{sum(1 for e in tabelle.values() if e['faelle'] >= MIN_ZELLE)} "
          f"mit mindestens {MIN_ZELLE} Faellen, {len(stark)} davon ueber dem "
          f"Breakeven")
    for k, n, pz in sorted(stark, key=lambda x: -x[2])[:8]:
        print(f"    {str(k):46} {n:5} Faelle  {100 * pz:5.1f} %")

    print("\n" + "=" * 78)
    if not durch:
        print("DIE BREMSE LIESSE NICHTS DURCH. Ein Filter, der immer nein")
        print("sagt, ist der Deadloop - nicht anwenden.")
    elif q_d <= 100 * schwelle:
        print("DIE BREMSE LAESST ETWAS DURCH, aber auch das Durchgelassene")
        print("traegt sich nicht. Sie waehlt also aus, ohne zu verbessern.")
    else:
        print("DIE DURCHGELASSENEN LIEGEN UEBER DEM BREAKEVEN.")
        print("Erst hier lohnt die naechste Frage: haelt das auch auf")
        print("einer zweiten Anlageklasse und in einzelnen Jahren?")
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(json.dumps({
            "klasse": a.klasse, "instrument": a.instrument,
            "anker": len(faelle), "ausgang": ausg,
            "breakeven": schwelle, "kosten_r": kosten_r,
            "durchgelassen": len(durch), "quote_durch": q_d,
            "blockiert": len(blockiert), "quote_blockiert": q_b,
            "zellen": len(tabelle), "zellen_ueber_breakeven": len(stark),
        }, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
