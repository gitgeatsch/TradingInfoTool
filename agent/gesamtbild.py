# -*- coding: utf-8 -*-
"""Die Zusammenfuehrung (Umbauplan 93 E, 20.08.2026)

⚠️ FALLSTRICK E1 IST DER WICHTIGSTE DES GANZEN KAPITELS, und er lautet:

    Jede Stufe kann zur Bremse werden, wenn sie zur BEDINGUNG wird. Kein
    Kriterium darf ein Urteil verhindern. Es darf nur bestimmen, welcher Art
    das Urteil ist.

Deshalb ist dieses Modul KEINE Note und KEIN Filter. Es rechnet nichts neu,
es entscheidet nichts, und es kann keinen Einstieg verhindern.

DER TRICK: ES LIEST DIE MAIL, DIE OHNEHIN ENTSTEHT.

Alle vier Stufen setzen bereits ein Etikett - "GUENSTIG", "UNGUENSTIG",
"NOCH KEINE BEWERTUNG MOEGLICH". Dieses Modul zaehlt sie und stellt das
Ergebnis nach vorn. Es gibt also KEINE zweite Rechnung, die von der ersten
abweichen koennte - der Fehler, der dieses Projekt am 18.08. zwei Vormittage
gekostet hat (vier Kopien derselben Stopzeile).

    Vier Merkmale: 1 spricht dafuer, 1 dagegen, 2 noch nicht bewertbar.

⚠️ "NOCH NICHT BEWERTBAR" IST DIE HAEUFIGSTE ANTWORT, und das ist ehrlich.
Die Lebendigkeitsreihe ist erst ab Ende September auswertbar, der Rangplatz
hat gemessen keinen handelbaren Vorteil. Wer daraus eine Note baute, bekaeme
eine Zahl, die Sicherheit vortaeuscht, wo keine ist.

WAS DAS FUER DEN LESER TUT. Die Mail hat sechs Abschnitte und ist lang. Diese
drei Zeilen stehen ganz oben und sagen, wie viel Boden unter der Empfehlung
ist - bevor er die erste Zahl liest.
"""
from __future__ import annotations

# Die Etiketten, die die vier Stufen setzen. Sie stehen hier NICHT als Kopie,
# sondern als das, wonach gesucht wird - wer eines umbenennt, muss hier
# nachziehen, und eine Paketpruefung haelt das fest.
DAFUER = "GUENSTIG"
DAGEGEN = "UNGUENSTIG"
UNBEKANNT = ("NOCH KEINE BEWERTUNG MOEGLICH", "KEIN HANDELBARER VORTEIL",
             "KEINE eigene Messung")

# Die vier Merkmale und die Zeile, an der man sie erkennt. Reihenfolge wie im
# Plan: Trichter (immer), Drift (gemessen), Lebendigkeit (Merkmal), Anlass.
MERKMALE = (
    # ⚠️ "UEBLICHE KURSBEWEGUNG", NICHT "SCHWANKUNGSBREITE UND STOP"
    # (Schritt 31, 2.446-begriffe b). Der Block ist der Trichter - und
    # "Schwankungsbreite" heisst in dieser Mail die ATR. `trichter.saetze`
    # warnt selbst davor, beides zu verwechseln; der Kopf tat es.
    ("Uebliche Kursbewegung", "Uebliche Kursbewegung"),
    ("Rangplatz in der Anlageklasse", "Rangplatz nach"),
    ("Lebendigkeit des Projekts", "Lebendigkeit des Projekts"),
    ("Bekannte Termine", "Bekannte Termine"),
)


