"""P9c (11.10.2026) - Fristen der Statusseite nach der Datenaenderung: GEGENPROBE an einer Kopie.

    python Basisinfos/Rechenkern_02_10/p9c_gegenprobe.py <Pruefverzeichnis>

  C1 Fristen: Hebel, Kontingente, Rollen-Kontingent 300 s; Betrieb, Schalter 60 s (aus der Marke `_frist_sekunden`)
  C2 Werte gleich: jede der drei Karten zwischengespeichert = frisch gerechnet (nur die Frist aendert sich, nicht die Rechnung)
  C3 Neuberechnung im Minutentakt: Kosten aller Getter mit Frist <= 60 s, vorher (5 Karten) gegen jetzt (2 Karten)
  C4 nach Ablauf der 300 s rechnet die Hebelkarte wieder neu (kein Dauerspeicher)
"""
import os
import sqlite3
import sys
import time

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
D = os.path.abspath(sys.argv[1])
import agent.betriebslage as BL  # noqa: E402

BL.DATEN = D
import remote.status as RS  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(ok)
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


c = sqlite3.connect("file:%s?mode=ro" % os.path.join(D, "tradinginfotool.db").replace("\\", "/"), uri=True)
c.row_factory = sqlite3.Row
F = {n: getattr(getattr(RS, n), "_frist_sekunden", None) for n in
     ("_get_hebel_lage", "_get_kontingente", "_get_rollen_budget", "_get_betrieb", "_get_schalter")}
pruefe("C1", F == {"_get_hebel_lage": 300, "_get_kontingente": 300, "_get_rollen_budget": 300, "_get_betrieb": 60, "_get_schalter": 60},
       "%s" % F)

RS.leere_aggregat_cache()
gleich = []
# ⚠️ Die Hebelkarte ist ZEITABHAENGIG: H15 zinst die Finanzierungskosten seit Eroeffnung sekundengenau auf, die Liquidation
# wandert also schon zwischen zwei Aufrufen (9. Nachkommastelle). Gleich heisst hier: alle Felder gleich, Liquidation und Abstand
# bis auf diese Aufzinsung - und die wird fuer 5 Minuten beziffert (das ist der Preis der Frist).
ZEIT_FELDER = ("liquidation_eur", "abstand")


def gleich_bis_zins(x, y):
    if isinstance(x, dict) and isinstance(y, dict):
        return x.keys() == y.keys() and all(gleich_bis_zins(x[k], y[k]) if k not in ZEIT_FELDER else
                                            (x[k] is None and y[k] is None) or abs((x[k] or 0) - (y[k] or 0)) <= 1e-6 * max(1, abs(x[k] or 0))
                                            for k in x)
    if isinstance(x, list) and isinstance(y, list):
        return len(x) == len(y) and all(gleich_bis_zins(a_, b_) for a_, b_ in zip(x, y))
    return x == y


for n, args in (("_get_hebel_lage", (c,)), ("_get_kontingente", (c,)), ("_get_rollen_budget", (c,))):
    a = getattr(RS, n)(*args)                       # frisch
    b = getattr(RS, n)(*args)                       # aus dem Zwischenspeicher
    roh = getattr(RS, n).__wrapped__(*args)         # die Rechnung selbst, ohne Speicher
    gleich.append((n, a is b or a == b, gleich_bis_zins(a, roh)))
# Aufzinsung in 5 Minuten: Liquidation je Position aus zwei Rechnungen mit 1 s Abstand, hochgerechnet
p1 = RS._get_hebel_lage.__wrapped__(c)["positionen"]
time.sleep(1.0)
p2 = RS._get_hebel_lage.__wrapped__(c)["positionen"]
drift = {x["symbol"]: 300 * abs((y["liquidation_eur"] or 0) - (x["liquidation_eur"] or 0)) for x, y in zip(p1, p2)}
pruefe("C2", all(sp and rr for _, sp, rr in gleich),
       " · ".join("%s Speicher=%s Rechnung=%s" % (n, "ok" if sp else "ANDERS", "ok" if rr else "ANDERS") for n, sp, rr in gleich)
       + " · Aufzinsung der Liquidation in 5 min: " + ", ".join("%s %.3f EUR" % kv for kv in drift.items()))


def minute(namen):
    """Kosten, wenn genau diese Karten ablaufen und neu rechnen."""
    t = time.perf_counter()
    for n in namen:
        fn = getattr(RS, n).__wrapped__
        fn(c) if n not in ("_get_schalter",) else fn()
    return time.perf_counter() - t


for _ in range(2):
    vorher = minute(["_get_betrieb", "_get_hebel_lage", "_get_schalter", "_get_kontingente", "_get_rollen_budget"])
    jetzt = minute(["_get_betrieb", "_get_schalter"])
pruefe("C3", jetzt < vorher / 3, "je Minute neu: vorher %.3f s (5 Karten) -> jetzt %.3f s (2 Karten); NB etwa x4" % (vorher, jetzt))

RS.leere_aggregat_cache()
RS._get_hebel_lage(c)
k = "_get_hebel_lage"
zeit, wert = RS._AGGREGAT_CACHE[k]
RS._AGGREGAT_CACHE[k] = (zeit - 301, "ALT")                  # Ablauf nachstellen
neu = RS._get_hebel_lage(c)
pruefe("C4", neu != "ALT" and isinstance(neu, dict), "nach 301 s neu gerechnet: %s" % (neu != "ALT"))
c.close()
print()
print("%d von %d gleich" % (sum(ERG), len(ERG)))
