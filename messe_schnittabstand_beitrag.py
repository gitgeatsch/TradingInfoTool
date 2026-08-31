# -*- coding: utf-8 -*-
"""P2: der ABSTAND ZUM EIGENEN 200-SCHNITT als Beitrag (31.08.2026)

⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG, geschrieben BEVOR gerechnet wurde.

## Warum diese Groesse und keine andere

Nutzervorgabe 31.08.: *"Krypto muss und braucht einen Entscheider, der bei
ALLEN Assets wirkt."*

Funding und Turnover kommen aus FREMDQUELLEN und haben deshalb zwangslaeufig
Luecken - nach dem Nachladen am 31.08. immer noch 7 von 43 Werten ohne jeden
Beitrag (AIOZ, CANTON, CAT, FLOKI, SUPRA, VSN, XNO). Binance und CoinGecko
listen nicht jeden Wert, und daran aendert kein Abruf etwas.

    Ein Beitrag, der bei ALLEN Assets wirken soll, muss aus der eigenen
    KURSREIHE kommen - die haben wir per Definition fuer jeden Wert.

Genau das war die Eigenschaft von Vorfilter H (Abdeckung 100 %), und genau
sie fehlt seinen Nachfolgern.

## Die Groesse

    abstand_schnitt = Kurs / 200-Tage-Schnitt - 1

⚠️ NUR RUECKWAERTS: der Schnitt der Tage i-200 .. i-1, der Kurs von i.

`messe_lage_beitrag.py` hat sie am 29.08. bereits gemessen - mit der
richtigen Klammer (je Kalendertag) und dem richtigen Mass (Bewegung in R),
auf 523 Reihen:

    H  5   +0,0785 R   t = +2,93     Negativkontrolle +0,0071 (t 0,50)
    H 20   +0,1962 R   t = +1,79     Negativkontrolle -0,0520 (t -1,13)
    H 60   +1,0305 R   t = +2,12     Negativkontrolle -0,0085 (t -0,04)

⚠️ ABER DAS WAR EINE MERKMALSMESSUNG. Was fehlt, ist genau das, was bei
Funding den Faktor 5,5 ausgemacht hat: die Wirkung als REGEL.

## Was diese Messung klaert

  W1 ALS REGEL       drei Zahlen: wieviele Faelle sperrt sie, waren die
                     schlechter, was bleibt netto
  W2 BEITRAGSTABELLE Punkte je Fuenftel, geschrumpft - wie bei Funding
  W3 SYMBOLZAHL      ⚠️ NEU AM 31.08. GEFUNDEN: bei Funding schrumpft die
                     Spanne mit der Zahl der Symbole je Tag (2,52 bei allen
                     Tagen, 0,93 bei >= 250) - und zwar EIGENSTAENDIG, nicht
                     ueber die Zeit. Die Produktion rangt ueber ~300. Diese
                     Messung weist die Tabelle deshalb JE SYMBOLZAHL aus.
  W4 ROBUSTHEIT      beide Historienhaelften, drei Zeitabschnitte
  W5 SURVIVORSHIP    lebende gegen eingestellte Reihen
  W6 ABDECKUNG       fuer wieviele Werte liegt die Groesse vor?

## Vorab festgelegt

  nutzbar        monoton ueber die Fuenftel, ausserhalb des Placebo-Bandes,
                 beide Haelften gleiches Vorzeichen, kein Survivorship-
                 Artefakt, UND als Regel wirksam
  nur Merkmal    traegt als Merkmal, aber die Regel bringt nichts
  nicht nutzbar  sonst

    python messe_schnittabstand_beitrag.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import messe_eigenschaft_beitrag as B                         # noqa: E402

SCHNITT = 200
HORIZONT = 20
MIND_JE_TAG = 15
PLACEBO_LAEUFE = 40
CRV = 2.0


def baue():
    """Je Kalendertag: Abstand zum 200-Schnitt und Bewegung in R."""
    reihen = B.lade()
    je_tag, ende = {}, {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        ende[sym] = tage[-1]
        for i in range(SCHNITT, len(c) - HORIZONT):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            # ⚠️ NUR RUECKWAERTS: c[i-200 .. i-1]
            schnitt = c[i - SCHNITT:i].mean()
            if schnitt <= 0:
                continue
            je_tag.setdefault(tage[i], []).append({
                "sym": sym,
                "abstand": float(c[i] / schnitt - 1.0),
                "in_r": float((c[i + HORIZONT] - c[i]) / r)})
    letzte = max(ende.values())
    lebt = {s: (d >= letzte[:8] + "01") for s, d in ende.items()}
    for z in je_tag.values():
        for x in z:
            x["lebt"] = lebt.get(x["sym"], False)
    return je_tag


def tabelle(je_tag, tage=None, mische=None, mind=MIND_JE_TAG, bedingung=None):
    """Median je Fuenftel, je Kalendertag gebildet - wie bei Funding."""
    sammel = {k: [] for k in range(5)}
    n_tage = 0
    for tag in (tage if tage is not None else je_tag):
        z = je_tag.get(tag) or []
        if bedingung is not None:
            z = [x for x in z if bedingung(x)]
        if len(z) < mind:
            continue
        n_tage += 1
        w = np.array([x["abstand"] for x in z], dtype=float)
        y = np.array([x["in_r"] for x in z], dtype=float)
        if mische is not None:
            w = mische.permutation(w)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(5):
            m = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
    if any(len(sammel[k]) < 30 for k in range(5)):
        return None, n_tage
    return [st.mean(sammel[k]) for k in range(5)], n_tage


def punkte(werte):
    """Fuenftelwerte in Prozentpunkte, geschrumpft (halbiert)."""
    if werte is None:
        return None
    mittel = st.mean(werte)
    f = 1.0 / (1.0 + CRV)
    return [round(100.0 * (x - mittel) * f / 2.0, 2) for x in werte]


def zeige(titel, werte, n_tage, einzug=4):
    if werte is None:
        print("%s%-32s %5d Tage  zu wenige" % (" " * einzug, titel, n_tage))
        return None
    p = punkte(werte)
    print("%s%-32s %5d Tage  %s  Spanne %+.2f"
          % (" " * einzug, titel, n_tage,
             " / ".join("%+5.2f" % x for x in p), p[0] - p[4]))
    return p


def main():
    print("Lade Reihen (523 aus messdaten.db)...", flush=True)
    je_tag = baue()
    alle = [x for z in je_tag.values() for x in z]
    print("%d Anker, %d Kalendertage, %d Symbole"
          % (len(alle), len(je_tag), len({x["sym"] for x in alle})))

    print()
    print("=" * 96)
    print("P2 — DER ABSTAND ZUM EIGENEN 200-SCHNITT ALS BEITRAG")
    print("=" * 96)

    # ---- W6 ABDECKUNG ------------------------------------------------
    print()
    print("W6 — ABDECKUNG: fuer wieviele Werte liegt die Groesse vor?")
    print("  %d von %d Reihen (%.0f %%) - die Groesse braucht nur die Kursreihe"
          % (len({x["sym"] for x in alle}), len(B.lade()),
             100 * len({x["sym"] for x in alle}) / len(B.lade())))
    print("  ⚠️ Voraussetzung: mindestens %d Handelstage Historie." % SCHNITT)

    # ---- W2 BEITRAGSTABELLE ------------------------------------------
    print()
    print("W2 — DIE BEITRAGSTABELLE (Fuenftel 0 = am tiefsten unter dem Schnitt)")
    voll, n_voll = tabelle(je_tag)
    p_voll = zeige("alle Tage", voll, n_voll)

    # ---- W3 SYMBOLZAHL ----------------------------------------------
    print()
    print("W3 — ⚠️ HAENGT DIE SPANNE AN DER SYMBOLZAHL? (bei Funding: ja)")
    print("  Die Produktion rangt ueber alle Werte, fuer die die Groesse")
    print("  vorliegt. Wenn die Tabelle nur bei wenigen Symbolen gilt, ist")
    print("  sie nicht uebertragbar - derselbe Fehlertyp wie bei H.")
    for mind in (15, 100, 200, 250):
        w, n = tabelle(je_tag, mind=mind)
        zeige("Tage mit >= %d Symbolen" % mind, w, n)

    # ---- W4 ROBUSTHEIT ----------------------------------------------
    print()
    print("W4 — ROBUSTHEIT")
    tage = sorted(je_tag)
    mitte = tage[len(tage) // 2]
    for klar, teil in (("erste Haelfte", [t for t in tage if t < mitte]),
                       ("zweite Haelfte", [t for t in tage if t >= mitte])):
        w, n = tabelle(je_tag, tage=teil)
        zeige(klar, w, n)
    for klar, von, bis in (("2018-2020", "2018", "2021"),
                           ("2021-2023", "2021", "2024"),
                           ("2024-2026", "2024", "2027")):
        w, n = tabelle(je_tag, tage=[t for t in tage if von <= t < bis])
        zeige(klar, w, n)

    # ---- W5 SURVIVORSHIP --------------------------------------------
    print()
    print("W5 — SURVIVORSHIP")
    for klar, bed in (("lebende Reihen", lambda x: x["lebt"]),
                      ("eingestellte Reihen", lambda x: not x["lebt"])):
        w, n = tabelle(je_tag, bedingung=bed)
        zeige(klar, w, n)

    # ---- Kontrollen ---------------------------------------------------
    print()
    print("KONTROLLEN")
    rng = np.random.default_rng(20260831)
    echt = (p_voll[0] - p_voll[4]) if p_voll else float("nan")
    p = []
    for _ in range(PLACEBO_LAEUFE):
        w, _n = tabelle(je_tag, mische=rng)
        if w:
            q = punkte(w)
            p.append(q[0] - q[4])
    p = np.array(p)
    u, o = np.quantile(p, [0.025, 0.975])
    print("  NEGATIV (Rang je Tag gemischt): Band %+.2f .. %+.2f (Mitte %+.2f)"
          % (u, o, float(p.mean())))
    print("  echt %+.2f  ->  %s"
          % (echt, "AUSSERHALB - der Befund haelt" if (echt < u or echt > o)
             else "⚠️ INNERHALB - vom Zufall nicht zu trennen"))

    # ---- W1 ALS REGEL -------------------------------------------------
    print()
    print("W1 — ⚠️ ALS REGEL, NICHT ALS MERKMAL (bei Funding Faktor 5,5)")
    print('  Die Regel: "kein Einstieg im obersten Fuenftel" (am weitesten')
    print("  UEBER dem Schnitt). Drei Zahlen:")
    gesperrt, bleibt = [], []
    for tag, z in je_tag.items():
        if len(z) < MIND_JE_TAG:
            continue
        w = np.array([x["abstand"] for x in z], dtype=float)
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for x, q in zip(z, r):
            (gesperrt if q >= 0.8 else bleibt).append(x["in_r"])
    n = len(gesperrt) + len(bleibt)
    print("    wieviele Faelle:      %d von %d (%.1f %% gesperrt)"
          % (len(gesperrt), n, 100 * len(gesperrt) / n))
    print("    waren die schlechter: Median %+.4f R gegen %+.4f R"
          % (st.median(gesperrt), st.median(bleibt)))
    print("    was bleibt netto:     %+.4f R gegen %+.4f R ohne Regel (%+.4f)"
          % (st.median(bleibt), st.median(gesperrt + bleibt),
             st.median(bleibt) - st.median(gesperrt + bleibt)))


if __name__ == "__main__":
    main()
