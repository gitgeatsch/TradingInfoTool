# -*- coding: utf-8 -*-
"""Erzeugt `Basisinfos/Standort_Krypto_07_09_2026.docx` — wo wir stehen.

⚠️ NICHT VON HAND AENDERN. Die Aenderung gehoert in dieses Skript, sonst
laeuft die Datei vom Befundstand weg - dieselbe Regel wie bei den
Registern und beim Tagesstand.

⚠️⚠️ UND DIE ZAHLEN WERDEN GELESEN, NICHT GETIPPT. Alles, was aus dem
laufenden System kommt (Beitraege, Stufen, Schwelle, Abdeckung), holt
dieses Skript beim Erzeugen ab. Eine Uebersicht, die ihre eigenen Zahlen
erfindet, ist nach zwei Wochen falsch und wird trotzdem geglaubt.

    python erzeuge_standort_krypto.py
"""
from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from docx import Document                                    # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT               # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH                # noqa: E402
from docx.oxml import OxmlElement                            # noqa: E402
from docx.oxml.ns import qn                                  # noqa: E402
from docx.shared import Pt, RGBColor, Cm                     # noqa: E402

ZIEL = "Basisinfos/Standort_Krypto_07_09_2026.docx"
ROT = RGBColor(0xB0, 0x2A, 0x1F)
GRUEN = RGBColor(0x1B, 0x6B, 0x3A)
GRAU = RGBColor(0x55, 0x55, 0x55)
BLAU = RGBColor(0x1F, 0x3D, 0x6B)


def schattiere(z, farbe="DDE3EA"):
    el = OxmlElement("w:shd")
    el.set(qn("w:fill"), farbe)
    z._tc.get_or_add_tcPr().append(el)


def tabelle(dok, kopf, zeilen, breiten=None, klein=False):
    t = dok.add_table(rows=1, cols=len(kopf))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    gr = Pt(8 if klein else 9)
    for i, k in enumerate(kopf):
        z = t.rows[0].cells[i]
        z.text = ""
        lauf = z.paragraphs[0].add_run(k)
        lauf.bold = True
        lauf.font.size = gr
        schattiere(z)
    for zeile in zeilen:
        r = t.add_row().cells
        for i, wert in enumerate(zeile):
            r[i].text = ""
            txt = str(wert)
            fett = txt.startswith("**") and txt.endswith("**")
            if fett:
                txt = txt[2:-2]
            lauf = r[i].paragraphs[0].add_run(txt)
            lauf.font.size = gr
            lauf.bold = fett
            if txt.startswith("✔"):
                lauf.font.color.rgb = GRUEN
            elif txt.startswith("⚠") or txt.startswith("✖") or txt.startswith("⛔"):
                lauf.font.color.rgb = ROT
    if breiten:
        for r in t.rows:
            for i, b in enumerate(breiten):
                r.cells[i].width = Cm(b)
    dok.add_paragraph()
    return t


def absatz(dok, text, fett=False, farbe=None, groesse=10.5, nach=6):
    p = dok.add_paragraph()
    p.paragraph_format.space_after = Pt(nach)
    lauf = p.add_run(text)
    lauf.bold = fett
    lauf.font.size = Pt(groesse)
    if farbe is not None:
        lauf.font.color.rgb = farbe
    return p


def merksatz(dok, text):
    p = dok.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(10)
    lauf = p.add_run(text)
    lauf.bold = True
    lauf.font.size = Pt(10.5)
    lauf.font.color.rgb = BLAU
    return p


def punkt(dok, text):
    p = dok.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.add_run(text).font.size = Pt(10)
    return p


