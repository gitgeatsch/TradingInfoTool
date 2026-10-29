# -*- coding: utf-8 -*-
"""MESSUNG Messplan W „Wal-Fluss“ §4/§5 (vorab 3c9e873f). Läuft nur, wenn der Selbsttest bestanden ist (``p102_wale_selbsttest.json``).

Je Wert (BTC Haupt, ETH zweiter Weg), Markt (Spot, Futures) und Horizont (1/3/7 T): D = Mittel(y | oberstes Fünftel E) −
Mittel(y | unterstes), Band, Nullpunkt, Stufe. Dazu die sieben Punkte für TRÄGT und die Vergleichsarme G roh, R roh (ohne Urteil).

    python -X utf8 Basisinfos/Rechenkern_02_10/p102_wale_messung.py
"""
import json
import os
import socket
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p102_wale_basis as B  # noqa: E402

AUSGABE = os.path.join(B.HIER, "p102_wale_messung.txt")
SELBSTTEST = os.path.join(B.HIER, "p102_wale_selbsttest.json")


def pp(x):
    return "%+.2f" % (100 * x) if np.isfinite(x) else "  –  "


def vz(x):
    return 0 if not np.isfinite(x) or x == 0 else (1 if x > 0 else -1)


def main() -> int:
    if not os.path.exists(SELBSTTEST):
        print("✖ kein bestandener Selbsttest (%s) - Messplan §6: erst der Selbsttest" % SELBSTTEST)
        return 1
    st = json.load(open(SELBSTTEST, encoding="utf-8"))
    if not st.get("bestanden"):
        print("✖ Selbsttest NICHT bestanden - nicht messen (Fassung 2)")
        return 1
    B.NULLWELT = st["nullwelt"]
    vorher = B.fingerabdruck()
    rng = np.random.default_rng(20261030)
    tg, aus = B.lade()
    w = B.maske(tg, B.URTEIL)
    z = ["MESSUNG Messplan W (%s, %s) · Nullwelt %s (Selbsttest) · Urteil %s bis %s · q 5 %% Haupt · Log-Ertrag brutto, Pp"
         % (socket.gethostname(), datetime.now().isoformat(timespec="seconds"), B.NULLWELT, B.URTEIL[0], B.URTEIL[1])]
    erg = {}
    for s in B.SYMBOLE:
        z.append("\n══ %s ══" % s)
        for m in B.MAERKTE:
            g, r, e, lab = aus[s]["markt"][m][B.Q_HAUPT]
            for h in B.HORIZONTE:
                x = st["X"].get("%s|%s|%d" % (s, m, h))
                auf = 2 * x if x else None                                  # X in k; D verschiebt um 2k (Selbsttest S3)
                y = aus[s]["y"][(h, 0)]
                haupt = B.bewerte(lab[w], y[w], h, rng, aufloesung=auf)
                jahre = {j: B.differenz(lab[B.maske(tg, zr)], y[B.maske(tg, zr)]) for j, zr in B.JAHRE.items()}
                leiter = {q: B.differenz(aus[s]["markt"][m][q][3][w], y[w]) for q in B.STUFEN}
                bew = aus[s]["r"][w]
                grenzen = np.nanquantile(bew, (1 / 3, 2 / 3))
                schicht = np.digitize(bew, grenzen)
                schichten = [B.differenz(np.where(schicht == i, lab[w], np.nan), y[w]) for i in range(3)]
                verzug = B.differenz(lab[w], aus[s]["y"][(h, 6)][w])
                ep2 = B.bewerte(lab[B.maske(tg, B.EPOCHE2)], y[B.maske(tg, B.EPOCHE2)], h, rng, aufloesung=auf)
                arm_g = B.differenz(B.fuenftel(g)[w], y[w])
                arm_r = B.differenz(B.fuenftel(r)[w], y[w])
                erg[(s, m, h)] = dict(haupt=haupt, jahre=jahre, leiter=leiter, schichten=schichten, verzug=verzug, ep2=ep2)
                z.append("  %-7s H%d  D %s [%s .. %s] Null %s · %s · %d/%d Tage oben/unten, %d Bl., AK %.3f"
                         % (m, h, pp(haupt["D"]), pp(haupt["unten"]), pp(haupt["oben"]), pp(haupt["nullpunkt"]), haupt["stufe"],
                            haupt["n_oben"], haupt["n_unten"], haupt["n_bloecke"], haupt["ak"]))
                z.append("            2025 %s · 2026 %s · q 1/5/10/20 %s · Schichten Fall/Mitte/Anstieg %s · Verzug 06:00 %s"
                         % (pp(jahre["2025"]), pp(jahre["2026"]), " ".join(pp(leiter[q]) for q in B.STUFEN),
                            " ".join(pp(v) for v in schichten), pp(verzug)))
                z.append("            Epoche 2023-07..2024-12: D %s · %s · Vergleichsarme: G roh %s, R roh %s"
                         % (pp(ep2["D"]), ep2["stufe"], pp(arm_g), pp(arm_r)))
    z.append("\n══ URTEIL je Hypothese (BTC Haupt; Messplan §5, alle 7 Punkte) ══")
    for m in B.MAERKTE:
        for h in B.HORIZONTE:
            a, b = erg[("BTCUSDT", m, h)], erg[("ETHUSDT", m, h)]
            v = vz(a["haupt"]["D"] - a["haupt"]["nullpunkt"])
            eh = b["haupt"]
            p = [a["haupt"]["stufe"].startswith("TRAEGT ("),
                 vz(a["jahre"]["2025"]) == v and vz(a["jahre"]["2026"]) == v,
                 sum(vz(x) == v for x in a["leiter"].values()) >= 3,
                 vz(eh["D"]) == v and ((eh["unten"] > eh["nullpunkt"]) if v > 0 else (eh["oben"] < eh["nullpunkt"])),
                 sum(vz(x) == v for x in a["schichten"]) >= 2,
                 vz(a["verzug"]) == v,
                 bool(st["bestanden"])]
            z.append("  %-7s H%d  Punkte 1-7: %s  ->  %s" % (m, h, " ".join("✔" if x else "✖" for x in p),
                                                          ("TRÄGT (%s)" % ("Große netto kaufen -> höher" if v > 0 else "Große netto kaufen -> niedriger"))
                                                          if all(p) else "trägt nicht nach Vorab-Regel (Stufe: %s)" % a["haupt"]["stufe"]))
    nachher = B.fingerabdruck()
    z.append("\nSeiteneffekt: geschützte Datei unverändert: %s" % (vorher == nachher))
    text = "\n".join(z)
    print(text)
    with open(AUSGABE, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
