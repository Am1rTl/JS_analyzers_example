import os
import json
import subprocess
from flask import Flask, request, jsonify

# Загружаем конфигурацию
CONFIG_PATH = "config.json"
LOG_PATH = "log.json"
CGROUP_NAME = "vscode_sandbox"

if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "w") as f:
        json.dump({}, f)

if not os.path.exists(LOG_PATH):
    with open(LOG_PATH, "w") as f:
        json.dump([], f)

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)

def log_event(event_type, data):
    log_entry = {"type": event_type, "data": data}
    try:
        with open(LOG_PATH, "a") as log_file:
            json.dump(log_entry, log_file)
            log_file.write("\n")
    except Exception as e:
        print(f"Error writing log: {e}")

def setup_acl(file_path, permission, user="nobody"):
    try:
        subprocess.run(["setfacl", "-m", f"u:{user}:{permission}", file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error setting ACL: {e}")

def setup_iptables():
    try:
        subprocess.run(["iptables", "-A", "OUTPUT", "-j", "LOG", "--log-prefix", "[NET_LOG]"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error setting iptables rule: {e}")

def setup_cgroups():
    try:
        cgroup_path = f"/sys/fs/cgroup/{CGROUP_NAME}"
        os.makedirs(cgroup_path, exist_ok=True)
        with open(f"{cgroup_path}/cgroup.procs", "w") as f:
            f.write(str(os.getpid()))
    except Exception as e:
        print(f"Error setting up cgroups: {e}")

def monitor_processes():
    try:
        processes = subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout
        log_event("process", processes)
    except Exception as e:
        print(f"Error monitoring processes: {e}")

def launch_vscode_in_sandbox():
    try:
        vscode_path = subprocess.run(["which", "code"], capture_output=True, text=True).stdout.strip()
        if not vscode_path:
            print("VSCode not found!")
            return
        cgroup_path = f"/sys/fs/cgroup/{CGROUP_NAME}/cgroup.procs"
        process = subprocess.Popen([vscode_path], preexec_fn=lambda: open(cgroup_path, "w").write(str(os.getpid())))
        print("Run vscode")
        log_event("vscode_launch", f"Launched VSCode in {CGROUP_NAME}")
    except Exception as e:
        print(f"Error launching VSCode in sandbox: {e}")

# Flask UI
app = Flask(__name__)

@app.route("/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        new_config = request.json
        save_config(new_config)
        return jsonify({"status": "success"})
    return jsonify(load_config())

@app.route("/logs", methods=["GET"])
def logs():
    try:
        with open(LOG_PATH, "r") as log_file:
            return "<pre>" + log_file.read() + "</pre>"
    except FileNotFoundError:
        return jsonify({"error": "Log file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    setup_iptables()
    #setup_cgroups()
    launch_vscode_in_sandbox()
    app.run(debug=True)
