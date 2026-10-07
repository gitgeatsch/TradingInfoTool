"""ENTWURF Mailabschnitt 'Altcoins - Fortbestand und Gelegenheit' mit beiden Ebenen (Voranalyse_Spot §26) - aus echten Daten, nur Anschauung.

    python Basisinfos/Spot_Voranalyse_04_10/mail_entwurf.py   -> Basisinfos/Spot_Voranalyse_04_10/mail_entwurf_beide_ebenen.md

Nur lesend (mode=ro). Bestand aus der DESKTOP-KOPIE von holdings (Stand 19.07.2026; im Betrieb der NB-Stand). Kein Kaufsignal.
Ebene 2 (Gelegenheit, gemessen §25.6): Watchlist-Rang auf Marktwert-Klassen. Ebene 1 (Fortbestand): Fakten in Worten, mit der
Einordnung aus §25.6, was in der Vergangenheit guenstig, neutral oder unguenstig war. Gesperrte Symbole (symbol_zuordnung.csv 'gesperrt'
und Markpreis-Sperre AUDIO/MBL/ONE) erscheinen nicht in der Rangliste.
"""
import csv
import json
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import mk_messung as MK  # noqa: E402

M, W, A = MK.M, MK.W, MK.A
K, POS, ENDE = MK.K, MK.POS, MK.ENDE
PROFIL = MK.PROFIL
ZIEL = os.path.join(HIER, "mail_entwurf_beide_ebenen.md")
GESPERRT = {r["binance"] for r in csv.DictReader(open("Basisinfos/symbol_zuordnung.csv", encoding="utf-8"), delimiter=";") if r["markt"] == "gesperrt"} | {"AUDIO", "MBL", "ONE"}
KERN = {"BTC", "ETH", "SOL"}
NAMEN_KL = {"H": "Highcap", "M": "Midcap", "S": "Smallcap"}


def monat(t):
    out, _, _ = MK.klassen_mw(t)
    D = pd.DataFrame([dict(t=t, sym=s, kl=k) for s, k in out.items() if not np.isnan(K[s].values[POS[t]])])
    F = M.merkmale(D)
    Zl = W.Leicht(D)
    w = W.wert(Zl, F)
    p = M.pct_in_zelle(Zl, w)
    teil = {k: (M.pct_in_zelle(Zl, F[k]) if s == "oben" else 1 - M.pct_in_zelle(Zl, F[k])) for k, s in W.WAHL}
    return D.assign(wert=w, p=p, **{"r_" + k: v for k, v in teil.items()}, **{k: F[k] for k in ("F1", "F2", "F8", "F9")})


def gebuehren(s, t):
    out = {}
    for tab in ("gebuehr", "halter"):
        c = sqlite3.connect("file:data/_spot/gebuehren.db?mode=ro", uri=True)
        a, b = (t - pd.Timedelta(days=365)).date().isoformat(), (t - pd.Timedelta(days=1)).date().isoformat()
        v = c.execute("SELECT SUM(usd), MIN(datum) FROM %s WHERE symbol=? AND datum BETWEEN ? AND ?" % tab, (s, a, b)).fetchone()
        v0 = c.execute("SELECT SUM(usd) FROM %s WHERE symbol=? AND datum BETWEEN ? AND ?" % tab,
                       (s, (t - pd.Timedelta(days=730)).date().isoformat(), (t - pd.Timedelta(days=366)).date().isoformat())).fetchone()
        out[tab] = (v[0], v0[0])
    return out


