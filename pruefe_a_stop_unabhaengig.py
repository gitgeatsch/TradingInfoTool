"""Gegenpruefung A (Voranalyse_A_Positionsfuehrung_01_10.md): der nachgezogene Stop UNABHAENGIG nachgerechnet.

Liest die Spur von ``messe_k6_hebelstufe.py --stop-wahl --spur <csv>`` (je Einstieg Symbol, Stunde, Spot-Rendite und
Ausstiegsstunde jeder Stop-Zelle) und rechnet eine Stichprobe direkt aus den Rohdaten nach - eigene ATR, eigene
Stop-Linie, eigener Ausstieg, ueber die STUNDE (nicht den Zeilenindex) adressiert:

    ATR      = Mittel der 24 letzten Spot-Spannen (high-low)/close bis einschliesslich Einstiegsstunde, mal sqrt(24)
    Linie    = hoechstes Markpreis-Hoch seit dem Einstieg (bis zur VORstunde, Start = Einstieg) - k x ATR
    Ausloesung = erste Stunde s <= H mit Markpreis-Tief <= Linie
    Ausstieg = v 0: an der Linie · v >= 1: Markpreis-Schluss der Stunde s + v · sonst Schluss nach H
    Spot     = Ausstieg/Einstieg - 1 - 0,3 %

Nur lesen (``mode=ro``), keine Netzabfrage. Aufruf:
    python pruefe_a_stop_unabhaengig.py <spur.csv> [anzahl] [--gegenprobe] [--jahr 2025,2026]

``--jahr``: welche Jahre der Spur (Vorgabe 2024 = Wahl). Eingestellte Paare (Menge unverzerrt) werden am ENDE der Reihe
abgerechnet (N3); Einstiege, deren Fenster ueber das Reihenende reicht, kommen ALLE zusaetzlich in die Stichprobe.

``--gegenprobe``: hebt die Linie schon mit dem Hoch der LAUFENDEN Stunde (Vorgriff) - die Pruefung MUSS dann abweichen.
"""
from __future__ import annotations

import csv
import math
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

HIER = os.path.dirname(os.path.abspath(__file__))
B0 = datetime(2020, 1, 1)


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)


