# -*- coding: utf-8 -*-
"""Stimmt die H-Messkette ueberhaupt? Von Grund auf (31.08.2026)

## Der Anlass

Nutzereinwand 31.08.: *"du hast mehrmals aus dem Cache gearbeitet - bei
einem Fehler wird das immer zu denselben Ergebnissen fuehren."*

⚠️ BERECHTIGT UND UNBEANTWORTET. Fuenf Zwischenspeicher mit zusammen 1,3 GB
sind in dieser Arbeit entstanden, und ALLE stammen aus derselben Quelle:
`simuliere_bremse._reihen_roh` -> `messe_marken._SwingSpeicher` ->
`messe_marken._niveaus_schnell`. Ein Fehler dort ist in jeder einzelnen
Messung dieser drei Tage enthalten - und faellt durch keine Wiederholung
auf, weil jede Wiederholung ihn mitbringt.

## Was hier geprueft wird - und zwar OHNE Zwischenspeicher

  V1 PRODUKTION     Rechnet `messe_marken` dasselbe wie `vorfilter.bewerte()`?
                    Die Messung nutzt eine eigene A/B-Logik; die Produktion
                    hat ihre eigene. Laufen sie auseinander, misst diese
                    Arbeit seit drei Tagen etwas anderes als das System tut.
  V2 QUELLE         Stimmen die Kursreihen? Stichproben gegen die Datenbank,
                    ohne den Umweg ueber die Ladefunktion.
  V3 MARKEN         Sind die Niveaus plausibel - Anzahl, Abstand, Alter?
                    Und: ist `_gefegt` wirklich rueckwaertsgerichtet?
  V4 QUERVERGLEICH  Stimmen die fuenf Zwischenspeicher untereinander ueberein,
                    wo sie dasselbe messen? Ein Cache, der von den anderen
                    abweicht, ist ein Fund.
  V5 LOOKAHEAD      Die gefaehrlichste Klasse: weiss ein Anker etwas ueber
                    seine eigene Zukunft? Geprueft mit einer GEKUERZTEN
                    Reihe - kennt der Anker dieselben Marken, wenn die
                    Zukunft physisch fehlt?

⚠️ V5 IST DER KERNTEST. Wenn die Marken die Zukunft kennen, ist JEDER Befund
dieser drei Tage wertlos - auch die negativen.

    python pruefe_h_kette_von_grund_auf.py
"""
import io
import json
import sqlite3
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from messe_marken import (CRV, K, MIN_BERUEHRUNGEN,                # noqa: E402
                          _niveaus_schnell, _SwingSpeicher)
from simuliere_bremse import _reihen_roh, klassen_aus_db           # noqa: E402

DB = "data/messdaten.db"
FEHLER = []


def pruefe(name, bedingung, hinweis=""):
    print("%s  %s%s" % ("  OK  " if bedingung else "  FEHL", name,
                        ("   -> " + hinweis) if hinweis and not bedingung else ""))
    if not bedingung:
        FEHLER.append(name)


print("=" * 100)
print("DIE H-MESSKETTE VON GRUND AUF — ohne Zwischenspeicher")
print("=" * 100)

print()
print("Lade Reihen frisch aus der Datenbank...", flush=True)
roh = _reihen_roh(DB, "krypto", klassen_aus_db(DB))
print("%d Reihen geladen." % len(roh))
proben = sorted(roh)[:8]

# ---------------------------------------------------------------- V2 QUELLE
print()
print("-" * 100)
print("V2 — DIE QUELLE: stimmen die Kursreihen mit der Datenbank?")
print("-" * 100)
c = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
abw = 0
for sym in proben:
    cc, hh, ll, vv, aa, off, dd = roh[sym]
    zeilen = c.execute(
        "SELECT date, close, high, low FROM price_history_ohlc "
        "WHERE symbol=? AND currency='USD' AND close IS NOT NULL AND close>0 "
        "ORDER BY date", (sym,)).fetchall()
    db_tage = {t[:10]: (float(k), float(h or k), float(l or k))
               for t, k, h, l in zeilen}
    stich = [int(x) for x in np.linspace(0, len(cc) - 1, 20)]
    for i in stich:
        tag = dd[i]
        if tag not in db_tage:
            abw += 1
            continue
        k_db, h_db, l_db = db_tage[tag]
        if (abs(float(cc[i]) - k_db) > 1e-9 or abs(float(hh[i]) - h_db) > 1e-9
                or abs(float(ll[i]) - l_db) > 1e-9):
            abw += 1
