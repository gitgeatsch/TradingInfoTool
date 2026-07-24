"""Hebel-Risiko-/Positionsgroessen-/Liquidationspreis-Formeln (RM-1/RM-10/RM-11/
AZ-7, 2026-07-14, siehe docs/hebel_positionsformel.md fuer die volle Herleitung
+ Kalibrierung gegen 311 echte Bitpanda-Margin-Positionen).

Bewusst ein EIGENES Modul, nicht in risk_gate.py gefaltet - andere Schwellenwerte
und ein anderes Timing als Spot (RM-1 fuer Hebel ist 1%, nicht die Spot-2%; die
Liquidationspreis-Formel hat eine Zeitkomponente, die es bei Spot nicht gibt).
`CRV_MINIMUM` wird trotzdem aus risk_gate.py importiert statt dupliziert - die
CRV-Pflicht selbst bleibt bei 2.0, unveraendert gegenueber Spot (Nutzer-
Entscheidung 2026-07-14: die hebel-spezifischen Zusatzrisiken sind bereits an
der Quelle adressiert, siehe unten - eine zusaetzlich verschaerfte CRV waere
Risiko-Stapelung statt gezielter Loesung).

Gleiches Grundprinzip wie risk_gate.py: pre_check_hebel() laeuft VOR dem
LLM-Call (harte Obergrenze als Fakt), post_check_hebel() erzwingt danach
dieselben Regeln nochmal deterministisch - das Modell wird nie blind vertraut."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from agent.krypto.anticyclic import LONG_BIAS_EXTREME_THRESHOLD_PCT
from agent.krypto.risk_gate import CRV_MINIMUM, KONFIDENZ_SCHWELLE_HOCH, KONFIDENZ_SCHWELLE_NIEDRIG

RICHTUNG_LONG = "LONG"
RICHTUNG_SHORT = "SHORT"
ZWEIG_KONTRA = "kontra"

_HEBEL_ACTIONS_MIT_HEBEL = ("ERÖFFNEN", "NACHKAUFEN", "HEBEL_ERHÖHEN")

# 2026-07-22, echter VIRTUAL-Fund: LONG-Signal fuer einen Alt-Coin waehrend
# `btc_matrix == "baer_flucht"` (BTC faellt, Dominanz steigt) - das LLM nannte
# das Regime im Gegenargument korrekt als staerksten Einwand, aber NUR weil es
# das nackte Label selbst richtig interpretiert hat, nicht weil das System es
# ihm erklaert oder deterministisch gedeckelt haette (agent/krypto/regime.py::
# BTC_MATRIX dokumentiert explizit "Alt-Ausbrueche meist Fallen" fuer genau
# diese beiden Zustaende - Spot-Pipeline (analyst.py Regel 8) kennt diese Regel
# bereits, Hebel bisher nicht).
_ALT_LONG_SKEPSIS_BTC_MATRIX_STATES = ("btc_season", "baer_flucht")


def regime_konflikt_hebel(regime: str, richtung: str) -> bool:
    """Position widerspricht dem aktuellen Regime (z.B. LONG im baer-Regime).
    Als eigene Funktion extrahiert (2026-07-19), damit sowohl der Hebel-Deckel
    als auch die Risikofaktoren-Anzeige (compute_risikofaktoren_hebel()) auf
    exakt derselben Bedingung basieren - keine zwei Stellen, die driften
    koennten."""
    return (regime == "baer" and richtung == RICHTUNG_LONG) or (regime == "bulle" and richtung == RICHTUNG_SHORT)


def retail_konsens_risiko(
    retail_long_bias_extreme: bool | None, long_account_pct: float | None, richtung: str,
) -> bool:
    """2026-07-19, echter AVAX-Fund (siehe post_check_hebel()-Docstring):
    True, wenn die empfohlene Richtung mit der extremen Mehrheits-
    positionierung der Retail-Trader uebereinstimmt, statt (antizyklisch
    korrekt) dagegen zu wetten. Symmetrisch zu anticyclic.py::
    LONG_BIAS_EXTREME_THRESHOLD_PCT (65%) - bei SHORT gilt die Crowd als "im
    Konsens", wenn <= 35% der Konten long sind (also >= 65% short)."""
    if retail_long_bias_extreme and richtung == RICHTUNG_LONG:
        return True
    if (
        long_account_pct is not None
        and long_account_pct <= (100 - LONG_BIAS_EXTREME_THRESHOLD_PCT)
        and richtung == RICHTUNG_SHORT
    ):
        return True
    return False


def these_regime_widerspruch(trade_thesis_typ: str | None, regime_konflikt: bool) -> bool:
    """2026-07-19, echter VIRTUAL/AVAX-Fund: `trade_thesis_typ == 'swing_strategie'`
    bedeutet laut SYSTEM_PROMPT ein "bestaetigter, noch nicht ausgereizter
    Trend" - das widerspricht sich mit einem gleichzeitigen Regime-Konflikt
    (die Position ist per Definition ein Gegen-Trend-Setup). Reine
    Sichtbarmachungs-Inkonsistenz, KEIN Hebel-Deckel (es gibt keine saubere
    numerische Dimension dafuer) - taucht nur in der Risikofaktoren-Liste auf."""
    return trade_thesis_typ == "swing_strategie" and regime_konflikt


@dataclass
class Risikofaktor:
    name: str
    bewertung: str  # "positiv" | "neutral" | "negativ"
    begruendung: str


def _kontrathese_bestaetigt_seit_stunden(
    verlauf: list, aktuelle_llm_richtung: str, now_unix: int,
) -> float:
    """Kontrathese-Uebersetzung (2026-07-24, echter NEAR/HYPE-Fund): wie lange
    (in Stunden) liegt bereits eine DURCHGEHENDE Kontrathese in dieselbe
    Richtung vor - laeuft von JETZT rueckwaerts durch `verlauf` (bereits
    neueste-zuerst sortiert, siehe db.get_hebel_signal_history()), bis der
    erste Eintrag OHNE passende Kontrathese auftaucht. Gibt 0.0 zurueck, wenn
    schon der letzte Eintrag nicht passt - dann beginnt der Streak jetzt neu.

    Bewusst zeitfenster- statt zyklusbasiert (siehe Nutzer-Diskussion,
    echter Export 2026-07-24): eine reine "letzte Bewertung stimmt auch
    schon zu"-Pruefung waere bei einem 15-Minuten-Screening-Takt praktisch
    wirkungslos gegen Rauschen (echte Daten zeigten 65%->60%->zurueck auf
    LONG binnen 30 Minuten) - das Zeitfenster bleibt unabhaengig davon, wie
    oft tatsaechlich neu bewertet wird, und erlaubt trotzdem weiterhin
    beliebig haeufiges Monitoring (bewusst NICHT ueber den Cooldown
    gedrosselt - haeufiges Hinschauen bei erhoehtem Risiko ist erwuenscht,
    nur das vorschnelle HANDELN darauf soll gedaempft werden)."""
    streak_start_unix = now_unix
    for sig in verlauf:
        if not sig.kontrathese_zu_position or sig.kontrathese_llm_richtung != aktuelle_llm_richtung:
            break
        streak_start_unix = int(datetime.fromisoformat(sig.created_at).timestamp())
    return max(0.0, (now_unix - streak_start_unix) / 3600)


