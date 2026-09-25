# -*- coding: utf-8 -*-
"""REVERSE ENGINEERING: wie ist die LAGE vor scharfen Anstiegen?

Vorabfestlegung 15: `Basisinfos/Vorabfestlegung_15_Reverse_Engineering_25_09.md`

**Nutzervorgabe 25.09.2026:** *"Es gibt Assets welche an einem Tag in 3
Stunden 20 oder mehr Prozent steigen - Dann mach reverse Engineering - Wie
ist die LAGE bei diesen Assets wenn diese kurze und hohe Anstiege
verzeichnen."*

Und die Einordnung: *"Die Hebelgeometrie ist uninteressant da wir dies
bereits kennen - erst wenn wir den Hebel Einstieg und die Bewertung fuer die
Hebelhoehe kennen kommt die Geometrie ins Spiel"*.

═══════════════════════════════════════════════════════════════════════
 WARUM FALL-KONTROLLE UND NICHT FUENFTEL-SPANNE
═══════════════════════════════════════════════════════════════════════

Alle bisherigen Messungen fragten: *unterscheiden sich die MITTELWERTE der
Fuenftel?* Gemessen (2.593): Streuung 0,19 bei 2.184 Tagen, also
Nachweisgrenze 0,0102 - und der erwartete Effekt liegt bei 0,002 bis 0,012.
**Effekt gleich Fehler.**

Diese Messung fragt anders: *wie sah die Lage VOR den Ereignissen aus, die
den Trade getragen haetten?* Das Ereignis ist selten und extrem, der
Kontrast damit gross. Die Pruefgroesse ist der LIFT:

    Lift = P(Ereignis | oberstes Merkmalsfuenftel) / P(Ereignis)

➤ Lift 2,0 heisst: in dieser Lage passiert es doppelt so oft. Das ist genau
die Auskunft, die eine Hebelbewertung braucht - eine Mittelwertdifferenz ist
es nicht.

⭐ Ein Merkmal kann im MITTEL nichts bewegen und trotzdem die EXTREME
ordnen. Eine Mittelwertmessung sieht das per Konstruktion nicht.

═══════════════════════════════════════════════════════════════════════
 DER NULLPUNKT - und warum er so gezogen wird
═══════════════════════════════════════════════════════════════════════

Ereignisse HAEUFEN SICH: ein marktweiter Schub trifft viele Symbole
gleichzeitig. Ein naiver Binomialtest wuerde jede Haeufung signifikant
machen. Deshalb wird die MERKMALSZUORDNUNG INNERHALB JEDER STUNDE
gemischt - die Haeufung bleibt erhalten, nur die Zuordnung faellt.

⚠️ 40 Ziehungen, 90. Perzentil - aus `messnorm`, nicht aus eigenen Zahlen.

⚠️ NUR LESEN. Keine Datenbank wird beschrieben.

    python messe_reverse_scharfe_anstiege.py [--symbole N] [--schnell]
"""
from __future__ import annotations

import os
import sqlite3
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                           # noqa: E402
from messe_hebel_dimension import _lade_terminmarkt            # noqa: E402

STUNDEN_DB = os.path.join("data", "stundenkurse.db")
FUNDING_DB = os.path.join("data", "funding_historie.db")

STOP = 0.05                      # GRENZEN['stop_min_relativ'] - die engste
ZIELE = (0.10, 0.15, 0.20)       # CRV 2 / 3 / 4
HORIZONTE = (3, 6, 12, 24)
VORLAUF = 30                     # Stunden Warmlauf fuer die Merkmale
MIND_JE_STUNDE = 10              # sonst gibt es kein Fuenftel
SAAT = 20260925


# ═══════════════════════════════════════════════════════════════════════
#  Laden
# ═══════════════════════════════════════════════════════════════════════

def lade_kurse(grenze=None) -> dict:
    """{symbol: (stunden, high, low, close, volumen)} als Arrays."""
    c = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    syms = [r[0] for r in c.execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol "
        "HAVING COUNT(*) > 2000 ORDER BY COUNT(*) DESC")]
    if grenze:
        syms = syms[:grenze]
    aus = {}
    for s in syms:
        rows = c.execute(
            "SELECT stunde, high, low, close, volumen FROM stundenkurse "
            "WHERE symbol=? ORDER BY stunde", (s,)).fetchall()
        if len(rows) < 500:
            continue
        aus[s] = (
            [r[0] for r in rows],
            np.array([r[1] for r in rows], float),
            np.array([r[2] for r in rows], float),
            np.array([r[3] for r in rows], float),
            np.array([(r[4] or 0.0) for r in rows], float),
        )
    c.close()
    return aus


