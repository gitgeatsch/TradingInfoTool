# -*- coding: utf-8 -*-
"""Phase 4, Punkt 2c — WELCHE HEBEL FALLEN AN?

## ⚠️⚠️ Die Planfrage war halb tautologisch

Sie lautet *„welche Hebel fallen an, liegen sie in 2-5x"*. Der zweite
Teil kann per Konstruktion gar nicht anders ausgehen: `hebel_ab` 2,0
schiebt alles Kleinere nach Spot, `hebel_grenze` 5,0 deckelt alles
Groessere. Die 16 echten Hebelsignale seit dem 12.09. liegen deshalb
zwangslaeufig zwischen 2,2x und 5,0x.

➔ Die Frage, die etwas entscheidet, ist die nach der **Kennlinie**:

    WO liegt die Schwelle, ab der aus einer Quote ein Hebel wird?
    WO faengt der Deckel an zu binden?
    WIE BREIT ist das Fenster dazwischen - und wovon haengt es ab?

## ⚠️⚠️⚠️ DAS KAPITAL IST EINE ACHSE, UND SIE FEHLT IM PLAN

`nominal = r x Kapital / Stopabstand`, `hebel = nominal / Hebelnenner`.
Der Hebel haengt damit **linear am Kapital** - bei gleicher Quote und
gleichem Stop ergibt doppeltes Kapital den doppelten Hebel. Eine
Kennlinie ohne diese Achse beschreibt einen einzigen Kontostand.

## Was NICHT gemessen werden kann, und warum

Gespeichert wird in `signals` nur der GEDECKELTE `hebel`. `hebel_roh`,
`grenze_greift`, `aggregat_greift` und `liquidation_greift` rechnet
`betraege.hebelrechnung` aus und gibt sie zurueck - **geschrieben wird
keines davon**. Auch die Quote `q` steht nirgends; nur `potential_r`.

⚠️ Deshalb ist die REALE Verteilung am Betrieb heute nicht auswertbar,
sondern nur die Kennlinie der Rechnung. Das ist dieselbe Klasse wie
2.459-ungemessen: die Zahl existiert im Lauf und fehlt in der Ablage.

⚠️ Gerechnet wird mit dem ECHTEN Code (`betraege.hebelrechnung`, rein -
ohne DB, Uhr oder Netz) und den LAUFENDEN Einstellungen aus
`config.yaml`, nicht mit den Code-Vorgaben: dort steht `aktiv: False`,
laufend ist `true` (2.494-hebel-aktiv-live).

    python phase4_2c_hebelverteilung.py
"""
from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import config as _config                                   # noqa: E402
from agent import betraege as B                            # noqa: E402

# ⚠️ Das Kapital aus einem ECHTEN Signal zurueckgerechnet, nicht geraten:
# BEAMX 20.09., hebel 2,5125 · Einsatz 500 EUR · Verlust am Stop 170,78
# EUR -> Stopabstand 13,60 %, Risiko 170,78 EUR. Mit dem in 2.446-zahlen
# dokumentierten Kapital 17.987 EUR ergibt das r = 0,95 % - innerhalb der
# Klammer 0,50 bis 1,25 %, also stimmig.
KAPITAL_EUR = 17987.0
CRV = 2.0
QUOTEN = (0.34, 0.36, 0.38, 0.40, 0.45, 0.50, 0.55, 0.60)
STOPS = (0.05, 0.08, 0.12, 0.17, 0.25)
KAPITALE = (5000.0, 10000.0, 17987.0, 30000.0)


def _einstellungen() -> dict:
    """Die LAUFENDEN Werte, nicht die Code-Vorgaben."""
    cfg = _config.load_config() or {}
    e = ((cfg.get("rollen_kette") or {}).get("hebel_aus_quote") or {})
    return {k: v for k, v in e.items() if k in B.HEBEL_AUS_QUOTE_VORGABE}


def _rechne(q, stop, kapital, e):
    try:
        return B.hebelrechnung(quote=q, crv=CRV, kapital_eur=kapital,
                               stop_rel=stop, einstellungen=e)
    except Exception as exc:                                # noqa: BLE001
        return {"fehler": str(exc)[:40]}


