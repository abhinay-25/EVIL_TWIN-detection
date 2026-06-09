# WiFi Fundamentals: SSID, BSSID, and Core Concepts

## 1) What is SSID?

### Definition
**SSID** = **Service Set Identifier**

It is the network name that users see when they search for WiFi networks to connect to.

### Examples
- `"HomeWiFi"`
- `"CafeNetwork"`
- `"AirportFreeWiFi"`
- `"CompanyGuest"`

### Characteristics
- Human-readable text string
- Up to 32 characters long
- Can contain spaces, numbers, and special characters
- Each WiFi network broadcasts its SSID in beacon frames
- Multiple access points (APs) can share the SAME SSID

### Why Use SSID?
Users need a way to identify and distinguish different networks they want to connect to. Without SSID, users would only see MAC addresses (which are meaningless to most people).

---

## 2) What is BSSID?

### Definition
**BSSID** = **Basic Service Set Identifier**

It is the unique MAC (Media Access Control) address of a specific WiFi access point (AP).

### Format
A 48-bit address, typically written in hexadecimal with colons:
- `AA:BB:CC:DD:EE:FF`
- `00:1A:2B:3C:4D:5E`

### Characteristics
- Globally unique identifier (theoretically)
- Each WiFi access point has exactly one BSSID
- The BSSID is the hardware MAC address of the AP's WiFi radio
- Unlike SSID, BSSID is NOT user-friendly but is unique per device

### Why Use BSSID?
- Network drivers and WiFi management tools use BSSID to identify the exact physical access point
- BSSID differentiates between two APs broadcasting the same SSID
- Roaming between multiple APs with same SSID uses BSSID to know which specific AP the device connects to

---

## 3) Relationship Between SSID and BSSID

### Example Scenario: Home Network with WiFi Mesh

Suppose you have a mesh WiFi system at home. You might see:

**From User's Perspective (SSID):**
```
Available Networks:
- HomeWiFi
- CafeNetwork
- AirportFreeWiFi
```

**From Technical Perspective (BSSID):**
```
HomeWiFi (SSID) is actually broadcast by:
  - BSSID: AA:BB:CC:DD:EE:01  (Living Room Router - 2.4 GHz)
  - BSSID: AA:BB:CC:DD:EE:02  (Living Room Router - 5 GHz)
  - BSSID: AA:BB:CC:DD:EE:03  (Bedroom Repeater - 2.4 GHz)
  - BSSID: AA:BB:CC:DD:EE:04  (Bedroom Repeater - 5 GHz)
```

**Key Insight:**
- All four BSSIDs broadcast the same SSID (`HomeWiFi`)
- But they are 4 distinct physical devices (or device radios)

---

## 4) Signal Strength (RSSI / Signal Level)

### Definition
**RSSI** = **Received Signal Strength Indicator**

It measures the strength of the WiFi signal from an access point.

### Unit
Measured in **dBm** (decibels relative to one milliwatt).

### Typical Range
- `-30 dBm` to `-90 dBm`
- Closer to 0 (e.g., `-30`) = stronger signal
- Farther from 0 (e.g., `-90`) = weaker signal

### Examples
```
-30 dBm  → Excellent (very close, strong signal)
-50 dBm  → Good (close, strong)
-70 dBm  → Fair (moderate distance)
-85 dBm  → Weak (far away)
-90 dBm  → Very weak (edge of range)
```

### Why It Matters for Evil Twin Detection
- A rogue AP placed very close to a target might have unusually strong signal (> -50 dBm)
- This is one of the heuristics used by this project to flag suspicious networks

---

## 5) WiFi Scan Process

### What Happens When You "Scan" for Networks?

1. **Passive Scanning** (Traditional, slower):
   - WiFi radio listens on each channel for beacon frames sent by APs
   - Takes ~100-300ms per channel
   - Multiple channels = several seconds total

2. **Active Scanning** (This project uses it):
   - WiFi radio sends probe requests on each channel
   - Access points respond with probe responses
   - Faster than passive scanning
   - This project waits 5 seconds after scan initiation to collect all responses

### Scan Results Structure
The scanner collects all nearby APs and organizes them by SSID:

```python
{
  "HomeWiFi": {
    "AA:BB:CC:DD:EE:01": -45,  # BSSID: signal strength
    "AA:BB:CC:DD:EE:03": -73
  },
  "CafeNetwork": {
    "11:22:33:44:55:66": -65
  },
  "AirportFreeWiFi": {
    "99:88:77:66:55:44": -72,
    "99:88:77:66:55:45": -80
  }
}
```

---

## 6) Why Multiple BSSIDs per SSID Occur Legitimately

