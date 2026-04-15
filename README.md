# Raftar IP

A privacy-first IP rotation tool built by **Avi**. Raftar IP automatically rotates your public IP address every 60 seconds using the Tor network, with a premium web dashboard to control everything.

## Features

- **One-Click Activation** — Toggle your IP shield on/off from a sleek web dashboard
- **Auto IP Rotation** — Your IP address changes every 60 seconds automatically
- **Country Selection** — Lock your exit node to Switzerland 🇨🇭, Japan 🇯🇵, Germany 🇩🇪, or France 🇫🇷
- **Force New IP** — Manually trigger an instant IP rotation on demand
- **Live System Logs** — Real-time terminal-style log feed showing exactly what's happening
- **Uptime Counter & Countdown Timer** — See how long you've been protected and when the next rotation hits

## How It Works

```
Browser → Privoxy (HTTP Proxy :8118) → Tor (SOCKS5 :9050) → Internet
```

When activated, Raftar IP configures your Mac's HTTP/HTTPS proxy to route all browser traffic through a local Privoxy instance, which forwards it through the Tor network. Every 60 seconds, a new Tor circuit is requested, giving you a completely new IP address.

## Prerequisites

- macOS with [Homebrew](https://brew.sh/) installed
- Python 3.9+

## Setup

### 1. Install Tor & Privoxy

```bash
brew install tor privoxy
```

### 2. Configure Tor Control Port

```bash
echo "ControlPort 9051" >> $(brew --prefix)/etc/tor/torrc
echo "ExitNodes {ch}" >> $(brew --prefix)/etc/tor/torrc
echo "StrictNodes 1" >> $(brew --prefix)/etc/tor/torrc
```

### 3. Configure Privoxy to forward to Tor

```bash
echo "forward-socks5t / 127.0.0.1:9050 ." >> $(brew --prefix)/etc/privoxy/config
```

### 4. Start the services

```bash
brew services start tor
brew services start privoxy
```

### 5. Install Python dependencies

```bash
pip3 install flask requests stem pysocks
```

## Running

```bash
python3 app.py
```

Then open your browser to **http://localhost:3000**

## Usage

1. Click **Connect to Raftar** and enter your Mac password when prompted
2. Your browser traffic is now anonymized through the Tor network
3. Use the **country buttons** to switch your exit node region
4. Use **Force New IP** to instantly get a new identity
5. Watch the live terminal logs for real-time system activity
6. Click **Disconnect** to restore your normal connection

## Created by

**Avi**