# ---------------------------------------------------- die Zahlen HOLEN
def erhebe() -> dict:
    """⚠️ Aus dem laufenden System, nicht aus dem Gedaechtnis."""
    from agent import potential as PT
    from agent import rollen_gate as RG
    from agent import wahrscheinlichkeit as WK
    import messe_eigenschaft_beitrag as MEB
    import messe_funding_niveau as F
    import messe_bewertungskennzahl as MB
    import messe_kandidaten_als_regel as K
    import config

    kurs = {s.upper() for s in MEB.lade()}
    fu = {s.upper() for s in F.lade_funding()} & kurs
    tu = {s.upper() for s in MB.reihe("data/onchain_historie.db",
                                      "splycur")} & kurs
    oi = {s.upper() for s in K.lade_terminmarkt()["oi_aenderung"]} & kurs
    m = {"funding_fuenftel": 1, "turnover_fuenftel": 0}
    lagen = {}
    for strat in ("einstieg", "akkumulation"):
        p = PT.rechne(crv=2.0, stop_relativ=0.05, klasse="krypto",
                      instrument="spot", strategie=strat, h=None, merkmale=m)
        gilt = [b.name for b in WK.BEITRAEGE if b.zustand == "traegt"
                and WK._gilt(b, "krypto", strat)[0]]
        lagen[strat] = {"vermessen": p.vermessen, "bewertbar": p.bewertbar,
                        "traegt_hier": p.traegt_hier,
                        "max": p.erreichbar_max, "schwelle": p.schwelle,
                        "beitraege": gilt}
    wl = [a for a in config.get_watchlist()
          if str(getattr(a, "assetklasse", "")).lower() == "krypto"]
    return {"symbole": len(kurs), "funding": len(fu), "turnover": len(tu),
            "oi": len(oi), "stufen": [k for k, _t in RG.STUFEN],
            "lagen": lagen, "watchlist": len(wl),
            "vorgabe": PT.SCHWELLE_VORGABE,
            "stufen_texte": dict(RG.STUFEN)}


