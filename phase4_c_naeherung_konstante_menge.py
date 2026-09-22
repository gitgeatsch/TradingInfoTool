# -*- coding: utf-8 -*-
"""TRAEGT `umschlag_naeherung`? - heutige Menge rueckwaerts konstant.

⚠️⚠️⚠️ WOHER DIE IDEE KOMMT - UND WARUM SIE NICHT NEU IST.
Befund 2.417-naeherung vom 13.09.2026 sagt woertlich:

    „Als ERSATZ fuer eine echte Umlaufmenge taugt sie nicht. Als
     AUSWEITUNG auf Symbole, fuer die es gar keine gibt, bleibt sie
     OFFEN - dann aber mit ausgeschlossenen Umstellungswerten und
     benanntem Fenster."

Diese Option stand acht Tage offen und wurde nie verfolgt. Gefunden
erst am 21.09. auf Nutzerfrage *„Wo ist deine Lösung als experte"* -
nachdem ich denselben Befund am selben Tag ZWEIMAL nur halb gelesen
hatte.

## Der Gedanke

    turnover = Volumen / (Preis x Menge)

Preis und Volumen liegen fuer die VOLLE Historie vor (`messdaten.db`,
505 Kryptoreihen ab 2023). Es fehlt allein die MENGE - und die ist
traege. Setzt man die HEUTIGE Menge rueckwaerts konstant an, loest das
BEIDE Engpaesse auf einmal: Abdeckung (59 -> 375 Symbole) und
Fensterlaenge (365 Tage -> volle Historie, also auch H20).

## ⚠️⚠️ VORABFESTLEGUNG - alles hier steht VOR dem ersten Lauf

### Die drei Arme

    ECHT       echte Menge (`umschlag_gesamt`), nur die gemeinsamen
               Symbole            -> der Massstab, R-R11
    NAEH-GEM   Naeherung, DIESELBEN Symbole
               -> trennt die NAEHERUNG von der MENGE
    NAEH-VOLL  Naeherung, alle zulaessigen
               -> die eigentliche Frage

⚠️ Ohne NAEH-GEM waere jede Differenz uninterpretierbar: sie mischte
den Naeherungsfehler mit dem Mengeneffekt. Dieselbe Konstruktion wie in
`phase4_c_kalibrierung_freefloat` (2.505).

### Die Ausschluesse, beide aus einem UNABHAENGIGEN Grund

    Umstellungen   Tagessprung im PREIS ueber Faktor 5 - der bestehende
                   Erzeuger aus `pruefe_datenqualitaet.py` (14 von 523
                   Reihen, LUNA 177.400, COCOS 1.295, DREP 108). KEIN
                   Katalog, eine strukturelle Regel.
    Mengendrift    max/min der Mengenreihe ueber Faktor 6,53.

⚠️⚠️ DIE 6,53 IST ABGELEITET, NICHT GESETZT: so breit ist ein
turnover-Fuenftel im Querschnitt (Median ueber 263 Tage x 3
Grenzpaare; 25. Perzentil 5,65, 75. 7,51). Eine Mengendrift UNTER
dieser Breite kann ein Symbol hoechstens EIN Fuenftel verschieben.
Wer die Grenze aus der Driftverteilung abliest, waehlt sie nach dem
Ergebnis - das waere Suchpreis.

### Was als Ergebnis gilt

| NAEH-VOLL | Deutung |
|---|---|
| traegt auf ALLEN zulaessigen Mengen, mind. ein Horizont | ✔ tragfaehig |
| traegt auf EINIGEN | ⚠ nicht robust - Befund, kein Grund zur Mengenwahl |
| traegt auf KEINER | ✖ die Naeherung bringt nichts |

⚠️ ECHT laeuft als MASSSTAB mit. Faellt er durch, sagt das etwas ueber
Fenster und Menge - nicht ueber die registrierte Tabelle (R-R11).

### Was diese Messung NICHT kann

⚠️ Die Mengendrift ist nur ueber 365 Tage bekannt (CoinGecko gibt nicht
mehr). Ueber die volle Historie driftet MEHR, und wie viel, ist nicht
messbar. Der Naeherungsfehler ist damit eine UNTERGRENZE. Die direkte
Fehlermessung auf den Symbolen MIT echter Menge (2.417: 88,1 Prozent
gleiches Fuenftel ab 2023) bleibt der beste Anhaltspunkt - und die
Driftverteilung der neuen Symbole ist im Median vergleichbar (1,111
gegen 1,076), in den Schwaenzen schwerer (95. Perzentil 3,04 gegen
1,77).

⚠️ NUR LESEND, keine Netzabrufe, keine Standard-DB.
"""
import os
import sqlite3
import sys
import time

