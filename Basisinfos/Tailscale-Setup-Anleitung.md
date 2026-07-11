# Tailscale einrichten — Notebook von unterwegs erreichen

**Zweck:** Grundlage für den geplanten Remote-Zugriff aufs 24/7-Notebook
(siehe `Regelwerksmanual.md` Kap. 12, Diskussion 2026-07-11). Tailscale selbst
macht noch nichts an der TradingInfoTool-App — es baut nur ein privates,
verschlüsseltes Netz zwischen deinen Geräten auf, in dem später eine kleine
Steuer-Seite erreichbar sein wird. Kein Portforwarding, keine öffentliche
Internet-Exposition, kostenlos für Privatnutzung (bis 3 Nutzer/100 Geräte).

**Zeitaufwand:** ca. 10-15 Minuten, keine Netzwerk-Kenntnisse nötig.

---

## Schritt 1: Tailscale-Konto erstellen

1. Öffne https://tailscale.com in einem Browser (egal auf welchem Gerät).
2. "Get Started" / "Sign Up" klicken.
3. Mit deinem **Google-Konto** einloggen (empfohlen — kein neues Passwort
   nötig, geht in Sekunden). Du kannst dein normales Google-Konto nehmen,
   das ist unabhängig von der separaten Frage rund um den Notification-
   Versand-Account aus der Mail-Diskussion.
4. Damit ist dein "Tailnet" (dein privates Netz) angelegt — es trägt einen
   Namen wie `dein-name.ts.net`, den brauchst du später wieder.

## Schritt 2: Tailscale auf dem Notebook installieren

1. Am Notebook (Windows): https://tailscale.com/download öffnen, "Download
   for Windows" klicken, Installer ausführen.
2. Nach der Installation öffnet sich ein Tailscale-Icon im System-Tray
   (unten rechts neben der Uhr).
3. Icon anklicken → "Log in" → mit demselben Google-Konto wie in Schritt 1
   einloggen.
4. Das Notebook ist jetzt Teil deines Tailnets. Icon anklicken zeigt dir
   seinen Tailscale-Namen (etwas wie `notebook.dein-name.ts.net`) und seine
   private IP (100.x.x.x) — **beides notieren**, brauchst du in Schritt 4.

## Schritt 3: Tailscale auf dem Handy installieren

1. Play Store öffnen (Android), nach "Tailscale" suchen, installieren.
2. App öffnen → "Log in" → dasselbe Google-Konto wie in Schritt 1.
3. Fertig — das Handy ist jetzt ebenfalls im selben Tailnet.

## Schritt 4: Verbindung testen

Am einfachsten mit einem Ping vom Handy zum Notebook:

1. Auf dem Handy in der Tailscale-App unter "My Devices" nachsehen, ob das
   Notebook mit grünem Punkt (online) angezeigt wird.
2. Testweise: sobald am Notebook irgendein lokaler Webserver auf einem Port
   läuft (das kommt erst mit der Steuer-Seite, aktuell also noch nichts zu
   testen) — dann würdest du vom Handy-Browser aus einfach
   `http://notebook.dein-name.ts.net:<PORT>` öffnen und die Seite erscheint,
   exakt wie im Heimnetz, auch über mobile Daten unterwegs.
3. Für den Moment reicht: grüner Punkt beim Notebook in der Handy-App =
   Verbindung steht, alles Weitere folgt mit der Steuer-Seite.

## Optional, aber empfohlen: MagicDNS aktivieren

Damit du `notebook.dein-name.ts.net` statt einer nackten IP-Adresse nutzen
kannst (einfacher zu merken, ändert sich nie):

1. https://login.tailscale.com/admin/dns öffnen (im Browser, eingeloggt).
2. "Enable MagicDNS" anklicken, falls nicht schon aktiv (ist es meistens
   standardmäßig).

## Was NICHT hier passiert

- Tailscale läuft unabhängig davon, ob TradingInfoTool gerade läuft oder
  nicht — einmal eingerichtet, bleibt das Notebook über sein Tailscale-
  Netzwerk erreichbar, solange es an und online ist.
- Kein Sicherheitsrisiko durch offene Ports nach außen — Tailscale exponiert
  nichts öffentlich, nur Geräte innerhalb deines eigenen Tailnets sehen sich.

## Die Steuer-Seite ist fertig (2026-07-11, siehe `remote/server.py`, Flask —
## nicht FastAPI wie ursprünglich hier vermerkt)

Sobald du am Notebook einen `REMOTE_ACCESS_TOKEN` in `.env` gesetzt hast
(Token erzeugen: `python -c "import secrets; print(secrets.token_urlsafe(32))"`,
siehe `.env.example`) und `main.py` läuft, erreichst du die Seite unter:

```
http://notebook.dein-name.ts.net:8765/?token=DEIN_TOKEN
```

Am besten diesen Link einmal auf dem Handy als Homescreen-Icon speichern
(Chrome: Menü → "Zum Startbildschirm hinzufügen").

## Windows-Firewall-Falle beim ersten Start

Sobald `main.py` mit gesetztem `REMOTE_ACCESS_TOKEN` zum ersten Mal startet,
bindet Python an Port 8765 — Windows Defender Firewall zeigt dabei einen
Sicherheitsdialog mit Checkboxen für "Private Netzwerke" und "Öffentliche
Netzwerke". **Wichtig:** Tailscales virtueller Netzwerkadapter wird von
Windows oft als "Öffentliches Netzwerk" eingestuft, obwohl es technisch ein
privates VPN ist — bestätigst du im Dialog nur "Privat", bleibt die Seite über
Tailscale unerreichbar, obwohl sie am Notebook selbst (`localhost:8765`)
einwandfrei funktioniert.

**Empfehlung:** den Tailscale-Adapter gezielt auf "Privat" setzen, statt sich
auf die Dialog-Checkbox zu verlassen (PowerShell als Administrator):
```powershell
Set-NetConnectionProfile -InterfaceAlias "Tailscale" -NetworkCategory Private
```
Das vermeidet zusätzlich, den Port versehentlich für ein echtes öffentliches
WLAN (z. B. Café) zu öffnen, falls das Notebook je dort mitläuft.

## Nächster Schritt

Keiner mehr offen für dieses Feature — nur noch am Notebook selbst
durchführen (Token setzen, App starten, Firewall-Dialog wie oben behandeln,
Link vom Handy aus testen).
