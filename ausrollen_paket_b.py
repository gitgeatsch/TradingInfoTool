# -*- coding: utf-8 -*-
"""ROLLOUT PAKET B AM NOTEBOOK - der Soll-Zustand in EINEM Lauf (Schritt 24).

Stehende Regel: *am Notebook immer eine zusammengestellte Gesamtpaket-
Installation, nicht einzelne Schritte nacheinander* - der inkrementelle Weg
hat dort schon einmal eine Luecke hinterlassen. Dieses Skript ist die
Vollstaendigkeitspruefung dazu: es sagt, ob nach dem Pull alles da ist, was
Paket B braucht, und rechnet die eine Sache nach, die kein Pull mitbringt.

    python ausrollen_paket_b.py                 nur pruefen, schreibt nichts
    python ausrollen_paket_b.py --nachrechnen   dazu die fehlenden Tage in
                                                `portfolio_wert_historie`

WAS GEPRUEFT WIRD:

    C  Code      die Paket-B-Module sind da (Pull vollstaendig)
    K  config    Hebel aus der Quote, Aggregat-Deckel, Anlass, alte Ketten
    S  Schema    `signals.instrument` und `verlust_am_stop_eur` - mit
                 LESEPROBE (wer eine Spalte anlegt, muss eine Zeile lesen)
    P  Kapital   Portfoliowert frisch? Die Luecke seit dem letzten Eintrag
                 (Befund 2.376-rollout) - ohne sie ist das Kapital "alt" und
                 der Deckel steht auf dem falschen Betrag
    D  Daten     Frischepruefung aller Quellen (S-1)
    H  Hebel     Schalter je Asset, offene Positionen, Stand des Deckels

⚠️ DESKTOP NIE GEGEN DIE PRODUKTIONSDATENBANK (stehende Regel): am Desktop
schreibt `--nachrechnen` nur mit `--db` auf eine Kopie.
"""
from __future__ import annotations

import argparse
import platform
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent
sys.path.insert(0, str(WURZEL))

DESKTOP = "9900K"
ergebnisse: list = []


def zeile(marke: str, name: str, beleg: str = "") -> None:
    ergebnisse.append((marke, name))
    print("  %s  %s" % (marke, name))
    for z in [x for x in str(beleg or "").splitlines() if x.strip()][:20]:
        print("         " + z)


def ok(name, bedingung, beleg=""):
    zeile("✔" if bedingung else "✖", name, beleg)


