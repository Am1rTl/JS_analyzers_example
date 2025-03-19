import psutil
import time
import subprocess

def get_pid():
    command = "ps aux | grep code | grep -v grep | sort -h | head -n 1"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    output_lines = result.stdout.strip().split('\n')[0]
    output_lines = output_lines.strip().split(' ')
    run = True
    while run:
        try:
            pid = int(output_lines[0])
            run = False
        except:
            output_lines.pop(0)
    return pid

def monitor_process(pid):
    with open('process_info.log', 'w') as log_file:
        while True:
            try:
                # Получаем процесс по PID
                proc = psutil.Process(pid)
                # Получаем данные о CPU и RAM для основного процесса
                cpu_usage = proc.cpu_percent(interval=1)  # Получаем процент использования CPU
                memory_usage = proc.memory_info().rss  # Использование RAM в МБ
                
                # Получаем дочерние процессы
                child_procs = proc.children(recursive=True)
                total_cpu_usage = cpu_usage
                total_memory_usage = memory_usage
                
                # Суммируем показатели дочерних процессов
                for child in child_procs:
                    total_cpu_usage += child.cpu_percent(interval=0)  # Получаем CPU дочернего процесса
                    total_memory_usage += child.memory_info().rss  # Использование RAM в МБ
                
                # CPU RAM
    
                total_memory_usage_percentage = (total_memory_usage / psutil.virtual_memory().total) * 100  # Convert to percentage
                log_file.write(str(total_cpu_usage) + ' ' + str(int(total_memory_usage_percentage)) + '\n')
                log_file.write("\n")
                log_file.flush()
            
            except psutil.NoSuchProcess:
                log_file.write(f"Процесс с PID {pid} не найден.\n")
                break
            except psutil.AccessDenied:
                log_file.write(f"Нет доступа к процессу с PID {pid}.\n")
                break
            
            time.sleep(10)  # Ждем 10 секунд перед следующей проверкой

if __name__ == "__main__":
    try:
        pid = get_pid()
        print(f"PID получен, начинаю логирование процесса {pid}")
        monitor_process(pid)
    except ValueError:
        print("Пожалуйста, введите корректный числовой PID.")
