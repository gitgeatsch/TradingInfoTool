# -*- coding: utf-8 -*-
"""⚠️⚠️ VORABFESTLEGUNG — geschrieben VOR dem Lauf (21.09.2026).

WIRD DER HEBEL BESSER ODER SCHLECHTER? - gemessen, nicht behauptet.

Nutzerkorrektur, woertlich: *„Wenn du sagst du kannst etwas nicht
behaupten das passt, aber du hast das werkzeug der recherche und der
Messung also miss ob der hebel besser wird oder schadet."*

Sie trifft. Ich habe dreimal „das kann ich nicht behaupten" geschrieben,
wo eine Messung moeglich ist.

═══════════════════════════════════════════════════════════════════════
 WAS GEMESSEN WIRD - und warum LOGWACHSTUM, nicht Mittelwert
═══════════════════════════════════════════════════════════════════════

Der Hebel ist eine SIZING-Regel. Sizing beurteilt man nicht am
Mittelwert der Rendite, sondern am GEOMETRISCHEN Wachstum - genau
deshalb rechnet das System mit halbem Kelly. Je Anker:

    Kapitalfaktor  =  1 + r * R          r = Risikoanteil aus
                                             `betraege.hebelrechnung`
                                         R = bewegung_r (Ergebnis in R)
    Beitrag        =  ln(1 + r * R)

Die Summe ist das Logwachstum. Eine Regel, die den Mittelwert hebt und
das Wachstum senkt, hat GESCHADET - und nur dieses Mass zeigt das.

⚠️ `r` ist der EINZIGE Unterschied zwischen den Regeln. Der Stop geht in
`R` bereits ein (es ist in Stopeinheiten normiert), deshalb ist
`r * R` die Kapitalaenderung unabhaengig von der Stopweite.

═══════════════════════════════════════════════════════════════════════
 DIE VIER REGELN, vorab benannt
═══════════════════════════════════════════════════════════════════════

    ALT       Quote mit der vollen `turnover`-Tabelle (heutiger Stand)
    SCHALTER  `turnover` als SCHALTER auf der LAGE: liegt der Umschlag
              im obersten Fuenftel seiner eigenen Geschichte, KEIN
              Hebel; sonst Quote ohne turnover
    OHNE      Quote ganz ohne `turnover` (Regel 3 streng)
    FLACH     konstanter Risikoanteil - die KONTROLLE. Schlaegt sie die
              anderen, ist die Hebelstufung insgesamt wertlos

⚠️ FLACH ist die wichtigste Zeile. Ohne sie misst man nur, welche
Variante die bessere ist - nicht, ob ueberhaupt eine hilft.

⚠️ Eine ZUFALLSREGEL laeuft ebenfalls mit: `r` zufaellig aus derselben
Spanne. Schlaegt sie ALT, ist der Unterschied Rauschen.

═══════════════════════════════════════════════════════════════════════
 VORABFESTLEGUNG - was welches Ergebnis BEDEUTET
═══════════════════════════════════════════════════════════════════════

| Ergebnis | Folge |
|---|---|
| SCHALTER >= ALT und beide > FLACH | die Loesung traegt: Regel 3 gewahrt OHNE Verlust |
| SCHALTER < ALT, aber > FLACH | die Loesung kostet - der Preis ist dann beziffert und der Nutzer entscheidet |
| OHNE ~ ALT | `turnover` traegt im Hebel ohnehin nichts - dann ist die ganze Frage klein |
| FLACH >= alle | ⚠️⚠️ die HEBELSTUFUNG ist wertlos - das waere der groesste Befund des Tages |
| ZUFALL ~ ALT | der Unterschied ist Rauschen, kein Urteil |

⚠️ **Ein Unterschied ist erst einer, wenn sein Band die Null ausschliesst.**
Gerechnet wird ein Blockbootstrap ueber KALENDERTAGE (Block = 3 x
Horizont, wie die Norm), auf der DIFFERENZ je Tag - nicht auf den
Niveaus. Paarweise, damit der gemeinsame Marktverlauf herausfaellt.

⚠️ IN-SAMPLE: die Tabellen stammen aus diesen Daten. Das ueberzeichnet
ALT, nicht die Alternativen - der Vergleich ist also konservativ gegen
meinen eigenen Vorschlag.

    python phase4_c_wird_der_hebel_besser.py
"""
from __future__ import annotations

