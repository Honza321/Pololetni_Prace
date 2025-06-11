import network
import socket
import time
import machine
import dht

# --- KONFIGURACE ---
SSID = 'A53'
PASSWORD = 'pnrv1845'

SERVER_IP = '192.168.50.40'
SERVER_PORT = 80

SOIL_DRY_VALUE = 200    
SOIL_WET_VALUE = 7200   

# --- INICIALIZACE ---
dht_sensor = dht.DHT11(machine.Pin(2))
soil_sensor_pin = machine.ADC(26)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Připojuji se k Wi-Fi...")
        wlan.connect(SSID, PASSWORD)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
        print()
    if wlan.isconnected():
        print("Připojeno k Wi-Fi")
        print("IP adresa:", wlan.ifconfig()[0])
    else:
        print("Nepodařilo se připojit k Wi-Fi!")

def get_sensor_data():
    temperature = -1
    humidity = -1
    soil_raw = -1
    soil_percent = -1

    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()
    except Exception as e:
        print("Chyba při čtení DHT11:", e)
    
    try:
        soil_raw = soil_sensor_pin.read_u16()
        print(f"Raw soil moisture: {soil_raw}")
        if SOIL_WET_VALUE != SOIL_DRY_VALUE:
            soil_percent = ((soil_raw - SOIL_DRY_VALUE) / (SOIL_WET_VALUE - SOIL_DRY_VALUE)) * 100
            soil_percent = max(0, min(100, soil_percent))
            soil_percent = round(soil_percent, 1)
        else:
            soil_percent = 0
    except Exception as e:
        print("Chyba při čtení vlhkosti půdy:", e)

    return temperature, humidity, soil_percent 

def serve_html(temp, hum, soil_hum_percent):
    temp_str = f"{temp} °C" if temp != -1 else "N/A"
    hum_str = f"{hum} %" if hum != -1 else "N/A"
    soil_hum_percent_str = f"{soil_hum_percent} %" if soil_hum_percent != -1 else "N/A" 

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Chytrý květináč</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0; padding: 0;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #d4edda, #a8d5a3);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
            transition: background 0.3s ease, color 0.3s ease;
            color: #2d4a1f;
        }}
        .dark-mode {{
            background: #1e2e12;
            color: #c7e4a1;
        }}
        .dark-mode .container {{
            background: #2d3e18;
            box-shadow: 0 0 20px rgba(199, 228, 161, 0.7);
            color: #c7e4a1;
        }}
        .toggle-dark {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 16px;
            background: #2d4a1f;
            color: #d0f0a7;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            z-index: 1000;
            box-shadow: 0 0 10px #d0f0a7;
            transition: background 0.3s ease, color 0.3s ease;
        }}
        .toggle-dark:hover {{
            background: #3e6129;
            color: #e1f8b6;
        }}
        .container {{
            background: white;
            padding: 2.5em;
            border-radius: 16px;
            box-shadow: 0 0 25px rgba(45, 74, 31, 0.2);
            text-align: center;
            width: 100%;
            max-width: 420px;
            min-height: 480px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #2d4a1f;
            transition: color 0.3s ease;
        }}
        h1 {{
            font-size: 2em;
            margin-bottom: 1.2em;
            color: #1f3a0d;
            transition: color 0.3s ease;
        }}
        .dark-mode h1 {{
            color: #d0f0a7;
            text-shadow: 0 0 10px #a9d86e;
        }}
        .sensor {{
            font-size: 1.2em;
            margin: 0.8em 0;
            display: flex;
            justify-content: space-between;
            padding: 0 10px;
            color: #3a5f21;
            transition: color 0.3s ease;
        }}
        .sensor strong {{
            font-weight: bold;
            color: #254214;
        }}
        .dark-mode .sensor {{
            color: #c7e4a1;
        }}
        .dark-mode .sensor strong {{
            color: #b0d06d;
        }}
        .button-container {{
            margin-top: 2em;
        }}
        .button-container button {{
            padding: 12px 24px;
            border: none;
            background: #4a7a1f;
            color: white;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            transition: background 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 0 8px #4a7a1f;
        }}
        .button-container button:hover {{
            background: #3e661a;
            box-shadow: 0 0 12px #3e661a;
        }}
        .dark-mode .button-container button {{
            background: #7fbf3e;
            box-shadow: 0 0 10px #7fbf3e;
            color: #1e2e12;
        }}
        .dark-mode .button-container button:hover {{
            background: #a2d455;
            box-shadow: 0 0 14px #a2d455;
        }}
    </style>
    <script>
        function updateData() {{
            fetch('/data')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('temp').textContent = data.temp + " °C";
                    document.getElementById('hum').textContent = data.hum + " %";
                    document.getElementById('soil_hum').textContent = data.soil_hum + " %"; 
                }})
                .catch(err => console.error("Chyba při načítání dat:", err));
        }}

        function toggleDarkMode() {{
            document.body.classList.toggle("dark-mode");
        }}

        function zalitKvetinac() {{
            alert("Zalévání spuštěno! 💧");
        }}

        setInterval(updateData, 5000);
        window.onload = updateData;
    </script>
</head>
<body>
    <button class="toggle-dark" onclick="toggleDarkMode()">🌙 Noční režim</button>
    <div class="container">
        <h1>Chytrý květináč 🌱</h1>
        <p class="sensor"><span>🌡️ Teplota:</span> <strong id="temp">{temp_str}</strong></p>
        <p class="sensor"><span>💧 Vlhkost vzduchu:</span> <strong id="hum">{hum_str}</strong></p>
        <p class="sensor"><span>🌱 Vlhkost půdy:</span> <strong id="soil_hum">{soil_hum_percent_str}</strong></p>
        <div class="button-container">
            <button onclick="zalitKvetinac()">💦 Zalít květináč</button>
        </div>
    </div>
</body>
</html>"""
    return html


def run_web_server():
    addr = socket.getaddrinfo(SERVER_IP, SERVER_PORT)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print(f"Server běží na http://{SERVER_IP}:{SERVER_PORT}") 

    while True:
        try:
            cl, addr = s.accept()
            print("Připojeno od:", addr)
            request = cl.recv(1024).decode()
            print("Request:", request)

            if "GET /data" in request:
                temp, hum, soil_hum_percent = get_sensor_data()
                json_response = f'{{"temp": {temp}, "hum": {hum}, "soil_hum": {soil_hum_percent}}}'
                cl.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
                cl.sendall(json_response)
            else: 
                temp, hum, soil_hum_percent = get_sensor_data()
                html = serve_html(temp, hum, soil_hum_percent)
                cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
                cl.sendall(html)

            cl.close()
            time.sleep(0.1)

        except OSError as e:
            print("Chyba socketu:", e)
            cl.close()
        except Exception as e:
            print("Neočekávaná chyba:", e)
            cl.close()

# --- START ---
connect_wifi()
run_web_server()
