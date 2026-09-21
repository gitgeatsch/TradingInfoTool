# -*- coding: utf-8 -*-
"""IST DIE LAGE NUR DIE EIGENSCHAFT MIT UMWEG - ODER UMGEKEHRT?

⚠️⚠️ DIE FRAGE, AN DER DIE HEBELENTSCHEIDUNG HAENGT. Die Zerlegung hat
gezeigt: BEIDE Teile von `turnover` tragen - die Asset-EIGENSCHAFT
(nachlaufender Schnitt) und die LAGE (Abstand dazu). Die Vorabfestlegung
sagt dann „trennen, nicht mitteln". Aber vorher ist EINE Frage offen,
und sie ist die eigentliche:

    Traegt die LAGE noch, wenn man die EIGENSCHAFT FESTHAELT?

Denn beide stammen aus derselben Zahl. Traegt die Lage nur, weil sie
nebenbei dieselben Assets auswaehlt, ist sie kein eigener Beitrag - sie
ist die Eigenschaft mit Umweg. Das ist Prueflisten-Frage 1 (Methodik
2.80): *ist der Kandidat ein Mitlaeufer?*

⚠️ FUER DEN HEBEL ist genau das entscheidend. Regel 3 verbietet, den
HEBEL aus einem Asset-Rang zu erzeugen. Traegt die Lage EIGENSTAENDIG,
kann der Hebel auf ihr allein stehen - regelkonform und ohne Verlust.
Traegt sie es nicht, bleibt `turnover` im Kern ein Asset-Rang, und die
Regel-3-Frage ist offen.

## Der Aufbau - das ECHTE Hauswerkzeug, nicht nachgebaut

`messe_kandidaten_als_regel.geschichtet()` sortiert je Kalendertag nach
der SCHICHT in Fuenftel und laesst die Regel INNERHALB jedes Faches
wirken. Ueber alle Faecher hinweg ist die Schichtverteilung der
Gesperrten damit dieselbe wie die der Behaltenen - was uebrig bleibt,
kann die Schicht nicht mehr erklaeren.

## ⚠️ NORMKONFORM, nicht mit EINER Negativkontrolle

`mitlaeufer()` stellt dem Ergebnis EINE gemischte Ziehung gegenueber.
Der Messstandard vom 08.09. verlangt den Nullpunkt als MITTELWERT aus
40 Nullwelten (`eine-ziehung-ist-kein-nullpunkt`). Hier werden deshalb
`NULL_ZIEHUNGEN` geschichtete Nullwelten gezogen und gemittelt - genau
wie `messnorm.pruefe` es fuer den ungeschichteten Fall tut.

⚠️⚠️ WAS FEHLT UND WAS DAS BEDEUTET: eine Trennschaerfe (gepflanzte
Leiter) gibt es auf dem geschichteten Pfad nicht. Damit ist hier NUR
EIN POSITIVER BEFUND DEUTBAR. Ein Nullbefund heisst „kein Befund",
nicht „traegt nicht" - und er ist ohnehin schwaecher als oben, weil die
Faecher klein sind und das Band dadurch breiter (so steht es im
Docstring von `geschichtet`).

    python phase4_c_mitlaeufer_asset_lage.py
    python phase4_c_mitlaeufer_asset_lage.py --horizonte 2,3 --ziehungen 20
"""
from __future__ import annotations

import os
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402
import messe_bewertungskennzahl as M                       # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402
import messe_regel_wirksamkeit as W                        # noqa: E402
import messnorm as N                                       # noqa: E402
import phase4_c_hypothese_turnover as HY                   # noqa: E402
import phase4_c_kalibrierung_freefloat as C                # noqa: E402

SAAT = 20260921


def _arg(args, f, v):
    return args[args.index(f) + 1] if f in args else v


def band(titel, d, rng, block, still=True):
    if not still:
        return M.urteil_tage(titel, d, rng, block)
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        return M.urteil_tage(titel, d, rng, block)


