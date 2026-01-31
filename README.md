# BirdNET Vocalization

**Add vocalization classification to your BirdNET-Pi: song, call, or alarm**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Note:** We hope this feature will eventually be integrated into BirdNET-Pi itself. Until then, this addon provides the functionality as a separate service that works alongside your existing BirdNET-Pi installation.

---

## Prerequisites

**You need a working BirdNET-Pi installation first!**

This addon does NOT replace BirdNET-Pi. It adds vocalization type classification to an existing BirdNET-Pi system.

| Component | What it does | Required? |
|-----------|--------------|-----------|
| [BirdNET-Pi](https://github.com/Nachtzuster/BirdNET-Pi) | Identifies bird **species** from audio | **Yes, install first** |
| This addon | Identifies vocalization **type** (song/call/alarm) | Optional |

```
Your Raspberry Pi
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  BirdNET-Pi (required)          This Addon (optional)           │
│  ┌─────────────────────┐        ┌─────────────────────┐        │
│  │ 1. Microphone       │        │ 4. Reads birds.db   │        │
│  │ 2. Records audio    │        │ 5. Loads audio file │        │
│  │ 3. "It's a Robin!"  │───────▶│ 6. CNN analysis     │        │
│  │    → birds.db       │        │ 7. "It's a song!"   │        │
│  │                     │        │    → vocalization.db│        │
│  └─────────────────────┘        └──────────┬──────────┘        │
│         ▲                                  │                    │
│         │                                  ▼                    │
│    Never modified                   Web Viewer :8088            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## What does it do?

When BirdNET-Pi detects a bird, this addon classifies the *type* of vocalization:

| Detection | Without Addon | With Addon |
|-----------|---------------|------------|
| American Robin | "American Robin detected" | "American Robin - **song** (93%)" |
| Merel | "Merel gedetecteerd" | "Merel - **zang** (91%)" |
| Blue Jay | "Blue Jay detected" | "Blue Jay - **alarm** (87%)" |

### Why is this useful?

- **Song/Zang/Gesang**: Bird is marking territory or attracting a mate
- **Call/Roep/Ruf**: Contact calls, flock communication
- **Alarm**: Predator nearby! (cat, hawk, etc.)

---

## Quick Install

### Option 1: Interactive Install (recommended)

This downloads the script first, then runs it - allowing you to select your region from the menu:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh)
```

You will see a menu:
```
  1) North America - English (46 species, ~75 MB)
  2) Europe - Dutch/Nederlands (219 species, ~8 GB)
  3) Europe - German/Deutsch (219 species, ~8 GB)
  4) Europe - English (219 species, ~8 GB)

Enter choice [1-4]:
```

### Option 2: Non-interactive Install

If you know which region you want, you can specify it directly. Note the `bash -s -- --region X` syntax:

```bash
# North America - English
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 1

# Europe - Dutch
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 2

# Europe - German
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 3

# Europe - English
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 4
```

> **Note:** Piping directly to bash (`curl ... | bash`) without `--region` will NOT work interactively. Use the `bash <(curl ...)` syntax for interactive installs.

### What the installer does
1. Find your BirdNET-Pi installation
2. Ask for your region and language (if not specified)
3. Download the appropriate models (~75 MB for USA, ~7 GB for Europe)
4. Set up the classification service
5. Set up the web viewer

That's it! Classification starts automatically.

---

## Troubleshooting

### "Error: No region specified and not running interactively"

This happens when you pipe directly to bash without specifying a region:
```bash
# This will NOT work:
curl -sSL .../install.sh | bash
```

**Solution:** Use one of these methods:

1. **Interactive (recommended):**
   ```bash
   bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh)
   ```

2. **Non-interactive with region:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 2
   ```

### 404 Error when downloading

Make sure you're using the correct URL. The install script is at:
```
https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh
```

### Service not starting

Check the logs:
```bash
journalctl -u birdnet-vocalization -e
```

Common issues:
- BirdNET-Pi not found: Specify path with `--birdnet-dir`
- Models not downloaded: Check `/opt/birdnet-vocalization/models/`

---

## Web Viewer

After installation, view your results at:

```
http://<your-pi-ip>:8088
```

### Overview Tab
- Real-time classification results with audio playback
- Statistics (total songs, calls, alarms, model coverage)
- Charts: vocalizations over time, top 10 species
- Filter by species or vocalization type
- **Feedback buttons** (👍/👎) to rate classification accuracy

### Behavior Insights Tab
- **Weekly trends**: Compare song/call/alarm counts vs last week
- **Alerts**: Automatic detection of unusual patterns
  - Alarm spikes (300%+ increase in 24h)
  - Unusual silence (normally active species not heard)
- **Hourly activity**: When are birds most active? (dawn chorus visible!)
- **Species breakdown**: % song/call/alarm per species (top 15)

---

## Available Models

### North America (46 species, ~75 MB)

[**Download models**](https://huggingface.co/RonnyCHL/birdnet-vocalization-models)

Language: English (song/call/alarm)

American Robin, American Crow, American Goldfinch, Baltimore Oriole, Barn Swallow, Black-capped Chickadee, Blue Jay, Brown-headed Cowbird, Brown Thrasher, Canada Goose, Carolina Chickadee, Carolina Wren, Cedar Waxwing, Chipping Sparrow, Common Grackle, Common Yellowthroat, Dark-eyed Junco, Downy Woodpecker, Eastern Bluebird, Eastern Meadowlark, Eastern Phoebe, Eastern Towhee, European Starling, Gray Catbird, House Finch, House Sparrow, Indigo Bunting, Killdeer, Mallard, Mourning Dove, Northern Cardinal, Northern Flicker, Northern Mockingbird, Pine Warbler, Purple Finch, Red-bellied Woodpecker, Red-tailed Hawk, Red-winged Blackbird, Scarlet Tanager, Song Sparrow, Tree Swallow, Tufted Titmouse, White-breasted Nuthatch, White-throated Sparrow, Wood Thrush, Yellow-rumped Warbler

### Europe (219 species, ~8 GB)

[**Download models**](https://huggingface.co/RonnyCHL/birdnet-vocalization-models)

Languages available:
- **Dutch/Nederlands**: zang/roep/alarm
- **German/Deutsch**: Gesang/Ruf/Alarm
- **English**: song/call/alarm

Trained with "ultimate" architecture for improved accuracy.

**Includes 24 Nordic/Scandinavian species:**
- **Owls:** Great Grey Owl, Ural Owl, Tengmalm's Owl, Pygmy Owl, Snowy Owl, Northern Hawk-Owl
- **Grouse:** Western Capercaillie, Black Grouse, Rock Ptarmigan, Willow Ptarmigan
- **Crossbills:** Two-barred Crossbill, Parrot Crossbill
- **Corvids:** Siberian Jay, Spotted Nutcracker
- **Others:** Tree Sparrow, Siberian Tit, White-throated Dipper, Three-toed Woodpecker, White-backed Woodpecker, Red-throated Pipit, Lapland Longspur, Rustic Bunting, Common Rosefinch, Red-breasted Flycatcher

---

## Commands

```bash
# Check classification service
sudo systemctl status birdnet-vocalization

# Check web viewer
sudo systemctl status birdnet-vocalization-viewer

# View live logs
journalctl -u birdnet-vocalization -f

# Restart services
sudo systemctl restart birdnet-vocalization
sudo systemctl restart birdnet-vocalization-viewer
```

---

## Configuration

Edit the service if needed:

```bash
sudo systemctl edit birdnet-vocalization
```

Options:
- `--birdnet-dir` - Path to BirdNET-Pi (default: /home/pi/BirdNET-Pi)
- `--models-dir` - Path to models (default: /opt/birdnet-vocalization/models)
- `--interval` - Check interval in seconds (default: 30)
- `--language` - Output language: en, nl, de (default: en)

---

## Uninstall

```bash
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/uninstall.sh | bash
```

Your BirdNET-Pi installation will not be affected.

---

## Requirements

- **BirdNET-Pi** (working installation) - [Install first](https://github.com/Nachtzuster/BirdNET-Pi)
- Python 3.10+
- Disk space: ~100 MB (North America) or ~8 GB (Europe)
- Raspberry Pi 4 or newer recommended

---

## BirdNET-Pi Integration

We hope vocalization classification will become a native feature in BirdNET-Pi. If you'd like to see this happen, consider:

- Sharing your experience with this addon
- Requesting the feature in [BirdNET-Pi discussions](https://github.com/Nachtzuster/BirdNET-Pi/discussions)

Until then, this addon provides a safe, non-invasive way to add vocalization classification.

---

## Contributing

We welcome contributions! Use the issue templates for:

- **🐛 Bug Report**: Something not working? [Report it](https://github.com/RonnyCHL/birdnet-vocalization/issues/new?template=bug_report.yml)
- **🐦 Species Request**: Want a new bird species? [Request it](https://github.com/RonnyCHL/birdnet-vocalization/issues/new?template=species_request.yml)
- **📊 Model Feedback**: Classification wrong? [Let us know](https://github.com/RonnyCHL/birdnet-vocalization/issues/new?template=model_feedback.yml)

Training code: See [emsn-vocalization](https://github.com/RonnyCHL/emsn-vocalization)

## Credits

- Training data: [Xeno-canto](https://xeno-canto.org/) bird sound database
- Inspired by: [BirdNET-Pi](https://github.com/Nachtzuster/BirdNET-Pi)
- Author: Ronny Hullegie

## License

MIT License - free to use, modify, and distribute.

---

# BirdNET Vocalization (Nederlands)

**Voeg vocalisatie classificatie toe aan je BirdNET-Pi: zang, roep of alarm**

---

## Vereisten

**Je hebt eerst een werkende BirdNET-Pi installatie nodig!**

Deze addon vervangt BirdNET-Pi NIET. Het voegt vocalisatie type classificatie toe aan een bestaand BirdNET-Pi systeem.

| Component | Wat het doet | Vereist? |
|-----------|--------------|----------|
| [BirdNET-Pi](https://github.com/Nachtzuster/BirdNET-Pi) | Identificeert vogel **soort** uit audio | **Ja, eerst installeren** |
| Deze addon | Identificeert vocalisatie **type** (zang/roep/alarm) | Optioneel |

```
Jouw Raspberry Pi
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  BirdNET-Pi (vereist)           Deze Addon (optioneel)          │
│  ┌─────────────────────┐        ┌─────────────────────┐        │
│  │ 1. Microfoon        │        │ 4. Leest birds.db   │        │
│  │ 2. Neemt audio op   │        │ 5. Laadt audiobestand│       │
│  │ 3. "Het is een      │───────▶│ 6. CNN analyse      │        │
│  │    Merel!"          │        │ 7. "Het is zang!"   │        │
│  │    → birds.db       │        │    → vocalization.db│        │
│  └─────────────────────┘        └──────────┬──────────┘        │
│         ▲                                  │                    │
│         │                                  ▼                    │
│    Wordt nooit aangepast            Web Viewer :8088            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Wat doet het?

Wanneer BirdNET-Pi een vogel detecteert, classificeert deze addon het *type* vocalisatie:

| Detectie | Zonder Addon | Met Addon |
|----------|--------------|-----------|
| Merel | "Merel gedetecteerd" | "Merel - **zang** (91%)" |
| Koolmees | "Koolmees gedetecteerd" | "Koolmees - **roep** (87%)" |
| Gaai | "Gaai gedetecteerd" | "Gaai - **alarm** (89%)" |

### Waarom is dit nuttig?

- **Zang**: Vogel markeert territorium of trekt partner aan
- **Roep**: Contact roepen, communicatie binnen groep
- **Alarm**: Roofdier in de buurt! (kat, sperwer, etc.)

---

## Snelle Installatie

### Optie 1: Interactieve Installatie (aanbevolen)

Dit downloadt het script eerst, dan voert het uit - zodat je je regio kunt kiezen:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh)
```

Je ziet dan een menu:
```
  1) North America - English (46 species, ~75 MB)
  2) Europe - Dutch/Nederlands (219 species, ~8 GB)
  3) Europe - German/Deutsch (219 species, ~8 GB)
  4) Europe - English (219 species, ~8 GB)

