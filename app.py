from flask import Flask, render_template
from scanner import scan_networks
from analyzer import analyze_networks

app = Flask(__name__)
    
@app.route("/")
def index():        
    networks = scan_networks()
    analyzed = analyze_networks(networks)   
    # Summary for chart       
    summary = {"SAFE": 0, "SUSPICIOUS": 0, "HIGH_RISK": 0}
   
    for net in analyzed:
           
        if net["status"] == "HIGH RISK":
            summary["HIGH_RISK"] += 1
        else:
            summary[net["status"]] += 1

    return render_template("index.html", data=analyzed, summary=summary)
      
if __name__ == "__main__":
    app.run(debug=True)