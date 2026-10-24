"""P77b ZWEITER WEG FUER DIE HISTORIE (23.10.2026, F-1 Fassung 2, §6.1 Punkt 3).

    python -X utf8 Basisinfos/Rechenkern_02_10/p77b_hist_rest_abgleich.py

Befund aus p77: im Ueberlappungsmonat wichen 57 von 62.359 Zeilen ab. An genau diesen Stunden ist die Archivkerze (data.binance.vision)
FLACH (open = high = low = close, Volumen winzig) - abgeschnitten -, waehrend der Bestand die volle Kerze hat. Die REST-Schnittstelle
(api.binance.com/api/v3/klines, frei) liefert die Werte des Bestands (Stichprobe CRV 2021-12-04 21:00, CHZ 2021-12-14 04:00):
der Bestand stammt von dort.

Darum wird die GESAMTE eingefuegte Historie (Zeilen vor dem Bestandsbeginn je Symbol) ueber REST ein zweites Mal geholt und Zeile fuer
Zeile verglichen. Wo beide abweichen, gilt REST (= Quelle des Bestands); Zeilen, die nur REST kennt, werden eingefuegt.
Schreibt nur in data/_hist/stundenkurse.db; Protokoll data/_hist/rest_abgleich.csv.
"""
import csv
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

import requests

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
REST = "https://api.binance.com/api/v3/klines"
ZIEL = os.path.join("data", "_hist", "stundenkurse.db")


def ms(st):
    return int(datetime.strptime(st, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)


def txt(t):
    return datetime.fromtimestamp(t / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def rest(paar, von, bis):
    """Alle 1h-Kerzen [von, bis) in ms -> {stunde: (o, h, l, c, v)}."""
    out, t = {}, von
    while t < bis:
        for v in range(5):
            try:
                r = requests.get(REST, params=dict(symbol=paar, interval="1h", startTime=t, endTime=bis - 1, limit=1000), timeout=60)
                if r.status_code == 429:
                    time.sleep(30)
                    continue
                d = r.json()
                break
            except (requests.RequestException, ValueError):
                time.sleep(5 * (v + 1))
        else:
            raise SystemExit("ABBRUCH: REST %s ab %s nicht erreichbar" % (paar, txt(t)))
        if not d:
            break
        for k in d:
            out[txt(k[0])] = tuple(float(x) for x in k[1:6])
        t = d[-1][0] + 3600 * 1000
        time.sleep(0.15)
    return out


def main():
    alt = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
    erst = dict(alt.execute("SELECT symbol, MIN(stunde) FROM stundenkurse GROUP BY symbol").fetchall())
    alt.close()
    h = sqlite3.connect(ZIEL)
    prot = []
    for s in sorted(erst):
        a = h.execute("SELECT MIN(stunde) FROM stundenkurse WHERE symbol=? AND stunde < ?", (s, erst[s])).fetchone()[0]
        if a is None:
            continue
        arch = {r[0]: r[1:] for r in h.execute("SELECT stunde, open, high, low, close, volumen FROM stundenkurse WHERE symbol=? AND stunde < ?",
                                               (s, erst[s]))}
        R = rest(s + "USDT", ms(a), ms(erst[s]))
        gleich = abw = flach_abw = nur_arch = 0
        upd = []
        for st, w in arch.items():
            r = R.get(st)
            if r is None:
                nur_arch += 1
                continue
            if max(abs(x - y) / max(abs(y), 1e-12) for x, y in zip(w[:4], r[:4])) <= 1e-9:
                gleich += 1
            else:
                abw += 1
                flach_abw += w[0] == w[1] == w[2] == w[3]
                upd.append(r + (s, st))
        nur_rest = [(s, st) + r for st, r in R.items() if st not in arch]
        h.executemany("UPDATE stundenkurse SET open=?, high=?, low=?, close=?, volumen=? WHERE symbol=? AND stunde=?", upd)
        h.executemany("INSERT OR IGNORE INTO stundenkurse VALUES (?,?,?,?,?,?,?)", nur_rest)
        h.commit()
        prot.append(dict(symbol=s, von=a, bis=erst[s], archiv=len(arch), rest=len(R), gleich=gleich, abweichend=abw,
                         davon_flach=flach_abw, nur_archiv=nur_arch, nur_rest=len(nur_rest)))
        print("  %-8s %s..%s Archiv %6d REST %6d gleich %6d abweichend %4d (flach %4d) nur Archiv %d nur REST %d" % (
            s, a[:7], erst[s][:7], len(arch), len(R), gleich, abw, flach_abw, nur_arch, len(nur_rest)), flush=True)
    h.close()
    sp = list(prot[0])
    with open(os.path.join("data", "_hist", "rest_abgleich.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, sp, delimiter=";")
        w.writeheader()
        w.writerows(prot)
    S = {k: sum(p[k] for p in prot) for k in ("archiv", "rest", "gleich", "abweichend", "davon_flach", "nur_archiv", "nur_rest")}
    print("REST-ABGLEICH %d Symbole: %s" % (len(prot), S))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
