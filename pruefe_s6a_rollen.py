# -*- coding: utf-8 -*-
"""Gegenpruefung S6a ueber ALLE Rollen und ihre Abhaengigkeiten.

⚠️ WOZU. S6a aendert die FRAGE an das Modell. Eine geaenderte Frage kann an
vier Stellen scheitern, und drei davon merkt man erst im Betrieb:

    1  Prompt und Schema sagen Verschiedenes  -> Antwort scheitert am Schema
    2  der Validator kennt das Vokabular nicht -> Signal wird verworfen
    3  eine ANDERE Rolle liest die Aktion      -> stiller Fehlschluss
    4  die Datenbank kennt den Wert nicht      -> Schreibfehler im Betrieb

Geprueft werden ALLE Rollen, nicht nur die geaenderte.
"""
import sys

sys.path.insert(0, ".")
ok = fehl = 0


def p(name, bedingung, detail=""):
    global ok, fehl
    print(f"  {'OK  ' if bedingung else 'FEHL'}  {name}"
          + (f"   [{detail}]" if not bedingung and detail else ""))
    if bedingung:
        ok += 1
    else:
        fehl += 1


from agent import empfehlung_vertrag as EV                    # noqa: E402
from agent import llm_schema as LS                            # noqa: E402
from agent import rolle_trader as RT                          # noqa: E402
from agent import signal_abbildung as SA                      # noqa: E402

print("=" * 74)
print("1) ROLLE BC (Trader) - die geaenderte Rolle")
print("=" * 74)
for instr in ("spot", "hebel"):
    pr = RT.prompt_fuer(instr, "einstieg")
    sch = LS.baue_trader_schema(RT, instr)
    props = sch.get("properties", sch)
    enum = set(props["aktion"]["enum"])
    p(f"{instr}: Schema-Enum = AKTIONEN", enum == set(EV.AKTIONEN),
      f"{sorted(enum)}")
    p(f"{instr}: jede Schema-Aktion steht im Prompt",
      all(a in pr for a in enum),
      f"fehlt: {[a for a in enum if a not in pr]}")
    p(f"{instr}: keine ALTE Aktion mehr im Prompt",
      not any(a in pr for a in ("HEBEL_ERHÖHEN", "HEBEL_SENKEN",
                                "TEILVERKAUF", "SCHLIESSEN")),
      "sonst nennt der Prompt etwas, das das Schema verbietet")
    p(f"{instr}: Richtungsfeld in Schema UND Vorlage",
      "richtung" in props and '"richtung"' in pr)
p("beide Prompts sind woertlich gleich",
  RT.prompt_fuer("spot", "einstieg") == RT.prompt_fuer("hebel", "einstieg"))

print("\n" + "=" * 74)
print("2) DER VALIDATOR - nimmt er jede Schema-Aktion an?")
print("=" * 74)
basis = {"begruendung": "x", "was_dagegen": "y", "umgeworfen_durch": "z"}
for instr in ("spot", "hebel"):
    for a in EV.AKTIONEN:
        e = dict(basis, aktion=a)
        if a in EV.HEBEL_MIT_EINSTIEG:
            e["richtung"] = "LONG"
        if a in EV.BRAUCHT_BETRAG:
            e["tranche_eur"] = 300
        try:
            r = EV.validiere(dict(e), "X", instrument=instr)
            gut = r.get("aktion") in EV.AKTIONEN
        except Exception as exc:                              # noqa: BLE001
            gut, r = False, str(exc)
        p(f"{instr}/{a} wird angenommen", gut, str(r)[:80])

print("\n" + "=" * 74)
print("3) DIE DATENBANK - erreicht jede Aktion die Spalte?")
print("=" * 74)
for a in EV.AKTIONEN:
    p(f"{a} -> {SA.UMBENENNUNG.get(a, a)}",
      SA.UMBENENNUNG.get(a, a) in SA.AKTIONEN)
p("und die ALTEN Namen bleiben lesbar",
  set(EV.AKTION_AUS_HEBEL.values()) <= set(EV.AKTIONEN))

print("\n" + "=" * 74)
print("4) DIE ANDEREN ROLLEN - liest jemand die Aktion?")
print("=" * 74)
import io                                                     # noqa: E402
import subprocess                                             # noqa: E402

quellen = [f for f in subprocess.run(
    ["git", "ls-files", "agent/*.py", "agent/**/*.py"],
    capture_output=True, text=True, encoding="utf-8").stdout.split()]
treffer = {}
for f in quellen:
    if "hebel_" in f or "budget_allocator" in f:
        continue                      # alte Kette, laeuft fuer Krypto nicht
    try:
        s = io.open(f, encoding="utf-8").read()
    except Exception:                                         # noqa: BLE001
        continue
    for alt in ("ERÖFFNEN", "TEILVERKAUF", "SCHLIESSEN", "HEBEL_ERHÖHEN",
                "HEBEL_SENKEN"):
        if alt in s:
            treffer.setdefault(f, []).append(alt)
print("  Dateien der NEUEN Kette, die alte Aktionsnamen nennen:")
for f, a in sorted(treffer.items()):
    print(f"     {f:44}{', '.join(sorted(set(a)))}")
print("  (Kommentare und Abbildungen sind erlaubt - Vergleiche nicht.)")

print("\n" + "=" * 74)
print("5) ROLLE A (Lagebild), G (Gegenpruefung) - beruehrt S6a sie?")
print("=" * 74)
for modul, rolle in (("agent/rolle_lagebild.py", "A Lagebild"),
                     ("agent/krypto/gegenpruefung.py", "G Gegenpruefung"),
                     ("agent/rolle_befund.py", "B Befund")):
    try:
        s = io.open(modul, encoding="utf-8").read()
    except Exception:
        print(f"  {rolle:20} Datei nicht gefunden: {modul}")
        continue
    nennt = [a for a in ("ERÖFFNEN", "TEILVERKAUF", "SCHLIESSEN", "HALTEN",
                         "KAUFEN", "NICHTS_TUN") if a in s]
    print(f"  {rolle:20}{modul:38}{', '.join(nennt) or '-'}")

print(f"\n{ok + fehl} Pruefungen, {fehl} fehlgeschlagen")
raise SystemExit(1 if fehl else 0)
