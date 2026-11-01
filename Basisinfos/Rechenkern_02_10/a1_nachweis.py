"""A1 NACHWEIS (Voranalyse_A1 §5 P1-P5) - gegen die HANDEINORDNUNG a1_stichprobe_hand.csv (festgeschrieben VOR jedem Blick auf die Ausgabe des
Moduls, git hash-object e798513c).

ABLAUF: Prompt 1 (35eb32461b60) -> a1_nachweis_prompt1.txt; die Bereiche fehlten im Prompt -> Prompt 2. Auf Stichprobe 1 ist Prompt 2
GESCHOENT (dort wurde der Fehler gefunden); die GUELTIGE Zahl kommt aus Stichprobe 2 (a1_stichprobe2.py, Hand 05caccb8).
SEIT PROMPT 3 (7b94d07d7d1d, a1_validierung3.py): dieses Skript liest die Antworten zum AKTUELLEN Prompt - die Ausgabe in
a1_nachweis.txt gilt fuer Prompt 2 (05e921720b82) und ist nur mit dem Modul aus Commit 06a6bf83 reproduzierbar.

VORAB FESTGELEGT (01.11.2026, vor der Auswertung):
  * Bewertet wird, was das Modul im Weg a liefert: Börse mit Regel -> Regel; Börse ohne Regel -> LLM; Nachricht mit Vorfilter-Treffer -> LLM;
    Nachricht OHNE Treffer -> "nicht gelesen" = kein Ereignis.
  * Typ richtig = gleicher Typ wie die Hand. Ereignis richtig = beide (typ nicht in KEIN_EREIGNIS) gleich. Asset richtig = nur auf
    Hand-Ereignissen mit bekannten Assets (nicht "?"), Mengen gleich nach Schnitt mit dem Universum.
  * Band: Wilson 95 %. Je Schicht getrennt; Nachrichten zusätzlich: wie gut wäre das LLM auf ALLEN 90 (Weg b).
  * VORFILTER-VOLLSTÄNDIGKEIT (die Bedingung aus Weg a): relevante Ereignisse = Hand-Ereignis mit bereich != sonstiges. Hochgerechnet
    auf die Grundgesamtheit (3.533 Treffer, 21.660 ohne). RISIKO-Typen = hack_exploit, depeg_aussetzung, delisting_*, paar_entfernt,
    regulierung_klage. KRITERIUM: Weg a bleibt, wenn der Filter von den relevanten RISIKO-Ereignissen >= 90 % erfasst (Punktwert) UND
    die obere Wilson-Grenze des Anteils relevanter Risiko-Ereignisse unter den Nicht-Treffern <= 5 % liegt. Sonst: Weg b.
  * P4: dieselben Stapel zweimal (Lauf 11, 12) -> Anteil gleicher Typ. P5-Kontext: Antwort im zeitlich geordneten Hauptlauf (Lauf 1)
    gegen den gemischten Stapel (Lauf 11) - nur Auskunft, sobald Lauf 1 die Stichprobe enthält.

    python a1_nachweis.py --llm        # Lauf 11 und 12 auf der Stichprobe (Groq, ~40.000 Token) in data/_a1/a1_stichprobe_llm.db
    python a1_nachweis.py              # Auswertung ohne Netz -> a1_nachweis.txt
"""
import json
import math
import os
import sqlite3
import sys

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, PROJ)
from agent import binance_ankuendigungen as BA  # noqa: E402
from agent import ereignisse as E  # noqa: E402

LLM_DB = os.path.join(PROJ, "data", "_a1", "a1_stichprobe_llm.db")
RISIKO = ("hack_exploit", "depeg_aussetzung", "delisting_token", "delisting_futures", "delisting_margin", "paar_entfernt", "regulierung_klage")
GG = {"nachricht_treffer": 3533, "nachricht_kein": 21660}
AUS = []


