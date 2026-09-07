# -*- coding: utf-8 -*-
"""Erzeugt den Arbeitsstand als Word-Datei (06.-07.09.2026).

⚠️ NICHT VON HAND AENDERN - die Aenderung gehoert in dieses Skript, sonst
laeuft die Datei vom Befundstand weg. Dieselbe Regel wie bei den Registern.

    python erzeuge_stand_word.py
"""
from __future__ import annotations

import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from docx import Document                                    # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT               # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH                # noqa: E402
from docx.oxml import OxmlElement                            # noqa: E402
from docx.oxml.ns import qn                                  # noqa: E402
from docx.shared import Pt, RGBColor, Cm                     # noqa: E402

ZIEL = "Basisinfos/Stand_06_09_2026.docx"

ROT = RGBColor(0xB0, 0x2A, 0x1F)
GRUEN = RGBColor(0x1B, 0x6B, 0x3A)
GRAU = RGBColor(0x55, 0x55, 0x55)
BLAU = RGBColor(0x1F, 0x3D, 0x6B)


def schattiere(zelle, farbe="EFEFEF"):
    el = OxmlElement("w:shd")
    el.set(qn("w:fill"), farbe)
    zelle._tc.get_or_add_tcPr().append(el)


def tabelle(dok, kopf, zeilen, breiten=None):
    t = dok.add_table(rows=1, cols=len(kopf))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, k in enumerate(kopf):
        z = t.rows[0].cells[i]
        z.text = ""
        lauf = z.paragraphs[0].add_run(k)
        lauf.bold = True
        lauf.font.size = Pt(9)
        schattiere(z, "DDE3EA")
    for zeile in zeilen:
        r = t.add_row().cells
        for i, wert in enumerate(zeile):
            r[i].text = ""
            p = r[i].paragraphs[0]
            txt = str(wert)
            fett = txt.startswith("**") and txt.endswith("**")
            if fett:
                txt = txt[2:-2]
            lauf = p.add_run(txt)
            lauf.font.size = Pt(9)
            lauf.bold = fett
            if txt.startswith("✔"):
                lauf.font.color.rgb = GRUEN
            elif txt.startswith("⚠") or txt.startswith("✖"):
                lauf.font.color.rgb = ROT
    if breiten:
        for r in t.rows:
            for i, b in enumerate(breiten):
                r.cells[i].width = Cm(b)
    dok.add_paragraph()
    return t


def absatz(dok, text, fett=False, farbe=None, groesse=10.5, vor=0, nach=6):
    p = dok.add_paragraph()
    p.paragraph_format.space_before = Pt(vor)
    p.paragraph_format.space_after = Pt(nach)
    lauf = p.add_run(text)
    lauf.bold = fett
    lauf.font.size = Pt(groesse)
    if farbe is not None:
        lauf.font.color.rgb = farbe
    return p


def merksatz(dok, text):
    """Ein hervorgehobener Kernsatz - eingerueckt, farbig, fett."""
    p = dok.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(10)
    lauf = p.add_run(text)
    lauf.bold = True
    lauf.font.size = Pt(10.5)
    lauf.font.color.rgb = BLAU
    return p


def punkt(dok, text, ebene=0):
    p = dok.add_paragraph(style="List Bullet" if ebene == 0
                          else "List Bullet 2")
    p.paragraph_format.space_after = Pt(3)
    lauf = p.add_run(text)
    lauf.font.size = Pt(10)
    return p


