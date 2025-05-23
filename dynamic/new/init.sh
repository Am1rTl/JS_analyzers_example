#!/bin/bash

set -x

# Remove the user if it exists
sudo userdel -r vscext 2>/dev/null

# Create the user
sudo useradd -m -s /bin/bash vscext

# Set permissions for the extensions directory
sudo mkdir -p /home/amir/.vscode/extensions
#sudo chown -R vscext:vscext /home/amir/.vscode/
sudo setfacl -d -m u:vscext:rwx /home/amir/.vscode/
#sudo usermod -aG amir vscext
sudo setfacl -R -m u:vscext:rwx /home/amir


# Allow the new user to access the display
xhost +SI:localuser:vscext
touch /tmp/asd
chmod 666 /tmp/asd
echo "Succeed create user"
echo "Start set privileges"
echo "Privileges were changed"
echo "Starting the installation"
sudo mkdir -p /home/vscext/asd
sudo cp /home/amir/Загрузки/code-stable-x64-1741787903.tar.gz /home/vscext/asd/
sudo tar -xzvf /home/vscext/asd/code-stable-x64-1741787903.tar.gz -C /home/vscext/asd/

# Create necessary log files and directories
sudo rm -rf /tmp/asd
mkdir -p /tmp/asd
touch /tmp/asda
chmod 666 /tmp/asda

# Create log files in the current directory
touch process_info.log files_read.log files_write.log
chmod 666 process_info.log files_read.log files_write.log

# Create log files in the web directory
touch web/process_info.log web/files_read.log web/files_write.log
chmod 666 web/process_info.log web/files_read.log web/files_write.log

# Make sure rules file exists
echo "{}" > web/rules
chmod 666 web/rules

# Run main.py to start logging
echo "Starting kernel log capture"
python main.py

echo "Set iptables rule"
sudo iptables -I OUTPUT -m owner --uid-owner `id -u vscext` -j LOG --log-prefix "VSCode : " --log-level 4

echo "Run application and vscode"
sudo python web/strace.py & python web/strace_log.py & python web/get_sys_info.py & sudo python web/app.py & firefox-esr http://127.0.0.1:5000/ & sudo -u vscext /home/vscext/asd/VSCode-linux-x64/./code --extensions-dir /home/`whoami`/.vscode/extensions/
