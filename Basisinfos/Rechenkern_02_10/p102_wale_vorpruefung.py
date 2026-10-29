# -*- coding: utf-8 -*-
"""VORPRÜFUNG Messplan W §7 — Vollständigkeit, Blöcke, Autokorrelation, Fallzahlen. OHNE Kursbezug (kein Blick auf Erträge).

    1  Vollständigkeit   je Reihe alle Tage da, Archiv = REST-Kerze, Datei deckt 00:00-23:59, Stunden = Tag
    2  Reproduktion      G (q 5 %) auf den Stichprobentagen = Stichprobe (``wale_stichprobe.db``, eigener Rechenweg dort)
    3  Kurse             Stundenkurse an jedem Einstiegszeitpunkt (00:00 und 06:00) vorhanden
    4  Fallzahlen        Tage je Fünftel und Jahr, Blöcke im Urteilsfenster je Horizont (>= 20 nötig), Autokorrelation von E

    python -X utf8 Basisinfos/Rechenkern_02_10/p102_wale_vorpruefung.py
"""
import os
import socket
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p102_wale_basis as B  # noqa: E402
import wale_stichprobe as WS  # noqa: E402
import messnorm as N  # noqa: E402

AUSGABE = os.path.join(B.HIER, "p102_wale_vorpruefung.txt")


def main() -> int:
    vorher = B.fingerabdruck()
    con = B.ro()
    tg, aus = B.lade()
    bis = tg[-1]
    z = ["VORPRÜFUNG Messplan W (%s, %s) · Tage %s bis %s" % (socket.gethostname(), datetime.now().isoformat(timespec="seconds"), tg[0], bis)]
    ok = True
    # 1 Vollständigkeit
    z.append("\n1 VOLLSTÄNDIGKEIT (Soll %d Tage je Reihe)" % len(tg))
    for s in B.SYMBOLE:
        for m in B.MAERKTE:
            n, lo, hi, ohne = con.execute("""SELECT COUNT(*), MIN(umsatz_usd/kerze_usd), MAX(umsatz_usd/kerze_usd), SUM(kerze_usd IS NULL)
                                             FROM tag WHERE symbol=? AND markt=? AND datum<=?""", (s, m, bis.isoformat())).fetchone()
            ab = con.execute("""SELECT COUNT(*) FROM tag WHERE symbol=? AND markt=? AND datum<=? AND (ABS(umsatz_usd/kerze_usd-1) > 0.005
                                OR substr(erste_utc,12,5) > '00:05' OR substr(letzte_utc,12,5) < '23:55')""", (s, m, bis.isoformat())).fetchone()[0]
            sw = con.execute("""SELECT COUNT(*) FROM (SELECT t.datum, ABS(SUM(st.usd)/t.umsatz_usd-1) a FROM tag t JOIN stunde st
                                USING (symbol, markt, datum) WHERE t.symbol=? AND t.markt=? AND t.datum<=? GROUP BY t.datum HAVING a > 1e-6)""",
                             (s, m, bis.isoformat())).fetchone()[0]
            gut = n == len(tg) and not ohne and not sw
            ok &= gut
            z.append("  %s %-7s %4d Tage · Archiv/Kerze %.4f..%.4f · auffällig %d · Stunden≠Tag %d · %s"
                     % (s, m, n, lo, hi, ab, sw, "✔" if gut else "✖"))
    # 2 Reproduktion der Stichprobe
    z.append("\n2 REPRODUKTION Stichprobe (BTCUSDT, G und R bei q 5 %, eigener Rechenweg in wale_stichprobe.schwelle)")
    sp = B.ro(WS.ABLAGE)
    idx = {d.isoformat(): i for i, d in enumerate(tg)}
    for m in B.MAERKTE:
        g, r, _, _ = aus["BTCUSDT"]["markt"][m][B.Q_HAUPT]
        abw, n = 0.0, 0
        for (datum,) in sp.execute("SELECT DISTINCT datum FROM verteilung WHERE markt=?", (m,)):
            zeilen = sp.execute("SELECT klasse, SUM(CASE WHEN seite='kauf' THEN usd ELSE 0 END), SUM(CASE WHEN seite='verkauf' THEN usd ELSE 0 END)"
                                " FROM verteilung WHERE markt=? AND datum=? AND einheit='sweep' GROUP BY klasse ORDER BY klasse DESC",
                                (m, datum)).fetchall()
            ges = sum(k + v for _, k, v in zeilen)
            kum, gross = 0.0, 0.0
            for kl, k, v in zeilen:
                kum += k + v
                gross += k - v
                if kum >= B.Q_HAUPT * ges:
                    break
            gr = gross / ges
            abw = max(abw, abs(gr - g[idx[datum]]))
            n += 1
        gut = n == 93 and abw < 1e-9
        ok &= gut
        z.append("  %-7s %d Tage · größte Abweichung G %.2e · %s" % (m, n, abw, "✔" if gut else "✖"))
    sp.close()
    # 3 Kurse an den Einstiegszeitpunkten
    z.append("\n3 KURSE an den Einstiegszeitpunkten")
    for s in B.SYMBOLE:
        px = B.kurse(con, s)
        fehlt = [(d, st) for d in tg + [bis + timedelta(days=i) for i in range(1, 9)] for st in (0, 6)
                 if B._ms(d, st) not in px and B._ms(d, st) < int(datetime.now().timestamp() * 1000) - 3600000]
        ok &= not fehlt
        z.append("  %s fehlend %d %s" % (s, len(fehlt), fehlt[:3] if fehlt else "✔"))
    # 4 Fallzahlen
    z.append("\n4 FALLZAHLEN (q 5 %%) · Urteil %s bis %s" % B.URTEIL)
    w = B.maske(tg, B.URTEIL)
    for h in B.HORIZONTE:
        blk = N._block(h)
        z.append("  H%d: Block %d T -> %d Blöcke im Urteilsfenster %s" % (h, blk, -(-int(w.sum()) // blk), "✔" if w.sum() / blk >= 20 else "✖ < 20"))
        ok &= w.sum() / blk >= 20
    for s in B.SYMBOLE:
        for m in B.MAERKTE:
            g, r, e, lab = aus[s]["markt"][m][B.Q_HAUPT]
            fin = np.isfinite(e[:-1]) & np.isfinite(e[1:])
            ak = np.corrcoef(e[:-1][fin], e[1:][fin])[0, 1]
            erst = next((tg[i] for i in range(len(tg)) if np.isfinite(lab[i])), None)
            je = []
            for j in (2023, 2024, 2025, 2026):
                mj = np.array([d.year == j for d in tg])
                je.append("%d: %d/%d/%d" % (j, (lab[mj] == 1).sum(), (lab[mj] == 0).sum(), (lab[mj] == -1).sum()))
            z.append("  %s %-7s E ab %s, Fünftel ab %s, AK(1) %+.3f · oben/mitte/unten %s"
                     % (s, m, next((tg[i] for i in range(len(tg)) if np.isfinite(e[i])), None), erst, ak, " · ".join(je)))
    con.close()
    nachher = B.fingerabdruck()
    ok &= vorher == nachher
    z.append("\nSeiteneffekt: geschützte Datei unverändert: %s" % (vorher == nachher))
    z.append("ERGEBNIS: %s" % ("BESTANDEN" if ok else "NICHT BESTANDEN"))
    text = "\n".join(z)
    print(text)
    with open(AUSGABE, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
