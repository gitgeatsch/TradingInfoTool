"""Haelt die Ausstiegsregel in ALLEN Marktphasen? (Nutzer-Vorgabe 04.08.)

DIE SORGE, die ich selbst formuliert habe: in einer Aufwaertsphase koennte ein
Trailing-Stop Gewinner zu frueh beenden - dort laufen Bewegungen weiter statt
zu drehen. Der Befund (+0,092 R) stammt aus einer Baerenphase.

WARUM DAS PRUEFBAR IST, obwohl die Signale nur drei Wochen abdecken: die
KURSHISTORIE reicht 748 Tage und enthaelt alle drei Phasen (AUF 183, SEIT 379,
AB 156 Tage, BTC-getaktet). Die Regel wird deshalb nicht an Signalen geprueft,
sondern an MECHANISCHEN Einstiegen ueber die gesamte Historie - dieselbe
Technik wie die Basislinie, nur je Phase getrennt.

Das ist kein Ersatz fuer echte Signale in einer Aufwaertsphase. Es beantwortet
aber die entscheidende Teilfrage: dreht sich das VORZEICHEN des Effekts?
"""
import io
import json
import statistics
import sys

sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")

from agent.krypto.backward_tracking import gap_bewusster_fill  # noqa: E402

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))

def durchlauf(reihe, i, trailing: bool):
    """Ein mechanischer LONG-Einstieg am Schlusskurs von Tag i."""
    e = reihe[i]["close"]
    if not e or e <= 0:
        return None
    risiko = e * STOP_REL
    stop, ziel = e - risiko, e + risiko * CRV
    mfe = 0.0
    for p in reihe[i + 1:i + 2 + HORIZONT]:
        hoch, tief, auf = p["high"], p["low"], p["open"]
        if hoch is None or tief is None:
            continue
        if tief <= stop:
            fill = gap_bewusster_fill(stop, auf, ist_stop=True, ist_short=False)
            return (fill - e) / risiko
        mfe = max(mfe, (hoch - e) / risiko)
        if trailing and mfe >= 1.0:
            stop = max(stop, e + risiko * (mfe - 1.0))
        if hoch >= ziel:
            fill = gap_bewusster_fill(ziel, auf, ist_stop=False, ist_short=False)
            return (fill - e) / risiko
    letzter = reihe[min(i + 1 + HORIZONT, len(reihe) - 1)]["close"]
    return None if not letzter else (letzter - e) / risiko


def main() -> int:
    """Laeuft nur beim direkten Aufruf - NICHT beim Import.

    Die erste Fassung stand als Modulcode da (unveraendert aus dem
    Scratchpad uebernommen) und startete bei JEDEM Import einen Lauf
    ueber 12.421 mechanische Einstiege. Beim Import-Regressionscheck
    vor dem Deploy aufgefallen - genau dafuer ist er da.
    """
    reihen = {}
    for q in ("preishistorie_signal_symbole", "preishistorie_ueberholte_symbole"):
        for s, rr in ((d.get(q) or {}).get("preishistorie_je_symbol") or {}).items():
            g = [p for p in (rr or []) if p.get("currency") == "USD"]
            if len(g) > 60:
                reihen[s] = sorted(g, key=lambda p: str(p["date"])[:10])

    # --- Phasen aus BTC ableiten, 30-Tage-Trend --------------------------------
    btc = reihen.get("BTC")
    if not btc:
        raise SystemExit("BTC-Historie fehlt")
    F, SCHWELLE = 30, 8.0
    phase_je_tag = {}
    for i in range(F, len(btc)):
        a, b = btc[i - F]["close"], btc[i]["close"]
        if not a or not b:
            continue
        v = (b / a - 1) * 100
        phase_je_tag[str(btc[i]["date"])[:10]] = (
            "AUF" if v > SCHWELLE else ("AB" if v < -SCHWELLE else "SEIT"))

    # --- Mechanische Einstiege: Median-Parameter der echten Signale ------------
    STOP_REL, CRV, HORIZONT = 0.0394, 2.6, 14



    ergebnis: dict[str, dict[str, list[float]]] = {}
    for sym, reihe in reihen.items():
        for i in range(len(reihe) - HORIZONT - 2):
            tag = str(reihe[i]["date"])[:10]
            ph = phase_je_tag.get(tag)
            if ph is None:
                continue
            ohne = durchlauf(reihe, i, False)
            mit = durchlauf(reihe, i, True)
            if ohne is None or mit is None:
                continue
            ergebnis.setdefault(ph, {"ohne": [], "mit": []})
            ergebnis[ph]["ohne"].append(ohne)
            ergebnis[ph]["mit"].append(mit)

    print("=" * 78)
    print("AUSSTIEGSREGEL JE MARKTPHASE - mechanische Einstiege, echte Kurse")
    print("=" * 78)
    print(f"Parameter: Stop {STOP_REL*100:.2f} %, CRV {CRV}, Horizont {HORIZONT} T, "
          f"Trailing ab 1,0 R Abstand 1,0 R")
    print(f"Phasen aus BTC, {F}-Tage-Trend, Schwelle +-{SCHWELLE:.0f} %")
    print()
    print(f"{'Phase':7s} {'n':>7s} {'EW ohne':>9s} {'EW mit':>9s} {'Delta':>9s} "
          f"{'Trefferq ohne':>14s} {'mit':>7s}")
    for ph in ("AUF", "SEIT", "AB"):
        w = ergebnis.get(ph)
        if not w or len(w["ohne"]) < 50:
            print(f"{ph:7s}   zu wenig Faelle")
            continue
        o, m = statistics.fmean(w["ohne"]), statistics.fmean(w["mit"])
        to = sum(1 for x in w["ohne"] if x > 0) / len(w["ohne"]) * 100
        tm = sum(1 for x in w["mit"] if x > 0) / len(w["mit"]) * 100
        marke = "   <-- Vorzeichen dreht" if (m - o) < 0 else ""
        print(f"{ph:7s} {len(w['ohne']):7d} {o:+9.3f} {m:+9.3f} {m-o:+9.3f} "
              f"{to:13.1f}% {tm:6.1f}%{marke}")

    print()
    alle_o = [x for w in ergebnis.values() for x in w["ohne"]]
    alle_m = [x for w in ergebnis.values() for x in w["mit"]]
    if alle_o:
        print(f"{'GESAMT':7s} {len(alle_o):7d} {statistics.fmean(alle_o):+9.3f} "
              f"{statistics.fmean(alle_m):+9.3f} "
              f"{statistics.fmean(alle_m)-statistics.fmean(alle_o):+9.3f}")
    print()
    print("Lesart: bleibt Delta in ALLEN drei Phasen positiv, ist die Regel")
    print("phasenrobust. Dreht das Vorzeichen in AUF, braucht sie eine")
    print("Phasen-Abschaltung - genau die Selbstjustierung.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
