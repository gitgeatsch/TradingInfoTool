"""Schwerpunkte-Tab (2026-07-20, Release 2 der Kategorie-Taxonomie, Task #332 -
siehe Basisinfos/Kategorie_Basisinformationen_Release2.md Abschnitt 5) - reine
CRUD-/Statuswechsel-Verwaltung fuer database/models.py::These. Bewusst KEINE
automatische Bewertung/Sortierung/Hervorhebung hier (das ist Task #343 -
Screener/Diversifikations-Marker - und Task #334 - Marktscan-Bias). Setzt das
vom Nutzer bestaetigte Transparenz-Prinzip um (2026-07-19: "die Punkte muessen
fuer den User transparent sein also minimum an Interpretation erforderlich") -
der review_am-Vorschlag zeigt IMMER seine Begruendung sichtbar neben dem Feld,
nie eine stille, unerklaerte Vorbelegung.

Eigener, lokaler Kategorie-Selector (`_build_these_kategorie_selector()`) statt
Wiederverwendung von `ui.app._build_kategorie_selector()`: eine These kann sich
auf eine GANZE Hauptgruppe beziehen (Unterkategorie optional, anders als beim
Asset-Dialog, wo eine leere Unterkategorie "kein Schwerpunkt" bedeutet) - UND
eine Wiederverwendung wuerde ohnehin einen Zirkel-Import ui.app <-> ui.thesen_view
erzeugen (ui.app importiert die Tabs, nicht umgekehrt)."""
from __future__ import annotations

import dataclasses
import tkinter as tk
from datetime import date, datetime, timedelta, timezone
from tkinter import messagebox, ttk

import config as config_module
import database.db as db
import ui.theme as theme
from database.models import These
from ui.row_tooltip import add_row_tooltips
from ui.sortable_tree import make_sortable
from ui.widget_tooltip import add_widget_tooltip

_GESAMTE_HAUPTGRUPPE = "(gesamte Hauptgruppe)"

_RICHTUNG_LABELS_STANDARD = {"uebergewichten": "Übergewichten", "neutral": "Neutral", "meiden": "Meiden"}
_RICHTUNG_LABELS_ABSICHERUNG = {"aktiv": "Aktiv", "inaktiv": "Inaktiv"}

_MECHANISMUS_LABELS = {
    "m2_liquiditaet": "M2-Liquidität",
    "cot_positionierung": "CFTC-COT-Positionierung",
    "zinskurve": "Zinskurve (10J minus 2J)",
    "dollar_index": "Dollar-Index-Trend (DXY, 12 Monate)",
    "baerenmarkt_overlay": "Bärenmarkt-Overlay",
}

_STATUS_LABELS = {"aktiv": "Aktiv", "erledigt": "Erledigt", "verworfen": "Verworfen"}


def _richtung_optionen(hauptgruppe_id: str | None) -> dict[str, str]:
    if hauptgruppe_id == "absicherung":
        return _RICHTUNG_LABELS_ABSICHERUNG
    return _RICHTUNG_LABELS_STANDARD


def _mechanismus_label(mechanismus: str | None) -> str:
    """Nimmt einen (moeglicherweise komma-getrennten, 2026-07-24 #333 Multi-
    Indikator-Design) Mechanismus-String entgegen - `These.pruef_mechanismus`
    speichert mehrere Mechanismen als "m2_liquiditaet,cot_positionierung"."""
    if not mechanismus:
        return "kein automatischer Check"
    teile = [t.strip() for t in mechanismus.split(",") if t.strip()]
    return " + ".join(_MECHANISMUS_LABELS.get(t, t) for t in teile)


def _kategorie_anzeige(hauptgruppe_name: str, unterkategorie_name: str | None) -> str:
    if unterkategorie_name is None:
        return f"{hauptgruppe_name} (gesamte Hauptgruppe)"
    return f"{hauptgruppe_name} / {unterkategorie_name}"


