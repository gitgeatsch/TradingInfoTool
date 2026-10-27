"""P100 Quellenpruefung des Konzepts 'Lagegerechte Handlung' (27.10.2026, E-165): jede genannte Befund- (2.xxx) und
Entscheidungsnummer (E-xxx) muss im Register bzw. in den Entscheidungen existieren; Spot-Paragraphen im Spot-Dokument.

    python -X utf8 Basisinfos/Rechenkern_02_10/p100_konzept_quellen.py

Nur lesend.
"""
import glob
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(HIER)
sys.stdout.reconfigure(encoding="utf-8")
KONZEPT = os.path.join(B, "Konzept_Lagegerechte_Handlung_27_10.md")


def lies(p):
    return open(p, encoding="utf-8").read()


def main():
    k = lies(KONZEPT)
    reg = lies(os.path.join(B, "REGISTER_Befunde.md"))
    ent = lies(os.path.join(B, "Entscheidungen_Hebelneubau.md"))
    spot = "\n".join(lies(p) for p in glob.glob(os.path.join(B, "*Spot*.md")))
    fehl = []
    befunde = sorted(set(re.findall(r"\b(2\.\d{3})\b", k)))
    for b in befunde:
        if not re.search(r"\*\*%s-" % re.escape(b), reg):
            fehl.append("Befund %s nicht im Register" % b)
    ents = sorted(set(re.findall(r"\bE-(\d{2,3})\b", k)), key=int)
    for e in ents:
        if int(e) == 165:
            continue                                            # die Entscheidung dieses Konzepts selbst
        if not re.search(r"^# E-%s " % e, ent, re.M):
            fehl.append("E-%s nicht in den Entscheidungen" % e)
    paras = sorted(set(re.findall(r"Spot §(\d+\.\d+)", k)))     # nur Verweise ins Spot-Dokument, nicht die eigenen §
    for p in paras:
        if not re.search(r"§ ?%s\b|^#+ *%s\b" % (re.escape(p), re.escape(p)), spot, re.M):
            fehl.append("Spot §%s nicht im Spot-Dokument" % p)
    print("Befunde %d geprueft: %s" % (len(befunde), ", ".join(befunde)))
    print("Entscheidungen %d geprueft: %s" % (len(ents), ", ".join("E-" + e for e in ents)))
    print("Spot-Paragraphen %d geprueft: %s" % (len(paras), ", ".join(paras)))
    print("\n".join(fehl) if fehl else "alle Quellen vorhanden")
    return 1 if fehl else 0


if __name__ == "__main__":
    sys.exit(main())
