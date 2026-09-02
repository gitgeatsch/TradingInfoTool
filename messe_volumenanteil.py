# -*- coding: utf-8 -*-
"""N-13-1': der VOLUMENANTEIL als Ersatz fuer den Turnover (02.09.2026).

## Warum dieses Werkzeug ueberhaupt gebraucht wird

N-13a hat gemessen: Turnover ist nur fuer **6 von 43** Krypto-Werten
bestimmbar. Ursache ist der Nenner - die Umlaufmenge kommt aus der
CoinMetrics-Community-API und deckt 66 ueberwiegend aeltere Werte ab.
Damit steht bei 84 % der Watchlist das Potential auf EINEM Beitrag
(Funding), und ein System mit einem Beitrag kann diesen Beitrag nicht mehr
pruefen.

N-13-1' schlaegt eine Groesse vor, die den fehlenden Nenner gar nicht
braucht:

    Volumenanteil = Umsatz(i,t) / Summe aller Umsaetze am Tag t

Reiner Querschnitt, nur aus dem Volumen - und das liegt fuer alle 578
Messreihen vor, fuer einen neu aufgenommenen Wert ab Tag 1 (N-13b).

## ⚠️⚠️ DIE FORMFRAGE KOMMT VOR DER MESSUNG

Stehende Vorgabe: *"Die FORM der Groesse vor der Messung klaeren."* Hier
ist sie nicht kosmetisch, sondern entscheidet, ob die Groesse ueberhaupt
zulaessig ist:

> **Ein Volumenanteil ist zuallererst ein GROESSENmass.** BTC hat jeden
> Tag einen grossen Anteil, ein kleiner Altcoin jeden Tag einen kleinen.
> Waere der Anteil je Symbol nahezu konstant, dann sagte eine Regel
> darauf nicht *"heute ist ein schlechter Zeitpunkt"*, sondern
> *"dieses Asset ist schlecht"* - und das ist **Regel 3**
> ("wir bewerten Zeitpunkte, nicht Assets").

Deshalb misst dieses Werkzeug in ZWEI Schritten, und der erste kann den
zweiten verhindern:

    --form     zerlegt die Streuung des Rangs: wieviel liegt ZWISCHEN den
               Symbolen (= Asset-Eigenschaft), wieviel INNERHALB eines
               Symbols ueber die Zeit (= Zeitpunkt-Aussage)?
    --wirkung  erst wenn die Form taugt: die Regel gegen ihren
               quotengleichen Zufall, mit Tagesklammer

⚠️ **Turnover laeuft als MASSSTAB mit.** Er ist der registrierte Beitrag,
den der Volumenanteil ersetzen soll. Ist seine Streuung genauso
asset-lastig, dann ist mein Einwand kein Einwand gegen den Kandidaten,
sondern gegen den Bestand - und das waere der wichtigere Befund.

## Die Vorabfestlegung

  Richtung    OBEN sperren - dieselbe Begruendung wie bei Turnover: viel
              Umschlag heisst viel Aufmerksamkeit heisst eher
              ueberbewertet. Die Gegenrichtung wird NICHT gemessen, das
              verdoppelte den Suchpreis.
  Zielgroesse Ertrag in R ueber H20, wie bei allen registrierten Beitraegen
  Zellen      ZWEI, beide vorab benannt (Methodik 2.49): der ROHE Anteil
              und der Anteil gegen die eigene Gewohnheit der letzten 20
              Tage. Eine dritte Form wird nicht gemessen.
  Bedingung   der Asset-Anteil der Rang-Streuung darf den des
              registrierten Beitrags (Turnover) nicht um mehr als
              5 Punkte uebersteigen - sonst ist es ein Asset-Mass

## Ergebnis von Schritt 1 (02.09.2026)

Auf der GEMEINSAMEN Menge (66 Symbole, 2.728 Kalendertage) und mit
geeichter Skala - ein je Symbol fester Wert liegt bei 95,9 %, reiner
Zufall bei 0,1 %:

    Volumenanteil roh        69,8 %   ✖ Asset-Mass, Bedingung gefallen
    Volumenanteil relativ     1,4 %   ✔ zulaessig
    Turnover (Massstab)      49,7 %

⚠️ Der wichtigere Nebenbefund steht in der letzten Zeile: **der
registrierte Beitrag Turnover ist zur Haelfte eine Asset-Eigenschaft.**

⚠️ MEINE ERSTE FASSUNG DIESES VERGLEICHS WAR FALSCH: sie stellte 578
Symbole gegen 65. Der Asset-Anteil haengt an der Zahl der Symbole - grobe
Raenge springen staerker und lassen eine Groesse zeitpunktartiger
aussehen. Der Unterschied wuchs nach der Korrektur von 6,2 auf 20,1
Punkte; die falsche Rechnung hatte das Problem KLEINER gezeigt.

    python messe_volumenanteil.py --form
    python messe_volumenanteil.py --wirkung
"""
import argparse
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B
import messe_regel_wirksamkeit as W

