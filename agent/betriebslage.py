# -*- coding: utf-8 -*-
"""DIE BETRIEBSLAGE - eine Quelle fuer Statusseite (remote/status.py) und Teilexport (nb_teilexport_betriebsdaten.py).

P9 (10.10.2026, Plan_Asset_Lebenszyklus_14_09.md G-L/G-N/G-O; Nutzer: *"mit Statusseite starten"*). Vorher rechnete der Teilexport
alles inline, die Statusseite zeigte nichts zu REGEL0, H15, Schaltern und Kontrollen - zwei Werkzeuge, die auseinanderlaufen
konnten. Hier stehen die ABFRAGEN; beide Aufrufer formatieren nur noch.

REGELN (CLAUDE.md, Produktion am NB):
  * NUR LESEN. Fremde Dateien (regel0_signale.db, Stunden-/Markpreis-Dateien) ausschliesslich ``mode=ro``; die Produktions-DB ueber
    die Verbindung des Aufrufers (Statusseite) oder ``mode=ro`` (Teilexport). Kein Netz, kein Schreiben, keine Mail.
  * Jede Funktion faengt nichts still ab - der Aufrufer entscheidet (Statusseite: ``_safe``; Teilexport: ⛔-Zeile).
"""
from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, timezone

HIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATEN = os.path.join(HIER, "data")
KONTROLLEN_DATEI = os.path.join(HIER, "Basisinfos", "nb_kontrollen.yaml")


def ro(pfad: str) -> sqlite3.Connection:
    return sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True, timeout=5)


def tabellen(c) -> list[str]:
    return [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]


def _spalten(c, t) -> set:
    return {r[1] for r in c.execute('PRAGMA table_info("%s")' % t)}


# ══ Hebel ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def hebel_positionen(c) -> dict:
    """Status-Zaehlung und offene Positionen aus ``hebel_positions`` (wie Teilexport Abschnitt HEBEL-POSITIONEN)."""
    st = c.execute("SELECT status, COUNT(*) FROM hebel_positions GROUP BY status ORDER BY 2 DESC").fetchall()
    offen = c.execute("SELECT symbol, richtung, status, hebel_effektiv, positionswert_eur, eigenkapital_eur, kreditbetrag_eur, "
                      "eroeffnet_am, liquidationspreis_geschaetzt_eur FROM hebel_positions WHERE geschlossen_am IS NULL "
                      "ORDER BY eroeffnet_am").fetchall()
    return {"je_status": [(s, n) for s, n in st], "offen": [tuple(r) for r in offen],
            "summe_wert": sum(r[4] or 0 for r in offen), "summe_ek": sum(r[5] or 0 for r in offen),
            "summe_kredit": sum(r[6] or 0 for r in offen)}


def hebelfuehrung_gemeldet(c, n: int = 8) -> list:
    """Was H15 gemeldet hat (Schluessel hebelfuehrung:<id>:<Empfehlung>:<Stufe>:<Tag>), juengste zuerst."""
    return [tuple(r) for r in c.execute("SELECT job_id, zuletzt_am FROM job_laeufe WHERE job_id LIKE 'hebelfuehrung:%' "
                                        "ORDER BY zuletzt_am DESC LIMIT ?", (n,)).fetchall()]


def portfoliowert(c, n: int = 3) -> list:
    return [tuple(r) for r in c.execute("SELECT datum, wert_eur, cash_eur FROM portfolio_wert_historie ORDER BY datum DESC LIMIT ?",
                                        (n,)).fetchall()]


def hebel_fuehrung_jetzt(conn) -> list[dict]:
    """Die H15-Sicht JETZT je offener Position: Kurs, Liquidation, Abstand, Empfehlung, Warnstufe (``hebelfuehrung.lade``, nur lesend).
    ``conn`` braucht ``row_factory = sqlite3.Row`` (die Produktionsverbindung der Statusseite)."""
    from agent import hebelfuehrung as HF
    from agent import regel0_groesse as G

    w = G.lade()
    aus = []
    for t in HF.lade(conn, nahe_grenze=float(w.get("liquidations_warnung_abstand") or HF.LIQ_NAHE_GRENZE)):
        aus.append({"symbol": t.get("symbol"), "richtung": t.get("richtung"), "hebel": t.get("hebel"),
                    "kurs_eur": t.get("kurs_eur"), "liquidation_eur": t.get("liquidation_eur"),
                    "abstand": t.get("abstand_liquidation"), "empfehlung": t.get("empfehlung"), "stufe": t.get("nahe_stufe"),
                    "eigenkapital_eur": t.get("eigenkapital_eur"), "positionswert_eur": t.get("positionswert_eur"),
                    "eroeffnet_am": t.get("eroeffnet_am"), "grund": ((t.get("gruende") or [""])[0] or "")[:200]})
    return aus


