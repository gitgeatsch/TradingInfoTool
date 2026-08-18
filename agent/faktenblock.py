# -*- coding: utf-8 -*-
"""Der deterministische Faktenblock fuer die E-Mail (Paket 12, 12.08.2026).

DIE ZWEITE SCHIENE. Nutzer am 12.08.: *"ganz wichtig - nein, es sollen keine
Zahlen in die Ablaufkette bzw. LLM - aber als Info bzw. wo als Fakt vorhanden
und sinnvoll ergaenzen (deterministische Schiene kombiniert)."*

    Faktentext  -> das Modell  -> R-T1..R-T9: relativ vor absolut
    Faktenblock -> der Nutzer  -> ABSOLUT ZUERST, Etikett statt Perzentil

Der Denkfehler der ersten Mail war, die Saetze fuer das MODELL zu uebernehmen.
Daher stand dort "3,9 Schwankungsbreiten hoeher, bei 62.000 EUR" statt
umgekehrt. R-T1/R-T2 wurden fuer ein Modell hergeleitet, das absolute Zahlen
nicht einordnen kann - der Nutzer kann das.

JEDE ZEILE SAGT DREI DINGE. Nutzer, 12.08.: *"so gestalten, dass es fuer mich
lesbar ist und klar, was die Information tatsaechlich besagt (kurze
Beschreibung, mit was ist gut und was ist schlecht)."* Also:

    Schwankung   3,0 % je Tag                             GUENSTIG
      Wie stark der Kurs taeglich schwingt, gemessen an seinem eigenen Jahr.
      Ruhig ist besser - ueber alle Einstiege gemessen: 29,5 % Treffer am
      guten Ende gegen 17,8 % am anderen, Schnitt 23,5 %.

Der Wirkungssatz spricht ausdruecklich ueber ALLE Einstiege, nicht ueber
diesen. Die erste Fassung lautete "ruhige Einstiege erreichten ihr Ziel in
29,5 % der Faelle" - das liest sich, als sei es die Aussicht DIESES Signals.
Sie ist es nicht: es ist die gemessene Verteilung, in die dieses Signal faellt.

Der Wert allein ist nicht benutzbar - "Perzentil 74" war genau der Einwand.
Die Wirkung allein auch nicht. Erst beides zusammen ist eine Information.

DER KERN SIND DREI FAMILIEN, NICHT ZEHN (Umbauplan 12.8, gemessen an 37
Symbolen und 20.494 Ankern gegen die Geometrie, die die App vorschlaegt).

MOMENTUM ERSCHEINT GENAU EINMAL. Rueckgang seit 60-Tage-Hoch, Abstand zur
50-Tage-Linie, Trend 20 Tage und RSI 14 haengen mit 0,59 bis 0,89 zusammen -
EIN Faktor, nicht vier. Wer sie einzeln auffuehrt, laesst einen Aufbau viermal
so gut belegt aussehen, wie er ist. Fear & Greed gehoert in dieselbe Familie
(zur Haelfte aus dem Kurs abgeleitet), nicht daneben.

ZUSATZINFO - DER MASSSTAB. Nutzer: *"kein Beiwerk ohne Sinn."* Sinnvoll ist,
was eine Dimension aufmacht, die die drei Familien NICHT abdecken. Ein weiteres
kursabgeleitetes Mass tut das nicht. Vier Kategorien bestehen: KOSTEN,
POSITIONIERUNG, FUNDAMENTAL, VORAUSSCHAUEND.

WAS FEHLT, WIRD BENANNT. Ein Kernfakt ohne Wert erscheint als Luecke, nicht als
Leerzeile - sonst sieht ein Signal mit zwei Fakten aus wie eines mit dreien.
"""
from __future__ import annotations

BASIS_TREFFER = 23.5        # ueber alle 20.494 Anker (Umbauplan 12.8)

