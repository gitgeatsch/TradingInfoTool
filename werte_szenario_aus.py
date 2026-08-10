"""Was der Brier-Score NICHT sagt - Zerlegung und Kalibrierung.

WOZU. Ein Brier-Score von 0,68 gegen eine Basisrate von 0,63 sagt "schlechter",
aber nicht WORAN es liegt. Dafuer gibt es die Zerlegung nach Murphy (1973), den
Standard der Prognosebewertung:

    Brier = Unsicherheit - Aufloesung + Verlaesslichkeit

  UNSICHERHEIT   wie schwer die Aufgabe an sich ist. Haengt nur an der
                 Ausgangsverteilung, nicht am Schaetzer - fuer alle
                 Verfahren identisch, deshalb kein Verdienst und kein Vorwurf.
  AUFLOESUNG     unterscheidet der Schaetzer die Faelle ueberhaupt? Wer immer
                 dasselbe sagt, hat Aufloesung 0. GROSS ist gut, sie wird
                 abgezogen.
  VERLAESSLICHKEIT  stimmen die genannten Wahrscheinlichkeiten? Wer "70 %"
                 sagt, sollte in 70 % der Faelle recht behalten. KLEIN ist gut.

DIE UNTERSCHEIDUNG IST ENTSCHEIDEND fuer die Frage, was als Naechstes zu tun
ist:

  Aufloesung ~ 0        Das Modell nennt fast immer dieselbe Verteilung. Es
                        hat nichts ueber den Einzelfall zu sagen - dann fehlt
                        INFORMATION, und mehr Prompt-Arbeit ist vergeblich.
  Aufloesung gross,     Das Modell unterscheidet Faelle, liegt aber daneben.
  Verlaesslichkeit      Dann ist Kalibrierung moeglich - die Ausschlaege sind
  gross                 da, sie zeigen nur in die falsche Richtung oder sind
                        zu stark. Das ist reparierbar.

Ein Schaetzer, der die Basisrate nur knapp verfehlt, kann also in zwei
voellig verschiedenen Zustaenden sein - und die Konsequenz ist jedes Mal eine
andere. Genau deshalb reicht die eine Zahl nicht.

    python werte_szenario_aus.py --datei szenario_stufe1.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
from collections import defaultdict

SCHLUESSEL = ("ziel_zuerst_pct", "stop_zuerst_pct", "keines_pct")
AUSGAENGE = ("ziel", "stop", "keines")


def zerlege(verteilungen, wahrheiten, klassen: int = 10) -> dict | None:
    """Murphy-Zerlegung, gemittelt ueber die drei Ausgaenge.

    Die Wahrscheinlichkeiten werden in `klassen` Faecher gruppiert; je Fach
    wird verglichen, wie oft das Ereignis tatsaechlich eintrat. Zu grobe
    Faecher verwischen die Aussage, zu feine lassen je Fach zu wenige Faelle -
    zehn ist der uebliche Kompromiss."""
    paare = [(v, w) for v, w in zip(verteilungen, wahrheiten) if v and w]
    if len(paare) < 20:
        return None
    n = len(paare)
    aus = {"n": n}
    unsicherheit = aufloesung = verlaesslichkeit = 0.0
    for ausgang, schluessel in zip(AUSGAENGE, SCHLUESSEL):
        basis = sum(1 for _, w in paare if w == ausgang) / n
        unsicherheit += basis * (1 - basis)
        faecher = defaultdict(list)
        for v, w in paare:
            p = float(v[schluessel]) / 100.0
            faecher[min(int(p * klassen), klassen - 1)].append((p, 1.0 if w == ausgang else 0.0))
        for eintraege in faecher.values():
            k = len(eintraege)
            p_mittel = statistics.fmean(p for p, _ in eintraege)
            o_mittel = statistics.fmean(o for _, o in eintraege)
            verlaesslichkeit += k / n * (p_mittel - o_mittel) ** 2
            aufloesung += k / n * (o_mittel - basis) ** 2
    aus.update(unsicherheit=round(unsicherheit, 4),
               aufloesung=round(aufloesung, 4),
               verlaesslichkeit=round(verlaesslichkeit, 4))
    return aus


def streuung(verteilungen) -> dict:
    """Wie stark weichen die Verteilungen voneinander ab?

    Ein Schaetzer, der immer dasselbe sagt, hat Streuung nahe null - und dann
    ist die Aufloesung zwangslaeufig auch null. Die beiden Masse pruefen sich
    gegenseitig."""
    gueltig = [v for v in verteilungen if v]
    if len(gueltig) < 2:
        return {}
    return {s: round(statistics.pstdev([float(v[s]) for v in gueltig]), 1)
            for s in SCHLUESSEL}


def wirtschaftlich(eintraege, wahrheiten, kosten_r: float) -> dict:
    """Was die Empfehlungsregel TATSAECHLICH eingebracht haette.

    WARUM DAS NEBEN DEM BRIER-SCORE STEHT. Beide Masse koennen sich
    widersprechen, und beide Richtungen kommen vor:

      * Gut kalibriert, wirtschaftlich nutzlos - der Schaetzer trifft, kommt
        aber nie ueber die Handlungsschwelle. Nichts zu handeln ist korrekt
        und bringt null.
      * Schlecht kalibriert, wirtschaftlich brauchbar - er liegt im Mittel
        daneben, aber die wenigen Faelle, in denen er stark wird, sind die
        richtigen.

    Der Brier-Score misst die Schaetzung, diese Rechnung misst die
    ENTSCHEIDUNG. Nur letztere entscheidet ueber den Rollout."""
    from agent.szenario_entscheidung import leite_empfehlung_ab, realisiertes_r

    gehandelt, summe, gesperrt = 0, 0.0, 0
    for e, w in zip(eintraege, wahrheiten):
        if not e.get("verteilung"):
            continue
        emp = leite_empfehlung_ab(e["verteilung"], kosten_r=kosten_r,
                                  unsicherheit=e.get("unsicherheit"))
        if e.get("unsicherheit") in ("hoch",):
            gesperrt += 1
        if not emp["handeln"]:
            continue
        r = realisiertes_r(w)
        if r is None:
            continue
        gehandelt += 1
        summe += r - abs(kosten_r)
    return {"trades": gehandelt, "summe_r": round(summe, 2),
            "je_trade": round(summe / gehandelt, 3) if gehandelt else None,
            "gesperrt": gesperrt}


def bootstrap_je_trade(eintraege, wahrheiten, symbole, kosten_r: float,
                       runden: int = 2000, seed: int = 20260810) -> tuple | None:
    """Streubereich des R je Trade - CLUSTER-Bootstrap ueber Symbole.

    WARUM UEBER SYMBOLE UND NICHT UEBER FAELLE. Je Symbol stecken mehrere
    Anker in der Stichprobe, und die haengen zusammen: dasselbe Symbol in
    derselben Marktphase liefert aehnliche Fakten und aehnliche Ausgaenge. Wer
    einzelne Faelle zieht, tut so, als waeren es unabhaengige Beobachtungen,
    und bekommt ein zu enges Intervall - er haelt Zufall fuer Befund.

    Gezogen werden deshalb ganze Symbole mit allen ihren Faellen."""
    import random
    from agent.szenario_entscheidung import leite_empfehlung_ab, realisiertes_r

    je_symbol = defaultdict(list)
    for e, w, s in zip(eintraege, wahrheiten, symbole):
        if not e.get("verteilung"):
            continue
        emp = leite_empfehlung_ab(e["verteilung"], kosten_r=kosten_r,
                                  unsicherheit=e.get("unsicherheit"))
        r = realisiertes_r(w)
        if emp["handeln"] and r is not None:
            je_symbol[s].append(r - abs(kosten_r))
        else:
            je_symbol.setdefault(s, [])
    schluessel = list(je_symbol)
    if len(schluessel) < 3:
        return None
    rng = random.Random(seed)
    werte = []
    for _ in range(runden):
        gezogen = [r for k in rng.choices(schluessel, k=len(schluessel))
                   for r in je_symbol[k]]
        if gezogen:
            werte.append(statistics.fmean(gezogen))
    if len(werte) < runden // 2:
        return None
    werte.sort()
    return (werte[int(0.025 * len(werte))], werte[int(0.975 * len(werte))],
            len(schluessel))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datei", required=True)
    p.add_argument("--kosten-r", type=float, default=0.0,
                   help="Handelskosten je Trade in R (Standard 0 = brutto)")
    args = p.parse_args()
    d = json.loads(pathlib.Path(args.datei).read_text(encoding="utf-8"))
    wahrheiten = [f["wahrheit"] for f in d["faelle"]]

    print(f"{len(wahrheiten)} Faelle")
    print(f"Ausgangsverteilung: "
          + ", ".join(f"{a}={sum(1 for w in wahrheiten if w == a)}" for a in AUSGAENGE))
    print("\n" + "=" * 82)
    print(f"{'Verfahren':26} {'Brier':>8} {'Unsich.':>8} {'Aufloes.':>9} "
          f"{'Verlaess.':>10} {'Rest':>7} {'Streu.':>7}")
    print("-" * 82)
    for name, eintraege in d["ergebnisse"].items():
        w = [e["brier"] for e in eintraege if e.get("brier") is not None]
        if not w:
            continue
        vert = [e.get("verteilung") for e in eintraege]
        z = zerlege(vert, wahrheiten)
        st = streuung(vert)
        b = statistics.fmean(w)
        # KONTROLLE: Brier = Unsicherheit - Aufloesung + Verlaesslichkeit gilt
        # exakt nur ohne Fachbildung. Innerhalb eines Fachs streuen die
        # genannten Wahrscheinlichkeiten noch, und dieser Anteil taucht in
        # keinem der drei Glieder auf - er ist der Rest. Ein KLEINER Rest ist
        # normal und ein gutes Zeichen; ein grosser hiesse, die Faecher sind
        # zu grob und die Zerlegung waere nicht mehr aussagekraeftig.
        rest = (b - (z["unsicherheit"] - z["aufloesung"]
                     + z["verlaesslichkeit"])) if z else None
        print(f"{name:26} {b:8.4f} "
              + (f"{z['unsicherheit']:8.4f} {z['aufloesung']:9.4f} "
                 f"{z['verlaesslichkeit']:10.4f} {rest:+7.4f} "
                 if z else f"{'-':>8} {'-':>9} {'-':>10} {'-':>7} ")
              + f"{st.get('ziel_zuerst_pct', 0):7.1f}")

    print("\n" + "=" * 82)
    print(f"WIRTSCHAFTLICH (Kosten {args.kosten_r:.3f} R je Trade)")
    print(f"{'Verfahren':26} {'Trades':>8} {'Summe R':>9} {'je Trade':>10} "
          f"{'95 % Bereich je Trade':>24}")
    print("-" * 82)
    symbole = [f["symbol"] for f in d["faelle"]]
    for name, eintraege in d["ergebnisse"].items():
        b = wirtschaftlich(eintraege, wahrheiten, args.kosten_r)
        je = f"{b['je_trade']:+.3f}" if b["je_trade"] is not None else "-"
        bs = bootstrap_je_trade(eintraege, wahrheiten, symbole, args.kosten_r)
        bereich = (f"[{bs[0]:+.3f} .. {bs[1]:+.3f}]" if bs else "-")
        print(f"{name:26} {b['trades']:8d} {b['summe_r']:+9.2f} {je:>10} "
              f"{bereich:>24}")

    # GEGENPROBE: haette man JEDEN Fall gehandelt, muss sich die Summe direkt
    # aus der Ausgangsverteilung ergeben. Weicht die Rechnung davon ab, ist
    # nicht das Modell schlecht, sondern die Auswertung kaputt.
    from agent.szenario_entscheidung import realisiertes_r
    alle = [realisiertes_r(w) for w in wahrheiten]
    soll = sum(r - abs(args.kosten_r) for r in alle if r is not None)
    print("-" * 82)
    print(f"{'ALLE Faelle gehandelt':26} {len(alle):8d} {soll:+9.2f} "
          f"{soll / len(alle):+10.3f} {0:10d}   <- Gegenprobe")
    print("  Ein Verfahren ist nur dann etwas wert, wenn es je Trade BESSER")
    print("  liegt als diese Zeile - sonst waehlt es die Faelle nicht aus,")
    print("  sondern verkleinert sie nur.")

    # --- Die Deadloop-Frage -------------------------------------------------
    # Seit Wochen liefert das System keine handelbaren LONG-Signale. Bisher war
    # das nicht sauber zu trennen: das Modell WAEHLTE die Richtung, also war
    # jede Schieflage zugleich Ursache und Wirkung. Hier ist die Richtung
    # VORGEGEBEN und beide Seiten stehen auf denselben Ankern mit derselben
    # Zonengeometrie - ein LONG- und ein SHORT-Aufbau je Anker, gleich schwer
    # gebaut. Damit ist der Vergleich zum ersten Mal fair.
    richtungen = [f["richtung"] for f in d["faelle"]]
    if len(set(richtungen)) > 1:
        print("\n" + "=" * 82)
        print("NACH RICHTUNG - dieselben Anker, dieselbe Zonengeometrie")
        print(f"{'Verfahren':22} {'LONG Brier':>11} {'p(ziel) LONG':>13} "
              f"{'SHORT Brier':>12} {'p(ziel) SHORT':>14}")
        print("-" * 82)
        for name, eintraege in d["ergebnisse"].items():
            zeile = [name]
            for r in ("LONG", "SHORT"):
                w = [e["brier"] for e, x in zip(eintraege, richtungen)
                     if x == r and e.get("brier") is not None]
                p = [float(e["verteilung"]["ziel_zuerst_pct"])
                     for e, x in zip(eintraege, richtungen)
                     if x == r and e.get("verteilung")]
                zeile.append(f"{statistics.fmean(w):.4f}" if w else "-")
                zeile.append(f"{statistics.fmean(p):.1f} %" if p else "-")
            print(f"{zeile[0]:22} {zeile[1]:>11} {zeile[2]:>13} "
                  f"{zeile[3]:>12} {zeile[4]:>14}")
        for r in ("LONG", "SHORT"):
            tat = [w for w, x in zip(wahrheiten, richtungen) if x == r]
            traf = sum(1 for w in tat if w == "ziel")
            print(f"  TATSAECHLICH {r:5}: Ziel zuerst in {traf} von {len(tat)} "
                  f"Faellen ({100.0 * traf / len(tat):.1f} %)")
        print("  Sagt ein Verfahren fuer LONG deutlich weniger p(ziel) als")
        print("  die tatsaechliche Quote hergibt, unterdrueckt es LONG - und")
        print("  zwar unabhaengig vom Gate, das hier gar nicht mitspielt.")

    print("\n=== LESART ===")
    print("  Aufloesung nahe 0  -> der Schaetzer sagt fast immer dasselbe. Ihm")
    print("                        fehlt INFORMATION ueber den Einzelfall;")
    print("                        weitere Prompt-Arbeit ist vergeblich.")
    print("  Aufloesung gross,  -> er unterscheidet Faelle, liegt aber daneben.")
    print("  Verlaesslichkeit      Das ist KALIBRIERBAR - die Ausschlaege sind")
    print("  gross                 da, sie zeigen nur falsch.")
    print("  Streuung nahe 0    -> Gegenprobe zur Aufloesung: wer immer")
    print("                        dieselbe Zahl nennt, kann nicht aufloesen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