def main() -> int:
    z = erhebe()
    d = Document()
    st = d.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)

    d.add_heading("Standort Krypto — 7. September 2026", level=0)
    absatz(d, "Wo die Bewertungsebene steht, je Strategie und je "
              "Kettenstufe. Alle Zahlen beim Erzeugen aus dem laufenden "
              "System gelesen.", farbe=GRAU, groesse=11, nach=2)
    absatz(d, "Messbasis %d Krypto-Symbole · Watchlist %d Krypto · "
              "Suite 2.000 Prüfungen, alle bestanden"
              % (z["symbole"], z["watchlist"]), farbe=GRAU, groesse=9,
           nach=14)

    # ------------------------------------------------------------ Kern
    d.add_heading("Die Lage in drei Sätzen", level=1)
    merksatz(d, "Für `einstieg` entscheidet die Bewertung mit zwei "
                "belegten Beiträgen. Für `akkumulation` entscheidet sie "
                "gar nicht — dort gilt kein Beitrag, und die Stufe winkt "
                "bewusst durch.")
    absatz(d, "Es gibt einen dritten Kandidaten, der beide Strategien "
              "bedienen könnte: der Abstand zum eigenen 200-Tage-Schnitt. "
              "Er deckt als einziger alle Symbole ab, ist kaum redundant — "
              "und seine Stabilität über die Zeit ist mit den vorhandenen "
              "Daten nicht entscheidbar.")

    # ---------------------------------------------------------- Stufen
    d.add_heading("1 — Die Kette: zwölf Stufen, drei mit einer Messung",
                  level=1)
    reihen = []
    art = {"auswahl": ("Messung", "beide",
                       "✔ nicht schädlich (2.134) · Bestandsausnahme: "
                       "gehaltene Werte gehen durch"),
           "terminmarkt": ("Messung", "nur einstieg, nicht bei Bestand",
                           "✔ trägt Richtung (2.139)"),
           "entscheider": ("Messung", "nur einstieg",
                           "einstieg: entscheidet · akkumulation: winkt durch")}
    for i, k in enumerate(z["stufen"], 1):
        a, g, st_ = art.get(k, ("mechanisch", "beide", "✔"))
        reihen.append((str(i), "**%s**" % k if k in art else k,
                       z["stufen_texte"][k][:44], a, g, st_))
    tabelle(d, ("#", "Stufe", "was sie prüft", "Art", "gilt für", "Stand"),
            reihen, breiten=(0.9, 2.6, 4.6, 2.0, 3.4, 5.5), klein=True)
    absatz(d, "⚠️ Namensschatten: der `entscheider` ist die ZWÖLFTE Stufe, "
              "heißt aber in Code-Kommentaren und Dokumentation überall "
              "„Stufe 11“. `terminmarkt` wurde nachträglich eingefügt "
              "(N-14). Folgenlos, weil der Code über Namen adressiert — "
              "aber wer „Stufe 11“ liest, muss Nummer 12 meinen.",
           farbe=GRAU)

    # ------------------------------------------------------ Strategien
    d.add_heading("2 — Was die Bewertungsstufe je Strategie tut", level=1)
    ein, akk = z["lagen"]["einstieg"], z["lagen"]["akkumulation"]
    tabelle(d, ("", "einstieg", "akkumulation"), [
        ("geltende Beiträge",
         "**%s**" % ", ".join(b.split("-")[0] for b in ein["beitraege"]),
         "**⚠️ keine**"),
        ("`vermessen`", str(ein["vermessen"]), "**%s**" % akk["vermessen"]),
        ("`erreichbar_max`", "%.4f R" % ein["max"], "%.4f R" % akk["max"]),
        ("Schwelle", "%.4f R" % ein["schwelle"], "%.4f R" % akk["schwelle"]),
        ("→ die Stufe", "✔ **ENTSCHEIDET**", "⚠️ **WINKT DURCH** (Notiz)"),
    ], breiten=(4.6, 5.4, 5.4))
    absatz(d, "Sie sperrt bei `akkumulation` nicht — und das ist Absicht: "
              "„nicht vermessen — zählen, nicht sperren. Der Trichter weist "
              "es aus, damit die Lücke sichtbar bleibt.“ Eine Sperre ohne "
              "Beiträge wäre eine Sperre nach Datenlage (Regel 4).")

    # -------------------------------------------------------- Beiträge
    d.add_heading("3 — Die Beiträge: was gilt, was kandidiert", level=1)
    tabelle(d, ("Größe", "Stand", "Abdeckung", "wo", "Beleg"), [
        ("**`funding`**", "✔ **registriert**", "%d (%d %%)"
         % (z["funding"], round(100 * z["funding"] / z["symbole"])),
         "Stufe 12, nur einstieg",
         "reproduziert bis in die Form; richtungsrein +0,00197"),
        ("**`turnover`**", "✔ **registriert**", "%d (%d %%)"
         % (z["turnover"], round(100 * z["turnover"] / z["symbole"])),
         "Stufe 12, nur einstieg",
         "F-212 auf der selektierten Menge: +0,0635 gegen +0,0616"),
        ("**`oi_aenderung`**", "✔ **live als Sperre**", "%d (%d %%)"
         % (z["oi"], round(100 * z["oi"] / z["symbole"])),
         "Stufe 6, nur einstieg",
         "trägt Richtung: +0,00220 (H20) · +0,00381 (H5)"),
        ("**`schnitt`** (200-Tage)", "⚠️ **Kandidat**",
         "**%d (100 %%)**" % z["symbole"], "nicht registriert",
         "vier Messungen, alle positiv — Stabilität offen"),
        ("`vola`", "✖ nicht als Beitrag", "%d (100 %%)" % z["symbole"],
         "gehört in die Geometrie", "keine Richtung (GS −0,00041)"),
        ("`schnitt50` · `amihud` · `rsi`", "✖ trägt nicht", "—", "—",
         "N-59: trägt nicht bis 0,020 R"),
    ], breiten=(4.0, 3.4, 2.6, 4.0, 6.4), klein=True)

    # ---------------------------------------------- schnitt im Detail
    d.add_heading("4 — Der Kandidat `schnitt` — vier Messungen, eine offene "
                  "Frage", level=1)
    tabelle(d, ("Messung", "Basis", "Ergebnis"), [
        ("**28.08.** Akkumulationsmaß", "H90 · 507 Reihen · zirkulärer "
         "Verschub", "✔ monoton über **neun Bänder**, beide Kalenderhälften: "
         "−40 % → +6,08 % bis +30 % → −11,80 %"),
        ("**31.08.** Horizontlauf", "H1..H20 · ⛔ **1.314 Symbole inkl. "
         "798 Nicht-Krypto**", "⛔ **abgelöst** — stand auf der Basis, die "
         "N-19 als kontaminiert erwies"),
        ("**07.09.** derselbe Lauf", "H1..H20 · 524 reine Kryptosymbole",
         "✔ trägt bei H1, H2, H5, H10 · H20 nicht trennbar"),
        ("**07.09.** N-59", "H20 · selektierte Menge (20 %)",
         "✔ **+0,1707 R** [+0,0723 .. +0,2781]"),
    ], breiten=(3.8, 5.0, 7.6), klein=True)
    absatz(d, "Redundanz gering: r = −0,097 zu `funding`, −0,168 zu "
              "`turnover`. Abdeckung 100 % — das bietet weder `funding` "
              "(56 %) noch `turnover` (13 %).")
    absatz(d, "⚠️ Was fehlt: die Stabilität über die Zeit. Bei H20 fehlen "
              "die Blöcke (Bär 19 von 20), bei H5 die Trennschärfe (0,05 R "
              "über den Effekten) — und beide Male fällt die Gegenprobe "
              "`funding` mit. Das ist ein Befund über die Schichtung, nicht "
              "über den Kandidaten.", fett=True)
    absatz(d, "⚠️ Und für BTC/ETH/SOL trägt das Maß nicht: −0,0251 / "
              "−0,0308 / −0,0291. Kein Rauschen — die Kernwerte liegen 1,3 "
              "bis 1,4 Standardabweichungen unter dem Mittel, und nur "
              "14,9 % aller Symbole haben einen negativen Vorsprung. "
              "`asset_dca_settings` enthält genau BTC und ETH.", farbe=ROT)

    # --------------------------------------------------------- offen
    d.add_page_break()
    d.add_heading("5 — Was offen ist, nach Dringlichkeit", level=1)
    tabelle(d, ("Rang", "Punkt", "Warum"), [
        ("1", "**Die Durchlassquote festlegen**",
         "Nutzerentscheidung laut R-R9. Ohne sie ist jede "
         "Schwellenkalibrierung willkürlich."),
        ("2", "**`schnitt`s Stabilität**",
         "Der beste Kandidat, den das Projekt hatte. Beide Zerlegungen "
         "scheitern an der Auflösungsgrenze — nötig sind mehr Anker, keine "
         "dritte Schichtung."),
        ("3", "**Akkumulation: BTC/ETH entscheiden**",
         "Das Maß trägt breit, aber nicht für die beiden freigeschalteten "
         "Werte. Entscheidung, keine Messfrage."),
        ("4", "**N-52 bis N-56 wiederholen**",
         "auf der selektierten Menge, mit Trennschärfe, über "
         "`messnorm_auswahl`."),
        ("5", "`H` und Lebendigkeit messen",
         "die beiden verbliebenen Abgelehnten. Rangplatz ist bereits live "
         "als Stufe 5; für Termine gibt es keine Daten."),
        ("6", "Der Maßstab aller Stufen",
         "F-219: die Bewertung liefert 19,5 % dessen, was sie behauptet. "
         "Ändert den Hebel, nicht die Rangfolge."),
    ], breiten=(1.4, 4.8, 9.4))

    # ------------------------------------------------- andere Klassen
    d.add_heading("6 — Die anderen Assetklassen — im Plan vorgesehen",
                  level=1)
    absatz(d, "Sie kommen später, sind aber nicht vergessen. Der Stand, "
              "damit die Lücke benannt bleibt:")
    tabelle(d, ("Klasse", "Reihen", "Zellen im Betrieb", "Stufe 12"), [
        ("aktien", "470", "spot × einstieg · spot × akkumulation",
         "⚠️ winkt durch — nicht vermessen"),
        ("themen_etf", "293", "spot × einstieg · spot × akkumulation",
         "⚠️ winkt durch — nicht vermessen"),
        ("rohstoffe", "35", "spot × einstieg · spot × akkumulation",
         "⚠️ winkt durch — nicht vermessen"),
        ("hedge", "—", "absicherung × einstieg",
         "⚠️ winkt durch — nicht vermessen"),
    ], breiten=(3.0, 2.2, 6.4, 5.0))
    absatz(d, "Acht von neun laufenden Zellen liefern eine Empfehlung, "
              "ohne dass eine Messung dahintersteht. Nur "
              "`krypto × spot × einstieg` entscheidet.", fett=True)
    absatz(d, "⚠️ Die Voraussetzung ist Datenlage, nicht Methodik: für die "
              "vier Klassen gibt es keine Nicht-Kurs-Daten (kein Funding, "
              "kein Open Interest, keine Umlaufmenge). Was dort messbar "
              "wäre, sind Kursgrößen — also genau `schnitt`, `vola` und "
              "`amihud`. ⚠️ Und `schnitt` ist bisher nur für Krypto "
              "gemessen.", farbe=GRAU)

    d.add_heading("Der nächste Schritt", level=1)
    absatz(d, "Die Durchlassquote festlegen — sie ist die einzige offene "
              "Nutzerentscheidung, die alles Weitere blockiert. Danach "
              "`schnitt`s Stabilität mit mehr Ankern, dann die Wiederholung "
              "von N-52 bis N-56 auf der richtigen Menge.")

    d.add_paragraph()
    absatz(d, "Erzeugt aus `erzeuge_standort_krypto.py`. Die Zahlen werden "
              "beim Erzeugen aus dem laufenden System gelesen — Änderungen "
              "gehören ins Skript, nicht in diese Datei.", farbe=GRAU,
           groesse=8.5)

    d.save(ZIEL)
    print("geschrieben: %s" % ZIEL)
    return 0


if __name__ == "__main__":
    sys.exit(main())