def profil_saetze(s, t, r):
    """Ebene 1 in ganzen Saetzen, je Fakt mit der Einordnung aus §25.6."""
    z = []
    if (s not in PROFIL.index or PROFIL.at[s, "mw"] != PROFIL.at[s, "mw"]) and r is not None:
        z.append("⚠️ **Kein Strukturprofil:** Bei CoinGecko ist der Coin nicht unter den 1.500 größten oder ohne Angaben. Das ist für sich ein Warnzeichen (z. B. eingestellte Projekte wie FTT).")
    elif s not in PROFIL.index:
        z.append("*Strukturprofil: Zuordnung zu CoinGecko offen (Kürzel nicht eindeutig gefunden; im Betrieb über die Zuordnungstabelle).*")
    if s in PROFIL.index:
        p = PROFIL.loc[s]
        if p.fest == 1 and p.ausgegeben == p.ausgegeben:
            z.append("Die Gesamtmenge ist fest; %.0f %% sind ausgegeben%s *(Angebot: in der Vergangenheit neutral)*." % (
                100 * min(p.ausgegeben, 1), ", es kommen kaum neue Tokens auf den Markt" if p.ausgegeben >= 0.9 else
                ", der Rest kommt noch auf den Markt und kann verwässern"))
        elif p.ausgegeben == p.ausgegeben:
            z.append("Es gibt keine feste Höchstmenge; neue Tokens können laufend dazukommen *(Angebot: in der Vergangenheit neutral)*.")
        if p.fdv_mw == p.fdv_mw and p.fdv_mw > 1.5:
            z.append("Der Wert aller künftigen Tokens liegt beim %s-Fachen des heutigen Marktwerts; es steht also noch viel Verwässerung aus *(seit 2024 ungünstig)*." % de(p.fdv_mw))
        kat = json.loads(p.kategorien) if isinstance(p.kategorien, str) else []
        merk = []
        for stich, wort, einordnung in (("Real World Assets", "Tokenisierung realer Werte (RWA)", "günstig, aber wenige Fälle und Rückschau-Vorbehalt"),
                                        ("Meme", "Meme-Coin ohne eigenen Nutzen", "seit 2024 ungünstig"),
                                        ("Gaming", "Gaming", "seit 2024 ungünstig"),
                                        ("Artificial Intelligence", "KI", "seit 2024 ungünstig, davor günstig: wechselt mit der Mode"),
                                        ("Layer 1", "eigene Blockchain (Layer 1)", "seit 2024 neutral"),
                                        ("Decentralized Finance", "DeFi", "seit 2024 günstig, davor ungünstig: wechselhaft"),
                                        ("Infrastructure", "Infrastruktur", "wechselhaft")):
            if any(stich in k for k in kat):
                merk.append("%s *(%s)*" % (wort, einordnung))
        if any("Coinbase 50" in k for k in kat):
            merk.append("im Coinbase-50-Index *(spricht für Größe und Bekanntheit; als Vorhersage wegen Rückschau nicht belegt)*")
        if merk:
            z.append("Einordnung: " + "; ".join(merk) + ".")
    g = gebuehren(s, t)
    geb, geb0 = g["gebuehr"]
    hal, _ = g["halter"]
    if geb is not None and geb > 0:
        trend = "" if not geb0 else (" (Vorjahr %s, also %s)" % (geld(geb0), "steigend" if geb > geb0 else "fallend"))
        satz = "Nutzer zahlten in den letzten 12 Monaten %s Gebühren%s" % (geld(geb), trend)
        if hal is not None and hal > 0:
            satz += "; davon kamen %s beim Token-Halter an (Rückkauf, Verbrennen oder Ausschüttung)" % geld(hal)
        else:
            satz += "; beim Token-Halter kommt davon nichts Messbares an, der Token ist eher Stimmrecht als Anteil"
        z.append(satz + " *(Gebühren: in der Vergangenheit eher ungünstig, wenige Fälle)*.")
    else:
        z.append("Bei DefiLlama sind für diesen Coin keine Gebühren erfasst, oder das Kürzel ist mehrdeutig und noch nicht zugeordnet (z. B. UNI, LINK); der Nutzen ist auf diesem Weg nicht messbar.")
    return " ".join(z)


def de(x, nk=1):
    return ("%%.%df" % nk % x).replace(".", ",")


def zahl(x):
    """Kurse lesbar: 4 gueltige Stellen, deutsches Komma, keine e-Schreibweise."""
    if x >= 1:
        return de(x, 2 if x < 100 else 1)
    stellen = max(2, -int(np.floor(np.log10(x))) + 3)
    return ("%%.%df" % stellen % x).replace(".", ",")


def geld(x):
    if x >= 1e9:
        return "%s Mrd. $" % de(x / 1e9)
    if x >= 1e6:
        return "%s Mio. $" % de(x / 1e6, 0)
    if x >= 1e4:
        return "%s Mio. $" % de(x / 1e6, 2)
    return "weniger als 0,01 Mio. $"


def gelegenheit_satz(r):
    teile = sorted([(r.r_F8, "seit %s Jahren an Binance gehandelt" % de(r.F8 / 365)), (r.r_F1, "%.0f %% unter dem Allzeithoch" % (-100 * r.F1)),
                    (r.r_F2, "das Hoch liegt %.0f Monate zurück" % (r.F2 / 30.4))] +
                   ([(r.r_F9, "die Nutzung (TVL) wuchs schneller als der Kurs")] if r.F9 == r.F9 else []), key=lambda x: -x[0])
    return ", ".join(t for _, t in teile[:3])


