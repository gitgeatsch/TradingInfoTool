# -*- coding: utf-8 -*-
"""PRUEFSTAND: die ECHTE Hebelmail aus der ECHTEN Kette - ohne Produktion.

⚠️ SCHRITT 41 (Fachpruefung Mail und GUI, 13.09.2026). Die Pruefung braucht
eine AKTUELLE Mail. Versandte Mails werden nirgends gespeichert, und die
Beispiele im Austauschordner reichen nur bis 03.09. - vor der neuen
Gliederung (S-4) und vor Paket B. Eine selbst zusammengesetzte Mail waere
eine Kopie der Kette; geprueft wuerde die Kopie.

## Wie

`rollen_lauf.fuehre_lauf(betriebsart="trocken")` - dieselbe Kette wie im
Betrieb, aber ohne Modellaufruf, ohne Schreiben, ohne Versand; die Mails
kommen im Rueckgabewert. Genau so erzeugt die Suite ihre Hebelmails
(`paket_b1`, `_lauf`).

    Datenbank     KOPIE der Produktionssicherung, im Speicher geoeffnet
                  (`Connection.backup`) - die Sicherung selbst wird nie
                  beschrieben, die Produktion nie beruehrt
    Bremsen       aus (`pruefe_pakete._ohne_bremsen`, ABGELESEN, nicht
                  abgeschrieben) - sonst sperrt der Cooldown der
                  gesicherten Produktion den Wert
    Signalhistorie  geleert - dieselbe Neutralisierung wie in `paket_b1`

## ⚠️ WAS ECHT IST UND WAS GESTELLT

    ECHT          Kurse, ATR, Bestand, Kapital, Marken, Lage, Termine,
                  Kosten, Hebelrechnung, Gliederung - alles, was die Kette
                  deterministisch aus der Datenbank baut
    GESTELLT      die MODELLANTWORTEN (Lagebild, Urteil, Belege) und die
                  MARKTRAENGE - im Trockenlauf gibt es sie nicht. Sie sind
                  im Text als [GESTELLT] markiert und werden in der
                  Fachpruefung NICHT inhaltlich bewertet.

Der Stop des Urteils bildet die echte SOL-Mail vom 12.09. nach: 8,94 %%
unter dem Kurs (88,14 -> 80,26 EUR, Befund 2.390).

AUFRUF:
    python pruefstand_hebelmail.py <pfad-zur-sicherung.db> [SYMBOL] [LONG|SHORT]
    python pruefstand_hebelmail.py <pfad-zur-sicherung.db> [SYMBOL] --schalter
        (Richtungsschalter am abgefangenen Versand - siehe `schalterprobe`)
"""
from __future__ import annotations

import io
import sqlite3
import sys


