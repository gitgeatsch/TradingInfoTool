"""L-A Lagebild Gesamtmarkt (24.10.2026, E-137, Voranalyse_Lagebild_Gesamtmarkt_23_10.md) - Pruefstand am SEITENEFFEKT, nur Wegwerf-
Dateien (D:\\CLAUDE_Temp). Liest FRED und alternative.me live (frei, nur lesend) - wie am NB.

    python -X utf8 Basisinfos/Rechenkern_02_10/p81_lagebild_pruefstand.py > Basisinfos/Rechenkern_02_10/p81_lagebild_pruefstand.txt

  G1  R-R11 gegen die Atlas-Rechnung p73 (Zwischenablage data/_ra/p73_fred.csv, Stand 23.10.): Baerenmarkt-Phasen des Nasdaq bitgleich
      zu p73.baer_phasen, laufender Bullenmarkt seit 2025-04-08; letzte Inversion je Kurve wie p73 (d); Sahm wie p73 (e)
  G2  Auskunft Rueckschau 1982-2026: Monate mit Rezessionsampel ROT gegen NBER-Rezessionen (Treffer, Fehlalarme) - keine Bedingung
  G3  drei Zustaende (fehlt / veraltet / ok) in zeile_gesamtmarkt und stand(); Fehlervermerk sichtbar; O54-Zeile unveraendert;
      L4 traegt den High-Yield-Aufschlag (Nutzer 24.10.)
  G4  lauf() mit kaputtem Abruf: O54 UND Gesamtmarkt behalten den alten Stand MIT Vermerk, Schluessel verborgen
  G5  lauf() nur der Gesamtmarkt kaputt: O54 frisch, Gesamtmarkt alt mit Vermerk (eigener Fehlerpfad)
  G6  Mails: REGEL0 (Einschaetzung 'Gesamtmarkt' unter 'Makro', Technik, HTML); B1/B3/B4 mit zeile_mail -> eigene Zeile 'Gesamtmarkt';
      Job-Aufrufe zeile_mail() viermal
  G7  Statusseite (Block in der Makro-Karte vor Betrieb & Lage, Render liest m.gesamtmarkt), Getter, GUI (gesamt_zeilen), Diagnose
  G8  Desktop-Prod und die echte Ablage unveraendert
"""
import hashlib
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta, timezone

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Rechenkern_02_10"))
sys.stdout.reconfigure(encoding="utf-8")
import wegwerf  # noqa: E402,F401

import pandas as pd  # noqa: E402
import requests  # noqa: E402

import config  # noqa: E402
import agent.makro_lage as ML  # noqa: E402
import agent.regel0_groesse as G  # noqa: E402
import agent.regel0_mail as RM  # noqa: E402
import agent.spot_abbau as SA  # noqa: E402
import agent.spot_mitnahme as SM  # noqa: E402
import agent.spot_upbit as SU  # noqa: E402
from database import db  # noqa: E402

config.load_env()
KEY = os.environ.get("FRED_API_KEY", "")
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-4s %-9s %s" % (k, "bestanden" if ok else "FEHLER", text))


def summe(p):
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


VOR = {"prod": summe(db.DB_PATH), "ablage": summe(ML.ABLAGE)}
T = tempfile.mkdtemp(prefix="p81_")
HEUTE = date.today()

# ══ G1 R-R11 gegen p73 ════════════════════════════════════════════════════════════════════════════════════════════════════════
with redirect_stdout(io.TextIOWrapper(io.BytesIO(), encoding="utf-8")):
    import p73_atlas_t3_lang as P73
D = P73.lade()                                               # Zwischenablage vom 23.10. (die Atlas-Rechnung)
ph_m, of_m = ML.baer_phasen(D["NASDAQCOM"])
ph_p, of_p = P73.baer_phasen(D["NASDAQCOM"])
inv_p73 = {}
for name, k in (("10J–2J", "T10Y2Y"), ("10J–3M", "T10Y3M")):
    m = D[k].resample("ME").mean()
    inv = [(a, b) for a, b, w in P73.strecken(m < 0) if w]
    inv_p73[name] = m[(m.index >= inv[-1][0]) & (m < 0)].index[-1].strftime("%Y-%m")
