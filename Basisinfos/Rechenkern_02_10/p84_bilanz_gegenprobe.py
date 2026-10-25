"""P84 GEGENPROBE Gesamtbilanz R-3 (25.10.2026, Basisinfos/Bilanz_Gesamt_25_10.md, E-141) und Word-Fassung.

    python -X utf8 Basisinfos/Rechenkern_02_10/p84_bilanz_gegenprobe.py [<ziel.docx>]

G1  jede in der Bilanz zitierte E-Nummer existiert in Entscheidungen_Hebelneubau.md
G2  die tragenden Zahlen der Bilanz stehen so in ihren Quellen (Liste unten, je Zahl die Quelldatei)
G3  die acht Berichtigungen stehen als Nachtrag an den Eintraegen (E-36, E-127, E-130-E-132, E-134, E-135, E-139)
G4  Word-Fassung: aus der .md erzeugt (build_docx.md_nach_docx), zurueckgelesen: Ueberschriften und Tabellen gleich der .md, Kernsaetze enthalten
"""
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.stdout.reconfigure(encoding="utf-8")
B = "Basisinfos/Bilanz_Gesamt_25_10.md"
E = "Basisinfos/Entscheidungen_Hebelneubau.md"
R = "Basisinfos/Rechenkern_02_10/"
ZAHLEN = [  # (Zahl wie in der Bilanz, Quelle, Text wie in der Quelle)
    ("+0,0057", "Basisinfos/Kern_29_09/best__unverzerrt_2.txt", "+0.0057"),
    ("+0,0156 (Nullmittel unverzerrt:2)", "Basisinfos/Kern_29_09/best__unverzerrt_2.txt", "Mittel +0.0156"),
    ("+0,0106", "Basisinfos/Kern_29_09/best__unverzerrt_3.txt", "+0.0106"),
    ("+0,0127", "Basisinfos/Kern_29_09/best__unverzerrt_3.txt", "Mittel +0.0127"),
    ("−0,35 bis +0,79", "Basisinfos/Voranalyse_REGEL0_Kosten_23_10.md", "−0,35 bis +0,79"),
    ("≥ 50 %", "Basisinfos/Voranalyse_REGEL0_Kosten_23_10.md", "≥ 50 % der Einstiege"),
    ("30 % Fehlalarm", R + "p83_robustheit_r.txt", "Fehlalarm je Handel 30 %"),
    ("Nachlauf Nasdaq 0,05/0,07", R + "p75_atlas_t1_krypto.txt", "NACH  8%/14%/0.05 (n60) | 4%/10%/0.07"),
    ("Nachlauf Stablecoins 0,00/0,33", R + "p75_atlas_t1_krypto.txt", "NACH  0%/11%/0.00 (n11) | 4%/4%/0.33"),
    ("F&G n = 13", R + "p75_atlas_t1_krypto.txt", "69%/46%/0.97 (n13)"),
    ("F&G 0,955", R + "p75_gegenprobe.txt", "0.972 / 0.955"),
    ("je Tag −0,24 %", R + "p83_robustheit_r.txt", "je Tag -0.239 %"),
    ("+4,87 Pp", E, "+4,87 Pp"),
    ("−12,5 Pp", E, "12,5 Pp"),
    ("76 % gegen kalt 0 %", E, "76 %"),
    ("Korb ab 2024 −57 %", "Basisinfos/Bestandsaufnahme_brutto_netto_22_10.md", "57 %"),
    ("E3 +13,9 Pp", "Basisinfos/Bestandsaufnahme_brutto_netto_22_10.md", "13,9"),
    ("40 → 77 %", R + "p72_gegenprobe.txt", "2024-26 40 % · 2020-26 77 %"),
]


def main():
    b = open(B, encoding="utf-8").read()
    e = open(E, encoding="utf-8").read()
    vorh = set(re.findall(r"^# (E-\d+) ·", e, flags=re.M))
    zit = set(re.findall(r"\bE-(\d+)", b))
    fehlt = sorted((n for n in zit if "E-" + n not in vorh), key=int)
    ok1 = not fehlt
    print("G1 zitierte E-Nummern %d, in den Entscheidungen vorhanden %d, fehlend: %s -> %s" % (len(zit), len(zit) - len(fehlt), fehlt or "keine",
                                                                                          "ok" if ok1 else "NICHT OK"))
    falsch = []
    for z, q, t in ZAHLEN:
        if t not in open(q, encoding="utf-8").read():
            falsch.append("%s (%s)" % (z, q))
    ok2 = not falsch
    print("G2 tragende Zahlen gegen die Quelle: %d von %d gefunden%s -> %s" % (len(ZAHLEN) - len(falsch), len(ZAHLEN),
                                                                             (" · fehlt: " + "; ".join(falsch)) if falsch else "", "ok" if ok2 else "NICHT OK"))
    soll = ["E-36", "E-127", "E-130", "E-131", "E-132", "E-134", "E-135", "E-139"]
    da = []
    for k in soll:
        m = re.search(r"^# %s ·.*?(?=^# E-\d+ ·|\Z)" % k, e, flags=re.M | re.S)
        da.append(bool(m and "Nachtrag 25.10.2026 (E-141" in m.group(0)))
    ok3 = all(da)
    print("G3 Nachtraege an den Eintraegen: %d von %d -> %s" % (sum(da), len(soll), "ok" if ok3 else "NICHT OK"))
    ok4 = True
    if len(sys.argv) > 1:
        from pathlib import Path

        import build_docx as BD
        from docx import Document
        ziel = Path(sys.argv[1])
        BD.md_nach_docx(Path(B), ziel)
        d = Document(str(ziel))
        h_docx = sum(1 for p in d.paragraphs if p.style.name.startswith("Heading") or p.style.name.startswith("Title"))
        h_md = len(re.findall(r"^#{1,6} ", b, flags=re.M))
        t_md = len(re.findall(r"^\|[-| :]+\|\s*$", b, flags=re.M))
        text = "\n".join(p.text for p in d.paragraphs) + "\n".join(c.text for t in d.tables for r in t.rows for c in r.cells)
        kern = ["Teil A — Prüfbericht", "Vier davon waren bisher nicht dokumentiert", "Kein Einstiegssignal mit belegtem Vorsprung",
                "B.7 Bausteine für eine Kombination", "nicht entscheidbar"]
        fehlend = [k for k in kern if k not in text]
        ok4 = h_docx == h_md and len(d.tables) == t_md and not fehlend
        print("G4 Word-Fassung %s (%.0f KB): Ueberschriften %d/%d · Tabellen %d/%d · Kernsaetze fehlend: %s -> %s" % (
            ziel, ziel.stat().st_size / 1024, h_docx, h_md, len(d.tables), t_md, fehlend or "keine", "ok" if ok4 else "NICHT OK"))
    print("ERGEBNIS %d von %d" % (sum([ok1, ok2, ok3, ok4]), 4))


if __name__ == "__main__":
    main()
