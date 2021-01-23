#!/bin/bash
boldRed="\e[1;91m"
green="\e[0;92m"
yellow="\e[0;33m"
reset="\e[0m"


set +e #
echo -e "\e[92mStopping Service and Grabbing New Code...\e[0m" #
echo "" #
echo "_________________________________________________________ " #
sudo systemctl stop oden.service
cd /home/volumio/Oden
#git reset --hard
git config core.filemode false  # Copying from Windows changes execute bit on Linux so ignore it
git pull

thefile='/usr/lib/libbcm_host.so'
if [[ -L $thefile ]]; then
    if [[ -e $thefile ]]; then
        echo -e "${green}it's already there, no worries...${reset}"
    else
        unlink $thefile
        echo -e "${boldRed}$thefile link was broken and removed"
        echo -e "Let George know there's a problem!!${reset}"
    fi
else
    echo -e "${yellow}$thefile isn't a link, I'll add it${reset}"
    sudo systemctl stop mpd.service
    sudo ln -s /opt/vc/lib/libbcm_host.so /usr/lib/
    sudo systemctl start mpd.service
fi

sudo systemctl start oden.service
echo "" #
echo "_________________________________________________________ " #
echo -e "\e[92mCode has been updated...\e[0m" #