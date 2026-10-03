"""Kalibrierlauf P1-b fuer die Rolle MARKT ueber Marktphasen (E-52; Voranalyse_Schritt7 Par. 20.12.1, K-a/K-b).

Frage: Unterscheidet der Markt ueber 2025 und 2026, oder sagt er auch ueber Phasen hinweg fast immer dasselbe? Im Lauf 0.1c
(Anker nur 2026, eine Angstphase) stand er bei 82 % *stuetzt*. Vorab festgelegte Folge (K-b): bleibt er ueber Phasen ueber 70 %,
stuetzt sich der Entscheider nur noch auf den Trader, und der Markt steht als Auskunft daneben.

Ein REGEL0-Einstieg je Monat 2025-01 bis 2026-08 (Spur der Messung, feste Saat), nur die Rolle Markt, Fassung des Rollenkatalogs
(drei Stimmen). Alles aus EINER NB-Sicherung (nur gelesen). Wegwerf-DB und Wegwerf-Ablage, Deckel 75 echte Aufrufe.

    python Basisinfos/Rechenkern_02_10/kalibrier_markt.py <NB-Sicherung .db/.db.gz>
"""
from __future__ import annotations

import collections as C
import csv
import gzip
import os
import random
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)
DECKEL = 75
B0 = datetime(2020, 1, 1, tzinfo=timezone.utc)


def main(quelle: str) -> int:
    from dotenv import load_dotenv
    load_dotenv()
    import database.db as db
    tmp = tempfile.mkdtemp(prefix="kalibrier_markt_")
    db.DB_PATH = Path(tmp) / "wegwerf.db"
    c0 = sqlite3.connect(db.DB_PATH); c0.row_factory = sqlite3.Row; db.init_db(c0); c0.close()
    std_vorher = os.path.getmtime(os.path.join(HIER, "data", "tradinginfotool.db"))
    nb = os.path.join(tmp, "nb.db")
    (shutil.copyfileobj(gzip.open(quelle), open(nb, "wb")) if quelle.endswith(".gz") else shutil.copy(quelle, nb))
    from api.gemini import GeminiClient
    import agent.regel0_llm as L
    K = L.lade()
    K = dict(K, rollen=dict(K["rollen"], trader=dict(K["rollen"]["trader"], an=False), entscheider=dict(K["rollen"]["entscheider"], an=False)),
             max_signale_je_lauf=10 ** 6, lauf_zeitgrenze_s=10 ** 6, tageslimit_aufrufe=10 ** 6)
    client = GeminiClient(api_key=os.environ["GEMINI_API_KEY"])
    zaehl = {"n": 0}
    roh_chat = client.chat

    def chat(*a, **kw):
        if zaehl["n"] >= DECKEL:
            raise RuntimeError("Deckel von %d Aufrufen erreicht" % DECKEL)
        zaehl["n"] += 1
        return roh_chat(*a, **kw)
    client.chat = chat
    sp = list(csv.DictReader(open(os.path.join(HIER, "data", "_vergleich", "b0_spur_bestand.csv")), delimiter=";"))
    je_monat = C.defaultdict(list)
    for z in sp:
        if int(z["stufe"]) > 0:
            je_monat[(B0 + timedelta(hours=int(z["std"]))).strftime("%Y-%m")].append(z)
    rnd = random.Random(20261003)
    ablage = os.path.join(tmp, "ablage")
    os.makedirs(ablage)
    um = L.Umlauf(K, client, ablage)
    print("Fassung %s, Modell %s, Stimmen %s" % (K["fassung"], K["modell"], K.get("stimmen")))
    urteile, faelle = [], []
    for monat in sorted(m for m in je_monat if "2025-01" <= m <= "2026-08"):
        z = rnd.choice(je_monat[monat])
        sig = B0 + timedelta(hours=int(z["std"]))
        r = dict(symbol=z["symbol"], bitpanda=None, signalstunde=sig.strftime("%Y-%m-%d %H:%M"), stufe=int(z["stufe"]), kurs=None,
                 einstieg=(sig + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"), ausstieg=(sig + timedelta(hours=25)).strftime("%Y-%m-%d %H:%M"))
        e = L.pruefe_signal(r, client, ablage, "data", nb, K, umlauf=um).get("markt", {})
        u = e.get("urteil") or ("-" + str(e.get("fehlt"))[:40])
        urteile.append(u)
        faelle.append((monat, r, e))
        print("  %s  %-16s Stimmen %s  %s" % (monat, u, e.get("stimmen"), (e.get("begruendung") or "")[:110]), flush=True)
    gueltig = [u for u in urteile if not u.startswith("-")]
    v = C.Counter(gueltig)
    top = v.most_common(1)[0][1] / len(gueltig) if gueltig else 1.0
    for jahr in ("2025", "2026"):
        vj = C.Counter(u for (m, _r, _e), u in zip(faelle, urteile) if m.startswith(jahr) and not u.startswith("-"))
        print("  %s: %s" % (jahr, dict(vj)))
    print("\nP1-b Markt ueber Phasen: %d gueltig · Verteilung %s · groesste Stufe %.0f %% -> %s" % (
        len(gueltig), dict(v), 100 * top, "OK" if top <= 0.70 else "NICHT erfuellt"))
    print("Aufrufe gesamt: %d (Deckel %d) · Standard-DB unberuehrt: %s" % (
        zaehl["n"], DECKEL, os.path.getmtime(os.path.join(HIER, "data", "tradinginfotool.db")) == std_vorher))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