def _urteil(zeilen: list[str], anfang: str) -> str | None:
    """dafuer / dagegen / unbekannt - oder None, wenn es den Block nicht gibt.

    ⚠️ NUR DIE ZEILEN DIESES BLOCKS. Ein "UNGUENSTIG" aus dem Trichter darf
    nicht dem Terminblock zugerechnet werden; die Bloecke sind durch
    Leerzeilen getrennt und beginnen mit ihrer Ueberschrift."""
    gefunden, block = False, []
    for z in zeilen:
        # ⚠️ OHNE EINRUECKUNG VERGLEICHEN (Betriebsfund 20.08.2026).
        #
        # In BESTANDSMAILS steht der ganze Rechnungsblock eingerueckt unter
        # "Zusaetzlicher Einstieg:". `startswith` am rohen Text fand den
        # Trichter dort nicht - die Kopfzeile meldete "von 3 pruefbaren
        # Merkmalen", obwohl vier Bloecke in der Mail standen. Gemessen an
        # den echten Mails vom 20.08.: ONDO 4 vorhanden / 3 gezaehlt,
        # VIRTUAL 3 / 2. CAT (nicht eingerueckt) stimmte - deshalb faellt es
        # nur auf, wenn man mehrere Mails nebeneinander legt.
        if z.lstrip().startswith(anfang):
            gefunden, block = True, []
            continue
        if gefunden:
            if not z.strip():
                break
            block.append(z)
    if not gefunden:
        return None
    text = "\n".join(block)
    if DAGEGEN in text:
        return "dagegen"
    if any(w in text for w in UNBEKANNT):
        return "unbekannt"
    if DAFUER in text:
        return "dafuer"
    return "unbekannt"


def bewerte(zeilen: list[str]) -> dict:
    """Was sagen die vier Merkmale? ZAEHLT NUR, RECHNET NICHT."""
    je = {}
    for name, anfang in MERKMALE:
        u = _urteil(list(zeilen or []), anfang)
        if u is not None:
            je[name] = u
    return {"je_merkmal": je,
            "dafuer": sum(1 for v in je.values() if v == "dafuer"),
            "dagegen": sum(1 for v in je.values() if v == "dagegen"),
            "unbekannt": sum(1 for v in je.values() if v == "unbekannt"),
            "vorhanden": len(je)}


def saetze(zeilen: list[str]) -> list[str]:
    """Die drei Zeilen fuer den Kopf der Mail.

    ⚠️ SIE SPERREN NICHTS. Auch "3 dagegen, 0 dafuer" ist kein Veto - es ist
    eine Zusammenfassung dessen, was weiter unten ohnehin steht."""
    from agent.schreibweise import de

    b = bewerte(zeilen)
    if not b["vorhanden"]:
        return []
    teile = []
    if b["dafuer"]:
        teile.append(f"{de(b['dafuer'], 0)} spricht dafuer")
    if b["dagegen"]:
        teile.append(f"{de(b['dagegen'], 0)} dagegen")
    if b["unbekannt"]:
        teile.append(f"{de(b['unbekannt'], 0)} noch nicht bewertbar")
    # "Merkmale", nicht "Auf einen Blick:" (Schritt 31) - die Zeile steht
    # seit S-4 IM Abschnitt "AUF EINEN BLICK", der Titel stand doppelt.
    aus = [f"Merkmale        von {de(b['vorhanden'], 0)} pruefbaren "
           + ", ".join(teile) + "."]
    # ⚠️ WAS DAGEGEN SPRICHT, GEHOERT AN DEN ANFANG DER ZEILE - sonst liest
    # es niemand. Und es ist eine Warnung, keine Sperre.
    dagegen = [n for n, v in b["je_merkmal"].items() if v == "dagegen"]
    if dagegen:
        aus.append("⚠️ Dagegen spricht: " + ", ".join(dagegen)
                   + ". Das ist ein Hinweis, keine Sperre - die Einzelheiten "
                     "stehen unten.")
    aus.append("   Diese Zeile fasst nur zusammen, was weiter unten steht. "
               "Sie verhindert keine Empfehlung und ersetzt keine.")
    return aus


# Woran eine Grenze der Rechnung zu erkennen ist ("Cash frei 418 EUR !!
# reicht fuer diese Position nicht") - dieselbe Marke, die `entscheidungs-
# rechnung.saetze()` und `verkaufsrechnung` fuer Warnungen setzen.
MARKE_GRENZE = "!!"
# Die erste Zeile von `gegenpruefer_rollen.satz()`, wenn Z1 anschlaegt.
Z1_ANGESCHLAGEN = "(Z1) hat angeschlagen"


# Welche Zeile des Blocks die TATSACHE hinter dem UNGUENSTIG traegt: beim
# Terminblock die erste (die Termine stehen nach Naehe sortiert, der naechste
# loest die Warnung aus), sonst die Zeile unmittelbar davor ("Ihr Ziel liegt
# 22,3 % entfernt - JENSEITS ...").
KOPF_TATSACHE_ERSTE_ZEILE = ("Bekannte Termine",)