# ══ REGEL0 ═════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def nachlader(daten: str = DATEN) -> dict:
    """Je REGEL0-Datei: Stand, Symbole auf Stand, die letzten drei Laeufe (wie Teilexport REGEL0-DATENBASIS)."""
    import agent.regel0_nachlader as NL

    ok, grund = NL.betrieb_erlaubt(daten)
    dateien = []
    for d in NL.DATEIEN:
        p = os.path.join(daten, d)
        if not os.path.exists(p):
            dateien.append({"datei": d, "fehlt": True})
            continue
        c = ro(p)
        try:
            tab = "markpreis" if d.startswith("markpreis") else "stundenkurse"
            je = [m for (m,) in c.execute("SELECT MAX(stunde) FROM %s GROUP BY symbol" % tab)]
            hoch = max(je) if je else None
            aktuell = sum(1 for m in je if hoch and NL._ms(m) >= NL._ms(hoch) - 2 * NL.H_MS)
            laeufe = [tuple(r) for r in c.execute("SELECT * FROM _nachlader ORDER BY rowid DESC LIMIT 3")] \
                if "_nachlader" in tabellen(c) else None
        finally:
            c.close()
        dateien.append({"datei": d, "fehlt": False, "stand": hoch, "aktuell": aktuell, "gesamt": len(je), "laeufe": laeufe})
    return {"schreibt": ok, "grund": grund, "dateien": dateien}


def nachlader_kurz(daten: str = DATEN) -> dict:
    """Fuer die Statusseite: je REGEL0-Datei nur der LETZTE Nachladerlauf aus ``_nachlader`` - ohne den ``GROUP BY symbol`` ueber die
    ganze Kursreihe, den ``nachlader()`` fuer den Teilexport rechnet (auf stundenkurse_alle.db Sekunden, nicht Millisekunden)."""
    import agent.regel0_nachlader as NL

    ok, grund = NL.betrieb_erlaubt(daten)
    dateien = []
    for d in NL.DATEIEN:
        p = os.path.join(daten, d)
        if not os.path.exists(p):
            dateien.append({"datei": d, "fehlt": True})
            continue
        c = ro(p)
        try:
            r = c.execute("SELECT * FROM _nachlader ORDER BY rowid DESC LIMIT 1").fetchone() if "_nachlader" in tabellen(c) else None
        finally:
            c.close()
        dateien.append({"datei": d, "fehlt": False, "letzter_lauf": tuple(r) if r else None})
    return {"schreibt": ok, "grund": grund, "dateien": dateien}


