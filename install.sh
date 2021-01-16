#!/bin/bash
set +e #
echo -e "\e[92mSeting up...\e[0m" #
echo "" #
echo "_________________________________________________________ " #
sudo dpkg-reconfigure tzdata #
sudo apt update #

sudo apt install -y build-essential libffi-dev libc6-dev libbz2-dev libexpat1-dev liblzma-dev\
 zlib1g-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev\
 libsqlite3-dev libssl-dev tk-dev ir-keytable make git-core autoconf libtool

cd #
echo -e "\e[92mInstalling OpenSSL 1.1.1b\e[0m" #
mkdir -p /home/volumio/src #
cd /home/volumio/src && mkdir -p openssl && cd openssl #
wget https://www.openssl.org/source/openssl-1.1.1b.tar.gz #
tar xvf openssl-1.1.1b.tar.gz && cd openssl-1.1.1b #
./config --prefix=/home/volumio/src/openssl-1.1.1b --openssldir=/home/volumio/src/openssl-1.1.1b && make -j4 && make install #

cd #
sudo cp /home/volumio/Oden/ConfigurationFiles/ldconf/libc.conf /etc/ld.so.conf.d #
sudo ldconfig #
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/home/volumio/src/openssl-1.1.1b/lib #

echo -e "\e[92mInstalling Python 3.9.1 and related modules\e[0m" #
cd /home/volumio/src && mkdir -p python && cd python #
wget https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tar.xz #
tar xf Python-3.9.1.tar.xz #
cd Python-3.9.1 #
cp /home/volumio/Oden/ConfigurationFiles/python/Setup.local /home/volumio/src/python/Python-3.9.1/Modules #
# Without optimization you can use -j4, but with it you'll get segfault
./configure --prefix=/home/volumio/src/Python-3.9.1 --with-openssl=/home/volumio/src/openssl-1.1.1b && make profile-opt && make altinstall #

export PATH=/home/volumio/src/Python-3.9.1/bin:$PATH #
export LD_LIBRARY_PATH=/home/volumio/src/Python-3.9.1/bin #

sudo apt install -y python3-dev python3-setuptools python3-pip libfreetype6-dev libjpeg-dev\
 python-rpi.gpio libcurl4-openssl-dev libfftw3-dev libasound2-dev libpulse-dev #

sudo apt-get -y build-dep python3-lxml # Needed for selectors

/home/volumio/src/Python-3.9.1/bin/pip3.9 install --upgrade setuptools pip wheel #
/home/volumio/src/Python-3.9.1/bin/pip3.9 install --upgrade luma.oled #
/home/volumio/src/Python-3.9.1/bin/pip3.9 install\
 psutil socketIO-client pycurl gpiozero readchar numpy requests smbus evdev config selectors #
echo -e "\e[92mAll Python related modules are installed...\e[0m" #
cd #

mkdir -p bladelius
mkdir -p bladelius/var
touch bladelius/var/mute
touch bladelius/var/vol
touch bladelius/var/input
touch bladelius/var/stat

# Don't need to add to bash_aliases
FILE=/home/volumio/.bash_aliases
if [ -f "$FILE" ]; then
    echo "$FILE exists."
    rm $FILE
fi

declare -A FILES
FILES=(
    ["python3.9"]="/usr/local/bin/python39"
    ["pip3.9"]="/usr/local/bin/pip39"
    )
for thefile in "${!FILES[@]}"
do
    if [[ -L ${FILES[$thefile]} ]]; then
        if [[ -e ${FILES[$thefile]} ]]; then
            echo "${FILES[$thefile]} exists and link is good"
        else
            unlink ${FILES[$thefile]}
            echo "${FILES[$thefile]} link was broken so it was removed"
        fi
    else
        echo "${FILES[$thefile]} isn't a link, I'll add it"
        ln -s "/home/volumio/src/Python-3.9.1/bin/$thefile" ${FILES[$thefile]}
    fi
done

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

# Add these now before boot so ir-keytable command can find the IR
sudo dtoverlay gpio-ir gpio_pin=18 gpio_pull=up
sudo dtoverlay rotary-encoder pin_a=23 pin_b=22 relative_axis=1 steps-per-period=2
sudo ir-keytable -c -w /etc/rc_keymaps/bdg_oden

echo -e "\e[92mInstalling Oden...\e[0m"
chmod +x /home/volumio/Oden/oden.py #
sudo cp /home/volumio/Oden/service-files/oden.service /lib/systemd/system/ #
sudo systemctl daemon-reload #
sudo systemctl enable oden.service #

echo -e "\e[92mAll done installing Oden files, please reboot...\e[0m"

exit 0 #