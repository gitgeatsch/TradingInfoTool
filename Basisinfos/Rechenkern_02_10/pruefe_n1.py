"""N-1 (E-57, 04.10.2026) am SEITENEFFEKT: verpasste Signalstunden nachrechnen - R-R11 gegen den lueckenlosen Lauf.

A  Stundenlaeufe T0 .. T0+6 lueckenlos                   (so haette der Betrieb gerechnet)
B  Stundenlaeufe T0 und T0+6 - dazwischen Ausfall 5 h    (der Lauf T0+6 holt die Signalstunden T0+1 .. T0+3 nach)
Erwartung: B legt fuer jede Signalstunde, die A ablegt, DIESELBEN Signale (Symbol, v-dach, endgueltige Stufe) ab - ausser der
Stunde T0, die ausserhalb des 3-h-Fensters liegt (sie darf fehlen und muss als verloren erkennbar sein).
Dazu die Mail: ein nachgeholtes Signal, dessen Einstieg vorbei ist, bekommt KEINE Signalmail, sondern den Vermerk *verpasst*.

Am Desktop gegen die Messbasis, Ablage und Modelle in Wegwerfordnern (die Daten nur lesend) - kein Netz, keine Mail.
"""
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.getcwd())
import agent.regel0_ablage as AB
import agent.regel0_mail as RM
import agent.regel0_stundenlauf as SL

ok_alle = []


def pruefe(name, bed, info=""):
    ok_alle.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % str(info)[:400]) if info and not bed else ""), flush=True)


