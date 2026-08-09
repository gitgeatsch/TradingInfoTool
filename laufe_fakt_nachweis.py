"""Fuehrt den Nachweisrahmen aus Stufe 3 gegen ECHTE Faktensaetze aus.

    python laufe_fakt_nachweis.py --db <kopie.db> --fakt liquiditaetszonen --trocken
    python laufe_fakt_nachweis.py --db <kopie.db> --fakt liquiditaetszonen \
        --fakt antizyklisch --pause 2.0 --ausgabe lauf.json

WAS DAS SKRIPT TUT UND WARUM ES SO GEBAUT IST

Es verbindet drei Teile, die einzeln schon abgenommen sind: die gespeicherten
Faktensaetze aus `hebel_signals.facts_json`, die Kursreihen aus derselben
DB-Kopie, und `bewerte_fakt_wirkung.nachweisrahmen()`. Der eigene Beitrag ist
die Auswahl der Faelle - und die ist der heikelste Teil des ganzen Verfahrens.

NICHT aus dem Notebook-Export: der fuehrt nur eine geschichtete Stichprobe
(268 von 1.203, 14-Tage-Fenster) fuer eine andere Frage. Aus der DB kommen
600 statt 122 Faelle und 17 statt 12 Symbole - siehe _lade_faelle().

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


def _lade_faelle(conn, reihen: dict, horizont: int, fakt: str,
                 deckel_je_symbol: int) -> tuple[list[dict], dict]:
    """Faktensaetze aus der DATENBANK, die den Fakt tragen und voll beobachtbar sind.

    WARUM AUS DER DB UND NICHT AUS DEM EXPORT (Korrektur 2026-08-09). Der erste
    Entwurf zog aus `hebel_faktensaetze` im Notebook-Export - und das ist eine
    GESCHICHTETE STICHPROBE fuer einen anderen Zweck: 268 gezogen, 935 bewusst
    NICHT gezogen, rollierendes Fenster von 14 Tagen, je Zelle (Tag x action)
    zwoelf Stueck. Sie beantwortet "kommt ein neuer Fakt-Block im Betrieb an",
    nicht "wie wirkt ein Fakt".

    Der Unterschied ist gross, und er trifft genau die Groesse, auf die es
    ankommt:

        aus dem Export:  122 Faelle auf 12 Symbolen
        aus der DB:      600 Faelle auf 17 Symbolen (Horizont 7)

    `hebel_signals` fuehrt `facts_json` auf ALLEN 1.905 Zeilen ueber 33 Symbole.

    DECKEL JE SYMBOL statt blindem Kuerzen. Die effektive Stichprobengroesse ist
    die Zahl distinkter Symbole (Methodik 2.5) - und die bleibt bei JEDEM Deckel
    gleich (17). Ein Deckel kostet also fast keine Aussagekraft, senkt aber die
    Laufzeit erheblich UND die Konzentration des groessten Symbols (ohne Deckel
    15,5 %, bei 15 nur noch 7,5 %). Gezogen wird ueber den Zeitraum verteilt,
    nicht die ersten N - sonst haengt alles an einer Marktphase."""
    diagnose = Counter()
    je_symbol: dict[str, list] = {}
    for r in conn.execute("SELECT id, symbol, created_at, action, richtung, "
                          "facts_json FROM hebel_signals ORDER BY created_at"):
        diagnose["gesamt"] += 1
        try:
            fakten = json.loads(r["facts_json"])
        except (TypeError, json.JSONDecodeError):
            diagnose["kein_faktensatz"] += 1
            continue
        if fakt.split(".")[0] not in fakten:
            diagnose["ohne_fakt"] += 1
            continue
        reihe = reihen.get(r["symbol"])
        if not reihe:
            diagnose["ohne_kursreihe"] += 1
            continue
        tag = str(r["created_at"])[:10]
        if sum(1 for p in reihe if p["date"] >= tag) < horizont + 1:
            diagnose["zu_kurz_beobachtet"] += 1
            continue
        fakten["_fall_id"] = r["id"]
        je_symbol.setdefault(r["symbol"], []).append(
            {"id": r["id"], "symbol": r["symbol"], "created_at": tag,
             "richtung": r["richtung"], "action_damals": r["action"],
             "fakten": fakten})

    faelle = []
    for symbol, eigene in sorted(je_symbol.items()):
        if deckel_je_symbol and len(eigene) > deckel_je_symbol:
            schritt = max(1, len(eigene) // deckel_je_symbol)
            eigene = eigene[::schritt][:deckel_je_symbol]
            diagnose["durch_deckel_gekuerzt"] += 1
        faelle.extend(eigene)
    diagnose["brauchbar"] = len(faelle)
    diagnose["symbole"] = len(je_symbol)
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


def _lade_bekannte_antworten(pfad: str | None) -> dict:
    """Antworten eines frueheren Laufs, als {(arm, fall_id): antwort}.

    WOZU. 488 Aufrufe am Stueck reissen das Ratenlimit - die Messung vom 09.08.
    brach nach rund 25 schnellen Aufrufen ein. Ohne Wiederaufnahme waere jeder
    Abbruch ein Totalverlust, und der zweite Versuch wuerde dieselben Fragen
    erneut stellen.

    Ein Transportfehler gilt dabei ausdruecklich NICHT als beantwortet
    (Methodik-Nachtrag 09.08., Punkt 3): sonst zementiert der erste misslungene
    Lauf seine eigenen Luecken."""
    if not pfad or not pathlib.Path(pfad).exists():
        return {}
    daten = json.loads(pathlib.Path(pfad).read_text(encoding="utf-8"))
    bekannt = {}
    for e in daten.get("rohantworten", []):
        if "antwort" not in e or e.get("fall_id") is None:
            continue          # Transport- und Formfehler: erneut versuchen
        bekannt[(e["arm"], e["fall_id"])] = e["antwort"]
    return bekannt


def _echter_provider(protokoll: list, arm_name: str, bekannt: dict,
                     pause_sekunden: float):
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

    zaehler = [0]

    def modell(fakten, arm=None):
        # `arm` kommt seit 09.08. von bewerte_arm() und ist A1/A2/B. Ohne ihn
        # landeten im ersten echten Lauf alle drei Arme unter demselben
        # Schluessel (dem FAKTNAMEN) - eine Wiederaufnahme daraus haette sie
        # stillschweigend gleichgemacht.
        schluessel_arm = f"{arm_name}/{arm}" if arm else arm_name
        fall_id = fakten.get("_fall_id")
        vorhanden = bekannt.get((schluessel_arm, fall_id))
        if vorhanden is not None:
            protokoll.append({"arm": schluessel_arm, "fall_id": fall_id,
                              "antwort": vorhanden, "quelle": "wiederverwendet"})
            return vorhanden
        # Drossel: der freie Endpunkt bricht bei schnellen Serien ein.
        if zaehler[0]:
            time.sleep(pause_sekunden)
        zaehler[0] += 1
        try:
            antwort = call_llm_for_hebel_signal(client, fakten)
        except Exception as exc:
            name = type(exc).__name__
            # Transport gegen Form trennen (Methodik-Nachtrag 09.08., Punkt 3).
            # Ein Ratenlimit ist UNGEMESSEN und darf den Fakt nicht bestrafen;
            # ein Formfehler dagegen endet real in einem HALTEN-Signal.
            if any(w in str(exc) or w in name for w in
                   ("429", "Timeout", "timeout", "Connection", "503", "502")):
                protokoll.append({"arm": schluessel_arm, "fall_id": fall_id,
                                  "fehler": "transport", "typ": name})
                raise nw.TransportFehler(str(exc)) from exc
            protokoll.append({"arm": schluessel_arm, "fall_id": fall_id,
                              "fehler": "form", "typ": name})
            return {"kein_json": True}
        protokoll.append({"arm": schluessel_arm, "fall_id": fall_id, "antwort": {
            k: v for k, v in antwort.items() if k != "_raw_response"}})
        return antwort

    return modell


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, help="KOPIE der Produktions-DB")
    p.add_argument("--deckel-je-symbol", type=int, default=15,
                   help="hoechstens so viele Faelle je Symbol (0 = kein Deckel). "
                        "Kostet keine Symbole und damit fast keine Aussagekraft, "
                        "senkt aber Laufzeit und Konzentration deutlich")
    p.add_argument("--fakt", action="append", required=True,
                   help="Fakt-Pfad, mehrfach angebbar (A-Arme werden geteilt)")
    p.add_argument("--horizont", type=int, default=7)
    p.add_argument("--mindestfaelle", type=int, default=30,
                   help="Leerlauf-Wache: darunter wird gar nicht erst angerufen")
    p.add_argument("--trocken", action="store_true")
    p.add_argument("--ausgabe", default="fakt_nachweis.json")
    p.add_argument("--fortsetzen", help="Protokoll eines abgebrochenen Laufs")
    p.add_argument("--pause", type=float, default=1.5,
                   help="Sekunden zwischen zwei Aufrufen (freier Endpunkt "
                        "bricht bei schnellen Serien ein)")
    args = p.parse_args()

    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    reihen = lade_kursreihen(conn)

    faelle, diagnose = _lade_faelle(conn, reihen, args.horizont, args.fakt[0],
                                   args.deckel_je_symbol)
    print("FALLAUSWAHL (Quelle: hebel_signals.facts_json, NICHT der Export)")
    for k in ("gesamt", "kein_faktensatz", "ohne_fakt", "ohne_kursreihe",
              "zu_kurz_beobachtet", "brauchbar"):
        print(f"  {k:22} {diagnose[k]:5}")
    if faelle:
        z = Counter(f["symbol"] for f in faelle)
        r = Counter(f["richtung"] for f in faelle)
        groesste = max(z.values()) / len(faelle)
        print(f"  {'Richtung':22} {dict(r)}")
        print(f"  {'Symbole':22} {len(z):5}   <- die EFFEKTIVE Stichprobe (Methodik 2.5)")
        print(f"  {'groesstes Symbol':22} {groesste:5.1%}"
              + ("   ACHTUNG >25 %" if groesste > 0.25 else "   (unter der 25-%-Grenze)"))
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
        "symbole": len({f["symbol"] for f in faelle}),
        "deckel_je_symbol": args.deckel_je_symbol,
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
    if len({f["symbol"] for f in faelle}) < 50:
        print(f"  HINWEIS: {len({f['symbol'] for f in faelle})} Symbole liegen unter "
              f"der n>=50-Schwelle aus Methodik 2.5. Ein Befund aus diesem Lauf "
              f"ist HYPOTHESENGENERIEREND, nicht operationalisierbar - er darf "
              f"keine Schwelle verschieben und kein Gate begruenden.")
    if not args.trocken:
        print("  (bei ~5,5 s Median entspricht das rund "
              f"{aufrufe * 5.5 / 60:.0f} Minuten seriell)")
    print()

    bekannt = _lade_bekannte_antworten(args.fortsetzen)

    # DER TROCKENLAUF MUSS AUCH DEN ECHTEN ZWEIG BERUEHREN (2026-08-09).
    # Der erste echte Lauf brach nach null LLM-Aufrufen mit einem TypeError ab:
    # `_echter_provider()` hatte zwei Argumente mehr bekommen, die Aufrufstelle
    # war nicht mitgezogen. Der Trockenlauf konnte das nicht finden - er nimmt
    # den ANDEREN Zweig des Ternaers und faehrt nie am echten Provider vorbei.
    #
    # Ein Trockenlauf, der genau die Stelle auslaesst, die nur der echte Lauf
    # benutzt, prueft die Verdrahtung nur zur Haelfte. Deshalb wird die Fabrik
    # hier auch trocken AUFGEBAUT (sie setzt dabei keinen einzigen Aufruf ab) -
    # ein Signaturfehler faellt damit im Trockenlauf auf, nicht erst nach dem
    # Start.
    import inspect
    noetig = set(inspect.signature(_echter_provider).parameters)
    print(f"Signaturpruefung _echter_provider: {sorted(noetig)}")
    if args.trocken:
        try:
            _echter_provider(protokoll_probe := [], "probe", {}, 0.0)
            print("  OK - die echte Provider-Fabrik laesst sich aufbauen "
                  "(kein Aufruf abgesetzt)")
        except SystemExit as exc:
            print(f"  HINWEIS - Fabrik nicht aufbaubar: {exc}")
        except TypeError as exc:
            print(f"  ABBRUCH - Signaturfehler, der echte Lauf wuerde sofort "
                  f"scheitern: {exc}")
            return 3
    print()
    if bekannt:
        print(f"Wiederaufnahme: {len(bekannt)} Antworten aus {args.fortsetzen} "
              f"werden wiederverwendet, nicht erneut angefragt.")
        print()
    protokoll: list = []
    beginn = time.time()
    ergebnisse = {}
    for fakt in args.fakt:
        provider = _trocken_provider() if args.trocken else \
            _echter_provider(protokoll, fakt, bekannt, args.pause)
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
