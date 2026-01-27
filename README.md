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

```bash
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/install.sh | bash
```

The installer will:
1. Find your BirdNET-Pi installation
2. Ask for your region and language
3. Download the appropriate models
4. Set up the classification service
5. Set up the web viewer

That's it! Classification starts automatically.

---

## Web Viewer

After installation, view your results at:

```
http://<your-pi-ip>:8088
```

The web viewer shows:
- Real-time classification results
- Statistics (total songs, calls, alarms)
- Filter by species or vocalization type
- Auto-refresh every 30 seconds

---

## Available Models

### North America (46 species, ~75 MB)

[**Download models**](https://drive.google.com/drive/folders/1zJ-rR6FTEkGjVPt77VHRmuQLZGmoHnaD)

Language: English (song/call/alarm)

American Robin, American Crow, American Goldfinch, Baltimore Oriole, Barn Swallow, Black-capped Chickadee, Blue Jay, Brown-headed Cowbird, Brown Thrasher, Canada Goose, Carolina Chickadee, Carolina Wren, Cedar Waxwing, Chipping Sparrow, Common Grackle, Common Yellowthroat, Dark-eyed Junco, Downy Woodpecker, Eastern Bluebird, Eastern Meadowlark, Eastern Phoebe, Eastern Towhee, European Starling, Gray Catbird, House Finch, House Sparrow, Indigo Bunting, Killdeer, Mallard, Mourning Dove, Northern Cardinal, Northern Flicker, Northern Mockingbird, Pine Warbler, Purple Finch, Red-bellied Woodpecker, Red-tailed Hawk, Red-winged Blackbird, Scarlet Tanager, Song Sparrow, Tree Swallow, Tufted Titmouse, White-breasted Nuthatch, White-throated Sparrow, Wood Thrush, Yellow-rumped Warbler

### Europe (199 species, ~7 GB)

[**Download models**](https://drive.google.com/drive/folders/1jtGWWTqWh4l0NmRZIHHAvzRTLjC0g--P)

Languages available:
- **Dutch/Nederlands**: zang/roep/alarm
- **German/Deutsch**: Gesang/Ruf/Alarm
- **English**: song/call/alarm

Trained with "ultimate" architecture for improved accuracy.

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
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/uninstall.sh | bash
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

- Report issues: [GitHub Issues](https://github.com/RonnyCHL/birdnet-vocalization/issues)
- Request species: Open an issue with the species name
- Training code: See [emsn-vocalization](https://github.com/RonnyCHL/emsn-vocalization)

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

```bash
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/install.sh | bash
```

De installer zal:
1. Je BirdNET-Pi installatie vinden
2. Vragen naar je regio en taal
3. De juiste modellen downloaden
4. De classificatie service instellen
5. De web viewer instellen

Klaar! Classificatie start automatisch.

---

## Web Viewer

Na installatie, bekijk je resultaten op:

```
http://<je-pi-ip>:8088
```

De web viewer toont:
- Real-time classificatie resultaten
- Statistieken (totaal zang, roep, alarm)
- Filter op soort of vocalisatie type
- Auto-refresh elke 30 seconden

---

## Beschikbare Modellen

### Europa (199 soorten, ~7 GB)

[**Download modellen**](https://drive.google.com/drive/folders/1jtGWWTqWh4l0NmRZIHHAvzRTLjC0g--P)

Beschikbare talen:
- **Nederlands**: zang/roep/alarm
- **Duits/Deutsch**: Gesang/Ruf/Alarm
- **Engels/English**: song/call/alarm

Getraind met "ultimate" architectuur voor verbeterde nauwkeurigheid.

### Noord-Amerika (46 soorten, ~75 MB)

[**Download modellen**](https://drive.google.com/drive/folders/1zJ-rR6FTEkGjVPt77VHRmuQLZGmoHnaD)

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
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/uninstall.sh | bash
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

- Meld problemen: [GitHub Issues](https://github.com/RonnyCHL/birdnet-vocalization/issues)
- Vraag soorten aan: Open een issue met de soortnaam
- Training code: Zie [emsn-vocalization](https://github.com/RonnyCHL/emsn-vocalization)

## Credits

- Training data: [Xeno-canto](https://xeno-canto.org/) vogel geluiden database
- Geïnspireerd door: [BirdNET-Pi](https://github.com/Nachtzuster/BirdNET-Pi)
- Auteur: Ronny Hullegie

## Licentie

MIT License - vrij te gebruiken, aan te passen en te verspreiden.
