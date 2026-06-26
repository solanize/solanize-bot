#!/usr/bin/env bash
# Solanize Data Bot - tek komut kurulum
# Kullanım:  bash <(curl -sSL https://raw.githubusercontent.com/solanize/solanize-bot/main/install.sh)
set -e

REPO_URL="https://github.com/solanize/solanize-bot.git"   # <-- kendi repo adresini yaz
DIR="solanize-bot"

echo ">> Solanize Data Bot kuruluyor..."

command -v git    >/dev/null 2>&1 || { echo "HATA: git gerekli."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "HATA: python3 gerekli."; exit 1; }

if [ -d "$DIR/.git" ]; then
  echo ">> Mevcut kopya güncelleniyor..."
  cd "$DIR" && git pull --ff-only
else
  git clone "$REPO_URL" "$DIR"
  cd "$DIR"
fi

python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo ">> Kurulum sihirbazı başlıyor..."
./venv/bin/python3 setup.py < /dev/tty

echo ""
echo ">> Botu çalıştırmak için:"
echo "     cd $DIR && ./venv/bin/python3 solanize_bot.py"
