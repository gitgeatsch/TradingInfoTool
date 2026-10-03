"""Gegenpruefung Hebel-Tab H-1 bis H-4 (Voranalyse_Schritt7 Par. 17; Nutzer 03.10.2026: *"Ja H-1 bis H-4 wie vorgeschlagen"*).

Alles auf WEGWERFPFADEN: eine Wegwerf-Ablage mit jedem Status, eine Kopie der NB-Sicherung (in einen Wegwerfordner kopiert,
mit einer Wegwerf-Position). Der echte Tab (ui/hebel_view.HebelView) wird in einem unsichtbaren Fenster gebaut und gelesen.
Nachgewiesen am Seiteneffekt: die Ablage bleibt bytegleich, die Standard-DB unberuehrt.

Aufruf:  python Basisinfos/Rechenkern_02_10/pruefe_h17.py <NB-Sicherung .db oder .db.gz>
"""
from __future__ import annotations

import gzip
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)

ERG = []


def pruefe(name, ok, info=""):
    ERG.append(bool(ok))
    print("  %s %s%s" % ("✔" if ok else "⛔", name, (" - %s" % info) if info else ""))


def _h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(quelle):
    import agent.regel0_ablage as AB
    import agent.regel0_ansicht as A
    import agent.regel0_groesse as G
    import agent.regel0_mail as RM
    import database.db as db

    std = os.path.join(HIER, "data", "tradinginfotool.db")
    std_vorher = os.path.getmtime(std) if os.path.exists(std) else None
    tmp = tempfile.mkdtemp(prefix="pruefe_h17_")
    kopie = os.path.join(tmp, "nb_kopie.db")
    (shutil.copyfileobj(gzip.open(quelle), open(kopie, "wb")) if quelle.endswith(".gz") else shutil.copy(quelle, kopie))
    db.DB_PATH = kopie

    def fabrik():
        c = sqlite3.connect(kopie)
        c.row_factory = sqlite3.Row
        return c

    c = fabrik()
    schalter = db.get_hebel_pruefung_toggle_map(c)
    an = sorted(k for k, v in schalter.items() if v)
    aus = sorted(k for k, v in schalter.items() if not v) or ["NIEMAND"]
    c.close()
    assert len(an) >= 8, an

    jetzt = datetime.now(timezone.utc)
    voll = jetzt.replace(minute=0, second=0, microsecond=0)
    t = lambda d: d.strftime("%Y-%m-%d %H:%M")

    def zeile(asset, sig_vor_h, **kw):
        sig = voll - timedelta(hours=sig_vor_h)
        r = dict(symbol=asset + "B", signalstunde=t(sig), einstieg=t(sig + timedelta(hours=1)), ausstieg=t(sig + timedelta(hours=25)),
                 vh=0.041, stufe_vorlaeufig=5, stufe=5, p2=0.001, p3=0.004, p5=0.012, hebel_schalter=1, bitpanda=asset, zusatz=0,
                 btc=0, version="regel0_1", erfasst_am=t(sig + timedelta(hours=1)), endgueltig_am=t(sig + timedelta(hours=2)),
                 kurs=1.234, kurs_markt="spot")
        r.update(kw)
        return r

    faelle = {
        "Einstieg": zeile(an[0], 1, stufe=None, endgueltig_am=None),          # Einstiegsstunde laeuft noch, Stufe vorlaeufig
        "läuft": zeile(an[1], 5, mail_signal_am=t(voll - timedelta(hours=4)), mail_signal_stufe=5),
        "Ausstieg fällig": zeile(an[2], 28, mail_signal_am=t(voll - timedelta(hours=27)), mail_signal_stufe=3, stufe=5,
                                 mail_korrektur_am=t(voll - timedelta(hours=26))),
        "beendet": zeile(an[3], 60, mail_signal_am=t(voll - timedelta(hours=59)), mail_signal_stufe=5,
                         mail_erinnerung_am=t(voll - timedelta(hours=34))),
        "kein Handel": zeile(an[4], 3, stufe_vorlaeufig=0, stufe=0),
        "nicht gemailt (Zuordnung)": zeile(an[5], 4, mail_gesperrt_am=t(voll - timedelta(hours=3)),
                                           abgleich="Bitpanda 0.0062 USD, Binance X 0.0125 (Abweichung +101.6 %)"),
        "Schalter aus": zeile(aus[0], 2, hebel_schalter=0),
        "ohne Bitpanda": zeile("ZK", 2, bitpanda=None, hebel_schalter=None),
    }
    # aelteres Signal desselben Assets wie "läuft" - die Liste zeigt das JUENGSTE
    faelle["aelter"] = zeile(an[1], 80, symbol=an[1] + "B")
    ab_ordner = os.path.join(tmp, "ablage")
    os.makedirs(ab_ordner)
    ca = AB.oeffne(ab_ordner)
    sp = [r[1] for r in ca.execute("PRAGMA table_info(signal)")]
    for r in faelle.values():
        ks = [k for k in r if k in sp]
        ca.execute("INSERT INTO signal (%s) VALUES (%s)" % (",".join(ks), ",".join("?" * len(ks))), [r[k] for k in ks])
    ca.commit()
    ca.close()
    ablage = os.path.join(ab_ordner, AB.ABLAGE_NAME)
    h_vorher = _h(ablage)

    # Wegwerf-Position (H-3): eroeffnet 2 h nach dem Einstieg des "läuft"-Signals; eine zweite ohne Signal
    r_l = faelle["läuft"]
    auf = (A._ende(r_l["einstieg"]) + timedelta(hours=1)).isoformat()
    c = fabrik()
    for sym, wann in ((an[1], auf), (an[6], (jetzt - timedelta(hours=3)).isoformat())):
        c.execute("INSERT INTO hebel_positions (symbol, richtung, status, eroeffnet_am, hebel_effektiv, eigenkapital_eur, "
                  "liquidationspreis_geschaetzt_eur, letzte_transaktion_unix_timestamp) VALUES (?,?,?,?,?,?,?,?)",
                  (sym, "LONG", "offen", wann, 5.0, 300.0, 1.0, int(jetzt.timestamp())))
    c.commit()
    c.close()

    print("1) reine Funktionen (agent/regel0_ansicht.py)")
    rows = A.lese(ab_ordner)
    pruefe("lese: alle Zeilen, nur gelesen", len(rows) == len(faelle) and _h(ablage) == h_vorher, "%d Zeilen" % len(rows))
    pruefe("lese: ohne Datei eine leere Liste (und KEINE Datei angelegt)",
           A.lese(os.path.join(tmp, "leer")) == [] and not os.path.exists(os.path.join(tmp, "leer", AB.ABLAGE_NAME)))
    st = {k: A.status(r, jetzt) for k, r in faelle.items()}
    pruefe("jeder Status wird erkannt",
           all(st[k].startswith(k) for k in ("Einstieg", "läuft", "Ausstieg fällig", "beendet", "kein Handel", "nicht gemailt (Zuordnung)")),
           "; ".join("%s -> %s" % kv for kv in st.items()))
    pruefe("Hebel: endgueltig, vorlaeufig mit Vermerk, kein Handel '-'",
           (A.hebel_text(faelle["läuft"]), A.hebel_text(faelle["Einstieg"]), A.hebel_text(faelle["kein Handel"])) == ("5x", "5x (vorläufig)", "-"))
    j = A.juengste_je_asset(rows)
    pruefe("je Asset das JUENGSTE Signal", j[an[1]]["signalstunde"] == faelle["läuft"]["signalstunde"])
    offen = {(an[1], "LONG"), (an[6], "LONG")}
    sicht2 = {n for n, r in j.items() if A.sichtbar(r, jetzt, schalter, offen, True)}
    sichtalle = {n for n, r in j.items() if A.sichtbar(r, jetzt, schalter, offen, False)}
    pruefe("2 Tage: 'beendet' (60 h) weg, Schalter aus weg, ohne Bitpanda weg",
           an[3] not in sicht2 and aus[0] not in sicht2 and "ZK" not in sicht2 and {an[0], an[1], an[2], an[4], an[5]} <= sicht2,
           sorted(sicht2))
    pruefe("Alle: 'beendet' wieder da, Schalter aus bleibt weg", an[3] in sichtalle and aus[0] not in sichtalle, sorted(sichtalle))
    werte = G.lade()
    _ti, _me, text = A.detail(faelle["läuft"], rows, jetzt, werte)
    s_l, v_l = A.stufe(faelle["läuft"])
    _b, mail = RM.signal_mail(faelle["läuft"], s_l, v_l, G.rechne(s_l, 0, werte), werte, jetzt)
    pruefe("Detail = derselbe Text wie die Signalmail, dazu der Mailstand",
           text.startswith(mail) and "MAILSTAND" in text and "verschickt" in text)
    _t2, _m2, t_k = A.detail(faelle["kein Handel"], rows, jetzt, werte)
    _t3, _m3, t_g = A.detail(faelle["nicht gemailt (Zuordnung)"], rows, jetzt, werte)
    _t4, _m4, t_f = A.detail(faelle["Ausstieg fällig"], rows, jetzt, werte)
    pruefe("Detail: kein Handel / gesperrt mit Abgleich / Korrektur",
           "OHNE HANDEL" in t_k and "NICHT verschickt" in t_g and "Abweichung +101.6" in t_g and "Korrektur:" in t_f)
    v1 = A.positions_vermerk(an[1], "LONG", auf, rows)
    v2 = A.positions_vermerk(an[6], "LONG", (jetzt - timedelta(hours=3)).isoformat(), rows)
    v3 = A.positions_vermerk(an[1], "LONG", (A._ende(r_l["signalstunde"]) + timedelta(hours=30)).isoformat(), rows)
    v4 = A.positions_vermerk(an[1], "SHORT", auf, rows)
    pruefe("H-3: Vermerk nur mit Signal in den 24 h davor, nur LONG",
           v1.startswith("REGEL0, Ausstieg") and v2 == "" and v3 == "" and v4 == "", "%r / %r / %r / %r" % (v1, v2, v3, v4))
    _g = G.alter_hebelweg_aus

    def _kaputt(werte=None):
        raise OSError("unlesbar")
    G.alter_hebelweg_aus = _kaputt
    try:
        h_kaputt = A.knopf_hinweis()
    finally:
        G.alter_hebelweg_aus = _g
    pruefe("H-2: Schalter an -> gesperrt, Schalter aus -> frei, unlesbar -> gesperrt",
           A.knopf_hinweis(dict(werte, alter_hebelweg_aus=True)) is not None
           and A.knopf_hinweis(dict(werte, alter_hebelweg_aus=False)) is None and h_kaputt is not None, h_kaputt)

    print("2) der echte Tab (ui/hebel_view.HebelView, unsichtbares Fenster)")
    import tkinter as tk
    import ui.hebel_view as HV
    wurzel = tk.Tk()
    wurzel.withdraw()
    try:
        v = HV.HebelView(wurzel, fabrik, [], None, None, None)
        v._regel0_ordner = ab_ordner
        v.refresh()
        r0 = {iid: row[1] for iid, row in v._rows.items() if row[0] == "regel0"}
        werte_liste = {iid: v.tree.item(iid, "values") for iid in r0}
        pruefe("die REGEL0-Zeilen stehen in DERSELBEN Liste, mit These REGEL0 24 h",
               set(r0) == {"%s:LONG" % n for n in sicht2} and all(w[4] == A.THESE for w in werte_liste.values()),
               sorted(r0))
        pruefe("Status und Hebel in der Liste wie aus den reinen Funktionen",
               all(werte_liste[i][2] == A.status(r0[i], datetime.now(timezone.utc)) and werte_liste[i][3] == A.hebel_text(r0[i]) for i in r0))
        i_l = "%s:LONG" % an[1]
        v.tree.selection_set(i_l)
        v.update()
        v._render_selection(v._rows[i_l])
        txt = v.detail_text.get("1.0", "end")
        pruefe("Auswahl zeigt den Mailtext, der Knopf ist aus",
               "REGEL0.1 - HEBEL-SIGNAL LONG" in txt and "MAILSTAND" in txt and str(v.analyze_button.cget("state")) == "disabled")
        v._on_history_clicked()                          # darf mit einer REGEL0-Zeile nicht stolpern
        pruefe("Signal-Historie oeffnet auch bei einer REGEL0-Zeile", True)
        pos = {v.positions_tree.item(i, "values")[0]: v.positions_tree.item(i, "values") for i in v.positions_tree.get_children()}
        pruefe("Positionsliste: REGEL0-Vermerk bei der Position mit Signal, '-' bei der ohne",
               pos[an[1]][6].startswith("REGEL0, Ausstieg") and pos[an[6]][6] == "-", "%s / %s" % (pos[an[1]][6], pos[an[6]][6]))
        v._zeitfenster_var.set("alle")
        v.refresh()
        pruefe("Anzeige Alle: auch das beendete Signal", "%s:LONG" % an[3] in v._rows and v._rows["%s:LONG" % an[3]][0] == "regel0")
        pruefe("H-2 im Tab: der Knopf meldet die Sperre (Schalter in regel0_betrieb.yaml an)",
               (HV.HebelView._alte_analyse_hinweis() or "").startswith("Gesperrt: alter Hebelweg aus"), HV.HebelView._alte_analyse_hinweis())
        _orig = A.knopf_hinweis
        try:
            A.knopf_hinweis = lambda werte=None: None
            frei_hin = HV.HebelView._alte_analyse_hinweis()
        finally:
            A.knopf_hinweis = _orig
        pruefe("Gegenprobe: mit Schalter aus faellt die Pruefung auf die Kettenregel zurueck (kein REGEL0-Hinweis)",
               not (frei_hin or "").startswith("Gesperrt: alter Hebelweg aus"), frei_hin)
        # Gegenrichtung der Zusammenfuehrung: eine ALTE Zeile, die juenger ist als das REGEL0-Signal desselben Assets, bleibt
        c = fabrik()
        alt = db.get_latest_hebel_signal_per_symbol_and_richtung(c)
        alt.update(db.get_latest_rollen_hebel_signal_per_symbol_and_richtung(c))
        c.close()
        kand = sorted(k[0] for k in alt if k[1] == "LONG" and schalter.get(k[0]) and k[0] not in an[:7])
        if kand:
            x = kand[0]
            alt_zeit = HV._als_utc(alt[(x, "LONG")].created_at)
            sig_alt = (alt_zeit - timedelta(days=30)).replace(minute=0, second=0, microsecond=0)
            ca = sqlite3.connect(ablage)
            ca.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, stufe_vorlaeufig, stufe, hebel_schalter, bitpanda, version) "
                       "VALUES (?,?,?,?,?,?,?,?,?)", (x + "B", t(sig_alt), t(sig_alt + timedelta(hours=1)), t(sig_alt + timedelta(hours=25)),
                                                    3, 3, 1, x, "regel0_1"))
            ca.commit(); ca.close()
            v.refresh()
            art_alt = v._rows.get("%s:LONG" % x, ("fehlt",))[0]
            ca = sqlite3.connect(ablage)
            ca.execute("UPDATE signal SET signalstunde=?, einstieg=?, ausstieg=? WHERE symbol=?",
                       (t(voll - timedelta(hours=6)), t(voll - timedelta(hours=5)), t(voll + timedelta(hours=19)), x + "B"))
            ca.commit(); ca.close()
            v.refresh()
            art_neu = v._rows.get("%s:LONG" % x, ("fehlt",))[0]
            pruefe("Zusammenfuehrung: die JUENGERE Zeile gewinnt - alte bleibt gegen ein aelteres REGEL0-Signal, REGEL0 ersetzt eine aeltere",
                   art_alt == "signal" and art_neu == "regel0", "%s: alte Zeile %s -> %s / %s" % (x, str(alt_zeit)[:16], art_alt, art_neu))
            h_vorher = _h(ablage)                        # die Pruefung selbst hat die Wegwerfablage veraendert
        else:
            pruefe("Zusammenfuehrung pruefbar (alte LONG-Zeile eines Assets mit Schalter an in der Kopie)", False, "keine gefunden")
        v._regel0_ordner = os.path.join(tmp, "gibt_es_nicht")
        v.refresh()
        pruefe("ohne Ablage: keine REGEL0-Zeile, kein Absturz", not any(r[0] == "regel0" for r in v._rows.values()))
        v.destroy()
    finally:
        wurzel.destroy()

    print("3) Seiteneffekte")
    pruefe("die Ablage ist bytegleich (der Tab schreibt nie hinein)", _h(ablage) == h_vorher)
    pruefe("die Standard-DB ist unberuehrt",
           std_vorher is None or os.path.getmtime(std) == std_vorher)
    n = sum(ERG)
    print("SCHLUSS: %s (%d von %d)" % ("✔ bestanden" if n == len(ERG) else "⛔ NICHT bestanden", n, len(ERG)))
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if n == len(ERG) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
