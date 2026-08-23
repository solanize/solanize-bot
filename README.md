# Solanize Bot

Solanize veri akışından **contract adreslerini (CA) yakalayıp, senin belirlediğin kurallara göre kendi BASED botuna ileten** kişisel bir bottur.

Tamamen **senin Telegram hesabınla** çalışır (userbot). İstersen kendi **bilgisayarına**, istersen bir **sunucuya (VPS)** kurarsın — 7/24 kesintisiz çalışması için sunucu önerilir. Merkezî bir sunucumuz/aracımız yoktur; api bilgilerin, oturumun ve tüm ayarların yalnızca **sende** kalır.

---

## İçindekiler
- [Nasıl çalışır](#nasıl-çalışır)
- [Gerekenler](#gerekenler)
- [Kurulum (tek komut)](#kurulum-tek-komut)
- [Komutlar](#komutlar)
  - [Temel kontrol](#1-temel-kontrol)
  - [Kişisel filtreler — *ne gelmesin*](#2-kişisel-filtreler--ne-gelmesin)
  - [Alım kuralları — *ne mutlaka gelsin*](#3-alım-kuralları--ne-mutlaka-gelsin)
  - [Ekstra kaynaklar](#4-ekstra-kaynaklar)
- [Öncelik sırası](#öncelik-sırası)
- [Bot yönetimi](#bot-yönetimi)
- [Güvenlik ve gizlilik](#güvenlik-ve-gizlilik)
- [Sık sorulanlar](#sık-sorulanlar)

---

## Nasıl çalışır

1. Bot, Solanize grubuna düşen sinyalleri **senin hesabınla** dinler.
2. Her mesaj için **kişisel filtrelerinden** geçirir (engellediğin hesap/kelime, yanıt/alıntı vb. elenir).
3. Mesaj türüne göre karar verir:
   - **Hareket Algılandı** sinyali → `/hareket` açıksa ve piyasa değeri belirlediğin tavanın altındaysa iletir.
   - **Normal sinyal** → Solana CA'yı `/allsol`, EVM CA'yı `/allevm` açıksa iletir (istersen piyasa değeri tavanıyla).
4. Yakaladığı CA'yı **senin ayarladığın BASED botuna** gönderir; gerisini BASED botun yapar.

Karar tamamen **client-side**'dır: Solanize'ın ana feed'ine dokunmazsın, yalnızca **sana gelen/ilettiğin** kısmı kendine göre şekillendirirsin.

---

## Gerekenler

| Gereksinim | Nereden |
|---|---|
| **api_id + api_hash** | https://my.telegram.org → *API development tools* |
| **Solanize üyeliği** | Abone ol / üye ol: **[@SolanizeAbonelik_bot](https://t.me/SolanizeAbonelik_bot)** *(üye değilsen kurulum başlamaz)* |
| **Kendi BASED botun** | CA'ları göndereceğin bot: **[based_eth_bot](https://t.me/based_eth_bot?start=r_Jackyz)** |
| **python3 + git** | Sunucunda/makinende kurulu olmalı |

---

## Kurulum (tek komut)

```bash
bash <(curl -sSL https://raw.githubusercontent.com/solanize/solanize-bot/main/install.sh)
```

## Güncelleme

Bot güncellendiğinde tek komut yeter:

```bash
bash <(curl -sSL https://raw.githubusercontent.com/solanize/solanize-bot/main/update.sh)
```

Ayarların (`config.json`) ve Telegram oturumun **korunur** — tekrar giriş yapman gerekmez,
safe/block listelerin ve açık-kapalı tercihlerin aynen kalır.

Güncellemenin geçtiğini doğrulamak için Kayıtlı Mesajlar'dan `/status` yaz;
çıktıda **Onchain Alert** ve **Binance Stock** satırlarını görüyorsan tamamdır.

Bu tek komut sırasıyla şunları yapar:

1. Kodu indirir, sanal ortam (venv) kurar, bağımlılıkları yükler.
2. **Kurulum sihirbazını** başlatır — sorularına sırayla cevap verirsin:
   - **Adım 1/4 — API:** `api_id` ve `api_hash` girersin.
   - **Adım 2/4 — Giriş:** telefon numaran + Telegram'a gelen kod (2FA şifren varsa o da).
     > ⚠️ Gelen kodu **elle yaz, kopyala-yapıştır yapma** — Telegram yapıştırılan kodu geçersiz kılabilir.
   - **Adım 3/4 — Üyelik:** Solanize üyeliğin **otomatik doğrulanır.** Üye değilsen kurulum burada durur.
   - **Adım 4/4 — BASED bot:** BASED botunun `@kullanıcıadı` (girince doğrulanır).
3. Ayarları kaydeder ve **botu 7/24 arka planda başlatır** (systemd servisi; sunucu yeniden başlasa bile otomatik açılır).

Kurulum bittiğinde bot çalışıyordur. Komutları aşağıdaki gibi **Telegram > Kayıtlı Mesajlar**'a yazarsın.

---

## Komutlar

> Tüm komutlar **Telegram uygulamanda "Kayıtlı Mesajlar" (Saved Messages)** sohbetine yazılır. Bot senin hesabınla çalıştığı için komutları oradan alır.

### 1) Temel kontrol

| Komut | Ne işe yarar |
|---|---|
| `/status` | Botun anlık durumunu gösterir: hangi modlar açık, tavanlar, kaç filtre/kural/kaynak var. **İlk bakılacak komut.** |
| `/on` | Botu açar — sinyaller iletilmeye başlar. |
| `/off` | Botu tamamen durdurur — hiçbir sinyal iletilmez (ayarların korunur). |
| `/allsol on [tavan]` | **Solana** CA iletimini açar. `tavan` **opsiyonel ve senin belirlediğin** piyasa değeridir: yazmazsan sınırsız, yazarsan yalnızca o değerin altındakiler iletilir. Örn: `/allsol on` (sınırsız), `/allsol on 100k`, `/allsol on 250k`. *(Piyasa değeri okunamayan mesaj yine iletilir.)* |
| `/allsol off` | Solana iletimini kapatır. |
| `/allevm on [tavan]` | **EVM** CA iletimini açar. Tavan opsiyonel ve **sen seçersin**. Örn: `/allevm on`, `/allevm on 50k`, `/allevm on 1m`. |
| `/allevm off` | EVM iletimini kapatır. |
| `/hareket on <tavan>` | **"Hareket Algılandı"** (resurgence) sinyallerini açar — yalnızca **senin belirlediğin** piyasa değerinin altındakiler iletilir. Örn: `/hareket on 15k`, `/hareket on 50k`. Erken/düşük-cap girişleri yakalamak için. |
| `/onchain on` / `/onchain off` | **Onchain Alert** başlığını açar/kapatır — akıllı cüzdan takibinden gelen sinyaller BASED bot'a iletilir. Varsayılan: kapalı. |
| `/bstock on` / `/bstock off` | **Binance Stock List** başlığını açar/kapatır — Binance stock-meme listelemeleri BASED bot'a iletilir. Varsayılan: kapalı. |
| `/hareket off` | Hareket Algılandı iletimini kapatır. |

> **Tavan formatı:** `15k` = 15.000, `1m` = 1.000.000, ya da düz sayı (`50000`). Değerleri tamamen sen seçersin; `15k`/`50k` sadece örnektir.

### 2) Kişisel filtreler — *ne gelmesin*

Feed'i kendine göre süzersin. **Ana feed'e dokunmaz, yalnızca senin botunu etkiler.**

| Komut | Ne işe yarar | Örnek |
|---|---|---|
| `/block <handle>` | Bir X hesabını **engeller** — o hesabın sinyalleri sana iletilmez. | `/block elonmusk` |
| `/unblock <handle>` | Hesap engelini kaldırır. | `/unblock elonmusk` |
| `/blocklist` | Tüm filtrelerini (engelli hesaplar, kelimeler, beyaz liste, yanıt ayarı) tek listede gösterir. | |
| `/blocklist add <kelime>` | Bir **kelimeyi engeller** — o kelimenin geçtiği hiçbir mesaj iletilmez. | `/blocklist add presale` |
| `/blocklist remove <kelime>` | Kelime engelini kaldırır. | `/blocklist remove presale` |
| `/only <handle...>` | **Beyaz liste modu:** yalnızca yazdığın hesaplar işlenir, gerisi elenir. Boşlukla birden fazla yazılır. | `/only cobie ansem` |
| `/only clear` | Beyaz listeyi kapatır (tekrar tüm hesaplar işlenir). | |
| `/replies on` | Yanıt/alıntı (replied/quoted) mesajlarını **da** işler. | |
| `/replies off` | Yanıt/alıntı mesajlarını **atlar** — **varsayılan ve güvenli.** Bir hesabın altına rastgele biri sahte CA yazarsa alınmasın diye. | |

### 3) Alım kuralları — *ne mutlaka gelsin*

Bu kurallar **modları, tavanları ve filtreleri atlar** — koşul tuttuğunda CA her hâlükârda iletilir.

| Komut | Ne işe yarar | Örnek |
|---|---|---|
| `/safe add <handle>` | Bir hesabı **güvenli** işaretler — o hesabın CA'ları **her zaman** iletilir (mod kapalı olsa, tavan aşılsa, filtre olsa bile). En güvendiğin hesaplar için. | `/safe add cobie` |
| `/safe remove <handle>` | Hesabı güvenli listesinden çıkarır. | `/safe remove cobie` |
| `/safe` | Güvenli hesap listesini gösterir. | |
| `/vip <handle> <kelime> <ca>` | **Kelime-tetikli kural:** belirttiğin hesap belirttiğin kelimeyi geçince, mesajdaki CA yerine **senin verdiğin sabit CA'yı** iletir. Önceden bilinen bir lansmanı yakalamak için. | `/vip projexyz launch 0xABC...` |
| `/unvip <handle>` | O hesabın VIP kuralını siler. | |
| `/viplist` | Tüm VIP kurallarını gösterir. | |
| `/retry <ca>` | Bir CA'yı **tekrar iletir** (aynı CA daha önce iletildiyse tekrar-engeli sıfırlanır). | `/retry 0xABC...` |

### 4) Ekstra kaynaklar

Solanize'a **ek olarak**, üye olduğun başka kanalları da sinyal kaynağı yapabilirsin. Onlardan gelen CA'lar da aynı kural ve filtrelerden geçip BASED'e gider.

| Komut | Ne işe yarar | Örnek |
|---|---|---|
| `/addtg <id\|@kanal>` | Bir kanalı kaynak olarak ekler. **O kanala üye olman gerekir.** | `/addtg @benim_alpha_kanalim` |
| `/deltg <id\|@kanal>` | Kaynağı çıkarır. | |
| `/listtg` | Eklediğin ekstra kaynakları listeler. | |

> Solanize her zaman dinlenir. Ekstra kaynaklarda **tüm göndericiler** işlenir (kanalı sen eklediğin için güvendiğin varsayılır).

---

## Öncelik sırası

Bir mesaj geldiğinde bot şu sırayla değerlendirir:

```
VIP kural  →  Safe hesap  →  Hareket Algılandı  →  Normal (allsol / allevm + tavan)
```

- **VIP** ve **Safe** en üsttedir: mod, tavan ve kişisel filtreleri **atlar**.
- **Kişisel filtreler** (block / only / replies) yalnızca normal ve hareket akışına uygulanır — safe/vip bunlardan muaftır.

---

## Bot yönetimi

Kurulum botu **systemd servisi** olarak başlatır (systemd olan sistemlerde):

| İşlem | Komut |
|---|---|
| Durum | `systemctl --user status solanize-bot` |
| Canlı log | `journalctl --user -u solanize-bot -f` |
| Durdur | `systemctl --user stop solanize-bot` |
| Başlat | `systemctl --user start solanize-bot` |
| Güncelle | `bash <(curl -sSL https://raw.githubusercontent.com/solanize/solanize-bot/main/install.sh)` (kodu çeker, yeniden başlatır) |

*systemd yoksa* bot arka planda çalışır, logu `bot.log` dosyasına yazar; durdurmak için `pkill -f solanize_bot.py`.

---

## Güvenlik ve gizlilik

- Bot **senin makinende / sunucunda** çalışır. `api_hash` ve Telegram oturumun **hiçbir yere gönderilmez**, yalnızca sende kalır.
- `config.json` ve oturum dosyaları `.gitignore` ile korunur — asla paylaşılmaz/commit edilmez.
- Kod tamamen **açık kaynaktır**; ne yaptığını satır satır görebilirsin.
- Varsayılan olarak yanıt/alıntı mesajları işlenmez — sahte-çağrı tuzağına karşı koruma.

---

## Sık sorulanlar

**"Solanize grubunda değilsin" diyor.**
Bot yalnızca Solanize üyelerine çalışır. Önce gruba üye ol (yöneticiye başvur), sonra kurulumu tekrar çalıştır.

**Kod istedi ama kabul etmiyor.**
Telegram'dan gelen giriş kodunu **elle yaz**, kopyala-yapıştır yapma.

**BASED botunu sonra mı gireceğim?**
Kurulumda `atla` yazarak geçebilir, sonra `config.json` içindeki `based_bot` alanına ekleyebilirsin.

**Bot çalışıyor mu, nasıl anlarım?**
Kayıtlı Mesajlar'a `/status` yaz — açık/kapalı modları ve ayarları gösterir.
