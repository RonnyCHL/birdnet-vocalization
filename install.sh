#!/bin/bash
#
# BirdNET Vocalization Installer
#
# Adds vocalization classification (song/call/alarm) to your BirdNET-Pi
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/install.sh | bash
#

set -e

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
echo -e "${BLUE}[1/6] Detecting BirdNET-Pi installation...${NC}"

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
echo -e "${BLUE}[2/6] Select your region...${NC}"
echo ""
echo "  1) North America (46 species, ~75 MB)"
echo "  2) Europe (coming soon)"
echo ""
read -p "Enter choice [1-2]: " REGION_CHOICE

case $REGION_CHOICE in
    1)
        REGION="usa"
        MODEL_COUNT=46
        MODEL_SIZE="75 MB"
        ;;
    2)
        echo -e "${YELLOW}European models coming soon! Using North America for now.${NC}"
        REGION="usa"
        MODEL_COUNT=46
        MODEL_SIZE="75 MB"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Selected: $REGION ($MODEL_COUNT species, $MODEL_SIZE)${NC}"

# Install dependencies
echo -e "${BLUE}[3/6] Installing dependencies...${NC}"

# Check if pip packages are installed
PACKAGES="torch librosa scikit-image numpy"
MISSING=""

for pkg in $PACKAGES; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING="$MISSING $pkg"
    fi
done

if [ -n "$MISSING" ]; then
    echo "Installing Python packages:$MISSING"
    pip3 install --user $MISSING
fi

# Clone repository
echo -e "${BLUE}[4/6] Downloading vocalization classifier...${NC}"

if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    sudo -u $USER git pull
else
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$USER "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Download models
echo -e "${BLUE}[5/6] Downloading models ($MODEL_SIZE)...${NC}"

MODELS_DIR="$INSTALL_DIR/models"
mkdir -p "$MODELS_DIR"

# Install gdown if not available
if ! command -v gdown &> /dev/null; then
    echo "Installing gdown for Google Drive download..."
    pip3 install --user gdown --quiet
fi

# Download models
echo "Downloading models from Google Drive..."
if command -v gdown &> /dev/null; then
    gdown --folder "$MODELS_FOLDER_ID_USA" -O "$MODELS_DIR/" --quiet 2>/dev/null || {
        echo -e "${YELLOW}Automatic download failed.${NC}"
        echo ""
        echo "Please manually download models from:"
        echo -e "${BLUE}$MODELS_URL_USA${NC}"
        echo ""
        echo "And place the .pt files in: $MODELS_DIR/"
        echo ""
        read -p "Press Enter after downloading models to continue..."
    }
else
    echo -e "${YELLOW}Could not install gdown.${NC}"
    echo ""
    echo "Please manually download models from:"
    echo -e "${BLUE}$MODELS_URL_USA${NC}"
    echo ""
    echo "And place the .pt files in: $MODELS_DIR/"
    echo ""
    read -p "Press Enter after downloading models to continue..."
fi

# Verify models
MODEL_FILES=$(find "$MODELS_DIR" -name "*.pt" 2>/dev/null | wc -l)
if [ "$MODEL_FILES" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No models found. Service will start but won't classify.${NC}"
    echo "Download models from: $MODELS_URL_USA"
fi

# Create systemd service
echo -e "${BLUE}[6/6] Setting up service...${NC}"

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=BirdNET Vocalization Classifier
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/src/service.py --birdnet-dir $BIRDNET_DIR --models-dir $MODELS_DIR
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}

# Done!
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
echo -e "║              Installation Complete!                        ║"
echo -e "╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "The vocalization classifier is now running!"
echo ""
echo "Commands:"
echo "  Status:   sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:     journalctl -u ${SERVICE_NAME} -f"
echo "  Stop:     sudo systemctl stop ${SERVICE_NAME}"
echo "  Start:    sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "Data stored in: $INSTALL_DIR/data/vocalization.db"
echo ""
echo -e "${BLUE}Thank you for using BirdNET Vocalization!${NC}"
echo "Report issues: https://github.com/RonnyCHL/birdnet-vocalization/issues"
