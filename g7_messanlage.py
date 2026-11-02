"""G7 MESSANLAGE — Wert eines TAGES-Urteils (Sicht-Gutachten, Zustand, Bedenken-Stufe) gegen eine STETIGE Zielgröße (G7 Stufe 0b,
Voranalyse_G7_Messplan_02_11.md, Nutzer 02.11.: *„a/a/a, Stufe 0 bauen – prüfen, gegenprüfen und doku“*).

Warum eine eigene Anlage neben ``messnorm``: messnorm misst BEITRÄGE je Asset und Einstieg (Lage, Querschnitt). Hier steht EIN Wert je
Tag (das Urteil einer Sicht) gegen EINE Marktreihe. Übernommen aus messnorm, nicht neu gesetzt:
  * Block = ``messnorm._block(H)`` = max(15, 3 H); unter ``MIN_BLOECKE`` = 20 Blöcken **KEIN BEFUND**
  * Nullpunkt = MITTEL der Nullwelten (nicht das Maximum), Band = 5./95. Perzentil (Messstandard 08./09.09.)
  * Selbsttest gegen bekannte Wahrheit, Pflanzung als Auflösungskurve, 1.000 Ziehungen (Memory: Selbsttest Stufung)

Neu, und WARUM:
  * ZIELGRÖSSE stetig in σ (G7-2: Einbruch ja/nein hat nur 2–6 Episoden je Zeitraum):
        ertrag_s(T, H) = ln(P[T+H] / P[T]) / (σ_T · √H)          σ_T = Std. der Tageslog-Erträge der 60 Tage VOR T
        tief_s(T, H)   = ln(min P[T+1..T+H] / P[T]) / (σ_T · √H)  der tiefste Punkt auf dem Weg (≤ 0)
  * NULLWELT = KREISVERSCHIEBUNG der Urteilsreihe, ALLE n − 1 Verschiebungen (die volle Bahn). Sie erhält die BALLUNG des Urteils
    (gleiche Läufe, gleiche Rate) und die Abhängigkeit der Zielgröße — genau das, was eine Zufallsziehung je Tag zerstört (Memory:
    *Nullwelt bei geballten Signalen*: Zufallsstunden-Rang 30 % Fehlalarm). Über die volle Bahn ist es ein EXAKTER Randomisierungstest.
    ⚠️ Gemessen 02.11. im Selbsttest: der erste Bau zog 200–1.000 ZUFÄLLIGE Verschiebungen von mindestens einem Block — auf 332 Tagen
    6,3–8,8 % Fehlalarm statt 5 %. Mit der vollen Bahn 4,5–6,2 % (600 Ziehungen, Standardfehler 0,9 Pp)
  * STATISTIK: bei einem Ja/Nein-Urteil Mittel(Zielgröße | ja) − Mittel(| nein); bei einem stetigen Urteil (Rang) die Rangkorrelation

⚠️ Nur Rechnung. Liest nichts, schreibt nichts.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

import messnorm

MIN_BLOECKE = 20
SIGMA_TAGE = 60


def zielgroesse(kurs: pd.Series, H: int, art: str = "ertrag") -> pd.Series:
    """Je Tag T die Zielgröße über H Tage in σ. ``kurs`` täglich, Index Datum. NaN, wo σ oder die Zukunft fehlt."""
    k = kurs.sort_index().astype(float)
    r = np.log(k).diff()
    sig = r.rolling(SIGMA_TAGE).std().shift(1)             # nur VOR T
    if art == "ertrag":
        x = np.log(k.shift(-H) / k)
    elif art == "tief":
        m = pd.concat([k.shift(-i) for i in range(1, H + 1)], axis=1).min(axis=1, skipna=False)
        x = np.minimum(np.log(m / k), 0.0)
    else:
        raise ValueError(art)
    return (x / (sig * math.sqrt(H))).rename("%s_%d" % (art, H))


def _stat(u: np.ndarray, z: np.ndarray) -> float:
    if set(np.unique(u)) <= {0.0, 1.0}:
        a, b = z[u == 1], z[u == 0]
        return float(a.mean() - b.mean()) if len(a) and len(b) else float("nan")
    ru, rz = pd.Series(u).rank().values, pd.Series(z).rank().values
    return float(np.corrcoef(ru, rz)[0, 1])


def messe(urteil: pd.Series, ziel: pd.Series, H: int, rng=None, ziehungen=None, richtung: str = "beide", mit_null: bool = False) -> dict:
    """Wert eines Tages-Urteils gegen die Zielgröße.

    ``richtung``: "unten" (das Urteil sagt Schlechtes voraus -> Statistik soll NEGATIV sein, einseitig), "oben", oder "beide"
    (keine fachliche Richtung -> zweiseitig, Memory: *Vorab-Messplan ohne fachliche Richtung zweiseitig*).
    ``rng``/``ziehungen`` bleiben nur für alte Aufrufe stehen — die Nullwelt ist die VOLLE Bahn und damit ohne Zufall."""
    d = pd.concat([urteil.rename("u"), ziel.rename("z")], axis=1).dropna()
    n = len(d)
    blk = messnorm._block(H)
    nb = n // blk
    aus = {"tage": n, "block": blk, "bloecke": nb, "H": H, "richtung": richtung}
    if nb < MIN_BLOECKE:
        return {**aus, "urteil": "KEIN BEFUND", "grund": "%d Blöcke < %d" % (nb, MIN_BLOECKE)}
    u, z = d.u.values.astype(float), d.z.values.astype(float)
    if len(np.unique(u)) < 2:
        return {**aus, "urteil": "KEIN BEFUND", "grund": "Urteil ohne Streuung"}
    s = _stat(u, z)
    null = np.array([_stat(np.roll(u, k), z) for k in range(1, n)])
    null = null[np.isfinite(null)]
    mitte, lo, hi = float(null.mean()), float(np.percentile(null, 5)), float(np.percentile(null, 95))
    lo2, hi2 = float(np.percentile(null, 2.5)), float(np.percentile(null, 97.5))
    if richtung == "unten":
        traegt, p = s < lo, float((null <= s).mean())
    elif richtung == "oben":
        traegt, p = s > hi, float((null >= s).mean())
    else:
        traegt = s < lo2 or s > hi2
        p = float(2 * min((null <= s).mean(), (null >= s).mean()))
    return {**aus, "stat": s, "nullpunkt": mitte, "band": (lo, hi) if richtung != "beide" else (lo2, hi2), "p": min(1.0, p),
            "abstand": s - mitte, "urteil": "TRÄGT" if traegt else "trägt nicht", "anteil_ja": float(u.mean()) if
            set(np.unique(u)) <= {0.0, 1.0} else float("nan"), **({"null": null} if mit_null else {})}


def geballt(n: int, rate: float, lauf: float, rng) -> np.ndarray:
    """Ein Ja/Nein-Urteil mit BALLUNG: Markov-Kette mit Rate ``rate`` und mittlerer Lauflänge ``lauf`` (Tage) — unabhängig von allem."""
    p_aus = 1.0 / lauf                                            # ja -> nein
    p_ein = rate * p_aus / (1 - rate)                             # nein -> ja, so dass die Rate stimmt
    x = np.zeros(n)
    x[0] = rng.random() < rate
    for i in range(1, n):
        x[i] = (rng.random() >= p_aus) if x[i - 1] else (rng.random() < p_ein)
    return x


def selbsttest(ziel: pd.Series, H: int, rng, ziehungen: int = 1000, null_ziehungen=None, rate: float = 0.2,
               laeufe=(1, 3, 10), staerken=(0.1, 0.2, 0.3, 0.5)) -> dict:
    """Gegen bekannte Wahrheit, auf der ECHTEN Zielgröße:
      * NULL: geballte Urteile ohne jeden Bezug zur Zukunft -> Fehlalarmquote (Soll ≤ 5 %, einseitig „unten“)
      * PFLANZUNG: an den Ja-Tagen wird die Zielgröße um ``staerke`` σ gesenkt -> Fundquote je Stärke (die Auflösung)."""
    z = ziel.dropna()
    n = len(z)
    aus = {"H": H, "tage": n, "bloecke": n // messnorm._block(H), "fehlalarm": {}, "fund": {}}
    for L in laeufe:
        f = 0
        for _ in range(ziehungen):
            u = pd.Series(geballt(n, rate, L, rng), index=z.index)
            f += messe(u, z, H, rng, null_ziehungen, "unten")["urteil"] == "TRÄGT"
        aus["fehlalarm"][L] = f / ziehungen
    for s in staerken:
        k = 0
        m = max(1, ziehungen // 5)
        for _ in range(m):
            u = pd.Series(geballt(n, rate, 3, rng), index=z.index)
            k += messe(u, z - s * u, H, rng, null_ziehungen, "unten")["urteil"] == "TRÄGT"
        aus["fund"][s] = k / m
    return aus
