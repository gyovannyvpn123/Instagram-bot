#!/bin/bash

clear
echo -e "\e[91m[*] Instagram Bot Installer - by GyovaNyy\e[0m"

# Dă permisiune acestui fișier dacă nu o are
chmod +x install.sh

# Instalăm pachetele necesare
echo -e "\e[92m[*] Verificăm și instalăm pachete necesare...\e[0m"
pkg update -y && pkg upgrade -y
pkg install -y python git curl

# Clonăm repository-ul tău
REPO="https://github.com/gyovannyvpn123/Instagram-bot.git"
FOLDER="Instagram-bot"

if [ -d "$FOLDER" ]; then
    echo -e "\e[93m[*] Directorul $FOLDER există deja. Facem pull...\e[0m"
    cd "$FOLDER" && git pull
else
    echo -e "\e[96m[*] Clonăm repository-ul...\e[0m"
    git clone "$REPO"
    cd "$FOLDER"
fi

# Instalăm pip și dependențele
echo -e "\e[92m[*] Instalăm dependențele...\e[0m"
pip install --upgrade pip

# Instalează doar ce e listat în pyproject.toml (doar requests momentan)
DEPS=$(awk '/\[project.dependencies\]/ {found=1; next} /\[/ {found=0} found && NF {gsub(/"/, "", $1); print $1}' pyproject.toml)
pip install $DEPS

# Rulează scriptul
echo -e "\e[92m[*] Instalare completă!\e[0m"
echo -e "\e[96m[*] Rulăm acum scriptul: python main.py...\e[0m"
python main.py