def compute_risikofaktoren_hebel(
    *, richtung: str, regime: str, confidence_pct: float | None,
    crv: float | None, confluence=None,
    gegenszenario_pct: float | None, gegenszenario_schwelle: float | None,
    crv_knapp_schwelle_relativ: float | None,
    retail_long_bias_extreme: bool | None, long_account_pct: float | None,
    trade_thesis_typ: str | None,
    hebel_erlaubt: bool = True, veto_reason: str | None = None,
    historische_erfolgsquote: dict | None = None,
    min_sample_fuer_aussage: int = 15,
    sl_abstand_relativ: float | None = None,
    sl_abstand_eng_schwelle_relativ: float | None = None,
    funding_rate_stunde: float | None = None,
    funding_kosten_usd_pro_tag: float | None = None,
    funding_rate_hoch_schwelle_relativ_stunde: float | None = None,
    ist_core_asset: bool = False,
    btc_matrix_state: str | None = None,
    btc_matrix_hinweis: str | None = None,
    liquiditaetszonen: dict | None = None,
    kontrathese_zu_position: bool = False,
    kontrathese_llm_richtung: str | None = None,
    kontrathese_bestaetigt: bool = False,
    kontrathese_bestaetigt_seit_stunden: float | None = None,
) -> list["Risikofaktor"]:
    """2026-07-19 (Nutzer-Wunsch: E-Mail/App-Neustrukturierung in 3 Abschnitte -
    Mathematisch berechnet / LLM-Bewertung / Konklusion mit Risikofaktoren).
    Deterministische Zusammenfassung aller bereits vorhandenen Deckel-/
    Konsistenz-Checks in eine kompakte positiv/neutral/negativ-Liste fuer
    Abschnitt 3 - bewusst NICHT vom LLM generiert (genau das war beim
    AVAX-Fund das eigentliche Problem: das Modell selbst hatte einen
    Interpretationsfehler). Nutzt dieselben Pruef-Funktionen wie die
    eigentliche Hebel-Deckelung (regime_konflikt_hebel(), retail_konsens_
    risiko(), these_regime_widerspruch()) - keine zweite, potenziell
    driftende Implementierung derselben Bedingungen."""
    faktoren: list[Risikofaktor] = []

    if not hebel_erlaubt:
        faktoren.append(Risikofaktor("Hebel-Veto", "negativ", veto_reason or "Hebel nicht erlaubt."))
        return faktoren

    # Kontrathese-Uebersetzung (2026-07-24, siehe HebelSignal.kontrathese_zu_
    # position-Docstring + post_check_hebel()) - IMMER als erster, am meisten
    # herausgehobener Faktor, da action/richtung an dieser Stelle bereits das
    # UEBERSETZTE Ergebnis tragen und ohne diesen Hinweis nicht nachvollziehbar
    # waeren, warum z.B. ploetzlich TEILVERKAUF/SCHLIESSEN statt der gewohnten
    # Positions-Ueberwachung erscheint.
    if kontrathese_zu_position:
        konf_text = f" (Konfidenz {confidence_pct:.0f}%)" if confidence_pct is not None else ""
        if kontrathese_bestaetigt:
            status_text = (
                f"über ca. {kontrathese_bestaetigt_seit_stunden:.1f}h bestätigt"
                if kontrathese_bestaetigt_seit_stunden is not None
                else "eindeutiger Alarm (hohe Konfidenz), sofort ausgelöst"
            )
        else:
            status_text = "erstmalige Erkennung, noch nicht bestätigt - deshalb noch keine Aktion ausgelöst"
        faktoren.append(Risikofaktor(
            "Kontrathese zur offenen Position", "negativ",
            f"Modell sieht aktuell ein {kontrathese_llm_richtung}-Signal{konf_text}, obwohl eine "
            f"offene {richtung}-Position besteht (auf Bitpanda nicht als echte Gegenposition "
            f"ausführbar) - {status_text}.",
        ))

    regime_konflikt = regime_konflikt_hebel(regime, richtung)
    if regime_konflikt:
        faktoren.append(Risikofaktor(
            "Regime-Konflikt", "negativ",
            f"Position ({richtung}) widerspricht dem aktuellen {regime}-Regime.",
        ))
    else:
        faktoren.append(Risikofaktor(
            "Regime-Ausrichtung", "positiv",
            f"Position ({richtung}) folgt dem aktuellen {regime}-Regime, kein Gegen-Trend-Setup.",
        ))

    if these_regime_widerspruch(trade_thesis_typ, regime_konflikt):
        faktoren.append(Risikofaktor(
            "These-Regime-Widerspruch", "negativ",
            "Als 'bestätigter Trend' (swing_strategie) eingestuft, obwohl die Position "
            "gleichzeitig dem Regime widerspricht - innerer Widerspruch in der Klassifikation.",
        ))

    # 2026-07-22, echter VIRTUAL-Fund (siehe Konstanten-Kommentar oben): eigene,
    # von `regime_konflikt_hebel()` UNABHAENGIGE Dimension - die BTC-Dominanz-
    # Matrix warnt speziell vor Alt-Coin-LONG-Ausbruechen, unabhaengig vom
    # generischen baer/bulle-Regime (ein Alt-LONG kann z.B. auch bei Regime
    # "seitwaerts" in "baer_flucht" liegen). Text wird bewusst 1:1 aus
    # `btc_matrix_beschreibung` uebernommen (bereits ein vollstaendiger,
    # verstaendlicher Satz aus regime.py::BTC_MATRIX) statt neu formuliert -
    # eine Quelle der Wahrheit, kein driftender Zweittext.
    if (
        richtung == RICHTUNG_LONG
        and not ist_core_asset
        and btc_matrix_state in _ALT_LONG_SKEPSIS_BTC_MATRIX_STATES
        and btc_matrix_hinweis
    ):
        faktoren.append(Risikofaktor("Alt-Coin-Marktphase", "negativ", btc_matrix_hinweis))

    if gegenszenario_pct is not None and gegenszenario_schwelle is not None:
        if gegenszenario_pct >= gegenszenario_schwelle:
            faktoren.append(Risikofaktor(
                f"Gegenszenario-Wahrscheinlichkeit {gegenszenario_pct:.0f}%", "negativ",
                f"Modell schätzt die Wahrscheinlichkeit für das Gegenszenario hoch ein "
                f"(>= Schwelle {gegenszenario_schwelle:.0f}%).",
            ))
        else:
            faktoren.append(Risikofaktor(
                f"Gegenszenario-Wahrscheinlichkeit {gegenszenario_pct:.0f}%", "positiv",
                f"Modell schätzt das Gegenszenario als eher unwahrscheinlich ein "
                f"(< Schwelle {gegenszenario_schwelle:.0f}%).",
            ))

    if confluence is not None:
        if confluence.overall_bias == "gemischt":
            faktoren.append(Risikofaktor(
                "Technische Konfluenz", "negativ",
                "Technische Indikatoren widersprechen sich (weder bullish noch bearish dominiert).",
            ))
        else:
            faktoren.append(Risikofaktor(
                "Technische Konfluenz", "positiv",
                f"Technische Indikatoren zeigen eine eindeutige Tendenz ({confluence.overall_bias}).",
            ))

    # 2026-07-22, echter Fund (BTC-Signal 21:35 in derselben Nacht): eine hohe
    # CRV kann aus einem sehr weiten Take-Profit ODER aus einem sehr ENGEN
    # Stop-Loss entstehen - die reine Verhaeltniszahl unterscheidet das nicht.
    # Ein 1,12%-Stop bei 3x Hebel wurde als "CRV deutlich ueber Minimum,
    # positiv" gewertet, obwohl normales Kursrauschen (kein Krisenereignis
    # noetig) den Stop ausloesen kann - der SL-Abstand gehoert deshalb IMMER
    # mit in den Text (Fakt zuerst, wie beim Retail-Konsens-Fix oben).
    sl_abstand_text = (
        f" Stop-Loss-Abstand vom Entry: {sl_abstand_relativ * 100:.1f}%."
        if sl_abstand_relativ is not None else ""
    )
    if crv is not None:
        if crv_knapp_schwelle_relativ is not None and crv < CRV_MINIMUM * (1 + crv_knapp_schwelle_relativ):
            faktoren.append(Risikofaktor(
                f"CRV {crv:.2f}", "negativ",
                f"Chance-Risiko-Verhältnis liegt nur knapp über dem Minimum ({CRV_MINIMUM:.1f})."
                f"{sl_abstand_text}",
            ))
        elif crv >= CRV_MINIMUM * 1.5:
            faktoren.append(Risikofaktor(
                f"CRV {crv:.2f}", "positiv",
                f"Chance-Risiko-Verhältnis liegt deutlich über dem Minimum ({CRV_MINIMUM:.1f})."
                f"{sl_abstand_text}",
            ))
        else:
            faktoren.append(Risikofaktor(
                f"CRV {crv:.2f}", "neutral",
                f"Solide über dem Minimum, aber nicht herausragend.{sl_abstand_text}",
            ))

    if (
        sl_abstand_relativ is not None
        and sl_abstand_eng_schwelle_relativ is not None
        and sl_abstand_relativ < sl_abstand_eng_schwelle_relativ
    ):
        faktoren.append(Risikofaktor(
            f"Enger Stop-Loss ({sl_abstand_relativ * 100:.1f}%)", "negativ",
            f"Stop-Loss liegt nur {sl_abstand_relativ * 100:.1f}% vom Entry entfernt (Schwelle: "
            f"{sl_abstand_eng_schwelle_relativ * 100:.1f}%) - kann bei gehebelter Position bereits "
            "durch normales Kursrauschen ausgelöst werden, unabhängig von einer hohen CRV.",
        ))

    # 2026-07-22, echter Fund (mehrfach in derselben Nacht: BTC/ONDO/HYPE/XLM/
    # INJ bei 51-64% long): die alte Version pruefte NUR "ist es extrem?" und
    # beschriftete JEDEN Nicht-Extremfall pauschal als "positiv"/"steht NICHT
    # im Konsens" - auch wenn 51-64% long UND die Empfehlung LONG war, also
    # tatsaechlich DIESELBE Richtung wie die (nicht-extreme) Mehrheit. Fix:
    # "Fakt zuerst" - der Text nennt IMMER explizit die Mehrheit und ob die
    # empfohlene Richtung damit uebereinstimmt oder nicht, die Bewertung wird
    # ERST DANACH aus diesem eindeutigen Vergleich abgeleitet (3 Stufen statt
    # einer binären Ja/Nein-Phrase, die falsch sein konnte).
    if long_account_pct is not None:
        mehrheit_ist_long = long_account_pct > 50.0
        richtung_folgt_mehrheit = (
            (richtung == RICHTUNG_LONG and mehrheit_ist_long)
            or (richtung == RICHTUNG_SHORT and not mehrheit_ist_long)
        )
        mehrheits_pct = long_account_pct if mehrheit_ist_long else (100.0 - long_account_pct)
        mehrheits_richtung = "long" if mehrheit_ist_long else "short"
        fakt = (
            f"{long_account_pct:.0f}% der Retail-Konten sind long positioniert "
            f"({mehrheits_pct:.0f}% Mehrheit {mehrheits_richtung}) - Empfehlung ({richtung}) liegt "
            f"{'in derselben Richtung wie' if richtung_folgt_mehrheit else 'entgegen'} der Mehrheit."
        )
        if richtung_folgt_mehrheit and retail_konsens_risiko(retail_long_bias_extreme, long_account_pct, richtung):
            faktoren.append(Risikofaktor(
                f"Retail-Konsens ({long_account_pct:.0f}% long)", "negativ",
                f"{fakt} Extreme Mehrheitspositionierung in dieselbe Richtung - antizyklisch "
                "betrachtet ein Kontraindikator, keine Stütze.",
            ))
        elif richtung_folgt_mehrheit:
            faktoren.append(Risikofaktor(
                f"Retail-Konsens ({long_account_pct:.0f}% long)", "neutral",
                f"{fakt} Nicht extrem genug für einen klaren Kontraindikator, aber auch kein "
                "antizyklischer Pluspunkt.",
            ))
        else:
            faktoren.append(Risikofaktor(
                f"Retail-Konsens ({long_account_pct:.0f}% long)", "positiv",
                f"{fakt} Antizyklisch betrachtet ein unterstützendes Signal.",
            ))

    if confidence_pct is not None:
        if confidence_pct < KONFIDENZ_SCHWELLE_NIEDRIG:
            faktoren.append(Risikofaktor(
                f"Konfidenz {confidence_pct:.0f}%", "negativ", "Niedrige Konfidenz für eine gehebelte Position.",
            ))
        elif confidence_pct >= KONFIDENZ_SCHWELLE_HOCH:
            faktoren.append(Risikofaktor(f"Konfidenz {confidence_pct:.0f}%", "positiv", "Hohe Konfidenz."))
        else:
            faktoren.append(Risikofaktor(f"Konfidenz {confidence_pct:.0f}%", "neutral", "Mittlere Konfidenz."))

    # 2026-07-21, echter BTC-Fund: SYSTEM_PROMPT weist das Modell bereits an, den
    # mitgelieferten Stichprobengroessen-Hinweis von compute_win_rate_fact() zu
    # lesen und bei kleiner Stichprobe nicht zu ueberschaetzen - im echten Fall
    # (n=5) landete dieser Hinweis aber NICHT im freien Gegenargument-Text, nur
    # die nackte 0%-Zahl. Genau das gleiche Prinzip wie bei den uebrigen
    # Risikofaktoren oben (bewusst NICHT vom LLM generiert, siehe Modul-Docstring
    # zum AVAX-Fund): die Stichproben-Warnung gehoert deterministisch in Abschnitt
    # 3, nicht ins Ermessen des jeweiligen LLM-Laufs.
    if historische_erfolgsquote is not None:
        anzahl = historische_erfolgsquote.get("anzahl_ausgewertete_signale")
        quote = historische_erfolgsquote.get("trefferquote_pct")
        if anzahl is not None and anzahl < min_sample_fuer_aussage:
            faktoren.append(Risikofaktor(
                f"Historische Trefferquote {quote:.0f}% (n={anzahl})", "neutral",
                f"Basiert auf nur {anzahl} bisher ausgewerteten Hebel-Signalen - "
                f"statistisch NICHT belastbar (Mindeststichprobe fuer eine "
                f"verlaessliche Aussage: {min_sample_fuer_aussage}). Ernst nehmen, "
                "aber nicht als robusten Beweis werten - gilt zudem fuer den "
                "gesamten Hebel-Track-Record, nicht spezifisch fuer dieses Symbol.",
            ))
        elif quote is not None:
            bewertung = "negativ" if quote < 30 else ("positiv" if quote >= 60 else "neutral")
            faktoren.append(Risikofaktor(
                f"Historische Trefferquote {quote:.0f}% (n={anzahl})", bewertung,
                f"Basiert auf {anzahl} bisher ausgewerteten Hebel-Signalen (gesamter "
                "Track-Record, nicht symbolspezifisch).",
            ))

    # 2026-07-22, echter LINK-Fund (Nutzer-Screenshot): der rohe Funding-Rate-
    # Float wurde bisher unformatiert vom LLM in den Risiken-Text kopiert
    # ("2.624963888888792e-06") - siehe hebel_analyst.py-Fix fuer den
    # LLM-Fakt selbst. Hier zusaetzlich (Fakt zuerst, Wertung danach, gleiches
    # Prinzip wie CRV/Enger-Stop-Loss oben): die Rate MIT Zeiteinheit (Kraken
    # veroeffentlicht Funding stuendlich, siehe hebel_screening.py) UND ein
    # konkreter USD/Tag-Betrag bei der tatsaechlichen Positionsgroesse -
    # letzteres kann/soll das LLM nicht selbst ausrechnen (kein verlaesslicher
    # Taschenrechner), deshalb komplett deterministisch.
    if funding_rate_stunde is not None:
        fakt = f"Ø {funding_rate_stunde * 100:.5f}%/Stunde (Mittelwert letzte 24h)"
        if funding_kosten_usd_pro_tag is not None:
            richtung_hinweis = "zulasten" if funding_kosten_usd_pro_tag >= 0 else "zugunsten"
            fakt += (
                f" - bei aktueller Positionsgröße ca. {abs(funding_kosten_usd_pro_tag):.2f} USD/Tag "
                f"{richtung_hinweis} der Position (schwankt mit dem Satz, keine feste Kostenzusage)."
            )
        ist_hoch = (
            funding_rate_hoch_schwelle_relativ_stunde is not None
            and abs(funding_rate_stunde) >= funding_rate_hoch_schwelle_relativ_stunde
        )
        faktoren.append(Risikofaktor("Funding-Kosten", "negativ" if ist_hoch else "neutral", fakt))

    # Liquiditaetszonen (Marketmaker-Konzept, Stufe 1, 2026-07-23) - rein
    # informativ/neutral, KEIN Deckel (siehe agent/krypto/liquidity_zones.py
    # Modul-Docstring): das Konzept sagt NICHT zwingend "schlecht", sondern
    # "Timing-Vorsicht/moegliches Stop-Hunt-Risiko vor der Bewegung" - deshalb
    # bewusst nie "negativ", unabhaengig von Richtung/Seite.
    if liquiditaetszonen is not None and liquiditaetszonen.get("in_naehe_ungefegter_zone"):
        seite = liquiditaetszonen.get("seite")
        zone = liquiditaetszonen.get(
            "naechste_buyside_zone" if seite == "buyside" else "naechste_sellside_zone"
        ) or {}
        faktoren.append(Risikofaktor(
            f"Nähe zu Liquiditätszone ({seite})", "neutral",
            f"Kurs liegt {zone.get('abstand_prozent')}% von einer noch nicht gefegten "
            f"{'Buy-Side' if seite == 'buyside' else 'Sell-Side'}-Zone entfernt "
            f"({zone.get('touches')} Beruehrungen, zuletzt {zone.get('letzte_beruehrung_datum')}) - "
            "moegliches Stop-Hunt-Risiko vor der eigentlichen Bewegung, kein Richtungsurteil.",
        ))

    return faktoren


