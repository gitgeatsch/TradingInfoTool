"""A1 — DRITTE Stichprobe: Prompt 3 gegen Prompt 2 (Voranalyse_A1 §8, Nutzer 01.11.: „a, Prompt 3 – prüfen, gegenprüfen und doku“).

REIHENFOLGE (nachweisbar über die Commits):
  1. Prompt 3 geschrieben NUR aus den Fehlern der zweiten Stichprobe (a1_nachweis.txt), vor dem Ziehen dieser Stichprobe
  2. --ziehe: 60 Nachrichten (30 Vorfilter-Treffer, 30 ohne, Saat 20261103), ohne die 150 der Stichproben 1 und 2
  3. Handeinordnung a1_stichprobe3_hand.csv VOR jedem LLM-Lauf auf dieser Stichprobe, festgeschrieben per Commit
  4. --llm: Prompt 3 (Lauf 11 und 12) und Prompt 2 (aus Commit 06a6bf83, Lauf 11) auf denselben 60 Titeln
  5. Auswertung ohne Netz -> a1_validierung3.txt

VORAB FESTGELEGT (01.11.2026, vor dem LLM-Lauf):
  * Messgrößen wie in a1_nachweis.validierung: Typ richtig, Ereignis ja/nein, Asset (Hand-Ereignis mit bekannten Assets), Sicht
    relevant ja/nein; dazu FEHLALARM = LLM relevant, Hand nicht · VERLUST = Hand relevant, LLM nicht
  * ENTSCHEIDUNG: Prompt 3 ersetzt Prompt 2, wenn er (1) WENIGER Fehlalarme hat UND (2) höchstens EINEN Verlust mehr. Sonst bleibt
    Prompt 2 (Modul zurück). Gepaarter Vorzeichentest auf „Sicht relevant ja/nein gleich“ nur als Auskunft (60 sind wenig)
  * Hochrechnung auf alle Nachrichten mit den Schichtgewichten (3.533 Treffer, 21.660 ohne) — Auskunft
  * Prompt 3 auf Stichprobe 2 ist GESCHÖNT (dort wurde er hergeleitet) — wird nicht gerechnet

    python a1_validierung3.py --ziehe
    python a1_validierung3.py --llm      # ~3 x 3 Stapel Groq (~25.000 Token) in data/_a1/a1_stichprobe_llm.db
    python a1_validierung3.py
"""
import importlib.util
import json
import math
import os
import sqlite3
import subprocess
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
from agent import ereignisse as E  # noqa: E402

SAAT = 20261103
LLM_DB = os.path.join(PROJ, "data", "_a1", "a1_stichprobe_llm.db")
P2_COMMIT = "06a6bf83"
GG = {"nachricht_treffer": 3533, "nachricht_kein": 21660}
QUELLE = "stichprobe3"
AUS = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    AUS.append(s)


