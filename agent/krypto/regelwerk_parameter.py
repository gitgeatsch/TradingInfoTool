"""Parameter-Übersicht (2026-07-17, Regime-Status+Parameter-Übersicht) — reine
Anzeige der in Basisinfos/Regelwerksmanual.md Kap. 15 ("Offene/vorläufige Werte")
dokumentierten Kalibrierungs-Parameter mit ihrem AKTUELL in config.yaml
konfigurierten Wert. Rein lesend (P-7 Advisory-only), keine neue Logik, keine
Änderung an Live-Verhalten — nur Sichtbarkeit dessen, was ohnehin schon in
config.yaml steht.

Kategorie a/b/c: die Einordnung aus der Machbarkeits-Analyse (2026-07-17,
Plandatei swift-napping-muffin) — a) reine technische/betriebliche
Kalibrierung, b) Risikotoleranz-/Werte-Parameter (nie automatisch anzupassen,
unabhängig von Datenlage), c) gemischt/komplex (technischer Kern, aber
spürbare Risiko-Wirkung). Das ist eine Ausgangsbasis, KEINE abschließende
Antwort — die Governance-Frage (was darf sich wie anpassen) ist bewusst
weiterhin offen.

`begruendung`/`geaendert_am` sind manuell aus den config.yaml-Inline-
Kommentaren transkribiert (yaml.safe_load() liefert keine Kommentare mit) —
muss beim inhaltlichen Ändern eines Wertes in config.yaml von Hand
nachgezogen werden, siehe Pflegehinweis in der Plandatei."""
from __future__ import annotations

KATEGORIE_A = "a) technische Kalibrierung"
KATEGORIE_B = "b) Risikotoleranz/Werte"
KATEGORIE_C = "c) gemischt/komplex"

_REGIME_REIHENFOLGE = ("krise_extrem", "baer", "seitwaerts", "bulle", "euphorie_extrem")