Enter choice [1-4]:
```

### Optie 2: Non-interactieve Installatie

Als je al weet welke regio je wilt, kun je het direct specificeren. Let op de `bash -s -- --region X` syntax:

```bash
# Europa - Nederlands
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 2

# Europa - Duits
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 3

# Europa - Engels
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 4

# Noord-Amerika - Engels
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 1
```

> **Let op:** Direct pipen naar bash (`curl ... | bash`) zonder `--region` werkt NIET interactief. Gebruik de `bash <(curl ...)` syntax voor interactieve installaties.

### Wat de installer doet
1. Je BirdNET-Pi installatie vinden
2. Vragen naar je regio en taal (indien niet opgegeven)
3. De juiste modellen downloaden (~75 MB voor USA, ~7 GB voor Europa)
4. De classificatie service instellen
5. De web viewer instellen

Klaar! Classificatie start automatisch.

---

## Problemen Oplossen

### "Error: No region specified and not running interactively"

Dit gebeurt als je direct naar bash piped zonder regio:
```bash
# Dit werkt NIET:
curl -sSL .../install.sh | bash
```

**Oplossing:** Gebruik een van deze methodes:

1. **Interactief (aanbevolen):**
   ```bash
   bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh)
   ```

2. **Non-interactief met regio:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 2
   ```

