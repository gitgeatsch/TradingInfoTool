# -*- coding: utf-8 -*-
"""DIE EHRENRUNDE zu `messe_stopweite_historisch.py`.

⚠️ Nutzerauftrag 13.09.2026: *„mach noch eine ehrenrunde zur Gegenpruefung
damit wir spaeter das Thema nicht mehr aufmachen muessen."*

Sieben Gegenproben. Jede fragt: **haengt das Ergebnis an einer Annahme,
die ich frei gewaehlt habe?** Wenn ja, ist es keine Messung, sondern eine
Einstellung.

    1 AUFLOESUNG       Die Leiter beginnt bei 0,02 R und meldet "ab 0,02".
                       Das ist ein BODEN, keine Messung - die echte
                       Aufloesung kann darunter liegen. Feinere Leiter.
    2 AUFLOESUNGSQUOTE Wie viele Anker treffen Stop oder Ziel, wie viele
                       enden in Mark-to-Market? Bei weiten Stops laeuft
                       fast alles bis zum Horizont - das muss man wissen,
                       um die Zahl zu lesen.
    3 GLEICHTAGSREGEL  Stop-vor-Ziel ist eine ANNAHME. Umgedreht rechnen.
                       Kippt ein Urteil, haengt es an der Annahme.
    4 SAAT UND ANKER   Andere Saat, halbe Ankerzahl. Wandern die Zahlen,
                       war es Ziehungsrauschen.
    5 BEZUGSPUNKT      8 % ist der Betriebspunkt, nicht die Wahrheit.
                       Gegen 5 % und 12 % nachrechnen - plus die
                       Additivitaetsprobe, die die Paarung selbst prueft.
    6 ZEITFENSTER      ⚠️ Stehender Befund: *ab 2023 traegt, davor nicht*.
                       Die Anker liegen ueber die ganze Historie. Haelt
                       das Bild im Fenster, das im Betrieb gilt?
    7 R-R11            Reproduktionspflicht. Befund 2.431 sagte
                       "ueber 12 % traegt" auf der SIGNALstichprobe. Die
                       historische Messung darf ihn nur umstossen, wenn
                       sie ihn zuerst REPRODUZIERT - also auf denselben
                       Symbolen nachrechnet.

AUFRUF:
    python pruefe_stopweite_gegen.py
    python pruefe_stopweite_gegen.py --schnell    # 120 Symbole
"""
from __future__ import annotations

import argparse
import io
import json
import statistics
import sys

import messe_eigenschaft_beitrag as B
import messe_stopweite_historisch as M

HZ = 10          # der mittlere Horizont - die anderen zwei stehen im Hauptlauf
FEIN = (0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40)


def _ew(paar_w: dict) -> float:
    return statistics.fmean([x for v in paar_w.values() for x in v])


def _zeile(name: str, paar: dict, bezug=M.BEZUG) -> dict:
    """Eine Ergebniszeile: je Weite die gepaarte Differenz mit Bandzeichen."""
    aus = {}
    print("  %-30s" % name, end="")
    for w in M.WEITEN:
        if abs(w - bezug) < 1e-12:
            continue
        lo, hi = M._block_bootstrap(paar[w])
        d = _ew(paar[w])
        aus[w] = (d, lo, hi)
        zeichen = "+" if lo > 0 else ("-" if hi < 0 else "o")
        print(" %+6.3f%s" % (d, zeichen), end="")
    print()
    return aus


def _kopf(bezug=M.BEZUG) -> None:
    print("  %-30s" % "", end="")
    for w in M.WEITEN:
        if abs(w - bezug) < 1e-12:
            continue
        print(" %6.0f %%" % (100 * w), end="")
    print()
    print("  " + "-" * 30 + "-" * (8 * (len(M.WEITEN) - 1)))


