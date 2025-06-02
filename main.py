import network
import socket
import time
import machine
import dht

# 📶 Wi-Fi připojení
SSID = 'A53'
PASSWORD = 'pnrv1845'

# 🌡️ Inicializace senzoru DHT11 (např. GP2 = fyzický pin 4)
dht_sensor = dht.DHT11(machine.Pin(2))

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("📡 Připojuji se k Wi-Fi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("✅ Připojeno k Wi-Fi")
    print("🌐 IP adresa:", wlan.ifconfig()[0])

# 📊 Čtení hodnot ze senzoru
def get_sensor_data():
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
    except Exception as e:
        print("❌ Chyba při čtení DHT11:", e)
        temperature = humidity = -1
    return temperature, humidity

# 🌐 HTML stránka s JavaScriptem pro automatické aktualizace
def serve_html(temp, hum):
    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <title>Chytrý květináč</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #a8edea, #fed6e3);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}
        .container {{
            background: white;
            padding: 2em;
            border-radius: 16px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            text-align: center;
            width: 90%;
            max-width: 400px;
        }}
        h1 {{
            font-size: 1.8em;
            margin-bottom: 1em;
        }}
        .sensor {{
            font-size: 1.2em;
            margin: 0.5em 0;
        }}
        button {{
            padding: 1em 2em;
            font-size: 1em;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
        }}
        button:hover {{
            background-color: #45a049;
        }}
    </style>
    <script>
        function updateData() {{
            fetch('/data')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('temp').textContent = data.temp + " °C";
                    document.getElementById('hum').textContent = data.hum + " %";
                }})
                .catch(err => console.error("Chyba při načítání dat:", err));
        }}

        setInterval(updateData, 5000);
        window.onload = updateData;
    </script>
</head>
<body>
    <div class="container">
        <h1>Chytrý květináč 🌱</h1>
        <p class="sensor">🌡️ Teplota: <strong id="temp">{temp} °C</strong></p>
        <p class="sensor">💧 Vlhkost vzduchu: <strong id="hum">{hum} %</strong></p>
        <button onclick="alert('Zalévání spuštěno!')">Zalít</button>
    </div>
</body>
</html>"""

# 🌍 Webový server
def run_web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("🚀 Server běží na http://0.0.0.0:80")

    while True:
        cl, addr = s.accept()
        print("💻 Připojeno od:", addr)
        request = cl.recv(1024).decode()
        print("📥 Request:", request)

        if "GET /data" in request:
            temp, hum = get_sensor_data()
            json_response = f'{{"temp": {temp}, "hum": {hum}}}'
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            cl.sendall(json_response)
        else:
            temp, hum = get_sensor_data()
            html = serve_html(temp, hum)
            cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            cl.sendall(html)

        cl.close()

# ▶️ Spuštění
connect_wifi()
run_web_server()
