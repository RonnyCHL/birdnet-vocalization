# BirdNET Vocalization

**Add vocalization classification to your BirdNET-Pi: song, call, or alarm**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## What does it do?

When BirdNET-Pi detects a bird, this addon classifies the *type* of vocalization:

| Detection | Without | With Vocalization |
|-----------|---------|-------------------|
| American Robin | "American Robin detected" | "American Robin - **song** (93%)" |
| Northern Cardinal | "Northern Cardinal detected" | "Northern Cardinal - **call** (87%)" |
| Blue Jay | "Blue Jay detected" | "Blue Jay - **alarm** (91%)" |

### Why is this useful?

- **Song**: Bird is marking territory or attracting a mate
- **Call**: Contact calls, flock communication
- **Alarm**: Predator nearby! (cat, hawk, etc.)

## Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/install.sh | bash
```

The installer will:
1. Detect your BirdNET-Pi installation
2. Ask for your region (North America / Europe)
3. Download the appropriate models
4. Set up the background service

That's it! Classification starts automatically.

## How it Works

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  BirdNET-Pi     │     │  Vocalization        │     │ vocalization.db │
│  birds.db       │────▶│  Service             │────▶│ (separate DB)   │
│  (untouched!)   │     │                      │     │                 │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
```

**Important:** This addon *never* modifies BirdNET-Pi's files or database. All classification results are stored in a separate `vocalization.db`. BirdNET-Pi updates won't affect this addon.

## Available Models

### North America (46 species)
American Robin, American Crow, American Goldfinch, Baltimore Oriole, Barn Swallow, Black-capped Chickadee, Blue Jay, Brown-headed Cowbird, Brown Thrasher, Canada Goose, Carolina Chickadee, Carolina Wren, Cedar Waxwing, Chipping Sparrow, Common Grackle, Common Yellowthroat, Dark-eyed Junco, Downy Woodpecker, Eastern Bluebird, Eastern Meadowlark, Eastern Phoebe, Eastern Towhee, European Starling, Gray Catbird, House Finch, House Sparrow, Indigo Bunting, Killdeer, Mallard, Mourning Dove, Northern Cardinal, Northern Flicker, Northern Mockingbird, Pine Warbler, Purple Finch, Red-bellied Woodpecker, Red-tailed Hawk, Red-winged Blackbird, Scarlet Tanager, Song Sparrow, Tree Swallow, Tufted Titmouse, White-breasted Nuthatch, White-throated Sparrow, Wood Thrush, Yellow-rumped Warbler

### Europe (coming soon)
197 species available - contact for early access.

## Commands

```bash
# Check status
sudo systemctl status birdnet-vocalization

# View live logs
journalctl -u birdnet-vocalization -f

# Stop service
sudo systemctl stop birdnet-vocalization

# Start service
sudo systemctl start birdnet-vocalization

# Restart after update
sudo systemctl restart birdnet-vocalization
```

## View Results

Classification results are stored in SQLite:

```bash
sqlite3 /opt/birdnet-vocalization/data/vocalization.db \
  "SELECT common_name, vocalization_type, confidence
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

## Uninstall

```bash
sudo systemctl stop birdnet-vocalization
sudo systemctl disable birdnet-vocalization
sudo rm /etc/systemd/system/birdnet-vocalization.service
sudo rm -rf /opt/birdnet-vocalization
```

## Requirements

- BirdNET-Pi (working installation)
- Python 3.10+
- ~100 MB disk space (including models)
- Raspberry Pi 4 or newer recommended

## Technical Details

- **Models**: CNN classifiers trained on Xeno-canto audio data
- **Audio processing**: 3-second segments, 48kHz, mel spectrograms
- **Database**: SQLite (vocalization.db), linked by detection filename
- **Memory**: ~200 MB RAM when processing

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
