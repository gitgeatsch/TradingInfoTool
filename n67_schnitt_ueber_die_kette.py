# -*- coding: utf-8 -*-
"""N-67 — `schnitt` UEBER DIE KETTE simuliert (07.09.2026)

## Die Frage, die eine Einzelmessung nicht beantwortet

N-59 hat `schnitt` auf der selektierten Menge gemessen: +0,1759 R. Das
heisst **nicht**, dass er in der Kette etwas beitraegt. Dort haben vorher
schon `funding` und `turnover` gewirkt.

> Traegt `schnitt` noch, NACHDEM die bestehenden Beitraege gewirkt haben -
> und wie viele Empfehlungen kostet er?

Beides ist zu simulieren, nicht zu schaetzen.

## Die nachgebaute Reihenfolge

    Stufe 5    Auswahl nach 250-Tage-Momentum, oberste 20 %
    Stufe 12   die bestehenden Beitraege sperren ihr oberstes Fuenftel
               (funding und turnover - so wirken ihre Stufentabellen:
                das oberste Fuenftel traegt -1,70 bzw. -2,40 Punkte)
    NEU        `schnitt` sperrt sein oberstes Fuenftel - auf dem, WAS
               UEBRIG BLEIBT

⚠️ **Der dritte Schritt laeuft auf der Restmenge, nicht auf der ganzen.**
Genau darin unterscheidet sich diese Datei von N-59. Wer `schnitt` wieder
auf allen Gewaehlten misst, bekommt N-59s Zahl zurueck und weiss nichts
Neues.

## ⚠️ Entzerrt, weil die Statistik es verlangt

N-65: `median(Gruppe) - median(alle)` ist bei kleinen Gruppen nach oben
verzerrt - in einer Welt ohne Information lieferte sie +0,10 bis +0,16 R.
Jede Zahl unten hat ihren eigenen Nullwert abgezogen (20 Mischungen).

## Was gezaehlt wird - und zwar VORHER benannt

    1  Wieviele Anker bleiben nach den bestehenden Beitraegen uebrig?
       Bleiben zu wenige, ist die Frage nicht beantwortbar - dann ist
       DAS das Ergebnis.
    2  Wieviele davon sperrt `schnitt` zusaetzlich? (Durchlassquote)
    3  Was bringt das in R - auf der Restmenge, entzerrt?
    4  KONTROLLE: dieselbe Rechnung mit `zufall` an `schnitt`s Stelle.
       Er darf auf der Restmenge so wenig tragen wie ueberall.

    python n67_schnitt_ueber_die_kette.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_beitrag_auf_auswahl as A                        # noqa: E402
import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_funding_niveau as F                             # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messe_regel_wirksamkeit as RW                         # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n64_schnitt_stufen import PUNKT_JE_R, band               # noqa: E402

HORIZONT, MENGE = 20, "20%"
ZIEH, SAAT = 20, 20260907


def welten(reihen):
    """Je Kandidat die Tageswelt - dieselbe Ladung fuer alle."""
    zus = {"funding": F.lade_funding(),
           "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    return {a: K.baue(reihen, a, zus.get(a), horizont=HORIZONT)
            for a in ("schnitt", "funding", "turnover", "zufall")}


def kette(w, mom, anteil, dritter, mische=None):
    """Die Reihenfolge Auswahl -> bestehende Beitraege -> `dritter`.

    Gibt (wirkung_je_tag, gezaehlt) zurueck. `gezaehlt` haelt fest, wie
    viele Anker jede Stufe durchlaesst - vor jeder Deutung.
    """
    aus = {}
    z = {"gewaehlt": [], "nach_beitraegen": [], "gesperrt_dritter": []}
    for tag, zeilen in w["schnitt"].items():
        if len(zeilen) < 12:
            continue
        syms = [x["sym"] for x in zeilen]
        y = np.array([x["in_r"] for x in zeilen], float)
        m = A._auswahl_maske(zeilen, mom.get(tag) or {}, anteil, None)
        if m is None or m.sum() < 6:
            continue
        z["gewaehlt"].append(int(m.sum()))

        # ---- die bestehenden Beitraege sperren ihr oberstes Fuenftel ---
        frei = m.copy()
        for a in ("funding", "turnover"):
            zt = {x["sym"]: x["kennzahl"] for x in w[a].get(tag, [])}
            kz = np.array([zt.get(s, np.nan) for s in syms], float)
            ok = np.isfinite(kz)
            if ok.sum() < 12:
                continue            # ⚠️ keine Datenlage -> keine Sperre
            r = np.full(len(syms), np.nan)
            r[ok] = RW.rang(kz[ok])
            frei &= ~(np.nan_to_num(r, nan=0.0) >= RW.GRENZE)
        if frei.sum() < 4:
            continue
        z["nach_beitraegen"].append(int(frei.sum()))

        # ---- der dritte Beitrag auf der RESTMENGE ---------------------
        zt = {x["sym"]: x["kennzahl"] for x in w[dritter].get(tag, [])}
        kz = np.array([zt.get(s, np.nan) for s in syms], float)
        ok = np.isfinite(kz) & frei
        if ok.sum() < 4:
            continue
        rr = RW.rang(kz[ok])
        if mische is not None:
            rr = mische.permutation(rr)
        sperr = rr >= RW.GRENZE
        if sperr.sum() < 1 or (~sperr).sum() < 1:
            continue
        z["gesperrt_dritter"].append(float(sperr.mean()))
        yw = y[ok]
        aus[tag] = float(np.median(yw[~sperr])) - float(np.median(yw))
    return aus, z


def main() -> int:
    t0 = time.time()
    print("=" * 96)
    print("N-67 — `schnitt` UEBER DIE KETTE: traegt er NACH den anderen?")
    print("=" * 96)
    reihen = B.lade()
    mom = momentum250(reihen)
    w = welten(reihen)
    anteil = MENGEN[MENGE]
    block = _block(HORIZONT)
    print("  %d Reihen . Menge %s . Block %d . %d Nullziehungen"
          % (len(reihen), MENGE, block, ZIEH))

    print()
    print("  %-10s %9s %24s %10s %9s %11s"
          % ("Dritter", "roh R", "Band", "Null R", "entzerrt", "Punkte"))
    erg = {}
    for dritter in ("schnitt", "zufall"):
        echt, z = kette(w, mom, anteil, dritter)
        e = band(echt, block)
        if e is None:
            print("  %-10s  zu wenige Tage (%d)" % (dritter, len(echt)))
            continue
        null = []
        for i in range(ZIEH):
            n, _ = kette(w, mom, anteil, dritter,
                         mische=np.random.default_rng(SAAT + i))
            nb = band(n, block, zieh=300, saat=SAAT + i)
            if nb:
                null.append(nb[0])
        nw = float(np.mean(null)) if null else 0.0
        erg[dritter] = {"e": e, "null": nw, "z": z,
                        "wirkung": e[0] - nw}
        print("  %-10s %+9.4f [%+.4f .. %+.4f] %+10.4f %+9.4f %+11.2f"
              % (dritter, e[0], e[1], e[2], nw, e[0] - nw,
                 (e[0] - nw) * PUNKT_JE_R), flush=True)

    # ---- Die Zaehlung, vor der Deutung ---------------------------------
    z = erg.get("schnitt", {}).get("z")
    if z:
        print()
        print("  DIE DURCHLASSQUOTE — was jede Stufe uebrig laesst")
        print("     %-32s %10s" % ("Stufe", "Anker/Tag"))
        print("     %-32s %10.1f" % ("nach Auswahl (Stufe 5, 20 %)",
                                     float(np.mean(z["gewaehlt"]))))
        print("     %-32s %10.1f" % ("nach funding + turnover",
                                     float(np.mean(z["nach_beitraegen"]))))
        print("     %-32s %10.1f %%"
              % ("davon sperrt `schnitt` noch",
                 100 * float(np.mean(z["gesperrt_dritter"]))))
        print("     %d Kalendertage im Band" % erg["schnitt"]["e"][3])

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 96)
    print("WAS DAS HEISST")
    print("=" * 96)
    s, zf = erg.get("schnitt"), erg.get("zufall")
    if zf is None or s is None:
        print("  ⚠️ Nicht beide Arme messbar - kein Urteil.")
        return 1
    print("  Kontrolle `zufall` auf der Restmenge: %+.4f R entzerrt"
          % zf["wirkung"])
    if abs(zf["wirkung"]) > 0.03:
        print("     ⚠️⚠️ Die Kontrolle traegt - der Aufbau ist kaputt,")
        print("        alles Weitere wertlos.")
        return 1
    print("     ✔ liegt bei null, wie sie muss.")
    print()
    print("  `schnitt` NACH den bestehenden Beitraegen: %+.4f R entzerrt"
          % s["wirkung"])
    # ⚠️ Der Vergleich gegen die Kontrolle, nicht gegen null - sie traegt
    # die Restverzerrung des Aufbaus mit.
    if s["wirkung"] > zf["wirkung"] + 0.03:
        print("  ✔✔ ER TRAEGT ZUSAETZLICH. Das ist mehr als N-59 gezeigt")
        print("     hat: dort stand er allein, hier nach den anderen.")
    elif s["wirkung"] < zf["wirkung"] - 0.03:
        print("  ⚠️⚠️ ER SCHADET auf der Restmenge - umgekehrtes Vorzeichen.")
    else:
        print("  ⚠️ ER TRAEGT NICHT ZUSAETZLICH. Von der Kontrolle nicht zu")
        print("     unterscheiden - was er sieht, haben funding und")
        print("     turnover schon gesperrt. Das passt zur gemessenen")
        print("     Redundanz (2.158, Spearman +0,418 in der Auswahl).")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