def lade_funding() -> dict:
    if not os.path.exists(FUNDING_DB):
        return {}
    c = sqlite3.connect("file:%s?mode=ro" % FUNDING_DB, uri=True)
    aus = defaultdict(dict)
    for s, t, w in c.execute("SELECT symbol, datum, wert FROM funding"):
        aus[str(s).upper()][str(t)[:10]] = float(w)
    c.close()
    return aus


# ═══════════════════════════════════════════════════════════════════════
#  Das EREIGNIS - vektorisiert, Stop zuerst
# ═══════════════════════════════════════════════════════════════════════

def ereignisse(high, low, close, runter=False):
    """-> {(ziel, H): bool-Array} und ein `gueltig`-Array.

    ⭐⭐ `runter=True` SPIEGELT das Ereignis: Ziel nach UNTEN (-ziel),
    Stop nach OBEN (+5 %). Das ist die entscheidende Kontrolle - ein
    Merkmal, das nach oben UND unten gleich stark traegt, misst
    VOLATILITAET, nicht RICHTUNG, und ist als Hebelbewertung wertlos.
    (Stehende Regel: `vola` ist Geometrie, nicht Richtung.)

    ⚠️⚠️ DIE REIHENFOLGE INNERHALB EINER STUNDE IST UNBEKANNT (die Kerze
    hat high UND low). Wie `barriere_je_reihe`: der STOP wird zuerst
    geprueft, Gleichstaende fallen also zum Stop - die vorsichtige
    Annahme. Auf Tagesbasis kostete sie +0,0003 (2.583).

    ⭐ VEKTORISIERT UEBER DIE SCHRITTE, nicht ueber die Anker: fuer jeden
    Versatz k wird EIN numpy-Vergleich gerechnet. Bei H=24 sind das 24
    Durchlaeufe je Ziel statt 24 x n Schleifendurchlaeufe. Und weil die
    Horizonte geschachtelt sind, liefert EINE Folge alle vier - es wird
    bei k = 3, 6, 12 und 24 ein Zwischenstand genommen.
    """
    n = len(close)
    hmax = max(HORIZONTE)
    aus = {}
    gueltig = np.zeros(n, bool)
    gueltig[VORLAUF:n - hmax] = True
    idx = np.arange(n)
    for ziel_rel in ZIELE:
        if runter:
            stop_kurs = close * (1.0 + STOP)      # Stop liegt OBEN
            ziel_kurs = close * (1.0 - ziel_rel)  # Ziel liegt UNTEN
        else:
            stop_kurs = close * (1.0 - STOP)
            ziel_kurs = close * (1.0 + ziel_rel)
        fertig = ~gueltig.copy()          # ungueltige gelten als fertig
        treffer = np.zeros(n, bool)
        for k in range(1, hmax + 1):
            j = np.minimum(idx + k, n - 1)
            offen = ~fertig
            if not offen.any():
                pass
            else:
                if runter:
                    stop_hit = offen & (high[j] >= stop_kurs)
                    ziel_hit = offen & (low[j] <= ziel_kurs)
                else:
                    stop_hit = offen & (low[j] <= stop_kurs)
                    ziel_hit = offen & (high[j] >= ziel_kurs)
                # Stop zuerst: wo beides, gilt Stop
                neu_stop = stop_hit
                neu_ziel = ziel_hit & ~stop_hit
                treffer |= neu_ziel
                fertig |= (neu_stop | neu_ziel)
            if k in HORIZONTE:
                aus[(ziel_rel, k)] = treffer.copy() & gueltig
        # Sicherheit: die Zielgroesse ist binaer
    return aus, gueltig


# ═══════════════════════════════════════════════════════════════════════
#  Die LAGE - streng kausal, nur Stunden < t
# ═══════════════════════════════════════════════════════════════════════

def _rsi(close, n=14):
    d = np.diff(close, prepend=close[0])
    auf = np.where(d > 0, d, 0.0)
    ab = np.where(d < 0, -d, 0.0)
    ka = np.convolve(auf, np.ones(n) / n, mode="full")[:len(close)]
    kb = np.convolve(ab, np.ones(n) / n, mode="full")[:len(close)]
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = ka / kb
    aus = 100.0 - 100.0 / (1.0 + rs)
    aus[:n] = np.nan
    return aus


