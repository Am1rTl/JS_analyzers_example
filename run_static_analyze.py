# Создаем и настраиваем анализатор и монитор
extension_path = "/path/to/extension"
extension_id = "publisher.extension-name"

# Статический анализ
analyzer = VSCodeExtensionAnalyzer(extension_path)
results = analyzer.analyze()
print(analyzer.generate_report(results))

# Запуск мониторинга процессов
monitor = VSCodeProcessMonitor(extension_id)
monitor.start_monitoring()

try:
    # Основной код приложения
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # Корректное завершение при нажатии Ctrl+C
    monitor.stop_monitoring()
