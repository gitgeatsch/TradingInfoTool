# -*- coding: utf-8 -*-
"""Was hat die Umschaltung im echten Betrieb bewirkt? (02.09.2026)

## Der Anlass

Am 02.09. wurde der Codestand vom 29.08. auf den vom 02.09. gezogen und
scharf geschaltet. Die entscheidende Frage danach ist nicht, ob es
laeuft - sondern **wo die Kette jetzt verliert**:

    vorher (Log 30.08.-02.09.)   entscheider zaehlte nur  -> 113 Signale
    nachher                      entscheider verwirft     -> erwartet ~2

## ⚠️ Warum ein eigenes Werkzeug

`notebook_diagnose.json` ist **215 MB**. Die vorhandenen NB-Werkzeuge
laden sie mit `json.load()` komplett in den Speicher; am Desktop geht
das, ist aber langsam und unnoetig. Hier wird STREAMEND gelesen: nur die
Zeilen mit `Durchlaessigkeit` und die Job-Meldungen, alles andere wird
uebersprungen.

## Was ausgewertet wird

  1  der Trichter je Stufe - und ob die NEUE Stufe `terminmarkt` greift
  2  der Verlauf je Tag: aendert sich etwas ab dem Neustart?
  3  Signale und Mails je Tag
  4  ⚠️ die stillen Ausfaelle: fehlt eine Messbasis, steht das als
     `logger.error` im Log - und nur dort

    python pruefe_nb_nach_umschaltung.py
"""
import ast
import collections
import io
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PFAD = (r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"
        r"\notebook_diagnose.json")


def zeilen(pfad):
    """Streamt die Datei und gibt nur die interessanten Zeilen zurueck.

    ⚠️ Die Log-Zeilen stehen als JSON-Strings, also mit \\n maskiert und
    in Anfuehrungszeichen. Ein naiver Zeilenleser findet sie nicht - hier
    wird deshalb ueber die Bloecke gesucht und am maskierten Umbruch
    getrennt.
    """
    rest = ""
    with io.open(pfad, encoding="utf-8", errors="replace") as f:
        while True:
            block = f.read(8 << 20)
            if not block:
                break
            teile = (rest + block).replace("\\n", "\n").split("\n")
            rest = teile.pop()
            for z in teile:
                yield z
    if rest:
        yield rest


_DATUM = re.compile(r"(\d{4}-\d\d-\d\d)")


def _tag(zeile):
    """Das Datum IRGENDWO in der Zeile, nicht nur am Anfang.

    ⚠️ Gefunden beim Selbsttest gegen den Export vom 29.08.: die Log-
    zeilen stehen im JSON als Strings und tragen fuehrende
    Anfuehrungszeichen und Einrueckung. `zeile[:10]` lieferte deshalb
    `"2026-` statt eines Datums, und die Tagesspalte war unbrauchbar.
    """
    m = _DATUM.search(zeile[:60])
    return m.group(1) if m else "?"


