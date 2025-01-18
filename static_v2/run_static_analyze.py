from static_analyzer import VSCodeExtensionAnalyzer  # Import the class

# Создаем экземпляр анализатора
analyzer = VSCodeExtensionAnalyzer("/home/amir/.vscode/extensions/postman.postman-for-vscode-1.6.1")

# Запускаем анализ
results = analyzer.analyze()

# Генерируем отчет
report = analyzer.generate_report(results)

# Выводим отчет
print(report)
