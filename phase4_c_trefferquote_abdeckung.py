# -*- coding: utf-8 -*-
"""WIE VIEL PROZENT MEHR? - Kette mit Lueckenrabatt gegen Kette mit
Abdeckung, auf der NEUTRALEN Einstiegsbewertung.

⚠️⚠️⚠️ ZWEI EIGENE FEHLLESUNGEN STECKEN IN DER VORGESCHICHTE DIESER
DATEI (22.09.2026). Sie stehen hier, weil beide wiederkommen koennen.

## Fehllesung 1 - der angeglichene Auswahlanteil

`phase4_c_ist_das_ergebnis_besser.py` hat die Schwelle des neuen Arms
per Bisektion auf denselben Auswahlanteil gedreht. Das ist richtig, wenn
man ORDNUNG gegen ORDNUNG vergleicht (2.518). Es ist falsch fuer die
Frage, um die es hier geht: der LUECKENRABATT ist genau der Unterschied,
und er steckt im Auswahlanteil. Hier wird deshalb NICHT angeglichen -
der Anteil wird je Arm AUSGEWIESEN (R-R8/B4).

## Fehllesung 2 - der Horizont, und sie war die schwerere

Ich hatte aus 2.513-horizont geschlossen, die Einstiegsbewertung
gehoere auf H3. ⛔ FALSCH. Der Befund traegt seine eigene
Einschraenkung: *„die 555 Faelle sind BESTANDSENTSCHEIDUNGEN
(NACHKAUFEN, REDUZIEREN, HALTEN); Neueinstiege gibt es seit A1 praktisch
nicht."* Gemessen war die FUEHRUNG, nicht der EINSTIEG.

⚠️⚠️ DIE ARCHITEKTUR, die das klaert (Nutzervorgabe 22.09., am Code
nachgeprueft):

    1. EINSTIEGSBEWERTUNG   neutral, gilt fuer Spot UND Hebel GLEICH
                            funding + turnover -> Quote -> Potential
    2. Kommt ein Signal?
    3. ERST DANN            Risiko- und Hebelrechnung, dynamisch je Trade
                            `hebel = verlustanteil / stop_rel`, gedeckelt
                            (entscheidungsrechnung.py:182, 1698)
                            ⇒ HIER kommt die Haltedauer ins Spiel
    4. SPOT                 eher langfristig -> Akkumulation

Die Haltedauer des HEBELS ist nicht der Horizont der BEWERTUNG. Und eine
eigene Hebel-Bewertung darf es nach Regel 3 gar nicht geben - 2a hat das
entschieden. Deshalb misst diese Datei `bewegung_r` (*„wie viel ist zu
holen"*) auf dem registrierten H20, NICHT `barriere` und NICHT H3.

## Die drei Arme

    A  HEUTE      ALT-Tabelle, Abdeckung `splycur`   (Lueckenrabatt aktiv)
    B  LOESUNG    NEU-Tabelle, Abdeckung Naeherung
    C  NUR MENGE  ALT-Tabelle, Abdeckung Naeherung

C trennt Tabelle von Abdeckung. ⚠️ Faellt C mit B zusammen, waehlen
beide Tabellen dieselben Faelle - dann ist die Tabelle folgenlos, und
das ist ein Ergebnis, kein Fehler (es bestaetigt 2.518 von der anderen
Seite).

## ⚠️⚠️ WAS DIESE MESSUNG NICHT KANN

Die Anker stammen aus `K.baue(..., naeh, ...)` - also nur von Symbolen,
die eine Naeherungsmenge haben. Arm B hat darauf per Konstruktion
100 Prozent Abdeckung, im BETRIEB sind es 59. Der gemessene Effekt ist
damit eine OBERGRENZE der Abdeckungswirkung, nicht der Betriebswert.

## ⚠️ VORABFESTLEGUNG (vor dem Lauf geschrieben)

| Ergebnis | Deutung |
|---|---|
| B ueber A, Band ueber null | ✔ die Loesung gewinnt haeufiger |
| Baender ueberlappen | ⚠ kein Unterschied nachweisbar |
| B unter A, Band unter null | ✖ die Loesung gewinnt seltener |

⚠️ NULLKONTROLLE mit gemischten Raengen · POSITIVKONTROLLE auf die
DIFFERENZ (Methodik 2.105) · NUR LESEND.
"""
import os
import statistics as st
import sys
import time

if hasattr(sys.stdout, "reconfigure"):        # ⚠ Suite ersetzt stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import numpy as np                                          # noqa: E402

import agent.potential as P                                 # noqa: E402
import agent.wahrscheinlichkeit as WK                       # noqa: E402
import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import phase4_c_kalibrierung_freefloat as KF                # noqa: E402
import phase4_c_naeherung_konstante_menge as NK             # noqa: E402
import messnorm_auswahl as MA                             # noqa: E402
from messe_beitrag_auf_auswahl import _auswahl_maske      # noqa: E402