# Die drei gemessenen Familien. `hoch_ist_gut` sagt, an welchem Ende der gute
# Fall liegt; `gut`/`schlecht` sind die gemessenen Trefferquoten dort.
KERN = {
    "schwankung": {
        "titel": "Schwankung",
        "hoch_ist_gut": False, "gut": 29.5, "schlecht": 17.8,
        "was": "Wie stark der Kurs taeglich schwingt, gemessen an seinem "
               "eigenen Jahr.",
        "richtung": "Ruhig ist besser",
    },
    "momentum": {
        "titel": "Kurs",
        "hoch_ist_gut": True, "gut": 28.0, "schlecht": 18.9,
        "was": "Wie weit der Kurs unter seinem Hoch der letzten drei Monate "
               "steht.",
        "richtung": "Nahe am Hoch ist besser",
    },
    "volumen": {
        "titel": "Volumen",
        "hoch_ist_gut": True, "gut": 27.1, "schlecht": 22.5,
        "was": "Wie viel heute gehandelt wird, verglichen mit den letzten "
               "20 Tagen.",
        "richtung": "Viel Umsatz ist besser",
    },
}

# Urteil aus dem Fuenftel. Bewusst drei Stufen statt fuenf - "leicht
# unterdurchschnittlich" ist keine Entscheidungshilfe.
_URTEIL = ("GUENSTIG", "MITTEL", "UNGUENSTIG")

KATEGORIEN = ("Kosten", "Positionierung", "Fundamental", "Vorausschauend")

# Welche Zusatzinfo in welchem Bereich vorkommen kann - aus der Bestandsaufnahme
# der sechs build_facts() (Umbauplan 12.2). Bewusst je Bereich verschieden,
# weil die Datenlage es ist.
ZUSATZ_JE_BEREICH = {
    # LIQUIDATION STEHT HIER NICHT. Sie gehoert der Rechnung (Abschnitt 2),
    # die sie aus dem gewaehlten Hebel ableitet. In der ersten Fassung stand
    # sie an beiden Stellen - und mit VERSCHIEDENEN Zahlen, weil die eine aus
    # einem Fakt und die andere aus der Rechnung kam. Genau der Fehler, den
    # die alte Hebel-Mail hatte (Umbauplan 12.5).
    # ⚠️ EIN FAKTENSATZ STATT ZWEI (S4, 18.08.2026, Umbauplan Kapitel 90).
    #
    # Bis heute bekam die Spot-Beurteilung EINEN Zusatzfakt, die
    # Hebel-Beurteilung VIER - fuer dasselbe Asset, zum selben Zeitpunkt, mit
    # demselben Kurs. Die Begruendung war das Instrument; sie traegt nicht:
    # Finanzierungsrate, Put-Skew und der Anteil der Long-Konten sagen etwas
    # ueber die POSITIONIERUNG im Markt, und die ist dieselbe, ob man sie
    # gehebelt handelt oder nicht.
    #
    # UND SIE SIND DIE INDIKATOREN, DIE DIE LITERATUR NENNT: hohes Open
    # Interest bei negativem Funding ist ein ueberfuellter Shortmarkt - eine
    # Aussage ueber den Kurs, nicht ueber das Instrument.
    #
    # DAS IST KEINE NEUTRALE AENDERUNG. Ein groesserer Faktensatz heisst ein
    # anderer Fingerabdruck, also eine andere Ausloeserate bei Spot. Gemessen
    # und dokumentiert in Umbauplan 92.8.
    "krypto_hebel": ("funding_eur_tag", "put_skew",
                     "retail_long_pct", "btc_relativwert_pct"),
    "krypto_spot": ("funding_eur_tag", "put_skew",
                    "retail_long_pct", "btc_relativwert_pct"),
    "aktien": ("kgv", "insider_saldo", "short_interest_pct", "analysten_trend"),
    "rohstoffe": ("lagerbestand_trend", "cot_netto_pct"),
    "themen_etf": (),
    "hedge": ("portfolio_exposure_eur",),
}

