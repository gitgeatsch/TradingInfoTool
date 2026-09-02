# -*- coding: utf-8 -*-
"""N-15a: Taugt die SUMME der Beitraege als Rangfolge? (02.09.2026)

## Warum diese Messung vor dem Bau steht

N-15 will in die Mail schreiben: *„Nach den gemessenen Beitraegen steht
AVAX heute auf Platz 26 von 36."* Damit dieser Satz etwas wert ist, muss
die Rangfolge selbst trennen - sonst ist sie eine schoene Zahl ohne
Belegkraft.

⚠️ **Diese Frage ist noch nie gestellt worden.** Funding und Turnover sind
EINZELN gemessen (+0,0246 R und +0,0616 R als Regel). Ob ihre SUMME mehr
leistet als der bessere von beiden, weiss niemand.

## ⚠️ DIE VORABFESTLEGUNG — vor der ersten Zahl

    Groesse       Summe der Beitragspunkte, genau wie im Betrieb:
                  `wahrscheinlichkeit.BEITRAEGE`, Stufen je Fuenftel
    Form          Querschnitt mit TAGESKLAMMER - die Raenge sind
                  Querschnitte, also muss es die Summe auch sein
    Zielgroesse   Ertrag in R ueber H20, Median je Tag
    Richtung      hohe Summe = gut  ->  die Regel sperrt das UNTERSTE
                  Fuenftel. Die Gegenrichtung wird NICHT gemessen.
    Zellen        EINE, vorab benannt (Methodik 2.49)

### Die Bedingung, an der es scheitern kann

> **Die Summe muss mindestens so gut trennen wie der BESTE Einzelbeitrag
> auf derselben Ankermenge.** Tut sie es nicht, ist eine Rangfolge ueber
> die Summe schlechter als eine ueber den einzelnen Beitrag - und der
> Satz in der Mail waere irrefuehrend.

⚠️ Gemessen wird auf der GEMEINSAMEN Menge: Turnover gibt es nur fuer 66
Symbole. Wer die Summe auf 578 und den Einzelbeitrag auf 66 misst,
vergleicht zwei verschiedene Maerkte (Pruefliste 2.80, Frage 2).

## Und die Monotonie, weil die Mail Fuenftel nennt

Die geplante Mailzeile sagt „im unteren Mittelfeld" - das behauptet eine
**Reihenfolge**. Wenn das dritte Fuenftel besser laeuft als das erste, ist
diese Sprache falsch. Deshalb wird zusaetzlich die Monotonie geprueft,
mit Band je Fuenftel.

    python messe_beitragssumme.py [--selbsttest]
"""
import argparse
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F
import messe_regel_wirksamkeit as W

HORIZONT = 20
MIND_JE_TAG = 15
BLOCK = max(90, HORIZONT * 3)


def _stufen():
    """Die Beitragstabellen aus dem Betrieb - keine zweite Quelle."""
    from agent import wahrscheinlichkeit as WK
    aus = {}
    for b in WK.BEITRAEGE:
        if getattr(b, "zustand", "") == "traegt" and getattr(b, "stufen", None):
            aus[b.merkmal] = tuple(float(x) for x in b.stufen)
    return aus


