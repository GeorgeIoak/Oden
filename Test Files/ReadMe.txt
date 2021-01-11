#copy config.txt and userconfig.txt

git clone https://github.com/Maschine2501/NR1-UI.git
bash NR1-UI/install.sh
sudo reboot

sudo apt install -y ir-keytable
sudo nano /lib/udev/rules.d/60-ir-keytable.rules

Make the following change, comment out the last line and replace:

#ACTION=="add", SUBSYSTEM=="rc", RUN+="/usr/bin/ir-keytable -a  etc/rc_maps.cfg -s $name"
ACTION=="add", SUBSYSTEM=="input", SUBSYSTEMS=="rc", KERNEL=="event*", ENV{.rc_sysdev}="$id", RUN+="/usr/bin/ir-keytable -a /etc/rc_maps.cfg -s $env{.rc_sysdev}"

# need to edit /etc/rc_maps.cfg and add the oden remote codes file after you create the file /etc/rc_keymaps/bdg_oden

sudo nano /etc/rc_keymaps/bdg_oden
# table bdg_oden_rc5, type: RC5
0x81b KEY_VOLUMEUP
0x81c KEY_VOLUMEDOWN
0x818 KEY_PREVIOUS
0x817 KEY_NEXT

sudo nano /etc/rc_maps.cfg
#driver table                    file
*       *                        /etc/rc_keymaps/bdg_oden

ln -s /home/volumio/src/Python-3.8.5/bin/python3.8 /usr/local/bin/python38
ln -s /home/volumio/src/Python-3.8.5/bin/pip3.8 /usr/local/bin/pip38
pip38 install pcf8574, evdev, config

#copy config.py
mkdir bladelius
mkdir bladelius/var
touch bladelius/var/mute
touch bladelius/var/vol
touch bladelius/var/input
touch bladelius/var/stat

#volumio uses uses /etc/triggerhappy/triggers.d/audio.conf to control volume. need to comment out volume
sudo nano /etc/triggerhappy/triggers.d/audio.conf
#VOLUME UP
#KEY_VOLUMEUP 1 /usr/local/bin/volumio volume plus

#VOLUME DOWN
#KEY_VOLUMEDOWN 1 /usr/local/bin/volumio volume minus

# Set up RAM Drive
sudo mkdir -p /mnt/ramdisk
sudo chown -R volumio:volumio /mnt/ramdisk
sudo mount -osize=1M -t tmpfs tmpfs /mnt/ramdisk
# Make Ram Disk Automatic on Boot
sudo nano /etc/fstab
tmpfs /mnt/ramdisk tmpfs defaults,noatime,mode=755,uid=volumio,gid=volumio,size=1M 0 0

2021/01/04
Preparing to install selectors module so I can check 2 event sources at the "same time"

sudo apt-get build-dep python3-lxml
pip38 install selectors