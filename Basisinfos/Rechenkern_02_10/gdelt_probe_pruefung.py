# -*- coding: utf-8 -*-
"""PRÜFUNG DER GDELT-PROBE (Probe + Auswertung) — ohne Netz, gegen bekannte Wahrheit, in Wegwerfordnern.

    python -X utf8 Basisinfos/Rechenkern_02_10/gdelt_probe_pruefung.py      -> gdelt_probe_pruefung.txt

P1 eigenständig (nur Standardbibliothek, schreibt nur die eigene .jsonl) · P2 gleich dem Quelltext von sichten_quellen, samt
Mutation · P3 Zeitplan · P4 eine Runde mit Sperre/Netzfehler/Unsinn, Abstand 600 s auch über Runden · P5 14 Tage mit Neustart und
verschlafenen Runden · P6 kein Seiteneffekt außer der eigenen Datei · P7 Auswertung findet gepflanzte Lücken, Revisionen und
Stundenauflösung — und meldet in der sauberen Welt nichts.
"""
from __future__ import annotations

import ast
import json
import os
import random
import shutil
import sys
import tempfile
import types
from datetime import datetime, timedelta, timezone

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
sys.path.insert(0, HIER)
import wegwerf  # noqa: E402,F401  (tempfile-Ordner auf D:)
import gdelt_probe_auswertung as AW  # noqa: E402

AUS = os.path.join(HIER, "gdelt_probe_pruefung.txt")
U = timezone.utc
ERG = []


def pruefe(name: str, ok: bool, info: str = "") -> None:
    ERG.append((ok, name, info))
    print("  %s %s%s" % ("✔" if ok else "✖", name, (" — " + info) if info else ""), flush=True)


def neu():
    P = AW.probe_modul()
    P._LETZTE[0] = None
    return P


# ── P1 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def p1():
    baum = ast.parse(open(AW.PROBE_SKRIPT, encoding="utf-8").read())
    mods = {n.names[0].name.split(".")[0] for n in ast.walk(baum) if isinstance(n, ast.Import)}
    mods |= {n.module.split(".")[0] for n in ast.walk(baum) if isinstance(n, ast.ImportFrom) and n.module}
    fremd = sorted(m for m in mods if m not in sys.stdlib_module_names and m != "__future__")
    pruefe("P1 nur Standardbibliothek", not fremd, "Importe %s" % ", ".join(sorted(mods)) if not fremd else "fremd: %s" % fremd)
    P = neu()
    for p in ("x/tradinginfotool.db", "x/tradinginfotool.jsonl", "x/probe.db"):
        try:
            P.ausgabe_pfad(["", "--ausgabe", p])
            pruefe("P1 verweigert %s" % p, False)
        except SystemExit:
            pruefe("P1 verweigert %s" % p, True)
    pruefe("P1 Vorgabe = eigene Datei neben dem Skript", P.ausgabe_pfad([""]) == os.path.join(P.ORDNER, "gdelt_probe_%s.jsonl" % P.RECHNER))


# ── P2 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def p2():
    gl = AW.gleichheit_quelltext()
    pruefe("P2 gleich dem Quelltext (%d Merkmale)" % len(gl), all(g for *_, g in gl),
           "; ".join(k for k, _, _, g in gl if not g))
    T = tempfile.mkdtemp(prefix="gdelt_p2_")
    try:
        s = open(AW.PROBE_SKRIPT, encoding="utf-8").read()
        for alt, neu_, merkmal in (("GDELT_ABSTAND_S = 600", "GDELT_ABSTAND_S = 60", "Abstand"),
                                   ('"aktien": \'"stock market" sourcelang:english\'', '"aktien": \'"stock market"\'', "Abfragen"),
                                   ("ZWEITER_VERSUCH_S = 120", "ZWEITER_VERSUCH_S = 30", "Pause"),
                                   ("LAUFEND_TAGE = 14", "LAUFEND_TAGE = 7", "Fenster")):
            assert s.count(alt) == 1, alt
            p = os.path.join(T, "m.py")
            open(p, "w", encoding="utf-8").write(s.replace(alt, neu_))
            g = AW.gleichheit_quelltext(AW.probe_modul(p))
            rot = [k for k, _, _, ok in g if not ok]
            pruefe("P2 Mutation %s wird rot" % merkmal, len(rot) == 1 and merkmal.lower()[:5] in rot[0].lower(), str(rot))
    finally:
        wegwerf.aufraeumen(T)


# ── P3 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def t(s):
    return datetime.fromisoformat(s).replace(tzinfo=U)