stich = D["T10Y3M"].index[-1].date()
L1 = ML.rezession(D["T10Y2Y"], D["T10Y3M"], D["SAHMREALTIME"], stich)
roh = ML.hole_alle(KEY, HEUTE)
ex = ML.hole_gesamt(KEY, HEUTE)
fg = ML.hole_fg()
g = ML.gesamtmarkt(roh, ex, fg, HEUTE)
pruefe("G1", ph_m == ph_p and of_m == of_p and len(ph_m) == 13 and of_m is None and ph_m[-1][1].date().isoformat() == "2025-04-08"
       and L1["inversion_zuletzt"] == inv_p73 and L1["sahm"][0] == float(D["SAHMREALTIME"].iloc[-1])
       and g["werte"]["nasdaq"]["bull_seit"] == "2025-04-08" and g["werte"]["rezession"]["inversion_zuletzt"] == inv_p73,
       "Nasdaq-Phasen %d bitgleich zu p73 %s · Bull seit %s (live %s, %.1f Mon.) · letzte Inversion %s = p73 %s · Sahm %.2f" % (
           len(ph_m), ph_m == ph_p, ph_m[-1][1].date(), g["werte"]["nasdaq"]["bull_seit"], g["werte"]["nasdaq"]["bull_monate"],
           L1["inversion_zuletzt"], inv_p73, L1["sahm"][0]))

# ══ G2 Rueckschau der Rezessionsampel (Auskunft) ══════════════════════════════════════════════════════════════════════════════
monate = pd.date_range("1982-01-31", D["SAHMREALTIME"].index[-1] + pd.offsets.MonthEnd(0), freq="ME")
rot = []
for t in monate:
    r = ML.rezession(D["T10Y2Y"][:t], D["T10Y3M"][:t], D["SAHMREALTIME"][:t], t.date())
    rot.append(r["rot"])
rot = pd.Series(rot, index=monate)
rec = (D["USREC"].resample("ME").last() > 0).reindex(monate).ffill().fillna(False)
st = [(a, b) for a, b, w in P73.strecken(rot) if w]
treffer, fehl = [], []
for a, b in st:
    nah = rec[(rec.index >= a - pd.DateOffset(months=12)) & (rec.index <= b + pd.DateOffset(months=12))].any()
    (treffer if nah else fehl).append("%s..%s" % (a.strftime("%Y-%m"), b.strftime("%Y-%m")))
recs = [(a, b) for a, b, w in P73.strecken(rec.astype(bool)) if w]
erkannt = sum(bool(rot[(rot.index >= a - pd.DateOffset(months=12)) & (rot.index <= b)].any()) for a, b in recs)
pruefe("G2", True, "Auskunft 1982-%s: ROT in %d Monaten, %d Strecken · nahe einer Rezession (+-12 Mon.): %s · Fehlalarm: %s · "
       "Rezessionen mit ROT (ab 12 Mon. vorher bis Ende): %d von %d" % (
           monate[-1].strftime("%Y-%m"), int(rot.sum()), len(st), ", ".join(treffer) or "-", ", ".join(fehl) or "-", erkannt, len(recs)))

# ══ G3 drei Zustaende ═════════════════════════════════════════════════════════════════════════════════════════════════════════
d = ML.lage_aus(roh, HEUTE)
d["gesamtmarkt"] = g
alt = dict(d, gesamtmarkt=dict(g, stand=(HEUTE - timedelta(days=ML.VERALTET_TAGE + 1)).isoformat()))
mitf = dict(d, gesamtmarkt=dict(g, fehler="HTTPError: 502 (heute)"))
z_f, z_v, z_ok, z_e = ML.zeile_gesamtmarkt({}), ML.zeile_gesamtmarkt(alt), ML.zeile_gesamtmarkt(d), ML.zeile_gesamtmarkt(mitf)
ohne = dict(d)
ohne.pop("gesamtmarkt")
pruefe("G3", ML.zustand_gesamtmarkt(None) == "fehlt" and ML.zustand_gesamtmarkt(alt) == "veraltet" and ML.zustand_gesamtmarkt(d) == "ok"
       and "NICHT VERFÜGBAR" in z_f and "VERALTET" in z_v and "VERALTET" not in z_ok and "letzter Abruf gescheitert" in z_e
       and ML.stand(alt)["gesamtmarkt"]["zustand"] == "veraltet" and ML.zeile(d) == ML.zeile(ohne) and len(g["zeilen"]) == 6
       and "High-Yield-Aufschlag" in g["zeilen"][3][2] and g["datenstand"].get("HY"),
       "fehlt / veraltet / ok / Vermerk: %s / %s / %s / %s · O54-Zeile unveraendert %s · 6 Zeilen %s · L4 mit HY-Aufschlag %s (Stand %s)" % (
           "NICHT VERFÜGBAR" in z_f, "VERALTET" in z_v, ML.zustand_gesamtmarkt(d), "gescheitert" in z_e, ML.zeile(d) == ML.zeile(ohne),
           len(g["zeilen"]) == 6, "High-Yield-Aufschlag" in g["zeilen"][3][2], g["datenstand"].get("HY")))