### Scenario A: Enterprise/Campus Network
- Large building with many access points
- All broadcast same SSID (e.g., `"CorporateNetwork"`)
- Each AP has different BSSID
- User's device roams between them as it moves

### Scenario B: Dual-Band Router
- Modern routers have 2.4 GHz and 5 GHz radios
- Both radios can broadcast same SSID
- Each radio gets its own BSSID
- User device picks the band with better signal

### Scenario C: WiFi Mesh System
- Multiple mesh nodes in a home
- All broadcast same SSID
- Each node has its own BSSID
- Device automatically connects to nearest/strongest node

---

## 7) How Evil Twin Attacks Exploit SSID/BSSID

### Classic Evil Twin Attack Flow

1. **Attacker sets up rogue AP** with:
   - Same SSID as legitimate network (e.g., `"AirportFreeWiFi"`)
   - Different BSSID (attacker's hardware MAC)
   - Often no password (open network) or weak encryption

2. **Victim connects** to the rogue BSSID thinking it's the legitimate network
   - User sees SSID they recognize
   - Doesn't check BSSID (most users don't know it exists)
   - Or many "identical" SSIDs appear, victim picks wrong BSSID

3. **Attacker intercepts traffic**
   - All traffic goes through attacker's AP
   - Attacker can see/modify unencrypted traffic
   - Can perform man-in-the-middle (MITM) attacks

### Example
```
Legitimate Airport WiFi:
  SSID: AirportFreeWiFi
  BSSID: 00:11:22:33:44:55
  Encryption: WPA2

Evil Twin (Attacker's Rogue AP):
  SSID: AirportFreeWiFi  (same SSID!)
  BSSID: AA:BB:CC:DD:EE:FF  (different, attacker's device)
  Encryption: None (open) or weak

User connecting:
  Sees "AirportFreeWiFi" twice
  Picks one randomly (50% chance it's the rogue!)
  Now connected to attacker's AP
```

---

## 8) Detection Heuristics Used by This Project

### Heuristic 1: Multiple BSSIDs Under Same SSID
```
If (count of distinct BSSIDs for one SSID) > 1:
  risk_score += 40
  reason: "Multiple BSSID detected"
```

**Why this is suspicious:**
- In typical home/small business scenario, one SSID = one BSSID
- Multiple BSSIDs can indicate mesh/enterprise (legitimate) OR evil twin (attacker + legitimate)

**Limitation:**
- Legitimate mesh/enterprise networks have multiple BSSIDs per SSID too
- This rule alone is not definitive proof of attack

### Heuristic 2: Very Strong Signal
```
For each BSSID:
  If (signal > -50 dBm):
    risk_score += 20
    reason: "Unusually strong signal"
```

**Why this is suspicious:**
- Attacker places rogue AP close to targets for reliable connection
- Very strong signal in public place can indicate rogue AP
- Expected signal: -60 to -80 dBm in typical public spaces

**Limitation:**
- Legitimate nearby router also produces strong signal

### Heuristic 3: Large Signal Spread Within Same SSID
```
If (max_signal - min_signal) > 20 dBm:
  risk_score += 30
  reason: "Large signal strength difference"
```

**Why this is suspicious:**
- If two APs with same SSID have very different signals, one might be rogue/anomalous
- Legitimate mesh nodes should have similar spread (same location/design)
- Big difference suggests different placement (attacker vs legitimate)

**Limitation:**
- Multi-floor buildings, outdoors with obstructions can naturally produce large spread
- Not a strong standalone indicator

---

## 9) Other WiFi Parameters (Not Used by This Project, But Relevant)

### Channel Number
- WiFi operates on predefined channels (1-13 on 2.4 GHz, 36-165 on 5 GHz)
- Legitimate enterprise networks pick specific channels
- Evil Twin might jump channels or use unexpected ones

### Encryption Type
- WPA2/WPA3 = modern, secure
- WEP = very old, broken
- Open = no encryption
- If legitimate network uses WPA2 but you see same SSID with no encryption, likely evil twin

### Vendor OUI (Organizationally Unique Identifier)
- First 3 bytes of BSSID identify the hardware vendor
- `00:1A:2B` might be manufacturer "Cisco"
- If legitimate AP is Cisco but new BSSID is from unknown vendor, suspicious

### Beacon Interval
- How often AP broadcasts beacon frames (typically 100ms)
- Rogue APs might use non-standard intervals

---

## 10) Visual Summary

