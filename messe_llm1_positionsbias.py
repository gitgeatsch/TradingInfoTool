"""Ist LLM1 positionsempfindlich wie LLM2? (2026-08-04, Desktop-Livelauf)

DER AUSGANGSBEFUND liegt seit dem 29.07. vor und wurde an der echten Z.ai-API
gemessen (`gegenpruefung.py::leite_eigene_richtung_positionsrobust`):

    Gegenindikator FRUEH in der Liste  -> fast vollstaendig ignoriert (6/6)
    Gegenindikator am ENDE             -> deutlich staerker gewichtet (4/6)
    Gegenindikator in der MITTE        -> noch entschiedener (6/6)

Das ist die U-foermige Aufmerksamkeitskurve der "Lost in the Middle"-Literatur:
Anfang UND Mitte schwach, nur die letzte Position bekommt verlaesslich Gewicht.
LLM2 bekam daraufhin Position Swapping (zwei Reihenfolgen, Vergleich).

**LLM1 HAT DAVON NICHTS.** Seine 17 Bloecke stehen in fester Reihenfolge:

    1 asset ... 7 trigger ... 16 markt_kontext  17 disclaimers

`trigger` - der Grund, WARUM das Signal ueberhaupt existiert - steht auf
Position 7 von 17, also in der schwachen Mitte. Auf der staerksten Position
(zuletzt) steht `disclaimers`, ein Hinweistext ohne Marktevidenz.

DIESE MESSUNG prueft, ob sich das auf die Entscheidung auswirkt. Vier Arme:

    A1  Originalreihenfolge
    A2  Originalreihenfolge  <- IDENTISCH, misst das Eigenrauschen
    B1  umgekehrte Reihenfolge
    B2  trigger ans Ende, disclaimers davor

Ohne A2 waere jede Zahl unbrauchbar - LLM1 laeuft mit temperature=0.2 und
antwortet auch bei identischem Prompt unterschiedlich.

Lauf: python messe_llm1_positionsbias.py [--n 3] [--w 6]
Braucht MISTRAL_API_KEY. Verbraucht n x 4 x w Aufrufe.
"""
from __future__ import annotations

import json
import os
import statistics
import sys

from agent.krypto.hebel_analyst import SYSTEM_PROMPT
from api.mistral import MistralClient

ORDNER = r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten"


def _arg(name: str, default: int) -> int:
    if name in sys.argv:
        try:
            return int(sys.argv[sys.argv.index(name) + 1])
        except (IndexError, ValueError):
            pass
    return default


def baue_fakten(sig: dict, stamm: dict) -> dict:
    """Realistischer Faktensatz in der PRODUKTIVEN Blockreihenfolge.

    Nicht der historische Satz - der wird nicht gespeichert. Aber Struktur und
    Werte stammen aus einem echten Signal, und fuer die Positionsfrage zaehlt
    die Struktur, nicht die historische Treue."""
    sym = sig["symbol"]
    entry = ((sig.get("entry_usd_von") or 0) + (sig.get("entry_usd_bis") or 0)) / 2
    return {
        "asset": {"symbol": sym, "name": (stamm.get(sym) or {}).get("name", sym),
                  "rolle": (stamm.get(sym) or {}).get("rolle", "unbekannt")},
        "preis": {"usd": entry, "aktualisiert_vor_min": 3},
        "technische_analyse": {"rsi_14": 41.2, "macd": "bearish",
                               "confluence": {"gesamttendenz": "gemischt"}},
        "regime": {"wert": sig.get("regime", "baer"), "quelle": "deterministisch",
                   "btc_trend": "abwärts (EMA20 < EMA50 < EMA200)",
                   "fear_greed": {"wert": 28, "einstufung": "Angst"}},
        "regime_profil": {"min_konfidenz_prozent": 60},
        "antizyklisch": {
            "funding_rate_aktuell_prozent_pro_stunde": 0.0012,
            "funding_rate_aktuell_prozent_pro_tag": 0.0288,
            "funding_rate_extrem": False,
            "long_konten_anteil_prozent": 64.8,
            "retail_long_bias_extrem": False,
        },
        "trigger": {"trigger_zweig": sig.get("trigger_zweig", "trendfolge"),
                    "score_gesamt": sig.get("trigger_score", 64.2),
                    "oi_change_pct_lookback": -0.02,
                    "kursaenderung_pct_lookback": -1.74},
        "position_aktuell": {"vorhanden": False},
        "historische_erfolgsquote": {"hinweis": "zu wenige Faelle (n<15)"},
        "liquiditaetszonen": {"naechste_zone_unter": entry * 0.96},
        "signal_stabilitaet": {"letzte_richtung": sig.get("richtung", "LONG")},
        "btc_relativwert": {"einordnung": "im Mittelfeld"},
        "optionsmarkt": {"dvol_prozent": 52.0},
        "hebel_kontext": {"max_hebel_config": 5,
                          "max_sicherer_hebel_geschaetzt": 3},
        "markt_kontext": {"naechste_fomc_sitzungen": {"in_tagen": 19}},
        "disclaimers": {"hinweis": "Alle Angaben ohne Gewähr, keine Anlageberatung."},
    }


