import psutil
import time

def monitor_process(pid):
    while True:
        try:
            # Получаем процесс по PID
            proc = psutil.Process(pid)
            # Получаем данные о CPU и RAM для основного процесса
            cpu_usage = proc.cpu_percent(interval=1)  # Получаем процент использования CPU
            memory_usage = proc.memory_info().rss / (1024 * 1024)  # Использование RAM в МБ
            
            # Получаем дочерние процессы
            child_procs = proc.children(recursive=True)
            total_cpu_usage = cpu_usage
            total_memory_usage = memory_usage
            
            # Суммируем показатели дочерних процессов
            for child in child_procs:
                total_cpu_usage += child.cpu_percent(interval=0)  # Получаем CPU дочернего процесса
                total_memory_usage += child.memory_info().rss / (1024 * 1024)  # Использование RAM в МБ
            
            print(f"PID: {pid}, Процесс: {proc.name()}, CPU: {cpu_usage}%, RAM: {memory_usage:.2f} MB")
            print(f"Суммарное использование CPU: {total_cpu_usage}%, Суммарное использование RAM: {total_memory_usage:.2f} MB")
        
        except psutil.NoSuchProcess:
            print(f"Процесс с PID {pid} не найден.")
            break
        except psutil.AccessDenied:
            print(f"Нет доступа к процессу с PID {pid}.")
            break
        
        time.sleep(10)  # Ждем 10 секунд перед следующей проверкой

if __name__ == "__main__":
    try:
        pid = int(input("Введите PID процесса для мониторинга: "))
        monitor_process(pid)
    except ValueError:
        print("Пожалуйста, введите корректный числовой PID.")
