"""Haelt der Trichter, was er sagt? (19.08.2026, Umbauplan 93 A - Fallstrick A2)

DIE FRAGE. `agent/trichter.py` behauptet in jeder Mail: "in 80 von 100 Faellen
bleibt die Kursaenderung binnen fuenf Handelstagen innerhalb dieser Spanne".
Das ist die erste widerlegbare Aussage dieses Systems - und eine widerlegbare
Aussage, die niemand nachrechnet, ist wieder nur eine Behauptung.

⚠️ DIE GESAMTQUOTE IST KEIN TEST. Die Faktoren in trichter.FAKTOR wurden auf
GENAU DIESEN Reihen kalibriert. Dass sie darauf passen, ist keine Leistung,
sondern Arithmetik - ein Quantil trifft sein eigenes Quantil. Wer diese Zahl
als Bestaetigung liest, hat sich selbst geprueft.

DER TEST IST DER WALK-FORWARD: den Faktor NUR aus der Vergangenheit
bestimmen und auf der Zeit danach messen, die er nicht gesehen hat. Genau so
laeuft er auch im Betrieb.

⚠️ UND DIE ANKERZAHL LUEGT. Taegliche Anker mit 20-Tage-Horizont ueberlappen
sich 19-fach; 30.000 Anker sind keine 30.000 unabhaengigen Faelle. Die
wirksame Zahl ist rund n/Horizont, und nur mit ihr darf man rechnen, ob eine
Abweichung ueberhaupt etwas bedeutet. Sonst wird jede Schwankung "hoch
signifikant".

DER KNIFF: gemessen wird nicht "getroffen ja/nein", sondern das VERHAELTNIS
|Schlussaenderung| / (ATR x sqrt(t)). Daraus laesst sich jede Trefferquote zu
jedem Faktor ohne Neuberechnung ablesen - und der kalibrierte Faktor ist
einfach das Quantil derselben Zahlen.

    python messe_trichter_treffer.py [--db ...] [--bloecke 4] [--schnell]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")
from agent import trichter as TR                              # noqa: E402


def _klassen() -> dict:
    """Symbol -> Anlageklasse. AN DER QUELLE, nicht geraten."""
    import config as C
    return {x.symbol: str(getattr(x, "assetklasse", "") or "?").lower()
            for x in C.get_watchlist()}

# Ab wann ist eine Abweichung ein Befund und nicht Rauschen? Drei
# Standardfehler auf der WIRKSAMEN Ankerzahl, mindestens aber drei
# Prozentpunkte - unter drei Punkten lohnt keine Aufregung.
MINDEST_ABWEICHUNG_PP = 3.0
SIGMA = 3.0


def _atr_reihe(h, l, c, fenster: int = 14) -> np.ndarray:
    tr = np.maximum(h[1:] - l[1:],
                    np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    return np.array([tr[max(0, i - fenster + 1):i + 1].mean()
                     for i in range(fenster - 1, len(tr))])


def sammle(db: str, schnell: bool) -> dict:
    """Je Horizont eine Liste (Jahr, Verhaeltnis). MEHR BRAUCHT ES NICHT."""
    from backtest_llm1_historisch import lade_reihen_aus_db

    aus: dict[int, list] = {hz: [] for hz in TR.HORIZONTE}
    reihen = 0
    for _sym, kerzen in lade_reihen_aus_db(db).items():
        # ⚠️ HILFSREIHEN GEHOEREN NICHT IN DIE KALIBRIERUNG (19.08.2026).
        #
        # _THEMEN_ETF_BENCHMARK_SPY und die drei _ROHSTOFF_FUTURES sind
        # interne Vergleichsreihen - fuer sie entsteht nie eine Mail, also
        # darf ihr Verhalten den Trichter nicht mitbestimmen. Sie reichen
        # aber bis 2001 zurueck und stellten damit die HAELFTE aller Anker.
        # Der erste ausgelieferte Faktor 0,98 ist auf ihnen mitgewachsen.
        if _sym.startswith("_"):
            continue
        if len(kerzen) < 200:
            continue
        if schnell:
            kerzen = kerzen[-500:]
        c = np.array([float(x.close) for x in kerzen])
        h = np.array([float(x.high) for x in kerzen])
        l = np.array([float(x.low) for x in kerzen])
        a = _atr_reihe(h, l, c)
        if len(a) < 130:
            continue
        off = len(c) - len(a)
        reihen += 1
        for hz in TR.HORIZONTE:
            wurzel = math.sqrt(hz)
            for i in range(len(a) - hz):
                atr, jetzt = a[i], c[off + i]
                if atr <= 0 or jetzt <= 0:
                    continue
                # DASSELBE VERHAELTNIS, DAS trichter.spanne UMSTELLT.
                aus[hz].append((
                    int(str(kerzen[off + i].date)[:4]),
                    abs(c[off + i + hz] - jetzt) / (atr * wurzel),
                    _sym))
    return {"reihen": reihen, "werte": aus}


def _quote(werte, faktor: float) -> float:
    return float(np.mean(np.asarray(werte) <= faktor)) if len(werte) else 0.0


def _schranke(n: int, hz: int, anteil: float) -> float:
    """Wie weit darf es abweichen, bevor es etwas heisst?

    ⚠️ WIRKSAME ANKERZAHL, NICHT ROHE. Ueberlappende Fenster liefern keine
    unabhaengigen Faelle."""
    n_wirksam = max(1.0, n / float(hz))
    se = math.sqrt(anteil * (1 - anteil) / n_wirksam)
    return max(MINDEST_ABWEICHUNG_PP, SIGMA * 100 * se)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--bloecke", type=int, default=4,
                   help="Zeitbloecke fuer den Walk-Forward")
    p.add_argument("--schnell", action="store_true")
    p.add_argument("--datei", default="messwerte_trichter.json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 76)
    print("HAELT DER TRICHTER? - Trefferquote je Horizont (Fallstrick A2)")
    print("=" * 76)
    d = sammle(a.db, a.schnell)
    print(f"  {d['reihen']} Reihen"
          + ("   [SCHNELL: nur die letzten 500 Kerzen]" if a.schnell else ""))

    bericht = {"stand": TR.STAND, "reihen": d["reihen"], "horizonte": {}}
    auffaellig = []
    anteil = 0.80

    for hz in TR.HORIZONTE:
        paare = d["werte"][hz]
        if not paare:
            continue
        jahre = np.array([x[0] for x in paare])
        v = np.array([x[1] for x in paare])
        syms = np.array([x[2] for x in paare])
        # ⚠️ GEMESSEN WIRD DER FAKTOR, DER AUCH AUSGELIEFERT WIRD.
        #
        # Seit dem 19.08. gilt je Anlageklasse ein eigener Faktor. Die
        # Messung gegen den globalen Rueckfall zu fahren, hiesse etwas zu
        # pruefen, das im Betrieb nicht mehr vorkommt - und genau das ist
        # das Muster, das in diesem Projekt schon zweimal ein Vorzeichen
        # gedreht hat (falsche Basislinie beim Strukturstop).
        _kl0 = _klassen()
        f_zeile = np.array([TR.faktoren(_kl0.get(s))[0][0.80] for s in syms])
        treffer = v <= f_zeile
        n = len(v)
        print("\n" + "-" * 76)
        print(f"HORIZONT {hz} HANDELSTAGE   {n} Anker, wirksam rund "
              f"{n // hz} (Ueberlappung)")
        print("-" * 76)

        # --- 1. IN-SAMPLE: zur Einordnung, NICHT als Beleg ----------------
        print("  auf allen Daten, ausgelieferte Faktoren je Klasse "
              "(IN-SAMPLE - sie stammen von hier):")
        for teil in sorted(TR.FAKTOR):
            fz = np.array([TR.faktoren(_kl0.get(s))[0][teil] for s in syms])
            q = 100 * float(np.mean(v <= fz))
            print(f"    Soll {100 * teil:.0f} %   Ist {q:5.1f} %   "
                  f"Abweichung {q - 100 * teil:+5.1f} pp")

        # --- 2. WALK-FORWARD: der eigentliche Test ------------------------
        jahr_liste = sorted(set(int(x) for x in jahre.tolist()))
        schnitt = max(1, len(jahr_liste) // a.bloecke)
        bloecke = [jahr_liste[i:i + schnitt]
                   for i in range(0, len(jahr_liste), schnitt)][-a.bloecke:]
        print(f"\n  WALK-FORWARD ({len(bloecke)} Bloecke) - Faktor NUR aus "
              f"der Zeit davor, gemessen auf der Zeit danach:")
        print("    Zeitraum        n     Faktor(alt)  Quote(alt)  "
              "Quote(ausgeliefert)")
        for blk in bloecke:
            innen = np.isin(jahre, blk)
            davor = jahre < min(blk)
            if innen.sum() < 60 or davor.sum() < 200:
                print(f"    {min(blk)}-{max(blk)}   zu wenig Historie davor "
                      f"({int(davor.sum())} Anker) - kein Urteil")
                continue
            f_alt = float(np.quantile(v[davor], anteil))
            q_alt = 100 * _quote(v[innen], f_alt)
            q_neu = 100 * float(np.mean(treffer[innen]))
            gr = _schranke(int(innen.sum()), hz, anteil)
            marke = "  <-- ABWEICHUNG" if abs(q_neu - 80.0) > gr else ""
            print(f"    {min(blk)}-{max(blk)}  {int(innen.sum()):>7}"
                  f"      {f_alt:.2f}       {q_alt:5.1f} %      {q_neu:5.1f} %"
                  f"   (Grenze +/-{gr:.1f} pp){marke}")
            if marke:
                auffaellig.append(f"{hz} Tage, {min(blk)}-{max(blk)}: "
                                  f"{q_neu:.1f} % statt 80 %")

        # --- 2b. GEGENPROBE: LIEGT ES AN DER ZEIT ODER AN DER BESETZUNG? ---
        #
        # ⚠️ DIE BLOECKE ENTHALTEN NICHT DIESELBEN REIHEN. 2001 gab es keine
        # Kryptowerte; der aelteste Block besteht aus Aktien und Rohstoffen,
        # der juengste aus allem. Ein Unterschied zwischen den Bloecken kann
        # also die ZUSAMMENSETZUNG sein statt die Zeit - und wer das nicht
        # trennt, kalibriert eine Anlageklasse weg.
        #
        # Deshalb dasselbe noch einmal, aber NUR auf Reihen, die in jedem
        # Block vorkommen. Bleibt der Unterschied, ist er zeitlich.
        gemeinsam = None
        for blk in bloecke:
            hier = set(syms[np.isin(jahre, blk)].tolist())
            gemeinsam = hier if gemeinsam is None else (gemeinsam & hier)
        gemeinsam = gemeinsam or set()
        print(f"\n  GEGENPROBE - nur die {len(gemeinsam)} Reihen, die in "
              f"ALLEN Bloecken vorkommen (Besetzung konstant):")
        if len(gemeinsam) < 2:
            print("    zu wenige durchgehende Reihen - kein Urteil")
        else:
            treu = np.isin(syms, list(gemeinsam))
            for blk in bloecke:
                m = treu & np.isin(jahre, blk)
                if m.sum() < 60:
                    continue
                print(f"    {min(blk)}-{max(blk)}  {int(m.sum()):>7}"
                      f"   Quote {100 * float(np.mean(treffer[m])):5.1f} %")

        # --- 2c. JE ANLAGEKLASSE - DIE FRAGE AUS FALLSTRICK A1 ------------
        #
        # Die Gegenprobe hat gezeigt, dass der Unterschied zwischen den
        # Bloecken an der Besetzung haengt. Dann ist die naechste Frage nicht
        # "wann", sondern "was" - und A1 lautete genau so: ein Faktor fuer
        # alle, oder einer je Klasse?
        print("\n  JE ANLAGEKLASSE (ausgelieferter Faktor gegen den, den die "
              "Klasse selbst verlangt):")
        kl = _klassen()
        klassen = np.array([kl.get(s, "?") for s in syms])
        je_klasse = {}
        for name in sorted(set(klassen.tolist())):
            m = klassen == name
            if m.sum() < 200:
                continue
            eigene = {str(k): round(float(np.quantile(v[m], k)), 2)
                      for k in sorted(TR.FAKTOR)}
            je_klasse[name] = {
                "anker": int(m.sum()), "faktoren": eigene,
                "quote_ausgeliefert": round(
                    100 * float(np.mean(treffer[m])), 1)}
            print(f"    {name:8} {int(m.sum()):>7} Anker  Quote "
                  f"ausgeliefert: "
                  f"{je_klasse[name]['quote_ausgeliefert']:5.1f} %  "
                  f"eigene Faktoren "
                  + " ".join(f"{k}:{x:.2f}" for k, x in eigene.items()))

        # --- 3. ALTERUNG: die Quote je Jahr, ausgeliefertem Faktor --------
        print("\n  ALTERUNG - Quote je Jahr, ausgelieferter Faktor je Klasse "
              "(Soll 80 %):")
        je_jahr = {}
        for j in jahr_liste:
            m = jahre == j
            if m.sum() < 60:
                continue
            je_jahr[int(j)] = round(100 * float(np.mean(treffer[m])), 1)
        zeile = "    " + "  ".join(f"{j}:{q:5.1f}" for j, q in
                                   sorted(je_jahr.items())[-10:])
        print(zeile if je_jahr else "    zu wenige Anker je Jahr")

        bericht["horizonte"][hz] = {
            "anker": n, "wirksam": n // hz,
            # Dieselbe Rechnung wie die gedruckte Tabelle - je Zeile der
            # Faktor ihrer Klasse, nicht der globale Rueckfall.
            "in_sample": {
                str(k): round(100 * float(np.mean(v <= np.array(
                    [TR.faktoren(_kl0.get(s))[0][k] for s in syms]))), 1)
                for k in sorted(TR.FAKTOR)},
            "je_jahr": je_jahr,
            "durchgehende_reihen": len(gemeinsam),
            "je_klasse": je_klasse}

    print("\n" + "=" * 76)
    if auffaellig:
        print("DER TRICHTER TRAEGT NICHT UEBERALL:")
        for z in auffaellig:
            print(f"   {z}")
        print("\n   Zu tun: die Faktoren in agent/trichter.FAKTOR neu "
              "kalibrieren - und die neue Ankerzahl im Docstring, in der "
              "Mailzeile und in ANKER_GEMESSEN mitziehen.")
    else:
        print("Der Trichter traegt: keine Abweichung ueber der Rauschgrenze.")
    print("=" * 76)

    bericht["auffaellig"] = auffaellig
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(
            json.dumps(bericht, ensure_ascii=False, indent=1))
        print(f"  geschrieben: {a.datei}")
    return 2 if auffaellig else 0


if __name__ == "__main__":
    raise SystemExit(main())
