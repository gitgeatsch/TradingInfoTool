# -*- coding: utf-8 -*-
"""Messung 1 des Regelwerks: die drei registrierten Traeger auf BEWERTUNG 1.

**27.09.2026** · `Basisinfos/Regelwerk_Hebel_Bewertung_27_09.md`, Punkt 5.1

═══════════════════════════════════════════════════════════════════════
 ⛔ WARUM ES DIESE MESSUNG GIBT
═══════════════════════════════════════════════════════════════════════

Nutzerkritik 27.09.: *"Was ist mit turnover und funding, diese waren
bereits gesetzt oder? Du hast recherchiert und noch immer keine Ahnung
zum Einstieg und den Merkmalen."*

An EINEM Tag habe ich zehn KURSmerkmale gemessen und die drei einzigen
registrierten Traeger des Systems kein einziges Mal geladen. Sie sind auf
**H20 gegen `bewegung_r`** registriert - der Spot-Lage. Auf BEWERTUNG 1
(*kommt eine Bewegung nach oben?*) sind sie UNGEMESSEN.

═══════════════════════════════════════════════════════════════════════
 DREI NUTZERKORREKTUREN, DIE IM BAU STECKEN
═══════════════════════════════════════════════════════════════════════

    1  ZIELGROESSE MESSEN, NICHT ANNEHMEN
       *"Zur Zielgroesse - hast du diese gemessen oder angenommen?"*
       +15 %/6 h war ANGENOMMEN (aus 2.594 uebernommen). Teil 0 misst
       jetzt die HAEUFIGKEIT jeder Kombination aus Hoehe und Fenster -
       das ist die Zahl, die ueber die Brauchbarkeit entscheidet.

    2  KARENZ IST EINE ACHSE, KEIN FILTER
       *"bin mir nicht sicher, ob du dies nur fuer die Messung als
       Annahme siehst oder wir gute Signale kappen."*
       ⭐ k=0 IST DER BETRIEBSFALL - im Betrieb steigt man sofort ein.
       k>0 ist DIAGNOSE: sagt das Merkmal vorher oder begleitet es nur?
       Beide Zahlen werden ausgewiesen, keine kappt die andere.

    3  MEHR ALS 24 STUNDEN ZULASSEN
       *"Trades koennen kuerzer oder laenger laufen - erst die
       Positionsfuehrung ist nach einem Einstieg relevant. Gestern hast
       du 24 h als Optimum angesehen - aber das musst du selbst
       nachpruefen."*
       Das Fenster ist eine ACHSE bis 120 Stunden, keine Festlegung.

═══════════════════════════════════════════════════════════════════════
 DIE DREI GRUPPEN - sauber getrennt
═══════════════════════════════════════════════════════════════════════

    A  REGISTRIERTE TRAEGER   funding · turnover · oi_aenderung
                              Die einzigen drei, die je getragen haben.
    B  TERMINMARKT-NEBEN      taker_verh · konten_verh · top_konten_verh
                              In 2.594 als *nur Bewegung* eingestuft,
                              aber nie mit Karenz und nie je Asset.
    C  KONTROLLE              volumenschub · zufall
                              `zufall` MUSS im Nullband liegen.

⚠️⚠️ TURNOVER HAT NUR EIN JAHR HISTORIE. `umlaufmenge_cg.db` reicht von
2025-09-21 bis 2026-09-22. Die registrierte Form (Volumen je Umlaufmenge)
ist damit ueber fuenf Jahre NICHT messbar; `volumenschub` (Volumen gegen
den eigenen Median) laeuft als assetintern normierte Schwestergroesse mit
und ist NICHT dasselbe.

⚠️ MODUS: `messen`. Keine Kalibrierung, keine Hebelhoehe.
⚠️ NUR LESEN.  python messe_traeger_auf_bewertung1.py [--symbole N]
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from hebel_neubau import pruefe_quellen                         # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_hebel_neudimension import VORLAUF                    # noqa: E402

# --funding-vortag (Probe 2.652): funding als Tagessumme des Vortags
VORTAG = False

# ⚠️ Der Riegel: die ROHGROESSEN sind frei (E-3), die alten
# Beitragsstufen nicht. `funding_fuenftel` wuerde hier abbrechen.
pruefe_quellen("funding", "turnover", "oi_aenderung", "taker_verh",
               "konten_verh", "top_konten_verh", "volumenschub")

# ⚠⚠⚠ NACH ABDECKUNG GRUPPIERT, NICHT NACH HERKUNFT - Nutzervorgabe
# 27.09.2026: *"DU brauchst jetzt die gesamten Beitraege - lade diese nach
# [...] ICH brauche eine grosse ABDECKUNG in der Produktion."*
#
# ⭐ DIE BESTANDSAUFNAHME, die das erzwungen hat (alle 116 Kurssymbole):
#
#     funding           116 Symbole · 2019-09 bis 2026-08 · taeglich
#     terminmarkt       116 Symbole · 2021-12 bis 2026-09 · STUENDLICH
#     umlaufmenge_cg    113 Symbole · NUR EIN JAHR
#     markt.turnover     48 Symbole · nur ein Jahr
#     onchain.splycur    17 Symbole · 13 Jahre
#     tvl                36 Symbole · 8 Jahre
#
# ⛔ `turnover` IST STRUKTURELL NICHT ZU RETTEN: keine Quelle gibt
# gleichzeitig hohe Abdeckung UND lange Historie. Er laeuft mit, aber in
# einer eigenen Gruppe und mit ausgewiesener Menge.
#
# ⭐⭐ DIE REGEL, DIE DARAUS FOLGT: volle Abdeckung haben nur Merkmale
# ohne EXTERNE Quelle - assetintern aus Kurs und Volumen - plus funding
# und Terminmarkt, weil die aus derselben Boerse kommen wie die Kurse.
GRUPPEN = {
    "A volle Abdeckung": ("funding", "oi_aenderung", "oi_je_umsatz",
                          "volumenschub"),
    "B Terminmarkt weitere": ("taker_verh", "konten_verh",
                              "top_konten_verh", "top_summe_verh"),
    "C eingeschraenkte Menge": ("turnover",),
    "D Kontrolle": ("zufall",),
}
ALLE = tuple(n for g in GRUPPEN.values() for n in g)

HOEHEN = (0.10, 0.15, 0.20, 0.30)
FENSTER = (6, 12, 24, 48, 72, 120)
# ⚠⚠ NUR ZWEI KARENZEN - UND DAS IST EINE SPEICHERGRENZE, KEINE
# METHODENENTSCHEIDUNG. Die erste Fassung fuehrte vier Karenzen x 24
# Zielgroessen x 2 Richtungen = 192 Arrays zu je 3,2 Mio Eintraegen und
# ist mit `Unable to allocate` abgebrochen.
# ⭐ Die beiden, die das URTEIL tragen, bleiben: k=0 ist der
# BETRIEBSFALL, k=24 beantwortet *sagt es vorher oder begleitet es*.
# Die Zwischenstufen waren Diagnose und sind verzichtbar.
KARENZEN = (0, 24)
# ⚠️ Brauchbar heisst: haeufig genug fuer eine Messung, selten genug fuer
# ein Geschaeft. 2.594 hat +20 %/3 h mit 0,087 % als ZU SELTEN verworfen.
HAEUFIG_MIN, HAEUFIG_MAX = 0.002, 0.08

# ⭐⭐ DIE VIER ZIELGROESSEN, AUF DENEN GEMESSEN WIRD - und die Wahl
# ist BEGRUENDET, nicht bequem: je Hoehe das Fenster, dessen Haeufigkeit
# am naechsten bei 1,5 Prozent liegt. Gemessen in Teil 0:
#
#     +10 %/H6   1,415 %      +20 %/H24  1,597 %
#     +15 %/H12  1,296 %      +30 %/H48  1,498 %
#
# ⚠ BEI GLEICHER HAEUFIGKEIT SIND DIE LIFTS DIREKT VERGLEICHBAR. Wer
# unterschiedlich seltene Ereignisse nebeneinanderstellt, vergleicht die
# Seltenheit mit. Und die volle Landkarte steht trotzdem in Teil 0.
#
# ⚠⚠ Es ist zugleich eine SPEICHERgrenze: alle 16 brauchbaren
# Zielgroessen x 2 Karenzen x 40 Merkmalszellen haben die erste Fassung
# mit `Unable to allocate` abgebrochen.
ZIELE = ((0.10, 6), (0.15, 12), (0.20, 24), (0.30, 48))
ZIEHUNGEN = 40
SAAT = 20260927
MIN_TREFFER, MIN_SYMBOLE, MIN_EREIGNISSE = 30, 20, 10
SPIEGEL = 1.717       # geeicht in 2.603


def lade_funding():
    c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
    aus = {}
    for sym, datum, wert in c.execute(
            "SELECT symbol, datum, wert FROM funding WHERE wert IS NOT NULL"):
        aus.setdefault(sym, {})[str(datum)[:10]] = float(wert)
    c.close()
    return aus


def lade_umlauf():
    c = sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True)
    aus = {}
    for sym, datum, wert in c.execute(
            "SELECT symbol, datum, wert FROM umlaufmenge "
            "WHERE wert IS NOT NULL AND wert > 0"):
        aus.setdefault(sym, {})[str(datum)[:10]] = float(wert)
    c.close()
    return aus


def termin_verbindung():
    """Eine offene Nur-Lese-Verbindung zum Terminmarkt.

    ⚠⚠⚠ JE SYMBOL LADEN, NICHT ALLES - DAS WAR DER SPEICHERFEHLER.
    Die erste Fassung baute ein Dict mit 3,3 MILLIONEN String-Schluesseln
    und 6-Tupeln. Ein Python-Dict dieser Groesse belegt ueber ein
    Gigabyte, und der Lauf brach mit `Unable to allocate` bei einem
    Array von DREI MEGABYTE ab - der Speicher war laengst weg.

    ⭐ Die Daten werden ohnehin SYMBOLWEISE verarbeitet. Sie alle
    gleichzeitig zu halten, hatte nie einen Grund.
    """
    return sqlite3.connect(
        "file:data/terminmarkt_historie.db?mode=ro", uri=True)


def termin_symbol(c, sym):
    """-> {stunde: (oi, oi_wert, taker, konten, top, top_summe)} fuer EIN Symbol."""
    return {str(r[0]): r[1:] for r in c.execute(
        "SELECT stunde, oi, oi_wert, taker_verh, konten_verh, "
        "top_konten_verh, top_summe_verh FROM terminmarkt WHERE symbol=?",
        (sym,))}


def ereignisse_alle(h, l, cc, hoehen, fenster, karenz):
    """-> {(hoehe, fenster): bool-Array} und dasselbe nach unten.

    ⭐ EINE Schleife bis zum laengsten Fenster, mit Zwischenstaenden -
    statt einer Schleife je Fenster. Bei sechs Fenstern bis 120 h spart
    das den Faktor 5 an Rechenzeit.
    """
    n = len(cc)
    idx = np.arange(n)
    hoch = np.full(n, -np.inf)
    tief = np.full(n, np.inf)
    auf, ab = {}, {}
    for s in range(karenz + 1, karenz + max(fenster) + 1):
        j = np.minimum(idx + s, n - 1)
        hoch = np.maximum(hoch, h[j])
        tief = np.minimum(tief, l[j])
        f = s - karenz
        if f in fenster:
            with np.errstate(divide="ignore", invalid="ignore"):
                rh = hoch / np.maximum(cc, 1e-12) - 1.0
                rt = tief / np.maximum(cc, 1e-12) - 1.0
            for ho in hoehen:
                auf[(ho, f)] = rh >= ho
                ab[(ho, f)] = rt <= -ho
    return auf, ab


def _lift(treffer, ereig, si, n_sym):
    lifte, gew = [], []
    for i in range(n_sym):
        m = si == i
        t = m & treffer
        k = int(t.sum())
        if k < MIN_TREFFER:
            continue
        basis = float(ereig[m].mean())
        if basis <= 0:
            continue
        lifte.append(float(ereig[t].mean()) / basis)
        gew.append(k)
    if not lifte:
        return np.nan, np.nan, 0
    lifte, gew = np.array(lifte), np.array(gew, float)
    return (float((lifte * gew).sum() / gew.sum()),
            100.0 * float((lifte > 1.0).mean()), len(lifte))


def main() -> int:
    grenze = (int(sys.argv[sys.argv.index("--symbole") + 1])
              if "--symbole" in sys.argv else None)
    global VORTAG
    VORTAG = "--funding-vortag" in sys.argv
    print("=" * 108)
    print("MESSUNG 1 - DIE DREI REGISTRIERTEN TRAEGER AUF BEWERTUNG 1")
    print("=" * 108)
    print("  " + N.standardzeile())
    print("  ⚠️ MODUS: messen. Keine Kalibrierung, keine Hebelhoehe.")
    print("  ⚠️ Bewertung 1 = *kommt eine Bewegung nach oben?* ·")
    print("     Zielgroesse EREIGNIS, Bezug das EIGENE Symbol (Lift)")
    print("  ⚠️ Ohne Gebuehren und Finanzierung (Regel 2)")
    if VORTAG:
        print("  ⭐ PROBE 2.652: funding = Tagessumme des VORTAGS "
              "(--funding-vortag)")
    print()

    kurse = lade_kurse(grenze)
    syms = {s for s in kurse if s.upper() != "BTC"}
    print("  lade funding …", flush=True)
    FU = lade_funding()
    print("  lade umlaufmenge …", flush=True)
    UM = lade_umlauf()
    tmc = termin_verbindung()
    print("  geladen: funding %d · umlauf %d Symbole · terminmarkt wird"
          % (len(FU), len(UM)), flush=True)
    print("  JE SYMBOL nachgeladen (sonst > 1 GB im Speicher)", flush=True)
    print()

    alle_st = set()
    for (s, *_r) in kurse.values():
        alle_st.update(s)
    sl = sorted(alle_st)
    sid = {s: i for i, s in enumerate(sl)}
    _, tag_je_i = np.unique(np.array([x[:10] for x in sl]),
                            return_inverse=True)
    jahr_je_i = np.array([int(x[:4]) for x in sl], np.int64)

    rng = np.random.default_rng(SAAT)
    G, SI, namen = [], [], []
    MM = {k: [] for k in ALLE}
    EVA = {k: {} for k in KARENZEN}
    EVB = {k: {} for k in KARENZEN}
    for sym, (st, h, l, cc, vol) in kurse.items():
        if sym.upper() == "BTC":
            continue
        n = len(cc)
        atr = atr_tag_relativ(h, l, cc)
        tage = [str(x)[:10] for x in st]
        if VORTAG:
            # 2.652-vorgriff-funding: die Tagessumme des VORTAGS - zu jeder
            # Stunde des Tages d vollstaendig abgerechnet und bekannt
            fu = np.array([FU.get(sym, {}).get(
                (datetime.strptime(d, "%Y-%m-%d") - timedelta(days=1))
                .strftime("%Y-%m-%d"), np.nan) for d in tage])
        else:
            fu = np.array([FU.get(sym, {}).get(d, np.nan) for d in tage])
        um = np.array([UM.get(sym, {}).get(d, np.nan) for d in tage])
        tmm = termin_symbol(tmc, sym)
        L = (np.nan,) * 6
        oi = np.array([(tmm.get(str(x), L)[0] or np.nan) for x in st], float)
        oiw = np.array([(tmm.get(str(x), L)[1] or np.nan) for x in st], float)
        tk = np.array([(tmm.get(str(x), L)[2] or np.nan) for x in st], float)
        kv = np.array([(tmm.get(str(x), L)[3] or np.nan) for x in st], float)
        tkv = np.array([(tmm.get(str(x), L)[4] or np.nan) for x in st], float)
        tsv = np.array([(tmm.get(str(x), L)[5] or np.nan) for x in st], float)
        with np.errstate(divide="ignore", invalid="ignore"):
            # oi_aenderung: relative Aenderung des Open Interest ueber 24 h
            oi24 = np.concatenate([np.full(24, np.nan), oi[:-24]])
            oi_ae = oi / np.maximum(oi24, 1e-12) - 1.0
            # turnover: Stundenvolumen je freiem Umlauf
            turn = vol / np.maximum(um, 1e-12)
            # volumenschub: Volumen gegen den eigenen 7-Tage-Median
            k7 = 168
            vs = np.full(n, np.nan)
            if n > k7:
                # gleitender Median ist teuer - gleitendes MITTEL genuegt
                # als Bezug, und es ist assetintern
                # ⚠ `cs` hat n+1 Eintraege - das gleitende Mittel der
                # Fenster, die bei k7 ENDEN, ist cs[k7:] - cs[:-k7] und
                # hat n+1-k7 Werte. Es gehoert auf die Positionen
                # k7-1 .. n-1, nicht k7 .. n.
                cs = np.concatenate([[0.0], np.cumsum(np.nan_to_num(vol))])
                mit = (cs[k7:] - cs[:-k7]) / k7          # n+1-k7 Werte
                vs[k7 - 1:] = vol[k7 - 1:] / np.maximum(mit, 1e-12)
        with np.errstate(divide="ignore", invalid="ignore"):
            # ⭐ oi_je_umsatz: wieviel offene Position steht je Einheit
            # Stundenumsatz? Assetintern, volle Abdeckung - `oi_wert` und
            # Volumen sind beide zu 100 Prozent gefuellt.
            umsatz = np.maximum(vol * cc, 1e-12)
            oi_ju = oiw / umsatz
        werte = {"funding": fu, "turnover": turn, "oi_aenderung": oi_ae,
                 "oi_je_umsatz": oi_ju, "taker_verh": tk,
                 "konten_verh": kv, "top_konten_verh": tkv,
                 "top_summe_verh": tsv, "volumenschub": vs,
                 "zufall": rng.standard_normal(n)}
        gu = np.isfinite(atr) & (atr > 0)
        gu[:VORLAUF] = False
        gu[-(max(KARENZEN) + max(FENSTER) + 1):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        namen.append(sym)
        G.append(np.array([sid[x] for x in st], np.int64)[s2])
        SI.append(np.full(len(s2), len(namen) - 1, np.int64))
        for k in ALLE:
            # ⚠ float32 halbiert 254 MB auf 127 - die Merkmale
            # brauchen keine 15 Stellen
            MM[k].append(np.asarray(werte[k][s2], np.float32))
        for kar in KARENZEN:
            auf, ab = ereignisse_alle(h, l, cc, HOEHEN, FENSTER, kar)
            for schl in auf:
                if kar != 0 and schl not in ZIELE:
                    continue        # Speicher: k>0 nur fuer die ZIELE
                EVA[kar].setdefault(schl, []).append(auf[schl][s2])
                # ⚠ Die Gegenrichtung braucht nur die Spiegelprobe, und
                # die laeuft auf k=0. Sie fuer jede Karenz zu halten war
                # die Haelfte des Speichers - fuer nichts.
                if kar == 0 and schl in ZIELE:
                    EVB[kar].setdefault(schl, []).append(ab[schl][s2])
    G = np.concatenate(G)
    SI = np.concatenate(SI)
    MM = {k: np.concatenate(v) for k, v in MM.items()}
    tmc.close()
    del kurse, FU, UM
    import gc; gc.collect()
    for kar in KARENZEN:
        EVA[kar] = {k: np.concatenate(v) for k, v in EVA[kar].items()}
        EVB[kar] = {k: np.concatenate(v) for k, v in EVB[kar].items()}
    tag, jahr = tag_je_i[G], jahr_je_i[G]
    print("  %d Anker · %d Tage · %d Symbole"
          % (len(G), len(np.unique(tag)), len(namen)), flush=True)
    print()
    print("  ABDECKUNG je Merkmal (Anteil mit Wert):")
    for gname, mer in GRUPPEN.items():
        for k in mer:
            print("    %-18s %-22s %6.1f %%"
                  % (gname if k == mer[0] else "", k,
                     100.0 * float(np.isfinite(MM[k]).mean())))
    print()

    # ══ TEIL 0: DIE ZIELGROESSEN-LANDKARTE ═══════════════════════════
    print("=" * 108)
    print("TEIL 0 - DIE ZIELGROESSE WIRD GEMESSEN, NICHT ANGENOMMEN")
    print("  Nutzerfrage: *hast du diese gemessen oder angenommen?* -")
    print("  angenommen. Hier die HAEUFIGKEIT jeder Kombination.")
    print("  ⭐ Brauchbar = haeufig genug fuer eine Messung (>%.1f %%),"
          % (100 * HAEUFIG_MIN))
    print("     selten genug fuer ein Geschaeft (<%.0f %%)."
          % (100 * HAEUFIG_MAX))
    print()
    print("  %8s %s" % ("Hoehe", " ".join("%10s" % ("H%d" % f)
                                          for f in FENSTER)))
    brauchbar = []
    for ho in HOEHEN:
        zeile = []
        for f in FENSTER:
            p = float(EVA[0][(ho, f)].mean())
            zeile.append(p)
            if HAEUFIG_MIN <= p <= HAEUFIG_MAX:
                brauchbar.append((ho, f))
        print("  %7.0f%% %s" % (100 * ho,
                                " ".join("%9.3f%%" % (100 * p)
                                         for p in zeile)))
    print()
    print("  ➤ %d brauchbare Zielgroessen: %s"
          % (len(brauchbar),
             ", ".join("+%.0f%%/H%d" % (100 * a, b) for a, b in brauchbar)))
    print()
    print("  ⭐ GEMESSEN WIRD AUF VIER DAVON - je Hoehe das Fenster mit")
    print("     der Haeufigkeit naechst 1,5 %%: %s"
          % ", ".join("+%.0f%%/H%d (%.3f %%)"
                      % (100 * a, b, 100 * float(EVA[0][(a, b)].mean()))
                      for a, b in ZIELE))
    print("     ⚠ Bei GLEICHER Haeufigkeit sind die Lifts vergleichbar.")
    brauchbar = list(ZIELE)
    # ⚠ Teil 0 brauchte ALLE 24 Kombinationen, Teil 1 nur die vier ZIELE.
    # Die uebrigen belegen 64 MB; die Haeufigkeiten stehen oben schon.
    for _schl in [x for x in EVA[0] if x not in ZIELE]:
        del EVA[0][_schl]
    import gc as _gc
    _gc.collect()
    if not brauchbar:
        print("  ⛔ KEINE - die Grenzen sind falsch gesetzt oder die Daten")
        print("     geben die Frage nicht her.")
        return 1
    print()

    # ══ TEIL 1: DIE MERKMALE, je Zielgroesse und Karenz ══════════════
    print("=" * 108)
    print("TEIL 1 - DIE MERKMALE auf den brauchbaren Zielgroessen")
    print("  ⭐ k=0 ist der BETRIEBSFALL (man steigt sofort ein).")
    print("     k>0 ist DIAGNOSE: sagt das Merkmal VORHER oder begleitet es?")
    print("  ⚠️ Beide Zahlen werden ausgewiesen - keine kappt die andere.")
    print()
    # Schwellen: absolut, aus den eigenen Perzentilen des Merkmals
    schwellen = {}
    for k in ALLE:
        W = MM[k]
        if not np.isfinite(W).any():
            continue
        q = np.nanpercentile(W, [1, 5, 95, 99])
        schwellen[k] = [("<=", q[0]), ("<=", q[1]),
                        (">=", q[2]), (">=", q[3])]
    zellen = [(k, op, sw) for k in ALLE if k in schwellen
              for op, sw in schwellen[k]]
    print("  %d Merkmale x %d Schwellen x %d Zielgroessen = %d Zellen"
          % (len(schwellen), 4, len(brauchbar),
             len(zellen) * len(brauchbar)))
    print("  ⚠️ Das Mehrfachtesten zaehlt gegen ALLE davon.")
    print()

    # Bestes-von-N-Band, tagestreu, ueber alle Zellen UND Zielgroessen
    o = np.argsort(tag, kind="stable")
    gr = np.flatnonzero(np.diff(tag[o])) + 1
    bloecke = np.split(np.arange(len(tag)), gr)
    masken = [((MM[k] >= sw) if op == ">=" else (MM[k] <= sw))
              & np.isfinite(MM[k]) for (k, op, sw) in zellen]
    # ⚠⚠ DIE SORTIERUNG EINMAL, NICHT JE ZIEHUNG. `EVA[0][schl][o]`
    # erzeugte bei jeder der 40 Ziehungen und jeder Zielgroesse ein neues
    # temporaeres Array - 320 Stueck, und der Speicher fragmentierte, bis
    # eine Anforderung von DREI Megabyte scheiterte.
    ev_sort = {schl: EVA[0][schl][o] for schl in brauchbar}
    m_sort = [m[o] for m in masken]
    maxima = []
    for _z in range(ZIEHUNGEN):
        # ⚠ int32 genuegt fuer 3,2 Mio Indizes und halbiert den Bedarf
        perm = np.arange(len(tag), dtype=np.int32)
        for b in bloecke:
            perm[b] = rng.permutation(b)
        beste = 0.0
        for schl in brauchbar:
            ev_p = ev_sort[schl][perm]
            basis = float(ev_p.mean())
            if basis <= 0:
                continue
            for ms in m_sort:
                if not ms.any():
                    continue
                beste = max(beste, float(ev_p[ms].mean()) / basis)
        maxima.append(beste)
    del ev_sort, m_sort
    import gc as _gc2
    _gc2.collect()
    band = float(np.percentile(maxima, 90))
    print("  ➤ Bestes-von-%d-Band (tagestreu, %d Ziehungen): %.4f"
          % (len(zellen) * len(brauchbar), ZIEHUNGEN, band))
    print()

    treffer = []
    for schl in brauchbar:
        ho, f = schl
        print("  ── Zielgroesse +%.0f %% in %d h (Haeufigkeit %.3f %%)"
              % (100 * ho, f, 100 * float(EVA[0][schl].mean())))
        print("     %-18s %10s %8s %9s %8s %8s  %s"
              % ("Merkmal", "Schwelle", "Symbole", "Lift k=0", "Spiegel",
                 "k=24/k0", "Urteil"))
        for i, (k, op, sw) in enumerate(zellen):
            m = masken[i]
            lf0, pos, nsym = _lift(m, EVA[0][schl], SI, len(namen))
            if nsym < MIN_SYMBOLE or not np.isfinite(lf0):
                continue
            lf_ab, _p, _n = _lift(m, EVB[0][schl], SI, len(namen))
            sp = (lf0 / lf_ab) if lf_ab and lf_ab > 0 else np.nan
            lf24, _p2, n24 = _lift(m, EVA[24].get(schl, EVA[0][schl]),
                                   SI, len(namen))
            halte = (lf24 / lf0) if lf0 > 0 and np.isfinite(lf24) else np.nan
            hoch = bool(sp and sp >= SPIEGEL)
            gut = bool(lf0 > band and pos >= 60.0 and hoch)
            if gut:
                treffer.append((schl, k, op, sw, m, lf0, pos, sp, halte))
            if gut or lf0 > band:
                print("     %-18s %s%9.4f %8d %9.3f %8.3f %8.2f  %s"
                      % (k, op, sw, nsym, lf0, sp,
                         halte if np.isfinite(halte) else float("nan"),
                         "✔" if gut else
                         "⛔ Richtung RUNTER" if sp and sp > 0
                         and 1 / sp >= SPIEGEL else "⚠ nur Bewegung"))
        print()
    print("  ➤ %d Zellen ueberleben Nullband, Mehrfachtesten, Richtung "
          "und je-Asset" % len(treffer))
    print()

    # ══ TEIL 2: ZEITSTABILITAET UND WEGLASSPROBE ═════════════════════
    print("=" * 108)
    print("TEIL 2 - ZEITSTABILITAET UND WEGLASSPROBE fuer die %d Treffer"
          % len(treffer))
    print()
    if not treffer:
        print("  ⛔ Nichts zu pruefen.")
    js = np.unique(jahr)
    gehalten = []
    for (schl, k, op, sw, m, lf0, pos, sp, halte) in treffer:
        ev = EVA[0][schl]
        print("  %s %s %.4f auf +%.0f %%/H%d  (Lift %.3f · Spiegel %.3f · "
              "k24/k0 %.2f)" % (k, op, sw, 100 * schl[0], schl[1], lf0, sp,
                                halte))
        zs = ges = 0
        for j in js:
            jm = jahr == j
            n_j = int((jm & m).sum())
            b_ = float(ev[jm].mean()) if jm.any() else 0.0
            if b_ <= 0 or not n_j:
                continue
            erw = n_j * b_
            l_j = float(ev[jm & m].mean()) / b_
            if erw < MIN_EREIGNISSE:
                print("      %d  %7d Anker  Lift %8.3f  zu duenn (%.1f "
                      "erwartete Ereignisse)" % (j, n_j, l_j, erw))
                continue
            ges += 1
            zs += l_j > 1.0
            print("      %d  %7d Anker  Lift %8.3f  %s"
                  % (j, n_j, l_j, "✔" if l_j > 1.0 else "⛔"))
        wl = wges = 0
        for j in list(js) + [None]:
            keep = np.ones(len(ev), bool) if j is None else (jahr != j)
            b_ = float(ev[keep].mean())
            if b_ <= 0 or not (keep & m).any():
                continue
            wges += 1
            wl += (float(ev[keep & m].mean()) / b_) > 1.0
        ok = bool(ges and zs == ges and wl == wges)
        if ok:
            gehalten.append((schl, k, op, sw, lf0, halte))
        print("      ➤ Zeitstabil %d von %d · Weglassprobe %d von %d  %s"
              % (zs, ges, wl, wges,
                 "✔ ALLE SECHS PRUEFUNGEN" if ok else "⛔ faellt"))
        print()

    print("=" * 108)
    print("ERGEBNIS: %d Zellen halten alle sechs Pruefungen" % len(gehalten))
    for (schl, k, op, sw, lf0, halte) in gehalten:
        gruppe = next(g for g, mer in GRUPPEN.items() if k in mer)
        print("  ✔ %-22s %-16s %s%9.4f  auf +%.0f %%/H%d  Lift %.3f  "
              "Vorlauf %s"
              % (gruppe, k, op, sw, 100 * schl[0], schl[1], lf0,
                 "JA (k24/k0 %.2f)" % halte if halte >= 0.8
                 else "nein (%.2f) - begleitet, sagt nicht vorher" % halte))
    print("=" * 108)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
