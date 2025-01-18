# Создаем экземпляр анализатора
analyzer = VSCodeExtensionAnalyzer("/path/to/extension")

# Запускаем анализ
results = analyzer.analyze()

# Генерируем отчет
report = analyzer.generate_report(results)
print(report)