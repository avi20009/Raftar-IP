import os
import time
import subprocess
import threading
import datetime
from flask import Flask, jsonify, send_from_directory, request
import requests
from stem import Signal
from stem.control import Controller

app = Flask(__name__, static_folder='static')

TOR_PORT = 9050
CONTROL_PORT = 9051

state = {
    "running": False,
    "current_ip": None,
    "message": "",
    "logs": [],
    "uptime_start": None,
    "next_rotation_time": None
}

def add_log(msg):
    timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
    state["logs"].append(f"[{timestamp}] {msg}")
    if len(state["logs"]) > 50:
        state["logs"].pop(0)

def check_tor_ip():
    try:
        session = requests.session()
        session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        r = session.get('https://api.ipify.org?format=json', timeout=10)
        return r.json().get('ip')
    except Exception as e:
        return None

def trigger_rotation(is_manual=False):
    prefix = "[MANUAL] " if is_manual else "[AUTO] "
    add_log(f"{prefix}Initiating Raftar circuit rotation...")
    try:
        with Controller.from_port(port=CONTROL_PORT) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            add_log("Signal NEWNYM successfully transmitted.")
            add_log("Building new encrypted relay circuit...")
        
        time.sleep(4) # buffer for circuit setup
        add_log("Circuit established. Resolving new exit node IP...")
        new_ip = check_tor_ip()
        
        if new_ip:
            if new_ip != state["current_ip"]:
                state["current_ip"] = new_ip
                state["message"] = f"Secured: {new_ip}"
                add_log(f"SUCCESS: Identity masked. New IP is {new_ip}")
            else:
                add_log("Circuit rebuilt, but exit node IP remained the same (common in strict node configs).")
        else:
            add_log("WARNING: Verification failed. Is Raftar Network connected to the internet?")
    except Exception as e:
        add_log(f"ERROR: Raftar Engine disconnected. {e}")

def rotation_worker():
    while True:
        if state["running"]:
            now = time.time()
            if not state.get("next_rotation_time") or now >= state["next_rotation_time"]:
                trigger_rotation(is_manual=False)
                state["next_rotation_time"] = time.time() + 60
        time.sleep(1)

rotation_thread = threading.Thread(target=rotation_worker, daemon=True)
rotation_thread.start()

