from flask import Flask, send_file, jsonify, request
from pathlib import Path
import subprocess
from datetime import datetime
import tempfile
import os
import io
import serial
import time

app = Flask(__name__)

# Inicjalizacja sprzętowego portu szeregowego 
try:
    arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
    time.sleep(2)  # Dajemy 2 sekundy na restart Arduino po otwarciu portu
except Exception as e:
    print(f"[ERROR] Nie można otworzyć portu Arduino: {e}")
    arduino = None


def take_photo():
    # 1. Wyślij komendę 'C' do Arduino, żeby zapalić białe LEDy
    global arduino
    if arduino and arduino.is_open:
        try:
            arduino.reset_input_buffer()
            arduino.reset_output_buffer()
            arduino.write(b'C')
            arduino.flush()
            time.sleep(0.5) # Dajmy Arduino ułamek sekundy na włączenie przekaźnika
        except Exception as e:
            print(f"Błąd zapalania LEDów: {e}")

    # 2. Zrób zdjęcie
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = Path(tempfile.gettempdir())
    filename = tmp_dir / f"photo_{timestamp}.jpg"
    cmd = ["rpicam-still", "--width", "4056", "--height", "3040", "-o", str(filename), "-n"]
    subprocess.run(cmd, check=True)
    if arduino and arduino.is_open:
        try:
            arduino.write(b'X')
            arduino.flush()
        except Exception as e:
            print(f"Bład gaszenia led {e}")
    return filename

@app.route("/capture", methods=["POST"])
def capture():
    try:
        filename = take_photo()
        with open(filename, 'rb') as f:
            bufor_zdjecia = io.BytesIO(f.read())
        os.remove(filename)
        return send_file(bufor_zdjecia, mimetype="image/jpeg")
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "error": f"Capture failed: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 501

@app.route("/bump", methods=["POST"])
def bump():
    return "Bump", 200


@app.route('/arduino', methods=['POST'])
def arduino_command():
    if not arduino or not arduino.is_open:
        return jsonify({"status": "error", "error": "Brak fizycznego połączenia z Arduino"}), 500
    
    data = request.get_json()
    cmd = data.get('cmd', '')
    
    try:
        # 1. Czyszczenie buforów i wysłanie komendy (np. "L", "R", "P 5.5")
        arduino.reset_input_buffer()
        arduino.reset_output_buffer()
        arduino.write(cmd.encode('utf-8'))
        arduino.flush()
        
        # 2. Obsługa odpowiedzi dla komend, które faktycznie coś zwracają (Sensory i Bump)
        if cmd in ['R', 'B']:
            # Czekamy na odpowiedź z mikrokontrolera
            response = arduino.readline().decode('utf-8').strip()
            return jsonify({"status": "ok", "response": response})
            
        # 3. Dla pozostałych komend wykonawczych (światło, woda) po prostu zgłaszamy sukces
        return jsonify({"status": "ok", "response": f"Wykonano: {cmd}"})
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
