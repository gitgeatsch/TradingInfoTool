# -*- coding: utf-8 -*-
"""Der HEBEL-NEUBAU - Rollen, Kandidaten und der RIEGEL gegen SPOT.

**27.09.2026.** Nutzervorgabe woertlich: *"WIR sind bei einem NEUBAU des
Hebels, die alten Beitraege sind nicht relevant. NUR HEBEL UMBAU. Die
EINZIGE Gemeinsamkeit ist der Pruefzeitpunkt von SPOT und HEBEL und die
gleichzeitige Bewertung. Der SPOT-Teil kommt spaeter, wenn Hebel
funktioniert - trenne ALT von NEU, sonst killt uns der Umbau."*

Und davor, am 25.09.: *"wir bauen den Hebel-Arm vollstaendig neu. Wenn
Hebel funktioniert, dann gehen wir zu den anderen Strategien."*

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️⚠️ WOZU DIESES MODUL DA IST
═══════════════════════════════════════════════════════════════════════

Ich bin am 26. und 27.09. **dreimal** in den Spot-Arm zurueckgerutscht:

    1. `funding_fuenftel` und `turnover_fuenftel` als "unsere Beitraege"
       behandelt - sie tragen `instrumente=("spot",)` und sind auf H20
       und `bewegung_r` gemessen, also auf der SPOT-Lage
    2. die Kelly-Nullstelle aus `betraege.hebelrechnung` als
       Bewertungsschwelle benutzt - dieselbe Formel, die der Spot-Arm
       fuer seine Quote verwendet
    3. `ema_abstand_atr` als EINSTIEGSSIGNAL vermessen, obwohl es im
       Neubauplan ausdruecklich die RISIKOSPERRE ist (Rolle C)

⚠️ Ein Hinweis in der Doku hat das nicht verhindert. Deshalb steht der
Riegel hier IM CODE: wer eine Hebel-Neubaumessung baut, importiert
`pruefe_quellen()` und bekommt einen ABBRUCH statt einer Warnung.

═══════════════════════════════════════════════════════════════════════
 DIE DREI ROLLEN - aus dem Neubauplan vom 25.09.
═══════════════════════════════════════════════════════════════════════

    A  RICHTUNG              geht es aufwaerts? Trendumkehr?
                             Testform: monotone Ordnung PLUS Spiegelprobe
    B  BEWEGUNGSERWARTUNG    kommt ueberhaupt etwas?
                             Testform: gegen die AUFLOESUNGSRATE, nicht
                             gegen `q` - B ist richtungslos
    C  RISIKOSPERRE          ueberdehnt, ueberhitzt?
                             Testform: AUSSCHLUSSTEST - verbessert das
                             WEGLASSEN des Extrems das Ergebnis des Rests?

    Anordnung:  A und B und NICHT C
                keine Summe, kein gemeinsames Fuenftel

⚠️ Nutzerbefund 25.09.: *"Mein Fehler bis zum 25.09.: alle drei Rollen in
EINE Rangliste geworfen und nach 'oberstes Fuenftel' gefragt."* - und am
27.09. habe ich denselben Fehler wiederholt.
"""
from __future__ import annotations

# ══ DIE ROLLEN ══════════════════════════════════════════════════════
ROLLEN = {
    "A": "Richtung - geht es aufwaerts? Trendumkehr?",
    "B": "Bewegungserwartung - kommt ueberhaupt etwas? (richtungslos)",
    "C": "Risikosperre - ueberdehnt, ueberhitzt?",
}

# ══ DIE KANDIDATEN je Rolle - Stand 27.09.2026 ══════════════════════
#
# ⚠️ "gebaut" heisst: als Merkmal berechenbar und gemessen. "offen"
# heisst: im Neubauplan genannt, aber noch nicht gebaut. Das ist laut
# Plan eine BAUfrage, keine Datenfrage - alle sind aus den vorhandenen
# Stundenkerzen rechenbar.
KANDIDATEN = {
    "A": [
        ("trendstruktur", "offen", "ueber mehrere Zeitebenen"),
        ("ema_lage", "offen", ""),
        ("ema_steigung", "offen", ""),
        ("rsi_aenderung", "offen",
         "tief UND steigend - bisher nur Niveaus gemessen"),
    ],
    "B": [
        ("bandenge", "offen", "Squeeze"),
    ],
    "C": [
        ("ema_abstand_atr", "gemessen",
         "2.642: Risiko-Filter, d 0,521 auf MAE gegen 0,267 auf MFE - "
         "genau die Rolle, die der Plan ihm zuweist"),
    ],
}

