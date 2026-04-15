#!/bin/bash

# ============================================
#   Raftar IP — One-Click Launcher
#   Created by Avi
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}  ╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}  ║         RAFTAR IP  —  by Avi         ║${NC}"
echo -e "${CYAN}${BOLD}  ║     Privacy-First IP Rotation Tool   ║${NC}"
echo -e "${CYAN}${BOLD}  ╚══════════════════════════════════════╝${NC}"
echo ""

# ---- Step 1: Check for Homebrew ----
echo -e "${YELLOW}[1/6]${NC} Checking for Homebrew..."
if command -v brew &>/dev/null; then
    echo -e "  ${GREEN}✔${NC} Homebrew found"
elif [ -f /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
    echo -e "  ${GREEN}✔${NC} Homebrew found (Apple Silicon)"
else
    echo -e "  ${RED}✘${NC} Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)"
    echo -e "  ${GREEN}✔${NC} Homebrew installed"
fi

# Make sure brew is in PATH for this session
eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

# ---- Step 2: Install Tor ----
echo -e "${YELLOW}[2/6]${NC} Checking for Tor..."
if brew list tor &>/dev/null; then
    echo -e "  ${GREEN}✔${NC} Tor already installed"
else
    echo -e "  ${CYAN}↓${NC} Installing Tor..."
    brew install tor
    echo -e "  ${GREEN}✔${NC} Tor installed"
fi

# ---- Step 3: Install Privoxy ----
echo -e "${YELLOW}[3/6]${NC} Checking for Privoxy..."
if brew list privoxy &>/dev/null; then
    echo -e "  ${GREEN}✔${NC} Privoxy already installed"
else
    echo -e "  ${CYAN}↓${NC} Installing Privoxy..."
    brew install privoxy
    echo -e "  ${GREEN}✔${NC} Privoxy installed"
fi

# ---- Step 4: Configure Tor & Privoxy ----
echo -e "${YELLOW}[4/6]${NC} Configuring services..."

TORRC_PATH="$(brew --prefix)/etc/tor/torrc"
PRIVOXY_CONFIG="$(brew --prefix)/etc/privoxy/config"

# Tor: Enable ControlPort
if ! grep -q "^ControlPort 9051" "$TORRC_PATH" 2>/dev/null; then
    echo "ControlPort 9051" >> "$TORRC_PATH"
    echo -e "  ${GREEN}✔${NC} Tor ControlPort 9051 enabled"
else
    echo -e "  ${GREEN}✔${NC} Tor ControlPort already configured"
fi

# Tor: Set default exit nodes to Switzerland
if ! grep -q "^ExitNodes" "$TORRC_PATH" 2>/dev/null; then
    echo "ExitNodes {ch}" >> "$TORRC_PATH"
    echo "StrictNodes 1" >> "$TORRC_PATH"
    echo -e "  ${GREEN}✔${NC} Default exit nodes set to Switzerland"
else
    echo -e "  ${GREEN}✔${NC} Exit nodes already configured"
fi

# Privoxy: Forward to Tor SOCKS5
if ! grep -q "^forward-socks5t" "$PRIVOXY_CONFIG" 2>/dev/null; then
    echo "" >> "$PRIVOXY_CONFIG"
    echo "forward-socks5t / 127.0.0.1:9050 ." >> "$PRIVOXY_CONFIG"
    echo -e "  ${GREEN}✔${NC} Privoxy → Tor forwarding configured"
else
    echo -e "  ${GREEN}✔${NC} Privoxy forwarding already configured"
fi

# ---- Step 5: Install Python dependencies ----
echo -e "${YELLOW}[5/6]${NC} Installing Python dependencies..."
pip3 install flask requests stem pysocks "requests[socks]" --quiet 2>/dev/null
echo -e "  ${GREEN}✔${NC} Python packages ready"

# ---- Step 6: Start services ----
echo -e "${YELLOW}[6/6]${NC} Starting background services..."
brew services restart tor 2>/dev/null
brew services restart privoxy 2>/dev/null
sleep 3

# Verify services
if nc -z 127.0.0.1 9050 2>/dev/null; then
    echo -e "  ${GREEN}✔${NC} Tor is running on port 9050"
else
    echo -e "  ${RED}✘${NC} Tor failed to start. Try: brew services restart tor"
fi

if nc -z 127.0.0.1 8118 2>/dev/null; then
    echo -e "  ${GREEN}✔${NC} Privoxy is running on port 8118"
else
    echo -e "  ${RED}✘${NC} Privoxy failed to start. Try: brew services restart privoxy"
fi

# ---- Launch ----
echo ""
echo -e "${GREEN}${BOLD}  ══════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}   Raftar IP is starting!${NC}"
echo -e "${GREEN}${BOLD}   Open: ${CYAN}http://localhost:3000${NC}"
echo -e "${GREEN}${BOLD}  ══════════════════════════════════════${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/app.py"
