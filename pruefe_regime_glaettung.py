"""Gegenpruefung der Regime-Glaettung und des Divergenz-Fakts (2026-08-06).

Prueft die vier Dinge, die schiefgehen koennen, und zwar einzeln:

  A) RECHNET DIE GLAETTUNG RICHTIG - Stuetzstellen, Stetigkeit, Monotonie,
     Randfaelle.
  B) AENDERT SICH HEUTE WIRKLICH NICHTS - die Kalibrierungszusage ist keine
     Absichtserklaerung, sondern pruefbar: bei ganzzahliger Konfidenz muss der
     stetige Wert exakt dieselben Signale durchlassen wie die harte 75.
  C) IST DER FAKT KORREKT VERDRAHTET - Feld vorhanden, Einordnung passend zur
     Zahl, keine Ausnahme bei fehlenden Daten.
  D) IST DIE REGEL SAUBER - Nummer frei, Fakt namentlich erwaehnt, und der
     Hedging-Schutz vorhanden (die Regel MUSS explizit sagen, dass eine
     Divergenz kein Grund fuer pauschale Vorsicht ist - sonst laeuft sie in
     denselben Mechanismus, der die EROEFFNEN-Quote von 93 % auf 3 % gedrueckt
     hat).

Kein Produktivlauf, keine LLM-Aufrufe, keine Produktiv-DB.
"""
from __future__ import annotations

import io
import json
import sys

fehler: list[str] = []


def pruefe(bedingung: bool, text: str) -> None:
    print(f"  [{'ok' if bedingung else '!!'}] {text}")
    if not bedingung:
        fehler.append(text)