def wilson(k, n, z=1.96):
    q = k / n
    m = (q + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(q * (1 - q) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return q, max(0, m - h), min(1, m + h)


def fmt(k, n):
    q, lo, hi = wilson(k, n)
    return "%d/%d = %.0f %% [%.0f–%.0f]" % (k, n, 100 * q, 100 * lo, 100 * hi)


def ziehe():
    alt = set(pd.read_csv(os.path.join(HIER, "a1_stichprobe.csv")).meldung) | set(pd.read_csv(os.path.join(HIER, "a1_stichprobe2.csv")).meldung)
    N = E.meldungen("nachricht")
    N = N[(N.zeit >= "2025-12-01") & (N.zeit < "2026-10-17") & ~N.meldung.isin(alt)]
    N["vf"] = N.titel.map(E.vorfilter)
    S = pd.concat([N[N.vf].sample(30, random_state=SAAT).assign(schicht="nachricht_treffer"),
                   N[~N.vf].sample(30, random_state=SAAT).assign(schicht="nachricht_kein")], ignore_index=True)
    S["nr"] = range(401, 401 + len(S))
    S[["nr", "schicht", "quelle", "meldung", "zeit", "titel"]].to_csv(os.path.join(HIER, "a1_stichprobe3.csv"), index=False, encoding="utf-8")
    print(len(S), "gezogen, ausgeschlossen", len(alt))


def prompt2_modul():
    """Prompt 2 genau so, wie er am 01.11. gebaut war - aus dem Commit, nicht nachgeschrieben."""
    ziel = os.path.join(PROJ, "data", "_a1", "ereignisse_prompt2.py")
    open(ziel, "w", encoding="utf-8").write(subprocess.check_output(["git", "show", "%s:agent/ereignisse.py" % P2_COMMIT], cwd=PROJ, text=True,
                                                                     encoding="utf-8"))
    s = importlib.util.spec_from_file_location("ereignisse_prompt2", ziel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def stichprobe3():
    S = pd.read_csv(os.path.join(HIER, "a1_stichprobe3.csv"))
    H = pd.read_csv(os.path.join(HIER, "a1_stichprobe3_hand.csv"), sep=";", keep_default_na=False)
    assert sorted(H.nr) == sorted(S.nr), "Handeinordnung unvollständig"
    return S.merge(H, on="nr")


def llm():
    from dotenv import dotenv_values
    key = dotenv_values(os.path.join(PROJ, ".env")).get("GROQ_API_KEY")
    S = stichprobe3()
    S["quelle"], S["meldung"] = QUELLE, S.nr.astype(str)
    M = S[["quelle", "meldung", "titel"]]
    P2 = prompt2_modul()
    c = E.verbinde(LLM_DB)
    print("Prompt 3", E.PROMPT_SHA, "Lauf 11", E.llm_lauf(c, M, key, lauf=11), "Lauf 12", E.llm_lauf(c, M, key, lauf=12))
    print("Prompt 2", P2.PROMPT_SHA, "Lauf 11", P2.llm_lauf(c, M, key, lauf=11))
    c.close()


def antworten(c, lauf, sha):
    L = pd.read_sql("SELECT meldung, typ, assets, bereich FROM llm_antwort WHERE quelle=? AND lauf=? AND prompt_sha=?", c,
                    params=(QUELLE, lauf, sha))
    assert len(L) == 60, "Lauf %d / %s: %d Antworten" % (lauf, sha, len(L))
    return L.set_index("meldung")


def bewerte(S, L, W, A, name):
    """Je Meldung: LLM-Typ, -Ereignis, -Assets, -Sicht; die Hand-Spalten stehen schon in S."""
    R = pd.DataFrame(index=S.index)
    R["typ"] = [L.loc[str(n)].typ for n in S.nr]
    R["bereich"] = [L.loc[str(n)].bereich for n in S.nr]
    R["assets"] = [json.dumps(E.assets_pruefen(json.loads(L.loc[str(n)].assets), t, W, A)) for n, t in zip(S.nr, S.titel)]
    R["ereignis"] = ~R.typ.isin(E.KEIN_EREIGNIS)
    R["sicht"] = [E.sicht(json.loads(a), b) if e else None for a, b, e in zip(R.assets, R.bereich, R.ereignis)]
    sa = S.h_ereignis & S.h_assets_w.notna()
    hs, ms = S.h_sicht, R.sicht
    beide = hs.notna() & ms.notna()
    fa, ve = int((hs.isna() & ms.notna()).sum()), int((hs.notna() & ms.isna()).sum())
    p("\n%s" % name)
    p("  Typ richtig %s · Ereignis ja/nein %s · Asset (Hand-Ereignis) %s" % (
        fmt((S.typ == R.typ).sum(), len(S)), fmt((S.h_ereignis == R.ereignis).sum(), len(S)),
        fmt((S.h_assets_w[sa] == R.assets[sa]).sum(), int(sa.sum()))))
    p("  Sicht relevant ja/nein gleich %s · beide relevant, gleiche Sicht %s · FEHLALARM %d · VERLUST %d" % (
        fmt((hs.notna() == ms.notna()).sum(), len(S)), fmt((hs[beide] == ms[beide]).sum(), int(beide.sum())), fa, ve))
    # Hochrechnung: Anteil der Nachrichten, die fälschlich an eine Sicht gehen / fälschlich fehlen (Schichtgewichte)
    g = S.schicht.map(GG) / S.schicht.map(S.schicht.value_counts())
    p("  hochgerechnet auf alle Nachrichten: Fehlalarm %.0f %% · Verlust %.0f %% · Sicht relevant gleich %.0f %%" % (
        100 * (g * (hs.isna() & ms.notna())).sum() / g.sum(), 100 * (g * (hs.notna() & ms.isna())).sum() / g.sum(),
        100 * (g * (hs.notna() == ms.notna())).sum() / g.sum()))
    for i in S.index[(S.typ != R.typ) | (hs.notna() != ms.notna()) | (beide & (hs != ms))]:
        p("    %3d %-20s -> %-20s Sicht %-5s -> %-5s %s" % (S.nr[i], S.typ[i], R.typ[i], hs[i], ms[i], S.titel[i][:70]))
    R["ok"] = hs.notna() == ms.notna()
    return R, fa, ve


def vorzeichen(a, b):
    """exakter zweiseitiger Vorzeichentest auf den gepaarten Abweichungen (McNemar)."""
    n, k = int((a != b).sum()), int((a & ~b).sum())
    if n == 0:
        return k, n, 1.0
    q = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1)) / 2 ** n
    return k, n, min(1.0, 2 * q)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if "--ziehe" in sys.argv:
        return ziehe()
    if "--llm" in sys.argv:
        return llm()
    W, A = E.welt(), E.alias()
    P2 = prompt2_modul()
    S = stichprobe3()
    S["h_ereignis"] = ~S.typ.isin(E.KEIN_EREIGNIS)
    S["h_assets_w"] = [None if x.strip() == "?" else json.dumps(sorted({k for k in x.split() if k in W})) for x in S.assets]
    S["h_sicht"] = pd.Series([E.sicht(json.loads(a) if a else [], b) if (e and b != "sonstiges") else None
                              for a, b, e in zip(S.h_assets_w.fillna("[]"), S.bereich, S.h_ereignis)], index=S.index)
    c = sqlite3.connect("file:%s?mode=ro" % LLM_DB.replace("\\", "/"), uri=True)
    p("A1 VALIDIERUNG 3 · Modell %s · Prompt 3 %s gegen Prompt 2 %s · 60 Nachrichten (30 Treffer, 30 ohne) · Hand vorher festgeschrieben"
      % (E.MODELL, E.PROMPT_SHA, P2.PROMPT_SHA))
    p("  Hand: %d Ereignisse, davon %d an eine Sicht" % (int(S.h_ereignis.sum()), int(S.h_sicht.notna().sum())))
    R2, fa2, ve2 = bewerte(S, antworten(c, 11, P2.PROMPT_SHA), W, A, "PROMPT 2 (%s) — zweite gültige Messung" % P2.PROMPT_SHA)
    R3, fa3, ve3 = bewerte(S, antworten(c, 11, E.PROMPT_SHA), W, A, "PROMPT 3 (%s)" % E.PROMPT_SHA)
    L12 = antworten(c, 12, E.PROMPT_SHA)
    p("\nP4 Prompt 3, derselbe Stapel zweimal: gleicher Typ %s" % fmt(sum(R3.typ[i] == L12.loc[str(n)].typ for i, n in zip(S.index, S.nr)), 60))
    k, n, pw = vorzeichen(R3.ok, R2.ok)
    p("Gepaart (Auskunft): Sicht relevant ja/nein — nur Prompt 3 richtig %d, nur Prompt 2 richtig %d · Vorzeichentest p = %.2f" % (k, n - k, pw))
    ja = fa3 < fa2 and ve3 <= ve2 + 1
    p("\nENTSCHEIDUNG (vorab): Fehlalarm %d -> %d (%s), Verlust %d -> %d (%s) => %s" % (
        fa2, fa3, "weniger" if fa3 < fa2 else "NICHT weniger", ve2, ve3, "höchstens +1" if ve3 <= ve2 + 1 else "MEHR als +1",
        "PROMPT 3 ERSETZT PROMPT 2" if ja else "PROMPT 2 BLEIBT"))
    open(os.path.join(HIER, "a1_validierung3.txt"), "w", encoding="utf-8").write("\n".join(AUS) + "\n")


if __name__ == "__main__":
    main()