def schichtprobe(je_tag, schicht, block, ziehungen, saat):
    """Wirkung INNERHALB der Schicht, gegen 40 geschichtete Nullwelten."""
    rng = np.random.default_rng(saat)
    d = K.geschichtet(je_tag, schicht)
    # ⚠⚠ DIE BLOCKSPERRE FEHLTE. `urteil_tage` rechnet ein Band aus
    # so vielen Bloecken, wie da sind - `messnorm` verweigert unter 20
    # ("bei 5 Bloecken 19,5 % Fehlalarme statt 5 %"). Auf dem
    # geschichteten Pfad gibt es diese Sperre nicht, also muss sie hier
    # stehen. Genau die Klasse Fehler, die am selben Tag als
    # 2.506-randlage registriert wurde - und ich haette sie beinahe
    # wiederholt.
    bloecke = len(d) // block if block else 0
    if len(d) < block + 30 or bloecke < 20:
        return {"zuwenig": bloecke, "tage": len(d)}
    haupt = band("netto", d, rng, block)
    if haupt is None:
        return None
    mittel = []
    for z in range(ziehungen):
        dn = K.geschichtet(je_tag, schicht,
                           mische=np.random.default_rng(saat + 1000 + z))
        nb = band("null %d" % z, dn, np.random.default_rng(saat + z), block)
        if nb:
            mittel.append(nb["mittel"])
    null = float(np.mean(mittel)) if mittel else 0.0
    return {"wirkung": haupt["mittel"], "unten": haupt["unten"],
            "oben": haupt["oben"], "null": max(0.0, null),
            "tage": len(d), "nullen": len(mittel)}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    horizonte = tuple(int(x) for x in
                      _arg(args, "--horizonte", "2,3,5").split(","))
    ziehungen = int(_arg(args, "--ziehungen", str(N.NULL_ZIEHUNGEN)))
    rueck = int(_arg(args, "--rueckblick", str(HY.RUECKBLICK)))
    saat = int(_arg(args, "--saat", str(SAAT)))

    print("=" * 104)
    print("MITLAEUFERTEST - traegt die LAGE noch, wenn die EIGENSCHAFT "
          "festgehalten wird?")
    print("=" * 104)
    print("  " + N.standardzeile())
    neu, weg, ges = C.menge_neu(C.MENGE_DB, True)
    datei, _sql = MR.MESSBASIS["schnitt"]
    log_u, ab = HY.reihen_umschlag(neu, datei)
    asset, lage = HY.zerlege(log_u, rueck)
    reihen = B.lade()
    print("  Fenster ab %s · Rueckblick %d · Nullwelten je Zelle %d"
          % (ab, rueck, ziehungen))
    print("  ⚠️ NUR EIN POSITIVER BEFUND IST HIER DEUTBAR - auf dem "
          "geschichteten Pfad")
    print("     gibt es keine Trennschaerfe. Ein Nullbefund heisst "
          ",kein Befund`.")
    print()

    for H in horizonte:
        je_a = C.beschneiden(
            K.baue(reihen, "turnover_markt", asset, horizont=H), None, ab)
        je_l = C.beschneiden(
            K.baue(reihen, "turnover_markt", lage, horizont=H), None, ab)
        # gemeinsame Basis - nur Tage und Symbole, die BEIDE haben
        a_je_tag = {t: {x["sym"]: x["kennzahl"] for x in z}
                    for t, z in je_a.items()}
        l_je_tag = {t: {x["sym"]: x["kennzahl"] for x in z}
                    for t, z in je_l.items()}
        gem_a, gem_l = {}, {}
        for t, z in je_a.items():
            s = l_je_tag.get(t) or {}
            behalten = [x for x in z if x["sym"] in s]
            if len(behalten) >= K.MIND_JE_TAG:
                syms = {y["sym"] for y in behalten}
                gem_a[t] = behalten
                gem_l[t] = [x for x in je_l[t] if x["sym"] in syms]
        if not gem_a:
            print("  H%d -> keine gemeinsame Basis" % H)
            continue
        block = N._block(H)
        print("-" * 104)
        print("  H%d · gemeinsame Basis %d Tage · %d Anker · Block %d"
              % (H, len(gem_a), sum(len(z) for z in gem_a.values()), block))
        print("-" * 104)
        # ---- messen die beiden ueberhaupt Verschiedenes? --------------
        ks = []
        for t, z in gem_a.items():
            s = l_je_tag[t]
            ra = W.rang([x["kennzahl"] for x in z])
            rb = W.rang([s[x["sym"]] for x in z])
            if len(ra) > 3:
                r = float(np.corrcoef(ra, rb)[0, 1])
                if r == r:
                    ks.append(r)
        if ks:
            print("     Rangkorrelation EIGENSCHAFT gegen LAGE je Tag: "
                  "Median %+.3f · |rho| > 0,3 an %.0f %% der Tage"
                  % (st.median(ks), 100 * np.mean(np.abs(ks) > 0.3)))
            print("     ⚠️ Eine niedrige Korrelation entlastet NICHT - "
                  "sie sagt nur, dass die")
            print("        Rangfolgen verschieden sind, nicht dass die "
                  "WIRKUNG es ist.")
        print()
        print("     %-46s %9s %20s %9s %6s  %s"
              % ("Zelle", "Wirkung", "Band", "Nullpkt", "Tage", "Urteil"))
        # ⚠⚠ DIE DRITTE ZEILE IST DIE KONTROLLE - UND SIE IST DER
        # ZWEITE ANLAUF.
        #
        # ERSTER ANLAUF, VERWORFEN (21.09.2026): die LAGE nach SICH
        # SELBST schichten, in der Erwartung, der Effekt breche
        # zusammen. Er brach nicht - und das war KEIN Werkzeugfehler,
        # sondern ein Denkfehler von mir. `geschichtet` sperrt
        # INNERHALB jedes Fuenftels erneut die obersten `GRENZE`; bei
        # Schichtung nach sich selbst bleibt die Ordnung erhalten und
        # die Regel wirkt auf feinerem Raster weiter. Der Effekt
        # schrumpfte folgerichtig auf rund ein Drittel (+0,0128 ->
        # +0,0040), ohne zu verschwinden. Eine Mutation, die auch bei
        # intaktem Werkzeug nicht bricht, pruefte nichts.
        #
        # ZWEITER ANLAUF, DIESER: nach einer ZUFALLSGROESSE schichten.
        # Zufallsfaecher tragen keine Information - das Ergebnis muss
        # dann dem UNGESCHICHTETEN entsprechen. Weicht die Schichtung
        # nach der EIGENSCHAFT davon ab, hat die Eigenschaft
        # tatsaechlich etwas herausgerechnet; stimmen beide ueberein,
        # ist die Rede von "eigenstaendig" leer.
        #
        # ⚠ Das ist die Kontrolle, die selbst geprueft ist
        # (`kontrollen-muessen-selbst-geprueft-werden`).
        # ⚠⚠ ZWEI Zufallsschichten, nicht eine. Die erste Fassung
        # gab nur der LAGE eine Kontrolle. Damit war nicht zu
        # unterscheiden, ob die EIGENSCHAFT DURCH die Schichtung faellt
        # oder auf diesem Pfad NIE getragen hat - ein voreiliger
        # Schluss waere die Folge gewesen. Jede Zeile bekommt ihre
        # eigene Zufallskontrolle.
        _z = np.random.default_rng(saat + 77)
        zufall_l = {t: {x["sym"]: float(_z.random()) for x in z}
                    for t, z in gem_l.items()}
        zufall_a = {t: {x["sym"]: float(_z.random()) for x in z}
                    for t, z in gem_a.items()}
        for titel, je, schicht in (
                ("LAGE innerhalb der EIGENSCHAFTS-Fuenftel", gem_l,
                 a_je_tag),
                ("EIGENSCHAFT innerhalb der LAGE-Fuenftel", gem_a,
                 l_je_tag),
                ("KONTROLLE LAGE in ZUFALLS-Fuenfteln", gem_l,
                 zufall_l),
                ("KONTROLLE EIGENSCHAFT in ZUFALLS-Fuenfteln", gem_a,
                 zufall_a)):
            r = schichtprobe(je, schicht, block, ziehungen, saat)
            if r is None or "zuwenig" in r:
                print("     %-46s -> KEIN BEFUND: nur %s Bloecke von 20 "
                      "gefordert (%s Tage)"
                      % (titel, (r or {}).get("zuwenig", "?"),
                         (r or {}).get("tage", "?")))
                continue
            traegt = r["unten"] > r["null"]
            print("     %-46s %+9.4f [%+.4f..%+.4f] %+9.4f %6d  %s"
                  % (titel, r["wirkung"], r["unten"], r["oben"],
                     r["null"], r["tage"],
                     "TRAEGT EIGENSTAENDIG" if traegt
                     else "kein Befund (siehe Kopf)"), flush=True)
        print()
    print("=" * 104)
    print("  ⚠️ LESEART FUER DEN HEBEL: traegt die LAGE eigenstaendig, "
          "kann der Hebel")
    print("     auf ihr allein stehen - Regel 3 waere gewahrt, ohne "
          "etwas zu verlieren.")
    print("     Traegt sie es nicht, bleibt `turnover` im Kern ein "
          "Asset-Rang.")
    print("  ⚠️ R-R11: H2..H5, 365 Tage, freier Umlauf. Sagt nichts "
          "ueber die registrierte")
    print("     Tabelle (H20, 2.636 Tage, Gesamtausgabe).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
