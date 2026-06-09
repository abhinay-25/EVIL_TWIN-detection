# Complete Code Flow Analysis: Line-by-Line Breakdown

## Overview
This document explains every file, every function, and key code lines in the WiFi Evil Twin Detector project.

---

# File 1: `scanner.py` - WiFi Network Scanning Module

## Purpose
Discovers nearby WiFi networks and organizes them by SSID.

## Complete Code with Line-by-Line Explanation

```python
import pywifi              # Line 1: Import PyWiFi library for WiFi access
import time                # Line 2: Import time module (used for delay)

def scan_networks():       # Line 4: Define function to scan nearby networks
    """
    Scans for WiFi networks and groups them by SSID.
    Returns: dict with SSID as key, BSSIDs+signals as value
    """
    
    wifi = pywifi.PyWiFi()  # Line 9: Create PyWiFi object to interface with OS WiFi APIs
    interfaces = wifi.interfaces()  # Line 10: Get list of WiFi adapters on this computer
    
    # Line 12: Safety check - if no WiFi adapters found, return empty dict
    if len(interfaces) == 0:
        return {}
    
    # Line 15: Pick the first WiFi adapter (most systems have 1-2)
    iface = interfaces[0]
    
    # Line 17: Trigger active WiFi scan on this adapter
    # Active scan: sends probe requests, APs respond with their details
    iface.scan()
    
    # Line 20: Wait 5 seconds for scan to complete
    # PyWiFi needs time to collect all nearby AP responses
    time.sleep(5)
    
    # Line 23: Retrieve all scan results from the adapter
    # results is a list of network objects discovered
    results = iface.scan_results()
    
    # Line 26: Initialize empty dict to store organized networks
    # Structure will be: {"SSID": {"BSSID": signal_strength}}
    networks = {}
    
    # Line 29: Loop through each network found in scan results
    for net in results:
        
        # Line 31: Skip hidden WiFi networks (empty SSID)
        # Hidden networks broadcast without revealing their name
        if net.ssid == "":
            continue
        
        # Line 34: If this is the first time seeing this SSID, create new key
        if net.ssid not in networks:
            networks[net.ssid] = {}
        
        # Line 37: Store this AP under the SSID
        # Key is BSSID (MAC address), value is signal strength in dBm
        networks[net.ssid][net.bssid] = net.signal
    
    # Line 40: Return organized dict with all networks
    return networks
```

## Data Structure Returned

```python
# Example output from scan_networks():
{
    "HomeWiFi": {
        "AA:BB:CC:DD:EE:01": -45,   # BSSID: signal strength (dBm)
        "AA:BB:CC:DD:EE:02": -65
    },
    "CafeNetwork": {
        "11:22:33:44:55:66": -70
    },
    "AirportFreeWiFi": {
        "00:11:22:33:44:55": -72,
        "AA:BB:CC:DD:EE:FF": -45    # Suspicious: very strong signal
    }
}
```

## Key Concepts in scanner.py

- **PyWiFi**: Python wrapper around native OS WiFi APIs (Windows, Linux, macOS)
- **interfaces()**: Returns list of WiFi adapters/network interfaces
- **iface.scan()**: Initiates WiFi scan (sends probe requests)
- **time.sleep(5)**: Waits for scan to complete (5 seconds is arbitrary but sufficient)
- **scan_results()**: Returns list of discovered access points
- **Attributes**: Each network object has `.ssid`, `.bssid`, `.signal` properties

---

# File 2: `analyzer.py` - Risk Scoring and Analysis Module

## Purpose
Takes scanner output and assigns risk scores based on heuristic rules.

## Complete Code with Line-by-Line Explanation

