import subprocess

# Пример команды с аргументами
command = "sudo cat /dev/kmsg > /tmp/asd"

# Запуск команды в фоновом режиме
process = subprocess.Popen(command, shell=True)

print("Команда запущена в фоновом режиме.")