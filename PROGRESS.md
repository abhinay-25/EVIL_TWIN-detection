# Development Progress Log

## May 1, 2026
- - Defined project scope for WiFi Evil Twin detection
- - Outlined core modules: scanner, analyzer, dashboard

## May 2, 2026
- - Researched evil twin attack patterns and BSSID spoofing
- - Documented threat model for open and WPA2 networks

## May 3, 2026
- - Drafted functional requirements for scan and alert workflow
- - Listed target platforms: Windows with PyWiFi support

## May 4, 2026
- - Evaluated PyWiFi for wireless interface access
- - Verified local adapter enumeration on development machine

## May 5, 2026
- - Created initial Flask application skeleton
- - Added health-check route for local development

## May 6, 2026
- - Designed REST endpoints for scan and results
- - Planned JSON response schema for network list

## May 7, 2026
- - Set up project virtual environment and dependencies
- - Locked baseline versions in requirements.txt

## May 8, 2026
- - Prototyped basic WiFi scan invocation
- - Logged raw scan result fields for analysis

## May 9, 2026
- - Implemented scan retry handling for empty results
- - Added guard when no wireless interface is found

## May 10, 2026
- - Grouped scan results by SSID in memory
- - Stored BSSID and signal pairs per network name

## May 11, 2026
- - Filtered hidden and empty SSID entries
- - Normalized signal values for downstream scoring

## May 12, 2026
- - Extracted scanner logic into scanner.py module
- - Reduced coupling from Flask route handlers

## May 13, 2026
- - Tuned scan wait interval for stable result sets
- - Tested repeated scans for consistency

## May 14, 2026
- - Started analyzer module with duplicate BSSID detection
- - Assigned initial risk points for multiple BSSIDs

## May 15, 2026
- - Added strong-signal anomaly rule above -50 dBm
- - Recorded human-readable reasons per SSID

## May 16, 2026
- - Implemented signal spread check across duplicate SSIDs
- - Flagged large dBm differences as suspicious

## May 17, 2026
- - Defined SAFE, SUSPICIOUS, and HIGH RISK thresholds
- - Mapped numeric scores to status labels

## May 18, 2026
- - Connected analyzer output to API response payload
- - Returned reasons array for dashboard display

## May 19, 2026
- - Built base HTML layout for monitoring dashboard
- - Added Tailwind CSS via CDN for rapid UI iteration

## May 20, 2026
- - Created network results table with status badges
- - Color-coded HIGH RISK rows for quick triage

## May 21, 2026
- - Added manual rescan button and loading state
- - Wired frontend fetch call to scan endpoint

## May 22, 2026
- - Integrated Chart.js for signal distribution view
- - Plotted per-SSID signal bars from scan data

## May 23, 2026
- - Improved dashboard empty-state messaging
- - Handled no-network and scan-error scenarios

## May 24, 2026
- - Refined mobile-friendly responsive layout
- - Adjusted table overflow for smaller screens

## July 10, 2026
- Initialized WiFi network scanner module using PyWiFi
- Implemented SSID grouping and BSSID deduplication in scanner.py
- Verified scan cycle completes with 5-second result wait

## July 11, 2026
- Built risk scoring engine in analyzer.py with BSSID and signal anomaly rules
- Defined HIGH RISK (>=70), SUSPICIOUS (>=30), and SAFE status thresholds
- Connected analyzer output to dashboard risk display pipeline