def estimate_liquidation_price(
    entry_price: float, hebel: float, richtung: str,
    days_held: float = 0.0, funding_rate_daily_pct: float = 0.18,
    sicherheitsmarge_relativ: float = 0.0,
) -> float:
    """Konservative Schaetzung (Bitpanda veroeffentlicht keine exakte Formel) -
    soll Liquidation eher zu frueh als zu spaet anzeigen (sichere Richtung fuer
    ein Warnsystem). `days_held=0` bei der Empfehlung selbst (Position existiert
    noch nicht, keine Haltedauer zu raten) - `days_held` > 0 nur, sobald eine
    Position real offen ist und die echten verstrichenen Tage bekannt sind.

    2026-07-16 KORRIGIERT: die urspruengliche Formel ignorierte den unbekannten
    Maintenance-Margin-Puffer komplett (Liquidation erst bei Eigenkapital=0) -
    live an einer echten offenen LINK-Position gegengeprueft: Bitpandas
    tatsaechlicher Liquidationspreis lag ca. 7% HOEHER (fuer einen LONG - loest
    frueher aus) als die alte Schaetzung, also GENAU in die falsche, unsichere
    Richtung (weniger statt mehr Sicherheitsabstand als angezeigt). Rueck-
    rechnung aus diesem echten Fall ergab eine implizite Wartungsmarge von
    ~6,5% Eigenkapitalanteil - mit dieser Zahl reproduziert die Formel unten
    (Long, Tag 0) den echten Bitpanda-Wert fast exakt (6,3505 vs. real 6,3515).

    Fix: `sicherheitsmarge_relativ` (config risiko.hebel.liquidations_
    sicherheitsmarge_relativ) wird als Naeherung fuer diese Wartungsmarge auch
    hier eingerechnet, indem der komplette Hebel-Abstand-Term durch (1 -
    sicherheitsmarge_relativ) geteilt wird (Long) bzw. durch (1 +
    sicherheitsmarge_relativ) (Short) - mathematisch hergeleitet aus Eigen-
    kapital(t)/Positionswert(t) = Wartungsmarge bei Liquidation, nicht nur
    eine multiplikative Naeherung.

    2026-07-19 NEU KALIBRIERT (Nutzer-Fund: "Liquidationspreis auf ein
    realistisches Niveau bringen, ist u.U. zu restriktiv"): der bisherige
    Config-Wert (17,5%, "Mittelwert einer 15-20%-Spanne") hatte KEINE echte
    Quelle. Jetzt hergeleitet aus Bitpandas offizieller Doku (Bitpanda
    Helpdesk: Margin Level = Positionswert / Kreditbetrag, Liquidation bei
    Margin Level < ~105-110% - mathematisch aequivalent zu sicherheitsmarge_
    relativ = 1 - 1/Schwelle, also 4,76%-9,09%) UND gegen 4 echte rekonstruierte
    Liquidationsfaelle geprueft (LINK/TAO/TAO/SUI aus der Bitpanda-Transaktions-
    historie, siehe importer/bitpanda_margin_positions.py) - 2 davon (SUI, TAO
    id=87) mit ruhigem statt Crash-Kursverlauf am Schliesstag erlaubten eine
    praezise Rueckrechnung: implizierte Marge 6,75% (SUI) bzw. 8,4% (TAO). Neuer
    Config-Wert 0.09 liegt knapp ueber dem hoechsten real beobachteten Wert -
    bewusst weiterhin ein kleiner Sicherheitspuffer, aber kein 2x-Overkill mehr
    wie die alten 17,5%. Volle Herleitung: Regelwerksmanual.md, Nachtrag
    2026-07-19 "Liquidationspreis-Sicherheitsmarge neu kalibriert".

    Default 0.0 (kein Puffer, altes Verhalten) fuer Rueckwaertskompatibilitaet,
    falls kein Wert uebergeben wird."""
    zeit_faktor = days_held * (funding_rate_daily_pct / 100)
    hebel_abstand = 1 / hebel
    if richtung == RICHTUNG_SHORT:
        return entry_price * (1 + hebel_abstand - zeit_faktor) / (1 + sicherheitsmarge_relativ)
    return entry_price * (1 - hebel_abstand + zeit_faktor) / (1 - sicherheitsmarge_relativ)


