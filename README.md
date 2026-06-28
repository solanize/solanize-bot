# Solanize Data Bot

Solanize veri akışından **contract adreslerini yakalayıp kendi BASED botuna ileten**, tamamen **senin Telegram hesabınla** çalışan bağımsız bir bottur. Sunucu yok, 3. parti anahtar yok — her şey sende.

## Tek komutla kurulum
```bash
bash <(curl -sSL https://raw.githubusercontent.com/solanize/solanize-bot/main/install.sh)
```
Kurulum sihirbazı seni adım adım yönlendirir.

**Based bot:** https://t.me/based_eth_bot?start=r_Jackyz

## Manuel kurulum
```bash
git clone https://github.com/solanize/solanize-bot.git
cd solanize-bot
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python3 setup.py
./venv/bin/python3 solanize_bot.py
```
İlk açılışta telefon + Telegram doğrulama kodu istenir (oturum bir kez açılır).

## Gerekenler
- **api_id / api_hash** → https://my.telegram.org (API development tools)
- **Solanize grubuna üyelik** (erişim için yöneticiye başvur)
- **Kendi BASED botun** (CA göndereceğin bot)

## Komutlar (Telegram → Kayıtlı Mesajlar)
| Komut | Ne yapar |
|---|---|
| `/status` | Bot durumunu gösterir |
| `/on` / `/off` | Botu tamamen aç / kapat |
| `/allsol on\|off` | Solana adres iletimini aç/kapat |
| `/allevm on\|off` | EVM adres iletimini aç/kapat |
| `/hareket on 15k` | "Hareket Algılandı" sinyallerini AÇ — sadece mcap ≤ 15k iletilir |
| `/hareket off` | "Hareket Algılandı" iletimini kapat |

## Nasıl çalışır
1. Solanize'a düşen mesajları dinler.
2. **Hareket Algılandı** mesajıysa: `/hareket on` ise ve mcap ≤ belirlediğin değer ise CA'yı iletir.
3. Normal sinyalse: Solana CA → `/allsol` açıksa iletir; EVM CA → `/allevm` açıksa iletir.
4. Yakalanan CA, ayarladığın BASED botuna gönderilir.

## Güvenlik
`config.json` ve oturum dosyaları `.gitignore` ile korunur — **asla paylaşılmaz/commit edilmez.** api_hash ve oturumun yalnızca senin makinende kalır.
