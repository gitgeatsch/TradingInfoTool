# -*- coding: utf-8 -*-
"""Die Messbasen fuers Notebook - als winziges Paket (02.09.2026).

## Der Anlass

Nutzerfrage vor dem Scharfschalten: *„Was ist mit der neuen Datenbank, wie
kommt die auf das NB?"*

⚠️ **`*.db` steht in `.gitignore`.** Ein `git pull` bringt Code, keine
Daten. Und der Produktionscode liest seit dem 31.08. vier Datenbanken, die
es auf dem Notebook nicht gibt:

    data/funding_historie.db       22 MB
    data/onchain_historie.db       22 MB
    data/terminmarkt_historie.db  132 MB
    data/messdaten.db             166 MB

## ⚠️⚠️ Warum das nicht bloss unbequem ist

Fehlen sie, liefert `marktrang.messbasis()` eine **leere Menge**, und
`raenge()` ueberspringt die Groesse mit einem `logger.error` - der Lauf
bricht nicht ab. Beide tragenden Beitraege (Funding, Turnover) haetten
dann keinen Rang, das Potential laege bei **0,000**, und die scharf
geschaltete Stufe 11 sperrte **alles**.

> **Ein Pull ohne diese Dateien schaltet die Kette stumm - und zwar
> lautlos.** Genau der Deadloop, aus dem das System gerade kommt.

## Die Loesung: es sind gar nicht die Daten, die gebraucht werden

Drei der vier Dateien werden vom Produktionscode **nur nach der
Symbolliste** gefragt:

    funding      SELECT DISTINCT symbol FROM funding
    turnover     SELECT DISTINCT symbol FROM splycur
    oi           SELECT DISTINCT symbol FROM terminmarkt_tag
                 UNION SELECT DISTINCT symbol FROM terminmarkt

Aus 176 MB werden damit **wenige Kilobyte**. Nur `messdaten.db` wird
wirklich ausgelesen (`schnitte()` rechnet den 200-Tage-Schnitt) - und die
ist verzichtbar, weil der Schnittabstand am 31.08. als Beitrag gefallen
ist und nur noch als Anzeige laeuft.

## ⚠️ Und warum die Paketdateien sich SELBST kennzeichnen

Eine verkleinerte Datenbank, die aussieht wie eine echte, ist eine Falle:
wer spaeter darauf misst, misst auf einer Attrappe und merkt es nicht -
derselbe Fehlertyp wie „ein alter Wert sieht aus wie ein frischer".

Deshalb traegt jede erzeugte Datei eine Tabelle `_nur_symbolliste` mit
Herkunft, Zeitpunkt und der ausdruecklichen Warnung. `pruefe_pakete.py`
kann sie damit erkennen.

    python baue_messbasis_paket.py --ziel "K:/My Drive/Claude_Austauschordner/Messbasis"
"""
import argparse
import os
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Die Tabellen, aus denen die Symbolliste stammt - je Quelldatei.
# ⚠️ MUSS ZU `marktrang.MESSBASIS` PASSEN. Weicht es ab, baut das Paket
# eine Symbolmenge, die im Betrieb nie gelesen wird.
QUELLEN = {
    "funding_historie.db": [("funding", "symbol")],
    "onchain_historie.db": [("splycur", "symbol")],
    "terminmarkt_historie.db": [("terminmarkt", "symbol"),
                                ("terminmarkt_tag", "symbol")],
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ziel", required=True)
    p.add_argument("--quelle", default="data")
    a = p.parse_args()
    os.makedirs(a.ziel, exist_ok=True)

    # ---- Gegenprobe: passt das zu marktrang.MESSBASIS? -----------------
    from agent import marktrang as MR
    erwartet = {os.path.basename(pfad): frage
                for pfad, frage in MR.MESSBASIS.values()}
    print("=" * 84)
    print("GEGENPROBE — deckt sich das Paket mit `marktrang.MESSBASIS`?")
    print("=" * 84)
    for datei, tabellen in QUELLEN.items():
        frage = erwartet.get(datei, "")
        fehlt = [t for t, _s in tabellen if t not in frage]
        print("  %-30s %s" % (datei,
                              "✔ deckt sich" if not fehlt
                              else "✖ Tabellen fehlen in MESSBASIS: %s" % fehlt))
        if fehlt:
            print("     ⚠️ ABBRUCH - ein Paket, das eine andere Menge baut als")
            print("        der Betrieb liest, ist schlimmer als keines.")
            return 1
    nicht_im_paket = set(erwartet) - set(QUELLEN)
    if nicht_im_paket:
        print("  ⚠️ NICHT im Paket: %s" % sorted(nicht_im_paket))
        print("     (bewusst - `messdaten.db` wird wirklich ausgelesen,")
        print("      nicht nur nach Symbolen gefragt)")

    print()
    print("=" * 84)
    print("PAKET BAUEN")
    print("=" * 84)
    gesamt = 0
    for datei, tabellen in QUELLEN.items():
        quelle = os.path.join(a.quelle, datei)
        if not os.path.exists(quelle):
            print("  %-30s QUELLE FEHLT - uebersprungen" % datei)
            continue
        ziel = os.path.join(a.ziel, datei)
        if os.path.exists(ziel):
            os.remove(ziel)
        q = sqlite3.connect("file:%s?mode=ro" % quelle, uri=True)
        z = sqlite3.connect(ziel)
        n_ges = 0
        for tabelle, spalte in tabellen:
            try:
                syms = [r[0] for r in q.execute(
                    "SELECT DISTINCT %s FROM %s WHERE %s IS NOT NULL"
                    % (spalte, tabelle, spalte))]
            except sqlite3.Error:
                continue
            # ⚠️ DIESELBEN SPALTENNAMEN wie im Original - die Abfrage im
            # Betrieb ist woertlich dieselbe.
            z.execute("CREATE TABLE %s (%s TEXT)" % (tabelle, spalte))
            z.executemany("INSERT INTO %s (%s) VALUES (?)" % (tabelle, spalte),
                          [(s,) for s in syms])
            n_ges += len(syms)
        # Die Selbstkennzeichnung
        z.execute("CREATE TABLE _nur_symbolliste "
                  "(hinweis TEXT, herkunft TEXT, gebaut_am TEXT)")
        z.execute("INSERT INTO _nur_symbolliste VALUES (?,?,?)",
                  ("NUR DIE SYMBOLLISTE - keine Messdaten. Diese Datei "
                   "genuegt dem Betrieb (marktrang.messbasis liest nur "
                   "DISTINCT symbol), ist aber fuer JEDE Messung "
                   "unbrauchbar. Wer hier misst, misst auf einer Attrappe.",
                   datei, __import__("datetime").datetime.now().isoformat()))
        z.commit(); z.close(); q.close()
        kb = os.path.getsize(ziel) / 1024
        gesamt += kb
        print("  %-30s %5d Symbole  ->  %6.1f KB (Original %.0f MB)"
              % (datei, n_ges, kb, os.path.getsize(quelle) / 1e6))
    print()
    print("  Paket gesamt: %.1f KB  (statt 176 MB)" % gesamt)
    print()
    print("  ⚠️ `data/messdaten.db` ist NICHT dabei - sie wird wirklich")
    print("     ausgelesen. Am Notebook entweder `lade_messreihen.py`")
    print("     laufen lassen oder darauf verzichten: der Schnittabstand")
    print("     ist am 31.08. als Beitrag gefallen und ist nur noch Anzeige.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
