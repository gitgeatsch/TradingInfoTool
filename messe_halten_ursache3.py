"""Welcher Fakt traegt das HALTEN - diesmal ABBAUEND statt aufbauend (05.08.).

WARUM EIN DRITTER ANLAUF. Die Runden 1 und 2 (messe_halten_ursache.py/2.py)
kamen mit einem klaren Negativbefund zurueck: acht Ankerpunkte, sieben
Varianten, durchgehend 96-100 % EROEFFNEN. Kein Faktenblock erzeugte HALTEN.
Ich habe daraus geschlossen, das HALTEN komme nicht aus dem Faktensatz.

DAS WAR EIN FEHLSCHLUSS, und der Nutzer hat auf die Loesung gezeigt: beide
Runden bauten von einem DUENNEN, rekonstruierten Faktensatz nach oben auf und
fuegten Bloecke hinzu. Wenn HALTEN aber erst ab einer gewissen Dichte an
Gegenargumenten entsteht, wird diese Schwelle beim Aufbauen nie erreicht - man
misst dann nur, dass man sie nicht erreicht hat. Genau dieselbe Saettigung
liess auch den historischen Backtest auf dieser Achse blind laufen (94-100 %
EROEFFNEN in ALLEN Armen, auch im Arm "Stand vor 28.07.").

SEIT HEUTE GEHT ES RICHTIG HERUM. Der Export liefert `facts_json` - die
ECHTEN Faktensaetze aus dem Betrieb. 48 davon haben nachweislich ein selbst
gewaehltes HALTEN erzeugt. Statt von duenn nach dick aufzubauen, wird hier von
einem echten, HALTEN-erzeugenden Satz ABGEBAUT: ein Block raus, erneut fragen.
Kippt die Antwort auf EROEFFNEN, war genau dieser Block der Traeger.

DER KONTROLLARM IST PFLICHT. A1 und A2 sind derselbe, unveraenderte
Faktensatz. Bleibt das Modell dort nicht bei HALTEN, ist der Testfall
untauglich (das Modell haelt ihn heute schlicht nicht mehr) und alle
Entfernungen darunter waeren unlesbar. Das wird je Fall geprueft, nicht global.

ABGEBAUT WIRD BLOCKWEISE auf oberster Ebene. Bewusst NICHT feiner: bei 16
Bloecken und mehreren Wiederholungen ist das schon ein grosser Lauf, und die
Frage lautet zunaechst "welcher Bereich", nicht "welches Einzelfeld". `asset`,
`preis` und `disclaimers` bleiben immer drin - ohne sie ist der Faktensatz
formal kaputt, und ein Modell, das auf einen kaputten Satz mit HALTEN
antwortet, sagt nichts ueber Fakten aus.

Lauf: python -u messe_halten_ursache3.py [--n 6] [--w 3]
"""
from __future__ import annotations

import copy
import io
import json
import os
import re
import statistics
from collections import Counter, defaultdict

from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient
from backtest_llm1_historisch import _arg, frage
from teste_regel28 import lade_testfaelle

# Ohne diese drei ist der Faktensatz formal unvollstaendig - ihre Entfernung
# wuerde nicht die Wirkung eines Fakts messen, sondern die Reaktion auf einen
# kaputten Eingang.
UNANTASTBAR = {"asset", "preis", "disclaimers"}


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

    n, w = _arg("--n", 6), _arg("--w", 3)
    faelle, gesamt = lade_testfaelle(n)
    if not faelle:
        print("keine Testfaelle")
        return 1

    bloecke = sorted(set(json.loads(faelle[0]["facts_json"])) - UNANTASTBAR)
    print("=" * 78)
    print(f"{len(faelle)} echte HALTEN-Faktensaetze (von {gesamt}) x "
          f"{len(bloecke) + 2} Varianten x {w} = "
          f"{len(faelle) * (len(bloecke) + 2) * w} Aufrufe")
    print(f"Abgebaut wird: {', '.join(bloecke)}")
    print(f"Immer drin   : {', '.join(sorted(UNANTASTBAR))}")
    print("=" * 78)

    client = MistralClient(api_key=key)
    ergebnis: dict[str, list[str]] = defaultdict(list)
    tauglich = 0

    for f in faelle:
        basis = json.loads(f["facts_json"])
        print(f"\n{f['symbol']} @ {f['created_at'][:16]} (Betrieb: HALTEN):", flush=True)

        # Kontrollarm zuerst - ist der Fall ueberhaupt noch reproduzierbar?
        kontrolle = []
        for arm in ("A1 unveraendert", "A2 unveraendert (Rauschen)"):
            for _ in range(w):
                a = frage(client, basis, SYSTEM_PROMPT)
                if a:
                    kontrolle.append(str(a.get("action", "?")).upper())
                    ergebnis[arm].append(kontrolle[-1])
        halten_anteil = (sum(1 for x in kontrolle if x == "HALTEN") / len(kontrolle)
                         if kontrolle else 0.0)
        print(f"  Kontrolle unveraendert  {dict(Counter(kontrolle))}"
              f"  -> HALTEN {halten_anteil * 100:.0f}%", flush=True)
        if halten_anteil < 0.5:
            print("  UNTAUGLICH - das Modell haelt diesen Fall heute nicht mehr,"
                  " Entfernungen waeren unlesbar. Fall uebersprungen.", flush=True)
            continue
        tauglich += 1

        for blk in bloecke:
            kopie = copy.deepcopy(basis)
            kopie.pop(blk, None)
            acts = []
            for _ in range(w):
                a = frage(client, kopie, SYSTEM_PROMPT)
                if a:
                    acts.append(str(a.get("action", "?")).upper())
                    ergebnis[f"ohne {blk}"].append(acts[-1])
            er = sum(1 for x in acts if x in ("ERÖFFNEN", "EROEFFNEN"))
            marke = "  <-- KIPPT" if acts and er / len(acts) >= 0.5 else ""
            print(f"  ohne {blk:28s} {dict(Counter(acts))}{marke}", flush=True)

    print("\n" + "=" * 78)
    print(f"{tauglich} von {len(faelle)} Faellen waren tauglich "
          f"(Kontrollarm blieb bei HALTEN)")
    print("=" * 78)
    if not tauglich:
        print("KEIN tauglicher Fall - der Aufbau kann nichts aussagen.")
        return 2
    print(f"{'Variante':34s}{'n':>5s}{'EROEFFNEN':>11s}{'HALTEN':>9s}")
    for name in ("A1 unveraendert", "A2 unveraendert (Rauschen)") + tuple(
            f"ohne {b}" for b in bloecke):
        v = ergebnis.get(name, [])
        if not v:
            continue
        er = sum(1 for x in v if x in ("ERÖFFNEN", "EROEFFNEN")) / len(v)
        ha = sum(1 for x in v if x == "HALTEN") / len(v)
        marke = "   <-- TRAEGT das HALTEN" if er >= 0.5 else ""
        print(f"{name:34s}{len(v):5d}{er * 100:10.0f}%{ha * 100:8.0f}%{marke}")
    print("\nLesart: kippt eine Entfernung auf EROEFFNEN, war dieser Block der")
    print("Grund fuer die Zurueckhaltung. Kippt KEINE, liegt es an der Summe -")
    print("dann ist kein einzelner Block verantwortlich, sondern die Dichte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
