#!/usr/bin/env bash
# Solanize Data Bot — tek komut guncelleme
# Kullanim:  bash <(curl -sSL https://raw.githubusercontent.com/solanize/solanize-bot/main/update.sh)
#
# Ayarlarina (config.json) ve Telegram oturumuna DOKUNMAZ — bunlar git tarafindan
# takip edilmedigi icin kod sifirlansa bile silinmez. Tekrar giris yapman gerekmez.

REPO_URL="https://github.com/solanize/solanize-bot.git"

echo ""
echo "  Solanize Bot guncelleniyor..."
echo ""

# ── 1) bot klasorunu bul ──
if [ -d ".git" ] && [ -f "solanize_bot.py" ]; then
  DIR="$(pwd)"
elif [ -d "$HOME/solanize-bot/.git" ]; then
  DIR="$HOME/solanize-bot"
elif [ -d "solanize-bot/.git" ]; then
  DIR="$(pwd)/solanize-bot"
else
  echo "  X  Bot klasoru bulunamadi."
  echo "     Botun kurulu oldugu klasore gir, tekrar dene:  cd solanize-bot"
  exit 1
fi
cd "$DIR" || exit 1
echo "  Klasor: $DIR"

# ── 2) ayarlari yedekle (garanti olsun) ──
BK="$(mktemp -d)"
cp config.json "$BK/" 2>/dev/null
cp ./*.session "$BK/" 2>/dev/null

# ── 3) kodu son surume esitle (config/session takip edilmiyor -> etkilenmez) ──
if ! git fetch origin --quiet 2>/dev/null; then
  echo "  X  GitHub'a baglanilamadi. Internet baglantini kontrol et."
  exit 1
fi
git reset --hard origin/main --quiet 2>/dev/null || git reset --hard origin/master --quiet 2>/dev/null

# ── 4) ayarlar yerinde mi (olmadik bir sey olduysa geri koy) ──
[ -f config.json ] || cp "$BK/config.json" . 2>/dev/null
ls ./*.session >/dev/null 2>&1 || cp "$BK"/*.session . 2>/dev/null
rm -rf "$BK"

# ── 5) bagimliliklar ──
if [ -x "./venv/bin/pip" ]; then
  ./venv/bin/pip install -q --upgrade -r requirements.txt 2>/dev/null
else
  python3 -m venv venv >/dev/null 2>&1
  ./venv/bin/pip install -q --upgrade pip >/dev/null 2>&1
  ./venv/bin/pip install -q -r requirements.txt 2>/dev/null
fi

# ── 6) yeniden baslat ──
RESTARTED=0
if command -v systemctl >/dev/null 2>&1 && systemctl --user list-unit-files 2>/dev/null | grep -q "solanize-bot.service"; then
  systemctl --user restart solanize-bot.service 2>/dev/null && RESTARTED=1
fi
if [ "$RESTARTED" != "1" ]; then
  pkill -f "solanize_bot.py" 2>/dev/null
  sleep 1
  setsid ./venv/bin/python3 solanize_bot.py < /dev/null > bot.log 2>&1 &
fi
sleep 4

# ── 7) sonuc ──
echo ""
if pgrep -f "solanize_bot.py" >/dev/null 2>&1; then
  echo "  ==============================================="
  echo "   GUNCELLEME TAMAM — bot calisiyor."
  echo "  ==============================================="
  echo ""
  echo "   Ayarlarin korundu, tekrar giris gerekmiyor."
  echo ""
  echo "   YENI komutlar (Telegram > Kayitli Mesajlar):"
  echo "     /onchain on    Onchain Alert sinyalleri"
  echo "     /bstock  on    Binance Stock List sinyalleri"
  echo "   Ikisi de varsayilan KAPALI."
  echo ""
  echo "   Kontrol: /status  yaz — 'Onchain Alert:' satirini goruyorsan tamamdir."
else
  echo "  !  Bot baslamadi. Log:  tail -30 $DIR/bot.log"
fi
echo ""
