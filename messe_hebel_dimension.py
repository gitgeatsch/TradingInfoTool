# -*- coding: utf-8 -*-
"""H-A: die HEBEL-Dimension auf der Stundenbasis (24.09.2026)

Vorabfestlegung: `Basisinfos/Vorabfestlegung_Stundenbasis_24_09.md`
Plan: `Basisinfos/Gesamtlage_Hebelumbau_24_09.md` Paragraf 4, Schritt H-A.

Nutzervorgabe: *„JETZT geht es um den HEBELUMBAU nur HEBEL. Du kannst spot
als Vergleich fuer den Einstieg nehmen - Wirkung vorher nachher - ABER
vermessen und analysiert soll nur der Hebel werden."*

═══════════════════════════════════════════════════════════════════════
 ZWEI FRAGEN, GETRENNT AUSGEWIESEN
═══════════════════════════════════════════════════════════════════════

A1  DIE BASISLINIE. Wo liegt die Trefferquote je Haltedauer und Stopweite -
    ueber oder unter der Kelly-Nullstelle 1/(1+CRV) = 0,3333?

    ⚠️ A1 schliesst A2 NICHT aus. Eine Teilmenge kann ueber der Nullstelle
    liegen, auch wenn der Schnitt darunter liegt. A1 sagt, WIE WEIT die
    Kandidaten heben muessen - nicht, ob es sich lohnt zu suchen.

A2  DIE KANDIDATEN. Welche der sechs stuendlichen Terminmarktgroessen
    trennen - auf welcher Haltedauer?

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ DIE ZIELGROESSE - und warum sie neu ist
═══════════════════════════════════════════════════════════════════════

    ergebnis_r   Ziel zuerst      +CRV
                 Stop zuerst      -1
                 keins von beiden (Kurs - Einstieg) / Stopabstand
                                  ⭐ der Stundenschlusskurs am Ende

Der dritte Fall ist der Kern. Bei H2 bleiben 61,3 Prozent der Trades OFFEN
(2.582) - `barriere` wirft sie weg und misst ein Drittel der Wirklichkeit,
und zwar das unguenstigste. ⚠️ Auf TAGESdaten kennt man diesen Kurs nicht;
deshalb ist die Stundenbasis die Voraussetzung, nicht eine Verbesserung.

⚠️ Gebuehren und Finanzierung gehen NICHT ein (Regel 2). Sie gehoeren in
die Mail, nicht in die Bewertung.

═══════════════════════════════════════════════════════════════════════
 ⚠️ DER STOP IST EINE ACHSE, KEINE KONSTANTE
═══════════════════════════════════════════════════════════════════════

    prod       min(25 %, max(5 %, 0,75 x ATR14))   die Produktionsgeometrie
    skaliert   dasselbe x sqrt(H/24)               haltedauergerecht

Gemessen am 24.09.: mit der Skalierung wird die Ausgangsverteilung ueber
alle Haltedauern fast konstant - die Signatur einer haltedauerneutralen
Geometrie. Beide laufen nebeneinander; welche besser ist, entscheidet
diese Messung.

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ SPOT IST DER VERGLEICHSARM, NICHT DER MASSSTAB
═══════════════════════════════════════════════════════════════════════

H20 auf Tagesbasis laeuft als EINE Zeile mit, damit die Wirkung
vorher/nachher sichtbar ist. Er wird NICHT bewertet und NICHT optimiert -
der Nutzerhinweis dazu lautet *„Spot ist ohnehin falsch"*.

    python messe_hebel_dimension.py
    python messe_hebel_dimension.py --symbole 30      # Probelauf
    python messe_hebel_dimension.py --nur-a1          # nur die Basislinie
"""
from __future__ import annotations

import os
import sqlite3
import sys
from collections import defaultdict

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STUNDEN_DB = os.path.join("data", "stundenkurse.db")
TERMIN_DB = os.path.join("data", "terminmarkt_historie.db")
HALTEDAUERN = (6, 12, 24, 48, 72)
CRV = 2.0
ATR_FENSTER = 14
ATR_ANTEIL, STOP_MIN, STOP_MAX = 0.75, 0.05, 0.25     # Produktionsgeometrie
TAKT = 6                   # jede 6. Stunde ein Anker
MIND_FUENFTEL = 500        # weniger ist kein Fuenftel, sondern ein Einzelfall
NULLWELTEN = 200
SAAT = 20260924

