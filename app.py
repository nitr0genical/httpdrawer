from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Global state memory cache
server_state = {
    "active_password": "0",
    "pixel_queue": [],
    "reset_signal": False
}

# 🌐 INTERACTIVE DRAWING WEB INTERFACE (HTML/CSS/JS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTTP drawer</title>
    <style>
        body {
            font-family: 'Courier New', Courier, monospace;
            background-color: #090d16;
            color: #cbd5e1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }
        .container {
            background-color: #111827;
            padding: 20px;
            border-radius: 0px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.8);
            border: 2px solid #374151;
            text-align: center;
            width: 380px;
        }
        h1 { color: #f8fafc; margin: 0 0 15px 0; font-size: 20px; text-transform: uppercase; letter-spacing: 1px; }
        
        .config-section {
            background-color: #1f2937;
            padding: 10px;
            border-radius: 0px;
            margin-bottom: 15px;
            text-align: left;
            border: 1px solid #374151;
        }
        .config-section label {
            font-size: 10px;
            color: #9ca3af;
            text-transform: uppercase;
            font-weight: bold;
            display: block;
            margin-bottom: 4px;
        }
        .config-section input {
            width: 93%;
            background-color: #111827;
            border: 1px solid #4b5563;
            padding: 6px;
            color: #f8fafc;
            border-radius: 0px;
            font-family: monospace;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(16, 18px);
            grid-template-rows: repeat(16, 18px);
            gap: 1px;
            background-color: #374151;
            padding: 4px;
            border-radius: 0px;
            margin-bottom: 15px;
            justify-content: center;
            border: 1px solid #4b5563;
        }
        .pixel {
            width: 18px;
            height: 18px;
            background-color: #000000;
            cursor: pointer;
            border-radius: 0px;
        }
        .palette {
            display: flex;
            justify-content: center;
            gap: 6px;
            margin-bottom: 15px;
            background: #1f2937;
            padding: 8px;
            border-radius: 0px;
            border: 1px solid #374151;
            flex-wrap: wrap;
        }
        .swatch {
            width: 24px;
            height: 24px;
            border-radius: 0px;
            cursor: pointer;
            border: 2px solid #374151;
        }
        .swatch.active { border-color: #ffffff; }
        .btn {
            background-color: #374151;
            color: #f8fafc;
            border: 1px solid #4b5563;
            padding: 10px;
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
            border-radius: 0px;
            cursor: pointer;
            width: 100%;
            transition: 0.1s;
            margin-bottom: 6px;
            font-family: 'Courier New', Courier, monospace;
        }
        .btn:hover { background-color: #4b5563; color: #ffffff; }
        .transmit-btn { background-color: #1f2937; border-color: #6b7280; }
        .transmit-btn:hover { background-color: #374151; }
        
        .status-box { margin-top: 12px; font-size: 12px; color: #9ca3af; min-height: 18px; }
        .credits { margin-top: 15px; font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; }
    </style>
</head>
<body>

    <div class="container">
        <h1>Httpmitter</h1>
        
        <div class="config-section">
            <label>Transmitter Password</label>
            <input type="text" id="tx-password" value="1234" placeholder="enter pass...">
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

        <button class="btn transmit-btn" onclick="sendFrame()">Transmit Frame</button>
        <button class="btn" onclick="stopTransmission()">Force Stop + Reset</button>
        <button class="btn" onclick="clearGrid()">Clear Frame</button>
        
        <div class="status-box" id="status">Ready</div>
        <div class="credits">Powered by Gemini AI</div>
    </div>

    <script>
        const grid = document.getElementById('pixel-matrix');
        const swatches = document.querySelectorAll('.swatch');
        let selectedColor = { r: 3, g: 0, b: 0, hex: '#ff0000' };
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
            document.getElementById('status').innerText = "Matrix cleared locally";
        }

        async function sendFrame() {
            const pixels = document.querySelectorAll('.pixel');
            const dataPayload = [];
            const userPass = document.getElementById('tx-password').value;

            let lastActiveIndex = -1;
            pixels.forEach((p, idx) => {
                if (parseInt(p.dataset.r) > 0 || parseInt(p.dataset.g) > 0 || parseInt(p.dataset.b) > 0) {
                    lastActiveIndex = idx;
                }
            });

            if (lastActiveIndex === -1) {
                document.getElementById('status').innerText = "Frame is empty!";
                return;
            }

            for (let i = 0; i <= lastActiveIndex; i++) {
                const p = pixels[i];
                dataPayload.push({ 
                    index: i, 
                    x: i % 16, 
                    y: Math.floor(i / 16), 
                    r: parseInt(p.dataset.r), 
                    g: parseInt(p.dataset.g), 
                    b: parseInt(p.dataset.b) 
                });
            }

            document.getElementById('status').innerText = `Transmitting ${dataPayload.length} pixels...`;
            
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
                    document.getElementById('status').innerText = "Success";
                } else {
                    document.getElementById('status').innerText = "Error: " + (resData.error || "Failed");
                }
            } catch (err) {
                document.getElementById('status').innerText = "Connection error";
            }
        }

        async function stopTransmission() {
            const userPass = document.getElementById('tx-password').value;
            document.getElementById('status').innerText = "Stopping & resetting...";

            try {
                const response = await fetch('/stop-queue', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: userPass })
                });
                
                if (response.ok) {
                    document.getElementById('status').innerText = "Stopped + Reset";
                } else {
                    document.getElementById('status').innerText = "Error";
                }
            } catch (err) {
                document.getElementById('status').innerText = "Connection error";
            }
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.post("/queue-matrix")
def queue_matrix():
    data = request.json
    if not data or "pixels" not in data or "password" not in data:
        return jsonify({"error": "Malformed payload structure"}), 400
    
    server_state["active_password"] = str(data["password"])
    server_state["pixel_queue"] = []
    server_state["reset_signal"] = False

    # 1. Initial Reset signal with Clock = 0 (00000010 -> Reset=1, Clock=0)
    server_state["pixel_queue"].append({"value": "00000010"})

    # 2. Stream pixels with Clock permanently set to 1 (C=1)
    for idx, p in enumerate(data["pixels"]):
        bin_r = format(p["r"] & 3, '02b')
        bin_g = format(p["g"] & 3, '02b')
        bin_b = format(p["b"] & 3, '02b')
        rgb_6bit = f"{bin_r}{bin_g}{bin_b}"
        
        # Reset=0, Clock=1
        server_state["pixel_queue"].append({"value": f"{rgb_6bit}01"})
        
    return jsonify({"status": "synchronized", "count": len(server_state["pixel_queue"])}), 200

@app.post("/stop-queue")
def stop_queue():
    data = request.json
    if data and "password" in data and str(data["password"]) == server_state["active_password"]:
        server_state["pixel_queue"] = []
        server_state["reset_signal"] = True
        return jsonify({"status": "stopped"}), 200
    return jsonify({"error": "Unauthorized"}), 401

@app.route('/roblox', methods=["GET"])
def roblox_communication():
    incoming_pass = request.headers.get("Password")
    client_status = request.args.get("client_status", "unknown")
    
    if incoming_pass != server_state["active_password"]:
        return jsonify({"value": "00000000"}), 200
        
    if server_state["reset_signal"]:
        server_state["reset_signal"] = False
        return jsonify({"value": "00000010"}), 200  # Reset=1, Clock=0
        
    if len(server_state["pixel_queue"]) > 0:
        return jsonify(server_state["pixel_queue"].pop(0)), 200
        
    return jsonify({"value": "00000000"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
