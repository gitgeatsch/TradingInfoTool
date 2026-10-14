"""P18b Watchlist = Grundliste + Ergaenzung (14.10.2026, Plan_Asset_Lebenszyklus G-Z8) - Pruefstand an einer WEGWERF-KOPIE der Produktion.

    python Basisinfos/Rechenkern_02_10/p18b_pruefstand.py <Prod-Sicherung tradinginfotool.db | .db.gz>

  W1  App-Start am NB nachgestellt: init_db auf der Kopie legt NUR watchlist_ergaenzung an - alle anderen Tabellen mit gleicher Zeilenzahl
  W2  Teil 0 auf echten Daten: get_watchlist() = die Liste aus config.yaml (bitgleich), alle Eintraege Quelle 'grundliste'
  W3  der AUTOMATISCHE Weg: der Hebel-Importer (auto_add_unknown_hebel_symbols) legt einen neuen Hebel-Coin in der Ergaenzung an
      (Herkunft hebel_import) - config.yaml bitgleich
  W4  der Bitpanda-Bestandsabgleich ordnet den neuen Coin danach zu (Katalog -> Watchlist-Symbol), ohne Neustart
  W5  die Diagnose-Bausteine: watchlist_herkunft / watchlist_ergaenzung zeigen den Eintrag, Punkt 17 meldet ihn als Hinweis
  W6  die Original-Sicherung ist unberuehrt (Pruefsumme), config.yaml bitgleich
"""
import gzip
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

QUELLE = os.path.abspath(sys.argv[1])
WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import config as C  # noqa: E402
import database.db as db  # noqa: E402
import git_stand as GS  # noqa: E402
from api.bitpanda import BitpandaAsset  # noqa: E402
from importer import bitpanda_bestand as BB  # noqa: E402
from importer import bitpanda_margin_positions as MP  # noqa: E402

ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


q_vor, cfg_vor = summe(QUELLE), summe(C.CONFIG_PATH)
T = tempfile.mkdtemp(prefix="p18b_")
KOPIE = os.path.join(T, "prod.db")
if QUELLE.endswith(".gz"):
    with gzip.open(QUELLE, "rb") as f, open(KOPIE, "wb") as g:
        shutil.copyfileobj(f, g)
else:
    shutil.copy(QUELLE, KOPIE)
alt_pfad = db.DB_PATH
db.DB_PATH = Path(KOPIE)
C._config_cache = None


def zahlen(c):
    return {t: c.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
            for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}


try:
    c = sqlite3.connect(KOPIE)
    c.row_factory = sqlite3.Row
    vor = zahlen(c)
    db.init_db(c)
    nach = zahlen(c)
    c.close()
    neu = sorted(set(nach) - set(vor))
    gleich = all(nach[t] == vor[t] for t in vor)
    pruefe("W1", neu == ["watchlist_ergaenzung"] and gleich and nach["watchlist_ergaenzung"] == 0,
           "init_db: neue Tabellen %s · alle %d anderen mit gleicher Zeilenzahl %s" % (neu, len(vor), gleich))
    import yaml
    datei = [e["symbol"] for e in yaml.safe_load(open(C.CONFIG_PATH, encoding="utf-8"))["watchlist"]]
    wl = C.get_watchlist()
    herk = C.watchlist_herkunft()
    pruefe("W2", [a.symbol for a in wl] == datei and set(q for q, _ in herk.values()) == {"grundliste"},
           "%d Eintraege wie config.yaml · Quellen %s" % (len(wl), sorted(set(q for q, _ in herk.values()))))
    # W3: eine offene Hebelposition der Kopie auf einen unbekannten Coin umgestellt (nur in der Wegwerf-Kopie)
    c = sqlite3.connect(KOPIE)
    pid = c.execute("SELECT id FROM hebel_positions WHERE geschlossen_am IS NULL ORDER BY id LIMIT 1").fetchone()
    c.execute("UPDATE hebel_positions SET symbol='ZZHEB' WHERE id=?", (pid[0],))
    c.commit()
    c.close()
    c = sqlite3.connect(KOPIE)
    c.row_factory = sqlite3.Row
    hinzu = MP.auto_add_unknown_hebel_symbols(c, C.get_watchlist(), [BitpandaAsset("ZZHEB", "Zz Hebel", "cryptocoin")], None)
    c.close()
    h3 = C.watchlist_herkunft()
    pruefe("W3", hinzu == ["ZZHEB"] and h3.get("ZZHEB") == ("ergaenzung", "hebel_import") and summe(C.CONFIG_PATH) == cfg_vor,
           "Hebel-Importer: hinzugefuegt %s · Herkunft %s · config.yaml %s" % (hinzu, h3.get("ZZHEB"),
                                                                              "bitgleich" if summe(C.CONFIG_PATH) == cfg_vor else "GEAENDERT"))
    # W4: der Bestandsabgleich ordnet ueber die Watchlist-Symbole zu
    sym = {a.symbol for a in C.get_watchlist()}

    class _E:
        isin = None
        symbol = "ZZHEB"
    pruefe("W4", BB.zuordnen(_E(), sym, {}) == "ZZHEB", "Katalog ZZHEB -> %s (ohne Neustart, get_watchlist liest die Ergaenzung je Aufruf)" %
           BB.zuordnen(_E(), sym, {}))
    # W5: Diagnose-Bausteine + Punkt 17
    stamm = {a.symbol: {"assetklasse": a.assetklasse, "rolle": a.rolle, "beobachtungsstatus": a.beobachtungsstatus, "name": a.name,
                        "coingecko_id": a.coingecko_id, "quelle": h3[a.symbol][0], "herkunft": h3[a.symbol][1]} for a in C.get_watchlist()}
    gs = {"head": GS.lesen().get("head"), "geaendert": [], "stash": [], "fehler": [], "quelle_head": "git", "zweig": "main"}
    m, i = GS.bewerte({"git_stand": gs, "watchlist_stammdaten": stamm, "watchlist_ergaenzung": C.watchlist_ergaenzung()})
    pruefe("W5", not [x for x in m if "Watchlist" in x] and any("Ergaenzung am NB: ZZHEB (Herkunft hebel_import)" in x for x in i)
           and len(C.watchlist_ergaenzung()) == 1, "Punkt 17: Auffaelligkeiten %s · Hinweis %s" % (
               [x for x in m if "Watchlist" in x], [x for x in i if "ZZHEB" in x]))
finally:
    db.DB_PATH = alt_pfad
    C._config_cache = None
pruefe("W6", summe(QUELLE) == q_vor and summe(C.CONFIG_PATH) == cfg_vor, "Original-Sicherung und config.yaml unberuehrt")
shutil.rmtree(T, ignore_errors=True)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