# ⚠️ SECHS KANDIDATEN, JEDER MIT HYPOTHESE (Vorabfestlegung 10 Paragraf 4).
# `punkte` ist ausgeschlossen: Werte 9-12, Median 12 - ein
# Vollstaendigkeitsmass der Quelle, kein Marktmerkmal.
KANDIDATEN = (
    ("K1 oi-Aenderung 6h", "oi", "aenderung"),
    ("K2 taker_verh", "taker_verh", "niveau"),
    ("K3 taker_verh 6h", "taker_verh", "aenderung"),
    ("K4 top minus retail", "_top_minus", "niveau"),
    ("K5 konten_verh", "konten_verh", "niveau"),
    ("K6 Position je Konto", "_je_konto", "aenderung"),
    ("KON zufall", "_zufall", "niveau"),
)


def _lade_kurse(grenze=None) -> dict:
    c = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    syms = [r[0] for r in c.execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol "
        "HAVING COUNT(*) > 2000 ORDER BY COUNT(*) DESC")]
    if grenze:
        syms = syms[:grenze]
    aus = {}
    for s in syms:
        rows = c.execute("SELECT stunde, high, low, close FROM stundenkurse "
                         "WHERE symbol=? ORDER BY stunde", (s,)).fetchall()
        if len(rows) >= 500:
            aus[s] = rows
    c.close()
    return aus


def _lade_terminmarkt(syms: set) -> dict:
    """{symbol: {stunde: dict}} - die sechs Groessen, `punkte` weggelassen.

    ⚠️ DER FILTER STEHT IN SQL, NICHT IN PYTHON. Meine erste Fassung las
    ALLE 3,36 Mio Zeilen und verwarf sie danach - das kostete Minuten und
    den Speicher fuer die ganze Tabelle. Bei einem Probelauf ueber 15
    Symbole wurden 99 Prozent der gelesenen Zeilen weggeworfen.
    """
    c = sqlite3.connect("file:%s?mode=ro" % TERMIN_DB, uri=True)
    platz = ",".join("?" * len(syms))
    aus = defaultdict(dict)
    for sym, stunde, oi, oiw, tkv, tsv, kv, tv in c.execute(
            "SELECT symbol, stunde, oi, oi_wert, top_konten_verh, "
            "top_summe_verh, konten_verh, taker_verh FROM terminmarkt "
            "WHERE symbol IN (%s)" % platz, tuple(sorted(syms))):
        aus[sym][stunde] = {"oi": oi, "oi_wert": oiw, "top_konten_verh": tkv,
                            "top_summe_verh": tsv, "konten_verh": kv,
                            "taker_verh": tv}
    c.close()
    return aus


def _atr(stunde, hi, lo, cl):
    """Taeglicher ATR14 je Stunde - der ATR des VORTAGS, nie der laufende."""
    tag = np.array([s[:10] for s in stunde])
    gr = np.flatnonzero(np.r_[True, tag[1:] != tag[:-1]])
    t_hi = np.maximum.reduceat(hi, gr)
    t_lo = np.minimum.reduceat(lo, gr)
    t_cl = cl[np.r_[gr[1:] - 1, len(cl) - 1]]
    if len(t_hi) < ATR_FENSTER + 2:
        return None
    vor = np.r_[t_cl[0], t_cl[:-1]]
    tr = np.maximum(t_hi - t_lo, np.maximum(np.abs(t_hi - vor),
                                            np.abs(t_lo - vor)))
    a = np.full(len(tr), np.nan)
    lauf = np.cumsum(tr)
    a[ATR_FENSTER - 1:] = ((lauf[ATR_FENSTER - 1:]
                            - np.r_[0, lauf[:-ATR_FENSTER]]) / ATR_FENSTER)
    je = np.repeat(np.arange(len(gr)), np.diff(np.r_[gr, len(hi)]))
    return np.r_[np.nan, a[:-1]][je]


