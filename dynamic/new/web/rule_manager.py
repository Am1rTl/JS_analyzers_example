import json
import subprocess
from typing import Dict, List, Optional

class RuleManager:
    def __init__(self):
        self.rules_file = "rules"
        self.current_rules = self.load_rules()

    def load_rules(self) -> Dict:
        try:
            with open(self.rules_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _clear_iptables_rules(self):
        """Очищает все правила iptables"""
        subprocess.run(['iptables', '-F'])  # Очистить все цепочки
        subprocess.run(['iptables', '-X'])  # Удалить пользовательские цепочки
        subprocess.run(['iptables', '-P', 'INPUT', 'ACCEPT'])  # Установить политику по умолчанию
        subprocess.run(['iptables', '-P', 'OUTPUT', 'ACCEPT'])
        subprocess.run(['iptables', '-P', 'FORWARD', 'ACCEPT'])

    def apply_network_rules(self, rules: Dict):
        """Применяет правила сетевой активности"""
        # Сначала очищаем все существующие правила
        self._clear_iptables_rules()
        
        action = rules.get('networkAction')
        if action == 'blockAll':
            # Блокировать весь трафик
            subprocess.run(['iptables', '-P', 'OUTPUT', 'DROP'])
        elif action == 'allowAll':
            # Разрешить весь трафик
            subprocess.run(['iptables', '-P', 'OUTPUT', 'ACCEPT'])
        
        # Применить правила для подстрок
        substring_rules = rules.get('substringRules', [])
        for rule in substring_rules:
            action = 'DROP' if rule.get('action') == 'block' else 'ACCEPT'
            pattern = rule.get('pattern')
            if pattern:
                # Используем string match для проверки подстроки в пакетах
                subprocess.run([
                    'iptables', '-A', 'OUTPUT',
                    '-m', 'string', '--string', pattern,
                    '--algo', 'bm',  # Boyer-Moore алгоритм
                    '-j', action
                ])

        # Применить правила для портов
        port_rules = rules.get('portRules', [])
        for rule in port_rules:
            action = 'DROP' if rule.get('action') == 'block' else 'ACCEPT'
            port = rule.get('port')
            if port:
                # Правило для исходящего трафика на указанный порт
                subprocess.run([
                    'iptables', '-A', 'OUTPUT',
                    '-p', 'tcp', '--dport', str(port),
                    '-j', action
                ])
                subprocess.run([
                    'iptables', '-A', 'OUTPUT',
                    '-p', 'udp', '--dport', str(port),
                    '-j', action
                ])

        # Применить правила для IP-адресов
        ip_rules = rules.get('ipRules', [])
        for rule in ip_rules:
            action = 'DROP' if rule.get('action') == 'block' else 'ACCEPT'
            ip = rule.get('ip')
            if ip:
                # Правило для конкретного IP-адреса
                subprocess.run([
                    'iptables', '-A', 'OUTPUT',
                    '-d', ip,
                    '-j', action
                ])

    def apply_file_rules(self, rules: Dict):
        """Применяет правила для файловых операций"""
        read_action = rules.get('readAction')
        write_action = rules.get('writeAction')
        
        # Применить правила чтения
        if read_action == 'blockAll':
            # Использовать AppArmor или SELinux для ограничения доступа
            pass
        
        # Применить правила записи
        if write_action == 'blockAll':
            # Использовать AppArmor или SELinux для ограничения доступа
            pass

    def apply_resource_rules(self, rules: Dict):
        """Применяет правила использования ресурсов"""
        resource_action = rules.get('resourceAction')
        if resource_action == 'limit':
            # Установить ограничения на CPU и память
            subprocess.run(['ulimit', '-u', '50'])  # ограничить количество процессов
            subprocess.run(['ulimit', '-m', '1000000'])  # ограничить использование памяти

    def apply_rules(self):
        """Применяет все правила из конфигурации"""
        rules = self.load_rules()
        self.apply_network_rules(rules)
        self.apply_file_rules(rules)
        self.apply_resource_rules(rules)
