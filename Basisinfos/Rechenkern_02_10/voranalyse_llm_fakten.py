"""Voranalyse LLM-Pruefblock zur REGEL0-Mail (Voranalyse_Schritt7 Par. 19, 03.10.2026): die Zahlen, nachrechenbar.

Liest NUR: eine NB-Sicherung (mode=ro, in einen Wegwerfordner entpackt) und die Spur der REGEL0-Messung
(data/_vergleich/b0_spur_bestand.csv). Schreibt nichts ausser auf stdout.

    python Basisinfos/Rechenkern_02_10/voranalyse_llm_fakten.py <NB-Sicherung .db oder .db.gz>
"""
from __future__ import annotations

import collections as C
import csv
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import statistics as st
import sys
import tempfile

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(quelle: str) -> None:
    tmp = tempfile.mkdtemp(prefix="vor_llm_")
    kopie = os.path.join(tmp, "nb.db")
    (shutil.copyfileobj(gzip.open(quelle), open(kopie, "wb")) if quelle.endswith(".gz") else shutil.copy(quelle, kopie))
    c = sqlite3.connect("file:%s?mode=ro" % kopie.replace("\\", "/"), uri=True)
    c.row_factory = sqlite3.Row

    print("1) DIE ROLLEN-KETTE IM BETRIEB (Signale ab 26.09.)")
    rs = [dict(r) for r in c.execute("SELECT * FROM signals WHERE created_at >= '2026-09-26' ORDER BY created_at")]
    print("   Signale", len(rs), "| Aktionen", C.Counter(r["action"] for r in rs).most_common())
    print("   Modell Rolle BC", C.Counter(r["modell"] for r in rs).most_common(3), "| Prompt-Stand", C.Counter(r["prompt_stand"] for r in rs).most_common(2))
    print("   Instrument", C.Counter(r["instrument"] for r in rs).most_common(), "| Rolle G geurteilt", C.Counter(r["zai_gegenpruefung_urteil"] for r in rs).most_common())
    print("   Z.ai-Aufrufe je Tag", [(r["tag"], r["anzahl"]) for r in c.execute(
        "SELECT tag, anzahl FROM api_call_kontingent_taeglich WHERE source='zai' ORDER BY tag DESC LIMIT 8")])
    print("   Terminmarkt-Symbole (Grundlage von Rolle G)", c.execute("SELECT COUNT(DISTINCT symbol) FROM open_interest_snapshot").fetchone()[0])

    print("2) ROLLE A - Lagebilder (live aufgezeichnet)")
    lb = [dict(r) for r in c.execute("SELECT erstellt_am, fakten_json, klassen_json, modell, prompt_stand FROM lagebilder ORDER BY erstellt_am")]
    kr = []
    for r in lb:
        e = [x["einstufung"] for x in json.loads(r["klassen_json"] or "[]") if x.get("klasse") == "krypto"]
        if e:
            kr.append((r, e[0]))
    print("   Lagebilder", len(lb), "von", lb[0]["erstellt_am"][:16], "bis", lb[-1]["erstellt_am"][:16],
          "| Modell", C.Counter(r["modell"] for r in lb).most_common(2), "| Prompt", C.Counter(r["prompt_stand"] for r in lb).most_common(1))
    print("   krypto-Einstufung", C.Counter(e for _r, e in kr).most_common())
    g = C.defaultdict(list)
    for r, e in kr:
        g[hashlib.sha1((r["fakten_json"] or "").encode()).hexdigest()].append(e)
    mehr = [v for v in g.values() if len(v) > 1]
    paare = sum(len(v) * (len(v) - 1) // 2 for v in mehr)
    gleich = sum(1 for v in mehr for i in range(len(v)) for j in range(i + 1, len(v)) if v[i] == v[j])
    print("   bei IDENTISCHEN Fakten: %d Faktenstaende mehrfach gefragt, %d davon mit verschiedener Einstufung; %d von %d Wiederholungspaaren gleich (%.0f %%)"
          % (len(mehr), sum(len(set(v)) > 1 for v in mehr), gleich, paare, 100.0 * gleich / max(paare, 1)))

    print("3) ROLLE G - worauf sich ihre Einwaende stuetzen (ab 20.08.)")
    k = C.Counter()
    for u, gr in c.execute("SELECT zai_gegenpruefung_urteil, zai_gegenpruefung_kurzbegruendung FROM signals "
                           "WHERE zai_gegenpruefung_urteil IS NOT NULL AND created_at >= '2026-08-20'"):
        t = (gr or "").lower()
        quelle_g = ("Long-Konten" if "konten" in t else "Finanzierungsrate" if "finanzierung" in t else "offene Kontrakte" if "kontrakt" in t
                    else "Boersenfluss" if ("boerse" in t or "fluss" in t) else "sonst")
        k[(u, quelle_g)] += 1
    ja = {q: n for (u, q), n in k.items() if u == "ja"}
    n_ja = sum(ja.values())
    print("   Urteile", sum(k.values()), "| Einwand ja", n_ja, "| ja je Grundlage", sorted(ja.items(), key=lambda x: -x[1]),
          "| Long-Konten + Finanzierungsrate %.0f %% der Einwaende" % (100.0 * (ja.get("Long-Konten", 0) + ja.get("Finanzierungsrate", 0)) / max(n_ja, 1)))

    print("4) WIE LANGE EINE VORWAERTSMESSUNG BRAUCHT (REGEL0-Spur 2025-26, Ertrag 24 h ohne Hebel)")
    sp = list(csv.DictReader(open(os.path.join(HIER, "data", "_vergleich", "b0_spur_bestand.csv")), delimiter=";"))
    an = set()
    for r in c.execute("SELECT symbol, hebel_pruefung_erlaubt FROM asset_hebel_settings"):
        if r[1]:
            an.add(r[0])
    for name, menge in (("alle Assets der Messung", sp), ("Assets mit Hebel-Schalter an (Namensgleichheit)", [r for r in sp if r["symbol"] in an])):
        x = [float(r["spot"]) for r in menge]
        tage = sum({"2025": 365, "2026": 243}[j] for j in {r["jahr"] for r in menge})
        je_tag = len(menge) / tage
        sd = st.pstdev(x)
        print("   %s: n=%d, %.1f je Tag, Mittel %+.3f %%, Streuung %.2f %%" % (name, len(menge), je_tag, 100 * st.mean(x), 100 * sd))
        for d in (0.005, 0.01):
            n = (1.96 + 0.84) ** 2 * sd ** 2 * (1 / 0.5 + 1 / 0.5) / d ** 2
            print("      Unterschied %.1f Prozentpunkte zwischen zwei gleich grossen Gruppen (80 %% Macht, 5 %%): n=%d Handel = %d Tage"
                  % (100 * d, n, n / je_tag))
    c.close()
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1])
