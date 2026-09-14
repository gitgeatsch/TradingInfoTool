# -*- coding: utf-8 -*-
"""Wie lange dauert ein Trade WIRKLICH bis zur ersten Marke?

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Warum (Befund 2.444, Nutzerfrage 13.09.2026)

Die Mail nennt "Haltedauer etwa 25 Handelstage". Die Zahl kommt aus
`entscheidungsrechnung._haltedauer_tage = (Zielweg / ATR)^2`. Bei der
ATR-Regel liegt der Stop bei 2,5 ATR, das Ziel bei CRV 2 also bei 5 ATR -
und 5^2 = 25 steht deshalb bei JEDEM solchen Trade. Der Docstring sagt
selbst: *"sie gehoert gegen die eigenen Reihen nachgerechnet - offener
Punkt"*. Der Nutzer erwartet 3-5 Tage; dokumentiert sind ein
Betriebshorizont von 3-5 Tagen (2.226, D3) und 0,3 Tage Median an 188
echten NB-Positionen (2.380-annahmen).

Die Zahl speist die FINANZIERUNG in der Mailrechnung. Sie wirkt NICHT auf
Bewertung, Hebel oder Stop (Regel 2).

## Was gemessen wird

    frageart      `geometrie` -> Menge = MESSUNIVERSUM (messnorm)
    Menge         messmenge.V1, Krypto-Reihen ueber 400 Tagen, Vorlauf 200
    Anker         60 je Symbol, Saat fest
    Geometrie     Stop = k x ATR, Ziel = CRV x k x ATR, CRV 2 - wie die
                  Kette. ATR aus `indicators.calculations.atr_wilder`,
                  DERSELBEN Funktion, kausal am Anker
    k             0,75 (stop_min_atr) · 1,0 · 1,5 · 2,0 · 2,5 (Betrieb) · 3,0
    Zielgroesse   TAGE BIS ZUR ERSTEN MARKE - Stop ODER Ziel, was zuerst
                  kommt. Gleichtag zaehlt als Stop (fuer die DAUER egal)
    Horizont      120 Tage (= `tage_max`). Wer bis dahin nichts trifft, ist
                  ZENSIERT - gezaehlt, nicht verworfen
    Kalender      ⚠️ Krypto handelt durchgehend, die Kerzen enthalten
                  Wochenenden: ein Tag hier ist ein KALENDERtag
    Band          Median, Block-Bootstrap ueber SYMBOLE, 1.000 Ziehungen, 95 %
    Richtung      LONG und SHORT getrennt

## Die Aussage, die geprueft wird - und wann sie gilt

    Liegt der Formelwert (CRV x k)^2 AUSSERHALB des Bands um den
    gemessenen Median?

    WIDERLEGT     ausserhalb, UND die Positivkontrolle ist bestanden
    VEREINBAR     innerhalb
    KEIN BEFUND   Positivkontrolle nicht bestanden - dann misst die
                  Anlage die Dauer nicht richtig, und jede Zahl ist wertlos

⚠️ Der Median ist nur definiert, wenn mehr als die Haelfte bis zum
Horizont aufloest - sonst steht dort "> 120", nicht eine Zahl.

## ⚠️ NACHTRAG NACH DEM VORABTEST (80 Symbole) - als Nachtrag benannt

Die vorab festgelegte Urteilsregel bleibt unveraendert. Der Vorabtest hat
aber gezeigt, dass die Formel dem Median ERSTAUNLICH NAHE kommt (k = 2,5:
23 Tage LONG, 27 SHORT, Formel 25) - die Baender sind nur so eng, dass
ein, zwei Tage schon "WIDERLEGT" ergeben. Zwei Spalten kommen deshalb
dazu, ausdruecklich NACH dem ersten Blick auf die Daten:

    Abweichung    Formel / Median - 1 - die PRAKTISCHE Groesse neben dem
                  statistischen Urteil
    ATR/sigma     Median des Verhaeltnisses ATR zu Tagesschwankung
                  (Standardabweichung der Schlusskursaenderung ueber 20
                  Tage) am Anker. Vermuteter Mechanismus: die Zeit bis zur
                  ERSTEN Schranke ist a x b in sigma; mit a = k x ATR/sigma
                  und b = CRV x a ergibt sich CRV x k^2 x (ATR/sigma)^2. Ist
                  ATR/sigma nahe Wurzel 2, landet man bei (CRV x k)^2 -
                  genau der Formel. Die Spalte prueft das.

## Kontrollen

    REPRODUKTION (R-R11)  Befund 2.435 Probe 2 meldete: bei 8 % Stop loesen
                          80 % der Anker innerhalb von 10 Tagen auf. Mit
                          DENSELBEN Ankern muss die neue Tagesrechnung
                          genau dieselbe Zahl liefern - sonst zaehlt sie
                          anders als die bestehende Anlage.
    POSITIVKONTROLLE      synthetische, driftfreie Reihen mit bekannter
                          Wahrheit: die erwartete Zeit bis zur ERSTEN von
                          zwei Schranken -a und +b ist bei Brownscher
                          Bewegung a x b (in Tagesschwankungen), mit
                          Korrektur fuer die Diskretisierung. 5 Saaten,
                          alle muessen auf 10 % treffen.
    GEGENPROBEN           beide Richtungen · nur ab 2023 (stehender Befund
                          zum Zeitfenster) · zweite Saat

AUFRUF:
    python messe_haltedauer.py
    python messe_haltedauer.py --schnell         # 80 Symbole
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

import messe_eigenschaft_beitrag as B
import messe_stopweite_historisch as M
import messmenge
import messnorm

KS = (0.75, 1.0, 1.5, 2.0, 2.5, 3.0)
CRV = 2.0
HORIZONT = 120
ANKER = 60
SAAT = 20260914
BOOTSTRAP = 1000
MARKEN_TAGE = (3, 5, 10, 20)
PK_SAATEN = 5
PK_TOLERANZ = 0.10


def austrittstag(hoch, tief, schluss, idx, stop_abst, ziel_abst, horizont,
                 short):
    """Tag der ersten Marke je Anker - vektorisiert ueber `idx`.

    `stop_abst`, `ziel_abst`: ABSOLUTE Abstaende je Anker (Arrays).
    Rueckgabe (tag, art): tag 1..horizont, bei Zensur horizont+1;
    art -1 Stop, +1 Ziel, 0 zensiert. Gleichtag zaehlt als Stop."""
    ein = schluss[idx]
    if short:
        stop, ziel = ein + stop_abst, ein - ziel_abst
    else:
        stop, ziel = ein - stop_abst, ein + ziel_abst
    n = len(idx)
    tag = np.full(n, horizont + 1, dtype=np.int64)
    art = np.zeros(n, dtype=np.int64)
    offen = np.ones(n, dtype=bool)
    for k in range(1, horizont + 1):
        j = idx + k
        gueltig = offen & (j < len(schluss))
        if not gueltig.any():
            break
        jj = np.minimum(j, len(schluss) - 1)
        h, t = hoch[jj], tief[jj]
        traf_s = gueltig & ((h >= stop) if short else (t <= stop))
        traf_z = gueltig & ((t <= ziel) if short else (h >= ziel)) & ~traf_s
        tag[traf_s | traf_z] = k
        art[traf_s] = -1
        art[traf_z] = 1
        offen &= ~(traf_s | traf_z)
    return tag, art


def waehle_anker(reihen, syms, anker, horizont, saat):
    """⚠️ EXAKT die Ankerwahl von `messe_stopweite_historisch.sammle` -
    Reihenfolge der Zufallszahlen eingeschlossen. Nur so ist die
    Reproduktion von 2.435 eine Pruefung und kein Zufall."""
    rng = np.random.default_rng(saat)
    aus = {}
    for sym in syms:
        c = reihen[sym]
        moegl = np.arange(M.VORLAUF, len(c) - horizont - 1)
        if len(moegl) < 5:
            continue
        aus[sym] = rng.choice(moegl, size=min(anker, len(moegl)), replace=False)
    return aus


def _arrays(r):
    return (np.array([x[2] for x in r], float), np.array([x[3] for x in r], float),
            np.array([x[1] for x in r], float))


def reproduktion(reihen, syms) -> tuple[bool, str]:
    """R-R11: dieselben Anker wie 2.435 Probe 2, dieselbe Zahl?"""
    _roh, _paar, _n, quote = M.sammle(reihen, syms, 60, 10, False,
                                      weiten=(0.08,), bezug=0.08)
    alt = quote[0.08][0], quote[0.08][1]
    anker = waehle_anker(reihen, syms, 60, 10, M.SAAT)
    auf = ges = 0
    for sym, idx in anker.items():
        h, t, c = _arrays(reihen[sym])
        tag, _art = austrittstag(h, t, c, idx, 0.08 * c[idx],
                                 CRV * 0.08 * c[idx], 10, False)
        auf += int((tag <= 10).sum())
        ges += len(idx)
    ok = (auf, ges) == alt
    return ok, ("2.435 Probe 2: %d von %d aufgeloest (%.1f %%) · neue "
                "Tagesrechnung: %d von %d (%.1f %%)"
                % (alt[0], alt[1], 100 * alt[0] / alt[1], auf, ges,
                   100 * auf / max(ges, 1)))


def positivkontrolle(pfade=2000, tage=200, teil=20) -> list:
    """Driftfreie Irrfahrt, Tagesschwankung 1, `teil` Unterschritte je Tag.

    Erwartete Zeit bis zur ersten von zwei Schranken -a, +b: a x b in der
    stetigen Brownschen Bewegung. Diskret ueberschiessen die Schranken um
    rho = 0,5826 x Schrittweite (Siegmund) - also (a+rho)(b+rho) - und der
    Tag wird erst am ENDE des Tages gezaehlt, im Mittel +0,5."""
    aus = []
    rho = 0.5826 / np.sqrt(teil)
    for a, b in ((1.0, 2.0), (2.5, 5.0)):
        erwartet = (a + rho) * (b + rho) + 0.5
        treffer = []
        for s in range(PK_SAATEN):
            rng = np.random.default_rng(777 + s)
            schritte = rng.normal(0.0, 1.0 / np.sqrt(teil), (pfade, tage * teil))
            pfad = np.cumsum(schritte, axis=1).reshape(pfade, tage, teil)
            hoch = np.concatenate([np.zeros((pfade, 1)), pfad.max(axis=2)], axis=1)
            tief = np.concatenate([np.zeros((pfade, 1)), pfad.min(axis=2)], axis=1)
            schl = np.concatenate([np.zeros((pfade, 1)), pfad[:, :, -1]], axis=1)
            # Pfade hintereinander, jeder mit eigenem Anker am Tag 0
            L = tage + 1
            idx = np.arange(pfade) * L
            tag, art = austrittstag(hoch.ravel(), tief.ravel(), schl.ravel(),
                                    idx, np.full(pfade, a), np.full(pfade, b),
                                    tage - 1, False)
            gemessen = float(tag[art != 0].mean())
            treffer.append((gemessen, abs(gemessen - erwartet) / erwartet
                            <= PK_TOLERANZ, float((art == 0).mean())))
        aus.append((a, b, erwartet, treffer))
    return aus


def _median_band(je_symbol: list, saat: int) -> tuple:
    """Median ueber alle Anker + Block-Bootstrap ueber Symbole.

    Zensierte stehen als horizont+1 drin - der Median bleibt richtig,
    solange weniger als die Haelfte zensiert ist."""
    alle = np.concatenate(je_symbol)
    med = float(np.median(alle))
    rng = np.random.default_rng(saat)
    S = len(je_symbol)
    meds = np.empty(BOOTSTRAP)
    for i in range(BOOTSTRAP):
        meds[i] = np.median(np.concatenate(
            [je_symbol[j] for j in rng.integers(0, S, S)]))
    meds.sort()
    return med, float(meds[int(0.025 * BOOTSTRAP)]), float(meds[int(0.975 * BOOTSTRAP)])


def lauf(reihen, syms, short: bool, saat: int = SAAT, ab: str | None = None,
         kopf: str = "") -> dict:
    from indicators.calculations import atr_wilder
    anker = waehle_anker(reihen, syms, ANKER, HORIZONT, saat)
    je_k = {k: {"tage": [], "art": []} for k in KS}
    verhaeltnis: list = []
    for sym, idx in anker.items():
        r = reihen[sym]
        if ab:
            idx = idx[[r[i][0] >= ab for i in idx]]
            if len(idx) == 0:
                continue
        h, t, c = _arrays(r)
        res = atr_wilder(h, t, c)
        if not res.available:
            continue
        atr = np.asarray(res.value, float)[idx]
        ok = np.isfinite(atr) & (atr > 0)
        idx, atr = idx[ok], atr[ok]
        if len(idx) == 0:
            continue
        _d = np.diff(c)
        _sig = np.array([np.std(_d[i - 20:i]) if i >= 21 else np.nan
                         for i in idx])
        with np.errstate(invalid="ignore", divide="ignore"):
            verhaeltnis.extend((atr / _sig)[np.isfinite(atr / _sig)].tolist())
        for k in KS:
            tag, art = austrittstag(h, t, c, idx, k * atr, CRV * k * atr,
                                    HORIZONT, short)
            je_k[k]["tage"].append(tag)
            je_k[k]["art"].append(art)

    print()
    print("=" * 110)
    print("%s%s   |   %d Symbole" % (kopf, "SHORT" if short else "LONG",
                                     len(je_k[KS[0]]["tage"])))
    print("=" * 110)
    q = float(np.median(verhaeltnis)) if verhaeltnis else float("nan")
    print("  %-5s %7s %8s │ %5s %5s %5s %5s │ %-22s %6s │ %6s %6s %7s %-10s"
          % ("k ATR", "Anker", "zensiert", "<=3", "<=5", "<=10", "<=20",
             "MEDIAN [Band]", "Stop%", "Formel", "Abw.", "a x b", "URTEIL"))
    print("  " + "-" * 106)
    aus = {}
    for k in KS:
        tage = np.concatenate(je_k[k]["tage"])
        art = np.concatenate(je_k[k]["art"])
        n = len(tage)
        zens = float((art == 0).mean())
        anteile = [float((tage <= m).mean()) for m in MARKEN_TAGE]
        formel = (CRV * k) ** 2
        if zens >= 0.5:
            med = lo = hi = float("nan")
            band = "> %d (zensiert)" % HORIZONT
            urteil = "KEIN MEDIAN"
        else:
            med, lo, hi = _median_band(je_k[k]["tage"], saat + int(k * 100))
            band = "%4.0f [%3.0f;%3.0f]" % (med, lo, hi)
            urteil = ("WIDERLEGT" if (formel < lo or formel > hi)
                      else "vereinbar")
        stop_anteil = float((art == -1).sum() / max(1, (art != 0).sum()))
        aus[k] = {"n": n, "zens": zens, "anteile": anteile, "med": med,
                  "lo": lo, "hi": hi, "formel": formel, "urteil": urteil,
                  "stop": stop_anteil}
        abw = (formel / med - 1.0) if med == med and med > 0 else float("nan")
        ab_vorh = CRV * (k * q) ** 2 + 0.5
        aus[k].update({"abw": abw, "ab": ab_vorh})
        print("  %5.2f %7d %7.1f %% │ %4.0f%% %4.0f%% %4.0f%% %4.0f%% │ %-22s %5.0f%% │ %6.1f %+5.0f%% %7.1f %s"
              % (k, n, 100 * zens, *(100 * x for x in anteile), band,
                 100 * stop_anteil, formel, 100 * abw, ab_vorh, urteil))
    print("  ➤ ATR/sigma am Anker: Median %.3f (Wurzel 2 = 1,414). "
          "Spalte ,a x b' = CRV x (k x ATR/sigma)^2 + 0,5 - die Vorhersage "
          "aus der Positivkontrolle, in ATR umgerechnet." % q)
    aus["atr_sigma"] = q
    return aus


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--schnell", action="store_true")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 110)
    print("WIE LANGE DAUERT EIN TRADE BIS ZUR ERSTEN MARKE?  (Befund 2.444)")
    print("=" * 110)
    print(messnorm.standardzeile())
    print(messmenge.zeile())
    print("frageart `geometrie` -> Menge = Messuniversum · Zielgroesse: Tage bis "
          "zur ersten Marke · CRV %.1f · Horizont %d · Band: Median, Bootstrap "
          "ueber Symbole" % (CRV, HORIZONT))
    print("⚠️ Krypto-Kerzen enthalten Wochenenden - ein Tag ist ein KALENDERtag.")

    reihen = B.lade()
    syms = M.symbolliste(reihen, 80 if a.schnell else 10000)

    print()
    print("POSITIVKONTROLLE - misst die Anlage eine BEKANNTE Dauer?")
    print("-" * 110)
    pk_ok = True
    for aa, bb, erw, tr in positivkontrolle():
        alle = all(x[1] for x in tr)
        pk_ok &= alle
        print("  Schranken -%.1f / +%.1f   erwartet %.2f Tage   gemessen %s   %s"
              % (aa, bb, erw, " ".join("%.2f" % x[0] for x in tr),
                 "%d/%d BESTANDEN" % (sum(x[1] for x in tr), len(tr))
                 if alle else "✖ NICHT BESTANDEN"))
    print("  ➤ Die Kontrolle rechnet in TAGESSCHWANKUNGEN (sigma). Die Formel "
          "der Mail rechnet in ATR -")
    print("    ein direkter Vergleich waere falsch; er steht unten im Hauptlauf "
          "samt Umrechnung.")

    print()
    print("REPRODUKTION (R-R11)")
    print("-" * 110)
    rep_ok, rep_txt = reproduktion(reihen, syms)
    print("  %s   %s" % (rep_txt, "✔ IDENTISCH" if rep_ok else "✖ ABWEICHUNG"))

    if not (pk_ok and rep_ok):
        print()
        print("⚠️⚠️ KEIN BEFUND - Positivkontrolle oder Reproduktion nicht "
              "bestanden. Die Zahlen unten sind nicht zu verwenden.")

    lauf(reihen, syms, False, kopf="HAUPTLAUF - ")
    lauf(reihen, syms, True, kopf="HAUPTLAUF - ")
    lauf(reihen, syms, False, ab="2023-01-01", kopf="GEGENPROBE ab 2023 - ")
    lauf(reihen, syms, False, saat=SAAT + 99, kopf="GEGENPROBE Saat B - ")


if __name__ == "__main__":
    main()