### 404 Error bij downloaden

Zorg dat je de juiste URL gebruikt. Het install script staat op:
```
https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh
```

### Service start niet

Check de logs:
```bash
journalctl -u birdnet-vocalization -e
```

Veelvoorkomende problemen:
- BirdNET-Pi niet gevonden: Specificeer pad met `--birdnet-dir`
- Modellen niet gedownload: Check `/opt/birdnet-vocalization/models/`

---

## Web Viewer

Na installatie, bekijk je resultaten op:

```
http://<je-pi-ip>:8088
```

### Overzicht Tab
- Real-time classificatie resultaten met audio afspelen
- Statistieken (totaal zang, roep, alarm, model dekking)
- Grafieken: vocalisaties over tijd, top 10 soorten
- Filter op soort of vocalisatie type
- **Feedback knoppen** (👍/👎) om classificatie nauwkeurigheid te beoordelen

### Gedragsinzichten Tab
- **Wekelijkse trends**: Vergelijk zang/roep/alarm met vorige week
- **Alerts**: Automatische detectie van ongewone patronen
  - Alarm pieken (300%+ toename in 24u)
  - Ongebruikelijke stilte (normaal actieve soort niet gehoord)
- **Activiteit per uur**: Wanneer zijn vogels het meest actief? (ochtendkoor zichtbaar!)
- **Soort breakdown**: % zang/roep/alarm per soort (top 15)

