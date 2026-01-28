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
MODELS_URL_USA="https://drive.google.com/drive/folders/1zJ-rR6FTEkGjVPt77VHRmuQLZGmoHnaD"
MODELS_FOLDER_ID_USA="1zJ-rR6FTEkGjVPt77VHRmuQLZGmoHnaD"
MODELS_URL_EUROPE="https://drive.google.com/drive/folders/1jtGWWTqWh4l0NmRZIHHAvzRTLjC0g--P"
MODELS_FOLDER_ID_EUROPE="1jtGWWTqWh4l0NmRZIHHAvzRTLjC0g--P"
SERVICE_NAME="birdnet-vocalization"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       BirdNET Vocalization Classifier Installer            ║"
echo "║                                                            ║"
echo "║  Adds song/call/alarm classification to BirdNET-Pi         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

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
echo -e "${BLUE}[2/7] Select your region...${NC}"
echo ""
echo "  1) North America - English (46 species, ~75 MB)"
echo "  2) Europe - Dutch/Nederlands (199 species, ~7 GB)"
echo "  3) Europe - German/Deutsch (199 species, ~7 GB)"
echo "  4) Europe - English (199 species, ~7 GB)"
echo ""

# If not provided via argument, ask interactively
if [ -z "$REGION_CHOICE" ]; then
    # Check if stdin is a terminal
    if [ -t 0 ]; then
        read -p "Enter choice [1-4]: " REGION_CHOICE
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
        echo "  Regions: 1=USA-English, 2=Europe-Dutch, 3=Europe-German, 4=Europe-English"
        exit 1
    fi
fi

case $REGION_CHOICE in
    1)
        REGION="usa"
        LANGUAGE="en"
        MODEL_COUNT=46
        MODEL_SIZE="75 MB"
        MODELS_FOLDER_ID="$MODELS_FOLDER_ID_USA"
        MODELS_URL="$MODELS_URL_USA"
        ;;
    2)
        REGION="europe"
        LANGUAGE="nl"
        MODEL_COUNT=199
        MODEL_SIZE="7 GB"
        MODELS_FOLDER_ID="$MODELS_FOLDER_ID_EUROPE"
        MODELS_URL="$MODELS_URL_EUROPE"
        ;;
    3)
        REGION="europe"
        LANGUAGE="de"
        MODEL_COUNT=199
        MODEL_SIZE="7 GB"
        MODELS_FOLDER_ID="$MODELS_FOLDER_ID_EUROPE"
        MODELS_URL="$MODELS_URL_EUROPE"
        ;;
    4)
        REGION="europe"
        LANGUAGE="en"
        MODEL_COUNT=199
        MODEL_SIZE="7 GB"
        MODELS_FOLDER_ID="$MODELS_FOLDER_ID_EUROPE"
        MODELS_URL="$MODELS_URL_EUROPE"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Selected: $REGION - $LANGUAGE ($MODEL_COUNT species, $MODEL_SIZE)${NC}"

# Clone repository first (we need the directory for venv)
echo -e "${BLUE}[3/7] Downloading vocalization classifier...${NC}"

if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull || true
else
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$USER "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Create virtual environment and install dependencies
echo -e "${BLUE}[4/7] Setting up Python environment...${NC}"

VENV_DIR="$INSTALL_DIR/venv"
PYTHON_BIN="$VENV_DIR/bin/python3"
PIP_BIN="$VENV_DIR/bin/pip3"
GDOWN_BIN="$VENV_DIR/bin/gdown"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Install packages in venv
echo "Installing Python packages (this may take a few minutes)..."
"$PIP_BIN" install --upgrade pip --quiet
"$PIP_BIN" install torch librosa scikit-image numpy gdown --quiet

# Download models
echo -e "${BLUE}[5/7] Downloading models ($MODEL_SIZE)...${NC}"

MODELS_DIR="$INSTALL_DIR/models"
mkdir -p "$MODELS_DIR"

echo "Downloading models from Google Drive..."
if [ "$MODEL_SIZE" = "7 GB" ]; then
    echo -e "${YELLOW}Note: European models are ~7 GB. This may take 10-30 minutes...${NC}"
fi

# Use --remaining-ok to handle folders with >50 files
# Run multiple times to get all files (gdown limitation)
DOWNLOAD_ATTEMPTS=5
for i in $(seq 1 $DOWNLOAD_ATTEMPTS); do
    echo "Download pass $i of $DOWNLOAD_ATTEMPTS..."
    "$GDOWN_BIN" --folder "$MODELS_FOLDER_ID" -O "$MODELS_DIR/" --remaining-ok 2>&1 | grep -v "^Processing\|^Retrieving\|^Downloading" || true

    # Check if we have enough models
    CURRENT_MODELS=$(find "$MODELS_DIR" -name "*.pt" 2>/dev/null | wc -l)
    if [ "$CURRENT_MODELS" -ge "$MODEL_COUNT" ]; then
        echo -e "${GREEN}Downloaded all $CURRENT_MODELS models${NC}"
        break
    fi
    echo "Found $CURRENT_MODELS models so far..."
done

# Final check
MODEL_FILES=$(find "$MODELS_DIR" -name "*.pt" 2>/dev/null | wc -l)
if [ "$MODEL_FILES" -lt "$MODEL_COUNT" ]; then
    echo -e "${YELLOW}Downloaded $MODEL_FILES of $MODEL_COUNT models.${NC}"
    echo ""
    echo "Some models may be missing. You can manually download from:"
    echo -e "${BLUE}$MODELS_URL${NC}"
    echo ""
    echo "And place additional .pt files in: $MODELS_DIR/"
    echo ""
    if [ -t 0 ]; then
        read -p "Press Enter to continue anyway..."
    fi
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
ExecStart=$PYTHON_BIN $INSTALL_DIR/src/webviewer.py --data-dir $INSTALL_DIR/data
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}-viewer
sudo systemctl start ${SERVICE_NAME}-viewer

# Done!
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
echo -e "║              Installation Complete!                        ║"
echo -e "╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "The vocalization classifier is now running!"
echo ""
echo -e "${GREEN}Web Viewer: http://$(hostname -I | awk '{print $1}'):8088${NC}"
echo ""
echo "Commands:"
echo "  Status:   sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:     journalctl -u ${SERVICE_NAME} -f"
echo "  Viewer:   sudo systemctl status ${SERVICE_NAME}-viewer"
echo ""
echo "Data stored in: $INSTALL_DIR/data/vocalization.db"
echo "Language: $LANGUAGE"
echo ""
echo -e "${BLUE}Thank you for using BirdNET Vocalization!${NC}"
echo "Report issues: https://github.com/RonnyCHL/birdnet-vocalization/issues"
