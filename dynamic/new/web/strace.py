import threading
import psutil
import time
import subprocess
import os
import re

def get_pid():
    command = "ps aux | grep code | grep -v grep | sort -h | head -n 1"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output_lines = result.stdout.strip().split('\n')[0]
    output_lines = output_lines.strip().split()
    run = True
    while run:
        try:
            pid = int(output_lines[0])
            run = False
        except:
            output_lines.pop(0)
    return pid

def get_child_processes(pid):
    try:
        parent = psutil.Process(pid)
        return parent.children(recursive=True)  # Получаем всех дочерних процессов
    except psutil.NoSuchProcess:
        return []

def monitor_strace_log(pid):
    with open('process_info.log', 'a') as log_file:
        while True:
            time.sleep(1)  # Проверяем файл каждую секунду
            if os.path.exists('/tmp/file_log'):
                with open('/tmp/file_log', 'r') as strace_log:
                    lines = strace_log.readlines()
                    for line in lines:
                        log_file.write(line)
                        log_file.flush()

                        #print(line)
                        if "read" in line:
                            match = int(line.split("(")[1].split(",")[0])
                            fd = match
                            child_fd_path = f"/proc/{pid}/fd/{fd}"
                            try:
                                child_fd_link = os.readlink(child_fd_path)
                                if '/' in child_fd_link:
                                    log_file.write('r' + child_fd_link)
                            except FileNotFoundError:
                                continue
                            log_file.flush()

                        elif "write" in line:
                            match = int(line.split("(")[1].split(",")[0])
                            fd = match
                            child_fd_path = f"/proc/{pid}/fd/{fd}"
                            try:
                                child_fd_link = os.readlink(child_fd_path)
                                if '/' in child_fd_link:
                                    log_file.write('w' + child_fd_link)
                            except:
                                print("Something went wrong")
                            log_file.flush()
    

                        # Проверяем дочерние процессы
                        child_processes = get_child_processes(pid)
                        for child in child_processes:
                            child_fd_info = f"/proc/{child.pid}/fd"
                            if os.path.exists(child_fd_info):
                                for child_fd in os.listdir(child_fd_info):
                                    child_fd_path = os.path.join(child_fd_info, child_fd)
                                    try:
                                        child_fd_link = os.readlink(child_fd_path)
                                        if '/' in child_fd_link:
                                            log_file.write(f"{child.pid}: {child_fd_link}\n")
                                    except:
                                        continue
                                log_file.flush()

if __name__ == "__main__":
    try:
        pid = get_pid()
        print(f"PID получен, начинаю логирование процесса {pid}")
        monitor_strace_log(pid)
    except ValueError:
        print("Пожалуйста, введите корректный числовой PID.")