```python
def analyze_networks(networks):    # Line 1: Function receives dict of networks
    """
    Analyzes networks for Evil Twin indicators.
    Input: networks dict from scanner.py
    Output: list of dicts with risk scores and reasons
    """
    
    analyzed_data = []  # Line 7: Initialize list to store analysis results
    
    # Line 9: Iterate through each SSID and its associated BSSIDs
    for ssid, bssids in networks.items():
        # ssid = network name (string)
        # bssids = dict of {BSSID: signal_strength}
        
        # Line 12: Clean SSID to handle non-ASCII characters
        # Some networks have unicode names that don't display well
        # encode('ascii', 'ignore') converts to ASCII, replacing non-ASCII with nothing
        # decode() converts bytes back to string
        safe_ssid = ssid.encode('ascii', 'ignore').decode()
        
        # Line 15: Initialize risk score for this SSID
        # Starts at 0, increased by rules below
        risk_score = 0
        
        # Line 16: Initialize list to store reasons for the score
        # Each rule that triggers adds an explanation string
        reasons = []
        
        # Line 19: Extract all BSSID:signal pairs into a list of tuples
        # Example: [("AA:BB:CC:DD:EE:01", -45), ("AA:BB:CC:DD:EE:02", -65)]
        unique_entries = list(bssids.items())
        
        # Line 22: Extract just the signal values into a separate list
        # Example: [-45, -65]
        signals = [signal for _, signal in unique_entries]
        
        # ═══════════════════════════════════════════════════════════
        # RULE A: Multiple BSSIDs for Same SSID
        # ═══════════════════════════════════════════════════════════
        
        # Line 25: Check if multiple BSSIDs (access points) found for this SSID
        if len(unique_entries) > 1:
            # Line 26: Multiple APs with same SSID detected
            risk_score += 40  # Add 40 points to risk score
            reasons.append("Multiple BSSID detected")  # Store the reason
        
        # ═══════════════════════════════════════════════════════════
        # RULE B: Unusually Strong Signal
        # ═══════════════════════════════════════════════════════════
        
        # Line 30: Loop through each signal strength value
        for signal in signals:
            # Line 31: Check if any signal is stronger than -50 dBm
            # -50 dBm is considered "unusually strong" for a distant AP
            # Signals below -50 are typical for medium distance
            if signal > -50:
                # Line 32: Strong signal detected
                risk_score += 20  # Add 20 points per unusually strong signal
                reasons.append("Unusually strong signal")
        
        # ═══════════════════════════════════════════════════════════
        # RULE C: Large Signal Strength Spread
        # ═══════════════════════════════════════════════════════════
        
        # Line 35: Check if we have at least 2 signals to compare
        if len(signals) > 1:
            # Line 36: Calculate the difference between strongest and weakest signal
            # Example: max([-45, -65]) - min([-45, -65]) = -45 - (-65) = 20
            diff = max(signals) - min(signals)
            
            # Line 37: Check if spread exceeds 20 dBm
            # Large spread can indicate one AP is much closer than others
            # Suspicious if one is rogue (placed close to victims)
            if diff > 20:
                # Line 38: Large spread detected
                risk_score += 30  # Add 30 points
                reasons.append("Large signal strength difference")
        
        # ═══════════════════════════════════════════════════════════
        # STATUS ASSIGNMENT
        # ═══════════════════════════════════════════════════════════
        
        # Line 41: Assign status based on total risk score
        if risk_score >= 70:
            # Line 42: High score = likely threat
            status = "HIGH RISK"
        elif risk_score >= 30:
            # Line 43: Medium score = needs investigation
            status = "SUSPICIOUS"
        else:
            # Line 44: Low score = probably safe
            status = "SAFE"
        
        # ═══════════════════════════════════════════════════════════
        # BUILD RESULT ENTRY
        # ═══════════════════════════════════════════════════════════
        
        # Line 47: Append analysis result to output list
        analyzed_data.append({
            "ssid": safe_ssid,                    # Network name
            "risk": risk_score,                   # Total risk points
            "status": status,                     # HIGH RISK/SUSPICIOUS/SAFE
            "reasons": list(set(reasons)),        # Unique reasons (set removes duplicates)
            "details": unique_entries             # List of all BSSIDs and their signals
        })
    
    # Line 54: Return list of analyzed networks
    return analyzed_data
```

## Risk Scoring Summary Table

| Rule | Condition | Points | Reason |
|------|-----------|--------|--------|
| A | More than 1 BSSID for same SSID | +40 | Multiple BSSID detected |
| B | Any signal > -50 dBm | +20 each | Unusually strong signal |
| C | Signal spread > 20 dBm | +30 | Large signal strength difference |

## Status Assignment

```python
if risk_score >= 70:     # Total points >= 70
    status = "HIGH RISK"   # Alert user immediately
elif risk_score >= 30:   # Total points >= 30 but < 70
    status = "SUSPICIOUS"  # Worth investigating
else:                     # Total points < 30
    status = "SAFE"        # Probably okay
```

## Example Calculation Walkthrough