def set_mac_proxy(enable):
    cmds = []
    
    if enable:
        # Set HTTP proxy → Privoxy (which forwards to Tor SOCKS5)
        cmds.append("networksetup -setwebproxy \\\"Wi-Fi\\\" 127.0.0.1 8118 off")
        cmds.append("networksetup -setwebproxystate \\\"Wi-Fi\\\" on")
        # Set HTTPS proxy → Privoxy
        cmds.append("networksetup -setsecurewebproxy \\\"Wi-Fi\\\" 127.0.0.1 8118 off")
        cmds.append("networksetup -setsecurewebproxystate \\\"Wi-Fi\\\" on")
    else:
        cmds.append("networksetup -setwebproxystate \\\"Wi-Fi\\\" off")
        cmds.append("networksetup -setsecurewebproxystate \\\"Wi-Fi\\\" off")

    combined_cmd = " && ".join(cmds)
    applescript = f'do shell script "{combined_cmd}" with administrator privileges'
    
    try:
        add_log("Prompting for macOS System Privileges...")
        subprocess.run(['osascript', '-e', applescript], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/proxy.pac')
def serve_pac():
    pac_content = '''function FindProxyForURL(url, host) {
    if (host === "127.0.0.1" || host === "localhost" || host === "192.168.1.86") {
        return "DIRECT";
    }
    return "SOCKS5 127.0.0.1:9050; SOCKS 127.0.0.1:9050; DIRECT";
}'''
    return app.response_class(pac_content, mimetype='application/x-ns-proxy-autoconfig')

@app.route('/api/status', methods=['GET'])
def get_status():
    uptime_sec = 0
    time_left_sec = 0
    if state["running"]:
        if state["uptime_start"]:
            uptime_sec = int((time.time() - state["uptime_start"]))
        if state.get("next_rotation_time"):
            time_left_sec = max(0, int(state["next_rotation_time"] - time.time()))
    
    return jsonify({
        "running": state["running"],
        "ip": state["current_ip"],
        "message": state["message"],
        "logs": state["logs"],
        "uptime": uptime_sec,
        "time_left": time_left_sec
    })

@app.route('/api/rotate', methods=['POST'])
def force_rotate():
    if not state["running"]:
        return jsonify({"error": "Service is not running"}), 400
    
    state["next_rotation_time"] = time.time() + 60
    threading.Thread(target=trigger_rotation, args=(True,)).start()
    return jsonify({"status": "Rotation signaled"})

COUNTRY_MAP = {
    "ch": "Switzerland",
    "jp": "Japan",
    "de": "Germany",
    "fr": "France"
}

def change_exit_country(code):
    """Rewrites ExitNodes in torrc and restarts Tor"""
    torrc_path = subprocess.check_output(
        ["/opt/homebrew/bin/brew", "--prefix"], text=True
    ).strip() + "/etc/tor/torrc"
    
    with open(torrc_path, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if line.startswith("ExitNodes"):
            new_lines.append(f"ExitNodes {{{code}}}\n")
        else:
            new_lines.append(line)
    
    with open(torrc_path, "w") as f:
        f.writelines(new_lines)
    
    subprocess.run(["/opt/homebrew/bin/brew", "services", "restart", "tor"],
                    capture_output=True, timeout=15)
    time.sleep(3)  # Wait for Tor to reconnect

@app.route('/api/country', methods=['POST'])
def set_country():
    data = request.get_json()
    code = data.get("code", "").lower()
    
    if code not in COUNTRY_MAP:
        return jsonify({"error": "Invalid country code"}), 400
    
    country_name = COUNTRY_MAP[code]
    add_log(f"Switching exit nodes to {country_name} ({{{code}}})...")
    
    try:
        change_exit_country(code)
        add_log(f"Tor daemon restarted with ExitNodes locked to {country_name}.")
        
        # Fetch new IP to confirm
        if state["running"]:
            state["next_rotation_time"] = time.time() + 60
            ip = check_tor_ip()
            if ip:
                state["current_ip"] = ip
                add_log(f"New exit IP via {country_name}: {ip}")
            else:
                add_log(f"WARNING: Could not verify IP. {country_name} nodes may be limited.")
        
        return jsonify({"status": "ok", "country": country_name})
    except Exception as e:
        add_log(f"ERROR: Failed to switch country. {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/toggle', methods=['POST'])
def toggle():
    new_state = not state["running"]
    
    if new_state:
        add_log("Booting Raftar Proxy Engine...")
        success = set_mac_proxy(True)
        if not success:
            add_log("Authorization denied by User. Aborting boot sequence.")
            return jsonify({"error": "Auth failed"}), 500
            
        add_log("macOS PAC Auto-Proxy successfully injected into Wi-Fi settings.")
        state["running"] = True
        state["uptime_start"] = time.time()
        state["next_rotation_time"] = time.time() + 60
        state["message"] = "Connecting..."
        
        def initial_boot():
            add_log("Verifying connection to Raftar network...")
            ip = check_tor_ip()
            if ip:
                state["current_ip"] = ip
                state["message"] = f"Secured: {ip}"
                add_log(f"Connection Verified. Shield Active. Original exit: {ip}")
            else:
                state["message"] = "Network Timeout"
                add_log("WARNING: Failed to handshake with Raftar relay.")
                
        threading.Thread(target=initial_boot).start()
    else:
        add_log("Initiating shutdown sequence...")
        success = set_mac_proxy(False)
        state["running"] = False
        state["current_ip"] = None
        state["uptime_start"] = None
        state["message"] = "Disconnected"
        add_log("macOS Wi-Fi interface proxy disabled. Identity exposed.")
        
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    add_log("System initialized. Awaiting commands.")
    app.run(host='0.0.0.0', port=3000, debug=False)
