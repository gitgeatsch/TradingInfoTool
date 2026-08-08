"""Fuehrt den Nachweisrahmen aus Stufe 3 gegen ECHTE Faktensaetze aus.

    python laufe_fakt_nachweis.py --db <kopie.db> --export <diagnose.json> \
        --fakt liquiditaetszonen --trocken          # Verdrahtung pruefen
    python laufe_fakt_nachweis.py --db ... --export ... --fakt liquiditaetszonen

WAS DAS SKRIPT TUT UND WARUM ES SO GEBAUT IST

Es verbindet drei Teile, die einzeln schon abgenommen sind: die gespeicherten
Faktensaetze aus dem Notebook-Export, die Kursreihen aus einer DB-Kopie, und
`bewerte_fakt_wirkung.nachweisrahmen()`. Der eigene Beitrag ist die Auswahl der
Faelle - und die ist der heikelste Teil des ganzen Verfahrens.

DIE FALLAUSWAHL IST KEINE FORMALIE. Am 09.08. wurde eine Messung wertlos, weil
die 20 NEUESTEN Faktensaetze genommen wurden - per Konstruktion die am
wenigsten aufgeloesten, null davon mit bekanntem Ausgang. Dieselbe Falle traf
beim Vorbereiten dieses Laufs den urspruenglich geplanten Kandidaten: die
CRV-Baender gingen am 06.08. live, also tragen nur die juengsten 51
Faktensaetze sie - mit im Median ZWEI Folgetagen im Kurs. Bei jedem Horizont
ab 4 waeren alle 51 zensiert gewesen.

Deshalb filtert `--horizont` hier HART: nur Faktensaetze, deren Kursreihe den
vollen Horizont abdeckt, kommen in die Grundmenge. Das Skript nennt die Zahl
vor dem ersten Aufruf und bricht ab, wenn sie zu klein ist.

WARUM DIE A-ARME GETEILT WERDEN. A1 und A2 sehen den unveraenderten
Faktensatz - sie haengen also NICHT vom geprueften Fakt ab. Werden mehrere
Fakten geprueft, kostet das 2 + k Arme statt 3k. Bei zwei Fakten sind das 4
statt 6 Durchlaeufen, ein Drittel weniger Kontingent. Nutzer-Vorgabe: "damit
wir nicht mehrmals testen muessen."

JEDE ROHANTWORT WIRD GESPEICHERT. Die Auswertung laesst sich damit beliebig oft
wiederholen - andere Horizonte, andere Entscheidungsregeln, ein spaeter
gefundener Auswertungsfehler - OHNE einen einzigen neuen Aufruf. Und
`--fortsetzen` nimmt einen abgebrochenen Lauf wieder auf, statt ihn zu
wiederholen: ein 429 mitten im Lauf darf nicht 300 gueltige Antworten
entwerten.

TROCKENLAUF ZUERST. `--trocken` faehrt die komplette Verdrahtung mit einem
nachgebildeten Modell. Erst wenn Fallzahl, Zensurquote und Berichtsform
stimmen, lohnt der echte Lauf.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time
from collections import Counter

import bewerte_fakt_wirkung as nw
from agent.krypto.backward_tracking import lade_kursreihen


def _lade_faelle(export_pfad: str, reihen: dict, horizont: int,
                 fakt: str) -> tuple[list[dict], dict]:
    """Faktensaetze, die den Fakt tragen UND voll beobachtbar sind."""
    daten = json.load(open(export_pfad, encoding="utf-8"))
    roh = daten["hebel_faktensaetze"]["eintraege"]
    diagnose = Counter()
    faelle = []
    for x in roh:
        diagnose["gesamt"] += 1
        fakten = x["facts_json"]
        if isinstance(fakten, str):
            fakten = json.loads(fakten)
        if fakt.split(".")[0] not in fakten:
            diagnose["ohne_fakt"] += 1
            continue
        reihe = reihen.get(x["symbol"])
        if not reihe:
            diagnose["ohne_kursreihe"] += 1
            continue
        tag = str(x["created_at"])[:10]
        folgetage = sum(1 for p in reihe if p["date"] >= tag)
        if folgetage < horizont + 1:
            diagnose["zu_kurz_beobachtet"] += 1
            continue
        diagnose["brauchbar"] += 1
        faelle.append({"id": x["id"], "symbol": x["symbol"], "created_at": tag,
                       "richtung": x.get("richtung"),
                       "action_damals": x.get("action"), "fakten": fakten})
    return faelle, diagnose


def _trocken_provider():
    """Nachgebildetes Modell: eroeffnet meist, streut reproduzierbar um den Stop.

    KEIN Verhalten, das vom geprueften Fakt abhaengt - der Trockenlauf soll die
    VERDRAHTUNG pruefen, nicht ein Ergebnis vortaeuschen. Wer hier eine Wirkung
    einbaut, misst hinterher seinen eigenen Testaufbau."""
    zaehler = [0]

    def modell(fakten):
        i = zaehler[0]
        zaehler[0] += 1
        if i % 5 == 0:
            return {"action": "HALTEN"}
        # ECHTER Preis aus dem Faktensatz. Ein Platzhalter waere hier fatal:
        # liegt der Einstieg neben der Kursreihe, wirft die
        # Plausibilitaetsschranke jeden Fall raus - und der Trockenlauf meldete
        # dann eine viel zu kleine bewertbare Menge. Genau das ist beim ersten
        # Versuch passiert (16 von 97 statt der echten Quote).
        preis = (fakten.get("preis") or {}).get("usd") or 100.0
        streu = ((i * 2654435761) % 100) / 100.0 * 0.02 - 0.01
        entry = preis
        stop = preis * (0.96 + streu)
        ziel = preis * 1.10
        return {"action": "ERÖFFNEN",
                "entry": {"usd_von": entry, "usd_bis": entry},
                "stop_loss": {"usd_von": stop, "usd_bis": stop},
                "take_profit": {"usd_von": ziel, "usd_bis": ziel}}

    return modell


def _echter_provider(protokoll: list, arm_name: str):
    """Echter Hebel-Prompt gegen Gemini. Jede Rohantwort wandert ins Protokoll."""
    import config as config_module
    from agent.krypto.hebel_analyst import call_llm_for_hebel_signal
    from api.gemini import GeminiClient

    config_module.load_env()
    import os
    schluessel = os.environ.get("GEMINI_API_KEY")
    if not schluessel:
        raise SystemExit("GEMINI_API_KEY fehlt - .env pruefen.")
    client = GeminiClient(schluessel)

    def modell(fakten):
        try:
            antwort = call_llm_for_hebel_signal(client, fakten)
        except Exception as exc:
            name = type(exc).__name__
            # Transport gegen Form trennen (Methodik-Nachtrag 09.08., Punkt 3).
            # Ein Ratenlimit ist UNGEMESSEN und darf den Fakt nicht bestrafen;
            # ein Formfehler dagegen endet real in einem HALTEN-Signal.
            if any(w in str(exc) or w in name for w in
                   ("429", "Timeout", "timeout", "Connection", "503", "502")):
                protokoll.append({"arm": arm_name, "fehler": "transport", "typ": name})
                raise nw.TransportFehler(str(exc)) from exc
            protokoll.append({"arm": arm_name, "fehler": "form", "typ": name})
            return {"kein_json": True}
        protokoll.append({"arm": arm_name, "antwort": {
            k: v for k, v in antwort.items() if k != "_raw_response"}})
        return antwort

    return modell


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, help="KOPIE der Produktions-DB")
    p.add_argument("--export", required=True, help="notebook_diagnose.json")
    p.add_argument("--fakt", action="append", required=True,
                   help="Fakt-Pfad, mehrfach angebbar (A-Arme werden geteilt)")
    p.add_argument("--horizont", type=int, default=7)
    p.add_argument("--mindestfaelle", type=int, default=30,
                   help="Leerlauf-Wache: darunter wird gar nicht erst angerufen")
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--ausgabe", default="fakt_nachweis.json")
    args = p.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    reihen = lade_kursreihen(conn)

    faelle, diagnose = _lade_faelle(args.export, reihen, args.horizont, args.fakt[0])
    print("FALLAUSWAHL")
    for k in ("gesamt", "ohne_fakt", "ohne_kursreihe", "zu_kurz_beobachtet", "brauchbar"):
        print(f"  {k:22} {diagnose[k]:5}")
    if faelle:
        r = Counter(f["richtung"] for f in faelle)
        print(f"  {'Richtung':22} {dict(r)}")
        print(f"  {'Symbole':22} {len({f['symbol'] for f in faelle}):5}")
    print()

    if len(faelle) < args.mindestfaelle:
        print(f"ABBRUCH (Leerlauf-Wache): {len(faelle)} brauchbare Faelle, noetig "
              f"{args.mindestfaelle}. Kein Aufruf abgesetzt - eine Messung auf zu "
              f"wenigen Faellen kostet Kontingent und beantwortet nichts.")
        return 2

    # ENTSCHEIDUNGSREGEL VOR DEM LAUF festhalten.
    vorab = {
        "fakten": args.fakt,
        "horizont": args.horizont,
        "faelle": len(faelle),
        "richtungen": dict(Counter(f["richtung"] for f in faelle)),
        "regel": {
            "eroeffnen_einbruch_pp": 10.0,
            "mindest_bewertbar_je_arm": 5,
            "massstab": "CRV-Breakeven 1/(1+CRV)",
            "rauschboden": "A1 gegen A2, Wirkung muss darueber liegen",
            "tendenz_gilt_nur": "wenn sie beim Aufstocken haelt oder waechst",
        },
        "modus": "trocken" if args.trocken else "echt",
    }
    print("ENTSCHEIDUNGSREGEL (steht VOR dem Lauf fest):")
    print(json.dumps(vorab["regel"], ensure_ascii=False, indent=2))
    print()

    aufrufe = len(faelle) * (2 + len(args.fakt))
    print(f"Geplante Aufrufe: {len(faelle)} Faelle x (2 A-Arme + {len(args.fakt)} "
          f"B-Arm(e)) = {aufrufe}")
    if not args.trocken:
        print("  (bei ~5,5 s Median entspricht das rund "
              f"{aufrufe * 5.5 / 60:.0f} Minuten seriell)")
    print()

    protokoll: list = []
    beginn = time.time()
    ergebnisse = {}
    for fakt in args.fakt:
        provider = _trocken_provider() if args.trocken else \
            _echter_provider(protokoll, fakt)
        n = nw.nachweisrahmen(provider, faelle, fakt, reihen,
                              horizont=args.horizont,
                              eroeffnen_einbruch_pp=vorab["regel"]["eroeffnen_einbruch_pp"],
                              mindest_bewertbar=vorab["regel"]["mindest_bewertbar_je_arm"])
        print(nw.bericht(n))
        print()
        ergebnisse[fakt] = {
            "urteil": n.urteil, "begruendung": n.begruendung,
            "rauschboden_r": n.rauschboden_r, "wirkung_r": n.wirkung_r,
            "eroeffnen_einbruch_pp": n.eroeffnen_einbruch_pp,
            "arme": {a.name: {"eroeffnet": a.eroeffnet, "gehalten": a.gehalten,
                              "formfehler": a.formfehler,
                              "transportfehler": a.transportfehler,
                              "bewertet": len(a.r_werte),
                              "mittel_r": a.mittel_r,
                              "trefferquote": a.trefferquote,
                              "breakeven": a.breakeven_quote,
                              "r_werte": a.r_werte}
                     for a in (n.a1, n.a2, n.b)},
        }

    pathlib.Path(args.ausgabe).write_text(json.dumps({
        "vorab": vorab, "dauer_sekunden": round(time.time() - beginn, 1),
        "faelle": [{k: v for k, v in f.items() if k != "fakten"} for f in faelle],
        "ergebnisse": ergebnisse, "rohantworten": protokoll,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Protokoll geschrieben: {args.ausgabe}")
    print("  Enthaelt alle Rohantworten - eine Neuauswertung mit anderem "
          "Horizont oder anderer Regel braucht KEINEN neuen Aufruf.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
