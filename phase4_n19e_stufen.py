# -*- coding: utf-8 -*-
"""N19-E NORMGERECHT: die Hebelstufen direkt gegen die Barrieren-Quote.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_Geometrie_Hebel_24_09.md`
Befunde 2.580 (Vorabfestlegung), 2.581 (zwei Brueche vor der Messung).

═══════════════════════════════════════════════════════════════════════
 WARUM DIESES WERKZEUG NEU IST - und `phase4_n19e_pruefen` nicht benutzt
═══════════════════════════════════════════════════════════════════════

`phase4_n19e_pruefen.py` enthaelt NULL Verweise auf `messnorm` - es ist
Altbestand. CLAUDE.md dazu: *„178 von 311 Messwerkzeugen sind Altbestand;
ein Befund aus dieser Gruppe gilt nur mit Vorbehalt."* Ohne Nachruestung
fehlten Nullpunkt, Nullwelten, Trennschaerfe, Positivkontrolle und Baender.

═══════════════════════════════════════════════════════════════════════
 DIE ZWEITEILUNG - `FRAGEARTEN` gibt sie selbst vor
═══════════════════════════════════════════════════════════════════════

    TEIL A   die Stufen SCHAETZEN je Fuenftel
             Frageart `zaehlung` - deskriptiv, KEIN Urteil
             ⚠️ trotzdem OUT-OF-SAMPLE: erste Haelfte fitten,
                zweite pruefen. Auf denselben Ankern zu fitten und
                zu pruefen waere per Konstruktion wahr.

    TEIL B   die daraus gebaute REGEL pruefen
             Frageart `beitrag` -> SELEKTIERTE Menge (F-212)
             volle Norm ueber `messnorm_auswahl.pruefe_auswahl` -
             dieselbe Anlage wie `k1c_hebel_barriere`

⚠️⚠️ TEIL A ALLEIN IST KEIN BEFUND. Eine geschaetzte Stufe ist eine Zahl;
ob sie traegt, entscheidet erst Teil B.

═══════════════════════════════════════════════════════════════════════
 WIE TEIL B EIN FUENFTEL NORMGERECHT PRUEFT - ohne Nachbildung
═══════════════════════════════════════════════════════════════════════

`pruefe_auswahl` misst eine AUSWAHLregel: "die obersten X Prozent nach
Kennzahl". Ein einzelnes Fuenftel ist genau das, wenn die Kennzahl ein
INDIKATOR ist - 1 fuer "in diesem Fuenftel", 0 sonst. Mit `menge='20%'`
waehlt die Anlage dann exakt dieses Fuenftel aus.

⚠️⚠️⚠️ UND DAS VORZEICHEN IST SPIEGELBILDLICH ZU TEIL A - das ist die
Falle, und ich bin am 24.09. selbst hineingelaufen.

`messnorm_auswahl` rechnet `mittel(frei) - mittel(alle)`, und `frei` sind
die Anker, die die Regel DURCHLAESST. Teil B misst also die Wirkung des
SPERRENS, nicht des Waehlens:

    Teil B POSITIV   Sperren hilft    -> das Fuenftel ist SCHLECHT
    Teil B NEGATIV   Sperren schadet  -> das Fuenftel ist GUT

➤ Eine positive Stufe in Teil A gehoert also zu einer NEGATIVEN Wirkung in
Teil B. Wer beide Vorzeichen gleichsetzt, liest einen Widerspruch, wo
Uebereinstimmung steht - genau das ist mir bei `turnover`/H20 passiert
(Teil A +1,75 Punkte, Teil B -0,0135; beides heisst *Fuenftel 0 ist gut*).

⚠️ Die Ausgabe weist das Vorzeichen deshalb AUSDRUECKLICH aus.

═══════════════════════════════════════════════════════════════════════
 WAS DIESES WERKZEUG NICHT TUT
═══════════════════════════════════════════════════════════════════════

⛔ Es misst NUR LONG - und das ist eine Nutzerentscheidung vom 24.09.:
   *„nein lass es - war nur eine Idee, das Thema ist ohnehin schon
   kompliziert, damit wird es noch problematischer."*

   ⚠️ FACHLICH WAERE ES OHNEHIN KEINE ABKUERZUNG GEWESEN: ein negativer
   LONG-Beitrag ist NICHT automatisch ein positiver SHORT-Beitrag. Er kann
   auch „hier bewegt sich nichts" oder „hier ist es unberechenbar"
   bedeuten. 2.435-richtung belegt es: *„LONG und SHORT verhalten sich
   verschieden - der Erwartungswert SELBST unterscheidet sich"*, und bei
   SHORT traegt die Stopweite gar nicht. Dazu kennt
   `k1c_hebel_barriere.barriere_je_reihe` kein `ist_short`.

   ➤ Short waere eine EIGENE Messung mit eigener Vorabfestlegung -
   zurueckgestellt, nicht vergessen.

⛔ Es entscheidet nicht die Geometrie (Stop, CRV) - die ist nachgeordnet.

⚠️ NUR LESEND.

    python phase4_n19e_stufen.py                      # H3, Vorgabe
    python phase4_n19e_stufen.py --horizont 20        # eine andere Achse
    python phase4_n19e_stufen.py --achse              # 2/3/5/10/20
    python phase4_n19e_stufen.py --mit-fuenftel4      # Gegenprobe
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import k1c_hebel_barriere as K1C                             # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_alle_kandidaten import zusatzquellen              # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

# ⚠️ Die Merkmale werden NICHT aufgezaehlt, sondern aus den registrierten
# Beitraegen abgeleitet (CLAUDE.md, Regel 4). Kommt morgen ein dritter
# dazu, waechst diese Messung von allein mit.
ACHSE = (2, 3, 5, 10, 20)


def merkmale_aus_register() -> list:
    """Welche Merkmale tragen heute Stufen? - aus `BEITRAEGE`, nicht gesetzt."""
    from agent import wahrscheinlichkeit as W

    aus = []
    for b in W.BEITRAEGE:
        if b.zustand == "traegt" and b.stufen and b.merkmal:
            # der Kandidatenname, unter dem `messe_kandidaten_als_regel`
            # die Reihe baut - aus dem Merkmalsnamen abgeleitet
            kand = b.merkmal.replace("_fuenftel", "")
            aus.append((kand, b.merkmal, tuple(b.stufen), b.name))
    return aus


def fuenftel_je_tag(je0) -> dict:
    """{tag: {sym: 0..4}} - Rang im Querschnitt DIESES Tages.

    ⚠️ Dieselbe Definition wie `marktrang`: Fuenftel 0 ist das NIEDRIGSTE.
    Tage mit unter fuenf Werten bekommen KEINEN Rang (None) - ein Wert
    ohne Rang ist nicht schlecht, sondern unbekannt (Regel 4).
    """
    aus = {}
    for tag, zeilen in je0.items():
        if len(zeilen) < 5:
            continue
        werte = sorted((float(x["kennzahl"]), x["sym"]) for x in zeilen)
        n = len(werte)
        aus[tag] = {sym: min(4, int(5 * i / n)) for i, (_, sym) in enumerate(werte)}
    return aus


def stufen_schaetzen(je_welt, f5, tage, zielgroesse="barriere") -> tuple:
    """TEIL A: je Fuenftel die Stufe - MIT TAGESKLAMMER und der Statistik
    der Zielgroesse.

    ⚠️⚠️⚠️ AM 24.09.2026 KOMPLETT ERSETZT - die erste Fassung war FALSCH,
    und R-R11 hat sie widerlegt.

    Sie rechnete (a) Mittelwerte statt der Statistik aus der Zielgroesse
    und (b) GEPOOLT ueber alle Anker statt je Tag geklammert. Ergebnis:
    die registrierten Stufen kamen um Faktor 2,3 (funding) und 3,3
    (turnover) zu GROSS heraus.

    ⚠️ Genau dieselbe Signatur steht im Kopf von
    `pruefe_n31_tagesklammer.je_tag_wirkung`: *„Das ist rund das
    3,8-fache ... derselbe Faktor bei beiden, die Signatur eines
    DEFINITIONSUNTERSCHIEDS. Gefunden hat es die Reproduktionskontrolle."*
    Dieselbe Falle, dieselbe Kontrolle, achtzehn Tage spaeter.

    ➤ JETZT WIRD DIE NORM BENUTZT statt nachgebaut: `je_tag_wirkung`
    rechnet je Tag `stat(frei) - stat(ALLE)` - gegen ALLE, nicht gegen
    die Gesperrten (auch das ein Faktor ~3,8, derselbe Kopf).

    Rueckgabe: (stufen, belegung) je Fuenftel.
    """
    import numpy as _np
    from pruefe_n31_tagesklammer import je_tag_wirkung as _jtw
    from messnorm import ZIELGROESSEN as _ZG

    stat = _ZG[zielgroesse].get("statistik", "median")
    tage_s = set(tage)
    stufen, belegung = [], []
    for k in range(5):
        # je Tag: die Anker DIESES Fuenftels als "frei", alle als Bezug -
        # genau die Form, die `je_tag_wirkung` erwartet
        # ⚠️⚠️ `je_tag_wirkung` rechnet `stat(y[~oben]) - stat(y)`, also
        # FREI gegen ALLE - und `oben` sind die GESPERRTEN. Fuer die Stufe
        # *dieses* Fuenftels muss es also umgekehrt belegt werden:
        # `oben = (Fuenftel != k)`, damit `~oben` genau das Fuenftel ist.
        # Wer hier `oben = (== k)` setzt, misst das SPERREN und bekommt
        # das Vorzeichen verkehrt.
        g = {}
        n = 0
        for tag in tage_s:
            rang = f5.get(tag)
            if not rang:
                continue
            zeilen = [(rang.get(x["sym"]), float(x["in_r"]))
                      for x in je_welt.get(tag, ())
                      if rang.get(x["sym"]) is not None]
            if len(zeilen) < 12:
                continue
            oben = _np.array([r != k for r, _ in zeilen], bool)
            y = _np.array([v for _, v in zeilen], float)
            if (~oben).sum() < 3 or oben.sum() < 1:
                continue
            g[tag] = (oben, y)
            n += int((~oben).sum())
        d = _jtw(g, stat) if g else {}
        stufen.append(100.0 * float(_np.mean(list(d.values()))) if d else 0.0)
        belegung.append(n)
    return stufen, belegung


def indikatorwelt(je_barriere, f5, fuenftel: int) -> dict:
    """Die Welt fuer TEIL B: Kennzahl = 1 im gesuchten Fuenftel, sonst 0.

    ⚠️ So waehlt `pruefe_auswahl` mit `menge='20%'` exakt dieses Fuenftel -
    ohne dass die Anlage nachgebaut werden muss.
    """
    aus = {}
    for tag, zeilen in je_barriere.items():
        rang = f5.get(tag)
        if not rang:
            continue
        z = [{"sym": x["sym"],
              "kennzahl": 1.0 if rang.get(x["sym"]) == fuenftel else 0.0,
              "in_r": x["in_r"]}
             for x in zeilen if rang.get(x["sym"]) is not None]
        if len(z) >= 12:
            aus[tag] = z
    return aus


def r_r11(reihen, zus, merkmale, H, ab, gesperrt) -> None:
    """R-R11: reproduziert das Werkzeug die REGISTRIERTEN Stufen?

    ⚠️⚠️ OHNE DIESEN NACHWEIS IST DAS N19-E-ERGEBNIS WERTLOS. Findet das
    Werkzeug auf `bewegung_r` NICHT die registrierten Stufen, dann liegt
    der Unterschied am WERKZEUG und nicht an der Zielgroesse - und die
    ganze Messung sagt nichts ueber den Zielgroessenbruch.

    DER WEG, genau wie die Stufen entstanden sind:

        1. die R-Wirkung je Fuenftel auf `bewegung_r` (das liefert
           `K.baue` als `in_r` - die Kursbewegung in Stopeinheiten)
        2. die Umrechnung `d(quote) = d(Potential) / (1 + CRV)`

    ⚠️ Schritt 2 ist die Umrechnung, die N19 als ueberschaetzend
    entlarvt hat. Sie wird hier BENUTZT, nicht geprueft - geprueft wird,
    ob damit die registrierten Zahlen herauskommen.
    """
    print("=" * 108)
    print("  R-R11: reproduziert das Werkzeug die REGISTRIERTEN Stufen?")
    print("  Weg: R-Wirkung auf `bewegung_r` (H%d), dann d(quote)=d(Pot)/(1+CRV)"
          % H)
    print("=" * 108)
    for kand, merkmal, live, name in merkmale:
        if kand == "zufall":
            continue
        try:
            je0 = K.baue(reihen, kand, zus.get(kand), horizont=H)
        except Exception as exc:                             # noqa: BLE001
            print("  %-22s -> %s" % (name[:22], str(exc)[:50]))
            continue
        if gesperrt:
            je0 = {t: [x for x in z if (t, x["sym"]) not in gesperrt]
                   for t, z in je0.items()}
            je0 = {t: z for t, z in je0.items() if z}
        f5 = fuenftel_je_tag(je0)
        je0 = {t: z for t, z in je0.items() if str(t)[:10] >= ab}
        tage = sorted(je0)
        # ⚠️ `stufen_schaetzen` liefert 100 x (Mittel - Gesamt). Auf
        # `bewegung_r` ist das die R-Wirkung in Hundertsteln; die
        # Umrechnung teilt durch (1+CRV).
        # ⚠️ Auf `bewegung_r` - deshalb MEDIAN, nicht Mittel. Die
        # Zielgroesse steuert die Statistik, nicht der Aufruf.
        roh, bel = stufen_schaetzen(je0, f5, tage,
                                    zielgroesse="bewegung_r")
        umger = [x / (1.0 + 2.0) for x in roh]
        print()
        print("  %s   (%d Tage)" % (name, len(tage)))
        print("    %-12s %s" % ("registriert",
                                " ".join("%+7.2f" % x for x in live)))
        print("    %-12s %s" % ("reproduziert",
                                " ".join("%+7.2f" % x for x in umger)))
        abw = [abs(a - b) for a, b in zip(live, umger)]
        vz = sum(1 for a, b in zip(live, umger) if (a > 0) == (b > 0))
        sp_l, sp_r = max(live) - min(live), max(umger) - min(umger)
        print("    ➤ Vorzeichen gleich in %d von 5 · Spanne %.2f gegen %.2f "
              "(Verhaeltnis %.2f) · groesste Abweichung %.2f Pkt"
              % (vz, sp_l, sp_r, sp_r / max(sp_l, 1e-9), max(abw)))
        print("    ➤ %s"
              % ("✔ REPRODUZIERT - Vorzeichen alle gleich, Spanne auf 30 % genau"
                 if vz == 5 and 0.7 <= sp_r / max(sp_l, 1e-9) <= 1.43
                 else "⚠️ TEILWEISE - Ordnung stimmt, Hoehe weicht ab"
                 if vz >= 4
                 else "⛔ NICHT REPRODUZIERT - das Werkzeug misst etwas anderes"))
    print()


def _wert(flag, vorgabe):
    a = sys.argv
    return a[a.index(flag) + 1] if flag in a else vorgabe


def main() -> int:
    hor_arg = _wert("--horizont", None)
    achse = ACHSE if "--achse" in sys.argv else (
        (int(hor_arg),) if hor_arg else (3,))
    ohne_f4 = "--mit-fuenftel4" not in sys.argv
    saat = int(_wert("--saat", "20260909"))
    ab = _wert("--ab", "2023-01-01")

    lage = N.Lage(instrument="hebel", strategie="einstieg", simuliert=True)
    print("=" * 108)
    print("N19-E NORMGERECHT - die Stufen direkt gegen die BARRIEREN-Quote")
    print("=" * 108)
    print("  %s" % N.standardzeile())
    print("  %s" % messmenge.zeile())
    print("  Lage: %s · Zielgroesse: %s"
          % (lage, N.ZIELGROESSE_JE_LAGE[("hebel", "einstieg")]))
    print("  ⚠️ NUR LONG - `barriere_je_reihe` kennt kein `ist_short`; "
          "2.435-richtung belegt, dass SHORT sich anders verhaelt.")
    print("  ⚠️ NUR KRYPTO (Nutzervorgabe) · Fenster ab %s · Saat %d" % (ab, saat))
    print("  Achse: %s%s" % ("/".join("H%d" % h for h in achse),
                             "" if ohne_f4 else "   ⚠️ MIT Fuenftel 4 (Gegenprobe)"))
    print()

    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    merkmale = merkmale_aus_register()
    # ⚠️⚠️⚠️ DIE KONTROLLE IST PFLICHT, NICHT KUER (Vorabfestlegung § 4).
    #
    # Ohne sie ist nicht zu unterscheiden, ob "kleine, instabile Stufen"
    # ein BEFUND ueber die Merkmale ist - oder schlicht das, was diese
    # Anlage bei JEDEM beliebigen Merkmal ausgibt. `zufall` traegt keine
    # Information; was dort herauskommt, ist der Massstab fuer alles andere.
    if "--ohne-kontrolle" not in sys.argv:
        merkmale = merkmale + [("zufall", "zufall_fuenftel",
                                (0.0,) * 5, "KONTROLLE zufall")]
    print("  Merkmale aus dem Register: %s"
          % ", ".join(m[3] for m in merkmale))

    # ---- die von Stufe 6 gesperrten Anker, EINMAL bestimmt -------------
    gesperrt = set()
    if ohne_f4:
        _oi = K.baue(reihen, "oi_aenderung", zus.get("oi_aenderung"),
                     horizont=max(achse))
        for tag, zeilen in _oi.items():
            werte = sorted(float(x["kennzahl"]) for x in zeilen)
            if len(werte) < 5:
                continue
            grenze = werte[int(round(0.8 * (len(werte) - 1)))]
            for x in zeilen:
                if float(x["kennzahl"]) >= grenze:
                    gesperrt.add((tag, x["sym"]))
        print("  ⚠️ Trichterstufe 6: %d Anker gesperrt (oberstes OI-Fuenftel, "
              "2.576)" % len(gesperrt))
    print()

    if "--r-r11" in sys.argv:
        r_r11(reihen, zus, merkmale, achse[0], ab, gesperrt)
        print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
        return 0

    for H in achse:
        print("=" * 108)
        print("  HORIZONT H%d   (Blocklaenge %d aus messnorm._block)"
              % (H, N._block(H)))
        print("=" * 108)
        for kand, merkmal, live, name in merkmale:
            try:
                je0 = K.baue(reihen, kand, zus.get(kand), horizont=H)
            except Exception as exc:                         # noqa: BLE001
                print("  %-22s -> %s" % (name[:22], str(exc)[:50]))
                continue
            if gesperrt:
                je0 = {t: [x for x in z if (t, x["sym"]) not in gesperrt]
                       for t, z in je0.items()}
                je0 = {t: z for t, z in je0.items() if z}
            f5 = fuenftel_je_tag(je0)
            je, anteil = K1C.barriere_je_tag(je0, reihen, H)
            je = {t: z for t, z in je.items() if str(t)[:10] >= ab}
            if not je:
                print("  %-22s -> leere Welt" % name[:22])
                continue
            tage = sorted(je)
            mitte = tage[len(tage) // 2]
            erste = [t for t in tage if t < mitte]
            zweite = [t for t in tage if t >= mitte]

            # ---- TEIL A: schaetzen auf der ERSTEN Haelfte --------------
            st_a, bel_a = stufen_schaetzen(je, f5, erste)
            st_b, bel_b = stufen_schaetzen(je, f5, zweite)
            print()
            print("  %s   (%d Tage, %.1f %% geloest, Split %s)"
                  % (name, len(tage), 100 * anteil, mitte))
            print("    %-10s %s" % ("heute",
                                    " ".join("%+7.2f" % x for x in live)))
            print("    %-10s %s   <- TEIL A, erste Haelfte"
                  % ("N19-E", " ".join("%+7.2f" % x for x in st_a)))
            print("    %-10s %s   <- zweite Haelfte (B6)"
                  % ("", " ".join("%+7.2f" % x for x in st_b)))
            print("    %-10s %s" % ("Belegung",
                                    " ".join("%7d" % x for x in bel_a)))
            sp_live = max(live) - min(live)
            sp_neu = max(st_a) - min(st_a)
            if sp_live <= 0:      # die Kontrolle hat keine registrierten Stufen
                print("    ⚠️ KONTROLLE - hier gibt es nichts zu vergleichen. "
                      "Was hier herauskommt, ist der MASSSTAB fuer oben.")
            gleich = sum(1 for a, b in zip(live, st_a)
                         if (a > 0) == (b > 0))
            print("    ➤ Spanne %.2f gegen %.2f (Faktor %s) · Vorzeichen "
                  "gleich in %d von 5 · Haelften gleiches Vorzeichen in %d von 5"
                  % (sp_live, sp_neu,
                     ("%.2f" % (sp_neu / sp_live)) if sp_live > 0 else "-",
                     gleich,
                     sum(1 for a, b in zip(st_a, st_b) if (a > 0) == (b > 0))))

            # ---- TEIL B: jedes Fuenftel normgerecht --------------------
            print("    TEIL B - normgerecht je Fuenftel (selektierte Menge)")
            print("      ⚠️ Wirkung = SPERREN dieses Fuenftels. POSITIV heisst "
                  ",Sperren hilft` = Fuenftel schlecht;")
            print("         NEGATIV heisst ,Sperren schadet` = Fuenftel gut. "
                  "Spiegelbildlich zu Teil A.")
            for f in range(5):
                welt = indikatorwelt(je, f5, f)
                if len(welt) < 30:
                    print("      Fuenftel %d -> zu wenige Tage (%d)"
                          % (f, len(welt)))
                    continue
                try:
                    b = MA.pruefe_auswahl(
                        "%s_f%d" % (kand, f), welt, mom, lage=lage,
                        menge="20%", rng=np.random.default_rng(saat),
                        horizont=H, hypothese="N19-E Stufen",
                        verwendung="Beitrag", zielgroesse="barriere")
                except Exception as exc:                     # noqa: BLE001
                    print("      Fuenftel %d -> %s" % (f, str(exc)[:60]))
                    continue
                deut = ("Fuenftel SCHLECHT" if b.wirkung > 0
                        else "Fuenftel GUT" if b.wirkung < 0 else "-")
                print("      Fuenftel %d  %+8.4f [%+.4f .. %+.4f]  %4d Tage "
                      "%3d Bloecke  %-22s %s"
                      % (f, b.wirkung, b.unten, b.oben, b.n_tage,
                         b.n_bloecke, K1C.kurz(b.urteil), deut))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    print()
    print("  ⚠️ TEIL A ist eine ZAEHLUNG, kein Urteil. Was traegt, sagt TEIL B.")
    print("  ⚠️ `hebel` hat in der Produktion NULL Signale - alles SIMULIERT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
