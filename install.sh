#!/usr/bin/env bash
# Solanize Data Bot — tek komut kurulum
# Kullanım:  bash <(curl -sSL https://raw.githubusercontent.com/solanize/solanize-bot/main/install.sh)
set -e

REPO_URL="https://github.com/solanize/solanize-bot.git"
DIR="solanize-bot"

echo ">> Solanize Data Bot kuruluyor..."

command -v git     >/dev/null 2>&1 || { echo "HATA: git gerekli.  (kur: apt install git)"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "HATA: python3 gerekli."; exit 1; }

if [ -d "$DIR/.git" ]; then
  echo ">> Mevcut kopya güncelleniyor..."
  cd "$DIR" && git pull --ff-only || true
else
  git clone "$REPO_URL" "$DIR"
  cd "$DIR"
fi

echo ">> Bağımlılıklar kuruluyor..."
python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo ""
echo "==================================================="
echo ">> KURULUM SİHİRBAZI — sorulara sırayla cevap ver."
echo "==================================================="
echo ""
./venv/bin/python3 setup.py < /dev/tty

if [ ! -f config.json ]; then
  echo "HATA: kurulum tamamlanmadı (config.json yok). Tekrar dene."; exit 1
fi

# eski instance/servis varsa durdur (cift calismayi onle)
systemctl --user stop solanize-bot.service 2>/dev/null || true
pkill -f "solanize_bot.py" 2>/dev/null || true
sleep 1

APP="$(pwd)"
PY="$APP/venv/bin/python3"

echo ""
echo ">> Bot 7/24 çalışacak şekilde başlatılıyor..."

started=0
# ── 1. TERCİH: systemd user servisi (yeniden başlatmada da otomatik açılır) ──
if command -v systemctl >/dev/null 2>&1; then
  mkdir -p "$HOME/.config/systemd/user"
  cat > "$HOME/.config/systemd/user/solanize-bot.service" <<EOF
[Unit]
Description=Solanize Data Bot
After=network-online.target

[Service]
WorkingDirectory=$APP
ExecStart=$PY $APP/solanize_bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF
  if systemctl --user daemon-reload 2>/dev/null && systemctl --user enable --now solanize-bot.service 2>/dev/null; then
    loginctl enable-linger "$USER" >/dev/null 2>&1 || true   # oturum kapansa/reboot olsa da çalışsın
    started=1
    echo ""
    echo "  ✅ Bot ÇALIŞIYOR — 7/24 servis kuruldu (yeniden başlatmada otomatik açılır)."
    echo "     Durum   : systemctl --user status solanize-bot"
    echo "     Canlı log: journalctl --user -u solanize-bot -f"
    echo "     Durdur  : systemctl --user stop solanize-bot"
    echo "     Başlat  : systemctl --user start solanize-bot"
  fi
fi

# ── FALLBACK: systemd yoksa arka planda (setsid) ──
if [ "$started" != "1" ]; then
  setsid "$PY" "$APP/solanize_bot.py" < /dev/null > "$APP/bot.log" 2>&1 &
  sleep 4
  if pgrep -f "solanize_bot.py" >/dev/null; then
    echo ""
    echo "  ✅ Bot ÇALIŞIYOR (arka planda)."
    echo "     Canlı log: tail -f $APP/bot.log"
    echo "     Durdur   : pkill -f solanize_bot.py"
    echo "     Başlat   : cd $APP && setsid ./venv/bin/python3 solanize_bot.py </dev/null >bot.log 2>&1 &"
    echo "     (Not: sunucu yeniden başlarsa tekrar başlatman gerekir.)"
  else
    echo "  ⚠️ Bot başlamadı olabilir. Log:  cat $APP/bot.log"
  fi
fi

echo ""
echo "  📋 Komutlar → Telegram > Kayıtlı Mesajlar:"
echo "     /status   /block <handle>   /safe add <handle>   /allevm on 50k   /addtg @kanal"
echo ""
echo ">> Kurulum tamamlandı. İyi kazançlar!"
