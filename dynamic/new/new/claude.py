#!/usr/bin/env python3
"""
Программа для поиска, завершения и перезапуска процессов расширений VSCode 
от имени пользователя vscode_sandbox в системе Linux.
"""

import os
import sys
import signal
import subprocess
import time
import logging
import pwd
import grp
import argparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/vscode_extension_manager.log')
    ]
)
logger = logging.getLogger(__name__)

def check_root_privileges():
    """Проверяет наличие прав root."""
    if os.geteuid() != 0:
        logger.error("Для выполнения этой программы требуются права root")
        sys.exit(1)

def find_vscode_extension_processes():
    """Находит все процессы расширений VSCode в системе."""
    try:
        cmd = "ps -eo pid,user,command | grep 'vscode.*extension' | grep -v grep"
        result = subprocess.check_output(cmd, shell=True, text=True)
        
        processes = []
        for line in result.strip().split('\n'):
            if not line:
                continue
                
            parts = line.strip().split(None, 2)
            if len(parts) >= 3:
                pid = int(parts[0])
                user = parts[1]
                command = parts[2]
                processes.append({
                    'pid': pid,
                    'user': user,
                    'command': command
                })
        
        return processes
    except subprocess.CalledProcessError:
        # Если команда не вернула результат (нет процессов)
        return []
    except Exception as e:
        logger.error(f"Ошибка при поиске процессов: {e}")
        return []

def get_process_environment(pid):
    """Получает переменные окружения процесса."""
    try:
        env_path = f"/proc/{pid}/environ"
        if not os.path.exists(env_path):
            logger.warning(f"Файл {env_path} не существует")
            return {}
            
        with open(env_path, 'rb') as f:
            env_data = f.read().split(b'\0')
        
        env = {}
        for item in env_data:
            if item:
                try:
                    key, value = item.decode('utf-8', errors='ignore').split('=', 1)
                    env[key] = value
                except ValueError:
                    pass
        
        return env
    except Exception as e:
        logger.error(f"Ошибка при получении переменных окружения для PID {pid}: {e}")
        return {}

def get_process_cwd(pid):
    """Получает рабочую директорию процесса."""
    try:
        cwd_path = f"/proc/{pid}/cwd"
        if os.path.exists(cwd_path):
            return os.readlink(cwd_path)
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении рабочей директории для PID {pid}: {e}")
        return None

def get_process_cmdline(pid):
    """Получает полную командную строку процесса."""
    try:
        cmdline_path = f"/proc/{pid}/cmdline"
        if not os.path.exists(cmdline_path):
            logger.warning(f"Файл {cmdline_path} не существует")
            return None
            
        with open(cmdline_path, 'rb') as f:
            cmdline = f.read().split(b'\0')
        
        # Убираем пустой элемент в конце
        if cmdline and not cmdline[-1]:
            cmdline = cmdline[:-1]
            
        return [arg.decode('utf-8', errors='ignore') for arg in cmdline]
    except Exception as e:
        logger.error(f"Ошибка при получении командной строки для PID {pid}: {e}")
        return None

def kill_process(pid):
    """Корректно завершает процесс."""
    try:
        # Сначала отправляем SIGTERM
        os.kill(pid, signal.SIGTERM)
        logger.info(f"Отправлен сигнал SIGTERM процессу {pid}")
        
        # Даем время на завершение
        for _ in range(5):  # 5 попыток с интервалом 0.5 сек
            time.sleep(0.5)
            try:
                # Проверяем, существует ли ещё процесс
                os.kill(pid, 0)
            except OSError:
                # Процесс уже завершен
                logger.info(f"Процесс {pid} успешно завершен")
                return True
        
        # Если процесс до сих пор существует, отправляем SIGKILL
        logger.warning(f"Процесс {pid} не ответил на SIGTERM, отправляем SIGKILL")
        os.kill(pid, signal.SIGKILL)
        time.sleep(0.5)
        
        # Проверяем, что процесс точно завершен
        try:
            os.kill(pid, 0)
            logger.error(f"Не удалось завершить процесс {pid}")
            return False
        except OSError:
            logger.info(f"Процесс {pid} успешно завершен после SIGKILL")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка при завершении процесса {pid}: {e}")
        return False

def check_user_exists(username):
    """Проверяет существование пользователя в системе."""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def restart_process_as_user(cmdline, env, cwd, username):
    """Перезапускает процесс от имени указанного пользователя."""
    if not check_user_exists(username):
        logger.error(f"Пользователь {username} не существует в системе")
        return False
    
    try:
        # Создаем строку команды
        cmd_str = ' '.join(f'"{arg}"' for arg in cmdline)
        
        # Строка с переменными окружения
        env_str = ' '.join(f'{k}="{v}"' for k, v in env.items())
        
        # Полная команда для sudo
        full_cmd = f"sudo -u {username} bash -c 'cd {cwd} && {env_str} {cmd_str}'"
        
        # Запускаем процесс в фоновом режиме
        subprocess.Popen(full_cmd, shell=True, 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         start_new_session=True)
        
        logger.info(f"Процесс перезапущен от имени пользователя {username}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при перезапуске процесса: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Управление процессами расширений VSCode')
    parser.add_argument('--user', default='vscode_sandbox', 
                        help='Имя пользователя для перезапуска процессов')
    parser.add_argument('--skip-kill', action='store_true', 
                        help='Не завершать существующие процессы')
    args = parser.parse_args()
    
    # Проверка прав root
    check_root_privileges()
    
    target_user = args.user
    logger.info(f"Целевой пользователь для перезапуска: {target_user}")
    
    # Находим процессы расширений VSCode
    processes = find_vscode_extension_processes()
    
    if not processes:
        logger.info("Процессы расширений VSCode не найдены")
        return
    
    logger.info(f"Найдено {len(processes)} процессов расширений VSCode")
    
    success_count = 0
    for proc in processes:
        pid = proc['pid']
        user = proc['user']
        cmd = proc['command']
        
        logger.info(f"Обрабатываю процесс {pid} от пользователя {user}: {cmd}")
        
        # Получаем информацию о процессе
        cmdline = get_process_cmdline(pid)
        env = get_process_environment(pid)
        cwd = get_process_cwd(pid)
        
        if not all([cmdline, cwd]):
            logger.warning(f"Не удалось получить всю необходимую информацию для процесса {pid}")
            continue
        
        # Пропускаем процессы, которые уже запущены от нужного пользователя
        if user == target_user:
            logger.info(f"Процесс {pid} уже запущен от пользователя {target_user}, пропускаем")
            continue
        
        # Завершаем процесс
        if not args.skip_kill:
            if not kill_process(pid):
                logger.warning(f"Не удалось корректно завершить процесс {pid}, пропускаем его перезапуск")
                continue
        
        # Перезапускаем процесс от имени target_user
        if restart_process_as_user(cmdline, env, cwd, target_user):
            success_count += 1
    
    logger.info(f"Успешно перезапущено {success_count} из {len(processes)} процессов")

if __name__ == "__main__":
    main()
