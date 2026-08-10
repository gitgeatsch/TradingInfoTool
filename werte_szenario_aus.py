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


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datei", required=True)
    args = p.parse_args()
    d = json.loads(pathlib.Path(args.datei).read_text(encoding="utf-8"))
    wahrheiten = [f["wahrheit"] for f in d["faelle"]]

    print(f"{len(wahrheiten)} Faelle")
    print(f"Ausgangsverteilung: "
          + ", ".join(f"{a}={sum(1 for w in wahrheiten if w == a)}" for a in AUSGAENGE))
    print("\n" + "=" * 82)
    print(f"{'Verfahren':26} {'Brier':>8} {'Unsich.':>8} {'Aufloes.':>9} "
          f"{'Verlaess.':>10} {'Streuung ziel':>14}")
    print("-" * 82)
    for name, eintraege in d["ergebnisse"].items():
        w = [e["brier"] for e in eintraege if e.get("brier") is not None]
        if not w:
            continue
        vert = [e.get("verteilung") for e in eintraege]
        z = zerlege(vert, wahrheiten)
        st = streuung(vert)
        print(f"{name:26} {statistics.fmean(w):8.4f} "
              + (f"{z['unsicherheit']:8.4f} {z['aufloesung']:9.4f} "
                 f"{z['verlaesslichkeit']:10.4f} " if z else f"{'-':>8} {'-':>9} {'-':>10} ")
              + f"{st.get('ziel_zuerst_pct', 0):14.1f}")

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
