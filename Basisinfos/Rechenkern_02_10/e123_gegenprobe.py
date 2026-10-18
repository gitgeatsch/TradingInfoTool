"""Gegenprobe E1-E3 (18.10.2026, Schritt7 §23.69) auf ECHTEN NB-Daten - nur Kopien, nie die Originale.

    python Basisinfos/Rechenkern_02_10/e123_gegenprobe.py <regel0_signale.db (NB-Kopie)> <tradinginfotool_*.db.gz (NB-Backup)>

G1  Zuordnung: fuer jeden echten Trade seit 03.10. dasselbe Signal wie ``trades()`` (der bewaehrte Weg, s1b 37/37) - zwei Wege
G2  Zuordnung auf 2.000 Zufallsfaellen gegen eine unabhaengige Rechnung (Grenzen 1 h / 26 h, Sekunden in der Eroeffnung)
G3  E2 auf der echten Historie nachgespielt: je gemailtem Signal mit erster Erinnerung ``versende`` zum Zeitpunkt Einstieg + 73 h
    (Positionsstand aus hebel_positions der Kopie, so wie er damals war) gegen eine unabhaengig geschriebene Erwartung
G4  die Zahlen im Fakt gegen die Ausgabe von p62 (Schritt7 §23.68), neu gerechnet
"""
import gzip
import os
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
import wegwerf  # noqa: E402,F401
import agent.regel0_ablage as AB  # noqa: E402
import agent.regel0_mail as RM  # noqa: E402
import agent.regel0_messstand as MS  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok_alle = []


def pruefe(name, bed, info=""):
    ok_alle.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info and not bed else ""))


w = tempfile.mkdtemp(prefix="e123_gp_")
abl = os.path.join(w, "abl")
os.makedirs(abl)
shutil.copyfile(sys.argv[1], os.path.join(abl, AB.ABLAGE_NAME))
prod = os.path.join(w, "prod.db")
with gzip.open(sys.argv[2], "rb") as q, open(prod, "wb") as z:
    shutil.copyfileobj(q, z)
cp = sqlite3.connect("file:%s?mode=ro" % prod.replace("\\", "/"), uri=True)
print("Kopien: Ablage %s · Prod %s (%.0f MB)" % (os.path.basename(sys.argv[1]), os.path.basename(sys.argv[2]), os.path.getsize(prod) / 1e6))

# ── G1
print("G1  echte Trades: zuordnung gegen trades()")
tr = MS.trades(cp, abl)
an = 0
for t in tr:
    s = MS.zuordnung(abl, t["symbol"], datetime.strptime(t["auf"], MS.FMT))
    pruefe("G1  %s %s: Signal %s / %s" % (t["symbol"], t["auf"], t["signal"], s and s["signalstunde"]), (s or {}).get("signalstunde") == t["signal"])
    ht = MS.haltedauer_text(abl, t["symbol"], datetime.strptime(t["auf"], MS.FMT))
    pruefe("G1  %s: Haltedauer-Text passt (%s)" % (t["symbol"], ht), ("eigene Entscheidung" in ht) == (t["signal"] is None))
    an += 1
pruefe("G1  mindestens ein Trade mit und einer ohne Signal geprueft", any(t["signal"] for t in tr) and any(not t["signal"] for t in tr), str(len(tr)))

# ── G2
print("G2  2.000 Zufallsfaelle gegen eine unabhaengige Rechnung")
rnd = random.Random(18102026)
g = tempfile.mkdtemp(prefix="e123_g2_", dir=w)
c = AB.oeffne(g)
basis = datetime(2026, 10, 1)
stunden = sorted({basis + timedelta(hours=rnd.randrange(0, 400)) for _ in range(120)})
for st in stunden:
    c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, stufe, bitpanda) VALUES (?,?,?,?,?,?)",
              ("X%d" % rnd.randrange(3), st.strftime(MS.FMT), st.strftime(MS.FMT), (st + timedelta(hours=24)).strftime(MS.FMT), 3, "SYM"))
c.commit(); c.close()
falsch = []
for _ in range(2000):
    auf = basis + timedelta(seconds=rnd.randrange(0, 420 * 3600))
    if rnd.random() < 0.3:                                          # Grenzfaelle: genau 1 h / 26 h nach einer Signalstunde
        auf = rnd.choice(stunden) + timedelta(hours=rnd.choice((1, 26)), seconds=rnd.choice((0, 0, 30)))
    soll = [s for s in stunden if timedelta(hours=1) <= auf - s <= timedelta(hours=26)]
    ist = MS.zuordnung(g, "sym", auf)
    if (ist["signalstunde"] if ist else None) != (soll[-1].strftime(MS.FMT) if soll else None):
        falsch.append((auf, soll[-1:] if soll else None, ist))
pruefe("G2  2.000 Faelle, sekundengenau gleich (spaetestes Signal 1-26 h davor)", not falsch, str(falsch[:3]))

# ── G3
print("G3  E2 auf der echten Historie nachgespielt")
src = sqlite3.connect("file:%s?mode=ro" % os.path.join(abl, AB.ABLAGE_NAME).replace("\\", "/"), uri=True)
src.row_factory = sqlite3.Row
sigs = [dict(r) for r in src.execute("SELECT * FROM signal WHERE mail_signal_am IS NOT NULL AND mail_erinnerung_am IS NOT NULL "
                                     "AND COALESCE(stufe, mail_signal_stufe) > 0")]