def p(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    AUS.append(s)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 3
    q = k / n
    m = (q + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(q * (1 - q) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return q, max(0, m - h), min(1, m + h)


def fmt(k, n):
    q, lo, hi = wilson(k, n)
    return "%d/%d = %.0f %% [%.0f–%.0f]" % (k, n, 100 * q, 100 * lo, 100 * hi)


def stichprobe():
    S = pd.read_csv(os.path.join(HIER, "a1_stichprobe.csv"))
    H = pd.read_csv(os.path.join(HIER, "a1_stichprobe_hand.csv"), sep=";", keep_default_na=False)
    S = S.merge(H, on="nr")
    S["zeit"] = pd.to_datetime(S.zeit, utc=True, format="ISO8601")
    return S


def llm_lauf_stichprobe():
    from dotenv import dotenv_values
    key = dotenv_values(os.path.join(PROJ, ".env")).get("GROQ_API_KEY")
    S = stichprobe()
    S["regel"] = [E.regel(t, E.B_REGELN if q == "binance" else E.U_REGELN) if q != "nachricht" else None for t, q in zip(S.titel, S.quelle)]
    M = S[S.regel.isna()].copy()                              # alles, was das LLM sieht (Börsen-Rest + alle 90 Nachrichten)
    M["quelle"] = "stichprobe"                                 # ein gemischter Stapel in nr-Reihenfolge
    M["meldung"] = M.nr.astype(str)
    c = E.verbinde(LLM_DB)
    for lauf in (11, 12):
        print(lauf, E.llm_lauf(c, M[["quelle", "meldung", "titel"]], key, lauf=lauf))
    S2 = stichprobe2()
    S2["quelle"], S2["meldung"] = "stichprobe2", S2.nr.astype(str)
    print("S2", E.llm_lauf(c, S2[["quelle", "meldung", "titel"]], key, lauf=11))
    c.close()


def stichprobe2():
    S = pd.read_csv(os.path.join(HIER, "a1_stichprobe2.csv"))
    H = pd.read_csv(os.path.join(HIER, "a1_stichprobe2_hand.csv"), sep=";", keep_default_na=False)
    return S.merge(H, on="nr")


def validierung(W, A, L):
    """ZWEITE Stichprobe (60 Nachrichten, nach Prompt 2 gezogen, Hand vorher festgeschrieben 05caccb8): die GUELTIGE Zahl fuer Prompt 2."""
    S = stichprobe2()
    S["h_ereignis"] = ~S.typ.isin(E.KEIN_EREIGNIS)
    S["h_assets_w"] = [None if x.strip() == "?" else json.dumps(sorted({k for k in x.split() if k in W})) for x in S.assets]
    S["l_typ"] = [L.loc[str(n)].typ for n in S.nr]
    S["l_bereich"] = [L.loc[str(n)].bereich for n in S.nr]
    S["l_assets"] = [json.dumps(E.assets_pruefen(json.loads(L.loc[str(n)].assets), t, W, A)) for n, t in zip(S.nr, S.titel)]
    S["l_ereignis"] = ~S.l_typ.isin(E.KEIN_EREIGNIS)
    hs = pd.Series([E.sicht(json.loads(a) if a else [], b) if (e and b != "sonstiges") else None
                    for a, b, e in zip(S.h_assets_w.fillna("[]"), S.bereich, S.h_ereignis)], index=S.index)
    ms = pd.Series([E.sicht(json.loads(a), b) if e else None for a, b, e in zip(S.l_assets, S.l_bereich, S.l_ereignis)], index=S.index)
    p("\nVALIDIERUNG PROMPT 2 — zweite Stichprobe, 60 Nachrichten, alle per LLM (Weg b), Hand vorher festgeschrieben (05caccb8)")
    sa = S[S.h_ereignis & S.h_assets_w.notna()]
    beide = hs.notna() & ms.notna()
    p("  Typ richtig %s · Ereignis ja/nein %s · Asset (Hand-Ereignis) %s" % (
        fmt((S.typ == S.l_typ).sum(), len(S)), fmt((S.h_ereignis == S.l_ereignis).sum(), len(S)),
        fmt((sa.h_assets_w == sa.l_assets).sum(), len(sa))))
    p("  Sicht: relevant ja/nein gleich %s · beide relevant, gleiche Sicht %s · Hand relevant, LLM nicht %d · LLM relevant, Hand nicht %d"
      % (fmt((hs.notna() == ms.notna()).sum(), len(S)), fmt((hs[beide] == ms[beide]).sum(), int(beide.sum())),
         int((hs.notna() & ms.isna()).sum()), int((hs.isna() & ms.notna()).sum())))
    for i in S.index[(S.typ != S.l_typ) | (hs.notna() != ms.notna()) | (beide & (hs != ms))]:
        p("    %3d %-20s -> %-20s Sicht %-5s -> %-5s %s" % (S.nr[i], S.typ[i], S.l_typ[i], hs[i], ms[i], S.titel[i][:70]))
    rel = hs.notna() & S.typ.isin(RISIKO)
    k_t, k_k = int((rel & (S.schicht == "nachricht_treffer")).sum()), int((rel & (S.schicht == "nachricht_kein")).sum())
    p("  Vorfilter, zweiter Blick: relevante Risiko-Ereignisse unter Treffern %s, ohne Treffer %s" % (fmt(k_t, 30), fmt(k_k, 30)))


def antworten(c, lauf, quelle="stichprobe"):
    L = pd.read_sql("SELECT meldung, typ, assets, bereich FROM llm_antwort WHERE quelle=? AND lauf=? AND prompt_sha=?", c,
                    params=(quelle, lauf, E.PROMPT_SHA))
    return L.set_index("meldung")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    if "--llm" in sys.argv:
        llm_lauf_stichprobe()
        return
    W, A = E.welt(), E.alias()
    S = stichprobe()
    c = sqlite3.connect("file:%s?mode=ro" % LLM_DB.replace("\\", "/"), uri=True)
    L11, L12 = antworten(c, 11), antworten(c, 12)
    p("A1 NACHWEIS · Prompt %s · Modell %s · Stichprobe %d · Universum %d" % (E.PROMPT_SHA, E.MODELL, len(S), len(W)))
    # ---- Ausgabe des Moduls je Meldung (Weg a)
    rows = []
    for r in S.itertuples():
        llm = L11.loc[str(r.nr)] if str(r.nr) in L11.index else None
        if r.quelle in ("binance", "upbit"):
            typ = E.regel(r.titel, E.B_REGELN if r.quelle == "binance" else E.U_REGELN)
            if typ is not None:
                a = E.binance_assets(typ, r.titel, "" if pd.isna(r.textanfang) else _volltext(r.meldung), W) if r.quelle == "binance" \
                    else E.upbit_assets(r.titel, W)
                meth = "regel"
            else:
                typ, a, meth = llm.typ, E.assets_pruefen(json.loads(llm.assets), r.titel, W, A), "llm"
        elif r.schicht == "nachricht_treffer":
            typ, a, meth = llm.typ, E.assets_pruefen(json.loads(llm.assets), r.titel, W, A), "llm"
        else:
            typ, a, meth = "nicht_gelesen", [], "vorfilter"
        b_typ = llm.typ if llm is not None else None
        b_a = E.assets_pruefen(json.loads(llm.assets), r.titel, W, A) if llm is not None else None
        rows.append((typ, json.dumps(a), meth, b_typ, None if b_a is None else json.dumps(b_a)))
    S[["m_typ", "m_assets", "methode", "b_typ", "b_assets"]] = pd.DataFrame(rows, index=S.index)
    S["h_ereignis"] = ~S.typ.isin(E.KEIN_EREIGNIS)
    S["m_ereignis"] = ~S.m_typ.isin(E.KEIN_EREIGNIS + ("nicht_gelesen",))
    S["h_assets_w"] = [None if x.strip() == "?" else json.dumps(sorted({k for k in x.split() if k in W})) for x in S.assets]

    p("\nP1/P2 — gegen die Hand, Wilson 95 % (Weg a, wie das Modul liefert)")
    p("%-20s %-8s %-28s %-28s %-28s" % ("Schicht", "Methode", "Typ richtig", "Ereignis ja/nein richtig", "Asset richtig (Hand-Ereignis)"))
    for (sch, meth), g in S.groupby(["schicht", "methode"], sort=False):
        ga = g[g.h_ereignis & g.h_assets_w.notna()]
        p("%-20s %-8s %-28s %-28s %-28s" % (sch, meth, fmt((g.typ == g.m_typ).sum(), len(g)), fmt((g.h_ereignis == g.m_ereignis).sum(), len(g)),
                                           fmt((ga.h_assets_w == ga.m_assets).sum(), len(ga))))
    nb = S[S.quelle == "nachricht"]
    nba = nb[nb.h_ereignis & nb.h_assets_w.notna()]
    p("%-20s %-8s %-28s %-28s %-28s" % ("nachricht (alle 90)", "llm=b", fmt((nb.typ == nb.b_typ).sum(), len(nb)),
                                       fmt((nb.h_ereignis == ~nb.b_typ.isin(E.KEIN_EREIGNIS)).sum(), len(nb)),
                                       fmt((nba.h_assets_w == nba.b_assets).sum(), len(nba))))
    p("\nAbweichungen Typ (Hand -> Modul):")
    for r in S[S.typ != S.m_typ].itertuples():
        p("  %3d %-17s %-20s -> %-20s %s" % (r.nr, r.schicht, r.typ, r.m_typ, r.titel[:80]))
    p("\nAbweichungen Asset auf Hand-Ereignissen (Hand ∩ Universum -> Modul):")
    for r in S[S.h_ereignis & S.h_assets_w.notna() & (S.h_assets_w != S.m_assets) & (S.methode != "vorfilter")].itertuples():
        p("  %3d %-17s %-24s -> %-24s %s" % (r.nr, r.schicht, r.h_assets_w, r.m_assets, r.titel[:70]))

    # AUSKUNFT - nach der ersten Auswertung ergänzt, KEIN Kriterium: was bei den SICHTEN ankommt. Viele Typ-Abweichungen betreffen
    # Meldungen ohne Krypto-/Makro-Bezug (Hand: bereich sonstiges) - die gehen an keine Sicht, ihr Typ ist dort gleichgültig.
    p("\nAUSKUNFT (nachträglich, kein Kriterium) — Nachrichten, alle 90 per LLM (Weg b): kommt die Meldung bei derselben Sicht an?")
    hs = [E.sicht(json.loads(a) if a else [], b) if (e and b != "sonstiges") else None
          for a, b, e in zip(nb.h_assets_w.fillna("[]"), nb.bereich, nb.h_ereignis)]
    ms = []
    for r in nb.itertuples():
        x = L11.loc[str(r.nr)]
        ms.append(E.sicht(json.loads(r.b_assets), x.bereich) if x.typ not in E.KEIN_EREIGNIS else None)
    hs, ms = pd.Series(hs, index=nb.index), pd.Series(ms, index=nb.index)
    beide = hs.notna() & ms.notna()
    p("  relevant ja/nein gleich %s · beide relevant: gleiche Sicht %s · Hand relevant, LLM nicht %d · LLM relevant, Hand nicht %d" % (
        fmt((hs.notna() == ms.notna()).sum(), len(nb)), fmt((hs[beide] == ms[beide]).sum(), int(beide.sum())),
        int((hs.notna() & ms.isna()).sum()), int((hs.isna() & ms.notna()).sum())))
    for i in nb.index[(hs.notna() != ms.notna()) | (beide & (hs != ms))]:
        p("    %3d Hand %-5s LLM %-5s %s" % (nb.nr[i], hs[i], ms[i], nb.titel[i][:80]))

    p("\nVORFILTER-VOLLSTÄNDIGKEIT (Bedingung aus Weg a, Kriterium vorab im Kopf)")
    rel = nb.h_ereignis & (nb.bereich != "sonstiges")
    for name, maske in (("relevante Ereignisse", rel), ("relevante RISIKO-Ereignisse", rel & nb.typ.isin(RISIKO))):
        k_t = int((maske & (nb.schicht == "nachricht_treffer")).sum())
        k_k = int((maske & (nb.schicht == "nachricht_kein")).sum())
        q_t, q_k = wilson(k_t, 45), wilson(k_k, 45)
        n_t, n_k = q_t[0] * GG["nachricht_treffer"], q_k[0] * GG["nachricht_kein"]
        rec = n_t / (n_t + n_k) if n_t + n_k else float("nan")
        rec_lo = q_t[1] * GG["nachricht_treffer"] / (q_t[1] * GG["nachricht_treffer"] + q_k[2] * GG["nachricht_kein"])
        rec_hi = q_t[2] * GG["nachricht_treffer"] / (q_t[2] * GG["nachricht_treffer"] + q_k[1] * GG["nachricht_kein"])
        p("  %-28s Treffer %s · ohne Treffer %s · hochgerechnet %.0f gegen %.0f · erfasst %.0f %% [grob %.0f–%.0f]" % (
            name, fmt(k_t, 45), fmt(k_k, 45), n_t, n_k, 100 * rec, 100 * rec_lo, 100 * rec_hi))
        if "RISIKO" in name:
            ok = rec >= 0.90 and q_k[2] <= 0.05
            p("  KRITERIUM (vorab): erfasst >= 90 %% und obere Grenze ohne Treffer <= 5 %% -> %s" % (
                "ERFÜLLT - Weg a bleibt" if ok else "NICHT ERFÜLLT - Weg b"))
    p("  verlorene relevante Ereignisse in der Stichprobe:")
    for r in nb[rel & (nb.schicht == "nachricht_kein")].itertuples():
        p("    %3d %-18s %s" % (r.nr, r.typ, r.titel[:90]))

    p("\nP4 — derselbe Stapel zweimal (Lauf 11 gegen 12, Temperatur 0)")
    g = L11.join(L12, rsuffix="_2", how="inner")
    p("  gleicher Typ %s · gleiche Assets %s" % (fmt((g.typ == g.typ_2).sum(), len(g)), fmt((g.assets == g.assets_2).sum(), len(g))))
    for m, r in g[g.typ != g.typ_2].iterrows():
        p("    %4s %-20s / %-20s %s" % (m, r.typ, r.typ_2, S.set_index(S.nr.astype(str)).titel[m][:70]))
    c.close()

    p("\nP3 — Gleichheit mit dem Betrieb auf ALLEN Binance-Meldungen (Mail-Arten, A1-2)")
    B = E.meldungen("binance")
    B["art"] = [BA.art(t, k) for t, k in zip(B.titel, B.katalog)]
    B["typ"] = [E.regel(t, E.B_REGELN) for t in B.titel]
    for typ, a in E.BETRIEB_ART.items():
        s1, s2 = set(B.meldung[B.art == a]), set(B.meldung[B.typ == typ])
        p("  %-18s Betrieb %3d · A1 %3d · gemeinsam %3d · nur Betrieb %d · nur A1 %d %s" % (
            typ, len(s1), len(s2), len(s1 & s2), len(s1 - s2), len(s2 - s1), [t[:60] for t in B.titel[B.meldung.isin(s2 - s1)]]))
        p("    -> %s" % ("✔ Betrieb ⊆ A1" if not (s1 - s2) else "✘ A1 verliert Betriebsmeldungen"))

    p("\nP5 — kein Vorgriff, auf der Ablage %s" % E.ABLAGE)
    X = E.lade()
    p("  Ereignisse in der Ablage: %d (%s)" % (len(X), X.groupby("methode").size().to_dict()))
    p("  bekannt_ab >= zeit bei allen: %s" % (X.bekannt_ab >= X.zeit).all())
    N = E.meldungen("nachricht").set_index("meldung")
    xn = X[X.quelle == "nachricht"]
    if len(xn):
        auf = N.aufnahme.reindex(xn.meldung)
        ok = [(pd.isna(a) or b <= E._iso(a)) for a, b in zip(auf, xn.bekannt_ab)]
        p("  Nachrichten: bekannt_ab <= Archivaufnahme bei %d von %d" % (sum(ok), len(ok)))
    tage = pd.date_range("2025-12-01", "2026-10-29", freq="D", tz="UTC")
    vorgriff = sum(int((E.am(X, t).bekannt_ab > E._iso(t)).sum()) for t in tage)
    gekuerzt = sum(not E.am(X, t).meldung.equals(E.am(X[X.bekannt_ab <= E._iso(t)], t).meldung) for t in tage)
    p("  %d Stichtage: Zeilen mit bekannt_ab > T %d · volle Ablage = auf bekannt_ab <= T gekürzte Ablage: %d Abweichungen" % (
        len(tage), vorgriff, gekuerzt))
    # Stapelkontext: Antwort im zeitlich geordneten Hauptlauf (Lauf 1) gegen den gemischten Stichproben-Stapel (Lauf 11)
    c1 = sqlite3.connect("file:%s?mode=ro" % E.ABLAGE.replace("\\", "/"), uri=True)
    L1 = pd.read_sql("SELECT quelle, meldung, typ FROM llm_antwort WHERE lauf=1 AND prompt_sha=?", c1, params=(E.PROMPT_SHA,))
    c1.close()
    L1 = L1.set_index(["quelle", "meldung"]).typ
    k = [(L11.typ.get(str(r.nr)), L1.get((r.quelle, r.meldung))) for r in S.itertuples()]
    k = [(a, b) for a, b in k if a is not None and b is not None]
    p("  Stapelkontext (Auskunft): gleicher Typ Hauptlauf gegen gemischten Stapel %s - zum Vergleich P4 (Wiederholung) oben" % (
        fmt(sum(a == b for a, b in k), len(k)) if k else "noch keine Stichproben-Meldung im Hauptlauf"))
    validierung(W, A, antworten(sqlite3.connect("file:%s?mode=ro" % LLM_DB.replace("\\", "/"), uri=True), 11, "stichprobe2"))
    open(os.path.join(HIER, "a1_nachweis.txt"), "w", encoding="utf-8").write("\n".join(AUS) + "\n")


_VOLL = {}


def _volltext(code):
    if not _VOLL:
        B = E.meldungen("binance")
        _VOLL.update(dict(zip(B.meldung, B.text.fillna(""))))
    return _VOLL.get(code, "")


if __name__ == "__main__":
    main()
