"""G7 STUFE 3b — PRÜFEN nach 2.058/2.058, Weg 1 über das Modul (Code-Seite). Vorlage: Prüfung 3a vom 11.11. (Scratchpad pruef_3a.py).
Gesichert 13.11.2026, damit eine neue Sitzung nach einer Unterbrechung sofort weitermachen kann.

⚠️ Gibt KEINE Bedenken-Werte aus und schaut nicht gegen Kurse - nur Zählungen, Mengen, Prüfsummen. Ablage nur lesend.

    python -X utf8 Basisinfos/Rechenkern_02_10/g7_stufe3b_pruefen.py
Danach: g7_stufe3b_gegenpruefen.py (Weg 2, ohne Modul) · erst dann `python -m agent.finales_llm --messung` GENAU EINMAL
(vorher die Ablage kopieren) · danach g7_stufe3_messung_gegen.py.
"""
import os
import sqlite3
import sys

PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJ)
os.chdir(PROJ)
from agent import finales_llm as F      # noqa: E402

c = sqlite3.connect("file:%s?mode=ro" % F.ABLAGE.replace("\\", "/"), uri=True)
print("integrity", c.execute("PRAGMA integrity_check").fetchone()[0])
print("vorpruefung-Zeilen (Soll 1, WEITER):", c.execute("SELECT COUNT(*), MIN(ergebnis) FROM vorpruefung").fetchone())
print("messung-Zeilen (Soll 0 vor der Messung):", c.execute("SELECT COUNT(*) FROM messung").fetchone()[0])
print("prompt_sha jetzt", F.prompt_sha(), "eingefroren", F.PROMPT_EINGEFROREN, "· Modell", F.MODELL,
      "· messung_sha", F.messung_sha(), "eingefroren", F.MESSUNG_EINGEFROREN)
q = ("SELECT COUNT(*), COUNT(DISTINCT symbol||'|'||stunde), SUM(form_ok), SUM(belege_ohne_stelle), SUM(versuche), MIN(am), MAX(am), "
     "COUNT(DISTINCT modell), COUNT(DISTINCT prompt_sha), COUNT(DISTINCT modell_antwort) FROM urteil WHERE phase='3b'")
print("3b: n, eindeutig, lesbar, ohne Stelle, versuche, von, bis, #modell, #prompt, #modell_antwort =", c.execute(q).fetchone())
print("modell_antwort 3b:", c.execute("SELECT modell_antwort, COUNT(*) FROM urteil WHERE phase='3b' GROUP BY 1").fetchall())
print("Phasen:", c.execute("SELECT phase, COUNT(*) FROM urteil GROUP BY 1").fetchall())
M = F.menge()
V = set(zip(F.vorauswahl().symbol, F.vorauswahl().stunde))
W = set(zip(M.symbol, M.stunde)) - V
U = {(s, t) for s, t in c.execute("SELECT symbol, stunde FROM urteil WHERE phase='3b'")}
A = {(s, t) for s, t in c.execute("SELECT symbol, stunde FROM urteil WHERE phase='3a'")}
print("Menge b ohne Vorauswahl", len(W), "· fehlen", len(W - U), "· zuviel", len(U - W), "· 3a∩3b", len(A & U),
      "· 3a∪3b = Menge b:", (A | U) == set(zip(M.symbol, M.stunde)))
print("teil 3b:", c.execute("SELECT teil, COUNT(*) FROM urteil WHERE phase='3b' GROUP BY 1").fetchall())
n, ok = c.execute("SELECT COUNT(*), SUM(form_ok) FROM urteil WHERE phase IN ('3a','3b')").fetchone()
print("unlesbar 3a+3b: %d von %d = %.2f %% (technisch Rot ab 5 %%)" % (n - ok, n, 100 * (n - ok) / n))
qq = F.Quelle()
ge = F.eingaben_geaendert(c, qq, ("3a", "3b"))
print("eingaben_geaendert 3a+3b:", len(ge), ge[:3])
R = M[[(y, s) in W for y, s in zip(M.symbol, M.stunde)]]
vg = sum(bool(e["vorgriff"]) or bool(e["fehlt"]) for e in (F.eingabe(qq, r) for r in R.itertuples()))
print("3b: Vorgriff oder fehlende Gutachten in der Eingabe:", vg)
print("darf_3b:", F.darf_3b(c))
