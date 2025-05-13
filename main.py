import network
import socket
import time

# 📶 Připojení k Wi-Fi
SSID = 'A53'
PASSWORD = 'pnrv1845'

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

# 🌐 HTML stránka
def serve_html():
    return """<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <title>Chytrý květináč</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #a8edea, #fed6e3);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background: white;
            padding: 2em;
            border-radius: 16px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            text-align: center;
            width: 90%;
            max-width: 400px;
        }
        h1 {
            font-size: 1.8em;
            margin-bottom: 1em;
        }
        button {
            padding: 1em 2em;
            font-size: 1em;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Vítej u chytrého květináče 🌱</h1>
        <button onclick="alert('Zalévání spuštěno!')">Zalít</button>
    </div>
</body>
</html>"""

# 🌍 Spuštění webového serveru na portu 80
def run_web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print("🚀 Server běží na http://0.0.0.0:80")

    while True:
        cl, addr = s.accept()
        print("💻 Připojeno od:", addr)
        request = cl.recv(1024)
        response = serve_html()
        cl.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        cl.sendall(response)
        cl.close()

# ▶️ Hlavní program
connect_wifi()
run_web_server()


