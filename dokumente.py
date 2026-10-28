"""Das DOKUMENTEN-REGISTER: jedes Dokument unter Basisinfos/, nach Art geordnet, mit Stand und Einstufung (28.10.2026).

    python dokumente.py            # schreibt Basisinfos/REGISTER_Dokumente.md
    python dokumente.py --pruefe   # nur vergleichen (Paket Gesamtplan)

Nutzer 28.10.2026: *„vergiss nicht, dass wir auch noch weitere Zentraldokumente, Messplaene und Regelwerke fuehren - also die Verweise,
damit nichts verloren geht“*. ⚠️ Das Blatt wird ERZEUGT, nie von Hand geaendert: eine Aufzaehlung von Hand veraltet still (Regel 4 der
Pruefungen gegen eine Kopie). Die ART kommt aus dem Dateinamen, die EINSTUFUNG aus dem Text des Dokuments selbst:
  HISTORIE      Kopfzeile "HISTORIE – nicht fortschreiben"
  vor Messstandard   Standkopf <!-- STAND: ... --> (markiere_dokumente)
  laufend       im Gesamtplan verlinkt
  Arbeitsblatt  sonst (datierte Voranalyse, Messung, Bericht)

ZEILENTREU: Dokumente, die anderswo mit ZEILENNUMMER zitiert werden ("Kette_Landkarte.md Z. 151"). Bei ihnen steht der Verweis auf den
Gesamtplan am ENDE, damit sich keine Zeile verschiebt.
"""
import glob
import os
import sys

import markiere_dokumente as MD

HIER = os.path.dirname(os.path.abspath(__file__))
BASIS = os.path.join(HIER, "Basisinfos")
ZIEL = os.path.join(BASIS, "REGISTER_Dokumente.md")
ZEILENTREU = ("Anforderungen_Umbau_28_08.md", "Kette_Landkarte.md", "Spezifikation.md", "Regelwerk_Entscheidungslog.md",
              "Umbauplan_Gesamtsystem_12_08.md", "Ausloeser_und_Begruendungen_27_08.md", "Arbeitsstand_Deadloop_09_08.md",
              "Gesamtplan_Wo_wir_stehen_28_08.md")
VERWEIS_OBEN = "> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte."
VERWEIS_UNTEN = "\n\n---\n\n> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md). *(Verweis am Ende, weil dieses Dokument mit Zeilennummern zitiert wird.)*\n"
HISTORIE = "HISTORIE – nicht fortschreiben"

# Art nach dem Anfang des Dateinamens; die erste passende Zeile gewinnt
ARTEN = (
    ("Plan", ("Gesamtplan", "Plan_", "Bauplan_", "Umbauplan_", "Arbeitsstand_", "UEBERGABE_", "Uebergabe_", "Anleitung_", "Arbeitsplan_",
              "Plananpassung_", "Offene_Punkte_", "Reparaturliste_")),
    ("Messplan / Vorabfestlegung", ("Messplan_", "Vorabfestlegung_", "Messkonzept_", "Selektion", "Spiegelprobe", "Zielgroessen",
                                    "Pruefplan_", "Pruefliste_")),
    ("Regelwerk / Methodik", ("Regelwerk", "Spezifikation", "Test_und_Verifikationsmethodik", "MEMORY_SYNC_STRATEGY", "Symbolzuordnung",
                              "Regler_", "Definition_")),
    ("Entscheidungen / Fakten", ("Entscheidungen_", "Entscheidung_", "Fakten_", "Befundkarte", "REGISTER_")),
    ("Konzept", ("Konzept_", "Umbaukonzept_", "Loesungskonzept_", "Rollenkonzept_", "Architektur", "Hypothese_", "Option_", "Fallback_",
                 "REGEL0_", "Kategorie_", "Kombinationsmatrix_", "Konstruktion_", "Ausloeser_")),
    ("Voranalyse / Recherche", ("Voranalyse_", "Bestandsaufnahme_", "Recherche_", "Vorschlag_", "Datenbasis_", "Anforderungen_",
                                "Machbarkeit_", "Abhaengigkeitspruefung_", "A1_", "Auswahl_", "Bitpanda_Umstellung", "Drift_", "HA1_", "HK1_",
                                "Hebelarm_", "RR11_", "Messungen_")),
    ("Lage / Bilanz / Bericht", ("Bilanz_", "Zwischenstand_", "Status", "Was_", "Hebelstatus", "Lagebestimmung", "Lagebewertung", "Gesamtlage",
                                 "Einordnung_", "Roter_Faden")),
    ("Betrieb / Technik", ("Tailscale", "Rollout_", "Ausrollen_", "Kette_Landkarte", "Spot_Voranalyse_04_10/")),
)