def baue(reihen, funding, menge, horizont=HORIZONT):
    """Anker mit Funding-Fuenftel, Turnover-Fuenftel und ihrer Summe.

    ⚠️ DIE FUENFTEL ENTSTEHEN JE KALENDERTAG - genau wie `marktrang`. Wer
    sie ueber die ganze Historie bildet, misst die Marktlage mit.
    """
    stufen = _stufen()
    roh = {}
    for sym, r in reihen.items():
        tage = [z[0] for z in r]
        c = np.array([z[1] for z in r])
        h = np.array([z[2] for z in r])
        t_ = np.array([z[3] for z in r])
        v = np.array([z[4] for z in r])
        br = B.spanne(h, t_, c, B.SCHWANKUNG)
        f = funding.get(sym.upper()) or {}
        m = menge.get(sym.upper()) or {}
        for i in range(60, len(c) - horizont):
            if not np.isfinite(br[i]) or br[i] <= 0:
                continue
            fw = f.get(tage[i])
            mw = m.get(tage[i])
            tw = (float(v[i]) / float(mw)) if (mw and mw > 0 and v[i]) else None
            if fw is None and tw is None:
                continue
            roh.setdefault(tage[i], []).append(
                {"sym": sym, "f": fw, "t": tw,
                 "in_r": float((c[i + horizont] - c[i]) / br[i])})
    # je Tag die Fuenftel und die Summe
    aus = {}
    for tag, z in roh.items():
        mit_f = [x for x in z if x["f"] is not None]
        mit_t = [x for x in z if x["t"] is not None]
        if len(mit_f) < MIND_JE_TAG or len(mit_t) < MIND_JE_TAG:
            continue
        for schluessel, teil, tab in (("ff", mit_f, stufen.get("funding_fuenftel")),
                                      ("tf", mit_t, stufen.get("turnover_fuenftel"))):
            if not tab:
                continue
            w = [x["f"] if schluessel == "ff" else x["t"] for x in teil]
            r = W.rang(w)
            for x, rr in zip(teil, r):
                x[schluessel] = min(int(rr * 5), 4)
                x[schluessel + "_p"] = tab[x[schluessel]]
        # ⚠️ NUR ANKER MIT BEIDEN - sonst haette die "Summe" bei manchen
        # nur einen Summanden, und der Vergleich waere keiner.
        beide = [x for x in z if "ff_p" in x and "tf_p" in x]
        if len(beide) < MIND_JE_TAG:
            continue
        for x in beide:
            x["summe"] = x["ff_p"] + x["tf_p"]
        aus[tag] = beide
    return aus


def _als(je_tag, feld):
    """Dieselben Anker, andere Kennzahl - fuer den fairen Vergleich."""
    return {t: [{"sym": x["sym"], "kennzahl": float(x[feld]),
                 "in_r": x["in_r"]} for x in z] for t, z in je_tag.items()}