def betriebskonfiguration() -> dict:
    """Die ECHTE `Basisinfos/config.yaml` - nur die Bremsen abgeschaltet.

    ⚠️⚠️ DIE ERSTE FASSUNG DIESES PRUEFSTANDS UEBERGAB NUR
    `_ohne_bremsen()`. Damit fehlte `rollen_kette.hebel_aus_quote.aktiv`,
    dessen Vorgabe im Code `False` ist - die Mail zeigte "Hebel 1,3x" aus
    dem alten Risikobudget-Weg, den die Produktion seit Paket B gar nicht
    mehr geht (unter 2x wird Spot). Fast waere daraus ein Befund geworden.
    Der Scheduler (`scheduler/rollen_job.py`) reicht die GANZE Konfiguration
    durch - also tut es der Pruefstand auch.

    ⚠️ Gelesen wird die Datei DIESES Geraets. Sie kann von der am Notebook
    abweichen (bekannter Sync-Konflikt der config.yaml)."""
    import copy
    import yaml
    import pruefe_pakete as PP
    with io.open("Basisinfos/config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    ob = PP._ohne_bremsen()
    cfg = copy.deepcopy(cfg)
    cfg.setdefault("rollen_kette", {}).update(ob.get("rollen_kette") or {})
    cfg["anlass"] = {**(cfg.get("anlass") or {}), **(ob.get("anlass") or {})}
    cfg["budget_allocator"] = {**(cfg.get("budget_allocator") or {}),
                               **(ob.get("budget_allocator") or {})}
    return cfg


def baue(db_pfad: str, symbol: str = "SOL", stop_rel: float = 1 - 80.26 / 88.14,
         instrument: str = "hebel", richtung: str = "LONG",
         vorbereiten=None) -> dict:
    """Die echte Kette gegen eine Kopie der Sicherung - ohne Produktion.

    `vorbereiten` ist ein Haken auf die SPEICHERKOPIE, aufgerufen mit der
    Verbindung, bevor die Kette laeuft.

    ⚠️⚠️ WOZU (23.09.2026): `pruefstand_kaufmail` muss die Cash-Lage
    STELLEN koennen - die drei Faelle der Cash-Zeile (F4) haengen an
    Meta-Werten, und die echte Lage zeigt nur EINEN davon. Ohne den Haken
    haette der Kaufmail-Pruefstand diese Funktion KOPIEREN muessen, und
    zwei Kopien derselben Ladung sind zwei Stellen zum Auseinanderlaufen
    (`test-ruft-echten-code-nicht-kopie`).

    ⚠️ Die Kopie liegt im SPEICHER. Was der Haken schreibt, erreicht
    weder die Sicherung noch die Produktion.
    """
    from agent import rollen_eingabe as RE
    from agent import rollen_lauf as RL
    from backtest_llm1_historisch import lade_reihen_aus_db
    import database.db as DBM
    import pruefe_pakete as PP

    q = sqlite3.connect("file:%s?mode=ro" % db_pfad, uri=True)
    con = sqlite3.connect(":memory:")
    q.backup(con)
    q.close()
    con.row_factory = sqlite3.Row
    con.execute("DELETE FROM signals")
    try:
        con.execute("DELETE FROM hebel_signals")
    except sqlite3.Error:
        pass
    con.commit()
    DBM.set_hebel_pruefung_erlaubt(con, symbol, True)
    if vorbereiten is not None:
        vorbereiten(con)
        con.commit()

    reihen = lade_reihen_aus_db(db_pfad)
    if symbol not in reihen:
        raise SystemExit("%s hat keine Kursreihe in %s" % (symbol, db_pfad))
    r = reihen[symbol]
    i = len(r) - 1
    kurs = RE.kurs_eur(symbol, r, i, db_pfad)
    stop = round(kurs * ((1.0 + stop_rel) if richtung == "SHORT"
                         else (1.0 - stop_rel)), 2)
    befund = {
        "aktion": "KAUFEN", "richtung": richtung,
        "einstieg_eur": round(kurs, 2), "stop_eur": stop,
        "belege": [{"fakt": "[GESTELLT] ein Beleg", "richtung": "dafuer",
                    "gewicht": "hoch"}],
        "unabhaengige_faktoren": 2,
        "begruendung": "[GESTELLT] Begruendung des Modells.",
        "was_dagegen": "[GESTELLT] Einwand des Modells.",
        "umgeworfen_durch": "[GESTELLT] Tagesschluss unter der Marke.",
    }
    antworten = {
        "lagebild": {"lage": "[GESTELLT] Lagebild.",
                     "klassen": [{"klasse": "krypto", "einstufung": "neutral",
                                  "warum": "[GESTELLT]"}],
                     "belege": ["[GESTELLT]"]},
        "befund": {symbol: befund},
        "marktraenge": {symbol: {"funding_fuenftel": 0,
                                 "turnover_fuenftel": 0}},
    }
    # ⚠️⚠️ DIE STANDARD-DB UMBIEGEN (14.09.2026) - Pflicht nach
    # Memory `feedback_desktop_kein_produktivstart` (Vorfall 21.07.: ein
    # Pruefskript schrieb eine Zeile in die Desktop-DB, obwohl alle Clients
    # None waren). Die erste Fassung dieses Pruefstands tat es NICHT: die
    # Kette notiert den Abruf der freien CoinMetrics-Quelle in
    # `api_health_status` ueber `get_connection()`, also in
    # `data/tradinginfotool.db` - gemessen am 14.09., die einzige geaenderte
    # Tabelle. Jetzt zeigt `DB_PATH` fuer die Dauer des Laufs auf eine
    # Wegwerfkopie; danach wird er zurueckgesetzt und die Kopie geloescht.
    import shutil
    import tempfile
    from pathlib import Path

    _alt_pfad = DBM.DB_PATH
    _tmp = Path(tempfile.mkdtemp(prefix="pruefstand_")) / "standard.db"
    shutil.copy2(db_pfad, _tmp)
    DBM.DB_PATH = _tmp
    try:
        erg = RL.fuehre_lauf(conn=con, reihen={symbol: r}, symbole=[symbol],
                             betriebsart="trocken", instrument=instrument,
                             strategie="einstieg", antworten=antworten,
                             config=betriebskonfiguration(), db=db_pfad)
    finally:
        DBM.DB_PATH = _alt_pfad
        shutil.rmtree(_tmp.parent, ignore_errors=True)
    erg["_kurs"], erg["_stop"], erg["_tag"] = kurs, stop, r[i].date \
        if hasattr(r[i], "date") else "?"
    return erg


def schalterprobe(db_pfad: str, symbol: str = "SOL") -> list[dict]:
    """Der Richtungsschalter am ECHTEN Versand - LONG und SHORT, beide Modi.

    ⚠️⚠️ WARUM ES DAS BRAUCHT (14.09.2026, Nutzerauftrag nach Schritt 31:
    *"pruefe, dass bei long und short sowie LONG ONLY nichts gebrochen
    ist"*). `baue()` laeuft TROCKEN - und der Trockenlauf kehrt VOR dem
    Schalter zurueck (`if betriebsart == TROCKEN: return`). Er zeigt deshalb
    auch bei `nur_long` eine SHORT-Mail. Das ist kein Fehler, aber es heisst:
    ueber den Versand sagt `baue()` NICHTS.

    Hier laeuft dieselbe Kette SCHARF, mit
      - einem gestellten Modell-Client (dieselben Antworten wie `baue`),
      - `zai_client=None` (keine zweite Meinung, kein Kontingent),
      - einem ABGEFANGENEN Versand (es geht keine Mail hinaus).
    Geschrieben wird nur in die Speicherkopie. ⚠️ Die Kette notiert den
    Abruf der freien CoinMetrics-Quelle in `api_health_status` ueber
    `get_connection()` - seit 14.09. zeigt `DB_PATH` fuer die Dauer von
    `baue()` auf eine Wegwerfkopie (Desktop-DB vorher/nachher hashgleich,
    Befund 2.449). ⚠️ Trotzdem am Notebook nur mit Bedacht: der Lauf ruft
    echte freie Quellen ab und kopiert die angegebene Sicherung.

    Erwartet (gemessen 14.09. an der Sicherung 2026-09-12_0646):
        nur_long LONG  versendet     nur_long SHORT  NICHT versendet
        beide    LONG  versendet     beide    SHORT  versendet
    und in allen vier Faellen ein geschriebenes Signal - der Schalter darf
    die Messung nicht anfassen (Nutzervorgabe 05.08.)."""
    from agent import rollen_lauf as RL
    import json

    orig_cfg, orig_lauf = betriebskonfiguration, RL.fuehre_lauf
    aus = []
    try:
        for modus in ("nur_long", "beide"):
            for ri in ("LONG", "SHORT"):
                gesendet = []

                def _cfg(m=modus):
                    c = orig_cfg()
                    c.setdefault("budget_allocator", {})["hebel_richtung_modus"] = m
                    return c

                def _lauf(**kw):
                    ant = kw["antworten"]

                    class _Gestellt:
                        def chat(self, messages, **k):
                            inhalt = messages[-1]["content"]
                            if symbol not in inhalt:
                                return json.dumps(ant["lagebild"], ensure_ascii=False)
                            return json.dumps(ant["befund"][symbol], ensure_ascii=False)

                    kw.update(betriebsart=RL.SCHARF, client=_Gestellt(),
                              modell="gestellt", zai_client=None,
                              versand=lambda b, t, bilder=None: gesendet.append(b))
                    return orig_lauf(**kw)

                globals()["betriebskonfiguration"] = _cfg
                RL.fuehre_lauf = _lauf
                erg = baue(db_pfad, symbol, richtung=ri)
                m = (erg.get("mails") or [{}])[0]
                aus.append({"modus": modus, "richtung": ri,
                            "versendet": bool(gesendet),
                            "nicht_versendet": m.get("nicht_versendet"),
                            "signal_id": m.get("signal_id")})
    finally:
        globals()["betriebskonfiguration"] = orig_cfg
        RL.fuehre_lauf = orig_lauf
    return aus


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if "--schalter" in sys.argv:
        for z in schalterprobe(sys.argv[1],
                               next((a for a in sys.argv[2:]
                                     if not a.startswith("--")), "SOL")):
            print("%-8s %-5s versendet=%-5s nicht_versendet=%-8s signal_id=%s"
                  % (z["modus"], z["richtung"], z["versendet"],
                     z["nicht_versendet"], z["signal_id"]))
        return
    sym = sys.argv[2] if len(sys.argv) > 2 else "SOL"
    ri = sys.argv[3] if len(sys.argv) > 3 else "LONG"
    erg = baue(sys.argv[1], sym, richtung=ri)
    print("Kurs %.2f EUR, Stop %.2f EUR, Stand %s, Fehler: %s"
          % (erg["_kurs"], erg["_stop"], erg["_tag"], erg.get("fehler") or "-"))
    print("Mails: %d" % len(erg.get("mails") or []))
    for m in erg.get("mails") or []:
        print("=" * 100)
        print("BETREFF:", m.get("betreff"))
        print("=" * 100)
        print(m.get("text"))


if __name__ == "__main__":
    main()
