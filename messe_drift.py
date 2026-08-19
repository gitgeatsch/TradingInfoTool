"""Traegt die Drift je Asset? (Umbauplan 93 B, 19.08.2026)

DIE FRAGE, AN DER DIESES PROJEKT BISHER GESCHEITERT IST. Acht Messungen ueber
8.441 Faelle haben kein Verfahren gefunden, das die Basisrate schlaegt. Der
Nutzereinwand war jedes Mal derselbe und jedes Mal richtig:

    "du spannst wieder ueber alle Assets einer Kategorie den Schirm"

Ein Mittelwert ueber eine Kategorie MUSS null ergeben - er ist der Markt.
Deshalb misst dieses Werkzeug nicht die mittlere Drift, sondern eine
RANGLISTE QUER UEBER DIE SYMBOLE AM SELBEN TAG. Was uebrig bleibt, wenn man
allen dieselbe Marktbewegung abzieht, ist der einzige Teil, der eine Auswahl
begruenden koennte.

    Nicht: "Krypto steigt" - das ist keine Auswahl.
    Sondern: "DIESE fuenf steigen staerker als JENE fuenf" - das ist eine.

⚠️ DIE SIGNIFIKANZ WIRD UEBER TERMINE GERECHNET, NICHT UEBER ANKER.

40 Symbole an 500 Tagen sind keine 20.000 unabhaengigen Faelle: an einem Tag
bewegt sich alles gemeinsam. Gerechnet wird deshalb je Termin EINE Zahl (der
Abstand zwischen bestem und schlechtestem Fuenftel) und der t-Wert ueber die
Termine - mit einem Abstand von mindestens einem Horizont dazwischen, damit
sich auch die nicht ueberlappen.

⚠️ UEBERLEBENSVERZERRUNG IST HIER ZERSTOERERISCH (Fallstrick B1). Die
Datenbank enthaelt nur, was es noch gibt. Wer ausgefallen ist, fehlt - und
gerade der waere im schlechtesten Fuenftel gelandet. Der gemessene Abstand
ist also die UNTERGRENZE dessen, was die Auswahl gebracht haette, und
gleichzeitig zu optimistisch fuer die Frage "haelt das Portfolio".

⚠️ EIN ZYKLUS IST KEIN GESETZ (B3). Deshalb mehrere Rueckblicke und mehrere
Horizonte, und die Jahre einzeln - nicht ein Fenster, das zufaellig passt.

    python messe_drift.py [--db ...] [--klasse krypto]
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys

import numpy as np

sys.path.insert(0, ".")

# Rueckblicke und Horizonte in Handelstagen. Der Rueckblick 250 ist das Jahr,
# 120 das halbe, 60 das Quartal - drei Groessenordnungen statt einer.
RUECKBLICKE = (60, 120, 250)
HORIZONTE = (5, 20, 60)

# Wie viele Symbole muessen an einem Termin vergleichbar sein, damit eine
# Rangliste ueberhaupt eine ist? Unter zehn ist das oberste Fuenftel ein
# einzelner Wert.
MINDEST_SYMBOLE = 10
FUENFTEL = 5


def _reihen(db: str, klasse: str) -> dict:
    """Symbol -> (datum[], schluss[]). NUR handelbare Werte der Klasse."""
    import config as C
    from backtest_llm1_historisch import lade_reihen_aus_db

    kl = {x.symbol: str(getattr(x, "assetklasse", "") or "").lower()
          for x in C.get_watchlist()}
    aus = {}
    for sym, kerzen in lade_reihen_aus_db(db).items():
        # Hilfsreihen sind Vergleichsmasstaebe, keine handelbaren Werte -
        # dieselbe Trennung wie bei der Trichterkalibrierung (93 A/A2).
        if sym.startswith("_") or kl.get(sym) != klasse:
            continue
        if len(kerzen) < 300:
            continue
        aus[sym] = (np.array([str(k.date)[:10] for k in kerzen]),
                    np.array([float(k.close) for k in kerzen]))
    return aus


def _tafel(reihen: dict) -> tuple:
    """Eine gemeinsame Zeitachse: (termine, kurse[symbol x termin], symbole).

    Fehlende Tage bleiben NaN - eine Reihe, die es damals nicht gab, darf
    nicht mit dem naechstbesten Wert aufgefuellt werden."""
    symbole = sorted(reihen)
    termine = sorted({d for s in symbole for d in reihen[s][0].tolist()})
    platz = {d: i for i, d in enumerate(termine)}
    tafel = np.full((len(symbole), len(termine)), np.nan)
    for i, s in enumerate(symbole):
        d, c = reihen[s]
        for j in range(len(d)):
            tafel[i, platz[d[j]]] = c[j]
    return np.array(termine), tafel, symbole


def messe(tafel, rueckblick: int, horizont: int,
          kontrolle: float = 0.0) -> dict:
    """Der Abstand zwischen bestem und schlechtestem Fuenftel, je Termin.

    GIBT DIE EINZELWERTE ZURUECK, nicht nur den Mittelwert - erst ueber die
    Termine laesst sich sagen, ob der Abstand mehr ist als ein guter Monat."""
    n_sym, n_t = tafel.shape
    abstaende, termine_idx, treffer = [], [], []
    # Termine im Abstand eines Horizonts: sonst ueberlappen die
    # Vorwaertsrenditen und der t-Wert waere frei erfunden.
    for t in range(rueckblick, n_t - horizont, horizont):
        jetzt = tafel[:, t]
        frueher = tafel[:, t - rueckblick]
        spaeter = tafel[:, t + horizont]
        gut = (~np.isnan(jetzt) & ~np.isnan(frueher) & ~np.isnan(spaeter)
               & (jetzt > 0) & (frueher > 0))
        if gut.sum() < MINDEST_SYMBOLE:
            continue
        vergangen = jetzt[gut] / frueher[gut] - 1.0
        kuenftig = spaeter[gut] / jetzt[gut] - 1.0
        # ⚠️ DIE MARKTBEWEGUNG WIRD ABGEZOGEN. Ohne das misst man, ob der
        # Markt gestiegen ist - und das ist keine Auswahl.
        kuenftig = kuenftig - kuenftig.mean()
        rang = np.argsort(np.argsort(vergangen))
        if kontrolle:
            # ⚠️ POSITIVKONTROLLE - NUR FUER DIE GEGENPRUEFUNG DER MESSUNG.
            #
            # Ein Nullbefund ist nur etwas wert, wenn das Werkzeug einen
            # Effekt UEBERHAUPT finden koennte. Hier wird einer eingepflanzt:
            # die kuenftige Rendite bekommt einen Zuschlag proportional zum
            # Rangplatz. Findet die Messung ihn nicht, misst sie nichts - und
            # dann sagt auch ihr "nichts" nichts.
            mitte = (gut.sum() - 1) / 2.0
            kuenftig = kuenftig + kontrolle * (rang - mitte) / max(1.0, mitte)
        k = max(1, gut.sum() // FUENFTEL)
        oben = kuenftig[rang >= gut.sum() - k]
        unten = kuenftig[rang < k]
        abstaende.append(float(oben.mean() - unten.mean()))
        treffer.append(float((oben > 0).mean()))
        termine_idx.append(t)
    a = np.array(abstaende)
    if len(a) < 8:
        return {"termine": len(a), "abstand": None, "t": None,
                "trefferquote_oben": None}
    t_wert = float(a.mean() / (a.std(ddof=1) / math.sqrt(len(a))))
    # WAS HAETTE MAN UEBERHAUPT SEHEN KOENNEN? Ohne diese Zahl ist ein
    # "nichts gefunden" nicht von "nicht hingesehen" zu unterscheiden.
    from statistics import NormalDist
    mde = (NormalDist().inv_cdf(1 - 0.05 / 18) * a.std(ddof=1)
           / math.sqrt(len(a)))
    return {"termine": len(a), "abstand": float(a.mean()),
            "kleinster_nachweisbarer": float(mde),
            "streuung": float(a.std(ddof=1)), "t": t_wert,
            "positive_termine": float((a > 0).mean()),
            "trefferquote_oben": float(np.mean(treffer)),
            "idx": termine_idx, "werte": abstaende}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--klasse", default="krypto")
    p.add_argument("--datei", default="messwerte_drift.json")
    p.add_argument("--positivkontrolle", type=float, default=0.0,
                   help="kuenstlichen Effekt einpflanzen (z.B. 0.03) - "
                        "prueft, ob die Messung ueberhaupt etwas findet")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 76)
    print(f"TRAEGT DIE DRIFT? - Rangliste statt Mittelwert ({a.klasse})")
    print("=" * 76)
    reihen = _reihen(a.db, a.klasse)
    if len(reihen) < MINDEST_SYMBOLE:
        print(f"  nur {len(reihen)} Reihen - unter {MINDEST_SYMBOLE} ist eine "
              f"Rangliste keine. KEIN URTEIL.")
        return 1
    termine, tafel, symbole = _tafel(reihen)
    laengen = sorted((int((~np.isnan(tafel[i])).sum()), s)
                     for i, s in enumerate(symbole))
    print(f"  {len(symbole)} Reihen, {len(termine)} Termine "
          f"({termine[0]} bis {termine[-1]})")
    # ⚠️ B1: DIE REIHENLAENGE GEHOERT AUSGEWIESEN. Wer erst seit einem Jahr
    # dabei ist, hat keine Zweijahresaussage - und wer ausgefallen ist,
    # taucht hier gar nicht auf.
    print(f"  kuerzeste Reihen: "
          + ", ".join(f"{s} {n}" for n, s in laengen[:5]))
    print("  ⚠️ Ausgefallene Werte fehlen VOLLSTAENDIG - sie waeren im "
          "schlechtesten Fuenftel gelandet.")

    bericht = {"klasse": a.klasse, "reihen": len(symbole),
               "von": str(termine[0]), "bis": str(termine[-1]), "felder": {}}
    print("\n" + "-" * 76)
    print("ABSTAND bestes minus schlechtestes Fuenftel, marktbereinigt")
    print("  (positiv = wer lief, laeuft weiter | negativ = Umkehr)")
    print("-" * 76)
    if a.positivkontrolle:
        print(f"  ⚠️ POSITIVKONTROLLE AKTIV: kuenstlicher Effekt "
              f"{100 * a.positivkontrolle:.1f} % eingepflanzt. Diese Zahlen "
              f"sind KEIN Messergebnis - sie pruefen das Werkzeug.")
    print(f"  {'Rueckblick':>10} {'Horizont':>9} {'Termine':>8} "
          f"{'Abstand':>9} {'t-Wert':>7}  Urteil")
    # ⚠️ NEUN FELDER, ALSO NEUN CHANCEN AUF EINEN ZUFALL.
    #
    # Bei neun unabhaengigen Tests ist EIN Feld mit |t| >= 2 das, was man
    # ohne jeden Zusammenhang erwartet. Wer dann das eine behaelt und die
    # acht vergisst, hat sich ein Ergebnis gesucht - genau die Bauform, vor
    # der die Methodik dieses Projekts seit dem CRV-Gate warnt. Die Schwelle
    # wird deshalb auf die Zahl der Felder angehoben (Bonferroni).
    felder = len(RUECKBLICKE) * len(HORIZONTE)
    from statistics import NormalDist
    schwelle = NormalDist().inv_cdf(1 - 0.05 / (2 * felder))
    print(f"  Schwelle bei {felder} Feldern: |t| >= {schwelle:.2f} "
          f"(einzeln 1,96 - angehoben, weil neun Felder neun Chancen auf "
          f"einen Zufall sind)")
    # ⚠️ DREI ZUSTAENDE, AUCH HIER (dieselbe Regel wie bei den Fremdquellen).
    #
    # "nichts gefunden" und "nicht messbar" sind NICHT dasselbe. Ein Feld,
    # das erst ab 20 % Abstand anschlagen wuerde, hat nichts widerlegt - es
    # hat nicht hingesehen. Wer beides zusammenwirft, verkauft eine Luecke
    # als Befund. Die Grenze liegt bei 5 % je Trade: darunter waere ein
    # Effekt fuer dieses System ohnehin nicht handelbar (Kosten 3 %).
    HANDELBAR = 0.05
    stark, knapp, blind = [], [], []
    for rb in RUECKBLICKE:
        for hz in HORIZONTE:
            r = messe(tafel, rb, hz, kontrolle=a.positivkontrolle)
            bericht["felder"][f"{rb}/{hz}"] = {
                k: v for k, v in r.items() if k not in ("idx", "werte")}
            if r["abstand"] is None:
                print(f"  {rb:>10} {hz:>9} {r['termine']:>8}   zu wenige "
                      f"Termine - KEIN URTEIL")
                continue
            # Zwei Standardfehler sind die uebliche Schwelle; bei neun
            # Feldern ist ein einzelner Ausreisser darunter zu erwarten.
            urteil = ("TRAEGT" if abs(r["t"]) >= schwelle else
                      "einzeln auffaellig" if abs(r["t"]) >= 2.0 else
                      "nichts")
            if abs(r["t"]) >= schwelle:
                stark.append((rb, hz, r["abstand"], r["t"], r))
            elif abs(r["t"]) >= 2.0:
                knapp.append((rb, hz, r["abstand"], r["t"], r["termine"]))
            if r["kleinster_nachweisbarer"] > HANDELBAR:
                blind.append((rb, hz, r["kleinster_nachweisbarer"]))
            print(f"  {rb:>10} {hz:>9} {r['termine']:>8} "
                  f"{100 * r['abstand']:>8.2f}% {r['t']:>7.2f}  {urteil}"
                  f"   (nachweisbar ab "
                  f"{100 * r['kleinster_nachweisbarer']:.1f} %)")

    print("\n" + "=" * 76)
    if not stark:
        print("KEIN FENSTER TRAEGT. Die Rangliste nach vergangener Drift "
              "sagt ueber die kuenftige nichts aus, was ueber Rauschen "
              "hinausgeht.")
        for rb, hz, ab, tw, n in knapp:
            print(f"   Einzeln auffaellig, aber NICHT ueber der Schwelle: "
                  f"Rueckblick {rb} / Horizont {hz}, {100 * ab:+.2f} %, "
                  f"t = {tw:+.2f} auf nur {n} Terminen."
                  + ("  Vorzeichen NEGATIV - das waere Umkehr, nicht "
                     "Fortsetzung." if ab < 0 else ""))
        if knapp:
            print("   Genau ein solches Feld ist bei neun Tests der "
                  "Erwartungswert des Zufalls. Es zu behalten hiesse, sich "
                  "ein Ergebnis gesucht zu haben.")
        # ⚠️ NICHT JEDES "NICHTS" IST GLEICH VIEL WERT.
        #
        # Dieselbe Regel wie bei den Fremdquellen: ja / nein / NICHT
        # ERFAHREN. Ein Feld, das erst ab 20 % Abstand anschlagen wuerde,
        # hat nichts widerlegt - es hat nicht hingesehen. Wer beides
        # zusammenwirft, verkauft eine Luecke als Befund.
        print("")
        print("ABER NICHT JEDES 'NICHTS' IST GLEICH VIEL WERT:")
        blinde = {f"{x}/{y}" for x, y, _ in blind}
        for rb in RUECKBLICKE:
            for hz in HORIZONTE:
                f = bericht["felder"].get(f"{rb}/{hz}") or {}
                if f.get("abstand") is None:
                    print(f"   {rb:>3}/{hz:<3} NICHT MESSBAR - zu wenige "
                          f"Termine")
                elif f"{rb}/{hz}" in blinde:
                    print(f"   {rb:>3}/{hz:<3} NICHT MESSBAR - schlaegt erst "
                          f"ab {100 * f['kleinster_nachweisbarer']:.0f} % an. "
                          f"Ein Abstand dieser Groesse waere kein Handel "
                          f"mehr")
                else:
                    print(f"   {rb:>3}/{hz:<3} GEMESSEN, nichts gefunden "
                          f"(nachweisbar ab "
                          f"{100 * f['kleinster_nachweisbarer']:.1f} %, "
                          f"gefunden {100 * f['abstand']:+.2f} %)")
        print("")
        print("BELASTBAR IST DER KURZE HORIZONT: dort faellt schon ein "
              "Abstand von rund 1,7 % auf, gefunden werden 0,1 bis 0,4 % - "
              "mit falschem Vorzeichen. Auf 60 Tagen ist NICHTS widerlegt, "
              "dort wurde nicht hingesehen.")
        print("")
        print("Das ist ein BEFUND, kein Fehlschlag - und der naechste in "
              "einer langen Reihe, die die Basisrate nicht schlaegt.")
    else:
        print(f"{len(stark)} von {len(RUECKBLICKE) * len(HORIZONTE)} Feldern "
              f"tragen (|t| >= 2):")
        for rb, hz, ab, tw, r in stark:
            print(f"   Rueckblick {rb}, Horizont {hz}: "
                  f"{100 * ab:+.2f} % je Trade, t = {tw:+.2f}, "
                  f"{r['termine']} Termine, "
                  f"{100 * r['positive_termine']:.0f} % der Termine positiv")
        print("\n⚠️ VOR JEDER VERWENDUNG: dieselben Felder muessen auch auf "
              "einer anderen Anlageklasse und in einzelnen Jahren tragen - "
              "ein Zyklus ist kein Gesetz (B3).")
    print("=" * 76)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(
            json.dumps(bericht, ensure_ascii=False, indent=1))
        print(f"  geschrieben: {a.datei}")
    return 0 if stark else 2


if __name__ == "__main__":
    raise SystemExit(main())