def selbsttest():
    """⚠️ Die Kontrolle ist der erste Verdaechtige - erst Kunstdaten."""
    print("=" * 80)
    print("SELBSTTEST — zwei Welten mit bekannter Antwort")
    print("=" * 80)
    rng = np.random.default_rng(3)
    for name, staerke in (("Welt 1: die Summe traegt WIRKLICH", 0.40),
                          ("Welt 2: reines Rauschen", 0.0)):
        je_tag = {}
        for i in range(900):
            tag = "2024-%02d-%02d-%03d" % (1 + i % 12, 1 + i % 28, i)
            n = 40
            ff = rng.integers(0, 5, n)
            tf = rng.integers(0, 5, n)
            summe = ff + tf
            y = rng.normal(size=n) - staerke * (W.rang(summe) < 0.2)
            je_tag[tag] = [{"sym": "S%02d" % k, "kennzahl": float(summe[k]),
                            "in_r": float(y[k])} for k in range(n)]
        d = W.wirkung(je_tag, oben_sperren=False)[0]
        e = M.urteil_tage("  %-34s" % name, d, np.random.default_rng(1), 90)
        erwartet = staerke > 0
        print("     erwartet: %s -> %s"
              % ("TRAEGT" if erwartet else "still",
                 "✔" if bool(e and e["traegt"]) == erwartet else "✖ DURCHGEFALLEN"))
    print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selbsttest", action="store_true")
    a = p.parse_args()
    if a.selbsttest:
        selbsttest()
        return 0

    print("Lade ...", flush=True)
    reihen = B.lade()
    funding = F.lade_funding()
    menge = M.reihe("data/onchain_historie.db", "splycur")
    je_tag = baue(reihen, funding, menge)
    n = sum(len(z) for z in je_tag.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    print("Gemeinsame Menge: %d Anker · %d Symbole · %d Kalendertage"
          % (n, syms, len(je_tag)))
    if not je_tag:
        print("keine gemeinsamen Anker")
        return 1

    rng = np.random.default_rng(20260902)
    print()
    print("#" * 80)
    print("# KONTROLLE ZUERST — Funding allein, auf DIESER Menge")
    print("#" * 80)
    # ⚠️ `W.bericht` DRUCKT NUR - es gibt nichts zurueck (Zeile 102:
    # `return` ohne Wert). Meine erste Fassung las den Rueckgabewert und
    # verglich dann -9 gegen -9. Die Zahlen werden deshalb selbst
    # gerechnet, mit derselben Funktion, die `bericht` benutzt.
    def _messe(titel, feld, positiv=False):
        anker = _als(je_tag, feld)
        W.bericht(titel, anker, False, rng, mit_positivkontrolle=positiv)
        netto = M.urteil_tage("", W.wirkung(anker, False)[0],
                              np.random.default_rng(7), BLOCK)
        # ⚠️ UND DIE NEGATIVKONTROLLE GEHOERT ABGEZOGEN. Bei allen drei
        # Groessen ist sie positiv (+0,008 bis +0,010) - kein Zufall,
        # sondern die bekannte Verzerrung des Masses `Median(behalten) -
        # Median(alle)` bei SCHIEFEN Verteilungen und kleinem n je Tag
        # (F-171: bei n=20 rund +0,023, bei n=60 rund +0,004; hier sind
        # es 32). Wer gegen NULL liest, ueberschaetzt jede Groesse um
        # denselben Betrag - der Vergleich bleibt fair, die Hoehe nicht.
        # ⚠️⚠️ UEBER MEHRERE MISCHUNGEN MITTELN, nicht eine nehmen.
        #
        # Meine erste Fassung zog EINE Mischung je Groesse - und bekam
        # +0,0115 / +0,0069 / +0,0016 auf DERSELBEN Ankermenge. Waere das
        # die Massverzerrung, muesste sie bei allen drei gleich sein; sie
        # ist es nicht. Der Unterschied war reiner Zufall, und die
        # "bereinigten" Zahlen haetten je nach Saat ein anderes Urteil
        # ergeben.
        #
        # Dieselbe Lehre wie bei F-170: eine einzelne Mischung ist eine
        # Zufallszahl, kein Nullpunkt. Zehn davon sind einer.
        nullwerte = []
        for saat in range(10):
            e0 = M.urteil_tage("", W.wirkung(
                anker, False, mische=np.random.default_rng(500 + saat))[0],
                np.random.default_rng(7), BLOCK)
            if e0:
                nullwerte.append(e0["mittel"])
        null = {"mittel": float(np.mean(nullwerte))} if nullwerte else None
        streuung = float(np.std(nullwerte)) if nullwerte else float("nan")
        return {"netto": netto["mittel"] if netto else float("nan"),
                "null": null["mittel"] if null else float("nan"),
                "streuung": streuung, "reihe": W.wirkung(anker, False)[0],
                "traegt": bool(netto and netto["traegt"])}

    e_f = _messe("A  FUNDING allein", "ff_p")
    e_t = _messe("B  TURNOVER allein", "tf_p")
    e_s = _messe("C  DIE SUMME (N-15a)", "summe", positiv=True)

    # ---- der GEPAARTE Vergleich ---------------------------------------
    # ⚠️⚠️ ZWEI BAENDER ZU VERGLEICHEN IST DER FALSCHE TEST.
    #
    # Meine erste Fassung stellte die drei bereinigten Zahlen nebeneinander
    # und erklaerte die groesste zum Sieger. Die Baender dazu lauten
    # [+0,015 .. +0,050], [+0,021 .. +0,084], [+0,019 .. +0,079] - sie
    # ueberlappen fast vollstaendig. Bei einer Aufloesung von rund
    # ±0,03 R einen Unterschied von 0,003 R zu behaupten ist Rauschen,
    # gleich in welche Richtung es faellt.
    #
    # Der richtige Test ist GEPAART: beide Regeln laufen auf denselben
    # Ankern und denselben Kalendertagen. Die Differenz JE TAG kuerzt
    # alles Gemeinsame heraus - Marktphase, Volatilitaet, die
    # Massverzerrung selbst. Uebrig bleibt genau die Frage, die gestellt
    # war: traegt die Summe MEHR als der beste Einzelbeitrag?
    #
    # Und die Bereinigung entfaellt dabei: die Verzerrung wirkt auf beide
    # Reihen gleich und faellt in der Differenz heraus.
    bester = e_t if e_t["netto"] >= e_f["netto"] else e_f
    bname = "Turnover" if bester is e_t else "Funding"
    gemeinsam = sorted(set(e_s["reihe"]) & set(bester["reihe"]))
    diff = {tag: e_s["reihe"][tag] - bester["reihe"][tag]
            for tag in gemeinsam}
    print()
    print("=" * 80)
    print("C2 DER GEPAARTE VERGLEICH — Summe minus %s, je Kalendertag" % bname)
    print("=" * 80)
    print("  %d Tage in beiden Reihen" % len(diff))
    e_d = M.urteil_tage("  Summe - %s" % bname, diff,
                        np.random.default_rng(7), BLOCK)
    # ⚠️ POSITIVKONTROLLE FUER DEN GEPAARTEN TEST SELBST (2.93). Wenn die
    # Summe WIRKLICH um 0,02 R besser waere - wuerde dieser Test es finden?
    # Ohne diese Zeile ist ein "nicht unterscheidbar" nicht von "die
    # Anlage kann es nicht sehen" zu trennen, und genau das ist hier die
    # entscheidende Frage: der gesuchte Unterschied liegt bei 0,003 R.
    M.urteil_tage("  Positivkontrolle: +0,02 R aufgepraegt",
                  {k: v + 0.02 for k, v in diff.items()},
                  np.random.default_rng(7), BLOCK)
    M.urteil_tage("  Positivkontrolle: +0,01 R aufgepraegt",
                  {k: v + 0.01 for k, v in diff.items()},
                  np.random.default_rng(7), BLOCK)

    # ---- die Monotonie, weil die Mail Fuenftel nennt -------------------
    print()
    print("=" * 80)
    print("D  IST DIE REIHENFOLGE ECHT? — Ertrag je Fuenftel der Summe")
    print("=" * 80)
    proTag = {k: {} for k in range(5)}
    for tag, z in je_tag.items():
        s = np.array([x["summe"] for x in z], float)
        y = np.array([x["in_r"] for x in z], float)
        r = W.rang(s)
        med = []
        for k in range(5):
            m_ = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            med.append(float(np.median(y[m_])) if m_.sum() >= 2 else np.nan)
        if np.isnan(med).any():
            continue
        mm = float(np.mean(med))
        for k in range(5):
            proTag[k][tag] = med[k] - mm
    urteile, werte = [], []
    for k in range(5):
        e = M.urteil_tage("  Fuenftel %d (0 = niedrigste Summe)" % k,
                          proTag[k], rng, BLOCK)
        urteile.append(e)
        werte.append(e["mittel"] if e else float("nan"))
    steigend = all(werte[k] <= werte[k + 1] for k in range(4))
    print()
    print("  MONOTON steigend: %s" % ("JA" if steigend else "NEIN"))

    # ---- die vorab gesetzte Bedingung ---------------------------------
    print()
    print("=" * 80)
    print("DIE VORAB GESETZTE BEDINGUNG")
    print("=" * 80)
    print("  %-22s %10s %18s %12s"
          % ("", "NETTO", "Negativk. (10 Saaten)", "bereinigt"))
    for name, e in (("A Funding allein", e_f), ("B Turnover allein", e_t),
                    ("C die Summe", e_s)):
        print("  %-22s %+9.4f   %+8.4f ± %.4f %+11.4f R"
              % (name, e["netto"], e["null"], e["streuung"],
                 e["netto"] - e["null"]))
    print()
    print("  ⚠️ Die Streuung sagt, wie belastbar die Bereinigung ist. Liegt")
    print("     der Unterschied zwischen zwei Groessen INNERHALB davon, ist")
    print("     er nicht unterscheidbar.")
    best = max(e_f["netto"] - e_f["null"], e_t["netto"] - e_t["null"])
    summe = e_s["netto"] - e_s["null"]
    print()
    print("  bester Einzelbeitrag %+.4f R · Summe %+.4f R (beide bereinigt)"
          % (best, summe))
    print("  ⚠️ Dieser Nebeneinander-Vergleich entscheidet NICHTS - die drei")
    print("     Baender ueberlappen fast vollstaendig. Es zaehlt C2:")
    print()

    # ⚠️⚠️ DAS URTEIL HAENGT AM GEPAARTEN TEST, nicht am Groessenvergleich.
    if e_d and e_d["unten"] > 0:
        print("  -> ✔ DIE SUMME TRENNT NACHWEISLICH BESSER (%+.4f R "
              "[%+.4f .. %+.4f])" % (e_d["mittel"], e_d["unten"], e_d["oben"]))
        urteil = "besser"
    elif e_d and e_d["oben"] < 0:
        print("  -> ✖ DIE SUMME TRENNT NACHWEISLICH SCHLECHTER (%+.4f R "
              "[%+.4f .. %+.4f])" % (e_d["mittel"], e_d["unten"], e_d["oben"]))
        print("     Eine Rangfolge ueber die Summe waere schlechter als eine")
        print("     ueber den Turnover-Rang allein.")
        urteil = "schlechter"
    else:
        print("  -> ○ NICHT UNTERSCHEIDBAR%s"
              % ((" (%+.4f R [%+.4f .. %+.4f])"
                  % (e_d["mittel"], e_d["unten"], e_d["oben"])) if e_d else ""))
        print("     Die vorab gesetzte Bedingung ist damit weder erfuellt")
        print("     noch widerlegt: die Summe trennt nicht nachweislich")
        print("     besser als der beste Einzelbeitrag - aber auch nicht")
        print("     schlechter.")
        print("     ⚠️ Das ist KEIN Freibrief. Eine Rangfolge, die nicht")
        print("        besser trennt als eine einzelne Groesse, braucht eine")
        print("        andere Begruendung als 'sie ist genauer'.")
        urteil = "unentschieden"

    # ---- E: die PRODUKTIONSLAGE nachgestellt --------------------------
    # ⚠️⚠️ GEMESSEN WURDE AUF ANKERN MIT BEIDEN BEITRAEGEN (Zeile 119).
    # In der Produktion ist das die AUSNAHME: bei 37 von 44 Werten steht
    # die Bewertung auf einem einzigen Beitrag, weil der zweite keine
    # Messbasis hat.
    #
    # Und dann ist die Summe keine vergleichbare Groesse mehr. Ein Wert
    # mit Funding -0,54 und fehlendem Turnover hat Summe -0,54. Ein Wert
    # mit Funding -0,54 und Turnover +0,54 hat Summe 0,00 - und steht in
    # der Rangliste HOEHER, ohne besser zu sein. Die Summe belohnt das
    # Vorhandensein von Daten, nicht die Lage des Werts.
    #
    # Das ist die Umkehrung des Befunds vom 31.08. ("Mittelwert statt
    # Summe widerlegt"): dort benachteiligte der Mittelwert Werte mit
    # MEHR Beitraegen, hier bevorteilt die Summe Werte mit WENIGER.
    # Beide Male ist die Ursache dieselbe - eine Kennzahl, deren Skala
    # von der Datenlage abhaengt.
    #
    # Hier wird genau das nachgestellt: bei 84 % der Werte je Tag faellt
    # der Turnover-Beitrag weg, wie im Betrieb.
    print()
    print("=" * 80)
    print("E  DIE PRODUKTIONSLAGE - wenn bei 84 % der Werte ein Beitrag fehlt")
    print("=" * 80)

    def _lage(saat, still=True):
        """Die Fuenftel, wenn nur 16 % der Werte beide Beitraege haben."""
        luecke = np.random.default_rng(saat)
        proTagE = {k: {} for k in range(5)}
        for tag, z in je_tag.items():
            hat = luecke.random(len(z)) < 0.16
            s = np.array([x["ff_p"] + (x["tf_p"] if h else 0.0)
                          for x, h in zip(z, hat)], float)
            y = np.array([x["in_r"] for x in z], float)
            if len(s) < 10:
                continue
            r = W.rang(s)
            med = [float(np.median(y[(r >= k / 5) & (r < (k + 1) / 5 + 1e-9)]))
                   if ((r >= k / 5) & (r < (k + 1) / 5 + 1e-9)).sum() else np.nan
                   for k in range(5)]
            if any(np.isnan(med)):
                continue
            mm = float(np.mean(med))
            for k in range(5):
                proTagE[k][tag] = med[k] - mm
        # ⚠️ `urteil_tage` DRUCKT IMMER - bei fuenf Ziehungen waeren das
        # 25 Zeilen ohne Titel, die niemand zuordnen kann. Die stillen
        # Laeufe schreiben deshalb ins Leere.
        import contextlib
        import io as _io
        aus = []
        with (contextlib.nullcontext() if not still
              else contextlib.redirect_stdout(_io.StringIO())):
            for k in range(5):
                aus.append(M.urteil_tage(
                    "  Fuenftel %d (Produktionslage)" % k,
                    proTagE[k], rng, BLOCK))
        return aus

    # ⚠️⚠️ UEBER MEHRERE LUECKEN-SAATEN, nicht eine. Dieselbe Lehre wie
    # bei der Negativkontrolle oben: WELCHE Werte den zweiten Beitrag
    # verlieren, ist eine Zufallsziehung. Eine einzige davon ist keine
    # Aussage ueber die Produktionslage, sondern eine ueber diese Ziehung.
    #
    # Meine erste Fassung nahm Saat 23, sah eine monotone Reihe und haette
    # daraus fast "unter realer Datenlage ist die Ordnung sauberer"
    # geschlossen. Ob das stimmt, entscheidet sich erst hier.
    fest = _lage(23, still=False)
    monoton, obenauf = 0, 0
    for saat in (23, 101, 202, 303, 404):
        a = _lage(saat)
        w = [x["mittel"] if x else float("nan") for x in a]
        monoton += all(w[k] <= w[k + 1] for k in range(4))
        obenauf += bool(a[-1] and a[-1]["unten"] > 0)
    print()
    print("  ueber 5 Luecken-Ziehungen: %d/5 monoton · %d/5 oberstes "
          "Fuenftel traegt" % (monoton, obenauf))
    oben_e = obenauf >= 4
    stabil_e = monoton >= 4
    print("  -> das oberste Fuenftel traegt auch unter Datenluecke: %s"
          % ("JA" if oben_e else "NEIN"))
    print("  -> die Ordnung ist unter Datenluecke stabil monoton: %s"
          % ("JA" if stabil_e else "NEIN"))
    if stabil_e:
        print()
        print("  ⚠️⚠️ BEMERKENSWERT: mit BEIDEN Beitraegen ist die Reihe NICHT")
        print("     monoton, mit nur einem schon. Die Nicht-Monotonie kommt")
        print("     also aus der MISCHUNG - zwei Raenge auf verschiedenen")
        print("     Skalen addiert ergeben keine wohlgeordnete Groesse.")
        print("     Das spricht gegen die Summe als Rangfolge, nicht dafuer.")

    # ---- F: welche GROESSE ist wohlgeordnet? --------------------------
    # ⚠️ Block E stellt die Datenluecke nach - aber bei 84 % Luecke IST
    # die Groesse fast nur noch der Funding-Rang. Der Befund dort koennte
    # also zweierlei heissen: "die Luecke schadet nicht" oder "der
    # Funding-Rang allein ist besser geordnet als die Summe". Das ist
    # nicht dasselbe, und die Mail haengt an der Antwort.
    #
    # Hier wird es direkt gefragt: dieselben Anker, dieselbe Rechnung,
    # nur die Kennzahl wechselt.
    print()
    print("=" * 80)
    print("F  WELCHE GROESSE IST WOHLGEORDNET? - Fuenftel je Kennzahl")
    print("=" * 80)

    def _fuenftel(feld, titel):
        proT = {k: {} for k in range(5)}
        for tag, z in je_tag.items():
            s = np.array([x[feld] for x in z], float)
            y = np.array([x["in_r"] for x in z], float)
            if len(s) < 10:
                continue
            r = W.rang(s)
            med = [float(np.median(y[(r >= k / 5) & (r < (k + 1) / 5 + 1e-9)]))
                   if ((r >= k / 5) & (r < (k + 1) / 5 + 1e-9)).sum() else np.nan
                   for k in range(5)]
            if any(np.isnan(med)):
                continue
            mm = float(np.mean(med))
            for k in range(5):
                proT[k][tag] = med[k] - mm
        import contextlib
        import io as _io
        aus = []
        with contextlib.redirect_stdout(_io.StringIO()):
            for k in range(5):
                aus.append(M.urteil_tage("", proT[k], rng, BLOCK))
        w = [x["mittel"] if x else float("nan") for x in aus]
        mono = all(w[k] <= w[k + 1] for k in range(4))
        print("  %-22s %s   Spanne %+.4f   monoton: %s"
              % (titel, " ".join("%+.3f" % v for v in w),
                 w[-1] - w[0], "JA" if mono else "NEIN"))
        # ⚠️ DIE BAENDER GEHOEREN DAZU, sonst liest man eine Reihenfolge
        # aus Punktschaetzern ab. Monoton STEIGENDE Punkte heissen noch
        # nicht, dass die Stufen dazwischen unterscheidbar sind - und die
        # Mail nennt genau diese Stufen.
        print("  %-22s %s" % ("", " ".join(
            ("[%+.3f..%+.3f]" % (x["unten"], x["oben"])) if x else "   ?   "
            for x in aus)))
        trennbar = [k for k, x in enumerate(aus)
                    if x and (x["unten"] > 0 or x["oben"] < 0)]
        print("  %-22s trennbar: Fuenftel %s"
              % ("", ", ".join(str(k) for k in trennbar) or "keines"))
        return mono, w

    print("  %-22s %-35s %14s %s"
          % ("Kennzahl", "Fuenftel 0 .. 4", "Spanne", ""))
    m_f, w_f = _fuenftel("ff_p", "Funding allein")
    m_t, w_t = _fuenftel("tf_p", "Turnover allein")
    m_s, w_s = _fuenftel("summe", "die Summe")
    print()
    if m_f and not m_s:
        print("  ⚠️⚠️ DER EINZELBEITRAG IST GEORDNET, DIE SUMME NICHT.")
        print("     Damit ist die Frage von N-15a beantwortet - nicht ueber")
        print("     die Trennschaerfe (die ist gleich), sondern ueber die")
        print("     ORDNUNG. Eine Mailzeile, die einen Rang nennt, braucht")
        print("     eine wohlgeordnete Groesse. Die Summe ist keine.")

    print()
    print("=" * 80)
    print("WAS DAVON IN DIE MAIL DARF")
    print("=" * 80)
    if steigend:
        print("  ✔ Die Reihenfolge ist monoton - Fuenftel-Sprache ist gedeckt.")
        return 0
    print("  ✖ KEINE FEINE RANGFOLGE. Die Reihenfolge ist nicht monoton -")
    print("     'Platz 26 von 36, im unteren Mittelfeld' behauptet eine")
    print("     Ordnung, die in den Fuenfteln 0-3 nicht existiert.")
    print()
    print("  Was die Fuenftel HERGEBEN:")
    oben_ok = bool(urteile[-1] and urteile[-1]["unten"] > 0)
    unten_ok = bool(urteile[0] and urteile[0]["oben"] < 0)
    if oben_ok:
        print("     ✔ das OBERSTE Fuenftel traegt          %+.4f R"
              % urteile[-1]["mittel"])
    if unten_ok:
        print("     ✔ das UNTERSTE Fuenftel ist umgekehrt  %+.4f R"
              % urteile[0]["mittel"])
    mitte = [k for k in (1, 2, 3)
             if urteile[k] and urteile[k]["unten"] <= 0 <= urteile[k]["oben"]]
    print("     ○ nicht trennbar: Fuenftel %s"
          % (", ".join(str(k) for k in mitte) if mitte else "keines"))
    if oben_ok and unten_ok:
        print()
        print("  -> Gedeckt ist eine DREISTUFIGE Aussage:")
        print("     'im obersten Fuenftel' / 'im untersten Fuenftel' /")
        print("     'dazwischen - nicht unterscheidbar'.")
        print("     ⚠️ Das dritte Wort ist die ehrliche Form. Wer die Mitte")
        print("        weiter aufteilt, erfindet eine Ordnung.")
    return 0 if urteil != "schlechter" else 1


if __name__ == "__main__":
    sys.exit(main())
