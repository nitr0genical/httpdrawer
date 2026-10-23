from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Server configuration
PASSWORD = "1234"  # Match this password in your Roblox Transmitter Header
BIT_LENGTH = 6     # 2 bits Red, 2 bits Green, 2 bits Blue

# A FIFO (First-In, First-Out) list to hold pixels waiting to be requested by Roblox
pixel_queue = []

# 🌐 INTERACTIVE DRAWING WEB INTERFACE (HTML/CSS/JS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Build Logic Canvas Matrix</title>
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
        }
        h1 { color: #38bdf8; margin: 0 0 15px 0; font-size: 24px; }
        
        /* 16x16 Canvas Matrix grid styling */
        .grid {
            display: grid;
            grid-template-columns: repeat(16, 20px);
            grid-template-rows: repeat(16, 20px);
            gap: 1px;
            background-color: #334155;
            padding: 4px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .pixel {
            width: 20px;
            height: 20px;
            background-color: #000000;
            cursor: pointer;
            border-radius: 2px;
            transition: background 0.1s ease;
        }
        
        /* Toolkit layout */
        .palette {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 20px;
            background: #0f172a;
            padding: 10px;
            border-radius: 8px;
        }
        .swatch {
            width: 35px;
            height: 35px;
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
        
        .status-box {
            margin-top: 15px;
            font-size: 14px;
            color: #94a3b8;
        }
    </style>
</head>
<body>

    <div class="container">
        <h1>🎨 Matrix Studio</h1>
        
        <!-- Color selections mapping to 6-bit configurations -->
        <div class="palette">
            <!-- Colors are predefined with maximum values for their bits -->
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
        
        <div class="status-box" id="status">Draw your artwork and press Send.</div>
    </div>

    <script>
        const grid = document.getElementById('pixel-matrix');
        const swatches = document.querySelectorAll('.swatch');
        let selectedColor = { r: 3, g: 0, b: 0, hex: '#ff0000' };
        let isDrawing = false;

        // Initialize 16x16 working canvas
        for (let i = 0; i < 256; i++) {
            const pixel = document.createElement('div');
            pixel.classList.add('pixel');
            pixel.dataset.index = i;
            pixel.dataset.r = "0";
            pixel.dataset.g = "0";
            pixel.dataset.b = "0";
            
            // Mouse drawing binds
            pixel.addEventListener('mousedown', () => { isDrawing = true; paint(pixel); });
            pixel.addEventListener('mouseenter', () => { if(isDrawing) paint(pixel); });
            grid.appendChild(pixel);
        }
        window.addEventListener('mouseup', () => isDrawing = false);

        // Palette Selector logic
        swatches.forEach(swatch => {
            swatch.addEventListener('click', () => {
                document.querySelector('.swatch.active').classList.remove('active');
                swatch.classList.add('active');
                selectedColor = {
                    r: swatch.dataset.r,
                    g: swatch.dataset.g,
                    b: swatch.dataset.b,
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

        // Convert the structural layout into sequential pixel updates
        async function sendFrame() {
            const pixels = document.querySelectorAll('.pixel');
            const dataPayload = [];

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

            document.getElementById('status').innerText = "Streaming matrix array data...";

            try {
                const response = await fetch('/queue-matrix', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pixels: dataPayload })
                });
                const resData = await response.json();
                document.getElementById('status').innerText = `Success! Enqueued ${resData.count} pixel nodes.`;
            } catch (err) {
                document.getElementById('status').innerText = "Error syncing canvas array.";
            }
        }
    </script>
</body>
</html>
"""

# 1. BROWSER GUI ROUTE
@app.get("/")
def index():
    return render_template_string(HTML_TEMPLATE)

# 2. WEB APP BACKEND COMPILER: Accepts the drawing and stores pixels sequentially
@app.post("/queue-matrix")
def queue_matrix():
    data = request.json
    if not data or "pixels" not in data:
        return jsonify({"error": "Missing payload"}), 400
    
    global pixel_queue
    pixel_queue = [] # Wipe any stale, leftover data strings

    for p in data["pixels"]:
        # Map values (0-3 max) into binary strings of 2 bits each
        bin_r = format(p["r"], '02b')
        bin_g = format(p["g"], '02b')
        bin_b = format(p["b"], '02b')
        
        # Merge values to produce a single 6-bit data packet (RR_GG_BB)
        binary_rgb = f"{bin_r}{bin_g}{bin_b}"
        
        pixel_queue.append({
            "pixel_index": p["index"],
            "x": p["x"],
            "y": p["y"],
            "binary_rgb": binary_rgb,
            "r_val": p["r"],
            "g_val": p["g"],
            "b_val": p["b"]
        })
        
    return jsonify({"status": "queued", "count": len(pixel_queue)}), 200

# 3. ROBLOX API PIPELINE: Delivers one single pixel per call to the transmitter
@app.route('/roblox', methods=["GET"])
def roblox_communication():
    password = request.headers.get("Password")
    if password != PASSWORD:
        return jsonify({"error": "Unauthorized. Invalid password header."}), 401
    
    global pixel_queue
    if len(pixel_queue) > 0:
        # Pull the oldest pixel out of the array line
        next_pixel = pixel_queue.pop(0)
        return jsonify(next_pixel), 200
    
    return jsonify({"status": "idle"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