c.close()
pruefe("160 Stichproben aus 8 Reihen stimmen mit der DB ueberein", abw == 0,
       "%d Abweichungen" % abw)

# --------------------------------------------------------------- V5 LOOKAHEAD
print()
print("-" * 100)
print("⚠️ V5 — DER KERNTEST: kennt ein Anker seine eigene ZUKUNFT?")
print("-" * 100)
print("  Gerechnet werden dieselben Marken zweimal: einmal auf der VOLLEN")
print("  Reihe, einmal auf einer bei i GEKUERZTEN. Sind sie verschieden,")
print("  fliesst Zukunft ein - und jeder Befund dieser drei Tage faellt.")
unterschiede, geprueft = 0, 0
for sym in proben[:5]:
    cc, hh, ll, vv, aa, off, dd = roh[sym]
    if len(cc) < 700:
        continue
    sp_voll = _SwingSpeicher(hh, ll)
    for i in [int(x) for x in np.linspace(400, len(cc) - 40, 6)]:
        atr = float(aa[i - off])
        if atr <= 0:
            continue
        n_voll = _niveaus_schnell(sp_voll, cc, hh, ll, i, atr)
        # Dieselbe Rechnung auf einer Reihe, die NACH i physisch endet
        c2, h2, l2 = cc[:i + 1], hh[:i + 1], ll[:i + 1]
        sp_kurz = _SwingSpeicher(h2, l2)
        n_kurz = _niveaus_schnell(sp_kurz, c2, h2, l2, i, atr)
        for seite in ("oben", "unten"):
            a = sorted((round(m["preis"], 10), m["beruehrungen"],
                        m.get("gefegt")) for m in n_voll[seite])
            b = sorted((round(m["preis"], 10), m["beruehrungen"],
                        m.get("gefegt")) for m in n_kurz[seite])
            geprueft += 1
            if a != b:
                unterschiede += 1
pruefe("%d Vergleiche voll gegen gekuerzt - kein Unterschied" % geprueft,
       unterschiede == 0,
       "%d Faelle weichen ab - die Marken kennen die Zukunft" % unterschiede)

# ------------------------------------------------------------- V1 PRODUKTION
print()
print("-" * 100)
print("V1 — PRODUKTION: rechnet `vorfilter.bewerte()` dasselbe H?")
print("-" * 100)
from agent import lagebeschreibung as LB                          # noqa: E402
from agent import vorfilter as VF                                 # noqa: E402

gleich, verschieden, ohne_urteil = 0, 0, 0
beispiele = []
for sym in proben[:5]:
    cc, hh, ll, vv, aa, off, dd = roh[sym]
    if len(cc) < 700:
        continue
    sp = _SwingSpeicher(hh, ll)
    for i in [int(x) for x in np.linspace(400, len(cc) - 40, 12)]:
        atr, kurs = float(aa[i - off]), float(cc[i])
        if not (atr > 0 and kurs > 0):
            continue
        stop = kurs - K * atr
        if stop <= 0:
            continue
        ziel = kurs + CRV * (kurs - stop)
        n = _niveaus_schnell(sp, cc, hh, ll, i, atr)
        # Messung
        frei = not any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                       and m["preis"] < ziel for m in n["oben"])
        gedeckt = any(m["beruehrungen"] >= MIN_BERUEHRUNGEN
                      and m["preis"] > stop for m in n["unten"])
        h_messung = bool(frei and gedeckt)
        # Produktion - mit demselben Markenwerk
        aus = VF.bewerte(n, stop, ziel, assetklasse="krypto")
        h_prod = aus.get("h")
        if h_prod is None:
            ohne_urteil += 1
            continue
        if bool(h_prod) == h_messung:
            gleich += 1
        else:
            verschieden += 1
            if len(beispiele) < 3:
                beispiele.append((sym, dd[i], h_messung, h_prod,
                                  aus.get("grund", "")))
print("  gleich %d   verschieden %d   ohne Urteil %d"
      % (gleich, verschieden, ohne_urteil))
for b in beispiele:
    print("    %s %s: Messung %s, Produktion %s  (%s)" % b)
