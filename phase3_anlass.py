# -*- coding: utf-8 -*-
"""DIE ANLASS-SCHWELLE MESSEN (19.09.2026, Schritt 59, nach S3).

Die Anlass-Stufe ist die einzige Bremse der Kette, die KEINE Luecke
hinterlaesst: sie verwirft mit der Begruendung *"Faktensatz unveraendert"* -
wo sich nichts geaendert hat, geht auch keine Bewertung verloren
(2.464-unterdrueckung, Nutzervorgabe 19.09.). Deshalb ist sie der Kandidat,
der die Wiederholungssperre ersetzen koennte.

Sie hat genau ZWEI Regler, beide heute auf Vorgabe:

    ignoriere_bloecke: []     Bloecke, deren Aenderung nicht als neue Frage zaehlt
    mindest_bloecke:   1      wie viele Bloecke sich bewegt haben muessen

⚠️ BEIDE KOENNEN NUR MEHR SPERREN, NIE WENIGER. Ein identischer Abdruck ist
immer eine Wiederholung; die Regler entscheiden nur, was als "geaendert"
zaehlt.

Die `config.yaml` haelt die offene Frage selbst fest: *"Marken tragen 59,3 %
aller Blockaenderungen. Sie sind kursnah und springen, sobald ein Tick ueber
eine Clustergrenze laeuft. Offen bleibt, ob das eine neue Lage ist oder
Rauschen; das entscheidet nur eine Messung mit umgestelltem Regler."*

## Zwei Fragen, zwei Guetegrade

    A ZAEHLUNG    Wie viele Fragen bleiben je Einstellung? Rein deskriptiv -
                  und die Zahl, an der das Kontingent haengt (500/Tag).

    B WIRKUNG     Sind die zusaetzlich gesperrten Lagen RUHIGER als die
                  bleibenden? Zielgroesse ist der BETRAG der Folgebewegung
                  in R - wo nichts passiert, kostet Sperren nichts.
                  ⚠️ Gegen eine Nullwelt, die gleich viele zufaellig sperrt.

⚠️ HINWEIS, KEIN NORMURTEIL. Die Beobachtungen decken 34 Tage ab
(15.08. bis 18.09.), die Kurse 71 - beides ein Marktregime, 59 Symbole. Fuer
den Horizont der Kette (H20) reicht das nicht; gemessen werden 6 und 24
Stunden. R-R11: das kann keinen Tagesbefund umstossen.

⚠️ RUFT DIE ECHTE FUNKTION. Die Varianten laufen durch `anlass.sperrt()`,
nicht durch eine Nachbildung - sonst misst man seine eigene Kopie.
⚠️ Nur lesend gegen die Tagessicherung der Produktion. Kein LLM.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import sys
import time

import numpy as np

from agent import anlass as A
import phase3_takt as T

STUNDEN = (6.0, 24.0)
NULL_ZIEHUNGEN = 40
SAAT = 20260919
VORBEHALT = ("HINWEIS, kein Normurteil: 34 Tage Beobachtungen, 59 Symbole, "
             "ein Marktregime, Horizonte 6 und 24 h statt H20 (R-R11)")

# Die Varianten. `None` heisst: der laufende Stand.
VARIANTEN = (
    ("laufend (mindest 1, nichts ignoriert)", [], 1),
    ("ohne marken", ["marken"], 1),
    ("mindestens 2 Bloecke", [], 2),
    ("mindestens 3 Bloecke", [], 3),
    ("ohne marken UND mindestens 2", ["marken"], 2),
    ("ohne marken UND mindestens 3", ["marken"], 3),
)


def lade_beobachtungen(con) -> list:
    """Die Beobachtungen, so wie `sperrt()` sie erwartet."""
    aus = []
    for (ts, sym, gleich_asset, gleich_voll, alter, bloecke) in con.execute(
            "SELECT erfasst_am, symbol, gleich_asset, gleich_voll,"
            " alter_stunden, geaenderte_bloecke FROM anlass_beobachtung"
            " WHERE alter_stunden IS NOT NULL"):
        t = T._zeit(ts)
        if t is None:
            continue
        roh = bloecke or ""
        if roh.startswith("["):
            try:
                liste = list(json.loads(roh))
            except Exception:
                liste = []
        else:
            liste = [x.strip() for x in roh.split(",") if x.strip()]
        aus.append({
            "zeit": t, "symbol": sym,
            "gleich_asset": bool(gleich_asset), "gleich_voll": bool(gleich_voll),
            "alter_stunden": float(alter), "geaenderte_bloecke": liste})
    return aus


def _konfig(ignoriere: list, mindest: int) -> dict:
    return {"anlass": {"aktiv": True, "abdruck": "asset",
                       "hoechstalter_stunden": A.HOECHSTALTER_STUNDEN,
                       "ignoriere_bloecke": list(ignoriere),
                       "mindest_bloecke": int(mindest)}}


def sperrt_maske(beob: list, ignoriere: list, mindest: int) -> np.ndarray:
    """Welche Beobachtungen wuerde diese Einstellung sperren?

    ⚠️ ueber `anlass.sperrt()` - die Funktion, die auch live entscheidet."""
    cfg = _konfig(ignoriere, mindest)
    return np.array([bool(A.sperrt(b, cfg)[0]) for b in beob], bool)


def bewegung_betrag(kurse: dict, atr: dict, beob: list) -> dict:
    """Der BETRAG der Folgebewegung je Beobachtung, in R.

    ⚠️ BETRAG, NICHT RICHTUNG: eine Beobachtung ist noch kein Signal, sie hat
    keine Richtung. Gefragt ist, ob ueberhaupt etwas passiert - wo nichts
    passiert, kostet Sperren nichts."""
    aus = {k: np.full(len(beob), np.nan) for k in STUNDEN}
    for i, b in enumerate(beob):
        reihe = kurse.get(b["symbol"])
        r_einheit = atr.get(b["symbol"])
        if not reihe or not r_einheit:
            continue
        p0 = T.kurs_bei(reihe[0], reihe[1], b["zeit"])
        if not p0:
            continue
        for k in STUNDEN:
            p1 = T.kurs_bei(reihe[0], reihe[1],
                            b["zeit"] + dt.timedelta(hours=k))
            if p1:
                aus[k][i] = abs(p1 - p0) / p0 / (T.STOP_ATR * r_einheit)
    return aus


def main() -> int:
    t0 = time.time()
    print("=" * 100)
    print("DIE ANLASS-SCHWELLE - WAS KOSTET SCHAERFER SPERREN?")
    print("=" * 100)
    print("  ⚠️ %s" % VORBEHALT)
    print("\n  Sicherung oeffnen ...")
    con = T._oeffne_sicherung()
    beob = lade_beobachtungen(con)
    tage = len({b["zeit"].date() for b in beob})
    print("  %d Beobachtungen ueber %d Tage, %d Symbole (%.0f s)"
          % (len(beob), tage, len({b["symbol"] for b in beob}),
             time.time() - t0))

    # ---- A  DIE ZAEHLUNG --------------------------------------------------
    print("\n  A · DIE ZAEHLUNG - wie viele Fragen bleiben?")
    bloecke = collections.Counter()
    for b in beob:
        for x in b["geaenderte_bloecke"]:
            bloecke[x] += 1
    gesamt_aenderungen = sum(bloecke.values())
    print("     Blockaenderungen insgesamt: %d" % gesamt_aenderungen)
    for name, n in bloecke.most_common(8):
        print("        %-16s %7d  (%4.1f %%)"
              % (name, n, 100.0 * n / max(gesamt_aenderungen, 1)))

    print("\n     %-34s %10s %10s %12s"
          % ("Einstellung", "gesperrt", "bleibt", "Fragen/Tag"))
    masken = {}
    for name, ign, mind in VARIANTEN:
        m = sperrt_maske(beob, ign, mind)
        masken[name] = m
        bleibt = int((~m).sum())
        print("     %-34s %9d %10d %12.0f"
              % (name, int(m.sum()), bleibt, bleibt / max(tage, 1)))

    # ---- B  DIE WIRKUNG ---------------------------------------------------
    print("\n  B · DIE WIRKUNG - sind die zusaetzlich Gesperrten ruhiger?")
    print("     Kurse laden ...")
    kurse = T.lade_kurse(con)
    atr = T.lade_atr()
    beweg = bewegung_betrag(kurse, atr, beob)
    grund = masken[VARIANTEN[0][0]]
    rng = np.random.default_rng(SAAT)
    print("     %-34s %6s %11s %11s %11s %9s"
          % ("Einstellung", "h", "gesperrt R", "bleibt R", "Nullwelt", "Urteil"))
    for name, ign, mind in VARIANTEN[1:]:
        m = masken[name]
        # ⚠️ NUR DIE ZUSAETZLICH GESPERRTEN: die heute schon gesperrten sind
        # in beiden Faellen weg und wuerden den Vergleich verwaessern.
        zusatz = m & ~grund
        frei = ~m
        for k in STUNDEN:
            v = beweg[k]
            a = v[zusatz & np.isfinite(v)]
            b = v[frei & np.isfinite(v)]
            if a.size < 50 or b.size < 50:
                print("     %-34s %6.0f  zu wenige Faelle (%d/%d)"
                      % (name, k, a.size, b.size))
                continue
            echt = float(np.median(a)) - float(np.median(b))
            # Nullwelt: gleich viele zufaellig aus den heute noch freien
            offen = np.where(~grund & np.isfinite(v))[0]
            null = []
            for i in range(NULL_ZIEHUNGEN):
                w = rng.choice(offen, min(int(zusatz.sum()), len(offen)),
                               replace=False)
                rest = np.setdiff1d(offen, w, assume_unique=False)
                if len(rest) < 50:
                    continue
                null.append(float(np.median(v[w])) - float(np.median(v[rest])))
            # ⚠️⚠️ OHNE NULLWELT KEIN URTEIL - UND KEIN "wie Zufall".
            #
            # Sperrt eine Variante fast alles, was heute frei ist, bleibt
            # kein Rest, gegen den sich eine gleich grosse Zufallssperre
            # vergleichen liesse. Die erste Fassung schrieb dann `nan` in
            # die Spalte und trotzdem "wie Zufall" in die Urteilsspalte -
            # also eine Aussage ueber einen Vergleich, den es nie gab.
            if len(null) < NULL_ZIEHUNGEN // 2:
                print("     %-34s %6.0f %+11.4f %+11.4f %11s %9s"
                      % (name, k, float(np.median(a)), float(np.median(b)),
                         "-", "KEIN URTEIL"))
                continue
            nw = float(np.mean(null))
            unten = float(np.percentile(null, 10))
            urteil = ("RUHIGER" if echt < unten else "wie Zufall")
            print("     %-34s %6.0f %+11.4f %+11.4f %+11.4f %9s"
                  % (name, k, float(np.median(a)), float(np.median(b)), nw,
                     urteil))

    # ---- DIE POSITIVKONTROLLE --------------------------------------------
    #
    # ⚠️ Die gemessenen Unterschiede sind klein (rund 0,01 R). Bevor daraus
    # etwas folgt, muss feststehen, dass dieser Aufbau einen Unterschied
    # dieser Groesse ueberhaupt auffindet - und dass er keinen findet, wo
    # keiner ist. Beides wird hier gepflanzt.
    print("\n  POSITIVKONTROLLE (Variante ,ohne marken`, 6 h)")
    m = masken["ohne marken"]
    zusatz = m & ~grund
    frei = ~m
    v = beweg[6.0]
    ok = np.isfinite(v)
    for d in (0.0, 0.005, 0.01, 0.02):
        v2 = v.copy()
        v2[zusatz] = np.maximum(v2[zusatz] - d, 0.0)
        a = v2[zusatz & ok]
        b = v2[frei & ok]
        echt = float(np.median(a)) - float(np.median(b))
        print("     %.3f R abgezogen -> Unterschied %+.4f R" % (d, echt))
    print("     (0,000 ist der ungepflanzte Fall - der Rest muss um genau")
    print("      den gepflanzten Betrag darunter liegen)")

    print("\n  LESEART")
    print("     gesperrt R  Median des BEWEGUNGSBETRAGS der zusaetzlich")
    print("                 gesperrten Lagen - klein heisst: da passierte nichts.")
    print("     bleibt R    dasselbe fuer die, die durchkommen.")
    print("     Nullwelt    derselbe Unterschied bei ZUFAELLIGER Sperrung")
    print("                 gleicher Groesse (%d Ziehungen)." % NULL_ZIEHUNGEN)
    print("     RUHIGER     unter dem 10. Perzentil der Nullwelt - die")
    print("                 Einstellung trifft gezielt ruhige Lagen.")
    print("\n  ⚠️ %s" % VORBEHALT)
    print("  (%.0f s)" % (time.time() - t0))
    print("=" * 100)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