Input SSID: `"AirportFreeWiFi"` with 2 BSSIDs:
- BSSID 1: `00:11:22:33:44:55` signal `-72 dBm` (legitimate)
- BSSID 2: `AA:BB:CC:DD:EE:FF` signal `-45 dBm` (rogue/evil twin)

Analysis:
```
Step 1: Check Rule A (Multiple BSSIDs)
  unique_entries = [("00:11:22:33:44:55", -72), ("AA:BB:CC:DD:EE:FF", -45)]
  len(unique_entries) = 2 > 1? YES
  risk_score += 40
  reasons.append("Multiple BSSID detected")
  
Step 2: Check Rule B (Strong Signal)
  signals = [-72, -45]
  For -72: -72 > -50? NO (skip)
  For -45: -45 > -50? YES ✓
    risk_score += 20
    reasons.append("Unusually strong signal")
  
Step 3: Check Rule C (Signal Spread)
  len(signals) = 2 > 1? YES
  diff = max([-72, -45]) - min([-72, -45])
  diff = -45 - (-72) = 27
  27 > 20? YES ✓
    risk_score += 30
    reasons.append("Large signal strength difference")

Final Calculation:
  risk_score = 0 + 40 + 20 + 30 = 90
  90 >= 70? YES
  status = "HIGH RISK"
  
Output:
{
  "ssid": "AirportFreeWiFi",
  "risk": 90,
  "status": "HIGH RISK",
  "reasons": [
    "Multiple BSSID detected",
    "Unusually strong signal",
    "Large signal strength difference"
  ],
  "details": [
    ("00:11:22:33:44:55", -72),
    ("AA:BB:CC:DD:EE:FF", -45)
  ]
}
```

---

# File 3: `app.py` - Flask Web Server Entry Point

## Purpose
Orchestrates scanner and analyzer, then displays results in web dashboard.

## Complete Code with Line-by-Line Explanation

```python
from flask import Flask, render_template  # Line 1: Import Flask and template renderer
from scanner import scan_networks         # Line 2: Import scanner function
from analyzer import analyze_networks     # Line 3: Import analyzer function

# Line 5: Create Flask application instance
# This is the web server that will listen for HTTP requests
app = Flask(__name__)

# Line 8: Define web route (URL path)
# @app.route("/") means this function handles requests to http://localhost:5000/
@app.route("/")
def index():                              # Line 10: Function name (can be anything)
    """
    Main page handler.
    This function is called every time user visits the dashboard.
    """
    
    # Line 15: Call scanner to get raw WiFi network data
    # Returns: {"SSID": {"BSSID": signal}}
    networks = scan_networks()
    
    # Line 19: Call analyzer to score each network
    # Returns: [{"ssid": ..., "risk": ..., "status": ...}, ...]
    analyzed = analyze_networks(networks)
    
    # Line 23: Initialize summary dict for chart
    # Will count how many networks in each risk category
    summary = {"SAFE": 0, "SUSPICIOUS": 0, "HIGH_RISK": 0}
    
    # Line 26: Iterate through analyzed networks
    for net in analyzed:
        # Line 27: Check network status
        if net["status"] == "HIGH RISK":
            # Line 28: Increment counter for HIGH RISK networks
            summary["HIGH_RISK"] += 1
        else:
            # Line 30: For other statuses, increment their counter
            # Note: status is either "SAFE" or "SUSPICIOUS", which match dict keys
            summary[net["status"]] += 1
    
    # Line 33: Render HTML template with data
    # render_template() looks for HTML file in templates/ folder
    # Passes "data" (analyzed networks) and "summary" (counts) to template
    # Template processes these variables and generates final HTML
    return render_template("index.html", data=analyzed, summary=summary)

# Line 37: Python entry point check
# This block only runs if script is executed directly (not imported)
if __name__ == "__main__":
    # Line 38: Start Flask development server
    # debug=True enables auto-reload when code changes
    # Default: runs on http://127.0.0.1:5000
    app.run(debug=True)
```

## Code Flow in `app.py`

```
1. Import modules (Flask, scanner, analyzer)
   ↓
2. Create Flask app object
   ↓
3. Define route @app.route("/")
   ↓
4. User visits http://localhost:5000/
   ↓
5. index() function is called
   ↓
6. Call scan_networks()
   └─ Returns: dict of networks
   ↓
7. Call analyze_networks(networks)
   └─ Returns: list of analyzed networks
   ↓
8. Build summary dict (count by status)
   ↓
9. Render template with data + summary
   └─ Returns: HTML to browser
   ↓
10. Browser displays dashboard
```

