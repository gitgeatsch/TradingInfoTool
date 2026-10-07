"""A1 - WORAN abschliessen (Voranalyse_Schritt7 §23.13, E-76/E-77): warum trennt der LLM-Trader (N4, Fassung 0.1e) nicht? NUR die Ablage,
KEINE neuen Aufrufe, nur lesend (mode=ro).

    python Basisinfos/Rechenkern_02_10/a1_woran.py

VORAB FESTGELEGT (07.10.2026, vor dem ersten Lauf):
  A1-a  Welche FAKTEN fuehrt der Trader als 'dagegen' an? - ueber ALLE gueltigen T-Stimmen: jeder Beleg wird einem Fakt-Typ zugeordnet
        (Stichwortregel unten, aus dem Wortlaut der Eingabe), Anteil 'dagegen' je Typ; dazu der Typ des Gegengrunds.
  A1-b  Woran haengt das Mehrheitsurteil? - die Zahlen der Eingabe je Anker (60-T-Aenderung, Abstand zum 200-T-Schnitt in Schwankungsbreiten,
        Marktstruktur, Umsatzfaktor, Schwankungsperzentil, Anteil Umsatz an Aufwaertstagen) gegen das Urteil (Anteil 'dagegen' je Drittel).
  A1-c  Hilft der Fakt, den der Trader als 'dagegen' wertet, in der WETTE (24-h-Ertrag nach dem Signal)? - je Fakt Rangkorrelation mit dem
        Ertrag, je Jahr, Nullwelt 1.000 Vertauschungen innerhalb des Tages. Ein Fakt, den der Trader als Gegengrund nutzt, der den Ertrag aber
        NICHT (oder umgekehrt) ordnet, ist der Mechanismus des Scheiterns (W6: argumentiert mit Trend gegen die Wette).
  A1-d  W6-Stichprobe: 30 Begruendungen (10 je Mehrheitsurteil stuetzt/dagegen/neutral, Saat 20261007) zum Lesen ausgegeben.
  W3 (Reihenfolge) folgt nach Ende von R_v.
Gegenpruefung (a1_gegenprobe.py): Zaehlung der Urteile unabhaengig von urteile(), Zahlenzerlegung von 10 Ankern gegen den Wortlaut.
"""
import json
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import n4_auswertung as NA  # noqa: E402

ABLAGE = os.path.join(os.path.dirname(os.path.dirname(HIER)), "data", "_n4", "n4_ablage.db")
TYPEN = [("Trend lang (60 T / 200-T-Schnitt)", ("200-tage", "60 tage", "lange sicht", "langen sicht")),
         ("Marktstruktur", ("marktstruktur", "hoehere hochs", "tiefere tiefs", "wendepunkt")),
         ("Widerstand", ("widerstand",)), ("Unterstuetzung", ("unterstuetzung", "unterstützung")),
         ("Schwankung", ("schwankungsbreite liegt", "perzentil")),
         ("Umsatz Hoehe", ("fache des 20-tage", "-fachen", "umsatz liegt")),
         ("Umsatz Aufwaertstage", ("aufwaertstage", "aufwärtstage")),
         ("Umsatz Verteilung", ("ueber dem schnitt", "über dem schnitt", "einzelne tage", "letzten 10 tage"))]


def typ(text):
    t = text.lower()
    for name, worte in TYPEN:
        if any(w in t for w in worte):
            return name
    return "sonstiges"


def zahlen(eingabe):
    d = json.loads(eingabe)
    z = " ".join(d.get("lage_des_werts", []))
    out = {}
    m = re.search(r"ueber 60 Tage ([-+]?\d+,\d+) %", z)
    out["aend60"] = float(m.group(1).replace(",", ".")) if m else np.nan
    m = re.search(r"([\d,]+) Schwankungsbreiten (unter|ueber) dem 200-Tage-Schnitt", z)
    out["abst200"] = (float(m.group(1).replace(",", ".")) * (-1 if m.group(2) == "unter" else 1)) if m else np.nan
    out["struktur_hoch"] = 1.0 if "hoehere Hochs und hoehere Tiefs" in z else (0.0 if "tiefere" in z or "Marktstruktur" in z else np.nan)
    m = re.search(r"Umsatz liegt beim ([\d,]+)-fachen", z)
    out["umsatz"] = float(m.group(1).replace(",", ".")) if m else np.nan
    m = re.search(r"im (\d+)\. Perzentil der letzten 250 Tage", z)
    out["schw_perz"] = float(m.group(1)) if m else np.nan
    m = re.search(r"entfielen (\d+) % des Umsatzes auf Aufwaertstage", z)
    out["auf_anteil"] = float(m.group(1)) if m else np.nan
    m = re.search(r"Widerstandsmarke liegt ([\d,]+) Schwankungsbreiten", z)
    out["widerstand"] = float(m.group(1).replace(",", ".")) if m else np.nan
    m = re.search(r"Unterstuetzungsmarke liegt ([\d,]+) Schwankungsbreiten", z)
    out["unterstuetzung"] = float(m.group(1).replace(",", ".")) if m else np.nan
    return out


