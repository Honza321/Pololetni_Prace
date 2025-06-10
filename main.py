import network
import socket
import time
import machine
import dht

# --- KONFIGURACE ---
SSID = 'A53'
PASSWORD = 'pnrv1845'

# Specifická IP adresa pro server
SERVER_IP = '192.168.50.40'
SERVER_PORT = 80

# Kalibrační hodnoty pro půdní vlhkoměr


SOIL_DRY_VALUE = 200 

SOIL_WET_VALUE = 270


# --- INICIALIZACE HARDWARU ---

# Inicializace senzoru DHT11 na GPIO 2 (Pin 4 na Pico W)
dht_sensor = dht.DHT11(machine.Pin(2))

# Inicializace analogového půdního vlhkoměru na ADC0 (GPIO 26 / Pin 31 na Pico W)
soil_sensor_pin = machine.ADC(26) 


# --- FUNKCE PRO WI-FI PŘIPOJENÍ ---

def connect_wifi():
    # Připojí se k Wi-Fi síti.
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


# --- FUNKCE PRO SENZORY ---

def get_sensor_data():
    # Čte hodnoty z DHT11 a půdního vlhkoměru.
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

        
        
        if SOIL_DRY_VALUE != SOIL_WET_VALUE:
            
            soil_percent = 100 - ((soil_raw - SOIL_WET_VALUE) / (SOIL_DRY_VALUE - SOIL_WET_VALUE)) * 100
            
            soil_percent = max(0, min(100, soil_percent))
            soil_percent = round(soil_percent, 1) # Zaokrouhlení na jedno desetinné místo
        else:
            soil_percent = 0 
    except Exception as e:
        print("Chyba při čtení půdního vlhkoměru:", e)

    return temperature, humidity, soil_percent 


# --- WEB SERVER A HTML STRÁNKA ---

def serve_html(temp, hum, soil_hum_percent):
    # Generuje HTML stránku s daty.
    temp_str = f"{temp} °C" if temp != -1 else "N/A"
    hum_str = f"{hum} %" if hum != -1 else "N/A"
    soil_hum_percent_str = f"{soil_hum_percent} %" if soil_hum_percent != -1 else "N/A" 

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            background: white;
            padding: 2em;
            border-radius: 16px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            text-align: center;
            width: 100%;
            max-width: 400px;
        }}
        h1 {{
            font-size: 1.8em;
            margin-bottom: 1em;
            color: #333;
        }}
        .sensor {{
            font-size: 1.2em;
            margin: 0.8em 0;
            color: #555;
            display: flex;
            justify-content: space-between;
            padding: 0 10px;
        }}
        .sensor strong {{
            font-weight: bold;
            color: #222;
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

        setInterval(updateData, 5000);
        window.onload = updateData;
    </script>
</head>
<body>
    <div class="container">
        <h1>Chytrý květináč 🌱</h1>
        <p class="sensor"><span>🌡️ Teplota:</span> <strong id="temp">{temp_str}</strong></p>
        <p class="sensor"><span>💧 Vlhkost vzduchu:</span> <strong id="hum">{hum_str}</strong></p>
        <p class="sensor"><span>🌱 Vlhkost půdy:</span> <strong id="soil_hum">{soil_hum_percent_str}</strong></p>
    </div>
</body>
</html>"""
    return html

def run_web_server():
    # Nastaví a spustí webový server.
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


# --- SPUŠTĚNÍ PROGRAMU ---
connect_wifi()
run_web_server()