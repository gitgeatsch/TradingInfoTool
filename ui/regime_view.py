"""Regime-Tab (2026-07-17, Nachfolger der Selbstverifikations-Machbarkeits-
Analyse, siehe Basisinfos/Regelwerksmanual.md Kap. 6/11/13). Rein passive
Anzeige des zuletzt bekannten Marktregime-Standes + der Kap.-15-
Kalibrierungsparameter — kein Live-Recompute, kein Netzwerk-Call, keine neue
Entscheidungslogik (P-7 Advisory-only-Prinzip). Konstruktor nimmt bewusst
NUR `db_conn_factory` entgegen, kein LLM-/API-Client noetig."""
from __future__ import annotations

from tkinter import ttk

import config as config_module
import ui.theme as theme
from agent.krypto.regelwerk_parameter import build_parameter_overview
from agent.krypto.regime import get_last_known_regime_status
from ui.row_tooltip import add_row_tooltips
from ui.sortable_tree import make_sortable

_REGIME_LABELS = {
    "krise_extrem": "Krise (extrem)",
    "baer": "Bär",
    "seitwaerts": "Seitwärts",
    "bulle": "Bulle",
    "euphorie_extrem": "Euphorie (extrem)",
}


class RegimeView(ttk.Frame):
    def __init__(self, parent, db_conn_factory):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._param_tooltips: dict[str, str] = {}

        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        status_frame = ttk.Frame(self, padding=8)
        status_frame.pack(fill="x")

        self._stand_label = ttk.Label(status_frame, text="Stand: -", font=("", 9, "bold"))
        self._stand_label.pack(anchor="w")
        self._regime_label = ttk.Label(status_frame, text="Regime: -", font=("", 12, "bold"))
        self._regime_label.pack(anchor="w", pady=(4, 0))
        self._reason_label = ttk.Label(status_frame, text="", wraplength=760, justify="left")
        self._reason_label.pack(anchor="w")

        self._detail_labels: dict[str, ttk.Label] = {}
        for key in ("btc_trend", "fear_greed", "dominanz", "zyklus_risiko", "liquiditaet"):
            lbl = ttk.Label(status_frame, text="", wraplength=760, justify="left")
            lbl.pack(anchor="w")
            self._detail_labels[key] = lbl

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=8, pady=6)

        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill="both", expand=True)
        ttk.Label(
            bottom, text="Parameter-Übersicht (Regelwerksmanual Kap. 15 — Mouseover für Begründung/Datum)",
            font=("", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        tree_frame = ttk.Frame(bottom)
        tree_frame.pack(fill="both", expand=True)

        columns = ("bezeichnung", "wert", "kategorie")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        headings = {"bezeichnung": "Bezeichnung", "wert": "Wert", "kategorie": "Kategorie"}
        widths = {"bezeichnung": 320, "wert": 220, "kategorie": 200}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self._reapply_sort = make_sortable(self.tree)
        add_row_tooltips(self.tree, lambda iid: self._param_tooltips.get(iid))

    def refresh(self) -> None:
        conn = self._db_conn_factory()
        try:
            regime_status = get_last_known_regime_status(conn)
        finally:
            conn.close()
        parameter_rows = build_parameter_overview(config_module.load_config())

        self._render_regime_status(regime_status)
        self._render_parameter_overview(parameter_rows)

    def _render_regime_status(self, status: dict | None) -> None:
        if status is None:
            self._stand_label.config(text="Stand: noch kein Signal vorhanden")
            self._regime_label.config(text="Regime: -", foreground=theme.default_text_color())
            self._reason_label.config(text="")
            for lbl in self._detail_labels.values():
                lbl.config(text="")
            return

        created_at = status.get("created_at")
        stand = created_at[:16].replace("T", " ") if created_at else "-"
        self._stand_label.config(text=f"Stand: {stand}")

        regime = status["regime"]
        label = _REGIME_LABELS.get(regime, regime)
        self._regime_label.config(text=f"Regime: {label}", foreground=theme.regime_color(regime))

        if status.get("regime_source") == "manuell":
            self._reason_label.config(text="⚠ manuell überschrieben")
        else:
            self._reason_label.config(text=status.get("regime_reason") or "")

        btc_trend = status.get("btc_trend_label") or "nicht verfügbar"
        self._detail_labels["btc_trend"].config(text=f"BTC-Trend: {btc_trend}")

        fg_label = status.get("fear_greed_label")
        fg_value = status.get("fear_greed_value")
        fg_text = f"{fg_label} ({fg_value})" if fg_label else "nicht verfügbar"
        self._detail_labels["fear_greed"].config(text=f"Fear & Greed: {fg_text}")

        dominanz = status.get("dominance_trend_label") or "nicht verfügbar"
        self._detail_labels["dominanz"].config(text=f"BTC-Dominanz-Trend: {dominanz}")

        zyklus_risiko = status.get("zyklus_risiko")
        zyklus_text = f"{zyklus_risiko:.2f}" if zyklus_risiko is not None else "nicht verfügbar"
        zyklus_begruendung = status.get("zyklus_risiko_begruendung")
        if zyklus_begruendung:
            zyklus_text += f" — {zyklus_begruendung}"
        self._detail_labels["zyklus_risiko"].config(text=f"Zyklus-Risiko: {zyklus_text}")

        liquiditaet = status.get("liquiditaets_regime") or "nicht verfügbar"
        liquiditaet_begruendung = status.get("liquiditaets_regime_begruendung")
        if liquiditaet_begruendung:
            liquiditaet += f" — {liquiditaet_begruendung}"
        self._detail_labels["liquiditaet"].config(text=f"Liquiditätsregime: {liquiditaet}")

    def _render_parameter_overview(self, rows: list[dict]) -> None:
        self.tree.delete(*self.tree.get_children())
        self._param_tooltips.clear()
        for i, row in enumerate(rows):
            iid = f"param_{i}"
            self.tree.insert("", "end", iid=iid, values=(row["bezeichnung"], row["wert"], row["kategorie"]))
            geaendert = row["geaendert_am"] or "kein Datum vermerkt"
            self._param_tooltips[iid] = f"{row['begruendung']} (zuletzt geändert: {geaendert})"
        theme.restripe_treeview(self.tree)
        self._reapply_sort()
