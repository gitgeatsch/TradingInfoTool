"""P22c Freigabe-Rhythmus als Fakt (15.10.2026, Spot §55) - Pruefstand am SEITENEFFEKT, nur Wegwerf-Dateien (D:).

    python Basisinfos/Rechenkern_02_10/p22c_pruefstand.py

  C1  Gegenprobe: der Rhythmus des Moduls = eine UNABHAENGIGE Schleifen-Rechnung (ohne pandas.pct_change) fuer alle Coins am 22.09.2026,
      und = die Voranalyse p55 (dieselbe Liste lebender Rhythmen)
  C2  die in der Mail genannten Trefferquoten (TREFFER) reproduziert die Rueckschau MIT DEM MODULCODE exakt (88 % von 76, 74 % von 23)
  C3  Texte: lebend (APT), ueberfaellig (APT, 4 Wochen spaeter ohne neue Daten), ohne Rhythmus (kein Satz), nicht rueckgeprueft (AVA)
  C4  Mails: B1/B3/REGEL0 ueber fakt() mit Satz; B4 ueber verw_am_stichtag mit Satz; Coin ohne Rhythmus ohne Satz
  C5  Statusseite: stand() liefert die Bestandscoins mit Rhythmus, nach Termin
  C6  Mengenreihe unveraendert
"""
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import date

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
import wegwerf  # noqa: E402,F401  Wegwerf-Ordner auf D: und Aufraeumen ohne stilles Scheitern (15.10.2026)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import agent.spot_abbau as SA  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
import agent.verwaesserung as VW  # noqa: E402
import p55_rhythmus_voranalyse as P55  # noqa: E402

ERG = []
HEUTE = pd.Timestamp("2026-09-22")


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


T = tempfile.mkdtemp(prefix="p22c_")
O = os.path.join(T, "nb")
os.makedirs(O)
shutil.copy("data/umlaufmenge_cg.db", os.path.join(O, SA.UMLAUF))
u_vor = summe(os.path.join(O, SA.UMLAUF))
REIHEN = SA._umlauf(O)
c = sqlite3.connect("file:%s?mode=ro" % os.path.join(O, SA.UMLAUF).replace("\\", "/"), uri=True)
OK = {r[0] for r in c.execute("SELECT symbol FROM abruf_symbol WHERE urteil='ok'")}
c.close()


# ══ C1 unabhaengige Schleife ═════════════════════════════════════════════════════════════════════════════════════════════════
def eigen(r, heute):
    r = r[r.index <= heute].sort_index()
    if len(r) < 30:
        return None
    tage = pd.date_range(r.index[0], r.index[-1], freq="D")
    werte, letzt, alter = [], None, 99
    for t in tage:                                              # vorwaerts fuellen hoechstens 3 T, wie das Modul
        if t in r.index:
            letzt, alter = float(r[t]), 0
        else:
            alter += 1
        werte.append(letzt if alter <= 3 else None)
    ev = []
    for i in range(1, len(tage)):
        a, b = werte[i - 1], werte[i]
        if a and b and b / a - 1 >= 0.01 and (not ev or (tage[i] - ev[-1]).days > 3):
            ev.append(tage[i])
        elif a and b and b / a - 1 >= 0.01:
            pass
    # "ein Ereignis je Folge": der erste Tag zaehlt, Folgetage mit <= 3 T Abstand zum VORIGEN Sprungtag gehoeren dazu
    sp = [tage[i] for i in range(1, len(tage)) if werte[i - 1] and werte[i] and werte[i] / werte[i - 1] - 1 >= 0.01]
    ev = [sp[0]] + [b for a, b in zip(sp[:-1], sp[1:]) if (b - a).days > 3] if sp else []
    e = [x for x in ev if x > heute - pd.Timedelta(days=365)]
    if len(e) < 4:
        return None
    ab = [(b - a).days for a, b in zip(e[:-1], e[1:])]
    for name, (lo, hi) in (("monatlich", (26, 35)), ("vierteljährlich", (80, 100)), ("wöchentlich", (6, 8))):
        im = [lo <= x <= hi for x in ab]
        if sum(im) / len(im) >= 0.7 and all(im[-2:]) and (heute - e[-1]).days <= hi + 5:
            med = int(np.median([x for x, j in zip(ab, im) if j]))
            return name, len(e), e[-1].date(), (e[-1] + pd.Timedelta(days=med)).date()
    return None


mod, eig = {}, {}
for s in sorted(OK):
    r = REIHEN.get(s)
    if r is None:
        continue
    m = VW.rhythmus(r, HEUTE)
    mod[s] = (m["art"], m["n"], m["letzte"], m["naechste"]) if m else None
    eig[s] = eigen(r, HEUTE)
ab1 = [s for s in mod if mod[s] != eig[s]]
# p55: dieselbe Liste lebender Rhythmen (p55 kennt die Bandnamen ohne Umlaut)
P = pd.DataFrame({s: REIHEN[s] for s in OK if s in REIHEN}).sort_index().asfreq("D").ffill(limit=3)
p55 = {s for s in P.columns if P55.rhythmus(P55.ereignisse(P[s].dropna()), P.index[-1])}
lebend = {s for s, v in mod.items() if v}
pruefe("C1", not ab1 and lebend == p55 and len(lebend) >= 5,
       "%d Coins · lebender Rhythmus %d (%s) · Abweichung Modul/Schleife %d%s · gleich p55 %s" % (
           len(mod), len(lebend), ", ".join(sorted(lebend)), len(ab1), (" " + str(ab1[:5])) if ab1 else "", lebend == p55))