if hasattr(sys.stdout, "reconfigure"):        # ⚠ Suite ersetzt stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import numpy as np                                          # noqa: E402

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messnorm as N                                        # noqa: E402
import messnorm_auswahl as MA                               # noqa: E402
import phase4_c_kalibrierung_freefloat as KF                # noqa: E402

AB = "2023-01-01"          # das Fenster aus `zeitfenster-ab-2023`
DRIFT_GRENZE = 6.53        # = Breite eines turnover-Fuenftels, abgeleitet
SPRUNG = 5.0               # Preissprung = Umstellungsverdacht (bestehend)
SAAT = 20260921


def _arg(a, f, v):
    return a[a.index(f) + 1] if f in a else v


def mengen_heute(datei: str = "data/umlaufmenge_cg.db") -> dict:
    """Die JUENGSTE Menge je Symbol - und die Driftpruefung dazu.

    ⚠⚠⚠ EINE BETRIEBSKOPIE WIRD HIER ABGEWIESEN
    (22.09.2026). Am Notebook liegt eine SCHLANKE Fassung dieser
    Datei - 14 Tage statt 365, gebaut von `baue_nb_umlaufmenge.py`,
    damit der Betrieb dort rechnen kann. Sie SIEHT AUS wie die
    Messbasis und ist es nicht.

    Genau dieser Fall hat schon einmal Schaden angerichtet
    (`betriebskopie-ist-keine-messbasis`). Deshalb traegt die Kopie
    die Markertabelle `_nur_betrieb`, und hier wird ABGEBROCHEN -
    nicht gewarnt. Eine Warnung uebersieht man; einen Abbruch nicht.

    ⚠ Der BETRIEBSleser (`marktrang.umlaufmengen_frei`) darf
    sie benutzen - dafuer ist sie da. Der Riegel sitzt hier, wo
    GEMESSEN wird.
    """
    c = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
    if c.execute("SELECT name FROM sqlite_master WHERE type='table' "
                 "AND name='_nur_betrieb'").fetchone():
        hinweis = (c.execute("SELECT hinweis FROM _nur_betrieb")
                   .fetchone() or ["(ohne Hinweis)"])[0]
        c.close()   # ⚠ sonst bleibt die Datei gesperrt - die Suite
        #             konnte ihre Wegwerfdatei nicht loeschen
        raise SystemExit(
            "⛔ %s ist eine BETRIEBSKOPIE, keine Messbasis. %s "
            "Die volle Historie liegt am Desktop unter demselben "
            "Namen." % (datei, hinweis))
    reihen: dict = {}
    for s, w in c.execute(
            "SELECT u.symbol, u.wert FROM umlaufmenge u "
            "  JOIN abruf_symbol a ON a.symbol = u.symbol "
            " WHERE a.urteil = 'ok' AND u.wert > 0 "
            " ORDER BY u.symbol, u.datum"):
        reihen.setdefault(s.upper(), []).append(float(w))
    heute, raus = {}, []
    for s, w in reihen.items():
        if len(w) < 60:
            continue
        d = max(w) / min(w) if min(w) > 0 else float("inf")
        if d > DRIFT_GRENZE:
            raus.append((s, d))
            continue
        heute[s] = w[-1]
    return heute, sorted(raus, key=lambda x: -x[1])


