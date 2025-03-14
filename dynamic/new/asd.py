#!/usr/bin/env python3
"""
Скрипт для перезапуска процессов расширений VSCode от пользователя vscode_sandbox в Linux.
"""

import os
import sys
import signal
import subprocess
import argparse
import pwd
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/vscode_restart.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_user_id(username):
    """Получение ID пользователя по имени."""
    try:
        return pwd.getpwnam(username).pw_uid
    except KeyError:
        logger.error(f"Пользователь {username} не найден")
        return None

def find_vscode_extension_processes(username):
    """Находит процессы расширений VSCode, запущенные указанным пользователем."""
    try:
        # Выполняем команду ps для поиска процессов VSCode extension
        cmd = f"ps -u {username} -o pid,command | grep 'vscode.*extension' | grep -v grep"
        result = subprocess.check_output(cmd, shell=True, text=True)
        processes = []
        
        for line in result.strip().split('\n'):
            if line:
                parts = line.strip().split(None, 1)
                if len(parts) >= 1:
                    pid = int(parts[0])
                    command = parts[1] if len(parts) > 1 else ""
                    processes.append((pid, command))
        
        return processes
    except subprocess.CalledProcessError:
        # Если команда не вернула результат (нет процессов)
        return []
    except Exception as e:
        logger.error(f"Ошибка при поиске процессов: {e}")
        return []

def restart_process(pid, command, username):
    """Перезапускает процесс с тем же командным аргументом."""
    try:
        # Получаем полную командную строку процесса
        cmd_path = f"/proc/{pid}/cmdline"
        if not os.path.exists(cmd_path):
            logger.warning(f"Путь {cmd_path} не существует, процесс мог завершиться")
            return False
        
        with open(cmd_path, 'rb') as f:
            cmdline = f.read().replace(b'\x00', b' ').decode('utf-8', errors='ignore')
        
        # Завершаем процесс
        os.kill(pid, signal.SIGTERM)
        logger.info(f"Отправлен сигнал SIGTERM процессу {pid}")
        
        # Даем процессу время на завершение
        import time
        time.sleep(2)
        
        # Проверяем, завершился ли процесс
        try:
            os.kill(pid, 0)
            logger.warning(f"Процесс {pid} не завершился, отправляем SIGKILL")
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        except OSError:
            # Процесс уже завершен
            pass
        
        # Перезапускаем процесс от имени пользователя
        restart_cmd = f"sudo -u {username} {cmdline}"
        logger.info(f"Перезапуск процесса: {restart_cmd}")
        subprocess.Popen(restart_cmd, shell=True)
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при перезапуске процесса {pid}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Перезапуск процессов расширений VSCode')
    parser.add_argument('--user', default='vscode_sandbox', help='Имя пользователя')
    args = parser.parse_args()
    
    # Проверка привилегий root
    if os.geteuid() != 0:
        logger.error("Этот скрипт должен быть запущен с правами root")
        sys.exit(1)
    
    username = args.user
    user_id = get_user_id(username)
    
    if user_id is None:
        sys.exit(1)
    
    logger.info(f"Поиск процессов расширений VSCode от пользователя {username}")
    processes = find_vscode_extension_processes(username)
    
    if not processes:
        logger.info(f"Процессы расширений VSCode от пользователя {username} не найдены")
        sys.exit(0)
    
    logger.info(f"Найдено {len(processes)} процессов")
    
    restart_count = 0
    for pid, command in processes:
        logger.info(f"Перезапуск процесса {pid}: {command}")
        if restart_process(pid, command, username):
            restart_count += 1
    
    logger.info(f"Перезапущено {restart_count} из {len(processes)} процессов")

if __name__ == "__main__":
    main()