# Je Zusatzinfo: Kategorie, der Satz mit dem Wert, und WAS SIE BESAGT samt
# Richtung. Ohne den zweiten Teil ist es Beiwerk - genau das, was nicht sein
# soll.
_ZUSATZ = {
    "funding_eur_tag": ("Kosten",
        lambda w: f"Finanzierung {_de(w, 2)} EUR je Tag, bei zehn Tagen "
                  f"{_de(10 * w, 2)} EUR",
        "Was der Hebel taeglich kostet. Weniger ist besser - bei langer "
        "Haltedauer frisst diese Gebuehr den Vorteil des Hebels auf."),
    "liquidation_eur": ("Kosten",
        lambda w: f"Zwangsliquidation bei etwa {_de(w)} EUR",
        "Ab hier schliesst die Boerse die Position selbst. Weit weg ist "
        "besser - liegt sie naeher als der Stop, greift sie zuerst."),
    "put_skew": ("Vorausschauend",
        lambda w: f"Absicherung nach unten ist {_de(abs(w), 1)} Punkte "
                  f"{'teurer' if w < 0 else 'billiger'} als nach oben",
        "Was andere fuer Absicherung zahlen - der einzige Fakt hier, der "
        "nicht aus der Vergangenheit stammt. Teurer heisst: der Markt "
        "erwartet eher Rueckschlaege."),
    "retail_long_pct": ("Positionierung",
        lambda w: f"{_de(w)} % der Privatkonten stehen long (Binance)",
        "Wie die Masse positioniert ist. Extremwerte ueber 75 % gelten als "
        "Warnsignal - wer schon gekauft hat, kann nicht mehr kaufen."),
    "btc_relativwert_pct": ("Positionierung",
        lambda w: f"Gegen Bitcoin {_de(w, 1)} % "
                  f"{'staerker' if w >= 0 else 'schwaecher'} in 30 Tagen",
        "Trennt 'dieser Wert steigt' von 'der ganze Markt steigt'. "
        "ACHTUNG, zweifach: haengt teilweise mit der Kursentwicklung oben "
        "zusammen, und `btc_relativwert.py` nennt sich selbst einen "
        "'mehrmonatigen Hintergrundwert - KEINE Aussage ueber die naechsten "
        "Tage'. Als Hintergrund lesen, nicht als Ausloeser."),
    "kgv": ("Fundamental",
        lambda w: f"Kurs-Gewinn-Verhaeltnis {_de(w, 1)}",
        "Wie viele Jahresgewinne im Kurs stecken. Niedriger ist guenstiger "
        "bewertet - sagt nichts ueber das Timing."),
    "insider_saldo": ("Positionierung",
        lambda w: f"Insider haben zuletzt netto "
                  f"{'gekauft' if w > 0 else 'verkauft'} "
                  f"({_de(abs(w))} Meldungen)",
        "Was die Fuehrungskraefte mit eigenem Geld tun. Kaeufe gelten als "
        "das aussagekraeftigere Signal - verkauft wird aus vielen Gruenden."),
    "short_interest_pct": ("Positionierung",
        lambda w: f"{_de(w, 1)} % der Aktien sind leerverkauft",
        "Wie viele auf fallende Kurse setzen. Hohe Werte schneiden in beide "
        "Richtungen: mehr Skepsis, aber auch Rueckkaufdruck bei Anstiegen."),
    "analysten_trend": ("Positionierung",
        lambda w: f"Analystenurteile: {w}",
        "Wohin die Einschaetzungen zuletzt gewandert sind. Der schwaechste "
        "der vier Punkte hier - als Hintergrund brauchbar, als Grund nicht."),
    "lagerbestand_trend": ("Fundamental",
        lambda w: f"Lagerbestaende: {w}",
        "Angebot und Nachfrage direkt. Fallende Bestaende sprechen fuer "
        "steigende Preise."),
    "cot_netto_pct": ("Positionierung",
        lambda w: f"Terminmarkt: Grossanleger netto {_de(w, 1)} % long",
        "Wie die professionelle Seite positioniert ist. Extreme in beide "
        "Richtungen gelten als Wendehinweis."),
    "portfolio_exposure_eur": ("Positionierung",
        lambda w: f"Abzusicherndes Volumen {_de(w)} EUR",
        "Keine Meinung, sondern die Rechengrundlage der Absicherung."),
}