def marke(s, t):
    v = K[s].values[POS[t] + 1:]
    v = v[~np.isnan(v)]
    if not len(v):
        return None
    hoch = v.max(); m = max(0.65 * hoch, 0.5 * v[0]); jetzt = v[-1]
    zustand = "unterschritten" if jetzt < m else ("nahe (weniger als 10 % Abstand)" if jetzt < 1.1 * m else "ok")
    return v[0], jetzt, m, zustand


def stufe(r):
    return "★★★" if r.p > 0.9 else ("★★" if r.p > 0.8 else "")


def profil_nachladen(symbole):
    """Fuer Bestand-Coins ausserhalb des Universums: Profil direkt bei CoinGecko (Suche nach dem Kuerzel, groesster Marktwert)."""
    import time
    import requests
    global PROFIL
    neu = []
    for s in symbole:
        try:
            such = requests.get("https://api.coingecko.com/api/v3/search?query=%s" % s, timeout=30).json().get("coins", [])
            kand = [c for c in such if c.get("symbol", "").upper() == s and c.get("market_cap_rank")]
            if not kand:
                continue
            i = sorted(kand, key=lambda c: c["market_cap_rank"])[0]["id"]
            time.sleep(2.5)
            m = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=%s" % i, timeout=30).json()[0]
            time.sleep(2.5)
            d = requests.get("https://api.coingecko.com/api/v3/coins/%s?localization=false&tickers=false&market_data=false&community_data=false&developer_data=false" % i,
                             timeout=30).json()
            time.sleep(2.5)
            fest = bool(m.get("max_supply"))
            aus = (m["circulating_supply"] / m["max_supply"]) if fest else (m["circulating_supply"] / m["total_supply"] if m.get("total_supply") else np.nan)
            neu.append(dict(symbol=s, cg_id=i, mw=m.get("market_cap"), fest=int(fest), ausgegeben=aus,
                            fdv_mw=(m["fully_diluted_valuation"] / m["market_cap"]) if m.get("fully_diluted_valuation") and m.get("market_cap") else np.nan,
                            kategorien=json.dumps(d.get("categories") or [], ensure_ascii=False)))
        except Exception:                                                     # noqa: BLE001
            continue
    if neu:
        PROFIL = pd.concat([PROFIL, pd.DataFrame(neu).set_index("symbol")])
    return [x["symbol"] for x in neu]


