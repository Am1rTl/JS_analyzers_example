import os
import subprocess
import pwd
import shutil
import json

def load_config(config_path="config.json"):
    """Загружает конфигурацию из JSON-файла."""
    try:
        with open(config_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("[ERROR] Файл конфигурации не найден!")
        return {}

def create_sandbox_user(username="vscode_sandbox"):
    """Создает нового пользователя для изолированного запуска VSCode."""
    try:
        pwd.getpwnam(username)
        print(f"[INFO] Пользователь {username} уже существует.")
    except KeyError:
        print(f"[INFO] Создаю пользователя {username}...")
        subprocess.run(["sudo", "useradd", "-m", "-s", "/bin/bash", username], check=True)

def apply_network_restrictions(username, enable):
    """Настраивает iptables для блокировки или разрешения сети."""
    if not enable:
        print("[INFO] Блокирую сетевые соединения...")
        subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", username, "-j", "DROP"], check=True)

def apply_file_restrictions(username, enable):
    """Настраивает ACL для ограничения доступа к файлам."""
    if not enable:
        print("[INFO] Ограничиваю доступ к файлам...")
        home_dir = f"/home/{username}"
        subprocess.run(["sudo", "setfacl", "-m", "u:{}:r--".format(username), home_dir], check=True)

def apply_cgroup_restrictions(username, max_processes):
    """Настраивает cgroup для ограничения количества процессов."""
    print(f"[INFO] Ограничиваю число процессов до {max_processes}...")
    cgroup_path = f"/sys/fs/cgroup/pids/{username}"
    subprocess.run(["sudo", "mkdir", "-p", cgroup_path], check=True)
    subprocess.run(["sudo", "bash", "-c", f"echo {max_processes} > {cgroup_path}/pids.max"], check=True)
    subprocess.run(["sudo", "bash", "-c", f"echo $(id -u {username}) > {cgroup_path}/cgroup.procs"], check=True)

def launch_vscode(username):
    """Запускает VSCode под новым пользователем."""
    print("[INFO] Запускаю VSCode...")
    subprocess.run(["sudo", "-u", username, "code"], check=True)

if __name__ == "__main__":
    SANDBOX_USER = "vscode_sandbox"
    config = load_config()
    
    create_sandbox_user(SANDBOX_USER)
    apply_network_restrictions(SANDBOX_USER, config.get("network", True))
    apply_file_restrictions(SANDBOX_USER, config.get("file_access", True))
    apply_cgroup_restrictions(SANDBOX_USER, config.get("max_processes", 10))
    launch_vscode(SANDBOX_USER)
