#!/bin/bash
set +e #
echo -e "\e[92mSeting up...\e[0m" #
echo "" #
echo "_________________________________________________________ " #
sudo dpkg-reconfigure tzdata #
sudo apt update #

version=$(curl localhost:3000/api/v1/getSystemInfo | jq '.systemversion|tonumber')
if [[ $version > 3 ]]; then
 echo -e "\e[92m volumio 3 installed...\e[0m" 
else
 echo -e "\e[92mInstalled volumio is version $version going to exit...\e[0m" #
 exit 0 #
fi
sudo apt install -y ir-keytable python3-dev python3-setuptools python3-pip\
 libfreetype6-dev libjpeg-dev python-rpi.gpio

cd #
git clone https://github.com/GeorgeIoak/Oden bladelius

pip3 install --upgrade setuptools pip wheel
pip3 install --upgrade luma.oled
pip3 install psutil socketIO-client pycurl gpiozero readchar numpy requests evdev config selectors
pip3 install ConfigParser
echo -e "\e[92mFinished Installing Python Modules...\e[0m"
# Replace system files
# TODO Change to reading and modifying
cd /
sudo tar -xvf /home/volumio/bladelius/odenfiles.tar
cd

sudo dtoverlay gpio-ir gpio_pin=18 gpio_pull=up
sudo dtoverlay rotary-encoder pin_a=23 pin_b=22 relative_axis=1 steps-per-period=2
cd
sudo cp bladelius/ConfigurationFiles/bdg_oden /etc/rc_keymaps/.
chmod +x bladelius/bladelius.py
chmod +x bladelius/service-files/bdg-backup.sh
sudo cp bladelius/service-files/bdg-backup.sh /lib/systemd/system-shutdown/.
sudo cp bladelius/service-files/rc.local /etc/.

# Set up RAM Drive
# TODO Change system state writes to use this RAM Drive
sudo mkdir -p /mnt/ramdisk
sudo chown -R volumio:volumio /mnt/ramdisk
sudo mount -osize=1M -t tmpfs tmpfs /mnt/ramdisk

# Add these now before boot so ir-keytable command can find the IR
sudo dtoverlay gpio-ir gpio_pin=18 gpio_pull=up
sudo dtoverlay rotary-encoder pin_a=23 pin_b=22 relative_axis=1 steps-per-period=2
sudo ir-keytable -c -w /etc/rc_keymaps/bdg_oden

echo -e "\e[92mInstalling Oden...\e[0m"
chmod +x /home/volumio/bladelius/bladelius.py #

sudo cp bladelius/service-files/bladelius.service /lib/systemd/system/.
sudo cp bladelius/service-files/bdg-backup.service /lib/systemd/system/.
sudo cp bladelius/service-files/bdg-init.service /lib/systemd/system/.

sudo systemctl daemon-reload
sudo systemctl enable bladelius
sudo systemctl enable bdg-backup.service
sudo systemctl enable bdg-init.service

echo -e "\e[92mAll done installing Oden files, please reboot...\e[0m"

exit 0 #