def regel0_rechnung(daten: str = DATEN) -> dict:
    """Modelldateien, letzte Laeufe, Signal- und Mailzaehler, entfallene Erinnerungen, juengste Signale (Teilexport REGEL0-RECHNUNG)."""
    md = os.path.join(daten, "regel0_modelle")
    pk = sorted(f for f in os.listdir(md) if f.endswith(".pkl")) if os.path.isdir(md) else []
    modelle = []
    for f in pk:
        ps = os.path.join(md, f + ".sha256")
        modelle.append((f.replace("regel0_modell_", "").replace(".pkl", ""),
                        open(ps, encoding="utf-8").read().strip()[:12] if os.path.exists(ps) else None))
    ab = os.path.join(daten, "regel0_signale.db")
    erg = {"modelle": modelle, "ablage": os.path.exists(ab)}
    if not erg["ablage"]:
        return erg
    c = ro(ab)
    try:
        erg["laeufe"] = [tuple(r) for r in c.execute("SELECT jetzt, sekunden, pakete, aktiv, frisch, veraltet, nicht_im_handel, neu, "
                                                       "endgueltig, meldung FROM lauf ORDER BY jetzt DESC LIMIT 6")]
        n_ = c.execute("SELECT COUNT(*), SUM(hebel_schalter=1) FROM signal").fetchone()
        erg["signale_gesamt"], erg["schalter_an"] = n_[0], n_[1] or 0
        sp_ = _spalten(c, "signal")
        erg["mail_spalten"] = "mail_signal_am" in sp_
        if erg["mail_spalten"]:
            erg["mails"] = tuple(c.execute("SELECT COUNT(mail_signal_am), COUNT(mail_korrektur_am), COUNT(mail_erinnerung_am) "
                                           "FROM signal").fetchone())
            if "mail_verpasst_am" in sp_:
                erg["verpasst"] = c.execute("SELECT COUNT(*) FROM signal WHERE mail_verpasst_am IS NOT NULL").fetchone()[0]
                erg["nachgeholt"] = tuple(c.execute("SELECT COUNT(*), GROUP_CONCAT(signalstunde, ', ') FROM (SELECT signalstunde FROM "
                                                    "nachgeholt ORDER BY signalstunde DESC LIMIT 12)").fetchone()) \
                    if "nachgeholt" in tabellen(c) else (0, "")
            if "erinnerung_entfallen_am" in sp_:
                erg["entfallen"] = [tuple(r) for r in c.execute(
                    "SELECT bitpanda, symbol, ausstieg, erinnerung_entfallen_am, erinnerung_grund FROM signal "
                    "WHERE erinnerung_entfallen_am IS NOT NULL ORDER BY erinnerung_entfallen_am DESC LIMIT 8")]
        erg["juengste"] = [tuple(r) for r in c.execute(
            "SELECT symbol, bitpanda, signalstunde, einstieg, vh, stufe_vorlaeufig, stufe, p5, hebel_schalter%s FROM signal "
            "ORDER BY signalstunde DESC LIMIT 15" % (", mail_signal_am, mail_korrektur_am, mail_erinnerung_am" if erg["mail_spalten"] else ""))]
    finally:
        c.close()
    return erg


def regel0_heute(daten: str = DATEN, tag: str | None = None) -> dict:
    """Fuer die Statusseite: Signale und Mails des UTC-Tages, letzter Lauf, faellige/entfallene Erinnerungen."""
    tag = tag or datetime.now(timezone.utc).date().isoformat()
    ab = os.path.join(daten, "regel0_signale.db")
    if not os.path.exists(ab):
        return {"ablage": False}
    c = ro(ab)
    try:
        sp = _spalten(c, "signal")
        lauf = c.execute("SELECT jetzt, sekunden, aktiv, frisch, veraltet, nicht_im_handel, meldung FROM lauf ORDER BY jetzt DESC LIMIT 1").fetchone()
        heute = c.execute("SELECT COUNT(*), SUM(hebel_schalter=1) FROM signal WHERE substr(signalstunde,1,10)=?", (tag,)).fetchone()
        erg = {"ablage": True, "tag": tag, "letzter_lauf": tuple(lauf) if lauf else None,
               "signale_heute": heute[0] or 0, "schalter_an_heute": heute[1] or 0}
        if "mail_signal_am" in sp:
            erg["gemailt_heute"] = c.execute("SELECT COUNT(*) FROM signal WHERE substr(mail_signal_am,1,10)=?", (tag,)).fetchone()[0]
        for sp_n, k in (("mail_gesperrt_am", "gesperrt_heute"), ("mail_verpasst_am", "verpasst_heute"),
                        ("mail_korrektur_am", "korrektur_heute"), ("erinnerung_entfallen_am", "entfallen_heute"),
                        ("mail_erinnerung_am", "erinnerung_heute")):
            if sp_n in sp:
                erg[k] = c.execute("SELECT COUNT(*) FROM signal WHERE substr(%s,1,10)=?" % sp_n, (tag,)).fetchone()[0]
        erg["liste_heute"] = [tuple(r) for r in c.execute(
            "SELECT symbol, signalstunde, stufe_vorlaeufig, stufe, hebel_schalter%s FROM signal WHERE substr(signalstunde,1,10)=? "
            "AND hebel_schalter=1 ORDER BY signalstunde DESC LIMIT 12" % (", mail_signal_am" if "mail_signal_am" in sp else ""), (tag,))]
    finally:
        c.close()
    return erg