def _build_these_kategorie_selector(frame, row: int, initial_hauptgruppe: str | None = None,
                                     initial_unterkategorie: str | None = None):
    """Zwei kaskadierende Comboboxen wie `ui.app._build_kategorie_selector()`,
    aber mit zwei Unterschieden: Hauptgruppe ist PFLICHT (eine These ohne
    Kategorie-Bezug ergibt keinen Sinn) und Unterkategorie ist optional ueber
    die erste Option `_GESAMTE_HAUPTGRUPPE` waehlbar. Zeigt zusaetzlich, dem
    Transparenz-Prinzip folgend, live eine Liste aller Unterkategorien, die
    unter der gewaehlten Hauptgruppe konsolidiert werden (Nutzer-Entscheidung
    #1: "vor allem sollte klar sein was unter den Hauptkategorien konsolidiert
    wird"). Gibt `get_ids()` zurueck: `(hauptgruppe_id, unterkategorie_id|None)`
    oder `(None, None)` solange keine Hauptgruppe gewaehlt ist."""
    kategorien = config_module.get_kategorien()
    hauptgruppen = kategorien["hauptgruppen"]
    hg_name_to_id = {hg["name"]: hg["id"] for hg in hauptgruppen}
    hg_id_to_obj = {hg["id"]: hg for hg in hauptgruppen}

    hauptgruppe_var = tk.StringVar()
    unterkategorie_var = tk.StringVar()

    ttk.Label(frame, text="Hauptgruppe").grid(row=row, column=0, sticky="w", pady=2)
    hg_combo = ttk.Combobox(
        frame, textvariable=hauptgruppe_var, state="readonly", width=32,
        values=[hg["name"] for hg in hauptgruppen],
    )
    hg_combo.grid(row=row, column=1, sticky="w", pady=2, padx=(8, 0))

    ttk.Label(frame, text="Unterkategorie").grid(row=row + 1, column=0, sticky="w", pady=2)
    uk_combo = ttk.Combobox(frame, textvariable=unterkategorie_var, state="readonly", width=32, values=[])
    uk_combo.grid(row=row + 1, column=1, sticky="w", pady=2, padx=(8, 0))

    konsolidiert_label = ttk.Label(frame, text="", wraplength=420, justify="left", foreground=theme.info_color())
    konsolidiert_label.grid(row=row + 2, column=0, columnspan=2, sticky="w", pady=(0, 4))

    def _on_hauptgruppe_changed(event=None) -> None:
        hg_name = hauptgruppe_var.get()
        hg_obj = hg_id_to_obj.get(hg_name_to_id.get(hg_name))
        uk_names = [uk["name"] for uk in hg_obj["unterkategorien"]] if hg_obj else []
        uk_combo.config(values=[_GESAMTE_HAUPTGRUPPE] + uk_names)
        if unterkategorie_var.get() not in uk_names:
            unterkategorie_var.set(_GESAMTE_HAUPTGRUPPE)
        if hg_obj:
            konsolidiert_label.config(
                text="Umfasst Unterkategorien: " + ", ".join(uk_names) if uk_names else
                "Diese Hauptgruppe hat keine Unterkategorien."
            )
        else:
            konsolidiert_label.config(text="")
        _on_selection_changed()

    hg_combo.bind("<<ComboboxSelected>>", _on_hauptgruppe_changed)
    uk_combo.bind("<<ComboboxSelected>>", lambda _e: _on_selection_changed())

    on_change_callback = {"fn": None}

    def set_on_change(fn) -> None:
        on_change_callback["fn"] = fn

    def _on_selection_changed() -> None:
        if on_change_callback["fn"] is not None:
            on_change_callback["fn"]()

    hg_obj = hg_id_to_obj.get(initial_hauptgruppe) if initial_hauptgruppe else None
    if hg_obj is not None:
        hauptgruppe_var.set(hg_obj["name"])
        _on_hauptgruppe_changed()
        if initial_unterkategorie:
            uk_obj = next((uk for uk in hg_obj["unterkategorien"] if uk["id"] == initial_unterkategorie), None)
            if uk_obj is not None:
                unterkategorie_var.set(uk_obj["name"])

    def get_ids() -> tuple[str | None, str | None]:
        hg_name = hauptgruppe_var.get()
        hg_id = hg_name_to_id.get(hg_name)
        hg_obj = hg_id_to_obj.get(hg_id)
        if hg_id is None or hg_obj is None:
            return None, None
        uk_name = unterkategorie_var.get()
        if not uk_name or uk_name == _GESAMTE_HAUPTGRUPPE:
            return hg_id, None
        uk_obj = next((uk for uk in hg_obj["unterkategorien"] if uk["name"] == uk_name), None)
        return hg_id, (uk_obj["id"] if uk_obj else None)

    return get_ids, hauptgruppe_var, set_on_change


