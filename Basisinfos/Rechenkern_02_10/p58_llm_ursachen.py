"""P58 URSACHENANALYSE: Warum trennen die LLM-Rollen nicht? (15.10.2026; Nutzer: "mir fehlt hierbei immer eine Begruendung und Analyse -
technisch und fachlich: wo sind wir falsch gelegen, wo koennten die Ursachen sein ... wir muessen wissen, wohin wir uns bewegen muessen")

    python Basisinfos/Rechenkern_02_10/p58_llm_ursachen.py

Nur lesend: data/_n4/n4_ablage.db, data/_n5/n5_ablage.db (mode=ro), data/_n5/n5_bericht_anker.csv (24-h-Ertrag je Anker), Stundenkurse
fuer die Zahlen der Lage zur Signalstunde (n5_auswertung.merkmale - derselbe Rechenweg wie der Regel-Arm F).

  A  Basislage: Urteilsverteilung, Ertrag je Urteil und Jahr (0.1e = N4, 0.2 = N5) - wie stark ist das LLM negativ gestimmt?
  B  WORAUF REAGIERT DAS LLM? Rangkorrelation jedes Merkmals mit dem Urteil (+1 stuetzt / 0 / -1 dagegen)
  C  WAS TRAEGT WIRKLICH? Rangkorrelation jedes Merkmals mit dem 24-h-Ertrag je Jahr - und gegen die Richtung, die das LLM ihm gibt
  D  DIE BEGRUENDUNGEN: welche Arten von Belegen nennt das LLM fuer 'dagegen' / 'dafuer' - und lagen Anker, bei denen ein Beleg 'dagegen'
     zaehlte, tatsaechlich schlechter?
  E  STABILITAET: Einstimmigkeit der 5 Stimmen, Wechsel bei vertauschten Bloecken (R_v)
Ergebnis: eine Liste der Ursachen mit Beleg - nicht eine Vermutung.
"""
import json
import os
import re
import sqlite3
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
os.chdir(PROJ)
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import n5_auswertung as A5  # noqa: E402

CODE = {"stuetzt": 1, "spricht_dagegen": -1, "neutral": 0}
KATEG = [  # (Name, Muster im Beleg-Text)
    ("Struktur tiefere Hochs / Abwaertstrend", r"tiefere hoch|abwaerts|abwärts|trend"),
    ("Unterstuetzung durchbrochen / tiefer", r"unterstuetzung|unterstützung"),
    ("Widerstand oberhalb", r"widerstand"),
    ("lange Sicht / 200-Tage-Schnitt", r"200-tage|60 tage|lange sicht|langen sicht"),
    ("Fall 6 h / 24 h (Rueckgang)", r"6 stunden|24 stunden|rueckgang|rückgang|gefallen|fall"),
    ("Umsatz / Volumen", r"umsatz|volumen"),
    ("Docht / Schluss nahe Tief", r"spanne|docht|nahe am tief|tief der"),
    ("Kapitulation / Liquidationen", r"kapitul|liquid"),
    ("Bitcoin", r"bitcoin|btc"),
    ("Praemie / Funding", r"praemie|prämie|funding|finanzier"),
    ("Schwankungsbreite", r"schwankung"),
]


def stimmen(pfad):
    c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
    st = pd.read_sql("SELECT pos, stimme, urteil, gueltig, roh, modell FROM stimme WHERE teil='T'", c)
    rv = pd.read_sql("SELECT pos, stimme, urteil, gueltig FROM stimme WHERE teil='R_v'", c) if c.execute(
        "SELECT 1 FROM stimme WHERE teil='R_v' LIMIT 1").fetchone() else pd.DataFrame()
    ein = pd.read_sql("SELECT pos, symbol, jahr, signalstunde, eingabe FROM eingabe", c)
    c.close()
    return st[st.gueltig == 1], (rv[rv.gueltig == 1] if len(rv) else rv), ein


def mehrheit(g):
    z = g.urteil.value_counts()
    if len(z) > 1 and z.iloc[0] == z.iloc[1]:
        return "uneinig"
    return z.index[0] if z.iloc[0] >= 3 else "uneinig"