def main():
    trichter = collections.defaultdict(lambda: [0, 0])
    je_tag = collections.defaultdict(lambda: collections.defaultdict(
        lambda: [0, 0]))
    laeufe = collections.Counter()
    signale = collections.defaultdict(lambda: [0, 0, 0])
    messbasis_fehler = collections.Counter()
    notizen = collections.Counter()
    andere_fehler = collections.Counter()

    print("Lese %s ..." % PFAD, flush=True)
    for z in zeilen(PFAD):
        if "Durchlaessigkeit" in z:
            m = re.search(r"Durchlaessigkeit: (\{[^}]*\})", z)
            tag = _tag(z)
            if not m:
                continue
            try:
                w = ast.literal_eval(m.group(1))
            except Exception:                                # noqa: BLE001
                continue
            laeufe[tag] += 1
            for stufe, paar in w.items():
                try:
                    b, v = paar
                except (TypeError, ValueError):
                    continue
                trichter[stufe][0] += b
                trichter[stufe][1] += v
                je_tag[tag][stufe][0] += b
                je_tag[tag][stufe][1] += v
        elif "Rollen-Kette Gruende:" in z:
            # ⚠️ DIE NOTIZEN FEHLTEN, und das hat mich am 03.09. zu einem
            # falschen Befund gefuehrt (F-182).
            #
            # Die `Durchlaessigkeit`-Zeile kennt zwei Zahlen: bestanden und
            # verloren. Das Gate kennt DREI Zustaende - der dritte ist
            # `notiz` ("konnte nicht pruefen"). So sah "terminmarkt: 1643
            # bestanden, 0 verloren" aus wie eine Stufe, die 1643 Werte
            # geprueft und alle durchgelassen hat. Tatsaechlich hat sie
            # fast keinen geprueft.
            #
            # Ich habe daraus zuerst einen Systemfehler gemacht. Es war
            # eine Luecke in DIESER Auswertung: `rollen_job` schreibt die
            # Notizen seit dem 02.09. mit, unter dem Schluessel `notiert`.
            #
            # ⚠️ STRUKTURIERT GELESEN, nicht gegrept: meine erste Fassung
            # suchte nach Stichworten und fing damit die ganze
            # Gruende-Zeile ein - unlesbar, und der Zaehler zaehlte Zeilen
            # statt Notizen.
            # ⚠️ KEIN `$` AM ENDE. Die Log-Zeilen stehen im Export als
            # JSON-STRINGS - hinter der Klammer folgen noch
            # Anfuehrungszeichen und Komma. Mit `\s*$` fand der Ausdruck
            # nichts, und die Auswertung meldete "keine Notizen" - genau
            # die Stille, gegen die dieser Block gebaut wurde.
            m = re.search(r"Gruende: (\{.*\})", z)
            if not m:
                continue
            try:
                w = ast.literal_eval(m.group(1))
            except Exception:                            # noqa: BLE001
                continue
            for stufe, teil in (w or {}).items():
                for text, k in (teil or {}).get("notiert") or ():
                    notizen[(stufe, str(text)[:58])] += int(k)
        elif "Signale," in z and "Rollen-Kette" in z:
            m = re.search(r"(\d+) Signale, (\d+) Mails, (\d+) Fehler", z)
            if m:
                t = _tag(z)
                for i in range(3):
                    signale[t][i] += int(m.group(i + 1))
        elif "Marktrang:" in z and ("uebersprungen" in z or "nicht abrufbar" in z):
            messbasis_fehler[z.split("Marktrang:")[1].strip()[:70]] += 1
        elif " ERROR " in z and "Rollen" in z:
            andere_fehler[z.split("ERROR")[1].strip()[:70]] += 1

    if not laeufe:
        print("⚠️ KEINE Durchlaessigkeits-Zeile gefunden - entweder ist der")
        print("   Export aelter als der erste Lauf, oder das Log-Fenster")
        print("   (`log_fenster_stunden`) reicht nicht weit genug zurueck.")
        return 1

    print()
    print("=" * 84)
    print("1) DER TRICHTER — %d Laeufe, %s bis %s"
          % (sum(laeufe.values()), min(laeufe), max(laeufe)))
    print("=" * 84)
    print("  %-26s %10s %10s %9s" % ("Stufe", "bestanden", "verloren",
                                     "Verlust"))
    for stufe, (b, v) in trichter.items():
        marke = "  <- NEU" if stufe == "terminmarkt" else ""
        print("  %-26s %10d %10d %8.1f %%%s"
              % (stufe, b, v, 100 * v / max(b + v, 1), marke))

    print()
    print("=" * 84)
    print("2) JE TAG — wo verliert die Kette, und was kommt heraus?")
    print("=" * 84)
    print("  %-12s %7s %8s %9s %9s %9s %8s"
          % ("Tag", "Laeufe", "hinein", "auswahl-", "termin-", "wiederh-",
             "HERAUS"))
    for tag in sorted(je_tag):
        w = je_tag[tag]
        hin = w["auftrag"][0] + w["auftrag"][1]
        print("  %-12s %7d %8d %9d %9d %9d %8d"
              % (tag, laeufe[tag], hin, w["auswahl"][1],
                 w["terminmarkt"][1], w["wiederholung"][1],
                 w["entscheider"][0]))

    print()
    print("=" * 84)
    print("2b) ⚠️ DIE NOTIZEN — wo eine Stufe NICHT PRUEFEN KONNTE")
    print("=" * 84)
    if notizen:
        print("  `bestanden` heisst 'hat die Stufe passiert', nicht 'wurde")
        print("  geprueft'. Wer nur den Trichter liest, sieht den")
        print("  Unterschied nicht:")
        print("  %-14s %6s  %s" % ("Stufe", "Anzahl", "Notiz"))
        for (stufe, text), n_ in notizen.most_common(10):
            print("  %-14s %6d  %s" % (stufe, n_, text))
    else:
        print("  keine im Log-Fenster (es zeigt nur die haeufigsten je Stufe)")

    print()
    print("=" * 84)
    print("3) SIGNALE UND MAILS")
    print("=" * 84)
    print("  %-12s %9s %9s %9s" % ("Tag", "Signale", "Mails", "Fehler"))
    for t in sorted(signale):
        print("  %-12s %9d %9d %9d" % (t, *signale[t]))

    print()
    print("=" * 84)
    print("4) ⚠️ DIE STILLEN AUSFAELLE")
    print("=" * 84)
    # ⚠️ NACH SCHWERE UNTERSCHEIDEN (02.09.2026). Meine erste Fassung
    # meldete jeden Messbasis-Fehler als "das ist der kritische Fall" - und
    # schrieb dazu, Funding und Turnover haetten keinen Rang. Beim ersten
    # echten Lauf fehlte aber nur `schnitt`, und das ist ABSICHT:
    # `messdaten.db` wurde bewusst nicht mitgegeben, weil der
    # Schnittabstand am 31.08. als Beitrag gefallen ist.
    #
    # Eine Warnung, die den harmlosen Fall wie den kritischen aussehen
    # laesst, wird beim dritten Mal ignoriert - und dann auch der echte.
    _KRITISCH = ("funding", "turnover", "oi")
    _schwer = {m: n for m, n in messbasis_fehler.items()
               if any(k in m.split()[0].lower() for k in _KRITISCH)}
    _harmlos = {m: n for m, n in messbasis_fehler.items() if m not in _schwer}
    if _schwer:
        print("  ⚠️⚠️ EINE TRAGENDE MESSBASIS FEHLT — der kritische Fall:")
        for m, n in sorted(_schwer.items(), key=lambda x: -x[1])[:6]:
            print("     %4dx %s" % (n, m))
        print()
        print("  Ohne sie haben Funding oder Turnover keinen Rang, das")
        print("  Potential liegt bei 0,000 und Stufe 11 sperrt alles.")
        print("  -> die drei Dateien aus `Messbasis` nach `data/` kopieren.")
    if _harmlos:
        print("  ○ nur nachrangige Messbasen fehlen — kein Handlungsbedarf:")
        for m, n in sorted(_harmlos.items(), key=lambda x: -x[1])[:4]:
            print("     %4dx %s" % (n, m))
        print("    `schnitt` ist erwartet: `messdaten.db` (166 MB) wurde")
        print("    bewusst nicht uebertragen. Kostet nur die Anzeigezeile.")
    if not messbasis_fehler:
        print("  ✔ keine Messbasis-Fehler im Log - die drei Dateien liegen")
        print("    am richtigen Ort und werden gelesen.")
    if andere_fehler:
        print()
        print("  Weitere Fehler der Rollen-Kette:")
        for m, n in andere_fehler.most_common(6):
            print("     %4dx %s" % (n, m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