def umsortiere(fakten: dict, art: str) -> dict:
    """asset bleibt vorn (reiner Bezeichner, wie bei gegenpruefung.py)."""
    keys = [k for k in fakten if k != "asset"]
    if art == "original":
        neu = keys
    elif art == "umgekehrt":
        neu = list(reversed(keys))
    elif art == "trigger_zuletzt":
        neu = [k for k in keys if k != "trigger"] + ["trigger"]
    else:
        raise ValueError(art)
    return {"asset": fakten["asset"], **{k: fakten[k] for k in neu}}


# Mistrals kostenloser Zugang begrenzt die Rate. Der erste Lauf feuerte 72
# Aufrufe in Folge - die meisten scheiterten mit HTTPError, uebrig blieben
# einzelne Antworten und ein unbrauchbarer Rauschboden von 0,000. Der Client
# selbst war in Ordnung, ein Einzelaufruf lief sofort durch.
WARTE_SEKUNDEN = 1.5
VERSUCHE = 4


def frage(client, fakten: dict) -> dict | None:
    import time
    msg = [{"role": "system", "content": SYSTEM_PROMPT},
           {"role": "user", "content": json.dumps(fakten, ensure_ascii=False)}]
    for versuch in range(VERSUCHE):
        try:
            time.sleep(WARTE_SEKUNDEN)
            roh = client.chat(msg, temperature=0.2,
                              response_format={"type": "json_object"})
            return json.loads(roh)
        except Exception as exc:
            if versuch == VERSUCHE - 1:
                print(f"    (nach {VERSUCHE} Versuchen aufgegeben: "
                      f"{type(exc).__name__})")
                return None
            time.sleep(WARTE_SEKUNDEN * (2 ** versuch))   # exponentiell warten
    return None


def sammle(client, fakten, w: int) -> tuple[list[str], list[float]]:
    acts, konf = [], []
    for _ in range(w):
        a = frage(client, fakten)
        if not a:
            continue
        acts.append(str(a.get("action", "?")).upper())
        k = a.get("confidence_pct")
        if isinstance(k, (int, float)):
            konf.append(float(k))
    return acts, konf