pruefe("Messung und Produktion urteilen identisch", verschieden == 0,
       "%d Abweichungen - die Messung misst nicht, was das System rechnet"
       % verschieden)

# ------------------------------------------------------------ V3 MARKEN
print()
print("-" * 100)
print("V3 — SIND DIE MARKEN PLAUSIBEL?")
print("-" * 100)
anz_oben, anz_unten, abst = [], [], []
for sym in proben:
    cc, hh, ll, vv, aa, off, dd = roh[sym]
    if len(cc) < 700:
        continue
    sp = _SwingSpeicher(hh, ll)
    for i in [int(x) for x in np.linspace(400, len(cc) - 40, 25)]:
        atr, kurs = float(aa[i - off]), float(cc[i])
        if not (atr > 0 and kurs > 0):
            continue
        n = _niveaus_schnell(sp, cc, hh, ll, i, atr)
        o = [m for m in n["oben"] if m["beruehrungen"] >= MIN_BERUEHRUNGEN]
        u = [m for m in n["unten"] if m["beruehrungen"] >= MIN_BERUEHRUNGEN]
        anz_oben.append(len(o))
        anz_unten.append(len(u))
        for m in o + u:
            abst.append(abs(m["preis"] - kurs) / atr)
print("  Marken je Anker: oben Median %.1f, unten Median %.1f"
      % (st.median(anz_oben), st.median(anz_unten)))
print("  Abstand in ATR:  Median %.2f, Minimum %.2f, Maximum %.1f"
      % (st.median(abst), min(abst), max(abst)))
pruefe("kein Abstand unter der Totzone %.2f ATR" % LB.NIVEAU_MIN_ABSTAND_ATR,
       min(abst) >= LB.NIVEAU_MIN_ABSTAND_ATR - 1e-9,
       "Minimum %.3f - die Totzone greift nicht" % min(abst))
pruefe("es gibt ueberhaupt Marken auf beiden Seiten",
       st.median(anz_oben) > 0 and st.median(anz_unten) > 0)

# -------------------------------------------------------- V4 QUERVERGLEICH
print()
print("-" * 100)
print("V4 — STIMMEN DIE FUENF ZWISCHENSPEICHER UEBEREIN?")
print("-" * 100)
import os                                                         # noqa: E402
caches = {"anker_h_2026_08_30.json": ("h", "in_r"),
          "anker_h_produktion_2026_08_30.json": ("h_alt", "r_alt"),
          "anker_h_neu_2026_08_30.json": (None, "in_r"),
          "anker_h3_2026_08_30.json": ("h_0.5_2", "in_r"),
          "anker_boden_2026_08_31.json": (None, "in_r")}
stand = {}
for datei, (hfeld, rfeld) in caches.items():
    if not os.path.exists(datei):
        print("  %-42s fehlt" % datei)
        continue
    d = json.loads(io.open(datei, encoding="utf-8").read())
    hq = (100 * sum(1 for a in d if a.get(hfeld)) / len(d)) if hfeld else None
    stand[datei] = {"n": len(d), "sym": len({a["sym"] for a in d}),
                    "von": min(a["datum"] for a in d),
                    "bis": max(a["datum"] for a in d),
                    "h": hq,
                    "med": st.median([a[rfeld] for a in d
                                      if a.get(rfeld) is not None])}
    print("  %-42s %7d Anker  %3d Sym  %s..%s  H %s  Median %+.4f"
          % (datei, stand[datei]["n"], stand[datei]["sym"],
             stand[datei]["von"][:7], stand[datei]["bis"][:7],
             ("%5.2f %%" % hq) if hq is not None else "  -   ",
             stand[datei]["med"]))
hs = [v["h"] for v in stand.values() if v["h"] is not None]
if len(hs) >= 2:
    pruefe("H-Quoten der Zwischenspeicher liegen beieinander (%.2f .. %.2f %%)"
           % (min(hs), max(hs)), max(hs) - min(hs) < 2.0,
           "Spanne %.2f Punkte - ein Cache misst etwas anderes"
           % (max(hs) - min(hs)))

print()
print("=" * 100)
if FEHLER:
    print("⚠️ %d PRUEFUNG(EN) FEHLGESCHLAGEN:" % len(FEHLER))
    for f in FEHLER:
        print("   - %s" % f)
    sys.exit(1)
print("ALLE PRUEFUNGEN BESTANDEN — die Messkette ist in Ordnung.")
