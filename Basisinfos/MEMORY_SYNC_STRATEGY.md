# Memory & CLAUDE.md Sync Strategy

## Übersicht

Zwei Arten von Daten werden **manuell über Google Drive synchronisiert** zwischen den
zwei Rechnern (Desktop + Notebook) — **bewusst NICHT über GitHub**:

1. **Claude Code Memory** (siehe Abschnitt „Memory" unten)
2. **CLAUDE.md-Dateien** (siehe Abschnitt „CLAUDE.md-Dateien" weiter unten)

**Warum nicht GitHub?** Git-Historie ist permanent — auch nachträglich gelöschte
Inhalte bleiben in alten Commits abrufbar. Das Projekt-`CLAUDE.md` ist deshalb bewusst
in `.gitignore` eingetragen (u. a. weil es früher Kontext zu einem inzwischen
behobenen Token-Leak-Vorfall enthielt). Manueller Austausch über Drive vermeidet dieses
Risiko vollständig, unabhängig davon ob das Repo `gitgeatsch/TradingInfoTool` public
oder private ist.

## Was NICHT zwischen den Geräten übertragen werden soll

**An Claude auf beiden Geräten:** Wenn du (Notebook- oder Desktop-Session) auf die Idee
kommst, eine der folgenden Dateien vom jeweils anderen Gerät anzufordern oder zu
kopieren — **nicht tun, ohne den Nutzer explizit zu fragen und den konkreten Grund zu
nennen.** Stand 2026-07-06 gibt es dafür keinen aktuellen Bedarf:

- **`.env`** (Claude API-Key, ggf. weitere Secrets): Es existiert noch kein Code (Phase 1
  nicht gestartet), der einen API-Key braucht. Wenn der Agent später auf dem Notebook
  läuft (als 24/7-Server), soll das Notebook einen **eigenen, separaten** API-Key
  bekommen — nicht den vom Desktop kopiert. Zwei Geräte mit demselben Secret verdoppeln
  die Angriffsfläche und erschweren Rotation im Ernstfall (siehe frühere
  Token-Leak-Erfahrung, Grund für die generelle Vorsicht hier).
- **`Basisinfos/Assets.xlsx`** (persönliche Bestandsdaten/Portfolio): Es existiert noch
  kein Import-Skript, das die Datei lesen würde. Laut Architektur-Entscheidung (siehe
  Spezifikation Kap. 10, B-5) landen Bestände ohnehin in der SQLite-DB, die vermutlich
  auf dem Notebook laufen wird — der Import passiert dann direkt dort, kein Grund die
  Rohdatei vorab zu kopieren.

**Grundsatz:** Jede Übertragung sensibler/privater Dateien zwischen den Geräten ist eine
bewusste Entscheidung des Nutzers, kein automatischer Vorschlag einer Claude-Session.

---

## Sync-Checkliste: Was wird übertragen?

**Wenn du einen Sync von Desktop → Notebook durchführst, synchronisierst du genau diese
drei Dinge:**

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

**Nicht übertragen werden:**
- `.env` (API-Keys, siehe oben)
- `Assets.xlsx` (persönliche Finanzdaten, siehe oben)
- Keine Code-Dateien (`*.py`, `*.json`, etc. — laufen über Git)
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