def umstellungen(reihen: dict) -> set:
    """Reihen mit einem Tagessprung ueber Faktor 5 - derselbe Erzeuger
    wie in `pruefe_datenqualitaet.py`. Strukturelle Regel, kein Katalog."""
    raus = set()
    for s, z in reihen.items():
        c = [x[1] for x in z if x[1] and x[1] > 0]
        for i in range(1, len(c)):
            v = c[i] / c[i - 1]
            if v > SPRUNG or v < 1.0 / SPRUNG:
                raus.add(s)
                break
    return raus


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    horizonte = tuple(int(x) for x in
                      _arg(args, "--horizonte", "3,5,20").split(","))
    ziele = tuple(_arg(args, "--zielgroesse", "bewegung_r").split(","))
    saat = int(_arg(args, "--saat", str(SAAT)))
    if "--nullsaat" in args:
        N.SAAT = int(_arg(args, "--nullsaat", str(N.SAAT)))
    t0 = time.time()

    print("=" * 112)
    print("TRAEGT `umschlag_naeherung`? - heutige Menge rueckwaerts "
          "konstant (2.417-naeherung)")
    print("=" * 112)
    print("  " + N.standardzeile())
    print()

    heute, drift_raus = mengen_heute()
    reihen = B.lade()
    umst = umstellungen(reihen)
    echt = MB.reihe("data/onchain_historie.db", "splycur")

    print("  AUSSCHLUESSE, beide aus einem unabhaengigen Grund")
    print("    Mengendrift ueber Faktor %.2f : %3d Symbole  %s"
          % (DRIFT_GRENZE, len(drift_raus),
             ", ".join("%s(%.0f)" % (s, d) for s, d in drift_raus[:6])))
    print("    Preissprung ueber Faktor %.0f   : %3d Reihen   %s"
          % (SPRUNG, len(umst), ", ".join(sorted(umst)[:8])))
    print()

    # ⚠️ `B.lade` liefert je Symbol Tupel (datum, close, high, low,
    # volumen) - `x[1]` ist der SCHLUSSKURS, darauf prueft
    # `umstellungen`. Nachgesehen, nicht angenommen:
    # `SELECT symbol, date, close, high, low, volume`.
    naeh = {s: m for s, m in heute.items() if s not in umst}
    gemeinsam = set(naeh) & set(echt)
    print("  MENGEN")
    print("    ECHT  (`umschlag_gesamt`, SplyCur) : %4d Symbole" % len(echt))
    print("    NAEH  (heutige Menge konstant)     : %4d Symbole" % len(naeh))
    print("    gemeinsam (der faire Vergleich)    : %4d" % len(gemeinsam))
    print()
    print("  ⚠️ Fenster ab %s. ECHT ist der MASSSTAB, nicht der "
          "Angeklagte (R-R11)." % AB)
    print()

    lagen = {}
    for (inst, strat), zg in N.ZIELGROESSE_JE_LAGE.items():
        if zg in ziele and zg not in lagen and inst in ("spot", "hebel"):
            lagen[zg] = N.Lage(instrument=inst, strategie=strat,
                               simuliert=(inst == "hebel"))

    # ⚠️ Die Naeherung als KONSTANTE Reihe: `K.baue` erwartet je Symbol
    # ein dict {tag: menge}. Eine Konstante ist das mit EINEM Wert fuer
    # jeden Tag - gebaut aus den Tagen, die die Kursreihe ohnehin hat.
    naeh_reihe = {}
    for s, m in naeh.items():
        z = reihen.get(s)
        if not z:
            continue
        naeh_reihe[s] = {str(x[0])[:10]: m for x in z}

    mom = KF.momentum250(reihen)
    arme = [("ECHT", echt, gemeinsam),
            ("NAEH-GEM", naeh_reihe, gemeinsam),
            ("NAEH-VOLL", naeh_reihe, None)]
    ergebnis: dict = {}

    for ziel in ziele:
        print("-" * 112)
        print("  ZIELGROESSE: %s" % ziel)
        print("-" * 112)
        print("  %-10s %3s %6s %6s %9s %22s %9s %7s  %s"
              % ("Arm", "H", "Syms", "Menge", "Wirkung", "Band", "Bezug",
                 "Bloecke", "Urteil"))
        for H in horizonte:
            KF._SPEICHER.clear()
            for name, quelle, filt in arme:
                try:
                    je0 = K.baue(reihen, "turnover", quelle, horizont=H)
                except Exception as exc:                   # noqa: BLE001
                    print("  %-10s %3d -> %s" % (name, H, str(exc)[:58]))
                    continue
                je = KF.beschneiden(je0, filt or None, AB)
                if not je:
                    print("  %-10s %3d -> leere Welt" % (name, H))
                    continue
                syms = len({x["sym"] for z in je.values() for x in z})
                for menge in MA.zulaessige_mengen(je, mom, horizont=H):
                    try:
                        b = MA.pruefe_auswahl(
                            "turnover", je, mom, lage=lagen[ziel],
                            menge=menge,
                            rng=np.random.default_rng(saat), horizont=H,
                            hypothese="C Naeherung konstante Menge",
                            verwendung="Beitrag", zielgroesse=ziel)
                    except Exception as exc:               # noqa: BLE001
                        print("  %-10s %3d %6s -> %s"
                              % (name, H, menge, str(exc)[:52]))
                        continue
                    ergebnis.setdefault((ziel, name), {})[(H, menge)] = b
                    print("  %-10s %3d %6d %6s %+9.4f [%+.4f..%+.4f] "
                          "%+9.4f %7d  %s"
                          % (name, H, syms, menge, b.wirkung, b.unten,
                             b.oben, b.bezugswert, b.n_bloecke,
                             KF.kurz(b.urteil)), flush=True)
            print()

    print("=" * 112)
    print("  WAS DIE DREI ARME ZUSAMMEN SAGEN")
    print("=" * 112)
    for ziel in ziele:
        print("  %s:" % ziel)
        for name, _q, _f in arme:
            je = ergebnis.get((ziel, name), {})
            if not je:
                print("    %-10s keine auswertbare Zelle" % name)
                continue
            traegt = sorted(k for k, b in je.items() if b.traegt)
            print("    %-10s %s"
                  % (name, " ".join("H%d/%s:%+.4f%s"
                                    % (k[0], k[1], je[k].wirkung,
                                       "*" if je[k].traegt else "")
                                    for k in sorted(je))))
            print("    %-10s traegt auf %d von %d Zellen%s"
                  % ("", len(traegt), len(je),
                     (": " + ", ".join("H%d/%s" % k for k in traegt))
                     if traegt else " - KEINER"))
        a = ergebnis.get((ziel, "ECHT"), {})
        g = ergebnis.get((ziel, "NAEH-GEM"), {})
        v = ergebnis.get((ziel, "NAEH-VOLL"), {})
        for links, rechts, titel in (
                (a, g, "NAEHERUNGSFEHLER (NAEH-GEM minus ECHT)"),
                (g, v, "MENGENGEWINN (NAEH-VOLL minus NAEH-GEM)")):
            k = sorted(set(links) & set(rechts))
            if not k:
                continue
            d = [rechts[x].wirkung - links[x].wirkung for x in k]
            print("    ➤ %s: %s · Median %+.4f R"
                  % (titel,
                     " ".join("H%d/%s:%+.4f"
                              % (x[0], x[1],
                                 rechts[x].wirkung - links[x].wirkung)
                              for x in k), float(np.median(d))))
        print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60))
    return 0


if __name__ == "__main__":
    sys.exit(main())
