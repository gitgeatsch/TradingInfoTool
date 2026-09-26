# -*- coding: utf-8 -*-
"""Womit trennt man RICHTUNG von BEWEGUNG? - geeicht an einer Simulation

**26.09.2026** · Vorabfestlegung 19 · Nutzerauftrag *"sauber konstruieren,
testen und simulieren"*.

═══════════════════════════════════════════════════════════════════════
 WARUM DAS NOETIG IST
═══════════════════════════════════════════════════════════════════════

Die registrierte Regel (2.594) lautet: wer ein gerichtetes EREIGNIS misst,
muss das gespiegelte mitmessen; Schwelle Verhaeltnis >= 1,30 oder <= 0,77.

    ⛔ MANGEL 1  Ich habe sie am 25./26.09. auf `E[R]` angewandt statt auf
                 ein Ereignis. Long- und Short-`E[R]` sind auf denselben
                 Ankern STRUKTURELL gegenlaeufig - ein garantiert
                 richtungsfreies Merkmal liefert dasselbe Vorzeichenmuster
                 wie ein reines Richtungsmerkmal. Nachgewiesen.

    ⚠️ MANGEL 2  Die Schwelle 1,30 ist nicht geeicht. Auf echten Daten
                 erreicht ein garantiert richtungsfreies Merkmal
                 (|kuenftige Bewegung|) ein Verhaeltnis von 2,57 und waere
                 als *Richtung* durchgegangen.

⚠️⚠️ Und Mangel 2 ist auf echten Daten NICHT zu beheben: ein Merkmal, das
garantiert nur Bewegung misst, gibt es dort nicht - grosse Kryptobewegungen
sind haeufiger nach oben, also steckt ueberall Richtung drin.

➤ Deshalb eine SIMULATION: nur dort ist die Wahrheit gesetzt.

═══════════════════════════════════════════════════════════════════════
 DIE KONSTRUKTION
═══════════════════════════════════════════════════════════════════════

    r(t) = drift(gruppe) + sigma(gruppe) * z(t)

    BEWEGUNG-Welt   drift = 0 fuer ALLE, sigma variiert
    RICHTUNG-Welt   sigma gleich fuer ALLE, drift variiert
    GEMISCHT        beides, in bekanntem Verhaeltnis (Dosis-Wirkung)

Das Merkmal ist die GRUPPENNUMMER - es ordnet per Konstruktion genau das,
was variiert wurde, und nichts sonst.

⚠️ Die Barrierengeometrie ist dieselbe wie im Betrieb (k x ATR, geklammert,
Stop zuerst) - sonst gaelte die Eichung fuer eine andere Geometrie als die
Anwendung.

    python pruefe_spiegelprobe.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_hebel_geometrie_neutral as GG                      # noqa: E402

CRV, H, K = 1.5, 6, 1.0
GRUPPEN = 5
REIHEN_JE_GRUPPE = 12
LAENGE = 4000
ZIEHUNGEN = 40
SAAT = 20260926
#: Dosis: Anteil Richtung an der Gesamtstreuung der Gruppen
DOSEN = (0.0, 0.25, 0.5, 0.75, 1.0)


def welt(rng, richtungsanteil):
    """-> (close-Reihen, Gruppennummer je Reihe).

    `richtungsanteil` 0 = reine BEWEGUNG, 1 = reine RICHTUNG.
    Die Gruppen unterscheiden sich in `sigma` (Bewegung) und/oder `drift`
    (Richtung); die Gesamtspreizung bleibt vergleichbar.
    """
    reihen, gruppe = [], []
    # Basiswerte so gewaehlt, dass die Barrieren in vernuenftiger Haeufigkeit
    # ansprechen - sonst misst man nur leere Zellen.
    for g in range(GRUPPEN):
        t = g / (GRUPPEN - 1.0) - 0.5              # -0,5 .. +0,5
        sigma = 0.010 * (1.0 + 0.8 * t * (1.0 - richtungsanteil))
        drift = 0.0015 * t * richtungsanteil
        for _ in range(REIHEN_JE_GRUPPE):
            r = drift + sigma * rng.standard_normal(LAENGE)
            reihen.append(100.0 * np.exp(np.cumsum(r)))
            gruppe.append(g)
    return reihen, np.array(gruppe)


def lifts(reihen, gruppe):
    """-> (lift_hoch, lift_runter) auf dem Ereignis ZIEL erreicht."""
    zl, zs, gg = [], [], []
    for c, g in zip(reihen, gruppe):
        # High/Low aus dem Pfad naehern: die Stundenspanne ist hier nicht
        # modelliert, also ist close zugleich high und low. Das macht die
        # Barrieren strenger, aber fuer BEIDE Seiten gleich - und nur der
        # Vergleich zaehlt.
        atr = GG.atr_tag_relativ(c, c, c)
        # ⚠️ ohne Stundenspanne ist atr null; ersatzweise die realisierte
        # Streuung der letzten 24 Schritte, auf Tagesmass skaliert
        with np.errstate(divide="ignore", invalid="ignore"):
            lr = np.diff(np.log(np.maximum(c, 1e-12)), prepend=0.0)
        kk = np.ones(24) / 24.0
        mu = np.convolve(lr, kk, mode="full")[:len(c)]
        mu2 = np.convolve(lr ** 2, kk, mode="full")[:len(c)]
        atr = np.sqrt(np.maximum(mu2 - mu ** 2, 0.0)) * np.sqrt(24.0)
        atr[:24] = np.nan
        stop = np.clip(K * atr, GG.STOP_MIN, GG.STOP_MAX)
        a, _b, _c2, gu, _d = GG.ausgaenge(c, c, c, stop, CRV * stop, H)
        e, _f, _g2, _h, _i = GG.ausgaenge(c, c, c, stop, CRV * stop, H,
                                          runter=True)
        s = np.flatnonzero(gu)
        if not len(s):
            continue
        zl.append(a[s]); zs.append(e[s]); gg.append(np.full(len(s), g))
    if not gg:
        return np.nan, np.nan
    zl = np.concatenate(zl); zs = np.concatenate(zs)
    gg = np.concatenate(gg)
    oben = gg == GRUPPEN - 1
    pl, ps = zl.mean(), zs.mean()
    if pl <= 0 or ps <= 0:
        return np.nan, np.nan
    return float(zl[oben].mean() / pl), float(zs[oben].mean() / ps)


def groessen(lh, lr):
    """Die fuenf Kandidaten aus Vorabfestlegung 19 § 2.2."""
    return {
        "V Verhaeltnis": lh / max(lr, 1e-9),
        "G Gegenlift": lr,
        "D Differenz": lh - lr,
        "S Summe/2 (Bewegung)": (lh + lr) / 2.0,
        "Q D/S": (lh - lr) / max((lh + lr) / 2.0, 1e-9),
    }


def main() -> int:
    print("=" * 100)
    print("WOMIT TRENNT MAN RICHTUNG VON BEWEGUNG? - Eichung an einer "
          "Simulation")
    print("=" * 100)
    print("  Vorabfestlegung 19 · %d Gruppen x %d Reihen x %d Schritte · "
          "%d Ziehungen" % (GRUPPEN, REIHEN_JE_GRUPPE, LAENGE, ZIEHUNGEN))
    print("  ⚠️ Die Wahrheit ist GESETZT: drift = Richtung, sigma = Bewegung")

    rng = np.random.default_rng(SAAT)
    sammel = {d: {} for d in DOSEN}
    for dosis in DOSEN:
        werte = {}
        for _ in range(ZIEHUNGEN):
            lh, lr = lifts(*welt(rng, dosis))
            if not (np.isfinite(lh) and np.isfinite(lr)):
                continue
            for k, v in groessen(lh, lr).items():
                werte.setdefault(k, []).append(v)
        sammel[dosis] = {k: np.array(v) for k, v in werte.items()}
        n = len(next(iter(werte.values()))) if werte else 0
        print("  Dosis %.2f: %d gueltige Ziehungen" % (dosis, n), flush=True)

    print()
    print("=" * 100)
    print("A3 DOSIS-WIRKUNG - steigt die Groesse MONOTON mit dem "
          "Richtungsanteil?")
    print("=" * 100)
    print("  %-22s %s" % ("Groesse",
                          " ".join("%9.2f" % d for d in DOSEN)))
    monoton = {}
    for k in groessen(1.0, 1.0):
        med = [float(np.median(sammel[d][k])) if k in sammel[d] else np.nan
               for d in DOSEN]
        d1 = np.diff(med)
        mono = bool(np.all(d1 > 0)) or bool(np.all(d1 < 0))
        monoton[k] = mono
        print("  %-22s %s   %s"
              % (k, " ".join("%9.3f" % m for m in med),
                 "✔ monoton" if mono else "⛔ springt"))

    print()
    print("=" * 100)
    print("A1 und A2 - Fehlalarm in der BEWEGUNG-Welt, Fundquote in der "
          "RICHTUNG-Welt")
    print("=" * 100)
    print("  ⭐ Die Schwelle wird ABGELESEN: Mitte zwischen dem 90. Perzentil")
    print("     der BEWEGUNG-Welt und dem 10. Perzentil der RICHTUNG-Welt.")
    print()
    print("  %-22s %10s %10s %10s %8s %8s"
          % ("Groesse", "BEW 90.P", "RICH 10.P", "Schwelle", "Fehlal.",
             "Fundq."))
    bestes = None
    for k in groessen(1.0, 1.0):
        b, r = sammel[0.0].get(k), sammel[1.0].get(k)
        if b is None or r is None or not len(b) or not len(r):
            continue
        b90, r10 = float(np.percentile(b, 90)), float(np.percentile(r, 10))
        if r10 <= b90:
            print("  %-22s %10.3f %10.3f %10s %8s %8s   ⛔ Verteilungen "
                  "ueberlappen" % (k, b90, r10, "-", "-", "-"))
            continue
        schwelle = (b90 + r10) / 2.0
        fehl = float((b > schwelle).mean())
        fund = float((r > schwelle).mean())
        ok = fehl <= 0.10 and fund >= 0.80 and monoton.get(k, False)
        print("  %-22s %10.3f %10.3f %10.3f %7.0f%% %7.0f%%   %s"
              % (k, b90, r10, schwelle, 100 * fehl, 100 * fund,
                 "✔✔ BESTEHT A1+A2+A3" if ok else "-"))
        if ok and (bestes is None or (fund - fehl) > bestes[1]):
            bestes = (k, fund - fehl, schwelle)

    print()
    print("=" * 100)
    if bestes is None:
        print("⛔ H0 NICHT WIDERLEGT - keine Groesse besteht alle drei Proben.")
        print("   Die Spiegelprobe auf dieser Geometrie ist damit OFFEN, und")
        print("   die heutigen Urteile bleiben ZURUECKGEZOGEN, nicht ersetzt.")
        return 1
    print("✔✔ H1: `%s` trennt · abgelesene Schwelle %.3f"
          % (bestes[0], bestes[2]))
    print("   ⚠️ Normalverteilte Renditen haben keine fetten Raender und kein")
    print("      Vola-Clustering - die Schwelle ist eine UNTERE Abschaetzung.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
