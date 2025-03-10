import json
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

class VSCodeExtensionAnalyzer:
    def __init__(self, extension_path: str):
        self.extension_path = Path(extension_path)
        self.suspicious_patterns = {
            'shell_execution': [
                r'child_process\.exec',
                r'require\([\'"]child_process[\'"]\)',
                r'spawn\(',
                r'shellExecute',
            ],
            'file_operations': [
                r'fs\.writeFile',
                r'fs\.unlink',
                r'fs\.rmdir',
                r'fs\.mkdir',
            ],
            'network': [
                r'http\.request',
                r'https\.request',
                r'net\.connect',
                r'fetch\(',
            ],
            'eval_execution': [
                r'eval\(',
                r'Function\(',
                r'new Function',
            ]
        }
        
    def scan_file(self, file_path: Path) -> Dict[str, List[int]]:
        """Сканирует файл на наличие подозрительных паттернов."""
        findings = {}
        
        if not file_path.is_file():
            return findings
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        for category, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        if category not in findings:
                            findings[category] = []
                        findings[category].append(i)
                        
        return findings

    def analyze_package_json(self) -> Optional[Dict]:
        """Анализирует package.json на подозрительные зависимости."""
        package_json = self.extension_path / 'package.json'
        if not package_json.is_file():
            return None
            
        with open(package_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        suspicious_deps = []
        all_deps = {
            **data.get('dependencies', {}),
            **data.get('devDependencies', {})
        }
        
        # Список потенциально опасных пакетов
        dangerous_packages = [
            'shell', 'exec', 'spawn', 'child_process', 'eval',
            'crypto', 'puppeteer', 'selenium'
        ]
        
        for dep in all_deps:
            if any(bad in dep.lower() for bad in dangerous_packages):
                suspicious_deps.append(dep)
                
        return {
            'suspicious_dependencies': suspicious_deps,
            'total_dependencies': len(all_deps)
        }

    def analyze(self) -> Dict:
        """Выполняет полный анализ расширения."""
        results = {
            'extension_path': str(self.extension_path),
            'findings': {},
            'package_analysis': None,
            'total_files_scanned': 0
        }
        
        # Анализ package.json
        results['package_analysis'] = self.analyze_package_json()
        
        # Сканирование всех JS/TS файлов
        for ext in ['.js', '.ts']:
            for file_path in self.extension_path.rglob(f'*{ext}'):
                if 'node_modules' not in str(file_path):
                    file_findings = self.scan_file(file_path)
                    if file_findings:
                        results['findings'][str(file_path)] = file_findings
                    results['total_files_scanned'] += 1
                    
        return results

    def generate_report(self, results: Dict) -> str:
        """Генерирует читаемый отчет по результатам анализа."""
        report = []
        report.append(f"Анализ расширения VSCode: {results['extension_path']}")
        report.append(f"Всего просканировано файлов: {results['total_files_scanned']}")
        
        if results['package_analysis']:
            pkg = results['package_analysis']
            report.append("\nАнализ package.json:")
            report.append(f"Всего зависимостей: {pkg['total_dependencies']}")
            if pkg['suspicious_dependencies']:
                report.append("Подозрительные зависимости:")
                for dep in pkg['suspicious_dependencies']:
                    report.append(f"- {dep}")
        
        if results['findings']:
            report.append("\nНайдены подозрительные паттерны:")
            for file_path, findings in results['findings'].items():
                report.append(f"\nФайл: {file_path}")
                for category, lines in findings.items():
                    report.append(f"- {category}: строки {', '.join(map(str, lines))}")
                    
        return "\n".join(report)

def monitor_extension_process(extension_id: str):
    """Мониторит процесс расширения и блокирует подозрительную активность."""
    try:
        # Получаем PID процесса расширения
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {extension_id}.exe'],
            capture_output=True,
            text=True
        )
        
        # TODO: Добавить логику мониторинга процесса
        # Например, использовать pywin32 для Windows или psutil для кросс-платформенного мониторинга
        
    except Exception as e:
        print(f"Ошибка при мониторинге процесса: {e}")