HORIZONT = 20
MIND_JE_TAG = 15


def _reihen():
    return B.lade()


def anteile(reihen, mindest=MIND_JE_TAG):
    """{tag: {symbol: Anteil am Tagesumsatz}} - reiner Querschnitt.

    ⚠️ UMSATZ, NICHT STUECKZAHL. `price_history_ohlc.volume` steht in
    Stueck; erst `volume * close` ist vergleichbar. Wer die Stueckzahl
    nimmt, misst den Preis mit - ein Wert zu 0,001 USD haette dann den
    groessten "Anteil" des Marktes.
    """
    je_tag = {}
    for sym, roh in reihen.items():
        for tag, schluss, _h, _t, vol in roh:
            if vol and vol > 0 and schluss > 0:
                je_tag.setdefault(tag, {})[sym] = float(vol) * float(schluss)
    aus = {}
    for tag, werte in je_tag.items():
        if len(werte) < mindest:
            continue
        summe = sum(werte.values())
        if summe > 0:
            aus[tag] = {s: v / summe for s, v in werte.items()}
    return aus


FENSTER = 20


def anteile_relativ(je_tag, fenster=FENSTER, mindest=MIND_JE_TAG):
    """Der Anteil GEGEN DIE EIGENE GEWOHNHEIT - die zweite Form.

    ⚠️ WARUM ES SIE BRAUCHT (02.09.2026). Der rohe Volumenanteil ist zu
    69,8 % eine Asset-Eigenschaft (Turnover: 49,7 %, auf derselben Menge
    gemessen). BTC hat jeden Tag einen grossen Anteil - eine Regel darauf
    sagte "dieses Asset", nicht "dieser Zeitpunkt", und das ist Regel 3.

    Diese Form teilt den festen Pegel heraus:

        relativ(i,t) = anteil(i,t) / Median(anteil(i, t-20 .. t-1))

    Was bleibt, ist die ABWEICHUNG von der eigenen Gewohnheit: "dieser
    Wert zieht heute ungewoehnlich viel Aufmerksamkeit auf sich."

    ⚠️ DER PREIS, und er gehoert genannt: das ist eine ZEITREIHE, und
    N-13b verlangt Querschnitte, weil ein neu aufgenommener Wert sonst
    blind ist. Hier sind es **20 Tage**, nicht 250 - die Blindheit ist
    kurz und endlich. Der Vergleich bleibt trotzdem ein Querschnitt: der
    RANG wird je Kalendertag ueber alle Werte gebildet.

    ⚠️ ZWEITE VORAB BENANNTE ZELLE. Der Suchpreis steigt damit von einer
    auf zwei Zellen (Methodik 2.49). Eine dritte Form wird NICHT gemessen.
    """
    tage = sorted(je_tag)
    verlauf, aus = {}, {}
    for tag in tage:
        werte = je_tag[tag]
        heute = {}
        for s, v in werte.items():
            vor = verlauf.get(s) or []
            if len(vor) >= fenster:
                m = float(np.median(vor[-fenster:]))
                if m > 0:
                    heute[s] = v / m
        if len(heute) >= mindest:
            aus[tag] = heute
        for s, v in werte.items():
            verlauf.setdefault(s, []).append(v)
    return aus


