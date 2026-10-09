"""H15 Pruefstand (09.10.2026, Schritt7 §23.29): die Hebelfuehrung echter Positionen im Abgleich-Lauf - am PFAD
`scheduler.background._hebelfuehrung_lauf`, an einer WEGWERF-Datenbank, mit Ersatz-Versand (keine Mail, kein Netz).

    python Basisinfos/Rechenkern_02_10/h15_pruefstand.py

  P1  Abstand ueber der Schwelle (Kurs 70.000)               -> keine Mail
  P2  Abstand 13 % (Kurs 62.000)                              -> Mail LIQUIDATION NAHE, Stufe 15 %
  P3  gleicher Tag, 12 % (Kurs 61.500)                        -> keine Mail (dieselbe Stufe)
  P4  8,6 % (Kurs 59.000)                                     -> Mail, Stufe 10 %
  P5  3,7 % (Kurs 56.000), Versand SCHEITERT                  -> nicht vermerkt; naechster Lauf mit Versand -> Mail Stufe 5 %
  P6  Kurs 53.000 (jenseits der Liquidation)                  -> Mail LIQUIDATION ERREICHT
  P7  naechster Tag: dieselbe Stufe ist wieder meldepflichtig
  P8  Schalter aus                                            -> kein Lauf
  P9  ohne Ersatz-Versand am Desktop                          -> uebersprungen (betrieb_erlaubt), kein Vermerk
  P10 Mailtext: Einstand, Liquidation, Abstand, 'Entscheidung liegt bei dir'
  P11 SEITENEFFEKT: die Standard-DB data/tradinginfotool.db ist unveraendert (Zeitstempel und Groesse)
"""
import os
import sqlite3
import sys
import tempfile

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import agent.hebelfuehrung as HF          # noqa: E402
import agent.regel0_groesse as G          # noqa: E402
import database.db as DB                  # noqa: E402
import scheduler.background as BG         # noqa: E402

STANDARD = os.path.join(WURZEL, "data", "tradinginfotool.db")
ok = n = 0


def pruefe(name, gut, info=""):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-4s %s  %s" % (name, "ok" if gut else "FEHLER", info))