def h_von(txt):
    return int((datetime.strptime(txt, "%Y-%m-%d %H:%M") - datetime(2020, 1, 1)).total_seconds() // 3600)


def h_txt(h):
    return (datetime(2020, 1, 1) + timedelta(hours=h)).strftime("%Y-%m-%d %H:%M")


def signale(abl):
    c = sqlite3.connect(os.path.join(abl, AB.ABLAGE_NAME))
    z = {(r[0], r[1]): (round(r[2], 9), r[3]) for r in c.execute("SELECT symbol, signalstunde, vh, stufe FROM signal")}
    nh = [r[0] for r in c.execute("SELECT signalstunde FROM nachgeholt")]
    c.close()
    return z, nh


T0 = h_von(sys.argv[1]) if len(sys.argv) > 1 else h_von("2026-09-23 10:00")
MOD = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp(prefix="r0_n1_mod_")
A, B = tempfile.mkdtemp(prefix="r0_n1_A_"), tempfile.mkdtemp(prefix="r0_n1_B_")
still = lambda *a, **k: None
print("N-1 Nachholen - R-R11 am Desktop, T0 = %s, Modelle %s" % (h_txt(T0), MOD), flush=True)
for t in range(T0, T0 + 7):
    SL.betrieb_lauf("data", t, A, MOD, ausgabe=still)
for t in (T0, T0 + 6):
    SL.betrieb_lauf("data", t, B, MOD, ausgabe=still)
sa, _ = signale(A)
sb, nh = signale(B)
# T0+1..T0+3 fehlten ganz; T0-1 hatte nur die vorlaeufige Stufe (der Lauf T0+1 fiel aus) und bekommt die endgueltige -
# aber nur, wenn es in T0-1 ueberhaupt ein Signal gab
_soll = [h_txt(T0 + i) for i in (1, 2, 3)]
_vor = any(k[1] == h_txt(T0 - 1) for k in sb)
pruefe("B hat die Signalstunden T0+1 .. T0+3 nachgeholt (und T0-1 nachgerechnet, wenn dort ein Signal lag) und vermerkt",
       sorted(nh) == sorted(_soll + ([h_txt(T0 - 1)] if _vor else [])), nh)
std_b = {h_txt(T0 + i) for i in (-2, -1, 1, 2, 3, 4, 5)}
a_teil = {k: v for k, v in sa.items() if k[1] in std_b}
b_teil = {k: v for k, v in sb.items() if k[1] in std_b}
# die juengste Stunde (T0+5) ist in A wie B nur VORLAEUFIG - beide mit derselben ATR der Signalstunde, also gleich
print("  verglichen: %d Signale in A, %d in B (Signalstunden T0-2..T0+5 ohne T0), davon in nachgeholten Stunden %d" % (
    len(a_teil), len(b_teil), sum(1 for k in b_teil if k[1] in nh)), flush=True)
pruefe("⭐ R-R11: dieselben Signale mit derselben v-dach und Stufe (Signalstunden T0-2..T0+5 ohne T0)",
       a_teil == b_teil and len(a_teil) > 0, "nur A %s / nur B %s / Stufe anders %s / A %d B %d" % (
           sorted(set(a_teil) - set(b_teil))[:5], sorted(set(b_teil) - set(a_teil))[:5],
           [(k, a_teil[k], b_teil[k]) for k in set(a_teil) & set(b_teil) if a_teil[k] != b_teil[k]][:5], len(a_teil), len(b_teil)))
verl = {k for k in sa if k[1] == h_txt(T0)}
pruefe("die Stunde T0 (ausserhalb 3 h) fehlt in B - erwartet; sie ist verloren und T1 der Testwoche muss sie nennen",
       not ({k for k in sb if k[1] == h_txt(T0)}), "%d Signale in A zur Stunde T0" % len(verl))
sys.path.insert(0, os.path.join(os.getcwd(), "Basisinfos", "Rechenkern_02_10"))
import pruefe_testwoche as PT
e = PT.auswerten(os.path.join(B, AB.ABLAGE_NAME), von=h_txt(T0), bis=h_txt(T0 + 6))
pruefe("T1 der Testwoche: in B ist genau die Signalstunde T0 verloren, die nachgeholten zaehlen nicht als verloren",
       (not e["bedingungen"]["T1 jede Stunde gerechnet"][0]) and ("verlorene Signalstunden: %s" % (datetime(2020, 1, 1) + timedelta(hours=T0)).strftime("%d.%m. %H:00"))
       in e["bedingungen"]["T1 jede Stunde gerechnet"][1] and "," not in e["bedingungen"]["T1 jede Stunde gerechnet"][1].split("verlorene Signalstunden:")[1],
       e["bedingungen"]["T1 jede Stunde gerechnet"][1])
e2 = PT.auswerten(os.path.join(A, AB.ABLAGE_NAME), von=h_txt(T0), bis=h_txt(T0 + 6))
pruefe("T1 der Testwoche: der lueckenlose Lauf A hat nichts verloren", e2["bedingungen"]["T1 jede Stunde gerechnet"][0],
       e2["bedingungen"]["T1 jede Stunde gerechnet"][1])

# Mail: nachgeholt und Einstieg vorbei -> verpasst, keine Signalmail; ein frisches Signal geht raus
d = tempfile.mkdtemp(prefix="r0_n1_mail_")
c = AB.oeffne(d)
for sym, sh in (("ALT", "2026-10-05 07:00"), ("NEU", "2026-10-05 10:00")):
    hh = datetime.strptime(sh, "%Y-%m-%d %H:%M")
    c.execute("INSERT INTO signal (symbol, signalstunde, einstieg, ausstieg, stufe_vorlaeufig, stufe, hebel_schalter, bitpanda) VALUES (?,?,?,?,?,?,?,?)",
              (sym, sh, (hh + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"), (hh + timedelta(hours=25)).strftime("%Y-%m-%d %H:%M"), 3, 3, 1, sym))
c.commit(); c.close()
post = []
z = RM.versende(d, lambda b, t, *a: post.append(b) or True, jetzt=datetime(2026, 10, 5, 11, 9, tzinfo=timezone.utc), werte=__import__(
    "agent.regel0_groesse", fromlist=["lade"]).lade(), kurse=lambda: (None, None))
c = sqlite3.connect(os.path.join(d, AB.ABLAGE_NAME))
v = dict(c.execute("SELECT symbol, mail_verpasst_am FROM signal").fetchall())
c.close()
pruefe("Mail: Einstieg vorbei (ALT, Einstieg 08:00, Schluss 09:00 UTC) -> verpasst, keine Mail; NEU -> Signalmail",
       z["verpasst"] == 1 and z["signal"] == 1 and v.get("ALT") and not v.get("NEU") and len(post) == 1 and " NEU " in post[0], (z, v, post))
for x in (A, B, d):
    shutil.rmtree(x, ignore_errors=True)
print("%d Pruefungen, %s" % (len(ok_alle), "ALLE BESTANDEN" if all(ok_alle) else "%d FEHLGESCHLAGEN" % ok_alle.count(False)), flush=True)