def stunde(std):
    return (B0 + timedelta(hours=int(std))).strftime("%Y-%m-%d %H:%M")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    gp = "--gegenprobe" in sys.argv
    jahre = set(sys.argv[sys.argv.index("--jahr") + 1].split(",")) if "--jahr" in sys.argv else {"2024"}
    arg = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] != "--jahr"]
    spur, anz = arg[0], int(arg[1]) if len(arg) > 1 else 300
    with open(spur, encoding="utf-8") as f:
        rd = csv.reader(f, delimiter=";")
        kopf = next(rd)
        zeilen = [z for z in rd if z[2] in jahre]
    zellen = [k[:-2] for k in kopf[3::2]]
    cs = ro(os.path.join(HIER, "data", "stundenkurse.db"))
    ce = ro(os.path.join(HIER, "data", "eingestellt_historie.db"))
    cm = ro(os.path.join(HIER, "data", "markpreis_historie.db"))
    # Spot-Reihe wie der Lader (messe_e2_beitraege.kursreihen): bestand aus stundenkurse.db, eingestellte aus
    # eingestellt_historie.db, Paare mit VORGESCHICHTE aus beiden (alt + neu) - hier als Vereinigung je Stunde
    letzte = {}
    for sym in sorted({z[0] for z in zeilen}):
        letzte[sym] = max(x for x in (c_.execute("SELECT MAX(stunde) FROM stundenkurse WHERE symbol=?", (sym,)).fetchone()[0]
                                      for c_ in (cs, ce)) if x is not None)
    hmax = max(int(n.split("_")[0]) for n in zellen) + 5
    ende = [z for z in zeilen if stunde(int(z[1]) + hmax) > letzte[z[0]]]
    random.seed(20261001)
    probe = random.sample(zeilen, min(anz, len(zeilen)))
    probe += [z for z in ende if z not in probe][:300]
    cache = {}
    abw = {z: [] for z in zellen}
    for z in probe:
        sym, std = z[0], int(z[1])
        if sym not in cache:
            sp = {}
            for c_ in (ce, cs):
                sp.update({r[0]: r[1:] for r in c_.execute(
                    "SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=? ORDER BY stunde", (sym,))})
            reihe = sorted(sp)
            mp = {r[0]: (r[1], r[2], r[3]) for r in cm.execute(
                "SELECT stunde, low / faktor, close / faktor, high / faktor FROM markpreis WHERE symbol=?", (sym,))}
            cache[sym] = (sp, reihe, {s: i for i, s in enumerate(reihe)}, mp)
        sp, reihe, pos, mp = cache[sym]
        t_end = reihe[-1]

        def bei(s_):
            # Stunde s_ nach dem Einstieg; hinter dem Reihenende gilt der letzte Schluss (Abrechnung bei der Einstellung)
            t_ = stunde(std + s_)
            return (None if t_ > t_end else mp[t_]), mp[min(t_, t_end)][1]
        t0 = stunde(std)
        i0 = pos[t0]
        spann = [(sp[reihe[i]][0] - sp[reihe[i]][1]) / sp[reihe[i]][2] for i in range(i0 - 23, i0 + 1)]
        atr = sum(spann) / 24.0 * math.sqrt(24.0)
        E0 = mp[t0][1]
        for zi, name in enumerate(zellen):
            H = int(name.split("_")[0]); rest = name.split("_", 1)[1]
            if rest == "ohne" or "ohne v" in rest:
                k, v = None, int(rest[-1]) if "v" in rest else 1
            else:
                k, v = float(rest.split()[1]), int(rest[-1])
            mx, ts, lv = 1.0, None, None
            if k is not None:
                for s in range(1, H + 1):
                    b_, _c = bei(s)
                    if b_ is None:
                        break
                    lo, _c, hi = b_
                    if gp:
                        mx = max(mx, hi / E0)
                    lin = mx - k * atr
                    if lo / E0 <= lin:
                        ts, lv = s, lin
                        break
                    mx = max(mx, hi / E0)
            if ts is None:
                px, te = bei(H)[1] / E0, H
            elif v == 0:
                px, te = lv, ts
            else:
                px, te = bei(ts + v)[1] / E0, ts + v
            r = px - 1.0 - 0.003
            r_tool, te_tool = float(z[3 + 2 * zi]), int(z[4 + 2 * zi])
            abw[name].append((abs(r - r_tool), te == te_tool, sym, std, r, r_tool, te, te_tool))
    print("GEGENPRUEFUNG A%s - unabhaengig nachgerechnet, Stichprobe %d von %d Einstiegen %s (davon %d am Reihenende)" % (
        " (GEGENPROBE mit Vorgriff - muss abweichen)" if gp else "", len(probe), len(zeilen), "/".join(sorted(jahre)),
        sum(1 for z in probe if z in ende)))
    fehler = 0
    for name in zellen:
        a = abw[name]
        mxa = max(x[0] for x in a); gl = sum(1 for x in a if x[0] < 1e-9 and x[1])
        print("  %-22s gleich %4d/%d · groesste Abweichung %.2e" % (name, gl, len(a), mxa))
        for x in [x for x in a if not (x[0] < 1e-9 and x[1])][:3]:
            fehler += 1
            print("      ⛔ %s %s: eigen %+.6f te %d · Werkzeug %+.6f te %d" % (x[2], stunde(x[3]), x[4], x[6], x[5], x[7]))
    print("SCHLUSS: %s" % ("✔ alle gleich" if not fehler else "⛔ Abweichungen"))
    return 0 if not fehler else 1


if __name__ == "__main__":
    raise SystemExit(main())
