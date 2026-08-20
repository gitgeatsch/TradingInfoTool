"""Wo steht ein Betrag mit Waehrung - und stimmt sie? (20.08.2026)

DER ANLASS. Eine echte Mail vom 20.08. zeigte ETH bei 1.931,49 EUR und
darunter "Stop auf 2.025,02 EUR nachziehen" - einen Stop UEBER dem
Marktpreis. Wer ihn so eintraegt, verkauft sofort. Die Rechnung war richtig,
die Waehrung nicht: 2.025,02 war USD, in EUR sind es 1.735.

Der Nutzer dazu: *"das EUR-USD-Umrechnen war immer schon punktuell ein
Problem - vielleicht kannst du das Thema nochmal breit pruefen, damit wir
nicht mehrere Stellen hin und her aendern."*

⚠️ DIE WURZEL IST EINE NAMENSKONVENTION OHNE DURCHSETZUNG.

Die Waehrung steckt im FELDNAMEN (`stop_eur`, `einstieg_eur`, `risiko_eur`),
und nichts prueft, ob der Inhalt dazu passt. Bei ETH enthaelt `risiko_eur`
den Wert 308,98 - das ist USD. Der Name luegt, und niemand merkt es, weil
keine Zeile Code den Namen mit dem Inhalt vergleicht.

WAS DIESES WERKZEUG TUT. Es durchsucht den Quelltext nach Stellen, die einen
Betrag MIT Waehrungsangabe ausgeben, und beantwortet je Stelle:

    UMGERECHNET   der Wert laeuft durch eine Umrechnung
    NATIV         das Feld heisst `_eur` UND die Quelle liefert EUR
    ROH           weder noch - hier steht moeglicherweise die falsche Waehrung
    UNKLAR        nicht mechanisch entscheidbar, gehoert angesehen

⚠️ ES ENTSCHEIDET NICHTS. Ob ein Feld wirklich EUR enthaelt, steht nicht im
Quelltext - das muss ein Mensch an der Quelle nachsehen. Dieses Werkzeug
sorgt nur dafuer, dass keine Stelle uebersehen wird.

    python pruefe_waehrungen.py [--alle]
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys

# Was als Umrechnung gilt. Wer eine weitere Funktion baut, traegt sie hier
# ein - sonst meldet das Werkzeug ihre Aufrufstellen als ROH, und das ist
# die richtige Richtung des Irrtums.
UMRECHNER = ("_in_eur", "in_eur", "eur_je_usd", "_zu_eur", "umgerechnet",
             "* fx", "fx_rate", "_eur_kurs")

# Ordner, die nicht zaehlen: Messwerkzeuge und Pruefskripte geben Zahlen fuer
# den Entwickler aus, nicht fuer den Nutzer.
AUS = ("pruefe_", "messe_", "teste_", "backtest_", "erhebe_", "baue_",
       "simuliere_", "lade_", "extract_", "__pycache__", ".git")

# Eine Zeile, die einen Betrag mit Waehrung ausgibt.
MUSTER = re.compile(r"(EUR|USD)")


def _dateien(nur_agent: bool) -> list[str]:
    aus = []
    for wurzel in (["agent", "ui", "api", "scheduler", "database", "remote"]
                   if not nur_agent else ["agent"]):
        for pfad, _dirs, dateien in os.walk(wurzel):
            if any(a in pfad for a in AUS):
                continue
            for d in dateien:
                if d.endswith(".py") and not any(d.startswith(a) for a in AUS):
                    aus.append(os.path.join(pfad, d))
    return sorted(aus)


def _zuweisungen(baum) -> dict:
    """name -> Ausdruck, je Funktion. FUER EINE EBENE AUFLOESEN.

    ⚠️ OHNE DAS NUR FEHLALARME. `ui/portfolio.py` schreibt
    `preis = format_money(cost_basis.effective_avg_price_eur)` und gibt dann
    `{preis} EUR` aus. Wer nur den f-String ansieht, meldet eine rohe Zahl,
    wo eine saubere steht - und ein Werkzeug mit Fehlalarmen wird nach dem
    dritten nicht mehr aufgerufen."""
    aus = {}
    for k in ast.walk(baum):
        if isinstance(k, ast.Assign):
            for ziel in k.targets:
                if isinstance(ziel, ast.Name):
                    try:
                        aus[ziel.id] = ast.unparse(k.value)
                    except Exception:                        # noqa: BLE001
                        pass
    return aus


def _zerlege(quelle: str, pfad: str) -> list[dict]:
    """Alle f-Strings mit Waehrungsangabe - MIT ihren eingesetzten Werten.

    ⚠️ UEBER DEN SYNTAXBAUM, NICHT UEBER TEXTSUCHE. Ein `grep` findet die
    Waehrung auch in Kommentaren und Docstrings, und genau daran ist eine
    fruehere Pruefung dieses Projekts gescheitert (Methodik 2.41)."""
    try:
        baum = ast.parse(quelle)
    except SyntaxError:
        return []
    namen = _zuweisungen(baum)
    aus = []
    for knoten in ast.walk(baum):
        if not isinstance(knoten, ast.JoinedStr):
            continue
        text = "".join(t.value for t in knoten.values
                       if isinstance(t, ast.Constant)
                       and isinstance(t.value, str))
        if not MUSTER.search(text):
            continue
        # Die eingesetzten Ausdruecke im Klartext - daran haengt das Urteil.
        werte = []
        for t in knoten.values:
            if not isinstance(t, ast.FormattedValue):
                continue
            w = ast.unparse(t.value)
            # Ein blosser Name wird EINMAL aufgeloest - mehr nicht. Zwei
            # Ebenen waeren schon eine Datenflussanalyse, und die gehoert
            # nicht in ein Pruefskript.
            werte.append(namen.get(w, w) if w.isidentifier() else w)
        aus.append({"datei": pfad, "zeile": knoten.lineno,
                    "text": text.strip()[:70], "werte": werte,
                    "waehrung": "EUR" if "EUR" in text else "USD"})
    return aus


def beurteile(eintrag: dict) -> str:
    """UMGERECHNET / NATIV / ROH / OHNE_BETRAG."""
    werte = " ".join(eintrag["werte"])
    if not werte.strip():
        return "OHNE_BETRAG"
    if any(u in werte for u in UMRECHNER):
        return "UMGERECHNET"
    # Ein Feldname auf `_eur` ist eine BEHAUPTUNG, keine Umrechnung. Er zaehlt
    # hier trotzdem als eigene Klasse, weil er der haeufigste Fall ist - und
    # weil genau er sich als unzuverlaessig erwiesen hat (risiko_eur = USD).
    # ⚠️ KEINE WORTGRENZE NACH "_eur" (korrigiert 20.08.2026). Die erste
    # Fassung suchte `_eur\b` und uebersah damit `entry_eur_von` - dort folgt
    # auf "eur" ein Unterstrich, und der ist ein Wortzeichen. Vier von fuenf
    # Fehlalarmen kamen daher.
    if "_eur" in werte and eintrag["waehrung"] == "EUR":
        return "NATIV"
    if "usd" in werte.lower() and eintrag["waehrung"] == "USD":
        return "NATIV"
    # Zahlen ohne Feldbezug (Summen, Deckel aus der Konfiguration) sind
    # keine Kursumrechnung - sie kommen als EUR herein.
    if not re.search(r"\b(kurs|preis|stop|einstieg|ziel|entry|hoch|tief)",
                     werte, re.I):
        return "OHNE_BETRAG"
    return "ROH"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--alle", action="store_true",
                   help="auch UMGERECHNET und OHNE_BETRAG zeigen")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("WAEHRUNGSANGABEN IM QUELLTEXT - wo steht ein Betrag mit EUR/USD?")
    print("=" * 78)
    alle = []
    for pfad in _dateien(False):
        try:
            quelle = io.open(pfad, encoding="utf-8").read()
        except OSError:
            continue
        for e in _zerlege(quelle, pfad):
            e["urteil"] = beurteile(e)
            alle.append(e)

    zaehl: dict[str, int] = {}
    for e in alle:
        zaehl[e["urteil"]] = zaehl.get(e["urteil"], 0) + 1
    print(f"  {len(alle)} Stellen mit Waehrungsangabe in "
          f"{len({e['datei'] for e in alle})} Dateien")
    for k in ("UMGERECHNET", "NATIV", "ROH", "OHNE_BETRAG"):
        print(f"    {k:14} {zaehl.get(k, 0):4}")

    for urteil in (("ROH", "NATIV") if not a.alle
                   else ("ROH", "NATIV", "UMGERECHNET", "OHNE_BETRAG")):
        teil = [e for e in alle if e["urteil"] == urteil]
        if not teil:
            continue
        print("\n" + "-" * 78)
        print(f"{urteil} ({len(teil)})")
        if urteil == "ROH":
            print("  ⚠️ Hier steht ein Kursbetrag mit Waehrungsetikett, ohne "
                  "dass eine Umrechnung erkennbar waere.")
        if urteil == "NATIV":
            print("  Der Feldname behauptet die Waehrung. Das ist eine "
                  "Behauptung, keine Pruefung - siehe risiko_eur (= USD).")
        print("-" * 78)
        for e in sorted(teil, key=lambda x: (x["datei"], x["zeile"])):
            print(f"  {e['datei']}:{e['zeile']}  [{e['waehrung']}]")
            print(f"      {e['text']}")
            print(f"      Werte: {', '.join(e['werte'])[:120]}")

    print("\n" + "=" * 78)
    roh = zaehl.get("ROH", 0)
    if roh:
        print(f"{roh} Stelle(n) OHNE erkennbare Umrechnung - jede einzeln "
              f"an der Quelle pruefen.")
    else:
        print("Keine Stelle ohne erkennbare Umrechnung.")
    print("=" * 78)
    return 0 if not roh else 2


if __name__ == "__main__":
    raise SystemExit(main())
