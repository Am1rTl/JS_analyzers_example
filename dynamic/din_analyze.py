import psutil
import time
import signal
import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from threading import Thread

class VSCodeProcessMonitor:
    def __init__(self, extension_id: str, rules_file: str = "security_rules.json"):
        self.extension_id = extension_id
        self.rules_file = Path(rules_file)
        self.suspicious_processes: Set[int] = set()
        self.is_monitoring = False
        self.logger = self._setup_logger()
        self.rules = self._load_security_rules()
        
    def _setup_logger(self) -> logging.Logger:
        """Настройка логирования."""
        logger = logging.getLogger(f"VSCodeMonitor_{self.extension_id}")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("vscode_monitor.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def _load_security_rules(self) -> Dict:
        """Загрузка правил безопасности из JSON файла."""
        default_rules = {
            "blocked_executables": [
                "cmd.exe", "powershell.exe", "bash.exe", "python.exe",
                "node.exe", "npm.exe"
            ],
            "blocked_network_ports": [
                80, 443, 8080, 22
            ],
            "max_memory_usage_mb": 500,
            "max_cpu_percent": 50,
            "suspicious_file_patterns": [
                r"C:\\Windows\\System32",
                r"/etc/",
                r"/usr/bin",
                r"registry.exe"
            ],
            "blocked_network_hosts": [
                "raw.githubusercontent.com",
                "pastebin.com",
                "ngrok.io"
            ]
        }

        if self.rules_file.exists():
            try:
                with open(self.rules_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки правил: {e}")
                return default_rules
        return default_rules

    def _is_suspicious_process(self, proc: psutil.Process) -> bool:
        """Проверка процесса на подозрительную активность."""
        try:
            # Проверка имени исполняемого файла
            if proc.name().lower() in self.rules["blocked_executables"]:
                self.logger.warning(f"Обнаружен заблокированный процесс: {proc.name()}")
                return True

            # Проверка использования памяти
            memory_usage_mb = proc.memory_info().rss / 1024 / 1024
            if memory_usage_mb > self.rules["max_memory_usage_mb"]:
                self.logger.warning(f"Превышение использования памяти: {memory_usage_mb}MB")
                return True

            # Проверка использования CPU
            if proc.cpu_percent() > self.rules["max_cpu_percent"]:
                self.logger.warning(f"Превышение использования CPU: {proc.cpu_percent()}%")
                return True

            # Проверка открытых файлов
            for file in proc.open_files():
                if any(pattern in file.path for pattern in self.rules["suspicious_file_patterns"]):
                    self.logger.warning(f"Подозрительный доступ к файлу: {file.path}")
                    return True

            # Проверка сетевых соединений
            for conn in proc.connections():
                if conn.status == 'ESTABLISHED':
                    if conn.laddr.port in self.rules["blocked_network_ports"]:
                        self.logger.warning(f"Заблокированное сетевое соединение: port {conn.laddr.port}")
                        return True

            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            return False

    def _block_process(self, pid: int):
        """Блокировка подозрительного процесса."""
        try:
            process = psutil.Process(pid)
            self.logger.warning(f"Блокировка процесса {pid} ({process.name()})")
            
            # Сначала пробуем мягкое завершение
            process.terminate()
            
            # Даем процессу 3 секунды на завершение
            time.sleep(3)
            
            # Если процесс все еще жив, убиваем его
            if process.is_running():
                process.kill()
                
            self.suspicious_processes.add(pid)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.error(f"Ошибка при блокировке процесса {pid}: {e}")

    def _monitor_process_tree(self, parent_pid: int):
        """Рекурсивный мониторинг дерева процессов."""
        try:
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)
            
            # Проверяем родительский процесс
            if self._is_suspicious_process(parent):
                self._block_process(parent_pid)
                return
                
            # Проверяем дочерние процессы
            for child in children:
                if child.pid not in self.suspicious_processes:
                    if self._is_suspicious_process(child):
                        self._block_process(child.pid)
                        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def find_extension_process(self) -> Optional[psutil.Process]:
        """Поиск процесса расширения VSCode."""
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if self.extension_id in str(proc.cmdline()):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None

    def start_monitoring(self):
        """Запуск мониторинга процессов."""
        self.is_monitoring = True
        self.logger.info("Запуск мониторинга процессов")
        
        def monitoring_loop():
            while self.is_monitoring:
                extension_process = self.find_extension_process()
                if extension_process:
                    self._monitor_process_tree(extension_process.pid)
                time.sleep(1)  # Проверка каждую секунду
                
        # Запуск мониторинга в отдельном потоке
        monitor_thread = Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()

    def stop_monitoring(self):
        """Остановка мониторинга процессов."""
        self.is_monitoring = False
        self.logger.info("Остановка мониторинга процессов")