def probe1_aufloesung(reihen, syms, anker) -> None:
    print()
    print("1  AUFLOESUNG - wie klein ist der kleinste Effekt, den die Anlage FINDET?")
    print("=" * 96)
    print("   Die Hauptmessung meldet ueberall 'ab 0,02 R'. 0,02 ist die unterste")
    print("   Sprosse der Leiter - also ein BODEN, keine Messung. Feiner nachgesehen:")
    _r, paar, _n, _q = M.sammle(reihen, syms, anker, HZ, False)
    print()
    print("   %-10s %14s   %s" % ("Weite", "Aufloesung", "gemessener Effekt"))
    print("   " + "-" * 62)
    for w in M.WEITEN:
        if abs(w - M.BEZUG) < 1e-12:
            continue
        gefunden = None
        for st in FEIN:
            lo, _hi = M._block_bootstrap(M._zentriert(paar[w], st))
            if lo == lo and lo > 0.0:
                gefunden = st
                break
        d = _ew(paar[w])
        print("   %8.0f %% %14s   %+.3f R   %s"
              % (100 * w, ("%.3f R" % gefunden) if gefunden else "> 0,40 R", d,
                 "Effekt UEBER der Aufloesung"
                 if gefunden and abs(d) > gefunden else "unter der Aufloesung"))


def probe2_quote(reihen, syms, anker) -> None:
    print()
    print("2  AUFLOESUNGSQUOTE - was wird ueberhaupt entschieden?")
    print("=" * 96)
    print("   ⚠️ Kein Aufloesungsfilter ist RICHTIG (sonst faellt der weite Stop")
    print("   aus der Stichprobe). Aber man muss wissen, wovon die Zahl kommt.")
    for short in (False, True):
        _r, _p, n, quote = M.sammle(reihen, syms, anker, HZ, short)
        print()
        print("   %-6s (%d Anker)   %s"
              % ("SHORT" if short else "LONG", n,
                 "  ".join("%.0f %%: %2.0f %%"
                           % (100 * w, 100 * quote[w][0] / max(quote[w][1], 1))
                           for w in M.WEITEN)))
    print()
    print("   Lesart: bei 2 % entscheidet fast jeder Anker an Stop oder Ziel,")
    print("   bei 20 % laeuft der Grossteil bis zum Horizont und wird zum")
    print("   Marktwert bewertet. Beides ist in R gerechnet und damit direkt")
    print("   vergleichbar - eine weit gestoppte Position ist pro R groesser,")
    print("   dieselbe Kursbewegung ist dort also WENIGER R. Das ist die")
    print("   richtige Waehrung, weil der Einsatz mit 1/Weite skaliert")
    print("   (genau die Hebelkette: hebel = risiko / (einsatz x stop_rel)).")


def probe3_gleichtag(reihen, syms, anker) -> None:
    print()
    print("3  GLEICHTAGSREGEL - haengt das Urteil an 'Stop vor Ziel'?")
    print("=" * 96)
    for short in (False, True):
        print("   %s" % ("SHORT" if short else "LONG"))
        _kopf()
        for name, sz in (("Stop zuerst (Betrieb)", True),
                         ("Ziel zuerst (guenstig)", False)):
            _r, paar, _n, _q = M.sammle(reihen, syms, anker, HZ, short,
                                        stop_zuerst=sz)
            _zeile("  " + name, paar)
    print("   + Band ueber null · - Band unter null · o Band schliesst null ein")


