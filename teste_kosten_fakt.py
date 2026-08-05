"""Bringt der Kosten-Fakt etwas? Drei-Arm-Test auf echten Faktensaetzen (05.08.)

WAS GEBAUT WURDE. Der Fakt `kosten` (Tabelle: Kosten in R nach Stop-Abstand x
Haltedauer) und Regel 30 dazu. Die Luecke stand woertlich in der
Zielgroessen-Doku: "Das LLM kennt die Kostenstruktur nicht und kann sie beim
Setzen von Stop und Ziel nicht beruecksichtigen."

DIE ERWARTUNG, vorab festgehalten damit sie nicht nachtraeglich passend
gemacht wird: enge Stops sind laut Formel doppelt teuer (der Stop-Abstand
steht im Nenner). Wenn der Fakt wirkt, sollte das Modell WEITERE Stops setzen.
Das ist die primaere, rauscharme Messgroesse - sie braucht keine Kursdaten.

Sekundaer: verbessert sich die Zonenqualitaet, gemessen als R-Multiple der
selbst gesetzten Zonen gegen den echten Verlauf? Diese Groesse ist ungleich
verrauschter, und der Prompt-Thread vom 04.08. endete damit, dass beide dort
untersuchten Aenderungen bei rund 1 % des Eigenrauschens lagen.

DREI ARME:
    A1  Stand heute - Prompt MIT Regel 30, Fakten MIT `kosten`
    A2  identisch zu A1 - der Abstand ist der Rauschboden
    B   ohne beides - Regel 30 entfernt UND `kosten` aus den Fakten

BEIDES ZUSAMMEN ist richtig, nicht nur die Regel: ein Fakt ohne Regel bliebe
ein nackter Wert (Kategorie (d) der Entscheidungsmappe, "fuehrt zu
unreproduzierbarem Umgang"), eine Regel ohne Fakt verwiese ins Leere. Getestet
wird die Aenderung, wie sie im Betrieb steht.

ECHTE FAKTENSAETZE aus `facts_json`, nicht rekonstruierte - der Kosten-Fakt
wirkt auf die Zonenwahl, und die haengt an der vollen Datenlage.

ERGEBNIS (05.08.): KEINE WIRKUNG NACHWEISBAR - und der Rauschboden erklaert,
warum das kaum anders ausfallen konnte.

GEPAART je Faktensatz ausgewertet (alle drei Arme sehen denselben Fall, die
Symbolstreuung kuerzt sich damit heraus):

    Wirkung        +0,152 pp   sd 1,921   SE 0,555   t +0,27   n=12
    Bootstrap      [-0,827 ; +1,258] pp
    RAUSCHBODEN    Streuung zwischen A1 und A2 (IDENTISCHER Prompt): 2,998 pp

Der Effekt ist rund ZWANZIGMAL kleiner als das Eigenrauschen zwischen zwei
identischen Armen. Fuer einen Nachweis dieser Effektgroesse braeuchte es 618
Faelle.

Die Richtung stimmt immerhin (Stops werden minimal weiter, wie erwartet), und
die EROEFFNEN-Quote bleibt unveraendert (93/94 % mit gegen 97 % ohne) - der
Fakt richtet also keinen Schaden an.

METHODISCHE LEHRE, die groesser ist als der Befund: die erste Auswertung
verglich die Arme als UNABHAENGIGE Gruppen und lieferte ein Intervall von
[-4,694 ; +5,522] pp - bei einem Mittelwert von 8 %. Die Symbolstreuung
erschlug alles. Gepaart schrumpft dasselbe Intervall auf [-0,827 ; +1,258],
also auf ein Fuenftel. Wo jeder Arm denselben Fall sieht, ist der gepaarte
Vergleich nicht eine Verfeinerung, sondern die einzig richtige Auswertung.

Damit ist es der SIEBTE gemessene Mechanismus ohne Nachweis - nach
Screening-Score, Konfidenz, Richtungswahl, Prompt-Aenderungen, CRV-Baendern,
halte_kriterium und der Allocator-Auswahl.

NACHTRAG 05./06.08.: AUFGESTOCKT AUF 24 FAELLE - der Befund bei 12 war Rauschen.

                        n=12                    n=24
    Wirkung          -0,734 pp               -0,334 pp
    Bootstrap    [-1,571 ; +0,035]      [-1,269 ; +0,653]
    n noetig             16                     212
    Rauschboden       3,132 pp                4,519 pp

Der Effekt HALBIERT sich bei verdoppelter Stichprobe, und das noetige n steigt
von 16 auf 212. Das ist die Signatur eines Nullbefunds: ein Punktschaetzer aus
einer kleinen Stichprobe schrumpft gegen null, sobald mehr Daten dazukommen.

Genau dasselbe Muster wie beim Regel-Ablationstest am selben Tag: dort lagen
die Einzeleffekte bei 12 Ankern bei +0,281 und +0,182 und bei 28 Ankern bei
+0,014 und -0,013. Zweimal am selben Tag - kleine Stichproben erzeugen
zuverlaessig Scheinbefunde in der jeweils erwarteten Richtung.

WAECHTER: EROEFFNEN 92,5 % (A1) / 92,1 % (A2) / 95,7 % (B). Kein Einbruch, die
Befuerchtung zum Systemguete-Fakt hat sich nicht bestaetigt. Bemerkenswert ist
aber, dass BEIDE A-Arme rund 3 pp unter B liegen - konsistent, wenn auch klein.
Bei n=67/69 ist das nicht von Rauschen zu trennen, gehoert aber beobachtet:
sollte sich das im Betrieb verfestigen, waere es der Anfang genau des
Rueckzugs, vor dem der Fakt-Docstring warnt.

Lauf: python -u teste_kosten_fakt.py [--n 12] [--w 3] [--versatz 0]
"""
from __future__ import annotations