## Data Passed to Template

```python
# Variables available in index.html template:
data = [
  {
    "ssid": "HomeWiFi",
    "risk": 0,
    "status": "SAFE",
    "reasons": [],
    "details": [("AA:BB:CC:DD:EE:01", -65)]
  },
  {
    "ssid": "AirportFreeWiFi",
    "risk": 90,
    "status": "HIGH RISK",
    "reasons": ["Multiple BSSID detected", ...],
    "details": [("00:11:22:33:44:55", -72), ("AA:BB:CC:DD:EE:FF", -45)]
  },
  ...
]

summary = {
  "SAFE": 1,
  "SUSPICIOUS": 2,
  "HIGH_RISK": 1
}
```

---

# File 4: `templates/index.html` - Dashboard UI

## Purpose
Displays scanned networks, risk scores, and visualizations to the user.

## File Structure & Line-by-Line Explanation

### HTML Header Section

```html
<!DOCTYPE html>
<html>
<head>
    <!-- Line 4: Set page title (appears in browser tab) -->
    <title>WiFi Evil Twin Detector</title>

    <!-- Line 7: Load Tailwind CSS from CDN -->
    <!-- Tailwind provides pre-built utility classes for styling -->
    <!-- Makes layout responsive and modern without writing CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- Line 11: Load Chart.js library -->
    <!-- Used to draw the doughnut chart showing risk distribution -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <!-- Line 14: Load Chart.js plugin for data labels -->
    <!-- Adds text labels showing percentages on the chart -->
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels"></script>
</head>

<!-- Line 18: Body background styling -->
<!-- bg-gray-900 = dark gray background, text-white = white text -->
<body class="bg-gray-900 text-white">

<!-- Line 21: Container with max width for centered layout -->
<!-- max-w-6xl = maximum width of 1280px, mx-auto = centered margins -->
<div class="max-w-6xl mx-auto p-6">

    <!-- Line 24: Main title -->
    <!-- text-4xl = very large font, text-cyan-400 = cyan color, text-center = centered -->
    <h1 class="text-4xl text-center text-cyan-400 font-bold mb-6">
        📡 Security Dashboard
    </h1>
```

### Auto-Refresh Script

```html
    <!-- Line 30: Auto-refresh script -->
    <script>
        // Line 31: setInterval() runs code every N milliseconds
        // 300000 ms = 300 seconds = 5 minutes
        // location.reload() refreshes the page (re-runs full pipeline: scan → analyze → display)
        setInterval(() => location.reload(), 300000);
    </script>
```

### Chart Section

```html
    <!-- Line 36: Container for the chart -->
    <!-- bg-gray-800 = dark background, p-4 = padding, rounded-xl = rounded corners -->
    <div class="bg-gray-800 p-4 rounded-xl mb-6 flex justify-center">
        <!-- Line 38: Fixed size for chart (300px × 300px) -->
        <div style="width: 300px; height: 300px;">
            <!-- Line 39: Canvas element where Chart.js draws the doughnut chart -->
            <!-- id="riskChart" is referenced in the JavaScript below -->
            <canvas id="riskChart"></canvas>
        </div>
    </div>
```

### Network Cards Section

