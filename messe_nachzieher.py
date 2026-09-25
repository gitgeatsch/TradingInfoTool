# -*- coding: utf-8 -*-
"""Der Nachzieher: welches Asset hat auf BTC noch nicht reagiert?

**Nutzervorgabe 25.09.2026, woertlich:**

    *"ja btc steigt alts ziehen verzoegert nach ABER NICHT ALLE GLEICHZEITIG
    das muss das system ueber die OPTIMALE LAGE DES ASSETS bewerten."*

    *"du sollst nicht das system oder den Markt messen sondern wir muessen
    BEITRAEGE FINDEN DIE FUER EINZELNE ASSETS GENUTZT WERDEN."*

**Vorabfestlegung 18** ist VOR dieser Messung geschrieben.

═══════════════════════════════════════════════════════════════════════
 ⭐⭐⭐ WAS DIESE MESSUNG VON 2.599 UNTERSCHEIDET
═══════════════════════════════════════════════════════════════════════

2.599 mass einen MARKTZUSTAND (*steigt BTC?*) - eine Zahl, die zu jeder
Stunde fuer ALLE 116 Assets DIESELBE ist. So etwas kann per Konstruktion
kein Asset vom anderen unterscheiden und ist nie ein Beitrag.

Hier ist das Merkmal der RUECKSTAND eines Assets: zur selben Stunde hat
jedes Asset einen ANDEREN Wert.

    2.599                        hier
    ---------------------------  -----------------------------------
    ein Wert je Stunde           116 Werte je Stunde
    Niveaufrage                  QUERSCHNITTsfrage
    Stundenklammer unmoeglich    Stundenklammer moeglich
    6-10 Regimewechsel           Asset-Stunden, also Millionen

⚠️⚠️ **Und genau das loest das Datenmengenproblem, an dem 2.599 scheiterte.**
Die Grenze *die effektive Stichprobe ist die Zahl der Regimewechsel* gilt
NUR fuer Marktzustaende. Ein Merkmal, das Assets unterscheidet, wird
INNERHALB der Stunde verglichen - und davon gibt es Millionen.

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE UND IHRE GEGENHYPOTHESE
═══════════════════════════════════════════════════════════════════════

    H1a  Das zurueckgebliebene Asset HOLT AUF          -> Einstieg
    H1b  Das zurueckgebliebene Asset ist SCHWACH       -> Sperre

⚠️ Beide sind plausibel und beide verwertbar. Deshalb wird ZWEISEITIG
geprueft - ein negatives Vorzeichen ist hier ein Ergebnis, kein Ausfall.

═══════════════════════════════════════════════════════════════════════
 DIE EINGEBAUTE GEGENPROBE
═══════════════════════════════════════════════════════════════════════

`beta` laeuft als MERKMAL mit. Traegt `rueckstand` nicht staerker als `beta`
allein, dann misst der Rueckstand nur, wie WILD ein Asset schwankt - das
waere Volatilitaet statt Richtung und damit 2.594 noch einmal.

⚠️ NUR LESEN.

    python messe_nachzieher.py [--symbole N] [--ab 2024-01-01]
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import (                     # noqa: E402
    atr_tag_relativ, ausgaenge, STOP_MIN, STOP_MAX)
from messe_q_beide_seiten import (                              # noqa: E402
    fuenftel_je_stunde, MIND_JE_FUENFTEL)

LEITWERT = os.path.join("data", "btc_leitwert.db")
K_ATR = 1.0
ZELLEN = ((1.5, 6), (1.5, 24), (2.0, 6))
#: ⭐⭐⭐ DIE BEDINGUNG - Nutzervorgabe 25.09.2026, woertlich:
#:
#:   *"wichtig ist nur zu unterscheiden, WARUM ist der Alt nicht gestiegen?
#:   und die Antwort die wir brauchen: WIE MUSS DIE LAGE DES ASSETS SEIN,
#:   DASS (WENN BTC STEIGT) EIN HEBEL IN FRAGE KOMMT"*
#:
#: ⚠️⚠️ Die erste Fassung mass ueber ALLE Stunden - auch die, in denen BTC
#: FAELLT. Dort bedeutet *zurueckgeblieben* das Gegenteil (weniger gefallen,
#: also stark), und die beiden Faelle heben sich gegenseitig auf.
#:
#: ➤ Die BTC-Bewegung wird deshalb zur zweiten ACHSE. Erst die Kreuztabelle
#: beantwortet die gestellte Frage, und zwar direkt ablesbar.
BTC_LAGEN = (("BTC faellt stark", None, -0.02),
             ("BTC faellt",       -0.02, -0.005),
             ("BTC seitwaerts",   -0.005, 0.005),
             ("BTC steigt",        0.005, 0.02),
             ("BTC steigt stark",  0.02, None))
RUECK_H = 6                     # ueber wie viele Stunden der Rueckstand zaehlt
BETA_TAGE = 30
MITLAUF_TAGE = 7
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
STAERKEN = (0.0, 0.10, 0.25, 0.50, 1.0)
N_POSITIV = 5
SAAT = 20260925


def lade_btc(sid: dict, T: int):
    """-> BTC-Schlusskurse auf der gemeinsamen Stundenachse (NaN wo fehlt)."""
    if not os.path.exists(LEITWERT):
        raise SystemExit("⛔ %s fehlt - erst `hole_btc_leitwert.py` laufen "
                         "lassen" % LEITWERT)
    c = sqlite3.connect("file:%s?mode=ro" % LEITWERT, uri=True)
    reihen = c.execute("SELECT stunde, close FROM leitwert WHERE symbol='BTC' "
                       "ORDER BY stunde").fetchall()
    c.close()
    aus = np.full(T, np.nan)
    for st, close in reihen:
        i = sid.get(st)
        if i is not None:
            aus[i] = close
    return aus


def _rendite(x, h):
    """Rendite ueber h Schritte - streng kausal, NaN am Anfang."""
    r = np.full(len(x), np.nan)
    if len(x) > h:
        with np.errstate(invalid="ignore", divide="ignore"):
            r[h:] = x[h:] / np.maximum(x[:-h], 1e-12) - 1.0
    return r


def _roll_beta(y, x, fenster):
    """Rollende Steigung y~x ueber `fenster` Schritte - STRENG KAUSAL.

    ⚠️ Der Wert zur Stunde t nutzt nur Stunden <= t. Umgesetzt ueber
    kumulierte Summen, damit es nicht 42.000 Einzelregressionen werden.
    """
    n = len(y)
    gut = np.isfinite(y) & np.isfinite(x)
    ys = np.where(gut, y, 0.0)
    xs = np.where(gut, x, 0.0)
    g = gut.astype(float)

    def _lauf(a):
        k = np.concatenate(([0.0], np.cumsum(a)))
        aus = np.full(n, np.nan)
        aus[fenster:] = k[fenster + 1:] - k[1:n - fenster + 1]
        return aus

    sxy, sxx = _lauf(xs * ys), _lauf(xs * xs)
    sx, sy, sn = _lauf(xs), _lauf(ys), _lauf(g)
    with np.errstate(invalid="ignore", divide="ignore"):
        zaehler = sxy - sx * sy / np.maximum(sn, 1e-9)
        nenner = sxx - sx * sx / np.maximum(sn, 1e-9)
        beta = np.where(np.abs(nenner) > 1e-18, zaehler / nenner, np.nan)
    return np.where(sn >= fenster * 0.5, beta, np.nan)


def _roll_korr(y, x, fenster):
    """Rollende Korrelation - kausal, gleiche Bauart wie `_roll_beta`."""
    n = len(y)
    gut = np.isfinite(y) & np.isfinite(x)
    ys, xs = np.where(gut, y, 0.0), np.where(gut, x, 0.0)
    g = gut.astype(float)

    def _lauf(a):
        k = np.concatenate(([0.0], np.cumsum(a)))
        aus = np.full(n, np.nan)
        aus[fenster:] = k[fenster + 1:] - k[1:n - fenster + 1]
        return aus

    sxy, sxx, syy = _lauf(xs * ys), _lauf(xs * xs), _lauf(ys * ys)
    sx, sy, sn = _lauf(xs), _lauf(ys), _lauf(g)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.maximum(sn, 1e-9)
        cov = sxy - sx * sy / m
        vx, vy = sxx - sx * sx / m, syy - sy * sy / m
        k = cov / np.sqrt(np.maximum(vx * vy, 1e-24))
    return np.where(sn >= fenster * 0.5, np.clip(k, -1.0, 1.0), np.nan)


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    ab = None
    if "--ab" in sys.argv:
        ab = sys.argv[sys.argv.index("--ab") + 1]
        if len(ab) == 10:
            ab += " 00:00"

    print("=" * 100)
    print("DER NACHZIEHER: welches Asset hat auf BTC noch nicht reagiert?")
    print("=" * 100)
    print("  Vorabfestlegung 18 · Frageart BEITRAG · k = %.2f x ATR" % K_ATR)
    print("  ⚠️ Das Merkmal unterscheidet ASSETS - anders als 2.599, das")
    print("     einen Marktzustand mass (ein Wert fuer alle).")
    print("  ⭐ Deshalb: STUNDENKLAMMER und die einfache Nullwelt.")

    kurse = lade_kurse(grenze)
    alle = set()
    for (stunden, *_r) in kurse.values():
        alle.update(stunden)
    stundenliste = sorted(alle)
    sid = {s: i for i, s in enumerate(stundenliste)}
    T = len(stundenliste)
    print("  %d Symbole · %d Stunden" % (len(kurse), T), flush=True)

    btc_close = lade_btc(sid, T)
    print("  BTC-Leitwert: %d von %d Stunden belegt"
          % (int(np.isfinite(btc_close).sum()), T))
    btc_r6 = _rendite(btc_close, RUECK_H)
    btc_r1 = _rendite(btc_close, 1)

    # ══ DOMINANZ-AENDERUNG als REGLER ════════════════════════════════
    #
    # Nutzeridee 25.09.2026: *"btc kurs und oder dominanz positive oder
    # negative Beitraege"* und *"u.U. kann btc und die dominanz wie ein
    # REGLER funktionieren"*.
    #
    # ⛔ Die ECHTE Dominanz ist nicht messbar: `macro_snapshot` hat 3.384
    # Zeilen, aber nur 10 Werte mit `btc_dominance_pct` (2026-07-07 bis
    # 07-19). Es gibt keine Historie, nur aktuelle Werte fuer den Betrieb.
    #
    # ⭐ Die AENDERUNG der Dominanz laesst sich dagegen exakt bilden, und
    # zwar stuendlich ueber die volle Historie:
    #
    #     Dominanz steigt  <=>  BTC steigt STAERKER als der Alt-Median
    #
    # ⚠️ Das ist nicht das Dominanz-NIVEAU, sondern ihre Richtung - und fuer
    # einen Regler ist genau das die relevante Groesse.
    #
    # ⚠️⚠️ UND DER WICHTIGE PUNKT: die Dominanz selbst ist ein MARKTZUSTAND
    # (ein Wert je Stunde fuer alle Assets) und damit nach
    # `feedback-nicht-den-markt-messen-sondern-beitraege-je-asset` KEIN
    # Beitragskandidat. Sie wird deshalb als ACHSE gefahren (wie die
    # BTC-Lage), und was je Asset unterschieden wird, ist die
    # EMPFAENGLICHKEIT - siehe `dominanz_wirkung` unten.
    alt_summe = np.zeros(T)
    alt_zahl = np.zeros(T)
    for sym, (stunden, high, low, close, volumen) in kurse.items():
        if sym.upper() == "BTC":
            continue
        ii = np.array([sid[x] for x in stunden], np.int64)
        rr = _rendite(close, RUECK_H)
        g = np.isfinite(rr)
        np.add.at(alt_summe, ii[g], rr[g])
        np.add.at(alt_zahl, ii[g], 1.0)
    with np.errstate(invalid="ignore"):
        alt_mittel = np.where(alt_zahl >= 5, alt_summe / np.maximum(alt_zahl, 1),
                              np.nan)
    dom_aenderung = btc_r6 - alt_mittel
    print("  Dominanz-Aenderung (BTC minus Alt-Mittel, %d h): %d Stunden "
          "belegt" % (RUECK_H, int(np.isfinite(dom_aenderung).sum())))
    ab_idx = 0 if ab is None else next(
        (i for i, x in enumerate(stundenliste) if x >= ab), T)
    if ab:
        print("  ⭐ Fenster ab %s: %d von %d Stunden" % (ab, T - ab_idx, T))

    # ── Merkmale je Symbol ────────────────────────────────────────────
    roh = []
    for sym, (stunden, high, low, close, volumen) in kurse.items():
        if sym.upper() == "BTC":
            # ⚠️ BTC gegen sich selbst hat Rueckstand null - es wuerde die
            # Fuenftel verzerren, ohne etwas beizutragen.
            continue
        idx = np.array([sid[s] for s in stunden], np.int64)
        a_r6 = _rendite(close, RUECK_H)
        a_r1 = _rendite(close, 1)
        b6, b1 = btc_r6[idx], btc_r1[idx]
        beta = _roll_beta(a_r1, b1, BETA_TAGE * 24)
        mit = _roll_korr(a_r1, b1, MITLAUF_TAGE * 24)
        merkmale = {
            "rueckstand_roh": b6 - a_r6,
            "rueckstand_beta": beta * b6 - a_r6,
            "mitlauf": mit,
            "beta": beta,
            # ⛔⛔⛔ HIER STAND `dominanz_wirkung = dom_aenderung x beta`.
            # DAS WAR FALSCH GEBAUT, nachgewiesen am Konstrukt:
            # `dom_aenderung` ist INNERHALB einer Stunde fuer alle Assets
            # dieselbe Zahl, das Produkt also `Konstante x beta`. Innerhalb
            # der Stundenklammer ist das MONOTON IN BETA - Rangkorrelation
            # +1,0000 bei positiver und -1,0000 bei negativer Aenderung.
            # Ueber viele Stunden hebt sich das auf, und genau deshalb lag
            # es im Nullband.
            #
            # ⚠️ Das Urteil *die Regler-Idee traegt nicht* war damit FALSCH.
            # Richtig: so gemessen KANN sie nicht tragen. Ein Marktzustand
            # wird zur ACHSE, nicht zum Faktor in einem Produkt - siehe die
            # Kreuztabelle BTC x DOMINANZ unten.
            #
            # ⭐ Was stattdessen ein Asset-Merkmal IST: der Rueckstand
            # gegen den ALT-MEDIAN (nicht gegen BTC). Er sagt, ob dieses
            # Asset innerhalb der Altcoins zurueck ist - und der Alt-Median
            # ist je Stunde konstant, das Asset selbst nicht.
            "rueckstand_alt": alt_mittel[idx] - a_r6,
        }
        roh.append((sym, idx, high, low, close, merkmale))
    print("  %d Symbole mit Merkmalen (BTC selbst ausgeschlossen)"
          % len(roh), flush=True)

    rng = np.random.default_rng(SAAT)
    for crv, H in ZELLEN:
        G, Z, S, RO, ZS, SS, ROS, MM = [], [], [], [], [], [], [], {k: [] for k in
                                           ("rueckstand_roh",
                                            "rueckstand_beta", "mitlauf",
                                            "beta", "rueckstand_alt",
                                            "zufall")}
        for (sym, idx, high, low, close, merkmale) in roh:
            atr = atr_tag_relativ(high, low, close)
            stop_rel = np.clip(K_ATR * atr, STOP_MIN, STOP_MAX)
            zz, ss, ro, gu, _gl = ausgaenge(high, low, close, stop_rel,
                                            crv * stop_rel, H)
            # ⭐ SPIEGELPROBE: derselbe Anker, SHORT-Geometrie (Stop oben,
            # Ziel unten). Das ist die einzige korrekte Gegenprobe - blosses
            # Vorzeichendrehen der Zielgroesse unterstellt dieselben
            # Ausgaenge und ist damit tautologisch.
            zs, ssh, ros, _gus, _g2 = ausgaenge(high, low, close, stop_rel,
                                                crv * stop_rel, H,
                                                runter=True)
            gu = gu & (idx >= ab_idx)
            for k, v in merkmale.items():
                gu = gu & np.isfinite(v)
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            G.append(idx[sel]); Z.append(zz[sel]); S.append(ss[sel])
            RO.append(ro[sel])
            ZS.append(zs[sel]); SS.append(ssh[sel]); ROS.append(ros[sel])
            for k in MM:
                MM[k].append(merkmale[k][sel] if k in merkmale
                             else rng.random(len(sel)))
        if not G:
            continue
        G = np.concatenate(G); Z = np.concatenate(Z); S = np.concatenate(S)
        RO = np.concatenate(RO)
        ZS = np.concatenate(ZS); SS = np.concatenate(SS)
        ROS = np.concatenate(ROS)
        MM = {k: np.concatenate(v) for k, v in MM.items()}
        r = np.where(Z, crv, np.where(S, -1.0, np.nan_to_num(RO)))
        r_short = np.where(ZS, crv, np.where(SS, -1.0, np.nan_to_num(ROS)))

        print()
        print("=" * 100)
        print("CRV %.1f · H%d · %d Anker · E[R] brutto %+.5f · Drift %+.5f"
              % (crv, H, len(G), float(r.mean()), float(np.mean(RO))))

        # ══ KREUZTABELLE BTC x DOMINANZ ═════════════════════════════
        #
        # Nutzervorgabe 25.09.2026, woertlich: *"wenn btc steigt steigen
        # auch alts aber nicht immer gleich - WENN DIE DOMINANZ FAELLT
        # STEIGEN ALTS STAERKER"*.
        #
        # ⭐ Das sind ZWEI Achsen, und die gesuchte Lage ist ihre Kreuzung:
        # BTC steigt UND Dominanz faellt. Beide sind Marktzustaende, also
        # ACHSEN und keine Beitraege - aber ihre Kreuzung sagt, WANN ein
        # Hebel ueberhaupt in Frage kommt.
        #
        # ⚠️ Beide Achsen sind RUECKWAERTS gebildet (letzte 6 h). Gemessen
        # wird, ob es DANACH weitergeht - sonst waere es Rueckschau.
        d_bei = dom_aenderung[G]
        b_bei = btc_r6[G]
        print("  ⭐ KREUZ  BTC x DOMINANZ  (E[R] brutto, Anker in Klammern)")
        print("     %-16s %22s %22s" % ("", "Dominanz FAELLT",
                                        "Dominanz STEIGT"))
        for etikett, unten, oben in (("BTC faellt", None, -0.005),
                                     ("BTC seitwaerts", -0.005, 0.005),
                                     ("BTC steigt", 0.005, None)):
            zeile = []
            for dom_faellt in (True, False):
                m = np.isfinite(b_bei) & np.isfinite(d_bei)
                if unten is not None:
                    m &= b_bei >= unten
                if oben is not None:
                    m &= b_bei < oben
                m &= (d_bei < 0) if dom_faellt else (d_bei >= 0)
                if m.sum() < MIND_JE_FUENFTEL:
                    zeile.append("%22s" % "(zu duenn)")
                    continue
                rr = r[m]
                tag = G[m] // 24
                ut = np.unique(tag)
                if len(ut) >= 30:
                    pos = np.searchsorted(ut, tag)
                    jt = (np.bincount(pos, weights=rr, minlength=len(ut))
                          / np.maximum(np.bincount(pos, minlength=len(ut)), 1))
                    se = float(np.std(jt, ddof=1) / np.sqrt(len(ut)))
                else:
                    se = float("nan")
                mw = float(rr.mean())
                zeichen = ("✔" if np.isfinite(se)
                           and abs(mw) > 1.645 * se else "⚠")
                zeile.append("%+8.4f±%.4f %s %7s"
                             % (mw, se, zeichen,
                                "(%dk)" % (m.sum() // 1000)))
            print("     %-16s %s" % (etikett, " ".join(zeile)))
        print("     ✔ = vom Null verschieden (tagesgeblockt) · "
              "⚠ = nicht zu trennen")
        print()

        # ── ACHSE: die BTC-Lage zum Ankerzeitpunkt ────────────────
        btc_bei_anker = btc_r6[G]
        print("  %-18s %8s %9s %9s %9s %9s   %s"
              % ("BTC-Lage", "Anker", "F0", "F1", "F2", "F3", "F4 (zurueck)"))
        for etikett, unten, oben in BTC_LAGEN:
            m = np.isfinite(btc_bei_anker)
            if unten is not None:
                m &= btc_bei_anker >= unten
            if oben is not None:
                m &= btc_bei_anker < oben
            if m.sum() < 5 * MIND_JE_FUENFTEL:
                print("  %-18s %8d  (zu duenn)" % (etikett, int(m.sum())))
                continue
            fz = fuenftel_je_stunde(G[m], MM["rueckstand_beta"][m])
            if fz is None:
                continue
            i2, f2 = fz
            rr = r[m]
            n5 = np.bincount(f2, minlength=5).astype(float)
            if (n5 < MIND_JE_FUENFTEL).any():
                print("  %-18s %8d  (Fuenftel zu duenn)" % (etikett,
                                                            int(m.sum())))
                continue
            e5 = np.bincount(f2, weights=rr[i2], minlength=5) / n5
            # ⚠️ BRUTTO ist hier die Hauptgroesse: die Frage lautet *kommt
            # ein Hebel in Frage*, und das ist die NIVEAUfrage (2.597 § 5.3).
            #
            # ⚠️⚠️⚠️ ABER DAS NIVEAU IST NICHT SO BELASTBAR WIE DIE ORDNUNG.
            # Die Anker einer BTC-Lage stammen aus WENIGEN Zeitfenstern -
            # dieselbe Clusterung, an der 2.599 scheiterte. Deshalb wird
            # der Niveauwert gegen einen TAGESGEBLOCKTEN Fehlerbereich
            # gestellt: die Anker werden nach Tagen gruppiert, und gestreut
            # wird ueber TAGE, nicht ueber Anker. Das ist die ehrliche
            # Unsicherheit.
            #
            # ⭐ Die ORDNUNG (F4 gegen F0 innerhalb derselben Stunde) ist
            # davon NICHT betroffen - sie ist ein Querschnitt.
            tag = G[m][i2] // 24
            utag = np.unique(tag)
            if len(utag) >= 30:
                pos = np.searchsorted(utag, tag)
                sm = np.bincount(pos, weights=rr[i2], minlength=len(utag))
                cn = np.bincount(pos, minlength=len(utag)).astype(float)
                je_tag = sm / np.maximum(cn, 1)
                # Streuung ueber TAGE, gewichtet wie die Tage zaehlen
                se = float(np.std(je_tag, ddof=1) / np.sqrt(len(utag)))
            else:
                se = float("nan")
            gesamt = float(rr[i2].mean())
            print("  %-18s %8d %s   %s"
                  % (etikett, int(m.sum()),
                     " ".join("%+9.4f" % x for x in e5),
                     "⭐⭐ F4 UEBER NULL" if e5[4] > 0
                     else ("⭐ F4 bestes" if e5[4] >= e5.max() - 1e-12
                           else "")))
            print("  %-18s %8s Niveau %+.4f ± %.4f (ueber %d Tage) %s"
                  % ("", "", gesamt, se, len(utag),
                     "✔ vom Null verschieden"
                     if np.isfinite(se) and abs(gesamt) > 1.645 * se
                     else "⚠ NICHT von null zu trennen"))
            print("  %-18s %8s Ordnung F4-F0 %+.4f (Querschnitt, von der "
                  "Clusterung UNberuehrt)" % ("", "", e5[4] - e5[0]))
        print()

        for name in ("rueckstand_beta", "rueckstand_roh",
                     "rueckstand_alt", "mitlauf", "beta", "zufall"):
            fz = fuenftel_je_stunde(G, MM[name])
            if fz is None:
                print("  %-16s zu duenn" % name)
                continue
            i2, f2 = fz
            n5 = np.bincount(f2, minlength=5).astype(float)
            if (n5 < MIND_JE_FUENFTEL).any():
                print("  %-16s zu duenn" % name)
                continue
            e5 = np.bincount(f2, weights=r[i2], minlength=5) / n5
            d5 = np.bincount(f2, weights=RO[i2], minlength=5) / n5
            netto = e5 - d5
            # ⚠️ ZWEISEITIG: das zurueckgebliebene Asset koennte aufholen
            # (Fuenftel 4 vorn) ODER schwach sein (Fuenftel 0 vorn). Beide
            # sind verwertbar, also zaehlt der BETRAG der Spanne.
            spanne = float(netto[4] - netto[0])
            nullw = []
            for _ in range(N_NULL):
                fzz = fuenftel_je_stunde(G, rng.random(len(G)))
                if fzz is None:
                    continue
                i3, f3 = fzz
                n3 = np.bincount(f3, minlength=5).astype(float)
                if (n3 < MIND_JE_FUENFTEL).any():
                    continue
                e3 = np.bincount(f3, weights=r[i3], minlength=5) / n3
                dd = np.bincount(f3, weights=RO[i3], minlength=5) / n3
                nt = e3 - dd
                nullw.append(abs(float(nt[4] - nt[0])))
            if len(nullw) < 10:
                print("  %-16s Nullband nicht zu bilden" % name)
                continue
            nullw = np.array(nullw)
            grenze90 = float(np.percentile(nullw, NULL_PERZ))
            traegt = abs(spanne) > grenze90
            print("  %-16s NETTO %s" % (name,
                                        " ".join("%+7.4f" % x for x in netto)))
            print("      Spanne(4-0) %+.5f · Nullpunkt %+.5f · %d. Perz "
                  "%+.5f · %s%s"
                  % (spanne, float(nullw.mean()), int(NULL_PERZ), grenze90,
                     "✔ TRENNT" if traegt else "- im Nullband",
                     ("  ⭐ Richtung: %s" %
                      ("zurueckgeblieben HOLT AUF" if spanne > 0
                       else "zurueckgeblieben bleibt SCHWACH"))
                     if traegt else ""))
            print("      brutto %s · bestes Fuenftel %+.5f %s"
                  % (" ".join("%+7.4f" % x for x in e5), float(e5.max()),
                     "⭐⭐ UEBER NULL" if e5.max() > 0 else "(unter null)"))
            if not traegt:
                continue

            # ── SPIEGELPROBE ─────────────────────────────────────────
            #
            # ⛔ Vorabfestlegung 18 § 3.2 hat sie ZUGESAGT, die erste
            # Fassung des Werkzeugs hatte sie NICHT - gefunden bei der vom
            # Nutzer verlangten Standardpruefung. Derselbe Fehler wie bei
            # Vorabfestlegung 15.
            #
            # Gespiegelt wird die ZIELGROESSE, nicht die Barriere: `-r` ist
            # genau das Ergebnis, das ein SHORT mit derselben Geometrie
            # erzielt haette. Ordnet das Merkmal beide Richtungen gleich
            # stark, ist es Bewegung ohne Richtung (2.594).
            e5s = np.bincount(f2, weights=r_short[i2], minlength=5) / n5
            d5s = np.bincount(f2, weights=-RO[i2], minlength=5) / n5
            geg = e5s - d5s
            sp_geg = float(geg[4] - geg[0])
            verh = abs(spanne) / max(abs(sp_geg), 1e-12)
            print("      ⭐ SPIEGELPROBE Gegenrichtung %+.5f · "
                  "Verhaeltnis %.2f · %s"
                  % (sp_geg, verh,
                     "✔ RICHTUNG (>=1,30)" if verh >= 1.30
                     else ("✔ inverse Richtung (<=0,77)" if verh <= 0.77
                           else "⚠️ BEWEGUNG OHNE RICHTUNG - kein Beitrag")))

            # ── TRENNSCHAERFE ────────────────────────────────────────
            # ⛔ Ebenfalls in § 4 zugesagt und nicht gebaut. Anteil echter
            # Ordnung in Zufall gemischt, Fundquote je Stufe - wie 2.597.
            rg = np.argsort(np.argsort(MM[name])) / max(1, len(MM[name]) - 1)
            aus = []
            for st in STAERKEN:
                w = []
                for _ in range(N_POSITIV):
                    mix = st * rg + (1.0 - st) * rng.random(len(G))
                    fzm = fuenftel_je_stunde(G, mix)
                    if fzm is None:
                        continue
                    i4, f4 = fzm
                    n4 = np.bincount(f4, minlength=5).astype(float)
                    if (n4 < MIND_JE_FUENFTEL).any():
                        continue
                    e4 = np.bincount(f4, weights=r[i4], minlength=5) / n4
                    dd4 = np.bincount(f4, weights=RO[i4], minlength=5) / n4
                    nt4 = e4 - dd4
                    w.append(abs(float(nt4[4] - nt4[0])))
                if w:
                    q = float((np.array(w) > grenze90).mean())
                    aus.append("%.2f:%.0f%%" % (st, 100 * q))
            print("      ⭐ TRENNSCHAERFE (Anteil:Fundquote) %s"
                  % " ".join(aus))
    print()
    print("  ⚠️ `zufall` UND `beta` sind Kontrollen. Traegt `rueckstand`")
    print("     nicht staerker als `beta`, misst es nur Volatilitaet -")
    print("     dann ist es 2.594 noch einmal, kein Beitrag.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