def probe4_saat(reihen, syms, anker) -> None:
    print()
    print("4  SAAT UND ANKERZAHL - Ziehungsrauschen oder Struktur?")
    print("=" * 96)
    _kopf()
    for name, saat, ak in (("Saat A, %d Anker" % anker, M.SAAT, anker),
                           ("Saat B, %d Anker" % anker, M.SAAT + 777, anker),
                           ("Saat C, %d Anker" % (anker // 2), M.SAAT + 4242,
                            anker // 2)):
        _r, paar, _n, _q = M.sammle(reihen, syms, ak, HZ, False, saat=saat)
        _zeile("  " + name, paar)


def probe5_bezug(reihen, syms, anker) -> None:
    print()
    print("5  BEZUGSPUNKT - 8 % ist der Betrieb, nicht die Wahrheit")
    print("=" * 96)
    ergeb = {}
    for bez in (0.05, 0.08, 0.12):
        _r, paar, _n, _q = M.sammle(reihen, syms, anker, HZ, False, bezug=bez)
        ergeb[bez] = paar
        print("   gegen %.0f %%:" % (100 * bez))
        _kopf(bezug=bez)
        _zeile("  gepaarte Differenz", paar, bezug=bez)
    print()
    print("   ADDITIVITAETSPROBE - prueft die PAARUNG selbst:")
    print("   d(w gegen 5 %) minus d(8 % gegen 5 %) muss EXAKT d(w gegen 8 %) sein.")
    ab = _ew(ergeb[0.05][0.08])
    schlimm = 0.0
    for w in M.WEITEN:
        if abs(w - 0.08) < 1e-12 or abs(w - 0.05) < 1e-12:
            continue
        links = _ew(ergeb[0.05][w]) - ab
        rechts = _ew(ergeb[0.08][w])
        schlimm = max(schlimm, abs(links - rechts))
        print("     %5.0f %%   %+.9f  gegen  %+.9f   Abweichung %.2e"
              % (100 * w, links, rechts, abs(links - rechts)))
    print("   groesste Abweichung %.2e   %s"
          % (schlimm, "OK" if schlimm < 1e-9 else "✖ die Paarung stimmt nicht"))


def probe6_zeitfenster(reihen, syms, anker) -> None:
    print()
    print("6  ZEITFENSTER - haelt das Bild dort, wo der Betrieb laeuft?")
    print("=" * 96)
    print("   ⚠️ Stehender Befund: ab 2023 traegt, davor nicht (+8,64 gegen +2,77).")
    print("   Die Anker der Hauptmessung liegen ueber die GANZE Historie.")
    for short in (False, True):
        print("   %s" % ("SHORT" if short else "LONG"))
        _kopf()
        for name, ab in (("ganze Historie", None),
                         ("nur ab 2023-01-01", "2023-01-01"),
                         ("nur ab 2025-01-01", "2025-01-01")):
            _r, paar, n, _q = M.sammle(reihen, syms, anker, HZ, short, ab=ab)
            _zeile("  %-20s %6d" % (name, n), paar)


def probe7_rr11(reihen, syms, anker) -> None:
    print()
    print("7  R-R11 REPRODUKTIONSPFLICHT - Befund 2.431 zuerst nachrechnen")
    print("=" * 96)
    print("   2.431 sagte auf der SIGNALstichprobe: 'ueber 12 % traegt', +0,230 R.")
    print("   Ein Befund darf nur von einer Messung umgestossen werden, die ihn")
    print("   zuerst REPRODUZIERT. Also: dieselben Symbole, historisch gerechnet.")
    try:
        # ⚠️ Die Symbolmengen kommen aus dem ECHTEN Werkzeug (`zonen`,
        # `band_von`), nicht aus einer nachgebauten Bandgrenze.
        import messe_stop_abstand_baender as S
        d = json.load(io.open(S.STANDARD_PFAD, encoding="utf-8"))
        breit, alle_sig = set(), set()
        for r in d.get("hebel_signals", []):
            z = S.zonen(r)
            if not z or not r.get("symbol"):
                continue
            alle_sig.add(r["symbol"])
            b = S.band_von(z["stop_rel"] * 100.0)
            if b and b[0] >= 12.0:
                breit.add(r["symbol"])
    except Exception as e:
        print("   ⚠️ Signalexport nicht lesbar (%s) - Probe 7 entfaellt" % e)
        return
    inband = [s for s in syms if s in breit]
    insig = [s for s in syms if s in alle_sig]
    print("   %d Signalsymbole gesamt, davon %d im Band >12 %%."
          % (len(alle_sig), len(breit)))
    print("   Mit langer Reihe in der Messmenge: %d bzw. %d."
          % (len(insig), len(inband)))
    if len(inband) < 5:
        print("   ⚠️ zu wenige - Probe 7 entfaellt")
        return
    print()
    _kopf()
    for name, menge in (("Symbole des Bandes >12 %", inband),
                        ("alle Signalsymbole", insig),
                        ("die volle Messmenge", syms)):
        _r, paar, _n, _q = M.sammle(reihen, menge, anker, HZ, False)
        _zeile("  %-24s %3d Sym" % (name, len(menge)), paar)
    print()
    print("   ⚠️ ENTSCHEIDEND: reproduziert 'ueber 12 % traegt' auf den")
    print("   Signalsymbolen? Steht dort kein +, war der Wert von 2.431 die")
    print("   AUSWAHL der Signale und nicht die Stopweite - dann ist der")
    print("   Befund widerlegt, und zwar regelkonform.")


FEINRASTER = (0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.12)


def probe8_feinraster(reihen, syms, anker) -> None:
    """⚠️ DIE FRAGE, AN DER DIE ENTSCHEIDUNG HAENGT.

    Das Hauptraster springt 5 - 8 - 12 %. Dass 8 % beide Nachbarn
    schlaegt, heisst nur: es ist der beste von SECHS. Ob es der GIPFEL
    ist, sagt erst ein feines Raster darum herum. Genau daran haengt, ob
    `stop_ziel_atr` bewegt werden muss oder nicht."""
    print()
    print("8  FEINRASTER UM DEN BETRIEBSPUNKT - ist 8 % der Gipfel?")
    print("=" * 96)
    print("   Das Hauptraster springt 5 - 8 - 12 %. Der beste von sechs ist")
    print("   noch kein Optimum. Hier in Ein-Prozent-Schritten, gepaart gegen 8 %.")
    for short in (False, True):
        _r, paar, n, _q = M.sammle(reihen, syms, anker, HZ, short,
                                   weiten=FEINRASTER)
        print()
        print("   %-6s (%d Anker)" % ("SHORT" if short else "LONG", n))
        print("   %-10s %10s %22s   %s"
              % ("Weite", "gepaart", "Band", "Urteil gegen 8 %"))
        print("   " + "-" * 70)
        for w in FEINRASTER:
            if abs(w - M.BEZUG) < 1e-12:
                print("   %8.0f %% %10s %22s   %s"
                      % (100 * w, "-", "(Bezugspunkt)", "der heutige Betrieb"))
                continue
            lo, hi = M._block_bootstrap(paar[w])
            d = _ew(paar[w])
            u = ("BESSER als 8 %" if lo > 0 else
                 ("schlechter als 8 %" if hi < 0 else "nicht trennbar von 8 %"))
            print("   %8.0f %% %+10.4f   [%+7.4f;%+7.4f]   %s"
                  % (100 * w, d, lo, hi, u))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--schnell", action="store_true")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    reihen = B.lade()
    syms = M.symbolliste(reihen, 120 if a.schnell else 10000)
    anker = 30 if a.schnell else 60

    print("=" * 96)
    print("EHRENRUNDE - GEGENPRUEFUNG DER STOPWEITENMESSUNG")
    print("=" * 96)
    print("Grundlage: %d Symbole, %d Anker je Symbol, Horizont %d, CRV %.1f"
          % (len(syms), anker, HZ, M.CRV))
    print("⚠️ Jede Probe ruft `messe_stopweite_historisch.sammle()` auf -")
    print("   den ECHTEN Code, keine Nachbildung.")

    probe1_aufloesung(reihen, syms, anker)
    probe2_quote(reihen, syms, anker)
    probe3_gleichtag(reihen, syms, anker)
    probe4_saat(reihen, syms, anker)
    probe5_bezug(reihen, syms, anker)
    probe6_zeitfenster(reihen, syms, anker)
    probe7_rr11(reihen, syms, anker)
    probe8_feinraster(reihen, syms, anker)


if __name__ == "__main__":
    main()
