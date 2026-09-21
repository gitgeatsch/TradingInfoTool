# -*- coding: utf-8 -*-
"""⚠️⚠️ VORABFESTLEGUNG — geschrieben VOR dem Lauf (21.09.2026).

Nutzerauftrag: *„erstelle zuerst eine Hypothese die für diesen Beitrag
gelten soll - als Experte - dann müssen wir sauber Messen ... achtung
Falle."* — und die Nachfrage, die den Aufbau gedreht hat: *„ist der Wert
tatsächlich Handelsvolumen je Umlaufmenge? Dann lag ich falsch mit
statisch und wir reden von unterschiedlichen Hypothesen und auch
Indikatoren."*

═══════════════════════════════════════════════════════════════════════
 AM CODE GEPRUEFT, NICHT AM REGISTERBLATT
═══════════════════════════════════════════════════════════════════════

    Messung  messe_kandidaten_als_regel:262   v[i] / menge
    Betrieb  agent/marktrang:774              volumen / menge[basis]

Ja - buchstaeblich Stueckvolumen je Umlaufmenge, an beiden Stellen
dieselbe Rechnung (das war der Zweck von Schritt 49).

═══════════════════════════════════════════════════════════════════════
 DER WIDERSPRUCH, DEN DAS AUFDECKT
═══════════════════════════════════════════════════════════════════════

    log turnover(t) = log Volumen(t) - log Menge(t)
                      ^^^^^^^^^^^^^^   ^^^^^^^^^^^^
                      Streuung 0,8312  Streuung 0,0212      (39 : 1)

Der Nenner ist je Asset praktisch eine KONSTANTE. `turnover` ist damit
ein **Volumenmass mit einem Asset-Festwert** - und sein
Querschnittsrang kodiert zu einem erheblichen Teil, WELCHES Asset es
ist, nicht in welchem ZUSTAND es ist.

⚠️ Die registrierte Hypothese lautet aber *„viel AUFMERKSAMKEIT heisst
eher ueberbewertet"*. Aufmerksamkeit ist ein ZUSTAND. Wenn der Rang
ueberwiegend eine Asset-Eigenschaft traegt, misst der Beitrag etwas
anderes, als sein Registerblatt behauptet.

⚠️⚠️ Und das beruehrt REGEL 3 des uebergeordneten Ziels: *„beim HEBEL
kein Asset-Rang - der Hebel kommt aus der Wahrscheinlichkeit DIESES
Trades."* ⚠️ Regel 3 verbietet den Querschnittsvergleich NICHT (F-227);
sie verbietet, den HEBEL aus einer Assetrangliste zu erzeugen. Ob
`turnover` naeher am einen oder am anderen liegt, ist genau die Frage.

═══════════════════════════════════════════════════════════════════════
 DIE HYPOTHESEN - jetzt DREI, nicht eine
═══════════════════════════════════════════════════════════════════════

Die Zerlegung ist exakt und ohne Lookahead. Mit `m_i(t)` = Mittel der
VORANGEGANGENEN `RUECKBLICK` Tage des eigenen log-turnover:

    log turnover_i(t)  =  m_i(t)            +  ( log turnover_i(t) - m_i(t) )
                          ^^^^^^^^             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                          ASSET (EIGENSCHAFT)   LAGE (ZUSTAND)

**H-A (Asset):** Der Rang des NIVEAUS traegt - dauerhaft klein-und-viel-
gehandelt zu sein ist die Information. Das waere eine EIGENSCHAFT.
⚠️ Traegt nur diese, ist der Beitrag ein Asset-Rang, und Regel 3 ist fuer
den Hebel zu pruefen.

**H-L (Lage):** Der Rang der ABWEICHUNG vom eigenen Schnitt traegt -
heute ungewoehnlich viel gehandelt zu werden ist die Information. Das
waere ein ZUSTAND und deckt sich mit der registrierten Formulierung
„Aufmerksamkeit".
⚠️ Das ist dieselbe Form wie `schnitt` (Abstand zum eigenen 200-Tage-
Schnitt), die im Haus bereits registriert ist.

**H-G (Gesamt):** `turnover` in der heutigen Form - die Summe beider.
Sie laeuft als KONTROLLE mit: die Zerlegung muss sie einfangen.

⚠️ EIN VIERTER ARM, DER DIE FALLE UMGEHT. Der Nutzer fragte nach
Verwaesserung. *„Ist Verwaesserung schlecht fuer den Kurs"* waere eine
MARKTfrage und damit der falsche Messgegenstand
(`wir-messen-unsere-qualitaet-nicht-den-markt`). Umgestellt:

**H-M (Mengenaenderung):** Die Emissionsdynamik als EIGENER Kandidat in
UNSERER Anlage. Traegt sie dort? Das ist eine Systemfrage; die
Marktaussage faellt als Nebenprodukt ab, ohne Gegenstand zu sein.

═══════════════════════════════════════════════════════════════════════
 VORABFESTLEGUNG - was welches Ergebnis BEDEUTET
═══════════════════════════════════════════════════════════════════════

| Ergebnis | Deutung | Folge |
|---|---|---|
| nur **H-L** traegt | der Beitrag ist ein ZUSTAND, wie sein Blatt sagt | Form auf die Abweichung umstellen - sauberer und Regel-3-fest |
| nur **H-A** traegt | der Beitrag ist eine ASSET-EIGENSCHAFT | Regel 3 fuer den HEBEL pruefen; in der MAIL bleibt er erwuenscht |
| **beide** tragen | zwei Groessen in einem Namen | TRENNEN - zwei Kandidaten, zwei Tabellen |
| **keiner**, aber H-G traegt | die Zerlegung zerstoert etwas | Zerlegung ist falsch gestellt, nicht der Beitrag |
| **H-M** traegt eigenstaendig | Verwaesserung ist ein eigener Beitrag | eigener Kandidat, NICHT in `turnover` mischen |

⚠️ **Was NICHT als Ergebnis zaehlt:** eine Einzelzelle. Geurteilt wird
nach der FORM ueber H2/H3/H5 (2.208-n86). Und ein Unterschied zwischen
zwei Armen ist erst einer, wenn sich die BAENDER trennen - zwei
Nullbefunde mit verschiedenem Vorzeichen sind kein Unterschied.

⚠️ **Wirksamkeit, nicht Merkmal:** geurteilt wird ueber die REGEL unter
der Tagesklammer (`pruefe_auswahl`), nicht ueber die Merkmalsspanne. Bei
`funding` lagen dazwischen Faktor 5,5.

⚠️ **R-R11:** Basis ist H2..H5 auf 365 Tagen und dem FREIEN UMLAUF. Die
Registrierung steht auf H20, 2.636 Tagen und der GESAMTAUSGABE. Diese
Messung kann die registrierte Tabelle WEDER bestaetigen NOCH umstossen.
Sie beantwortet eine Formfrage, keine Betragsfrage.

⚠️ **Menge** nach Datenlage je Arm (F-212), auf Wunsch fest - ein Urteil
auf einem Parameterwert ist keins.

    python phase4_c_hypothese_turnover.py
    python phase4_c_hypothese_turnover.py --feste-menge 20% --rueckblick 60
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

import agent.marktrang as MR                               # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402
import messmenge                                            # noqa: E402
import messnorm as N                                        # noqa: E402
import messnorm_auswahl as MA                              # noqa: E402
import phase3_stufen as ST                                  # noqa: E402
import phase4_c_kalibrierung_freefloat as C                # noqa: E402
from messe_beitrag_auf_auswahl import momentum250          # noqa: E402

SAAT = 20260921
RUECKBLICK = 60          # Tage fuer den eigenen Schnitt


def _arg(args, flagge, vorgabe):
    return args[args.index(flagge) + 1] if flagge in args else vorgabe


def reihen_umschlag(neu: dict, datei: str):
    """log(Volumen/Menge) je Symbol und Tag - die Ausgangsgroesse."""
    import sqlite3
    ab = min(t for d in neu.values() for t in d)
    m = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    aus = {}
    for sym, tag, v in m.execute(
            "SELECT symbol, date, volume FROM price_history_ohlc "
            " WHERE date >= ? AND volume > 0", (ab,)):
        s = sym.upper()
        d = neu.get(s)
        if not d:
            continue
        t = str(tag)[:10]
        q = d.get(t)
        if q and q > 0:
            aus.setdefault(s, {})[t] = math.log(v / q)
    m.close()
    return aus, ab


def zerlege(log_u: dict, rueckblick: int):
    """ASSET = nachlaufender Schnitt · LAGE = Abstand dazu. Kein Lookahead.

    ⚠️ Der Schnitt ist NACHLAUFEND und schliesst den heutigen Tag AUS.
    Ein Fenster, das den aktuellen Wert enthaelt, haette den Abstand
    systematisch geschrumpft und die Lage kuenstlich klein gemacht.
    """
    asset, lage = {}, {}
    for s, d in log_u.items():
        t = sorted(d)
        if len(t) < rueckblick + 30:
            continue
        for i in range(rueckblick, len(t)):
            frueher = [d[t[j]] for j in range(i - rueckblick, i)]
            m = st.mean(frueher)
            asset.setdefault(s, {})[t[i]] = m
            lage.setdefault(s, {})[t[i]] = d[t[i]] - m
    return asset, lage


def wachstum(neu: dict, rueckblick: int):
    """Emissionsdynamik: relative Mengenaenderung ueber `rueckblick` Tage."""
    aus = {}
    for s, d in neu.items():
        t = sorted(d)
        if len(t) < rueckblick + 30:
            continue
        for i in range(rueckblick, len(t)):
            a = d[t[i - rueckblick]]
            if a > 0:
                aus.setdefault(s, {})[t[i]] = (d[t[i]] - a) / a
    return aus


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    horizonte = tuple(int(x) for x in
                      _arg(args, "--horizonte", "2,3,5").split(","))
    fest = _arg(args, "--feste-menge", "")
    rueck = int(_arg(args, "--rueckblick", str(RUECKBLICK)))
    saat = int(_arg(args, "--saat", str(SAAT)))

    print("=" * 112)
    print("ASSET ODER LAGE? - was traegt an `turnover` wirklich")
    print("=" * 112)
    print("  " + N.standardzeile())
    print("  " + messmenge.zeile())
    neu, weg, ges = C.menge_neu(C.MENGE_DB, True)
    datei, _sql = MR.MESSBASIS["schnitt"]
    log_u, ab = reihen_umschlag(neu, datei)
    asset, lage = zerlege(log_u, rueck)
    wa = wachstum(neu, rueck)
    print()
    print("  Fenster ab %s · Rueckblick %d Tage · Tagesartefakte "
          "ausgeworfen %d von %d" % (ab, rueck, weg, ges))
    print("  Symbole: log-Umschlag %d · ASSET %d · LAGE %d · WACHSTUM %d"
          % (len(log_u), len(asset), len(lage), len(wa)))
    zellen = len(horizonte) * 4
    print("  ⚠️ %d Zellen - familienweiter Fehlalarm rund %.0f %%. "
          "Geurteilt wird nach FORM"
          % (zellen, 100 * ST.familienfehler(zellen)))
    print("     ueber H2/H3/H5, nicht nach einer Einzelzelle "
          "(2.208-n86).")
    print("  ⚠️ R-R11: H2..H5, 365 Tage, FREIER Umlauf. Die "
          "Registrierung steht auf H20,")
    print("     2.636 Tagen und der GESAMTAUSGABE - weder Bestaetigung "
          "noch Widerlegung.")
    print()

    reihen = B.lade()
    mom = momentum250(reihen)
    lg = N.Lage(instrument="spot", strategie="einstieg")
    # ⚠️ `turnover_markt` nimmt einen FERTIGEN Wert je Tag entgegen -
    # genau die Form, die hier gebraucht wird. Kein bestehendes `art`
    # wird angefasst (Vorgehen wie F-210).
    arme = (("H-G gesamt", log_u), ("H-A asset", asset),
            ("H-L lage", lage), ("H-M wachstum", wa))
    print("  %-14s %3s %6s %6s %9s %20s %9s %7s  %s"
          % ("Arm", "H", "Syms", "Menge", "Wirkung", "Band", "Bezug",
             "Blöcke", "Urteil"))
    erg: dict = {}
    for H in horizonte:
        for name, quelle in arme:
            je = C.beschneiden(
                K.baue(reihen, "turnover_markt", quelle, horizont=H),
                None, ab)
            if not je:
                print("  %-14s %3d -> leere Welt" % (name, H))
                continue
            menge = fest or MA.menge_nach_datenlage(je, mom, horizont=H)
            if menge is None:
                print("  %-14s %3d -> KEINE Menge haelt Anker UND Bloecke"
                      % (name, H))
                continue
            try:
                b = MA.pruefe_auswahl(
                    name.split()[-1], je, mom, lage=lg, menge=menge,
                    rng=np.random.default_rng(saat), horizont=H,
                    hypothese="Zerlegung Asset gegen Lage",
                    verwendung="Beitrag", zielgroesse="bewegung_r")
            except Exception as exc:                       # noqa: BLE001
                print("  %-14s %3d -> %s" % (name, H, str(exc)[:62]))
                continue
            erg.setdefault(name, {})[H] = b
            print("  %-14s %3d %6d %6s %+9.4f [%+.4f..%+.4f] %+9.4f "
                  "%7d  %s"
                  % (name, H, b.abdeckung_symbole, menge, b.wirkung,
                     b.unten, b.oben, b.bezugswert, b.n_bloecke,
                     C.kurz(b.urteil)), flush=True)
        print()

    print("=" * 112)
    print("  AUSWERTUNG NACH DER VORABFESTLEGUNG IM SKRIPTKOPF")
    print("=" * 112)
    for name, _q in arme:
        je_h = erg.get(name, {})
        if not je_h:
            print("  %-14s keine auswertbare Zelle" % name)
            continue
        traegt = sorted(h for h, b in je_h.items() if b.traegt)
        print("  %-14s %s   traegt bei %s"
              % (name,
                 " ".join("H%d:%+.4f%s" % (h, je_h[h].wirkung,
                                           "*" if je_h[h].traegt else "")
                          for h in sorted(je_h)),
                 ("H" + ", H".join(str(h) for h in traegt)) if traegt
                 else "KEINEM"))
    # ⚠⚠ NACH DER FORM URTEILEN, NICHT NACH EINER ZELLE.
    # Die erste Fassung zaehlte "traegt bei mindestens einem Horizont"
    # und meldete dadurch "BEIDE TRAGEN" - waehrend die Vorabfestlegung
    # im Skriptkopf ausdruecklich FORM ueber H2/H3/H5 verlangt
    # (2.208-n86). Genau der Fehler, den die eigene Vorgabe verbietet.
    #
    # ⚠ Ausserdem wird der ABSTAND zum Nullpunkt ausgewiesen: ein
    # TRAEGT mit 0,0006 R Abstand ist nach 2.477-stabilitaet ein
    # Grenzfall und ohne Saatprobe kein Befund.
    def _form(je_h):
        # ⚠⚠ `b.traegt` IGNORIERT DIE BLOCKSPERRE. `messnorm.urteil`
        # prueft die Blockzahl VOR `traegt`; eine Zelle mit 19 Bloecken
        # meldet "KEIN BEFUND" und hat trotzdem `traegt=True`. Die erste
        # Fassung zaehlte sie mit und meldete "3 von 3" fuer einen Arm,
        # dessen dritte Zelle gar kein Urteil hat.
        n = len(je_h)
        ohne = [h for h, b in je_h.items()
                if b.urteil.startswith("KEIN BEFUND")]
        t = [h for h, b in je_h.items() if b.traegt and h not in ohne]
        return len(t), n, sorted(t), sorted(ohne)

    print()
    print("  FORM statt Einzelzelle - und der ABSTAND zum Nullpunkt:")
    print("  %-14s %10s %28s  %s"
          % ("Arm", "traegt", "kleinster Abstand", "Einordnung"))
    for name, _q in arme:
        je_h = erg.get(name, {})
        if not je_h:
            continue
        nt, n, t, ohne = _form(je_h)
        ab = min((je_h[h].unten - je_h[h].bezugswert) for h in t) if t             else None
        if nt == n and n >= 3:
            ein = "FORM - traegt ueber alle Horizonte"
        elif nt >= 2:
            ein = "Form ueber %d benachbarte Zellen" % nt
        elif nt == 1:
            ein = "⚠ EINZELZELLE - Hinweis, kein Befund"
        else:
            ein = "traegt nicht"
        if ab is not None and ab < 0.002:
            ein += " ⚠ Abstand unter 0,002 - Saatprobe noetig"
        if ohne:
            ein += " ⚠ KEIN BEFUND bei H%s (Bloecke)" % ",H".join(
                str(x) for x in ohne)
        print("  %-14s %4d von %-3d %28s  %s"
              % (name, nt, n, ("%+.4f" % ab) if ab is not None else "-",
                 ein))

    a, l = erg.get("H-A asset", {}), erg.get("H-L lage", {})
    beide = sorted(set(a) & set(l))
    if beide:
        ta = sum(1 for h in beide if a[h].traegt)
        tl = sum(1 for h in beide if l[h].traegt)
        print()
        if ta and not tl:
            print("  ➤ NUR DIE ASSET-EIGENSCHAFT TRAEGT (%d von %d "
                  "Horizonten)." % (ta, len(beide)))
            print("     ⚠️ Dann ist `turnover` im Kern ein ASSET-RANG - "
                  "und Regel 3 ist")
            print("        fuer den HEBEL zu pruefen. In der MAIL bleibt "
                  "er erwuenscht.")
        elif tl and not ta:
            print("  ➤ NUR DIE LAGE TRAEGT (%d von %d Horizonten)."
                  % (tl, len(beide)))
            print("     ⚠️ Dann deckt sich der Beitrag mit seinem "
                  "Registerblatt, und die")
            print("        heutige Form schleppt einen Asset-Festwert "
                  "mit, der nichts beitraegt.")
        elif ta and tl:
            print("  ➤ BEIDE TRAGEN - zwei Groessen in einem Namen. "
                  "TRENNEN, nicht mitteln.")
        else:
            print("  ➤ KEINER der beiden traegt einzeln. ⚠️ Traegt H-G, "
                  "zerstoert die")
            print("     Zerlegung etwas - dann ist sie falsch gestellt, "
                  "nicht der Beitrag.")
    print()
    print("  ⚠️ DIE FALLE: H-M fragt NICHT ,ist Verwaesserung schlecht "
          "fuer den Kurs`.")
    print("     Er fragt ,traegt diese Groesse in UNSERER Anlage` - "
          "Systemfrage. Die")
    print("     Marktaussage faellt ab, ist aber nicht der Gegenstand.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
