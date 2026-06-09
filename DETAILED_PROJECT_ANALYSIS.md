# WiFi Evil Twin Detector - Detailed Project Analysis

## 1) Project Purpose
This project is a local WiFi monitoring dashboard that tries to identify potential Evil Twin attack patterns from nearby wireless scan results.

An Evil Twin attack usually means a malicious access point is impersonating a legitimate WiFi network (typically by copying the same SSID) to trick users into connecting.

This project does not perform packet-level authentication checks. Instead, it uses practical heuristics from scan data:
- duplicate SSID with multiple BSSIDs
- unusual signal behavior
- large signal spread among APs with the same SSID

## 2) Tech Stack Used
- Python 3
- Flask (web server + templating)
- PyWiFi (access nearby WiFi scan results)
- comtypes (Windows dependency needed by PyWiFi backend)
- Jinja2 templates (via Flask)
- Tailwind CSS (loaded from CDN)
- Chart.js + chartjs-plugin-datalabels (loaded from CDN)

Dependencies are defined in `requirements.txt`:
- Flask
- pywifi
- comtypes

## 3) Repository File-by-File Breakdown

### `app.py`
- Flask app entrypoint.
- Defines route `/`.
- Calls scanner and analyzer modules:
  - `scan_networks()` -> raw network snapshot grouped by SSID.
  - `analyze_networks()` -> risk score + status for each SSID.
- Builds summary counts for chart buckets:
  - `SAFE`
  - `SUSPICIOUS`
  - `HIGH_RISK` (internally mapped from status `HIGH RISK`)
- Renders `templates/index.html` with analyzed data + chart summary.

### `scanner.py`
- Uses PyWiFi to access wireless interfaces.
- Picks first interface (`interfaces[0]`).
- Triggers active scan (`iface.scan()`), then waits 5 seconds.
- Reads results and builds structure:

```python
{
  "SSID_NAME": {
    "BSSID_1": signal_dbm,
    "BSSID_2": signal_dbm
  }
}
```

- Ignores hidden/empty SSIDs (`net.ssid == ""`).

### `analyzer.py`
- Core detection logic.
- For each SSID group, computes risk score based on heuristic rules.
- Removes non-ASCII characters from SSID before display:
  - `ssid.encode('ascii', 'ignore').decode()`
- Outputs list entries with:
  - `ssid`
  - `risk`
  - `status`
  - `reasons`
  - `details` (BSSID + signal pairs)

### `templates/index.html`
- Dashboard UI.
- Auto-refresh script (currently set to 300000 ms = 5 minutes; comment says 1 minute).
- Card view per SSID with risk badge and reasons.
- Doughnut chart using summary counts.
- Browser alert pops when a `HIGH RISK` network appears.

### `README.md`
- Basic high-level overview and quick run command.
- Mentions features and stack.

### `.gitignore`
- Ignores Python cache, bytecode, local virtual env, and `.env`.

## 4) End-to-End Runtime Flow
1. User runs `python app.py`.
2. Flask starts local web server.
3. Browser requests `/`.
4. `app.py` calls `scan_networks()`.
5. `scanner.py` runs WiFi scan and groups APs by SSID.
6. `app.py` passes grouped data to `analyze_networks()`.
7. `analyzer.py` applies heuristic scoring rules.
8. `app.py` builds summary counts from statuses.
9. Flask renders dashboard template with detailed rows and chart data.
10. Page auto-refreshes periodically and repeats full pipeline.

## 5) How Evil Twin Suspicion Is Determined (Exact Parameters)
Detection is score-based. For each SSID, a `risk_score` starts at 0 and increases by rule hits.

### Rule A: Multiple BSSID under same SSID
Condition:
- Number of unique BSSID entries for an SSID is greater than 1.

Score impact:
- `+40`

Reason label:
- `Multiple BSSID detected`

Why it matters:
- Evil Twins often reuse the same SSID while broadcasting from different hardware.

