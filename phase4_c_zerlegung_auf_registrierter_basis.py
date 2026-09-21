# -*- coding: utf-8 -*-
"""⚠️⚠️ VORABFESTLEGUNG — geschrieben VOR dem Lauf (21.09.2026).

DIE EINSICHT, DIE DIESEN LAUF AUSLOEST: die Randlage (2.506-randlage) ist
eine Eigenschaft des FENSTERS, nicht der FRAGE. Ich habe sie den ganzen
Tag als Eigenschaft der Frage behandelt.

    Free Float    365 Tage  -> H20 braeuchte 1.200, Rueckblick kostet
                               das Urteil
    SplyCur       2.636 Tage -> H20 hat rund 44 Bloecke, ein Rueckblick
                               kostet nichts

Die Frage „EIGENSCHAFT oder ZUSTAND" laesst sich also auf der
REGISTRIERTEN Basis stellen - und dort ist sie sogar relevanter, weil
die laufende Tabelle genau dort steht.

═══════════════════════════════════════════════════════════════════════
 TEIL 1 - DIE REPRODUKTIONSPFLICHT (R-R11), ZUERST
═══════════════════════════════════════════════════════════════════════

Registerblatt `turnover`: Basis **H20, 2.636 Kalendertage**, Wert
**+0,0616 R [+0,0203 .. +0,1111]**. F-212 hat am 04.09. auf der
SELEKTIERTEN Menge nachgemessen: **+0,0635 R**.

⚠️ R-R11: *„Ein registrierter Befund darf nur von einer Messung
umgestossen werden, die ihn ZUERST reproduziert."* Bisher hat KEINE
Messung dieses Tages den registrierten Wert reproduziert - alle standen
auf neuer Basis. Diese hier holt das nach.

**Vorab festgelegt, was als Reproduktion gilt:** die Wirkung liegt
innerhalb des registrierten Bandes [+0,0203 .. +0,1111]. Liegt sie
darueber oder darunter, ist die Kette anders - und dann ist ALLES von
heute hinfaellig, nicht nur dieser Lauf.

═══════════════════════════════════════════════════════════════════════
 TEIL 2 - DIE ZERLEGUNG, DORT WO SIE ENTSCHEIDBAR IST
═══════════════════════════════════════════════════════════════════════

Dieselbe Zerlegung wie am Free Float, ohne Lookahead:

    log turnover(t) = m(t) + (log turnover(t) - m(t))
                      ASSET   LAGE

⚠️⚠️ EINE EINSCHRAENKUNG GEHOERT VORWEG, weil sie das Ergebnis
vorzeichnet: `SplyCur` ist fuer **24 von 42** Symbolen praktisch
statisch (Spanne unter 1 Prozent im Jahr, 2.506-zerlegung). Die LAGE ist
dort fast nur Volumenschwankung, die EIGENSCHAFT fast die ganze
Nennerinformation. Das ist ein ANDERER Zerlegungsfall als am freien
Umlauf - aber genau der, der fuer die laufende Tabelle gilt.

**Vorabfestlegung, was welches Ergebnis bedeutet:**

| Ergebnis | Deutung | Folge |
|---|---|---|
| nur LAGE traegt | die registrierte Tabelle steht auf einem ZUSTAND | Form umstellen ist eine Verbesserung, kein Bruch |
| nur EIGENSCHAFT traegt | sie steht auf einem ASSET-RANG | ⚠️ Regel-3-Frage fuer den Hebel wird scharf |
| beide | zwei Groessen in einem Namen, wie am freien Umlauf | trennen |
| keiner, aber GESAMT traegt | die Zerlegung zerstoert etwas | Zerlegung falsch gestellt |

⚠️ Geurteilt wird nach FORM ueber H5/H10/H20, nicht nach Einzelzellen -
bei den heutigen 78 Zellen liegt der familienweite Fehlalarm bei 86 %.

⚠️ Menge: **50 %** fest fuer alle Arme. Das ist die Menge, die
`menge_nach_datenlage` fuer `turnover` bei H20 waehlt (bei 20 % nur 10,1
Anker je Tag) - und eine feste Menge ist Pflicht, sobald Arme
verglichen werden.

⚠️ JEDE SEITE BEKOMMT IHRE ZUFALLSKONTROLLE. Ohne sie ist nicht zu
unterscheiden, ob ein Arm DURCH die Residualisierung faellt oder ohnehin
nicht traegt (2.507-kontrolle).

    python phase4_c_zerlegung_auf_registrierter_basis.py
    python phase4_c_zerlegung_auf_registrierter_basis.py --nur-repro
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
import agent.wahrscheinlichkeit as WA                      # noqa: E402
import messe_bewertungskennzahl as MB                      # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402
import messnorm as N                                       # noqa: E402
import messnorm_auswahl as MA                              # noqa: E402
import phase3_stufen as ST                                 # noqa: E402
import phase4_c_kalibrierung_freefloat as C                # noqa: E402
import phase4_c_zusatzbeitrag_normpfad as ZB               # noqa: E402
from messe_beitrag_auf_auswahl import momentum250          # noqa: E402

SAAT = 20260921
MENGE = "50%"
RUECKBLICK = 60
# ⚠️ Das registrierte Band, aus dem Registerblatt uebernommen und hier
# als VORABFESTLEGUNG fixiert - nicht nachtraeglich angepasst.
REG_WIRKUNG = 0.0616
REG_UNTEN, REG_OBEN = 0.0203, 0.1111


def _arg(args, f, v):
    return args[args.index(f) + 1] if f in args else v


def log_umschlag(reihen: dict, menge: dict) -> dict:
    """log(Stueckvolumen / SplyCur) je Symbol und Tag.

    ⚠️ Aus DENSELBEN Reihen wie `K.baue(art='turnover')` - Spalte 4 ist
    das Volumen. Eine zweite Quelle waere eine zweite Groesse.
    """
    aus = {}
    for sym, roh in reihen.items():
        m = menge.get(sym.upper())
        if not m:
            continue
        for z in roh:
            tag, v = z[0], z[4]
            q = m.get(tag)
            if q and q > 0 and v and v > 0:
                aus.setdefault(sym.upper(), {})[tag] = math.log(v / q)
    return aus


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    horizonte = tuple(int(x) for x in
                      _arg(args, "--horizonte", "5,10,20").split(","))
    rueck = int(_arg(args, "--rueckblick", str(RUECKBLICK)))
    menge = _arg(args, "--menge", MENGE)
    saat = int(_arg(args, "--saat", str(SAAT)))

    print("=" * 112)
    print("DIE ZERLEGUNG AUF DER REGISTRIERTEN BASIS - dort, wo sie "
          "entscheidbar ist")
    print("=" * 112)
    print("  " + N.standardzeile())
    reihen = B.lade()
    splycur = MB.reihe("data/onchain_historie.db", "splycur")
    mom = momentum250(reihen)
    lg = N.Lage(instrument="spot", strategie="einstieg")
    print("  Reihen %d · SplyCur %d Symbole · Menge %s · Rueckblick %d"
          % (len(reihen), len(splycur), menge, rueck))

    # ---- TEIL 1: R-R11 ------------------------------------------------
    print()
    print("#" * 112)
    print("# TEIL 1 - REPRODUKTION (R-R11). Registriert: %+.4f R "
          "[%+.4f .. %+.4f], H20, 2.636 Tage"
          % (REG_WIRKUNG, REG_UNTEN, REG_OBEN))
    print("#" * 112)
    je20 = K.baue(reihen, "turnover", splycur, horizont=20)
    tage = sorted(je20)
    print("  gebaut: %d Kalendertage (%s bis %s) · %d Anker · %d Symbole"
          % (len(tage), tage[0] if tage else "-", tage[-1] if tage else "-",
             sum(len(z) for z in je20.values()),
             len({x["sym"] for z in je20.values() for x in z})))
    try:
        rep = MA.pruefe_auswahl(
            "turnover", je20, mom, lage=lg, menge=menge,
            rng=np.random.default_rng(saat), horizont=20,
            hypothese="R-R11 Reproduktion der registrierten Basis",
            verwendung="Beitrag", zielgroesse="bewegung_r")
    except Exception as exc:                               # noqa: BLE001
        print("  ⛔ Reproduktion nicht moeglich: %s" % str(exc)[:80])
        return 2
    drin = REG_UNTEN <= rep.wirkung <= REG_OBEN
    print("  gemessen: %+.4f R [%+.4f .. %+.4f] · Null %+.4f · %d Tage "
          "· %d Bloecke · %d Symbole"
          % (rep.wirkung, rep.unten, rep.oben, rep.bezugswert,
             rep.n_tage, rep.n_bloecke, rep.abdeckung_symbole))
    print("  Urteil: %s" % rep.urteil)
    print()
    print("  ➤ %s"
          % ("✔✔ REPRODUZIERT - die Wirkung liegt im registrierten Band"
             if drin else
             "⛔⛔ NICHT REPRODUZIERT - die Wirkung liegt AUSSERHALB des "
             "registrierten Bandes"))
    if not drin:
        print("     ⚠️⚠️ Nach der Vorabfestlegung im Skriptkopf ist damit "
              "ALLES von heute")
        print("        hinfaellig, nicht nur dieser Lauf. Die Ursache "
              "gehoert geklaert,")
        print("        BEVOR irgendein Befund weiterverwendet wird.")
    if "--nur-repro" in args:
        return 0 if drin else 1

    # ---- TEIL 2: die Zerlegung ---------------------------------------
    print()
    print("#" * 112)
    print("# TEIL 2 - EIGENSCHAFT ODER ZUSTAND, auf 2.636 Tagen")
    print("#" * 112)
    log_u = log_umschlag(reihen, splycur)
    asset, lage = {}, {}
    for s, d in log_u.items():
        t = sorted(d)
        if len(t) < rueck + 200:
            continue
        for i in range(rueck, len(t)):
            m = st.mean([d[t[j]] for j in range(i - rueck, i)])
            asset.setdefault(s, {})[t[i]] = m
            lage.setdefault(s, {})[t[i]] = d[t[i]] - m
    _rz = np.random.default_rng(saat + 991)
    zuf_a = {s: {t: float(_rz.random()) for t in d}
             for s, d in asset.items()}
    zuf_l = {s: {t: float(_rz.random()) for t in d}
             for s, d in lage.items()}
    print("  log-Umschlag %d Symbole · ASSET %d · LAGE %d"
          % (len(log_u), len(asset), len(lage)))
    # ⚠️ Wie statisch ist der Nenner HIER? Vorweg ausgewiesen, weil es
    # das Ergebnis vorzeichnet.
    starr = 0
    for s in asset:
        w = [splycur[s][t] for t in sorted(splycur.get(s, {}))]
        if len(w) > 60 and st.median(w) > 0:
            starr += ((max(w) - min(w)) / st.median(w) < 0.01)
    print("  ⚠️ davon mit praktisch STARREM Nenner (Spanne unter 1 %%): "
          "%d von %d" % (starr, len(asset)))
    arme = (("GESAMT", log_u, None),
            ("EIGENSCHAFT", asset, None),
            ("LAGE", lage, None),
            ("LAGE ohne EIGEN", lage, asset),
            ("EIGEN ohne LAGE", asset, lage),
            ("LAGE ohne ZUFALL", lage, zuf_l),
            ("EIGEN ohne ZUFALL", asset, zuf_a),
            ("zufall (Kontrolle)", zuf_l, None))
    zellen = len(horizonte) * len(arme)
    print("  ⚠️ %d Zellen - familienweiter Fehlalarm rund %.0f %%. "
          "Geurteilt wird nach FORM."
          % (zellen, 100 * ST.familienfehler(zellen)))
    print()
    print("  %-20s %3s %6s %6s %9s %20s %9s %7s  %s"
          % ("Arm", "H", "Syms", "Raster", "Wirkung", "Band", "Bezug",
             "Blöcke", "Urteil"))
    erg: dict = {}
    for H in horizonte:
        for name, ziel, schicht in arme:
            q = ZB.residualisieren(ziel, schicht) if schicht else ziel
            _n, anteil = ZB.raster(q)
            je = K.baue(reihen, "turnover_markt", q, horizont=H)
            if not je:
                print("  %-20s %3d -> leere Welt" % (name, H))
                continue
            try:
                b = MA.pruefe_auswahl(
                    name.split()[0], je, mom, lage=lg, menge=menge,
                    rng=np.random.default_rng(saat), horizont=H,
                    hypothese="Zerlegung auf registrierter Basis",
                    verwendung="Beitrag", zielgroesse="bewegung_r")
            except Exception as exc:                       # noqa: BLE001
                print("  %-20s %3d -> %s" % (name, H, str(exc)[:56]))
                continue
            erg.setdefault(name, {})[H] = b
            print("  %-20s %3d %6d %5.0f%% %+9.4f [%+.4f..%+.4f] %+9.4f "
                  "%7d  %s"
                  % (name, H, b.abdeckung_symbole, 100 * anteil, b.wirkung,
                     b.unten, b.oben, b.bezugswert, b.n_bloecke,
                     C.kurz(b.urteil)), flush=True)
        print()

    print("=" * 112)
    print("  AUSWERTUNG NACH DER VORABFESTLEGUNG")
    print("=" * 112)
    for name, _z, _s in arme:
        je_h = erg.get(name, {})
        if not je_h:
            print("  %-20s keine auswertbare Zelle" % name)
            continue
        ohne = [h for h, b in je_h.items()
                if b.urteil.startswith("KEIN BEFUND")]
        t = sorted(h for h, b in je_h.items()
                   if b.traegt and h not in ohne)
        print("  %-20s %s   traegt bei %s%s"
              % (name,
                 " ".join("H%d:%+.4f%s" % (h, je_h[h].wirkung,
                                           "*" if (je_h[h].traegt and
                                                   h not in ohne) else "")
                          for h in sorted(je_h)),
                 ("H" + ", H".join(str(x) for x in t)) if t else "KEINEM",
                 (" ⚠️ kein Befund bei H%s"
                  % ",H".join(str(x) for x in ohne)) if ohne else ""))
    print()
    print("  ⚠️ DIE KONTROLLE ,zufall` MUSS STUMM SEIN. Traegt sie, ist "
          "der Lauf wertlos.")
    print("  ⚠️ R-R11 ist hier ERFUELLT oder NICHT - Teil 1 entscheidet "
          "das, nicht Teil 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
