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
import numpy as np
import statistics
import sys

sys.path.insert(0, r"D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool")

from agent.krypto.backward_tracking import gap_bewusster_fill  # noqa: E402

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"

# Mechanische Einstiege: Median-Parameter der echten Signale.
#
# ⚠️ SIE STANDEN BIS ZUM 26.08.2026 IN `main()` - also LOKAL, waehrend
# `durchlauf()` sie GLOBAL liest. Das Skript konnte damit nie laufen
# (`NameError: STOP_REL`), stand aber seit dem 04.08. im Werkzeugkasten
# 2.13 und galt als vorhanden. Gefunden erst, als es gebraucht wurde.
#
# ⚠️ UND ZWEI PRUEFUNGEN HABEN ES NICHT GEFANGEN: `finde_freie_namen.py`
# meldet es nicht, und in `pruefe_pakete.py` kommt das Skript gar nicht
# vor. Ein Werkzeug, das im Kasten steht und nicht laeuft, ist
# schlechter als keines - man verlaesst sich darauf.
STOP_REL, CRV, HORIZONT = 0.0394, 2.6, 14
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


BLOCKLAENGE = 30          # >= Horizont (14) - benachbarte Anker teilen Kerzen
ZIEHUNGEN = 1000


def block_bootstrap(diffs, blocklaenge=BLOCKLAENGE, ziehungen=ZIEHUNGEN,
                    saat=20260826):
    """Vertrauensintervall der MITTLEREN paarweisen Differenz.

    ⚠️ WARUM BOOTSTRAP UND KEINE PERMUTATION (Methodik 2.55). "Mit Trailing"
    und "ohne" sind zwei deterministische Umrechnungen DESSELBEN Kurspfades
    an DENSELBEN Ankern. Es gibt keine zufaellige Zuordnung, die eine
    Permutation zerstoeren koennte - sie wuerde eine Schwelle liefern, die
    dem Messwert entspricht (genau der Fehler von Kapitel 123).

    Die Frage lautet deshalb nicht "ist der Unterschied echt", sondern "wie
    genau ist er geschaetzt". Ein Intervall, das die Null nicht einschliesst,
    ist die Antwort.

    ⚠️ UND WARUM BLOECKE. Benachbarte Anker derselben Reihe teilen sich
    Kerzen (Horizont 14 Tage) - ihre Differenzen sind abhaengig. Einzelwerte
    zu ziehen wuerde diese Abhaengigkeit ignorieren und das Intervall zu eng
    machen. Gezogen werden deshalb zusammenhaengende Bloecke JE REIHE.
    """
    if not diffs:
        return None
    # Bloecke: zusammenhaengende Laeufe je Symbol
    je_sym = {}
    for sym, i, d in diffs:
        je_sym.setdefault(sym, []).append((i, d))
    bloecke = []
    for sym, werte in je_sym.items():
        werte.sort()
        w = [d for _i, d in werte]
        for s in range(0, len(w), blocklaenge):
            teil = w[s:s + blocklaenge]
            if teil:
                bloecke.append(teil)
    if len(bloecke) < 10:
        return None
    rng = np.random.default_rng(saat)
    n_ziel = sum(len(b) for b in bloecke)
    mittel = []
    for _z in range(ziehungen):
        gezogen, anzahl = [], 0
        while anzahl < n_ziel:
            b = bloecke[int(rng.integers(0, len(bloecke)))]
            gezogen.extend(b)
            anzahl += len(b)
        mittel.append(float(np.mean(gezogen[:n_ziel])))
    mittel.sort()
    return {"punkt": float(np.mean([d for _s, _i, d in diffs])),
            "u": mittel[int(0.025 * len(mittel))],
            "o": mittel[int(0.975 * len(mittel))],
            "bloecke": len(bloecke), "n": len(diffs)}


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
            ergebnis.setdefault(ph, {"ohne": [], "mit": [], "diff": []})
            ergebnis[ph]["ohne"].append(ohne)
            ergebnis[ph]["mit"].append(mit)
            # Herkunft mit: die Bloecke des Bootstraps muessen
            # ZUSAMMENHAENGENDE Anker derselben Reihe sein.
            ergebnis[ph]["diff"].append((sym, i, mit - ohne))

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
    # ---- BLOCK-BOOTSTRAP auf den paarweisen Differenzen (2.55) ----------
    print()
    print("=" * 78)
    print(f"BLOCK-BOOTSTRAP der Differenz (mit - ohne), {ZIEHUNGEN} Ziehungen,")
    print(f"Bloecke von {BLOCKLAENGE} zusammenhaengenden Ankern je Reihe")
    print("=" * 78)
    print(f"{'Phase':7s} {'n':>7s} {'Bloecke':>8s} {'Delta':>9s} "
          f"{'95%-Intervall':>22s}   Urteil")
    bs = {}
    for ph in ("AUF", "SEIT", "AB"):
        w = ergebnis.get(ph)
        if not w:
            continue
        r = block_bootstrap(w["diff"])
        if not r:
            print(f"{ph:7s}   zu wenige Bloecke")
            continue
        bs[ph] = r
        schliesst_null = r["u"] <= 0 <= r["o"]
        urteil = ("nicht von null zu trennen" if schliesst_null
                  else "SCHADET (Intervall unter null)" if r["o"] < 0
                  else "NUETZT (Intervall ueber null)")
        print(f"{ph:7s} {r['n']:7d} {r['bloecke']:8d} {r['punkt']:+9.3f} "
              f"[{r['u']:+7.3f}, {r['o']:+7.3f}]   {urteil}")
    print()
    print("Lesart (2.55): die Frage ist nicht 'ist der Unterschied echt',")
    print("sondern 'wie genau ist er geschaetzt'. Ein Intervall, das die")
    print("Null NICHT einschliesst, ist die Antwort.")

    print()
    print("Lesart: bleibt Delta in ALLEN drei Phasen positiv, ist die Regel")
    print("phasenrobust. Dreht das Vorzeichen in AUF, braucht sie eine")
    print("Phasen-Abschaltung - genau die Selbstjustierung.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
