"""Gegenprobe K-BP-1 (09.10.2026, Schritt7 Par. 23.35) - zweite Umsetzung der Zeilenzuordnung, nur lesend, kein Netz, keine DB.

    python Basisinfos/Rechenkern_02_10/kbp1_gegenprobe.py

  G1 ECHTE Rohantwort (nb_bitpanda_portfolio_roh_9900K.txt, Zeilen BTC/ETH/EURCV aus der Datei gelesen) mit den Wallets der
     Prod-Sicherung 09.10. 12:35 UTC: alle drei passen, Spot-Zeile = Spot-Menge (EURCV mit Spot 296,04 der Rohantwort)
  G2 zweite Umsetzung (ALLE Beschriftungen der Zeilen als Spot / Hebel / beides durchprobieren) gegen `spot_zeile` an 20.000
     Zufallsfaellen (0 bis 3 Zeilen, richtige und gestoerte Mengen, Reihenfolge gemischt, Spot 0, Kredit negativ): gleiche Antwort
     'passt' und gleiche Spot-Menge
  G3 der alte Fehler ist nachgestellt: `{asset_id: Zeile}` (letzte gewinnt) haette BTC und EURCV verworfen, die neue Zuordnung nicht
"""
import io
import itertools
import json
import os
import random
import re
import sys
import types

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
import importer.bitpanda_bestand as BB  # noqa: E402

ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def eigen(mengen, spot, hebel, sonst=0.0):
    """Zweite Umsetzung: jede Zeile ist S, H oder SH; hoechstens eine Zeile traegt S-Anteil, hoechstens eine H-Anteil."""
    t = lambda a, b: abs(a - b) <= max(1e-8, 1e-6 * max(abs(a), abs(b)))  # noqa: E731
    if abs(sonst) > 1e-12:
        return False, None
    if len(mengen) > 2:
        return False, None
    loesungen = []
    for lab in itertools.product(("S", "H", "SH"), repeat=len(mengen)):
        if sum("S" in x for x in lab) > 1 or sum("H" in x for x in lab) > 1:
            continue
        s_ist = sum(m for m, x in zip(mengen, lab) if x == "S")
        h_ist = sum(m for m, x in zip(mengen, lab) if x == "H")
        sh = [m for m, x in zip(mengen, lab) if x == "SH"]
        if sh:
            okk = t(sh[0], spot + hebel) and not any(x in ("S", "H") for x in lab)
        else:
            # FESTLEGUNG (09.10.): die Spot-Kontrolle prueft SPOT gegen SPOT - fehlt die Hebel-Zeile ganz, ist das eine Frage der
            # Hebel-Kontrolle, nicht des Spot-Bestands (die erste Fassung dieser Gegenprobe verlangte sie: 968 Faelle, Befund Par. 23.35)
            okk = t(s_ist, spot) and (t(h_ist, hebel) or not any(x == "H" for x in lab))
        if okk and len(mengen) == 2 and "SH" in lab:
            okk = False                          # zwei Zeilen: getrennt, nie eine als Summe
        if okk:
            sz = next((m for m, x in zip(mengen, lab) if "S" in x), None)
            if sz is not None and abs(spot) <= 1e-12 and "SH" in lab:
                sz = None                        # Spot 0: die Summenzeile IST die Hebelzeile
            loesungen.append(sz)
    if not mengen:
        return abs(spot) <= 1e-12 and abs(hebel) <= 1e-12, None
    return bool(loesungen), (loesungen[0] if loesungen else None)


# ---- G1 echte Rohantwort
roh = io.open(os.path.join("K:/My Drive", "Claude_Austauschordner", "Notebook_Analysedaten", "nb_bitpanda_portfolio_roh_9900K.txt"),
              encoding="utf-8").read()
zeilen = {}
for name, js in re.findall(r"--- (\w+) \(.*?\n((?:  Zeile .*\n?)+)", roh):
    zeilen[name] = [float(json.loads(z.split(": ", 1)[1])["balance"]["value"]) for z in js.strip().split("\n")]
wallets = {"BTC": (0.05496596, 0.0, 0.02038541), "ETH": (0.05685134, 0.48714122, 0.89636371), "EURCV": (296.04291657, 0.0, -2600.0)}
g1 = []
for s, (fr, ge, he) in wallets.items():
    p, passt, lesart = BB.spot_zeile([types.SimpleNamespace(menge_gesamt=m) for m in zeilen[s]], {"frei": fr, "gestakt": ge, "hebel": he, "sonst": 0.0})
    g1.append(passt and p is not None and abs(p.menge_gesamt - (fr + ge)) < 1e-9)
pruefe("G1", all(g1) and set(zeilen) == set(wallets), "Rohantwort %s · passt %s" % ({k: v for k, v in zeilen.items()}, g1))

# ---- G2 Zufall
rnd = random.Random(20261009)
fx = []
for _ in range(20000):
    spot = 0.0 if rnd.random() < 0.25 else round(rnd.uniform(0.001, 5000), 8)
    hebel = 0.0 if rnd.random() < 0.3 else round(rnd.choice((1, -1)) * rnd.uniform(0.001, 3000), 8)
    sonst = 0.0 if rnd.random() < 0.95 else 0.5
    art = rnd.random()
    if art < 0.35:
        mengen = [x for x in (spot, hebel) if abs(x) > 0]
    elif art < 0.5:
        mengen = [spot + hebel] if abs(spot + hebel) > 0 else []
    elif art < 0.6:
        mengen = [spot] if abs(spot) > 0 else []
    elif art < 0.85:
        mengen = [x * rnd.choice((1, 1, 1.01, 0.97)) for x in (spot, hebel) if abs(x) > 0]
    else:
        mengen = [round(rnd.uniform(-3000, 5000), 8) for _ in range(rnd.randint(0, 3))]
    rnd.shuffle(mengen)
    soll_passt, soll_spot = eigen(mengen, spot, hebel, sonst)
    p, passt, _ = BB.spot_zeile([types.SimpleNamespace(menge_gesamt=m) for m in mengen], {"frei": spot, "gestakt": 0.0, "hebel": hebel, "sonst": sonst})
    ist_spot = p.menge_gesamt if (passt and p is not None) else None
    if passt != soll_passt or (passt and ((ist_spot is None) != (soll_spot is None) or (ist_spot is not None and abs(ist_spot - soll_spot) > 1e-9))):
        fx.append((mengen, spot, hebel, sonst, passt, soll_passt, ist_spot, soll_spot))
pruefe("G2", not fx, "20.000 Faelle, Abweichungen %d %s" % (len(fx), fx[:2]))

# ---- G3 alter Fehler
alt = {s: z[-1] for s, z in zeilen.items()}         # letzte Zeile gewinnt
alt_passt = {s: abs(alt[s] - (wallets[s][0] + wallets[s][1])) < 1e-9 or abs(alt[s] - sum(wallets[s])) < 1e-9 for s in wallets}
pruefe("G3", alt_passt == {"BTC": False, "ETH": True, "EURCV": False}, "alte Logik (letzte Zeile): %s - genau die Mails vom 09.10." % alt_passt)
print("\n%d von %d gleich" % (ok, n))
