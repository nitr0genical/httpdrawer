from flask import Flask, jsonify, request, render_template_string, abort

app = Flask(__name__)

# 🔐 SECURITY ARCHITECTURE
SECRET_CANVAS_PATH = "mysecretcanvas99"  # Change this to your secret URL path extensions

# Global state memory cache
server_state = {
    "active_password": "1234",  # Fallback default password
    "pixel_queue": []
}

# 🌐 INTERACTIVE DRAWING WEB INTERFACE (HTML/CSS/JS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Private Studio Matrix</title>
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
            width: 360px;
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
            width: 30px;
            height: 30px;
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
            font-size: 16px;
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
        <h1>🎨 Matrix Studio</h1>
        
        <!-- Authentication Configuration Layer -->
        <div class="config-section">
            <label>Transmitter Password Setup</label>
            <input type="text" id="tx-password" value="1234" placeholder="Enter custom pass...">
        </div>
        
        <div class="palette">
            <div class="swatch active" style="background-color: #ff0000;" data-r="3" data-g="0" data-b="0"></div>
            <div class="swatch" style="background-color: #00ff00;" data-r="0" data-g="3" data-b="0"></div>
            <div class="swatch" style="background-color: #0000ff;" data-r="0" data-g="0" data-b="3"></div>
            <div class="swatch" style="background-color: #ffff00;" data-r="3" data-g="3" data-b="0"></div>
            <div class="swatch" style="background-color: #00ffff;" data-r="0" data-g="3" data-b="3"></div>
            <div class="swatch" style="background-color: #ff00ff;" data-r="3" data-g="0" data-b="3"></div>
            <div class="swatch" style="background-color: #ffffff;" data-r="3" data-g="3" data-b="3"></div>
            <div class="swatch" style="background-color: #000000;" data-r="0" data-g="0" data-b="0"></div>
        </div>

        <div class="grid" id="pixel-matrix"></div>

        <button class="btn" onclick="sendFrame()">📤 Send Frame to Roblox</button>
        <button class="btn clear-btn" onclick="clearGrid()">🗑️ Clear Matrix</button>
        
        <div class="status-box" id="status">Ready. Draw your matrix grid.</div>
    </div>

    <script>
        const grid = document.getElementById('pixel-matrix');
        const swatches = document.querySelectorAll('.swatch');
        let selectedColor = { r: 3, g: 0, b: 0, hex: '#ff0000' };
        let isDrawing = false;

        // Populate Matrix Architecture
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
                selectedColor = { r: swatch.dataset.r, g: swatch.dataset.g, b: swatch.dataset.b, hex: swatch.style.backgroundColor };
            });
        });

        function paint(pixel) {
            pixel.style.backgroundColor = selectedColor.hex;
            pixel.dataset.r = selectedColor.r; pixel.dataset.g = selectedColor.g; pixel.dataset.b = selectedColor.b;
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

            document.getElementById('status').innerText = "Compressing & sending queue...";
            
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
                    document.getElementById('status').innerText = `Success! Saved password & enqueued ${resData.count} pixels.`;
                } else {
                    document.getElementById('status').innerText = "Error: " + (resData.error || "Failed submission");
                }
            } catch (err) {
                document.getElementById('status').innerText = "Connection error. Check Render log status.";
            }
        }
    </script>
</body>
</html>
"""

# 1. ROOT ENTRY POINT: Blocked public pathing
@app.route("/", methods=["GET"])
def index():
    abort(404)

# 2. PRIVATE GUI ACCESS VIA SECURED PATH ROUTE
@app.route(f"/{SECRET_CANVAS_PATH}", methods=["GET"])
def secret_dashboard():
    return render_template_string(HTML_TEMPLATE)

# 3. ROOT PATH QUEUE PROCESSING ENDPOINT
@app.post("/queue-matrix")
def queue_matrix():
    data = request.json
    if not data or "pixels" not in data or "password" not in data:
        return jsonify({"error": "Malformed payload structure"}), 400
    
    # Save the custom password defined inside your canvas input text box
    server_state["active_password"] = str(data["password"])
    server_state["pixel_queue"] = []  # Clear out history array configurations

    for p in data["pixels"]:
        bin_r = format(p["r"], '02b')
        bin_g = format(p["g"], '02b')
        bin_b = format(p["b"], '02b')
        binary_rgb = f"{bin_r}{bin_g}{bin_b}"
        
        server_state["pixel_queue"].append({
            "pixel_index": p["index"],
            "x": p["x"],
            "y": p["y"],
            "binary_rgb": binary_rgb,
            "r_val": p["r"],
            "g_val": p["g"],
            "b_val": p["b"]
        })
        
    return jsonify({"status": "synchronized", "count": len(server_state["pixel_queue"])}), 200

@app.route('/roblox', methods=["GET"])
def roblox_communication():
    # Read authorization keys passed from the game
    incoming_pass = request.headers.get("Password")
    if incoming_pass != server_state["active_password"]:
        return jsonify({"error": "Unauthorized. Password header mismatch."}), 401
    if len(server_state["pixel_queue"]) > 0:
        return jsonify(server_state["pixel_queue"].pop(0)), 200
    return jsonify({"status": "idle"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
