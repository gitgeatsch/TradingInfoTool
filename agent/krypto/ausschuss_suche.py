"""Ausschuss-Suche (2026-08-04, Phase 1.1 aus Zielgroessen_und_Erfolgsmasse.md 7.2).

DIE FRAGE. Gibt es im geblockten Signalbestand eine ueber Einstiegsmerkmale
identifizierbare Teilmenge, deren Ergebnis mindestens dem der durchgelassenen
Signale entspricht? Wenn ja, laesst sich das Gate GEZIELT fuer genau diese
Faelle oeffnen - mehr Signale UND bessere, statt "Niveau senken".

WARUM DAS VERFAHREN VOR DEN DATEN KOMMT. 43 gemeinsame Merkmale mal rund 9
Schwellen sind knapp 400 Einzelhypothesen. Bei naiven 5 % erwartet man rund
20 "Funde" aus reinem Rauschen. Dazu kommt die Symbolklumpung: am 04.08.
ergab derselbe Zusammenhang naiv p=0,039 und symbolgeblockt p=0,194. Ohne
Kontrolle beider Effekte ist jeder Fund an echten Daten wertlos.

ZWEI MECHANISMEN LOESEN BEIDES GLEICHZEITIG:

1. MAX-STATISTIK STATT EINZELTEST. Nicht "ist Kandidat X signifikant?",
   sondern "ist der BESTE aus 400 Kandidaten besser als der beste, den
   Zufall liefert?". Die Nullverteilung wird ueber dasselbe vollstaendige
   Suchverfahren erzeugt - damit ist die Mehrfachtestung eingepreist, ohne
   Bonferroni-Korrektur und ihre Konservativitaet.

2. BLOCK-UMSORTIERUNG statt zeilenweiser Permutation. Die Ergebnisse eines
   Symbols bleiben als BLOCK zusammen; nur ihre Lage gegenueber der
   Merkmalsmatrix wechselt. Das zerstoert den Zusammenhang zwischen Merkmal
   und Ergebnis, erhaelt aber die Korrelation INNERHALB eines Symbols - und
   kommt mit ungleich grossen Bloecken zurecht, die wir haben (von 58
   Faellen beim groessten Symbol bis hinunter zu 1).

   Ein Wild Cluster Bootstrap (Rademacher-Vorzeichen je Symbol) stand hier
   zuerst und ist im eigenen Pruefstand durchgefallen - Begruendung bei
   _block_permutation_null().

Die Teststatistik ist bewusst ein t-artiger Wert und nicht der blosse
Teilmengen-Mittelwert: ueber viele Kandidaten maximiert, gewinnt sonst
immer die kleinste Teilmenge mit dem groessten Ausreisser.

TIER-UEBERGREIFEND. Die Merkmalsliste ist EINGABE, nicht fest verdrahtet -
43 Merkmale tragen Hebel und Spot gemeinsam (Inventur 04.08.). Derselbe Code
laeuft je Tier mit der jeweils gueltigen Liste. Kein zweites Verfahren fuer
Aktien oder Rohstoffe.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Eine Teilmenge unter diesem Anteil ist als Regel wertlos - sie wuerde das
# Signalvolumen nicht messbar erhoehen, und genau darum geht es (Ziel: mehr
# UND bessere Signale, nicht nur bessere).
MIN_ANTEIL = 0.10
# Schwellenkandidaten je Merkmal: die inneren Dezile. Randnahe Schnitte
# erzeugen Teilmengen unter MIN_ANTEIL und fallen ohnehin heraus.
QUANTILE = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])

# ABSOLUTE PREISFELDER DUERFEN NICHT ALS MERKMAL DIENEN.
#
# Gemessen am 04.08. an 413 aufgeloesten Hebel-Signalen: die
# Intraklassen-Korrelation dieser Felder liegt bei 0,998 bis 1,000 - fast
# ihre GESAMTE Streuung liegt zwischen den Symbolen, nicht innerhalb. Ein
# Schwellenschnitt auf `entry_usd_von` trennt deshalb nicht nach einer
# Eigenschaft des Signals, sondern nach dem Symbol: BTC kostet nun einmal
# fuenfstellig und KAIA Cent-Betraege.
#
# Die Suche wuerde daraus "Symbol X war gut" ableiten und es als
# Merkmalsregel ausgeben - eine Regel, die auf neuen Symbolen nichts wert
# ist und die Symbolkonzentration (bekannter Befund) als Erkenntnis
# verkleidet. Zum Vergleich: confidence_pct liegt bei 0,282,
# top_grund_1_kategorie bei 0,031.
#
# Die Zoneninformation geht dadurch NICHT verloren - sie gehoert in
# RELATIVER Form hinein (stop_rel, CRV, Abstand zum Entry), und die ist
# symbolunabhaengig.
MERKMALE_AUSSCHLUSS = frozenset({
    "entry_usd_von", "entry_usd_bis", "entry_usd",
    "entry_eur_von", "entry_eur_bis",
    "stop_loss_usd_von", "stop_loss_usd_bis", "stop_loss_usd",
    "stop_loss_eur_von", "stop_loss_eur_bis",
    "take_profit_usd_von", "take_profit_usd_bis", "take_profit_usd",
    "take_profit_eur_von", "take_profit_eur_bis",
    "halte_kriterium_ziel_preis_usd", "halte_kriterium_ziel_preis_eur",
    "mindestziel_usd", "mindestziel_eur",
    "liquidationspreis_geschaetzt_usd",
})


# BETRIEBSGRENZE, im eigenen Pruefstand gemessen (04.08.), nicht gesetzt.
# Falschtrefferquote der Block-Umsortierung nach Symbolabhaengigkeit der
# Merkmale:
#     ICC 0,30 -> 3 %   0,45 -> 3 %   0,60 -> 3 %   0,75 -> 8 %   0,85 -> 30 %
# Bis 0,75 traegt das Verfahren, bei 0,85 nicht mehr. Der Grund ist
# grundsaetzlich und durch kein Permutationsverfahren zu beheben: sind die
# Merkmale nahezu symbolkonstant, IST ein Merkmalsschnitt ein Symbolschnitt,
# und die Frage "Merkmal oder Symbol?" ist nicht mehr entscheidbar.
# Zum Vergleich, wie gross der Unterschied ist: dieselbe Welt bei ICC 0,85
# ergibt mit zeilenweiser Permutation 94 % Fehlalarme.
ICC_OBERGRENZE = 0.80


def intraklassen_korrelation(x: np.ndarray, symbole: np.ndarray) -> float | None:
    """Anteil der Merkmalsvarianz, der ZWISCHEN den Symbolen liegt.

    0 = symbolunabhaengig, 1 = je Symbol konstant. Gemessen an den echten
    Daten am 04.08.: confidence_pct 0,282, top_grund_1_kategorie 0,031 -
    aber entry_usd_von 0,999 und stop_loss_usd_von 1,000."""
    gesamt = float(np.var(x))
    if gesamt <= 0:
        return None
    _, cl = np.unique(symbole, return_inverse=True)
    mittel = np.array([x[cl == k].mean() for k in range(cl.max() + 1)])
    groesse = np.array([(cl == k).sum() for k in range(cl.max() + 1)])
    zwischen = float(np.average((mittel - x.mean()) ** 2, weights=groesse))
    return float(np.clip(zwischen / gesamt, 0.0, 1.0))


def pruefe_merkmalsliste(merkmalsnamen: list[str], X: np.ndarray | None = None,
                         symbole: np.ndarray | None = None) -> list[str]:
    """Meldet Merkmale, die als Symbol-Kennung wirken wuerden.

    Zwei Pruefungen, die zweite nur mit Daten:
    1. NAMENSLISTE - absolute Preisfelder, siehe MERKMALE_AUSSCHLUSS.
    2. GEMESSENE ICC gegen ICC_OBERGRENZE. Faengt auch Merkmale, die nicht
       auf der Namensliste stehen, sich aber genauso verhalten - die Liste
       kann nie vollstaendig sein.

    Rueckgabe ist die Menge der Verstoesse, leer heisst sauber. Bewusst KEIN
    stilles Filtern: wer ein Preisfeld uebergibt, hat vermutlich vergessen es
    in eine relative Groesse umzurechnen, und soll das merken. Stille
    Degradierung ist laut Methodik 2.5.8 der gefaehrlichste Fehlertyp dieses
    Projekts."""
    verstoesse = [m for m in merkmalsnamen if m in MERKMALE_AUSSCHLUSS]
    if X is None or symbole is None:
        return verstoesse
    for i, name in enumerate(merkmalsnamen):
        if name in verstoesse:
            continue
        icc = intraklassen_korrelation(X[:, i], symbole)
        if icc is not None and icc >= ICC_OBERGRENZE:
            verstoesse.append(f"{name} (ICC {icc:.3f})")
    return verstoesse


@dataclass
class Kandidat:
    """Eine gefundene Teilregel und ihre Kennzahlen."""

    merkmal: str
    schwelle: float
    richtung: str          # ">=" oder "<"
    n: int
    ew: float              # Mittelwert R in der Teilmenge
    ew_rest: float
    statistik: float

    @property
    def beschreibung(self) -> str:
        return f"{self.merkmal} {self.richtung} {self.schwelle:.4g}"


@dataclass
class Suchergebnis:
    bester: Kandidat | None
    p_wert: float | None
    hypothesen: int
    n_gesamt: int
    n_symbole: int
    null_ziehungen: int
    # Beitrags-Konzentration nach Methodik 2.5.5: traegt ein einzelnes Symbol
    # den halben Effekt? Ohne diese Angabe ist ein Fund nicht interpretierbar.
    top_symbol: str | None = None
    top_symbol_anteil: float | None = None
    warnungen: list[str] = field(default_factory=list)


def _statistik_alle_schnitte(X_sortiert_idx: np.ndarray, y: np.ndarray,
                             min_n: int) -> np.ndarray:
    """t-artige Statistik fuer JEDEN Schwellenschnitt aller Merkmale.

    Kern des Verfahrens und der Grund, warum es schnell genug ist: statt jede
    Teilmenge einzeln zu bilden, wird je Merkmal EINMAL sortiert (ausserhalb,
    die Sortierung aendert sich unter der Null nie) und dann ueber die
    kumulierte Summe jeder Praefix-Schnitt in O(1) ausgewertet.

    Rueckgabe: Matrix (Schnitte x Merkmale). Schnitte unterhalb der
    Mindestgroesse bekommen -inf und koennen nie gewinnen.
    """
    n, m = X_sortiert_idx.shape
    y_sortiert = y[X_sortiert_idx]                      # (n, m)
    cs = np.cumsum(y_sortiert, axis=0)                  # (n, m)
    cs2 = np.cumsum(y_sortiert ** 2, axis=0)
    gesamt, gesamt2 = cs[-1], cs2[-1]

    k = np.arange(1, n).reshape(-1, 1)                  # Praefixgroessen 1..n-1
    n_a, n_b = k, (n - k)
    summe_a, summe_b = cs[:-1], gesamt - cs[:-1]
    quad_a, quad_b = cs2[:-1], gesamt2 - cs2[:-1]

    mittel_a, mittel_b = summe_a / n_a, summe_b / n_b
    # Stichprobenvarianz, gegen numerische Ausloescher abgesichert
    var_a = np.maximum(quad_a / n_a - mittel_a ** 2, 0.0) * n_a / np.maximum(n_a - 1, 1)
    var_b = np.maximum(quad_b / n_b - mittel_b ** 2, 0.0) * n_b / np.maximum(n_b - 1, 1)

    nenner = np.sqrt(var_a / n_a + var_b / n_b)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (mittel_a - mittel_b) / nenner
    t[~np.isfinite(t)] = -np.inf

    # Beide Seiten des Schnitts sind gueltige Regeln ("< Schwelle" und
    # ">= Schwelle"), deshalb der Betrag - die Richtung wird spaeter aus dem
    # Vorzeichen der Differenz gelesen.
    t = np.abs(t)
    zu_klein = (n_a < min_n) | (n_b < min_n)
    t[np.broadcast_to(zu_klein, t.shape)] = -np.inf
    return t


def _bester_schnitt(X: np.ndarray, X_sortiert_idx: np.ndarray, y: np.ndarray,
                    merkmalsnamen: list[str], min_n: int) -> tuple[float, Kandidat | None]:
    t = _statistik_alle_schnitte(X_sortiert_idx, y, min_n)
    if not np.isfinite(t).any():
        return -np.inf, None
    flach = int(np.nanargmax(t))
    zeile, spalte = np.unravel_index(flach, t.shape)
    beste_stat = float(t[zeile, spalte])

    idx = X_sortiert_idx[:, spalte]
    grenze = zeile + 1                                   # Praefixgroesse
    unten, oben = idx[:grenze], idx[grenze:]
    schwelle = float(X[idx[grenze], spalte])
    # Die Teilmenge ist die BESSERE der beiden Seiten - gesucht sind gute
    # Signale, nicht bloss ein Unterschied.
    if y[unten].mean() >= y[oben].mean():
        teil, rest, richtung = unten, oben, "<"
    else:
        teil, rest, richtung = oben, unten, ">="
    return beste_stat, Kandidat(
        merkmal=merkmalsnamen[spalte], schwelle=schwelle, richtung=richtung,
        n=len(teil), ew=float(y[teil].mean()), ew_rest=float(y[rest].mean()),
        statistik=beste_stat)


def _block_permutation_null(y: np.ndarray, bloecke: list[np.ndarray],
                            rng: np.random.Generator) -> np.ndarray:
    """Eine Ziehung unter der Nullhypothese: ganze Symbolbloecke umsortiert.

    Die Ergebnisse eines Symbols bleiben als BLOCK zusammen, nur ihre Lage
    gegenueber der Merkmalsmatrix wechselt. Damit ist die Korrelation
    innerhalb eines Symbols erhalten, der Zusammenhang zu den Merkmalen
    zerstoert - genau die gesuchte Nullhypothese.

    WARUM NICHT WILD CLUSTER BOOTSTRAP (Rademacher-Vorzeichen je Symbol).
    Am 04.08. gebaut und im eigenen Pruefstand durchgefallen: unsere
    Ergebnisse sind praktisch ZWEIWERTIG (-1 bei Stop, +CRV bei Ziel,
    Schiefe +1,59). Ein Vorzeichenwechsel auf den zentrierten Werten macht
    daraus {-3,24; -1; +0,36; +2,6} mit Schiefe +0,35 - ein Traegerwechsel.
    Die Nullverteilung lag dadurch systematisch zu tief (95%-Punkt 4,17
    gegen beobachtete 4,70) und die Falschtrefferquote bei 18 % statt 5 %.
    Der Wild Bootstrap setzt symmetrische Fehler voraus; die haben wir nicht.

    Die Blockumsortierung erhaelt die Werte EXAKT - sie ordnet nur um.
    """
    reihenfolge = rng.permutation(len(bloecke))
    return np.concatenate([y[bloecke[i]] for i in reihenfolge])


def ausschuss_suche(X: np.ndarray, y: np.ndarray, symbole: np.ndarray,
                    merkmalsnamen: list[str], null_ziehungen: int = 400,
                    min_anteil: float = MIN_ANTEIL, seed: int = 20260804,
                    ) -> Suchergebnis:
    """Sucht die beste Teilmenge und prueft sie gegen die Max-Statistik-Null.

    X      (n x m) Merkmalsmatrix, bereits numerisch
    y      (n,)    R-Multiples
    symbole(n,)    Symbolzugehoerigkeit fuer die Blockung
    """
    n, m = X.shape
    min_n = max(3, int(np.ceil(min_anteil * n)))
    einzigartig, cluster_idx = np.unique(symbole, return_inverse=True)
    # Zeilenindizes je Symbol - Grundlage der Blockumsortierung. Die Bloecke
    # muessen NICHT gleich gross sein; genau daran scheitern die
    # Standardverfahren, und unsere Groessen reichen von 58 bis 1.
    bloecke = [np.flatnonzero(cluster_idx == k) for k in range(len(einzigartig))]
    X_sortiert_idx = np.argsort(X, axis=0, kind="stable")

    beobachtet, bester = _bester_schnitt(X, X_sortiert_idx, y, merkmalsnamen, min_n)
    hypothesen = m * (n - 1)
    warnungen: list[str] = []

    if bester is None:
        return Suchergebnis(None, None, hypothesen, n, len(einzigartig),
                            0, warnungen=["keine gueltige Teilmenge (n zu klein)"])

    rng = np.random.default_rng(seed)
    null = np.empty(null_ziehungen)
    for i in range(null_ziehungen):
        y_null = _block_permutation_null(y, bloecke, rng)
        null[i], _ = _bester_schnitt(X, X_sortiert_idx, y_null, merkmalsnamen, min_n)
    # +1 im Zaehler und Nenner: der beobachtete Wert zaehlt als eine mögliche
    # Ziehung mit. Ohne das kann p exakt 0 werden, was bei endlich vielen
    # Ziehungen nie zutrifft.
    p = float((np.sum(null >= beobachtet) + 1) / (null_ziehungen + 1))

    # Beitrags-Konzentration (Methodik 2.5.5)
    maske = ((X[:, merkmalsnamen.index(bester.merkmal)] >= bester.schwelle)
             if bester.richtung == ">=" else
             (X[:, merkmalsnamen.index(bester.merkmal)] < bester.schwelle))
    top_sym, top_anteil = None, None
    if maske.sum() > 0:
        beitrag = y[maske] - y.mean()
        gesamt = np.abs(beitrag).sum()
        if gesamt > 0:
            je_symbol: dict[str, float] = {}
            for s, b in zip(symbole[maske], beitrag):
                je_symbol[s] = je_symbol.get(s, 0.0) + abs(b)
            top_sym = max(je_symbol, key=je_symbol.get)
            top_anteil = je_symbol[top_sym] / gesamt
            if top_anteil > 0.5:
                warnungen.append(
                    f"Beitrags-Konzentration: {top_sym} traegt "
                    f"{top_anteil*100:.0f} % des Effekts (Methodik 2.5.5)")

    if len(np.unique(symbole)) < 8:
        warnungen.append(
            f"nur {len(np.unique(symbole))} Symbole - die Blockung hat wenig "
            "Freiheitsgrade, p ist entsprechend grob")

    return Suchergebnis(bester, p, hypothesen, n, len(np.unique(symbole)),
                        null_ziehungen, top_sym, top_anteil, warnungen)