def turnover_je_tag(reihen, mindest=MIND_JE_TAG):
    """Der MASSSTAB: Turnover = Volumen / Umlaufmenge, nur 66 Symbole."""
    import messe_bewertungskennzahl as MB
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    je_tag = {}
    for sym, roh in reihen.items():
        m = menge.get(sym.upper())
        if not m:
            continue
        for tag, _schluss, _h, _t, vol in roh:
            n = m.get(tag)
            if n and n > 0 and vol and vol > 0:
                je_tag.setdefault(tag, {})[sym] = float(vol) / float(n)
    return {t: w for t, w in je_tag.items() if len(w) >= mindest}


def zerlege(je_tag, titel):
    """Wieviel der Rang-Streuung liegt ZWISCHEN, wieviel INNERHALB?

    Je Kalendertag wird der Rang gebildet (0..1), damit die Tagesklammer
    steht. Dann:

        zwischen  Varianz der SYMBOLMITTEL
        innerhalb mittlere Varianz je Symbol ueber die Zeit

    Ein reines Asset-Mass haette `innerhalb` nahe null. Eine reine
    Zeitpunkt-Aussage haette `zwischen` nahe null.

    ⚠️ Dazu die AUTOKORRELATION des Rangs: sagt der Rang von gestern den
    von heute? Bei einem Asset-Mass ist sie nahe 1. Sie ist das
    anschaulichere Mass, weil sie nicht von der Zahl der Symbole abhaengt.
    """
    je_sym = {}
    for tag in sorted(je_tag):
        werte = je_tag[tag]
        # ⚠️ `W.rang` nimmt eine FOLGE und gibt eine Folge zurueck - anders
        # als `marktrang._rang`, das mit Woerterbuechern arbeitet. Zwei
        # gleichnamige Funktionen mit verschiedener Schnittstelle; wer sie
        # verwechselt, bekommt hier einen TypeError und anderswo vielleicht
        # nicht.
        syms = list(werte)
        r = W.rang([werte[s] for s in syms])
        for s, x in zip(syms, r):
            je_sym.setdefault(s, []).append((tag, float(x)))
    je_sym = {s: v for s, v in je_sym.items() if len(v) >= 120}
    if not je_sym:
        print("  %-26s zu wenige Reihen" % titel)
        return None
    mittel = {s: float(np.mean([x for _t, x in v])) for s, v in je_sym.items()}
    zwischen = float(np.var(list(mittel.values())))
    innerhalb = float(np.mean([np.var([x for _t, x in v])
                               for v in je_sym.values()]))
    # Autokorrelation Lag 1 und Lag 20, je Symbol, dann Median
    ak1, ak20 = [], []
    for v in je_sym.values():
        x = np.array([w for _t, w in v])
        for lag, ziel in ((1, ak1), (20, ak20)):
            if len(x) > lag + 30:
                a, b = x[:-lag], x[lag:]
                if a.std() > 1e-9 and b.std() > 1e-9:
                    ziel.append(float(np.corrcoef(a, b)[0, 1]))
    anteil_asset = zwischen / (zwischen + innerhalb) if (zwischen + innerhalb) else float("nan")
    print("  %-26s  %5.1f %%      %+.3f      %+.3f     %4d Symbole"
          % (titel, 100 * anteil_asset,
             np.median(ak1) if ak1 else float("nan"),
             np.median(ak20) if ak20 else float("nan"), len(je_sym)))
    return {"anteil_asset": anteil_asset,
            "ak1": float(np.median(ak1)) if ak1 else float("nan"),
            "ak20": float(np.median(ak20)) if ak20 else float("nan"),
            "symbole": len(je_sym)}


def baue_anker(reihen, quelle_je_tag, horizont=HORIZONT):
    """Anker im Format von `messe_regel_wirksamkeit.wirkung`."""
    je_tag = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        breite = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(60, len(c) - horizont):
            r = breite[i]
            if not np.isfinite(r) or r <= 0:
                continue
            w = (quelle_je_tag.get(tage[i]) or {}).get(sym)
            if w is None:
                continue
            je_tag.setdefault(tage[i], []).append(
                {"sym": sym, "kennzahl": float(w),
                 "in_r": float((c[i + horizont] - c[i]) / r)})
    return {t: z for t, z in je_tag.items() if len(z) >= MIND_JE_TAG}


