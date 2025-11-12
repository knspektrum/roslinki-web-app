from flask import Flask, send_file, jsonify
from pathlib import Path
import subprocess
from datetime import datetime
import tempfile

app = Flask(__name__)


def take_photo():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = Path(tempfile.gettempdir())
    filename = tmp_dir / f"photo_{timestamp}.jpg"

    cmd = ["rpicam-still", "-o", filename, "-n"]
    subprocess.run(cmd, check=True)
    return filename


@app.route("/capture", methods=["POST"])
def capture():
    try:
        filename = take_photo()
        return send_file(filename, mimetype="image/jpeg")
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "error": f"Capture failed: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 501


@app.route("/bump", methods=["POST"])
def bump():
    return "Bump", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