def pruefblock(daten: str = DATEN) -> dict:
    """LLM-Pruefblock: Aufrufe je Tag, Zeilen je Rolle/Fassung, Urteile, Fehler, juengste Zeilen (Teilexport REGEL0-PRUEFUNG)."""
    ab = os.path.join(daten, "regel0_signale.db")
    c = ro(ab) if os.path.exists(ab) else None
    if c is None:
        return {"lauf": False}
    try:
        if "pruefung" not in tabellen(c):
            return {"lauf": False}
        erg = {"lauf": True, "zeilen": c.execute("SELECT COUNT(*) FROM pruefung").fetchone()[0]}
        _auf = "aufrufe" in _spalten(c, "pruefung")
        erg["je_tag"] = [tuple(r) for r in c.execute(
            "SELECT tag_pazifik, %s, COUNT(*) FROM pruefung WHERE gefragt=1 GROUP BY tag_pazifik ORDER BY tag_pazifik DESC LIMIT 5"
            % ("SUM(COALESCE(aufrufe, 1))" if _auf else "COUNT(*)"))]
        erg["je_rolle"] = [tuple(r) for r in c.execute(
            "SELECT rolle, fassung, COUNT(*), SUM(urteil IS NOT NULL), SUM(fehler IS NOT NULL), ROUND(AVG(CASE WHEN gefragt=1 "
            "THEN sekunden END), 1) FROM pruefung GROUP BY rolle, fassung ORDER BY rolle")]
        erg["urteile"] = [tuple(r) for r in c.execute(
            "SELECT rolle, urteil, COUNT(*) FROM pruefung WHERE urteil IS NOT NULL GROUP BY rolle, urteil ORDER BY rolle, 3 DESC")]
        erg["fehler"] = [tuple(r) for r in c.execute(
            "SELECT fehler, COUNT(*) FROM pruefung WHERE fehler IS NOT NULL GROUP BY fehler ORDER BY 2 DESC LIMIT 6")]
        erg["juengste"] = [tuple(r) for r in c.execute(
            "SELECT symbol, signalstunde, rolle, urteil, fehler FROM pruefung ORDER BY am DESC LIMIT 9")]
    finally:
        c.close()
    return erg


def ankuendigungen(daten: str = DATEN) -> dict:
    """O29: Schalter, Laeufe, Meldungen, Zuordnungen, Vorwaertsprotokoll (Teilexport BINANCE-ANKUENDIGUNGEN; K-ANK-1)."""
    import agent.regel0_groesse as G

    erg = {"an": bool(G.lade().get("ankuendigung_aktiv")), "lauf": False}
    ab = os.path.join(daten, "regel0_signale.db")
    c = ro(ab) if os.path.exists(ab) else None
    if c is None:
        return erg
    try:
        if "ankuendigung_lauf" not in tabellen(c):
            return erg
        erg["lauf"] = True
        n_l, n_ok = c.execute("SELECT COUNT(*), SUM(ok) FROM ankuendigung_lauf").fetchone()
        erg["laeufe"], erg["fehlerfrei"] = n_l, n_ok or 0
        erg["letzte"] = [tuple(r) for r in c.execute(
            "SELECT am, ok, neu, zuordnungen, protokolliert, fehler, sekunden FROM ankuendigung_lauf ORDER BY am DESC LIMIT 4")]
        erg["meldungen"], erg["zuordnungen"] = c.execute(
            "SELECT (SELECT COUNT(*) FROM ankuendigung), (SELECT COUNT(*) FROM ankuendigung_ereignis)").fetchone()
        erg["je_art"] = [tuple(r) for r in c.execute("SELECT art, COUNT(*) FROM ankuendigung_ereignis GROUP BY art ORDER BY 2 DESC")]
        if "signal_ereignis" in tabellen(c):
            n_s, n_e = c.execute("SELECT COUNT(*), SUM(arten != 'keins') FROM signal_ereignis").fetchone()
            n_o = c.execute("SELECT COUNT(*) FROM signal s LEFT JOIN signal_ereignis e ON e.symbol=s.symbol AND "
                            "e.signalstunde=s.signalstunde WHERE e.symbol IS NULL").fetchone()[0]
            erg["protokoll"] = (n_s, n_e or 0, n_o)
            erg["mit_ereignis"] = [tuple(r) for r in c.execute(
                "SELECT symbol, signalstunde, arten FROM signal_ereignis WHERE arten != 'keins' ORDER BY signalstunde DESC LIMIT 6")]
    finally:
        c.close()
    return erg