def _schiebe(a, k):
    """a(t-k), vorne mit nan - der Riegel gegen Zukunftswissen."""
    aus = np.full(len(a), np.nan)
    if k < len(a):
        aus[k:] = a[:len(a) - k]
    return aus


def merkmale_je_symbol(sym, stunden, high, low, close, volumen, tm, fund):
    """{name: Array}. ⚠️ JEDER WERT NUR AUS STUNDEN <= t."""
    n = len(close)
    m = {}
    with np.errstate(divide="ignore", invalid="ignore"):
        logret = np.diff(np.log(np.maximum(close, 1e-12)), prepend=0.0)
    # vola: Streuung der letzten 24 Stundenrenditen, bis t
    k = np.ones(24) / 24.0
    mu = np.convolve(logret, k, mode="full")[:n]
    mu2 = np.convolve(logret ** 2, k, mode="full")[:n]
    vola = np.sqrt(np.maximum(mu2 - mu ** 2, 0.0))
    vola[:24] = np.nan
    m["vola"] = vola
    m["rsi"] = _rsi(close)
    with np.errstate(divide="ignore", invalid="ignore"):
        m["momentum_kurz"] = close / _schiebe(close, 24) - 1.0
        vs = np.convolve(volumen, np.ones(24), mode="full")[:n]
        vs[:24] = np.nan
        m["volumenschub"] = volumen * 24.0 / np.maximum(vs, 1e-12)
    # Terminmarkt, stuendlich
    t_sym = tm.get(sym) or {}
    if t_sym:
        for nam, feld in (("konten_verh", "konten_verh"),
                          ("top_konten_verh", "top_konten_verh"),
                          ("top_summe_verh", "top_summe_verh"),
                          ("taker_verh", "taker_verh")):
            a = np.array([(t_sym.get(s) or {}).get(feld, np.nan)
                          for s in stunden], float)
            m[nam] = a
        oi = np.array([(t_sym.get(s) or {}).get("oi", np.nan)
                       for s in stunden], float)
        with np.errstate(divide="ignore", invalid="ignore"):
            m["oi_aenderung"] = oi / _schiebe(oi, 6) - 1.0
    # funding: der Wert des VORTAGS, nie des laufenden Tages
    f = fund.get(sym.upper())
    if f:
        tage = sorted(f)
        vor = {}
        for i, t in enumerate(tage):
            vor[t] = f[tage[i - 1]] if i else np.nan
        m["funding"] = np.array([vor.get(str(s)[:10], np.nan)
                                 for s in stunden], float)
    return m


# ═══════════════════════════════════════════════════════════════════════
#  Der LIFT - vollvektorisiert ueber alle Stunden
# ═══════════════════════════════════════════════════════════════════════

def lift(gruppe, wert, treffer, rng=None):
    """Lift des OBERSTEN Fuenftels. `gruppe` = Stunden-Id (oder Stunde x
    Vola-Fuenftel). `rng` gesetzt -> die Zuordnung wird INNERHALB der
    Gruppe gemischt (Nullwelt).

    ⭐ Kein Python-Loop ueber 41.000 Stunden: ein `lexsort` bringt alles in
    Gruppen-dann-Wert-Ordnung, die Position in der Gruppe folgt aus
    `arange` minus Gruppenanfang.
    """
    ok = np.isfinite(wert)
    if ok.sum() < 1000:
        return None
    g, w, y = gruppe[ok], wert[ok], treffer[ok]
    if rng is not None:
        w = rng.random(len(w))
    ordnung = np.lexsort((w, g))
    gs = g[ordnung]
    ys = y[ordnung]
    # Gruppengrenzen
    neu = np.empty(len(gs), bool)
    neu[0] = True
    neu[1:] = gs[1:] != gs[:-1]
    start_idx = np.flatnonzero(neu)
    groesse = np.diff(np.append(start_idx, len(gs)))
    gross = groesse >= MIND_JE_STUNDE
    if not gross.any():
        return None
    start_je = np.repeat(start_idx, groesse)
    groesse_je = np.repeat(groesse, groesse)
    behalte = np.repeat(gross, groesse)
    pos = np.arange(len(gs)) - start_je
    oben = behalte & (pos >= np.ceil(0.8 * groesse_je))
    alle = behalte
    n_o, n_a = int(oben.sum()), int(alle.sum())
    if n_o < 200 or n_a < 1000:
        return None
    p_o = float(ys[oben].mean())
    p_a = float(ys[alle].mean())
    if p_a <= 0:
        return None
    return dict(lift=p_o / p_a, p_oben=p_o, p_alle=p_a, n_oben=n_o, n_alle=n_a)


