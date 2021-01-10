#!/bin/bash
set +e #
echo -e "\e[92mSeting up...\e[0m" #
echo "" #
echo "_________________________________________________________ " #
sudo dpkg-reconfigure tzdata #
sudo apt update #

sudo apt install -y build-essential libffi-dev libc6-dev libbz2-dev libexpat1-dev liblzma-dev \
zlib1g-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev \
libsqlite3-dev libssl-dev tk-dev ir-keytable build-dep python3-lxml #

cd #
echo -e "\e[92mInstalling OpenSSL 1.1.1b\e[0m" #
mkdir /home/volumio/src #
cd /home/volumio/src && mkdir openssl && cd openssl #
wget https://www.openssl.org/source/openssl-1.1.1b.tar.gz #
tar xvf openssl-1.1.1b.tar.gz && cd openssl-1.1.1b #
./config --prefix=/home/volumio/src/openssl-1.1.1b --openssldir=/home/volumio/src/openssl-1.1.1b && make -j4 && sudo make install #

cd #
sudo cp /home/volumio/Oden/ConfigurationFiles/ldconf/libc.conf /etc/ld.so.conf.d #
sudo ldconfig #
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/home/volumio/src/openssl-1.1.1b/lib #

echo -e "\e[92mInstalling Python 3.8.5 and related modules\e[0m" #
cd /home/volumio/src && mkdir python && cd python #
wget https://www.python.org/ftp/python/3.8.5/Python-3.8.5.tar.xz #
tar xf Python-3.8.5.tar.xz #
cd Python-3.8.5 #
sudo cp /home/volumio/Oden/ConfigurationFiles/python/Setup /home/volumio/src/python/Python-3.8.5/Modules #
./configure --prefix=/home/volumio/src/Python-3.8.5 --with-openssl=/home/volumio/src/openssl-1.1.1b && make -j4 && sudo make altinstall #

export PATH=/home/volumio/src/Python-3.8.5/bin:$PATH #
export LD_LIBRARY_PATh=/home/volumio/src/Python-3.8.5/bin #

sudo /home/volumio/src/Python-3.8.5/bin/pip3.8 install -U pip #
sudo /home/volumio/src/Python-3.8.5/bin/pip3.8 install -U setuptools #

sudo apt install -y python3-dev python3-setuptools python3-pip libfreetype6-dev libjpeg-dev \
python-rpi.gpio libcurl4-openssl-dev libssl-dev git-core autoconf make libtool libfftw3-dev \
libasound2-dev libncursesw5-dev libpulse-dev libtool #

sudo apt build-dep python3-lxml # Needed for selectors

sudo /home/volumio/src/Python-3.8.5/bin/pip3.8 install --upgrade setuptools pip wheel #
sudo /home/volumio/src/Python-3.8.5/bin/pip3.8 install --upgrade luma.oled #
sudo /home/volumio/src/Python-3.8.5/bin/pip3.8 install \
psutil socketIO-client pycurl gpiozero readchar numpy requests smbus evdev config selectors #
echo -e "\e[92mAll Python related modules are installed...\e[0m" #
cd #

mkdir bladelius
mkdir bladelius/var
touch bladelius/var/mute
touch bladelius/var/vol
touch bladelius/var/input
touch bladelius/var/stat

# Set up RAM Drive
# TODO Change system state writes to use this RAM Drive
sudo mkdir -p /mnt/ramdisk
sudo chown -R volumio:volumio /mnt/ramdisk
sudo mount -osize=1M -t tmpfs tmpfs /mnt/ramdisk

# Replace system files
# TODO Change to reading and modifying
cd /
sudo tar -xvf /home/volumio/Oden/odenfiles.tar
cd

sudo ir-keytable -c -w /etc/rc_keymaps/bdg_oden

echo -e "\e[92mInstalling Oden...\e[0m"
chmod +x /home/volumio/Oden/oden.py #
sudo cp /home/volumio/Oden/service-files/oden.service /lib/systemd/system/ #
sudo systemctl daemon-reload #
sudo systemctl enable oden.service #

echo -e "\e[92mAll done installing Oden files, please reboot...\e[0m"

exit 0 #