class TheseDialog(tk.Toplevel):
    """Neu-anlegen (`existing=None`) oder Bearbeiten (`existing` gesetzt) einer
    These. Status/Quelle/gesetzt_am werden hier NICHT editiert (Status laeuft
    ueber die Listen-Buttons in `ThesenView`, analog `set_hebel_pruefung_erlaubt()`-
    Mustern - eine neue These startet immer 'aktiv'/'manuell', `gesetzt_am` bleibt
    beim Bearbeiten unveraendert)."""

    def __init__(self, parent, existing: These | None, on_saved) -> None:
        super().__init__(parent)
        self._existing = existing
        self._on_saved = on_saved
        self.title("These bearbeiten" if existing else "Neue These")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)

        self._get_kategorie_ids, hauptgruppe_var, set_on_change = _build_these_kategorie_selector(
            frame, row=0,
            initial_hauptgruppe=existing.hauptgruppe if existing else None,
            initial_unterkategorie=existing.unterkategorie if existing else None,
        )
        self._hauptgruppe_var = hauptgruppe_var

        row = 3
        ttk.Label(frame, text="Richtung").grid(row=row, column=0, sticky="w", pady=2)
        self._richtung_var = tk.StringVar()
        self._richtung_combo = ttk.Combobox(frame, textvariable=self._richtung_var, state="readonly", width=20)
        self._richtung_combo.grid(row=row, column=1, sticky="w", pady=2, padx=(8, 0))
        row += 1

        ttk.Label(frame, text="Stärke (1-5, optional)").grid(row=row, column=0, sticky="w", pady=2)
        self._staerke_var = tk.StringVar(value=str(existing.staerke) if existing and existing.staerke else "(keine)")
        ttk.Combobox(
            frame, textvariable=self._staerke_var, state="readonly", width=10,
            values=["(keine)", "1", "2", "3", "4", "5"],
        ).grid(row=row, column=1, sticky="w", pady=2, padx=(8, 0))
        row += 1

        ttk.Label(frame, text="Begründung").grid(row=row, column=0, sticky="nw", pady=2)
        self._begruendung_text = tk.Text(frame, width=40, height=5, wrap="word")
        self._begruendung_text.grid(row=row, column=1, sticky="w", pady=2, padx=(8, 0))
        if existing:
            self._begruendung_text.insert("1.0", existing.begruendung)
        row += 1

        ttk.Label(frame, text="Objektiver Prüf-Mechanismus").grid(row=row, column=0, sticky="w", pady=(10, 2))
        self._mechanismus_label = ttk.Label(frame, text="-", wraplength=280, justify="left")
        self._mechanismus_label.grid(row=row, column=1, sticky="w", pady=(10, 2), padx=(8, 0))
        row += 1

        ttk.Label(frame, text="Wiedervorlage (review_am)").grid(row=row, column=0, sticky="w", pady=2)
        self._review_am_var = tk.StringVar(value=existing.review_am if existing and existing.review_am else "")
        ttk.Entry(frame, textvariable=self._review_am_var, width=14).grid(
            row=row, column=1, sticky="w", pady=2, padx=(8, 0)
        )
        row += 1
        self._review_begruendung_label = ttk.Label(
            frame, text="", wraplength=420, justify="left", foreground=theme.info_color(),
        )
        self._review_begruendung_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))
        row += 1

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(button_frame, text="Abbrechen", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(button_frame, text="Speichern", command=self._on_submit).pack(side="right")

        set_on_change(self._on_kategorie_changed)
        self._on_kategorie_changed(initial_richtung=existing.richtung if existing else None)

    def _on_kategorie_changed(self, initial_richtung: str | None = None) -> None:
        hg_id, uk_id = self._get_kategorie_ids()
        optionen = _richtung_optionen(hg_id)
        self._richtung_combo.config(values=list(optionen.values()))
        if initial_richtung and initial_richtung in optionen:
            self._richtung_var.set(optionen[initial_richtung])
        elif self._richtung_var.get() not in optionen.values():
            self._richtung_var.set(next(iter(optionen.values())))

        mechanismus_info = config_module.get_pruef_mechanismus(hg_id, uk_id) if hg_id else None
        if mechanismus_info is None:
            self._mechanismus_label.config(text="kein automatischer Check für diese Kategorie hinterlegt")
            self._review_begruendung_label.config(
                text="Kein automatischer Vorschlag für diese Kategorie - review_am bleibt frei wählbar."
            )
        else:
            self._mechanismus_label.config(text=_mechanismus_label(",".join(mechanismus_info["mechanismen"])))
            tage = mechanismus_info["review_tage_vorschlag"]
            begruendung = mechanismus_info["review_begruendung"]
            if tage is None:
                self._review_begruendung_label.config(text=f"Kein festes Intervall - {begruendung}")
            else:
                vorschlag = (date.today() + timedelta(days=tage)).isoformat()
                self._review_begruendung_label.config(
                    text=f"Vorschlag: {vorschlag} (heute + {tage} Tage) - {begruendung}"
                )
                if not self._existing and not self._review_am_var.get():
                    self._review_am_var.set(vorschlag)

    def _on_submit(self) -> None:
        hg_id, uk_id = self._get_kategorie_ids()
        if hg_id is None:
            messagebox.showwarning("These speichern", "Bitte eine Hauptgruppe auswählen.")
            return

        richtung_label = self._richtung_var.get()
        optionen = _richtung_optionen(hg_id)
        richtung_id = next((k for k, v in optionen.items() if v == richtung_label), None)
        if richtung_id is None:
            messagebox.showwarning("These speichern", "Bitte eine Richtung auswählen.")
            return

        begruendung = self._begruendung_text.get("1.0", "end").strip()
        if not begruendung:
            messagebox.showwarning("These speichern", "Bitte eine Begründung eintragen.")
            return

        staerke_raw = self._staerke_var.get()
        staerke = int(staerke_raw) if staerke_raw != "(keine)" else None

        review_am = self._review_am_var.get().strip() or None
        if review_am:
            try:
                date.fromisoformat(review_am)
            except ValueError:
                messagebox.showwarning("These speichern", "Wiedervorlage-Datum muss im Format JJJJ-MM-TT sein.")
                return

        mechanismus_info = config_module.get_pruef_mechanismus(hg_id, uk_id)
        pruef_mechanismus = ",".join(mechanismus_info["mechanismen"]) if mechanismus_info else None

        these = These(
            hauptgruppe=hg_id,
            unterkategorie=uk_id,
            richtung=richtung_id,
            staerke=staerke,
            begruendung=begruendung,
            pruef_mechanismus=pruef_mechanismus,
            gesetzt_am=self._existing.gesetzt_am if self._existing else date.today().isoformat(),
            review_am=review_am,
            status=self._existing.status if self._existing else "aktiv",
            quelle=self._existing.quelle if self._existing else "manuell",
        )
        self.destroy()
        self._on_saved(these)


class ThesenView(ttk.Frame):
    """Liste + Verwaltung aller Thesen. Nimmt bewusst nur `db_conn_factory`
    entgegen (kein LLM-/API-Client noetig, reine CRUD-Ansicht, Muster wie
    `RegimeView`)."""

    def __init__(self, parent, db_conn_factory):
        super().__init__(parent)
        self._db_conn_factory = db_conn_factory
        self._begruendung_tooltips: dict[str, str] = {}
        self._vorschlag_tooltips: dict[str, str] = {}
        self._nur_aktive_var = tk.BooleanVar(value=True)

        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        toolbar = ttk.Frame(self, padding=8)
        toolbar.pack(fill="x")

        neu_button = ttk.Button(toolbar, text="Neue These …", command=self._on_neu)
        neu_button.pack(side="left")
        add_widget_tooltip(
            neu_button,
            "Legt eine neue These an (Hauptgruppe/Unterkategorie, Richtung, Begründung). "
            "Startet immer mit Status 'Aktiv'. Rein manuell - es gibt (noch) keinen "
            "automatischen KI-Vorschläge-Job.",
        )

        bearbeiten_button = ttk.Button(toolbar, text="Bearbeiten …", command=self._on_bearbeiten)
        bearbeiten_button.pack(side="left", padx=(6, 0))
        add_widget_tooltip(
            bearbeiten_button,
            "Bearbeitet die in der Liste ausgewählte These (Richtung/Stärke/Begründung/"
            "Review-Datum). Ändert NICHT den Status - dafür die beiden Buttons rechts "
            "daneben.",
        )

        erledigt_button = ttk.Button(
            toolbar, text="Als erledigt markieren", command=lambda: self._on_status_wechsel("erledigt"),
        )
        erledigt_button.pack(side="left", padx=(6, 0))
        add_widget_tooltip(
            erledigt_button,
            "Setzt die ausgewählte These auf Status 'Erledigt' - verschwindet danach aus "
            "der Standardansicht ('Nur aktive anzeigen'), wirkt sich sofort NICHT mehr auf "
            "Hervorhebung/Sortierung in Watchlist/Portfolio/Screener aus.",
        )

        verwerfen_button = ttk.Button(
            toolbar, text="Verwerfen", command=lambda: self._on_status_wechsel("verworfen"),
        )
        verwerfen_button.pack(side="left", padx=(6, 0))
        add_widget_tooltip(
            verwerfen_button,
            "Setzt die ausgewählte These auf Status 'Verworfen' (z. B. weil sie sich als "
            "falsch herausgestellt hat) - gleiche Wirkung wie 'Als erledigt markieren', nur "
            "anderer Status zur Unterscheidung in der Historie.",
        )

        nur_aktive_check = ttk.Checkbutton(
            toolbar, text="Nur aktive anzeigen", variable=self._nur_aktive_var, command=self.refresh,
        )
        nur_aktive_check.pack(side="left", padx=(16, 0))
        add_widget_tooltip(
            nur_aktive_check,
            "Blendet erledigte/verworfene Thesen aus der Liste aus. Rein eine Anzeige-"
            "Filterung - löscht nichts, wirkt sich nicht auf gespeicherte Daten aus.",
        )

        tree_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        tree_frame.pack(fill="both", expand=True)

        columns = ("kategorie", "richtung", "staerke", "mechanismus", "status", "gesetzt_am", "review_am")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18, selectmode="browse")
        headings = {
            "kategorie": "Kategorie", "richtung": "Richtung", "staerke": "Stärke",
            "mechanismus": "Prüf-Mechanismus", "status": "Status",
            "gesetzt_am": "Gesetzt am", "review_am": "Review am",
        }
        widths = {
            "kategorie": 260, "richtung": 110, "staerke": 60, "mechanismus": 180,
            "status": 90, "gesetzt_am": 90, "review_am": 90,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda _e: self._on_bearbeiten())
        self._reapply_sort = make_sortable(self.tree)
        add_row_tooltips(self.tree, lambda iid: self._begruendung_tooltips.get(iid))

        # 2026-07-24, #333 Punkt 17 (Transparenz-Anforderung) - Fall-B-
        # Aenderungsaufforderungen (agent/kategorie_vorschlaege.py) haben
        # sonst KEINE GUI-Oberflaeche: sie liegen sonst unsichtbar in
        # these_aenderungsvorschlaege, ohne Weg zum Uebernehmen/Ablehnen.
        vorschlag_label_frame = ttk.Frame(self, padding=(8, 0, 8, 4))
        vorschlag_label_frame.pack(fill="x")
        ttk.Label(
            vorschlag_label_frame, text="Offene Änderungsaufforderungen (KI-Vorschläge-Job)",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(side="left")

        vorschlag_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        vorschlag_frame.pack(fill="x")

        vorschlag_columns = ("kategorie", "aktuell", "vorschlag", "mechanismus", "erkannt_am")
        self.vorschlag_tree = ttk.Treeview(
            vorschlag_frame, columns=vorschlag_columns, show="headings", height=5, selectmode="browse",
        )
        vorschlag_headings = {
            "kategorie": "Kategorie", "aktuell": "Aktuelle Richtung", "vorschlag": "Vorgeschlagene Richtung",
            "mechanismus": "Prüf-Mechanismus", "erkannt_am": "Erkannt am",
        }
        vorschlag_widths = {"kategorie": 260, "aktuell": 130, "vorschlag": 150, "mechanismus": 180, "erkannt_am": 140}
        for col in vorschlag_columns:
            self.vorschlag_tree.heading(col, text=vorschlag_headings[col])
            self.vorschlag_tree.column(col, width=vorschlag_widths[col], anchor="w")
        self.vorschlag_tree.pack(fill="x", side="left", expand=True)
        add_row_tooltips(self.vorschlag_tree, lambda iid: self._vorschlag_tooltips.get(iid))

        vorschlag_button_frame = ttk.Frame(vorschlag_frame)
        vorschlag_button_frame.pack(side="left", padx=(8, 0))
        uebernehmen_button = ttk.Button(vorschlag_button_frame, text="Übernehmen", command=self._on_vorschlag_uebernehmen)
        uebernehmen_button.pack(fill="x", pady=(0, 4))
        add_widget_tooltip(
            uebernehmen_button,
            "Übernimmt die vorgeschlagene Richtung in die bestehende These (per Update) "
            "und schließt die Änderungsaufforderung als 'übernommen' ab.",
        )
        ablehnen_button = ttk.Button(vorschlag_button_frame, text="Ablehnen", command=self._on_vorschlag_ablehnen)
        ablehnen_button.pack(fill="x")
        add_widget_tooltip(
            ablehnen_button,
            "Lehnt den Vorschlag ab - die bestehende These bleibt unverändert. Für dieselbe "
            "Richtung gilt danach 30 Tage Cooldown, bevor sie erneut vorgeschlagen werden kann "
            "(eine gegenläufige Richtung ist davon nicht betroffen).",
        )

    def refresh(self) -> None:
        conn = self._db_conn_factory()
        try:
            thesen = db.get_aktive_thesen(conn) if self._nur_aktive_var.get() else db.get_alle_thesen(conn)
            offene_vorschlaege = db.get_offene_aenderungsvorschlaege(conn)
        finally:
            conn.close()
        self._render(thesen)
        self._render_vorschlaege(offene_vorschlaege)

    def _render_vorschlaege(self, vorschlaege: list) -> None:
        selected = self.vorschlag_tree.selection()
        selected_id = selected[0] if selected else None

        self.vorschlag_tree.delete(*self.vorschlag_tree.get_children())
        self._vorschlag_tooltips.clear()

        conn = self._db_conn_factory()
        try:
            for vorschlag in vorschlaege:
                these = db.get_these(conn, vorschlag.these_id) if vorschlag.these_id else None
                if these is None:
                    continue
                hg_name, uk_name = self._kategorie_namen(these)
                kategorie_text = _kategorie_anzeige(hg_name, uk_name)
                richtung_optionen = _richtung_optionen(these.hauptgruppe)
                aktuell_label = richtung_optionen.get(these.richtung, these.richtung)
                vorschlag_label = richtung_optionen.get(vorschlag.vorgeschlagene_richtung, vorschlag.vorgeschlagene_richtung)
                iid = str(vorschlag.id)
                self.vorschlag_tree.insert(
                    "", "end", iid=iid,
                    values=(
                        kategorie_text, aktuell_label, vorschlag_label,
                        _mechanismus_label(vorschlag.mechanismus_typ), vorschlag.erkannt_am or "-",
                    ),
                )
                tooltip = vorschlag.begruendung
                if vorschlag.datenstand:
                    tooltip += f"\n\nDatenstand: {vorschlag.datenstand}"
                self._vorschlag_tooltips[iid] = tooltip
        finally:
            conn.close()

        theme.restripe_treeview(self.vorschlag_tree)
        if selected_id and self.vorschlag_tree.exists(selected_id):
            self.vorschlag_tree.selection_set(selected_id)

    def _on_vorschlag_uebernehmen(self) -> None:
        selected = self.vorschlag_tree.selection()
        if not selected:
            messagebox.showinfo("Übernehmen", "Bitte zuerst eine Änderungsaufforderung auswählen.")
            return
        vorschlag_id = int(selected[0])
        jetzt_iso = datetime.now(timezone.utc).isoformat()
        conn = self._db_conn_factory()
        try:
            vorschlag = db.get_these_aenderungsvorschlag(conn, vorschlag_id)
            if vorschlag is None or vorschlag.these_id is None:
                return
            these = db.get_these(conn, vorschlag.these_id)
            if these is None:
                return
            aktualisierte_these = dataclasses.replace(these, richtung=vorschlag.vorgeschlagene_richtung)
            db.update_these(conn, these.id, aktualisierte_these)
            db.set_these_aenderungsvorschlag_status(conn, vorschlag_id, "uebernommen", jetzt_iso)
        finally:
            conn.close()
        self.refresh()

    def _on_vorschlag_ablehnen(self) -> None:
        selected = self.vorschlag_tree.selection()
        if not selected:
            messagebox.showinfo("Ablehnen", "Bitte zuerst eine Änderungsaufforderung auswählen.")
            return
        vorschlag_id = int(selected[0])
        jetzt_iso = datetime.now(timezone.utc).isoformat()
        conn = self._db_conn_factory()
        try:
            db.set_these_aenderungsvorschlag_status(conn, vorschlag_id, "abgelehnt", jetzt_iso)
        finally:
            conn.close()
        self.refresh()

    def _render(self, thesen: list[These]) -> None:
        selected = self.tree.selection()
        selected_id = selected[0] if selected else None

        self.tree.delete(*self.tree.get_children())
        self._begruendung_tooltips.clear()

        for these in thesen:
            hg_name, uk_name = self._kategorie_namen(these)
            kategorie_text = _kategorie_anzeige(hg_name, uk_name)
            richtung_label = _richtung_optionen(these.hauptgruppe).get(these.richtung, these.richtung)
            iid = str(these.id)
            # 2026-07-24, #333 Punkt 15 (review_am-Ablauf-Verhalten, reiner
            # Kalender-Hinweis, kein Aenderungsvorschlag/keine E-Mail, siehe
            # Kategorie_Basisinformationen_Release2.md Abschnitt 11 Punkt 15).
            review_faellig = False
            if these.review_am:
                try:
                    review_faellig = date.fromisoformat(these.review_am) < date.today()
                except ValueError:
                    pass
            review_anzeige = f"⚠ {these.review_am}" if review_faellig else (these.review_am or "-")
            self.tree.insert(
                "", "end", iid=iid,
                values=(
                    kategorie_text,
                    richtung_label,
                    these.staerke if these.staerke else "-",
                    _mechanismus_label(these.pruef_mechanismus),
                    _STATUS_LABELS.get(these.status, these.status),
                    these.gesetzt_am,
                    review_anzeige,
                ),
                tags=(self._richtung_tag(these),),
            )
            begruendung_tooltip = these.begruendung
            if review_faellig:
                begruendung_tooltip += f"\n\n⚠ Wiedervorlage fällig seit {these.review_am}."
            self._begruendung_tooltips[iid] = begruendung_tooltip

        self.tree.tag_configure("richtung_positiv", foreground=theme.info_color())
        self.tree.tag_configure("richtung_negativ", foreground=theme.danger_color())
        self.tree.tag_configure("richtung_neutral", foreground=theme.default_text_color())

        theme.restripe_treeview(self.tree)
        self._reapply_sort()

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)

    @staticmethod
    def _richtung_tag(these: These) -> str:
        if these.richtung in ("uebergewichten", "aktiv"):
            return "richtung_positiv"
        if these.richtung in ("meiden",):
            return "richtung_negativ"
        return "richtung_neutral"

    @staticmethod
    def _kategorie_namen(these: These) -> tuple[str, str | None]:
        kategorien = config_module.get_kategorien()
        hg_obj = next((hg for hg in kategorien["hauptgruppen"] if hg["id"] == these.hauptgruppe), None)
        hg_name = hg_obj["name"] if hg_obj else these.hauptgruppe
        if these.unterkategorie is None or hg_obj is None:
            return hg_name, None
        uk_obj = next((uk for uk in hg_obj["unterkategorien"] if uk["id"] == these.unterkategorie), None)
        return hg_name, (uk_obj["name"] if uk_obj else these.unterkategorie)

    def _selected_these_id(self) -> int | None:
        selected = self.tree.selection()
        return int(selected[0]) if selected else None

    def _on_neu(self) -> None:
        TheseDialog(self, existing=None, on_saved=self._save_new)

    def _save_new(self, these: These) -> None:
        conn = self._db_conn_factory()
        try:
            db.create_these(conn, these)
        finally:
            conn.close()
        self.refresh()

    def _on_bearbeiten(self) -> None:
        these_id = self._selected_these_id()
        if these_id is None:
            messagebox.showinfo("These bearbeiten", "Bitte zuerst eine These auswählen.")
            return
        conn = self._db_conn_factory()
        try:
            existing = db.get_these(conn, these_id)
        finally:
            conn.close()
        if existing is None:
            messagebox.showwarning("These bearbeiten", "Diese These existiert nicht mehr.")
            self.refresh()
            return
        TheseDialog(self, existing=existing, on_saved=lambda these: self._save_edit(these_id, these))

    def _save_edit(self, these_id: int, these: These) -> None:
        conn = self._db_conn_factory()
        try:
            db.update_these(conn, these_id, these)
        finally:
            conn.close()
        self.refresh()

    def _on_status_wechsel(self, status: str) -> None:
        these_id = self._selected_these_id()
        if these_id is None:
            messagebox.showinfo("Status ändern", "Bitte zuerst eine These auswählen.")
            return
        label = _STATUS_LABELS.get(status, status)
        if not messagebox.askyesno("Status ändern", f"These wirklich als \"{label}\" markieren?"):
            return
        conn = self._db_conn_factory()
        try:
            db.set_these_status(conn, these_id, status)
        finally:
            conn.close()
        self.refresh()
