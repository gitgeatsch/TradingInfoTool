# -*- coding: utf-8 -*-
"""Ist das Ausrollen angekommen? (24.08.2026)

NACH DEM `git pull` UND DEM NEUSTART AUF DEM NOTEBOOK. Dieses Werkzeug fragt
genau das ab, was der Ausrollplan als Beobachtungspunkte nennt - in einem
Aufruf, damit es niemand einzeln zusammensucht.

⚠️ ES LIEST NUR. Keine Zeile wird geschrieben, kein Modell gerufen, kein
Kontingent verbraucht. Es darf deshalb neben der laufenden Produktion laufen.

WAS ES PRUEFT, und warum jeder Punkt einmal teuer war:

    1 SCHEMA        Spalte `strategie`, Tabelle `auswahl_schatten`.
                    ⚠️ Am 22.08. hat eine neue Spalte die App angehalten -
                    geschrieben wurde sie, gelesen nie.
    2 LESEPROBE     ueber den LESEPFAD DES MODELLS, nicht per SELECT. Das
                    Schreiben nennt Spalten einzeln, das Lesen bekommt sie alle.
    3 AUSWAHL       fuellt sich der Schatten? Wie viele Laeufe, wie viele
                    Gewaehlte, wie viele mit Aktion?
    4 TRICHTER      passiert die Stufe `auswahl` plausibel viele - und bleibt
                    der Trichter monoton?
    5 VERKAUFSSEITE traegt sie jetzt Fakten und Merkmale (B1/B2/B3)?
    6 ROHSTOFFE     haben OD7C/H/N/L eigene Kerzen? In der Desktop-Kopie hatten
                    sie NULL - am Notebook ist das zu pruefen.

Aufruf:  python pruefe_ausrollen.py
"""
from __future__ import annotations

import argparse
import sqlite3

GRUEN, ROT, GELB = "OK  ", "FEHL", "?   "


def _sag(zeichen: str, text: str, detail: str = "") -> None:
    print(f"  {zeichen}  {text}")
    if detail:
        print(f"        {detail}")


# ⚠️ NICHT JEDER VERLUST IST EIN FEHLER - und die Unterscheidung gehoert in
# die Zeile, nicht in den Kopf des Lesers (24.08.2026).
#
# DER ANLASS: das Werkzeug meldete "groesster Verlust bei `anlass`" und eine
# Zusammenfassung machte daraus "STALLED - der LLM-Generator haengt". Beides
# falsch: `anlass` ist ein HASH DES FAKTENTEXTES, kein Modell, und ein Verlust
# dort heisst "nichts hat sich geaendert, also nicht noch einmal fragen" - der
# Zweck der Stufe.
#
# DAS PROJEKT KENNT DIE UNTERSCHEIDUNG SCHON ("drei Arten von 'nicht jetzt'"):
# ein gesparter Aufruf ist etwas anderes als ein verworfenes Urteil.
BREMSEN = {
    "anlass": "Faktensatz unveraendert - gewollt, spart einen Aufruf",
    "auswahl": "nicht unter den besten k - gewollt, spart einen Aufruf",
    "wiederholung": "Mindestabstand - gewollt, spart einen Aufruf",
}
LUECKEN = {
    "auftrag": "Instrument/Strategie unzulaessig",
    "fakten": "Datenluecke - hier fehlt etwas",
    "lagebild": "kein Lagebild",
    "urteil": "das Modell wurde GEFRAGT und die Antwort verworfen",
}