# ══ G4 / G5 lauf mit kaputtem Abruf ═══════════════════════════════════════════════════════════════════════════════════════════
class Kaputt:
    def get(self, *a, **k):
        raise ConnectionError("gestellt: kein Netz, api_key=%s" % KEY)


class NurO54:
    """FRED fuer die O54-Reihen echt, alles andere (Gesamtmarkt-Reihen, alternative.me) kaputt."""
    def get(self, url, params=None, **k):
        if "stlouisfed" in url and (params or {}).get("series_id") in ML.REIHEN:
            return requests.get(url, params=params, **k)
        raise ConnectionError("gestellt: Gesamtmarkt-Quelle weg, api_key=%s" % KEY)


z4 = os.path.join(T, "m.json")
ML._schreibe(z4, d)
r4 = ML.lauf(z4, KEY, HEUTE, http=Kaputt(), pause=0)
g4 = r4["gesamtmarkt"]
pruefe("G4", r4["gesamt_kurz"] == d["gesamt_kurz"] and r4["fehler"] and g4.get("kurz") == g["kurz"] and g4.get("fehler")
       and KEY not in g4["fehler"] and KEY not in r4["fehler"] and "letzter Abruf gescheitert" in ML.zeile_gesamtmarkt(ML.lade(z4)),
       "O54 alt mit Vermerk %s · Gesamtmarkt alt mit Vermerk '%s' · Schluessel verborgen %s" % (
           bool(r4["fehler"]), (g4.get("fehler") or "")[:60], KEY not in (g4.get("fehler") or "")))
z5 = os.path.join(T, "n.json")
ML._schreibe(z5, alt)
r5 = ML.lauf(z5, KEY, HEUTE, http=NurO54(), pause=0)
pruefe("G5", r5.get("fehler") is None and r5["stand"] == HEUTE.isoformat() and r5["gesamtmarkt"].get("fehler")
       and r5["gesamtmarkt"]["stand"] == alt["gesamtmarkt"]["stand"] and KEY not in r5["gesamtmarkt"]["fehler"],
       "O54 frisch %s (Stand %s) · Gesamtmarkt alter Stand %s mit Vermerk '%s'" % (
           r5.get("fehler") is None, r5["stand"], r5["gesamtmarkt"]["stand"], (r5["gesamtmarkt"].get("fehler") or "")[:50]))

# ══ G6 Mails ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
_fl = lambda x: " ".join(x.split())  # noqa: E731
mt = ML.mailteil(d)
_rf = dict(symbol="TAO", bitpanda="TAO", signalstunde="2026-10-14 10:00", einstieg="2026-10-14 11:00", ausstieg="2026-10-15 11:00",
           kurs=300.0, kurs_markt="spot", p2=0.001, p3=0.007, p5=0.107, vh=0.0411, kurs_eur=260.0)