def max_safe_hebel(stop_loss_distance_pct: float, sicherheitsmarge_relativ: float) -> float:
    """RM-11: der Hebel muss so gewaehlt sein, dass zwischen Stop-Loss und
    geschaetztem Liquidationspreis ein Sicherheitsabstand bleibt - sonst greift
    Bitpandas Zwangsliquidation, BEVOR der eigene Stop-Loss ueberhaupt ausloesen
    kann. `sicherheitsmarge_relativ` (z.B. 0.175) ist ein relativer Puffer auf
    den reinen 1/Hebel-Abstand, keine additive Prozentzahl."""
    return (1 - sicherheitsmarge_relativ) / (stop_loss_distance_pct / 100)


@dataclass
class HebelPreCheckResult:
    hebel_erlaubt: bool
    veto_reason: str | None
    risikobetrag_usd: float | None
    max_sicherer_hebel: float | None
    config_max_hebel: float
    az7_kontra_deckel_aktiv: bool
    checks: list[str] = field(default_factory=list)


def pre_check_hebel(
    asset, account_equity_usd: float, stop_loss_distance_pct: float | None,
    regime_result, config: dict, trigger_zweig: str | None,
) -> HebelPreCheckResult:
    """Laeuft VOR dem LLM-Call. Berechnet Risikobetrag (RM-1-Aequivalent, 1%
    statt Spot-2%) + maximal sicheren Hebel aus der Stop-Loss-Distanz. AZ-7:
    kompletter Deckel auf 0 bei Extrem-Krise-Regime (gilt fuer BEIDE Zweige),
    zusaetzlicher Konservativ-Faktor NUR bei trigger_zweig == 'kontra' (Sanity-
    Check-Korrektur 2026-07-14 - AZ-7 stammt aus dem antizyklischen Kontext,
    ein bestaetigter Trend ist eine andere Risikokategorie)."""
    checks: list[str] = []
    hebel_cfg = config["risiko"]["hebel"]

    if regime_result.regime == "krise_extrem":
        checks.append("AZ-7: Hebel komplett deaktiviert (Regime krise_extrem)")
        return HebelPreCheckResult(
            hebel_erlaubt=False,
            veto_reason="Hebel im Regime 'krise_extrem' komplett deaktiviert (AZ-7)",
            risikobetrag_usd=None, max_sicherer_hebel=0.0,
            config_max_hebel=hebel_cfg["max_hebel"], az7_kontra_deckel_aktiv=False,
            checks=checks,
        )

    risikobetrag_usd = account_equity_usd * hebel_cfg["risiko_pro_trade_prozent_hebel"] / 100
    checks.append(f"RM-1 (Hebel, {hebel_cfg['risiko_pro_trade_prozent_hebel']}%): Risikobetrag {risikobetrag_usd:.2f} USD")

    max_sicherer_hebel = None
    if stop_loss_distance_pct is not None and stop_loss_distance_pct > 0:
        max_sicherer_hebel = max_safe_hebel(
            stop_loss_distance_pct, hebel_cfg["liquidations_sicherheitsmarge_relativ"],
        )
        az7_kontra_aktiv = trigger_zweig == ZWEIG_KONTRA
        if az7_kontra_aktiv:
            max_sicherer_hebel *= hebel_cfg["kontra_konservativ_faktor"]
            checks.append(
                f"AZ-7-Kontra-Bremse aktiv (Faktor {hebel_cfg['kontra_konservativ_faktor']}): "
                f"max. sicherer Hebel gedaempft auf {max_sicherer_hebel:.2f}x"
            )
        else:
            checks.append(f"RM-11: max. sicherer Hebel {max_sicherer_hebel:.2f}x (Stop-Distanz {stop_loss_distance_pct:.2f}%)")
    else:
        checks.append("RM-11: max. sicherer Hebel nicht berechenbar (keine Stop-Loss-Distanz)")

    return HebelPreCheckResult(
        hebel_erlaubt=True, veto_reason=None, risikobetrag_usd=risikobetrag_usd,
        max_sicherer_hebel=max_sicherer_hebel, config_max_hebel=hebel_cfg["max_hebel"],
        az7_kontra_deckel_aktiv=trigger_zweig == ZWEIG_KONTRA, checks=checks,
    )


