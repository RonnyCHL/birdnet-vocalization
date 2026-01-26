#!/bin/bash
#
# BirdNET Vocalization Uninstaller
#
# Completely removes the vocalization classifier from your system
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/RonnyCHL/birdnet-vocalization/main/uninstall.sh | bash
#
# Or if already installed:
#   /opt/birdnet-vocalization/uninstall.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/birdnet-vocalization"
SERVICE_NAME="birdnet-vocalization"

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║       BirdNET Vocalization Uninstaller                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Confirm
echo -e "${YELLOW}This will completely remove BirdNET Vocalization.${NC}"
echo ""
echo "The following will be deleted:"
echo "  - Service: ${SERVICE_NAME}"
echo "  - Directory: ${INSTALL_DIR}"
echo "  - Data: ${INSTALL_DIR}/data/vocalization.db"
echo ""
read -p "Are you sure? (y/N): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""

# Stop and disable service
echo -e "${BLUE}[1/3] Stopping service...${NC}"
if systemctl is-active --quiet ${SERVICE_NAME} 2>/dev/null; then
    sudo systemctl stop ${SERVICE_NAME}
    echo "Service stopped."
else
    echo "Service was not running."
fi

if systemctl is-enabled --quiet ${SERVICE_NAME} 2>/dev/null; then
    sudo systemctl disable ${SERVICE_NAME}
    echo "Service disabled."
fi

# Remove service file
echo -e "${BLUE}[2/3] Removing service file...${NC}"
if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    sudo rm "/etc/systemd/system/${SERVICE_NAME}.service"
    sudo systemctl daemon-reload
    echo "Service file removed."
else
    echo "Service file not found."
fi

# Remove installation directory
echo -e "${BLUE}[3/3] Removing installation directory...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    sudo rm -rf "$INSTALL_DIR"
    echo "Directory removed."
else
    echo "Directory not found."
fi

# Remove log file
if [ -f "/var/log/birdnet-vocalization.log" ]; then
    sudo rm "/var/log/birdnet-vocalization.log"
    echo "Log file removed."
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗"
echo -e "║           Uninstall Complete!                              ║"
echo -e "╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "BirdNET Vocalization has been removed from your system."
echo "Your BirdNET-Pi installation was not modified."
echo ""
echo -e "${BLUE}Thank you for trying BirdNET Vocalization!${NC}"
echo "Feedback: https://github.com/RonnyCHL/birdnet-vocalization/issues"