```html
    <!-- Line 44: Grid layout for network cards -->
    <!-- grid grid-cols-1 = 1 column on mobile -->
    <!-- md:grid-cols-2 = 2 columns on medium screens -->
    <!-- lg:grid-cols-3 = 3 columns on large screens (responsive design) -->
    <!-- gap-6 = 6 units of spacing between cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        <!-- Line 48: Jinja2 template loop (Python runs this on server) -->
        <!-- For each network in the "data" list passed from app.py -->
        {% for net in data %}
        
        <!-- Line 50: Individual network card -->
        <!-- bg-gray-800 = dark background -->
        <!-- p-5 = padding inside card -->
        <!-- rounded-xl = rounded corners -->
        <!-- shadow-lg = drop shadow -->
        <!-- hover:scale-105 = scales up 5% on mouse hover -->
        <!-- transition = smooth animation for hover effect -->
        <div class="bg-gray-800 p-5 rounded-xl shadow-lg hover:scale-105 transition">

            <!-- Line 54: Network SSID (name) -->
            <!-- text-xl = large font -->
            <!-- font-bold = bold text -->
            <!-- {{ net.ssid }} = Jinja2 variable substitution (inserts actual SSID) -->
            <h2 class="text-xl font-bold">{{ net.ssid }}</h2>

            <!-- Line 58: Risk score display -->
            <!-- text-sm = small font -->
            <!-- text-gray-400 = light gray color for secondary info -->
            <!-- {{ net.risk }} = displays numeric risk score (e.g., 90) -->
            <p class="text-sm text-gray-400">
                Risk Score: {{ net.risk }}
            </p>

            <!-- Line 63: Risk status badge with conditional coloring -->
            <!-- px-3 py-1 = padding -->
            <!-- rounded-full = fully rounded (pill shape) -->
            <!-- font-bold = bold text -->
            <!-- Jinja2 if/elif/else conditional:
                - If SAFE: green background (bg-green-500)
                - If SUSPICIOUS: yellow background (bg-yellow-400) + black text
                - Else (HIGH RISK): red background (bg-red-500)
            -->
            <span class="
                px-3 py-1 text-sm rounded-full font-bold
                {% if net.status == 'SAFE' %}
                    bg-green-500
                {% elif net.status == 'SUSPICIOUS' %}
                    bg-yellow-400 text-black
                {% else %}
                    bg-red-500
                {% endif %}
            ">
                <!-- Display the status text (SAFE, SUSPICIOUS, or HIGH RISK) -->
                {{ net.status }}
            </span>

            <!-- Line 78: Reasons list (why this network is flagged) -->
            <!-- text-sm = small font -->
            <!-- mt-2 = margin top (spacing) -->
            <!-- text-gray-300 = light gray text -->
            <!-- Jinja2 for loop: iterate through reasons list -->
            <ul class="text-sm mt-2 text-gray-300">
                {% for r in net.reasons %}
                <!-- Line 83: Bullet point with reason -->
                <!-- • = bullet character -->
                <!-- {{ r }} = inserts the reason text -->
                <li>• {{ r }}</li>
                {% endfor %}
            </ul>

        </div>

        <!-- Line 89: Alert popup if HIGH RISK detected -->
        <!-- This runs client-side (in browser) after page loads -->
        <!-- if net.status == "HIGH RISK" is evaluated server-side (Jinja2) -->
        {% if net.status == "HIGH RISK" %}
        <script>
            <!-- Line 91: Show browser alert dialog -->
            alert("HIGH RISK NETWORK DETECTED");
        </script>
        {% endif %}

        <!-- Line 95: End of loop -->
        {% endfor %}

    </div>

</div>

<!-- Line 100: End HTML body -->
</body>
```

### Chart.js Script Section

```html
<!-- Line 103: Script to create doughnut chart -->
<script>
    <!-- Line 104: window.onload ensures DOM is ready before running -->
    window.onload = function () {

        <!-- Line 106: Get reference to canvas element -->
        <!-- document.getElementById('riskChart') finds the <canvas id="riskChart"> -->
        const ctx = document.getElementById('riskChart');

        <!-- Line 109: Create new Chart instance -->
        new Chart(ctx, {
            <!-- Line 110: Chart type: doughnut (pie-shaped) -->
            type: 'doughnut',
            
            <!-- Line 112: Chart data -->
            data: {
                <!-- Line 113: Labels for each segment -->
                labels: ['Safe', 'Suspicious', 'High Risk'],
                
                <!-- Line 114: Datasets (data values) -->
                datasets: [{
                    <!-- Line 115: Actual count values -->
                    <!-- {{ summary["SAFE"] | default(0) }} = Jinja2 variable from Flask -->
                    <!-- | default(0) = if value is missing, use 0 instead -->
                    data: [
                        {{ summary["SAFE"] | default(0) }},        <!-- Count of SAFE networks -->
                        {{ summary["SUSPICIOUS"] | default(0) }},  <!-- Count of SUSPICIOUS networks -->
                        {{ summary["HIGH_RISK"] | default(0) }}    <!-- Count of HIGH RISK networks -->
                    ],
                    
                    <!-- Line 123: Colors for each segment -->
                    backgroundColor: [
                        '#22c55e',  <!-- Green for SAFE -->
                        '#facc15',  <!-- Yellow for SUSPICIOUS -->
                        '#ef4444'   <!-- Red for HIGH RISK -->
                    ]
                }]
            },
            
            <!-- Line 131: Chart options/configuration -->
            options: {
                responsive: true,          <!-- Scale chart with container -->
                maintainAspectRatio: false,<!-- Allow fixed 300×300 size -->
                
                <!-- Line 134: Plugins configuration -->
                plugins: {
                    <!-- Line 135: Hide legend (we show labels via datalabels plugin) -->
                    legend: {
                        display: false
                    },
                    
                    <!-- Line 139: Configure data labels plugin -->
                    datalabels: {
                        color: 'white',     <!-- Label text color -->
                        font: {
                            weight: 'bold',
                            size: 12
                        },
                        <!-- Line 145: Custom formatter for label text -->
                        formatter: function(value, context) {
                            <!-- Line 146: Get total sum of all values -->
                            let total = context.chart._metasets[0].total;
                            
                            <!-- Line 148: Calculate percentage -->
                            <!-- (value / total) * 100 = percentage -->
                            <!-- .toFixed(1) = round to 1 decimal place -->
                            let percent = total ? ((value / total) * 100).toFixed(1) : 0;
                            
                            <!-- Line 152: Get label name (Safe, Suspicious, High Risk) -->
                            let label = context.chart.data.labels[context.dataIndex];
                            
                            <!-- Line 155: Return formatted text -->
                            <!-- Example: "Safe\n5 (50.0%)" -->
                            return label + "\n" + value + " (" + percent + "%)";
                        }
                    }
                }
            },
            
            <!-- Line 162: Register the datalabels plugin -->
            plugins: [ChartDataLabels]
        });

    };
</script>

<!-- Line 168: Close body and HTML -->
</body>
</html>
```