def _de(wert: float, stellen: int = 0) -> str:
    """Deutsche Schreibweise - jetzt aus `agent/schreibweise.py`.

    ⚠️ HIER STAND EINE EIGENE KOPIE, und es gab VIER davon
    (faktenblock, ausstiegsrechnung, trefferbilanz, signal_mail.eur),
    die sich nur in der Vorgabe fuer die Stellenzahl unterschieden.
    Die Vorgabe bleibt hier - sie gehoert zum Verwendungszweck -,
    die Rechnung nicht."""
    from agent.schreibweise import de as _s_de

    return _s_de(wert, stellen)


ATR_FENSTER = 14
RUECKBLICK = 250
MOMENTUM_FENSTER = 60
VOLUMEN_FENSTER = 20


def werte_aus_reihe(hoch, tief, schluss, volumen, i: int | None = None,
                    tag_vollstaendig: bool = True) -> dict:
    """Die sechs Zahlen des Kerns aus einer OHLCV-Reihe.

    DIESE DEFINITIONEN MUESSEN DENEN DER MESSUNG ENTSPRECHEN. Sie stehen ein
    zweites Mal hier, weil `messe_top_fakten.py` ein Messskript ist und die
    Produktion nicht davon abhaengen soll - aber eine zweite Fassung ist genau
    die Sorte Kopie, die still veraltet (siehe die Kostensaetze, 12.08.).
    DESHALB GIBT ES EINE PRUEFUNG, DIE BEIDE AUF ECHTEN DATEN VERGLEICHT statt
    die Gleichheit nur zu behaupten.

    Das Perzentil laeuft ueber ein RUECKWAERTS-Fenster von 250 Tagen. Ein
    Perzentil ueber die ganze Reihe kennt die Zukunft - es weiss, wie hoch die
    Schwankung spaeter noch steigen wird.

    `tag_vollstaendig=False` LAESST DAS VOLUMEN WEG, und das ist keine
    Feinheit. Der laufende Tag hat naturgemaess weniger Umsatz als ein ganzer;
    an echten BTC-Daten stand das Volumen des letzten Tages beim 0,2-fachen des
    Mittels, also im untersten Perzentil. Ohne diesen Schalter haette JEDE
    Live-Mail "Volumen UNGUENSTIG" gemeldet - ein systematischer Fehler in
    jeder einzelnen Nachricht, und einer, der wie ein Befund aussieht.
    `lagebeschreibung._volumen()` kennt dieselbe Falle seit laengerem."""
    import numpy as np

    h = np.asarray(hoch, float); l = np.asarray(tief, float)
    c = np.asarray(schluss, float); v = np.asarray(volumen, float)
    i = len(c) - 1 if i is None else i
    # DAS GROESSTE FENSTER ENTSCHEIDET, NICHT DAS ERSTE (15.08.2026).
    #
    # Hier stand `RUECKBLICK + ATR_FENSTER` = 264. Die drei Perzentile blicken
    # aber ueber RUECKBLICK Tage ZURUECK und rechnen an jedem davon ein
    # eigenes Fenster: `rueckgang_bei(k)` greift auf `c[k - MOMENTUM_FENSTER :
    # k + 1]`. Beim aeltesten k (= i - RUECKBLICK) braucht das also
    # RUECKBLICK + MOMENTUM_FENSTER = 310 Kerzen.
    #
    # DAZWISCHEN LAG EINE LUECKE VON 46 KERZEN, und in der stuerzte es ab:
    # ein negativer Startindex laesst numpy vom Reihenende zaehlen, die
    # Auswahl wird LEER, und `.max()` auf einem leeren Feld wirft
    #
    #     ValueError: zero-size array to reduction operation maximum
    #
    # Gefunden an ASTER (299 Kerzen), 16-mal im Log seit dem 14.08. - gefangen
    # vom breiten Fehlerfang, also fiel das Symbol bei JEDEM Lauf still aus.
    # Das ist kein Einzelfall: JEDES Symbol durchlaeuft dieses Fenster,
    # waehrend seine Historie waechst. MON stand an diesem Tag bei 264.
    if i < RUECKBLICK + max(ATR_FENSTER, MOMENTUM_FENSTER, VOLUMEN_FENSTER):
        return {}

    def atr_bei(k):
        tr = np.maximum(h[k - ATR_FENSTER + 1:k + 1] - l[k - ATR_FENSTER + 1:k + 1],
                        np.maximum(np.abs(h[k - ATR_FENSTER + 1:k + 1] - c[k - ATR_FENSTER:k]),
                                   np.abs(l[k - ATR_FENSTER + 1:k + 1] - c[k - ATR_FENSTER:k])))
        return float(tr.mean())

    reihe = np.array([atr_bei(k) / c[k] for k in range(i - RUECKBLICK, i + 1)])
    atr_rel = reihe[-1]

    # DER LETZTE VOLLSTAENDIGE TAG STATT GAR KEINER (Gegenpruefung 13.08.).
    #
    # Die erste Fassung liess das Volumen beim laufenden Tag einfach weg -
    # richtig gedacht, aber in der Praxis bedeutet es: JEDES Live-Signal
    # rechnet auf dem juengsten Tag, also fehlte eine der DREI gemessenen
    # Familien in JEDER Nachricht. Der Faktenblock versprach drei Punkte und
    # lieferte zwei.
    #
    # Der Umsatz von GESTERN ist kein perfekter Ersatz, aber er ist ein
    # ganzer Tag - und ungleich mehr wert als eine Luecke. Dass er von
    # gestern ist, steht im Text.
    ende = i if tag_vollstaendig else i - 1
    fenster_v = v[ende - VOLUMEN_FENSTER:ende]
    vol_rel = (float(v[ende] / fenster_v.mean())
               if ende > VOLUMEN_FENSTER and fenster_v.mean() > 0 else None)

    def rueckgang_bei(k):
        hoechst = c[k - MOMENTUM_FENSTER:k + 1].max()
        return float(c[k] / hoechst - 1) if hoechst > 0 else 0.0

    rueck = np.array([rueckgang_bei(k) for k in range(i - RUECKBLICK, i + 1)])

    def vol_rel_bei(k):
        m = v[k - VOLUMEN_FENSTER:k].mean()
        return float(v[k] / m) if m > 0 else np.nan

    vols = np.array([vol_rel_bei(k) for k in range(ende - RUECKBLICK, ende + 1)])

    def rang(reihe_, wert):
        vor = reihe_[:-1]
        vor = vor[~np.isnan(vor)]
        return float((vor < wert).mean()) if len(vor) > 30 else None

    return {"atr_relativ": float(atr_rel),
            "schwankung_perzentil": rang(reihe, atr_rel),
            "rueckgang_60t": float(rueck[-1]),
            "momentum_perzentil": rang(rueck, rueck[-1]),
            "volumen_relativ": vol_rel,
            "volumen_von_gestern": bool(not tag_vollstaendig),
            "volumen_perzentil": rang(vols, vols[-1]) if vol_rel else None}