def neuaufnahme_und_abgleich(daten: str = DATEN, prod: str | None = None) -> dict:
    """Neuaufnahme (3 Laeufe), Datenbestand, gesperrte Mails, Hebel-Schalter ohne Daten (Teilexport REGEL0-NEUAUFNAHME)."""
    import csv as _csv

    erg = {"neuaufnahme": None, "gesperrt": None, "ohne_daten": None}
    pa = os.path.join(daten, "stundenkurse_alle.db")
    bestand = set()
    if os.path.exists(pa):
        c = ro(pa)
        try:
            if "_neuaufnahme" in tabellen(c):
                erg["neuaufnahme"] = [tuple(r) for r in c.execute("SELECT * FROM _neuaufnahme ORDER BY lauf_am DESC LIMIT 3")]
            else:
                erg["neuaufnahme"] = []
            bestand = {x for (x,) in c.execute("SELECT symbol FROM _quelle")}
        finally:
            c.close()
    pm = os.path.join(daten, "stundenkurse.db")
    if os.path.exists(pm):
        c = ro(pm)
        try:
            bestand |= {x for (x,) in c.execute("SELECT DISTINCT symbol FROM stundenkurse")}
        finally:
            c.close()
    ab = os.path.join(daten, "regel0_signale.db")
    if os.path.exists(ab):
        c = ro(ab)
        try:
            if "mail_gesperrt_am" in _spalten(c, "signal"):
                erg["gesperrt"] = [tuple(r) for r in c.execute(
                    "SELECT symbol, bitpanda, signalstunde, abgleich FROM signal WHERE mail_gesperrt_am IS NOT NULL "
                    "ORDER BY signalstunde DESC LIMIT 10")]
        finally:
            c.close()
    prod = prod or os.path.join(daten, "tradinginfotool.db")
    if os.path.exists(prod):
        zu = {}
        pz = os.path.join(HIER, "Basisinfos", "symbol_zuordnung.csv")
        if os.path.exists(pz):
            for r in _csv.DictReader(open(pz, encoding="utf-8"), delimiter=";"):
                zu[r["bitpanda"]] = None if r["markt"] == "gesperrt" else r["binance"]
        c = ro(prod)
        try:
            an = [r[0] for r in c.execute("SELECT symbol FROM asset_hebel_settings WHERE hebel_pruefung_erlaubt=1 ORDER BY symbol")]
        finally:
            c.close()
        erg["ohne_daten"] = [s for s in an if zu.get(s, s) not in bestand]
    return erg


# ══ Schalter, Jobs, Bestand, Kontingent ════════════════════════════════════════════════════════════════════════════════════
SCHALTER = ("testwoche_freigegeben", "alter_hebelweg_aus", "spot_kette_angehalten", "ankuendigung_aktiv", "hebelfuehrung_aktiv")


def schalter() -> dict:
    from agent import regel0_groesse as G

    w = G.lade()
    return {k: w.get(k) for k in SCHALTER}


def jobs(c) -> list:
    """Letzter erfolgreicher Lauf je Job (``job_laeufe`` ohne die H15-Meldeschluessel), juengste zuerst."""
    return [tuple(r) for r in c.execute("SELECT job_id, zuletzt_am FROM job_laeufe WHERE job_id NOT LIKE 'hebelfuehrung:%' "
                                        "ORDER BY zuletzt_am DESC").fetchall()]


