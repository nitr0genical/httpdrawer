from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Global state memory cache
server_state = {
    "active_password": "1234",  # Default fallback password
    "pixel_queue": []
}

# 🌐 INTERACTIVE DRAWING WEB INTERFACE (HTML/CSS/JS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>16x16 Matrix Transmitter Studio</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background-color: #1e293b;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            border: 1px solid #334155;
            text-align: center;
            width: 380px;
        }
        h1 { color: #38bdf8; margin: 0 0 15px 0; font-size: 22px; }
        
        .config-section {
            background-color: #0f172a;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: left;
        }
        .config-section label {
            font-size: 11px;
            color: #94a3b8;
            text-transform: uppercase;
            font-weight: bold;
            display: block;
            margin-bottom: 4px;
        }
        .config-section input {
            width: 92%;
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 8px;
            color: white;
            border-radius: 4px;
            font-family: monospace;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(16, 20px);
            grid-template-rows: repeat(16, 20px);
            gap: 1px;
            background-color: #334155;
            padding: 4px;
            border-radius: 8px;
            margin-bottom: 15px;
            justify-content: center;
        }
        .pixel {
            width: 20px;
            height: 20px;
            background-color: #000000;
            cursor: pointer;
            border-radius: 2px;
        }
        .palette {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 15px;
            background: #0f172a;
            padding: 8px;
            border-radius: 8px;
            flex-wrap: wrap;
        }
        .swatch {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            cursor: pointer;
            border: 3px solid transparent;
        }
        .swatch.active { border-color: #ffffff; transform: scale(1.1); }
        .btn {
            background-color: #10b981;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 15px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            transition: 0.2s;
        }
        .btn:hover { background-color: #059669; }
        .clear-btn { background-color: #ef4444; margin-top: 8px; }
        .clear-btn:hover { background-color: #dc2626; }
        .status-box { margin-top: 15px; font-size: 13px; color: #38bdf8; min-height: 20px; }
    </style>
</head>
<body>

    <div class="container">
        <h1>🎨 16x16 Matrix Studio</h1>
        
        <!-- Authentication Configuration Layer -->
        <div class="config-section">
            <label>Transmitter Password (Game & Web Match)</label>
            <input type="text" id="tx-password" value="1234" placeholder="Enter matching pass...">
        </div>
        
        <div class="palette">
            <div class="swatch active" style="background-color: #ff0000;" data-r="255" data-g="0" data-b="0"></div>
            <div class="swatch" style="background-color: #00ff00;" data-r="0" data-g="255" data-b="0"></div>
            <div class="swatch" style="background-color: #0000ff;" data-r="0" data-g="0" data-b="255"></div>
            <div class="swatch" style="background-color: #ffff00;" data-r="255" data-g="255" data-b="0"></div>
            <div class="swatch" style="background-color: #00ffff;" data-r="0" data-g="255" data-b="255"></div>
            <div class="swatch" style="background-color: #ff00ff;" data-r="255" data-g="0" data-b="255"></div>
            <div class="swatch" style="background-color: #ffffff;" data-r="255" data-g="255" data-b="255"></div>
            <div class="swatch" style="background-color: #000000;" data-r="0" data-g="0" data-b="0"></div>
        </div>

        <div class="grid" id="pixel-matrix"></div>

        <button class="btn" onclick="sendFrame()">📤 Transmit Frame</button>
        <button class="btn clear-btn" onclick="clearGrid()">🗑️ Clear Matrix</button>
        
        <div class="status-box" id="status">Ready. Draw your design.</div>
    </div>

    <script>
        const grid = document.getElementById('pixel-matrix');
        const swatches = document.querySelectorAll('.swatch');
        let selectedColor = { r: 255, g: 0, b: 0, hex: '#ff0000' };
        let isDrawing = false;

        for (let i = 0; i < 256; i++) {
            const pixel = document.createElement('div');
            pixel.classList.add('pixel');
            pixel.dataset.index = i;
            pixel.dataset.r = "0"; pixel.dataset.g = "0"; pixel.dataset.b = "0";
            
            pixel.addEventListener('mousedown', (e) => { e.preventDefault(); isDrawing = true; paint(pixel); });
            pixel.addEventListener('mouseenter', () => { if(isDrawing) paint(pixel); });
            grid.appendChild(pixel);
        }
        window.addEventListener('mouseup', () => isDrawing = false);

        swatches.forEach(swatch => {
            swatch.addEventListener('click', () => {
                document.querySelector('.swatch.active').classList.remove('active');
                swatch.classList.add('active');
                selectedColor = { 
                    r: parseInt(swatch.dataset.r), 
                    g: parseInt(swatch.dataset.g), 
                    b: parseInt(swatch.dataset.b), 
                    hex: swatch.style.backgroundColor 
                };
            });
        });

        function paint(pixel) {
            pixel.style.backgroundColor = selectedColor.hex;
            pixel.dataset.r = selectedColor.r; 
            pixel.dataset.g = selectedColor.g; 
            pixel.dataset.b = selectedColor.b;
        }

        function clearGrid() {
            document.querySelectorAll('.pixel').forEach(p => {
                p.style.backgroundColor = '#000000';
                p.dataset.r = "0"; p.dataset.g = "0"; p.dataset.b = "0";
            });
            document.getElementById('status').innerText = "Matrix cleared.";
        }

        async function sendFrame() {
            const pixels = document.querySelectorAll('.pixel');
            const dataPayload = [];
            const userPass = document.getElementById('tx-password').value;

            pixels.forEach(p => {
                const idx = parseInt(p.dataset.index);
                dataPayload.push({ 
                    index: idx, 
                    x: idx % 16, 
                    y: Math.floor(idx / 16), 
                    r: parseInt(p.dataset.r), 
                    g: parseInt(p.dataset.g), 
                    b: parseInt(p.dataset.b) 
                });
            });

            document.getElementById('status').innerText = "Transmitting to server...";
            
            try {
                const response = await fetch('/queue-matrix', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        password: userPass,
                        pixels: dataPayload 
                    })
                });
                
                const resData = await response.json();
                if (response.ok) {
                    document.getElementById('status').innerText = `Success! Enqueued ${resData.count} pixels.`;
                } else {
                    document.getElementById('status').innerText = "Error: " + (resData.error || "Failed submission");
                }
            } catch (err) {
                document.getElementById('status').innerText = "Connection error. Check server logs.";
            }
        }
    </script>
</body>
</html>
"""

# 1. PUBLIC ROOT ENTRY POINT (Now opens the drawing tool immediately)
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

# 2. QUEUE PROCESSING ENDPOINT (Receives from Web)
@app.post("/queue-matrix")
def queue_matrix():
    data = request.json
    if not data or "pixels" not in data or "password" not in data:
        return jsonify({"error": "Malformed payload structure"}), 400
    
    server_state["active_password"] = str(data["password"])
    server_state["pixel_queue"] = []

    for p in data["pixels"]:
        server_state["pixel_queue"].append({
            "pixel_index": p["index"],
            "x": p["x"],
            "y": p["y"],
            "r": p["r"],
            "g": p["g"],
            "b": p["b"]
        })
        
    return jsonify({"status": "synchronized", "count": len(server_state["pixel_queue"])}), 200

# 3. ROBLOX HTTP TRANSMITTER ENDPOINT
@app.route('/roblox', methods=["GET"])
def roblox_communication():
    incoming_pass = request.headers.get("Password")
    
    if incoming_pass != server_state["active_password"]:
        return jsonify({"error": "Unauthorized. Password mismatch."}), 401
        
    if len(server_state["pixel_queue"]) > 0:
        return jsonify(server_state["pixel_queue"].pop(0)), 200
        
    return jsonify({"status": "idle"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