def _urteil(perzentil: float, hoch_ist_gut: bool) -> str:
    """Fuenftel -> eines von drei Woertern.

    Das unterste und das oberste Fuenftel sind die gemessenen Enden; alles
    dazwischen ist MITTEL. Feiner zu unterscheiden hiesse, Genauigkeit zu
    behaupten, die die Messung nicht hergibt."""
    p = min(1.0, max(0.0, float(perzentil)))
    gut_ende = p >= 0.8 if hoch_ist_gut else p <= 0.2
    schlecht_ende = p <= 0.2 if hoch_ist_gut else p >= 0.8
    return _URTEIL[0] if gut_ende else (_URTEIL[2] if schlecht_ende else _URTEIL[1])


# WELCHE PERZENTILE DAS MODELL NIE ZU SEHEN BEKOMMT (17.08.2026).
#
# DER ANLASS: das Modell hat sie sich selbst ausgedacht. In den Belegen
# echter Signale stand
#
#     "Umsatzvolumen im 8. Perzentil (extrem ruhig)"
#     "Umsatzvolumen im 92. Perzentil der letzten 400 Tage"
#     "MORPHO Handelsvolumen im 100. Perzentil der letzten 400 Tage"
#
# - vierzehnmal, samt einer Fensterlaenge ("400 Tage"), die in keinem
# unserer Saetze vorkommt. `kern()` sagt es ausdruecklich: *"Das Perzentil
# erscheint NICHT im Text - es bestimmt nur das Urteilswort."* Das Modell
# hat aus dem Urteilswort (GUENSTIG/UNGUENSTIG) eine plausible Zahl
# zurueckgerechnet und sie als Messung hingeschrieben.
#
# Es ist die Umkehrung von R-T12: wir geben ein Etikett, und das Modell
# baut daraus die Zahl, die wir ihm bewusst nicht gegeben haben.
#
# ⚠️ `auch_woanders` IST DER GANZE TRICK. Die Schwankung hat sehr wohl ein
# Perzentil - im LAGEBILD, fuer den Markt ("Bitcoin-Volatilitaet im 0.
# Perzentil"). Ein Beleg, der das zitiert, ist korrekt, und ihn zu melden
# waere ein Fehlalarm. Von 33 Funden der ersten Prompt-Pruefung waren 31
# genau solche; nach dem dritten Fehlalarm liest niemand mehr hin.
PERZENTIL_NUR_INTERN = {
    "volumen": {"woerter": ("umsatzvolumen", "handelsvolumen",
                            "umsatz", "volumen"),
                "auch_woanders": False},
    "schwankung": {"woerter": ("schwankung", "volatilit"),
                   "auch_woanders": True},
    "momentum": {"woerter": ("kursentwicklung", "60-tage-hoch"),
                 "auch_woanders": False},
}


