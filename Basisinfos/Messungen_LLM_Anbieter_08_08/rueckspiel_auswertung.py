"""Auswertung des Ruecktests auf der GEMEINSAMEN Fallmenge.

WARUM NICHT DIE ZAHLEN AUS DEM LAUF: Gemini kassierte 10 HTTP-Fehler und ist
nur auf 28 von 38 Faellen ausgewertet, nemotron auf 38, laguna auf 36. Eine
R-Summe ueber unterschiedlich viele Faelle ist NICHT vergleichbar - wer weniger
Faelle beantwortet, sammelt mechanisch weniger Minus. Genau so entstehen
Scheinbefunde.

Deshalb: Schnittmenge bilden, alles darauf neu rechnen. Zusaetzlich die eine
Kennzahl, die der Lauf nicht ausgibt und die die HALTEN-Quote entschaerft:
TREFFERQUOTE UNTER DEN GENOMMENEN. Ein Modell, das 75 % ablehnt, sieht bei
35 Verlierern gegen 3 Gewinner automatisch gut aus - die Frage ist, ob das
Genommene besser ist als der Durchschnitt.
"""
import pathlib
import re

log = (pathlib.Path(__file__).parent / "rueckspiel.log").read_text(
    encoding="utf-8", errors="replace")

modelle, aktuell = {}, None
for zeile in log.splitlines():
    m = re.match(r"^--- (\S+)", zeile)
    if m:
        aktuell = m.group(1)
        modelle[aktuell] = {}
        continue
    if aktuell is None:
        continue
    t = re.match(r"\s*(\d+)\.\s+(\S+)\s+.*?ist\s+([-+][\d.]+) R\s+->\s+(NIMMT|meidet)", zeile)
    if t:
        modelle[aktuell][int(t.group(1))] = {
            "symbol": t.group(2), "crv": float(t.group(3)),
            "nimmt": t.group(4) == "NIMMT"}

gemeinsam = set.intersection(*(set(v) for v in modelle.values()))
print(f"Faelle je Modell: " + ", ".join(f"{k}={len(v)}" for k, v in modelle.items()))
print(f"GEMEINSAME Fallmenge: {len(gemeinsam)}\n")

crv = {i: next(v[i]["crv"] for v in modelle.values() if i in v) for i in gemeinsam}
mistral_r = sum(crv.values())
gewinner = {i for i in gemeinsam if crv[i] > 0}
print(f"Auf dieser Menge: Mistral {mistral_r:+.2f} R "
      f"({len(gemeinsam)-len(gewinner)} Verlierer, {len(gewinner)} Gewinner)\n")

print(f'{"Modell":<22}{"R-Summe":>9}{"genommen":>10}{"HALTEN":>8}'
      f'{"Treffer|genommen":>18}{"Gewinner erwischt":>19}')
for name, faelle in modelle.items():
    genommen = [i for i in gemeinsam if faelle[i]["nimmt"]]
    r = sum(crv[i] for i in genommen)
    tref = [i for i in genommen if crv[i] > 0]
    quote = f"{len(tref)}/{len(genommen)}" + (
        f" = {len(tref)/len(genommen):.0%}" if genommen else "")
    print(f"{name:<22}{r:>+9.2f}{len(genommen):>10}"
          f"{1-len(genommen)/len(gemeinsam):>7.0%}{quote:>18}"
          f"{len(tref)}/{len(gewinner):>18}")

print(f"\n{'Basislinie: alles nehmen':<22}{mistral_r:>+9.2f}{len(gemeinsam):>10}"
      f"{0:>7.0%}{f'{len(gewinner)}/{len(gemeinsam)} = {len(gewinner)/len(gemeinsam):.0%}':>18}")
print(f"{'Basislinie: nichts nehmen':<22}{0.0:>+9.2f}{0:>10}{1:>7.0%}{'-':>18}")
print("\nLESEHILFE: 'Treffer|genommen' ueber der Basislinie heisst, das Modell")
print("waehlt besser als der Zufall. Gleich oder darunter heisst, die bessere")
print("R-Summe kommt NUR aus der hoeheren Ablehnungsquote - das ist kein Urteil,")
print("sondern Zurueckhaltung.")
