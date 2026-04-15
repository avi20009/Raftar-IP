# Raftar IP

A privacy-first IP rotation tool built by **Avi**. Raftar IP automatically rotates your public IP address every 60 seconds using encrypted relay circuits, with a premium web dashboard to control everything.

## Features

- **One-Click Activation** — Toggle your IP shield on/off from a sleek web dashboard
- **Auto IP Rotation** — Your IP address changes every 60 seconds automatically
- **Country Selection** — Lock your exit node to Switzerland 🇨🇭, Japan 🇯🇵, Germany 🇩🇪, or France 🇫🇷
- **Force New IP** — Manually trigger an instant IP rotation on demand
- **Live System Logs** — Real-time terminal-style log feed showing exactly what's happening
- **Uptime Counter & Countdown Timer** — See how long you've been protected and when the next rotation hits

## Quick Start (One Command)

```bash
git clone https://github.com/avi20009/Raftar-IP.git
cd Raftar-IP
./start.sh
```

That's it. The script automatically:
- ✅ Installs Homebrew (if missing)
- ✅ Installs & configures Tor
- ✅ Installs & configures Privoxy
- ✅ Installs Python dependencies
- ✅ Starts all background services
- ✅ Launches the Raftar IP dashboard

Then open **http://localhost:3000** in your browser.

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.9+

## Usage

1. Click **Connect to Raftar** and enter your Mac password when prompted
2. Your browser traffic is now anonymized through encrypted relay circuits
3. Use the **country buttons** to switch your exit node region
4. Use **Force New IP** to instantly get a new identity
5. Watch the live terminal logs for real-time system activity
6. Click **Disconnect** to restore your normal connection

## Manual Setup

If you prefer to set things up manually instead of using `start.sh`:

```bash
# Install dependencies
brew install tor privoxy

# Configure Tor
echo "ControlPort 9051" >> $(brew --prefix)/etc/tor/torrc
echo "ExitNodes {ch}" >> $(brew --prefix)/etc/tor/torrc
echo "StrictNodes 1" >> $(brew --prefix)/etc/tor/torrc

# Configure Privoxy
echo "forward-socks5t / 127.0.0.1:9050 ." >> $(brew --prefix)/etc/privoxy/config

# Start services
brew services start tor
brew services start privoxy

# Install Python packages
pip3 install flask requests stem pysocks

# Launch
python3 app.py
```

## Created by

**Avi**
