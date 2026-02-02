#!/bin/bash
#
# BirdNET Vocalization Updater
#
# Updates your installation to the latest version
#
# Usage:
#   bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/update.sh)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/birdnet-vocalization"
SERVICE_NAME="birdnet-vocalization"

echo ""
echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════════════════════════╗"
echo "  ║     BirdNET Vocalization Updater                          ║"
echo "  ╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if installed
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}Error: BirdNET Vocalization is not installed.${NC}"
    echo "Please run the installer first:"
    echo "  bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh)"
    exit 1
fi

# Show current version
if [ -f "$INSTALL_DIR/VERSION" ]; then
    CURRENT_VERSION=$(cat "$INSTALL_DIR/VERSION")
    echo -e "Current version: ${YELLOW}$CURRENT_VERSION${NC}"
else
    echo -e "Current version: ${YELLOW}unknown${NC}"
fi

# Check for updates
echo -e "${BLUE}[1/4] Checking for updates...${NC}"
cd "$INSTALL_DIR"

# Fetch latest changes
sudo git fetch origin 2>/dev/null || {
    echo -e "${RED}Error: Could not connect to GitHub.${NC}"
    exit 1
}

# Check if updates available
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/master)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}Already up to date!${NC}"
    if [ -f "$INSTALL_DIR/VERSION" ]; then
        echo -e "Version: ${GREEN}$(cat $INSTALL_DIR/VERSION)${NC}"
    fi
    exit 0
fi

# Show what will be updated
echo ""
echo -e "${YELLOW}Updates available:${NC}"
git log --oneline HEAD..origin/master | head -10
echo ""

# Confirm update
read -p "Do you want to update? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Update cancelled."
    exit 0
fi

# Stop service
echo -e "${BLUE}[2/4] Stopping service...${NC}"
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# Pull updates
echo -e "${BLUE}[3/4] Downloading updates...${NC}"
sudo git pull origin master

# Restart service
echo -e "${BLUE}[4/4] Restarting service...${NC}"
sudo systemctl start "$SERVICE_NAME"

# Show new version
echo ""
if [ -f "$INSTALL_DIR/VERSION" ]; then
    NEW_VERSION=$(cat "$INSTALL_DIR/VERSION")
    echo -e "${GREEN}Updated to version: $NEW_VERSION${NC}"
else
    echo -e "${GREEN}Update complete!${NC}"
fi

echo ""
echo -e "${GREEN}BirdNET Vocalization has been updated successfully!${NC}"
echo ""
echo "View the web interface at: http://$(hostname -I | awk '{print $1}'):8088"
echo ""