def p3():
    P = neu()
    st = t("2026-11-03T13:50:00")
    pruefe("P3 zuerst die Startrunde", P.faellige_runde(st, set(), st) == "start")
    pruefe("P3 nach dem Start bis 18:30 nichts", P.faellige_runde(t("2026-11-03T18:29:00"), {"start"}, st) is None)
    pruefe("P3 18:30 fällig", P.faellige_runde(t("2026-11-03T18:30:00"), {"start"}, st) == "2026-11-03T18:30:00+00:00")
    e = {"start", "2026-11-03T18:30:00+00:00"}
    pruefe("P3 erledigte Runde nicht doppelt", P.faellige_runde(t("2026-11-03T19:00:00"), e, st) is None)
    pruefe("P3 verschlafen bis 06:45: nur 06:30 nachgeholt", P.faellige_runde(t("2026-11-04T06:45:00"), e, st) == "2026-11-04T06:30:00+00:00")
    pruefe("P3 nächste Rundenzeit nach 13:50 = 18:30", P.naechste_slotzeit(st) == t("2026-11-03T18:30:00"))
    pruefe("P3 nächste Rundenzeit nach 23:59 = 00:30 Folgetag", P.naechste_slotzeit(t("2026-11-03T23:59:00")) == t("2026-11-04T00:30:00"))
    pruefe("P3 Fenster 14 Tage bis heute 00:00 UTC", P.fenster(t("2026-11-02T23:30:00")) == (t("2026-10-19T00:00:00").date(), t("2026-11-02T00:00:00").date()))
    pruefe("P3 56 feste Runden in 14 Tagen", len(P.slots_zwischen(st, st + timedelta(days=14))) == 56)


# ── P4 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def gdelt_json(ab, bis, werte=None, doppelt=None):
    d, pkt = ab, []
    while d < bis:
        w = (werte or {}).get(d.isoformat(), -1.0)
        pkt.append({"date": d.strftime("%Y%m%d") + "T000000Z", "value": w})
        if doppelt == d.isoformat():
            pkt.append({"date": d.strftime("%Y%m%d") + "T120000Z", "value": w + 0.5})
        d += timedelta(days=1)
    return json.dumps({"query_details": {}, "timeline": [{"series": "Average Tone", "data": pkt}]})


def p4():
    P = neu()
    T = tempfile.mkdtemp(prefix="gdelt_p4_")
    try:
        f = os.path.join(T, "p.jsonl")
        folge = {"krypto": [(200, None)], "fed": [(429, "Please limit requests"), (200, None)],
                 "aktien": [(429, "Please limit"), (429, "Please limit")], "konflikt": [(None, "netz"), (200, "<html>Fehler")]}
        ton_von = {q: k for k, q in P.GDELT.items()}

        def hole(abfrage, ab, bis):
            http, text = folge[ton_von[abfrage]].pop(0)
            if http == 200 and text is None:
                return 200, gdelt_json(ab, bis), None
            if http is None:
                return None, "", "URLError: netz"
            return http, text, None if http == 200 else "HTTP %d" % http
        uhr = [1000.0]
        gewartet = []

        def warte(s):
            gewartet.append(round(s))
            uhr[0] += s
        P.hole = hole
        ok = P.runde(f, "start", warte=warte, uhr=lambda: uhr[0])
        z = P.lies(f)
        ab = [x for x in z if x["art"] == "abruf"]
        pruefe("P4 zwei von vier Tönen mit Werten", ok == 2 and z[-1] == {**z[-1], "art": "runde_ende", "toene_ok": 2}, "toene_ok=%d" % ok)
        pruefe("P4 sieben Versuche, jeder protokolliert", [(x["ton"], x["versuch"], x["http"]) for x in ab] ==
               [("krypto", 1, 200), ("fed", 1, 429), ("fed", 2, 200), ("aktien", 1, 429), ("aktien", 2, 429),
                ("konflikt", 1, None), ("konflikt", 2, 200)], str([(x["ton"], x["versuch"], x["http"]) for x in ab]))
        pruefe("P4 200 ohne JSON gilt als Fehler, nicht als leere Reihe",
               ab[-1]["punkte"] is None and "keine JSON" in (ab[-1]["fehler"] or ""))
        pruefe("P4 14 Tagespunkte bei Erfolg (Fenster ohne heute)", len(ab[0]["punkte"]) == 14, "%d" % len(ab[0]["punkte"]))
        pruefe("P4 Wartezeiten: 600 zwischen Tönen, 120 vor dem 2. Versuch", gewartet == [600, 120, 600, 120, 600, 120], str(gewartet))
        # über Runden: die nächste Runde 100 s nach der letzten Abfrage wartet die restlichen 500 s
        folge.update({k: [(200, None)] for k in folge})
        uhr[0] += 100
        gewartet.clear()
        P.runde(f, "2026-11-03T18:30:00+00:00", warte=warte, uhr=lambda: uhr[0])
        pruefe("P4 Abstand gilt auch über Runden (500 s Rest, dann 600)", gewartet == [500, 600, 600, 600], str(gewartet))
    finally:
        wegwerf.aufraeumen(T)


