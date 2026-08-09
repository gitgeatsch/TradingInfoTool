"""Wie stabil ist der Anbieter bei IDENTISCHER Eingabe? (2026-08-09)

WOZU, und warum VOR dem langen Lauf (Nutzer-Vorgabe 09.08.): *"lies nach, dein
eigener Befund sagte dass Gemini und Openrouter eher instabil sind - gegenueber
Mistral das sollten wir bedenken bzw. kurz pruefen vor dem Lauf."*

DER DOKUMENTIERTE BEFUND, den diese Datei nachmisst: `nemotron-3-super-120b`
lieferte am 08.08. bei zwei identischen Laeufen **4 Richtungsdreher von 34 =
~12 %**. Der Rauschpegel produzierte damit MEHR Dreher als der eigentliche
Formatvergleich (3 von 36). Fuer Gemini ist die RICHTUNGSSTABILITAET ungemessen
- dort ist nur bekannt, dass es am EROEFFNEN-Waechter scheiterte (Quote 76 % ->
61 % unter striktem Schema, weshalb Gemini `json_object` behaelt).

WARUM DAS ueber den Lauf ENTSCHEIDET, nicht nur ihn begleitet. Ein Effekt, der
kleiner ist als die Streuung bei identischer Eingabe, ist nicht nachweisbar -
egal wie viele Anker man nachlegt. Diese Messung sagt VORHER, welche
Effektgroesse ueberhaupt erreichbar ist, und welcher Anbieter das mit weniger
Aufrufen schafft.

WAS GEMESSEN WIRD, je Anker mehrfach mit BITGLEICHER Eingabe:

    Richtungsdreher   Anteil der Wiederholungen, die von der Mehrheitsrichtung
                      desselben Ankers abweichen
    Konfidenz         Streuung in Punkten (Standardabweichung je Anker)
    Hebel-Vorschlag   Streuung - Regel 2 verlangt hier eine Daempfung, also
                      muss die Groesse ueberhaupt stabil genug dafuer sein
    Selbsteinschaetzung  wie oft weicht `folgen` von der Mehrheit ab
    Dauer             der zweite Entscheidungsgrund: Gemini ist ~6x schneller

FAIRNESS ZWISCHEN DEN ANBIETERN, ausdruecklich: jeder bekommt das
Antwortformat, das fuer ihn ENTSCHIEDEN wurde (OpenRouter striktes
`json_schema`, Gemini `json_object`) - nicht dasselbe. Ein Vergleich unter
gleichem Format waere kein Vergleich der Betriebsbedingungen, sondern ein
Laborvergleich, den wir nie fahren wuerden.

LESEART. Wer weniger dreht UND schneller ist, traegt den Lauf. Bei Gleichstand
gewinnt die Stabilitaet, nicht die Geschwindigkeit - ein schneller Lauf mit
unlesbarem Ergebnis ist der teuerste.

    python pruefe_llm_stabilitaet.py --anker 3 --wiederholungen 5
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter

from backtest_llm1_historisch import baue_historische_fakten, lade_reihen
import messe_regimephasen_llm as M


def _kennwerte(antworten: list[dict]) -> dict:
    """Streuung EINES Ankers ueber seine Wiederholungen."""
    richtungen = [a.get("richtung") for a in antworten if a.get("richtung")]
    konf = [a["confidence_pct"] for a in antworten
            if isinstance(a.get("confidence_pct"), (int, float))]
    heb = [a["hebel_vorschlag"] for a in antworten
           if isinstance(a.get("hebel_vorschlag"), (int, float))]
    fazit = [(a.get("eigene_einschaetzung") or {}).get("folgen")
             for a in antworten]
    fazit = [f for f in fazit if f]
    def abweichung(werte):
        if not werte:
            return None
        mehrheit = Counter(werte).most_common(1)[0][0]
        return sum(1 for w in werte if w != mehrheit) / len(werte)
    return {
        "n": len(antworten),
        "richtungs_abweichung": abweichung(richtungen),
        "fazit_abweichung": abweichung(fazit),
        "konfidenz_streuung": statistics.stdev(konf) if len(konf) > 1 else None,
        "konfidenz_spanne": (max(konf) - min(konf)) if len(konf) > 1 else None,
        "hebel_streuung": statistics.stdev(heb) if len(heb) > 1 else None,
        "richtungen": dict(Counter(richtungen)),
        "fazit": dict(Counter(fazit)),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anker", type=int, default=3)
    p.add_argument("--wiederholungen", type=int, default=5)
    p.add_argument("--anbieter", default="openrouter,gemini")
    p.add_argument("--pause", type=float, default=0.5)
    p.add_argument("--ausgabe", default="llm_stabilitaet.json")
    args = p.parse_args()

    import os

    import config as config_module
    from agent import llm_schema
    from agent.krypto.hebel_analyst import SYSTEM_PROMPT, _validate_hebel
    config_module.load_env()

    reihen = lade_reihen()
    btc = reihen["BTC"]
    fest = M.stabile_tage(M.btc_phasen(btc))
    je_phase = M.waehle_anker(reihen, fest, args.anker, 3)
    # REIHUM ueber die Phasen, nicht eine nach der anderen: sonst misst man die
    # Stabilitaet in genau einer Marktlage und uebertraegt sie stillschweigend
    # auf die anderen. Und die Ankerzahl ist hier die knappe Groesse - der
    # dokumentierte 12-%-Befund stammt aus 34 PAAREN; bei drei Ankern ist
    # "null Dreher" mit ~15 % Wahrscheinlichkeit reiner Zufall und widerlegt
    # gar nichts.
    anker = []
    for runde in range(max(len(je_phase[p]) for p in M.ARME) or 1):
        for phase in M.ARME:
            if runde < len(je_phase[phase]) and len(anker) < args.anker:
                sym, i = je_phase[phase][runde]
                anker.append((phase, M.LABEL[phase], sym, i))
    print(f"Anker: " + ", ".join(f"{p}/{s}@{reihen[s][i].date}"
                                for p, _, s, i in anker))
    print(f"Wiederholungen je Anker: {args.wiederholungen}")

    klienten = {}
    if "openrouter" in args.anbieter:
        from api.openrouter import OpenRouterClient
        k = OpenRouterClient(os.environ["OPENROUTER_API_KEY"])
        klienten["openrouter"] = (
            k, llm_schema.response_format_fuer(k, "agent.krypto.hebel_analyst"))
    if "gemini" in args.anbieter:
        from api.gemini import GeminiClient
        k = GeminiClient(os.environ["GEMINI_API_KEY"])
        klienten["gemini"] = (
            k, llm_schema.response_format_fuer(k, "agent.krypto.hebel_analyst"))
    for name, (_, fmt) in klienten.items():
        print(f"  {name:12} Antwortformat {fmt.get('type')}")
    print(f"  -> {len(anker) * args.wiederholungen * len(klienten)} Aufrufe\n")

    ergebnis: dict[str, dict] = {}
    roh: dict[str, dict] = {}
    for name, (klient, fmt) in klienten.items():
        print(f"=== {name}")
        je_anker, dauern, fehler = {}, [], Counter()
        for phase, label, sym, i in anker:
            fakten = baue_historische_fakten(sym, reihen[sym], i, btc)
            fakten["regime"] = dict(fakten["regime"])
            fakten["regime"]["wert"] = label
            nutzlast = json.dumps(fakten, ensure_ascii=False)
            antworten = []
            for w in range(args.wiederholungen):
                time.sleep(args.pause)
                beginn = time.time()
                try:
                    txt = klient.chat(
                        [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": nutzlast}],
                        temperature=0.2, response_format=fmt)
                    antworten.append(_validate_hebel(json.loads(txt), sym))
                    dauern.append(time.time() - beginn)
                except Exception as exc:  # noqa: BLE001
                    fehler[type(exc).__name__] += 1
            k = _kennwerte(antworten)
            je_anker[f"{phase}/{sym}"] = k
            def f(x, s="{:5.1%}"):
                return s.format(x) if x is not None else "    -"
            print(f"  {phase:11} {sym:8} gueltig {k['n']}/{args.wiederholungen}  "
                  f"Richtungsdreher {f(k['richtungs_abweichung'])}  "
                  f"Fazit-Dreher {f(k['fazit_abweichung'])}  "
                  f"Konf-Streuung {f(k['konfidenz_streuung'], '{:5.2f}')}  "
                  f"{k['richtungen']}")
        gueltig = sum(v["n"] for v in je_anker.values())
        drehe = [v["richtungs_abweichung"] for v in je_anker.values()
                 if v["richtungs_abweichung"] is not None]
        streu = [v["konfidenz_streuung"] for v in je_anker.values()
                 if v["konfidenz_streuung"] is not None]
        ergebnis[name] = {
            "gueltig": gueltig,
            "versuche": len(anker) * args.wiederholungen,
            "richtungsdreher_mittel": statistics.fmean(drehe) if drehe else None,
            "konfidenz_streuung_mittel": statistics.fmean(streu) if streu else None,
            "dauer_median": statistics.median(dauern) if dauern else None,
            "fehler": dict(fehler),
        }
        roh[name] = je_anker
        e = ergebnis[name]
        print(f"  ZUSAMMEN  gueltig {gueltig}/{e['versuche']}  "
              f"Richtungsdreher {(e['richtungsdreher_mittel'] or 0):5.1%}  "
              f"Konf-Streuung {(e['konfidenz_streuung_mittel'] or 0):5.2f}  "
              f"Median {(e['dauer_median'] or 0):5.1f} s"
              + (f"  Fehler {dict(fehler)}" if fehler else ""))
        print()

    print("=" * 76)
    print("VERGLEICH - wer traegt den langen Lauf?")
    print(f"{'Anbieter':12} {'gueltig':>9} {'Dreher':>8} {'Konf-Streu':>11} "
          f"{'Dauer':>8}  Referenz: nemotron 08.08. = 12 % Dreher")
    for name, e in ergebnis.items():
        print(f"{name:12} {e['gueltig']:4}/{e['versuche']:<4} "
              f"{(e['richtungsdreher_mittel'] or 0):7.1%} "
              f"{(e['konfidenz_streuung_mittel'] or 0):11.2f} "
              f"{(e['dauer_median'] or 0):7.1f} s")
    print()
    print("WAS DARAUS FOLGT fuer die Effektgroesse: ein Konfidenz-Effekt muss")
    print("groesser sein als die obige Streuung, sonst ist er nicht lesbar.")
    print("Ein Richtungseffekt muss ueber der Dreherquote liegen.")
    if len(ergebnis) > 1:
        # `x or 1` war hier falsch: in Python ist 0.0 FALSY, also wurde
        # ausgerechnet der beste Wert - null Richtungsdreher - zu 1 und damit
        # zum schlechtesten. Das Skript kuerte deshalb den instabileren
        # Anbieter zum Sieger. Gefunden am 09.08. beim Gegenlesen des
        # Ergebnisses, nicht vom Test - ein Urteil, das man nicht nachrechnet,
        # ist eine Behauptung.
        def _schluessel(eintrag):
            dreher = eintrag[1]["richtungsdreher_mittel"]
            dauer = eintrag[1]["dauer_median"]
            return (1.0 if dreher is None else dreher,
                    999.0 if dauer is None else dauer)

        best = min(ergebnis.items(), key=_schluessel)
        print(f"\nSTABILER: {best[0]} - bei Gleichstand entscheidet die")
        print("Stabilitaet, nicht die Geschwindigkeit.")
        print("VORBEHALT: die Anbieter laufen mit VERSCHIEDENEM Antwortformat")
        print("(so, wie sie auch im Betrieb liefen). Der Vergleich misst die")
        print("Betriebsbedingung, nicht das Modell im Labor.")

    import pathlib
    pathlib.Path(args.ausgabe).write_text(
        json.dumps({"zusammen": ergebnis, "je_anker": roh},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nGeschrieben: {args.ausgabe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
