#!/bin/bash
set +e #
echo -e "\e[92mSeting up...\e[0m" #
echo "" #
echo "_________________________________________________________ " #
sudo dpkg-reconfigure tzdata #
sudo apt-get update #
sudo apt-get install -y build-essential libffi-dev libc6-dev libbz2-dev libexpat1-dev liblzma-dev \
zlib1g-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev \
libsqlite3-dev libssl-dev ir-keytable build-dep python3-lxml#
cd #
sudo chmod +x /home/volumio/Oden/PreConfiguration.sh #
sudo chmod +x /home/volumio/Oden/pcf-i2c-adress-config.sh #
sudo chmod +x /home/volumio/Oden/ftp.sh #
sudo echo "dtparam=spi=on" >> /boot/userconfig.txt #
sudo echo "dtparam=i2c=on" >> /boot/userconfig.txt #

sed -i 's/\(SpectrumActive = \)\(.*\)/\1False/' /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #
sed -i 's/\(NR1UIRemoteActive = \)\(.*\)/\1False/' /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py

echo -e "\e[92mInstalling OpenSSL 1.1.1b\e[0m" #
mkdir /home/volumio/src #
cd /home/volumio/src && mkdir openssl && cd openssl #
wget https://www.openssl.org/source/openssl-1.1.1b.tar.gz #
tar xvf openssl-1.1.1b.tar.gz && cd openssl-1.1.1b #
./config --prefix=/home/volumio/src/openssl-1.1.1b --openssldir=/home/volumio/src/openssl-1.1.1b && make && sudo make install #
cd #
sudo cp /home/volumio/Oden/ConfigurationFiles/ldconf/libc.conf /etc/ld.so.conf.d #
sudo ldconfig #
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/home/volumio/src/openssl-1.1.1b/lib #
echo -e "\e[92mInstalling Python 3.9.1 and related modules\e[0m" #
cd /home/volumio/src && mkdir python && cd python #
wget https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tar.xz #
tar xf Python-3.9.1.tar.xz #
cd Python-3.9.1 #
sudo cp /home/volumio/Oden/ConfigurationFiles/python/Setup /home/volumio/src/python/Python-3.9.1/Modules #
./configure --prefix=/home/volumio/src/Python-3.9.1 --with-openssl=/home/volumio/src/openssl-1.1.1b && make -j4 && sudo make altinstall #
export PATH=/home/volumio/src/Python-3.9.1/bin:$PATH #
export LD_LIBRARY_PATh=/home/volumio/src/Python-3.9.1/bin #
sudo /home/volumio/src/Python-3.9.1/bin/pip3.9 install -U pip #
sudo /home/volumio/src/Python-3.9.1/bin/pip3.9 install -U setuptools #
sudo apt-get install -y python3-dev python3-setuptools python3-pip libfreetype6-dev libjpeg-dev \
python-rpi.gpio libcurl4-openssl-dev libssl-dev git-core autoconf make libtool libfftw3-dev \
libasound2-dev libncursesw5-dev libpulse-dev libtool evdev config selectors #
sudo /home/volumio/src/Python-3.9.1/bin/pip3.9 install --upgrade setuptools pip wheel #
sudo /home/volumio/src/Python-3.9.1/bin/pip3.9 install --upgrade luma.oled #
sudo /home/volumio/src/Python-3.9.1/bin/pip3.9 install psutil socketIO-client pcf8574 pycurl gpiozero readchar numpy requests #
echo -e "\e[92mAll Python related modules are installed...\e[0m" #
cd #

mkdir bladelius
mkdir bladelius/var
touch bladelius/var/mute
touch bladelius/var/vol
touch bladelius/var/input
touch bladelius/var/stat

# Set up RAM Drive
sudo mkdir -p /mnt/ramdisk
sudo chown -R volumio:volumio /mnt/ramdisk
sudo mount -osize=1M -t tmpfs tmpfs /mnt/ramdisk

tar -xf odenfiles.tar

# echo -e "\e[92mInstalling Oden...\e[0m"
# chmod +x /home/volumio/Oden/nr1ui.py #
# sudo cp /home/volumio/Oden/service-files/nr1ui.service /lib/systemd/system/ #
# sudo systemctl daemon-reload #
# sudo systemctl enable nr1ui.service #
sed -i 's/\(DisplayTechnology = \)\(.*\)/\1"'"spi1322"'"/' /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #

sed -i 's/\(NowPlayingLayout = \)\(.*\)/\1"'"No-Spectrum"'"/' /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py # 
echo "No-Spectrum" > /home/volumio/Oden/ConfigurationFiles/LayoutSet.txt #

sed -i 's/\(oledrotation = \)\(.*\)/\10/' /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py # 

sed -i "s/\(oledBtnA = \)\(.*\)/\14/" /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #
sed -i "s/\(oledBtnB = \)\(.*\)/\117/" /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #
sed -i "s/\(oledBtnC = \)\(.*\)/\15/" /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #
sed -i "s/\(oledBtnD = \)\(.*\)/\16/" /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #
#sed -i "s/\(oledRtrLeft = \)\(.*\)/\1$LNumber/" /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #
#sed -i "s/\(oledRtrRight = \)\(.*\)/\1$RNumber/" /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #
#sed -i "s/\(oledRtrBtn = \)\(.*\)/\1$RBNumber/" /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #

sed -i "s/\(oledPause2StopTime = \)\(.*\)/\130.0/" /home/volumio/Oden/ConfigurationFiles/PreConfiguration.py #

echo " " #
echo -e "\e[91mPlease set Audio-Output to HDMI or Headphones and save setting.\e[0m" #
echo -e "\e[91mNow Select your DAC/Playback device and save aggain.\e[0m" #
exit 0 #