Caveat:
- Legitimate enterprise/campus/mesh networks also have many AP radios under one SSID.

### Rule B: Unusually strong signal
Condition:
- For each signal value, if `signal > -50` dBm.

Score impact:
- `+20` for each matching signal record

Reason label:
- `Unusually strong signal`

Why it matters:
- A rogue AP placed physically close to victims may appear very strong.

Caveat:
- Legitimate nearby router/AP can also produce very strong RSSI.

### Rule C: Large signal spread inside same SSID group
Condition:
- At least two signal values exist, and:
- `max(signals) - min(signals) > 20` dBm

Score impact:
- `+30`

Reason label:
- `Large signal strength difference`

Why it matters:
- Big spread can indicate one AP is abnormally close/strong while another is farther, which can be suspicious in some environments.

Caveat:
- Multi-floor buildings, extenders, and mixed AP placements can produce large spread naturally.

## 6) Status Classification Logic
Final status is assigned from total `risk_score`:
- `HIGH RISK` if score >= 70
- `SUSPICIOUS` if score >= 30 and < 70
- `SAFE` if score < 30

This creates a simple triage pipeline:
- low score -> informational
- medium score -> investigate
- high score -> immediate alerting in UI

## 7) Practical Example of Scoring
Suppose SSID `OfficeWiFi` has 2 BSSIDs with signals `-45` and `-73` dBm.

- Multiple BSSID: `+40`
- Strong signal `-45 > -50`: `+20`
- Signal spread = `(-45) - (-73) = 28` (>20): `+30`
- Total = `90` -> `HIGH RISK`

## 8) Data Model Passed to the Template
Each analyzed item is a dict like:

```python
{
  "ssid": "OfficeWiFi",
  "risk": 90,
  "status": "HIGH RISK",
  "reasons": [
    "Multiple BSSID detected",
    "Unusually strong signal",
    "Large signal strength difference"
  ],
  "details": [
    ("AA:BB:CC:DD:EE:FF", -45),
    ("11:22:33:44:55:66", -73)
  ]
}
```

## 9) Security Value and Current Limits
### What this project does well
- Gives quick visibility into potentially suspicious SSID behavior.
- Easy to run and explain.
- Useful for awareness, demos, and first-level triage.

### What it does not verify
- It does not validate AP authenticity using certificates or enterprise auth metadata.
- It does not inspect management frames deeply (beacons/probe responses via monitor mode).
- It does not fingerprint known trusted BSSID vendors/manufacturers.
- It does not verify channel consistency, encryption mismatch, or captive portal behavior.

Result:
- It is a heuristic detector, not a cryptographic or protocol-forensic verifier.

## 10) OS and Environment Notes
- Designed to run on systems where PyWiFi can access scan APIs.
- On Windows, `comtypes` helps backend interoperability.
- Requires a compatible wireless adapter and permission to scan nearby networks.

## 11) Improvement Ideas (If You Want Better Real Detection)
1. Add known-good baseline profiles per SSID:
   - expected BSSID set
   - expected channels
   - expected encryption/auth mode
2. Add channel-based anomaly scoring:
   - same SSID but unusual channel jump can be suspicious.
3. Add encryption mismatch checks:
   - same SSID with weaker auth from unknown BSSID is high risk.
4. Add vendor OUI lookup:
   - suspicious if BSSID vendor differs from known AP vendor.
5. Add temporal consistency:
   - rogue APs often appear briefly or with unstable behavior.
6. Add packet capture mode (Scapy/monitor mode) for stronger evidence.
7. Export scan history to database and trend anomalies over time.

## 12) Quick Summary
The project determines Evil Twin risk by combining 3 primary parameters from WiFi scan data:
- count of BSSIDs per SSID
- very strong RSSI signals (> -50 dBm)
- RSSI spread within the SSID group (> 20 dBm)

Those signals are translated to a weighted score, then mapped into `SAFE`, `SUSPICIOUS`, or `HIGH RISK`, and displayed through a Flask dashboard.
