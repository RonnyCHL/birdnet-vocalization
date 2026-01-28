# Sessie Samenvatting: BirdNET Vocalization Installer Fixes

**Datum:** 2026-01-28
**Onderwerp:** Installer bugfixes en documentatie voor birdnet-vocalization community addon

## Uitgevoerde Werkzaamheden

### 1. README Verbeterd
- Duidelijkere installatie-instructies met twee opties:
  - **Optie 1:** Interactief met `bash <(curl ...)` - toont menu voor regio selectie
  - **Optie 2:** Non-interactief met `curl ... | bash -s -- --region X`
- Troubleshooting sectie toegevoegd voor veelvoorkomende fouten
- Uitleg waarom `curl ... | bash` zonder `--region` niet werkt (stdin niet interactief)

### 2. Installer Bugfixes
- **Probleem:** Na uninstall + herinstallatie faalde `git pull` omdat `.git` directory ontbrak
- **Oplossing:** Installer detecteert nu drie scenario's:
  1. `.git` bestaat → `git fetch` + `git reset --hard`
  2. Directory bestaat zonder `.git` → repair met `git init` + fetch + tracking instellen
  3. Fresh install → normale `git clone`

### 3. Update Functie Fix
- **Probleem:** Web update faalde met "no tracking information" error
- **Oplossing:** `git pull` vervangen door `git pull origin master` om tracking issues te vermijden
- Installer stelt nu ook tracking in na repo repair

### 4. Community Feedback
- Gebruiker Svardsten53 meldde probleem met interactieve installatie
- Reactie geschreven met uitleg en correcte instructies
- Documentatie bijgewerkt naar aanleiding van feedback

## Geteste Scenario's
- Fresh install met USA region (46 modellen, ~75 MB)
- Fresh install met EU-Dutch region (196 modellen, ~7 GB)
- Herinstallatie na uninstall
- Web-based update via "Update Available" knop
- Edge browser compatibiliteit (eerder gefixt)

## Commits naar GitHub (birdnet-vocalization)
1. `docs: improve install instructions with troubleshooting section`
2. `fix: handle reinstall after uninstall with missing .git directory`
3. `fix: use explicit git pull origin master for updates`

## Huidige Status
- Installer werkt voor alle scenario's (fresh, update, repair)
- Web viewer werkt in Edge en Firefox
- EU modellen (196 soorten) succesvol gedownload en getest
- USA modellen (46 soorten) beschikbaar
- Wachten op feedback van community gebruiker

## Bestanden Gewijzigd (in birdnet-vocalization repo)
- `README.md` - Uitgebreide documentatie
- `install.sh` - Robuustere installatie logica
- `src/webviewer.py` - Fix voor update functie