```
┌─────────────────────────────────────────────────────────────────┐
│  WiFi Network Structure                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SSID Level (User Sees This):                                 │
│  ├─ "HomeWiFi"                                                 │
│  │   └─ (Multiple APs can broadcast this SSID)                │
│  ├─ "CafeNetwork"                                              │
│  └─ "AirportFreeWiFi"                                          │
│                                                                 │
│  BSSID Level (Technical, Unique per AP):                      │
│  ├─ "HomeWiFi" broadcasted by:                                │
│  │   ├─ AA:BB:CC:DD:EE:01 (-45 dBm)  [Main Router, 5 GHz]   │
│  │   └─ AA:BB:CC:DD:EE:02 (-65 dBm)  [Extender, 2.4 GHz]    │
│  │                                                             │
│  ├─ "AirportFreeWiFi" broadcasted by:                         │
│  │   ├─ 00:11:22:33:44:55 (-70 dBm)  [Legitimate AP]        │
│  │   └─ AA:BB:CC:DD:EE:FF (-45 dBm)  [EVIL TWIN - too close] │
│  └─ "CafeNetwork" broadcasted by:                             │
│      └─ 11:22:33:44:55:66 (-65 dBm)  [Single AP]            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Detection Logic (This Project):
  AirportFreeWiFi:
    ✓ Multiple BSSIDs: +40
    ✓ Unusually strong signal (-45): +20
    ✗ Signal spread (70-45=25 > 20): +30
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Total: 90 → HIGH RISK ⚠️
```

---

## 11) Real-World Example: Airport WiFi Evil Twin

### Scenario
You're at an airport. You want to connect to `"AirportFreeWiFi"` to check your flight status.

### What You See (SSID Level)
```
Available Networks:
- AirportFreeWiFi (Signal: ███████░░ Strong)
- AirportFreeWiFi (Signal: ████░░░░░ Medium)
```

Two identical SSIDs appear! Which one is real?

### What's Actually Happening (BSSID Level)
```
Network 1 (Real):
  SSID: AirportFreeWiFi
  BSSID: 00:11:22:33:44:55
  Encryption: WPA2
  Signal: -70 dBm (from airport's installed AP in terminal)

Network 2 (Evil Twin):
  SSID: AirportFreeWiFi
  BSSID: AA:BB:CC:DD:EE:FF
  Encryption: Open (no password)
  Signal: -45 dBm (from attacker's rogue AP nearby)
```

### User's Mistake
- Picks Network 2 because signal is stronger
- Connects to attacker's rogue AP instead of real airport WiFi
- Now attacker intercepts all traffic

### This Project Would Flag It
```
SSIDs Scanned:
  AirportFreeWiFi:
    Risk Factors:
      ✓ Multiple BSSIDs (2 found): +40
      ✓ Unusually strong signal (-45 dBm): +20
      ✓ Signal spread (70 - 45 = 25 > 20): +30
    
    Total Risk Score: 90 / 100
    Status: 🔴 HIGH RISK
    
    Reasons:
      - Multiple BSSID detected
      - Unusually strong signal
      - Large signal strength difference
```

---

## 12) Key Takeaways

| Concept | What It Is | Why It Matters | Example |
|---------|-----------|----------------|---------|
| **SSID** | Network name users see | Identifies network to users | `"HomeWiFi"` |
| **BSSID** | Unique MAC address per AP | Identifies exact physical AP | `AA:BB:CC:DD:EE:FF` |
| **RSSI/Signal** | Signal strength in dBm | Indicates proximity/quality | `-45 dBm` = strong |
| **Multiple BSSIDs/SSID** | Many APs with same name | Normal for mesh/enterprise; suspicious if unexpected | Mesh router with 4 radios |
| **Signal Spread** | Difference between strongest/weakest | May indicate mixed AP types or suspicious placement | 25 dBm spread = potentially suspicious |

---

## 13) Further Defense Against Evil Twins

1. **Check BSSID Before Connecting**
   - Most phones display BSSID in advanced WiFi settings
   - Write down legitimate network's BSSID ahead of time
   - Verify before connecting in public place

2. **Use Enterprise Authentication**
   - WPA2-Enterprise with certificate verification
   - Rogue AP can't fake certificate chain
   - Used in corporate networks

3. **Use VPN**
   - Encrypts all traffic even on compromised network
   - Attacker only sees encrypted data

4. **Avoid Unencrypted Networks**
   - Never use "open" WiFi for sensitive work
   - Use HTTPS-only browsing (browser enforces it)

5. **Use WiFi Protected Access (WPA2/WPA3)**
   - Modern encryption standard
   - Prevents eavesdropping even on legitimate network

6. **Monitor Tools**
   - Tools like this project provide early warning
   - Combined with user awareness = defense in depth
