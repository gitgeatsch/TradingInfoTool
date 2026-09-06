# -*- coding: utf-8 -*-
"""N24 — IST `vola` EIN MARKTBEFUND ODER UNSERE EIGENE GEOMETRIE? (06.09.2026)

## Warum diese Pruefung, bevor `vola` registriert wird

`vola` ist die staerkste gemessene Groesse:

    Dreiteilung  +2,921 · -0,264 · -2,646   (2/2 Nachbarn, BEIDE Haelften)
    als Regel    +0,01043 [+0,00857 .. +0,01250]

Nach der Kalibrierung traege sie **88 % des Beitragsgewichts**. Genau
deshalb darf sie nicht ungeprueft hinein.

## ⚠️⚠️ DER VERDACHT — er steht im Code selbst

`agent/wahrscheinlichkeit.BEITRAEGE` fuehrt:

    Beitrag(name="Trichter (uebliche Kursbewegung)", zustand="enthalten",
            warum="er BESTIMMT die Geometrie und damit die Basisrate -
                   er ist schon drin und darf nicht zweimal zaehlen")

Der Trichter ist die ATR. Und `vola` ist:

    kz = br[i] / median(br[i-250 .. i])          # ATR relativ zu SICH SELBST

Formal nicht dasselbe: der Trichter ist die ABSOLUTE ATR (sie setzt die
Barrieren), `vola` die RELATIVE. Nach der Skalierung ist die absolute
Groesse herausgekuerzt, die relative nicht.

**Aber die Frage bleibt offen:** sagt `vola` etwas ueber den MARKT - oder
nur darueber, wie gut unsere ATR-skalierte Geometrie heute passt? Im
Messaufbau stand der Stop bei `c - 1,0 x br[i]`, also selbst auf der ATR.

## ⚠️⚠️ WAS DER ERSTE VORABTEST GEFUNDEN HAT (06.09., erste Fassung)

In einer Kunstwelt mit Volatilitaetsclustern und **null Richtungs-
information** fand der Originalaufbau `vola` trotzdem:

    G0 heutige ATR   +0,01084 [+0,00658 .. +0,01521]  0 von 5  ✔ TRAEGT
    Drittel          +0,024 · -0,002 · -0,022   - dieselbe FORM wie echt

**Der Mechanismus ist rein mechanisch:** niedrige relative Vola heisst,
die Volatilitaet kehrt nach oben zurueck. Dann wird eine Barriere
ueberhaupt ERREICHT, statt dass der Anker flach auslaeuft. Ein flacher
Auslauf zaehlt als 0 - genau wie ein Stop. Und ein aufgeloester Trade ist
bei CRV 2 zu etwa einem Drittel ein Treffer.

    mehr Aufloesung -> mehr Treffer, OHNE einen Hauch von Richtung.

Die erste Gegenprobe (G1/G2: Barrieren, die sich nicht mit `vola` bewegen)
taugt dafuer NICHT - sie wird von einem GROESSENeffekt mit umgekehrtem
Vorzeichen erschlagen (ein ruhiges Asset erreicht eine feste Barriere
seltener). Beide Welten kamen negativ heraus, auch die mit echter Drift.

## Die Zerlegung — jetzt auf RICHTUNG statt auf Geometrie

    G0   der Originalaufbau, CRV 2, Barrieren auf der heutigen ATR
         ⚠️ nur zur REPRODUKTION - er mischt Aufloesung und Richtung

    GS   SYMMETRISCHE Barrieren (+-1 x heutige ATR), und gezaehlt wird
         nur unter den AUFGELOESTEN: wer oben zuerst?
         ⚠️ Unter einem Zufallslauf ist das 0,5 - unabhaengig von der
            Volatilitaet. Die Aufloesungsquote ist herausbedingt, die
            Groesse herausskaliert. Was bleibt, ist RICHTUNG.

    VZ   das Vorzeichen der 5-Tage-Rendite
    B    `bewegung_r` auf dem eigenen ATR-Median
         ⚠️⚠️ BEIDE SIND KONTAMINIERT - vom Vorabtest gefangen, siehe unten.
            Sie werden gezeigt, aber sie entscheiden NICHT.

## ⚠️⚠️ DER ZWEITE VORABTEST — drei von vier Massstaeben feuern im Leeren

In Welt A (null Richtungsinformation) ergab die Regel:

    G0   +0,01084 [+0,00658 .. +0,01521]   ⚠️ feuert
    GS   +0,00279 [-0,00141 .. +0,00701]   ✔ sauber
    VZ   +0,00610 [+0,00071 .. +0,01081]   ⚠️ feuert
    B    +0,04050 [+0,00526 .. +0,07099]   ⚠️ feuert

**Die Gruende sind herleitbar - und sie gelten fuer ECHTE Daten genauso:**

  VZ  Bei lognormalen Kursen liegt der Median UNTER dem Mittel, und zwar
      umso weiter, je hoeher die Volatilitaet: P(Rendite > 0) sinkt mit
      Sigma, ganz ohne Richtung. Wer die ruhigen behaelt, hebt die Quote.
  B   erbt dieselbe Schiefe ueber das Tagesmittel.
  G0  die Aufloesungsquote (oben beschrieben).

  GS  hat als EINZIGER einen Nullpunkt, der VORAB herleitbar bei 0,5
      liegt - unabhaengig von der Volatilitaet. Symmetrische Barrieren,
      und nur aufgeloeste Anker zaehlen: die Groesse kuerzt sich heraus,
      die Aufloesungsquote ist herausbedingt.

⚠️ GS ist deshalb nicht der Massstab, der das gewuenschte Ergebnis
   liefert, sondern der einzige mit einem BEGRUENDBAREN Nullpunkt. Der
   Grund stand vor der Messung fest; die Kunstwelt hat ihn bestaetigt.

    ENTSCHEIDET: GS.   Gezeigt, aber ohne Stimme: G0, VZ, B.

## Vorabtest (`--probe`) — auf KUNSTDATEN, mit dem Grenzfall

    Welt A  Zufallslauf MIT Volatilitaetsclustern, KEINE Richtungsinfo
            -> ein `vola`-Befund kann hier nur GEOMETRIE sein
            Erwartung: G0 zeigt etwas (der Artefakt), GS und VZ NICHT
    Welt B  wie A, aber niedrige relative Vola -> echte Aufwaertsdrift
            Erwartung: GS UND VZ zeigen es

    python n24_vola_geometrieprobe.py --probe
    python n24_vola_geometrieprobe.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_regel_wirksamkeit as W                          # noqa: E402

CRV, BRUCH, HORIZONT, BLOCK = 2.0, 5.0, 5, 15
MISCHUNGEN = 5
FEST_PROZENT = 0.05          # G2: 5 % vom Kurs je Seite
VORLAUF = 260                # `vola` braucht 250 Tage Median + Puffer

# ⚠️ `bedingt` heisst: der Anker zaehlt nur, wenn er ueberhaupt aufgeloest
# hat. Damit ist die AUFLOESUNGSQUOTE herausbedingt - genau der Kanal, ueber
# den der Kunstwelt-Artefakt lief.
MASSSTAEBE = (("g0", "G0 CRV 2 auf heutiger ATR", False),
              ("gs", "GS symmetrisch, nur aufgeloest", True),
              ("vz", "VZ Vorzeichen der Rendite", False),
              ("bewegung_r", "B  bewegung_r", False),
              # ⚠️ NICHT Kontrolle, sondern der VERDACHT SELBST: loesen
              # ruhige Assets ihre Barrieren oefter auf? Traegt das, ist
              # `vola` kein Nullbefund, sondern ein Hebel an der GEOMETRIE.
              ("auf", "AUF Aufloesungsquote (CRV 2)", False),
              # ⚠️ DIE ZERLEGUNGSPROBE: G0 = AUF x (Gewinnanteil unter den
              # Aufgeloesten). Ist G0R null, ist G0 VOLLSTAENDIG die
              # Aufloesungsquote - dann bleibt kein Rest zu erklaeren.
              ("g0r", "G0R Treffer|aufgeloest", False),
              # ⚠️⚠️ DIE ENTSCHEIDENDE GEGENPROBE (06.09., N25).
              # Die Trefferquote behandelt einen FLACHEN AUSLAUF wie einen
              # Stop - beides zaehlt 0. Wirtschaftlich ist das falsch: ein
              # flacher Auslauf kostet fast nichts, ein Stop kostet 1 R.
              #
              # Wer nur die AUFLOESUNGSQUOTE hebt, wandelt flache Auslaeufe
              # in Aufloesungen um. Bei CRV 2 und richtungsneutraler
              # Aufloesung ist deren Erwartungswert
              #     1/3 x (+2 R)  +  2/3 x (-1 R)  =  0
              # Er hebt also die QUOTE, ohne den ERTRAG zu heben.
              #
              # Ein Beitrag, der hier nichts bringt, gehoert nicht in die
              # Bewertung - egal wie gut er in der Quote aussieht.
              ("ewr", "EWR Erwartungswert in R", False))


def _kz_und_geometrie(c, h, t, br, i):
    """Kennzahl und die drei Stopweiten an Anker i.

    ⚠️ NUR VERGANGENHEIT: `median(br[i-250 .. i])` schliesst i ein, aber
    nichts danach. `br[i]` selbst kennt nur Kurse bis i.
    """
    med = float(np.median(br[i - 250:i + 1]))
    if not np.isfinite(med) or med <= 0:
        return None, None
    kz = float(br[i] / med)
    weiten = (float(br[i]), med, float(FEST_PROZENT * c[i]))
    return kz, weiten


def _ausgang(c, h, t, i, weite, crv):
    """+1 Ziel zuerst, -1 Stop zuerst, 0 keins von beiden."""
    ziel, stop = c[i] + crv * weite, c[i] - weite
    for j in range(i + 1, i + HORIZONT + 1):
        if t[j] <= stop:
            return -1
        if h[j] >= ziel:
            return +1
    return 0


def baue(reihen):
    """je Tag: Liste mit Kennzahl, drei Trefferfahnen, bewegung_r."""
    je_tag: dict = {}
    for sym, z in reihen.items():
        tage = [x[0] for x in z]
        c = np.array([x[1] for x in z], float)
        h = np.array([x[2] for x in z], float)
        t = np.array([x[3] for x in z], float)
        br = B.spanne(h, t, c, B.SCHWANKUNG)
        vh = c[1:] / np.maximum(c[:-1], 1e-12)
        bruch = (vh > BRUCH) | (vh < 1.0 / BRUCH)
        for i in range(max(B.SCHWANKUNG, VORLAUF), len(c) - HORIZONT):
            if not np.isfinite(br[i]) or br[i] <= 0:
                continue
            if bruch[i:i + HORIZONT].any():
                continue
            kz, weiten = _kz_und_geometrie(c, h, t, br, i)
            if kz is None:
                continue
            heute, med = weiten[0], weiten[1]
            rend = float(c[i + HORIZONT] - c[i])
            # GS: symmetrisch auf der HEUTIGEN ATR - die Groesse kuerzt sich
            # heraus. `None` heisst "nicht aufgeloest" und faellt weg.
            sym = _ausgang(c, h, t, i, heute, 1.0)
            roh = _ausgang(c, h, t, i, heute, CRV)
            e = {"kennzahl": kz,
                 # flach = zum Marktpreis geschlossen, nicht 0 gesetzt
                 "ewr": (CRV if roh > 0 else -1.0 if roh < 0
                         else float((c[i + HORIZONT] - c[i]) / heute)),
                 "g0": 1.0 if roh > 0 else 0.0,
                 "auf": 0.0 if roh == 0 else 1.0,
                 "g0r": None if roh == 0 else (1.0 if roh > 0 else 0.0),
                 "gs": (1.0 if sym > 0 else 0.0) if sym != 0 else None,
                 "vz": 1.0 if rend > 0 else 0.0,
                 # ⚠️ bewegung_r auf der MEDIAN-Weite - barrierenfrei, und
                 # der Nenner haengt nicht am Zaehler von `vola`.
                 "bewegung_r": rend / med}
            je_tag.setdefault(tage[i], []).append(e)
    return {t: z for t, z in je_tag.items() if len(z) >= 20}


def drittel(je_tag, feld, mische=None):
    """Die drei Faecher als Abweichung vom Tagesmittel."""
    reihen = [dict() for _ in range(3)]
    for tag, z0 in je_tag.items():
        z = [x for x in z0 if x[feld] is not None]
        if len(z) < 9:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x[feld] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * 3).astype(int), 2)
        basis = float(y.mean())
        for i in range(3):
            m = f == i
            if m.sum() >= 3:
                reihen[i][tag] = float(y[m].mean()) - basis
    return reihen


def regel(je_tag, feld, mische=None):
    """Bestes Drittel behalten, oberstes Fach sperren - die Regelwirkung."""
    aus = {}
    for tag, z0 in je_tag.items():
        # ⚠️ Bei GS faellt jeder nicht aufgeloeste Anker heraus - erst DANN
        # wird gerangt, sonst raenge man gegen Anker, die gar nicht zaehlen.
        z = [x for x in z0 if x[feld] is not None]
        if len(z) < 9:
            continue
        w = np.array([x["kennzahl"] for x in z], float)
        y = np.array([x[feld] for x in z], float)
        r = W.rang(w)
        if mische is not None:
            r = mische.permutation(r)
        f = np.minimum((r * 3).astype(int), 2)
        frei = f < 2
        if frei.sum() < 3 or (~frei).sum() < 1:
            continue
        aus[tag] = float(y[frei].mean()) - float(y.mean())
    return aus


def traegt(b, k):
    """⚠️ ZWEISEITIG. Ein Band, das ganz im MINUS liegt, ist genauso ein
    Befund wie eines ganz im Plus - nur mit umgekehrtem Vorzeichen.

    06.09.2026, vom N25-Vorabtest gefangen: bei `vola` (ATR / eigener
    Median) heisst NIEDRIG "gleich steigt die Vola" -> MEHR Aufloesung.
    Bei roher Volatilitaet heisst NIEDRIG schlicht "ruhig" -> WENIGER.
    Derselbe Kanal, umgekehrtes Vorzeichen. Ein einseitiges Kriterium
    haette den zweiten Fall fuer einen Nullbefund gehalten.
    """
    if b is None:
        return False
    return (b[1] > 0 or b[2] < 0) and k == 0


def band(d, zieh=2000, saat=20260906):
    rng = np.random.default_rng(saat)
    x = np.array([d[q] for q in sorted(d)], float)
    n = len(x)
    if n < BLOCK + 30:
        return None
    nb = max(1, n // BLOCK)
    st = np.arange(n - BLOCK + 1)
    a = np.empty(zieh)
    for j in range(zieh):
        s = rng.choice(st, nb)
        a[j] = np.concatenate([x[i:i + BLOCK] for i in s]).mean()
    return (float(x.mean()), float(np.percentile(a, 2.5)),
            float(np.percentile(a, 97.5)))


def kontrolle(je_tag, feld, echt):
    """⚠️ FUENF Mischungen - eine Ziehung ist kein Nullpunkt."""
    treffer = 0
    for k in range(MISCHUNGEN):
        rng = np.random.default_rng(70000 + k)
        b = band(regel(je_tag, feld, mische=rng))
        if b and abs(b[0]) >= abs(echt):
            treffer += 1
    return treffer


# ----------------------------------------------------------------- Kunstwelt
def kunstwelt(mit_drift: bool, tage=1400, symbole=45, saat=4242,
              cluster=0.10):
    """Zufallslauf MIT Volatilitaetsclustern.

    Welt A (mit_drift=False)  keinerlei Richtungsinformation
    Welt B (mit_drift=True)   niedrige relative Vola -> Aufwaertsdrift
    """
    rng = np.random.default_rng(saat)
    reihen = {}
    for s in range(symbole):
        # Volatilitaet als eigener, traeger Prozess (Clustering)
        lv = np.zeros(tage)
        for i in range(1, tage):
            lv[i] = 0.97 * lv[i - 1] + rng.normal(0, cluster)
        vol = 0.03 * np.exp(lv)
        c = np.empty(tage)
        c[0] = 100.0
        for i in range(1, tage):
            drift = 0.0
            if mit_drift and i > 260:
                # relative Vola aus der VERGANGENHEIT
                rel = vol[i - 1] / np.median(vol[max(0, i - 251):i])
                if rel < 0.9:
                    drift = 0.0035
            c[i] = c[i - 1] * float(np.exp(drift
                                           + rng.normal(0, vol[i]) - 0.5 * vol[i] ** 2))
        spanne = c * vol
        h = c + np.abs(rng.normal(0, 0.6, tage)) * spanne
        t = c - np.abs(rng.normal(0, 0.6, tage)) * spanne
        reihen["K%02d" % s] = [(("2020-01-01_%04d" % i), c[i], h[i], t[i], 1.0)
                               for i in range(tage)]
    return reihen


def zeige(je_tag, titel):
    print()
    print("  %s" % titel)
    print("     %-28s %10s %24s  %s"
          % ("Massstab", "Regel", "Band", "Kontrolle"))
    erg = {}
    for feld, lab, _bed in MASSSTAEBE:
        b = band(regel(je_tag, feld))
        if not b:
            print("     %-28s   zu wenige Tage" % lab)
            continue
        k = kontrolle(je_tag, feld, b[0])
        tr = traegt(b, k)
        print("     %-28s %+9.5f [%+.5f .. %+.5f]  %d von %d %s"
              % (lab, b[0], b[1], b[2], k, MISCHUNGEN,
                 "✔ TRAEGT" if tr else ""), flush=True)
        erg[feld] = (b[0], b[1], tr)
    for feld, lab, _bed in MASSSTAEBE:
        d = drittel(je_tag, feld)
        print("     %-28s %s" % ("Drittel " + lab.split()[0], "  ".join(
            "%+.4f" % (band(x)[0] if band(x) else float("nan")) for x in d)))
    return erg


def main() -> int:
    t0 = time.time()
    probe = "--probe" in sys.argv
    print("=" * 92)
    print("N24 — traegt `vola` ueber den MARKT oder ueber UNSERE GEOMETRIE?")
    print("=" * 92)

    if probe:
        print("  VORABTEST auf Kunstdaten — der Grenzfall zuerst")
        a = zeige(baue(kunstwelt(False)),
                  "WELT A — Vola-Cluster, KEINE Richtungsinfo "
                  "(ein Befund waere reine Geometrie)")
        a2 = zeige(baue(kunstwelt(False, cluster=0.20, saat=9191)),
                   "WELT A2 — DOPPELT so starke Cluster, weiter keine "
                   "Richtung (⚠️ GS muss AUCH hier schweigen)")
        b = zeige(baue(kunstwelt(True)),
                  "WELT B — niedrige relative Vola -> echte Drift "
                  "(muss durchkommen)")
        print()
        print("  URTEIL DES VORABTESTS")
        ok = True
        # 1) Der echte Effekt MUSS unter GS durchkommen.
        if b.get("gs", (0, 0, False))[2]:
            print("     ✔ ein ECHTER Effekt kommt unter GS durch (%+.5f)"
                  % b["gs"][0])
        else:
            print("     ⚠️ ein echter Effekt kommt NICHT durch - der Test "
                  "ist zu streng oder falsch gebaut")
            ok = False
        # 2) ⚠️ DER GRENZFALL: der reine Artefakt darf GS NICHT ausloesen -
        #    und das bei BEIDEN Clusterstaerken (Eigenschaft, nicht Punkt).
        stumm = [n for n, w in (("A", a), ("A2", a2))
                 if not w.get("gs", (0, 0, False))[2]]
        if len(stumm) == 2:
            print("     ✔ und GS schweigt in BEIDEN artefaktreinen Welten "
                  "(%+.5f · %+.5f)" % (a["gs"][0], a2["gs"][0]))
        else:
            print("     ⚠️⚠️ GS feuert im Leeren (stumm nur in: %s) - dann "
                  "trennt es nicht, was es trennen soll"
                  % (", ".join(stumm) or "keiner"))
            ok = False
        # 3) Und der Artefakt muss unter G0 sichtbar bleiben - sonst ist die
        #    Kunstwelt nicht der Grenzfall, fuer den sie gebaut wurde.
        if a.get("g0", (0, 0, False))[2]:
            print("     ✔ die Kunstwelt IST der Grenzfall (G0 %+.5f in "
                  "einer Welt ohne Richtung)" % a["g0"][0])
        else:
            print("     ⚠️ die Kunstwelt zeigt den Artefakt nicht - sie "
                  "prueft den Grenzfall nicht")
            ok = False
        print("     %s" % ("Der Test darf auf die echten Daten."
                           if ok else
                           "⚠️ NICHT auf die echten Daten - erst reparieren."))
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 0 if ok else 1

    print("  Lade Reihen ...", flush=True)
    reihen = B.lade()
    je_tag = baue(reihen)
    anker = sum(len(z) for z in je_tag.values())
    print("  %d Kalendertage, %d Anker (Vorlauf %d Tage)"
          % (len(je_tag), anker, VORLAUF))
    erg = zeige(je_tag, "ECHTE DATEN")

    print()
    print("=" * 92)
    print("WAS DAS HEISST")
    print("=" * 92)
    g0 = erg.get("g0", (0.0, 0.0, False))
    gs = erg.get("gs", (0.0, 0.0, False))
    vz = erg.get("vz", (0.0, 0.0, False))
    bw = erg.get("bewegung_r", (0.0, 0.0, False))
    # ⚠️ GS ENTSCHEIDET - vorab festgelegt, mit herleitbarem Nullpunkt.
    # VZ und `bewegung_r` sind vom Vorabtest als kontaminiert erwiesen und
    # haben keine Stimme. Wer sie hier mitzaehlt, sucht sich den Massstab
    # nach dem Ergebnis aus.
    auf = erg.get("auf", (0.0, 0.0, False))
    if gs[2]:
        print("  ✔ `vola` traegt RICHTUNG - unter symmetrischen Barrieren,")
        print("     nur aufgeloeste Anker: Groesse herausskaliert,")
        print("     Aufloesung herausbedingt. Ein Marktbefund.")
        print("     Registrierung als Beitrag ist begruendet.")
    else:
        print("  ⚠️⚠️ `vola` traegt KEINE Richtung. Der G0-Befund ist dann")
        print("     die AUFLOESUNGSQUOTE: ruhige Assets loesen ihre Barrieren")
        print("     oefter auf, und ein aufgeloester Trade ist zu einem")
        print("     Drittel ein Treffer. Das ist eine Aussage ueber unsere")
        print("     GEOMETRIE, nicht ueber den Markt - und gehoert damit in")
        print("     die Stop-/Zielwahl, nicht in `BEITRAEGE`.")
        print("     ⚠️ Das ist KEIN Nullbefund ueber `vola` - es ist ein")
        print("        Befund darueber, WO `vola` hingehoert.")
        if auf[2]:
            print()
            print("  ✔✔ UND DER MECHANISMUS IST BELEGT: die Aufloesungsquote")
            print("     selbst traegt %+.5f [%+.5f .. ...]. Ruhige Assets"
                  % (auf[0], auf[1]))
            print("     loesen ihre Barrieren nachweisbar oefter auf.")
            print("     ⚠️ Damit ist `vola` ein Hebel an der GEOMETRIE:")
            print("        wie weit der Stop, wie lang der Horizont - und")
            print("        ueber `hebel = verlustanteil / stop_rel` faellt")
            print("        daraus der HEBEL. Das ist die Achse, die laut")
            print("        Befundlage fehlt (Horizont-Achse).")
        else:
            print()
            print("  ⚠️ Aber auch die Aufloesungsquote traegt nicht (%+.5f) -"
                  % auf[0])
            print("     dann ist der Mechanismus NICHT der vermutete, und")
            print("     der G0-Befund bleibt unerklaert. Nicht registrieren,")
            print("     bevor das geklaert ist.")
    print("     G0 %+.5f · GS %+.5f · VZ %+.5f · B %+.5f · AUF %+.5f"
          % (g0[0], gs[0], vz[0], bw[0], auf[0]))
    print("     ⚠️ VZ und B haben keine Stimme (Vorabtest: kontaminiert).")
    g0r = erg.get("g0r", (0.0, 0.0, False))
    print()
    print("  DIE ZERLEGUNGSPROBE — bleibt vom G0-Befund etwas uebrig,")
    print("  wenn man auf die AUFGELOESTEN bedingt?")
    # ⚠️⚠️ DER REST WIRD NICHT GEGEN NULL GEPRUEFT, SONDERN GEGEN DEN
    # ARTEFAKT. G0R hat ASYMMETRISCHE Barrieren (+2/-1) - dort kommt der
    # Groessenkanal auch nach dem Bedingen zurueck: wer sich mehr bewegt,
    # erreicht eher das FERNE Ziel. Genau deshalb ist GS symmetrisch.
    # Gemessen in den richtungsfreien Kunstwelten (06.09.):
    #     Welt A  +0,00770    Welt A2  +0,00731
    ARTEFAKT_G0R = 0.00750
    print("     Der Rest betraegt G0R %+.5f." % g0r[0])
    print("     ⚠️ Er wird gegen den ARTEFAKT geprueft, nicht gegen null:")
    print("        in den richtungsfreien Kunstwelten ergab G0R %+.5f und"
          % 0.00770)
    print("        %+.5f - G0R ist wegen der ASYMMETRIE (+2/-1) selbst" % 0.00731)
    print("        nicht richtungsrein.")
    if abs(g0r[0]) <= 1.5 * ARTEFAKT_G0R:
        print("     ✔ Der Rest liegt in der Groesse des Artefakts. Es")
        print("       bleibt nichts, was man als Marktbefund lesen koennte.")
    else:
        print("     ⚠️ Der Rest UEBERSTEIGT den Artefakt deutlich - dann")
        print("       gehoert er erklaert, bevor `vola` abgeraeumt wird.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
