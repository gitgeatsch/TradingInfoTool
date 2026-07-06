# Memory Sync Strategy

## Übersicht

Das `projects/` Verzeichnis (Claude Code Memory) wird **manuell über Google Drive synchronisiert** zwischen zwei Rechnern:
- **Desktop:** `D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\`
- **Notebook:** `C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\`

**Sicherheit:** Lokale Backups vor jedem Sync-Punkt verhindern Datenverlust.

---

## Struktur

```
.claude/
├── projects/
│   ├── D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/memory/
│   └── C--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/memory/
│
└── backups/
    ├── memory_backup_2026-07-06.zip
    ├── memory_backup_2026-07-07.zip
    └── [weitere Backups...]
```

---

## Sync-Prozess (manuell)

### **Von Desktop → Notebook**

1. **Backup erstellen** (Sicherung der aktuellen Memory)
   ```powershell
   $date = Get-Date -Format 'yyyy-MM-dd'
   Compress-Archive -Path "D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\projects" `
     -DestinationPath "D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\backups\memory_backup_$date.zip" `
     -Force
   ```

2. **Zu Google Drive hochladen**
   - Ordner: `D:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\projects\`
   - In Drive-Ordner: `/TradingInfoTool/memory_sync/` oder ähnlich
   - Neue Datei oder Update bestehende Datei

3. **Auf Notebook: Backup VOR dem Download**
   ```powershell
   $date = Get-Date -Format 'yyyy-MM-dd_HHmm'
   Compress-Archive -Path "C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\projects" `
     -DestinationPath "C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\backups\memory_backup_vor_sync_$date.zip" `
     -Force
   ```

4. **Von Drive herunterladen**
   - Neuer Inhalt in: `C:\CLAUDE_Projects\SoftwareProjekte\TradingInfoTool\.claude\projects\`
   - Überschreibt alte Memory, Backup ist gesichert

5. **Starten:** `claude code .`

---

### **Von Notebook → Desktop** (umgekehrt)

1. **Auf Notebook:** Backup erstellen (wie oben, mit C:\ Pfad)
2. **Zu Drive hochladen**
3. **Desktop:** Backup erstellen (vor Download)
4. **Von Drive herunterladen** (in D:\ Ordner)
5. **Starten:** `claude code .`

---

## Wichtige Regeln

- ✅ **Immer Backup vor Sync** — keine Ausnahmen
- ✅ **Nie beide Rechner gleichzeitig an Memory arbeiten**
- ✅ **Backups lokal halten** — mindestens letzte 7 Tage
- ✅ **Klar dokumentieren** — siehe Log unten

---

## Sync-Log (manuell führen)

```markdown
2026-07-06 14:30 | Desktop → Drive | Memory aktualisiert (Agent-Architektur finalisiert)
2026-07-06 15:00 | Notebook ← Drive | Memory heruntergeladen, Notebook-Arbeit möglich
2026-07-07 10:00 | Notebook → Drive | Memory aktualisiert (Phase 1 Setup)
...
```

**Datei:** `.claude/SYNC_LOG.txt` oder in der Git-History nachschauen.

---

## Fallback: Bei Datenverlust

Falls etwas schiefgeht:
1. Lokale Backups im `backups/` Ordner prüfen
2. Neueste `.zip` extrahieren
3. Zurückgehen zu letztem bekannten guten Stand

---

## Workflow-Checklist

### Desktop → Notebook
- [ ] Backup erstellen (`memory_backup_YYYY-MM-DD.zip`)
- [ ] Zu Google Drive hochladen
- [ ] Auf Notebook: Backup erstellen
- [ ] Von Drive herunterladen
- [ ] Memory-Ordner auf Notebook aktualisiert
- [ ] `claude code .` starten

### Notebook → Desktop
- [ ] Backup erstellen (mit C:\ Pfad)
- [ ] Zu Google Drive hochladen
- [ ] Desktop: Backup erstellen
- [ ] Von Drive herunterladen
- [ ] Memory-Ordner auf Desktop aktualisiert
- [ ] `claude code .` starten

---

**Erstellt:** 2026-07-06 | **Strategie:** Manueller Drive-Sync mit lokalen Backups