def main():
    vorher = (os.path.getmtime(STANDARD), os.path.getsize(STANDARD)) if os.path.exists(STANDARD) else None
    d = tempfile.mkdtemp(prefix="h15_")
    pfad = os.path.join(d, "wegwerf.db")
    c = sqlite3.connect(pfad)
    c.row_factory = sqlite3.Row                     # wie im Betrieb (database.db.get_connection)
    DB.init_db(c)
    spalten = [r[1] for r in c.execute("PRAGMA table_info(hebel_positions)")]
    werte = {"symbol": "BTC", "richtung": "LONG", "status": "offen", "eroeffnet_am": "2026-10-09T04:38:53+00:00", "hebel_effektiv": 3.0,
             "positionswert_eur": 1500.0, "kreditbetrag_eur": 1000.0, "eigenkapital_eur": 500.0, "positionsmenge": 0.02038541}
    werte = {k: v for k, v in werte.items() if k in spalten}
    for cid, name, typ, notnull, vorgabe, pk in c.execute("PRAGMA table_info(hebel_positions)").fetchall():
        if notnull and vorgabe is None and not pk and name not in werte:      # Pflichtfelder aus dem SCHEMA, nicht aufgezaehlt
            werte[name] = 1759984733 if "unix" in name else (0 if "INT" in (typ or "").upper() or "REAL" in (typ or "").upper() else "")
    c.execute("INSERT INTO hebel_positions (%s) VALUES (%s)" % (", ".join(werte), ", ".join("?" * len(werte))), list(werte.values()))
    c.commit()
    c.close()

    def fabrik():
        x = sqlite3.connect(pfad)
        x.row_factory = sqlite3.Row                 # wie im Betrieb
        return x

    zaehler = [0]

    def kurs(k):
        zaehler[0] += 1
        x = sqlite3.connect(pfad)
        x.execute("INSERT INTO price_cache (symbol, coingecko_id, price_usd, price_eur, fetched_at) VALUES ('BTC','bitcoin',?,?,?)",
                  (k * 1.1, k, "2026-10-09T08:%02d:00+00:00" % zaehler[0]))
        x.commit()
        x.close()

    post = []

    def versand_ok(b, t):
        post.append((b, t)); return True

    def versand_fehl(b, t):
        post.append(("FEHLGESCHLAGEN " + b, t)); return False

    kurs(70000); r = BG._hebelfuehrung_lauf(fabrik, versand=versand_ok)
    pruefe("P1", r.get("gelaufen") and not r.get("mail"), "Abstand %s" % r.get("empfehlungen"))
    kurs(62000); r = BG._hebelfuehrung_lauf(fabrik, versand=versand_ok)
    pruefe("P2", r.get("mail") and "LIQUIDATION NAHE BTC" in r["mail"][0] and r["empfehlungen"][0][3] == 0.15 and r.get("zugestellt"),
           r["mail"][0] if r.get("mail") else "-")
    mail_p2 = r["mail"][1] if r.get("mail") else ""
    kurs(61500); r = BG._hebelfuehrung_lauf(fabrik, versand=versand_ok)
    pruefe("P3", r.get("gelaufen") and not r.get("mail"), "Stufe %s" % (r["empfehlungen"][0][3] if r.get("empfehlungen") else "-"))
    kurs(59000); r = BG._hebelfuehrung_lauf(fabrik, versand=versand_ok)
    pruefe("P4", r.get("mail") and r["empfehlungen"][0][3] == 0.1, "Stufe %s" % (r["empfehlungen"][0][3] if r.get("empfehlungen") else "-"))
    kurs(56000); r1 = BG._hebelfuehrung_lauf(fabrik, versand=versand_fehl)
    r2 = BG._hebelfuehrung_lauf(fabrik, versand=versand_ok)
    pruefe("P5", r1.get("mail") and r1.get("zugestellt") is False and r2.get("mail") and r2["empfehlungen"][0][3] == 0.05 and r2.get("zugestellt"),
           "erst nicht zugestellt, dann gemeldet")
    kurs(53000); r = BG._hebelfuehrung_lauf(fabrik, versand=versand_ok)
    pruefe("P6", r.get("mail") and "LIQUIDATION ERREICHT" in r["mail"][0], r["mail"][0] if r.get("mail") else "-")
    x = fabrik()
    t13 = HF.lade(x, nahe_grenze=0.15, jetzt="2026-10-10T08:00:00+00:00")
    x.execute("DELETE FROM price_cache"); x.commit()
    x.execute("INSERT INTO price_cache (symbol, coingecko_id, price_usd, price_eur, fetched_at) VALUES ('BTC','bitcoin',1,62000,'2026-10-10T08:00:00+00:00')")
    x.commit()
    t13 = HF.lade(x, nahe_grenze=0.15, jetzt="2026-10-10T08:00:00+00:00")
    heute = HF.neue_meldungen(x, t13, tag="2026-10-09")
    morgen = HF.neue_meldungen(x, t13, tag="2026-10-10")
    x.close()
    pruefe("P7", not heute and len(morgen) == 1, "heute %d · morgen %d" % (len(heute), len(morgen)))
    alt = G.lade
    try:
        G.lade = lambda pfad=None: dict(alt(pfad), hebelfuehrung_aktiv=False)
        r = BG._hebelfuehrung_lauf(fabrik, versand=versand_ok)
    finally:
        G.lade = alt
    pruefe("P8", not r.get("gelaufen") and r.get("grund") == "Schalter aus", str(r.get("grund")))
    x = fabrik(); vor = x.execute("SELECT COUNT(*) FROM job_laeufe WHERE job_id LIKE 'hebelfuehrung:%'").fetchone()[0]; x.close()
    r = BG._hebelfuehrung_lauf(fabrik)
    x = fabrik(); nach = x.execute("SELECT COUNT(*) FROM job_laeufe WHERE job_id LIKE 'hebelfuehrung:%'").fetchone()[0]; x.close()
    pruefe("P9", not r.get("gelaufen") and vor == nach, "Grund: %s" % r.get("grund"))
    pruefe("P10", all(s in mail_p2 for s in ("Einstand", "Liquidation", "13,0 %", "Entscheidung liegt bei dir")), "Mailtext P2 geprueft")
    nachher = (os.path.getmtime(STANDARD), os.path.getsize(STANDARD)) if os.path.exists(STANDARD) else None
    pruefe("P11", vorher == nachher, "Standard-DB %s" % ("unveraendert" if vorher == nachher else "VERAENDERT"))
    print("\nMail P2 (Auszug):\n" + "\n".join(mail_p2.splitlines()[:14]))
    print("\n%d von %d bestanden" % (ok, n))
    return ok == n


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
