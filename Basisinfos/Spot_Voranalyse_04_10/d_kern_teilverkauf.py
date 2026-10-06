"""Spot D1-M und D2-M (Voranalyse_Spot_Neubau_04_10.md §12 und §12.5, vorab: Commits 2fdd6fa, 8962b52; E-68).

    python Basisinfos/Spot_Voranalyse_04_10/d_kern_teilverkauf.py

Nur lesend: data/_spot/coinmetrics.db (BTC, ETH), data/messdaten.db (SOL). Kein Netz, kein LLM. Alles in USD (Verhaeltnisse
haengen nicht an der Waehrung). Zufluss 1 Einheit am Starttag und jedem Monatsersten, gekauft zum Tagesschluss, keine Gebuehren
und keine Steuern (Regel 2).

D1-M: Mischungen M0 (100 % BTC, nur Massstab), V1 je 1/3, V2 70/20/10, V3 50/30/20, V4 nach Schwankung (1 / Streuung der
      Tagesrenditen der letzten 365 Tage, mind. 30, am Vortag); Ausgleich R0 nie, R1 ueber die Zufluesse (kein Verkauf),
      R2 alle 12 Monate auf das Ziel (mit Verkauf). Starts 01.10.2020, 2021, 2022, 2023, 11.01.2024; Ende 20.09.2026.
D2-M: je Kernwert; Ausloeser Klima q aus BTC (F3), bekannt am Schluss t-1, ausgefuehrt zum Schluss t; Stufen 0,80/0,90/0,95,
      je Zyklus einmal, wieder scharf nach einer Zone (q <= 0,20). Faelle b1-b4, d1-d2 (§12.3); Gegenwelt H0 = nie verkaufen.

AUSLEGUNG, vor dem ersten Lauf festgelegt (im Plan nicht genau bestimmt):
  - R2: Ausgleich am Tag 365, 730, ... nach dem Start (nach dem Kauf dieses Tages)
  - R1: der Zufluss fuellt zuerst die Luecken zum Ziel (anteilig), ein Rest geht nach Zielgewicht
  - b2-b4: Rueckkauf-Zyklus beginnt am ersten Zonentag mit wartendem Geld; Basis = Geld an diesem Tag; Drittel bei q <= 0,20 /
    0,10 / 0,05; spaeter verkauftes Geld kommt in den naechsten Zyklus; 365 T nach dem ersten Drittel wird der Rest gekauft
  - b1: das ganze wartende Geld am ersten Zonentag
  - groesster Rueckgang auf Vermoegen / Eingezahltes (bei D2 inkl. wartendem Geld bzw. Entnahme)
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src = open("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py", encoding="utf-8").read().split("pb, mb = lade")[0]
g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py")}
exec(compile(src, "k3", "exec"), g)

pb, mb = g["lade"]("btc")
pe, _me = g["lade"]("eth")
Q = g["klima"](pb, mb, pd.Timestamp("2013-01-01"))
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
ps = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol='SOL' ORDER BY date",
                 c, parse_dates=["date"]).set_index("date")["close"].asfreq("D").ffill()
c.close()
KURS = {"BTC": pb, "ETH": pe, "SOL": ps}
ENDE_D1 = pd.Timestamp("2026-09-20")


def zuflusstage(idx, start):
    return [t for t in idx if t == start or t.day == 1]


def max_rueckgang(wert, ein):
    x = np.asarray(wert) / np.asarray(ein)
    return float((x / np.maximum.accumulate(x) - 1).min())


# ============================================================================ D1-M
def schwankung(sym, t):
    r = np.log(KURS[sym]).diff()[:t - pd.Timedelta(days=1)].dropna().iloc[-365:]
    return float(r.std()) if len(r) >= 30 else np.nan


def ziel(mix, t):
    if mix == "M0":
        return {"BTC": 1.0, "ETH": 0.0, "SOL": 0.0}
    if mix == "V1":
        return {"BTC": 1 / 3, "ETH": 1 / 3, "SOL": 1 / 3}
    if mix == "V2":
        return {"BTC": 0.7, "ETH": 0.2, "SOL": 0.1}
    if mix == "V3":
        return {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2}
    inv = {s: 1 / schwankung(s, t) for s in KURS}
    tot = sum(inv.values())
    return {s: v / tot for s, v in inv.items()}


def d1(mix, art, start, ende=ENDE_D1):
    idx = pd.date_range(start, ende)
    zt = set(zuflusstage(idx, start))
    st = {s: 0.0 for s in KURS}
    ein, verk, rows = 0.0, 0, []
    for i, t in enumerate(idx):
        p = {s: KURS[s][t] for s in KURS}
        if t in zt:
            ein += 1.0
            w = ziel(mix, t)
            if art == "R1":
                wert = {s: st[s] * p[s] for s in KURS}
                ges = sum(wert.values()) + 1.0
                luecke = {s: max(0.0, w[s] * ges - wert[s]) for s in KURS}
                L = sum(luecke.values())
                if L >= 1.0:
                    kauf = {s: luecke[s] / L for s in KURS}
                else:
                    kauf = {s: luecke[s] + (1.0 - L) * w[s] for s in KURS}
            else:
                kauf = {s: w[s] for s in KURS}
            for s in KURS:
                st[s] += kauf[s] / p[s]
        if art == "R2" and i > 0 and i % 365 == 0:
            w = ziel(mix, t)
            ges = sum(st[s] * p[s] for s in KURS)
            for s in KURS:
                neu = w[s] * ges / p[s]
                verk += neu < st[s] - 1e-12
                st[s] = neu
        rows.append((t, sum(st[s] * p[s] for s in KURS), ein))
    r = pd.DataFrame(rows, columns=["t", "wert", "ein"]).set_index("t")
    return r, verk


def lauf_d1():
    starts = [pd.Timestamp(x) for x in ("2020-10-01", "2021-01-01", "2022-01-01", "2023-01-01", "2024-01-11")]
    print("=" * 30, "D1-M Kernwerte BTC/ETH/SOL - Ende %s" % ENDE_D1.date(), "=" * 30)
    w0 = ziel("V4", pd.Timestamp("2026-09-01"))
    print("V4 nach Schwankung, Gewichte am 01.09.2026: " + " · ".join("%s %.0f %%" % (s, 100 * v) for s, v in w0.items()))
    m0 = {st: d1("M0", "R0", st)[0] for st in starts}
    print("M0 100 % BTC: " + " · ".join("%s Verm. %.1f auf %d eingezahlt, Rueckgang %+.0f %%" % (
        st.date(), m0[st]["wert"].iloc[-1], m0[st]["ein"].iloc[-1], 100 * max_rueckgang(m0[st]["wert"], m0[st]["ein"])) for st in starts))
    print("\n  Fall     | Endvermoegen / M0 je Start (2020-10 / 2021 / 2022 / 2023 / 2024-01-11) | Median | Rueckgang Median (M0) | Monatsenden >= M0 | Verkaeufe")
    m0_rg = float(np.median([max_rueckgang(m0[s]["wert"], m0[s]["ein"]) for s in starts]))
    erg = []
    for mix in ("V1", "V2", "V3", "V4"):
        for art in ("R0", "R1", "R2"):
            qs, rgs, ant, vk = [], [], [], 0
            for st in starts:
                r, v = d1(mix, art, st)
                vk += v
                qs.append(r["wert"].iloc[-1] / m0[st]["wert"].iloc[-1])
                rgs.append(max_rueckgang(r["wert"], r["ein"]))
                me = r.index[r.index.is_month_end & (r.index >= st + pd.DateOffset(years=1))]
                ant.append(float((r.loc[me, "wert"] >= m0[st].loc[me, "wert"]).mean()) if len(me) else np.nan)
            med, rg = float(np.median(qs)), float(np.median(rgs))
            erg.append((mix, art, med, rg))
            print("  %s %s   | %s | %.2f   | %+.0f %% (%+.0f %%)         | %3.0f %%             | %d" % (
                mix, art, "  ".join("%.2f" % x for x in qs), med, 100 * rg, 100 * m0_rg, 100 * np.nanmean(ant), vk))
    zul = [e for e in erg if e[3] >= m0_rg - 0.05]
    rang = {"R0": 0, "R1": 1, "R2": 2}
    if zul:
        best = sorted(zul, key=lambda e: (-round(e[2], 2), rang[e[1]]))[0]
        print("\n  EMPFEHLUNG nach der Regel (§12.2): %s %s (Median %.2f x M0, Rueckgang %+.0f %%)" % (best[0], best[1], best[2], 100 * best[3]))
    else:
        best = None
        print("\n  EMPFEHLUNG nach der Regel: KEINE Mischung haelt den Rueckgang innerhalb von 5 Pp zu M0")
    nicht = [e for e in erg if e[3] < m0_rg - 0.05]
    print("  ausgeschlossen (Rueckgang mehr als 5 Pp schlechter als M0): " + (", ".join("%s %s (%+.0f %%)" % (e[0], e[1], 100 * e[3]) for e in nicht) or "keine"))
    return best


# ============================================================================ D2-M
FAELLE = {"b1": (0.10, (0.80, 0.90, 0.95), "alles"), "b2": (0.10, (0.80, 0.90, 0.95), "drittel"), "b3": (0.20, (0.80, 0.90, 0.95), "drittel"),
          "b4": (0.20, (0.80,), "drittel"), "d1": (0.10, (0.80, 0.90, 0.95), "entnahme"), "d2": (0.20, (0.80, 0.90, 0.95), "entnahme")}


def d2(sym, start, fall, ende=None, mix=None):
    """fall None = H0. mix: dict Gewichte -> Teilverkauf auf dem ganzen Mix (D1 x D2, Auskunft)."""
    syms = list(mix) if mix else [sym]
    ende = ende or min(KURS[s].index[-1] for s in syms)
    idx = pd.date_range(start, ende)
    zt = set(zuflusstage(idx, start))
    qv = Q.shift(1)
    anteil, stufen, rk = FAELLE[fall] if fall else (0, (), None)
    scharf = set(stufen)
    st = {s: 0.0 for s in syms}
    kost = {s: 0.0 for s in syms}                              # Einstand fuer realisierte Gewinne
    geld = entn = ein = 0.0
    zyklus = None                                              # Rueckkauf-Zyklus: dict(basis, t1, gekauft)
    verk = rueck = 0
    gewinne, zonen_ende, rows = [], [], []
    in_zone = False
    for t in idx:
        p = {s: KURS[s][t] for s in syms}
        q = qv.get(t, np.nan)
        if t in zt:
            ein += 1.0
            for s in syms:
                w = mix[s] if mix else 1.0
                st[s] += w / p[s]; kost[s] += w
        if fall and not np.isnan(q):
            for s_ in sorted(scharf):
                if q >= s_:
                    scharf.discard(s_)
                    for s in syms:
                        m = st[s] * anteil
                        erl = m * p[s]
                        ein_k = kost[s] * anteil
                        gewinne.append((t, s, s_, erl, erl - ein_k))
                        st[s] -= m; kost[s] -= ein_k
                        if rk == "entnahme":
                            entn += erl
                        else:
                            geld += erl
                    verk += 1
            if q <= 0.20:
                scharf = set(stufen)
                in_zone = True
                if rk == "alles" and geld > 1e-12:
                    _kaufe(st, kost, p, geld, mix, syms); geld = 0.0; rueck += 1
                elif rk == "drittel" and geld > 1e-12:
                    if zyklus is None:
                        zyklus = {"basis": geld, "t1": t, "stufe": set()}
                    for grenze in (0.20, 0.10, 0.05):
                        if q <= grenze and grenze not in zyklus["stufe"]:
                            zyklus["stufe"].add(grenze)
                            b = zyklus["basis"] / 3 if grenze != 0.05 else geld
                            b = min(b, geld)
                            _kaufe(st, kost, p, b, mix, syms); geld -= b; rueck += 1
            elif in_zone and q > 0.20:
                in_zone = False
                zonen_ende.append(t)
            if rk == "drittel" and zyklus is not None and geld > 1e-12 and (t - zyklus["t1"]).days >= 365:
                _kaufe(st, kost, p, geld, mix, syms); geld = 0.0; rueck += 1
            if zyklus is not None and geld <= 1e-12:
                zyklus = None
        wert = sum(st[s] * p[s] for s in syms)
        rows.append((t, wert, geld, entn, ein, sum(st.values()) if not mix else wert))
    r = pd.DataFrame(rows, columns=["t", "wert", "geld", "entn", "ein", "stueck"]).set_index("t")
    r.attrs.update(verk=verk, rueck=rueck, gewinne=gewinne, zonen_ende=zonen_ende, stueck=dict(st))
    return r


def _kaufe(st, kost, p, betrag, mix, syms):
    for s in syms:
        w = mix[s] if mix else 1.0
        st[s] += betrag * w / p[s]; kost[s] += betrag * w


def lauf_d2(best_mix):
    starts = {"BTC": ["2015-01-01", "2017-01-01", "2019-01-01", "2021-01-01", "2023-01-01", "2024-01-11"],
              "ETH": ["2017-01-01", "2019-01-01", "2021-01-01", "2023-01-01", "2024-01-11"],
              "SOL": ["2020-09-01", "2021-01-01", "2023-01-01", "2024-01-11"]}
    print("\n" + "=" * 30, "D2-M Teilverkauf (b) und Entnahme (d) nach dem BTC-Klima", "=" * 30)
    stimmig = {}
    for sym in ("BTC", "ETH", "SOL"):
        print("\n%s (Ende %s)" % (sym, KURS[sym].index[-1].date()))
        print("  Fall | (b) Stueck / H0 je Start %s | Verm. / H0 | Rueckgang (H0) | Geld am Ende | Verk./Rueckk." % "/".join(x[:7] for x in starts[sym]))
        h0 = {s: d2(sym, pd.Timestamp(s), None) for s in starts[sym]}
        for fall in ("b1", "b2", "b3", "b4"):
            st_q, w_q, rg, rg0, gl, vk, rk = [], [], [], [], [], 0, 0
            for s in starts[sym]:
                r = d2(sym, pd.Timestamp(s), fall)
                h = h0[s]
                st_q.append(r.attrs["stueck"][sym] / h.attrs["stueck"][sym])
                w_q.append((r["wert"].iloc[-1] + r["geld"].iloc[-1]) / h["wert"].iloc[-1])
                rg.append(max_rueckgang(r["wert"] + r["geld"], r["ein"])); rg0.append(max_rueckgang(h["wert"], h["ein"]))
                gl.append(r["geld"].iloc[-1] / r["ein"].iloc[-1]); vk += r.attrs["verk"]; rk += r.attrs["rueck"]
            ok_ = sum(x > 1 for x in st_q) >= 2 / 3 * len(st_q) and st_q[-1] >= 0.95
            stimmig[(sym, fall)] = ok_
            print("  %s   | %s | %s | %+.0f %% (%+.0f %%) | %3.0f %% | %d/%d" % (
                fall, " ".join("%.3f" % x for x in st_q), " ".join("%.2f" % x for x in w_q), 100 * np.median(rg), 100 * np.median(rg0),
                100 * np.median(gl), vk, rk))
        for fall in ("d1", "d2"):
            rel, ent = [], []
            for s in starts[sym]:
                r, h = d2(sym, pd.Timestamp(s), fall), h0[s]
                rel.append((r["wert"].iloc[-1] + r["entn"].iloc[-1]) / h["wert"].iloc[-1])
                ent.append(r["entn"].iloc[-1] / r["ein"].iloc[-1])
            print("  %s   | (d) Rest + Entnahme / H0: %s | entnommen in %% des Eingezahlten: %s" % (
                fall, " ".join("%.2f" % x for x in rel), " ".join("%.0f %%" % (100 * x) for x in ent)))
        # je Zyklus: Stueck / H0 am Ende jeder Zone (b2), Start = erster Start
        r = d2(sym, pd.Timestamp(starts[sym][0]), "b2"); h = h0[starts[sym][0]]
        ze = [t for t in r.attrs["zonen_ende"] if t in h.index]
        if ze:
            print("  b2 je Zyklus (Start %s), Stueck / H0 am Ende jeder Zone: %s" % (starts[sym][0][:7], " · ".join(
                "%s %.3f" % (t.date(), r.loc[t, "stueck"] / h.loc[t, "stueck"]) for t in ze)))
        gw = r.attrs["gewinne"]
        if gw:
            print("  Auskunft realisierte Gewinne b2 (Start %s, USD je eingezahlte Einheit): %s" % (starts[sym][0][:7], " · ".join(
                "%s Stufe %.2f %+.2f" % (t.date(), s_, gwn) for t, _s, s_, _e, gwn in gw[:8])))
    print("\nSTIMMIG (b) nach §12.3 (Stueck > H0 bei BTC UND ETH in >= 2/3 der Starts, Start 2024 >= 0,95; SOL Auskunft):")
    for fall in ("b1", "b2", "b3", "b4"):
        print("  %s: BTC %s, ETH %s, SOL (Auskunft) %s -> %s" % (fall, *("ja" if stimmig[(s, fall)] else "nein" for s in ("BTC", "ETH", "SOL")),
                                                                "STIMMIG" if stimmig[("BTC", fall)] and stimmig[("ETH", fall)] else "nicht stimmig"))
    if best_mix:
        w = ziel(best_mix[0], pd.Timestamp("2024-01-01")) if best_mix[0] != "V4" else ziel("V4", pd.Timestamp("2024-01-01"))
        st0 = pd.Timestamp("2020-10-01")
        h = d2(None, st0, None, ENDE_D1, w); r = d2(None, st0, "b2", ENDE_D1, w)
        print("\nAUSKUNFT D1 x D2: Mischung %s (Gewichte fest %s) mit b2, Start 2020-10: Vermoegen / H0 %.3f" % (
            best_mix[0], {k: round(v, 2) for k, v in w.items()}, (r["wert"].iloc[-1] + r["geld"].iloc[-1]) / h["wert"].iloc[-1]))


if __name__ == "__main__":
    print("Spot D1-M / D2-M (Voranalyse_Spot §12) - Daten: BTC/ETH CoinMetrics bis %s, SOL messdaten bis %s, Klima q aus BTC" % (
        pb.index[-1].date(), ps.index[-1].date()))
    b = lauf_d1()
    lauf_d2(b)
