# -*- coding: utf-8 -*-
"""Die A-Faktoren: gibt es eine Lage, die `E[R]` ueber null hebt?

**26.09.2026**, Nutzerauftrag: *"wir brauchen den positiven Beitrag"*.

Dies sind die Merkmale, die seit dem 25.09. im Bauplan stehen und nie
gebaut wurden. Nutzervorgabe zur fachlichen Anordnung:

    *"1. Hebel Einstieg - muss eine Lage sein: steigender Kurs,
    TRENDUMKEHR, etc.  2. Hebel und Hoehe: kein hohes Risiko, nicht
    UEBERKAUFT & eine grosse Bewegung im kurzen Timeframe zu erwarten."*

═══════════════════════════════════════════════════════════════════════
 DER STAND, GEGEN DEN GEMESSEN WIRD
═══════════════════════════════════════════════════════════════════════

    2.597   `E[R]` BRUTTO ist in 0 von 60 Zellen positiv, bester Wert
            -0,0034. Die Niveaufrage ist offen.
    2.602   Die Sperre *BTC steigt UND Dominanz steigt* hebt `E[R]` von
            -0,00275 auf -0,00155 (H6). Belegt gegen die Suche (Faktor 6)
            und out-of-sample (B6).

⭐ **Deshalb wird HIER AUF DER GESPERRTEN MENGE gemessen.** Sie ist die
Menge, auf der ein Betrieb tatsaechlich handeln wuerde, und dort fehlen
nur noch **0,00155** bis null. Auf der vollen Menge waeren es 0,00275.

═══════════════════════════════════════════════════════════════════════
 DIE SIEBEN A-FAKTOREN - alle je Asset, alle streng kausal
═══════════════════════════════════════════════════════════════════════

    rsi_aenderung      RSI(t) - RSI(t-6)          steigt er?
    rsi_umkehr         (50 - RSI) x (RSI - RSI_6) ⭐ TIEF *UND* STEIGEND -
                       genau die *Trendumkehr* der Nutzervorgabe. Das
                       Produkt ist hier zulaessig, weil BEIDE Faktoren je
                       Asset verschieden sind (anders als 2.601, wo ein
                       Marktzustand im Produkt stand)
    ema_lage           close / EMA48 - 1          steigender Kurs?
    ema_steigung       EMA48 / EMA48(t-24) - 1    Trendrichtung
    ema_abstand_atr    (close - EMA48) / ATR      ⭐ UEBERDEHNT? Der bessere
                       *ueberkauft*-Massstab als RSI, weil in ATR gemessen
    bandenge           Streuung(20) / EMA20       ⭐ SQUEEZE - *grosse
                       Bewegung im kurzen Timeframe zu erwarten*
    trendstruktur      sign(EMA12-EMA48) + sign(EMA48-EMA200)
                       mehrere Zeitebenen gleichgerichtet?

**Kontrollen:** `zufall` (Rauschen) und `vola` (ist alles nur
Volatilitaet? - die Lehre aus 2.594 und 2.601)

═══════════════════════════════════════════════════════════════════════
 DIE STANDARDS - diesmal von Anfang an, nicht nachgeruestet
═══════════════════════════════════════════════════════════════════════

⚠️⚠️ Bei Vorabfestlegung 15 UND 18 waren Spiegelprobe und Trennschaerfe
zugesagt und fehlten im Werkzeug. Beide sind hier eingebaut, bevor der
erste Lauf startet.

    Nullband        Zufallsfuenftel in der Stunde, 40 Ziehungen, 90. Perz
    Spiegelprobe    echte SHORT-Geometrie ueber `ausgaenge(runter=True)` -
                    blosses Vorzeichendrehen ist tautologisch (2.601)
    Trennschaerfe   Anteil echter Ordnung in Zufall, Fundquote je Stufe
    B6              erste gegen zweite Haelfte
    ⭐ brutto       die Zielgroesse ist `E[R]` BRUTTO - die NIVEAUfrage.
                    Netto wird mitgefuehrt, entscheidet aber nicht.

⚠️ NUR LESEN.  python messe_a_faktoren.py [--symbole N] [--ohne-sperre]
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import (                    # noqa: E402
    lade_kurse, lade_funding, merkmale_je_symbol, _rsi, _schiebe)
from messe_hebel_dimension import _lade_terminmarkt             # noqa: E402
from messe_hebel_geometrie_neutral import (                     # noqa: E402
    atr_tag_relativ, ausgaenge, STOP_MIN, STOP_MAX)
from messe_q_beide_seiten import (                              # noqa: E402
    fuenftel_je_stunde, MIND_JE_FUENFTEL)

LEITWERT = os.path.join("data", "btc_leitwert.db")
K_ATR = 1.0
ZELLEN = ((1.5, 6), (1.5, 24), (2.0, 6))
RUECK_H = 6
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
STAERKEN = (0.0, 0.25, 0.50, 1.0)
N_POSITIV = 5
SAAT = 20260926


def _ema(x, p):
    """EMA - kausal, mit NaN-Vorlauf."""
    a = 2.0 / (p + 1.0)
    aus = np.full(len(x), np.nan)
    if len(x) <= p:
        return aus
    s = float(np.mean(x[:p]))
    aus[p - 1] = s
    for i in range(p, len(x)):
        s = a * x[i] + (1 - a) * s
        aus[i] = s
    return aus


def a_faktoren(close, atr):
    """Die sieben A-Faktoren. ⚠️ JEDER WERT NUR AUS STUNDEN <= t."""
    n = len(close)
    e12, e48, e200 = _ema(close, 12), _ema(close, 48), _ema(close, 200)
    e20 = _ema(close, 20)
    r = _rsi(close)
    m = {}
    m["rsi_aenderung"] = r - _schiebe(r, 6)
    # ⭐ tief UND steigend: beide Faktoren sind je Asset verschieden,
    # anders als der Marktzustand im Produkt von 2.601
    m["rsi_umkehr"] = (50.0 - r) * (r - _schiebe(r, 6))
    with np.errstate(divide="ignore", invalid="ignore"):
        m["ema_lage"] = close / e48 - 1.0
        m["ema_steigung"] = e48 / _schiebe(e48, 24) - 1.0
        m["ema_abstand_atr"] = (close - e48) / np.maximum(atr * close, 1e-12)
        # Streuung der letzten 20 Stunden, kausal
        k = np.ones(20) / 20.0
        mu = np.convolve(close, k, mode="full")[:n]
        mu2 = np.convolve(close ** 2, k, mode="full")[:n]
        sd = np.sqrt(np.maximum(mu2 - mu ** 2, 0.0))
        sd[:20] = np.nan
        m["bandenge"] = sd / np.maximum(e20, 1e-12)
        m["trendstruktur"] = (np.sign(e12 - e48) + np.sign(e48 - e200))
    return m


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    ohne_sperre = "--ohne-sperre" in sys.argv

    print("=" * 100)
    print("DIE A-FAKTOREN: gibt es eine Lage, die E[R] ueber null hebt?")
    print("=" * 100)
    print("  ⭐ Zielgroesse: E[R] BRUTTO (die Niveaufrage, 2.597 § 5.3)")
    print("  ⭐ Gemessen %s der Sperre aus 2.602"
          % ("OHNE" if ohne_sperre else "AUF DER GESPERRTEN MENGE"))
    print("  ⚠️ Spiegelprobe und Trennschaerfe sind von Anfang an eingebaut")
    print("     - bei Vorabfestlegung 15 und 18 waren sie zugesagt und")
    print("       fehlten. Das soll sich nicht wiederholen.")

    kurse = lade_kurse(grenze)
    tm = _lade_terminmarkt(set(kurse))
    fund = lade_funding()
    print("  Terminmarkt: %d Symbole · Funding: %d Symbole"
          % (len(tm), len(fund)), flush=True)
    alle = set()
    for (stunden, *_r) in kurse.values():
        alle.update(stunden)
    stundenliste = sorted(alle)
    sid = {s: i for i, s in enumerate(stundenliste)}
    T = len(stundenliste)

    # ── die Sperre aus 2.602 ──────────────────────────────────────────
    c = sqlite3.connect("file:%s?mode=ro" % LEITWERT, uri=True)
    reihen = c.execute("SELECT stunde, close FROM leitwert WHERE symbol='BTC' "
                       "ORDER BY stunde").fetchall()
    c.close()
    btc = np.full(T, np.nan)
    for st, cl in reihen:
        i = sid.get(st)
        if i is not None:
            btc[i] = cl
    btc_r = np.full(T, np.nan)
    btc_r[RUECK_H:] = btc[RUECK_H:] / np.maximum(btc[:-RUECK_H], 1e-12) - 1.0
    alt_s, alt_n = np.zeros(T), np.zeros(T)
    for sym, (stunden, high, low, close, volumen) in kurse.items():
        if sym.upper() == "BTC":
            continue
        ii = np.array([sid[x] for x in stunden], np.int64)
        rr = np.full(len(close), np.nan)
        if len(close) > RUECK_H:
            rr[RUECK_H:] = (close[RUECK_H:]
                            / np.maximum(close[:-RUECK_H], 1e-12) - 1.0)
        g = np.isfinite(rr)
        np.add.at(alt_s, ii[g], rr[g]); np.add.at(alt_n, ii[g], 1.0)
    with np.errstate(invalid="ignore"):
        alt_m = np.where(alt_n >= 5, alt_s / np.maximum(alt_n, 1), np.nan)
    dom = btc_r - alt_m
    gesperrt_std = (btc_r > 0.005) & (dom > 0.0)
    print("  Sperre deckt %d von %d Stunden (%.1f %%)"
          % (int(np.nansum(gesperrt_std)), T,
             100.0 * np.nansum(gesperrt_std) / T), flush=True)

    rng = np.random.default_rng(SAAT)
    # ⭐⭐⭐ Die BEKANNTEN Traeger aus 2.594/2.597 laufen MIT - sie sind die
    # einzigen Merkmale, die je eine RICHTUNG gezeigt haben (Lift ~1,9 bis
    # zur strengsten Vola-Kontrolle, Spiegelprobe bestanden). Sie einzeln
    # wegzulassen und nur neue Faktoren zu messen, waere der dritte Anlauf
    # ohne das, was schon belegt ist.
    BEKANNT = ("momentum_kurz", "rsi")
    NEU = ("rsi_umkehr", "rsi_aenderung", "ema_lage", "ema_steigung",
           "ema_abstand_atr", "bandenge", "trendstruktur")
    # ⭐⭐⭐ Nutzerhinweis 26.09.: *"was ist mit den schon bekannten
    # Beitraegen oi_aenderung, funding, etc. in Kombination?"* - sie fehlten
    # in allen Messungen seit dem 25.09., weil `merkmale_je_symbol` mit
    # LEEREN Dicts aufgerufen wurde.
    #
    # ⚠️ 2.594 hat sie gemessen und als *nur Bewegung* eingestuft
    # (`oi_aenderung` Lift 1,654 -> 1,542, `funding` 1,216 gegen 1,302 in
    # der Gegenrichtung). ABER NIE IN KOMBINATION - und eine Groesse, die
    # ALLEIN nur Bewegung misst, kann in der Schnittmenge mit einem
    # Richtungstraeger sehr wohl etwas beitragen.
    TERMIN = ("oi_aenderung", "funding", "taker_verh", "konten_verh",
              "top_konten_verh", "volumenschub")
    NAMEN = BEKANNT + NEU + TERMIN + ("vola", "zufall")

    for crv, H in ZELLEN:
        G, R, RS, RO, MM = [], [], [], [], {k: [] for k in NAMEN}
        for sym, (stunden, high, low, close, volumen) in kurse.items():
            if sym.upper() == "BTC":
                continue
            idx = np.array([sid[s] for s in stunden], np.int64)
            atr = atr_tag_relativ(high, low, close)
            stop = np.clip(K_ATR * atr, STOP_MIN, STOP_MAX)
            zz, ss, ro, gu, _g = ausgaenge(high, low, close, stop,
                                           crv * stop, H)
            zs, sh, ros, _g2, _g3 = ausgaenge(high, low, close, stop,
                                              crv * stop, H, runter=True)
            mk = a_faktoren(close, atr)
            with np.errstate(divide="ignore", invalid="ignore"):
                lr = np.diff(np.log(np.maximum(close, 1e-12)), prepend=0.0)
            kk = np.ones(24) / 24.0
            mu = np.convolve(lr, kk, mode="full")[:len(close)]
            mu2 = np.convolve(lr ** 2, kk, mode="full")[:len(close)]
            vo = np.sqrt(np.maximum(mu2 - mu ** 2, 0.0)); vo[:24] = np.nan
            mk["vola"] = vo
            # die bekannten Traeger aus 2.594/2.597
            # ⭐ `merkmale_je_symbol` kennt Terminmarkt und Funding - genau
            # deshalb wird es hier MIT `tm` und `fund` aufgerufen, nicht mit
            # leeren Dicts wie in den Laeufen davor.
            mr = merkmale_je_symbol(sym, stunden, high, low, close, volumen,
                                    tm, fund)
            for k, v in mr.items():
                if k in NAMEN:
                    mk[k] = v
            if not ohne_sperre:
                gu = gu & ~np.nan_to_num(gesperrt_std[idx], nan=False)
            # ⚠️ Fehlt ein Merkmal fuer dieses Symbol (kein Terminmarkt),
            # wird es mit NaN gefuellt statt die Ankermenge zu leeren - die
            # Fuenftelbildung uebergeht NaN ohnehin. Nur die PREIS-Merkmale
            # sind Pflicht, sonst waere die Menge eine andere als in 2.597.
            for k in NAMEN:
                if k not in mk:
                    mk[k] = np.full(len(close), np.nan)
            for k in BEKANNT + NEU:
                gu = gu & np.isfinite(mk[k])
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            G.append(idx[sel])
            R.append(np.where(zz[sel], crv, np.where(ss[sel], -1.0,
                                                     np.nan_to_num(ro[sel]))))
            RS.append(np.where(zs[sel], crv, np.where(sh[sel], -1.0,
                                                      np.nan_to_num(ros[sel]))))
            RO.append(ro[sel])
            for k in NAMEN:
                MM[k].append(mk[k][sel] if k != "zufall"
                             else rng.random(len(sel)))
        if not G:
            continue
        G = np.concatenate(G); R = np.concatenate(R); RS = np.concatenate(RS)
        RO = np.concatenate(RO)
        MM = {k: np.concatenate(v) for k, v in MM.items()}
        er_alle = float(R.mean())
        print()
        print("=" * 100)
        print("CRV %.1f · H%d · %d Anker · E[R]_alle %+.5f   ➤ es fehlen "
              "%+.5f bis null" % (crv, H, len(G), er_alle, -er_alle))

        # Nullband einmal je Zelle - es haengt nicht am Merkmal
        nullw = []
        for _ in range(N_NULL):
            fz = fuenftel_je_stunde(G, rng.random(len(G)))
            if fz is None:
                continue
            i2, f2 = fz
            n2 = np.bincount(f2, minlength=5).astype(float)
            if (n2 < MIND_JE_FUENFTEL).any():
                continue
            e2 = np.bincount(f2, weights=R[i2], minlength=5) / n2
            nullw.append(float(e2.max() - e2.mean()))
        if len(nullw) < 10:
            print("  Nullband nicht zu bilden")
            continue
        nullw = np.array(nullw)
        grenze90 = float(np.percentile(nullw, NULL_PERZ))
        print("  Nullband (bestes Fuenftel gegen Mittel): Nullpunkt %+.5f · "
              "%d. Perz %+.5f" % (float(nullw.mean()), int(NULL_PERZ),
                                  grenze90))

        for name in NAMEN:
            fz = fuenftel_je_stunde(G, MM[name])
            if fz is None:
                continue
            i2, f2 = fz
            n5 = np.bincount(f2, minlength=5).astype(float)
            if (n5 < MIND_JE_FUENFTEL).any():
                continue
            e5 = np.bincount(f2, weights=R[i2], minlength=5) / n5
            spanne = float(e5.max() - e5.mean())
            bestes = int(np.argmax(e5))
            traegt = spanne > grenze90
            kz = "  <- KONTROLLE" if name in ("zufall", "vola") else ""
            # ⚠️⚠️ DIE GRUNDGESAMTHEIT IST KEINE STELLSCHRAUBE: ein
            # Terminmarkt-Merkmal liegt nicht fuer jedes Symbol vor, wird
            # also auf einer KLEINEREN Menge gemessen. Sein Bezug ist dann
            # `E[R]` auf SEINER eigenen Menge, nicht `er_alle` - sonst
            # vergleicht man zwei verschiedene Mengen.
            eigen = float(R[i2].mean())
            anteil = 100.0 * len(i2) / len(G)
            print("  %-16s %s" % (name,
                                  " ".join("%+8.5f" % x for x in e5)))
            if anteil < 99.0:
                print("      ⚠️ nur %.1f %% der Anker (%d) · E[R] auf DIESER "
                      "Menge %+.5f (gesamt %+.5f)"
                      % (anteil, len(i2), eigen, er_alle))
            print("      bestes Fuenftel %d = %+.5f · Spanne %+.5f · %s%s%s"
                  % (bestes, e5[bestes], spanne,
                     "✔ ordnet" if traegt else "- im Nullband",
                     "   ⭐⭐⭐ UEBER NULL" if e5[bestes] > 0 and traegt
                     else ("   (unter null)" if traegt else ""), kz))
            # ── ⭐⭐⭐ IST DAS BESTE FUENFTEL VON NULL ZU UNTERSCHEIDEN?
            #
            # ⚠️⚠️ Das Nullband oben gilt fuer die SPANNE, nicht fuer den
            # WERT. *Ueber null* ist ohne diese Rechnung keine Aussage.
            #
            # Zwei Pruefungen, beide noetig:
            #   (a) tagesgeblockter Fehler - die Anker eines Fuenftels
            #       stammen aus wenigen Tagen und sind nicht unabhaengig
            #   (b) ⭐ AUSWAHL-NULLWELT: das BESTE von fuenf Fuenfteln zu
            #       nehmen ist Rueckschau. Gemessen wird deshalb, wie hoch
            #       das beste Fuenftel eines ZUFALLSmerkmals liegt - also
            #       der Anteil, der allein aus dem Auswaehlen entsteht.
            if e5[bestes] > 0 and traegt:
                mb = np.zeros(len(G), bool)
                mb[i2[f2 == bestes]] = True
                tg = G[mb] // 24
                ut = np.unique(tg)
                if len(ut) >= 30:
                    pos = np.searchsorted(ut, tg)
                    jt = (np.bincount(pos, weights=R[mb], minlength=len(ut))
                          / np.maximum(np.bincount(pos, minlength=len(ut)), 1))
                    se = float(np.std(jt, ddof=1) / np.sqrt(len(ut)))
                else:
                    se = float("nan")
                beste_null = [float((np.bincount(
                    fz2[1], weights=R[fz2[0]], minlength=5)
                    / np.maximum(np.bincount(fz2[1], minlength=5), 1)).max())
                    for fz2 in (fuenftel_je_stunde(G, rng.random(len(G)))
                                for _ in range(N_NULL))
                    if fz2 is not None]
                bn = float(np.percentile(np.array(beste_null), NULL_PERZ))                     if len(beste_null) >= 10 else float("nan")
                print("      ⭐⭐ IST ES ECHT?  Wert %+.5f · Tagesfehler "
                      "±%.5f %s"
                      % (e5[bestes], se,
                         "✔ von null verschieden"
                         if np.isfinite(se) and e5[bestes] > 1.645 * se
                         else "⚠️ NICHT von null zu trennen"))
                print("         Auswahl-Nullwelt: bestes Fuenftel eines "
                      "ZUFALLSmerkmals liegt bei %+.5f (%d. Perz) · %s"
                      % (bn, int(NULL_PERZ),
                         "✔ daruber" if np.isfinite(bn) and e5[bestes] > bn
                         else "⛔ NICHT darueber - das ist die Auswahl"))
            if not traegt or name in ("zufall",):
                continue
            # Spiegelprobe auf echter Short-Geometrie
            e5s = np.bincount(f2, weights=RS[i2], minlength=5) / n5
            sp_g = float(e5s.max() - e5s.mean())
            verh = spanne / max(sp_g, 1e-12)
            print("      ⭐ SPIEGELPROBE Short-Spanne %+.5f · Verhaeltnis "
                  "%.2f · %s"
                  % (sp_g, verh,
                     "✔ RICHTUNG" if verh >= 1.30
                     else ("✔ inverse Richtung" if verh <= 0.77
                           else "⚠️ BEWEGUNG OHNE RICHTUNG - kein Beitrag")))
            # Trennschaerfe
            rgv = np.argsort(np.argsort(MM[name])) / max(1, len(MM[name]) - 1)
            aus = []
            for st in STAERKEN:
                w = []
                for _ in range(N_POSITIV):
                    mix = st * rgv + (1.0 - st) * rng.random(len(G))
                    fzm = fuenftel_je_stunde(G, mix)
                    if fzm is None:
                        continue
                    i4, f4 = fzm
                    n4 = np.bincount(f4, minlength=5).astype(float)
                    if (n4 < MIND_JE_FUENFTEL).any():
                        continue
                    e4 = np.bincount(f4, weights=R[i4], minlength=5) / n4
                    w.append(float(e4.max() - e4.mean()))
                if w:
                    aus.append("%.2f:%.0f%%"
                               % (st, 100 * float((np.array(w) > grenze90).mean())))
            print("      ⭐ TRENNSCHAERFE %s" % " ".join(aus))
        # ══ KOMBINATION: A (bekannter Traeger) UND B (neuer Faktor) ══
        #
        # ⭐ Nutzerhinweis 26.09.: *"koennen wir nicht mit den bereits
        # bekannten aus der Vormittagsmessung von gestern kombinieren?"* -
        # und genau das ist die Anordnung A ∧ B ∧ ¬C aus dem Bauplan vom
        # 25.09., die bisher nie gebaut wurde.
        #
        # ⚠️ Die Frage ist NICHT *traegt B?*, sondern *bringt B etwas
        # ZUSAETZLICH zu A?* Der Bezug ist deshalb das oberste Fuenftel von
        # A ALLEIN, nicht der Gesamtdurchschnitt.
        #
        # ⚠️⚠️ Und die Nullwelt muss die VERKLEINERUNG der Menge enthalten:
        # eine Schnittmenge ist kleiner und streut deshalb staerker. Als
        # Gegenprobe wird A mit einem ZUFALLSmerkmal geschnitten - gleiche
        # Groesse, keine Information.
        print()
        print("  " + "=" * 96)
        print("  ⭐⭐ KOMBINATION  A (bekannt) ∧ B (neu)   [Sperre ¬C ist "
              "bereits angewandt]")
        for a_name in BEKANNT:
            fza = fuenftel_je_stunde(G, MM[a_name])
            if fza is None:
                continue
            ia, fa = fza
            top_a = np.zeros(len(G), bool)
            top_a[ia[fa == 4]] = True
            if top_a.sum() < 5 * MIND_JE_FUENFTEL:
                continue
            er_a = float(R[top_a].mean())
            print("  %s allein (oberstes Fuenftel): %d Anker · E[R] %+.5f"
                  % (a_name, int(top_a.sum()), er_a))
            for b_name in NEU + ("vola",):
                fzb = fuenftel_je_stunde(G, MM[b_name])
                if fzb is None:
                    continue
                ib, fb = fzb
                for rand, etikett in ((4, "B oben"), (0, "B unten")):
                    top_b = np.zeros(len(G), bool)
                    top_b[ib[fb == rand]] = True
                    beide = top_a & top_b
                    if beide.sum() < MIND_JE_FUENFTEL:
                        continue
                    er_ab = float(R[beide].mean())
                    # Nullwelt: A geschnitten mit ZUFALL gleicher Groesse
                    quote = beide.sum() / max(top_a.sum(), 1)
                    nw = []
                    for _ in range(N_NULL):
                        z = rng.random(len(G))
                        schwelle = np.quantile(z[top_a], quote)
                        m = top_a & (z <= schwelle)
                        if m.sum() >= MIND_JE_FUENFTEL:
                            nw.append(float(R[m].mean()) - er_a)
                    if len(nw) < 10:
                        continue
                    g90 = float(np.percentile(np.array(nw), NULL_PERZ))
                    zugewinn = er_ab - er_a
                    if zugewinn <= g90:
                        continue
                    print("      + %-16s %-8s %7d Anker · E[R] %+.5f · "
                          "ZUGEWINN %+.5f (Band %+.5f) %s"
                          % (b_name, etikett, int(beide.sum()), er_ab,
                             zugewinn, g90,
                             "⭐⭐⭐ UEBER NULL" if er_ab > 0 else ""))
        print()

    print()
    print("  ⚠️ `vola` und `zufall` sind KONTROLLEN. Traegt ein A-Faktor")
    print("     nicht staerker als `vola`, misst er Volatilitaet - das war")
    print("     2.594 und 2.601.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
