#!/bin/bash
#
# BirdNET Vocalization Installer
#
# Adds vocalization classification (song/call/alarm) to your BirdNET-Pi
#
# Usage (interactive):
#   bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh)
#
# Usage (non-interactive):
#   curl -sSL ... | bash -s -- --region 1   # North America - English
#   curl -sSL ... | bash -s -- --region 2   # Europe - Dutch
#   curl -sSL ... | bash -s -- --region 3   # Europe - German
#   curl -sSL ... | bash -s -- --region 4   # Europe - English
#

set -e

# Parse command line arguments
REGION_CHOICE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION_CHOICE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/RonnyCHL/birdnet-vocalization"
INSTALL_DIR="/opt/birdnet-vocalization"
HF_REPO="RonnyCHL/birdnet-vocalization-models"
SERVICE_NAME="birdnet-vocalization"

echo ""
echo -e "${BLUE}"
echo "    ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫"
echo ""
echo "        ╔══════════════════════════════════════════╗"
echo "        ║   🐦  BirdNET Vocalization Classifier    ║"
echo "        ╚══════════════════════════════════════════╝"
echo ""
echo "           Is it a song, a call, or an alarm?"
echo ""
echo "    ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫"
echo -e "${NC}"
echo ""
echo "  This addon adds vocalization type classification to your"
echo "  BirdNET-Pi. When BirdNET detects a bird, this classifier"
echo "  will tell you if it's singing, calling, or giving an alarm."
echo ""
echo "  • Song  = Territory marking, attracting mates"
echo "  • Call  = Contact calls, flock communication"
echo "  • Alarm = Predator nearby! (cat, hawk, etc.)"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please don't run as root. The script will use sudo when needed.${NC}"
    exit 1
fi

# Detect BirdNET-Pi installation
echo -e "${BLUE}[1/7] Detecting BirdNET-Pi installation...${NC}"

BIRDNET_DIR=""
for dir in "/home/$USER/BirdNET-Pi" "/home/pi/BirdNET-Pi" "/opt/BirdNET-Pi"; do
    if [ -d "$dir" ] && [ -f "$dir/scripts/birds.db" ]; then
        BIRDNET_DIR="$dir"
        break
    fi
done

if [ -z "$BIRDNET_DIR" ]; then
    echo -e "${RED}BirdNET-Pi not found!${NC}"
    echo "Please enter the path to your BirdNET-Pi installation:"
    read -r BIRDNET_DIR
    if [ ! -d "$BIRDNET_DIR" ] || [ ! -f "$BIRDNET_DIR/scripts/birds.db" ]; then
        echo -e "${RED}Invalid BirdNET-Pi directory${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Found BirdNET-Pi at: $BIRDNET_DIR${NC}"

# Select region
echo -e "${BLUE}[2/7] Select your region and language...${NC}"
echo ""
echo "  1) North America - English (46 species, ~75 MB)"
echo ""
echo "  Europe (219 species, ~8 GB):"
echo "  2) Dutch/Nederlands      (zang/roep/alarm)"
echo "  3) German/Deutsch        (Gesang/Ruf/Alarm)"
echo "  4) English               (song/call/alarm)"
echo "  5) Swedish/Svenska       (sång/läte/varningsläte)"
echo "  6) Norwegian/Norsk       (sang/kall/alarm)"
echo "  7) Danish/Dansk          (sang/kald/alarm)"
echo "  8) Finnish/Suomi         (laulu/kutsu/hälytys)"
echo "  9) French/Français       (chant/cri/alarme)"
echo " 10) Spanish/Español       (canto/reclamo/alarma)"
echo " 11) Italian/Italiano      (canto/richiamo/allarme)"
echo " 12) Polish/Polski         (śpiew/głos/alarm)"
echo " 13) Portuguese/Português  (canto/chamado/alarme)"
echo " 14) Czech/Čeština         (zpěv/hlas/poplach)"
echo " 15) Hungarian/Magyar      (ének/hívás/riasztás)"
echo " 16) Romanian/Română       (cântec/strigăt/alarmă)"
echo " 17) Slovak/Slovenčina     (spev/hlas/poplach)"
echo " 18) Ukrainian/Українська  (спів/поклик/тривога)"
echo " 19) Russian/Русский       (пение/позыв/тревога)"
echo ""