def vola_band(gruppe, vola, baender=3):
    """-> Array 0..baender-1, der Vola-Rang INNERHALB jeder Stunde (nan -> -1).

    ⚠️ TERZILE, nicht Fuenftel (korrigiert 25.09., die eigene
    Gegenpruefung fand es): Stunde x Fuenftel ergibt bei 116 Symbolen 23
    Mitglieder und im obersten Merkmalsfuenftel nur 4 - die
    Mindestbesetzung verwirft dann Zellen. Mit Terzilen sind es 38 bzw. 8.
    Das haelt die Vola weniger streng fest, dafuer ist die Zelle besetzt;
    der Tausch steht in der Ausgabe.

    ⚠️ Das Fuenftel wird je Stunde gebildet, nicht global - sonst waere es
    ein Regimemass (welche Woche war ruhig) statt eines Querschnittsmasses
    (welches Asset ist heute unruhig).
    """
    aus = np.full(len(gruppe), -1, np.int8)
    ok = np.isfinite(vola)
    g, v = gruppe[ok], vola[ok]
    ordnung = np.lexsort((v, g))
    gs = g[ordnung]
    neu = np.empty(len(gs), bool)
    neu[0] = True
    neu[1:] = gs[1:] != gs[:-1]
    start = np.flatnonzero(neu)
    groesse = np.diff(np.append(start, len(gs)))
    pos = np.arange(len(gs)) - np.repeat(start, groesse)
    rel = pos / np.maximum(np.repeat(groesse, groesse) - 1, 1)
    f = np.minimum((rel * baender).astype(np.int8), baender - 1)
    tmp = np.full(len(g), -1, np.int8)
    tmp[ordnung] = f
    aus[ok] = tmp
    return aus


def gruppenbau(gruppe, wert, treffer):
    """Die Gruppenstruktur EINMAL: je Stunde n, k (Ereignisse) und m
    (Groesse des obersten Fuenftels). -> (n, k, m, p_alle) oder None.

    ⭐ Danach braucht die Nullwelt keine Sortierung mehr: sie ist
    hypergeometrisch.
    """
    ok = np.isfinite(wert)
    if ok.sum() < 1000:
        return None
    g, y = gruppe[ok], treffer[ok].astype(np.int64)
    ordnung = np.argsort(g, kind="stable")
    gs, ys = g[ordnung], y[ordnung]
    neu = np.empty(len(gs), bool)
    neu[0] = True
    neu[1:] = gs[1:] != gs[:-1]
    start = np.flatnonzero(neu)
    n = np.diff(np.append(start, len(gs)))
    k = np.add.reduceat(ys, start)
    gross = n >= MIND_JE_STUNDE
    n, k = n[gross], k[gross]
    if not len(n):
        return None
    m = n - np.ceil(0.8 * n).astype(np.int64)
    gut = m >= 1
    n, k, m = n[gut], k[gut], m[gut]
    if not len(n) or n.sum() < 1000 or m.sum() < 200:
        return None
    return n, k, m, float(k.sum()) / float(n.sum())


