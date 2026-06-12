def analyze_networks(networks):
    analyzed_data = []

    for ssid, bssids in networks.items():

        safe_ssid = ssid.encode('ascii', 'ignore').decode()

        risk_score = 0
        reasons = []

        unique_entries = list(bssids.items())
        signals = [signal for _, signal in unique_entries]    

        if len(unique_entries) > 1:
            risk_score += 40
            reasons.append("Multiple BSSID detected")    

        for signal in signals:
            if signal > -50:
                risk_score += 20
                reasons.append("Unusually strong signal")     

        if len(signals) > 1:  
            diff = max(signals) - min(signals)
            if diff > 20:
                risk_score += 30     
                reasons.append("Large signal strength difference")          
       
        if risk_score >= 70:
            status = "HIGH RISK"              
        elif risk_score >= 30:
            status = "SUSPICIOUS"              
        else:
            status = "SAFE"           

        analyzed_data.append({
            "ssid": safe_ssid,
            "risk": risk_score,       
            "status": status,
            "reasons": list(set(reasons)),
            "details": unique_entries
        })

    return analyzed_data