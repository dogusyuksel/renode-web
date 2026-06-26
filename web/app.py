from flask import Flask, request, jsonify
import os, json, threading, subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
import os, shutil
import time
import subprocess
import signal

app = Flask(__name__, static_folder="static", static_url_path="")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def run_copy(ts, test_duration, verbose_log):
    try:
        if os.path.exists(f"/workspace/{ts}"):
            shutil.rmtree(f"/workspace/{ts}")

        for f in os.listdir(f"/workspace/web/{ts}"):
            if f.endswith(".elf"):
                os.replace(f"/workspace/web/{ts}/{f}", f"/workspace/web/{ts}/firmware.elf")
                break

        if os.path.exists(f"/workspace/web/{ts}"):
            shutil.copytree(f"/workspace/web/{ts}", f"/workspace/{ts}")

        verbose_flag = "log_enable" if verbose_log else "log_disable"
        subprocess.call(f"cd /workspace && python3 auto_resc_generator.py {verbose_flag} &", shell=True)
        surec1 = subprocess.Popen(
            "cd /workspace && renode uploads/example.resc",
            shell=True,
            start_new_session=True
        )
        time.sleep(15)
        # run custom test here
        if os.path.exists(f"/workspace/{ts}/custom_test.py"):
            subprocess.call(f"cd /workspace/{ts} && python3 custom_test.py > /workspace/{ts}/custom_test_report.txt", shell=True)

        time.sleep(int(int(test_duration) - 15))
        try:
            os.killpg(os.getpgid(surec1.pid), signal.SIGKILL)
        except Exception as e:
            print(f"{e}")

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

        test_config = {
            "test_duration": int(request.form.get("testDuration", 30)),
            "verbose_log": request.form.get("verboseLog") == "true"
        }

        custom_script = request.form.get("customScript")
        if custom_script:
            with open(os.path.join(session_dir,"custom_test.py"),"w") as f:
                f.write(custom_script)

        elf = request.files.get("elf")
        if elf:
            filename = secure_filename(elf.filename)
            elf.save(os.path.join(session_dir, filename))

        threading.Thread(
            target=run_copy,
            args=(session_dir, test_config["test_duration"], test_config["verbose_log"]),
            daemon=True
        ).start()

        return jsonify({
            "status":"ok",
            "folder":session_dir,
            "test_duration": test_config["test_duration"],
            "verbose_log": test_config["verbose_log"],
            "custom_script_uploaded": custom_script is not None
        })

    except Exception as e:
        return jsonify({"error":str(e)}),500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