spalten = [r[1] for r in src.execute("PRAGMA table_info(signal)")]
src.close()
pos = cp.execute("SELECT symbol, richtung, eroeffnet_am, geschlossen_am FROM hebel_positions").fetchall()


def iso(x):
    return datetime.fromisoformat(x).astimezone(timezone.utc) if x else None


def erwartung(s, t):
    name = (s.get("bitpanda") or s["symbol"]).upper()
    offen = [p for p in pos if p[0].upper() == name and (p[1] or "LONG") == "LONG" and iso(p[2]) <= t and (p[3] is None or iso(p[3]) > t)]
    if not offen:
        return "entfaellt-keine"
    sigst = datetime.strptime(s["signalstunde"], MS.FMT).replace(tzinfo=timezone.utc)
    return "entfaellt-eigene" if all(iso(p[2]) < sigst for p in offen) else "mail"


print("  %d gemailte Signale mit erster Erinnerung in der Kopie" % len(sigs))
zaehl = {}
for s in sigs:
    t = datetime.strptime(s["einstieg"], MS.FMT).replace(tzinfo=timezone.utc) + timedelta(hours=73, minutes=9)
    e = erwartung(s, t)
    d = tempfile.mkdtemp(prefix="e123_g3_", dir=w)
    c = AB.oeffne(d)
    k = [x for x in spalten if x in s]
    c.execute("INSERT INTO signal (%s) VALUES (%s)" % (",".join(k), ",".join("?" * len(k))), [s[x] for x in k])
    c.execute("UPDATE signal SET mail_erinnerung72_am=NULL, erinnerung72_entfallen_am=NULL, erinnerung72_grund=NULL")
    c.commit(); c.close()
    befund = {"stand": t - timedelta(minutes=5), "veraltet": False, "stunden": 0.1,
              "positionen": [(p[0], p[1], p[2]) for p in pos if iso(p[2]) <= t and (p[3] is None or iso(p[3]) > t)]}
    post = []
    RM.versende(d, lambda b, tx, *a: post.append(b) or True, jetzt=t, werte={}, position=lambda: befund)
    c = AB.oeffne(d)
    r = c.execute("SELECT mail_erinnerung72_am, erinnerung72_grund FROM signal").fetchone()
    c.close()
    ist = "mail" if (post and r[0]) else ("entfaellt-eigene" if "eigene" in (r[1] or "") else ("entfaellt-keine" if r[1] else "nichts"))
    zaehl[e] = zaehl.get(e, 0) + 1
    if ist != e or e == "mail":
        print("    %s %s Stufe %s: erwartet %s, versende %s %s" % (s.get("bitpanda") or s["symbol"], s["signalstunde"], s.get("stufe"), e, ist,
                                                                  post[0] if post else ""))
    pruefe("G3  %s %s" % (s.get("bitpanda") or s["symbol"], s["signalstunde"]), ist == e, "%s != %s" % (ist, e)) if ist != e else ok_alle.append(True)
print("  Erwartung je Fall: %s" % zaehl)
pruefe("G3  alle %d Faelle gleich" % len(sigs), all(ok_alle[-len(sigs):]) if sigs else False)

# ── G4
print("G4  Zahlen im Fakt gegen p62 (neu gerechnet)")
aus = subprocess.run([sys.executable, "-X", "utf8", "Basisinfos/Rechenkern_02_10/p62_ausstieg_vorpruefung.py"], capture_output=True, text=True,
                     encoding="utf-8").stdout
tag = [float(x) for x in re.findall(r"je weiterem Tag im Mittel ([+-]\d+\.\d+) %", aus)]
lq = [tuple(map(float, m)) for m in re.findall(r"binnen 24 h (\d+\.\d) / (\d+\.\d) % der Einstiege · binnen 168 h (\d+\.\d) / (\d+\.\d) %", aus)]
print("  je weiterem Tag: %s · Tief (24h -20/-33, 168h -20/-33): %s" % (tag, lq))
pruefe("G4  vier Mengen gelesen", len(tag) == 4 and len(lq) == 4, aus[-500:])
pruefe("G4  'kostete 0,3-0,4 % je weiteren Tag' deckt alle vier", tag and all(-0.45 <= x <= -0.25 for x in tag), str(tag))
pruefe("G4  5x: binnen 24 h 0,4-0,6 %, binnen 7 T 12-13 %", lq and all(0.35 <= a <= 0.65 and 11.5 <= c_ <= 13.5 for a, _b, c_, _d in lq), str(lq))
pruefe("G4  3x: binnen 24 h 0,2-0,4 %, binnen 7 T 2-4 %", lq and all(0.15 <= b <= 0.45 and 1.5 <= d_ <= 4.5 for _a, b, _c, d_ in lq), str(lq))
pruefe("G4  2024 umgekehrt (H168 netto > H24 netto)", all(float(a) < float(b) for a, b in re.findall(
    r"netto H24 ([+-]\d+\.\d+) % · H168 ([+-]\d+\.\d+) %", aus)), str(re.findall(r"Auskunft 2024.*", aus)))
cp.close()
wegwerf.aufraeumen(w)
print("%d Pruefungen, %s" % (len(ok_alle), "ALLE BESTANDEN" if all(ok_alle) else "%d FEHLGESCHLAGEN" % ok_alle.count(False)))
