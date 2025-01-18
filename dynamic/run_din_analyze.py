
import time

from din_analyze import VSCodeSecurityMonitor

# Создаем монитор
monitor = VSCodeSecurityMonitor()

# Показываем список расширений с анализом
monitor.print_monitored_extensions()

# Запускаем мониторинг
print("\nЗапуск мониторинга... (Ctrl+C для остановки)")
try:
    monitor.start_monitoring()
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    monitor.stop_monitoring()
    print("\nМониторинг остановлен")