def bestand_meta(c) -> dict:
    """Zeitpunkte und Marken des Bitpanda-Abgleichs (nur lesen)."""
    def meta(k):
        r = c.execute("SELECT value FROM meta WHERE key=?", (k,)).fetchone()
        return r[0] if r else None
    return {"bestand_synced_at": meta("bitpanda_holdings_synced_at"), "salden_fassung": meta("bitpanda_wallet_salden_fassung"),
            "buchungen_stand": meta("bitpanda_buchungen_stand"), "hebel_synced_at": meta("hebel_positions_synced_at")}


def gemini_je_verbraucher(daten: str = DATEN, c_prod=None) -> dict:
    """Gemini-Verbrauch des Pazifik-Tages je VERBRAUCHER: REGEL0-Pruefblock (Ablage), Rest aus ``api_call_kontingent_taeglich``.
    Die Seite zeigte bisher alles unter *Rollen-Kette* (Befund G-C)."""
    aus = {}
    ab = os.path.join(daten, "regel0_signale.db")
    if os.path.exists(ab):
        c = ro(ab)
        try:
            if "pruefung" in tabellen(c):
                r = c.execute("SELECT tag_pazifik, SUM(COALESCE(aufrufe, 1)) FROM pruefung WHERE gefragt=1 GROUP BY tag_pazifik "
                              "ORDER BY tag_pazifik DESC LIMIT 1").fetchone()
                aus["regel0_pruefblock"] = {"tag": r[0], "aufrufe": r[1]} if r else {"tag": None, "aufrufe": 0}
        finally:
            c.close()
    if c_prod is not None:
        try:
            aus["je_quelle_heute"] = [tuple(r) for r in c_prod.execute(
                "SELECT source, anzahl FROM api_call_kontingent_taeglich WHERE tag=(SELECT MAX(tag) FROM api_call_kontingent_taeglich) "
                "ORDER BY anzahl DESC").fetchall()]
        except sqlite3.Error:
            aus["je_quelle_heute"] = None
    return aus


# ══ Parameter (nur lesend; Art: wahl / gemessen / schaetzung) ═════════════════════════════════════════════════════════════
def parameter(daten: str = DATEN) -> list[dict]:
    """Die zentralen Parameter des NEUEN Systems mit Datei und Art (G-L). Geaendert wird nur ueber die Datei."""
    from agent import regel0_groesse as G
    from agent import regel0_rechnung as R
    from agent import hebelfuehrung as HF

    w = G.lade()
    aus = []

    def p(gruppe, name, wert, datei, art, beleg=""):
        aus.append({"gruppe": gruppe, "name": name, "wert": wert, "datei": datei, "art": art, "beleg": beleg})

    p("REGEL0 Regel", "Regelversion", R.REGELVERSION, "agent/regel0_rechnung.py", "gemessen", "E-45")
    p("REGEL0 Regel", "Schwelle s", R.SCHWELLE, "agent/regel0_rechnung.py", "gemessen", "2.688 (auf 2024 gewaehlt)")
    p("REGEL0 Regel", "Ruhe nach Ereignis (h)", R.RUHE, "agent/regel0_rechnung.py", "gemessen", "2.694")
    p("REGEL0 Regel", "Haltedauer hoechstens (h)", R.HMAX, "agent/regel0_rechnung.py", "gemessen", "2.689 (Tageshandel)")
    md = os.path.join(daten, "regel0_modelle")
    pk = sorted(f for f in os.listdir(md) if f.endswith(".pkl")) if os.path.isdir(md) else []
    p("REGEL0 Modell", "Modelldatei", pk[-1] if pk else "-", "data/regel0_modelle/", "gemessen", "Monatstraining")
    for k in ("positionswert_eur", "einsatz_min_eur", "einsatz_max_eur", "richtwert_gleichzeitig", "sperre_ab_richtwert"):
        p("REGEL0 Groesse", k, w.get(k), "Basisinfos/regel0_betrieb.yaml", "wahl", "E-44")
    for k in SCHALTER:
        p("Schalter", k, w.get(k), "Basisinfos/regel0_betrieb.yaml", "wahl")
    p("H15", "liquidations_warnung_abstand", w.get("liquidations_warnung_abstand"), "Basisinfos/regel0_betrieb.yaml", "wahl", "E-88")
    p("H15", "Warnstufen (Anteile der Schwelle)", HF.LIQ_STUFEN, "agent/hebelfuehrung.py", "wahl", "E-88")
    try:
        from agent.entscheidungsrechnung import GRENZEN
        p("H15", "Liquidationsmarge", GRENZEN.get("liquidations_marge"), "Basisinfos/config.yaml risiko.hebel", "schaetzung",
          "RM-11 (Bitpanda veroeffentlicht keine Formel)")
    except Exception:                                                      # noqa: BLE001
        pass
    try:
        import yaml
        llm = yaml.safe_load(open(os.path.join(HIER, "Basisinfos", "regel0_llm.yaml"), encoding="utf-8")) or {}
        for k in ("fassung", "modell", "stimmen", "zeitgrenze_s", "tageslimit_aufrufe", "max_signale_je_lauf"):
            p("LLM-Pruefblock", k, llm.get(k), "Basisinfos/regel0_llm.yaml", "wahl", "E-80, N4/N5")
    except Exception:                                                      # noqa: BLE001
        pass
    try:
        import messnorm
        p("Messstandard", "Standardzeile", messnorm.standardzeile(), "messnorm.py", "gemessen", "08.09.2026")
    except Exception:                                                      # noqa: BLE001
        pass
    return aus