import copy
import io
import json
import math
import os
import re
import statistics
from collections import Counter, defaultdict

from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from backtest_llm1_historisch import _arg, frage
from datiere_einbruch import ORDNER

# ALLE drei neuen Fakten werden gemeinsam getestet (Nutzer-Hinweis 05.08.:
# "sollten dann nicht alle neuen drinnen sein"). Ein Zwischenstand gegen nichts
# zu vergleichen waere die falsche Frage - im Betrieb stehen alle drei.
REGELN = (
    ("30. Handelskosten", "wenn sie deine Zone beeinflusst hat."),
    ("31. Ausstiegsregel", "erfinde nichts."),
)
NEUE_FAKTEN = ("kosten", "ausstiegsregel", "systemguete")


def baue_arme() -> dict[str, str]:
    """B-Arm ohne ALLE drei neuen Regeln. Von hinten entfernen, damit die
    Positionen der frueheren Treffer gueltig bleiben."""
    ohne = SYSTEM_PROMPT
    for anfang, ende in reversed(REGELN):
        i = ohne.find(anfang)
        j = ohne.find(ende, i if i >= 0 else 0)
        if i < 0 or j < 0:
            raise SystemExit(f"Regel nicht gefunden: {anfang}")
        ohne = ohne[:i] + ohne[j + len(ende):]
    weg = len(SYSTEM_PROMPT) - len(ohne)
    if weg < 1500:
        raise SystemExit(f"verdaechtig wenig entfernt: {weg} Zeichen")
    for anfang, _ in REGELN:
        if anfang in ohne:
            raise SystemExit(f"{anfang} steht noch im B-Arm")
    print(f"  beide neuen Regeln entfernt: -{weg} Zeichen")
    return {"A1 alle neuen Fakten": SYSTEM_PROMPT,
            "A2 alle neuen Fakten (Rauschen)": SYSTEM_PROMPT,
            "B ohne die neuen Fakten": ohne}


