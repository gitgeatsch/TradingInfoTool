"""Kalibrierlauf P1 der LLM-Sofortfassung 0.1 (E-52; Voranalyse_Schritt7 Par. 20.11.5) - ECHTE Aufrufe auf gemini-3.5-flash-lite.

Prueft, was vor der Produktion feststehen muss (vorab festgelegt):
    P1-a  Antworten formgueltig >= 95 % je Rolle
    P1-b  je Rolle KEINE Stufe ueber 70 % (sonst unterscheidet die Rolle nichts, R-T6)
    P1-c  Wiederholung gleich >= 90 % (dieselbe Eingabe ein zweites Mal)
    P1-d  anonym: 0 Eingaben mit Name/Jahr/Kurs, und das Modell erkennt aus der Trader-Eingabe weder Wert noch Zeitraum
    P1-e  Ende zu Ende: drei fertige Signalmails mit Block und Chart (Vorschau als HTML)

Anker: 50 REGEL0-Einstiege 2026 aus der Spur der Messung (data/_vergleich/b0_spur_bestand.csv, zufaellig mit fester Saat).
Markt-Fakten aus einer NB-Sicherung (nur gelesen), Kurse aus data/ (nur gelesen).
⚠️ Kein Schreiben in die Standard-DB: db.DB_PATH zeigt auf eine Wegwerfdatei (der Client zaehlt seine Aufrufe dort hinein).
⚠️ Die Ablage ist eine Wegwerfablage. Das Kontingent ist echt (500 je Tag und Modell, Topf mit dem NB): Deckel 260 Aufrufe.

    python Basisinfos/Rechenkern_02_10/kalibrier_llm.py <NB-Sicherung .db/.db.gz> <Ausgabeordner>
"""
from __future__ import annotations

import base64
import collections as C
import csv
import gzip
import json
import os
import random
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

HIER = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HIER)
os.chdir(HIER)
DECKEL = int(os.environ.get("KAL_DECKEL", "260"))
ANKER = int(os.environ.get("KAL_ANKER", "50"))
WIEDER = int(os.environ.get("KAL_WIEDER", "15"))
B0 = datetime(2020, 1, 1, tzinfo=timezone.utc)


