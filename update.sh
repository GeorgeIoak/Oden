#!/bin/bash
set +e #
echo -e "\e[92mStopping Service and Grabbing New Code...\e[0m" #
echo "" #
echo "_________________________________________________________ " #
sudo systemctl stop oden.service
cd /home/volumio/Oden
git pull
sudo systemctl start oden.service
echo "" #
echo "_________________________________________________________ " #
echo -e "\e[92mCode has been updated...\e[0m" #