# ── P5 + P6 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────
class Halt(Exception):
    pass


def p5_p6():
    T = tempfile.mkdtemp(prefix="gdelt_p5_")
    try:
        P = neu()
        f = os.path.join(T, "gdelt_probe_TEST.jsonl")
        uhr = [t("2026-11-03T13:50:00")]
        halt_bei = [t("2026-11-06T02:00:00")]

        def schlaf(s):
            uhr[0] += timedelta(seconds=s)
            if halt_bei[0] and uhr[0] >= halt_bei[0]:
                halt_bei[0] = None
                raise Halt()

        def runde(pfad, k, **_):
            P.schreibe(pfad, {"art": "abruf", "runde": k, "ts": P.iso(uhr[0]), "ton": "krypto", "versuch": 1, "http": 200,
                              "fehler": None, "dauer_s": 1, "fenster": [], "punkte": []})
            P.schreibe(pfad, {"art": "runde_ende", "runde": k, "ts": P.iso(uhr[0]), "toene_ok": 4})
            uhr[0] += timedelta(minutes=35)
            return 4
        P.jetzt = lambda: uhr[0]
        P.time = types.SimpleNamespace(sleep=schlaf)
        P.runde = runde
        vorher = set(os.listdir(T))
        try:
            P.main(["", "--ausgabe", f])
        except Halt:
            pass
        uhr[0] = t("2026-11-06T13:10:00")            # Rechner lag 11 h aus: 06:30 verpasst, 12:30 wird nachgeholt
        rc = P.main(["", "--ausgabe", f])
        z = P.lies(f)
        r = [x["runde"] for x in z if x["art"] == "runde_ende"]
        pruefe("P5 läuft 14 Tage und endet von selbst", rc == 0 and z[-1]["art"] == "fertig" and uhr[0] >= t("2026-11-17T13:50:00"))
        pruefe("P5 ein Start, ein Neustart, Startzeit bleibt", sum(x["art"] == "start" for x in z) == 1 and
               sum(x["art"] == "neustart" for x in z) == 1)
        pruefe("P5 keine Runde doppelt", len(r) == len(set(r)), "%d Runden" % len(r))
        soll = {P.iso(s) for s in P.slots_zwischen(t("2026-11-03T13:50:00"), t("2026-11-17T13:50:00"))} | {"start"}
        fehlt = sorted(soll - set(r))
        pruefe("P5 genau die verschlafene Runde fehlt (06.11. 06:30)",
               fehlt == ["2026-11-06T06:30:00+00:00"], str(fehlt))
        st, zz = AW.lade_probe(f)
        rr = AW.auswerten(st, zz, AW.historie(), None, bis=t("2026-11-18T00:00:00"))
        pruefe("P5 Auswertung zählt die fehlende Runde", rr["runden_fehlen"] == fehlt and rr["neustarts"] == 1,
               "%s" % rr["runden_fehlen"])
        nachher = set(os.listdir(T))
        pruefe("P6 einzige neue Datei ist die eigene .jsonl", nachher - vorher == {"gdelt_probe_TEST.jsonl"}, str(nachher - vorher))
    finally:
        wegwerf.aufraeumen(T)