## UI Layout Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  📡 Security Dashboard                                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                          Chart Section                          │
│                          (Doughnut)                            │
│                  ┌──────────────────────┐                      │
│                  │   SAFE: 5 (50%)     │                      │
│                  │ SUSPICIOUS: 3 (30%) │                      │
│                  │ HIGH RISK: 2 (20%)  │                      │
│                  └──────────────────────┘                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                        Network Cards Grid                       │
│                    (Responsive: 1-3 columns)                   │
│                                                                 │
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ │ HomeWiFi         │  │ CafeNetwork      │  │ AirportFreeWiFi  │
│ │ Risk Score: 0    │  │ Risk Score: 25   │  │ Risk Score: 90   │
│ │ [SAFE]           │  │ [SUSPICIOUS]     │  │ [HIGH RISK]      │
│ └──────────────────┘  └──────────────────┘  └──────────────────┘
│                                                                 │
│ ┌──────────────────┐  ┌──────────────────┐                     │
│ │ GuestNetwork     │  │ OfficeWiFi       │                     │
│ │ Risk Score: 15   │  │ Risk Score: 55   │                     │
│ │ [SAFE]           │  │ [SUSPICIOUS]     │                     │
│ └──────────────────┘  └──────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Auto-refresh: Every 5 minutes
```

## Card Component Detail

```
Each card displays:
┌─────────────────────────────────┐
│ SSID Name                       │  ← h2 heading (large, bold)
│                                 │
│ Risk Score: XX                  │  ← Gray secondary text
│                                 │
│ [STATUS BADGE]                  │  ← Color-coded status
│ ┌─────────────────────────────┐ │     GREEN  = SAFE
│ │ • Reason 1                  │ │     YELLOW = SUSPICIOUS
│ │ • Reason 2                  │ │     RED    = HIGH RISK
│ │ • Reason 3                  │ │
│ └─────────────────────────────┘ │  ← Unordered list of reasons
└─────────────────────────────────┘
   (Scales up 5% on hover)
