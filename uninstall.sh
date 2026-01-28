#!/bin/bash
#
# BirdNET Vocalization Uninstaller
#
# Completely removes the vocalization classifier from your system.
#
# Usage:
#   bash /opt/birdnet-vocalization/uninstall.sh
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
echo -e "${YELLOW}"
echo "    ╔══════════════════════════════════════════╗"
echo "    ║   BirdNET Vocalization Uninstaller       ║"
echo "    ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Please don't run as root. The script will use sudo when needed.${NC}"
    exit 1
fi

# Confirm
echo -e "${YELLOW}This will completely remove BirdNET Vocalization from your system.${NC}"
echo ""
echo "  The following will be removed:"
echo "    - Services (classifier and web viewer)"
echo "    - Installation directory ($INSTALL_DIR)"
echo "    - Sudoers configuration"
echo ""
echo -e "${BLUE}Your BirdNET-Pi installation will NOT be affected.${NC}"
echo ""

read -p "Are you sure you want to uninstall? [y/N]: " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}[1/4] Stopping services...${NC}"
sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || true
sudo systemctl stop ${SERVICE_NAME}-viewer 2>/dev/null || true
sudo systemctl disable ${SERVICE_NAME} 2>/dev/null || true
sudo systemctl disable ${SERVICE_NAME}-viewer 2>/dev/null || true
echo -e "${GREEN}Services stopped${NC}"

echo -e "${BLUE}[2/4] Removing service files...${NC}"
sudo rm -f /etc/systemd/system/${SERVICE_NAME}.service
sudo rm -f /etc/systemd/system/${SERVICE_NAME}-viewer.service
sudo systemctl daemon-reload
echo -e "${GREEN}Service files removed${NC}"

echo -e "${BLUE}[3/4] Removing sudoers configuration...${NC}"
sudo rm -f /etc/sudoers.d/birdnet-vocalization
echo -e "${GREEN}Sudoers configuration removed${NC}"

echo -e "${BLUE}[4/4] Removing installation directory...${NC}"
# Ask about data
if [ -f "$INSTALL_DIR/data/vocalization.db" ]; then
    echo ""
    echo -e "${YELLOW}Found vocalization database with your classification history.${NC}"
    read -p "Keep the data directory for backup? [Y/n]: " keep_data
    if [[ "$keep_data" =~ ^[Nn]$ ]]; then
        sudo rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}Installation directory removed (including data)${NC}"
    else
        # Move data to home directory
        BACKUP_DIR="$HOME/birdnet-vocalization-backup"
        mkdir -p "$BACKUP_DIR"
        cp -r "$INSTALL_DIR/data" "$BACKUP_DIR/"
        echo -e "${GREEN}Data backed up to: $BACKUP_DIR${NC}"
        sudo rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}Installation directory removed${NC}"
    fi
else
    sudo rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}Installation directory removed${NC}"
fi

echo ""
echo -e "${GREEN}"
echo "    ╔══════════════════════════════════════════╗"
echo "    ║   ✓  Uninstall Complete!                 ║"
echo "    ╚══════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "  BirdNET Vocalization has been removed from your system."
echo ""
echo "  To reinstall:"
echo "    bash <(curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/master/install.sh)"
echo ""
echo -e "${BLUE}Thank you for trying BirdNET Vocalization!${NC}"
echo ""