def _merkmal(tm_sym: dict, stunde: str, art: str, feld: str):
    """Ein Kandidatenwert - oder None, wenn die Datenlage fehlt."""
    jetzt = tm_sym.get(stunde)
    if not jetzt:
        return None
    if feld == "_zufall":
        return None                       # wird spaeter gezogen
    if feld == "_top_minus":
        a, b = jetzt.get("top_konten_verh"), jetzt.get("konten_verh")
        wert = (a - b) if (a is not None and b is not None) else None
    elif feld == "_je_konto":
        a, b = jetzt.get("oi_wert"), jetzt.get("oi")
        wert = (a / b) if (a and b) else None
    else:
        wert = jetzt.get(feld)
    if wert is None or art == "niveau":
        return wert
    # ⚠️ Aenderung ueber 6 h - RELATIV, damit Symbole vergleichbar sind
    from datetime import datetime, timedelta
    vor6 = (datetime.strptime(stunde, "%Y-%m-%d %H:%M")
            - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M")
    frueher = tm_sym.get(vor6)
    if not frueher:
        return None
    if feld == "_je_konto":
        a0, b0 = frueher.get("oi_wert"), frueher.get("oi")
        alt = (a0 / b0) if (a0 and b0) else None
    else:
        alt = frueher.get(feld)
    if alt is None or abs(alt) < 1e-12:
        return None
    return wert / alt - 1.0


def _barrieren(hi, lo, cl, atr, idx, h, skaliert):
    """ergebnis_r und Ausgang je Anker - die Zielgroesse aus Paragraf 2."""
    e = cl[idx]
    rel = np.clip(ATR_ANTEIL * atr[idx] / e, STOP_MIN, STOP_MAX)
    if skaliert:
        rel = rel * np.sqrt(h / 24.0)
    s = rel * e
    ziel, stop = e + CRV * s, e - s
    erst_z = np.full(len(idx), h, np.int32)
    erst_s = np.full(len(idx), h, np.int32)
    for t in range(1, h + 1):
        fh, fl = hi[idx + t], lo[idx + t]
        erst_z = np.where((erst_z == h) & (fh >= ziel), t, erst_z)
        erst_s = np.where((erst_s == h) & (fl <= stop), t, erst_s)
    traf_z, traf_s = erst_z < h, erst_s < h
    unklar = traf_z & traf_s & (erst_z == erst_s)
    ist_z = traf_z & ~unklar & (~traf_s | (erst_z < erst_s))
    ist_s = (traf_s & ~unklar & (~traf_z | (erst_s < erst_z))) | unklar
    offen = ~traf_z & ~traf_s
    # ⭐ DIE ZIELGROESSE: offen wird NICHT weggeworfen
    erg = np.where(ist_z, CRV, np.where(ist_s, -1.0, (cl[idx + h] - e) / s))
    return erg, ist_z, ist_s, offen, unklar


def _fuenftel_je_stunde(werte: dict) -> dict:
    """{stunde: {sym: 0..4}} - quer ueber die Symbole DERSELBEN Stunde.

    ⚠️ AUFSTEIGEND, Fuenftel 0 ist der niedrigste Rohwert - dieselbe
    Konvention wie `marktrang._fuenftel`. Wer sie dreht, dreht jeden
    Beitrag ins Gegenteil, ohne dass etwas anschlaegt.

    ⚠️⚠️ QUER UEBER DIE SYMBOLE, NICHT UEBER DIE ZEIT. Ein Rang ueber die
    eigene Historie waere eine andere Groesse - gemessen dreht das bei
    `schnitt` sogar das Vorzeichen (REGISTER_Kandidaten).
    """
    aus = {}
    for stunde, je_sym in werte.items():
        gut = [(s, w) for s, w in je_sym.items() if w is not None
               and np.isfinite(w)]
        if len(gut) < 8:              # unter acht ist es kein Querschnitt
            continue
        gut.sort(key=lambda x: x[1])
        n = len(gut) - 1
        aus[stunde] = {s: min(int((i / n) * 5), 4)
                       for i, (s, _w) in enumerate(gut)}
    return aus


def _wirkung(gesammelt: dict, fuenftel: int, stat=np.median) -> float:
    """stat(oberstes Fuenftel) - stat(alle), je Stunde geklammert.

    ⚠️ DIE STUNDENKLAMMER IST PFLICHT. Zu einer Stunde bewegt sich der
    ganze Markt gemeinsam; ungeklammert misst man die Marktbewegung und
    nennt sie Beitrag. Dieselbe Begruendung wie die Tagesklammer in
    `pruefe_n31_tagesklammer`.
    """
    diffs, gew = [], []
    for _stunde, (f, y) in gesammelt.items():
        m = f == fuenftel
        if m.sum() < 2 or (~m).sum() < 2:
            continue
        diffs.append(float(stat(y[m]) - stat(y)))
        gew.append(int(m.sum()))
    if len(diffs) < 30:
        return float("nan"), 0
    return float(np.average(diffs, weights=gew)), len(diffs)


def _nullpunkt(gesammelt: dict, fuenftel: int, rng) -> np.ndarray:
    """Der Nullpunkt - die Fuenftelzuordnung je Stunde GEMISCHT.

    ⚠️ Gemischt wird INNERHALB der Stunde. Das erhaelt die Marktbewegung
    und zerstoert nur die Zuordnung - genau das, was die Nullhypothese
    behauptet. 200 Welten (Messstandard 08.09.: ein Maximum ist kein
    Schaetzer, der Nullpunkt ist der MITTELWERT der Nullwelten; das
    90. Perzentil ist die ausgewiesene obere Grenze).
    """
    aus = []
    for _ in range(NULLWELTEN):
        diffs, gew = [], []
        for _stunde, (f, y) in gesammelt.items():
            fm = rng.permutation(f)
            m = fm == fuenftel
            if m.sum() < 2 or (~m).sum() < 2:
                continue
            diffs.append(float(np.median(y[m]) - np.median(y)))
            gew.append(int(m.sum()))
        if len(diffs) >= 30:
            aus.append(float(np.average(diffs, weights=gew)))
    return np.array(aus)


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    nur_a1 = "--nur-a1" in sys.argv
    rng = np.random.default_rng(SAAT)

    print("=" * 100)
    print("H-A: DIE HEBEL-DIMENSION AUF DER STUNDENBASIS")
    print("=" * 100)
    kurse = _lade_kurse(grenze)
    print("  %d Symbole · Takt %d h · CRV %.1f · LONG · nur Krypto"
          % (len(kurse), TAKT, CRV))
    print("  Kelly-Nullstelle 1/(1+CRV) = %.4f" % (1.0 / (1.0 + CRV)))

    # ───────────────────────────── A1 ─────────────────────────────────
    print()
    print("=" * 100)
    print("A1 - DIE BASISLINIE: wo liegt die Quote je Haltedauer und Stop?")
    print("=" * 100)
    gesammelt = {}          # (h, skaliert) -> {stunde: (fuenftel, erg)}
    a1 = {}
    for skaliert in (False, True):
        for h in HALTEDAUERN:
            erg_alle, z, s, o, u = [], 0, 0, 0, 0
            anker = {}
            for sym, rows in kurse.items():
                st = [r[0] for r in rows]
                hi = np.array([r[1] for r in rows], float)
                lo = np.array([r[2] for r in rows], float)
                cl = np.array([r[3] for r in rows], float)
                atr = _atr(st, hi, lo, cl)
                if atr is None:
                    continue
                idx = np.arange(0, len(cl) - h, TAKT)
                idx = idx[np.isfinite(atr[idx]) & (atr[idx] > 0)]
                if not len(idx):
                    continue
                e, iz, is_, io, iu = _barrieren(hi, lo, cl, atr, idx, h,
                                                skaliert)
                erg_alle.append(e)
                z += int(iz.sum()); s += int(is_.sum())
                o += int(io.sum()); u += int(iu.sum())
                for k, j in enumerate(idx):
                    anker.setdefault(st[j], []).append((sym, float(e[k])))
            if not erg_alle:
                continue
            ea = np.concatenate(erg_alle)
            n = len(ea)
            entschieden = z + s
            a1[(h, skaliert)] = {
                "n": n, "ziel": z, "stop": s, "offen": o, "unklar": u,
                "quote": z / max(1, entschieden),
                "median": float(np.median(ea)),
                "mittel": float(np.mean(ea))}
            gesammelt[(h, skaliert)] = anker
    for skaliert in (False, True):
        print()
        print("  STOP %s" % ("skaliert x sqrt(H/24)" if skaliert
                             else "PRODUKTION min(25%, max(5%, 0,75 x ATR))"))
        print("  %-5s %10s %7s %7s %7s  %9s  %10s %10s"
              % ("H", "Anker", "Ziel%", "Stop%", "offen%", "QUOTE",
                 "Median r", "Mittel r"))
        for h in HALTEDAUERN:
            d = a1.get((h, skaliert))
            if not d:
                continue
            m = "  ⚠️ unter Null" if d["quote"] < 1.0 / (1.0 + CRV) else "  ✔"
            print("  %-5s %10s %6.1f%% %6.1f%% %6.1f%%  %8.4f  %+10.4f %+10.4f%s"
                  % ("%dh" % h, f"{d['n']:,}".replace(",", "."),
                     100 * d["ziel"] / d["n"], 100 * d["stop"] / d["n"],
                     100 * d["offen"] / d["n"], d["quote"],
                     d["median"], d["mittel"], m))
    print()
    print("  ⚠️ QUOTE = Ziel / (Ziel + Stop) - die BEDINGTE Trefferquote, aus")
    print("     der `q` entsteht. Median/Mittel sind `ergebnis_r` UEBER ALLE")
    print("     Anker, also MIT den offenen - das ist die neue Zielgroesse.")
    if nur_a1:
        return 0

    # ───────────────────────────── A2 ─────────────────────────────────
    print()
    print("=" * 100)
    print("A2 - DIE KANDIDATEN: welche Groesse trennt, auf welcher Haltedauer?")
    print("=" * 100)
    print("  Terminmarkt laden...", flush=True)
    tm = _lade_terminmarkt(set(kurse))
    print("  %d Symbole mit stuendlichen Merkmalen" % len(tm), flush=True)

    treffer, geprueft = [], 0
    for name, feld, art in KANDIDATEN:
        print()
        print("  ── %s (%s, %s) %s" % (name, feld, art, "─" * 40),
              flush=True)
        for h in HALTEDAUERN:
            anker = gesammelt.get((h, False)) or {}
            werte = {}
            for stunde, liste in anker.items():
                je = {}
                for sym, _e in liste:
                    w = (float(rng.random()) if feld == "_zufall"
                         else _merkmal(tm.get(sym) or {}, stunde, art, feld))
                    if w is not None and np.isfinite(w):
                        je[sym] = w
                if len(je) >= 8:
                    werte[stunde] = je
            f5 = _fuenftel_je_stunde(werte)
            samml = {}
            for stunde, liste in anker.items():
                zu = f5.get(stunde)
                if not zu:
                    continue
                paare = [(zu[s], e) for s, e in liste if s in zu]
                if len(paare) >= 4:
                    samml[stunde] = (np.array([p[0] for p in paare]),
                                     np.array([p[1] for p in paare], float))
            if len(samml) < 30:
                print("     %-5s  zu duenn (%d Stunden)" % ("%dh" % h, len(samml)))
                continue
            geprueft += 1
            w, ns = _wirkung(samml, 4)
            null = _nullpunkt(samml, 4, rng)
            if not len(null) or not np.isfinite(w):
                print("     %-5s  kein Nullpunkt" % ("%dh" % h))
                continue
            p90 = float(np.percentile(null, 90))
            traegt = w > p90
            if traegt:
                treffer.append((name, h, w, p90))
            print("     %-5s  Fuenftel 4: %+.4f R   Nullpunkt %+.4f "
                  "(90. Perz %+.4f)   %s   %d Stunden"
                  % ("%dh" % h, w, float(null.mean()), p90,
                     "TRAEGT" if traegt else "traegt nicht", ns), flush=True)

    # ---- der Suchpreis, vorab festgelegt -------------------------------
    print()
    print("=" * 100)
    print("DER SUCHPREIS - Paragraf 4.1 der Vorabfestlegung")
    print("=" * 100)
    erwartet = 0.10 * geprueft
    print("  %d Zellen geprueft · bei 10 %% Fehlerrate erwartet: %.1f Treffer"
          % (geprueft, erwartet))
    print("  tatsaechlich: %d" % len(treffer))
    for name, h, w, p90 in treffer:
        print("     %-22s %3dh   %+.4f gegen %+.4f" % (name, h, w, p90))
    print()
    if not treffer:
        print("  ⛔ KEIN Kandidat traegt.")
    elif len(treffer) <= erwartet:
        print("  ⚠️ Die Trefferzahl liegt NICHT ueber der Zufallserwartung -")
        print("     nach Paragraf 4.1 ist das KEIN Befund.")
    else:
        nach_name = defaultdict(list)
        for name, h, _w, _p in treffer:
            nach_name[name].append(h)
        mehr = {k: v for k, v in nach_name.items() if len(v) >= 2}
        print("  ⚠️ Die FORM zaehlt: ein echter Effekt zeigt sich ueber")
        print("     BENACHBARTE Haltedauern, nicht in einer einzelnen Zelle.")
        print("  Kandidaten mit mehr als einer Haltedauer: %s"
              % (dict(mehr) or "KEINER - das ist die Signatur von Zufall"))
    print()
    print("  ⚠️ `KON zufall` darf NICHT tragen - sonst ist der Lauf ungueltig.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
