from flask import Flask, request, jsonify
import os, json, threading, subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
import os, shutil
import time
import subprocess
import signal

calmdown_wait = 15

app = Flask(__name__, static_folder="static", static_url_path="")

UPLOAD_DIR = "uploads"
UPLOAD_PATH = f"/workspace/{UPLOAD_DIR}"
UPLOAD_WEB_PATH = f"/workspace/web/{UPLOAD_DIR}"
SCRIPTS_PATH = "/workspace/scripts"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def run_scripts(test_duration, verbose_log):
    try:
        if os.path.exists(f"{UPLOAD_PATH}"):
            shutil.rmtree(f"{UPLOAD_PATH}")

        for f in os.listdir(f"{UPLOAD_WEB_PATH}"):
            if f.endswith(".elf"):
                os.replace(
                    f"{UPLOAD_WEB_PATH}/{f}", f"{UPLOAD_WEB_PATH}/firmware.elf"
                )
                break

        if os.path.exists(f"{UPLOAD_WEB_PATH}"):
            shutil.copytree(f"{UPLOAD_WEB_PATH}", f"{UPLOAD_PATH}")

        verbose_flag = "log_enable" if verbose_log else "log_disable"
        subprocess.call(
            f"cd {SCRIPTS_PATH} && python3 auto_resc_generator.py {verbose_flag}",
            shell=True,
        )

        test_duration_int = int(test_duration)

        surec1 = subprocess.Popen(
            f"cd /workspace && renode {UPLOAD_PATH}/example.resc",
            shell=True,
            start_new_session=True,
        )
        time.sleep(calmdown_wait)
        # run custom test here
        if os.path.exists(f"{UPLOAD_PATH}/custom_test.py"):
            surec2 = subprocess.Popen(
                f"cd {UPLOAD_PATH} && python3 -u custom_test.py > {UPLOAD_PATH}/custom_test_report.txt",
                shell=True,
                start_new_session=True,
            )

        time.sleep(int(test_duration_int - calmdown_wait))
        try:
            os.killpg(os.getpgid(surec2.pid), signal.SIGKILL)
            os.killpg(os.getpgid(surec1.pid), signal.SIGKILL)
        except Exception as e:
            print(f"{e}")

        subprocess.call(
            f"cd {SCRIPTS_PATH} && python3 report_creator.py --connections {UPLOAD_PATH}/structure.json --diagram {UPLOAD_PATH}/diagram.png --log {UPLOAD_PATH}/log.txt --custom {UPLOAD_PATH}/custom_test_report.txt --out {UPLOAD_PATH}/report.pdf",
            shell=True,
        )
    except Exception as e:
        print(e)


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    try:
        payload = json.loads(request.form.get("data"))

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        with open(os.path.join(UPLOAD_DIR, "structure.json"), "w") as f:
            json.dump(payload, f, indent=2)

        test_config = {
            "test_duration": int(request.form.get("testDuration", 30)),
            "verbose_log": request.form.get("verboseLog") == "true",
        }

        custom_script = request.form.get("customScript")
        if custom_script is None:
            custom_script = str('print("No custom command executed!")')

        with open(os.path.join(UPLOAD_DIR, "custom_test.py"), "w") as f:
            f.write(custom_script)

        elf = request.files.get("elf")
        if elf:
            filename = secure_filename(elf.filename)
            elf.save(os.path.join(UPLOAD_DIR, filename))

        threading.Thread(
            target=run_scripts,
            args=(
                test_config["test_duration"],
                test_config["verbose_log"],
            ),
            daemon=True,
        ).start()

        return jsonify(
            {
                "status": "ok",
                "folder": session_dir,
                "test_duration": test_config["test_duration"],
                "verbose_log": test_config["verbose_log"],
                "custom_script_uploaded": custom_script is not None,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
