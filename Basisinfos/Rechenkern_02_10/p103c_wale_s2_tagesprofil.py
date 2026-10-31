# -*- coding: utf-8 -*-
"""G16 Wale STUFE 2 — VORANALYSE, Teil G: WANN im Folgetag sitzt der Effekt? (31.10.2026, nur AUSKUNFT zur Planung)

Teil F (p103b) nahm an, der Tageseffekt verteile sich GLEICHMÄSSIG über den Folgetag (Verdünnung = Überlappung). Hier wird das
auf den Daten von Fassung 4 nachgesehen — dieselben sechs Werte, dasselbe Urteilsfenster, dieselben Fünftel. Das ist KEIN neues
Urteil (die Daten sind gesehen), sondern die Schätzung einer Planungsgröße: wie viel des Effekts erreicht ein Einstieg zur Stunde v.

    D(v) = gepoolter Unterschied oberstes - unterstes Fünftel von E(t) für das 24-h-Fenster ab Stunde v nach Tagesende t
           (v = 0 ist H1 von Fassung 4, v = 6 der Verzug 06:00; v = 24..26 entspricht einem Einstieg 00-02 Uhr mit E des Vorvortags)
    Abschnitte: 6-h-Stücke des Folgetags (Summe = H1)

    python -X utf8 Basisinfos/Rechenkern_02_10/p103c_wale_s2_tagesprofil.py
"""
import os
import sys
from datetime import datetime, timedelta, timezone

import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import p102_wale_basis as B  # noqa: E402
import p103_wale_s2_voranalyse as V  # noqa: E402

AUS = []


def zeige(s=""):
    print(s, flush=True)
    AUS.append(s)


def preis(px, d, std):
    t = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) + timedelta(hours=std)
    return px.get(int(t.timestamp() * 1000), np.nan)


def fenster(px, tg, a, b):
    """ln(P(t+1, Stunde a) / ... ) — Ertrag von Stunde a bis Stunde b nach dem Ende des Tages t (= 00:00 t+1)."""
    d1 = [d + timedelta(days=1) for d in tg]
    return np.log(np.array([preis(px, d, b) for d in d1]) / np.array([preis(px, d, a) for d in d1]))


def main():
    B.fassung4()
    vorher = B.fingerabdruck()
    tg, aus = B.lade()
    w = B.maske(tg, B.URTEIL)
    S = B.SYMBOLE
    con = B.ro()
    px = {s: B.kurse(con, s) for s in S}
    con.close()
    lab = {s: aus[s]["markt"]["spot"][B.Q_HAUPT][3][w] for s in S}
    tgw = [d for d, m in zip(tg, w) if m]

    def D(a, b):
        return 100 * B.differenz_gepoolt([lab[s] for s in S], [fenster(px[s], tgw, a, b) for s in S])

    zeige("VORANALYSE G16 STUFE 2 — G TAGESPROFIL (Gerät %s, %s) · Fassung 4: %s · %s .. %s · gepoolt, Pp, Log brutto · NUR AUSKUNFT"
          % (os.environ.get("COMPUTERNAME", "?"), datetime.now().isoformat(timespec="seconds"), " ".join(s[:-4] for s in S), *B.URTEIL))
    zeige("  Kontrolle: D(0..24) %.3f (Fassung 4 H1 +0,35) · D(6..30) %.3f (Verzug +0,44)" % (D(0, 24), D(6, 30)))
    zeige("\n  6-h-Stücke nach Tagesende: " + " · ".join("%02d-%02d h %+.3f" % (a, a + 6, D(a, a + 6)) for a in range(0, 48, 6)))
    prof = {v: D(v, v + 24) for v in range(0, 27)}
    zeige("\n  24-h-Fenster ab Stunde v nach Tagesende (Einstieg v Uhr am Folgetag, v >= 24: 00-02 Uhr mit E des Vorvortags):")
    zeige("  " + " · ".join("%d %+.2f" % (v, d) for v, d in prof.items()))

    # Gewichtet mit der Einstiegsstunde der REGEL0 (Betriebsregel: ab 03:00 E des Vortags, sonst des Vorvortags)
    E = V.einstiege()
    T = V.spot_tabelle(sorted(set().union(*[set(e.symbol) for e in E.values()])))
    M, *_ = V.abdeckung(E, T)
    for m, e in E.items():
        h = e.ein.dt.hour.to_numpy()[M[m]]             # Einstieg = Schluss der Einstiegsstunde
        v = np.where(h >= V_STICH, h, h + 24)
        d_ein = np.mean([prof[int(x)] for x in v])
        zeige("  %-13s erwartetes D am Einstieg (Profil gewichtet mit der Einstiegsstunde) %+.3f Pp = %.2f × H1" % (m, d_ein, d_ein / prof[0]))
    nachher = B.fingerabdruck()
    zeige("\nSeiteneffekt: geschützte Datei unverändert: %s" % (vorher == nachher))
    with open(os.path.join(HIER, "p103c_wale_s2_tagesprofil.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(AUS) + "\n")


V_STICH = 3

if __name__ == "__main__":
    main()