def hinweis(name, beleg=""):
    zeile("○", name, beleg)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=None, help="Standard: die Betriebsdatenbank")
    p.add_argument("--nachrechnen", action="store_true",
                   help="fehlende Tage in portfolio_wert_historie schreiben")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    import config
    from database import db as DBM

    pfad = Path(a.db).resolve() if a.db else DBM.DB_PATH
    geraet = platform.node()
    if (a.nachrechnen and geraet.upper() == DESKTOP
            and pfad.resolve() == Path(DBM.DB_PATH).resolve()):
        print("ABBRUCH: am Desktop wird die Betriebsdatenbank nicht beschrieben "
              "- mit --db auf eine Kopie zeigen.")
        return 2
    print("=" * 76)
    print("ROLLOUT PAKET B - Soll-Zustand")
    print("=" * 76)
    print("Geraet    : %s" % geraet)
    print("Datenbank : %s%s" % (pfad, "" if pfad.exists() else "   ✖ FEHLT"))
    try:
        kopf = subprocess.run(["git", "log", "-1", "--format=%h %ci %s"],
                              cwd=WURZEL, capture_output=True, text=True,
                              encoding="utf-8").stdout.strip()
        offen = subprocess.run(["git", "status", "--porcelain"], cwd=WURZEL,
                               capture_output=True, text=True,
                               encoding="utf-8").stdout.strip()
    except OSError:
        kopf, offen = "git nicht aufrufbar", ""
    print("Code      : %s" % kopf)
    if not pfad.exists():
        return 2

    # ------------------------------------------------------------- C
    print("\n--- C  CODE ---")
    try:
        from agent import hebel_aggregat as HAG
        from agent import hebelfuehrung as HF
        ok("C1 Paket-B-Module da: Hebelfuehrung, Aggregat-Deckel mit Variante B",
           hasattr(HAG, "STOP_ANGENOMMEN") and hasattr(HF, "KOPPEL_TAGE")
           and abs(HF.KOPPEL_TAGE - 1.0) < 1e-9,
           "Stop angenommen %s · Fenster %s h" % (HAG.STOP_ANGENOMMEN,
                                                  24 * HF.KOPPEL_TAGE))
    except ImportError as exc:
        ok("C1 Paket-B-Module da", False, "%s - der Pull ist unvollstaendig" % exc)
        return 1
    _lokal = [z for z in offen.splitlines() if z.strip()]
    if _lokal:
        hinweis("C2 lokale Aenderungen im Arbeitsverzeichnis - vor dem Pull "
                "ansehen (config.yaml wird von der App selbst beschrieben)",
                "\n".join(_lokal[:10]))
    else:
        ok("C2 Arbeitsverzeichnis sauber", True)

    # ------------------------------------------------------------- K
    print("\n--- K  CONFIG ---")
    from agent import betraege as BE
    cfg = config.load_config() or {}
    hq = BE.hebel_aus_quote_einstellungen(cfg)
    ok("K1 Hebel aus der Quote: Grenze 5x, ab 2x, Nenner 500 EUR, Deckel 3 %",
       abs(float(hq["hebel_grenze"]) - 5.0) < 1e-9
       and abs(float(hq["hebel_ab"]) - 2.0) < 1e-9
       and abs(float(hq["hebelnenner_eur"]) - 500.0) < 1e-9
       and abs(float(hq["aggregat_anteil"]) - 0.03) < 1e-9,
       "%r" % {k: hq[k] for k in ("aktiv", "hebel_grenze", "hebel_ab",
                                  "hebelnenner_eur", "aggregat_anteil",
                                  "r_min", "r_max")})
    hinweis("K2 Schalter Hebel aus der Quote: %s" % (
        "AN" if hq.get("aktiv") else "AUS - es entsteht kein Hebelgeschaeft"))
    _sw = {n: bool(((cfg.get(n) or {}) if isinstance(cfg.get(n), dict) else {})
                   .get("aktiv")) for n in ("anlass", "marktscan", "hebel_screening")}
    hinweis("K3 Anlass-Sperre %s · alter Marktscan %s · altes Hebel-Screening %s"
            % tuple("an" if _sw[n] else "aus"
                    for n in ("anlass", "marktscan", "hebel_screening")),
            "der alte Marktscan verschickt eigene Mails (2.369); "
            "`hebel_screening.aktiv: false` legt nur das Screening still, "
            "Positionsabgleich und Hebelfuehrung laufen weiter (2.379-schalter)")

    # ------------------------------------------------------------- S
    print("\n--- S  SCHEMA ---")
    conn = sqlite3.connect(str(pfad), timeout=30)
    conn.row_factory = sqlite3.Row
    spalten = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
    fehlen = [c for c in ("instrument", "verlust_am_stop_eur", "strategie")
              if c not in spalten]
    if fehlen and a.nachrechnen:
        from agent import signal_abbildung as SA
        DBM.init_db(conn)
        SA.migriere(conn)
        spalten = {r[1] for r in conn.execute("PRAGMA table_info(signals)")}
        fehlen = [c for c in fehlen if c not in spalten]
    if fehlen:
        hinweis("S1 Spalten fehlen noch: %s - werden beim ersten Lauf der App "
                "angelegt; danach dieses Skript noch einmal" % ", ".join(fehlen))
    else:
        ok("S1 Spalten `instrument`, `verlust_am_stop_eur`, `strategie` vorhanden", True)
        try:
            s = DBM.get_latest_signal(conn, "BTC")
            ok("S2 LESEPROBE: eine Signalzeile laesst sich mit allen Spalten lesen",
               s is not None and hasattr(s, "verlust_am_stop_eur"),
               "%s %s instrument=%r verlust_am_stop_eur=%r"
               % (getattr(s, "symbol", "-"), getattr(s, "action", "-"),
                  getattr(s, "instrument", None),
                  getattr(s, "verlust_am_stop_eur", None)))
        except Exception as exc:                             # noqa: BLE001
            ok("S2 LESEPROBE", False, "%s: %s" % (type(exc).__name__, exc))

    # ------------------------------------------------------------- P
    print("\n--- P  KAPITAL ---")
    from agent import portfolio_historie as PH
    hist = DBM.get_portfolio_wert_historie(conn)
    tage = sorted(z["datum"] for z in hist)
    letzter = tage[-1] if tage else None
    gestern = (datetime.now(timezone.utc).date() - timedelta(days=1))
    luecke = []
    if letzter:
        d = date.fromisoformat(letzter) + timedelta(days=1)
        while d <= gestern:
            luecke.append(d.isoformat())
            d += timedelta(days=1)
    innen = []
    for x, y in zip(tage, tage[1:]):
        if (date.fromisoformat(y) - date.fromisoformat(x)).days > 1:
            innen.append("%s -> %s" % (x, y))
    print("  letzter Eintrag %s · fehlende Tage bis gestern: %d%s"
          % (letzter, len(luecke), (" (%s bis %s)" % (luecke[0], luecke[-1]))
             if luecke else ""))
    if innen:
        hinweis("P0 aeltere Luecken im Verlauf (werden nicht nachgerechnet)",
                "\n".join(innen[-5:]))
    if luecke and a.nachrechnen:
        for tag in luecke:
            try:
                r = PH.schreibe_tageswert(conn, datum=tag)
                print("     %s  %s  Wert %s EUR · Abdeckung %s · fortgeschrieben %s"
                      % (tag, "geschrieben" if r.get("geschrieben") else "NICHT geschrieben",
                         "-" if r.get("wert_eur") is None else "%.0f" % r["wert_eur"],
                         r.get("abdeckung"), r.get("fortgeschrieben")))
            except Exception as exc:                         # noqa: BLE001
                print("     %s  FEHLER %s: %s" % (tag, type(exc).__name__, exc))
        conn.commit()
    elif luecke:
        hinweis("P1 %d Tage fehlen - mit --nachrechnen schreiben (Befund "
                "2.376-rollout)" % len(luecke))
    kap = PH.aktuelles_kapital(conn)
    ok("P2 das Kapital fuer den Hebel ist FRISCH",
       kap.get("verwendbar") and kap.get("zustand") == "frisch",
       "%s EUR · Zustand %s · %s" % ("-" if kap.get("wert_eur") is None
                                     else "%.0f" % kap["wert_eur"],
                                     kap.get("zustand"), kap.get("satz") or ""))

    # ------------------------------------------------------------- D
    print("\n--- D  DATEN ---")
    from agent import datenfrische as DF
    try:
        fr = DF.pruefe(conn)
        auff = DF.auffaellig(fr)
        ok("D1 alle Quellen frisch (oder Symbolliste)", not auff,
           "\n".join(DF.als_text(auff)))
    except Exception as exc:                                 # noqa: BLE001
        ok("D1 Frischepruefung", False, "%s: %s" % (type(exc).__name__, exc))

    # ------------------------------------------------------------- H
    print("\n--- H  HEBEL ---")
    try:
        krypto = [x.symbol for x in config.get_watchlist()
                  if str(getattr(x, "assetklasse", "")).lower() == "krypto"]
        an = {r[0] for r in conn.execute(
            "SELECT symbol FROM asset_hebel_settings WHERE hebel_pruefung_erlaubt = 1")}
        hinweis("H1 Hebel-Schalter je Asset: %d von %d Kryptowerten an - nur dort "
                "entsteht ein Hebelgeschaeft" % (len(an & set(krypto)), len(krypto)),
                "aus: " + ", ".join(sorted(set(krypto) - an)))
    except Exception as exc:                                 # noqa: BLE001
        hinweis("H1 Hebel-Schalter nicht lesbar: %s" % exc)
    try:
        pos = HF.lade(conn)
        hinweis("H2 offene Hebelpositionen: %d" % len(pos),
                "\n".join("%s %s %.1fx · %s" % (t["symbol"], t["richtung"],
                                                t.get("hebel") or 0,
                                                t.get("empfehlung")) for t in pos))
        if kap.get("wert_eur"):
            agg = HAG.aggregat(conn, kapital_eur=float(kap["wert_eur"]),
                               anteil=float(hq["aggregat_anteil"]),
                               hebelnenner_eur=float(hq["hebelnenner_eur"]))
            hinweis("H3 " + agg["satz"],
                    "\n".join("%s %s %.2f EUR - %s" % (x["art"], x["symbol"],
                                                       x["risiko_eur"], x["grund"])
                              for x in agg["posten"]))
    except Exception as exc:                                 # noqa: BLE001
        ok("H2 Hebelfuehrung und Deckel lesbar", False,
           "%s: %s" % (type(exc).__name__, exc))
    conn.close()

    print("\n" + "=" * 76)
    rot = [n for m, n in ergebnisse if m == "✖"]
    print("%d Punkte · %d nicht erfuellt · %d Hinweise"
          % (len(ergebnisse), len(rot), sum(1 for m, _ in ergebnisse if m == "○")))
    for n in rot:
        print("  ✖ " + n)
    print("DANACH: python pruefe_pakete.py  ·  python simuliere_kette.py "
          "--nachweis-paket-b  (arbeitet auf einer Kopie)  ·  App neu starten")
    print("=" * 76)
    return 1 if rot else 0


if __name__ == "__main__":
    raise SystemExit(main())
