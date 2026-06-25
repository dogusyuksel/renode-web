from flask import Flask, request, jsonify
import os, json, threading, subprocess
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="static", static_url_path="")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def run_copy(ts):
    try:
        subprocess.call(f"rm -rf /workspace/{ts} && cp -rf /workspace/web/{ts} /workspace/{ts}", shell=True)
        subprocess.call(f"cd /workspace && python3 auto_resc_generator.py && cd -", shell=True)
        subprocess.call(f"cd /workspace && timeout 30 renode uploads/example.resc", shell=True)
        subprocess.call(f"cd /workspace && python3 report_creator.py --connections uploads/structure.json --diagram uploads/diagram.png --log uploads/log.txt --out uploads/report.pdf", shell=True)
    except Exception as e:
        print(e)

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    try:
        payload = json.loads(request.form.get("data"))

        session_dir = UPLOAD_DIR
        os.makedirs(session_dir, exist_ok=True)

        with open(os.path.join(session_dir,"structure.json"),"w") as f:
            json.dump(payload,f,indent=2)

        elf = request.files.get("elf")
        if elf:
            filename = secure_filename(elf.filename)
            elf.save(os.path.join(session_dir, filename))

        threading.Thread(target=run_copy,args=(session_dir,),daemon=True).start()

        return jsonify({
            "status":"ok",
            "folder":session_dir
        })

    except Exception as e:
        return jsonify({"error":str(e)}),500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
