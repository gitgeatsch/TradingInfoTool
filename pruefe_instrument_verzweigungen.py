# -*- coding: utf-8 -*-
"""Jede Verzweigung am `instrument` in der NEUEN Kette - mit Urteil.

⚠️ WOZU. S6b hat den zweiten Lauf entfernt: Krypto laeuft seither NUR mit
`instrument="spot"`. Jede Bedingung der Form `instrument == "hebel"` ist damit
fuer Krypto TOTER CODE - und keine davon wird rot, sie tut einfach nichts mehr.

GEFUNDEN WURDEN SO, EINZELN UND ZU SPAET:

    23.08.  der Cooldown-Topf des Hebel-Laufs (3,5 h) - Produktion stumm
    23.08.  Finanzierungsrate und Liquidationsabstand im Lagebild
    23.08.  ⚠️ `rechne()` rechnet den Hebel aus dem LAUF - seit S6b nie mehr
    23.08.  ⚠️ die `hebel`-Spalte wird nie geschrieben - Topf und Cooldown tot

DIESES WERKZEUG LISTET SIE ALLE, mit ihrem Urteil. Wer eine neue Verzweigung
am Instrument baut, muss sie hier eintragen - sonst faellt die Pruefung durch.
"""
from __future__ import annotations

import ast
import io
import subprocess
import sys

sys.path.insert(0, ".")

# Die Module der NEUEN Kette. Die alten Pipelines duerfen am Instrument
# verzweigen - dort gibt es beide Laeufe noch.
NEUE_KETTE = {
    "rollen_lauf", "rollen_eingabe", "rollen_gate", "rolle_trader",
    "rolle_analyst", "gegenpruefer_rollen", "empfehlung_vertrag",
    "entscheidungsrechnung", "betraege", "toepfe", "assetklassen",
    "lagebeschreibung", "positionierung", "handelsauftrag", "warteschlange",
    "wiederholung", "anlass", "anlass_kalender", "signal_abbildung",
    "signal_mail", "vorfilter", "wahrscheinlichkeit", "asset_schalter",
    "szenario_fakten", "faktenblock", "verkaufsrechnung", "ausstiegsrechnung",
    "marktlage", "mindestkriterien", "llm_schema",
    # ⚠️ NACHGETRAGEN 28.08.2026 - beide fehlten, und beide tragen eine der
    # WICHTIGSTEN Stellen:
    #   positionsfuehrung  liest `hebel_signals` nur bei instrument=="hebel"
    #                      -> sieht seit S6b NIE eine Hebelposition
    #   trefferbilanz      vergibt das Kosten-Tier "hebel" nur dort
    #                      -> rechnet fuer JEDES Krypto-Signal mit dem
    #                         Spot-Tier: 0,60 R statt 0,76 R (-21 %)
    "positionsfuehrung", "trefferbilanz",
}

