import io
import os
import subprocess
from pathlib import Path

import time
import serial
import tempfile
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_file


SERVICE_VERSION = "0.1.1"
DEFAULT_PORT = "/dev/ttyUSB0"
BAUDRATE = 9600

app = Flask(__name__)
serial_lock = threading.Lock()
arduino = None


def get_arduino_connection() -> None | serial.Serial:
    """Tries to connect or re-connect to the Arduino if disconnected."""
    global arduino
    with serial_lock:
        if arduino:
            if arduino.is_open and arduino.port and os.path.exists(arduino.port):
                return arduino
            try:
                arduino.close()
            except Exception:
                pass
            arduino = None

        candidate_ports = [DEFAULT_PORT, "/dev/ttyACM0", "/dev/ttyUSB1"]
        for port in candidate_ports:
            if not os.path.exists(port):
                continue
            try:
                arduino = serial.Serial(port, BAUDRATE, timeout=2)
                time.sleep(2)
                print(f"[INFO] Connected to Arduino on {port}") #!---- Zmiana na logger ----
                return arduino
            
            except Exception:
                continue
        arduino = None
        return None
    
    
def take_photo() -> Path:
    dev = get_arduino_connection()
    with serial_lock:
        if dev and dev.is_open:
            try:
                dev.reset_input_buffer()
                dev.reset_output_buffer()
                dev.write(b'C')
                dev.flush()
                time.sleep(0.5)
                
            except Exception as e:
                print(f"[ERROR] Failed to turn on camera LEDs: {e}") #!---- Zmiana na logger ----
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = Path(tempfile.gettempdir())
    filename = tmp_dir / f"photo_{timestamp}.jpg"
    cam_tool = "rpicam-still" if subprocess.run(["which", "rpicam-still"], capture_output=True).returncode == 0 else "libcamera-still"
    cmd = [cam_tool, "--width", "4056", "--height", "3040", "-o", str(filename), "-n"]
    
    try:
        subprocess.run(cmd, check=True)
    finally:
        with serial_lock:
            if dev and dev.is_open:
                try:
                    dev.write(b'X')
                    dev.flush()
                    
                except Exception as e:
                    print(f"[ERROR] Failed to restore normal lights: {e}")
    return filename


@app.route("/health", methods=["GET"])
def health():
    dev = get_arduino_connection()
    return jsonify({
        "status": "ok",
        "version": SERVICE_VERSION,
        "arduino_connected": bool(dev and dev.is_open),
        "port": dev.port if (dev and dev.is_open) else None,
    }), 200
    
    
@app.route("/capture", methods=["POST"])
def capture():
    try:
        filename = take_photo()
        with open(filename, "rb") as f:
            bufor_zdjecia = io.BytesIO(f.read())
        os.remove(filename)
        return send_file(bufor_zdjecia, mimetype="image/jpeg")
    
    except subprocess.CalledProcessError as e:
        return jsonify(
            {"status": "error", "error": f"Camera capture failed: {e}"}
        ), 500
    except Exception as e:
        return jsonify(
            {"status": "error", "error": str(e)}
        ), 500
    
    
@app.route("/bump", methods=["POST"])
def bump():
    return "Bump", 200


@app.route("/arduino", methods=["POST"])
def arduino_command():
    dev = get_arduino_connection()
    if not dev or not dev.is_open:
        return jsonify(
            {"status": "error", "error": "No physical connection to Arduino"}
        ), 500
    
    data = request.get_json() or {}
    cmd = data.get("cmd", "")
    with serial_lock:
        try:
            dev.reset_input_buffer()
            dev.reset_output_buffer()
            dev.write(cmd.encode("utf-8"))
            dev.flush()
            
            if cmd in ["R", "B"]: #---- "R" - Read ;"B" - Bump ----
                response = dev.readline().decode("utf-8").strip()
                return jsonify({"status": "ok", "response": response})
            return jsonify(
                {"status": "ok", "response": f"Executed: {cmd}"}
            )
            
        except Exception as e:
            global arduino
            if arduino:
                try:
                    arduino.close()
                except Exception:
                    pass
                arduino = None
            return jsonify(
                {"status": "error", "error": str(e)}
            ), 500

        
if __name__ == "__main__":
    get_arduino_connection()
    app.run(host="0.0.0.0", port=5003)