def main() -> int:
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)

    # ---------------------------------------------------------------- Kopf
    t = d.add_heading("Arbeitsstand 6.–7. September 2026", level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.LEFT
    absatz(d, "Die Bewertungsebene des TradingInfoTool — was heute gemessen "
              "wurde, was gilt und wo es weitergeht.", farbe=GRAU,
           groesse=11, nach=2)
    absatz(d, "Methodik 2.134 bis 2.142 · Messungen N-52 bis N-58 · "
              "Suite 1.976 Prüfungen, alle bestanden", farbe=GRAU,
           groesse=9, nach=14)

    # ------------------------------------------------------------ Kernsatz
    d.add_heading("Der Tag in einem Satz", level=1)
    merksatz(d, "Wir haben herausgefunden, dass mehrere unserer Maßstäbe "
                "uns getäuscht haben — und dadurch steht die "
                "Bewertungsebene jetzt besser da als am Morgen, nicht "
                "schlechter.")
    absatz(d, "Der rote Faden war eine einzige Frage: Misst dieser Maßstab, "
              "was er zu messen vorgibt? Sechs Maßstäbe wurden geprüft, vier "
              "davon sind kontaminiert — sie schlagen in einer künstlichen "
              "Welt an, in der es nichts zu finden gibt. Sauber ist nur GS: "
              "symmetrische Barrieren, gezählt werden nur aufgelöste Anker. "
              "Sein Nullpunkt liegt beweisbar bei 0,5, unabhängig von der "
              "Volatilität.")

    # ------------------------------------------------------------- Befunde
    d.add_heading("Die sieben Befunde", level=1)
    tabelle(d, ("Nr.", "Befund", "Wirkung"), [
        ("N-52", "**`vola` trägt keine Richtung**", "Der stärkste Befund "
         "des Tages war unsere eigene Geometrie: ruhige Werte lösen ihre "
         "Barrieren öfter auf, und eine Auflösung ist zu ⅓ ein Treffer. "
         "Richtungsrein bleibt nichts (−0,00041, Kontrolle 2/5)."),
        ("N-53", "**`turnover` rehabilitiert**", "Es wurde am falschen "
         "Maßstab gemessen. Richtungsrein ist es mit +0,00512 der stärkste "
         "der drei Größen — zweieinhalbmal `funding`."),
        ("N-54", "Die zwei Ebenen sind unabhängig", "`vola` verstärkt "
         "`funding`/`turnover` nicht. Der einfachere Entwurf: die "
         "Geometrieebene stört die Bewertung nicht."),
        ("N-55", "`vola` ordnet die Höhe, nicht die Bauform", "In allen 12 "
         "Geometrien liegt die Spreizung über dem Artefakt (+0,035 bis "
         "+0,126 R). Aber dieselbe Geometrie gewinnt in allen Dritteln."),
        ("N-56", "**Die OI-Sperre trägt Richtung**", "Reproduziert in der "
         "Live-Form; GS +0,00220 (H20) und +0,00381 (H5). Sie steht zu "
         "Recht. ⚠️ Zugleich: `turnover`s Tabelle reproduziert nicht."),
        ("N-57", "**31,4 % laufen flach aus**", "Bei H5. Die "
         "Kalibrierungsbasis liegt dadurch um +0,29 R daneben — mit "
         "falschem Vorzeichen. ✔ Die Potentialformel selbst stimmt: unter "
         "den Aufgelösten 34,8 %, die Formel setzt 33,3 %."),
        ("N-58", "**`turnover`s Stufen sind nicht herleitbar**", "Weder "
         "Fünfteilung noch Zweiteilung noch Schalter. Trennschärfe 2,0 "
         "Punkte — die registrierte Tabelle hatte 5,55 Punkte Spanne. "
         "Wäre sie echt, hätten wir sie gesehen."),
    ], breiten=(1.6, 4.6, 9.8))

    # -------------------------------------------------------------- Stand
    d.add_heading("Stand der Bewertungsebene", level=1)
    absatz(d, "Alle vier Größen erstmals durch dasselbe richtungsreine "
              "Verfahren geschickt und damit vergleichbar:")
    tabelle(d, ("Größe", "GS (Richtung)", "Live", "Zustand"), [
        ("`funding`", "✔ +0,00197", "BEITRAEGE, 5 Stufen",
         "✔ reproduziert bis in die Form — monoton, Tabelle stimmt"),
        ("`turnover`", "✔ +0,00512", "BEITRAEGE, 5 Stufen",
         "⚠️ Größe gut, Tabelle nicht belegt"),
        ("`oi_aenderung`", "✔ +0,00220 / +0,00381", "Sperre in rollen_gate",
         "✔ reproduziert, steht zu Recht"),
        ("`vola`", "✖ −0,00041", "nicht registriert",
         "gehört in die Geometrie, ordnet die Höhe"),
    ], breiten=(3.2, 3.4, 4.2, 5.2))
    merksatz(d, "Drei tragende Größen statt der einen, von der am Morgen "
                "auszugehen war. Die Kalibrierungsblockade ist weg.")

    # ------------------------------------------------------ die Flach-Zahl
    d.add_heading("Die Zahl, die die Reihenfolge entscheidet", level=1)
    absatz(d, "Gemessen in der echten Produktionsgeometrie — Stop = "
              "max(5 % vom Kurs, 0,75 × ATR), gedeckelt bei 25 %, CRV 2,0 — "
              "über 687.748 Anker:")
    tabelle(d, ("bis Tag", "Ziel", "Stop", "FLACH", "EW Kalibrierung",
                "EW Produktion"), [
        ("**5**", "21,2 %", "47,5 %", "**31,4 %**", "**−0,3654 R**",
         "−0,0756 R"),
        ("20", "32,7 %", "62,0 %", "5,3 %", "−0,0199 R", "+0,0354 R"),
        ("60", "33,9 %", "64,0 %", "2,1 %", "+0,0179 R", "+0,0398 R"),
        ("120", "34,3 %", "64,3 %", "1,4 %", "+0,0280 R", "**+0,0430 R**"),
    ], breiten=(2.2, 2.2, 2.2, 2.6, 3.4, 3.4))
    absatz(d, "Median bis zur Auflösung: 3 Tage. 98,6 % lösen binnen 120 "
              "Tagen auf.")
    absatz(d, "In der Produktion gibt es diesen Ausgang gar nicht: die Kette "
              "hat keinen Zeitausstieg, eine Position läuft bis Stop oder "
              "Ziel. Jeder flache Anker in der Messung ist damit ein Anker, "
              "den die Kalibrierung als Nicht-Treffer zählt, obwohl die "
              "Produktion ihn noch offen hätte.")
    merksatz(d, "Und ein Fund, der die Bewertung entlastet: unter den "
                "aufgelösten Ankern liegt die Trefferquote bei 34,8 %, die "
                "Formel setzt 33,3 %. Die Potentialformel stimmt für die "
                "Produktion. Kaputt ist die Messung, mit der wir sie "
                "füttern.")

    # ------------------------------------------------------- eigene Fehler
    d.add_heading("Was heute umgestoßen wurde — auch von mir selbst",
                  level=1)
    absatz(d, "Sechs Aussagen sind im Lauf des Tages gefallen. Vier davon "
              "waren meine eigenen, und jede wurde von der jeweils nächsten "
              "Gegenprüfung gefangen — nicht von der ersten Messung.")
    tabelle(d, ("Aussage", "Warum sie fiel"), [
        ("„Die Auswahl ist schädlich“",
         "Grundmengen-Artefakt: k = 2 aus 516 statt aus 40 Symbolen. Eine "
         "Regel mit fester Trefferzahl ist ohne ihre Grundmenge nicht "
         "definiert."),
        ("„`vola` gehört registriert“",
         "An der Barrieren-Quote gemessen, die Auflösung und Richtung "
         "mischt. Richtungsrein bleibt nichts."),
        ("„`turnover` ist nicht belegt, stilllegen“",
         "Stand auf demselben gemischten Maßstab. Richtungsrein ist es der "
         "stärkste der drei."),
        ("„Die Registrierungsbasis H20/R ist kontaminiert“",
         "Zu stark formuliert. Belegt war das für H5 mit `vola`; bei H20 "
         "mit externen Kennzahlen feuert sie in keiner Kunstwelt."),
        ("„`q` zählt einen wertlosen Kanal mit“",
         "Falsch adressiert. Die Kette hat keinen Zeitausstieg — der Fehler "
         "sitzt in der Messkonvention, nicht in der Formel."),
        ("„Die Geometrie unterscheidet sich je vola-Drittel“",
         "Ausgabe des eigenen Skripts. Alle 36 von 36 Zellen bestanden, und "
         "die Kunstwelt hatte einen Strukturfehler."),
    ], breiten=(6.0, 10.0))

    d.add_heading("Die methodischen Lehren", level=2)
    punkt(d, "Ein Nullpunkt muss herleitbar sein. Drei von vier Maßstäben "
             "feuerten in einer Welt ohne Richtung — alle vier mit sauberer "
             "Zufallskontrolle. Die Kontrolle mischt die Zuordnung, nicht "
             "die Mechanik.")
    punkt(d, "Zweiseitig prüfen. Derselbe Kanal kann je nach Ausrichtung "
             "der Kennzahl das Vorzeichen wechseln; ein einseitiges "
             "Kriterium sieht nur die halbe Welt.")
    punkt(d, "Gleichstand geht an den Stop. Werden beide Barrieren am "
             "selben Tag berührt, weiß die Tageskerze nicht, was zuerst "
             "kam — die optimistische Auflösung erfand bis zu +0,39 R.")
    punkt(d, "Die Kunstwelt muss geeicht sein. Der echte Markt hat eine "
             "doppelt so breite Tagesspanne relativ zur Schlusskurs-"
             "bewegung; ungeeicht unterschätzt man das Artefakt um das "
             "Doppelte.")
    punkt(d, "Eine Regel mit fester Trefferzahl ist Teil der Regel, nicht "
             "der Messbasis — die Grundmenge gehört mitgeprüft.")

    # ------------------------------------------------- die Aenderung 07.09.
    d.add_page_break()
    d.add_heading("Die Änderung am laufenden System (7. September)", level=1)
    tabelle(d, ("", "vorher", "jetzt"), [
        ("`turnover_fuenftel`", "+3,15 · +0,83 · +0,22 · −1,79 · −2,40",
         "**+0,33 · +0,33 · +0,33 · −0,48 · −0,48**"),
        ("`SCHWELLE_VORGABE`", "0,080 R", "**0,005 R**"),
        ("`erreichbar_max`", "0,1335 R", "0,0489 R"),
        ("Durchlass", "16,4 %", "**54,0 %**"),
    ], breiten=(4.6, 6.0, 6.0))
    absatz(d, "Die Schwelle musste nicht aus Systematik mit, sondern aus "
              "Notwendigkeit: `erreichbar_max` fällt auf 0,0489 R — eine "
              "Schwelle von 0,080 hätte für jede Datenlage bedeutet, dass "
              "nichts mehr durchkommt. Das Verfahren wurde vorher an der "
              "alten Lage reproduziert und gab dort 0,080 zurück.")
    merksatz(d, "Der unangenehme Teil: härter filtern macht das Ergebnis "
                "schlechter. Die alte Schwelle 0,080 war die beste wegen "
                "turnovers riesiger Stufen — also wegen einer Tabelle, die "
                "nicht existiert. Die Trennschärfe der Schwelle kam aus "
                "einer Fiktion.")

    d.add_heading("⚠️ Ein Regelverstoß, selbst gefunden", level=2)
    absatz(d, "R-R9 verlangt als Zielgröße der Schwellenkalibrierung "
              "ausdrücklich die DURCHLASSQUOTE, nicht die Wirkung — und "
              "Punkt 4 der Prüfliste verbietet, das Maximum zu wählen. "
              "Genau das ist hier geschehen: optimiert wurde nach „Gewinn "
              "je verworfenem Signal“, und das Maximum wurde genommen.")
    absatz(d, "Die 0,005 sind damit vorläufig, nicht kalibriert. Sie halten "
              "das System betriebsfähig, ersetzen die Entscheidung aber "
              "nicht — welche Durchlassquote das System liefern soll, ist "
              "laut Regelwerk eine Nutzerentscheidung.", fett=True)
    tabelle(d, ("gewünschter Durchlass", "nötige Schwelle"), [
        ("54 % (aktuell)", "0,005"),
        ("32 %", "0,010"),
        ("19 %", "0,020"),
        ("15 % (etwa wie bisher)", "0,030"),
    ], breiten=(6.0, 5.0))

    # -------------------------------------------------------------- offen
    d.add_heading("Was offen ist", level=1)
    tabelle(d, ("Rang", "Punkt", "Warum"), [
        ("1", "**Die Durchlassquote festlegen**",
         "Nutzerentscheidung laut R-R9. Ohne sie ist die Schwelle 0,005 "
         "vorläufig und die Kalibrierung formal unvollständig."),
        ("2", "**Die fünf abgelehnten Beiträge unter GS neu vermessen**",
         "`H`, Rangplatz, Schnittabstand, Lebendigkeit, Termine — alle "
         "wurden auf der Basis abgelehnt, die sich als gegen "
         "richtungsreine Kandidaten verzerrt erwiesen hat. Genau der "
         "Fehler, der `turnover` beinahe gekostet hätte. Das System ist "
         "dünn, WEIL diese fünf abgelehnt wurden."),
        ("3", "Den Maßstab der Stufen korrigieren",
         "F-219: die Bewertung liefert 19,5 % dessen, was sie behauptet — "
         "alle Stufen sind rund 5× zu groß. Ändert Rangfolge und Schwelle "
         "nicht, wohl aber den Hebel (F-220)."),
        ("4", "`vola`s Zuschreibung",
         "Braucht eine Kunstwelt mit Brownscher Brücke je Tag statt "
         "unabhängigem Hoch/Tief-Rauschen."),
        ("5", "Randmaß-Nachmessung aus N-52",
         "N1-V2 fand am Randmaß einen Richtungseffekt. Nicht widerlegt "
         "(andere Zielgröße), aber unter Verdacht."),
        ("6", "Die älteren Punkte im Plan",
         "N-18 bis N-51, darunter die vier blockierten Nicht-Krypto-"
         "Klassen und der Gabelpunkt F-164."),
    ], breiten=(1.4, 4.8, 9.8))

    d.add_heading("Der nächste Schritt", level=1)
    absatz(d, "Die fünf abgelehnten Beiträge unter dem sauberen Maßstab neu "
              "vermessen. Das ist der einzige Weg, der die eigentliche "
              "Schwäche angeht: die Bewertungsebene trägt faktisch eine "
              "Größe, und der Code warnt selbst, dass ein System mit genau "
              "einem Beitrag diesen Beitrag nicht mehr prüfen kann.")
    absatz(d, "Alle fünf wurden auf einer Basis abgelehnt, die einen "
              "Richtungseffekt aufheben kann — bei `turnover` ist genau das "
              "passiert, und die Neumessung hat es zutage gebracht.",
           farbe=GRAU)

    d.add_paragraph()
    absatz(d, "Erzeugt aus `erzeuge_stand_word.py`. Änderungen gehören in "
              "das Skript, nicht in diese Datei — sonst läuft sie vom "
              "Befundstand weg.", farbe=GRAU, groesse=8.5)

    d.save(ZIEL)
    print("geschrieben: %s" % ZIEL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