CRV = 2.0
NEU_TAB = (2.32, 0.50, 0.34, -0.11, -3.06)      # H20, ab 2023 (2.517)
BLOCK = 60              # = messnorm._block(20)
ZIEH = 400
NULL = 40               # Nullziehungen - die Norm fuehrt 40, nicht 3


def _arg(a, f, v):
    return a[a.index(f) + 1] if f in a else v


def fuenftel(werte: list) -> dict:
    n = len(werte)
    werte = sorted(werte, key=lambda x: x[1])
    return {s: min(int(i / n * 5), 4) for i, (s, _v) in enumerate(werte)}


def potential(fu_pkt, tu_pkt):
    q = WK.basisrate(CRV) + (fu_pkt + tu_pkt) / 100.0
    return q * CRV - (1.0 - q)


def band(werte, saat):
    r = np.random.default_rng(saat)
    nb = max(1, len(werte) // BLOCK)
    z = []
    for _ in range(ZIEH):
        ix = r.integers(0, max(1, len(werte) - BLOCK), size=nb)
        z.append(float(np.mean(np.concatenate(
            [werte[i:i + BLOCK] for i in ix]))))
    z.sort()
    return (float(np.mean(werte)), z[int(.05 * ZIEH)], z[int(.95 * ZIEH)])


def baue_raenge(H: int):
    """Anker und Raenge je Tag - EINE Stelle fuer alle Messungen darauf.

    ⚠⚠ HERAUSGELOEST AM 22.09.2026, weil eine zweite Messung
    (Fuenftelwechsel beim Nennerwechsel, S5) dieselben Raenge braucht.
    Eine Kopie waere zwei Stellen zum Auseinanderlaufen
    (`test-ruft-echten-code-nicht-kopie`).

    -> (je, r_neu, r_alt, r_fu, reihen, mom)

        je      Ankertage mit `in_r`, Fenster ab `NK.AB`
        r_neu   turnover-Fuenftel auf der NAEHERUNGSmenge
        r_alt   turnover-Fuenftel auf `splycur` (die heutige Betriebsgroesse)
        r_fu    funding-Fuenftel
        mom     Momentum 250, fuer `messnorm_auswahl._auswahl_maske`
    """
    reihen = B.lade()
    heute, _r = NK.mengen_heute()
    umst = NK.umstellungen(reihen)
    naeh = {}
    for s, m in heute.items():
        if s in umst:
            continue
        z = reihen.get(s)
        if z:
            naeh[s] = {str(x[0])[:10]: m for x in z}
    echt = MB.reihe("data/onchain_historie.db", "splycur")
    fund = F.lade_funding()

    KF._SPEICHER.clear()
    je = KF.beschneiden(K.baue(reihen, "turnover", naeh, horizont=H),
                        None, NK.AB)

    r_neu, r_alt, r_fu = {}, {}, {}
    for tag, z in je.items():
        wn = [(x["sym"], x["kennzahl"]) for x in z]
        if len(wn) >= 12:
            r_neu[tag] = fuenftel(wn)
        wa = []
        for x in z:
            s = x["sym"]
            d, zr = echt.get(s), reihen.get(s)
            if not d or not zr:
                continue
            m = d.get(tag)
            if not m or m <= 0:
                continue
            for t, c, _h, _l, v in zr:
                if str(t)[:10] == tag and v and c and c > 0:
                    wa.append((s, float(v) / (float(c) * float(m))))
                    break
        if len(wa) >= 12:
            r_alt[tag] = fuenftel(wa)
        wf = [(s, d[tag]) for s, d in fund.items() if tag in d]
        if len(wf) >= 12:
            r_fu[tag] = fuenftel(wf)
    return je, r_neu, r_alt, r_fu, reihen, KF.momentum250(reihen)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    H = int(_arg(args, "--horizont", "20"))
    saat = int(_arg(args, "--saat", "20260922"))
    t0 = time.time()

    ALT_TAB = next(b.stufen for b in WK.BEITRAEGE
                   if b.merkmal == "turnover_fuenftel")
    FU_TAB = next(b.stufen for b in WK.BEITRAEGE
                  if b.merkmal == "funding_fuenftel")
    voll_alt = max(FU_TAB) + max(ALT_TAB)
    voll_neu = max(FU_TAB) + max(NEU_TAB)
    sch_alt = P.SCHWELLE_VORGABE
    sch_neu = P.SCHWELLE_VORGABE * (
        potential(max(FU_TAB), max(NEU_TAB))
        / potential(max(FU_TAB), max(ALT_TAB)))

    print("=" * 100)
    print("WIE VIEL PROZENT MEHR? - Lueckenrabatt gegen Abdeckung  "
          "(bewegung_r, H%d)" % H)
    print("=" * 100)
    print("  A HEUTE    %s  Schwelle %.4f" % (ALT_TAB, sch_alt))
    print("  B LOESUNG  %s  Schwelle %.4f" % (NEU_TAB, sch_neu))
    print("  C NUR MENGE  ALT-Tabelle auf der Naeherungs-Abdeckung")
    print("  ⚠️ Auswahlanteil NICHT angeglichen - er ist Teil des Effekts.")
    print()

    je, r_neu, r_alt, r_fu, reihen, mom = baue_raenge(H)

    n_ges = sum(len(z) for z in je.values())
    n_alt = sum(1 for t, z in je.items() for x in z
                if (r_alt.get(t) or {}).get(x["sym"]) is not None)
    print("  %d Ankertage, %d Anker" % (len(je), n_ges))
    print("  Anker MIT turnover-Wert:  A %.1f %%  ·  B/C 100,0 %% "
          "(im Betrieb 59 %% - siehe Kopf)"
          % (100.0 * n_alt / max(1, n_ges)))
    print()

    zulaessig = MA.zulaessige_mengen(je, mom, horizont=H)
    print("  ZULAESSIGE MENGEN (Datenlage, `messnorm_auswahl`): %s"
          % (", ".join(zulaessig) or "KEINE"))
    print("  ⚠ `frei` ist die MARKTfrage (P6), kein Beitragsurteil -")
    print("     das Urteil muss auf den SELEKTIERTEN Mengen halten.")
    print()

    def lauf(modus, menge, mische=None):
        """modus 'gewinn' = Anteil in_r > 0 · 'hoehe' = Median in_r.

        `menge` ist ein Name aus `messnorm_auswahl.MENGEN`. Angewandt
        wird GENAU die Maske des Hauses (`_auswahl_maske`, Momentum 250),
        nicht eine nachgebaute - sonst misst diese Datei eine andere
        Auswahl als die Norm.
        """
        rng = np.random.default_rng(mische) if mische is not None else None
        anteil = MA.MENGEN[menge]
        tage, q = {}, ([], [], [], [])
        for tag, z in je.items():
            fu_r = r_fu.get(tag)
            if not fu_r:
                continue
            if anteil < 1.0:
                if len(z) < 12:
                    continue
                maske = _auswahl_maske(z, mom.get(tag) or {}, anteil, None)
                if maske is None or not maske.any():
                    continue
                z = [x for x, ok in zip(z, maske) if ok]
            ta, tn = r_alt.get(tag, {}), r_neu.get(tag, {})
            if rng is not None:
                # ⚠️⚠️ KOPIE, NICHT IN PLACE. Mein erster Entwurf rechnete
                # `d.clear(); d.update(...)` auf den Dicts in `r_alt`/`r_neu`
                # - also auf den ECHTEN Raengen. Folge: jede weitere
                # Nullkontrolle mischte bereits Gemischtes.
                ta = dict(zip(list(ta), rng.permutation(list(ta.values()))))
                tn = dict(zip(list(tn), rng.permutation(list(tn.values()))))
            ya, yb, yc, alle = [], [], [], []
            for x in z:
                s = x["sym"]
                y = (1.0 if x["in_r"] > 0 else 0.0) if modus == "gewinn" \
                    else float(x["in_r"])
                alle.append(y)
                f = fu_r.get(s)
                if f is None:
                    continue
                fp = FU_TAB[f]
                a, nn = ta.get(s), tn.get(s)
                if potential(fp, ALT_TAB[a] if a is not None else 0.0) \
                        >= (sch_alt if a is not None
                            else sch_alt * max(FU_TAB) / voll_alt):
                    ya.append(y)
                if potential(fp, NEU_TAB[nn] if nn is not None else 0.0) \
                        >= (sch_neu if nn is not None
                            else sch_neu * max(FU_TAB) / voll_neu):
                    yb.append(y)
                if potential(fp, ALT_TAB[nn] if nn is not None else 0.0) \
                        >= (sch_alt if nn is not None
                            else sch_alt * max(FU_TAB) / voll_alt):
                    yc.append(y)
            if len(alle) < MA.MIND_ANKER or not ya or not yb or not yc:
                continue
            mit = (np.mean if modus == "gewinn" else np.median)
            m = float(mit(alle))
            tage[tag] = (float(mit(ya)) - m, float(mit(yb)) - m,
                         float(mit(yc)) - m)
            for i, w in enumerate((ya, yb, yc)):
                q[i].append(len(w) / len(alle))
            q[3].append(m)
        return tage, [st.mean(x) if x else 0.0 for x in q]

    def zeile(modus, menge, skala, saat):
        tage, anteile = lauf(modus, menge)
        # ⚠️⚠️ 20 BLOECKE, NICHT WENIGER. `messnorm._block(20)` gibt 60
        # Tage; die Norm fordert 20 Bloecke, also 1.200 auswertbare Tage.
        # `zulaessige_mengen` zaehlt auf der ROHEN Ankermenge - hier
        # fallen zusaetzlich Tage ohne funding-Rang weg, und dann hat
        # `5%` nur noch 12 Bloecke. Wer das uebergeht, faellt ein Urteil,
        # das die eigene Norm nicht traegt (erste Fassung tat es).
        if not tage:
            return None
        if len(tage) // BLOCK < 20:
            return {"duenn": len(tage) // BLOCK, "tage": len(tage)}
        t = sorted(tage)
        d = np.array([tage[x][1] - tage[x][0] for x in t]) * skala
        m, u, o = band(d, saat)
        nk = []
        for ms in range(NULL):
            tg, _a = lauf(modus, menge, mische=1000 + ms)
            if tg:
                nk.append(skala * st.mean(
                    [v[1] - v[0] for v in tg.values()]))
        null = st.mean(nk) if nk else 0.0
        return dict(tage=len(t), anker=anteile[3], q=anteile,
                    a=skala * (anteile[3] + st.mean([tage[x][0] for x in t])),
                    b=skala * (anteile[3] + st.mean([tage[x][1] for x in t])),
                    alle=skala * anteile[3], diff=m, u=u, o=o, null=null,
                    netto=m - null, bloecke=len(d) // BLOCK)

    def tabelle(modus, titel, einheit, skala, fmt):
        print("  " + "=" * 96)
        print("  %s   (Nullkontrolle %d Ziehungen)" % (titel, NULL))
        print("  " + "=" * 96)
        print("  %-6s %6s %7s %8s %8s %8s %9s %-18s %7s  %s"
              % ("Menge", "Tage", "Bloecke", "A HEUTE", "B LSG",
                 "ALLE", "DIFF", "Band", "NULLPKT",
                 "Urteil GEGEN DEN NULLPUNKT"))
        print("  " + "-" * 96)
        aus = {}
        for menge in ("5%", "10%", "20%", "50%", "frei"):
            r = zeile(modus, menge, skala, saat)
            if r is None:
                print("  %-6s %s" % (menge, "keine auswertbaren Tage"))
                continue
            if "duenn" in r:
                print("  %-6s %6d %7d   -- ZU DUENN: die Norm fordert 20 "
                      "Bloecke, kein Urteil --"
                      % (menge, r["tage"], r["duenn"]))
                continue
            # ⚠⚠ GEGEN DEN NULLPUNKT, NICHT GEGEN NULL -
            # der Messstandard vom 08.09. im Wortlaut. Die erste
            # Fassung pruefte `u > 0` und haette die HOEHE auf allen
            # drei Mengen als TRAGEND gemeldet, obwohl der Nullwert
            # dort ueber der unteren Bandgrenze liegt (10 %: Nullpunkt
            # +0,15 gegen Bandgrenze +0,01).
            traegt = r["u"] > r["null"]
            aus[menge] = traegt
            print(("  %-6s %6d %7d " + fmt + " " + fmt + " " + fmt
                   + " %+9.2f [%+7.2f..%+7.2f] %+7.2f  %s")
                  % (menge, r["tage"], r["bloecke"], r["a"], r["b"],
                     r["alle"], r["diff"], r["u"], r["o"], r["null"],
                     ("✔ TRAEGT" if traegt else
                      "✖ SCHLECHTER" if r["o"] < r["null"] else
                      "⚠ nicht trennbar")
                     + ("" if menge != "frei" else "  (MARKTfrage)")))
        print("  " + "-" * 96)
        sel = {k: v for k, v in aus.items() if k != "frei"
               and k in zulaessig}
        if not sel:
            print("  ⛔ KEINE selektierte Menge ist zulaessig - die "
                  "Frage ist hier nicht als Beitragsfrage zu stellen")
        elif all(sel.values()):
            print("  ✔✔ TRAEGT AUF ALLEN %d ZULAESSIGEN "
                  "SELEKTIERTEN MENGEN (%s)"
                  % (len(sel), ", ".join(sorted(sel))))
        elif any(sel.values()):
            print("  ⚠ NICHT ROBUST - traegt nur auf %s von %s"
                  % (", ".join(k for k, v in sel.items() if v) or "keiner",
                     ", ".join(sorted(sel))))
        else:
            print("  ✖ TRAEGT AUF KEINER zulaessigen selektierten "
                  "Menge - das `frei`-Ergebnis war eine MARKTantwort")
        print()

    tabelle("gewinn", "GEWINNANTEIL in Prozent  (Anteil mit in_r > 0)",
            "Pp", 100, "%7.1f%%")
    tabelle("hoehe", "HOEHE  (Median in_r)", "R", 1, "%8.4f")

    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