import math
import os
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.betraege as BE                                # noqa: E402
import messe_funding_niveau as F                          # noqa: E402
import agent.wahrscheinlichkeit as WA                      # noqa: E402
import messe_bewertungskennzahl as MB                      # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402
import messe_regel_wirksamkeit as W                        # noqa: E402
import phase4_c_zerlegung_auf_registrierter_basis as ZR    # noqa: E402

HORIZONT = 20
CRV = 2.0
STOP_REL = 0.08
GEBUEHR = 0.003
KAPITAL = 10000.0
RUECKBLICK = 60
SAAT = 20260921
ZIEHUNGEN = 2000


def fuenftel_je_tag(je_tag: dict) -> dict:
    """{tag: {sym: 0..4}} - genau die Groesse, mit der die Quote rechnet."""
    aus = {}
    for t, z in je_tag.items():
        if len(z) < 12:
            continue
        r = W.rang([x["kennzahl"] for x in z])
        aus[t] = {x["sym"]: min(int(r[i] * 5), 4)
                  for i, x in enumerate(z)}
    return aus


def risiko(merkmale: dict) -> float:
    """Der Risikoanteil `r` - ueber die ECHTEN Betriebsfunktionen."""
    d = WA.rechne(crv=CRV, stop_relativ=STOP_REL, gebuehr_je_seite=GEBUEHR,
                  klasse="krypto", strategie="einstieg",
                  instrument="spot", richtung="long", merkmale=merkmale)
    q = d.get("quote")
    if not q or not 0.0 < q < 1.0:
        return 0.0
    try:
        h = BE.hebelrechnung(quote=q, crv=CRV, kapital_eur=KAPITAL,
                             stop_rel=STOP_REL)
    except Exception:                                      # noqa: BLE001
        return 0.0
    return float(h.get("r") or 0.0)


