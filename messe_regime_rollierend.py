# -*- coding: utf-8 -*-
"""Ist der Marktzustand VORAB erkennbar? - Schritt 3 des Hebel-Neubaus

**Nutzerentscheidung 25.09.2026:** *"Regime rollierend messen"* - nach
Befund 2.598, der den Faktor 12 zwischen Regime und Lage gemessen hat.

**Vorabfestlegung 17** (`Basisinfos/Vorabfestlegung_17_Regime_25_09.md`)
ist VOR dieser Messung geschrieben und enthaelt H0, H1 und die Vorhersage.

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE
═══════════════════════════════════════════════════════════════════════

    Gibt es einen zum Zeitpunkt t VERFUEGBAREN Marktzustand, der
    `E[R]` BRUTTO ueber null hebt?

⚠️ Betont BRUTTO. Nach 2.597 ist das die NIVEAUfrage, und nur sie
entscheidet ueber den Hebel. Netto ist die Querschnittsfrage.

⚠️⚠️ H1 hat ZWEI Stufen, und nur die zweite traegt einen Hebel:
ORDNEN (das Fuenftel trennt) und TRAGEN (`E[R]` > 0). 2.594 hat gezeigt,
dass Ordnen ohne Tragen moeglich ist.

═══════════════════════════════════════════════════════════════════════
 ⭐⭐⭐ WARUM DIE NULLWELT AUS 2.597 HIER FALSCH WAERE
═══════════════════════════════════════════════════════════════════════

Alle Regime-Merkmale sind MARKTWEIT: zu einer Stunde haben alle Symbole
denselben Wert. Daraus folgt:

    (1) Die STUNDENKLAMMER funktioniert nicht - innerhalb einer Stunde
        ist der Wert konstant. Gemessen wird GEPOOLT, was fuer die
        Niveaufrage richtig ist (registriert: Niveau -> gepoolt).

    (2) ⛔⛔ Eine ANKERWEISE Permutation waere grob falsch. 3,2 Mio Anker
        stammen von rund 1.700 Tagen, und der Marktzustand bleibt ueber
        Tage nahezu gleich. Die EFFEKTIVE Stichprobe ist um
        Groessenordnungen kleiner als n - das Band waere absurd eng und
        JEDES Merkmal ein Treffer, auch `zufall`.

    ➤ Deshalb: ZYKLISCHE VERSCHIEBUNG des Merkmals gegen die Ausgaenge.
      Sie erhaelt die volle Autokorrelation beider Seiten und bricht nur
      den ZUSAMMENHANG. Verschiebung mindestens 90 Tage.

    ⭐ Und `zufall` wird AUTOKORRELIERT gebildet (gleitendes Mittel ueber
      30 Tage), nicht als weisses Rauschen - sonst haette es die Struktur
      gar nicht, um faelschlich zu treffen, und wuerde nichts pruefen.

═══════════════════════════════════════════════════════════════════════
 RUECKSCHAU GEGEN KAUSAL - die Lehre aus 2.598
═══════════════════════════════════════════════════════════════════════

    RUECKSCHAU  Fuenftelgrenzen aus dem GANZEN Fenster. ⛔ Kennt die
                Zukunft, ist keine Strategie.
    KAUSAL      Fuenftelgrenzen nur aus den Daten BIS t (expandierend).
                ✔ Nur diese Fassung darf in eine Bewertung.

In 2.598 hat genau diese Doppelung den Symbolauswahl-Weg als
Ueberanpassung entlarvt (Rueckschau +Faktor 4,5, kausal schlechter).

⚠️ NUR LESEN. Keine Datenbank wird beschrieben.

    python messe_regime_rollierend.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import sqlite3

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import (                     # noqa: E402
    atr_tag_relativ, ausgaenge, STOP_MIN, STOP_MAX)

K_ATR = 1.0                     # der lageneutrale Arm aus 2.597
#: ⚠️ Von vier auf ZWEI Zellen. Die vier teilten dieselben Anker
#: und lieferten keine unabhaengigen Tests - die gesparte Zeit
#: geht in MEHR Kontrollreihen, wo sie etwas beweist.
ZELLEN = ((1.5, 6), (1.5, 24))
#: ⭐⭐⭐ DAS FENSTER IST EINE ACHSE, KEINE EINSTELLUNG.
#:
#: Nutzerhinweis 25.09.2026, woertlich: *"der gesamtmarkt ist nicht mehr wie
#: 2021 und 2022 ob das ein vor oder nachteil ist weis ich nicht. Die ersten
#: jahre waren von uebertreibung gekennzeichnet."*
#:
#: ⚠️ Die eigenen Zahlen aus 2.598 stuetzen das: `E[R]` H24 betraegt 2022
#: -0,0430 und 2023 +0,0256, waehrend 2024 bis 2026 alle zwischen -0,0063
#: und +0,0040 liegen. Zwei Ausschlaege und drei ruhige Jahre.
#:
#: ➤ Deshalb wird NICHT entschieden, sondern BEIDES gemessen und die
#: Differenz hingeschrieben - wie bei Tagesklammer gegen gepoolt. Ein
#: Merkmal, das nur im vollen Fenster traegt, lebt von 2022.
#:
#: ⚠️ Und der Preis gehoert dazu: das kurze Fenster hat WENIGER
#: Regimewechsel, also eine kleinere effektive Stichprobe und ein
#: BREITERES Nullband. Es ist nicht der bessere Zuschnitt, nur der andere.
#: wird aus `--ab` gesetzt; 0 = volles Fenster.
AB_IDX = [0]
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
MIND_VERSATZ = 90 * 24          # 90 Tage, damit kein Restzusammenhang bleibt
SAAT = 20260925
MIND_JE_FUENFTEL = 5000
#: Fuenf Kontrollreihen - die Fehlalarmquote wird GEMESSEN.
N_KONTROLLEN = 10
#: Mindestbelegung, unter der ein Merkmal ausgeschlossen wird.
MIND_BELEGT = 5000
LEITWERT = os.path.join("data", "btc_leitwert.db")
#: Anlaufzeit, bevor die kausalen Fuenftelgrenzen belastbar sind.
KAUSAL_ANLAUF = 180 * 24


def _tage_mittel(x, tage, stunden=24):
    """Gleitendes Mittel der letzten `tage` - STRENG KAUSAL bis t."""
    n = len(x)
    f = tage * stunden
    m = np.convolve(np.nan_to_num(x), np.ones(f) / float(f),
                    mode="full")[:n]
    m[:f] = np.nan
    return m


def baue_regime(kurse, stundenliste, sid):
    """-> dict Merkmalsname -> Reihe ueber die GEMEINSAME Stundenachse.

    ⚠️ Jedes Merkmal ist zur Stunde t nur aus Daten <= t gebildet. Ein
    marktweites Merkmal, das in die Zukunft sieht, wuerde die ganze Frage
    beantworten, bevor sie gestellt ist.
    """
    T = len(stundenliste)
    ueber = np.zeros(T)          # Summe: Kurs ueber eigenem 30-Tage-Mittel
    zaehl = np.zeros(T)
    mom = np.full((len(kurse), T), np.nan)
    vol = np.full((len(kurse), T), np.nan)
    btc = np.full(T, np.nan)

    for i, (sym, (stunden, high, low, close, volumen)) in enumerate(
            kurse.items()):
        idx = np.array([sid[s] for s in stunden], np.int64)
        m30 = _tage_mittel(close, 30)
        with np.errstate(invalid="ignore"):
            ist_ueber = (close > m30).astype(float)
        gut = np.isfinite(m30)
        np.add.at(ueber, idx[gut], ist_ueber[gut])
        np.add.at(zaehl, idx[gut], 1.0)
        # 7-Tage-Rendite, kausal
        h = 7 * 24
        r7 = np.full(len(close), np.nan)
        if len(close) > h:
            r7[h:] = close[h:] / np.maximum(close[:-h], 1e-12) - 1.0
        mom[i, idx] = r7
        vol[i, idx] = atr_tag_relativ(high, low, close)

    rng = np.random.default_rng(SAAT)
    # ⭐ zufall AUTOKORRELIERT - weisses Rauschen wuerde hier nichts pruefen
    #
    # ⚠️⚠️⚠️ FUENF Kontrollreihen statt einer. Der erste Lauf hatte EINE, und
    # sie ordnete in 1 von 8 Tests. Das ist bei einem 90.-Perzentil-Band die
    # ERWARTETE Rate (10 %) - aber mit acht Tests laesst sich das nicht
    # zeigen, sondern nur behaupten. Und das vorab festgelegte Kriterium
    # lautete absolut ("traegt zufall, gilt kein Ergebnis"), war also zu
    # grob: es haette auf die RATE lauten muessen.
    #
    # ➤ Die Kontrolle wird VERSTAERKT, nicht das Kriterium gelockert. Fuenf
    # Reihen x 4 Zellen x 2 Fassungen = 40 Kontrolltests. Damit ist die
    # Fehlalarmquote MESSBAR statt begruendbar.

    # ══ BTC AUS DER LEITWERT-REIHE ═══════════════════════════════════
    #
    # ⭐ Nutzerhinweis 25.09.: *"BTC kann nicht der Zufall sein sondern die
    # Ursache - der komplette Kryptomarkt haengt vom steigen oder fallen
    # von btc ab."*
    #
    # ⚠️⚠️ Der erste Lauf nahm BTC aus `stundenkurse.db`, wo es erst ab
    # 2023-09 liegt - 62 % der Zeit, OHNE 2022 (E[R] -0,0430). Jetzt kommt
    # es aus `btc_leitwert.db`: 44.415 Stunden ab 2021-09, lueckenlos.
    btc_m30 = None
    if os.path.exists(LEITWERT):
        cl = sqlite3.connect("file:%s?mode=ro" % LEITWERT, uri=True)
        reihen = cl.execute("SELECT stunde, high, low, close FROM leitwert "
                            "WHERE symbol='BTC' ORDER BY stunde").fetchall()
        cl.close()
        bi = np.array([sid[r[0]] for r in reihen if r[0] in sid], np.int64)
        gut = [r for r in reihen if r[0] in sid]
        if len(gut) > 30 * 24:
            bh = np.array([r[1] for r in gut], float)
            bl = np.array([r[2] for r in gut], float)
            bc = np.array([r[3] for r in gut], float)
            b30 = _tage_mittel(bc, 30)
            with np.errstate(invalid="ignore"):
                btc[bi] = bc / np.maximum(b30, 1e-12) - 1.0
            h7 = 7 * 24
            br = np.full(len(bc), np.nan)
            if len(bc) > h7:
                br[h7:] = bc[h7:] / np.maximum(bc[:-h7], 1e-12) - 1.0
            btc_m30 = (br, atr_tag_relativ(bh, bl, bc), bi)
            print("    (Leitwert: %d von %d BTC-Stunden auf der Achse)"
                  % (len(gut), len(reihen)))
    else:
        print("    ⚠ %s fehlt - `btc_*` bleibt leer" % LEITWERT)

    with np.errstate(invalid="ignore"):
        breite = np.where(zaehl >= 5, ueber / np.maximum(zaehl, 1), np.nan)
    aus = {
        "breite": breite,
        "markt_momentum": np.nanmedian(mom, axis=0),
        "markt_vola": np.nanmedian(vol, axis=0),
        "btc_trend": btc,
    }
    if btc_m30 is not None:
        br, bv, bi = btc_m30
        for name, reihe in (("btc_momentum", br), ("btc_vola", bv)):
            voll = np.full(T, np.nan)
            voll[bi] = reihe
            aus[name] = voll
    for j in range(N_KONTROLLEN):
        aus["zufall_%d" % (j + 1)] = _tage_mittel(rng.standard_normal(T), 30)
    return aus


def _fuenftel_rueckschau(w):
    """Fuenftel aus dem GANZEN Fenster - kennt die Zukunft."""
    gr = np.nanpercentile(w, [20, 40, 60, 80])
    return np.searchsorted(gr, w, side="right")


def _fuenftel_kausal(w, stunde_idx):
    """Fuenftel nur aus Daten BIS t - expandierendes Fenster je Tag.

    ⚠️ Die Grenzen werden einmal je TAG neu gesetzt, nicht je Stunde: eine
    Neuberechnung je Stunde waere 40.000 Sortierungen und aendert nichts,
    weil sich ein expandierendes Perzentil in einer Stunde kaum bewegt.
    """
    f = np.full(len(w), -1, np.int8)
    ordnung = np.argsort(stunde_idx, kind="stable")
    w_s = w[ordnung]; t_s = stunde_idx[ordnung]
    tag = t_s // 24
    grenzen_tag = np.unique(tag)
    puffer = []
    pos = 0
    for tg in grenzen_tag:
        m = tag == tg
        k = int(m.sum())
        if puffer and len(puffer) >= 1:
            hist = np.concatenate(puffer)
            hist = hist[np.isfinite(hist)]
            if len(hist) >= 1000:
                gr = np.percentile(hist, [20, 40, 60, 80])
                f[ordnung[pos:pos + k]] = np.searchsorted(
                    gr, w_s[pos:pos + k], side="right")
        puffer.append(w_s[pos:pos + k])
        pos += k
    return f


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
    print("IST DER MARKTZUSTAND VORAB ERKENNBAR? - Schritt 3")
    print("=" * 100)
    print("  Vorabfestlegung 17 · k = %.2f x ATR · Nullwelt = ZYKLISCHE "
          "VERSCHIEBUNG (min. %d Tage)" % (K_ATR, MIND_VERSATZ // 24))
    print("  ⚠️ Gemessen wird E[R] BRUTTO - die NIVEAUfrage. H1 hat zwei")
    print("     Stufen: ORDNEN und TRAGEN (E[R] > 0). Nur die zweite ist")
    print("     ein Hebel.")

    kurse = lade_kurse(grenze)
    print("  %d Symbole geladen" % len(kurse), flush=True)

    # ── gemeinsame Stundenachse ───────────────────────────────────────
    alle = set()
    for (stunden, *_r) in kurse.values():
        alle.update(stunden)
    stundenliste = sorted(alle)
    sid = {s: i for i, s in enumerate(stundenliste)}
    print("  %d Stunden auf der gemeinsamen Achse" % len(stundenliste),
          flush=True)

    #: [Treffer, Tests] getrennt fuer Kontrollen und echte Merkmale.
    #: Merkmal -> [Treffer, Tests], NUR kausale Fassung.
    JE_MERKMAL: dict = {}

    if ab:
        AB_IDX[0] = next((i for i, x in enumerate(stundenliste) if x >= ab),
                         len(stundenliste))
        print("  ⭐ FENSTER ab %s: %d von %d Stunden"
              % (ab, len(stundenliste) - AB_IDX[0], len(stundenliste)))
        print("     ⚠ Nutzerhinweis: der Gesamtmarkt ist nicht mehr wie")
        print("        2021/2022 - die ersten Jahre waren Uebertreibung. Das")
        print("        Fenster ist eine ACHSE, keine Einstellung: beide Laeufe")
        print("        gehoeren nebeneinander, und die Differenz ist die")
        print("        Auskunft. Ein Merkmal, das nur voll traegt, lebt von 2022.")
        print("     ⚠ Preis: weniger Regimewechsel = BREITERES Nullband.")

    regime = baue_regime(kurse, stundenliste, sid)

    # ══ GEMEINSAMES ZEITFENSTER ─ registrierte Regel, hier zuerst verletzt ══
    #
    # ⛔⛔⛔ Der erste Lauf mass `btc_trend` NUR auf 2023-09 bis 2026-09, weil
    # die BTC-Reihe erst dort beginnt - 15.335 Stunden fehlen, darunter das
    # GANZE Jahr 2022 (E[R] -0,0430, das schlechteste). Es meldete daraufhin
    # in allen vier Zellen "ordnet und TRAEGT". Das war das Zeitfenster, nicht
    # BTC.
    #
    # ⭐ Verraten hat es sich dadurch, dass die KAUSALE Fassung STAERKER war
    # als die Rueckschau (Faktor 0,64) - unmoeglich, wenn beide dasselbe
    # messen, denn die Rueckschau kennt die Zukunft.
    #
    # ⚠️ Und der Fehler steckte doppelt: bei `np.roll` wandern die NaN mit,
    # also lief die Nullwelt auf einer ANDEREN Teilmenge als die Messung.
    #
    # ➤ Deshalb: alle Merkmale auf der SCHNITTMENGE der belegten Stunden.
    # ⚠️ Ein Merkmal, das GAR NICHT belegt ist, wuerde das gemeinsame
    # Fenster leeren und den Lauf STILL beenden - genau das passierte bei
    # `--symbole 15`, wo BTC nicht in der Teilmenge liegt. Solche Merkmale
    # werden AUSGESCHLOSSEN und gemeldet, nicht stillschweigend geduldet.
    for k in sorted(regime):
        belegt = int(np.isfinite(regime[k]).sum())
        if belegt < MIND_BELEGT:
            print("  ⛔ `%s` nur %d Stunden belegt (<%d) - wird "
                  "AUSGESCHLOSSEN, sonst leert es das gemeinsame Fenster"
                  % (k, belegt, MIND_BELEGT))
            del regime[k]
    if not regime:
        print("  ⛔ kein Merkmal ausreichend belegt - Abbruch")
        return 1
    gemeinsam = np.ones(len(stundenliste), bool)
    for v in regime.values():
        gemeinsam &= np.isfinite(v)
    if gemeinsam.sum() < MIND_BELEGT:
        print("  ⛔ gemeinsames Fenster nur %d Stunden - Abbruch"
              % int(gemeinsam.sum()))
        return 1
    print("  ⭐ Gemeinsames Fenster: %d von %d Stunden (%s bis %s)"
          % (int(gemeinsam.sum()), len(gemeinsam),
             stundenliste[int(np.flatnonzero(gemeinsam)[0])],
             stundenliste[int(np.flatnonzero(gemeinsam)[-1])]))
    print("     ⚠️ Registrierte Regel: gemeinsames Zeitfenster je Klasse.")
    print("     Ohne sie trug `btc_trend` scheinbar - es war 2023-09..2026-09")
    print("     und enthielt 2022 (E[R] -0,0430) nicht.")
    for k in regime:
        regime[k] = np.where(gemeinsam, regime[k], np.nan)
    for k, v in regime.items():
        print("    %-16s %d von %d Stunden belegt"
              % (k, int(np.isfinite(v).sum()), len(v)))

    for crv, H in ZELLEN:
        IDX, Z, S, RO = [], [], [], []
        for sym, (stunden, high, low, close, volumen) in kurse.items():
            atr = atr_tag_relativ(high, low, close)
            stop_rel = np.clip(K_ATR * atr, STOP_MIN, STOP_MAX)
            zz, ss, ro, gu, _gl = ausgaenge(high, low, close, stop_rel,
                                            crv * stop_rel, H)
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            IDX.append(np.array([sid[stunden[i]] for i in sel], np.int64))
            Z.append(zz[sel]); S.append(ss[sel]); RO.append(ro[sel])
        if not IDX:
            continue
        IDX = np.concatenate(IDX); Z = np.concatenate(Z)
        S = np.concatenate(S); RO = np.concatenate(RO)
        # ── auf das Fenster einschraenken (--ab) ───────────────────
        if AB_IDX[0]:
            im = IDX >= AB_IDX[0]
            IDX, Z, S, RO = IDX[im], Z[im], S[im], RO[im]
            if len(IDX) < 10 * MIND_JE_FUENFTEL:
                print("  zu wenig Anker im Fenster - uebersprungen")
                continue
        r = np.where(Z, crv, np.where(S, -1.0, np.nan_to_num(RO)))
        er_g = float(r.mean())

        print()
        print("=" * 100)
        print("CRV %.1f · H%d · %d Anker · GESAMT E[R] brutto %+.5f"
              % (crv, H, len(IDX), er_g))

        for name, reihe in regime.items():
            w = reihe[IDX]
            gut = np.isfinite(w)
            if gut.sum() < 5 * MIND_JE_FUENFTEL:
                print("  %-16s zu wenig belegt" % name)
                continue

            def _wirkung(f, maske):
                """-> (E[R] je Fuenftel, Spanne bestes gegen Mittel)."""
                m = maske & (f >= 0)
                if m.sum() < 5 * MIND_JE_FUENFTEL:
                    return None, np.nan, np.nan
                ff = f[m]; rr = r[m]
                n5 = np.bincount(ff, minlength=5).astype(float)
                if (n5 < MIND_JE_FUENFTEL).any():
                    return None, np.nan, np.nan
                e5 = np.bincount(ff, weights=rr, minlength=5) / n5
                return e5, float(e5.max()), float(e5.max() - e5.mean())

            f_r = np.where(gut, _fuenftel_rueckschau(
                np.where(gut, w, np.nan)), -1)
            e_r, best_r, sp_r = _wirkung(f_r.astype(np.int8), gut)

            f_k = _fuenftel_kausal(np.where(gut, w, np.nan), IDX)
            kausal_ok = gut & (IDX >= KAUSAL_ANLAUF)
            e_k, best_k, sp_k = _wirkung(f_k, kausal_ok)

            # ── NULLWELT: zyklische Verschiebung ──────────────────────
            # ⚠️ `hash()` ist zwischen Python-Laeufen NICHT stabil
            # (PYTHONHASHSEED) - damit waere die Messung nicht
            # reproduzierbar. R-R11 verlangt sie. Deshalb ein
            # stabiler Hash aus den Zeichen des Namens.
            saat_name = sum((i + 1) * ord(c)
                            for i, c in enumerate(name)) % 9973
            rng = np.random.default_rng(SAAT + H + int(100 * crv)
                                        + saat_name)
            T = len(reihe)
            nullw = []
            for _ in range(N_NULL):
                v = int(rng.integers(MIND_VERSATZ, max(MIND_VERSATZ + 1,
                                                       T - MIND_VERSATZ)))
                # ⚠️ NUR die belegten Werte rotieren - bei einem rohen
                # np.roll wandern die NaN mit, und dann laeuft die Nullwelt
                # auf einer anderen Ankermenge als die Messung.
                verschoben = np.full(T, np.nan)
                belegt = np.flatnonzero(np.isfinite(reihe))
                if len(belegt) > 1:
                    verschoben[belegt] = np.roll(reihe[belegt],
                                                 v % len(belegt))
                wv = verschoben[IDX]
                gv = np.isfinite(wv)
                fv = np.where(gv, _fuenftel_rueckschau(
                    np.where(gv, wv, np.nan)), -1).astype(np.int8)
                _e, _b, sp = _wirkung(fv, gv)
                if np.isfinite(sp):
                    nullw.append(sp)
            if len(nullw) < 10:
                print("  %-16s Nullband nicht zu bilden" % name)
                continue
            nullw = np.array(nullw)
            nullpunkt = float(nullw.mean())
            grenze90 = float(np.percentile(nullw, NULL_PERZ))

            print("  %-16s Nullpunkt %+.5f · %d. Perz %+.5f"
                  % (name, nullpunkt, int(NULL_PERZ), grenze90))
            # ⚠️⚠️ NUR die KAUSALE Fassung zaehlt fuers Urteil. Der letzte
            # Lauf zaehlte beide und verdoppelte damit die Tests kuenstlich -
            # Rueckschau und kausal teilen fast dieselbe Ordnung, sind also
            # keine zwei unabhaengigen Beobachtungen. Die Rueckschau bleibt
            # als Diagnose (Ueberanpassungsverdacht), nicht als Beweis.
            if np.isfinite(sp_k):
                JE_MERKMAL.setdefault(name, [0, 0])
                JE_MERKMAL[name][1] += 1
                if sp_k > grenze90:
                    JE_MERKMAL[name][0] += 1
            if e_r is not None:
                print("      RUECKSCHAU  E[R] je Fuenftel %s"
                      % " ".join("%+7.4f" % x for x in e_r))
                print("                  Spanne %+.5f  %s  ·  bestes "
                      "Fuenftel %+.5f  %s"
                      % (sp_r,
                         "✔ ordnet" if sp_r > grenze90
                         else "- im Nullband",
                         best_r,
                         # ⚠️ TRAEGT nur, wenn auch GEORDNET wird - ein
                         # bestes Fuenftel aus einer Ordnung im Nullband
                         # ist Zufall, nicht eine Lage.
                         ("⭐⭐ TRAEGT" if best_r > 0
                          else "⛔ traegt nicht") if sp_r > grenze90
                         else "(ohne Ordnung bedeutungslos)"))
            if e_k is not None:
                print("      ⭐ KAUSAL     E[R] je Fuenftel %s"
                      % " ".join("%+7.4f" % x for x in e_k))
                print("                  Spanne %+.5f  %s  ·  bestes "
                      "Fuenftel %+.5f  %s"
                      % (sp_k,
                         "✔ ordnet" if sp_k > grenze90
                         else "- im Nullband",
                         best_k,
                         ("⭐⭐ TRAEGT" if best_k > 0
                          else "⛔ traegt nicht") if sp_k > grenze90
                         else "(ohne Ordnung bedeutungslos)"))
                if np.isfinite(sp_r) and np.isfinite(sp_k):
                    print("                  ➜ Rueckschau/kausal "
                          "%.2f  %s"
                          % (sp_r / sp_k if sp_k else float("inf"),
                             "⚠ kausal deutlich schwaecher - "
                             "Ueberanpassungsverdacht"
                             if sp_k < 0.5 * sp_r else "✔ haelt kausal"))
            else:
                print("      ⭐ KAUSAL     zu duenn (Anlauf %d Stunden)"
                      % KAUSAL_ANLAUF)

    print()
    print("=" * 100)
    print("⭐⭐⭐ URTEIL - je Merkmal gegen die KONTROLLVERTEILUNG")
    print("=" * 100)
    print("  ⚠ Der letzte Lauf verglich die GEPOOLTE Quote gegen den")
    print("     Sollwert 10 % und meldete *Nullwelt geeicht*. Das beantwortet")
    print("     die falsche Frage: gepoolt verschwand, dass eine einzelne")
    print("     KONTROLLreihe 50 % erreichte, waehrend drei echte Merkmale")
    print("     bei 0 % lagen. Entschieden wird je Merkmal gegen die")
    print("     VERTEILUNG der Kontrollen.")
    print()
    kontrollen = sorted((v[0] / v[1]) for k, v in JE_MERKMAL.items()
                        if k.startswith("zufall") and v[1])
    echte = {k: v for k, v in JE_MERKMAL.items()
             if not k.startswith("zufall") and v[1]}
    if not kontrollen or not echte:
        print("  ⛔ zu wenig Daten fuer ein Urteil")
        return 1
    hoechste = kontrollen[-1]
    print("  KONTROLLREIHEN (%d): Quoten %s"
          % (len(kontrollen),
             " ".join("%.0f%%" % (100 * q) for q in kontrollen)))
    print("     hoechste %.0f %% · Median %.0f %%"
          % (100 * hoechste, 100 * kontrollen[len(kontrollen) // 2]))
    print()
    print("  Merkmal            Quote   ueber ALLEN Kontrollen?")
    for k in sorted(echte, key=lambda x: -echte[x][0] / echte[x][1]):
        tr, ts = echte[k]
        q = tr / ts
        drueber = sum(1 for kq in kontrollen if kq >= q)
        print("    %-16s %3d/%-3d %3.0f %%   %s"
              % (k, tr, ts, 100 * q,
                 "✔✔ JA - keine Kontrolle erreicht das"
                 if q > hoechste and q > 0 else
                 ("⛔ nein - %d von %d Kontrollen erreichen es"
                  % (drueber, len(kontrollen)) if q > 0 else "- kein Treffer")))
    print()
    print("  ⚠ Mit %d Kontrollreihen ist das 90. Perzentil der")
    print("     Kontrollverteilung nur grob schaetzbar. *Ueber allen")
    print("     Kontrollen* ist deshalb ein HINWEIS, noch kein Befund nach")
    print("     Messstandard - dafuer braeuchte es rund 40 Kontrollreihen."
          % ())
    print("     Aber es ist die richtige FRAGE, und die gepoolte war es nicht.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
