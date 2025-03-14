import os
import time

# Open /dev/kmsg in binary mode
with open("/dev/kmsg", 'rb') as f:
    while True:
        # Read a specific number of bytes (e.g., 1024)
        data = os.read(f.fileno(), 1024)
        if data:
            print(data.decode('utf-8', errors='ignore'))
        else:
            time.sleep(0.1)  # Sleep briefly to avoid busy waiting