def main():
    t = ENDE.replace(day=1)
    H = {m: monat(m) for m in [t - pd.DateOffset(months=k) for k in range(3, -1, -1)]}
    D = H[t]
    vor = H[t - pd.DateOffset(months=1)]
    c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
    bestand = sorted(s for s, in c.execute("SELECT symbol FROM holdings WHERE quantity > 0"))
    krypto_bestand = [s for s in bestand if s in K.columns or s in PROFIL.index or s in ("CANTON",)]
    nachgeladen = profil_nachladen([s for s in krypto_bestand if s not in PROFIL.index and s not in KERN])
    L = []
    for kl in ("H", "M", "S"):
        x = D[(D.kl == kl) & (D.p > 0.8) & ~D.sym.isin(GESPERRT)].sort_values("wert", ascending=False)
        L.append(x if kl == "H" else x.head(10))
    L = pd.concat(L)
    raus_gesperrt = sorted(set(D[(D.p > 0.8) & D.sym.isin(GESPERRT)].sym))
    vor_fuenftel = set(vor[vor.p > 0.8].sym)
    vor_kurz = set(pd.concat([vor[(vor.kl == "H") & (vor.p > 0.8)]] + [vor[(vor.kl == k) & (vor.p > 0.8)].sort_values("wert", ascending=False).head(10) for k in ("M", "S")]).sym)
    o = []
    o.append("# ENTWURF · Altcoins — Fortbestand und Gelegenheit · Monatserster %s" % t.strftime("%d.%m.%Y"))
    o.append("")
    o.append("*Datenstand Kurse %s · Bestand: Desktop-Kopie vom 19.07.2026 (im Betrieb der aktuelle Stand) · Anschauung, **kein Kaufsignal**.*" % ENDE.strftime("%d.%m.%Y"))
    o.append("")
    o.append("**So ist dieser Abschnitt zu lesen.** Jeder Coin hat zwei Ebenen.")
    o.append("")
    o.append("- **Fortbestand** sind Fakten über Angebot, Nutzung und Einordnung. Sie sagen, ob das Asset das Zeug hat, dauerhaft zu bestehen. Das System bewertet sie **nicht**; die Gewichtung liegt bei dir. In Klammern steht, wie sich der Fakt in der Vergangenheit ausgewirkt hat.")
    o.append("- **Gelegenheit** ist der gemessene Rang: Wie günstig steht der Coin gerade im Vergleich zu seiner Klasse? Coins wie diese hatten bisher seltener Abstürze und häufiger Verdopplungen. ★★★ = oberstes Zehntel der Klasse, ★★ = übriges oberstes Fünftel.")
    o.append("- Die **Marke** ist der Nachlauf: 35 % unter dem Höchststand seit dem Kauf, mindestens aber die Hälfte des Kaufkurses. Fällt der Kurs darunter, würde die Regel verkaufen.")
    o.append("")
    try:
        import a3_messung as A3
        import l_messung as LM
        q = pd.Series(A3.QV, index=A.IDX).dropna(); br = pd.Series(A3.BRV, index=A.IDX).dropna(); n = LM.NETTO
        o.append("## Phase (nur Fakten)")
        o.append("")
        o.append("- **BTC-Klima %s**: %s." % (de(q.iloc[-1], 2), "im unteren Drittel der Geschichte, eher billig" if q.iloc[-1] < 1 / 3 else
                                                  "im mittleren Bereich" if q.iloc[-1] < 2 / 3 else "im oberen Drittel, eher teuer"))
        o.append("- **Altseason-Breite %.0f %%**: So viele der 50 größten Altcoins liefen in den letzten 90 Tagen besser als BTC. Ab 75 %% spricht man von einer Altseason." % (100 * br.iloc[-1]))
        o.append("- **Netto-Liquidität USA %s Bio. $**, in 13 Wochen %s (%s %%). Seit 2024 hat sie die Altcoins kaum noch bewegt." % (
            de(n.iloc[-1], 2), "gestiegen" if n.iloc[-1] > n.iloc[-14] else "gesunken", de(100 * (n.iloc[-1] / n.iloc[-14] - 1))))
        o.append("- **Monatlicher MACD der Altcoins**: noch unter Null, aber das Kreuz mit der Signallinie ist nahe. Zum Vergleich: 2017 und 2020 folgte darauf eine Altseason, im November 2024 nicht.")
        o.append("")
    except Exception as ex:                                                          # noqa: BLE001
        o.append("*(Phase nicht berechnet: %s)*" % ex)
    o.append("## Dein Bestand")
    o.append("")
    for s in krypto_bestand:
        if s in KERN:
            o.append("- **%s** — Kern (BTC/ETH/SOL), Aufbau 70/20/10, nicht Teil dieser Liste." % s); continue
        x = D[D.sym == s]
        if not len(x):
            if s in GESPERRT:
                grund = "das Symbol ist wegen Verwechslungsgefahr gesperrt"
            elif s not in K.columns or K[s].dropna().empty:
                grund = "für diesen Coin gibt es in unseren Daten keinen Binance-Spotkurs (im Betrieb: Kurs aus der Zuordnungstabelle, z. B. CANTON = CC an den Futures)"
            elif K[s].dropna().index[-1] < t:
                grund = ("die Kursreihe in den Desktop-Messdaten endet am %s; der Coin kommt nicht von Binance-Spot. Im Betrieb braucht er eine "
                         "eigene Kursquelle (Bitpanda-Ticker oder CoinGecko)" % K[s].dropna().index[-1].strftime("%d.%m.%Y"))
            elif (t - K[s].dropna().index[0]).days < 180:
                grund = "zu jung für eine Einstufung (weniger als 180 Tage Kurs)"
            else:
                grund = "an diesem Stichtag in keiner Klasse (kein Umsatz im Fenster)"
            o.append("- **%s** — *keine Einstufung:* %s. *Fortbestand:* %s" % (s, grund, profil_saetze(s, t, None))); continue
        r = x.iloc[0]
        lage = "oberstes Fünftel" if r.p > 0.8 else ("obere Hälfte" if r.p > 0.5 else ("untere Hälfte" if r.p > 0.2 else "unterstes Fünftel"))
        o.append("- **%s** (%s) %s — *Gelegenheit:* %s der Klasse; %s. *Fortbestand:* %s" % (
            s, NAMEN_KL[r.kl], stufe(r), lage, gelegenheit_satz(r), profil_saetze(s, t, r)))
    if nachgeladen:
        o.append("- *Strukturprofil für %s direkt bei CoinGecko nachgeschlagen (Zuordnung über das Kürzel; im Betrieb über die Zuordnungstabelle).*" % ", ".join(nachgeladen))
    o.append("- *Neuzugänge seit der letzten Mail: im Betrieb aus dem Bitpanda-Abgleich (neu gekaufte Coins, auch Neuemissionen; zu junge Coins ohne Einstufung, nur Fakten).*")
    o.append("")
    o.append("## Rangliste (Gelegenheit, nach Marktwert-Klassen)")
    for kl, titel in (("H", "Highcaps (alle im obersten Fünftel)"), ("M", "Midcaps (die besten 10)"), ("S", "Smallcaps (die besten 10) — Vorsicht: Bei Smallcaps senkt die Auswahl das Absturzrisiko kaum")):
        o.append("")
        o.append("### %s" % titel)
        o.append("")
        for r in L[L.kl == kl].itertuples():
            neu = []
            if r.sym not in vor_fuenftel:
                neu.append("neu im Fünftel")
            elif r.sym not in vor_kurz and kl != "H":
                neu.append("neu unter den besten 10")
            seit = 0
            for k in range(0, 4):
                hm = H[t - pd.DateOffset(months=k)]
                if r.sym in set(hm[hm.p > 0.8].sym):
                    seit += 1
                else:
                    break
            mk = marke(r.sym, t)
            mtext = ("%s (Kurs am Folgetag des Stichtags %s, heute %+.0f %%) — %s" % (zahl(mk[2]), zahl(mk[0]), 100 * (mk[1] / mk[0] - 1), mk[3])) if mk else "kein Kurs"
            o.append("- %s **%s**%s%s — *Gelegenheit:* %s; seit %s Monat%s im obersten Fünftel. *Fortbestand:* %s *Marke:* %s." % (
                stufe(pd.Series({"p": r.p})), r.sym, " · im Bestand" if r.sym in bestand else "", (" · " + ", ".join(neu)) if neu else "",
                gelegenheit_satz(r), seit if seit < 4 else "mindestens 4", "" if seit == 1 else "en", profil_saetze(r.sym, t, r), mtext))
    raus = sorted(vor_kurz - set(L.sym) - GESPERRT)
    o.append("")
    o.append("*Nicht mehr in der Liste gegenüber dem Vormonat:* %s. *Wegen Datensperre ausgeschlossen:* %s." % (", ".join(raus) or "—", ", ".join(raus_gesperrt) or "—"))
    o.append("")
    o.append("## Protokoll (ohne Geld)")
    o.append("")
    o.append("Jede Liste wird ab dem Folgetag gegen ihre Klasse und gegen BTC mitgeschrieben. Abgerechnet wird nach 6 und 12 Monaten, gehalten und mit Marke. Erst dann wird über Geld entschieden.")
    o.append("")
    o.append("## Anhang — Skalen: was ist günstig, und warum")
    o.append("")
    o.append("| Kriterium | günstig | ungünstig | warum (gemessen) |")
    o.append("|---|---|---|---|")
    o.append("| Alter (an Binance) | viele Jahre | jung | Alte Überlebende werden seltener eingestellt oder stürzen ab. Das ist der stärkste Faktor seit 2024 |")
    o.append("| Abstand zum Allzeithoch | weit darunter (im Verbund) | nah am Hoch | 2021–23 die Quelle der Chance; allein seit 2024 eher ungünstig, im Verbund neutral |")
    o.append("| Hoch liegt zurück | lange | kürzlich | ein ausgebrannter Zyklus statt eines frischen Absturzes |")
    o.append("| Nutzung (TVL) gegen Kurs | wächst schneller als der Kurs | fällt mit | kleiner Beitrag, nur für etwa 20 % der Coins vorhanden |")
    o.append("| Angebot fest, voll ausgegeben | — | — | **in der Vergangenheit neutral**; die These *begrenzte Menge schützt* ist nicht bestätigt und nicht widerlegt |")
    o.append("| Viel Verwässerung ausstehend (FDV > 1,5 × Marktwert) | — | ja | seit 2024 ungünstig |")
    o.append("| Gebühren | — | — | in der Vergangenheit eher ungünstig, wenige Fälle; vermutete Ursache (nicht gemessen): Tokens mit vielen Freigaben |")
    o.append("| RWA / Tokenisierung | ja | — | günstig in beiden Zeiträumen; aber nur 11–13 Coins, und wer heute RWA ist, hat das Thema überlebt |")
    o.append("| Meme, Gaming | — | ja | seit 2024 klar ungünstig |")
    o.append("| Smallcap | — | ja | Die Auswahl senkt dort das Absturzrisiko kaum |")
    open(ZIEL, "w", encoding="utf-8").write("\n".join(o) + "\n")
    print("geschrieben: %s (%d Zeilen) · Liste H/M/S %d/%d/%d · Bestand Krypto %d · gesperrt ausgeschlossen %s" % (
        ZIEL, len(o), (L.kl == "H").sum(), (L.kl == "M").sum(), (L.kl == "S").sum(), len(krypto_bestand), raus_gesperrt))


if __name__ == "__main__":
    main()
