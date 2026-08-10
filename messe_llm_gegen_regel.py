"""Die Nullmessung: schlaegt das LLM eine deterministische Regel?

WARUM DIESE MESSUNG DIE ERSTE HAETTE SEIN MUESSEN (Nutzer, 10.08.: *"das kommt
aber spaet dafuer dass wir Wochen damit beschaeftigt sind"* - berechtigt).

Wir haben wochenlang die DARSTELLUNG der Fakten optimiert (Format, Bezugsgroessen,
Schrumpfung, Breakeven-Bezug) und gegen den ZUFALL gemessen. Der Zufall ist ein
wertloser Massstab - eine triviale Regel schlaegt ihn auch. Die Frage, die
zaehlt, lautet:

    Traegt das Sprachmodell etwas bei, das eine Regel auf DENSELBEN Fakten
    nicht auch hinbekommt?

Faellt die Antwort negativ aus, ist weitere Prompt-Arbeit vergeblich - dann
muss das LLM entweder neue Information bekommen (Text, den keine Regel
verwerten kann) oder die Rolle wechseln (Widerspruchspruefung, Regelanwendung,
Begruendung statt Richtungsentscheidung).

DAS MESSPROBLEM UND SEINE LOESUNG. Das gespeicherte Handelsergebnis
(take_profit/stop_loss) haengt an der Richtung, die das LLM gewaehlt hat, samt
seiner Zonen. Haette die Regel die Gegenrichtung gesagt, verraet dieses Feld
nicht, wie es ausgegangen waere - ein direkter Vergleich waere ein
Scheinvergleich.

Deshalb wird gegen die TATSAECHLICHE MARKTBEWEGUNG geprueft, nicht gegen das
Handelsergebnis. `max_realisiertes_crv` ist relativ zur Primaerrichtung; daraus
folgt die tatsaechliche Richtung, und gegen die laesst sich JEDE
Kandidatenrichtung messen. Exakt derselbe Massstab, den
`bewerte_zai_richtung()` seit dem 27.07. fuer Z.ai verwendet - bewusst nicht
neu erfunden, damit zwei Messungen dieselbe Sprache sprechen.

DIE REGELN sind absichtlich primitiv. Es geht nicht darum, eine gute Regel zu
finden, sondern um die Untergrenze: was bekommt man OHNE Sprachmodell aus
denselben Zahlen?

    python messe_llm_gegen_regel.py
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict

VORGABE_DB = ("C:/Users/Geatsch/AppData/Local/Temp/claude/"
              "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
              "9e774fdd-5a46-48f6-9d20-e6614cad35af/scratchpad/prod_kopie.db")


# ---------------------------------------------------------------- die Regeln
def regel_konfluenz(f: dict) -> str | None:
    """Mehrheit der technischen Indikatoren. Die naheliegendste Regel ueberhaupt."""
    k = ((f.get("technische_analyse") or {}).get("confluence") or {})
    b, s = k.get("bullish"), k.get("bearish")
    if b is None or s is None:
        return None
    return "LONG" if b > s else "SHORT" if s > b else None


def regel_rsi(f: dict) -> str | None:
    """Mittelwertrueckkehr: ueberverkauft -> LONG, ueberkauft -> SHORT."""
    r = (f.get("technische_analyse") or {}).get("rsi_14")
    if r is None:
        return None
    return "LONG" if r < 40 else "SHORT" if r > 60 else None


def regel_ema(f: dict) -> str | None:
    """Trendfolge ueber die EMA-Ordnung: Kurs ueber EMA-200 -> LONG."""
    ta = f.get("technische_analyse") or {}
    preis = (f.get("preis") or {}).get("usd")
    ema = (ta.get("ema") or {}).get("200")
    if preis is None or ema is None:
        return None
    return "LONG" if preis > ema else "SHORT"


def regel_immer_short(f: dict) -> str:
    """Die Nullhypothese des Baerenmarktes: immer SHORT.

    Nicht als Vorschlag gemeint. Sie steht hier, weil das Regime ueber den
    gesamten Zeitraum konstant "baer" war - schlaegt das LLM nicht einmal
    DIESE Regel, ist seine Richtungswahl ohne jeden Wert."""
    return "SHORT"


REGELN = {
    "Konfluenz-Mehrheit": regel_konfluenz,
    "RSI 40/60": regel_rsi,
    "Kurs vs EMA-200": regel_ema,
    "immer SHORT": regel_immer_short,
}


def tatsaechliche_richtung(reihe, datum: str, atr_anteil: float | None,
                           horizont: int) -> str | None:
    """Wohin lief der Kurs wirklich - OHNE Bezug auf irgendeine Empfehlung.

    HIER STAND EIN ZIRKELSCHLUSS (10.08., selbst gefunden). Die erste Fassung
    leitete die "tatsaechliche Richtung" aus `primaer_richtung` und dem MFE ab.
    Das MFE ist aber die maximale GUENSTIGE Auslenkung, also bereits relativ
    zur gewaehlten Richtung gemessen und fast immer positiv - die Wahrheit
    ergab sich damit fast immer als genau die Richtung, die das LLM genommen
    hatte. Ergebnis: 98,6 % Trefferquote. Das Modell wurde gegen sich selbst
    geprueft.

    Fuer `bewerte_zai_richtung()` ist dieser Massstab richtig, weil dort eine
    DRITTE Richtung dagegen gehalten wird. Fuer die Primaerrichtung selbst ist
    er unbrauchbar. Ich hatte das Werkzeug wiederverwendet, ohne zu pruefen,
    ob seine Voraussetzung noch gilt.

    Jetzt: der Kurs selbst. Vom Signaltag `horizont` Kerzen weiter, Bewegung
    in Vielfachen des ATR gemessen (nicht in Prozent - ein Prozent bedeutet
    bei BTC etwas anderes als bei einem Kleinstwert). Bleibt die Bewegung
    unter einem ATR, gilt sie als unentschieden und der Fall zaehlt nicht."""
    idx = None
    for i in range(len(reihe) - 1, -1, -1):
        if reihe[i].date <= datum:
            idx = i
            break
    if idx is None or idx + horizont >= len(reihe):
        return None
    ein = reihe[idx].close
    aus = reihe[idx + horizont].close
    if not ein:
        return None
    bewegung = (aus - ein) / ein
    schwelle = atr_anteil if atr_anteil and atr_anteil > 0 else 0.02
    if bewegung >= schwelle:
        return "LONG"
    if bewegung <= -schwelle:
        return "SHORT"
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=VORGABE_DB)
    p.add_argument("--aktionen", default="EROEFFNEN",
                   help="welche Aktionen zaehlen; 'alle' nimmt auch HALTEN")
    p.add_argument("--horizont", type=int, default=7,
                   help="Kerzen nach dem Signal (7 = wie die CRV-Baender)")
    args = p.parse_args()

    c = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    # NUR ECHTE RICHTUNGSENTSCHEIDUNGEN (Korrektur 10.08.). Von 1.905
    # Signalen sind 1.668 HALTEN - dort ist `richtung` kein Votum, sondern
    # Kontext: das Modell hat sich ausdruecklich GEGEN einen Trade
    # entschieden. Seine "Richtungswahl" daran zu messen, misst etwas, das es
    # nicht getroffen hat.
    zeilen = c.execute(
        "SELECT symbol, richtung, action, created_at, facts_json "
        "FROM hebel_signals "
        "WHERE facts_json IS NOT NULL AND richtung IN ('LONG','SHORT')"
    ).fetchall()
    if args.aktionen != "alle":
        vorher_n = len(zeilen)
        zeilen = [z for z in zeilen
                  if (z["action"] or "").upper().replace("Ö", "OE") == args.aktionen]
        print(f"Nur Aktion {args.aktionen}: {len(zeilen)} von {vorher_n} Signalen")
    c.close()
    from backtest_llm1_historisch import lade_reihen
    reihen = lade_reihen()
    print(f"Kursreihen: {len(reihen)} Symbole, Horizont {args.horizont} Kerzen")

    treffer: dict[str, Counter] = defaultdict(Counter)
    je_symbol: dict[str, Counter] = defaultdict(Counter)
    ohne_bewegung = 0
    bewertet = 0

    ohne_reihe = 0
    for z in zeilen:
        reihe = reihen.get(z["symbol"])
        if not reihe:
            ohne_reihe += 1
            continue
        try:
            f = json.loads(z["facts_json"])
        except (ValueError, TypeError):
            continue
        atr = (f.get("technische_analyse") or {}).get("atr") or {}
        atr_anteil = atr.get("relativ_prozent")
        atr_anteil = atr_anteil / 100.0 if atr_anteil else None
        echt = tatsaechliche_richtung(reihe, (z["created_at"] or "")[:10],
                                      atr_anteil, args.horizont)
        if echt is None:
            ohne_bewegung += 1
            continue
        bewertet += 1
        # Das LLM
        treffer["LLM (Primaermodell)"]["treffer" if z["richtung"] == echt
                                       else "fehl"] += 1
        je_symbol[z["symbol"]]["llm_t" if z["richtung"] == echt else "llm_f"] += 1
        # Die Regeln
        for name, fn in REGELN.items():
            r = fn(f)
            if r is None:
                treffer[name]["enthaltung"] += 1
                continue
            treffer[name]["treffer" if r == echt else "fehl"] += 1

    print(f"\nSignale mit Fakten und Richtung: {len(zeilen)}")
    print(f"  ohne Kursreihe: {ohne_reihe}")
    print(f"  ohne klare Bewegung (unter 1 ATR in {args.horizont} Kerzen): {ohne_bewegung}")
    print(f"  BEWERTET: {bewertet}")
    if bewertet < 30:
        print("\n  [WARNUNG] unter 30 Faellen - keine belastbare Aussage.")

    print("\n" + "=" * 74)
    print(f"{'Verfahren':26} {'Treffer':>8} {'Fehl':>7} {'Enthalt.':>9} {'Quote':>8}")
    print("-" * 74)
    reihenfolge = ["LLM (Primaermodell)"] + list(REGELN)
    quoten = {}
    for name in reihenfolge:
        t, fe = treffer[name]["treffer"], treffer[name]["fehl"]
        ent = treffer[name]["enthaltung"]
        q = 100.0 * t / (t + fe) if (t + fe) else None
        quoten[name] = (q, t + fe)
        print(f"{name:26} {t:8d} {fe:7d} {ent:9d} "
              + (f"{q:7.1f} %" if q is not None else "      -"))

    print("\n=== URTEIL ===")
    llm_q, llm_n = quoten["LLM (Primaermodell)"]
    beste = max((k for k in REGELN if quoten[k][0] is not None),
                key=lambda k: quoten[k][0], default=None)
    if llm_q is None or beste is None:
        print("  Nicht entscheidbar.")
        return 0
    rq, rn = quoten[beste]
    print(f"  LLM {llm_q:.1f} % (n={llm_n})  gegen beste Regel "
          f"'{beste}' {rq:.1f} % (n={rn})")
    # Zweiseitiger Test auf Anteilsgleichheit, ohne Zusatzpakete.
    from math import comb
    if llm_q > rq:
        print(f"  -> Das LLM liegt {llm_q - rq:+.1f} pp VOR der besten "
              f"einfachen Regel.")
    else:
        print(f"  -> Das LLM liegt {llm_q - rq:+.1f} pp HINTER der besten "
              f"einfachen Regel. Auf denselben Fakten traegt es damit nichts "
              f"bei, was diese Regel nicht auch hinbekommt.")
    print("\n  ZUR EINORDNUNG, ehrlich: 'immer SHORT' ist keine Strategie, "
          "sondern die Nullhypothese eines durchgehenden Baerenmarktes. "
          "Schlaegt das LLM sie nicht, sagt das mehr ueber den Zeitraum als "
          "ueber das Modell - aber es heisst auch, dass seine Richtungswahl "
          "in genau diesem Zeitraum keinen Beitrag geleistet hat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