# ── P7 ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def welt(H, luecke=None, revision=None, doppelt=None, seed=7, fehlt=None, aus=None):
    """Synthetische Probe 14 Tage ab 2026-11-03 13:50 mit bekannter Wahrheit. luecke=(ton, ab, bis): alle Abrufe des Tons in
    [ab, bis) gesperrt · revision=(ton, tag, delta): ab dem 2. Abruf, der den Tag enthält, gilt wahr+delta · doppelt=(ton, tag) ·
    fehlt=(ton, {tage}): GDELT hat diese Tage nicht (Abruf erfolgreich, Tag fehlt) · aus=(ab, bis): Rechner aus, kein Versuch."""
    P = neu()
    rnd = random.Random(seed)
    start = t("2026-11-03T13:50:00")
    ende = start + timedelta(days=14)
    wahr = {}
    for ton in P.GDELT:
        h = H[H.ton == ton].wert.tolist()
        d = t("2026-10-01T00:00:00").date()
        wahr[ton] = {}
        while d <= ende.date():
            wahr[ton][d.isoformat()] = rnd.choice(h)
            d += timedelta(days=1)
    z = [{"art": "start", "ts": P.iso(start), "ende": P.iso(ende), "rechner": "WELT", "python": "-", "fassung": P.FASSUNG,
          "pruefsumme": "-"}]
    gesehen = {}
    for k in ["start"] + [P.iso(s) for s in P.slots_zwischen(start, ende)]:
        ts0 = start if k == "start" else datetime.fromisoformat(k)
        if aus and aus[0] <= ts0 < aus[1]:
            continue
        for i, ton in enumerate(P.GDELT):
            ts = ts0 + timedelta(minutes=10 * i)
            ab, bis = P.fenster(ts)
            if luecke and ton == luecke[0] and luecke[1] <= ts < luecke[2]:
                z.append({"art": "abruf", "runde": k, "ts": P.iso(ts), "ton": ton, "versuch": 1, "http": 429, "fehler": "HTTP 429",
                          "punkte": None})
                continue
            w = dict(wahr[ton])
            if revision and ton == revision[0] and revision[1] < bis.isoformat():
                gesehen[revision[1]] = gesehen.get(revision[1], 0) + 1
                if gesehen[revision[1]] > 1:
                    w[revision[1]] += revision[2]
            dp = doppelt[1] if doppelt and doppelt[0] == ton and k == "start" else None
            pkt = json.loads(gdelt_json(ab, bis, w, dp))["timeline"][0]["data"]
            if fehlt and ton == fehlt[0]:
                pkt = [x for x in pkt if AW._tag(x["date"]) not in fehlt[1]]
            z.append({"art": "abruf", "runde": k, "ts": P.iso(ts), "ton": ton, "versuch": 1, "http": 200, "fehler": None,
                      "punkte": [[x["date"], x["value"]] for x in pkt]})
        z.append({"art": "runde_ende", "runde": k, "ts": P.iso(ts0), "toene_ok": 4})
    R = {ton: {d: w for d, w in r.items() if d >= "2026-10-20"} for ton, r in wahr.items()}
    return z[0], z, R


