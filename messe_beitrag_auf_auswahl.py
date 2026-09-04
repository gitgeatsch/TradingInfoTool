# -*- coding: utf-8 -*-
"""N-31: Tragen die Beitraege auf der SELEKTIERTEN Menge? (04.09.2026)

Vorabfestlegung: `Anforderungen_Umbau_28_08.md`, Abschnitt **N-31**.

## Warum simuliert wird

Aus dem NB-Export (9.474 Rollen-Laeufe): die Beitraege wirken auf **1.849
von 124.194** Ankern (1,5 %) - kalibriert wurden sie auf 612.000-724.000
ROHEN Ankern. Und die beitragsbasierte Entscheidung laeuft erst seit dem
02.09.: im Export sind das **41 Entscheidungen**. Aus Produktionsdaten ist
die Frage also nicht beantwortbar.

⚠️ Stehende Vorgabe: *„was wir nicht haben, simulieren wir."*

## Die Selektionsregel - AUS DEM BETRIEBSLOG ABGELESEN

    "Rang N von 41 nach der Entwicklung der letzten 250 Handelstage"
    Rang 2 nur 11x verworfen, Rang 3 550x   ->  k = 2 von ~41  ~  5 %

## Die drei Vorsichtsmassnahmen, jede aus einem frueheren Fehler

  2.109  DIE TAGESKLAMMER TRAEGT HIER NICHT. Bei 5 % je Tag bleiben zu
         wenige Werte fuer einen Vergleich INNERHALB des Tages. Deshalb
         gepoolt gemessen UND gepoolt gemischt - die Kontrolle durchlaeuft
         dieselbe Verengung wie der Kandidat.
  2.105  GEPAARTER Vergleich: gemessen wird die DIFFERENZ selektiert minus
         frei, nicht zwei Baender nebeneinander.
  2.88   POSITIVKONTROLLE AUF DIE DIFFERENZ. In F-183 fand die Anlage
         einen aufgepraegten Abfall von 0,02 R bei Funding NICHT - dort
         war "kein Abfall" deshalb keine Aussage. Feuert sie hier nicht,
         gilt derselbe Vorbehalt.

## ⚠️ Die Naeherung, benannt

Die Produktion waehlt 2 aus ~41 WATCHLIST-Werten; die Historie kennt diese
Watchlist nicht rueckwirkend. Nachgebaut wird die SELEKTIONSSTAERKE
(oberste 5 % je Tag), nicht die absolute Zahl - die waere je Tag zu klein
fuer jede Statistik.

    python messe_beitrag_auf_auswahl.py [--selbsttest]
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                         # noqa: E402
import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_funding_niveau as F                              # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messe_regel_wirksamkeit as W                           # noqa: E402

HORIZONT = 20
ZIEHUNGEN = 400          # Bootstrap-Ziehungen fuer die gepoolte Rechnung
MISCHUNGEN = 10          # 2.104: eine Ziehung ist kein Nullpunkt
# ⚠️ VORAB festgelegt. Die ENTSCHEIDUNG haengt an 0.05 (die Produktion);
# die uebrigen sind Einordnung (Dosis-Wirkungs-Kurve), keine freie Suche.
STUFEN = (0.05, 0.10, 0.20, 1.00)
SAAT = 20260904


def momentum250(reihen: dict) -> dict:
    """Der Rang, nach dem die AUSWAHL waehlt: Entwicklung ueber 250 Tage.

    ⚠️ Genau die Groesse aus dem Betriebslog - nicht eine aehnliche.
    Nachlaufend, kein Blick nach vorn.
    """
    aus: dict = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh], float)
        for i in range(250, len(c)):
            if c[i - 250] > 0:
                aus.setdefault(tage[i], {})[sym] = float(c[i] / c[i - 250] - 1.0)
    return aus


def _auswahl_maske(zeilen: list, mom_tag: dict, anteil: float,
                   mische_auswahl=None) -> np.ndarray | None:
    """Welche Anker des Tages ueberstehen die AUSWAHL? (Bool-Maske)

    ⚠️ `anteil >= 1.0` heisst "keine Auswahl" - dann ist ALLES gewaehlt,
    auch bei `mische_auswahl`. Das ist kein Sonderfall, sondern die
    Definition; die Negativkontrolle wirkt hier ueber den RANG (siehe
    `sammle`), nicht ueber die Auswahl.
    """
    n = len(zeilen)
    if anteil >= 1.0:
        return np.ones(n, bool)
    da = np.array([x["sym"] in mom_tag for x in zeilen])
    if da.sum() < 4:
        return None
    k = max(1, int(round(int(da.sum()) * anteil)))
    m = np.zeros(n, bool)
    idx = np.flatnonzero(da)
    if mische_auswahl is not None:
        m[mische_auswahl.permutation(idx)[:k]] = True
    else:
        w = np.array([mom_tag[zeilen[i]["sym"]] for i in idx], float)
        m[idx[np.argsort(-w)[:k]]] = True
    return m


def sammle(je_tag: dict, mom: dict, anteil: float,
           mische_rang=None, mische_auswahl=None,
           pflanze: float | None = None) -> dict:
    """Je Kalendertag die GEWAEHLTEN Anker als (oben?, Ergebnis).

    ⚠️⚠️ KEINE Tagesmediane mehr. Der erste Anlauf (04.09.) bildete je Tag
    einen Median - bei 5 % von ~40 Werten sind das ZWEI Anker, also ein
    Einzelwert gegen einen Einzelwert. Das erzeugte +0,4469 R, das
    Achtzehnfache des registrierten Beitrags: reines Rauschen.

    ⚠️ DER RANG KOMMT AUS DEM VOLLEN TAGESQUERSCHNITT, erst danach wird
    verengt - genau wie `marktrang` in der Produktion ueber die Messbasis
    rangt und nicht ueber die Auswahl.
    """
    aus: dict = {}
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 12:
            continue
        kz = np.array([x["kennzahl"] for x in zeilen], float)
        r = W.rang(kz)
        if mische_rang is not None:
            r = mische_rang.permutation(r)
        oben = r >= W.GRENZE
        y = np.array([x["in_r"] for x in zeilen], float)
        if pflanze:
            # ⚠️⚠️ VORZEICHEN, und es war im ersten Anlauf FALSCH herum.
            #
            # Die Kennzahl ist `median(frei) - median(gesperrt)`. Wer die
            # GESPERRTEN schlechter macht (`- pflanze`), macht die Regel
            # BESSER - die Kennzahl STEIGT. Genau das tat der erste Anlauf,
            # beschriftet als "Abfall aufgepraegt": +0,3679 -> +0,3879.
            # Geprueft werden sollte aber, ob die Anlage einen ABFALL findet.
            #
            # Ein Abfall entsteht, wenn die Gesperrten BESSER werden - dann
            # trennt die Regel weniger, und die Kennzahl faellt.
            y = y.copy()
            y[oben] = y[oben] + float(pflanze)
        m = _auswahl_maske(zeilen, mom.get(tag) or {}, anteil, mische_auswahl)
        if m is None or not m.any():
            continue
        aus[tag] = (oben[m], y[m])
    return aus


def _kennzahl(gesammelt: dict, tage: list) -> float:
    """GEPOOLT: Median(frei) - Median(ALLE) - die registrierte Definition.

    ⚠️⚠️ NICHT gegen die GESPERRTEN. `messe_regel_wirksamkeit.wirkung()`
    rechnet `median(frei) - median(alle)`; der erste Anlauf verglich frei
    gegen gesperrt und lag damit um Faktor 3,8 daneben (bei BEIDEN
    Beitraegen gleich - die Signatur eines Definitionsunterschieds).
    """
    frei, alle = [], []
    for t in tage:
        o, y = gesammelt[t]
        frei.append(y[~o])
        alle.append(y)
    f = np.concatenate(frei) if frei else np.array([])
    a = np.concatenate(alle) if alle else np.array([])
    if f.size < 5 or a.size < 10:
        return float("nan")
    return float(np.median(f) - np.median(a))


def urteil(name: str, gesammelt: dict, rng) -> dict | None:
    """Block-Bootstrap ueber KALENDERTAGE - nicht ueber Anker.

    ⚠️ Ueber Anker zu ziehen waere der zweite Fehler des ersten Anlaufs:
    benachbarte Anker desselben Tages haengen zusammen, die Baender
    waeren zu eng (2.107).
    """
    tage = sorted(gesammelt)
    if len(tage) < 60:
        print("    %-40s zu wenige Tage (%d)" % (name, len(tage)))
        return None
    echt = _kennzahl(gesammelt, tage)
    n = len(tage)
    boot = []
    for _ in range(ZIEHUNGEN):
        zieh = [tage[i] for i in rng.integers(0, n, n)]
        v = _kennzahl(gesammelt, zieh)
        if np.isfinite(v):
            boot.append(v)
    if len(boot) < 50:
        print("    %-40s Bootstrap zu duenn" % name)
        return None
    u, o = np.quantile(boot, [0.025, 0.975])
    anker = sum(len(y) for _o, y in gesammelt.values())
    urt = "TRAEGT" if u > 0 else ("UMGEKEHRT" if o < 0 else "nicht trennbar")
    print("    %-40s %+.4f R  [%+.4f .. %+.4f]  %d Tage · %d Anker  %s"
          % (name, echt, u, o, n, anker, urt))
    return {"mittel": echt, "unten": float(u), "oben": float(o),
            "traegt": bool(u > 0), "tage": n}


def _kontrolle(je_tag, mom, anteil, rng) -> None:
    """Die Kennzahl je Mischung EINZELN, dann gemittelt (2.104).

    ⚠️ Der erste Anlauf haengte zehn Mischungen aneinander - n stieg auf
    das Zehnfache, das Band schrumpfte um Faktor drei, und die Kontrolle
    meldete Befunde, die reine Rechenartefakte waren.
    """
    werte = []
    for s in range(MISCHUNGEN):
        g = sammle(je_tag, mom, anteil,
                   mische_rang=np.random.default_rng(SAAT + 900 + s))
        t = sorted(g)
        if len(t) >= 60:
            v = _kennzahl(g, t)
            if np.isfinite(v):
                werte.append(v)
    if not werte:
        print("    %-40s keine verwertbare Mischung" % "  Negativkontrolle")
        return
    a = np.array(werte)
    print("    %-40s %+.4f R  (Spanne %+.4f .. %+.4f ueber %d Mischungen)"
          % ("  Negativkontrolle (Rang gemischt)", a.mean(), a.min(),
             a.max(), a.size))


def gepaart(g_a: dict, g_b: dict, rng, name: str) -> dict | None:
    """2.105 - die DIFFERENZ, gepaart ueber die GEMEINSAMEN Kalendertage."""
    tage = sorted(set(g_a) & set(g_b))
    if len(tage) < 60:
        print("    %-40s zu wenige gemeinsame Tage (%d)" % (name, len(tage)))
        return None
    n = len(tage)
    echt = _kennzahl(g_a, tage) - _kennzahl(g_b, tage)
    boot = []
    for _ in range(ZIEHUNGEN):
        zieh = [tage[i] for i in rng.integers(0, n, n)]
        v = _kennzahl(g_a, zieh) - _kennzahl(g_b, zieh)
        if np.isfinite(v):
            boot.append(v)
    if len(boot) < 50:
        print("    %-40s Bootstrap zu duenn" % name)
        return None
    u, o = np.quantile(boot, [0.025, 0.975])
    urt = ("ABFALL" if o < 0 else ("ZUWACHS" if u > 0 else "nicht trennbar"))
    print("    %-40s %+.4f R  [%+.4f .. %+.4f]  %d Tage  %s"
          % (name, echt, u, o, n, urt))
    return {"mittel": echt, "unten": float(u), "oben": float(o),
            "abfall": bool(o < 0)}


def bericht(klar: str, je_tag: dict, mom: dict, rng) -> None:
    print()
    print("=" * 96)
    print("%s  —  REGEL: kein Einstieg im obersten 20 %%   [H%d]" % (klar, HORIZONT))
    print("=" * 96)
    for anteil in STUFEN:
        etikett = ("KEINE Auswahl (frei)" if anteil >= 1.0
                   else "oberste %2.0f %% nach 250-Tage-Momentum" % (100 * anteil))
        marke = "   <- die PRODUKTION" if abs(anteil - 0.05) < 1e-9 else ""
        print("  %s%s" % (etikett, marke))
        urteil("  NETTO", sammle(je_tag, mom, anteil), rng)
        _kontrolle(je_tag, mom, anteil, rng)
        print()
    print("  " + "-" * 92)
    print("  DER GEPAARTE VERGLEICH (2.105) — faellt der Beitrag auf der Auswahl ab?")
    g5 = sammle(je_tag, mom, 0.05)
    gv = sammle(je_tag, mom, 1.00)
    gepaart(g5, gv, rng, "  5 % minus frei")
    print()
    print("  ⚠️ POSITIVKONTROLLE AUF DIE DIFFERENZ (2.88 / F-183):")
    for s in (0.02, 0.05):
        g5p = sammle(je_tag, mom, 0.05, pflanze=s)
        gepaart(g5p, gv, rng,
                "     Abfall %.2f R aufgepraegt (nur auf 5 %%)" % s)
    print()
    print("     LESART: findet die Anlage schon -0,02 R NICHT, ist 'kein")
    print("     Abfall' hier KEINE Aussage (derselbe Vorbehalt wie F-183).")


def selbsttest() -> bool:
    """Zwei Welten mit bekannter Antwort.

    A: der Beitrag wirkt UEBERALL gleich  -> kein Abfall zu finden
    B: der Beitrag wirkt NUR ausserhalb der Auswahl -> Abfall MUSS kommen
    """
    ok = True
    for welt, nur_ausserhalb in (("A (wirkt ueberall)", False),
                                 ("B (wirkt NUR ausserhalb der Auswahl)", True)):
        rng = np.random.default_rng(5)
        je_tag, mom = {}, {}
        for t in range(500):
            n = 40
            kz = rng.uniform(size=n)
            mo = rng.uniform(size=n)
            tag = "t%03d" % t
            zeilen, mt = [], {}
            grenze = np.quantile(mo, 0.95)
            for i in range(n):
                sym = "S%02d" % i
                gewaehlt = mo[i] >= grenze
                straf = -0.30 if kz[i] > 0.8 else 0.0
                if nur_ausserhalb and gewaehlt:
                    straf = 0.0
                zeilen.append({"sym": sym, "kennzahl": float(kz[i]),
                               "in_r": float(rng.normal(straf, 0.5))})
                mt[sym] = float(mo[i])
            je_tag[tag] = zeilen
            mom[tag] = mt
        r2 = np.random.default_rng(3)
        g5 = sammle(je_tag, mom, 0.05)
        gv = sammle(je_tag, mom, 1.00)
        e = gepaart(g5, gv, r2, "  SELBSTTEST %s" % welt)
        gefunden = bool(e and e["abfall"])       # Abfall = Differenz NEGATIV
        if gefunden != nur_ausserhalb:
            print("  ✖ FEHLER: erwartet %s"
                  % ("Abfall" if nur_ausserhalb else "KEIN Abfall"))
            ok = False
    print("  ✔ Selbsttest bestanden" if ok else "  ✖ SELBSTTEST FEHLGESCHLAGEN")
    return ok


def main() -> int:
    if "--selbsttest" in sys.argv:
        return 0 if selbsttest() else 1
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    mom = momentum250(reihen)
    print("%d Krypto-Reihen · Momentum-Rang fuer %d Kalendertage"
          % (len(reihen), len(mom)))
    rng = np.random.default_rng(SAAT)
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    for klar, art, quelle in (("FUNDING-Rang", "funding", F.lade_funding()),
                              ("TURNOVER-Rang", "turnover", menge)):
        je_tag = K.baue(reihen, art, quelle, horizont=HORIZONT)
        bericht(klar, je_tag, mom, rng)
    return 0


if __name__ == "__main__":
    sys.exit(main())