def trichterzeilen(conn) -> list:
    """Je Gruppe die juengste Trichterzeile, als (zeichen, text, detail).

    ⚠️ EIGENE FUNKTION, WEIL DIESES STUECK ZWEIMAL FALSCH WAR (24.08.2026):
    einmal las es `bestanden_je_stufe` statt `bestanden` - die Namen der
    Python-Attribute statt der JSON-Schluessel -, und einmal zeigte es nur die
    Auswahl-Stufe, sodass "2 hinein, 0 heraus" dastand, ohne zu sagen, WO die
    zwei geblieben sind.

    Inline in `main()` war es nicht pruefbar. Als Funktion prueft
    `pruefe_pakete` es gegen eine Zeile, die `rollen_gate.schreibe()` WIRKLICH
    geschrieben hat - nicht gegen eine Annahme darueber."""
    import json as _json

    from agent.rollen_gate import STUFEN_NAMEN as _ST
    from agent.rollen_gate import TABELLE as _TAB

    aus = []
    laeufe = [r[0] for r in conn.execute(
        f"SELECT DISTINCT lauf FROM {_TAB} ORDER BY lauf")]
    if not laeufe:
        return [(GELB, "noch kein Durchlauf verzeichnet", "")]
    for lauf in laeufe:
        zeile = conn.execute(
            f"SELECT erfasst_am, hinein, heraus, daten_json FROM {_TAB} "
            f"WHERE lauf = ? ORDER BY rowid DESC LIMIT 1", (lauf,)).fetchone()
        d = _json.loads(zeile["daten_json"] or "{}")
        best = d.get("bestanden") or {}
        verl = d.get("verloren") or {}
        if not best and not verl:
            aus.append((ROT, f"{lauf}: Trichter nicht lesbar",
                        f"erwartet `bestanden`/`verloren`, gefunden "
                        f"{sorted(d)[:6]} - Fehler DIESER Pruefung"))
            continue
        hinein = zeile["hinein"] or 0
        # ⚠️ AUSGESCHRIEBEN, NICHT MIT SCHRAEGSTRICH (24.08.2026, fuenfte
        # Fehllesung). "fakten:3/2" wurde als "3 hinein, 2 fertig" gelesen -
        # es heisst "3 durch, 2 raus". Ein Schraegstrich zwischen zwei Zahlen
        # sagt nicht, was sie bedeuten, und der Leser raet.
        kette = " · ".join(
            f"{s} {best.get(s, 0)} durch"
            + (f" / {verl.get(s, 0)} raus" if verl.get(s) else "")
            for s in _ST if best.get(s) or verl.get(s))
        # ⚠️ ZWEI VERSCHIEDENE FEHLER, die beide "0 heraus" ergeben:
        #    NICHT MONOTON  eine Stufe zaehlt mehr, als hineingegangen sind
        #    LOCH           die Summe aus bestanden und verloren geht nicht auf
        zuviel = [s for s, n in best.items() if n > hinein]
        groesster = max(verl.items(), key=lambda p: p[1], default=(None, 0))
        # ⚠️ JEDE LUECKE WIRD GENANNT, nicht nur die groesste Verlustquelle.
        # Am 24.08. fielen 3 Symbole an der BREMSE und 2 an einer DATENLUECKE -
        # die Bremse war groesser und verdeckte die Luecke. Eine Luecke von 2
        # wiegt schwerer als eine Bremse von 3: die eine ist ein Mangel, die
        # andere der Zweck.
        luecken = []
        for _s, _n in verl.items():
            if _s in LUECKEN and _n:
                _gr = (d.get("gruende") or {}).get(_s) or {}
                _top = max(_gr.items(), key=lambda p: p[1])[0] if _gr else ""
                luecken.append(f"{_s} {_n}x" + (f" ({_top})" if _top else ""))
        grund = ""
        if groesster[0] and groesster[1]:
            gr = (d.get("gruende") or {}).get(groesster[0]) or {}
            art = (BREMSEN.get(groesster[0]) or LUECKEN.get(groesster[0])
                   or "Urteil")
            wo = ("BREMSE" if groesster[0] in BREMSEN else
                  "LUECKE" if groesster[0] in LUECKEN else "URTEIL")
            top = max(gr.items(), key=lambda p: p[1])[0] if gr else ""
            grund = (f"groesster Verlust: `{groesster[0]}` "
                     f"{groesster[1]}x [{wo}: {art}]"
                     + (f" - {top}" if top else ""))
        if zuviel:
            zeichen, detail = ROT, f"⚠️ NICHT MONOTON: {zuviel}"
        # ⚠️ AUF DEN WERT PRUEFEN, NICHT AUF DEN SCHLUESSEL (dritter
        # Fehler in diesem Werkzeug, 24.08.2026). `Durchlauf` legt
        # ALLE Stufen mit 0 an - `"auswahl" in best` ist deshalb immer
        # wahr und sagt nichts darueber, ob die Stufe erreicht wurde.
        elif hinein and not (best.get("auswahl") or verl.get("auswahl")):
            zeichen = GELB
            # ⚠️ NUR DANN GELB, WENN EINE LUECKE SCHULD IST. Haben die
            # BREMSEN alles abgefangen, ist die Auswahl zu Recht nicht
            # drangekommen - es gab nichts Neues zu fragen.
            _bremse = groesster[0] in BREMSEN and not luecken
            zeichen = GRUEN if _bremse else GELB
            detail = (("die Auswahl kam nicht dran, weil vorher gebremst "
                       "wurde - das ist der Zweck der Bremse. "
                       if _bremse
                       else "die Auswahl-Stufe wurde NICHT erreicht - ")
                      + (grund or "die Symbole fielen vorher")
                      + f"  |  {kette}")
        else:
            zeichen = GELB if luecken else GRUEN
            detail = kette + ("  |  " + grund if grund else "")
        if luecken:
            detail += "  |  ⚠️ DATENLUECKE: " + ", ".join(luecken)
        aus.append((zeichen,
                    f"{lauf:12} {str(zeile['erfasst_am'])[:16]} · hinein "
                    f"{hinein} -> heraus {zeile['heraus']}", detail))
    return aus


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--symbol", default="BTC")
    a = p.parse_args()

    c = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    schlecht = 0

    # ---- 1 SCHEMA ------------------------------------------------------
    print("\n1. SCHEMA - was der erste Lauf anlegen sollte")
    spalten = {r[1] for r in c.execute("PRAGMA table_info(signals)")}
    tabellen = {r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for was, da, hinweis in (
            ("Spalte signals.strategie", "strategie" in spalten,
             "entsteht beim ERSTEN Schreiben der Rollen-Kette"),
            ("Tabelle auswahl_schatten", "auswahl_schatten" in tabellen,
             "entsteht beim ERSTEN Lauf")):
        if da:
            _sag(GRUEN, was)
        else:
            _sag(GELB, was + " fehlt noch", hinweis)

    # ---- 2 LESEPROBE ---------------------------------------------------
    print("\n2. LESEPROBE - ueber den Lesepfad des Modells, nicht per SELECT")
    try:
        import database.db as db

        s = db.get_latest_signal(c, a.symbol)
        if s is None:
            _sag(GELB, f"noch kein Signal fuer {a.symbol}",
                 "nach dem ersten Umlauf wiederholen")
        else:
            _sag(GRUEN, f"{s.symbol} {s.action} - strategie = "
                        f"{getattr(s, 'strategie', 'FELD FEHLT')!r}",
                 f"geschrieben {str(s.created_at)[:16]}")
    except Exception as exc:                                 # noqa: BLE001
        schlecht += 1
        _sag(ROT, "der Lesepfad wirft", f"{type(exc).__name__}: {exc}")

    # ---- 3 AUSWAHL -----------------------------------------------------
    print("\n3. AUSWAHL - fuellt sich der Schatten?")
    try:
        from agent import auswahl as AW

        st = AW.stand(c)
        if st["zeilen"]:
            _sag(GRUEN, f"{st['zeilen']} Zeilen aus {st['laeufe']} Laeufen, "
                        f"{st['gewaehlt']} gewaehlt, {st['mit_aktion']} mit Aktion")
            for g in {r[0] for r in c.execute(
                    "SELECT DISTINCT gruppe FROM auswahl_schatten")}:
                s2 = AW.stumme_laeufe(c, g)
                # ⚠️ NULL HEISST ZWEIERLEI: "der letzte Gewaehlte hat
                # gekauft" ODER "es gibt gar nichts zu zaehlen". Das
                # muss dastehen, sonst liest sich eine leere Gruppe wie
                # eine gesunde.
                _wie = (f"{s2['laeufe']} Laeufe in Folge ohne Einstieg"
                        if s2["geprueft"] else
                        "noch KEIN gewaehlter Wert mit Aktion - nichts "
                        "zu zaehlen")
                _sag(GELB if (s2["stumm"] or not s2["geprueft"])
                     else GRUEN,
                     f"{g}: {_wie}"
                     + ("  ⚠️ die Auswahl liefert, die Kette nimmt keinen"
                        if s2["stumm"] else ""))
        else:
            _sag(GELB, "noch keine Zeile", "nach dem ersten Umlauf wiederholen")
    except Exception as exc:                                 # noqa: BLE001
        _sag(GELB, "Schatten noch nicht lesbar", str(exc))

    # ---- 4 TRICHTER ----------------------------------------------------
    print("")
    print("4. TRICHTER - je Gruppe die juengste Zeile, ganze Kette")
    try:
        for zeichen, text, detail in trichterzeilen(c):
            _sag(zeichen, text, detail)
    except Exception as exc:                                 # noqa: BLE001
        _sag(GELB, "Trichter nicht lesbar", str(exc))

    # ---- 5 VERKAUFSSEITE -----------------------------------------------
    print("\n5. VERKAUFSSEITE - traegt sie jetzt Fakten und Merkmale?")
    try:
        for r in c.execute(
                "SELECT action, COUNT(*) n, MIN(LENGTH(facts_json)) mn, "
                "MAX(LENGTH(facts_json)) mx FROM signals "
                "WHERE quelle_kette='rollen' AND action IN "
                "('HALTEN','REDUZIEREN','VERKAUFEN') GROUP BY action"):
            gut = (r["mx"] or 0) > 200
            if not gut:
                schlecht += 0          # noch keine neuen Zeilen ist kein Fehler
            _sag(GRUEN if gut else GELB,
                 f"{r['action']:11} n={r['n']:4}  facts_json "
                 f"{r['mn']} .. {r['mx']} Zeichen",
                 "" if gut else "⚠️ 17 Zeichen = alte Zeilen. Die neuen "
                                "entstehen erst mit dem naechsten Ausstieg")
    except sqlite3.Error as exc:
        _sag(GELB, "Verkaufsseite nicht lesbar", str(exc))

    # ---- 6 ROHSTOFFE ---------------------------------------------------
    print("\n6. ROHSTOFFE - haben sie eigene Kerzen?")
    try:
        import config

        roh = [x.symbol for x in config.get_watchlist()
               if x.assetklasse == "rohstoffe"]
        for sym in roh:
            n = c.execute("SELECT COUNT(*) FROM price_history_ohlc "
                          "WHERE symbol = ?", (sym,)).fetchone()[0]
            if n:
                _sag(GRUEN, f"{sym}: {n} Kerzen")
            else:
                schlecht += 1
                _sag(ROT, f"{sym}: KEINE eigene Kerze",
                     "die langen Reihen liegen nur unter "
                     "_ROHSTOFF_FUTURES_* - damit fehlt hier die Faktenbasis")
    except Exception as exc:                                 # noqa: BLE001
        _sag(GELB, "Watchlist nicht lesbar", str(exc))

    # ---- 7 LAEUFT DIE KETTE UEBERHAUPT? --------------------------------
    #
    # ⚠️ DIE MELDUNG "Alle LLM-Toepfe erschoepft - kein Lauf" HAT ZWEI
    # SEHR VERSCHIEDENE URSACHEN, und `waehle_client` unterscheidet sie nicht:
    #
    #     (a) das Kontingent ist wirklich aufgebraucht
    #     (b) es ist GAR KEIN Client uebergeben - `clients.get(quelle)` gibt
    #         None, die Schleife ueberspringt den Topf, und am Ende steht
    #         dieselbe Zeile. Das passiert, wenn die Schluessel fehlen.
    #
    # (b) ist nach einem Neustart der wahrscheinlichere Fall - und der
    # gefaehrlichere, weil er wie ein Kontingentproblem aussieht und keines
    # ist.
    print("")
    print("7. LAEUFT DIE KETTE - und woran es sonst liegt")
    try:
        from api.llm_basis import verbrauch_heute
        from scheduler.rollen_job import KETTE
        for quelle, modell, budget in KETTE:
            try:
                if quelle == "gemini" and modell:
                    from api.gemini import _kontingent_tag
                    v = verbrauch_heute(f"gemini:{modell}", _kontingent_tag())
                else:
                    v = verbrauch_heute(quelle)
            except Exception:                                # noqa: BLE001
                v = None
            name = f"{quelle}/{modell or chr(45)}"
            if v is None:
                _sag(GELB, f"{name:34} Verbrauch nicht lesbar")
            elif v >= budget * 0.85:
                _sag(GELB, f"{name:34} {v} von {budget} - Topf fast leer")
            else:
                _sag(GRUEN, f"{name:34} {v} von {budget}")
    except Exception as exc:                                 # noqa: BLE001
        _sag(GELB, "Kontingent nicht lesbar", str(exc))

    # Und die einfachste Frage von allen: kam seit dem Neustart ueberhaupt
    # ein Urteil an?
    try:
        letzte = c.execute(
            "SELECT MAX(created_at) FROM signals WHERE quelle_kette='rollen'"
        ).fetchone()[0]
        _sag(GRUEN if letzte else GELB,
             f"juengste Zeile der Rollen-Kette: {letzte or 'KEINE'}",
             "" if letzte else "die Kette hat noch nie geschrieben")
    except sqlite3.Error as exc:
        _sag(GELB, "Signaltabelle nicht lesbar", str(exc))

    c.close()
    print("\n" + "=" * 68)
    print("ALLES GRUEN" if not schlecht else f"{schlecht} PUNKT(E) OFFEN")
    print("⚠️ Gelb heisst 'noch nicht da' - nach dem ersten Umlauf "
          "wiederholen.\n   Rot heisst: nachsehen, bevor der naechste Lauf "
          "darauf aufbaut.")
    return 1 if schlecht else 0


if __name__ == "__main__":
    raise SystemExit(main())