_g = G.rechne(3, 0, G.lade())
_j = datetime(2026, 10, 14, 11, 9, tzinfo=timezone.utc)
s_mit = RM.signal_mail(_rf, 3, False, _g, {}, _j, None, None, None, None, None, mt)[1]
h_mit = RM.signal_html(_rf, 3, False, _g, {}, _j, None, None, 0, None, None, None, mt)
vorn, tech = s_mit.split("5  TECHNIK")
i_m, i_g = vorn.find("Makro"), vorn.find("Gesamtmarkt")
ok_r = 0 <= i_m < i_g and _fl(g["kurz"])[:40] in _fl(vorn) and "E-137" in tech and _fl(g["kurz"])[:40] in _fl(h_mit)
zl = ML.zeile_mail(d)
f1 = {"symbol": "TAO", "ausloese_kurs": 900.0, "startkurs_usd": 300.0, "menge": 2.0, "ende": "2027-01-01", "start": "2026-01-01",
      "ausloese_tag": "2026-09-01"}
f3 = {"symbol": "TAO", "kuerzel": "TAO", "utc": "2026-09-01 08:00:00", "alter_h": 1.5, "menge": 2.0, "id": 1, "titel": "Test"}
f4 = {"stichtag": "2026-10-01", "art": "erstliste", "liste": [("TAO", "TAO", "M", 0.8, 300, 900, 0.1, 1, None, 2.0)]}
b1 = SM.mail(f1, 1.5, False, None, None, zl)[1]
b3 = SU.mail(f3, False, None, 1.0, 1.0, None, zl)[1]
b4 = SA.mail(f4, {"TAO": 100.0}, set(), None, zl)[1]
eigene = all(any(z.strip().startswith("Gesamtmarkt ") for z in x.splitlines()) for x in (b1, b3, b4))
qb = open("scheduler/background.py", encoding="utf-8").read()
ok_job = qb.count('__import__("agent.makro_lage", fromlist=["zeile_mail"]).zeile_mail()') == 4 \
    and '__import__("agent.makro_lage", fromlist=["zeile"]).zeile()' not in qb
pruefe("G6", ok_r and eigene and ok_job, "REGEL0 'Gesamtmarkt' unter 'Makro' + Technik + HTML %s · B1/B3/B4 eigene Zeile %s · Job viermal zeile_mail %s" % (
    ok_r, eigene, ok_job))
print("     Muster B1:\n" + "\n".join("       " + z for z in b1.splitlines() if "Makro" in z or "Gesamtmarkt" in z))

# ══ G7 Statusseite, GUI, Diagnose ═════════════════════════════════════════════════════════════════════════════════════════════
qs = open("remote/server.py", encoding="utf-8").read()
import remote.status as RS  # noqa: E402
import ui.markt_tab as MT  # noqa: E402

ML.ABLAGE, _alt_ab = z4, ML.ABLAGE
try:
    gt = RS._get_makro_lage.__wrapped__() if hasattr(RS._get_makro_lage, "__wrapped__") else RS._get_makro_lage()
    import extract_notebook_diagnose as DG  # noqa: E402
    dg = DG._makro_lage()
finally:
    ML.ABLAGE = _alt_ab
ok_s = qs.index('id="makro-kopf"') < qs.index('id="gesamt-kopf"') < qs.index("section-header section-system") and "m.gesamtmarkt" in qs
pruefe("G7", ok_s and (gt.get("gesamtmarkt") or {}).get("zeilen") and len(MT.gesamt_zeilen(gt)) == 6 and "gesamtmarkt" in dg,
       "Statusseite Block in der Makro-Karte %s · Getter %d Zeilen · GUI %d Zeilen · Diagnose %s" % (
           ok_s, len((gt.get("gesamtmarkt") or {}).get("zeilen") or []), len(MT.gesamt_zeilen(gt)), "gesamtmarkt" in dg))

# ══ G8 unveraendert ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
NACH = {"prod": summe(db.DB_PATH), "ablage": summe(ML.ABLAGE)}
pruefe("G8", NACH == VOR, "Desktop-Prod unveraendert %s · echte Ablage unveraendert %s" % (NACH["prod"] == VOR["prod"], NACH["ablage"] == VOR["ablage"]))

print("\nLagebild heute:")
for z in g["zeilen"]:
    print("  %s %-20s %s" % (z[0], z[1], z[2]))
print("Mailzeile: " + ML.zeile_gesamtmarkt(d))
wegwerf.aufraeumen(T)
print("\n%d von %d bestanden" % (sum(ERG), len(ERG)))
