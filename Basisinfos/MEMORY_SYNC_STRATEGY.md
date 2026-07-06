# Memory Sync Strategy

## Übersicht

Die Claude Code Memory wird **manuell über Google Drive synchronisiert** zwischen zwei
Rechnern. Wichtig: Die Memory liegt **NICHT im Projektordner**, sondern im
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

## Wichtige Regeln

- ✅ **Immer Backup vor Sync** — keine Ausnahmen
- ✅ **Nie beide Rechner gleichzeitig an Memory arbeiten**
- ✅ **Backups lokal halten** — mindestens letzte 7 Tage
- ✅ **Pfade genau prüfen** — Memory liegt im Benutzerprofil (`C:\Users\...\.claude\`),
  NICHT im Projektordner. Nur die Backups liegen praktischerweise projekt-lokal.
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

### Desktop → Notebook
- [ ] Backup erstellen (aus `C:\Users\Geatsch\.claude\projects\D--...\memory\`)
- [ ] Zu Google Drive hochladen
- [ ] Auf Notebook: Backup erstellen (aus `C:\Users\<notebook-user>\.claude\projects\C--...\memory\`, falls vorhanden)
- [ ] Von Drive herunterladen nach `C:\Users\<notebook-user>\.claude\projects\C--...\memory\`
- [ ] `claude code .` im Projektordner starten

### Notebook → Desktop
- [ ] Backup erstellen (Notebook-Memory-Pfad)
- [ ] Zu Google Drive hochladen
- [ ] Desktop: Backup erstellen (Desktop-Memory-Pfad)
- [ ] Von Drive herunterladen nach `C:\Users\Geatsch\.claude\projects\D--...\memory\`
- [ ] `claude code .` im Projektordner starten

---

**Erstellt:** 2026-07-06 | **Korrigiert:** 2026-07-06 (Pfade auf tatsächliche User-Profil-Location korrigiert) | **Strategie:** Manueller Drive-Sync mit lokalen Backups