def spearman(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    return pd.Series(a[m]).rank().corr(pd.Series(b[m]).rank()) if m.sum() > 10 else np.nan


def main():
    d = pd.read_csv("data/_n5/n5_bericht_anker.csv", sep=";").set_index("pos")
    st5, rv5, ein = stimmen("data/_n5/n5_ablage.db")
    st4, rv4, _ = stimmen("data/_n4/n4_ablage.db")
    pos = d.index
    m5 = st5.groupby("pos").apply(mehrheit).reindex(pos)
    m4 = st4.groupby("pos").apply(mehrheit).reindex(pos)
    y = d.spot
    print("P58 URSACHENANALYSE LLM-Rollen · %d Anker (dieselben in N4 0.1e und N5 0.2) · Modell %s\n" % (len(pos), ", ".join(sorted(set(st5.modell) | set(st4.modell)))))

    # ══ A Basislage ══════════════════════════════════════════════════════════════════════════════════════════════════════════
    print("A  BASISLAGE (24-h-Ertrag nach dem Einstieg; die REGEL0 kauft JEDEN dieser Anker)")
    print("   Ertrag aller Anker: Mittel %+.2f %% · Anteil > 0: %.0f %% · je Jahr %s" % (100 * y.mean(), 100 * (y > 0).mean(),
          " · ".join("%d %+.2f %%" % (j, 100 * y[d.jahr == j].mean()) for j in (2025, 2026))))
    for name, m in (("0.1e (N4)", m4), ("0.2 (N5)", m5)):
        vt = m.value_counts().to_dict()
        je = " · ".join("%s n %d %+.2f %%" % (u, int((m == u).sum()), 100 * y[m == u].mean()) for u in ("stuetzt", "neutral", "spricht_dagegen", "uneinig") if (m == u).any())
        print("   %-10s Verteilung %s" % (name, vt))
        print("              Ertrag je Urteil: %s" % je)
    print()

    # ══ Merkmale ═════════════════════════════════════════════════════════════════════════════════════════════════════════════
    rows = []
    for p in pos:
        e = ein.loc[ein.pos == p].iloc[0]
        mm = A5.merkmale(e.symbol, e.signalstunde)
        txt = " ".join(json.loads(e.eingabe).get("lage_des_werts") or []).lower()
        mm["struktur_tiefer"] = 1.0 if "tiefere hochs bei tieferen tiefs" in txt else (0.5 if "tiefere hochs" in txt else 0.0)
        mm["unter_200"] = 1.0 if "unter dem 200-tage-schnitt" in txt else 0.0
        mm["stuetze_durchbrochen"] = 1.0 if "durchbrochen" in txt else 0.0
        g60 = re.search(r"ueber 60 tage ([+-]\d+[,.]\d)", txt)
        mm["lauf60"] = float(g60.group(1).replace(",", ".")) if g60 else np.nan
        rows.append(mm)
    X = pd.DataFrame(rows, index=pos)
    namen = {"lumsatz": "Umsatz 24 h (log)", "fall6": "Fall 6 h", "fall24": "Fall 24 h", "docht": "Docht", "lkapit": "Kapitulation (log)",
             "praemie": "Praemie", "btc24": "Bitcoin 24 h", "btc168": "Bitcoin 7 T", "struktur_tiefer": "Struktur tiefere Hochs/Tiefs",
             "unter_200": "unter 200-Tage-Schnitt", "stuetze_durchbrochen": "Unterstuetzung durchbrochen", "lauf60": "Lauf 60 T"}
    s5 = m5.map(CODE).astype(float).values
    s4 = m4.map(CODE).astype(float).values
    beta = A5.regel_f_modell(os.path.join("data", "_n5", "n5_regel_f.json"))["beta"][1:]
    beta = dict(zip(A5.MERK, beta))
    print("B/C  WORAUF REAGIERT DAS LLM - und WAS TRAEGT? (Rangkorrelationen; Vorzeichen: + = hoeher Wert -> 'stuetzt' bzw. hoeherer Ertrag)")
    print("   %-30s %9s %9s | %9s %9s | %10s | %s" % ("Merkmal", "LLM 0.1e", "LLM 0.2", "Ertr.2025", "Ertr.2026", "Regel 2024", "Befund"))
    befunde = []
    for k in namen:
        if k not in X:
            continue
        x = X[k].values.astype(float)
        l4, l5 = spearman(x, s4), spearman(x, s5)
        e25, e26 = spearman(x[d.jahr.values == 2025], y.values[d.jahr.values == 2025]), spearman(x[d.jahr.values == 2026], y.values[d.jahr.values == 2026])
        b = beta.get(k, np.nan)
        llm = np.nanmean([l4, l5])
        wahr = np.nanmean([e25, e26])
        if abs(llm) >= 0.15 and abs(wahr) >= 0.05 and np.sign(llm) != np.sign(wahr):
            bef = "VERKEHRT: LLM liest es andersherum"
        elif abs(llm) >= 0.15 and abs(wahr) < 0.05:
            bef = "LLM stuetzt sich darauf, traegt aber nicht"
        elif abs(llm) < 0.1 and abs(wahr) >= 0.1:
            bef = "traegt, LLM ignoriert es"
        else:
            bef = ""
        if bef:
            befunde.append((k, bef, llm, e25, e26))
        print("   %-30s %+9.2f %+9.2f | %+9.2f %+9.2f | %+10.4f | %s" % (namen[k], l4, l5, e25, e26, b, bef))
    print()

    # ══ D Begruendungen ══════════════════════════════════════════════════════════════════════════════════════════════════════
    print("D  DIE BEGRUENDUNGEN (Fassung 0.2): Belege je Art und Richtung - und der Ertrag der Anker, bei denen die Art 'dagegen' zaehlte")
    bel = []
    for r in st5.itertuples():
        try:
            j = json.loads(r.roh) if r.roh else {}
        except Exception:                                        # noqa: BLE001
            j = {}
        for b in j.get("belege") or []:
            t = str(b.get("fakt", "")).lower()
            kat = next((n for n, mu in KATEG if re.search(mu, t)), "sonstiges")
            bel.append((r.pos, r.stimme, kat, b.get("richtung")))
    B = pd.DataFrame(bel, columns=["pos", "stimme", "kat", "richtung"])
    print("   Belege gesamt %d (%.1f je Stimme)" % (len(B), len(B) / max(len(st5), 1)))
    for kat, g in B.groupby("kat"):
        dg = g[g.richtung == "dagegen"].pos.unique()
        df = g[g.richtung == "dafuer"].pos.unique()
        rest = [p for p in pos if p not in set(dg)]
        print("   %-38s dagegen %4d · dafuer %4d | Anker mit 'dagegen' %3d: Ertrag %+.2f %% (uebrige %+.2f %%)" % (
            kat, int((g.richtung == "dagegen").sum()), int((g.richtung == "dafuer").sum()), len(dg),
            100 * y.reindex(dg).mean() if len(dg) else np.nan, 100 * y.reindex(rest).mean()))
    print()

    # ══ E Stabilitaet ════════════════════════════════════════════════════════════════════════════════════════════════════════
    print("E  STABILITAET")
    for name, st, rv in (("0.1e (N4)", st4, rv4), ("0.2 (N5)", st5, rv5)):
        ein_ = st.groupby("pos").urteil.agg(lambda s: s.value_counts().iloc[0] / len(s))
        txt = "   %-10s 5 von 5 gleich: %.0f %% der Anker · 3 von 5 oder weniger: %.0f %%" % (name, 100 * (ein_ == 1).mean(), 100 * (ein_ <= 0.6).mean())
        if len(rv):
            mrv = rv.groupby("pos").apply(mehrheit)
            mt = st.groupby("pos").apply(mehrheit).reindex(mrv.index)
            txt += " · R_v (Bloecke vertauscht) gleiches Urteil %.0f %%" % (100 * (mrv == mt).mean())
        print(txt)
    print()
    print("ZUSAMMENFASSUNG DER BEFUNDE (aus B/C):")
    for k, bef, llm, e25, e26 in befunde:
        print("   - %s: %s (LLM %+.2f · Ertrag 2025 %+.2f / 2026 %+.2f)" % (namen[k], bef, llm, e25, e26))


if __name__ == "__main__":
    main()