# ══ Kontrollen (G-O: nie veraltet) ═════════════════════════════════════════════════════════════════════════════════════════
def _k_ank_1(c_prod, daten) -> tuple[bool, str]:
    a = ankuendigungen(daten)
    if not a.get("an"):
        return False, "Schalter aus"
    if not a.get("lauf") or not a.get("laeufe"):
        return False, "noch kein Lauf"
    return (a["fehlerfrei"] == a["laeufe"],
            "%d Laeufe, fehlerfrei %d" % (a["laeufe"], a["fehlerfrei"]))


def _k_bp_3(c_prod, daten) -> tuple[bool, str]:
    m = bestand_meta(c_prod)
    return m.get("salden_fassung") == "2", "Wallet-Salden-Fassung %s" % m.get("salden_fassung")


# Automatische Pruefungen: Name -> fn(c_prod, daten) -> (erfuellt, beleg). Neue Kontrollen tragen ihren Namen in der Datei.
KONTROLLEN = {"k_ank_1": _k_ank_1, "k_bp_3": _k_bp_3}


def kontrollen(c_prod=None, daten: str = DATEN, heute: date | None = None, datei: str = KONTROLLEN_DATEI) -> dict:
    """Liest ``Basisinfos/nb_kontrollen.yaml`` und wertet automatische Kontrollen LIVE aus. Ueberfaellige manuelle stehen als
    ``ueberfaellig``. Rueckgabe {'stand': Datei-Datum, 'eintraege': [...], 'offen': n, 'ueberfaellig': n}."""
    import yaml

    heute = heute or datetime.now(timezone.utc).date()
    if not os.path.exists(datei):
        return {"fehlt": True, "eintraege": [], "offen": 0, "ueberfaellig": 0}
    roh = yaml.safe_load(open(datei, encoding="utf-8")) or {}
    aus = []
    for e in roh.get("kontrollen") or []:
        e = dict(e)
        e["auto_beleg"] = None
        if e.get("status") == "offen" and e.get("art") == "automatisch" and e.get("pruefung") in KONTROLLEN and c_prod is not None:
            try:
                ok, beleg = KONTROLLEN[e["pruefung"]](c_prod, daten)
                e["auto_beleg"] = beleg
                if ok:
                    e["status_live"] = "erfuellt (automatisch)"
            except Exception as ex:                                        # noqa: BLE001
                e["auto_beleg"] = "Pruefung nicht moeglich: %s" % type(ex).__name__
        f = e.get("faellig_bis")
        e["ueberfaellig"] = bool(e.get("status") == "offen" and not e.get("status_live") and f and str(f) < heute.isoformat())
        aus.append(e)
    offen = [e for e in aus if e.get("status") == "offen" and not e.get("status_live")]
    return {"stand": roh.get("stand"), "eintraege": aus, "offen": len(offen), "ueberfaellig": sum(e["ueberfaellig"] for e in aus)}
