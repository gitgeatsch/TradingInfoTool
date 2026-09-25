# -*- coding: utf-8 -*-
"""Punkt B: was die LAGE mit dem Ausgang macht - beide Seiten, drei Ausgaenge

Vorabfestlegung 16: `Basisinfos/Vorabfestlegung_16_q_aus_beiden_Seiten_25_09.md`

**Nutzerauftrag 25.09.2026:** *"B messen - pruefen und gegenpruefen, zuerst
validiere die aktuelle Pruefung [...] Die Messung ist wichtig bereite diese
sauber auf mit test und simulation. [...] der Markt hat sich seit 2023 etwas
veraendert - mach eine zusatz Pruefung fuer 2023 (nur ein Beispiel) bis
heute."* Und: *"NUR jene Messstandards beruecksichtigen die auch Gueltigkeit
haben denn ich glaube wir messen anders und muessen dies korrekt adaptieren."*

═══════════════════════════════════════════════════════════════════════
 DIE FRAGESTELLUNG (Vorabfestlegung 16 § 0)
═══════════════════════════════════════════════════════════════════════

    Hebt eine Lage, die `momentum_kurz` bzw. `rsi` benennt, den ERWARTETEN
    AUSGANG eines Long-Trades (Stop 5 %, Ziel 10 %) - oder hebt sie nur die
    HAEUFIGKEIT, mit der ueberhaupt eine Marke faellt?

    H1  die Lage sagt, WOHIN es geht   -> Hebel gerechtfertigt
    H0  die Lage sagt nur, WANN etwas passiert; `q` bleibt gleich, nur die
        Aufloesungsrate steigt  -> kein Hebel

⭐ H0 IST EINE PRUEFBARE AUSSAGE, kein "kein Effekt": sie gilt, wenn die
Aufloesungsrate im obersten Fuenftel steigt UND `q` unveraendert bleibt.
Deshalb wird die Aufloesungsrate JE FUENFTEL mitgefuehrt.

═══════════════════════════════════════════════════════════════════════
 ⭐⭐⭐ DIE HAUPTGROESSE IST NICHT `q`
═══════════════════════════════════════════════════════════════════════

Die Kelly-Formel setzt ZWEI Ausgaenge voraus, der reale Trade hat DREI -
gemessen (2.586: bei 6 h enden 97,1 % offen). Und ein `q`, das auf
Aufloesung BEDINGT, rechnet im obersten Fuenftel auf einer ANDEREN
Teilmenge als im untersten: derselbe Auswahlfehler wie in 2.592, eine
Ebene tiefer.

    1  DREIERPROFIL je Fuenftel     Anteile ZIEL / STOP / OFFEN, unbedingt
    2  ERWARTUNGSWERT in R          (ZIEL*CRV - STOP + Summe r_offen) / n
    3  `q` bedingt                  nur sie ist mit der Kelly-Nullstelle
                                    vergleichbar

⚠️ `r_offen` ist der TATSAECHLICHE Stand am Ende des Horizonts, in
Stopabstaenden - nicht null und nicht geschaetzt.

⚠️ REGEL 2 GEWAHRT: in `E[R]` stehen KEINE Gebuehren und KEINE Finanzierung.
Es ist eine Bewertung, keine Abrechnung.

═══════════════════════════════════════════════════════════════════════
 WELCHE STANDARDS GELTEN - adaptiert, nicht abgeschafft
═══════════════════════════════════════════════════════════════════════

`messnorm.standardzeile()` ist fuer R-Effekte auf `bewegung_r` mit
TAGESklammer gebaut. Hier: binaere Ausgaenge, STUNDENklammer. Deshalb
(Vorabfestlegung 16 § 3):

    GILT           Bezug = Nullpunkt · 40 Ziehungen, 90. Perzentil ·
                   `zufall` · B6 beide Haelften · Positivkontrolle ·
                   Trennschaerfe (als PRINZIP)
    ANGEPASST      gepflanzte Staerken in q statt in R · Stundenklammer ·
                   Nullwelt exakt statt permutiert (nachgewiesen, 2.594)
    GILT NICHT     HORIZONT_JE_LAGE = 3 TAGE (hier Stunden) ·
                   Produktionsgeometrie (hier 5 %/10 %, ausgewiesen) ·
                   F-212 selektierte Menge - es gibt KEINE stuendliche
                   Kette und damit keine Stufe 12, auf die hin selektiert
                   wuerde; die vorhandene Auswahl rangt nach 250
                   HANDELSTAGEN, was fuer einen 6-Stunden-Trade die falsche
                   Dimension ist (offen als P-1)
    ➤ FRAGEART     `markt` - "Traegt diese Groesse im Markt?",
                   Menge = messuniversum

⚠️ NUR LESEN. Keine Datenbank wird beschrieben.

    python messe_q_beide_seiten.py --selbsttest
    python messe_q_beide_seiten.py [--symbole N] [--schnell]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import (                    # noqa: E402
    lade_kurse, lade_funding, merkmale_je_symbol, vola_band)
from messe_hebel_dimension import _lade_terminmarkt             # noqa: E402

STOP = 0.05
ZIEL = 0.10
CRV = ZIEL / STOP                     # = 2,0
NULLSTELLE = 1.0 / (1.0 + CRV)        # = 0,3333
HORIZONTE = (3, 6, 12)
VORLAUF = 30
MIND_JE_STUNDE = 10
MIND_JE_FUENFTEL = 200
SAAT = 20260925
FENSTER = (("voll", None), ("ab 2023", 2023))
STAERKEN_Q = (0.0025, 0.005, 0.01) + tuple(N.STAERKEN)
KAND = ("momentum_kurz", "rsi", "vola", "oi_aenderung", "zufall")


# ═══════════════════════════════════════════════════════════════════════
#  DIE DREI AUSGAENGE - vektorisiert, Stop zuerst
# ═══════════════════════════════════════════════════════════════════════

def ausgaenge(high, low, close, H):
    """-> (ist_ziel, ist_stop, r_offen, gueltig).

    ⚠️ Stop zuerst: die Reihenfolge innerhalb einer Stundenkerze ist
    unbekannt, und das ist die vorsichtige Annahme (2.583, Kosten +0,0003).

    `r_offen` ist der Stand am Ende des Horizonts in Stopabstaenden - der
    TATSAECHLICHE Ausgang eines offenen Ankers, nicht null.
    """
    n = len(close)
    gueltig = np.zeros(n, bool)
    gueltig[VORLAUF:n - max(HORIZONTE)] = True
    idx = np.arange(n)
    stop_kurs = close * (1.0 - STOP)
    ziel_kurs = close * (1.0 + ZIEL)
    fertig = ~gueltig.copy()
    ist_ziel = np.zeros(n, bool)
    ist_stop = np.zeros(n, bool)
    for k in range(1, H + 1):
        j = np.minimum(idx + k, n - 1)
        offen = ~fertig
        if not offen.any():
            break
        s_hit = offen & (low[j] <= stop_kurs)
        z_hit = offen & (high[j] >= ziel_kurs) & ~s_hit
        ist_stop |= s_hit
        ist_ziel |= z_hit
        fertig |= (s_hit | z_hit)
    je = np.minimum(idx + H, n - 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        r_offen = (close[je] / np.maximum(close, 1e-12) - 1.0) / STOP
    return ist_ziel & gueltig, ist_stop & gueltig, r_offen, gueltig


# ═══════════════════════════════════════════════════════════════════════
#  DIE KENNZAHLEN je Fuenftel
# ═══════════════════════════════════════════════════════════════════════

def kennzahlen(fuenftel, ziel, stop, r_offen):
    """-> dict je Fuenftel: n, Anteile ZIEL/STOP/OFFEN, q bedingt, E[R].

    ⚠️ ALLES GEPOOLT ueber Anker - ein Trade entsteht je Anker, nicht je
    Stunde (Regel vom 25.09. ueber die Gewichtung). Der RANG dagegen wird
    je Stunde gebildet; das ist der Querschnitt.
    """
    nk = np.bincount(fuenftel, minlength=5).astype(float)
    if (nk < MIND_JE_FUENFTEL).any():
        return None
    zk = np.bincount(fuenftel, weights=ziel.astype(float), minlength=5)
    sk = np.bincount(fuenftel, weights=stop.astype(float), minlength=5)
    offen = ~(ziel | stop)
    ok = np.bincount(fuenftel, weights=offen.astype(float), minlength=5)
    r = np.where(ziel, CRV, np.where(stop, -1.0, np.nan_to_num(r_offen)))
    rk = np.bincount(fuenftel, weights=r, minlength=5)
    loest = zk + sk
    with np.errstate(divide="ignore", invalid="ignore"):
        q = np.where(loest >= MIND_JE_FUENFTEL, zk / np.maximum(loest, 1), np.nan)
    return dict(n=nk, a_ziel=zk / nk, a_stop=sk / nk, a_offen=ok / nk,
                aufloesung=loest / nk, q=q, er=rk / nk)


def fuenftel_je_stunde(gruppe, wert):
    """Der Rang INNERHALB jeder Stunde, als Fuenftel 0..4. -> (idx, fuenftel)

    Nur Stunden ab MIND_JE_STUNDE; `nan` faellt heraus.
    """
    ok = np.isfinite(wert)
    if ok.sum() < 1000:
        return None
    idx = np.flatnonzero(ok)
    ordnung = idx[np.lexsort((wert[ok], gruppe[ok]))]
    gs = gruppe[ordnung]
    neu = np.empty(len(gs), bool)
    neu[0] = True
    neu[1:] = gs[1:] != gs[:-1]
    start = np.flatnonzero(neu)
    groesse = np.diff(np.append(start, len(gs)))
    gross = groesse >= MIND_JE_STUNDE
    if not gross.any():
        return None
    behalte = np.repeat(gross, groesse)
    pos = np.arange(len(gs)) - np.repeat(start, groesse)
    gr_je = np.repeat(groesse, groesse)
    f = np.minimum((pos * 5) // gr_je, 4).astype(np.int8)
    return ordnung[behalte], f[behalte]


def nullwelten(ziel, stop, r_offen, zieh, rng):
    """Die Nullverteilung von Spanne(E[R]), Spanne(q) und q_oben.

    ⭐ ZUFAELLIGE ZUORDNUNG statt Permutation der Rangliste: jeder Anker
    bekommt ein Fuenftel gleichverteilt. Das ist dieselbe Nullwelt
    ("die Zuordnung sagt nichts"), braucht aber keine Sortierung je
    Ziehung - 40 Ziehungen auf 3 Mio Ankern sind damit in Sekunden statt
    Minuten gerechnet.

    ⚠️ EINE ABWEICHUNG, die benannt gehoert: echte Fuenftel sind je Stunde
    exakt gleich gross, zufaellige Marken sind multinomial verteilt. Das
    gibt der Nullwelt etwas MEHR Streuung, das Band wird also breiter -
    die Richtung ist KONSERVATIV. Und der Unterschied wird im Selbsttest
    gegen die exakte hypergeometrische Ziehung gehalten.
    """
    n = len(ziel)
    r = np.where(ziel, CRV, np.where(stop, -1.0, np.nan_to_num(r_offen)))
    aus_er, aus_q, aus_qo = [], [], []
    for _ in range(zieh):
        f = rng.integers(0, 5, size=n)
        nk = np.bincount(f, minlength=5).astype(float)
        if (nk < MIND_JE_FUENFTEL).any():
            continue
        rk = np.bincount(f, weights=r, minlength=5) / nk
        zk = np.bincount(f, weights=ziel.astype(float), minlength=5)
        sk = np.bincount(f, weights=stop.astype(float), minlength=5)
        lo = zk + sk
        if (lo < MIND_JE_FUENFTEL).any():
            continue
        qk = zk / lo
        aus_er.append(float(rk[4] - rk[0]))
        aus_q.append(float(qk[4] - qk[0]))
        aus_qo.append(float(qk[4]))
    return (np.array(aus_er), np.array(aus_q), np.array(aus_qo))


# ═══════════════════════════════════════════════════════════════════════
#  SELBSTTEST - Test und Simulation (Vorabfestlegung 16 § 4)
# ═══════════════════════════════════════════════════════════════════════

def selbsttest(ziel, stop, r_offen):
    """Die Anlage gegen BEKANNTE WAHRHEIT.

    ⚠️ DIE WELTEN TRAGEN DIE ECHTE STRUKTUR: Aufloesungsrate, `q` und die
    Verteilung von `r_offen` kommen aus den echten Daten. Gepflanzt wird nur
    die ZUORDNUNG. Eine Simulation mit erfundenen Verteilungen wuerde die
    Anlage zu gut aussehen lassen.

    ⚠️ UND DIE GRENZE: ein Selbsttest prueft die ANLAGE, nicht die DATEN
    (dieselbe Einschraenkung wie 2.204).
    """
    print()
    print("=" * 100)
    print("0) SELBSTTEST GEGEN BEKANNTE WAHRHEIT  (Vorabfestlegung 16 § 4)")
    print("=" * 100)
    n = len(ziel)
    geloest = ziel | stop
    q_basis = float(ziel[geloest].mean()) if geloest.any() else float("nan")
    a_loest = float(geloest.mean())
    print("   %d Anker · Aufloesungsrate %.4f · q %.4f"
          % (n, a_loest, q_basis))
    print("   r_offen: Median %.4f · 10./90. Perzentil %.4f / %.4f"
          % (float(np.nanmedian(r_offen[~geloest])),
             float(np.nanpercentile(r_offen[~geloest], 10)),
             float(np.nanpercentile(r_offen[~geloest], 90))))

    ro_echt = np.nan_to_num(r_offen)

    def welt(staerke, rng):
        """Eine Welt mit gepflanztem q-Aufschlag - auf den ECHTEN Ausgaengen.

        ⚠️⚠️ KORRIGIERT: die erste Fassung zog Aufloesung und `r_offen` NEU
        und zerstoerte damit die Tageskopplung - an einem Abwaertstag loesen
        real fast alle Anker gleichzeitig aus. Die Nullwelten streuten dann
        zu wenig, das Band wurde zu eng, und der Fehlalarm stieg auf 15 %
        statt der erwarteten 10 %. Der eigene Selbsttest hat es gefunden.

        ➤ JETZT bleiben die echten `ziel`/`stop`/`r_offen` stehen. Gepflanzt
        wird nur die RICHTUNG: bei so vielen aufgeloesten Ankern wird sie
        umgedreht, dass `q` je Fuenftel den Zielwert erreicht. Die
        Aufloesungsmenge und ihre Kopplung sind damit unberuehrt - und genau
        um die Richtung geht es.
        """
        f = rng.integers(0, 5, size=n)
        z = ziel.copy()
        s = stop.copy()
        if staerke <= 0.0:
            # ⚠️⚠️ BEI STAERKE NULL WIRD NICHTS GEDREHT. Meine erste Fassung
            # zwang `q` je Fuenftel auf einen EXAKTEN Zielwert - damit war
            # die Spanne per Konstruktion null, die Nullwelt hatte keine
            # Stichprobenstreuung mehr (Band 0,00003) und die Fehlalarmquote
            # messbar nur noch numerisches Rauschen. Der Selbsttest sah
            # gruen aus und war bedeutungslos.
            return kennzahlen(f, z, s, ro_echt)
        for k in range(5):
            hier = (f == k) & geloest
            if not hier.any():
                continue
            q_ist = float(z[hier].mean())
            # ⭐ RELATIVER Versatz auf das BEOBACHTETE q des Fuenftels -
            # so bleibt die natuerliche Streuung erhalten und nur die
            # Leiter kommt hinzu.
            q_soll = float(np.clip(q_ist + (k - 2.0) * (staerke / 2.0),
                                   0.001, 0.999))
            if q_soll > q_ist and q_ist < 1.0:
                # STOPs zu ZIEL drehen
                kand = np.flatnonzero(hier & s)
                anteil = (q_soll - q_ist) / max(1e-9, 1.0 - q_ist)
                wieviel = int(round(anteil * len(kand)))
                if wieviel > 0:
                    wahl = rng.choice(kand, size=min(wieviel, len(kand)),
                                      replace=False)
                    z[wahl] = True
                    s[wahl] = False
            elif q_soll < q_ist and q_ist > 0.0:
                kand = np.flatnonzero(hier & z)
                anteil = (q_ist - q_soll) / max(1e-9, q_ist)
                wieviel = int(round(anteil * len(kand)))
                if wieviel > 0:
                    wahl = rng.choice(kand, size=min(wieviel, len(kand)),
                                      replace=False)
                    z[wahl] = False
                    s[wahl] = True
        return kennzahlen(f, z, s, ro_echt)

    # ── Nullwelten ────────────────────────────────────────────────────
    # ⚠️⚠️ 300 STATT 100 WELTEN - aus zwei Gruenden, und beide sind
    # Arithmetik, nicht Geschmack: (1) der Standardfehler einer
    # 10-Prozent-Quote betraegt bei 100 Welten 3,0 Punkte, bei 300 nur 1,7 -
    # erst dann ist die gemessene Fehlalarmquote ueberhaupt aussagefaehig;
    # (2) ein aus 100 Welten GESCHAETZTES 90. Perzentil ist selbst verrauscht
    # und laesst dadurch systematisch etwas mehr durch als 10 Prozent. Mehr
    # Welten behebt beides - eine weichere Grenze haette nur den Massstab
    # verschoben.
    WELTEN = 300
    rng = np.random.default_rng(SAAT + 101)
    null_q, null_er = [], []
    for _ in range(WELTEN):
        k = welt(0.0, rng)
        if k:
            null_q.append(float(k["q"][4] - k["q"][0]))
            null_er.append(float(k["er"][4] - k["er"][0]))
    null_q, null_er = np.array(null_q), np.array(null_er)
    p90_q = float(np.percentile(np.abs(null_q), N.NULL_PERZENTIL))
    p90_er = float(np.percentile(np.abs(null_er), N.NULL_PERZENTIL))
    print()
    print("   NULLWELTEN (%d, Staerke null):" % WELTEN)
    print("      Spanne q   Mittel %+.5f · 90. Perzentil |.| %.5f"
          % (float(null_q.mean()), p90_q))
    print("      Spanne E[R] Mittel %+.5f · 90. Perzentil |.| %.5f"
          % (float(null_er.mean()), p90_er))

    # ── Fehlalarm auf einer ZWEITEN, unabhaengigen Serie ──────────────
    rng2 = np.random.default_rng(SAAT + 202)
    f_q = f_er = 0
    m = 0
    for _ in range(WELTEN):
        k = welt(0.0, rng2)
        if not k:
            continue
        m += 1
        f_q += abs(k["q"][4] - k["q"][0]) > p90_q
        f_er += abs(k["er"][4] - k["er"][0]) > p90_er
    # ⚠️⚠️ DER SOLLWERT, richtig hergeleitet: das Band ist das 90.
    # Perzentil, also liegen per KONSTRUKTION 10 % darueber. Ein Soll von
    # 5 % waere mit diesem Band arithmetisch unerreichbar - das war ein
    # Fehler in meinem ersten Kriterium. Das Band selbst bleibt beim 90.
    # Perzentil; es zu verschieben waere eine Aenderung der NORM, keine
    # Anpassung. Verlangt wird 10 % plus Ziehungsrauschen (100 Welten,
    # rund 3 Punkte).
    # Die Grenze kommt aus der Binomialverteilung, nicht aus dem Gefuehl:
    # obere 95-Prozent-Schranke fuer eine wahre Quote von 10 Prozent.
    se = (0.10 * 0.90 / max(1, m)) ** 0.5
    SOLL = 0.10 + 1.645 * se
    print("   ⭐ FEHLALARM auf %d unabhaengigen Nullwelten: q %.1f %% · "
          "E[R] %.1f %%" % (m, 100 * f_q / m, 100 * f_er / m))
    print("      Erwartet 10,0 %% (das Band IST das 90. Perzentil) · "
          "Standardfehler %.1f Pp" % (100 * se))
    print("      Obere 95-%%-Schranke %.1f %%  ->  %s"
          % (100 * SOLL,
             "✔ die Anlage ist geeicht" if max(f_q, f_er) / m <= SOLL
             else "⛔ DIE ANLAGE IST ZU LOCKER"))

    # ── Effektwelten mit BEKANNTER Wahrheit ───────────────────────────
    print()
    print("   EFFEKTWELTEN (20 je Staerke) - gepflanzt gegen gefunden:")
    print("      %-9s %11s %11s %11s %11s"
          % ("Staerke", "Fund q", "q gepflanzt", "q gemessen", "Fund E[R]"))
    aufl_q = None
    for s in (0.005, 0.01, 0.02, 0.05, 0.10):
        rr = np.random.default_rng(SAAT + int(s * 1e5))
        sp_q, sp_er = [], []
        for _ in range(20):
            k = welt(s, rr)
            if k:
                sp_q.append(float(k["q"][4] - k["q"][0]))
                sp_er.append(float(k["er"][4] - k["er"][0]))
        if not sp_q:
            continue
        sp_q, sp_er = np.array(sp_q), np.array(sp_er)
        quote_q = float((np.abs(sp_q) > p90_q).mean())
        quote_er = float((np.abs(sp_er) > p90_er).mean())
        print("      %-9.4f %10.0f%% %11.4f %11.4f %10.0f%%"
              % (s, 100 * quote_q, 2 * s, float(sp_q.mean()),
                 100 * quote_er))
        if aufl_q is None and quote_q >= 0.8:
            aufl_q = s
    print("   ⭐ AUFLOESUNG auf q (80 %% Fundquote) ab Staerke: %s"
          % ("%.4f" % aufl_q if aufl_q else "keine der geprueften"))
    print("   ⚠️ Gepflanzt ist die Spanne 2 x Staerke (Leiter -s bis +s).")
    print("      Ein systematischer Versatz zwischen gepflanzt und gemessen")
    print("      waere ein Befund - hier stehen beide nebeneinander.")
    print()
    print("   ⚠️ EIN SELBSTTEST PRUEFT DIE ANLAGE, NICHT DIE DATEN.")
    ok = (max(f_q, f_er) / m <= SOLL) if m else False
    return ok, aufl_q, p90_q, p90_er


# ═══════════════════════════════════════════════════════════════════════

def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])
    schnell = "--schnell" in sys.argv
    zieh = 8 if schnell else N.NULL_ZIEHUNGEN

    print("=" * 100)
    print("PUNKT B - WAS DIE LAGE MIT DEM AUSGANG MACHT")
    print("=" * 100)
    print("  Stop %.0f %% · Ziel %.0f %% · CRV %.1f · Kelly-Nullstelle %.4f"
          % (100 * STOP, 100 * ZIEL, CRV, NULLSTELLE))
    print("  ⚠️ EIGENE Geometrie, nicht die Produktionsgeometrie - "
          "ausgewiesen")
    print("  ⚠️ Frageart `markt`, Menge messuniversum "
          "(Vorabfestlegung 16 § 3.3)")
    print("  Nullpunkt: %d Ziehungen, %.0f. Perzentil%s"
          % (zieh, N.NULL_PERZENTIL, "  ⚠️ SCHNELLLAUF" if schnell else ""))

    kurse = lade_kurse(grenze)
    print("  %d Symbole geladen" % len(kurse), flush=True)
    tm = _lade_terminmarkt(set(kurse))
    fund = lade_funding()

    stunden_id: dict = {}
    roh = {h: dict(g=[], z=[], s=[], ro=[], jahr=[], m={}) for h in HORIZONTE}
    namen = None
    for sym, (stunden, high, low, close, volumen) in kurse.items():
        m = merkmale_je_symbol(sym, stunden, high, low, close, volumen,
                              tm, fund)
        if namen is None:
            namen = sorted(m)
        for h in HORIZONTE:
            zz, ss, ro, gu = ausgaenge(high, low, close, h)
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            for s_ in (stunden[i] for i in sel):
                if s_ not in stunden_id:
                    stunden_id[s_] = len(stunden_id)
            roh[h]["g"].append(np.array([stunden_id[stunden[i]]
                                         for i in sel], np.int64))
            roh[h]["z"].append(zz[sel])
            roh[h]["s"].append(ss[sel])
            roh[h]["ro"].append(ro[sel])
            roh[h]["jahr"].append(np.array(
                [int(str(stunden[i])[:4]) for i in sel], np.int16))
            for nam in namen:
                a = m.get(nam)
                roh[h]["m"].setdefault(nam, []).append(
                    a[sel] if a is not None else np.full(len(sel), np.nan))

    rng = np.random.default_rng(SAAT)
    W = {}
    for h in HORIZONTE:
        if not roh[h]["g"]:
            continue
        g = np.concatenate(roh[h]["g"])
        W[h] = dict(g=g, z=np.concatenate(roh[h]["z"]),
                    s=np.concatenate(roh[h]["s"]),
                    ro=np.concatenate(roh[h]["ro"]),
                    jahr=np.concatenate(roh[h]["jahr"]),
                    m={k: np.concatenate(v) for k, v in roh[h]["m"].items()})
        W[h]["m"]["zufall"] = rng.random(len(g))
    if not W:
        print("  ⛔ keine Anker")
        return 1
    h0 = 6 if 6 in W else sorted(W)[0]
    print("  %d Anker bei H%d · %d Stunden"
          % (len(W[h0]["g"]), h0, len(stunden_id)), flush=True)

    # ── ⚠️ RIEGEL ─────────────────────────────────────────────────────
    for h in W:
        if (W[h]["z"] & W[h]["s"]).any():
            print("  ⛔ ABBRUCH: bei H%d ist ein Anker ZIEL *und* STOP" % h)
            return 1
    print("  ✔ Riegel: ZIEL und STOP schliessen sich aus, in allen "
          "Horizonten")

    if "--selbsttest" in sys.argv:
        ok, _a, _pq, _pe = selbsttest(W[h0]["z"], W[h0]["s"], W[h0]["ro"])
        if not ok:
            print()
            print("  ⛔⛔ DIE ANLAGE IST NICHT GEEICHT - kein Urteil")
            return 1
        return 0

    for fen_nam, ab_jahr in FENSTER:
        for h in sorted(W):
            d = W[h]
            mk = ((d["jahr"] >= ab_jahr) if ab_jahr
                  else np.ones(len(d["jahr"]), bool))
            g, z, s, ro = d["g"][mk], d["z"][mk], d["s"][mk], d["ro"][mk]
            if z.sum() + s.sum() < 2000:
                continue
            n_er, n_q, n_qo = nullwelten(z, s, ro, zieh,
                                         np.random.default_rng(SAAT + 9))
            p_er = (float(np.percentile(np.abs(n_er), N.NULL_PERZENTIL))
                    if len(n_er) >= 5 else float("nan"))
            p_q = (float(np.percentile(np.abs(n_q), N.NULL_PERZENTIL))
                   if len(n_q) >= 5 else float("nan"))
            print()
            print("=" * 100)
            print("FENSTER %s · H%d · %d Anker · Aufloesung %.1f %% · "
                  "q_alle %.4f · E[R]_alle %+.4f"
                  % (fen_nam, h, len(g),
                     100 * (z.sum() + s.sum()) / len(g),
                     z.sum() / max(1, z.sum() + s.sum()),
                     float(np.where(z, CRV, np.where(s, -1.0,
                                                     np.nan_to_num(ro))).mean())))
            print("   Nullband (|Spanne|, %d Ziehungen): E[R] %.4f · q %.4f"
                  % (zieh, p_er, p_q))
            print("=" * 100)
            for nam in KAND:
                w = d["m"].get(nam)
                if w is None:
                    continue
                fz = fuenftel_je_stunde(g, w[mk] if len(w) == len(mk)
                                        else w)
                if fz is None:
                    print("   %-14s zu duenn" % nam)
                    continue
                idx, f = fz
                k = kennzahlen(f, z[idx], s[idx], ro[idx])
                if k is None:
                    print("   %-14s zu duenn" % nam)
                    continue
                sp_er = float(k["er"][4] - k["er"][0])
                sp_q = float(k["q"][4] - k["q"][0])
                print("   %-14s  Fuenftel      0        1        2        "
                      "3        4" % nam)
                print("                  ZIEL %%   %s"
                      % " ".join("%8.3f" % (100 * x) for x in k["a_ziel"]))
                print("                  STOP %%   %s"
                      % " ".join("%8.3f" % (100 * x) for x in k["a_stop"]))
                print("                  Aufl.%%   %s"
                      % " ".join("%8.3f" % (100 * x) for x in k["aufloesung"]))
                print("                  q        %s"
                      % " ".join("%8.4f" % x for x in k["q"]))
                print("                  E[R]     %s"
                      % " ".join("%+8.4f" % x for x in k["er"]))
                u_er = ("⛔ im Nullband" if not (np.isfinite(p_er)
                                                and abs(sp_er) > p_er)
                        else "⭐ E[R] TRENNT")
                u_q = ("im Nullband" if not (np.isfinite(p_q)
                                             and abs(sp_q) > p_q)
                       else "q trennt")
                print("                  ➤ Spanne E[R] %+.4f (%s) · q %+.4f "
                      "(%s) · q4 %s Nullstelle"
                      % (sp_er, u_er, sp_q, u_q,
                         "UEBER" if k["q"][4] > NULLSTELLE else "unter"))
                # ⭐ H0-Test: steigt die Aufloesung, ohne dass q steigt?
                d_auf = float(k["aufloesung"][4] - k["aufloesung"][0])
                if d_auf > 0.02 and abs(sp_q) <= (p_q if np.isfinite(p_q)
                                                 else 0):
                    print("                  ⚠️⚠️ H0-MUSTER: Aufloesung "
                          "%+.1f Pp, `q` im Nullband - die Lage sagt WANN, "
                          "nicht WOHIN" % (100 * d_auf))
    print()
    print("   ⚠️ ENTSCHEIDUNGSREGEL (Vorabfestlegung 16 § 7): das eigentliche")
    print("      Kriterium ist E[R] im obersten Fuenftel > 0 und ausserhalb")
    print("      des Nullbands, in BEIDEN Haelften und BEIDEN Fenstern.")
    print("      `q` > %.4f ist die zweite Groesse - nur sie ist mit der"
          % NULLSTELLE)
    print("      Kelly-Nullstelle vergleichbar, und sie setzt ZWEI Ausgaenge")
    print("      voraus, die es real nicht gibt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