```

---

# File 5: `requirements.txt` - Python Dependencies

## Purpose
Lists Python packages needed to run the project.

## Content with Explanation

```
Flask                # Web framework for building the dashboard server
pywifi               # Library to access WiFi scanning APIs
comtypes             # Windows library needed by PyWiFi backend
```

## What Each Does

- **Flask**: Creates HTTP server, routes requests, renders templates
- **PyWiFi**: Interfaces with OS WiFi APIs to discover nearby networks
- **comtypes**: Provides Windows COM interface access (Windows only)

---

# File 6: `.gitignore` - Git Ignore File

## Purpose
Tells Git which files NOT to track/commit.

## Content with Explanation

```
__pycache__/    # Python bytecode cache folder (regenerated automatically)
*.pyc           # Python compiled files (should not be committed)
venv/           # Virtual environment folder (local, not shared)
.env            # Environment variables file (secrets, not shared)
```

---

# Complete End-to-End Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    USER VISITS DASHBOARD                         │
│              http://127.0.0.1:5000/ (browser)                   │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────────┐
        │   Flask Route Handler (app.py)     │
        │   def index():                     │
        │   ↓ calls scan_networks()          │
        └────────────┬───────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │   WiFi Scanner (scanner.py)        │
        │   - Create PyWiFi object           │
        │   - Get network interfaces         │
        │   - Trigger WiFi scan              │
        │   - Wait 5 seconds for results     │
        │   - Collect all APs                │
        │   - Group by SSID                  │
        │                                    │
        │   Returns: {                       │
        │     "SSID": {                      │
        │       "BSSID": signal_strength     │
        │     }                              │
        │   }                                │
        └────────────┬───────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │   Network Analyzer (analyzer.py)   │
        │   For each SSID:                   │
        │   ├─ Rule A: Check BSSID count     │
        │   ├─ Rule B: Check signal strength │
        │   ├─ Rule C: Check signal spread   │
        │   ├─ Calculate risk_score          │
        │   └─ Assign status (SAFE/SUSP/HR) │
        │                                    │
        │   Returns: [{                      │
        │     "ssid": "...",                 │
        │     "risk": XX,                    │
        │     "status": "...",               │
        │     "reasons": [...],              │
        │     "details": [...]               │
        │   }]                               │
        └────────────┬───────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │   Summary Builder (app.py)         │
        │   Count networks by status:        │
        │   - SAFE: X                        │
        │   - SUSPICIOUS: Y                  │
        │   - HIGH_RISK: Z                   │
        │                                    │
        │   Returns: {                       │
        │     "SAFE": count,                 │
        │     "SUSPICIOUS": count,           │
        │     "HIGH_RISK": count             │
        │   }                                │
        └────────────┬───────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │   Template Renderer (index.html)   │
        │   - Jinja2 processes template      │
        │   - Inserts analyzed data          │
        │   - Inserts summary counts         │
        │   - Generates HTML cards           │
        │   - Generates chart data           │
        │   - Embeds JavaScript              │
        │                                    │
        │   Returns: Complete HTML           │
        └────────────┬───────────────────────┘
                     │
                     ↓
        ┌────────────────────────────────────┐
        │   Browser Renders HTML             │
        │   - Displays title                 │
        │   - Renders doughnut chart         │
        │   - Renders network cards          │
        │   - Runs JavaScript:               │
        │     ├─ Auto-refresh (5 min)       │
        │     ├─ Chart.js visualization     │
        │     └─ Alerts on HIGH RISK        │
        │                                    │
        │   USER SEES DASHBOARD              │
        └────────────────────────────────────┘
```

---

# Key Data Transformations

## Transformation 1: Raw Scan → Organized Networks

```python
# Input from PyWiFi:
[
  Network(ssid="HomeWiFi", bssid="AA:BB:CC:DD:EE:01", signal=-45),
  Network(ssid="HomeWiFi", bssid="AA:BB:CC:DD:EE:02", signal=-65),
  Network(ssid="CafeNetwork", bssid="11:22:33:44:55:66", signal=-70),
  ...
]

# Transformed to (scanner.py output):
{
  "HomeWiFi": {
    "AA:BB:CC:DD:EE:01": -45,
    "AA:BB:CC:DD:EE:02": -65
  },
  "CafeNetwork": {
    "11:22:33:44:55:66": -70
  }
}
```

## Transformation 2: Organized Networks → Analyzed with Scores

```python
# Input (from scanner):
{"HomeWiFi": {"AA:BB:CC:DD:EE:01": -45, "AA:BB:CC:DD:EE:02": -65}}

# Processed (analyzer.py):
{
  "ssid": "HomeWiFi",
  "risk": 40,           # 40 from multiple BSSID, 20 from signal > -50
  "status": "SUSPICIOUS",
  "reasons": ["Multiple BSSID detected", "Unusually strong signal"],
  "details": [("AA:BB:CC:DD:EE:01", -45), ("AA:BB:CC:DD:EE:02", -65)]
}
```

## Transformation 3: Analyzed Data → Summary Counts

```python
# Input (analyzed list):
[
  {"status": "SAFE", ...},
  {"status": "SUSPICIOUS", ...},
  {"status": "HIGH RISK", ...}
]

# Transformed to (for chart):
{
  "SAFE": 1,
  "SUSPICIOUS": 1,
  "HIGH_RISK": 1
}
```