def null_exakt(struktur, zieh, rng):
    """Die Nullverteilung des Lifts - hypergeometrisch, ohne Sortierung."""
    n, k, m, p_alle = struktur
    if p_alle <= 0:
        return []
    aus = []
    for _ in range(zieh):
        tr = rng.hypergeometric(np.maximum(k, 0), np.maximum(n - k, 0), m)
        aus.append(float(tr.sum()) / float(m.sum()) / p_alle)
    return aus


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    schnell = "--schnell" in sys.argv
    nur = None
    if "--zellen" in sys.argv:
        nur = int(sys.argv[sys.argv.index("--zellen") + 1])

    print("=" * 100)
    print("REVERSE ENGINEERING - DIE LAGE VOR SCHARFEN ANSTIEGEN")
    print("=" * 100)
    print("  Vorabfestlegung 15 · Stop %.0f %% · Ziele %s · Horizonte %s h"
          % (100 * STOP, "/".join("%.0f%%" % (100 * z) for z in ZIELE),
             "/".join(str(h) for h in HORIZONTE)))
    print("  Nullpunkt aus messnorm: %d Ziehungen, %.0f. Perzentil%s"
          % (N.NULL_ZIEHUNGEN, N.NULL_PERZENTIL,
             "  ⚠️ SCHNELLLAUF: 8 Ziehungen" if schnell else ""))
    zieh = 8 if schnell else N.NULL_ZIEHUNGEN

    kurse = lade_kurse(grenze)
    print("  %d Symbole geladen" % len(kurse))
    tm = _lade_terminmarkt(set(kurse))
    fund = lade_funding()
    print("  Terminmarkt fuer %d Symbole · funding fuer %d"
          % (len(tm), len(fund)))

    # ── alles in eine flache Tabelle ──────────────────────────────────
    stunden_id: dict = {}
    sp_g, sp_ev, sp_m = [], defaultdict(list), defaultdict(list)
    sp_ab = defaultdict(list)
    sp_sym, sp_jahr = [], []
    namen = None
    for sym, (stunden, high, low, close, volumen) in kurse.items():
        ev, gueltig = ereignisse(high, low, close)
        ab, _ = ereignisse(high, low, close, runter=True)
        if not gueltig.any():
            continue
        m = merkmale_je_symbol(sym, stunden, high, low, close, volumen,
                              tm, fund)
        if namen is None:
            namen = sorted(m)
        sel = np.flatnonzero(gueltig)
        for s in (stunden[i] for i in sel):
            if s not in stunden_id:
                stunden_id[s] = len(stunden_id)
        sp_g.append(np.array([stunden_id[stunden[i]] for i in sel], np.int64))
        sp_sym.extend([sym] * len(sel))
        sp_jahr.append(np.array([int(str(stunden[i])[:4]) for i in sel],
                                np.int16))
        for schl, a in ev.items():
            sp_ev[schl].append(a[sel])
        for schl, a in ab.items():
            sp_ab[schl].append(a[sel])
        for nam in namen:
            a = m.get(nam)
            sp_m[nam].append(a[sel] if a is not None
                             else np.full(len(sel), np.nan))
    if not sp_g:
        print("  ⛔ keine Anker")
        return 1

    gruppe = np.concatenate(sp_g)
    jahr = np.concatenate(sp_jahr)
    sym_arr = np.array(sp_sym)
    ev = {k: np.concatenate(v) for k, v in sp_ev.items()}
    evab = {k: np.concatenate(v) for k, v in sp_ab.items()}
    mm = {k: np.concatenate(v) for k, v in sp_m.items()}
    rng = np.random.default_rng(SAAT)
    mm["zufall"] = rng.random(len(gruppe))
    print("  %d Anker · %d Stunden" % (len(gruppe), len(stunden_id)))

    # ── ⚠️ DER RIEGEL AUF DEN DATEN (Befund 2.590) ────────────────────
    for schl, a in ev.items():
        u = np.unique(a)
        if not set(u.tolist()) <= {False, True, 0, 1}:
            print("  ⛔ ABBRUCH: Ereignis %s ist nicht binaer: %s" % (schl, u))
            return 1
    print("  ✔ Riegel: alle %d Ereignisreihen sind binaer" % len(ev))

    # ── ⭐ DIE PROBE: hypergeometrische Nullwelt gegen Permutation ─────
    if "--nullprobe" in sys.argv:
        schl0 = sorted(ev)[0]
        y0 = ev[schl0]
        print()
        print("  PROBE: exakte Nullwelt gegen Permutation (Ziel %s, %d h)"
              % ("%.0f%%" % (100 * schl0[0]), schl0[1]))
        for nam in ("vola", "oi_aenderung", "zufall"):
            if nam not in mm:
                continue
            st = gruppenbau(gruppe, mm[nam], y0)
            if not st:
                continue
            a = null_exakt(st, 40, np.random.default_rng(1))
            rg = np.random.default_rng(2)
            b = [x["lift"] for x in
                 (lift(gruppe, mm[nam], y0, rng=rg) for _ in range(40)) if x]
            print("     %-16s exakt  Mittel %.4f · 10./90. %.4f/%.4f"
                  % (nam, float(np.mean(a)), float(np.percentile(a, 10)),
                     float(np.percentile(a, 90))))
            print("     %-16s perm   Mittel %.4f · 10./90. %.4f/%.4f"
                  % ("", float(np.mean(b)), float(np.percentile(b, 10)),
                     float(np.percentile(b, 90))))
            d = abs(float(np.percentile(a, 90)) - float(np.percentile(b, 90)))
            print("     %-16s ➤ Abweichung im 90. Perzentil %.4f  %s"
                  % ("", d,
                     "✔ dieselbe Nullwelt" if d < 0.02
                     else "⚠️ NICHT dieselbe - die Abkuerzung gilt nicht"))
        print()

    # ══ § 3 ZUERST: GIBT ES DIE EREIGNISSE UEBERHAUPT? ════════════════
    print()
    print("=" * 100)
    print("1) DIE HAEUFIGKEIT - vor jeder Bewertung (Vorabfestlegung 15 § 3)")
    print("=" * 100)
    print("   %-8s %-6s %10s %10s %9s %8s"
          % ("Ziel", "H", "Ereignisse", "Anteil", "Symbole", "Jahre"))
    tragfaehig = []
    for ziel_rel in ZIELE:
        for h in HORIZONTE:
            a = ev[(ziel_rel, h)]
            n = int(a.sum())
            syms = len(set(sym_arr[a].tolist()))
            jahre = len(set(jahr[a].tolist()))
            ok = (n / len(a) >= 0.001) and syms >= 20 and jahre >= 3
            print("   %-8s %-6d %10d %9.3f%% %9d %8d %s"
                  % ("%.0f%%" % (100 * ziel_rel), h, n, 100.0 * n / len(a),
                     syms, jahre, "✔" if ok else "⛔ Anekdote"))
            if ok:
                tragfaehig.append((ziel_rel, h))
    if not tragfaehig:
        print()
        print("   ⛔⛔ KEINE Zelle erfuellt Kriterium 0. Die Bewertungsfrage")
        print("        ist damit nachrangig - es ist kein Geschaeft.")
        return 0
    print()
    print("   ➤ %d von %d Zellen tragfaehig" % (len(tragfaehig), len(ev)),
          flush=True)
    if nur:
        tragfaehig = tragfaehig[:nur]
        print("   ⚠️ --zellen %d: nur die ersten %d werden bewertet"
              % (nur, len(tragfaehig)), flush=True)

    # ══ § 5 DER LIFT ══════════════════════════════════════════════════
    print()
    print("=" * 100)
    print("2) DER LIFT - P(Ereignis | oberstes Fuenftel) / P(Ereignis)")
    print("=" * 100)
    kandidaten = [n for n in sorted(mm) if n != "zufall"] + ["zufall"]

    for ziel_rel, h in tragfaehig:
        y = ev[(ziel_rel, h)]
        print()
        print("   ── Ziel +%.0f %% in %d h · Basisrate %.4f %%"
              % (100 * ziel_rel, h, 100 * y.mean()))
        print("      %-18s %7s %7s %8s %8s %8s  %s"
              % ("Merkmal", "Lift+", "Lift-", "+ / -", "Staerke",
                 "Nullband", "Urteil"), flush=True)
        # ⭐ EIN Nullpunkt je Merkmal (die Verfuegbarkeitsmuster sind
        #    verschieden) - aber gemischt wird immer gleich.
        yab = evab[(ziel_rel, h)]
        for nam in kandidaten:
            r = lift(gruppe, mm[nam], y)
            rab = lift(gruppe, mm[nam], yab)
            if r is None:
                print("      %-18s %s" % (nam, "zu duenn"), flush=True)
                continue
            rg = np.random.default_rng(SAAT + 7)
            st = gruppenbau(gruppe, mm[nam], y)
            nz = null_exakt(st, zieh, rg) if st else []
            # ⭐⭐ ZWEISEITIG. Ein Lift UNTER dem Nullband ist genauso
            # ein Befund wie einer darueber - und als Verhaeltnis oft
            # groesser: 0,529 entspricht 1,89. Die einseitige Fassung
            # hatte `top_konten_verh` (0,529), `top_summe_verh` (0,631)
            # und `konten_verh` (0,656) als ,Rauschen` ausgewiesen.
            if len(nz) >= 5:
                p90 = float(np.percentile(nz, N.NULL_PERZENTIL))
                p10 = float(np.percentile(nz, 100.0 - N.NULL_PERZENTIL))
            else:
                p90 = p10 = float("nan")
            l_ab = rab["lift"] if rab else float("nan")
            gut_ab = np.isfinite(l_ab) and l_ab > 0
            verh = (r["lift"] / l_ab) if gut_ab else float("nan")
            # ⭐ DAS URTEIL: erst aus dem Nullband heraus, DANN die Richtung
            l = r["lift"]
            # Staerke als Verhaeltnis, damit 0,53 und 1,89 vergleichbar sind
            staerke = max(l, 1.0 / l) if l > 0 else float("nan")
            draussen = (np.isfinite(p90) and np.isfinite(p10)
                        and (l > p90 or l < p10))
            invers = np.isfinite(l) and l < 1.0
            if not draussen:
                urteil = "⛔ im Nullband"
            elif not np.isfinite(verh):
                urteil = "ueber %.3f · Spiegel unbestimmt" % p90
            elif (not invers and verh >= 1.30) or (invers and verh <= 0.77):
                urteil = ("⭐ RICHTUNG%s" % (", invers" if invers else ""))
            else:
                urteil = "⚠️ nur BEWEGUNG - beide Seiten gleich"
            print("      %-18s %7.3f %7.3f %8.3f %8.3f  %.2f-%.2f  %s"
                  % (nam, l, l_ab, verh, staerke, p10, p90, urteil),
                  flush=True)
    print()
    print("   ⚠️ ENTSCHEIDUNGSREGEL (§ 7, vorab): Lift >= 1,5, ueber dem")
    print("      Nullpunkt, auf >= 2 Zielschwellen UND in beiden Haelften.")
    print("      `zufall` ueber dem Nullpunkt -> Lauf ungueltig.")
    print()
    print("   ⭐⭐ DIE SPIEGELPROBE IST DIE HARTE. `Lift-` ist dasselbe")
    print("      Ereignis nach UNTEN (-Ziel bevor +5 %). Wer auf beiden")
    print("      Seiten gleich traegt, misst VOLATILITAET und ist als")
    print("      Hebelbewertung wertlos - stehende Regel: vola ist")
    print("      Geometrie, nicht Richtung. Nur ein Verhaeltnis ueber")
    print("      1,30 oder unter 0,77 ist RICHTUNG.")
    print()
    print("   ⭐ `Staerke` ist max(Lift, 1/Lift) - damit sind ein Lift von")
    print("      0,53 und einer von 1,89 vergleichbar. Das Nullband ist")
    print("      ZWEISEITIG (10. bis 90. Perzentil der Nullziehungen); ein")
    print("      INVERSER Beitrag ist ausdruecklich erwuenscht, solange die")
    print("      Spiegelprobe ihn als Richtung bestaetigt.")
    print()
    # ══ PUNKT 3: BEI FESTGEHALTENER VOLA - als DOSIS-WIRKUNG ══════════
    if "vola" not in mm:
        return 0
    print()
    print("=" * 100)
    print("3) BEI FESTGEHALTENER `vola` - DOSIS-WIRKUNG "
          "(Vorabfestlegung 15 § 7 Punkt 3)")
    print("=" * 100)
    print("   ⭐ Der Rang wird je STUNDE x VOLA-BAND gebildet. Je mehr")
    print("      Baender, desto strenger ist `vola` festgehalten.")
    print("   ⚠️⚠️ EIN VOLA-ARTEFAKT MUSS GEGEN LIFT 1 ZERFALLEN, wenn die")
    print("      Kontrolle strenger wird. Ein eigener Beitrag nicht. Die")
    print("      RICHTUNG des Zerfalls ist die Auskunft, nicht der Einzelwert.")
    print("   ⚠️ Bei vielen Baendern werden die Zellen duenn und der")
    print("      Nullpunkt steigt - das Nullband gehoert mitgelesen.")

    def _mittlere_streuung(schl, werte):
        ordnung = np.argsort(schl, kind="stable")
        s, v = schl[ordnung], werte[ordnung]
        neu_ = np.empty(len(s), bool)
        neu_[0] = True
        neu_[1:] = s[1:] != s[:-1]
        st_ = np.flatnonzero(neu_)
        n_ = np.diff(np.append(st_, len(s)))
        su = np.add.reduceat(v, st_)
        su2 = np.add.reduceat(v * v, st_)
        gross = n_ >= 4
        if not gross.any():
            return float("nan")
        mu = su[gross] / n_[gross]
        var = np.maximum(su2[gross] / n_[gross] - mu * mu, 0.0)
        return float(np.sqrt((var * n_[gross]).sum() / n_[gross].sum()))

    STUFEN = (1, 3, 5, 8)
    for ziel_rel, h in tragfaehig[:2]:
        y = ev[(ziel_rel, h)]
        yab = evab[(ziel_rel, h)]
        print()
        print("   ── Ziel +%.0f %% in %d h" % (100 * ziel_rel, h), flush=True)
        # Kopfzeile: Vola-Reststreuung je Stufe
        kopf, rest = [], {}
        for b in STUFEN:
            if b == 1:
                g2 = gruppe
                gilt = np.isfinite(mm["vola"])
            else:
                vf = vola_band(gruppe, mm["vola"], b)
                gilt = vf >= 0
                g2 = gruppe * b + np.maximum(vf, 0)
            rest[b] = (g2, gilt)
            r_in = _mittlere_streuung(g2[gilt], mm["vola"][gilt])
            r_st = _mittlere_streuung(gruppe[gilt], mm["vola"][gilt])
            kopf.append("%d Bd (%.0f%%)" % (b, 100 * r_in / r_st if r_st
                                            else float("nan")))
        print("      %-18s %s   %s"
              % ("Merkmal", " ".join("%13s" % k for k in kopf), "Urteil"),
              flush=True)
        urteile = {}
        for nam in kandidaten:
            if nam == "vola":
                continue
            zeile, lifts = [], []
            for b in STUFEN:
                g2, gilt = rest[b]
                w = np.where(gilt, mm[nam], np.nan)
                r = lift(g2, w, y)
                rab = lift(g2, w, yab)
                if r is None:
                    zeile.append("%13s" % "zu duenn")
                    lifts.append(None)
                    continue
                st = gruppenbau(g2, w, y)
                nz = (null_exakt(st, zieh, np.random.default_rng(SAAT + 11))
                      if st else [])
                if len(nz) >= 5:
                    p90 = float(np.percentile(nz, N.NULL_PERZENTIL))
                    p10 = float(np.percentile(nz, 100.0 - N.NULL_PERZENTIL))
                else:
                    p90 = p10 = float("nan")
                l = r["lift"]
                l_ab = rab["lift"] if rab else float("nan")
                verh = (l / l_ab) if (np.isfinite(l_ab) and l_ab > 0) \
                    else float("nan")
                draussen = (np.isfinite(p90) and np.isfinite(p10)
                            and (l > p90 or l < p10))
                marke = "" if draussen else "~"
                zeile.append("%12.3f%s" % (l, marke))
                lifts.append(dict(lift=l, verh=verh, draussen=draussen,
                                  staerke=max(l, 1.0 / l) if l > 0 else np.nan))
            # ⭐ DAS URTEIL AUS DER DOSIS: haelt die Staerke bis zur
            #    strengsten besetzten Stufe, ist es KEIN Vola-Artefakt
            gut = [x for x in lifts if x]
            if len(gut) < 2:
                u = "zu duenn"
            else:
                s0, sN = gut[0]["staerke"], gut[-1]["staerke"]
                haelt = sN >= 1.0 + 0.6 * (s0 - 1.0)
                richtung = (gut[-1]["verh"] >= 1.30
                            if gut[-1]["lift"] >= 1.0
                            else gut[-1]["verh"] <= 0.77)
                if not gut[-1]["draussen"]:
                    u = "⛔ streng: im Nullband"
                elif not haelt:
                    u = "⚠️ ZERFAELLT (%.2f -> %.2f) - Vola" % (s0, sN)
                elif not richtung:
                    u = "⚠️ haelt, aber nur BEWEGUNG"
                else:
                    u = "⭐ EIGENER BEITRAG (%.2f -> %.2f)" % (s0, sN)
            urteile[nam] = u
            print("      %-18s %s   %s" % (nam, " ".join(zeile), u),
                  flush=True)
        print("      %-18s %s" % ("", "~ = im Nullband"), flush=True)
    print()
    print("   ⚠️⚠️ WAS HIER FAELLT, war Volatilitaet unter anderem Namen.")
    print("      Was bleibt, ist ein EIGENER Beitrag - und nur der taugt")
    print("      als Hebelbewertung neben `vola`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