def main():
    c = sqlite3.connect("file:%s?mode=ro" % ABLAGE, uri=True)
    st = pd.read_sql("SELECT pos, stimme, urteil, gueltig, roh FROM stimme WHERE teil='T'", c)
    st = st[st.gueltig == 1]
    print("A1 WORAN (Schritt7 §23.13) · gueltige T-Stimmen %d an %d Ankern · keine neuen Aufrufe\n" % (len(st), st.pos.nunique()))
    # A1-a
    bel, geg = [], []
    for r in st.itertuples():
        try:
            a = json.loads(r.roh)
            a = json.loads(a) if isinstance(a, str) else a
        except Exception:                                             # noqa: BLE001
            continue
        for b in a.get("belege", []) or []:
            bel.append((typ(b.get("fakt", "")), b.get("richtung"), r.urteil))
        geg.append((typ(a.get("gegengrund", "") or ""), r.urteil))
    B = pd.DataFrame(bel, columns=["typ", "richtung", "urteil"])
    G = pd.DataFrame(geg, columns=["typ", "urteil"])
    print("A1-a  Belege je Fakt-Typ (alle Stimmen): Anzahl · Anteil 'dagegen' · Anteil als GEGENGRUND genannt")
    for t_, g in B.groupby("typ"):
        print("      %-36s %5d · dagegen %3.0f %% · Gegengrund %3.0f %%" % (t_, len(g), 100 * (g.richtung == "dagegen").mean(), 100 * (G.typ == t_).mean()))
    # A1-b / A1-c
    d = NA.urteile(c, "T")
    e = pd.read_sql("SELECT pos, eingabe FROM eingabe", c).set_index("pos")
    Z = pd.DataFrame([dict(pos=p, **zahlen(e.at[p, "eingabe"])) for p in d.pos]).set_index("pos")
    d = d.join(Z, on="pos")
    print("\nA1-b  Urteil (Mehrheit) je Drittel der Eingabezahl: Anteil 'dagegen' / 'stuetzt' (n %d Anker)" % len(d))
    for k in ("aend60", "abst200", "umsatz", "schw_perz", "auf_anteil", "widerstand", "unterstuetzung", "struktur_hoch"):
        x = d[d[k].notna()]
        if x[k].nunique() <= 2:
            teile = [(v, x[x[k] == v]) for v in sorted(x[k].unique())]
            lab = ["= %g" % v for v, _ in teile]
        else:
            q = x[k].quantile([1 / 3, 2 / 3]).values
            teile = [(0, x[x[k] <= q[0]]), (1, x[(x[k] > q[0]) & (x[k] <= q[1])]), (2, x[x[k] > q[1]])]
            lab = ["<= %.1f" % q[0], "%.1f..%.1f" % (q[0], q[1]), "> %.1f" % q[1]]
        print("      %-15s %s" % (k, " | ".join("%s: dagegen %3.0f %% stuetzt %2.0f %% (n %d)" % (l_, 100 * (g.urteil == "spricht_dagegen").mean(),
                                                   100 * (g.urteil == "stuetzt").mean(), len(g)) for l_, (_, g) in zip(lab, teile))))
    rng = np.random.default_rng(20261007)
    print("\nA1-c  Ordnet die Eingabezahl den 24-h-Ertrag (die Wette)? Rangkorrelation, Nullwelt 1.000 Vertauschungen im Tag (zweiseitig)")
    print("      und wie stark haengt das URTEIL (Saldo der Stimmen) an derselben Zahl")
    for k in ("aend60", "abst200", "umsatz", "schw_perz", "auf_anteil", "widerstand", "unterstuetzung", "struktur_hoch"):
        teile = []
        for j in ("2025", "2026"):
            x = d[(d.jahr.astype(str) == j) & d[k].notna()]
            if len(x) < 20:
                teile.append("%s -" % j); continue
            rho = x[k].rank().corr(x.spot.rank())
            nul = []
            gr = [g.index.values for _, g in x.groupby("tag")]
            for _ in range(1000):
                y = x.spot.copy()
                for ix in gr:
                    y.loc[ix] = rng.permutation(y.loc[ix].values)
                nul.append(x[k].rank().corr(y.rank()))
            nul = np.array(nul)
            p2 = float(np.mean(np.abs(nul) >= abs(rho)))
            rho_u = x[k].rank().corr(x.saldo.rank())
            teile.append("%s Ertrag rho %+.3f (p2 %.3f) · Urteil rho %+.3f" % (j, rho, p2, rho_u))
        print("      %-15s %s" % (k, " | ".join(teile)))
    # A1-d Stichprobe
    print("\nA1-d  W6-Stichprobe: 30 Begruendungen (10 je Mehrheitsurteil)")
    rng2 = np.random.default_rng(20261007)
    for u in ("stuetzt", "spricht_dagegen", "neutral"):
        pos = d[d.urteil == u].pos.values
        for p in rng2.choice(pos, size=min(10, len(pos)), replace=False):
            r = st[(st.pos == p)].iloc[0]
            try:
                a = json.loads(r.roh); a = json.loads(a) if isinstance(a, str) else a
            except Exception:                                         # noqa: BLE001
                a = {}
            sp = d[d.pos == p].spot.iloc[0]
            print("   [%s] pos %4d %-8s 24h %+5.1f %% | %s | GEGEN: %s" % (u[:7], p, d[d.pos == p].symbol.iloc[0], 100 * sp,
                                                                     (a.get("begruendung") or "")[:230], (a.get("gegengrund") or "")[:140]))


if __name__ == "__main__":
    main()
