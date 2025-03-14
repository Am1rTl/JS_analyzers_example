sudo userdel vscext
sudo rm -rf /home/vscext/

sudo useradd -m -s /bin/bash vscext
xhost +SI:localuser:vscext
echo ''
echo "Succeed create user"
sudo -u vscext /bin/bash
