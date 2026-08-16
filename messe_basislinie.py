# -*- coding: utf-8 -*-
"""DIE BASISLINIE VOR DEM GLATTEN SCHNITT - aus dem NB-Export (16.08.2026).

NUTZERVORGABE: *„halte den alten Stand vom NB-Export fest und versuche, so viel
Information und Messungen zu erstellen, um einen Vergleich bzw. Anhaltspunkte
für nach dem aktuellen LLM-Umbau bzw. der Fertigstellung des glatten Schnitts
zu haben."*

WOZU. Nach dem Umbau wird jede Zahl anders aussehen - und ohne einen
festgehaltenen Vorher-Stand laesst sich nicht sagen, ob sie BESSER aussieht
oder nur ANDERS. Die Kette hat in vier Tagen den Prompt-Stand zweimal
gewechselt, den Richtungsabgleich stillgelegt, die Konsistenzpruefung entfernt
und Rolle G ueberhaupt erst zum Laufen gebracht. Wer danach misst, misst gegen
nichts.

WAS FESTGEHALTEN WIRD - und warum genau das:

    DURCHSATZ     hinein/heraus je Stufe. Die Kernfrage des Nutzers ("ich
                  moechte nicht 10 oder 100 Empfehlungen") haengt daran.
    AKTIONEN      Verteilung je Instrument. Nach dem Umbau muss sich zeigen,
                  ob NICHTS_TUN zunimmt, nicht ob es weniger Signale gibt.
    GEGENPRUEFUNG wie viele Einstiege eine zweite Stimme bekamen. Rolle G war
                  bis zum 17.08. tot - jeder spaetere Wert ist ein Zugewinn
                  gegen 0.
    BETRIEB       Laufzeit, Ausfallfenster, Jobausfuehrungen. Ohne sie liest
                  man Betriebsluecken als Modellverhalten.
    DATENLAGE     Alter der Kursreihen. Am 16.08. waren sie zwei Tage alt -
                  jede Aussage ueber Signalqualitaet steht auf diesem Vorbehalt.
    ERGEBNIS      Systemguete und Trefferbilanz, soweit vorhanden.

WAS DIESES SKRIPT NICHT TUT: bewerten. Es schreibt Zahlen mit Datum und
Herkunft. Die Deutung gehoert in den Umbauplan, nicht in ein Messwerkzeug.

AUFRUF:  python messe_basislinie.py [--export PFAD] [--ausgabe PFAD]
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import re
import sys


def _export_pfad() -> str:
    """Den Austauschordner NICHT raten - das Projekt loest ihn selbst auf.

    Der Laufwerksbuchstabe ist geraeteabhaengig (Desktop K:, Notebook G:).
    Am 17.08. habe ich behauptet, der Ordner sei nicht erreichbar, nachdem ich
    auf G: nachgesehen hatte. `_google_drive_wurzel()` gibt es seit dem 17.07.
    genau dafuer."""
    import extract_notebook_diagnose as X

    return str(X.ZIEL_ORDNER / "notebook_diagnose.json")


def _laufzeit(log: list) -> dict:
    """Wann lief die App, wann nicht - aus den Zeitstempeln des Logs.

    KEIN JOB-ZAEHLER SAGT DAS. Ein Job, der nie laeuft, sieht in jeder
    Auswertung aus wie ein Job ohne Arbeit. Erst die LUECKEN im Log zeigen,
    dass es keine Gelegenheit gab."""
    zeit = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d)")
    def t(z): return z if isinstance(z, str) else json.dumps(z, ensure_ascii=False)
    minuten = sorted({zeit.match(t(z)).group(1) for z in log if zeit.match(t(z))})
    if len(minuten) < 2:
        return {}
    fmt = "%Y-%m-%d %H:%M"
    luecken, aus_min = [], 0.0
    for a, b in zip(minuten, minuten[1:]):
        d = (datetime.datetime.strptime(b, fmt)
             - datetime.datetime.strptime(a, fmt)).total_seconds() / 60
        if d > 10:
            luecken.append({"von": a, "bis": b, "minuten": round(d)})
            aus_min += d
    spanne = (datetime.datetime.strptime(minuten[-1], fmt)
              - datetime.datetime.strptime(minuten[0], fmt)).total_seconds() / 60
    return {"von": minuten[0], "bis": minuten[-1],
            "fenster_stunden": round(spanne / 60, 1),
            "ausfall_stunden": round(aus_min / 60, 1),
            "ausfall_anteil_pct": round(100 * aus_min / spanne, 1) if spanne else None,
            "ausfallfenster": luecken}


def erhebe(d: dict) -> dict:
    def t(z): return z if isinstance(z, str) else json.dumps(z, ensure_ascii=False)
    log = d.get("log_auszug") or []
    rollen = [s for s in d.get("spot_signals") or []
              if s.get("quelle_kette") == "rollen"]
    def voll(s, k): return s.get(k) not in (None, "")

    je_tag = {}
    for tag in sorted({str(s["created_at"])[:10] for s in rollen}):
        g = [s for s in rollen if str(s["created_at"]).startswith(tag)]
        ein = [s for s in g if s.get("action") in
               ("ERÖFFNEN", "KAUFEN", "NACHKAUFEN")]
        je_tag[tag] = {
            "signale": len(g),
            "aktionen": dict(collections.Counter(s.get("action") for s in g)),
            "einstiege": len(ein),
            "mit_konsistenzurteil": sum(
                1 for s in ein if voll(s, "zai_gegenpruefung_urteil")),
            "mit_richtungsabgleich": sum(
                1 for s in ein if voll(s, "zai_eigene_richtung")),
        }

    jobs = collections.Counter()
    for z in log:
        m = re.search(r'Running job "(\w+)', t(z))
        if m:
            jobs[m.group(1)] += 1

    reihen = (d.get("ohlc_aktualitaet_je_symbol") or {}).get("symbole") or []
    letzte = collections.Counter(s.get("bis") for s in reihen)

    return {
        "erhoben_am": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "quelle": "notebook_diagnose.json",
        "log_fenster_stunden": d.get("log_fenster_stunden"),
        "betrieb": _laufzeit(log),
        "jobausfuehrungen": dict(jobs.most_common()),
        "rollen_signale_je_tag": je_tag,
        "rollen_signale_gesamt": len(rollen),
        "kursreihen_letzter_tag": dict(sorted(letzte.items(), reverse=True)),
        "durchlaessigkeit": (d.get("rollen_kette") or {}).get("durchlaessigkeit"),
        "systemguete": d.get("systemguete"),
        "gesamt_signalqualitaet": d.get("gesamt_signalqualitaet"),
        "richtungsverteilung": d.get("richtungsverteilung"),
        "llm_aufrufe_heute": d.get("llm_aufrufe_heute"),
        "gate_veto_haeufigkeit": d.get("gate_veto_haeufigkeit"),
        "auffaelligkeiten_anzahl": len(d.get("auffaelligkeiten") or []),
        "job_fehlschlaege_anzahl": len(d.get("job_fehlschlaege") or []),
    }


def bericht(b: dict) -> list[str]:
    z = ["=" * 74, "BASISLINIE VOR DEM GLATTEN SCHNITT", "=" * 74,
         f"erhoben {b['erhoben_am']} aus {b['quelle']}", ""]

    be = b.get("betrieb") or {}
    if be:
        z += ["BETRIEB", f"  Fenster        {be['von']} bis {be['bis']}"
                        f"  ({be['fenster_stunden']} h)",
              f"  App AUS        {be['ausfall_stunden']} h "
              f"({be['ausfall_anteil_pct']} %) in "
              f"{len(be['ausfallfenster'])} Fenstern > 10 min",
              "  laengste:"]
        for f in sorted(be["ausfallfenster"], key=lambda x: -x["minuten"])[:4]:
            z.append(f"     {f['von']} bis {f['bis']}   {f['minuten']} min")
        z.append("")

    z += ["JOBAUSFUEHRUNGEN"]
    for k, n in (b.get("jobausfuehrungen") or {}).items():
        z.append(f"  {n:>5}x  {k}")
    z.append("")

    z += ["ROLLEN-SIGNALE JE TAG",
          f"  {'Tag':12}{'Signale':>9}{'Einstiege':>11}{'Konsistenz':>12}"
          f"{'Richtung':>10}"]
    for tag, v in (b.get("rollen_signale_je_tag") or {}).items():
        z.append(f"  {tag:12}{v['signale']:>9}{v['einstiege']:>11}"
                 f"{v['mit_konsistenzurteil']:>12}{v['mit_richtungsabgleich']:>10}")
    z.append("")
    for tag, v in (b.get("rollen_signale_je_tag") or {}).items():
        z.append(f"  {tag}: {v['aktionen']}")
    z.append("")

    z += ["DATENLAGE - letzter Kerzentag ueber alle Reihen"]
    for tag, n in (b.get("kursreihen_letzter_tag") or {}).items():
        wt = ""
        try:
            wt = " (" + datetime.date.fromisoformat(str(tag)).strftime("%a") + ")"
        except (TypeError, ValueError):
            pass
        z.append(f"  {tag}{wt}  {n} Symbole")
    z += ["", f"Auffaelligkeiten {b['auffaelligkeiten_anzahl']} | "
              f"Job-Fehlschlaege {b['job_fehlschlaege_anzahl']}",
          "=" * 74,
          "KEINE BEWERTUNG. Diese Zahlen sind der Vergleichspunkt, nicht das",
          "Urteil - die Deutung gehoert in den Umbauplan.", "=" * 74]
    return z


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--export", default=None)
    p.add_argument("--ausgabe", default="Basisinfos/basislinie_vor_schnitt.json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    pfad = a.export or _export_pfad()
    with open(pfad, encoding="utf-8") as f:
        d = json.load(f)
    b = erhebe(d)
    print("\n".join(bericht(b)))
    with open(a.ausgabe, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(b, f, ensure_ascii=False, indent=2)
    print(f"\nFestgehalten: {a.ausgabe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