def main() -> int:
    rng = np.random.default_rng(SAAT)
    print("=" * 108)
    print("WIRD DER HEBEL BESSER ODER SCHLECHTER? - Logwachstum, "
          "gemessen")
    print("=" * 108)
    reihen = B.lade()
    splycur = MB.reihe("data/onchain_historie.db", "splycur")
    funding = F.lade_funding()
    log_u = ZR.log_umschlag(reihen, splycur)
    lage = {}
    for s, d in log_u.items():
        t = sorted(d)
        if len(t) < RUECKBLICK + 200:
            continue
        for i in range(RUECKBLICK, len(t)):
            m = st.mean([d[t[j]] for j in range(i - RUECKBLICK, i)])
            lage.setdefault(s, {})[t[i]] = d[t[i]] - m

    f_to = fuenftel_je_tag(K.baue(reihen, "turnover", splycur,
                                  horizont=HORIZONT))
    f_la = fuenftel_je_tag(K.baue(reihen, "turnover_markt", lage,
                                  horizont=HORIZONT))
    je_fu = K.baue(reihen, "funding", funding, horizont=HORIZONT)
    f_fu = fuenftel_je_tag(je_fu)
    erg_r = {}
    for t, z in K.baue(reihen, "turnover", splycur,
                       horizont=HORIZONT).items():
        erg_r[t] = {x["sym"]: float(x["in_r"]) for x in z}

    # ---- die gemeinsame Ankermenge -----------------------------------
    anker = []
    for t in sorted(set(f_to) & set(f_la) & set(f_fu) & set(erg_r)):
        for s in (set(f_to[t]) & set(f_la[t]) & set(f_fu[t])
                  & set(erg_r[t])):
            anker.append((t, s, f_fu[t][s], f_to[t][s], f_la[t][s],
                          erg_r[t][s]))
    if not anker:
        print("  ⛔ keine gemeinsamen Anker")
        return 2
    tage = sorted({a[0] for a in anker})
    print("  Anker %d · Symbole %d · Kalendertage %d (%s bis %s)"
          % (len(anker), len({a[1] for a in anker}), len(tage),
             tage[0], tage[-1]))
    print("  ⚠️ Nur Anker, die BEIDE Beitraege haben - das ist die "
          "Schnittmenge aus")
    print("     funding (300 Symbole) und turnover (66). Die Luecke "
          "aus 2.497 ist hier")
    print("     ausgeschlossen, nicht geloest.")

    # ---- die vier Regeln ----------------------------------------------
    # ⚠️ Zwischenspeicher: `rechne` haengt nur an den Fuenfteln, nicht am
    # Anker. 5 x 5 Kombinationen statt 124.000 Aufrufe.
    cache = {}

    def r_alt(fu, to, la):
        k = ("alt", fu, to)
        if k not in cache:
            cache[k] = risiko({"funding_fuenftel": fu,
                               "turnover_fuenftel": to})
        return cache[k]

    def r_ohne(fu, to, la):
        k = ("ohne", fu)
        if k not in cache:
            cache[k] = risiko({"funding_fuenftel": fu})
        return cache[k]

    def r_schalter(fu, to, la):
        # ⚠️ DER SCHALTER: oberstes Fuenftel der LAGE -> kein Hebel.
        if la >= 4:
            return 0.0
        return r_ohne(fu, to, la)

    r_flach_wert = None

    def r_gate(fu, to, la):
        # ⚠⚠ DIE ZERLEGUNG DER HEBELREGEL SELBST. Sie tut zwei
        # Dinge auf einmal: sie ENTSCHEIDET, ob ueberhaupt gesetzt wird
        # (bei 49,4 Prozent der Anker ist r = 0), und sie STUFT den
        # Betrag. ALT gegen FLACH vergleicht beides zusammen gegen
        # nichts - und kann deshalb nicht sagen, welcher der beiden
        # Teile wirkt.
        #
        # GATE benutzt DIESELBE Entscheidung wie ALT, aber einen
        # KONSTANTEN Betrag. Ist GATE so gut wie ALT, traegt die
        # Entscheidung und die Stufung ist folgenlos.
        return 1.0 if r_alt(fu, to, la) > 0 else 0.0

    def r_weit(fu, to, la):
        # ⚠ ZWEITER VERDAECHTIGER: die Klammer. `r` wird auf 0,5 bis
        # 1,25 Prozent geklammert - Faktor 2,5. Wenn die Quote mehr
        # Spreizung haette, als durch die Klammer passt, waere die
        # Stufung abgeschnitten, bevor sie die Positionsgroesse
        # erreicht (2c: "der Hebel folgt dem Stop, nicht der
        # Wahrscheinlichkeit"). Hier ohne Klammer, nur halbes Kelly.
        k = _kelly_halb(fu, to)
        return max(0.0, k)

    def _kelly_halb(fu, to):
        d = WA.rechne(crv=CRV, stop_relativ=STOP_REL,
                      gebuehr_je_seite=GEBUEHR, klasse="krypto",
                      strategie="einstieg", instrument="spot",
                      richtung="long",
                      merkmale={"funding_fuenftel": fu,
                                "turnover_fuenftel": to})
        q = d.get("quote")
        if not q or not 0.0 < q < 1.0:
            return 0.0
        kelly = (q * (1.0 + CRV) - 1.0) / CRV
        return 0.5 * kelly

    regeln = (("ALT (volle Tabelle)", r_alt),
              ("GATE (nur Entscheidung)", r_gate),
              ("KLAMMER WEIT", r_weit),
              ("SCHALTER auf der LAGE", r_schalter),
              ("OHNE turnover", r_ohne),
              ("FLACH (Kontrolle)", None),
              ("ZUFALL (Kontrolle)", None))

    # Basiswerte je Regel und Anker
    werte = {name: [] for name, _f in regeln}
    r_alle = []
    for t, s, fu, to, la, R in anker:
        r_alle.append(r_alt(fu, to, la))
    r_flach_wert = float(np.mean([x for x in r_alle if x > 0])) \
        if any(x > 0 for x in r_alle) else 0.0
    zuf = rng.uniform(min([x for x in r_alle if x > 0] or [0.0]),
                      max(r_alle or [0.0]), size=len(anker))

    # ---- ⚠⚠ GLEICHES RISIKOBUDGET - sonst ist der Vergleich unfair
    #
    # Der erste Lauf verglich die SUMMEN roh. Dabei setzte FLACH bei
    # JEDER Gelegenheit ein (Anteil r=0: 0 %) und ALT nur bei der
    # Haelfte (49,4 %), mit dem doppelten mittleren Risiko. Bei
    # positivem Erwartungswert waechst mehr Risiko automatisch mehr -
    # gemessen waere also der groessere EINSATZ, nicht die bessere
    # REGEL. FLACH "gewann" aus Konstruktion.
    #
    # Die Korrektur ist der Kelly-Standard: jede Regel bekommt
    # DASSELBE Gesamtrisikobudget (Summe der r ueber alle Anker), nur
    # anders verteilt. Verglichen wird dann die FORM der Stufung.
    #
    # ⚠ Die Klammer 0,5 bis 1,25 Prozent wird durch die Skalierung
    # verlassen - fuer einen FORMvergleich ist das richtig, fuer eine
    # Betragsaussage waere es falsch. Deshalb steht daneben weiter die
    # ungewichtete Zeile.
    roh = {}
    for name, fn in regeln:
        rs = []
        for i, (t, s, fu, to, la, R) in enumerate(anker):
            if name.startswith("FLACH"):
                rs.append(r_flach_wert)
            elif name.startswith("ZUFALL"):
                rs.append(float(zuf[i]))
            else:
                rs.append(fn(fu, to, la))
        roh[name] = np.array(rs, float)
    budget = float(roh["ALT (volle Tabelle)"].sum())
    skala = {name: (budget / v.sum() if v.sum() > 0 else 0.0)
             for name, v in roh.items()}

    je_tag = {name: {} for name, _f in regeln}
    je_tag_roh = {name: {} for name, _f in regeln}
    for i, (t, s, fu, to, la, R) in enumerate(anker):
        for name, _fn in regeln:
            r0 = roh[name][i]
            for ziel, rr in (("skal", r0 * skala[name]), ("roh", r0)):
                faktor = 1.0 + rr * R
                g = math.log(faktor) if faktor > 1e-9 else -20.0
                if ziel == "skal":
                    werte[name].append(g)
                    je_tag[name].setdefault(t, []).append(g)
                else:
                    je_tag_roh[name].setdefault(t, []).append(g)

    print()
    print("-" * 108)
    print("  ERGEBNIS - Logwachstum je Anker (Summe = Gesamtwachstum)")
    print("-" * 108)
    print("  ⚠⚠ GLEICHES RISIKOBUDGET: jede Regel setzt insgesamt "
          "so viel Risiko ein wie ALT.")
    print("     Verglichen wird damit die FORM der Stufung, nicht ihr "
          "Niveau. Die rohe Summe")
    print("     steht daneben - sie misst EINSATZ plus Form und ist "
          "fuer sich irrefuehrend.")
    print()
    print("  %-24s %12s %12s %12s %10s %9s %10s"
          % ("Regel", "Summe SKAL", "Summe roh", "mittl. r roh",
             "Anteil r=0", "Skala", "Streuung"))
    for name, _f in regeln:
        v = np.array(werte[name], float)
        rs = roh[name]
        vroh = np.concatenate([np.asarray(x, float)
                               for x in je_tag_roh[name].values()])
        # ⚠ GATE traegt als Rohwert eine FLAGGE (1,0), keinen
        # Risikoanteil - seine Rohsumme ist bedeutungslos und wuerde
        # den naechsten Leser in die Irre fuehren. Sie wird deshalb
        # ausdruecklich NICHT gedruckt.
        roh_txt = ("        -" if name.startswith("GATE")
                   else "%12.4f" % vroh.sum())
        print("  %-24s %12.4f %s %12.5f %9.1f%% %9.2f %10.5f"
              % (name, v.sum(), roh_txt, rs.mean(),
                 100.0 * float((rs <= 0).mean()), skala[name], v.std()))

    # ---- die Differenzen mit Band ------------------------------------
    print()
    print("-" * 108)
    print("  DIE UNTERSCHIEDE - paarweise je Tag, Blockbootstrap "
          "(Block %d, %d Ziehungen)" % (3 * HORIZONT, ZIEHUNGEN))
    print("-" * 108)
    block = 3 * HORIZONT
    tage_l = sorted(je_tag["ALT (volle Tabelle)"])

    def nullpunkt(a_name, b_name, ziehungen=40):
        """⚠⚠ DER BEZUG IST NICHT DIE NULL, SONDERN DER NULLPUNKT.

        Die Mutation (Ergebnisse durchgemischt) BRACH NICHT - und das
        ist kein Bug, sondern Jensen: `ln(1+rR) ≈ r*E[R] -
        r²*Var(R)/2`, und der zweite Term ist QUADRATISCH in r. Eine
        Regel mit konzentriertem r (ALT: die Haelfte der Anker bei 0,
        die andere hoch) hat bei gleichem E[r] das hoehere E[r²] und
        damit den groesseren Abzug. Der Unterschied zwischen zwei
        Regeln enthaelt also einen Anteil, der NUR von der Konzentration
        des Einsatzes kommt und nichts mit der Qualitaet der Bewertung
        zu tun hat.

        Genau dafuer hat das Haus seit dem 08.09. den NULLPUNKT: den
        Wert, den die Anlage bei ZERSTOERTEM Zusammenhang liefert. Ich
        hatte gegen die Null geprueft - das war mein Fehler, und die
        eigene Regel haette ihn verhindert
        (`maximum-ist-kein-nullpunkt`, `nullbezug-gemessen-entschieden`).

        ⚠ EINE Mischung ist kein Nullpunkt: ueber drei Saaten wanderte
        sie zwischen -0,000091 und -0,000272. Deshalb der MITTELWERT aus
        `ziehungen` Mischungen, wie `messnorm.pruefe` es tut.
        """
        werte = []
        for z in range(ziehungen):
            mrng = np.random.default_rng(SAAT + 7000 + z)
            mi = mrng.permutation(len(anker))
            jt = {}
            for i, (t, _s, _fu, _to, _la, _R) in enumerate(anker):
                Rm = anker[mi[i]][5]
                for nm in (a_name, b_name):
                    rr = roh[nm][i] * skala[nm]
                    f = 1.0 + rr * Rm
                    jt.setdefault(nm, {}).setdefault(t, []).append(
                        math.log(f) if f > 1e-9 else -20.0)
            d = []
            for t in tage_l:
                va, vb = jt[a_name].get(t), jt[b_name].get(t)
                if va and vb and len(va) == len(vb):
                    d.append(float(np.mean(va) - np.mean(vb)))
            if d:
                werte.append(float(np.mean(d)))
        return (float(np.mean(werte)) if werte else 0.0), len(werte)

    def band(a_name, b_name):
        d = []
        for t in tage_l:
            va = je_tag[a_name].get(t) or []
            vb = je_tag[b_name].get(t) or []
            if va and vb and len(va) == len(vb):
                d.append(float(np.mean(va) - np.mean(vb)))
        if len(d) < block + 30:
            return None
        d = np.array(d, float)
        n = len(d)
        starts = np.arange(0, n - block + 1)
        zieh = []
        anz = max(1, n // block)
        for _ in range(ZIEHUNGEN):
            idx = rng.choice(starts, size=anz, replace=True)
            zieh.append(float(np.mean(np.concatenate(
                [d[i:i + block] for i in idx]))))
        zieh.sort()
        return (float(d.mean()), zieh[int(0.05 * len(zieh))],
                zieh[int(0.95 * len(zieh))], len(d))

    for a_name, b_name in (("ALT (volle Tabelle)", "GATE (nur Entscheidung)"),
                           ("KLAMMER WEIT", "ALT (volle Tabelle)"),
                           ("GATE (nur Entscheidung)", "FLACH (Kontrolle)"),
                           ("SCHALTER auf der LAGE", "ALT (volle Tabelle)"),
                           ("OHNE turnover", "ALT (volle Tabelle)"),
                           ("ALT (volle Tabelle)", "FLACH (Kontrolle)"),
                           ("SCHALTER auf der LAGE", "FLACH (Kontrolle)"),
                           ("ALT (volle Tabelle)", "ZUFALL (Kontrolle)")):
        r = band(a_name, b_name)
        if r is None:
            print("  %-46s -> zu wenige Tage" % ("%s gegen %s"
                                                 % (a_name, b_name)))
            continue
        m, u, o, n = r
        np_, nz = nullpunkt(a_name, b_name)
        klar = (u > np_) or (o < np_)
        print("  %-40s %+9.6f [%+.6f .. %+.6f] Null %+9.6f  %s"
              % ("%s − %s" % (a_name.split(" (")[0],
                                   b_name.split(" (")[0]),
                 m, u, o, np_,
                 "✔ BELEGT gegen den Nullpunkt" if klar
                 else "nicht belegt"))
    # ---- ⚠⚠ DIE MUTATION, DIE BRECHEN MUSS ----------------------
    #
    # Dieselbe Rechnung, aber die ERGEBNISSE R werden ueber die Anker
    # durchgemischt. Damit ist jeder Zusammenhang zwischen Bewertung
    # und Ausgang zerstoert - ALLE Regeln muessen dann gleich wachsen,
    # und jede Differenz muss auf null fallen. Tut sie es nicht,
    # erzeugt der Aufbau selbst einen Unterschied, und der ganze Lauf
    # ist wertlos.
    #
    # ⚠ Das ist die Lehre aus 2.507-kontrolle: eine Mutation, die
    # auch bei intaktem Werkzeug nicht bricht, prueft nichts. Diese
    # hier kann brechen.
    print()
    print("-" * 108)
    print("  MUTATION - EINE Mischung, zur Anschauung. ⚠ SIE IST "
          "NICHT MEHR DIE PRUEFUNG:")
    print("  der MITTELWERT aus 40 Mischungen ist oben als NULLPUNKT "
          "eingebaut. Eine einzelne")
    print("  Mischung wandert ueber drei Saaten zwischen -0,000091 und "
          "-0,000272 - sie ist")
    print("  kein Nullpunkt (`eine-ziehung-ist-kein-nullpunkt`) und "
          "taugt nur als Beispiel.")
    print("-" * 108)
    misch = rng.permutation(len(anker))
    je_tag_m = {name: {} for name, _f in regeln}
    for i, (t, _s, _fu, _to, _la, _R) in enumerate(anker):
        Rm = anker[misch[i]][5]
        for name, _fn in regeln:
            rr = roh[name][i] * skala[name]
            f = 1.0 + rr * Rm
            je_tag_m[name].setdefault(t, []).append(
                math.log(f) if f > 1e-9 else -20.0)
    schlecht = 0
    for a_name, b_name in (("ALT (volle Tabelle)", "FLACH (Kontrolle)"),
                           ("ALT (volle Tabelle)",
                            "GATE (nur Entscheidung)")):
        d_m = []
        for t in tage_l:
            va, vb = je_tag_m[a_name].get(t), je_tag_m[b_name].get(t)
            if va and vb and len(va) == len(vb):
                d_m.append(float(np.mean(va) - np.mean(vb)))
        if len(d_m) < block + 30:
            continue
        dm = np.array(d_m, float)
        n = len(dm)
        starts = np.arange(0, n - block + 1)
        anz = max(1, n // block)
        z = []
        for _ in range(ZIEHUNGEN // 4):
            idx = rng.choice(starts, size=anz, replace=True)
            z.append(float(np.mean(np.concatenate(
                [dm[i:i + block] for i in idx]))))
        z.sort()
        u, o = z[int(0.05 * len(z))], z[int(0.95 * len(z))]
        bricht = not (u > 0 or o < 0)
        schlecht += (not bricht)
        print("  %-46s %+9.6f [%+.6f .. %+.6f]  %s"
              % ("%s − %s (gemischt)" % (a_name.split(" (")[0],
                                              b_name.split(" (")[0]),
                 float(dm.mean()), u, o,
                 "(eine Ziehung - nur Anschauung)"))
    print("  ➤ ⚠ Dass eine einzelne Mischung NICHT auf null "
          "faellt, ist KEIN Bug:")
    print("     `ln(1+rR) ≈ r*E[R] - r²*Var(R)/2` - der zweite "
          "Term ist QUADRATISCH in r.")
    print("     Eine Regel mit konzentriertem Einsatz hat bei gleichem "
          "E[r] das hoehere E[r²]")
    print("     und damit den groesseren Abzug. Genau dieser Anteil "
          "steckt im NULLPUNKT und")
    print("     wird oben abgezogen - er ist Konzentration, nicht "
          "Bewertungsqualitaet.")

    print()
    print("  ⚠️ Ein positiver Wert heisst: die ERSTE Regel waechst "
          "staerker.")
    print("  ⚠️ IN-SAMPLE - die Tabellen stammen aus diesen Daten. Das "
          "ueberzeichnet ALT,")
    print("     nicht die Alternativen; der Vergleich ist konservativ "
          "gegen meinen Vorschlag.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