def main() -> int:
    e = _einstellungen()
    ab, grenze = e.get("hebel_ab", 2.0), e.get("hebel_grenze", 5.0)
    print("=" * 104)
    print("PHASE 4 · PUNKT 2c - DIE KENNLINIE DES HEBELS")
    print("=" * 104)
    print("  Laufende Einstellungen: %s"
          % ", ".join("%s=%s" % (k, v) for k, v in sorted(e.items())))
    print("  CRV %.1f · Hebelnenner %s EUR · Klammer r %s bis %s"
          % (CRV, e.get("hebelnenner_eur"), e.get("r_min"), e.get("r_max")))
    print("  ⚠️ `hebel_ab` %.1f und `hebel_grenze` %.1f ERZWINGEN die Zone "
          "2-5x - dass die Werte dort" % (ab, grenze))
    print("     liegen, ist keine Aussage. Gefragt ist, WO die Schwelle "
          "und WO der Deckel greift.")
    print()

    # ---- 1  Kennlinie ueber Quote x Stopweite, echtes Kapital ---------
    print("-" * 104)
    print("  1) HEBEL ueber QUOTE x STOPWEITE, Kapital %s EUR"
          % ("%.0f" % KAPITAL_EUR))
    print("-" * 104)
    print("     %-7s %s" % ("Quote", "".join("%10s" % ("Stop %.0f%%" % (100 * s))
                                             for s in STOPS)))
    for q in QUOTEN:
        zellen = []
        for stop in STOPS:
            a = _rechne(q, stop, KAPITAL_EUR, e)
            if "fehler" in a:
                zellen.append("%10s" % "-")
                continue
            if not a["ist_hebel"]:
                zellen.append("%10s" % "SPOT")
            elif a["grenze_greift"]:
                zellen.append("%10s" % ("%.1f!" % a["hebel"]))
            else:
                zellen.append("%10.2f" % a["hebel"])
        print("     %-7.2f %s" % (q, "".join(zellen)))
    print("     SPOT = unter `hebel_ab`, wird Spot · ! = am Deckel "
          "`hebel_grenze`")
    print()

    # ---- 2  Wo kippt es? Die Schwellen je Stopweite -------------------
    print("-" * 104)
    print("  2) DIE SCHWELLEN - ab welcher Quote wird es ein Hebel, ab "
          "welcher bindet der Deckel?")
    print("-" * 104)
    print("     %-10s %14s %14s %14s" % ("Stopweite", "Hebel ab q",
                                         "Deckel ab q", "Fensterbreite"))
    for stop in STOPS:
        ab_q = deckel_q = None
        q = 0.3005
        while q < 0.95:
            a = _rechne(q, stop, KAPITAL_EUR, e)
            if "fehler" not in a:
                if ab_q is None and a["ist_hebel"]:
                    ab_q = q
                if deckel_q is None and a.get("grenze_greift"):
                    deckel_q = q
                    break
            q += 0.0005
        breite = ("%.4f" % (deckel_q - ab_q)) if (ab_q and deckel_q) else "-"
        print("     %-10s %14s %14s %14s"
              % ("%.0f %%" % (100 * stop),
                 ("%.4f" % ab_q) if ab_q else "nie",
                 ("%.4f" % deckel_q) if deckel_q else "nie", breite))
    print("     ⚠️ Die Fensterbreite ist der Quotenbereich, in dem der "
          "Hebel ueberhaupt STEUERT -")
    print("        darunter Spot, darueber immer 5x. Ist er schmal, ist "
          "der Hebel ein Schalter,")
    print("        kein Regler.")
    print()

    # ---- 2b  ⚠️⚠️ WARUM DAS FENSTER SO SCHMAL IST: die KLAMMER -------
    #
    # Verdacht nach Tabelle 1: `r` klebt an der Klammer, und dann haengt
    # der Hebel nur noch an Stop und Kapital - nicht mehr an der Quote.
    # Das gehoert GERECHNET, nicht behauptet.
    print("-" * 104)
    print("  2b) DIE URSACHE - wo klebt `r` an der Klammer?")
    print("-" * 104)
    print("     %-8s %12s %12s %12s %10s"
          % ("Quote", "Kelly", "halbes K.", "r (geklammert)", "Klammer"))
    for q in (0.3340, 0.3400, 0.3450, 0.3500, 0.3600, 0.4000, 0.5000):
        a = _rechne(q, 0.12, KAPITAL_EUR, e)
        if "fehler" in a:
            continue
        print("     %-8.4f %12.6f %12.6f %12.6f %10s"
              % (q, a["kelly"], a["kelly_halb"], a["r"], a["klammer"]))
    print("     ⚠️ Sobald `r` an `r_max` klebt, ist die Quote OHNE WIRKUNG "
          "auf die Hoehe -")
    print("        sie entscheidet nur noch, OB ein Hebel entsteht.")
    print()

    # ---- 3  Die Kapitalachse ------------------------------------------
    print("-" * 104)
    print("  3) ⚠️⚠️ DIE KAPITALACHSE - `hebel` haengt LINEAR am Kapital")
    print("-" * 104)
    print("     %-10s %s" % ("Stopweite",
                             "".join("%14s" % ("%.0f EUR" % k)
                                     for k in KAPITALE)))
    for stop in STOPS:
        z = []
        for kap in KAPITALE:
            ab_q = None
            q = 0.3005
            while q < 0.95:
                a = _rechne(q, stop, kap, e)
                if "fehler" not in a and a["ist_hebel"]:
                    ab_q = q
                    break
                q += 0.0005
            z.append("%14s" % (("q>=%.3f" % ab_q) if ab_q else "nie"))
        print("     %-10s %s" % ("%.0f %%" % (100 * stop), "".join(z)))
    print("     ⚠️ Bei kleinem Kapital entsteht ueberhaupt kein Hebel - "
          "dieselbe Quote, andere Antwort.")
    print()

    # ---- 4  ⚠️⚠️ DIE BINDUNG AN DIE ECHTEN SIGNALE -------------------
    #
    # Eine Kennlinie, die die 16 echten Hebelsignale nicht erklaert, hat
    # einen Faktor vergessen. Aus `hebel`, `position_size_eur` und
    # `verlust_am_stop_eur` laesst sich der Stopabstand und das Risiko
    # zurueckrechnen, daraus `r` und daraus die implizite QUOTE - die
    # nirgends gespeichert ist. Liegt sie im schmalen Fenster, passt die
    # Kennlinie; liegt sie darueber, fehlt etwas (Liquidationsdeckel,
    # Aggregat oder ein anderes Kapital).
    import os as _os
    import sqlite3 as _sq
    _db = None
    _a = sys.argv[1:]
    if "--db" in _a:
        _db = _a[_a.index("--db") + 1]
    if not _db or not _os.path.exists(_db):
        print("-" * 104)
        print("  4) BINDUNG AN DIE ECHTEN SIGNALE - uebersprungen "
              "(kein --db <sicherung.db>)")
        print("-" * 104)
        print()
        return 0
    print("-" * 104)
    print("  4) ⚠️⚠️ BINDUNG - erklaert die Kennlinie die ECHTEN Signale?")
    print("-" * 104)
    c = _sq.connect("file:%s?mode=ro" % _db.replace("\\", "/"), uri=True)
    print("     %-8s %-12s %8s %8s %9s %9s %s"
          % ("Symbol", "Tag", "Hebel", "Stop", "Risiko", "r", "implizite q"))
    _drin = _aus = 0
    _werte = []
    for sym, tag, heb, pos, verl in c.execute(
            "SELECT symbol, substr(created_at,1,10), hebel, "
            "       position_size_eur, verlust_am_stop_eur FROM signals "
            " WHERE instrument='hebel' AND hebel IS NOT NULL "
            "   AND verlust_am_stop_eur IS NOT NULL ORDER BY created_at"):
        if not (heb and pos and verl):
            continue
        stop = verl / (pos * heb)
        r = verl / KAPITAL_EUR
        # halbes Kelly = r  ->  Kelly = 2r  ->  q = (2r*crv + 1)/(1+crv)
        q = (2.0 * r * CRV + 1.0) / (1.0 + CRV)
        im_fenster = 0.3330 <= q <= 0.3520
        _werte.append((q, stop, heb, r))
        _drin += int(im_fenster)
        _aus += int(not im_fenster)
        print("     %-8s %-12s %8.3f %7.1f%% %9.2f %9.5f %9.4f %s"
              % (sym, tag, heb, 100 * stop, verl, r, q,
                 "" if im_fenster else "⚠️ ausserhalb"))
    print("     ➤ %d von %d liegen im dynamischen Fenster [0,3330 .. "
          "0,3520]" % (_drin, _drin + _aus))
    # ⚠️⚠️ WOHER KOMMT DIE STREUUNG DER HEBEL? Aus der Quote oder aus dem
    # Stop? `hebel = r x Kapital / (Stop x Nenner)` - beide Faktoren
    # koennen streuen. Das gehoert gerechnet, nicht geschaetzt.
    if _werte:
        _q = [x[0] for x in _werte]
        _st = [x[1] for x in _werte]
        _hb = [x[2] for x in _werte]
        _r = [x[3] for x in _werte]
        def _sp(v):
            return (max(v) / min(v)) if min(v) > 0 else float("nan")
        print()
        print("     ZERLEGUNG DER STREUUNG (Verhaeltnis groesster zu "
              "kleinstem Wert):")
        print("       Quote  %.4f bis %.4f  -> Faktor %.2f"
              % (min(_q), max(_q), _sp(_q)))
        print("       r      %.5f bis %.5f -> Faktor %.2f"
              % (min(_r), max(_r), _sp(_r)))
        print("       Stop   %.1f %% bis %.1f %%  -> Faktor %.2f"
              % (100 * min(_st), 100 * max(_st), _sp(_st)))
        print("       HEBEL  %.2f bis %.2f    -> Faktor %.2f"
              % (min(_hb), max(_hb), _sp(_hb)))
        print("     ➤ Die Quote streut um Faktor %.2f, der Stop um %.2f - "
              "der Hebel folgt dem STOP." % (_sp(_q), _sp(_st)))
    print("     ⚠️ Die Quote ist NICHT gespeichert - sie ist hier "
          "zurueckgerechnet, unter der Annahme")
    print("        Kapital %s EUR und r ungeklammert. Ein Wert am Rand "
          "kann auch heissen, dass" % ("%.0f" % KAPITAL_EUR))
    print("        die Klammer oder ein Deckel gegriffen hat.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