def post_check_hebel(
    parsed: dict, pre_result: HebelPreCheckResult, regime_result, config: dict, confluence=None,
    retail_long_bias_extreme: bool | None = None, long_account_pct: float | None = None,
    historische_erfolgsquote: dict | None = None, funding_rate_stunde: float | None = None,
    asset_rolle: str | None = None, liquiditaetszonen: dict | None = None,
    eur_usd_fx_rate: float | None = None,
    position_aktuell=None, kontrathese_verlauf: list | None = None, now_unix: int | None = None,
) -> dict:
    """Nimmt die bereits schema-validierte LLM-Antwort und erzwingt AZ-7/RM-1/
    RM-11/CRV noch einmal deterministisch, analog risk_gate.py::post_check().
    Haengt zusaetzlich die rein deterministisch berechneten Felder an
    (hebel_final, liquidationspreis_geschaetzt, eigenkapitalbedarf,
    ausfuehrbarkeit_hinweis) - die KI sieht/entscheidet diese Werte nicht.

    Nachtrag 2026-07-17 (echter LINK-Fall, siehe Memory
    project_hebel_rahmenbedingungen.md): zwei zusaetzliche Hebel-Deckel neben
    Config-Maximum/RM-11 - Regime-Richtungs-Konflikt (Position widerspricht
    dem Regime, z.B. LONG im baer-Regime) und hohe Gegenszenario-
    Wahrscheinlichkeit (das Modell selbst schaetzt via forecast.bear/bull
    hoch ein, dass sich die Position als falsch herausstellt). Beide rein
    deterministisch, unabhaengig davon ob das Modell das selbst schon
    beruecksichtigt hat.

    Nachtrag 2026-07-18 (echter CAT-Fall, Spot-Pendant): zwei WEITERE Deckel-
    Kandidaten - widerspruechliche technische Konfluenz (`confluence`,
    optional) und CRV knapp am Minimum (`crv`, siehe unten in
    `_hebel_deckel_kandidaten()`).

    Nachtrag 2026-07-19 (echter AVAX-Fund, gemeinsame E-Mail-Durchsicht):
    `retail_long_bias_extreme`/`long_account_pct` (optional, aus
    `AnticyclicContext`) - fuenfter Deckel-Kandidat "Retail-Konsens-Risiko".
    Auslöser: ein Signal begruendete LONG u.a. mit "Retail-Bias extrem long,
    was fuer eine Gegenbewegung spricht" - eine antizyklische Beobachtung, die
    LOGISCH GEGEN die empfohlene Richtung spricht (extreme Mehrheitsposition
    IN einer Richtung ist ein Kontraindikator GEGEN diese Richtung, nicht
    dafuer), aber trotzdem zur Stuetzung von LONG verwendet wurde. Der
    SYSTEM_PROMPT (hebel_analyst.py) wurde entsprechend ergaenzt, aber wie bei
    allen anderen Deckeln gilt: nie blind auf Prompt-Befolgung vertrauen,
    deshalb zusaetzlich hier deterministisch erzwungen.

    Nachtrag 2026-07-22 (echter VIRTUAL-Fund): `asset_rolle` (aus
    `WatchlistAsset.rolle`, "core" fuer BTC/ETH) wird nur fuer den neuen
    "Alt-Coin-Marktphase"-Risikofaktor benoetigt (siehe compute_risikofaktoren_
    hebel()) - `regime_result.btc_matrix_state`/`btc_matrix_beschreibung`
    werden direkt aus `regime_result` gelesen, kein separater Parameter noetig.

    Nachtrag 2026-07-24 (echter NEAR/HYPE-Fund, siehe HebelSignal.
    kontrathese_zu_position-Docstring fuer den vollen Root-Cause): SYSTEM_PROMPT
    Regel 2 (hebel_analyst.py) erlaubt dem LLM bewusst, fuer eine offene
    Position eine Gegenrichtung vorzuschlagen ("ERÖFFNEN SHORT" trotz offener
    LONG-Position) - auf Bitpanda nie als echte Gegenposition ausfuehrbar.
    `position_aktuell` (optional, `database.models.HebelPosition`) macht diesen
    Fall erkennbar; `kontrathese_verlauf` (optional, bereits neueste-zuerst
    sortierte Liste vergangener HebelSignal-Objekte fuer dieselbe Position,
    siehe hebel_pipeline.py) plus `now_unix` erlauben die Zeitfenster-
    Bestaetigung (siehe _kontrathese_bestaetigt_seit_stunden()) - verhindert,
    dass ein einzelner verrauschter 15-Minuten-Ausschlag sofort einen echten
    Trade (TEILVERKAUF/SCHLIESSEN) ausloest. Alle drei Parameter optional und
    wirkungslos, wenn `position_aktuell` None ist (reiner ERÖFFNEN-Fall ohne
    bestehende Position, unveraendertes Verhalten)."""
    result = dict(parsed)
    risk_veto = False
    risk_veto_reason = None
    crv: float | None = None
    sl_abstand_relativ: float | None = None
    positionsgroesse_usd: float | None = None
    action = str(result.get("action", "")).upper()
    richtung = str(result.get("richtung", "")).upper()
    hebel_cfg = config["risiko"]["hebel"]
    kontrathese_zu_position = False
    kontrathese_llm_richtung: str | None = None
    kontrathese_bestaetigt = False
    kontrathese_bestaetigt_seit_stunden: float | None = None

    if not pre_result.hebel_erlaubt:
        risk_veto = True
        risk_veto_reason = pre_result.veto_reason
        action = "HALTEN"
    elif (
        action == "ERÖFFNEN"
        and position_aktuell is not None
        and richtung != str(position_aktuell.richtung).upper()
    ):
        # Kontrathese-Uebersetzung (2026-07-24) - VOR dem CRV-Gate/HEBEL_SENKEN
        # unten, damit eine (fuer die hypothetische Gegenposition ohnehin
        # irrelevante) zu knappe CRV das Remapping nicht ueberschreibt. Greift
        # NUR bei ERÖFFNEN in GENAU der Gegenrichtung zur bestehenden Position -
        # eine echte Kurswende liefe ueber den jeweils ANDEREN (symbol,
        # richtung)-Schluessel und ist hiervon unberuehrt.
        kontrathese_zu_position = True
        kontrathese_llm_richtung = richtung
        confidence_pct = result.get("confidence_pct")
        if confidence_pct is not None and confidence_pct >= KONFIDENZ_SCHWELLE_HOCH:
            # Eindeutiger Alarm - keine Wartezeit, sofortige Reaktion auf die Position.
            action = "SCHLIESSEN"
            kontrathese_bestaetigt = True
        else:
            now_unix_effektiv = now_unix if now_unix is not None else int(datetime.now(timezone.utc).timestamp())
            kontrathese_bestaetigt_seit_stunden = _kontrathese_bestaetigt_seit_stunden(
                kontrathese_verlauf or [], kontrathese_llm_richtung, now_unix_effektiv,
            )
            schwelle_stunden = hebel_cfg.get("kontrathese_bestaetigung_stunden", 2.0)
            if (
                confidence_pct is not None and confidence_pct >= KONFIDENZ_SCHWELLE_NIEDRIG
                and kontrathese_bestaetigt_seit_stunden >= schwelle_stunden
            ):
                action = "TEILVERKAUF"
                kontrathese_bestaetigt = True
            else:
                action = "HALTEN"
        richtung = str(position_aktuell.richtung).upper()
        result["richtung"] = richtung

    def _hebel_deckel_kandidaten(crv: float | None = None) -> list[tuple[str, float]]:
        """Nachtrag 2026-07-17 (echter LINK-Fall): gemeinsame Deckel-Logik fuer
        beide Faelle, die einen Ziel-Hebel brauchen - ERÖFFNEN/NACHKAUFEN/
        HEBEL_ERHÖHEN (mit CRV-Pflicht) UND HEBEL_SENKEN (ohne, siehe unten,
        eine Reduktion braucht keine CRV-Rechtfertigung). `crv` optional -
        HEBEL_SENKEN hat kein CRV-Konzept, uebergibt daher nichts."""
        kandidaten: list[tuple[str, float]] = [("Config-Maximum", pre_result.config_max_hebel)]
        if pre_result.max_sicherer_hebel is not None:
            kandidaten.append(("RM-11 max. sicherer Hebel", pre_result.max_sicherer_hebel))

        regime_konflikt = regime_konflikt_hebel(regime_result.regime, richtung)
        if regime_konflikt:
            kandidaten.append(("Regime-Richtungs-Konflikt", hebel_cfg["regime_konflikt_hebel_deckel"]))

        forecast = result.get("forecast") or {}
        gegenszenario_feld = "bear" if richtung == RICHTUNG_LONG else "bull"
        gegenszenario_pct = (forecast.get(gegenszenario_feld) or {}).get("probability_pct")
        gegenszenario_hoch = (
            gegenszenario_pct is not None
            and gegenszenario_pct >= hebel_cfg["gegenszenario_wahrscheinlichkeit_schwelle_prozent"]
        )
        if gegenszenario_hoch:
            kandidaten.append(
                (f"Gegenszenario-Wahrscheinlichkeit {gegenszenario_pct:.0f}%", hebel_cfg["gegenszenario_hebel_deckel"])
            )

        # Nachtrag 2026-07-18 (echter CAT-Fall, Spot-Pendant siehe risk_gate.py::
        # post_check()): widerspruechliche technische Konfluenz - deterministisch,
        # unabhaengig davon ob das Modell den Widerspruch selbst benennt.
        if confluence is not None and confluence.overall_bias == "gemischt":
            kandidaten.append(("Widerspruechliche technische Konfluenz", hebel_cfg["technischer_konflikt_hebel_deckel"]))

        # Nachtrag 2026-07-18 (gleicher Fund): CRV knapp am Minimum - CRV_MINIMUM
        # war bisher ein binaeres Gate, 2,01 und 4,0 wurden identisch behandelt.
        crv_knapp_schwelle_relativ = hebel_cfg.get("crv_knapp_schwelle_relativ")
        if (
            crv is not None
            and crv_knapp_schwelle_relativ is not None
            and crv < CRV_MINIMUM * (1 + crv_knapp_schwelle_relativ)
        ):
            kandidaten.append((f"CRV knapp am Minimum ({crv:.2f})", hebel_cfg["crv_knapp_hebel_deckel"]))

        # Nachtrag 2026-07-19 (echter AVAX-Fund): Retail-Konsens-Risiko - die
        # empfohlene Richtung stimmt mit der extremen Mehrheitspositionierung
        # der Retail-Trader ueberein, statt (wie antizyklisch korrekt) dagegen
        # zu wetten. Symmetrische Schwelle zu anticyclic.py::
        # LONG_BIAS_EXTREME_THRESHOLD_PCT (65%) - bei SHORT ist die Crowd
        # "im Konsens", wenn <= 35% der Konten long sind (also >= 65% short).
        if retail_konsens_risiko(retail_long_bias_extreme, long_account_pct, richtung):
            kandidaten.append(("Retail-Konsens-Risiko", hebel_cfg["retail_konsens_hebel_deckel"]))

        return kandidaten

    if action == "HEBEL_SENKEN" and pre_result.hebel_erlaubt:
        # Kein CRV/Zonen-Zwang (eine Risikoreduktion braucht keine Chance-
        # Risiko-Rechtfertigung) - trotzdem denselben Sicherheits-Deckel
        # anwenden wie bei ERÖFFNEN, damit hebel_final ueberhaupt gesetzt
        # wird (vorher: HEBEL_SENKEN bekam NIE ein hebel_final, dadurch
        # konnte hebel_pipeline.py auch nie den konkreten Eigenkapital-
        # Nachschuss berechnen).
        hebel_vorschlag = result.get("hebel_vorschlag")
        deckel_kandidaten = _hebel_deckel_kandidaten()
        deckel_werte = [wert for _, wert in deckel_kandidaten]
        hebel_final = min([hebel_vorschlag] + deckel_werte) if hebel_vorschlag is not None else None
        if hebel_final is not None and hebel_vorschlag is not None and hebel_final < hebel_vorschlag:
            bindender_grund, _ = min(deckel_kandidaten, key=lambda paar: paar[1])
            result["hebel_korrektur_hinweis"] = (
                f"KI schlug {hebel_vorschlag:.2f}x vor, auf {hebel_final:.2f}x reduziert "
                f"(bindender Grund: {bindender_grund})."
            )
        else:
            result["hebel_korrektur_hinweis"] = None
        result["hebel_final"] = hebel_final

    if action in _HEBEL_ACTIONS_MIT_HEBEL and pre_result.hebel_erlaubt:
        entry = result.get("entry") or {}
        stop = result.get("stop_loss") or {}
        take = result.get("take_profit") or {}
        entry_von, entry_bis = entry.get("usd_von"), entry.get("usd_bis")
        stop_von, stop_bis = stop.get("usd_von"), stop.get("usd_bis")
        take_von, take_bis = take.get("usd_von"), take.get("usd_bis")

        if None not in (entry_von, entry_bis, stop_von, stop_bis, take_von, take_bis):
            entry_mid = (entry_von + entry_bis) / 2
            # CRV unveraendert 2.0 (Nutzer-Entscheidung 2026-07-14) - Short spiegelbildlich
            if richtung == RICHTUNG_SHORT:
                crv = (entry_mid - take_bis) / (stop_bis - entry_mid) if stop_bis > entry_mid else None
                sl_abstand_relativ = abs(stop_bis - entry_mid) / entry_mid if entry_mid > 0 else None
            else:
                crv = (take_von - entry_mid) / (entry_mid - stop_von) if entry_mid > stop_von else None
                sl_abstand_relativ = abs(entry_mid - stop_von) / entry_mid if entry_mid > 0 else None

            if crv is None or crv < CRV_MINIMUM:
                risk_veto = True
                reason = f"CRV {crv} unter Minimum {CRV_MINIMUM} (unveraendert ggü. Spot)"
                risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
                action = "HALTEN"
            else:
                hebel_vorschlag = result.get("hebel_vorschlag")
                deckel_kandidaten = _hebel_deckel_kandidaten(crv=crv)
                deckel_werte = [wert for _, wert in deckel_kandidaten]
                hebel_final = min([hebel_vorschlag] + deckel_werte) if hebel_vorschlag is not None else None

                if hebel_final is not None and hebel_vorschlag is not None and hebel_final < hebel_vorschlag:
                    bindender_grund, _ = min(deckel_kandidaten, key=lambda paar: paar[1])
                    result["hebel_korrektur_hinweis"] = (
                        f"KI schlug {hebel_vorschlag:.2f}x vor, auf {hebel_final:.2f}x reduziert "
                        f"(bindender Grund: {bindender_grund})."
                    )
                else:
                    result["hebel_korrektur_hinweis"] = None

                result["hebel_final"] = hebel_final
                if hebel_final is not None and hebel_final > 0 and entry_mid > 0:
                    result["liquidationspreis_geschätzt"] = estimate_liquidation_price(
                        entry_mid, hebel_final, richtung,
                        sicherheitsmarge_relativ=config["risiko"]["hebel"]["liquidations_sicherheitsmarge_relativ"],
                    )
                    positionsgroesse_usd = pre_result.risikobetrag_usd / (
                        abs(entry_mid - stop_von) / entry_mid
                    ) if pre_result.risikobetrag_usd and entry_mid != stop_von else None
                    result["eigenkapitalbedarf"] = (
                        positionsgroesse_usd / hebel_final if positionsgroesse_usd is not None else None
                    )
                    # Nachtrag 2026-07-23 (Nutzer-Fund am Signal-Detail-Panel):
                    # Entry/Stop-Loss/Take-Profit werden im selben Panel bereits
                    # in EUR gezeigt - Liquidationspreis/Eigenkapitalbedarf bisher
                    # nur in USD, erzwang eine stille Kopfrechnung. eur_usd_fx_rate
                    # (USD pro EUR, siehe risk_gate.py::pre_check() fuer dieselbe
                    # EURCV-Ableitung) macht die Umrechnung ohne zusaetzlichen
                    # API-Call moeglich.
                    if eur_usd_fx_rate:
                        result["liquidationspreis_geschätzt_eur"] = (
                            result["liquidationspreis_geschätzt"] / eur_usd_fx_rate
                        )
                        result["eigenkapitalbedarf_eur"] = (
                            result["eigenkapitalbedarf"] / eur_usd_fx_rate
                            if result["eigenkapitalbedarf"] is not None else None
                        )
        else:
            risk_veto = True
            reason = "Zonen unvollständig - Hebel-Empfehlung kann nicht sicher berechnet werden"
            risk_veto_reason = f"{risk_veto_reason}; {reason}" if risk_veto_reason else reason
            action = "HALTEN"

    result["ausführbarkeit_hinweis"] = (
        "Aktuell nicht über Bitpanda ausführbar (Short-Positionen werden dort noch nicht unterstützt)."
        if richtung == RICHTUNG_SHORT else None
    )

    result["action"] = action
    result["_risk_veto"] = risk_veto
    result["_risk_veto_reason"] = risk_veto_reason
    result["kontrathese_zu_position"] = kontrathese_zu_position
    result["kontrathese_llm_richtung"] = kontrathese_llm_richtung

    # Risikofaktoren-Liste (2026-07-19, Abschnitt 3 der neuen E-Mail-/App-
    # Struktur) - dieselben Werte wie oben in _hebel_deckel_kandidaten()
    # verwendet, hier nur zur Anzeige zusammengefasst statt zur Hebel-
    # Deckelung. forecast/gegenszenario_pct hier bewusst NEU aus `result`
    # gelesen statt aus der Closure exportiert - _hebel_deckel_kandidaten()
    # bleibt dadurch unveraendert (kein Regressionsrisiko fuer die bereits
    # verifizierte Deckel-Logik).
    forecast = result.get("forecast") or {}
    gegenszenario_feld = "bear" if richtung == RICHTUNG_LONG else "bull"
    gegenszenario_pct = (forecast.get(gegenszenario_feld) or {}).get("probability_pct")

    # 2026-07-22, echter LINK-Fund: konkreter USD/Tag-Betrag aus der bereits
    # oben berechneten Positionsgroesse (positionsgroesse_usd) - Kraken
    # veroeffentlicht Funding stuendlich (siehe hebel_screening.py), daher
    # *24 fuer den Tagessatz. None, falls Positionsgroesse oder Rate fehlen
    # (z.B. HALTEN/HEBEL_SENKEN ohne neue Positionsgroesse).
    funding_kosten_usd_pro_tag = (
        positionsgroesse_usd * funding_rate_stunde * 24
        if positionsgroesse_usd is not None and funding_rate_stunde is not None else None
    )
    risikofaktoren = compute_risikofaktoren_hebel(
        richtung=richtung,
        regime=regime_result.regime,
        confidence_pct=result.get("confidence_pct"),
        crv=crv,
        confluence=confluence,
        gegenszenario_pct=gegenszenario_pct,
        gegenszenario_schwelle=hebel_cfg.get("gegenszenario_wahrscheinlichkeit_schwelle_prozent"),
        crv_knapp_schwelle_relativ=hebel_cfg.get("crv_knapp_schwelle_relativ"),
        retail_long_bias_extreme=retail_long_bias_extreme,
        long_account_pct=long_account_pct,
        trade_thesis_typ=result.get("trade_thesis_typ"),
        hebel_erlaubt=pre_result.hebel_erlaubt,
        veto_reason=pre_result.veto_reason,
        historische_erfolgsquote=historische_erfolgsquote,
        sl_abstand_relativ=sl_abstand_relativ,
        sl_abstand_eng_schwelle_relativ=hebel_cfg.get("sl_abstand_eng_schwelle_relativ"),
        funding_rate_stunde=funding_rate_stunde,
        funding_kosten_usd_pro_tag=funding_kosten_usd_pro_tag,
        funding_rate_hoch_schwelle_relativ_stunde=hebel_cfg.get("funding_rate_hoch_schwelle_relativ_stunde"),
        ist_core_asset=(asset_rolle == "core"),
        btc_matrix_state=regime_result.btc_matrix_state,
        btc_matrix_hinweis=regime_result.btc_matrix_beschreibung,
        liquiditaetszonen=liquiditaetszonen,
        kontrathese_zu_position=kontrathese_zu_position,
        kontrathese_llm_richtung=kontrathese_llm_richtung,
        kontrathese_bestaetigt=kontrathese_bestaetigt,
        kontrathese_bestaetigt_seit_stunden=kontrathese_bestaetigt_seit_stunden,
    )
    result["_risikofaktoren"] = [
        {"name": f.name, "bewertung": f.bewertung, "begruendung": f.begruendung} for f in risikofaktoren
    ]
    return result