def main() -> int:
    from agent.krypto.regime import (
        _SCORE_STUETZSTELLEN, btc_ema50_einordnung, min_konfidenz_stetig,
        regime_score,
    )

    print("=" * 84)
    print("A) RECHNET DIE GLAETTUNG RICHTIG?")
    print("=" * 84)
    for score, soll in _SCORE_STUETZSTELLEN:
        ist = min_konfidenz_stetig(score)
        pruefe(ist == soll, f"Stuetzstelle {score:.2f} -> {ist} (soll {soll})")

    werte = [min_konfidenz_stetig(s / 100) for s in range(0, 101)]
    monoton = all(a >= b for a, b in zip(werte, werte[1:]))
    pruefe(monoton, "monoton fallend ueber den gesamten Score-Bereich")
    spruenge = [abs(a - b) for a, b in zip(werte, werte[1:])]
    pruefe(max(spruenge) < 0.6,
           f"keine Klippe - groesster Schritt je 1 % Score: {max(spruenge):.2f} pp")
    pruefe(min_konfidenz_stetig(-1) == _SCORE_STUETZSTELLEN[0][1]
           and min_konfidenz_stetig(2) == _SCORE_STUETZSTELLEN[-1][1],
           "ausserhalb [0,1] sauber geklemmt")
    pruefe(min_konfidenz_stetig(None) is None, "None -> None (kein Ersatzwert)")
    pruefe(regime_score(None, 100, 200, 25) is None
           and regime_score(100, None, 200, 25) is None
           and regime_score(100, 0, 200, 25) is None
           and regime_score(100, 100, 200, None) is None,
           "regime_score gibt bei fehlender Eingabe None statt zu raten")

    print()
    print("=" * 84)
    print("B) AENDERT SICH HEUTE WIRKLICH NICHTS?")
    print("=" * 84)
    pfad = (r'K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten'
            r'\notebook_diagnose.json')
    d = json.load(io.open(pfad, encoding="utf-8"))
    reihe = sorted([r for r in d["preishistorie_signal_symbole"]
                    ["preishistorie_je_symbol"]["BTC"] if r["currency"] == "USD"],
                   key=lambda r: r["date"])
    c = [r["close"] for r in reihe]

    def ema(v, n):
        k = 2 / (n + 1)
        e = v[0]
        for x in v[1:]:
            e = x * k + e * (1 - k)
        return e

    kurs, e50, e200 = c[-1], ema(c[-50:], 50), ema(c, 200)
    mh = sorted(d["rohdaten_fuer_backtest"]["macro_historie"], key=lambda r: r["date"])
    fg = [r["fear_greed_value"] for r in mh if r.get("fear_greed_value")][-1]
    score = regime_score(kurs, e50, e200, fg)
    stetig = min_konfidenz_stetig(score)
    print(f"  heutiger Zustand: BTC {kurs:.0f}, EMA50 {e50:.0f}, F&G {fg}")
    print(f"  Score {score:.3f} -> stetige Schwelle {stetig}  (hart: 75)")

    konf = [s["confidence_pct"] for s in d["spot_signals"] + d["hebel_signals"]
            if isinstance(s.get("confidence_pct"), (int, float))]
    ganzzahlig = all(float(x) == int(x) for x in konf)
    pruefe(ganzzahlig, f"alle {len(konf)} Konfidenzwerte ganzzahlig")
    hart = {i for i, x in enumerate(konf) if x >= 75}
    weich = {i for i, x in enumerate(konf) if x >= stetig}
    pruefe(hart == weich,
           f"identische Filterwirkung: {len(hart)} gegen {len(weich)} durchgelassen")
    pruefe(abs(stetig - 75.0) < 1.0,
           f"stetiger Wert bleibt binnen 1 pp der harten Schwelle ({stetig})")

    print()
    print("  Szenario halb erholt (Kurs ueber EMA50, Stimmung weiter aengstlich):")
    for auf in (0.0, 0.03, 0.06):
        s2 = regime_score(e50 * (1 + auf), e50, e200, fg)
        print(f"    BTC {auf*100:+.0f} % zur EMA50 -> Schwelle "
              f"{min_konfidenz_stetig(s2):.1f}  (heute hart: 75,0)")

    print()
    print("=" * 84)
    print("C) IST DER FAKT KORREKT VERDRAHTET?")
    print("=" * 84)
    for zahl, erwartet in ((-8.0, "deutlich darunter"), (-3.0, "darunter"),
                           (-0.5, "knapp darunter"), (0.5, "knapp darueber"),
                           (3.0, "darueber"), (8.0, "deutlich darueber")):
        pruefe(btc_ema50_einordnung(zahl) == erwartet,
               f"Einordnung {zahl:+.1f} % -> {btc_ema50_einordnung(zahl)}")
    pruefe(btc_ema50_einordnung(None) is None, "Einordnung None -> None")
    verboten = {"unklar", "uebergang", "unbekannt", "unsicher"}
    alle = {btc_ema50_einordnung(v) for v in (-9, -3, -0.5, 0.5, 3, 9)}
    pruefe(not (alle & verboten),
           f"keine Mehrdeutigkeits-Bezeichnung unter {sorted(alle)}")

    for modul in ("agent.krypto.hebel_analyst", "agent.krypto.analyst"):
        m = __import__(modul, fromlist=["build_facts"])
        quelle = io.open(m.__file__.replace(".pyc", ".py"), encoding="utf-8").read()
        pruefe('"btc_zu_ema50"' in quelle, f"{modul}: Fakt btc_zu_ema50 vorhanden")
        pruefe("btc_ema50_einordnung(" in quelle, f"{modul}: Einordnung verdrahtet")

    print()
    print("=" * 84)
    print("D) IST DIE REGEL SAUBER?")
    print("=" * 84)
    for modul, nr in (("agent.krypto.hebel_analyst", 33), ("agent.krypto.analyst", 37)):
        m = __import__(modul, fromlist=["SYSTEM_PROMPT"])
        p = [v for k, v in vars(m).items()
             if k.endswith("SYSTEM_PROMPT") and isinstance(v, str)][0]
        pruefe(f"{nr}. Regime-Divergenz" in p, f"{modul}: Regel {nr} vorhanden")
        pruefe(p.count(f"\n{nr}. ") == 1, f"{modul}: Regelnummer {nr} eindeutig")
        pruefe("`regime.btc_zu_ema50`" in p, f"{modul}: Fakt namentlich genannt")
        pruefe("KEINE unklare" in p, f"{modul}: Divergenz bejahend benannt")
        pruefe("pauschale Vorsicht" in p,
               f"{modul}: HEDGING-SCHUTZ vorhanden (kein Grund fuer pauschale Vorsicht)")
        pruefe("weniger" in p and "vorzuschlagen" in p,
               f"{modul}: ausdruecklicher Schutz gegen 'weniger vorschlagen'")
        pruefe("SCHEMA:" in p, f"{modul}: SCHEMA-Block intakt")

    print()
    print("=" * 84)
    print(f"ERGEBNIS: {len(fehler)} Fehler")
    for f in fehler:
        print(f"  - {f}")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
