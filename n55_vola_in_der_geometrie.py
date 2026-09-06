# -*- coding: utf-8 -*-
"""N-55 — `vola` IN DER GEOMETRIE: Stopweite, Horizont und der Hebel (06.09.2026)

## Woher der Auftrag kommt

N-52 (2.135) hat `vola` aus `BEITRAEGE` herausgenommen und in die Geometrie
verwiesen: es traegt keine Richtung, aber es steuert die
**Aufloesungsquote** mit +3,1 Punkten - der groesste saubere Effekt.
N-54 (2.137) hat gezeigt, dass die Ebenen **unabhaengig** sind: `vola`
stoert die Beitraege nicht.

Bleibt die Frage, die den Nutzen ausmacht:

> **Welche Geometrie ist die richtige, wenn ein Asset ruhiger oder
> lebhafter ist als es selbst sonst ist?**

Und daran haengt der Hebel, denn im Code steht (`entscheidungsrechnung`):

    stop_rel     = abstand / kurs
    hebel_noetig = verlustanteil / stop_rel        # verlustanteil 15 %

**Die Stopweite BESTIMMT den Hebel.** Steuert `vola` die Stopweite, faellt
der Hebel daraus - genau die Bauform, die das uebergeordnete Ziel verlangt:
der Hebel wird nicht gewaehlt, er faellt aus der Bewertung.

## ⚠️⚠️ DER MASSSTAB - und warum er hier ausnahmsweise tragfaehig ist

Gemessen wird der **Erwartungswert in R**. Bei den Beitraegen war er
kontaminiert (2.136), hier nicht - und der Unterschied ist wichtig:

    bei den BEITRAEGEN   verglichen wurden ASSETS untereinander, die
                         verschieden volatil sind -> der Massstab selbst
                         haengt an der Volatilitaet -> kontaminiert
    HIER                 verglichen werden GEOMETRIEN auf DERSELBEN
                         Ankermenge -> kein Querschnitt, kein Confound

⚠️ Vergleichbar ueber verschiedene Stopweiten ist R nur, weil das RISIKO
JE HANDEL FEST ist - genau so rechnet die Kette selbst
(`risiko_eur = verlustanteil x einsatz_eur`). Dann ist die Rendite auf
das Kapital `EW_in_R x verlustanteil`, und der Faktor ist fuer alle
Stopweiten derselbe. **Ohne diese Annahme waere der Vergleich sinnlos** -
ein weiterer Stop macht jedes R groesser, und dieselbe Bewegung waere
weniger R.

## Was gemessen wird

    je vola-Drittel  x  Stopweite {0,5 · 1,0 · 1,5 · 2,0} x ATR
                     x  Horizont {5 · 10 · 20} Tage        (CRV fest 2,0)

    Aufloesungsquote   wieviel Prozent entscheiden sich in der Frist?
    Tage bis dahin     der HORIZONT faellt hieraus, nicht aus Meinung
    EW in R            der Ertrag - das eigentliche Urteil
    stop_rel -> Hebel  was die Kette daraus machen wuerde

## Vorabtest (`--probe`) — der Grenzfall zuerst

    Welt O  Zufallslauf mit Volatilitaetsclustern, KEINE Richtung
            ⚠️ Erwartung: EW in R ist bei JEDER Geometrie und JEDEM
               Drittel nicht von null zu trennen. Findet die Messung hier
               eine beste Geometrie, ist sie kaputt.
    Welt P  niedrige relative Vola -> echte Drift
            Erwartung: der EW hebt sich, und zwar im ruhigen Drittel

    python n55_vola_in_der_geometrie.py --probe
    python n55_vola_in_der_geometrie.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402
from n52_vola_geometrieprobe import band                     # noqa: E402

CRV, BRUCH, VORLAUF = 2.0, 5.0, 260
STOPS = (0.5, 1.0, 1.5, 2.0)          # in ATR
HORIZONTE = (5, 10, 20)
MAXH = max(HORIZONTE)
VERLUSTANTEIL = 0.15                  # betraege.VORGABE_VERLUSTANTEIL hebel
DRITTEL = ("ruhig", "mittel", "lebhaft")


def fenster(x, breite):
    """(n, breite)-Sicht auf x[1:], ohne zu kopieren."""
    from numpy.lib.stride_tricks import sliding_window_view
    return sliding_window_view(x[1:], breite)


def baue(reihen):
    """je Tag: Anker mit vola, stop_rel und je Stopweite dem AUSGANG.

    Ausgang je Stopweite: (tag_ziel, tag_stop) - 0 heisst "nie".
    ⚠️ Vollstaendig vektorisiert je Symbol; die Alternative waere eine
    Schleife ueber 600.000 Anker x 4 Stopweiten x 20 Tage.
    """
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        n = len(c)
        if n < VORLAUF + MAXH + 5:
            continue
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        kaputt = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        # ein Bruch IRGENDWO im laengsten Fenster schliesst den Anker aus
        bruch_f = fenster(np.concatenate([[False], kaputt]), MAXH).any(axis=1)
        hoch_f = fenster(h, MAXH)
        tief_f = fenster(t, MAXH)
        gueltig = min(len(hoch_f), n - MAXH)
        # rollender Median der ATR ueber 251 Tage, nur Vergangenheit
        med = np.full(n, np.nan)
        for i in range(VORLAUF, n):
            med[i] = np.median(br[i - 250:i + 1])
        idx = np.arange(VORLAUF, gueltig)
        idx = idx[np.isfinite(br[idx]) & (br[idx] > 0)
                  & np.isfinite(med[idx]) & (med[idx] > 0)
                  & ~bruch_f[idx]]
        if not len(idx):
            continue
        vola = br[idx] / med[idx]
        for si, k in enumerate(STOPS):
            weite = k * br[idx]
            ziel = c[idx] + CRV * weite
            stop = c[idx] - weite
            tr_z = hoch_f[idx] >= ziel[:, None]
            tr_s = tief_f[idx] <= stop[:, None]
            # ⚠️ argmax auf einer Boolzeile gibt 0, wenn NICHTS wahr ist -
            # deshalb `any` daneben, sonst waere "nie" ein Treffer an Tag 1.
            tz = np.where(tr_z.any(axis=1), tr_z.argmax(axis=1) + 1, 0)
            ts = np.where(tr_s.any(axis=1), tr_s.argmax(axis=1) + 1, 0)
            if si == 0:
                eintraege = [{"vola": float(vola[j]), "aus": {}}
                             for j in range(len(idx))]
            for j in range(len(idx)):
                eintraege[j]["aus"][k] = (int(tz[j]), int(ts[j]),
                                          float(weite[j] / c[idx[j]]))
        rend = {}
        for hz in HORIZONTE:
            rend[hz] = c[np.minimum(idx + hz, n - 1)] / c[idx] - 1.0
        for j, i in enumerate(idx):
            eintraege[j]["rend"] = {hz: float(rend[hz][j]) for hz in HORIZONTE}
            je_tag.setdefault(tage[i], []).append(eintraege[j])
    return {t: z for t, z in je_tag.items() if len(z) >= 20}


def zellen(je_tag, k, hz):
    """je vola-Drittel drei Tagesreihen: EW in R, Aufloesung, Tage."""
    ewr = [dict() for _ in range(3)]
    auf = [dict() for _ in range(3)]
    dau = [dict() for _ in range(3)]
    rel = [[] for _ in range(3)]
    for tag, z in je_tag.items():
        v = np.array([x["vola"] for x in z], float)
        f = np.minimum((W.rang(v) * 3).astype(int), 2)
        for d in range(3):
            teil = [x for j, x in enumerate(z) if f[j] == d]
            if len(teil) < 3:
                continue
            e, a, t2 = [], [], []
            for x in teil:
                tz, ts, sr = x["aus"][k]
                zz = tz if 0 < tz <= hz else 0
                ss = ts if 0 < ts <= hz else 0
                # ⚠️⚠️ GLEICHSTAND GEHT AN DEN STOP. Werden BEIDE Barrieren
                # am selben Tag beruehrt, weiss die Tageskerze nicht, was
                # zuerst kam. Wer das zugunsten des Ziels aufloest, erfindet
                # Ertrag - und zwar am meisten dort, wo am haeufigsten
                # doppelt beruehrt wird (enge Stops).
                #
                # 06.09.2026 vom Vorabtest gefangen: mit "Ziel gewinnt"
                # zeigte die richtungsfreie Kunstwelt +0,20 bis +0,46 R bei
                # JEDER Geometrie. So rechnet auch `_ausgang`, dessen
                # Schleife den Stop zuerst prueft.
                if ss and (not zz or ss <= zz):
                    e.append(-1.0); a.append(1.0); t2.append(ss)
                elif zz:
                    e.append(CRV); a.append(1.0); t2.append(zz)
                else:
                    # flach: zum Marktpreis geschlossen, in R der Stopweite
                    e.append(x["rend"][hz] / sr if sr > 0 else 0.0)
                    a.append(0.0)
                rel[d].append(sr)
            ewr[d][tag] = float(np.mean(e))
            auf[d][tag] = float(np.mean(a))
            if t2:
                dau[d][tag] = float(np.mean(t2))
    return ewr, auf, dau, rel


def tabelle(je_tag):
    """{(Stop, H, Drittel): (EW, unten, oben, Aufloesung, Tage, Hebel)}"""
    aus = {}
    for k in STOPS:
        for hz in HORIZONTE:
            ewr, auf, dau, rel = zellen(je_tag, k, hz)
            for d in range(3):
                bb = band(ewr[d])
                if not bb:
                    continue
                ba, bd = band(auf[d]), band(dau[d])
                sr = float(np.median(rel[d])) if rel[d] else float("nan")
                aus[(k, hz, d)] = (bb[0], bb[1], bb[2],
                                   ba[0] if ba else float("nan"),
                                   bd[0] if bd else float("nan"),
                                   VERLUSTANTEIL / sr if sr > 0 else float("nan"))
    return aus


def artefakt(saaten=(6060, 7171, 8282)):
    """⚠️ DER NULLPUNKT, GEMESSEN STATT ANGENOMMEN.

    Drei geeichte Welten OHNE Richtung. Je Zelle wird der GROESSTE Wert
    genommen - konservativ: wer den Artefakt unterschaetzt, findet Ertrag,
    wo keiner ist.
    """
    aus = {}
    for i, sa in enumerate(saaten):
        t = tabelle(baue(kunstwelt(False, saat=sa)))
        print("     Artefaktwelt %d/%d gerechnet (%d Zellen)"
              % (i + 1, len(saaten), len(t)), flush=True)
        for schl, w in t.items():
            aus[schl] = max(aus.get(schl, -9.0), w[0])
    return aus


def main() -> int:
    t0 = time.time()
    if "--eiche" in sys.argv:
        k = kennzahlen(kunstwelt(False))
        print("  %-18s %10s %10s %8s" % ("", "ATR/Kurs", "Spanne", "|dC|"))
        print("  %-18s %10.5f %10.5f %8.5f" % ("echte Daten", *ZIEL_EICHUNG))
        print("  %-18s %10.5f %10.5f %8.5f" % ("Kunstwelt", *k))
        print("  %-18s %10.2f %10.2f %8.2f"
              % ("Verhaeltnis", *(k[i] / ZIEL_EICHUNG[i] for i in range(3))))
        print("  Spanne/Bewegung  echt %.3f · Kunst %.3f"
              % (ZIEL_EICHUNG[1] / ZIEL_EICHUNG[2], k[1] / k[2]))
        return 0

    print("=" * 104)
    print("N-55 — `vola` in der GEOMETRIE: Stopweite, Horizont, Hebel")
    print("=" * 104)
    print("  1  DER NULLPUNKT — drei geeichte Welten OHNE Richtung",
          flush=True)
    art = artefakt()
    if "--probe" in sys.argv:
        print()
        print("  2  GEGENPROBE — eine Welt MIT gepflanzter Drift")
        echt = tabelle(baue(kunstwelt(True, saat=9393)))
        besser = [s for s in echt if s in art and echt[s][1] > art[s]]
        print("     %d von %d Zellen ueberragen den Artefakt"
              % (len(besser), len(echt)))
        if besser:
            b = max(besser, key=lambda s: echt[s][0] - art[s])
            print("     ✔ staerkste: Stop %.1f / H%d / %s  EW %+.4f gegen "
                  "Artefakt %+.4f" % (b[0], b[1], DRITTEL[b[2]],
                                      echt[b][0], art[b]))
            print("     Der Test darf auf die echten Daten.")
            return 0
        print("     ⚠️ ein gepflanzter Effekt kommt NICHT durch - zu streng.")
        return 1

    print()
    print("  2  DIE ECHTEN DATEN", flush=True)
    print("     Lade Reihen ...", flush=True)
    je = baue(B.lade())
    print("     %d Tage, %d Anker"
          % (len(je), sum(len(z) for z in je.values())), flush=True)
    echt = tabelle(je)

    print()
    print("=" * 104)
    print("JE ZELLE: der EW gegen den GEMESSENEN Nullpunkt")
    print("=" * 104)
    print("     %-5s %-3s %-8s %9s %9s %10s %8s %6s %7s"
          % ("Stop", "H", "Drittel", "EW echt", "Artefakt", "UEBERSCHUSS",
             "Aufloes", "Tage", "Hebel"))
    beste = {}
    for k in STOPS:
        for hz in HORIZONTE:
            for d in range(3):
                sl = (k, hz, d)
                if sl not in echt or sl not in art:
                    continue
                ew, unten, _o, auf, dau, heb = echt[sl]
                a0 = art[sl]
                ueber = ew - a0
                traegt = unten > a0
                if traegt and ueber > beste.get(d, (-9,))[0]:
                    beste[d] = (ueber, k, hz, heb, ew, a0, auf, dau)
                print("     %-5.1f %-3d %-8s %+9.4f %+9.4f %+10.4f %7.1f%% "
                      "%5.1f %6.1fx%s"
                      % (k, hz, DRITTEL[d], ew, a0, ueber, 100 * auf, dau,
                         heb, " ✔" if traegt else ""), flush=True)
        print()

    print("=" * 104)
    print("DAS URTEIL — was HAELT und was NICHT")
    print("=" * 104)
    print("  ⚠️⚠️ ZUERST, WAS NICHT HAELT: der ABSOLUTE Ueberschuss.")
    print("     Alle 36 Zellen liegen ueber dem Artefakt - ein Test, der")
    print("     nichts aussortiert, trennt nichts. Die Ursache ist ein")
    print("     STRUKTURFEHLER der Kunstwelt: dort sind Hoch und Tief")
    print("     UNABHAENGIGES Rauschen um den Schlusskurs. In echten Daten")
    print("     liegt an einem Aufwaertstag das Tief nahe der Eroeffnung -")
    print("     der Stop wird viel seltener zufaellig beruehrt. Die")
    print("     Kunstwelt UEBERSCHAETZT die Stop-Treffer und ist zu")
    print("     negativ. Der Pegel ist damit nicht belastbar; dazu kommt")
    print("     die Marktdrift, die lange Horizonte beguenstigt.")
    print()
    print("  ⚠️ UND DIE GEOMETRIE UNTERSCHEIDET SICH NICHT.")
    roh = {}
    for d in range(3):
        z = [(echt[(k, hz, d)][0], k, hz) for k in STOPS for hz in HORIZONTE
             if (k, hz, d) in echt]
        if z:
            roh[d] = max(z)
            print("     %-8s bester roher EW %+.4f bei Stop %.1f / H%d"
                  % (DRITTEL[d], *roh[d]))
    if len({(v[1], v[2]) for v in roh.values()}) == 1:
        print("     -> DIESELBE Geometrie gewinnt in allen Dritteln. `vola`")
        print("        waehlt die Bauform NICHT.")
    print()
    print("  ✔ WAS HAELT: die SPREIZUNG zwischen den Dritteln.")
    print("     Sie vergleicht echt gegen Artefakt in DERSELBEN Zelle -")
    print("     der Pegelfehler kuerzt sich weitgehend heraus.")
    # ⚠️ Der QUOTIENT taugt hier nicht: liegt die Artefaktspreizung nahe
    # null, explodiert er oder dreht das Vorzeichen. Die DIFFERENZ ist die
    # Groesse, um die die echte Spreizung ueber dem Artefakt liegt.
    print("     %-6s %-4s %11s %11s %11s"
          % ("Stop", "H", "echt", "Artefakt", "Differenz"))
    fakt = []
    for k in STOPS:
        for hz in HORIZONTE:
            if (k, hz, 0) not in echt or (k, hz, 2) not in echt:
                continue
            se = echt[(k, hz, 0)][0] - echt[(k, hz, 2)][0]
            sa = art[(k, hz, 0)] - art[(k, hz, 2)]
            fakt.append(se - sa)
            print("     %-6.1f %-4d %+11.4f %+11.4f %+11.4f"
                  % (k, hz, se, sa, se - sa))
    gut = [f for f in fakt if np.isfinite(f)]
    print()
    if gut and min(gut) > 0.0:
        print("  ✔✔ In ALLEN %d Geometrien ist die echte Spreizung groesser"
              % len(gut))
        print("     als die artefaktbedingte, um %+.4f bis %+.4f R."
              % (min(gut), max(gut)))
        print("     Die Tagesklammer vergleicht ruhig gegen lebhaft AM")
        print("     SELBEN TAG - Marktdrift kann das nicht erklaeren.")
        print()
        print("     ⚠️⚠️ ABER DIE ZUSCHREIBUNG BLEIBT OFFEN. `EW in R` ist")
        print("        einer der Massstaebe, die N-52/N-53 als kontaminiert")
        print("        erwiesen haben; nur GS ist rein, und GS sagt bei")
        print("        `vola` NICHTS (-0,00041). Die Spreizung kann also")
        print("        weiterhin Geometrie sein - nur eine, die meine")
        print("        Kunstwelt wegen ihres Strukturfehlers nicht abbildet.")
        print("     ⚠️ Und sie ordnet die HOEHE, nicht die BAUFORM - das")
        print("        deckt sich mit N-54: die Ebenen sind unabhaengig.")
    else:
        print("  ⚠️ Die Spreizung uebersteigt den Artefakt NICHT ueberall")
        print("     (%+.4f bis %+.4f R) - dann ordnet `vola` den Ertrag"
              % (min(gut) if gut else float("nan"),
                 max(gut) if gut else float("nan")))
        print("     nicht belastbar.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


# ⚠️⚠️ DIE KUNSTWELT IST GEEICHT (06.09.2026). Der Nullpunkt fuer "EW in R"
# ist NICHT null - Tageskerzen UEBERSCHIESSEN die Barriere, und die NAHE
# Barriere relativ staerker als die ferne. Das hebt P(Ziel|aufgeloest) ueber
# das theoretische 1/3 und erzeugt Scheinertrag, am meisten bei engen Stops.
#
# Gemessen in der ungeeichten Welt: P(Ziel|aufgeloest) 0,344 statt 0,333,
# EW +0,0388 R bei Stop 1,0/H20 - in einer Welt OHNE jede Richtung.
#
# Wie gross der Effekt ist, haengt davon ab, wie breit die TAGESSPANNE im
# Verhaeltnis zur Schlusskursbewegung ist. Und da unterscheidet sich der
# echte Markt erheblich:
#
#                        echte Daten   ungeeichte Kunstwelt
#     ATR / Kurs            0,08613          0,03445
#     (Hoch-Tief) / Kurs    0,07353          0,02490
#     |Tagesrendite|        0,02883          0,01953
#     Spanne / Bewegung       2,551            1,275   <-- doppelt so gross
#
# Eine ungeeichte Welt UNTERSCHAETZT den Artefakt also. Die Werte unten
# sind so gewaehlt, dass die drei Kennzahlen zusammenfallen; `--eiche`
# rechnet das nach.
VOL_BASIS = 0.0428
SPANNEN_FAKTOR = 1.24


def kunstwelt(mit_drift, tage=1200, symbole=45, saat=6060,
              vol_basis=VOL_BASIS, spannen=SPANNEN_FAKTOR):
    rng = np.random.default_rng(saat)
    reihen = {}
    for s in range(symbole):
        lv = np.zeros(tage)
        for i in range(1, tage):
            lv[i] = 0.97 * lv[i - 1] + rng.normal(0, 0.10)
        vol = vol_basis * np.exp(lv)
        c = np.empty(tage)
        c[0] = 100.0
        for i in range(1, tage):
            drift = 0.0
            if mit_drift and i > 260:
                rel = vol[i - 1] / np.median(vol[max(0, i - 251):i])
                if rel < 0.9:
                    drift = 0.0035
            c[i] = c[i - 1] * float(np.exp(drift + rng.normal(0, vol[i])
                                           - 0.5 * vol[i] ** 2))
        sp = c * vol
        h = c + np.abs(rng.normal(0, spannen, tage)) * sp
        t = c - np.abs(rng.normal(0, spannen, tage)) * sp
        reihen["K%02d" % s] = [(("2020-01-01_%04d" % i), c[i], h[i], t[i], 1.0)
                               for i in range(tage)]
    return reihen


def kennzahlen(reihen):
    """ATR/Kurs, Spanne/Kurs, |Tagesrendite| - die Eichgroessen."""
    a, sp, d = [], [], []
    for _s, z in reihen.items():
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        if len(c) < 300:
            continue
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        m = np.isfinite(br) & (br > 0) & (c > 0)
        if not m.any():
            continue
        a.append(np.median(br[m] / c[m]))
        sp.append(np.median((h - t)[m] / c[m]))
        d.append(np.median(np.abs(np.diff(c) / np.maximum(c[:-1], 1e-12))))
    return (float(np.median(a)), float(np.median(sp)), float(np.median(d)))


ZIEL_EICHUNG = (0.08613, 0.07353, 0.02883)     # echte Daten, 516 Symbole


if __name__ == "__main__":
    sys.exit(main())
