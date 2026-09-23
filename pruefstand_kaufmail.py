# -*- coding: utf-8 -*-
"""PRUEFSTAND: die CASH-ZEILE in der echten SPOT-KAUFMAIL (K11a).

## Warum es diese Datei gibt

**K11a** steht seit dem 16.09.2026 offen und war der letzte Punkt der
Notebook-Kontrollliste. Der Befund `2.455-cash-gebaut` sagt, warum:

    OFFEN: Cash-Zeile in der Kaufmail (Nutzerblick, Text nicht gespeichert)

⚠️⚠️ **Versandte Mails werden nirgends gespeichert.** Der Punkt war
damit an einen Blick gebunden - eine Prüfung, die niemand wiederholen
kann und die bei jeder Änderung von vorn beginnt.

## Was schon geprueft war - und was nicht

    GEPRUEFT     `entscheidungsrechnung.cash_zeile` isoliert, vier Faelle
                 (Suite, Paket BitpandaCash)
    GEPRUEFT     Log, Export-Abschnitt `bitpanda_bestand`, Tageswert-
                 Spalte `cash_eur` - alle am 16./17.09. am Notebook
    OFFEN        ob die Zeile den Weg in den FERTIGEN MAILTEXT findet

Genau diese Luecke schliesst diese Datei: sie laesst die ECHTE Kette
laufen und sucht die Zeile im fertigen Text.

## Die drei Faelle (F4, Nutzerentscheidung 16.09.)

    1  der Betrag passt ins freie Cash       Zeile OHNE `!!`
    2  er passt nur mit aufgeloesten Orders  `!!` mit Anzahl, Betrag,
                                             aeltester Order
    3  er passt auch dann nicht              Hinweis OHNE `!!`

Dazu 2a: ist der Stand aelter als 6 Stunden (A1), entfaellt das `!!`.

⚠️ Die echte Lage zeigt immer nur EINEN Fall. Deshalb wird die Cash-Lage
in der SPEICHERKOPIE gestellt - ueber den Haken `vorbereiten` von
`pruefstand_hebelmail.baue`, nicht ueber eine zweite Kettenkopie.

## Womit es laeuft

    python pruefstand_kaufmail.py <pfad-zur-sicherung.db> [SYMBOL]

⚠️ NUR LESEND gegenueber Sicherung und Produktion: die Datenbank wird
mit `Connection.backup` in den SPEICHER kopiert, `DB_PATH` zeigt fuer die
Dauer des Laufs auf eine Wegwerfdatei (siehe `pruefstand_hebelmail`).
Kein Modellaufruf, kein Versand.
"""
from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⚠️ DER ECHTE PRUEFSTAND, NICHT EINE KOPIE: `baue` haelt die ganze
# Neutralisierung (Speicherkopie, Bremsen aus, DB_PATH umgebogen,
# Signalhistorie geleert). Eine zweite Fassung waere eine zweite Stelle
# zum Auseinanderlaufen.
from pruefstand_hebelmail import baue                        # noqa: E402

RESERVE_VORGABE = 2000.0


def stelle_cash(frei_fiat: float, gebunden: float, orders: int | None,
                aelteste: str | None = "2026-06-04T03:42:37Z",
                stand: str | None = None, symbol: str = "SOL"):
    """Einen Haken bauen, der Cash-Lage UND Spot-Zwang in der KOPIE setzt.

    ⚠️ Gesetzt werden genau die Meta-Werte, die `toepfe.cash_lage` liest -
    abgelesen dort, nicht geraten:
    `cash_reserve_fiat_eur`, `cash_gebunden_eur`, `cash_orders_anzahl`,
    `cash_aelteste_order` und der Stand.

    ⚠️⚠️ UND DER HEBELSCHALTER WIRD ABGESCHALTET, ohne ihn bleibt dieser
    Pruefstand wirkungslos. `pruefstand_hebelmail.baue` setzt
    `hebel_pruefung_erlaubt` hart auf True - dafuer ist er gebaut. Mein
    erster Lauf uebergab brav `instrument="spot"` und bekam viermal eine
    HEBELmail zurueck (Betreff *„KAUFEN (Hebel, LONG)"*, Hebel 4,41x),
    und die traegt keine Cash-Zeile. Vier saubere ROT-Meldungen ueber
    einen Code, der stimmt.

    ⚠️ Auch ein weiter Stop half nicht: 0,10 bis 0,50 ergaben alle Hebel -
    der SCHALTER entscheidet, nicht die Geometrie. Der Haken laeuft NACH
    `set_hebel_pruefung_erlaubt` und nimmt ihn deshalb zurueck.
    """
    def _hook(con):
        import database.db as DB
        DB.set_hebel_pruefung_erlaubt(con, symbol, False)
        DB.set_meta_wert(con, "cash_reserve_fiat_eur", str(frei_fiat))
        DB.set_meta_wert(con, "cash_gebunden_eur", str(gebunden))
        DB.set_meta_wert(con, "cash_orders_anzahl",
                         "" if orders is None else str(orders))
        DB.set_meta_wert(con, "cash_aelteste_order", aelteste or "")
        if stand is not None:
            DB.set_meta_wert(con, "cash_reserve_synced_at", stand)
    return _hook


