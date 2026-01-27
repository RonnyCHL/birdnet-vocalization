# BirdNET Vocalization

**Add vocalization classification to your BirdNET-Pi: song, call, or alarm**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **Note:** We hope this feature will eventually be integrated into BirdNET-Pi itself. Until then, this addon provides the functionality as a separate service that works alongside your existing BirdNET-Pi installation.

## What does it do?

When BirdNET-Pi detects a bird, this addon classifies the *type* of vocalization:

| Detection | Without | With Vocalization |
|-----------|---------|-------------------|
| American Robin | "American Robin detected" | "American Robin - **song** (93%)" |
| Merel | "Merel gedetecteerd" | "Merel - **zang** (91%)" |
| Blue Jay | "Blue Jay detected" | "Blue Jay - **alarm** (87%)" |

### Why is this useful?

- **Song/Zang**: Bird is marking territory or attracting a mate
- **Call/Roep**: Contact calls, flock communication
- **Alarm**: Predator nearby! (cat, hawk, etc.)

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/install.sh | bash
```

The installer will:
1. Detect your BirdNET-Pi installation
2. Ask for your region and language
3. Download the appropriate models
4. Set up the classification service
5. Set up the web viewer

That's it! Classification starts automatically.

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

## How it Works

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  BirdNET-Pi     │     │  Vocalization        │     │ vocalization.db │
│  birds.db       │────▶│  Service             │────▶│ (separate DB)   │
│  (untouched!)   │     │                      │     │                 │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Web Viewer     │
                        │  :8088          │
                        └─────────────────┘
```

**Important:** This addon *never* modifies BirdNET-Pi's files or database. All classification results are stored in a separate `vocalization.db`. BirdNET-Pi updates won't affect this addon.

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

## View Results

### Web Viewer (recommended)
Open `http://<your-pi-ip>:8088` in your browser.

### SQLite Query
```bash
sqlite3 /opt/birdnet-vocalization/data/vocalization.db \
  "SELECT common_name, vocalization_type_display, confidence
   FROM vocalizations
   ORDER BY classified_at DESC
   LIMIT 10"
```

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

## Uninstall

One-liner:
```bash
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/uninstall.sh | bash
```

Or manually:
```bash
sudo systemctl stop birdnet-vocalization birdnet-vocalization-viewer
sudo systemctl disable birdnet-vocalization birdnet-vocalization-viewer
sudo rm /etc/systemd/system/birdnet-vocalization*.service
sudo rm -rf /opt/birdnet-vocalization
```

## Requirements

- BirdNET-Pi (working installation)
- Python 3.10+
- Disk space: ~100 MB (North America) or ~8 GB (Europe)
- Raspberry Pi 4 or newer recommended

## Technical Details

- **Models**: CNN classifiers trained on Xeno-canto audio data
- **Architecture**: 3-layer CNN (standard) or 4-layer CNN (ultimate/Europe)
- **Audio processing**: 3-second segments, 48kHz, mel spectrograms
- **Database**: SQLite (vocalization.db), linked by detection filename
- **Memory**: ~200 MB RAM when processing

## BirdNET-Pi Integration

We hope vocalization classification will become a native feature in BirdNET-Pi. If you'd like to see this happen, consider:

- Sharing your experience with this addon
- Requesting the feature in [BirdNET-Pi discussions](https://github.com/mcguirepr89/BirdNET-Pi/discussions)

Until then, this addon provides a safe, non-invasive way to add vocalization classification.

## Contributing

- Report issues: [GitHub Issues](https://github.com/RonnyCHL/birdnet-vocalization/issues)
- Request species: Open an issue with the species name
- Training code: See [emsn-vocalization](https://github.com/RonnyCHL/emsn-vocalization)

## Credits

- Training data: [Xeno-canto](https://xeno-canto.org/) bird sound database
- Inspired by: [BirdNET-Pi](https://github.com/mcguirepr89/BirdNET-Pi)
- Author: Ronny Hullegie

## License

MIT License - free to use, modify, and distribute.
