from flask import Flask, request, jsonify
import os
import json
import subprocess
import threading
from datetime import datetime

app = Flask(__name__, static_folder="static", static_url_path="")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def copy(ts):
    try:
        full_cmd = f"./copy.sh {ts}"
        subprocess.check_call(full_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        return f"<pre>Yuklemede hata oluştu:\n{e}</pre>"

@app.route("/")
def index():
    # index.html dosyasını serve et
    return app.send_static_file("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        # JSON verisini al
        data = request.form.get("data")
        if not data:
            return jsonify({"error": "No data"}), 400

        parsed = json.loads(data)
        mcu = parsed.get("mcu", "unknown_mcu")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ELF dosyası varsa kaydet
        elf_file = request.files.get("elf")
        elf_name = None
        if elf_file:
            elf_name = "firmware.elf"
            elf_path = os.path.join(UPLOAD_DIR, elf_name)
            elf_file.save(elf_path)

        # JSON dosyasını kaydet
        json_name = "structure.json"
        json_path = os.path.join(UPLOAD_DIR, json_name)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)

        threading.Thread(target=copy, args=(ts,)).start()

        return jsonify({
            "message": "Upload successful",
            "json_file": json_name,
            "elf_file": elf_name,
            "time": ts
        }), 200

    except Exception as e:
        print("Upload error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