## Transformation 4: Data + Summary → HTML

```python
# Input to template:
data = [analyzed networks]
summary = {"SAFE": 1, "SUSPICIOUS": 1, "HIGH_RISK": 1}

# Template generates:
<!-- For each network -->
<div class="...">
  <h2>HomeWiFi</h2>
  <span class="...">SUSPICIOUS</span>
  ...
</div>

<!-- Chart -->
<canvas id="riskChart"></canvas>
<script>
  new Chart(..., {
    data: {
      labels: ['Safe', 'Suspicious', 'High Risk'],
      datasets: [{ data: [1, 1, 1], ... }]
    }
  })
</script>
```

---

# Execution Timeline (from Server Start to User Sees Dashboard)

```
Time    Component           Action
────────────────────────────────────────────────────────────────
0:00    User               Types http://127.0.0.1:5000 in browser
0:05    Browser            Sends GET / request to Flask server
0:10    app.py             Receives request, calls index() function
0:15    app.py             Calls scan_networks()
0:20    scanner.py         Creates PyWiFi object
0:25    scanner.py         Gets network interfaces
0:30    scanner.py         Starts WiFi scan
0:35    scanner.py         ⏳ WAITING (5 second sleep)
5:40    scanner.py         Collects scan results
5:45    scanner.py         Organizes by SSID, returns dict
5:50    app.py             Calls analyze_networks(networks)
5:55    analyzer.py        Loop through each SSID
6:00    analyzer.py        Rule A: check BSSID count
6:05    analyzer.py        Rule B: check signal strength
6:10    analyzer.py        Rule C: check signal spread
6:15    analyzer.py        Calculate risk_score
6:20    analyzer.py        Assign status
6:25    analyzer.py        Return analyzed data
6:30    app.py             Build summary counts
6:35    app.py             Call render_template()
6:40    index.html         Jinja2 processes template
6:45    index.html         Generates HTML + JavaScript
6:50    app.py             Returns HTML response
6:55    Browser            Receives HTML
7:00    Browser            Parses HTML, loads CSS/JS from CDN
7:05    Browser            Renders dashboard layout
7:10    Browser            Runs Chart.js script
7:15    Browser            Creates doughnut chart
7:20    Browser            User sees DASHBOARD ✓

Total: ~7.2 seconds from request to visible dashboard
```

---

# UI Location Summary

| Component | File | Location |
|-----------|------|----------|
| **Title** | `index.html` | Line 4-6, top center |
| **Chart (Doughnut)** | `index.html` | Line 36-41, center top |
| **Auto-refresh Script** | `index.html` | Line 30-34, triggers every 5 min |
| **Network Cards Grid** | `index.html` | Line 44-95, responsive layout |
| **SSID Name** | `index.html` | Line 54, card heading |
| **Risk Score** | `index.html` | Line 58, card subheading |
| **Status Badge** | `index.html` | Line 63-75, color-coded pill |
| **Reasons List** | `index.html` | Line 78-87, bulleted list |
| **Alert on HIGH RISK** | `index.html` | Line 89-94, JavaScript popup |
| **Chart Data** | `index.html` | Line 115-120, JavaScript |
| **Chart Colors** | `index.html` | Line 123-127, RGB hex codes |

---

# How Calculations Work (Mathematical Formulas)

## Risk Score Calculation

```
risk_score = 0

if (count_of_bssids > 1):
    risk_score += 40

for each signal in signals:
    if (signal > -50 dBm):
        risk_score += 20

if (count_of_signals > 1):
    signal_spread = max(signals) - min(signals)
    if (signal_spread > 20 dBm):
        risk_score += 30

Final risk_score ∈ [0, 40, 60, 70, 90, ...] (depends on rule hits)
```

## Status Assignment Calculation

```
if (risk_score >= 70):
    status = "HIGH RISK"
else if (risk_score >= 30):
    status = "SUSPICIOUS"
else:
    status = "SAFE"
```

## Chart Percentage Calculation

```
for each segment:
    percentage = (value / total_sum) × 100
    rounded = percentage.round(1 decimal place)
    
Display: label + count + percentage
Example: "Safe\n5 (50.0%)"
```

---

This document provides complete coverage of every file, every function, and every key calculation in the WiFi Evil Twin Detector project.