def vola_je_tag(reihen, mindest=MIND_JE_TAG):
    """Die nachlaufende Schwankungsbreite - der erste Mitlaeufer-Verdacht.

    Ein Tag mit ungewoehnlichem Volumen ist meist auch ein Tag mit
    ungewoehnlicher Bewegung. Traegt der Kandidat nur deshalb, waere er
    Volatilitaet mit Umweg - und die ist in F-165 bereits gemessen.
    """
    je_tag = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        br = B.spanne(h, t_, c, B.SCHWANKUNG)
        for i in range(60, len(c)):
            if np.isfinite(br[i]) and br[i] > 0 and c[i] > 0:
                je_tag.setdefault(tage[i], {})[sym] = float(br[i] / c[i])
    return {t: w for t, w in je_tag.items() if len(w) >= mindest}


def mitlaeufer(reihen, va):
    """Traegt der Kandidat noch, wenn die Verdaechtigen FESTGEHALTEN sind?

    Methodik 2.99, Schichtentest: je Kalendertag werden die Werte zuerst
    nach der Schicht in Fuenftel sortiert; die Regel sperrt dann ihr
    oberstes Fuenftel INNERHALB jedes Faches. Was uebrig bleibt, kann die
    Schicht nicht mehr erklaeren.

    ⚠️ ZWEI VERDAECHTIGE, beide vorab benannt:
        vola      ungewoehnliches Volumen faellt auf ungewoehnliche Bewegung
        turnover  dieselbe Familie - Umschlag gegen Bestand
    """
    import messe_kandidaten_als_regel as K
    rng = np.random.default_rng(20260902)
    block = max(90, HORIZONT * 3)
    vr = anteile_relativ(va)
    anker = baue_anker(reihen, vr)

    print()
    print("#" * 92)
    print("# GEGENPRUEFUNG — ist der Volumenanteil ein Mitlaeufer?")
    print("#" * 92)
    for name, schicht in (("VOLATILITAET", vola_je_tag(reihen)),
                          ("TURNOVER", turnover_je_tag(reihen))):
        # die Schicht muss dieselbe Form haben wie in `geschichtet`:
        # {tag: {symbol: wert}} - genau das liefern beide Funktionen.
        gem = {t: z for t, z in anker.items() if t in schicht}
        n_ank = sum(len(z) for z in gem.values())
        print()
        print("=" * 92)
        print("Volumenanteil INNERHALB der %s-Fuenftel  (%d Anker, %d Tage)"
              % (name, n_ank, len(gem)))
        print("=" * 92)
        M.urteil_tage("  NETTO (die Wirkung)",
                      K.geschichtet(gem, schicht), rng, block)
        M.urteil_tage("  Negativkontrolle",
                      K.geschichtet(gem, schicht, mische=rng), rng, block)
        # ungeschichtet auf DERSELBEN Teilmenge - sonst vergleicht man
        # zwei verschiedene Ankermengen
        M.urteil_tage("  ungeschichtet, gleiche Menge",
                      W.wirkung(gem, True)[0], rng, block)
    # ---- DIE ENTSCHEIDENDE MENGE ---------------------------------------
    #
    # ⚠️⚠️ WOFUER DER KANDIDAT UEBERHAUPT GEBAUT WUERDE. Der Schichtentest
    # gegen Turnover laeuft auf den 65 Werten, DIE Turnover haben. Genau
    # dort wird der Kandidat nicht gebraucht - er soll die 513 Werte
    # abdecken, fuer die es keinen Turnover gibt (N-13a: 6 von 43 in der
    # Watchlist).
    #
    # Auf dieser Menge ist die Mitlaeufer-Frage gegenstandslos: es gibt
    # nichts, dessen Mitlaeufer er sein koennte.
    #
    # ⚠️ EINE EINSCHRAENKUNG, und sie gehoert genannt: der Rang entsteht
    # hier INNERHALB der Teilmenge. In der Produktion entstuende er ueber
    # die ganze Messbasis (wie bei Funding). Das ist die konservativere
    # Rechnung - eine kleinere Grundmenge macht den Rang groeber.
    import messe_bewertungskennzahl as MB
    hat_turnover = set(MB.reihe("data/onchain_historie.db", "splycur"))
    ohne = {t_: [x for x in z if x["sym"].upper() not in hat_turnover]
            for t_, z in anker.items()}
    ohne = {t_: z for t_, z in ohne.items() if len(z) >= MIND_JE_TAG}
    n_o = sum(len(z) for z in ohne.values())
    syms_o = len({x["sym"] for z in ohne.values() for x in z})
    print()
    print("=" * 92)
    print("DIE ENTSCHEIDENDE MENGE: nur Werte OHNE Turnover  "
          "(%d Anker, %d Symbole, %d Tage)" % (n_o, syms_o, len(ohne)))
    print("=" * 92)
    M.urteil_tage("  NETTO (die Wirkung)", W.wirkung(ohne, True)[0], rng, block)
    M.urteil_tage("  Negativkontrolle",
                  W.wirkung(ohne, True, mische=rng)[0], rng, block)
    for s_ in (0.02, 0.05):
        M.urteil_tage("  Positivkontrolle %+.2f R" % s_,
                      W.wirkung(ohne, True, pflanze=s_)[0], rng, block)

    print()
    print("  LESART: bleibt die geschichtete Wirkung nahe der")
    print("  ungeschichteten, ist der Kandidat EIGENSTAENDIG. Faellt sie")
    print("  zusammen, war es die Schicht.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--form", action="store_true",
                   help="Schritt 1: Asset-Mass oder Zeitpunkt-Aussage?")
    p.add_argument("--wirkung", action="store_true",
                   help="Schritt 2: die Regel gegen ihren Zufall")
    p.add_argument("--mitlaeufer", action="store_true",
                   help="Schritt 3: Schichtentest gegen Vola und Turnover")
    a = p.parse_args()
    if not (a.form or a.wirkung or a.mitlaeufer):
        p.error("--form, --wirkung oder --mitlaeufer")

    print("Lade Kursreihen...", flush=True)
    reihen = _reihen()
    va = anteile(reihen)
    print("Volumenanteil: %d Kalendertage, %d Reihen"
          % (len(va), len(reihen)))

    if a.mitlaeufer:
        mitlaeufer(reihen, va)
        return

    if a.form:
        tu = turnover_je_tag(reihen)
        # ⚠️⚠️ AUF DIESELBE MENGE EINSCHRAENKEN - sonst sind die beiden
        # Zahlen nicht vergleichbar (Pruefliste 2.80, "gleiche Arme").
        #
        # Meine erste Fassung stellte 578 Symbole gegen 65 und schloss aus
        # dem Unterschied auf die Form. Der Asset-Anteil haengt aber an der
        # Zahl der Symbole: bei 578 ist der Rang fein aufgeloest, bei 65
        # grob - grobe Raenge springen staerker und lassen die Groesse
        # zeitpunktartiger aussehen, als sie ist. Der Vergleich war zu
        # Gunsten des Massstabs verzerrt.
        gemeinsame_tage = set(va) & set(tu)
        gemeinsame_syms = ({s for w in tu.values() for s in w}
                           & {s for w in va.values() for s in w})
        eng = lambda q: {t: {s: v for s, v in q[t].items()
                             if s in gemeinsame_syms}
                         for t in sorted(gemeinsame_tage)
                         if len({s for s in q[t] if s in gemeinsame_syms})
                         >= MIND_JE_TAG}
        va_e, tu_e = eng(va), eng(tu)
        print()
        print("=" * 84)
        print("SCHRITT 1 — IST DAS EIN ASSET-MASS ODER EINE ZEITPUNKT-AUSSAGE?")
        print("=" * 84)
        print("  Gemeinsame Menge: %d Symbole, %d Kalendertage"
              % (len(gemeinsame_syms), len(va_e)))
        print()
        print("  Groesse                      Asset-Anteil  Autokorr.1  Autokorr.20")
        e_va = zerlege(va_e, "Volumenanteil roh")
        e_vr = zerlege(eng(anteile_relativ(va)), "Volumenanteil relativ")
        e_tu = zerlege(tu_e, "Turnover (Massstab)")

        # ---- DIE SKALA EICHEN ------------------------------------------
        #
        # 55 % gegen 50 % sagt fuer sich genommen nichts - man muss wissen,
        # wo auf der Skala ein reines Asset-Mass und ein reines Rauschen
        # liegen. Beides wird hier gerechnet, auf DERSELBEN Menge.
        rng2 = np.random.default_rng(20260902)
        fest, zufall = {}, {}
        mittel_je_sym = {}
        for t, w in va_e.items():
            for s, v in w.items():
                mittel_je_sym.setdefault(s, []).append(v)
        mittel_je_sym = {s: float(np.mean(v)) for s, v in mittel_je_sym.items()}
        for t, w in va_e.items():
            fest[t] = {s: mittel_je_sym[s] for s in w}
            zufall[t] = {s: float(rng2.random()) for s in w}
        print()
        print("  Die Skala, auf derselben Menge geeicht:")
        e_fest = zerlege(fest, "POSITIVKONTROLLE: fest")
        e_null = zerlege(zufall, "NEGATIVKONTROLLE: Zufall")
        print()
        print("  LESART: 'Asset-Anteil' ist der Teil der Rang-Streuung, der")
        print("  ZWISCHEN den Symbolen liegt. Die beiden Kontrollen spannen")
        print("  die Skala auf: ein je Symbol FESTER Wert markiert das eine")
        print("  Ende, reiner Zufall das andere.")
        print()
        if e_va and e_tu and e_fest and e_null:
            spanne = e_fest["anteil_asset"] - e_null["anteil_asset"]
            lage = lambda e: (e["anteil_asset"] - e_null["anteil_asset"]) / spanne \
                if spanne > 0 else float("nan")
            print("  Auf der geeichten Skala (0 = Zufall, 1 = feste Asset-Eigenschaft):")
            print("    roh %.2f · relativ %.2f · Turnover %.2f"
                  % (lage(e_va), lage(e_vr) if e_vr else float("nan"),
                     lage(e_tu)))
            print()
            print("  VORAB FESTGELEGTE BEDINGUNG: der Kandidat darf nicht")
            print("  asset-lastiger sein als der registrierte Beitrag")
            print("  (Turnover %.1f %%, plus 5 Punkte Toleranz)."
                  % (100 * e_tu["anteil_asset"]))
            grenze = e_tu["anteil_asset"] + 0.05
            for name, e in (("roh    ", e_va), ("relativ", e_vr)):
                if not e:
                    print("    %s  nicht messbar" % name)
                    continue
                print("    %s %.1f %%  ->  %s"
                      % (name, 100 * e["anteil_asset"],
                         "✔ ZULAESSIG - Schritt 2 darf fuer diese Form laufen"
                         if e["anteil_asset"] <= grenze else
                         "✖ ASSET-MASS - eine Wirkungsmessung wuerde "
                         "Regel 3 messen"))
        return

    # ---- Schritt 2 ------------------------------------------------------
    rng = np.random.default_rng(20260902)
    print()
    print("#" * 92)
    print("# KONTROLLE ZUERST — Turnover muss reproduzieren")
    print("#" * 92)
    tu = turnover_je_tag(reihen)
    W.bericht("KONTROLLE TURNOVER H20", baue_anker(reihen, tu), True, rng,
              mit_positivkontrolle=False)
    # ⚠️ NUR DIE RELATIVE FORM. Die rohe ist in Schritt 1 an der vorab
    # gesetzten Bedingung gescheitert (69,8 % Asset-Anteil gegen 49,7 %);
    # sie hier trotzdem zu messen hiesse, eine gefallene Bedingung im
    # Nachhinein zu uebergehen - genau der Fehler vom 31.08. beim
    # Schnittabstand.
    vr = anteile_relativ(va)
    W.bericht("N-13-1' VOLUMENANTEIL RELATIV H20",
              baue_anker(reihen, vr), True, rng)


if __name__ == "__main__":
    main()