def main(quelle: str, ausgabe: str) -> int:
    from dotenv import load_dotenv
    load_dotenv()
    import database.db as db
    tmp = tempfile.mkdtemp(prefix="kalibrier_llm_")
    from pathlib import Path
    db.DB_PATH = Path(tmp) / "wegwerf.db"                        # der Client zaehlt hier hinein, nicht in die Standard-DB
    c0 = sqlite3.connect(db.DB_PATH); c0.row_factory = sqlite3.Row; db.init_db(c0); c0.close()
    std_vorher = os.path.getmtime(os.path.join(HIER, "data", "tradinginfotool.db"))
    nb = os.path.join(tmp, "nb.db")
    (shutil.copyfileobj(gzip.open(quelle), open(nb, "wb")) if quelle.endswith(".gz") else shutil.copy(quelle, nb))
    from api.gemini import GeminiClient
    import agent.regel0_llm as L
    import agent.regel0_chart as CH
    import agent.regel0_mail as RM
    import agent.regel0_groesse as G
    K = L.lade()
    client = GeminiClient(api_key=os.environ["GEMINI_API_KEY"])
    zaehl = {"n": 0}
    roh_chat = client.chat

    def chat(*a, **kw):
        if zaehl["n"] >= DECKEL:
            raise RuntimeError("Deckel von %d Aufrufen erreicht" % DECKEL)
        zaehl["n"] += 1
        return roh_chat(*a, **kw)
    client.chat = chat

    sp = [r for r in csv.DictReader(open(os.path.join(HIER, "data", "_vergleich", "b0_spur_bestand.csv")), delimiter=";")
          if r["jahr"] == "2026" and int(r["stufe"]) > 0]
    random.Random(20261003).shuffle(sp)
    ablage = os.path.join(tmp, "ablage")
    os.makedirs(ablage)
    um = L.Umlauf(dict(K, max_signale_je_lauf=10 ** 6, lauf_zeitgrenze_s=10 ** 6, tageslimit_aufrufe=10 ** 6), client, ablage)
    ergebnisse, eingaben, anonym_funde = [], {}, 0
    for z in sp:
        if len(ergebnisse) >= ANKER:
            break
        sig = B0 + timedelta(hours=int(z["std"]))
        s = sig.strftime("%Y-%m-%d %H:%M")
        r = dict(symbol=z["symbol"], bitpanda=None, signalstunde=s, einstieg=(sig + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                 ausstieg=(sig + timedelta(hours=25)).strftime("%Y-%m-%d %H:%M"), stufe=int(z["stufe"]), kurs=None)
        rows = L._stunden("data", r["symbol"], sig, sig)
        if not rows:
            continue
        r["kurs"] = float(rows[0][3])
        ein_t = L.trader_eingabe(r, "data", K)
        if ein_t is None:
            continue
        anonym_funde += bool(L.anonym_verletzt(ein_t, r))
        e = L.pruefe_signal(r, client, ablage, "data", nb, K, umlauf=um)
        ergebnisse.append((r, e, z))
        eingaben[r["symbol"] + s] = ein_t
        print("  %2d %-8s %s  M=%-16s T=%-16s E=%-14s (Aufrufe %d)" % (len(ergebnisse), r["symbol"], s, *(
            (e.get(k) or {}).get("urteil") or ("-" + str((e.get(k) or {}).get("fehlt", ""))[:14]) for k in ("markt", "trader", "entscheider")),
            zaehl["n"]), flush=True)

    print("\nP1-a/b: Formgueltigkeit und Stufenverteilung je Rolle")
    ok_ab = True
    for rolle in ("markt", "trader", "entscheider"):
        urteile = [e[rolle]["urteil"] for _r, e, _z in ergebnisse if rolle in e and "urteil" in e[rolle]]
        fehlt = [e[rolle].get("fehlt") for _r, e, _z in ergebnisse if rolle in e and "urteil" not in e[rolle]]
        n = len(urteile) + len(fehlt)
        gueltig = len(urteile) / n if n else 0
        vert = C.Counter(urteile)
        top = (vert.most_common(1)[0][1] / len(urteile)) if urteile else 1.0
        if rolle == "markt":
            # der Markt wird je gleichem Faktenstand nur EINMAL gefragt - die Verteilung ueber VERSCHIEDENE Tage zaehlt
            tage = {}
            for _r, e, _z in ergebnisse:
                if "urteil" in e.get("markt", {}):
                    tage[_r["signalstunde"][:10]] = e["markt"]["urteil"]
            vert = C.Counter(tage.values())
            top = (vert.most_common(1)[0][1] / len(tage)) if tage else 1.0
        okr = gueltig >= 0.95 and top <= 0.70
        ok_ab &= okr
        print("  %-12s gueltig %d/%d (%.0f %%) · Verteilung %s · groesste Stufe %.0f %% -> %s" % (
            rolle, len(urteile), n, 100 * gueltig, dict(vert), 100 * top, "OK" if okr else "NICHT erfuellt"))
        if fehlt:
            print("               Fehlgruende:", C.Counter(str(f)[:60] for f in fehlt).most_common(3))

    print("\nP1-c: Wiederholung (dieselbe Eingabe ein zweites Mal, ohne Wiederverwendung)")
    gleich = gesamt = 0
    def _mehrheit(rolle, eingabe):
        """Wie die Rolle im Betrieb urteilt: `stimmen` Aufrufe, Mehrheit, sonst *uneinig* (0.1c)."""
        st = []
        for _ in range(max(1, int(K.get("stimmen") or 1))):
            st.append(L.validiere(rolle, L.frage(client, K["modell"], L.SYSTEM[rolle], eingabe, 0.0))["urteil"])
        z_ = C.Counter(st).most_common(1)[0]
        return z_[0] if (z_[1] * 2 > len(st) or len(st) == 1) else "uneinig"

    for r, e, _z in ergebnisse[:WIEDER]:
        for rolle in ("trader",):
            if "urteil" not in e.get(rolle, {}):
                continue
            try:
                u2 = _mehrheit(rolle, eingaben[r["symbol"] + r["signalstunde"]])
                gesamt += 1
                gleich += u2 == e[rolle]["urteil"]
                print("   Wiederholung %-8s %s: %s -> %s" % (r["symbol"], rolle, e[rolle]["urteil"], u2))
            except Exception as exc:                         # noqa: BLE001
                print("   Wiederholung", r["symbol"], type(exc).__name__)
    tage_gesehen = {}
    for r, e, _z in ergebnisse:
        if "urteil" in e.get("markt", {}) and r["signalstunde"][:10] not in tage_gesehen and len(tage_gesehen) < max(3, WIEDER // 2):
            tage_gesehen[r["signalstunde"][:10]] = (r, e["markt"]["urteil"])
    for tag, (r, u) in tage_gesehen.items():
        try:
            m = L.markt_eingabe(r, nb)
            u2 = _mehrheit("markt", m)
            gesamt += 1
            gleich += u2 == u
            print("   Wiederholung Markt %s: %s -> %s" % (tag, u, u2))
        except Exception as exc:                             # noqa: BLE001
            print("   Wiederholung Markt", tag, type(exc).__name__)
    anteil = gleich / gesamt if gesamt else 0
    print("  gleich %d von %d (%.0f %%) -> %s" % (gleich, gesamt, 100 * anteil, "OK" if anteil >= 0.90 else "NICHT erfuellt"))

    print("\nP1-d: Anonymitaet")
    print("  Eingaben mit Name/Jahr/Kurs: %d" % anonym_funde)
    treffer = 0
    gefragt = 0
    for r, _e, z in ergebnisse[:int(os.environ.get("KAL_RATEN", "12"))]:
        ein = eingaben[r["symbol"] + r["signalstunde"]]
        try:
            a = L.frage(client, K["modell"], "Du bekommst die Kurs- und Volumenlage eines Werts ohne Namen und ohne Datum. "
                        "Rate trotzdem: um welchen Wert (Kuerzel) und um welchen Monat und welches Jahr handelt es sich? "
                        'Antworte AUSSCHLIESSLICH mit JSON: {"kuerzel": "<Kuerzel>", "monat": "<MM>", "jahr": "<JJJJ>"}', ein, 0.0)
            gefragt += 1
            hit_sym = str(a.get("kuerzel") or "").upper().replace("USDT", "") == r["symbol"].upper()
            hit_zeit = str(a.get("jahr")) == r["signalstunde"][:4] and str(a.get("monat")).zfill(2) == r["signalstunde"][5:7]
            treffer += hit_sym or hit_zeit
            print("   %-8s %s -> geraten %s %s/%s %s" % (r["symbol"], r["signalstunde"][:7], a.get("kuerzel"), a.get("monat"), a.get("jahr"),
                                                     "TREFFER" if (hit_sym or hit_zeit) else ""))
        except Exception as exc:                             # noqa: BLE001
            print("   Raten", r["symbol"], type(exc).__name__)
    print("  erkannt %d von %d -> %s" % (treffer, gefragt, "OK" if anonym_funde == 0 and treffer <= 1 else "NICHT erfuellt"))

    print("\nP1-e: Ende zu Ende - drei fertige Signalmails mit Block und Chart")
    os.makedirs(ausgabe, exist_ok=True)
    teile = []
    for r, e, _z in ergebnisse[:3]:
        g = G.rechne(r["stufe"], 0, G.lade())
        b, t = RM.signal_mail(dict(r, vh=0.04, p2=None, p3=None, p5=None, kurs_markt="spot", zusatz=0, btc=0, abgleich=None),
                              r["stufe"], False, g, G.lade(), datetime.now(timezone.utc))
        t = t + "\n\n" + "\n".join(L.mail_zeilen(e, K))
        png = CH.bild(r, "data", jetzt=datetime.strptime(r["ausstieg"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) + timedelta(hours=2))
        bild = ('<img src="data:image/png;base64,%s" style="max-width:100%%;border:1px solid #ddd">' % base64.b64encode(png).decode()) if png else ""
        teile.append("<h3>%s</h3><pre style='white-space:pre-wrap;font-size:13px'>%s</pre>%s<hr>" % (b, t.replace("<", "&lt;"), bild))
    html = ("<!doctype html><html><head><meta charset='utf-8'><title>REGEL0 Mailvorschau</title></head><body style='font-family:sans-serif;"
            "max-width:960px;margin:auto;padding:16px'><h2>REGEL0-Signalmail mit Pruefblock (Sofortfassung 0.1) - Vorschau aus dem "
            "Kalibrierlauf</h2><p>Anker aus 2026 (Rueckspiel), Kurse und Datum echt, Hebel aus der Messung; NICHT versandt.</p>%s</body></html>"
            % "".join(teile))
    open(os.path.join(ausgabe, "mailvorschau_llm_0_1.html"), "w", encoding="utf-8").write(html)
    print("  geschrieben:", os.path.join(ausgabe, "mailvorschau_llm_0_1.html"))
    print("\nAufrufe gesamt: %d (Deckel %d) · Standard-DB unberuehrt: %s" % (
        zaehl["n"], DECKEL, os.path.getmtime(os.path.join(HIER, "data", "tradinginfotool.db")) == std_vorher))
    shutil.copy(os.path.join(ablage, "regel0_signale.db"), os.path.join(ausgabe, "kalibrier_ablage.db"))   # alle Ein- und Ausgaben als Beleg
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