# ══ C2 Trefferquoten mit dem Modulcode ═══════════════════════════════════════════════════════════════════════════════════════
tr = {k: [] for k in VW.BAENDER}
for s in OK:
    r = REIHEN.get(s)
    if r is None:
        continue
    ev = VW.ereignisse(r)
    for i in range(3, len(ev) - 1):
        m = VW.rhythmus(r, ev[i])
        if m:
            tr[m["art"]].append(abs((ev[i + 1].date() - m["naechste"]).days) <= 3)
quote = {k: (int(round(100 * np.mean(v))), len(v)) for k, v in tr.items() if v}
pruefe("C2", all(quote.get(k) == v for k, v in VW.TREFFER.items()), "Rueckschau mit Modulcode %s · in der Mail genannt %s" % (quote, VW.TREFFER))

# ══ C3 Texte ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════
t_apt = VW.rhythmus_text(VW.rhythmus(REIHEN["APT"], HEUTE))
t_spaet = VW.rhythmus_text(VW.rhythmus(REIHEN["APT"], pd.Timestamp("2026-10-20")))
t_btc = VW.rhythmus_text(VW.rhythmus(REIHEN.get("BTC"), HEUTE))
t_ava = VW.rhythmus_text(VW.rhythmus(REIHEN["AVA"], HEUTE)) if "AVA" in REIHEN else None
pruefe("C3", t_apt and "die nächste um den" in t_apt and "88 %" in t_apt and t_spaet and "fällig gewesen" in t_spaet and t_btc is None
       and (t_ava is None or "nicht rückgeprüft" in t_ava),
       "APT: %s | 20.10.: ...%s | BTC: %s | AVA: ...%s" % (t_apt, (t_spaet or "")[-90:], t_btc, (t_ava or "-")[-70:]))

# ══ C4 Mails ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════
f_apt = VW.fakt(O, "APT", HEUTE.date(), REIHEN)
f_btc = VW.fakt(O, "BTC", HEUTE.date(), REIHEN)
f1 = {"symbol": "APT", "ausloese_kurs": 9.0, "startkurs_usd": 3.0, "menge": 2.0, "ende": "2027-01-01", "start": "2026-01-01", "ausloese_tag": "2026-09-01"}
m1 = SM.mail(f1, 1.5, False, None, f_apt["text"])[1]
mt = VW.mailteil(O, "APT", HEUTE.date())
c = SA.oeffne(O)
VW.schema(c)
c.execute("INSERT INTO verw_universum VALUES ('2026-09-01','APT','H',0.03,4)")
c.execute("INSERT INTO verw_universum VALUES ('2026-09-01','BTC','H',0.001,1)")
c.execute("INSERT INTO abbau_lauf (stichtag, am, status, art, universum) VALUES ('2026-09-01','x','fertig','erstliste',2)")
c.execute("INSERT INTO abbau_fuenftel VALUES ('2026-09-01','APT','APT','H',-0.9,600,1000,0.05,1,NULL,10)")
c.execute("INSERT INTO abbau_fuenftel VALUES ('2026-09-01','BTC','BTC','H',-0.2,30,3000,0.5,3,NULL,1)")
c.commit()
c.close()
liste = [("APT", "APT", "H", -0.9, 600, 1000, 0.05, 1, None, 10), ("BTC", "BTC", "H", -0.2, 30, 3000, 0.5, 3, None, 1)]
verw = SA.verw_am_stichtag(O, "2026-09-01", liste)
b4 = SA.mail({"stichtag": "2026-09-01", "art": "erstliste", "liste": liste}, {"APT": 100.0, "BTC": 100.0}, set(), verw)[1]
z_apt = next((z for z in b4.splitlines() if z.strip().startswith("Verwässerung") and "Freigaben zuletzt" in z), None)
# KORREKTUR 15.10. (erster Lauf C4 rot - Fehler im PRUEFSTAND): der Messlage-Satz beginnt auch mit "Verwässerung" - nur Coin-Zeilen zaehlen
z_btc = [z for z in b4.splitlines() if z.strip().startswith("Verwässerung 90 T")]
pruefe("C4", "Freigaben zuletzt monatlich" in f_apt["text"] and "Freigaben" not in f_btc["text"] and "Freigaben zuletzt" in m1
       and "Freigaben zuletzt" in mt["ein"] and z_apt and len(z_btc) == 2 and sum("Freigaben" in z for z in z_btc) == 1,
       "B1 %s · REGEL0 %s · B4 APT mit Satz %s, BTC ohne %s" % ("Freigaben zuletzt" in m1, "Freigaben zuletzt" in mt["ein"], bool(z_apt),
                                                             sum("Freigaben" in z for z in z_btc) == 1))

# ══ C5 Statusseite ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
st = SA.stand(O)
rh_st = st.get("verw_rhythmus") or []
pruefe("C5", [r[0] for r in rh_st] == ["APT"] and rh_st[0][1] == "monatlich",
       "stand()['verw_rhythmus'] = %s (Stand: heute, nicht der 22.09.)" % rh_st)

# ══ C6 unveraendert ══════════════════════════════════════════════════════════════════════════════════════════════════════════
pruefe("C6", summe(os.path.join(O, SA.UMLAUF)) == u_vor, "Mengenreihe unveraendert")
print("\nMuster (C3): " + (t_apt or "-"))
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