def _block(schluessel: str, wert_text: str, perzentil: float) -> list[str]:
    k = KERN[schluessel]
    urteil = _urteil(perzentil, k["hoch_ist_gut"])
    return [f"{k['titel']:<12} {wert_text:<40} {urteil}",
            f"  {k['was']}",
            f"  {k['richtung']} - ueber alle Einstiege gemessen: "
            f"{_de(k['gut'], 1)} % Treffer am guten Ende gegen "
            f"{_de(k['schlecht'], 1)} % am anderen, Schnitt {_de(BASIS_TREFFER, 1)} %."]


def kern(*, atr_relativ: float | None = None,
         schwankung_perzentil: float | None = None,
         rueckgang_60t: float | None = None,
         momentum_perzentil: float | None = None,
         volumen_relativ: float | None = None,
         volumen_von_gestern: bool = False,
         volumen_perzentil: float | None = None) -> tuple[list[str], list[str]]:
    """Die drei gemessenen Familien. Gibt (Zeilen, Luecken) zurueck.

    Jede Familie braucht ZWEI Angaben: den Wert zum Anzeigen und das Perzentil
    zum Einordnen. Das Perzentil erscheint NICHT im Text - es bestimmt nur das
    Urteilswort. Genau so war die Messung aufgebaut (Fuenftel), und genau so
    ist der Nutzereinwand beantwortet: die Zahl, die er lesen kann, steht da;
    die, die er nicht lesen kann, wirkt im Hintergrund."""
    zeilen, luecken = [], []

    if atr_relativ is None or schwankung_perzentil is None:
        luecken.append("Schwankung")
    else:
        zeilen += _block("schwankung", f"{_de(100 * atr_relativ, 1)} % je Tag",
                         schwankung_perzentil)

    if rueckgang_60t is None or momentum_perzentil is None:
        luecken.append("Kursentwicklung")
    else:
        zeilen += [""] if zeilen else []
        zeilen += _block(
            "momentum",
            "auf dem Hoch der letzten 60 Tage" if rueckgang_60t >= -0.001 else
            f"{_de(abs(100 * rueckgang_60t), 1)} % unter dem 60-Tage-Hoch",
            momentum_perzentil)

    if volumen_relativ is None or volumen_perzentil is None:
        luecken.append("Volumen")
    else:
        zeilen += [""] if zeilen else []
        zeilen += _block("volumen",
                         f"das {_de(volumen_relativ, 1)}-fache des Mittels"
                         # WOHER DIE ZAHL KOMMT, STEHT DABEI. Am laufenden Tag
                         # ist es der Umsatz von gestern - ein ganzer Tag statt
                         # eines angefangenen. Das zu verschweigen hiesse, eine
                         # Zahl von gestern als heutige auszugeben.
                         + (" (Vortag)" if volumen_von_gestern else ""),
                         volumen_perzentil)
    return zeilen, luecken