# ══ DER RIEGEL ══════════════════════════════════════════════════════
#
# Alles hier drin gehoert zum SPOT-Arm und hat im Hebel-Neubau nichts zu
# suchen. Die Liste ist bewusst KONKRET - ein allgemeines "keine
# Spot-Sachen" haette mich nicht aufgehalten.
SPOT_QUELLEN = {
    "funding_fuenftel": "Spot-Beitrag, instrumente=('spot',), auf H20 und "
                        "bewegung_r gemessen",
    "turnover_fuenftel": "Spot-Beitrag, instrumente=('spot',)",
    "schnitt_fuenftel": "Spot-Beitrag, zustand='null', seit 18.09. "
                        "ausgefallen (2.486-schnitt-tot)",
    "terminmarkt": "Spot-Quelle - der Hebel rechnet aus Stundenkerzen",
    "umlaufmenge": "Spot-Quelle",
    "funding_historie": "Spot-Quelle",
    "onchain_historie": "Spot-Quelle",
}

# ⚠️ Kelly ist KEINE Spot-Quelle, aber die Formel, mit der ich zweimal
# die Bewertung aus dem ERTRAG abgeleitet habe (2.641). Sie gehoert in
# die Erfolgsmessung, nie in die Bewertung.
ERTRAGSGROESSEN = {
    "kelly": "aus q und CRV, also aus ERTRAEGEN - 2.641 verbietet das in "
             "der Bewertung",
    "hebelrechnung": "agent/betraege.py - rechnet die Spot-Quote in einen "
                     "Hebel um; der Neubau ersetzt genau diese Kette",
    "bewegung_r": "Spot-Zielgroesse (H20)",
}


class SpotVermischung(RuntimeError):
    """Eine Hebel-Neubaumessung hat eine Spot-Groesse angefasst."""


def pruefe_quellen(*namen: str, erlaubt: tuple = ()) -> None:
    """ABBRUCH, wenn eine Spot- oder Ertragsgroesse im Hebel-Neubau auftaucht.

    ⚠️ Bewusst ein Abbruch und keine Warnung: eine Warnung haette ich
    dreimal ueberlesen. Wer eine Groesse WIRKLICH braucht, nennt sie in
    `erlaubt` - dann steht die Ausnahme im Aufruf und ist beim Lesen
    sichtbar, statt sich in einem Vorgabewert zu verstecken.

    >>> pruefe_quellen("ema_abstand_atr")           # geht durch
    >>> pruefe_quellen("funding_fuenftel")          # bricht ab
    Traceback (most recent call last):
    hebel_neubau.SpotVermischung: ...
    """
    schlecht = []
    for n in namen:
        k = str(n).strip().lower()
        if k in erlaubt:
            continue
        if k in SPOT_QUELLEN:
            schlecht.append("%s -> %s" % (n, SPOT_QUELLEN[k]))
        elif k in ERTRAGSGROESSEN:
            schlecht.append("%s -> %s" % (n, ERTRAGSGROESSEN[k]))
    if schlecht:
        raise SpotVermischung(
            "HEBEL-NEUBAU: diese Groessen gehoeren zum SPOT-Arm oder sind "
            "Ertragsgroessen und haben hier nichts zu suchen:\n  "
            + "\n  ".join(schlecht)
            + "\n\nDer Hebel wird VOLLSTAENDIG NEU gebaut (Nutzervorgabe "
              "25.09.). Die einzige Gemeinsamkeit mit Spot ist der "
              "PRUEFZEITPUNKT.\nWird eine Groesse wirklich gebraucht, "
              "gehoert sie sichtbar in `erlaubt=(...)`.")


def rollenblatt() -> str:
    """Die drei Rollen und der Stand je Kandidat, in Klartext."""
    z = ["DER HEBEL-NEUBAU - drei Rollen, Anordnung A und B und NICHT C", ""]
    for r in ("A", "B", "C"):
        z.append("  %s  %s" % (r, ROLLEN[r]))
        for name, stand, hinweis in KANDIDATEN[r]:
            z.append("       %-18s %-10s %s" % (name, stand, hinweis[:60]))
        z.append("")
    offen = sum(1 for r in KANDIDATEN.values() for k in r if k[1] == "offen")
    z.append("  ➤ %d von %d Kandidaten sind NOCH NICHT GEBAUT."
             % (offen, sum(len(v) for v in KANDIDATEN.values())))
    z.append("    Laut Neubauplan eine BAUfrage, keine Datenfrage - alle")
    z.append("    sind aus den vorhandenen Stundenkerzen rechenbar.")
    return "\n".join(z)


if __name__ == "__main__":
    # ⚠️ Die Windows-Konsole faellt sonst auf cp1252 zurueck und bricht
    # am ersten Pfeil ab - derselbe Fehler wie in mehreren Messskripten.
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(rollenblatt())
