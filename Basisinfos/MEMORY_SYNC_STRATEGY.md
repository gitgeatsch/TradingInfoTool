# Memory & CLAUDE.md Sync Strategy

## Drei Sync-Ebenen (Stand 2026-07-16 — korrigiert/vereinheitlicht)

Der Desktop↔Notebook-Sync läuft je nach Situation über einen von drei
unterschiedlichen Wegen, mit unterschiedlichem Umfang. Diese drei Ebenen
lösen den ursprünglichen, inzwischen überholten "immer Drive"-Ansatz weiter
unten ab:

1. **USB-Stick, vor Ort (bevorzugt, voller Umfang).** Wenn beide Geräte
   physisch zusammen sind: **alles** — `.env`, `Basisinfos/Assets.xlsx`,
   die SQLite-Datenbank, die Claude-Code-Memory UND beide `CLAUDE.md`-Dateien
   (Projekt + global). Vermeidet jede Cloud-Exposition von Secrets/
   persönlichen Finanzdaten. Voller Ablauf, Ordnerstruktur (`claudesync`)
   und Reihenfolge-Regeln: siehe Memory `reference_usb_sync_workflow.md`
   (liegt nicht im Repo, ist Claude-Code-Memory).

   **Wichtige Ausnahme seit 2026-07-17 — manuelle Einstandspreis-Korrekturen
   brauchen KEINE volle DB-Kopie mehr:** das Notebook läuft 24/7 und erzeugt
   laufend selbst Produktivdaten (Signale, Hebel-Positionen, Preis-Historie,
   Makro-Snapshots, API-Health-Verlauf) — eine volle DB-Überschreibung würde
   das jedes Mal vernichten. Für den konkreten, praktisch relevanten Fall
   "am Desktop einen manuellen Einstandspreis korrigiert/ergänzt" (Portfolio-
   Tab, Doppelklick auf eine Zeile) reicht jetzt eine einzige kleine Datei:

   - **Datei:** `data/holdings_manual_overrides.json` (liegt neben der DB,
     ebenfalls `.gitignore`'t, gleiche Sensitivität wie `Assets.xlsx`)
   - **Wird automatisch erzeugt/aktualisiert:** bei jeder Änderung eines
     manuellen Einstandspreises — kein Export-Schritt nötig.
   - **Wird automatisch angewendet:** beim nächsten Start von `main.py`
     auf dem Zielgerät (egal ob Desktop oder Notebook) — kein Import-Skript
     nötig, kein Neustart-Sonderfall.
   - **Sync-Schritt dafür:** nur diese eine JSON-Datei per USB (oder
     grundsätzlich jedem anderen Weg) auf das Zielgerät kopieren, an
     denselben relativen Pfad (`data/holdings_manual_overrides.json`) —
     fertig, keine weiteren Schritte.

   **Die volle DB-Kopie bleibt weiterhin nötig für:** Erstinstallation eines
   neuen Geräts, oder falls aus anderem Grund die komplette DB ersetzt werden
   muss (Reihenfolge-Regeln dafür unverändert in `reference_usb_sync_workflow.md`).
   Technischer Hintergrund/Code: `database/db.py::HOLDINGS_MANUAL_OVERRIDES_PATH`,
   `export_holdings_manual_overrides()`/`import_holdings_manual_overrides()`,
   siehe `Basisinfos/Regelwerksmanual.md` Kap. 14 (Nachtrag 2026-07-17).
2. **Google Drive, remote (nur wenn kein USB möglich, reduzierter Umfang).**
   Wenn die Geräte NICHT physisch zusammen sind UND weder `.env`/Secrets noch
   die Datenbank aktuell übertragen werden müssen: nur Claude-Code-Memory +
   beide `CLAUDE.md`-Dateien. Rest dieses Dokuments (unten) beschreibt genau
   diesen Fall im Detail.
3. **Nur `git push`/`git pull` (kleine Code-Änderungen ohne Memory-Relevanz).**
   Wenn eine Änderung rein den Code betrifft und keine neue Erkenntnis
   enthält, die eine künftige Session kennen müsste (kein Memory-Update
   nötig): einfacher Git-Sync reicht, ohne Memory/CLAUDE.md anzufassen.
   **Wichtig:** bei Schema-/Konfigurationsänderungen (z. B. `config.yaml`-
   Struktur, umbenannte Scheduler-Jobs) reicht ein reines `git pull` auf dem
   Zielgerät NICHT aus — der laufende Prozess muss zusätzlich neu gestartet
   werden, da `config.py`/der Scheduler den alten Stand im Speicher halten.

**Warum nicht immer GitHub?** Git-Historie ist permanent — auch nachträglich
gelöschte Inhalte bleiben in alten Commits abrufbar. Das Projekt-`CLAUDE.md`
ist deshalb bewusst in `.gitignore` eingetragen (u. a. weil es früher Kontext
zu einem inzwischen behobenen Token-Leak-Vorfall enthielt). Secrets/
persönliche Daten laufen deshalb nie über Git, sondern über Ebene 1 oder 2.

## Was NICHT ohne explizite Nutzer-Anweisung zwischen den Geräten übertragen werden soll

**An Claude auf beiden Geräten:** `.env` und `Basisinfos/Assets.xlsx` NICHT
automatisch/unaufgefordert anfordern oder kopieren — nur wenn der Nutzer das
explizit anweist (z. B. im Rahmen eines vollen Ebene-1-USB-Syncs, siehe oben).
Ein automatischer Vorschlag einer Claude-Session ist das nicht.

**Hinweis, historisch überholt:** eine frühere Fassung dieses Dokuments
(2026-07-06) begründete den generellen .env/DB-Ausschluss noch damit, dass
"kein Code existiert, der das braucht" (Phase 1 war damals noch nicht
gestartet) — das ist seit Langem nicht mehr zutreffend, die App läuft
produktiv, die DB enthält echte Portfoliodaten, `.env` echte API-Keys. Der
eigentliche Grund, .env/DB nicht *automatisch* zu übertragen, ist unverändert
gültig (siehe Memory `feedback_no_cross_device_secrets.md`), nur die
Begründung war veraltet.

---

## Sync-Checkliste: Was wird übertragen? (Ebene 2 — Drive, ohne .env/DB)

**Der Rest dieses Dokuments beschreibt Ebene 2 (Drive, remote, ohne Secrets/DB) im
Detail.** Für Ebene 1 (USB, vor Ort, voller Umfang inkl. `.env`/Assets.xlsx/DB) siehe
Memory `reference_usb_sync_workflow.md`.

**Wenn du einen Sync von Desktop → Notebook auf Ebene 2 durchführst, synchronisierst du
genau diese drei Dinge:**

| Was | Quelle (Desktop) | Ziel (Notebook) | Format | Anzahl |
|---|---|---|---|---|
| **1. Projekt-CLAUDE.md** | `D:\CLAUDE_Projects\...\CLAUDE.md` | `C:\CLAUDE_Projects\...\CLAUDE.md` | Textdatei | 1 Datei |
| **2. Globale CLAUDE.md** | `C:\Users\Geatsch\.claude\CLAUDE.md` | `C:\Users\<user>\.claude\CLAUDE.md` | Textdatei | 1 Datei |
| **3. Memory-Ordner (alle *.md)** | `C:\Users\Geatsch\.claude\projects\D--...\memory\` | `C:\Users\<user>\.claude\projects\C--...\memory\` | Markdown-Dateien | Alle (z. B. MEMORY.md, project_dev_setup.md, feedback_*.md, etc.) |

**Beispiel Kategorie 3 (Memory-Ordner) — alle diese Dateien werden übertragen:**
- `MEMORY.md` (Index aller Memory-Notizen)
- `project_dev_setup.md`
- `project_github_token.md`
- `project_stand_basisinfos.md`
- `feedback_assistant_name.md`
- `feedback_limits_strategy.md`
- `feedback_no_cross_device_secrets.md`
- (und später weitere `.md`-Dateien, die im Memory-Ordner hinzukommen)

**Auf Ebene 2 nicht übertragen (dafür Ebene 1/USB nutzen, falls nötig):**
- `.env` (API-Keys)
- `Assets.xlsx` (persönliche Finanzdaten)
- Die SQLite-Datenbank
- Keine Code-Dateien (`*.py`, `*.json`, etc. — laufen immer über Git, alle Ebenen)
- `.gitignore`, `requirements.txt`, etc. (laufen über Git)

---

## Teil 1: Memory

Die Claude Code Memory liegt **NICHT im Projektordner**, sondern im
**Windows-Benutzerprofil** (`C:\Users\<username>\.claude\`), unabhängig davon, auf
welchem Laufwerk das Projekt selbst liegt.

- **Desktop:** Projekt liegt auf `D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\`
  → Memory liegt auf `C:\Users\Geatsch\.claude\projects\D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory\`
- **Notebook:** Projekt liegt auf `C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\`
  → Memory liegt auf `C:\Users\<notebook-username>\.claude\projects\C--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory\`

**Wichtig zum Ordnernamen:** Das Präfix (`D--` bzw. `C--`) kodiert das **Laufwerk des
Projekt-Pfads**, nicht das Laufwerk, auf dem die Memory selbst liegt. Die Memory selbst
liegt auf beiden Rechnern unter `C:\Users\...\.claude\` (Standard-Windows-Benutzerprofil).
Unterschiedliche Ordnernamen auf Desktop/Notebook sind normal, kein Fehler.

**Sicherheit:** Lokale Backups vor jedem Sync-Punkt verhindern Datenverlust.

---

## Zwei getrennte `.claude`-Bereiche — nicht verwechseln

Es gibt **zwei unterschiedliche `.claude`-Ordner**, die leicht verwechselt werden:

| Bereich | Pfad | Inhalt | In Git? |
|---|---|---|---|
| **Projekt-lokal** | `<Projektordner>\.claude\` | `settings.json`, `launch.json` (Tool-Berechtigungen) | Nein (`.gitignore`) |
| **User-global (Memory)** | `C:\Users\<username>\.claude\projects\<kodierter-pfad>\memory\` | Die eigentliche Memory (`.md`-Dateien, `MEMORY.md`-Index) | Nein, nicht im Projekt-Repo |

**Die Memory-Sync-Strategie hier betrifft ausschließlich den zweiten Bereich** (User-global).

---

## Struktur

```
C:\Users\<username>\.claude\projects\
├── D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory\   ← Desktop
└── C--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory\   ← Notebook

<Projektordner>\.claude\backups\   ← lokale Backups (projekt-lokal, da praktisch)
    ├── memory_backup_2026-07-06.zip
    ├── memory_backup_2026-07-07.zip
    └── [weitere Backups...]
```

---

## Sync-Prozess (manuell)

### **Von Desktop → Notebook**

1. **Backup erstellen** (Sicherung der aktuellen Memory, Desktop-Pfad)
   ```powershell
   $date = Get-Date -Format 'yyyy-MM-dd'
   New-Item -ItemType Directory -Force -Path "D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\backups"
   Compress-Archive -Path "C:\Users\Geatsch\.claude\projects\D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory" `
     -DestinationPath "D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\backups\memory_backup_$date.zip" `
     -Force
   ```

2. **Zu Google Drive hochladen**
   - Quelle: `C:\Users\Geatsch\.claude\projects\D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory\`
   - Ziel in Drive: `/TradingInfoTool/memory_sync/` (oder ähnlich)

3. **Auf Notebook: Backup VOR dem Download** (Notebook-Pfad, `<username>` anpassen!)
   ```powershell
   $date = Get-Date -Format 'yyyy-MM-dd_HHmm'
   New-Item -ItemType Directory -Force -Path "C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\backups"
   Compress-Archive -Path "C:\Users\<notebook-username>\.claude\projects\C--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory" `
     -DestinationPath "C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\backups\memory_backup_vor_sync_$date.zip" `
     -Force
   ```
   *(Falls der Ordner auf dem Notebook noch nicht existiert, weil dort noch nie eine
   Session lief: Schritt überspringen, es gibt noch nichts zu sichern.)*

4. **Von Drive herunterladen**
   - Zielordner: `C:\Users\<notebook-username>\.claude\projects\C--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory\`
   - Ordner ggf. manuell anlegen, falls er noch nicht existiert
   - Dateien aus Drive dort hineinkopieren (überschreiben)

5. **Starten:** im Projektordner `claude code .`

---

### **Von Notebook → Desktop** (umgekehrt)

1. **Auf Notebook:** Backup erstellen (Notebook-Memory-Pfad, siehe oben)
2. **Zu Drive hochladen**
3. **Desktop:** Backup erstellen (Desktop-Memory-Pfad, vor Download)
4. **Von Drive herunterladen** in `C:\Users\Geatsch\.claude\projects\D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool\memory\`
5. **Starten:** `claude code .`

---

## Teil 2: CLAUDE.md-Dateien

Es gibt **zwei verschiedene CLAUDE.md-Dateien**, an zwei unterschiedlichen Orten. Beide
werden manuell synchronisiert, ändern sich aber viel seltener als die Memory — also
reicht ein Abgleich bei Bedarf, kein regelmäßiger Rhythmus.

### 2a. Projekt-`CLAUDE.md` (projektspezifisch)

**Ort:**
- Desktop: `D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\CLAUDE.md`
- Notebook: `C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\CLAUDE.md`

**Inhalt:** Projektbeschreibung, Tech-Stack, Anforderungen, Entwicklungsphasen — sollte
auf beiden Rechnern **identisch** sein, da es dasselbe Projekt beschreibt.

**Wichtig:** Diese Datei ist absichtlich in `.gitignore` (`CLAUDE.md`-Zeile) — **nicht
über `git pull`/`git push` synchronisieren**, auch nicht versehentlich mit `git add -f`
erzwingen. Immer manuell über Drive austauschen.

### 2b. Globales `CLAUDE.md` (rechnerübergreifend, für ALLE Projekte)

**Ort:**
- Desktop: `C:\Users\Geatsch\.claude\CLAUDE.md`
- Notebook: `C:\Users\<notebook-username>\.claude\CLAUDE.md`

**Inhalt:** Präferenzen, die für *alle* deine Projekte gelten (aktuell z. B. der Name
„Charlie"). Liegt außerhalb jedes Projektordners — hat mit Git grundsätzlich nichts zu
tun, egal welches Repo.

**Falls die Datei auf dem Notebook noch nicht existiert:** einfach neu anlegen mit dem
Inhalt von Desktop (keine Migration nötig, ist nur eine einzelne kurze Textdatei).

### Sync-Ablauf für beide CLAUDE.md-Dateien (gleiches Muster wie Memory)

1. **Vor dem Ändern/Überschreiben:** Kopie der aktuellen Datei lokal sichern (z. B. in
   `<Projektordner>\.claude\backups\CLAUDE.md_backup_YYYY-MM-DD.md` bzw. analog für die
   globale Datei)
2. **Hochladen zu Drive:** aktuelle Version in den gleichen Drive-Ordner wie die Memory
   legen (z. B. `/TradingInfoTool/memory_sync/CLAUDE_project.md` und
   `/TradingInfoTool/memory_sync/CLAUDE_global.md` — klar benennen, welche Datei welche ist)
3. **Auf dem Zielrechner:** vor dem Überschreiben ebenfalls Backup der dortigen Version,
   dann die Datei von Drive an den korrekten Pfad kopieren (siehe oben, 2a bzw. 2b)
4. Kein `claude code`-Neustart nötig — CLAUDE.md wird bei der nächsten Session-Anfrage
   ohnehin neu gelesen

**Merksatz fürs Notebook:** Zwei Dateien, zwei Orte — die eine (`CLAUDE.md` im
Projektordner) betrifft nur TradingInfoTool, die andere (`CLAUDE.md` im
`.claude`-Ordner deines Benutzerprofils) betrifft alle Projekte auf diesem Rechner.
Beide werden genauso wie die Memory behandelt: manuell, über Drive, mit Backup davor —
niemals über Git.

---

## Wichtige Regeln

- ✅ **Immer Backup vor Sync** — keine Ausnahmen (gilt für Memory UND CLAUDE.md)
- ✅ **Nie beide Rechner gleichzeitig an denselben Dateien arbeiten**
- ✅ **Backups lokal halten** — mindestens letzte 7 Tage
- ✅ **Pfade genau prüfen** — Memory liegt im Benutzerprofil (`C:\Users\...\.claude\`),
  NICHT im Projektordner. Nur die Backups liegen praktischerweise projekt-lokal.
- ✅ **CLAUDE.md niemals über Git syncen** — auch nicht versehentlich (`.gitignore`
  beachten, keine `git add -f`)
- ✅ **Klar dokumentieren** — siehe Log unten

---

## Sync-Log (manuell führen)

```markdown
2026-07-06 14:30 | Desktop → Drive | Memory aktualisiert (Agent-Architektur finalisiert)
2026-07-06 15:00 | Notebook ← Drive | Memory heruntergeladen, Notebook-Arbeit möglich
2026-07-07 10:00 | Notebook → Drive | Memory aktualisiert (Phase 1 Setup)
...
```

**Datei:** `.claude/SYNC_LOG.txt` (projekt-lokal, nicht versioniert) oder hier direkt fortschreiben.

---

## Fallback: Bei Datenverlust

Falls etwas schiefgeht:
1. Lokale Backups im `<Projektordner>\.claude\backups\` Ordner prüfen
2. Neueste `.zip` extrahieren
3. Inhalt zurück nach `C:\Users\<username>\.claude\projects\<kodierter-pfad>\memory\` kopieren

---

## Workflow-Checklist

### Desktop → Notebook (kompletter Sync mit Memory + CLAUDE.md)

**Schritt 1: Backup erstellen (Desktop)**
- [ ] Memory-Ordner: `C:\Users\Geatsch\.claude\projects\D--...\memory\` → ZIP in Backups
- [ ] Projekt-CLAUDE.md: `D:\CLAUDE_Projects\...\CLAUDE.md` → Kopie in Backups
- [ ] Globale CLAUDE.md: `C:\Users\Geatsch\.claude\CLAUDE.md` → Kopie in Backups

**Schritt 2: Zu Google Drive hochladen**
- [ ] Memory-Ordner (alle *.md-Dateien) → `/TradingInfoTool/memory_sync/memory/`
  (oder direkt einzelne Dateien oder ein ZIP, Hauptsache alles beisammen)
- [ ] CLAUDE_project.md → `/TradingInfoTool/memory_sync/`
- [ ] CLAUDE_global.md → `/TradingInfoTool/memory_sync/`

**Schritt 3: Auf Notebook vorbereiten**
- [ ] Memory-Ordner-Backup erstellen (falls vorhanden): `C:\Users\<user>\.claude\projects\C--...\memory\`
- [ ] CLAUDE_project.md-Backup erstellen (falls vorhanden): `C:\CLAUDE_Projects\...\CLAUDE.md`
- [ ] CLAUDE_global.md-Backup erstellen (falls vorhanden): `C:\Users\<user>\.claude\CLAUDE.md`

**Schritt 4: Von Drive herunterladen & überschreiben**
- [ ] Memory-Ordner: von Drive → `C:\Users\<user>\.claude\projects\C--...\memory\`
  (alle *.md-Dateien dorthin kopieren, alte Dateien überschreiben)
- [ ] CLAUDE_project.md: von Drive → `C:\CLAUDE_Projects\...\CLAUDE.md`
- [ ] CLAUDE_global.md: von Drive → `C:\Users\<user>\.claude\CLAUDE.md`

**Schritt 5: Starten**
- [ ] `claude code .` im Projektordner starten → sollte neue Memory haben

---

### Notebook → Desktop (umgekehrt, gleiches Prinzip)
- [ ] Backup erstellen (Notebook: Memory, beide CLAUDE.md)
- [ ] Zu Google Drive hochladen
- [ ] Desktop: Backup erstellen (vor Download)
- [ ] Von Drive herunterladen & überschreiben (Memory + beide CLAUDE.md)
- [ ] `claude code .` starten

---

### Nur CLAUDE.md synchronisieren (ohne Memory, seltener Fall)
Nutze diesen Ablauf, wenn sich **nur** eine CLAUDE.md-Datei geändert hat (ohne Memory-Änderungen):
- [ ] Betroffene Datei identifizieren: Projekt-`CLAUDE.md` und/oder globale `CLAUDE.md`?
- [ ] Backup der aktuellen Version auf dem Quellrechner
- [ ] Hochladen zu Drive (klar benannt: `CLAUDE_project.md` / `CLAUDE_global.md`)
- [ ] Auf Zielrechner: Backup der dortigen Version
- [ ] Von Drive herunterladen an korrekten Zielpfad (siehe Teil 2a/2b oben)
- [ ] Kein Neustart nötig, wird bei nächster Session automatisch gelesen

---

**Erstellt:** 2026-07-06 | **Korrigiert:** 2026-07-06 (Pfade auf tatsächliche User-Profil-Location korrigiert) | **Erweitert:** 2026-07-06 (CLAUDE.md-Sync ergänzt) | **Strategie:** Manueller Drive-Sync mit lokalen Backups, kein Git für Memory/CLAUDE.md