def zusatz(bereich: str, werte: dict, symbol: str | None = None) -> list[str]:
    """Die optionalen Fakten des Bereichs - nur die, fuer die ein Wert vorliegt.

    NICHTS WIRD ERFUNDEN und nichts wird als Luecke gemeldet: Zusatzinfo ist
    freiwillig, ihr Fehlen ist keine Aussage. Anders als beim Kern."""
    aus = []
    for schluessel in ZUSATZ_JE_BEREICH.get(bereich, ()):
        w = werte.get(schluessel)
        if w is None or (isinstance(w, str) and not w.strip()):
            continue
        # "Gegen Bitcoin 0,0 % staerker" - fuer Bitcoin selbst. Ein Wert gegen
        # sich selbst ist keine Aussage, sondern eine Tautologie mit Zahl.
        if schluessel == "btc_relativwert_pct" and (symbol or "").upper() == "BTC":
            continue
        kategorie, bau, bedeutung = _ZUSATZ[schluessel]
        aus += [f"[{kategorie}] {bau(w)}", f"  {bedeutung}"]
    return aus


def baue(bereich: str, *, kern_werte: dict, zusatz_werte: dict | None = None,
         symbol: str | None = None) -> list[str]:
    """Der ganze Block. Kern zuerst, Zusatzinfo als solche gekennzeichnet.

    DIE ABSICHERUNG BEKOMMT DEN KERN NICHT (Paket 14, 15.08.2026).

    GEFUNDEN IM TROCKENLAUF, an einer echten 3QSS-Mail:

        Schwankung   4,9 % je Tag                    UNGUENSTIG
          Ruhig ist besser - ueber alle Einstiege gemessen: 29,5 % Treffer
          am guten Ende gegen 17,8 % am anderen.

    Die drei Kernfamilien sind an EINSTIEGEN gemessen - an der Frage, ob ein
    Kauf sein Ziel vor dem Stop erreicht. Ein Absicherungsinstrument wird nicht
    gekauft, um zu steigen; es soll fallen, wenn das Depot faellt. "Ruhig ist
    besser" auf 3QSS anzuwenden heisst, eine Trefferquote aus einer anderen
    Grundgesamtheit als Messwert hinzuschreiben.

    DAS IST SCHLIMMER ALS EINE FEHLENDE ANGABE. Eine Luecke sieht man; eine
    Zahl mit falscher Herkunft liest sich wie ein Befund. Der Prompt fragt seit
    Paket 14 nach dem Portfolio - die Mail muss dieselbe Frage stellen.

    WAS BLEIBT: die Marken (wo liegt der Kurs) und die Portfoliolage aus
    `absicherung_fakten`. Beides steht ueber `lage_fakten` bzw. `marken` in der
    Mail und ist von dieser Aenderung unberuehrt."""
    if bereich == "hedge":
        z = zusatz(bereich, zusatz_werte or {}, symbol)
        return (["Die gemessenen Einstiegs-Trefferquoten gelten hier NICHT - "
                 "sie stammen von Kaufsignalen, und eine Absicherung wird "
                 "nicht gekauft, um zu steigen."] + (z or []))
    zeilen, luecken = kern(**kern_werte)
    if luecken:
        # EINE LUECKE IST EINE AUSSAGE. Ein Signal mit zwei Fakten darf nicht
        # aussehen wie eines mit dreien.
        zeilen += ["", f"Keine Angabe zu: {', '.join(luecken)}. "
                       + ("Ein Punkt weniger steht" if len(luecken) == 1
                          else f"{len(luecken)} Punkte weniger stehen")
                       + " damit hinter dieser Empfehlung."]
    z = zusatz(bereich, zusatz_werte or {}, symbol)
    if z:
        zeilen += ["", "ZUSATZINFO - nicht gemessen, zur eigenen Einordnung:", ""]
        zeilen += z
    return zeilen
