# -*- coding: utf-8 -*-
"""⚠️⚠️ VORABFESTLEGUNG — geschrieben VOR dem Lauf (21.09.2026).

WAS KOSTET ES, DIE ASSET-EIGENSCHAFT AUS DEM HEBEL ZU NEHMEN?

Nutzerauftrag: *„unternimm alles um eine Loesung herbeizufuehren."*
Ohne diese Zahl waere jede Empfehlung von mir eine Meinung mit
Messungen drumherum.

═══════════════════════════════════════════════════════════════════════
 WAS SCHON GEMESSEN IST - und deshalb hier NICHT wiederholt wird
═══════════════════════════════════════════════════════════════════════

Auf der registrierten Basis (SplyCur, 2.756 Tage, H20):

    GESAMT       +0,0904 R   die heutige Form
    EIGENSCHAFT  +0,0754 R   traegt 3/3, dominiert
    LAGE         +0,0338 R   traegt 2/3, nicht robust

Die Groesse der Einbusse ist damit bekannt: rund **37 Prozent** der
Wirkung bliebe. Offen ist etwas anderes, und das ist die eigentliche
Frage:

    Reicht das, um einen HEBEL zu stufen?

═══════════════════════════════════════════════════════════════════════
 DIE ZWEI MESSUNGEN, DIE DAS BEANTWORTEN
═══════════════════════════════════════════════════════════════════════

**A - DIE STUFENTABELLE.** Was traete konkret an die Stelle von
(+3,15 / +0,83 / +0,22 / -1,79 / -2,40)? Gerechnet mit DERSELBEN
Mechanik wie `rechne_turnover_beitrag` (Fuenftel-Median je Tag, gegen
den Gesamtschnitt, mal 100/(1+CRV), halbiert wegen In-Sample), auf der
REGISTRIERTEN Basis.

    Vorabfestlegung: die Tabelle der LAGE ist brauchbar, wenn sie
    (1) MONOTON faellt wie die registrierte und
    (2) eine Spanne hat, die im Hebel ankommt - Kriterium unter B.

**B - WAS DAVON IM HEBEL ANKOMMT.** Die Stufen gehen ueber den Zuschlag
in die Quote und von dort ueber halbes Kelly in den Hebelbetrag. Die
Kette ist NICHT linear: `hebel_ab` 2,0 und `hebel_grenze` 5,0 kappen
oben und unten, und die Klammer 0,5 bis 1,25 Prozent kappt `r`.

    Gerechnet mit der ECHTEN `betraege.hebelrechnung` - rein, ohne DB,
    Uhr oder Netz. Keine Nachbildung.

    Vorabfestlegung: die Lage-Tabelle reicht, wenn die Spanne der
    HEBEL zwischen bestem und schlechtestem Fuenftel mindestens EINE
    Hebelstufe betraegt. Ist sie kleiner, waere der Beitrag im Hebel
    folgenlos - und ein folgenloser Beitrag ist keiner.

═══════════════════════════════════════════════════════════════════════
 WAS DIESE MESSUNG NICHT KANN
═══════════════════════════════════════════════════════════════════════

⚠️ Sie sagt NICHT, ob der Hebel mit der Lage BESSER waere. Sie sagt, ob
er ueberhaupt noch stuft. Ob das Weglassen der Eigenschaft nuetzt, ist
eine Frage an die Zukunft und mit dieser Basis nicht zu beantworten -
meine drei fachlichen Gruende dafuer (Modellrisiko-Konzentration,
Inkonsistenz im Beitragssatz, Stabilitaetsannahme) bleiben ARGUMENTE.

⚠️ IN-SAMPLE, wie das Original: dieselben Daten, aus denen das Urteil
kommt. Deshalb halbiert - dieselbe Vorsicht wie dort.

    python phase4_c_was_kostet_der_schnitt.py
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

import agent.betraege as BE                                # noqa: E402
import agent.wahrscheinlichkeit as WA                      # noqa: E402
import messe_bewertungskennzahl as MB                      # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402
import phase4_c_zerlegung_auf_registrierter_basis as ZR    # noqa: E402

CRV = 2.0
MIND_JE_TAG = 15
RUECKBLICK = 60
# ⚠️ Der Arbeitspunkt des Betriebs, nicht erfunden: Kapital und Stop aus
# der laufenden Konfiguration bzw. dem gemessenen Median.
KAPITAL = 10000.0
STOP_REL = 0.08          # 8 % - der gemessene Gipfel (Stopweite-Befund)


def tabelle(je_tag: dict, crv: float = CRV):
    """Fuenftel-Stufen - dieselbe Rechnung wie `rechne_turnover_beitrag`."""
    sammel = {k: [] for k in range(5)}
    tage = 0
    for _t, z in je_tag.items():
        if len(z) < MIND_JE_TAG:
            continue
        tage += 1
        w = np.array([x["kennzahl"] for x in z])
        y = np.array([x["in_r"] for x in z])
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        for k in range(5):
            m = (r >= k / 5) & (r < (k + 1) / 5 if k < 4 else r <= 1.0)
            if m.sum() >= 2:
                sammel[k].append(float(np.median(y[m])))
    if not tage or any(not sammel[k] for k in range(5)):
        return None, 0
    werte = [st.mean(sammel[k]) for k in range(5)]
    mittel = st.mean(werte)
    f = 1.0 / (1.0 + crv)
    return [round(100.0 * (werte[k] - mittel) * f / 2.0, 2)
            for k in range(5)], tage


def monoton(s) -> bool:
    return all(s[i] >= s[i + 1] for i in range(4))


def hebel_je_stufe(stufen, uebrige_punkte=0.0):
    """Was kommt von der Tabelle im HEBELBETRAG an? Echte Funktion."""
    basis = 1.0 / (1.0 + CRV)
    aus = []
    for p in stufen:
        q = basis + (p + uebrige_punkte) / 100.0
        try:
            h = BE.hebelrechnung(quote=q, crv=CRV, kapital_eur=KAPITAL,
                                 stop_rel=STOP_REL)
        except Exception as exc:                           # noqa: BLE001
            aus.append((q, None, str(exc)[:40]))
            continue
        aus.append((q, h, ""))
    return aus


def main() -> int:
    print("=" * 108)
    print("WAS KOSTET ES, DIE ASSET-EIGENSCHAFT AUS DEM HEBEL ZU NEHMEN?")
    print("=" * 108)
    reg = next((b.stufen for b in WA.BEITRAEGE
                if b.merkmal == "turnover_fuenftel"), None)
    print("  registriert: %s"
          % ", ".join("%+.2f" % x for x in (reg or ())))
    reihen = B.lade()
    splycur = MB.reihe("data/onchain_historie.db", "splycur")
    log_u = ZR.log_umschlag(reihen, splycur)
    asset, lage = {}, {}
    for s, d in log_u.items():
        t = sorted(d)
        if len(t) < RUECKBLICK + 200:
            continue
        for i in range(RUECKBLICK, len(t)):
            m = st.mean([d[t[j]] for j in range(i - RUECKBLICK, i)])
            asset.setdefault(s, {})[t[i]] = m
            lage.setdefault(s, {})[t[i]] = d[t[i]] - m

    # ---- A  DIE STUFENTABELLEN ---------------------------------------
    print()
    print("-" * 108)
    print("  A) DIE STUFENTABELLE - was traete an die Stelle der "
          "registrierten Zeile?")
    print("-" * 108)
    print("  %-14s %3s %6s %7s %7s %7s %7s %7s  %7s  %s"
          % ("Groesse", "H", "Tage", "F0", "F1", "F2", "F3", "F4",
             "Spanne", "Form"))
    tab = {}
    for H in (5, 10, 20):
        for name, quelle in (("GESAMT", log_u), ("EIGENSCHAFT", asset),
                             ("LAGE", lage)):
            je = K.baue(reihen, "turnover_markt", quelle, horizont=H)
            s, tage = tabelle(je)
            if s is None:
                print("  %-14s %3d -> zu wenige Tage" % (name, H))
                continue
            tab[(name, H)] = s
            print("  %-14s %3d %6d %+7.2f %+7.2f %+7.2f %+7.2f %+7.2f  "
                  "%7.2f  %s"
                  % (name, H, tage, s[0], s[1], s[2], s[3], s[4],
                     s[0] - s[4],
                     "MONOTON" if monoton(s) else "⚠️ nicht monoton"))
        print()

    # ---- B  WAS DAVON IM HEBEL ANKOMMT -------------------------------
    print("-" * 108)
    print("  B) WAS KOMMT IM HEBELBETRAG AN? - echte "
          "`betraege.hebelrechnung`, CRV %.1f, Stop %.0f %%, Kapital "
          "%.0f EUR" % (CRV, 100 * STOP_REL, KAPITAL))
    print("-" * 108)
    print("  ⚠️ Die Kette ist NICHT linear: `hebel_ab` und "
          "`hebel_grenze` kappen, und die")
    print("     Klammer 0,5 bis 1,25 Prozent kappt `r`. Deshalb wird "
          "gerechnet, nicht geschaetzt.")
    print()
    print("  %-22s %8s %8s %8s %8s %8s   %s"
          % ("Tabelle", "F0", "F1", "F2", "F3", "F4", "Hebelspanne"))
    zeilen = [("registriert (H20)", list(reg or ()))]
    for name in ("GESAMT", "EIGENSCHAFT", "LAGE"):
        if (name, 20) in tab:
            zeilen.append(("%s (H20)" % name, tab[(name, 20)]))
    for titel, stufen in zeilen:
        if not stufen:
            continue
        erg = hebel_je_stufe(stufen)
        hs = []
        txt = []
        for q, h, fehler in erg:
            if h is None:
                txt.append("  -   ")
                continue
            hs.append(h["hebel"])
            txt.append("%5.2fx" % h["hebel"])
        spanne = (max(hs) - min(hs)) if hs else 0.0
        print("  %-22s %8s %8s %8s %8s %8s   %.2f Stufen%s"
              % (titel, txt[0], txt[1], txt[2], txt[3], txt[4], spanne,
                 "  ⚠️ unter EINER Stufe - im Hebel folgenlos"
                 if spanne < 1.0 else ""))
    print()
    print("  ⚠️ VORABFESTLEGUNG (Skriptkopf): die Lage-Tabelle reicht, "
          "wenn die Hebelspanne")
    print("     zwischen bestem und schlechtestem Fuenftel MINDESTENS "
          "EINE Stufe betraegt.")
    print("     Ein Beitrag, der im Hebel folgenlos ist, ist keiner.")
    print()
    print("  ⚠️ WAS DIESE MESSUNG NICHT SAGT: ob der Hebel mit der Lage "
          "BESSER waere.")
    print("     Sie sagt, ob er ueberhaupt noch stuft. In-Sample und "
          "halbiert, wie das Original.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