---

## Beschikbare Modellen

### Europa (219 soorten, ~8 GB)

[**Download modellen**](https://huggingface.co/RonnyCHL/birdnet-vocalization-models)

Beschikbare talen:
- **Nederlands**: zang/roep/alarm
- **Duits/Deutsch**: Gesang/Ruf/Alarm
- **Engels/English**: song/call/alarm

Getraind met "ultimate" architectuur voor verbeterde nauwkeurigheid.

**Inclusief 24 Noordse/Scandinavische soorten:**
- **Uilen:** Laplanduil, Oeraluil, Ruigpootuil, Dwerguil, Sneeuwuil, Sperweruil
- **Hoenders:** Auerhoen, Korhoen, Alpensneeuwhoen, Moerassneeuwhoen
- **Kruisbekken:** Witbandkruisbek, Grote Kruisbek
- **Kraaiachtigen:** Taigagaai, Notenkraker
- **Overig:** Ringmus, Bruinkopmees, Waterspreeuw, Drieteenspecht, Witrugspecht, Roodkeelpieper, IJsgors, Bosgors, Roodmus, Kleine Vliegenvanger

### Noord-Amerika (46 soorten, ~75 MB)

[**Download modellen**](https://huggingface.co/RonnyCHL/birdnet-vocalization-models)

Taal: Engels (song/call/alarm)

---

## Commando's

```bash
# Check classificatie service
sudo systemctl status birdnet-vocalization

# Check web viewer
sudo systemctl status birdnet-vocalization-viewer

# Bekijk live logs
journalctl -u birdnet-vocalization -f

# Herstart services
sudo systemctl restart birdnet-vocalization
sudo systemctl restart birdnet-vocalization-viewer
```

---

## Configuratie

Bewerk de service indien nodig:

```bash
sudo systemctl edit birdnet-vocalization
```

Opties:
- `--birdnet-dir` - Pad naar BirdNET-Pi (standaard: /home/pi/BirdNET-Pi)
- `--models-dir` - Pad naar modellen (standaard: /opt/birdnet-vocalization/models)
- `--interval` - Check interval in seconden (standaard: 30)
- `--language` - Output taal: en, nl, de (standaard: en)

---

## Verwijderen

```bash
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/uninstall.sh | bash
```

Je BirdNET-Pi installatie wordt niet aangetast.

---

## Vereisten

- **BirdNET-Pi** (werkende installatie) - [Eerst installeren](https://github.com/Nachtzuster/BirdNET-Pi)
- Python 3.10+
- Schijfruimte: ~100 MB (Noord-Amerika) of ~8 GB (Europa)
- Raspberry Pi 4 of nieuwer aanbevolen

---

## BirdNET-Pi Integratie

We hopen dat vocalisatie classificatie een native functie wordt in BirdNET-Pi. Als je dit wilt ondersteunen:

- Deel je ervaring met deze addon
- Vraag de functie aan in [BirdNET-Pi discussions](https://github.com/Nachtzuster/BirdNET-Pi/discussions)

Tot die tijd biedt deze addon een veilige, niet-invasieve manier om vocalisatie classificatie toe te voegen.

---

## Bijdragen

We verwelkomen bijdragen! Gebruik de issue templates voor:

- **🐛 Bug Melding**: Iets werkt niet? [Meld het](https://github.com/RonnyCHL/birdnet-vocalization/issues/new?template=bug_report.yml)
- **🐦 Soort Aanvraag**: Wil je een nieuwe vogelsoort? [Vraag het aan](https://github.com/RonnyCHL/birdnet-vocalization/issues/new?template=species_request.yml)
- **📊 Model Feedback**: Classificatie fout? [Laat het weten](https://github.com/RonnyCHL/birdnet-vocalization/issues/new?template=model_feedback.yml)

Training code: Zie [emsn-vocalization](https://github.com/RonnyCHL/emsn-vocalization)

## Credits

- Training data: [Xeno-canto](https://xeno-canto.org/) vogel geluiden database
- Geïnspireerd door: [BirdNET-Pi](https://github.com/Nachtzuster/BirdNET-Pi)
- Auteur: Ronny Hullegie

## Licentie

MIT License - vrij te gebruiken, aan te passen en te verspreiden.