def _dagegen_satz(zeilen: list[str], anfang: str) -> str | None:
    """Die TATSACHE hinter dem ersten UNGUENSTIG im Block - sonst der Satz.

    ⚠️ SCHRITT 31 (13.09.2026, 2.446-redundanz): hier stand der
    UNGUENSTIG-Satz selbst, gekuerzt am ersten Punkt. Er stand damit im Kopf
    fast woertlich wie weiter unten, und er sagte das WARUM ohne das WAS:
    *"ein Weg dieser Laenge ist in diesem Zeitraum die Ausnahme"* - welcher
    Weg, stand eine Zeile darueber. Der Kopf verspricht "je eine Zeile,
    Einzelheiten weiter unten": die Zeile ist die Tatsache, die Einordnung
    steht unten.

    Rueckfall auf den Satz, wenn die Tatsachenzeile keine Zahl traegt - eine
    Erklaerzeile ist keine Tatsache."""
    gefunden, block = False, []
    for z in zeilen:
        if z.lstrip().startswith(anfang):
            gefunden, block = True, []
            continue
        if gefunden:
            if not z.strip():
                break
            if DAGEGEN in z:
                _t = (block[0] if block and anfang.startswith(
                    KOPF_TATSACHE_ERSTE_ZEILE) else
                      (block[-1] if block else ""))
                _t = _t.strip()
                if "[" in _t:              # Quellenangabe "[federalreserve.gov]"
                    _t = _t[:_t.index("[")].strip()
                # `DAFUER` ist Teilwort von `DAGEGEN` - beide ausschliessen
                # heisst: eine Etikettzeile ist nie die Tatsache.
                if _t and any(c.isdigit() for c in _t) and DAFUER not in _t:
                    return _t
            block.append(z)
            if DAGEGEN in z:
                s = z.strip().replace("⚠️", "").strip()
                # AM SATZENDE KUERZEN, nicht mitten im Satz (erster Kettenlauf
                # 11.09.: "Was dann passiert, entscheidet ..."). Der ganze Satz
                # steht weiter unten.
                ende = s.find(". ")
                if 0 < ende < 180:
                    return s[:ende + 1]
                return s[:160] + ("..." if len(s) > 160 else "")
    return None


def dagegen(zeilen: list[str], gegenpruefung: list | None = None) -> list[str]:
    """S-4 (11.09.2026): WAS DAGEGEN SPRICHT - je eine Zeile, oben in der Mail.

    Aus dem Mailvorschlag vom 11.09. (Befund 2.372): der Leser soll die
    Einwaende sehen, bevor er sechs Abschnitte liest. Wie `saetze()` LIEST
    diese Funktion die fertige Mail - es gibt keine zweite Rechnung. Gesammelt
    wird, was weiter unten ohnehin als Warnung steht:

        die Gegenpruefung widerspricht     erste Zeile beginnt mit ▼
        ein Merkmal steht auf UNGUENSTIG   Trichter, Termine, ...
        eine Grenze der Rechnung           Zeilen mit "!!"
        die Treuepruefung Z1 schlaegt an

    ⚠️ SIE SPERRT NICHTS - und die Einzelheiten bleiben, wo sie waren."""
    aus = []
    g = [str(x) for x in (gegenpruefung or []) if str(x).strip()]
    if g and g[0].startswith("▼"):
        aus.append("✖  Gegenpruefung WIDERSPRICHT - "
                   + g[0].lstrip("▼").strip()[:140])
    je = bewerte(zeilen)["je_merkmal"]
    for name, anfang in MERKMALE:
        if je.get(name) == "dagegen":
            satz = _dagegen_satz(list(zeilen or []), anfang)
            aus.append(f"✖  {name}" + (f" - {satz}" if satz else ""))
    for z in zeilen or []:
        if MARKE_GRENZE in z:
            aus.append("✖  " + " ".join(z.replace(MARKE_GRENZE, "-").split()))
        elif Z1_ANGESCHLAGEN in z:
            # Die Einzelheiten stehen im Anhang B - hier nur der Hinweis, statt
            # einer Zeile, die mit einem Doppelpunkt ins Leere endet.
            aus.append("✖  " + z.strip().rstrip(":")
                       + " - Einzelheiten im Anhang B")
    return aus