# If not provided via argument, ask interactively
if [ -z "$REGION_CHOICE" ]; then
    # Check if stdin is a terminal
    if [ -t 0 ]; then
        read -p "Enter choice [1-19]: " REGION_CHOICE
    else
        echo -e "${RED}Error: No region specified and not running interactively.${NC}"
        echo ""
        echo "Use one of these methods:"
        echo ""
        echo "  Interactive (recommended):"
        echo "    bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh)"
        echo ""
        echo "  Non-interactive:"
        echo "    curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh | bash -s -- --region 1"
        echo ""
        echo "  Regions: 1=USA, 2=NL, 3=DE, 4=EN, 5=SV, 6=NO, 7=DA, 8=FI, 9=FR, 10=ES, 11=IT, 12=PL, 13=PT, 14=CS, 15=HU, 16=RO, 17=SK, 18=UK, 19=RU"
        exit 1
    fi
fi

case $REGION_CHOICE in
    1)
        REGION="usa"
        LANGUAGE="en"
        MODEL_COUNT=46
        MODEL_SIZE="75 MB"
        HF_SUBDIR="usa"
        ;;
    2)
        REGION="europe"
        LANGUAGE="nl"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    3)
        REGION="europe"
        LANGUAGE="de"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    4)
        REGION="europe"
        LANGUAGE="en"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    5)
        REGION="europe"
        LANGUAGE="sv"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    6)
        REGION="europe"
        LANGUAGE="no"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    7)
        REGION="europe"
        LANGUAGE="da"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    8)
        REGION="europe"
        LANGUAGE="fi"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    9)
        REGION="europe"
        LANGUAGE="fr"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    10)
        REGION="europe"
        LANGUAGE="es"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    11)
        REGION="europe"
        LANGUAGE="it"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    12)
        REGION="europe"
        LANGUAGE="pl"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    13)
        REGION="europe"
        LANGUAGE="pt"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    14)
        REGION="europe"
        LANGUAGE="cs"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    15)
        REGION="europe"
        LANGUAGE="hu"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    16)
        REGION="europe"
        LANGUAGE="ro"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    17)
        REGION="europe"
        LANGUAGE="sk"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    18)
        REGION="europe"
        LANGUAGE="uk"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    19)
        REGION="europe"
        LANGUAGE="ru"
        MODEL_COUNT=219
        MODEL_SIZE="8 GB"
        HF_SUBDIR="getrainde_modellen_EMSN_scientific"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Selected: $REGION - $LANGUAGE ($MODEL_COUNT species, $MODEL_SIZE)${NC}"

# Clone repository first (we need the directory for venv)
echo -e "${BLUE}[3/7] Downloading vocalization classifier...${NC}"

if [ -d "$INSTALL_DIR/.git" ]; then
    # Valid git repo exists - update it
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git fetch origin
    git reset --hard origin/master
elif [ -d "$INSTALL_DIR" ]; then
    # Directory exists but no .git (e.g., after failed uninstall)
    echo "Repairing installation (missing git repo)..."
    cd "$INSTALL_DIR"
    git init
    git remote add origin "$REPO_URL"
    git fetch origin
    git reset --hard origin/master
    git branch --set-upstream-to=origin/master master
else
    # Fresh install
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$USER "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Create virtual environment and install dependencies
echo -e "${BLUE}[4/7] Setting up Python environment...${NC}"

VENV_DIR="$INSTALL_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip3"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Install packages in venv
echo "Installing Python packages (this may take a few minutes)..."
"$PIP_BIN" install --upgrade pip --quiet

# Detect architecture and install appropriate PyTorch version
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "armv7l" ]; then
    # Raspberry Pi (ARM) - use piwheels compatible version
    echo "Detected Raspberry Pi ($ARCH), installing compatible PyTorch..."
    "$PIP_BIN" install torch==2.0.1 --extra-index-url https://www.piwheels.org/simple --quiet
else
    # x86/x64 - use standard PyTorch
    "$PIP_BIN" install torch==2.0.1 --quiet
fi

"$PIP_BIN" install librosa scikit-image numpy huggingface_hub --quiet

# Download models from Hugging Face
echo -e "${BLUE}[5/7] Downloading models from Hugging Face ($MODEL_SIZE)...${NC}"

MODELS_DIR="$INSTALL_DIR/models"
mkdir -p "$MODELS_DIR"