def cash_zeilen(erg: dict) -> list[str]:
    """Alle Zeilen der erzeugten Mails, die mit `Cash frei` beginnen."""
    aus = []
    for m in erg.get("mails") or []:
        for z in str(m.get("text") or "").split("\n"):
            if z.strip().startswith("Cash frei"):
                aus.append(z.strip())
    return aus


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    db = sys.argv[1]
    sym = sys.argv[2] if len(sys.argv) > 2 else "SOL"

    print("=" * 96)
    print("PRUEFSTAND KAUFMAIL - die Cash-Zeile im fertigen Text (K11a)")
    print("=" * 96)
    print("  Sicherung: %s" % db)
    print("  Symbol:    %s (Instrument spot, Strategie einstieg)" % sym)

    # ⚠️ DIE FAELLE WERDEN GESTELLT, nicht abgewartet. Die echte Lage
    # zeigt immer nur einen; eine Pruefung, die auf den richtigen Tag
    # wartet, ist keine.
    # ⚠️ DIE BETRAEGE SIND GERECHNET, NICHT GERATEN. `cash_frei_eur` ist
    # Fiat + Stablecoins - Reserve; gegen die Sicherung 23.09. ergaben
    # 2.100 EUR Fiat ein freies Cash von 1.459 EUR - und in das passen
    # 800 EUR Empfehlung MUEHELOS hinein. Mein erster Fall 2 war damit in
    # Wahrheit ein Fall 1, und der Pruefstand meldete ROT ueber sich
    # selbst. Fuer Fall 2 muss gelten: frei < Betrag <= frei + gebunden.
    faelle = [
        ("1 passt",
         stelle_cash(9000.0, 500.0, 2, symbol=sym),
         lambda z: "!!" not in z and "offenen Orders" in z),
        ("2 nur mit Orders",
         stelle_cash(1041.0, 3007.52, 11, symbol=sym),
         lambda z: "!!" in z and "reicht nur, wenn Sie offene Orders" in z),
        ("2a Stand alt (kein !!)",
         stelle_cash(1041.0, 3007.52, 11, symbol=sym,
                     stand="2020-01-01T00:00:00+00:00"),
         lambda z: "!!" not in z and "aelter als 6 Stunden" in z),
        ("3 reicht auch dann nicht",
         stelle_cash(0.0, 10.0, 1, symbol=sym),
         lambda z: "!!" not in z and "auch mit aufgeloesten Orders" in z),
    ]

    rot = 0
    for name, hook, erwartet in faelle:
        print("\n" + "-" * 96)
        print("  FALL %s" % name)
        print("-" * 96)
        try:
            erg = baue(db, sym, instrument="spot", vorbereiten=hook)
        except SystemExit as e:
            print("     ABBRUCH: %s" % e)
            rot += 1
            continue
        zeilen = cash_zeilen(erg)
        mails = erg.get("mails") or []
        betreff = str(mails[0].get("betreff")) if mails else "-"
        print("     Mails: %d   Betreff: %s" % (len(mails), betreff))
        # ⚠️ DER BETREFF GEHOERT IN DIE AUSGABE. Meine erste Fassung zeigte
        # ihn nicht, und vier Laeufe meldeten ROT fuer eine HEBELmail
        # (*„KAUFEN (Hebel, LONG)"*) - die traegt gar keine Cash-Zeile.
        if "Hebel" in betreff:
            print("     ⛔ das ist eine HEBELmail - der Spot-Zwang hat "
                  "nicht gegriffen")
            rot += 1
            continue
        if not zeilen:
            print("     ⛔ KEINE `Cash frei`-Zeile im Mailtext")
            if mails:
                print("        ⚠️⚠️ ERWARTBAR, und das ist der BEFUND zu "
                      "K11a: `rollen_lauf` setzt")
                print("        `cash_frei` und `cash_lage` im TROCKENLAUF "
                      "hart auf None")
                print("        (*\"er hat keine Verbindung zu einer echten "
                      "Lage\"*). Die Zeile")
                print("        KANN hier also nicht entstehen - obwohl "
                      "`cash_lage` gegen")
                print("        dieselbe Verbindung Werte liefert und "
                      "`cash_zeile` daraus")
                print("        den richtigen Text baut. Der Trockenlauf "
                      "ist das einzige")
                print("        Werkzeug fuer die Mail, und genau diese "
                      "Zeile blendet er aus.")
                print("        ➤ Deshalb war K11a seit 16.09. nur "
                      "durch einen BLICK zu")
                print("          beantworten. Solange der Riegel an der "
                      "BETRIEBSART haengt")
                print("          statt an der DATENLAGE, bleibt das so.")
            else:
                print("        (auch keine Mail - der Fall ist nicht "
                      "entstanden, siehe `fehler`: %s)"
                      % (erg.get("fehler") or "-"))
            rot += 1
            continue
        for z in zeilen:
            print("     %s" % z)
        ok = all(erwartet(z) for z in zeilen)
        print("     %s" % ("✔ wie erwartet" if ok
                           else "⛔ ANDERS ALS ERWARTET"))
        if not ok:
            rot += 1

    print("\n" + "=" * 96)
    print("ROT: %d von %d" % (rot, len(faelle)) if rot
          else "ALLE %d FAELLE WIE ERWARTET - K11a ist damit belegt, "
               "und zwar WIEDERHOLBAR" % len(faelle))
    print("=" * 96)
    return 1 if rot else 0


if __name__ == "__main__":
    raise SystemExit(main())
