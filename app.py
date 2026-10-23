from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

server_cache = {"value": 0}

BIT_LENGTH = 8
PASSWORD = "1234"  # Change this to match your Build Logic HTTP Transmitter Password Header

# 🌐 VISUAL DASHBOARD TEMPLATE (HTML/CSS/JS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Build Logic HTTP Reader</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .card {
            background-color: #1e293b;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            text-align: center;
            width: 380px;
            border: 1px solid #334155;
        }
        h1 { color: #38bdf8; font-size: 24px; margin-bottom: 20px; }
        .data-box {
            background-color: #0f172a;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid #38bdf8;
        }
        .label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
        .binary-display { font-family: monospace; font-size: 32px; font-weight: bold; color: #38bdf8; margin: 10px 0; letter-spacing: 2px; }
        .decimal-display { font-size: 16px; color: #cbd5e1; }
        .btn {
            background-color: #38bdf8;
            color: #0f172a;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            margin-top: 10px;
            width: 100%;
            transition: 0.2s;
        }
        .btn:hover { background-color: #0ea5e9; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📡 Build Logic Reader</h1>
        
        <div class="data-box">
            <div class="label">Binary Stream</div>
            <div class="binary-display" id="bin-val">00000000</div>
            <div class="decimal-display">Decimal Value: <span id="dec-val">0</span></div>
        </div>

        <button class="btn" onclick="fetchData()">🔄 Force Refresh</button>
    </div>

    <script>
        async function fetchData() {
            try {
                // Fetch the raw data from the server's data endpoint
                const response = await fetch('/data');
                const data = await response.json();
                
                const binaryStr = data.value;
                document.getElementById('bin-val').innerText = binaryStr;
                
                // Convert binary string back to standard Base-10 number for easy viewing
                document.getElementById('dec-val').innerText = parseInt(binaryStr, 2);
            } catch (error) {
                console.error("Error reading data:", error);
            }
        }

        // Auto-refresh the visual dashboard every 2 seconds
        setInterval(fetchData, 2000);
        fetchData();
    </script>
</body>
</html>
"""

# 1. WEB BROWSER INTERFACE: Serves the visual .read website
@app.route('/', methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

# 2. BROWSER DATA FETCH: Allows the visual dashboard to grab data without authentication
@app.route('/data', methods=["GET"])
def get_browser_data():
    return jsonify({"value": format(server_cache["value"], f'0{BIT_LENGTH}b')}), 200

# 3. ROBLOX INTERFACE: Handles the transmission from Build Logic
@app.route('/roblox', methods=["GET", "POST"])
def roblox_communication():
    if request.method == "POST":
        password = request.headers.get("Password")
        if password != PASSWORD:
            return jsonify({"error": "Unauthorized. Invalid or missing password."}), 401
 
        binary_value = request.form.get("value")
        if binary_value and len(binary_value) == BIT_LENGTH and all(c in "01" for c in binary_value):
            server_cache["value"] = int(binary_value, 2)
            return jsonify({"value": format(server_cache["value"], f'0{BIT_LENGTH}b')}), 200
 
        return jsonify({"error": f"Invalid binary value. Must be {BIT_LENGTH} bits of 0s and 1s."}), 400
 
    elif request.method == "GET":
        return jsonify({"value": format(server_cache["value"], f'0{BIT_LENGTH}b')}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
