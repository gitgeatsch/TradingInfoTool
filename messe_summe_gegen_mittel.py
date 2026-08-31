# -*- coding: utf-8 -*-
"""B: Traegt der MITTELWERT der Beitraege besser als ihre SUMME? (31.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Die Frage, und woher sie kommt

Nutzerfrage 31.08.: *„Die Schwelle kann man ja vorher sauber kalibrieren je
Beitrag bzw. Anzahl der Beitraege wird eine korrekte Schwelle angewendet."*

Der Anlass ist ein Konstruktionsproblem: `wahrscheinlichkeit.rechne()` bildet
die **Summe** der Beitragspunkte (`zuschlag += punkte`). Liegt bei einem Wert
nur Funding vor und bei einem anderen Funding UND Turnover, summiert man
ueber verschieden viele Summanden - wie ein Notendurchschnitt aus einem Fach
gegen einen aus drei Faechern.

Gemessen an der Produktion (31.08.):

    nur Funding    36 von 43 Werten   Spanne -0,051 .. +0,039 R
    beide           7 von 43 Werten   Spanne -0,133 .. +0,133 R

Eine feste Schwelle trifft damit zwei verschiedene Skalen. Bei 0,080 R waeren
36 von 43 Werten **dauerhaft gesperrt** - unerreichbar, egal wie gut ihr
Funding steht.

⚠️ Nutzervorgabe dazu, und sie ist der Grund fuer diese Messung: *„Wir
duerfen nicht davon ausgehen, dass wir eine 100-Prozent-Abdeckung der Daten
haben. Das System muss genauso mit 1, 2, 3 oder mehreren Beitraegen arbeiten
koennen - derzeit haben wir eher Datenmangel."*

## Die beiden Kandidaten

    SUMME    zuschlag = p1 + p2 + ...          (heute)
    MITTEL   zuschlag = (p1 + p2 + ...) / n    (Kandidat B)

⚠️ **WO BEIDE BEITRAEGE VORLIEGEN, IST DAS DIESELBE RANGFOLGE.** Der
Mittelwert ist dort die halbierte Summe - eine monotone Umformung, und eine
Regel auf Raengen kann davon nichts merken. **Der Unterschied entsteht
ausschliesslich beim VERGLEICH zwischen Ankern mit unterschiedlich vielen
Beitraegen.** Genau darauf zielt diese Messung; ein Lauf, der nur Anker mit
voller Datenlage betrachtet, kann per Konstruktion keinen Unterschied finden.

## Vorab festgelegt - was als Befund gilt

  MITTEL BESSER   Regelwirkung des Mittels liegt ueber der der Summe UND
                  ausserhalb des Placebo-Bandes UND beide Historienhaelften
                  zeigen dasselbe Vorzeichen
  KEIN UNTERSCHIED  die Vertrauensbaender ueberlappen - dann bleibt die
                  Summe, weil sie der Bestand ist (kein Umbau ohne Grund)
  SUMME BESSER    dann ist die Ungleichheit der Skalen belegt, aber nicht
                  schaedlich - und die Nutzerfrage ist mit "nein" beantwortet

⚠️ ZUSAETZLICH GEMESSEN WIRD DIE **ERREICHBARKEIT**: bei welcher Schwelle
faellt der erste Wert dauerhaft aus? Das ist der eigentliche Schaden der
Summe, und er zeigt sich nicht in der Regelwirkung.

## Die dritte Frage in diesem Lauf: der 50-Tage-Schnitt

Nutzeridee 31.08.: *„Was ist mit dem 50-Schnitt bzw. Abstand - haben wir
diesen gemessen?"* **Nein.** Gemessen wurde der Abstand zum **200**-Schnitt
(31.08. gefallen, bei keinem Horizont trennbar). Der 50er kommt im System nur
als MARKTBREITE vor ("18 von 51 Coins ueber ihrer 50-Tage-Linie"), nie als
eigener Abstand je Asset.

⚠️ VORAB BENANNT, warum gerade 50 und nicht eine freie Suche ueber 20/50/100:
der Handelshorizont liegt bei 1 bis 20 Tagen, der 200er misst die Lage im
Jahrestrend. Der 50er ist die naechstliegende Skala **oberhalb** des
Horizonts - nah genug, um die Lage zu treffen, weit genug, um nicht das
Tagesrauschen zu messen. **Eine Zelle, vorab benannt** (Suchpreis 2.49).

    python messe_summe_gegen_mittel.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_eigenschaft_beitrag as B                          # noqa: E402
import messe_kandidaten_als_regel as K                         # noqa: E402
import messe_regel_wirksamkeit as W                            # noqa: E402
from agent import wahrscheinlichkeit as WK                     # noqa: E402

SCHNITT_50 = 50
HORIZONT = 20


def _stufen(merkmal):
    for b in WK.BEITRAEGE:
        if b.merkmal == merkmal and b.stufen:
            return tuple(b.stufen)
    return None


def baue_gemischt(reihen, menge, funding, horizont=HORIZONT):
    """Anker mit EINEM oder ZWEI Beitraegen - die Mischung ist der Punkt.

    ⚠️ Ein Anker bekommt Turnover nur, wenn seine Umlaufmenge vorliegt (66
    von 523 Reihen). Genau diese Ungleichheit soll gemessen werden, sie wird
    deshalb NICHT weggefiltert.
    """
    je_tag = {}
    f_stufen = _stufen("funding_fuenftel")
    t_stufen = _stufen("turnover_fuenftel")
    if not f_stufen or not t_stufen:
        raise SystemExit("Funding oder Turnover nicht registriert")

    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        v = np.array([z[4] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        f_je = (funding or {}).get(sym.upper()) or {}
        m_je = (menge or {}).get(sym.upper()) or {}
        for i in range(260, len(c) - horizont):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            tag = tage[i]
            e = {"sym": sym, "in_r": float((c[i + horizont] - c[i]) / r)}
            fw = f_je.get(tag)
            if fw is not None:
                e["funding"] = float(fw)
            mw = m_je.get(tag)
            if mw and mw > 0:
                e["turnover"] = float(v[i] / mw)
            if c[i - SCHNITT_50:i].mean() > 0:
                e["schnitt50"] = float(c[i] / c[i - SCHNITT_50:i].mean() - 1.0)
            if "funding" in e or "turnover" in e:
                je_tag.setdefault(tag, []).append(e)
    return {t: z for t, z in je_tag.items() if len(z) >= 15}


def _fuenftel(werte):
    r = np.argsort(np.argsort(np.asarray(werte, float)))
    return np.minimum((r / max(len(werte) - 1, 1) * 5).astype(int), 4)


def kennzahl(je_tag, art):
    """Je Anker die Kennzahl - SUMME oder MITTEL der vorliegenden Beitraege."""
    f_st = _stufen("funding_fuenftel")
    t_st = _stufen("turnover_fuenftel")
    aus = {}
    for tag, z in je_tag.items():
        # Raenge JE TAG und JE GROESSE, nur ueber die, die den Wert haben
        mit_f = [x for x in z if "funding" in x]
        mit_t = [x for x in z if "turnover" in x]
        punkte = {id(x): [] for x in z}
        if len(mit_f) >= 5:
            for x, q in zip(mit_f, _fuenftel([x["funding"] for x in mit_f])):
                punkte[id(x)].append(f_st[q])
        if len(mit_t) >= 5:
            for x, q in zip(mit_t, _fuenftel([x["turnover"] for x in mit_t])):
                punkte[id(x)].append(t_st[q])
        zeilen = []
        for x in z:
            p = punkte[id(x)]
            if not p:
                continue
            wert = sum(p) if art == "summe" else sum(p) / len(p)
            zeilen.append({"sym": x["sym"], "kennzahl": wert,
                           "in_r": x["in_r"], "n": len(p)})
        if len(zeilen) >= 15:
            aus[tag] = zeilen
    return aus


def main():
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    import messe_bewertungskennzahl as MB
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    import messe_fremdgroesse as MF
    funding = (MF.lade_fremdreihe("data/funding_historie.db", "funding", "wert")
               if hasattr(MF, "lade_fremdreihe") else None)
    if funding is None:
        import sqlite3
        c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
        funding = {}
        for s, d, w in c.execute("SELECT symbol,datum,wert FROM funding"):
            funding.setdefault(str(s).upper(), {})[str(d)[:10]] = float(w)
        c.close()

    je_tag = baue_gemischt(reihen, menge, funding)
    alle = [x for z in je_tag.values() for x in z]
    print("%d Anker, %d Kalendertage" % (len(alle), len(je_tag)))

    print()
    print("=" * 96)
    print("B — SUMME GEGEN MITTELWERT")
    print("=" * 96)

    # ---- wie gemischt ist die Datenlage ueberhaupt? -------------------
    s_kz = kennzahl(je_tag, "summe")
    m_kz = kennzahl(je_tag, "mittel")
    n_je = [x["n"] for z in s_kz.values() for x in z]
    from collections import Counter
    c = Counter(n_je)
    print()
    print("  ⚠️ VORBEDINGUNG: wie viele Beitraege liegen je Anker vor?")
    for k in sorted(c):
        print("     %d Beitrag/Beitraege: %7d Anker (%.1f %%)"
              % (k, c[k], 100 * c[k] / len(n_je)))
    if len(c) < 2:
        print()
        print("  ⚠️⚠️ NUR EINE DATENLAGE - dann sind Summe und Mittel")
        print("     dieselbe Rangfolge, und diese Messung kann per")
        print("     Konstruktion keinen Unterschied finden. Abbruch.")
        return

    rng = np.random.default_rng(20260831)
    print()
    print("  Die Regel: kein Einstieg im obersten Fuenftel der Kennzahl")
    e_s = W.bericht("SUMME  (heute)", s_kz, True, rng)
    e_m = W.bericht("MITTEL (Kandidat B)", m_kz, True, rng)

    # ---- die eigentliche Frage: ERREICHBARKEIT ------------------------
    print()
    print("=" * 96)
    print("⚠️ DIE ERREICHBARKEIT — der Schaden, den die Regelwirkung NICHT zeigt")
    print("=" * 96)
    for art, kz in (("SUMME", s_kz), ("MITTEL", m_kz)):
        je_n = {}
        for z in kz.values():
            for x in z:
                je_n.setdefault(x["n"], []).append(x["kennzahl"])
        print()
        print("  %s — hoechster erreichbarer Wert je Datenlage:" % art)
        for k in sorted(je_n):
            print("     mit %d Beitrag/Beitraegen: max %+7.3f Punkte  (%d Anker)"
                  % (k, max(je_n[k]), len(je_n[k])))
        obergrenzen = {k: max(v) for k, v in je_n.items()}
        if len(obergrenzen) >= 2:
            tief = min(obergrenzen.values())
            hoch = max(obergrenzen.values())
            print("     -> eine Schwelle ueber %+.3f Punkten sperrt die"
                  % tief)
            print("        duennste Datenlage DAUERHAFT (Spanne %.2f zu %.2f)"
                  % (tief, hoch))


if __name__ == "__main__":
    main()