def abstand(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    alle = set(a) | set(b)
    return 0.5 * sum(abs(a.count(x) / len(a) - b.count(x) / len(b)) for x in alle)


def main() -> int:
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        from dotenv import load_dotenv
        load_dotenv()
        key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        print("MISTRAL_API_KEY fehlt")
        return 1

    n, w = _arg("--n", 3), _arg("--w", 6)
    import io
    d = json.load(io.open(ORDNER + r"\notebook_diagnose.json", encoding="utf-8"))
    stamm = d.get("watchlist_stammdaten") or {}
    kandidaten = [s for s in d["hebel_signals"]
                  if s.get("entry_usd_von") and s.get("take_profit_usd_von")][:n]
    if not kandidaten:
        print("keine Signale im Export")
        return 1

    client = MistralClient(api_key=key)
    print("=" * 74)
    print(f"LLM1 POSITIONS-BIAS   {len(kandidaten)} Faktensaetze x 4 Arme x {w} Wiederholungen")
    print(f"= {len(kandidaten) * 4 * w} Aufrufe, temperature=0.2 wie im Betrieb")
    print("=" * 74)

    r_act, r_konf = [], []
    w_um_act, w_um_konf, w_tr_act, w_tr_konf = [], [], [], []

    for sig in kandidaten:
        f = baue_fakten(sig, stamm)
        print(f"\n{sig['symbol']} ({sig.get('richtung', '?')}):")
        a1 = sammle(client, umsortiere(f, "original"), w)
        a2 = sammle(client, umsortiere(f, "original"), w)
        b1 = sammle(client, umsortiere(f, "umgekehrt"), w)
        b2 = sammle(client, umsortiere(f, "trigger_zuletzt"), w)
        for name, arm in (("A1 original", a1), ("A2 original", a2),
                          ("B1 umgekehrt", b1), ("B2 trigger zuletzt", b2)):
            k = f"{statistics.fmean(arm[1]):.1f}" if arm[1] else "-"
            print(f"  {name:20s} {dict((x, arm[0].count(x)) for x in set(arm[0]))}"
                  f"   Konfidenz {k}")
        r_act.append(abstand(a1[0], a2[0]))
        w_um_act.append(abstand(a1[0], b1[0]))
        w_tr_act.append(abstand(a1[0], b2[0]))
        if a1[1] and a2[1] and b1[1] and b2[1]:
            m1 = statistics.fmean(a1[1])
            r_konf.append(abs(m1 - statistics.fmean(a2[1])))
            w_um_konf.append(abs(m1 - statistics.fmean(b1[1])))
            w_tr_konf.append(abs(m1 - statistics.fmean(b2[1])))

    def m(x):
        return statistics.fmean(x) if x else 0.0

    print()
    print("=" * 74)
    print(f"{'':24s} {'action':>10s} {'Konfidenz':>12s} {'gegen Rauschen':>16s}")
    rb_a, rb_k = m(r_act), m(r_konf)
    print(f"{'RAUSCHBODEN (A1 vs A2)':24s} {rb_a:10.3f} {rb_k:11.2f} pp {'-':>16s}")
    for name, a, k in (("umgekehrt", m(w_um_act), m(w_um_konf)),
                       ("trigger zuletzt", m(w_tr_act), m(w_tr_konf))):
        srv = max((a / rb_a) if rb_a > 1e-9 else 0, (k / rb_k) if rb_k > 1e-9 else 0)
        print(f"{name:24s} {a:10.3f} {k:11.2f} pp {srv:15.1f}x")
    print()
    grenze = 2.0
    srv_max = max(
        (m(w_um_act) / rb_a) if rb_a > 1e-9 else 0,
        (m(w_tr_act) / rb_a) if rb_a > 1e-9 else 0,
        (m(w_um_konf) / rb_k) if rb_k > 1e-9 else 0,
        (m(w_tr_konf) / rb_k) if rb_k > 1e-9 else 0)
    if srv_max >= grenze:
        print(f"BEFUND: LLM1 IST positionsempfindlich ({srv_max:.1f}-faches "
              f"Eigenrauschen).")
        print("        Position Swapping wie bei LLM2 ist angezeigt.")
    elif rb_a < 1e-9 and rb_k < 1e-9:
        print("BEFUND: unbestimmt - kein Eigenrauschen messbar, "
              "Wiederholungen erhoehen.")
    else:
        print(f"BEFUND: keine nachweisbare Positionsempfindlichkeit "
              f"({srv_max:.1f}x Rauschen).")
        print("        Die feste Reihenfolge ist dann unkritisch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