if [ "$MODEL_SIZE" = "7 GB" ]; then
    echo -e "${YELLOW}Note: European models are ~7 GB. This may take 10-30 minutes...${NC}"
fi

echo "Downloading from huggingface.co/$HF_REPO..."

# Use huggingface_hub to download models
"$PYTHON_BIN" << PYEOF
from huggingface_hub import snapshot_download
import os

print("Starting download...")
try:
    snapshot_download(
        repo_id="$HF_REPO",
        repo_type="model",
        local_dir="$MODELS_DIR",
        allow_patterns=["$HF_SUBDIR/*.pt"],
        local_dir_use_symlinks=False
    )
    print("Download complete!")
except Exception as e:
    print(f"Download error: {e}")
    print("You can manually download from: https://huggingface.co/$HF_REPO")
PYEOF

# Move files from subdir to models dir and clean up
if [ -d "$MODELS_DIR/$HF_SUBDIR" ]; then
    mv "$MODELS_DIR/$HF_SUBDIR"/*.pt "$MODELS_DIR/" 2>/dev/null || true
    rm -rf "$MODELS_DIR/$HF_SUBDIR"
fi

# Remove HF cache files
rm -rf "$MODELS_DIR/.cache" "$MODELS_DIR/.huggingface" 2>/dev/null || true

# Verify models
MODEL_FILES=$(find "$MODELS_DIR" -maxdepth 1 -name "*.pt" 2>/dev/null | wc -l)
if [ "$MODEL_FILES" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No models found. Service will start but won't classify.${NC}"
    echo "Download models from: https://huggingface.co/$HF_REPO"
else
    echo -e "${GREEN}Downloaded $MODEL_FILES models${NC}"
fi

# Create data directory
mkdir -p "$INSTALL_DIR/data"

# Create systemd service
echo -e "${BLUE}[6/7] Setting up classification service...${NC}"

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=BirdNET Vocalization Classifier
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_BIN $INSTALL_DIR/src/service.py --birdnet-dir $BIRDNET_DIR --models-dir $MODELS_DIR --language $LANGUAGE
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}

# Setup web viewer service
echo -e "${BLUE}[7/7] Setting up web viewer...${NC}"

sudo tee /etc/systemd/system/${SERVICE_NAME}-viewer.service > /dev/null <<EOF
[Unit]
Description=BirdNET Vocalization Web Viewer
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_BIN $INSTALL_DIR/src/webviewer.py --data-dir $INSTALL_DIR/data --birdnet-dir $BIRDNET_DIR --models-dir $MODELS_DIR
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}-viewer
sudo systemctl start ${SERVICE_NAME}-viewer

# Add sudoers rule for passwordless service restart (needed for web update)
echo -e "${BLUE}Setting up auto-update permissions...${NC}"
SUDOERS_FILE="/etc/sudoers.d/birdnet-vocalization"
sudo tee $SUDOERS_FILE > /dev/null <<EOF
# Allow $USER to restart birdnet-vocalization services without password
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart birdnet-vocalization
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart birdnet-vocalization-viewer
EOF
sudo chmod 440 $SUDOERS_FILE

# Done!
IP_ADDR=$(hostname -I | awk '{print $1}')
echo ""
echo -e "${GREEN}"
echo "    ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫"
echo ""
echo "        ╔══════════════════════════════════════════╗"
echo "        ║   ✓  Installation Complete!              ║"
echo "        ╚══════════════════════════════════════════╝"
echo ""
echo "    ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫ ♪ ♫"
echo -e "${NC}"
echo ""
echo "  The vocalization classifier is now running!"
echo ""
echo -e "  ${GREEN}🌐 Web Viewer: http://${IP_ADDR}:8088${NC}"
echo ""
echo "  ┌─────────────────────────────────────────────────────────┐"
echo "  │  Commands:                                              │"
echo "  │    Status:  sudo systemctl status ${SERVICE_NAME}    │"
echo "  │    Logs:    journalctl -u ${SERVICE_NAME} -f         │"
echo "  └─────────────────────────────────────────────────────────┘"
echo ""
echo "  Language: $LANGUAGE"
echo "  Models:   $MODEL_FILES species"
echo "  Data:     $INSTALL_DIR/data/vocalization.db"
echo ""
echo -e "  ${BLUE}Thank you for using BirdNET Vocalization!${NC}"
echo "  Report issues: https://github.com/RonnyCHL/birdnet-vocalization/issues"
echo ""