# Jeder Eintrag: bezeichnung, kategorie, begruendung, geaendert_am, und entweder
# `pfad` (Tupel von Schlüsseln in config.yaml) oder `regime_feld` (Feldname
# innerhalb von regime.profile.<regime>.*, Wert wird über alle 5 Regime-Profile
# zusammengefasst) oder `code_konstante` (liest aus risk_gate.py statt config.yaml).
_PARAMETER: tuple[dict, ...] = (
    {
        "bezeichnung": "RM-2 Core-Allokations-Limit",
        "pfad": ("risiko", "max_allokation_pro_core_asset_prozent"),
        "kategorie": KATEGORIE_B,
        "begruendung": "Vorläufig, 2026-07-07 entschieden.",
        "geaendert_am": "2026-07-07",
    },
    {
        "bezeichnung": "RM-2 Allokations-Limit (taktisch)",
        "pfad": ("risiko", "max_allokation_pro_asset_prozent"),
        "kategorie": KATEGORIE_B,
        "begruendung": "RM-2: für rolle=taktisch.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "RM-4 Cash-Reserve-Minimum (%)",
        "pfad": ("risiko", "cash_reserve_min_prozent"),
        "kategorie": KATEGORIE_B,
        "begruendung": "[OFFEN] Vorschlag.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "RM-4 Cash-Reserve-Minimum (Festbetrag)",
        "pfad": ("risiko", "cash_reserve_min_fixed_eur"),
        "kategorie": KATEGORIE_B,
        "begruendung": "[OFFEN] Vorschlag - Hybrid-Formel (Prozent + Festbetrag).",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Small-Cap-Budget je Regime",
        "regime_feld": "small_cap_budget_prozent",
        "kategorie": KATEGORIE_B,
        "begruendung": "Anteil des Portfolios für Small-Caps, je Marktregime.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Mindest-Konfidenz je Regime",
        "regime_feld": "min_konfidenz_prozent",
        "kategorie": KATEGORIE_C,
        "begruendung": "R-5.10 - unterhalb dieser KI-Konfidenz wird ein Signal auf HALTEN gedämpft.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Regime-Gewicht: Technik",
        "regime_feld": "gewicht_technik",
        "kategorie": KATEGORIE_A,
        "begruendung": "Gewichtung der technischen Analyse in der Gesamtbewertung, je Regime.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Regime-Gewicht: Fundamental",
        "regime_feld": "gewicht_fundamental",
        "kategorie": KATEGORIE_A,
        "begruendung": "Gewichtung der Fundamentaldaten in der Gesamtbewertung, je Regime.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Regime-Gewicht: Momentum",
        "regime_feld": "gewicht_momentum",
        "kategorie": KATEGORIE_A,
        "begruendung": "Gewichtung des Momentums in der Gesamtbewertung, je Regime.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Regime-Gewicht: Makro/Kontext",
        "regime_feld": "gewicht_kontext_makro",
        "kategorie": KATEGORIE_A,
        "begruendung": "Gewichtung des Makro-Kontexts in der Gesamtbewertung, je Regime.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "RG-4 Makro-Multiplikator (risikoappetit_faktor)",
        "pfad": ("regime", "risikoappetit_faktor"),
        "kategorie": KATEGORIE_B,
        "begruendung": "[OFFEN] globaler Makro-Multiplikator, Spanne 0.3-1.0, aktuell fix auf 1.0.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "RM-10 maximaler Hebel",
        "pfad": ("risiko", "hebel", "max_hebel"),
        "kategorie": KATEGORIE_C,
        "begruendung": "Kalibriert gegen echte Bitpanda-Margin-Historie.",
        "geaendert_am": "2026-07-14",
    },
    {
        "bezeichnung": "Liquidations-Sicherheitsmarge",
        "pfad": ("risiko", "hebel", "liquidations_sicherheitsmarge_relativ"),
        "kategorie": KATEGORIE_C,
        "begruendung": "RM-11, Mittelwert der 15-20%-Spanne, [OFFEN].",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Hebel-Trigger: Open-Interest-Änderung",
        "pfad": ("hebel_screening", "trendfolge", "oi_aenderung_schwelle_prozent"),
        "kategorie": KATEGORIE_A,
        "begruendung": "[OFFEN] Platzhalter, keine OI-Historie zum Kalibrieren vorhanden.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Hebel-Trigger: Kursänderung",
        "pfad": ("hebel_screening", "trendfolge", "kursaenderung_schwelle_prozent"),
        "kategorie": KATEGORIE_A,
        "begruendung": "[OFFEN] angelehnt an das Marktscan-Muster.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Hebel-Trigger: Long-Bias oben",
        "pfad": ("hebel_screening", "kontra", "long_bias_extrem_oben_prozent"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Angehoben von anticyclic.py's 65%.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Hebel-Trigger: Long-Bias unten",
        "pfad": ("hebel_screening", "kontra", "long_bias_extrem_unten_prozent"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Spiegelwert zum oberen Long-Bias-Schwellenwert.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Boden-Zielzone: Reifegrad-Dämpfer",
        "pfad": ("boden_zielzone", "reifegrad_daempfer_staerke"),
        "kategorie": KATEGORIE_A,
        "begruendung": "[OFFEN] 0-1: zieht die historische Abweichungs-Bandkante zusammen.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Boden-Zielzone: Aktien-Bärenmarkt-Schwelle",
        "pfad": ("boden_zielzone", "equities_baermarkt_schwelle_prozent"),
        "kategorie": KATEGORIE_A,
        "begruendung": "[OFFEN] Drawdown vom trailing-Lookback-ATH, ab dem der Aktien-Overlay greift.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Boden-Zielzone: Bärenmarkt-Lookback (Jahre)",
        "pfad": ("boden_zielzone", "equities_baermarkt_lookback_jahre"),
        "kategorie": KATEGORIE_A,
        "begruendung": "[OFFEN] Zeitfenster für das Allzeithoch der Drawdown-Berechnung.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Boden-Zielzone: Overlay-Shift",
        "pfad": ("boden_zielzone", "equities_overlay_shift_std"),
        "kategorie": KATEGORIE_A,
        "begruendung": "[OFFEN] zusätzliche Vertiefung der Zielzone in Standardabweichungen.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Cooldown: Spot-Rotation",
        "pfad": ("budget_allocator", "spot_cooldown_stunden"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Fix nach einem echten Notebook-Vorfall (zu häufige Rotation ohne Cooldown).",
        "geaendert_am": "2026-07-15",
    },
    {
        "bezeichnung": "Cooldown: Spot-Rotation, Kern-Assets",
        "pfad": ("budget_allocator", "spot_cooldown_stunden_kern"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Zwei-Stufen-Cooldown - kürzerer Cooldown für rolle=core.",
        "geaendert_am": "2026-07-16",
    },
    {
        "bezeichnung": "Cooldown: Spot, ausgemustert",
        "pfad": ("budget_allocator", "spot_cooldown_stunden_ausgemustert"),
        "kategorie": KATEGORIE_A,
        "begruendung": "[OFFEN]/vorläufig, dritte Cooldown-Stufe (Klassifikations-Redesign).",
        "geaendert_am": "2026-07-16",
    },
    {
        "bezeichnung": "Cooldown: Hebel, ausgemustert",
        "pfad": ("budget_allocator", "hebel_cooldown_stunden_ausgemustert"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Analog zur Spot-Stufe, für Hebel-Trigger-Kandidaten.",
        "geaendert_am": "2026-07-16",
    },
    {
        "bezeichnung": "Cooldown: Hebel-Position (offen)",
        "pfad": ("budget_allocator", "hebel_position_cooldown_stunden"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Enger Cooldown für bereits getätigte, noch offene Hebel-Positionen.",
        "geaendert_am": "2026-07-16",
    },
    {
        "bezeichnung": "Backward-Tracking: Ablauf-Frist (Tage)",
        "pfad": ("backward_tracking", "abgelaufen_nach_tagen"),
        "kategorie": KATEGORIE_A,
        "begruendung": "[OFFEN] Vorschlag - ab wann ein unentschiedenes KAUFEN/NACHKAUFEN-Signal als abgelaufen gilt.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Z-2 Mindest-CRV (CRV_MINIMUM)",
        "code_konstante": "CRV_MINIMUM",
        "kategorie": KATEGORIE_C,
        "begruendung": "Code-Konstante in agent/krypto/risk_gate.py, nicht in config.yaml - Z-2.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Stop-Loss-ATR-Multiplikator",
        "code_konstante": "STOP_LOSS_ATR_MULTIPLE",
        "kategorie": KATEGORIE_A,
        "begruendung": "Code-Konstante in agent/krypto/risk_gate.py, nicht in config.yaml - Arbeits-Konvention, nicht spezifikationsseitig vorgegeben.",
        "geaendert_am": None,
    },
    {
        "bezeichnung": "Hedge: max. Abdeckungsanteil",
        "pfad": ("hedge", "max_abdeckung_anteil"),
        "kategorie": KATEGORIE_B,
        "begruendung": "Obergrenze relativ zur ungesicherten Long-Exposure, volle Abdeckung nur bei baer/krise_extrem gerechtfertigt.",
        "geaendert_am": "2026-07-18",
    },
    {
        "bezeichnung": "Hedge: Bull-Wahrscheinlichkeit-Schwelle",
        "pfad": ("hedge", "bull_wahrscheinlichkeit_schwelle_prozent"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Spiegelverkehrtes Pendant zum Gegenszenario-Deckel - Hedge-Risiko ist hohe Bull- statt Bear-Wahrscheinlichkeit (Decay). [OFFEN], unkalibrierter Startwert.",
        "geaendert_am": "2026-07-18",
    },
    {
        "bezeichnung": "Hedge: Bull-Wahrscheinlichkeit-Deckel-Anteil",
        "pfad": ("hedge", "bull_wahrscheinlichkeit_deckel_anteil"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Positionsgroessen-Reduktion bei ueberschrittener Bull-Schwelle.",
        "geaendert_am": "2026-07-18",
    },
    {
        "bezeichnung": "Multi-Asset-Batch: Cooldown gehalten (Std.)",
        "pfad": ("multi_asset_batch", "cooldown_stunden_gehalten"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Aktien/Rohstoffe/Hedge/Themen-ETF, gehaltene Positionen - taeglich neu pruefen.",
        "geaendert_am": "2026-07-18",
    },
    {
        "bezeichnung": "Multi-Asset-Batch: Cooldown beobachtet (Std.)",
        "pfad": ("multi_asset_batch", "cooldown_stunden_beobachtet"),
        "kategorie": KATEGORIE_A,
        "begruendung": "Reine Beobachtungs-Kandidaten, deutlich traeger als Krypto (Boersenzeiten/Wochenenden).",
        "geaendert_am": "2026-07-18",
    },
)


def _resolve_pfad(config: dict, pfad: tuple[str, ...]):
    wert = config
    for schluessel in pfad:
        if not isinstance(wert, dict) or schluessel not in wert:
            return None
        wert = wert[schluessel]
    return wert


def _resolve_regime_feld(config: dict, feld: str) -> str:
    profile = config.get("regime", {}).get("profile", {})
    werte = [profile.get(regime, {}).get(feld) for regime in _REGIME_REIHENFOLGE]
    if all(w is None for w in werte):
        return "nicht verfügbar"
    return "/".join("-" if w is None else str(w) for w in werte) + " (krise/bär/seitwärts/bulle/euphorie)"


def _resolve_code_konstante(name: str):
    from agent.krypto.risk_gate import CRV_MINIMUM, STOP_LOSS_ATR_MULTIPLE

    return {"CRV_MINIMUM": CRV_MINIMUM, "STOP_LOSS_ATR_MULTIPLE": STOP_LOSS_ATR_MULTIPLE}[name]


def build_parameter_overview(config: dict) -> list[dict]:
    """Liest den aktuellen Wert jedes Kap.-15-Parameters live aus `config`
    (bzw. aus den risk_gate.py-Konstanten) - Bezeichnung/Kategorie/Begründung/
    Änderungsdatum kommen aus der statischen Liste oben. Reine Lesefunktion,
    kein Seiteneffekt.

    Nach Kategorie sortiert (stabil - Reihenfolge innerhalb einer Kategorie
    bleibt wie in `_PARAMETER`) - Konsumenten (Remote-Seite, Desktop-Tab)
    gruppieren beim Anzeigen nach aufeinanderfolgender Kategorie, das setzt
    eine bereits sortierte Liste voraus."""
    ergebnis = []
    for eintrag in _PARAMETER:
        if "pfad" in eintrag:
            wert = _resolve_pfad(config, eintrag["pfad"])
        elif "regime_feld" in eintrag:
            wert = _resolve_regime_feld(config, eintrag["regime_feld"])
        else:
            wert = _resolve_code_konstante(eintrag["code_konstante"])
        ergebnis.append({
            "bezeichnung": eintrag["bezeichnung"],
            "wert": wert,
            "kategorie": eintrag["kategorie"],
            "begruendung": eintrag["begruendung"],
            "geaendert_am": eintrag["geaendert_am"],
        })
    ergebnis.sort(key=lambda r: r["kategorie"])
    return ergebnis