def art(name: str) -> str:
    if "Ergebnis" in name or name.startswith(("Befund", "N19E_", "P9_", "PunktB_", "Q_Kalibrierung", "Geometrie_")):
        return "Befund / Ergebnis"
    for a, anfaenge in ARTEN:
        if any(name.startswith(x) for x in anfaenge):
            return a
    return "Sonstiges"


def titel(text: str) -> str:
    for z in text.split("\n")[:8]:
        if z.startswith("# "):
            return z[2:].strip().replace("|", "/")
    return "–"


def dokumente() -> list:
    return sorted(glob.glob(os.path.join(BASIS, "*.md")) + glob.glob(os.path.join(BASIS, "*", "*.md")))


def einstufung(pfad: str, text: str, im_plan: set) -> str:
    if HISTORIE in text[:3000]:
        return "HISTORIE"
    datum, kopf = MD.stand(pfad)
    if kopf:
        return "vor Messstandard (%s)" % datum
    if os.path.basename(pfad) in im_plan:
        return "**laufend**"
    return "Arbeitsblatt"


def erzeuge() -> str:
    plan = open(os.path.join(BASIS, "Gesamtplan.md"), encoding="utf-8").read()
    im_plan = {os.path.basename(x) for x in __import__("re").findall(r"\]\(([^)#]+\.md)\)", plan)} | {"Gesamtplan.md"}
    zeilen = {}
    for p in dokumente():
        name = os.path.relpath(p, BASIS).replace("\\", "/")
        if os.path.basename(p) == "REGISTER_Dokumente.md":
            continue
        t = open(p, encoding="utf-8", errors="replace").read()
        zeilen.setdefault(art(name), []).append(
            "| [`%s`](%s) | %s | %s |" % (name, name, titel(t)[:110], einstufung(p, t, im_plan)))
    aus = ["# Register der Dokumente — alles unter `Basisinfos/`",
           "",
           "> ⚙️ **ERZEUGT von `python dokumente.py` — nie von Hand ändern.** Laufender Plan: [`Gesamtplan.md`](Gesamtplan.md).",
           "> Einstufung aus dem Dokument selbst: **laufend** = im Gesamtplan verlinkt · HISTORIE = als abgelöst gekennzeichnet · "
           "vor Messstandard = Standkopf vor dem 09.09.2026 · Arbeitsblatt = datierte Voranalyse, Messung oder Bericht.",
           "",
           "| Art | Anzahl |", "|---|---|"]
    reihen = [a for a, _ in ARTEN] + ["Befund / Ergebnis", "Sonstiges"]
    aus += ["| %s | %d |" % (a, len(zeilen.get(a, []))) for a in reihen if zeilen.get(a)]
    aus += ["| **gesamt** | **%d** |" % sum(len(v) for v in zeilen.values()), ""]
    for a in reihen:
        if not zeilen.get(a):
            continue
        aus += ["## %s" % a, "", "| Dokument | Titel | Einstufung |", "|---|---|---|"] + zeilen[a] + [""]
    return "\n".join(aus)


def main() -> int:
    neu = erzeuge()
    if "--pruefe" in sys.argv:
        alt = open(ZIEL, encoding="utf-8").read() if os.path.exists(ZIEL) else ""
        print("REGISTER_Dokumente.md %s" % ("aktuell" if alt == neu else "VERALTET - python dokumente.py"))
        return 0 if alt == neu else 1
    open(ZIEL, "w", encoding="utf-8").write(neu)
    print("geschrieben: %s (%d Dokumente)" % (ZIEL, neu.count("\n| [`")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