def p7():
    H = AW.historie()
    H = H[H.tag < "2026-10-20"]
    bis = t("2026-11-18T00:00:00")
    st, z, R = welt(H)
    r = AW.auswerten(st, z, H, R, bis=bis)
    pruefe("P7 saubere Welt: K1, K2, K3 erfüllt, HÄLT", r["k1_ok"] and r["k2_ok"] and r["k3_ok"] and r["haelt"],
           "Live-Tage %d, K2 %s, Revision %s" % (len(r["tage"]), r["k2"], r["revision"]))
    pruefe("P7 saubere Welt: 13 Live-Tage, Verzug ≤ 1 h", len(r["tage"]) == 13 and r["V"].verzug_h.max() <= 1.0,
           "%d / %.2f h" % (len(r["tage"]), r["V"].verzug_h.max()))
    # Lücke: aktien 2 Tage gesperrt -> Tage, deren erster Wert erst nach 24 h kommt
    # Sperre aktien 07.11. 00:00 bis 08.11. 06:00: der 06.11. kommt erst 08.11. 06:50 (30,8 h) -> 1 Lücke = 7,7 % -> K1 noch grün
    st, z, R = welt(H, luecke=("aktien", t("2026-11-07T00:00:00"), t("2026-11-08T06:00:00")))
    r = AW.auswerten(st, z, H, R, bis=bis)
    pruefe("P7 Sperre 30 h bei aktien: genau 1 Lücke, K1 noch grün (1/13)", r["k1"]["aktien"][0] == 1 and r["k1"]["krypto"][0] == 0
           and r["k1_ok"], "aktien %s" % (r["k1"]["aktien"],))
    # Sperre 05.11. 00:00 bis 07.11. 12:00: 04.11. (60,8 h) und 05.11. (36,8 h) -> 2 Lücken = 15 % -> rot
    st, z, R = welt(H, luecke=("aktien", t("2026-11-05T00:00:00"), t("2026-11-07T12:00:00")))
    r = AW.auswerten(st, z, H, R, bis=bis)
    pruefe("P7 Sperre 60 h: genau 2 Lücken, K1 rot", r["k1"]["aktien"][0] == 2 and not r["k1_ok"] and r["haelt"] is False,
           "aktien %s" % (r["k1"]["aktien"],))
    # Ursache der Lücke (Nutzer 02.11.: gesperrt / Quelle fehlt)
    u = r["k1_ursache"]["aktien"]
    pruefe("P7 Ursache: die 2 Lücken der Sperre heißen 'gesperrt'", u == {"gesperrt": 2, "quelle_fehlt": 0, "kein_abruf": 0}, str(u))
    st, z, R = welt(H, fehlt=("fed", {"2026-11-05", "2026-11-06", "2026-11-07"}))
    r = AW.auswerten(st, z, H, R, bis=bis)
    u = r["k1_ursache"]["fed"]
    pruefe("P7 Ursache: GDELT ohne 3 Tage -> 3 Lücken 'Quelle fehlt', andere Töne frei",
           u == {"gesperrt": 0, "quelle_fehlt": 3, "kein_abruf": 0} and r["k1"]["krypto"][0] == 0 and not r["k1_ok"], str(u))
    st, z, R = welt(H, aus=(t("2026-11-09T00:00:00"), t("2026-11-10T12:00:00")))
    r = AW.auswerten(st, z, H, R, bis=bis)
    u = r["k1_ursache"]["krypto"]
    pruefe("P7 Ursache: Rechner 36 h aus -> 'kein Abruf' (08.11.), bei allen Tönen gleich",
           u == {"gesperrt": 0, "quelle_fehlt": 0, "kein_abruf": 1} and len({str(v) for v in r["k1_ursache"].values()}) == 1,
           str(r["k1_ursache"]))
    st, z, R = welt(H)
    r = AW.auswerten(st, z, H, R, bis=bis)
    pruefe("P7 Ursache: saubere Welt ohne jede Ursache", r["V"].ursache.isna().all())
    # Revision
    st, z, R = welt(H, revision=("fed", "2026-11-08", 3.0))
    r = AW.auswerten(st, z, H, R, bis=bis)
    pruefe("P7 Revision: genau ein Ton-Tag geändert, Größe 3,0", r["revision"][2] == 1 and abs(r["revision"][1] - 3.0) < 1e-9,
           str(r["revision"]))
    # K2: R ist die Wahrheit OHNE Revision, live sah den Erstwert = Wahrheit -> gleich; R mit großer Abweichung -> ungleich
    st, z, R = welt(H)
    for d in list(R["fed"])[-14:]:
        R["fed"][d] += 4.0
    r = AW.auswerten(st, z, H, R, bis=bis)
    pruefe("P7 Rückspiel weicht ab (fed +4): K2 rot", r["k2_ok"] is False and r["haelt"] is False, str(r["k2"]))
    # K3
    st, z, R = welt(H, doppelt=("krypto", "2026-10-25"))
    r = AW.auswerten(st, z, H, R, bis=bis)
    pruefe("P7 Stundenauflösung in einem Abruf: K3 rot", r["k3_abrufe_nicht_taeglich"] == 1 and not r["k3_ok"],
           "%d" % r["k3_abrufe_nicht_taeglich"])
    # K2 offen ohne Rückspiel
    r = AW.auswerten(st, z, H, None, bis=bis)
    pruefe("P7 ohne Rückspiel: Urteil offen, nicht grün", r["haelt"] is None)
    # Fensterprobe gegen die echte Historie: die Welt nimmt Zufallswerte -> Abweichungen müssen gesehen werden
    st, z, R = welt(H)
    r = AW.auswerten(st, z, AW.historie(), R, bis=bis)
    pruefe("P7 Fensterprobe sieht Abweichungen gegen die Historie", r["fensterprobe"][0] > 0 and r["fensterprobe"][2] > 0,
           str(r["fensterprobe"]))


def main() -> int:
    for f in (p1, p2, p3, p4, p5_p6, p7):
        print(f.__name__, flush=True)
        f()
    n = sum(ok for ok, *_ in ERG)
    t_ = ["GDELT-PROBE — Prüfung %s: %d von %d grün" % (datetime.now(U).isoformat(timespec="minutes"), n, len(ERG))]
    t_ += ["  %s %s%s" % ("✔" if ok else "✖", name, (" — " + info) if info else "") for ok, name, info in ERG]
    open(AUS, "w", encoding="utf-8").write("\n".join(t_) + "\n")
    print(t_[0])
    return 0 if n == len(ERG) else 1


if __name__ == "__main__":
    sys.exit(main())