# ⚠️ JEDE STELLE TRAEGT IHR URTEIL, keinen Haken. `lebt` heisst: sie bekommt
# das ERGEBNIS-Etikett und kann weiterhin "hebel" sehen. `tot` heisst: sie
# bekommt das LAUF-Etikett und ist fuer Krypto seit S6b wirkungslos.
URTEIL = {
    ("handelsauftrag.py", "ist_hebelgeschaeft"): (
        "lebt", "✔ I-1 (28.08.2026): DIE Stelle, die diese Frage beantwortet. "
                "Sie liest zuerst das ERGEBNIS-Etikett und faellt nur ohne "
                "Rechnung auf `instrument` zurueck - das Muster hier ist der "
                "Rueckfall selbst, nicht sein Opfer"),
    # ---- NACHGETRAGEN 28.08.2026, nachdem der Sammler Aliase mitzaehlt ----
    ("asset_schalter.py", "darf_analysiert_werden"): (
        "tot", "⚠️ DER HEBEL-SCHALTER DES NUTZERS HAENGT HIER. `if i == "
               "\"hebel\"` mit `i = str(instrument...)` - seit S6b ist "
               "`instrument` immer \"spot\", die Bedingung trifft NIE zu und "
               "`get_hebel_pruefung_erlaubt` wird nie gefragt. Die GUI zeigt "
               "einen Schalter, der nichts bewirkt - dieselbe Klasse wie die "
               "13 Aktien im DCA-Standard. ✔ I-1b (28.08.2026): der Schalter "
               "wird jetzt in `rollen_lauf._ein_asset` gefragt, sobald das "
               "Etikett feststeht - hier KANN er nicht gefragt werden, weil "
               "diese Funktion VOR der Rechnung laeuft. Die Zeile bleibt fuer "
               "die alten Ketten mit zwei Laeufen"),
    ("handelsauftrag.py", "strategie_fuer"): (
        "lebt", "✔ ABSICHTLICH die Lauf-Frage: `if i != \"spot\"` haelt den "
                "Akkumulations-Schalter von der Hebel-Seite fern. Da es nur "
                "noch den Spot-Lauf gibt, greift er immer - genau so gewollt "
                "(der Kern soll akkumulieren). ⚠️ ABER: die Rechnung kann "
                "daraus `etikett=hebel` machen, und `hebel x akkumulation` "
                "ist ein VERBOTENES Paar, das hier niemand mehr prueft"),
    # ✔ positionsfuehrung.lade STEHT NICHT MEHR HIER (I-3, 28.08.2026):
    #   die Verzweigung ist ersatzlos weg, sie liest jetzt BEIDE Tabellen.
    #   Ein Urteil ohne Fundstelle meldet dieses Werkzeug selbst als Fehler -
    #   genau so soll eine erledigte Stelle verschwinden.
    ("rollen_lauf.py", "_ein_asset"): (
        "lebt", "✔ S6b: `_topf_instrument` folgt dem ERGEBNIS-Etikett, nicht "
                "dem Lauf. Genau die Umstellung, die die uebrigen Stellen "
                "noch brauchen"),
    ("toepfe.py", "belegt_eur"): (
        "lebt", "✔ bekommt `_topf_instrument` aus `_ein_asset` - also das "
                "Etikett, nicht den Lauf"),
    ("trefferbilanz.py", "kosten_r_aus_stop"): (
        "lebt", "✔ I-1a (28.08.2026): das Tier folgt jetzt dem HEBELWERT "
                "(`hebel > 1.0`), den die Funktion ohnehin bekommt. Gemessen: "
                "0,76 R bei Hebel 3 gegen 0,60 R bei Hebel 1. Das verbliebene "
                "`instrument`-Muster ist der Rueckfall fuer Altdaten ohne "
                "Hebelwert. VORHER:  `tier = \"hebel\" if instrument == "
               "\"hebel\"` wird nie wahr - jedes Krypto-Signal rechnet mit dem "
               "Spot-Tier. Bei Stop 5 %, 30 Tagen, Hebel 3: 0,60 R statt "
               "0,76 R, also 21 % zu wenig. Die Kosten fehlen genau dort, wo "
               "gehebelt wird"),
    ("wiederholung.py", "gesperrt_bis"): (
        "lebt", "✔ fragt `INSTRUMENTE_JE_GRUPPE` statt das Instrument: bei "
                "nur einem Lauf faellt der Filter auf `1=1`. S6b-bewusst "
                "gebaut (L4/L5, 28.08.)"),
    ("entscheidungsrechnung.py", "_crv_faktor"): (
        "tot", "bekommt das Lauf-Etikett aus `rechne()` - die CRV-Abstufung "
               "unterscheidet Spot und Hebel seit S6b nicht mehr"),
    ("entscheidungsrechnung.py", "rechne"): (
        "lebt", "✔ A1 (23.08.): fragt jetzt `hebel_handelbar` und leitet das "
                "Etikett aus `hebel_noetig` ab. Das verbliebene "
                "`instrument`-Muster ist der RUECKFALL fuer die alten Ketten, "
                "die beide Laeufe noch haben"),
    ("entscheidungsrechnung.py", "saetze"): (
        "lebt", "liest `e['instrument']` aus der fertigen Rechnung"),
    ("lagebeschreibung.py", "_bestand"): (
        "tot", "der Bestandssatz unterscheidet Spot- und Hebelposition - "
               "harmlos, weil `rollen_lauf` seit S6b BEIDE Bestaende liest"),
    ("positionierung.py", "_melde"): (
        "tot", "unterdrueckte die Luecken-Meldung im Hebel-Lauf; der "
               "Spot-Lauf meldete sie schon immer - unveraendert"),
    ("rollen_eingabe.py", "baue_fall"): (
        "tot", "waehlt die Gegenbestands-Richtung - harmlos, der spot-Zweig "
               "nennt die Hebelposition"),
    ("rollen_eingabe.py", "bestand"): (
        "tot", "las im Hebel-Lauf die Hebelposition. Harmlos, weil "
               "`rollen_lauf` seit S6b BEIDE Bestaende liest und die "
               "Hebelposition Vorrang hat"),
    ("rollen_eingabe.py", "gegenbestand_satz"): (
        "tot", "der Satz 'daneben liegt auch ...' - der spot-Zweig nennt die "
               "Hebelposition, also unveraendert richtig"),
    ("signal_abbildung.py", "felder_aus_entscheidung"): (
        "lebt", "✔ A2 (23.08.): die Spalte folgt dem `etikett` aus der "
                "Rechnung. Das `instrument` bleibt als Rueckfall fuer "
                "Rechnungen ohne Etikett - alte Ketten"),
    ("signal_mail.py", "baue_mail"): (
        "tot", "Betreff und Abschnitt der Mail - kosmetisch, aber falsch, "
               "solange die Rechnung einen Hebel ergeben kann"),
    ("toepfe.py", "sql_bedingung"): (
        "lebt", "bekommt `_topf_instrument`, also das ERGEBNIS"),
    ("toepfe.py", "budget_eur"): (
        "lebt", "bekommt `_topf_instrument`, also das ERGEBNIS"),
    ("warteschlange.py", "_bestaende"): (
        "tot", "Reihenfolge des Bestands - harmlos, beide Zweige liefern "
               "dieselben zwei Groessen, nur vertauscht"),
    ("warteschlange.py", "erklaere"): (
        "tot", "nur Text zur Reihenfolge"),
    ("vorfilter.py", "stand"): (
        "lebt", "kein Zweig, sondern eine GROUP-BY-Spalte im Export - sie "
                "zeigt, fuer welche Gruppe und welchen Lauf der "
                "Vorfilter-Schatten geschrieben wurde"),
}


