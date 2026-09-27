# -*- coding: utf-8 -*-
"""E2f: die RICHTUNG - neue Richtungsdaten und die alten Traeger im Pflichtablauf.

**27.09.2026.** Nutzervorgaben: *"die Richtung muss geloest werden"*, *"sauber
und langsam, bis wir die Grundlagen haben"*, *"in jedem Regime
funktionieren - wenn nicht, dann reden wir"*. Die Richtungsdaten (Befund
2.661) sind geladen und geprueft; die alten Traeger (funding Vortag,
oi_aenderung, konten_verh, momentum_kurz, rsi) stehen bisher nur auf
Stunden mit tagestreuer Nullwelt (2.648, 2.663) - sie laufen hier im
selben Pflichtablauf mit.

VORAB FESTGELEGT (vor dem ersten Lauf, nicht nachgestellt)
    Zeitraum     2023-01 bis 2026-08 fuer ALLE Kandidaten (gemeinsames
                 Fenster - die Richtungsdaten beginnen 2023-01)
    Kandidaten   NEU      kaeufer_1h, kaeufer_6h, kaeufer_24h (Anteil des
                          vom Kaeufer ausgeloesten Volumens), kaeufer_rel
                          (6 h minus 168 h - gegen die eigene Gewohnheit),
                          premium_jetzt, premium_24h (Mittel)
                 ALT      funding_vortag, oi_aenderung, konten_verh,
                          momentum_kurz, rsi
                 je Perzentil 1 / 5 / 95 / 99 - 44 Auswahlen
    KONTEXT      btcdom_24, btcdom_120 (Aenderung des BTCDOMUSDT-Index) -
                 MARKTWEIT, zur selben Stunde fuer alle Assets gleich, daher
                 KEIN Beitrag (stehende Nutzervorgabe); dazu die Sperre aus
                 2.601 (BTC 24 h gestiegen UND Dominanz 24 h gestiegen)
    Richtung     zwei Zielgroessen, beide regelfrei:
        q5    P(+5 % vor -5 %) / (P(+5 % zuerst) + P(-5 % zuerst)), 24 h
        q15   P(+15 % in 12 h) / (P(+15 % in 12 h) + P(-15 % in 12 h)) -
              die Form von 2.651 / 2.663
                 Wert: Dq = q der Auswahl minus q desselben Assets im
                 selben Monat (streng). Kein geeichter Spiegelwert noetig -
                 die Nullwelt eicht Dq selbst.
    Episoden     je Asset hoechstens ein Anker in 24 h
    Nullwelt     symboltreu im selben Monat, 40 Ziehungen; Grenze
                 Bestes-von-44 je Zielgroesse, zweiseitig, 90. Perzentil
    Stabilitaet  je Kalenderjahr (mind. 30 Episoden), Weglassprobe je Jahr,
                 je Asset (mind. 10 Episoden) Anteil mit gleichem Vorzeichen
    Vorwaerts    Pruefmonate 2024-01 bis 2026-08, Schwellen NUR aus den 12
                 Monaten davor; je BTC-Monatslage
    Gegenproben  P2 Merkmale 1 h aelter (muss halten), P3 1 h aus der
                 Zukunft (Vorgriff sichtbar?), P4 Ausgaenge innerhalb Symbol
                 und Monat vertauscht (muss ins Band)
    GEGENPROBE P5 (--zufall): statt der 11 Kandidaten zehn ZUFALLSmerkmale
                 (Rauschen je Symbol, gleitend geglaettet ueber 1 / 6 / 24 /
                 72 / 168 Anker, je zwei Saaten) durch DIESELBEN Kriterien -
                 wie viele *tragen*? Das ist die Fehlalarmquote der ganzen
                 Anlage einschliesslich Vorwaerts und Gegenproben
    TRAEGT       jenseits der Grenze, Jahre >= n-1, Weglass alle, Assets
                 >= 60 %, vorwaerts >= 75 % der Monate (mind. 12) und in
                 JEDER BTC-Lage dasselbe Vorzeichen, P2 dasselbe Vorzeichen
                 mit >= halber Groesse, P4 im Band. Positiv = RICHTUNG +,
                 negativ = SPERRE

NUR LESEND (`mode=ro`). Kein Stop, kein Trailing, keine Gebuehren (Regel 2).
Ebene B (2.641).
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402

RICHTUNG_DB = os.path.join(E2.HIER, "data", "richtung_historie.db")
NEU = ("kaeufer_1h", "kaeufer_6h", "kaeufer_24h", "kaeufer_rel",
       "premium_jetzt", "premium_24h")
ALT = ("funding_vortag", "oi_aenderung", "konten_verh", "momentum_kurz",
       "rsi")
KANDIDATEN = NEU + ALT
KONTEXT = ("btcdom_24", "btcdom_120")
PERZ = (1, 5, 95, 99)
ZIELE = ("q5", "q15")
ABSTAND_H = 24
ZIEHUNGEN, SAAT = 40, 20261003
MIN_ASSET = 10
BASIS = datetime(2020, 1, 1)
AB = int((datetime(2023, 1, 1) - BASIS).total_seconds() // 3600)
BIS = int((datetime(2026, 9, 1) - BASIS).total_seconds() // 3600)
PRUEF_AB = 2024 * 12 + 0
PRUEF_BIS = 2026 * 12 + 7


def _stunden(texte):
    """'YYYY-MM-DD HH:MM' -> Stunden seit 2020-01-01."""
    t = np.array([x.replace(" ", "T") for x in texte], "datetime64[h]")
    return (t - np.datetime64("2020-01-01T00", "h")).astype(np.int64)


def _summe(x, k):
    """Gleitende Summe ueber k Stunden, NaN sobald eine Stunde fehlt."""
    n = len(x)
    c = np.concatenate([[0.0], np.cumsum(np.nan_to_num(x))])
    f = np.concatenate([[0], np.cumsum(~np.isfinite(x))])
    aus = np.full(n, np.nan)
    if n >= k:
        s = c[k:] - c[:-k]
        leer = (f[k:] - f[:-k]) > 0
        aus[k - 1:] = np.where(leer, np.nan, s)
    return aus


def richtungsmerkmale(sym, cr):
    """-> (stunde0, dict Merkmal -> Array je Stunde ab stunde0) oder None."""
    fl = cr.execute("SELECT stunde, volumen, kauf_volumen FROM fluss "
                    "WHERE symbol=? ORDER BY stunde", (sym,)).fetchall()
    pr = cr.execute("SELECT stunde, close FROM premium WHERE symbol=? "
                    "ORDER BY stunde", (sym,)).fetchall()
    if not fl:
        return None
    hf = _stunden([r[0] for r in fl])
    hp = _stunden([r[0] for r in pr]) if pr else np.array([], np.int64)
    h0 = int(min(hf.min(), hp.min() if len(hp) else hf.min()))
    h1 = int(max(hf.max(), hp.max() if len(hp) else hf.max()))
    n = h1 - h0 + 1
    v = np.full(n, np.nan); kv = np.full(n, np.nan); pc = np.full(n, np.nan)
    v[hf - h0] = [r[1] if r[1] is not None else np.nan for r in fl]
    kv[hf - h0] = [r[2] if r[2] is not None else np.nan for r in fl]
    if len(hp):
        pc[hp - h0] = [r[1] if r[1] is not None else np.nan for r in pr]
    v = np.where(v > 0, v, np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        k1 = kv / v
        k6 = _summe(kv, 6) / _summe(v, 6)
        k24 = _summe(kv, 24) / _summe(v, 24)
        k168 = _summe(kv, 168) / _summe(v, 168)
    return h0, {"kaeufer_1h": k1, "kaeufer_6h": k6, "kaeufer_24h": k24,
                "kaeufer_rel": k6 - k168, "premium_jetzt": pc,
                "premium_24h": _summe(pc, 24) / 24.0}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 124)
    print("E2f - DIE RICHTUNG: neue Richtungsdaten und die alten Traeger im "
          "Pflichtablauf (2023-01 bis 2026-08)")
    print("=" * 124)
    D = E2.lade(hmax=72, erste=(("up15", 1.15, True), ("dn15", 0.85, False)))
    im = (D["STD"] >= AB) & (D["STD"] < BIS)
    SYM, STD, JAHR = D["SYM"][im], D["STD"][im], D["JAHR"][im]
    F = {m: D["F"][m][im].astype(np.float32) for m in ALT}
    Z24 = D["Z"][24]
    A5 = Z24["auf5"][im].astype(np.int8)
    B5 = Z24["ab5"][im].astype(np.int8)
    U15 = (D["T"]["up15"][im] <= 12).astype(np.int8)
    D15 = (D["T"]["dn15"][im] <= 12).astype(np.int8)
    syms = D["syms"]
    del D
    n = len(SYM)
    nsym = int(SYM.max()) + 1
    MON = monat_von(STD)
    rng = np.random.default_rng(SAAT)

    # ── Richtungsmerkmale an die Anker (kausal: Wert der Stunde ist zum
    # Schlusskurs des Ankers HH:59 bekannt)
    cr = sqlite3.connect("file:%s?mode=ro" % RICHTUNG_DB, uri=True)
    for m in NEU:
        F[m] = np.full(n, np.nan, np.float32)
    for si in np.unique(SYM):
        r = richtungsmerkmale(syms[si], cr)
        if r is None:
            continue
        h0, M = r
        mk = SYM == si
        pos = STD[mk] - h0
        ok = (pos >= 0) & (pos < len(M["kaeufer_1h"]))
        for m in NEU:
            w = np.full(mk.sum(), np.nan, np.float32)
            w[ok] = M[m][pos[ok]]
            F[m][mk] = w
    dom = cr.execute("SELECT stunde, close FROM btcdom ORDER BY stunde").fetchall()
    cr.close()
    hd = _stunden([x[0] for x in dom])
    dc = np.full(hd.max() - hd.min() + 1, np.nan)
    dc[hd - hd.min()] = [x[1] for x in dom]
    KX = {}
    for name, k in (("btcdom_24", 24), ("btcdom_120", 120)):
        with np.errstate(divide="ignore", invalid="ignore"):
            vor = np.concatenate([np.full(k, np.nan), dc[:-k]])
            ae = dc / vor - 1.0
        p = STD - hd.min()
        ok = (p >= 0) & (p < len(ae))
        KX[name] = np.full(n, np.nan)
        KX[name][ok] = ae[p[ok]]
    from messe_e2c_grosse_bewegungen import btc_merkmale
    BM = btc_merkmale()
    btc24 = np.array([BM.get(int(s), (np.nan,))[0] for s in STD])

    print("  %d Anker · %d Symbole · %d Monate" % (n, len(np.unique(SYM)),
                                                  len(np.unique(MON))))
    kandidaten = KANDIDATEN
    if "--zufall" in sys.argv:
        print("  ⭐ GEGENPROBE P5: ZUFALLSmerkmale statt der Kandidaten")
        kandidaten = []
        o = np.lexsort((STD, SYM))
        grenzen = np.flatnonzero(np.diff(SYM[o])) + 1
        for glatt in (1, 6, 24, 72, 168):
            for saat in (1, 2):
                r = np.random.default_rng(1000 * glatt + saat)
                x = r.standard_normal(n)
                v = np.empty(n)
                for teil in np.split(o, grenzen):
                    c = np.concatenate([[0.0], np.cumsum(x[teil])])
                    k = np.arange(1, len(teil) + 1)
                    lo = np.maximum(0, k - glatt)
                    v[teil] = (c[k] - c[lo]) / (k - lo)
                name = "zufall_g%d_s%d" % (glatt, saat)
                F[name] = v.astype(np.float32)
                kandidaten.append(name)
    print("  Abdeckung: " + " · ".join("%s %.1f%%" % (
        m, 100 * np.mean(np.isfinite(F[m]))) for m in kandidaten))

    # ── Bezug: eigenes Asset im selben Monat
    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    usm, sm_i = np.unique(SM, return_inverse=True)
    sm_anz = np.maximum(np.bincount(sm_i), 1)

    def smb(x):
        return np.bincount(sm_i, weights=x.astype(float)) / sm_anz

    BASE = {"a5": smb(A5), "b5": smb(B5), "u15": smb(U15), "d15": smb(D15)}
    PAAR = {"q5": ("a5", "b5", A5, B5), "q15": ("u15", "d15", U15, D15)}

    def dq(e, z, perm=None):
        if e.sum() == 0:
            return np.nan
        ka, kb, xa, xb = PAAR[z]
        ia = xa if perm is None else xa[perm]
        ib = xb if perm is None else xb[perm]
        a, b = ia[e].mean(), ib[e].mean()
        a0 = BASE[ka][sm_i[e]].mean(); b0 = BASE[kb][sm_i[e]].mean()
        q = a / (a + b) if a + b > 0 else np.nan
        q0 = a0 / (a0 + b0) if a0 + b0 > 0 else np.nan
        return q - q0

    def qabs(e, z):
        ka, kb, xa, xb = PAAR[z]
        a, b = xa[e].mean(), xb[e].mean()
        return a / (a + b) if a + b > 0 else np.nan

    ordnung = np.lexsort((STD, SYM))

    def entzerren(maske):
        idx = ordnung[maske[ordnung]]
        aus = np.zeros(n, bool)
        ls, lt = -1, -10 ** 9
        for i in idx:
            if SYM[i] != ls or STD[i] - lt >= ABSTAND_H:
                aus[i] = True
                ls, lt = SYM[i], STD[i]
        return aus

    o_sm = np.argsort(sm_i, kind="stable")
    sm_start = np.searchsorted(sm_i[o_sm], np.arange(len(usm)), "left")

    def ziehe(e):
        s = sm_i[e]
        r = (rng.random(len(s)) * sm_anz[s]).astype(np.int64)
        return o_sm[sm_start[s] + r]

    def auswahl(v, p, sw=None):
        ok = np.isfinite(v)
        if sw is None:
            sw = np.percentile(v[ok], p)
        return ok & ((v <= sw) if p < 50 else (v >= sw)), float(sw)

    AUS = []
    for m in kandidaten:
        for p in PERZ:
            mk, sw = auswahl(F[m], p)
            AUS.append((m, p, sw, entzerren(mk)))

    # Nullwelt
    null = {z: np.zeros((ZIEHUNGEN, len(AUS))) for z in ZIELE}
    for zi in range(ZIEHUNGEN):
        for ai, (_m, _p, _sw, e) in enumerate(AUS):
            idx = ziehe(e)
            ee = np.zeros(n, bool); ee[idx] = True
            # Mehrfachziehungen desselben Ankers zaehlen einfach - bei
            # Episoden selten; der Fehler macht das Band eher breiter
            for z in ZIELE:
                null[z][zi, ai] = dq(ee, z)
    band = {}
    for z in ZIELE:
        mu = np.nanmean(null[z], axis=0)
        sd = np.maximum(np.nanstd(null[z], axis=0, ddof=1), 1e-12)
        band[z] = (mu, sd, float(np.nanpercentile(
            np.nanmax(np.abs((null[z] - mu) / sd), axis=1), 90)))

    def jenseits(z, ai, w):
        mu, sd, g = band[z]
        return bool(np.isfinite(w) and abs((w - mu[ai]) / sd[ai]) > g)

    # Gegenproben-Zeiger
    vor1 = np.full(n, -1, np.int64)
    gl = (SYM[ordnung][1:] == SYM[ordnung][:-1]) & (np.diff(STD[ordnung]) == 1)
    vor1[ordnung[1:][gl]] = ordnung[:-1][gl]
    nach1 = np.full(n, -1, np.int64)
    nach1[ordnung[:-1][gl]] = ordnung[1:][gl]

    def verschoben(zeiger, m):
        v = np.full(n, np.nan)
        ok = zeiger >= 0
        v[ok] = F[m][zeiger[ok]]
        return v

    perm = np.arange(n)
    for s0 in range(len(usm)):
        a = o_sm[sm_start[s0]:sm_start[s0] + sm_anz[s0]]
        perm[a] = rng.permutation(a)

    # BTC-Monatslage
    cs = sqlite3.connect("file:%s?mode=ro" % E2.STUNDEN_DB, uri=True)
    rows = cs.execute("SELECT stunde, close FROM stundenkurse WHERE "
                      "symbol='BTC' ORDER BY stunde").fetchall()
    cs.close()
    bstd = _stunden([r[0] for r in rows])
    bcc = np.array([r[1] for r in rows], float)
    bmon = monat_von(bstd)
    btc_lage = {}
    for mm in np.unique(bmon):
        x = bcc[bmon == mm]
        rr = x[-1] / x[0] - 1.0
        btc_lage[int(mm)] = ("steigend" if rr > 0.05 else
                             "fallend" if rr < -0.05 else "seitwaerts")
    monate = [mm for mm in range(PRUEF_AB, PRUEF_BIS + 1) if (MON == mm).any()]

    def vorwaerts(v, p, z):
        aus = {}
        for mm in monate:
            kal = (MON >= mm - 12) & (MON < mm) & np.isfinite(v)
            if kal.sum() < 1000:
                continue
            sw = np.percentile(v[kal], p)
            e = entzerren((MON == mm) & np.isfinite(v)
                          & ((v <= sw) if p < 50 else (v >= sw)))
            if e.sum() >= 20:
                aus[mm] = dq(e, z)
        return aus

    def stabil(e, z, vz):
        jahre = [j for j in np.unique(JAHR[e]) if (e & (JAHR == j)).sum() >= 30]
        j_ok = sum(int(vz * dq(e & (JAHR == j), z) > 0) for j in jahre)
        w_ok = sum(int(vz * dq(e & (JAHR != j), z) > 0) for j in jahre)
        ka, kb, xa, xb = PAAR[z]
        d = (xa[e] - xb[e]) - (BASE[ka][sm_i[e]] - BASE[kb][sm_i[e]])
        je = np.bincount(SYM[e], weights=d, minlength=nsym)
        jn = np.bincount(SYM[e], minlength=nsym)
        g = jn >= MIN_ASSET
        a = float(np.mean(vz * je[g] > 0)) if g.any() else np.nan
        return j_ok, len(jahre), w_ok, a

    # ══ AUSGABE ════════════════════════════════════════════════════
    for z in ZIELE:
        print()
        print("=" * 124)
        print("ZIELGROESSE %s - Dq gegen das eigene Asset im selben Monat, "
              "Episoden · Grenze Bestes-von-%d z %.2f"
              % (z, len(AUS), band[z][2]))
        print("  %-15s %4s %9s %6s | %6s %7s | %5s %5s %5s | %7s %7s %7s | %6s %s"
              % ("Merkmal", "Perz", "Schwelle", "Epis.", "q abs", "Dq",
                 "Jahre", "Wegl", "Asset", "P2 1h-", "P3 1h+", "P4 tau",
                 "vorw.", "Urteil"))
        treffer = []
        for ai, (m, p, sw, e) in enumerate(AUS):
            w = dq(e, z)
            st = jenseits(z, ai, w)
            vz = 1.0 if w > 0 else -1.0
            j_ok, j_n, w_ok, a = stabil(e, z, vz)
            e2 = entzerren(auswahl(verschoben(vor1, m), p)[0])
            e3 = entzerren(auswahl(verschoben(nach1, m), p)[0])
            p2, p3 = dq(e2, z), dq(e3, z)
            p4 = dq(e, z, perm)
            vw = vorwaerts(F[m], p, z)
            vm = [x for x in vw.values() if np.isfinite(x)]
            vm_ok = sum(int(vz * x > 0) for x in vm)
            lagen = {}
            for mm, x in vw.items():
                if np.isfinite(x):
                    lagen.setdefault(btc_lage.get(mm, "?"), []).append(x)
            lage_ok = bool(lagen) and all(vz * np.mean(x) > 0
                                          for x in lagen.values())
            traegt = (st and j_n >= 3 and j_ok >= j_n - 1 and w_ok == j_n
                      and a >= 0.6 and len(vm) >= 12
                      and vm_ok >= 0.75 * len(vm) and lage_ok
                      and vz * p2 > 0 and abs(p2) >= 0.5 * abs(w)
                      and not jenseits(z, ai, p4))
            urteil = (("✔ RICHTUNG +" if vz > 0 else "⛔ SPERRE")
                      if traegt else "· nein")
            if traegt:
                treffer.append((m, p, lagen))
            print("  %-15s P%-3d %9.4f %6d | %6.3f %+6.3f%s | %2d/%-2d %2d/%-2d %4.0f%% | %+7.3f %+7.3f %+7.3f | %2d/%-3d %s"
                  % (m, p, sw, int(e.sum()), qabs(e, z), w,
                     "*" if st else " ", j_ok, j_n, w_ok, j_n,
                     100 * a if np.isfinite(a) else float("nan"),
                     p2, p3, p4, vm_ok, len(vm), urteil))
        print()
        print("  Grundlage (alle Anker): q abs %.3f" % qabs(np.ones(n, bool), z))
        if treffer:
            print("  VORWAERTS JE BTC-LAGE fuer die tragenden:")
            for m, p, lagen in treffer:
                print("    %-15s P%-3d %s" % (m, p, " · ".join(
                    "%s %+.3f (%d)" % (k, np.mean(x), len(x))
                    for k, x in sorted(lagen.items()))))

    if "--zufall" in sys.argv:
        print()
        print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
        return 0
    # ══ KONTEXT: Dominanz (marktweit, kein Beitrag) ═══════════════
    print()
    print("=" * 124)
    print("KONTEXT - BTC-DOMINANZ-INDEX (marktweit, KEIN Beitrag): Dq je "
          "Lage, Episoden, gegen das eigene Asset im Monat")
    alle = np.isfinite(KX["btcdom_24"]) & np.isfinite(btc24)
    lagen_k = (
        ("BTC 24h > 0 UND Dominanz 24h > 0 (2.601-Sperre)",
         alle & (btc24 > 0) & (KX["btcdom_24"] > 0)),
        ("BTC 24h > 0 UND Dominanz 24h < 0", alle & (btc24 > 0) & (KX["btcdom_24"] < 0)),
        ("BTC 24h < 0 UND Dominanz 24h > 0", alle & (btc24 < 0) & (KX["btcdom_24"] > 0)),
        ("BTC 24h < 0 UND Dominanz 24h < 0", alle & (btc24 < 0) & (KX["btcdom_24"] < 0)),
    )
    for name, mk in lagen_k:
        e = entzerren(mk)
        werte = []
        for z in ZIELE:
            w = dq(e, z)
            nz = []
            for _ in range(ZIEHUNGEN):
                ee = np.zeros(n, bool); ee[ziehe(e)] = True
                nz.append(dq(ee, z))
            nz = np.array(nz)
            zz = (w - np.nanmean(nz)) / max(np.nanstd(nz, ddof=1), 1e-12)
            jahre = [j for j in np.unique(JAHR[e]) if (e & (JAHR == j)).sum() >= 30]
            jj = sum(int(np.sign(dq(e & (JAHR == j), z)) == np.sign(w)) for j in jahre)
            werte.append("%s Dq %+.3f (z %+.1f, Jahre %d/%d)" % (z, w, zz, jj, len(jahre)))
        print("  %-48s %7d Epis. | %s" % (name, int(e.sum()), " | ".join(werte)))
    print("  ⚠️ Kontext-z ist ein EINZELtest je Zeile (4 Zeilen x 2 Ziele) - "
          "kein Bestes-von-N; eine Sperre daraus braucht den Pflichtablauf")
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
