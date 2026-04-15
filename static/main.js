const toggleBtn = document.getElementById('toggle-btn');
const btnText = document.getElementById('btn-text');
const statusText = document.getElementById('status-text');
const ipText = document.getElementById('ip-text');
const statusCard = document.getElementById('status-card');
const loader = document.getElementById('loader');
const terminalOutput = document.getElementById('terminal-output');
const forceRotateBtn = document.getElementById('force-rotate-btn');
const uptimeDisplay = document.getElementById('uptime');
const protocolDisplay = document.getElementById('protocol');

let isRunning = false;
let displayedLogsCount = 0;

function formatUptime(seconds) {
    if (!seconds) return "00:00:00";
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
}

function renderLogs(logs) {
    if (!logs || logs.length === 0) return;
    
    // Only append new logs
    if (logs.length > displayedLogsCount) {
        const newLogs = logs.slice(displayedLogsCount);
        newLogs.forEach(logLine => {
            // Split timestamp and message
            const match = logLine.match(/^\[(.*?)\] (.*)$/);
            const div = document.createElement('div');
            div.className = 'term-line';
            
            if (match) {
                div.innerHTML = `<span class="time">[${match[1]}]</span><span>${match[2]}</span>`;
            } else {
                div.textContent = logLine;
            }
            
            terminalOutput.appendChild(div);
        });
        displayedLogsCount = logs.length;
        
        // Auto scroll to bottom
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    } else if (logs.length < displayedLogsCount) {
        // App restarted or logs cleared
        terminalOutput.innerHTML = '';
        displayedLogsCount = 0;
        renderLogs(logs);
    }
}

async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        updateUI(data);
    } catch (err) {
        console.error("Failed to fetch status");
    }
}

function updateUI(data) {
    isRunning = data.running;
    renderLogs(data.logs);
    uptimeDisplay.innerText = formatUptime(data.uptime);
    
    // Format Time Left as mm:ss
    if (data.time_left !== undefined) {
        const tr_m = Math.floor(data.time_left / 60).toString().padStart(2, '0');
        const tr_s = (data.time_left % 60).toString().padStart(2, '0');
        document.getElementById('time-left').innerText = `${tr_m}:${tr_s}`;
    }
    
    if (isRunning) {
        statusCard.classList.add('active');
        statusText.innerText = "SHIELD ACTIVE";
        toggleBtn.className = 'toggle-btn on';
        btnText.innerText = "Disconnect";
        ipText.innerText = data.ip || "Routing...";
        protocolDisplay.innerText = "Raftar Secure Node";
        forceRotateBtn.disabled = false;
        forceRotateBtn.classList.remove('disabled');
    } else {
        statusCard.classList.remove('active');
        statusText.innerText = "DISCONNECTED";
        toggleBtn.className = 'toggle-btn off';
        btnText.innerText = "Connect to Raftar";
        ipText.innerText = "0.0.0.0";
        protocolDisplay.innerText = "Direct";
        document.getElementById('time-left').innerText = "--:--";
        forceRotateBtn.disabled = true;
        forceRotateBtn.classList.add('disabled');
    }
}

toggleBtn.addEventListener('click', async () => {
    loader.classList.remove('hidden');
    try {
        const response = await fetch('/api/toggle', { method: 'POST' });
        if(!response.ok) throw new Error("Failed");
        // Don't await full status here, let the interval pick it up
        fetchStatus();
    } catch (err) {
        alert("Failed to toggle proxy. Did you decline the prompt?");
    } finally {
        loader.classList.add('hidden');
    }
});

forceRotateBtn.addEventListener('click', async () => {
    if (!isRunning) return;
    
    forceRotateBtn.disabled = true;
    forceRotateBtn.innerHTML = "Rotating...";
    try {
        await fetch('/api/rotate', { method: 'POST' });
        fetchStatus(); // immediate poll to show logs
    } catch (e) {
        console.error(e);
    }
    
    setTimeout(() => {
        forceRotateBtn.disabled = false;
        forceRotateBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg> Force New IP`;
    }, 5000); // disable button for 5 secs
});

// Country selector
const countryBtns = document.querySelectorAll('.country-btn');
countryBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
        const code = btn.dataset.code;
        
        // Visual feedback - disable all buttons
        countryBtns.forEach(b => b.classList.add('switching'));
        
        try {
            const res = await fetch('/api/country', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });
            
            if (res.ok) {
                // Update active state
                countryBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
        } catch (e) {
            console.error("Country switch failed:", e);
        }
        
        // Re-enable buttons
        countryBtns.forEach(b => b.classList.remove('switching'));
        fetchStatus();
    });
});

// Setup continuous polling
fetchStatus();
setInterval(fetchStatus, 1000); // Poll every 1 second now for realtime logs and clock