class Sammler(ast.NodeVisitor):
    def __init__(self) -> None:
        self.funde: list[tuple[int, str]] = []
        self.aliase: set[str] = set()

    def visit_Assign(self, knoten):
        """Merkt sich Namen, die AUS `instrument` abgeleitet werden.

        `i = str(instrument or "").strip().lower()` macht `i` zu einem
        zweiten Namen fuer dieselbe Sache - und jede Bedingung auf `i` ist
        dieselbe Verzweigung."""
        try:
            quelle = ast.unparse(knoten.value)
        except Exception:                                    # noqa: BLE001
            quelle = ""
        if "instrument" in quelle:
            for ziel in knoten.targets:
                if isinstance(ziel, ast.Name):
                    self.aliase.add(ziel.id)
        self.generic_visit(knoten)

    def _pruefe(self, knoten) -> None:
        text = ast.unparse(knoten)
        # ⚠️ ALIASE MITZAEHLEN (28.08.2026). Die erste Fassung suchte den TEXT
        # "instrument" - und fand `asset_schalter.py:89` deshalb NICHT, weil
        # die Variable dort `i` heisst (`i = str(instrument or "")...`).
        # Genau die Stelle, an der der Hebel-Schalter des Nutzers haengt.
        #
        # Textsuche kann einen Datenfluss nicht sehen; sie findet nur den
        # Namen, den jemand zufaellig stehen liess. Deshalb sammelt der
        # Sammler jetzt zuerst die Namen, die AUS `instrument` entstehen.
        namen = ("instrument",) + tuple(self.aliase)
        if not any(n in text for n in namen) or len(text) > 90:
            return
        if any(w in text for w in ('"hebel"', "'hebel'", '"spot"', "'spot'")):
            self.funde.append((knoten.lineno, text[:80]))

    def visit_Compare(self, knoten):
        self._pruefe(knoten)
        self.generic_visit(knoten)

    def visit_Subscript(self, knoten):
        if "instrument" in ast.unparse(knoten):
            self.funde.append((knoten.lineno, ast.unparse(knoten)[:80]))
        self.generic_visit(knoten)


def _funktion_bei(quelle: str, zeile: int) -> str:
    name = "?"
    for i, l in enumerate(quelle.split("\n"), 1):
        if i > zeile:
            break
        s = l.strip()
        if s.startswith("def "):
            name = s[4:].split("(")[0]
    return name


def pruefe() -> int:
    dateien = [f for f in subprocess.run(
        ["git", "ls-files", "agent/*.py"], capture_output=True, text=True,
        encoding="utf-8").stdout.split()
        if f.replace("agent/", "").replace(".py", "") in NEUE_KETTE]
    gesehen, offen = set(), []
    print(f"{'Datei':26}{'Funktion':26}{'Urteil':8}Zeilen")
    print("=" * 92)
    for pfad in sorted(dateien):
        try:
            quelle = io.open(pfad, encoding="utf-8").read()
            baum = ast.parse(quelle)
        except (OSError, SyntaxError):
            continue
        s = Sammler()
        s.visit(baum)
        je_funktion: dict[str, list[int]] = {}
        for ln, _ in sorted(set(s.funde)):
            je_funktion.setdefault(_funktion_bei(quelle, ln), []).append(ln)
        kurz = pfad.replace("agent/", "")
        for fn, zeilen in sorted(je_funktion.items()):
            gesehen.add((kurz, fn))
            urteil, grund = URTEIL.get((kurz, fn), ("OFFEN", ""))
            if urteil == "OFFEN":
                offen.append(f"{kurz}::{fn} (Zeile {zeilen[0]})")
            print(f"  {kurz:24}{fn:26}{urteil:8}"
                  f"{', '.join(str(z) for z in zeilen)}")
    print("=" * 92)
    verwaist = [f"{d}::{f}" for d, f in URTEIL if (d, f) not in gesehen]
    for zeile in offen:
        print(f"  FEHL  ohne Urteil: {zeile}")
    for zeile in verwaist:
        print(f"  FEHL  Urteil ohne Fundstelle: {zeile}")
    tot = sum(1 for u, _ in URTEIL.values() if u == "tot")
    print(f"\n{len(gesehen)} Stellen, {tot} davon fuer Krypto TOT seit S6b")
    if not offen and not verwaist:
        print("  OK    jede Stelle traegt ihr Urteil")
    return 1 if (offen or verwaist) else 0


if __name__ == "__main__":
    raise SystemExit(pruefe())