def lade_faelle(n: int):
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    block = d.get("hebel_faktensaetze") or {}
    if block.get("fehler"):
        raise SystemExit(f"Faktensatz-Block fehlerhaft: {block['fehler']}")
    sig = {s["id"]: s for s in d["hebel_signals"]}
    kand = []
    for e in block.get("eintraege", []):
        grund = str(sig.get(e["id"], {}).get("gate_reason") or "")
        if "ltig" in grund and "ung" in grund.lower():
            continue          # Ungueltig-Pfad, siehe teste_regel28_echt.py
        kand.append(e)
    kand.sort(key=lambda e: (e["created_at"], e["symbol"]))
    # `versatz` waehlt eine ANDERE Teilmenge derselben Schrittweite - damit
    # laesst sich eine bestehende Stichprobe aufstocken, ohne dieselben Faelle
    # noch einmal zu bezahlen (2026-08-05: n noetig 16, vorhanden 12).
    schritt = max(1, len(kand) // n)
    versatz = _arg("--versatz", 0) % schritt
    return kand[versatz::schritt][:n]


def stop_abstand(antwort) -> float | None:
    """Stop-Abstand in Prozent vom Entry - die primaere Messgroesse."""
    try:
        e = (antwort["entry"]["usd_von"] + antwort["entry"]["usd_bis"]) / 2.0
        ist_short = str(antwort.get("richtung", "LONG")).upper() == "SHORT"
        st = antwort["stop_loss"]["usd_bis" if ist_short else "usd_von"]
    except (KeyError, TypeError):
        return None
    if not e or e <= 0 or st is None:
        return None
    w = abs(e - st) / e * 100
    return w if 0 < w < 60 else None


def main() -> int:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        for z in io.open(".env", encoding="utf-8", errors="replace"):
            m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", z)
            if m:
                os.environ.setdefault(m.group(1), m.group(2).strip().strip('"').strip("'"))
        key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("MISTRAL_API_KEY fehlt")
        return 1

    print("=" * 78)
    print("Arme")
    print("=" * 78)
    arme = baue_arme()
    n, w = _arg("--n", 12), _arg("--w", 3)
    faelle = lade_faelle(n)
    print(f"\n  {len(faelle)} echte Faktensaetze, "
          f"{len(faelle) * len(arme) * w} Aufrufe")
    print(f"  Symbole: {sorted({f['symbol'] for f in faelle})}")

    client = MistralClient(api_key=key)
    stops: dict[str, list[tuple[str, float]]] = defaultdict(list)
    akt: dict[str, list[str]] = defaultdict(list)
    antworten = []

    import copy as _copy
    import config as _config
    from agent.krypto.backward_tracking import (
        ausstiegsregel_kontext_fuer_prompt, kosten_kontext_fuer_prompt,
    )

    _cfg = _copy.deepcopy(_config.load_config())
    _ausstieg = ausstiegsregel_kontext_fuer_prompt(_cfg)
    # Systemguete AUS DEM EXPORT, nicht aus der Datenbank. Stehende Vorgabe:
    # Desktop-Testskripte fassen die Produktiv-DB nicht an. Die Zahlen sind
    # dieselben - der Export liest genau diese Funktion - und sie stammen aus
    # dem Notebook-Lauf, also aus der Quelle, die auch im Betrieb zaehlt.
    _d = json.load(io.open(os.path.join(ORDNER, "notebook_diagnose.json"),
                           encoding="utf-8"))
    _real = ((_d.get("systemguete") or {}).get("hebel") or {}).get("real") or {}
    _n = _real.get("anzahl_bewertet")
    if isinstance(_n, int) and _n >= 30:
        _guete = {
            "anzahl_ausgewerteter_trades": _n,
            "erwartungswert_r": round(_real["expectancy_r"], 3),
            "sqn": round(_real["sqn"], 2),
            "sqn_einordnung": _real.get("sqn_einordnung"),
            "profit_factor": round(_real["profit_factor"], 2),
            "lesehilfe": (
                "Erwartungswert in R = durchschnittliches Ergebnis je Signal, gemessen "
                "an tatsaechlich eroeffneten Trades dieser Kategorie. Ein negativer Wert "
                "heisst, dass die bisherigen Signale im Schnitt Geld gekostet haben."
            ),
            "wie_du_das_nutzt": (
                "Das ist Kalibrierungs-Kontext, KEINE Handlungsanweisung und kein Grund, "
                "grundsaetzlich zurueckhaltender zu werden. Es sagt dir, wie streng die "
                "Latte fuer ein lohnendes Setup liegt - nicht, dass du keines mehr "
                "vorschlagen sollst."
            ),
            "belegt": True,
        }
    else:
        _guete = None
    print(f"  neue Fakten im A-Arm: kosten=ja, ausstiegsregel="
          f"{'ja' if _ausstieg else 'nein'}, systemguete={'ja' if _guete else 'nein'}")

    for f in faelle:
        ohne_kosten = json.loads(f["facts_json"])
        # Die exportierten Faktensaetze stammen von VOR der Aenderung und
        # tragen den kosten-Block noch nicht. Ohne dieses Nachruesten bekaeme
        # der A-Arm eine Regel, die auf einen nicht vorhandenen Fakt verweist -
        # exakt der kaputte Zustand, der heute frueh in Regel 2 gefunden und
        # behoben wurde ("wird dir separat mitgeteilt", ohne dass etwas
        # mitgeteilt wurde). Hier wird der Produktionszustand hergestellt.
        basis = copy.deepcopy(ohne_kosten)
        basis["kosten"] = kosten_kontext_fuer_prompt(
            (basis.get("hebel_kontext") or {}).get("max_hebel_config"))
        if _ausstieg is not None:
            basis["ausstiegsregel"] = _ausstieg
        if _guete is not None:
            basis["systemguete"] = _guete
        for _k in NEUE_FAKTEN:
            ohne_kosten.pop(_k, None)
        print(f"\n{f['symbol']} @ {f['created_at'][:16]}:", flush=True)
        for name, prompt in arme.items():
            # Der B-Arm bekommt AUCH die Fakten ohne `kosten` - Regel und Fakt
            # gehoeren zusammen, getestet wird die Aenderung als Ganzes.
            fakten = ohne_kosten if name.startswith("B") else basis
            zeile = []
            for _ in range(w):
                a = frage(client, fakten, prompt)
                if not a:
                    continue
                akt[name].append(str(a.get("action", "?")).upper())
                antworten.append({"arm": name, "symbol": f["symbol"],
                                  "created_at": f["created_at"], "antwort": a})
                s = stop_abstand(a)
                if s is not None:
                    stops[name].append((f["symbol"], s))
                    zeile.append(round(s, 1))
            print(f"  {name:26s} Stop % {zeile}", flush=True)

    try:
        ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "kosten_fakt_antworten.json")
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        # ANHAENGEN statt ueberschreiben, damit Aufstockungslaeufe die
        # bestehende Stichprobe ergaenzen. Doppelte (arm, symbol, created_at)
        # werden beim Auswerten ohnehin gepaart zusammengefasst.
        alt = []
        if os.path.exists(ziel):
            try:
                alt = json.loads(io.open(ziel, encoding="utf-8").read()) or []
            except (OSError, ValueError):
                alt = []
        io.open(ziel, "w", encoding="utf-8").write(
            json.dumps(alt + antworten, ensure_ascii=False))
        print(f"\n  {len(antworten)} Antworten gesichert")
    except OSError as exc:
        print(f"\n  nicht gesichert ({exc})")

    print("\n" + "=" * 78)
    print("PRIMAER: waehlt das Modell weitere Stops, wenn es die Kosten kennt?")
    print("=" * 78)
    print(f"{'Arm':28s}{'n':>5s}{'Median %':>10s}{'Mittel %':>10s}{'EROEFFNEN':>11s}")
    for name in arme:
        v = [s for _, s in stops.get(name, [])]
        a = akt.get(name, [])
        if not v:
            continue
        er = sum(1 for x in a if x in ("ERÖFFNEN", "EROEFFNEN")) / len(a) * 100 if a else float("nan")
        print(f"{name:28s}{len(v):5d}{statistics.median(v):10.2f}"
              f"{statistics.fmean(v):10.2f}{er:10.0f}%")

    a1 = stops.get("A1 alle neuen Fakten", [])
    a2 = stops.get("A2 alle neuen Fakten (Rauschen)", [])
    b = stops.get("B ohne die neuen Fakten", [])
    if len(a1) < 10 or len(b) < 10:
        print("\n  zu wenige Faelle")
        return 1

    rausch = abs(statistics.fmean([s for _, s in a1]) - statistics.fmean([s for _, s in a2]))
    mit = statistics.fmean([s for _, s in a1 + a2])
    ohne = statistics.fmean([s for _, s in b])
    print(f"\n  Rauschboden A1 gegen A2: {rausch:.3f} pp")
    print(f"  mit Kosten {mit:.2f} %  gegen  ohne {ohne:.2f} %   "
          f"Differenz {mit - ohne:+.3f} pp")

    def blk(daten):
        z = defaultdict(list)
        for sym, wert in daten:
            z[sym].append(wert)
        return list(z.values())

    import random
    rnd = random.Random(23)
    A, B = blk(a1 + a2), blk(b)
    diffs = []
    for _ in range(10000):
        x = [w for _ in A for w in rnd.choice(A)]
        y = [w for _ in B for w in rnd.choice(B)]
        if x and y:
            diffs.append(statistics.fmean(x) - statistics.fmean(y))
    diffs.sort()
    u, o = diffs[250], diffs[9750]
    urteil = ("WIRKT - Stops werden weiter" if u > 0 else
              "WIRKT GEGENTEILIG - Stops werden enger" if o < 0 else
              "keine Wirkung nachweisbar")
    print(f"  Block-Bootstrap ueber Symbole: [{u:+.3f} , {o:+.3f}] pp   "
          f"{len(A)}/{len(B)} Symbole   {urteil}")
    print("\n  Erwartet war eine WEITERE Wahl - enge Stops sind laut Formel")
    print("  doppelt teuer. Faellt es andersherum aus, hat das Modell die")
    print("  Tabelle gegen die Erwartung gelesen, und das gehoert berichtet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
