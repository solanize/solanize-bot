#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SOLANIZE BOT kurulum sihirbazı — TEK AKIŞ:
api bilgileri -> Telegram girişi (telefon+kod) -> doğrulama (grup+based) -> kayıt.
Her adımda durup cevabını bekler, her adımı doğrular. Sonunda giriş yapılmış + hazır."""
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(HERE, "config.json")
SESSION_PATH = os.path.join(HERE, "solanize")   # -> solanize.session
SOURCE_CHAT_ID = -1003945790481                 # Solanize grubu

G = "\033[32m"; BG = "\033[1;92m"; DIM = "\033[2;32m"; Y = "\033[33m"; RED = "\033[31m"; R = "\033[0m"
CLR = "\033[2J\033[H"

LOGO = r"""
   ____   ___   _        _    _   _ ___ _____ _____
  / ___| / _ \ | |      / \  | \ | |_ _|__  /| ____|
  \___ \| | | || |     / _ \ |  \| || |  / / |  _|
   ___) | |_| || |___ / ___ \| |\  || | / /_ | |___
  |____/ \___/ |_____/_/   \_\_| \_|___/____||_____|
"""


def matrix_intro(duration=2.0):
    cols = 64
    chars = "アァカサタナハマヤラ0123456789ABCDEF$#@%&*+=/<>"
    try:
        sys.stdout.write(CLR)
        t0 = time.time()
        while time.time() - t0 < duration:
            line = "".join((G + random.choice(chars) + R) if random.random() < 0.45 else " " for _ in range(cols))
            sys.stdout.write(line + "\n"); sys.stdout.flush(); time.sleep(0.028)
        sys.stdout.write(CLR)
    except Exception:
        pass
    print(BG + LOGO + R)
    print(G + "        >>  SOLANIZE DATA BOT  —  KURULUM  <<\n" + R)


def ask(q, default=None):
    suffix = f" [{default}]" if default not in (None, "") else ""
    while True:
        try:
            v = input(f"  {G}?{R} {q}{suffix}: ").strip()
        except EOFError:
            v = ""
        if v:
            return v
        if default is not None:
            return default


def main():
    matrix_intro()
    print("  Bu bot SENİN Telegram hesabınla çalışır; Solanize verisini KENDİ BASED")
    print("  botuna iletir. Sunucumuz yok, hiçbir bilgi 3. kişiyle paylaşılmaz.\n")

    # ─────────────────────────── ADIM 1: API bilgileri ───────────────────────────
    print(f"{BG}  ADIM 1/4 — Telegram API bilgileri{R}")
    print(f"  {DIM}1. Tarayıcıda aç:  https://my.telegram.org{R}")
    print(f"  {DIM}2. Telegram telefon numaranla giriş yap.{R}")
    print(f"  {DIM}3. 'API development tools' -> herhangi bir isimle uygulama oluştur.{R}")
    print(f"  {DIM}4. Açılan sayfada 'api_id' (kısa sayı) ve 'api_hash' (uzun kod) yazar.{R}\n")
    while True:
        try:
            api_id = int(ask("api_id (sadece sayı)"))
            break
        except ValueError:
            print(f"  {RED}! api_id sadece sayı olmalı.{R}")
    api_hash = ask("api_hash (uzun kod)")

    try:
        from telethon.sync import TelegramClient
        from telethon.errors import ApiIdInvalidError
    except Exception:
        print(f"{RED}  ❌ telethon yüklü değil. Önce:  pip install -r requirements.txt{R}")
        sys.exit(1)

    # ─────────────────────────── ADIM 2: Telegram girişi ─────────────────────────
    print(f"\n{BG}  ADIM 2/4 — Telegram girişi{R}")
    print(f"  {DIM}Telefon numaran ve Telegram'a gelen KODU isteyecek (2FA şifren varsa onu da).{R}")
    print(f"  {Y}⚠️ Telegram'dan gelen kodu ELLE YAZ — KOPYALA-YAPIŞTIR YAPMA!{R}")
    print(f"  {Y}   (Kod yapıştırılırsa Telegram güvenlik gereği onu geçersiz kılabilir.){R}\n")
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    try:
        client.start()   # telefon -> kod -> (2FA) interaktif
    except ApiIdInvalidError:
        print(f"{RED}  ❌ api_id/api_hash yanlış. my.telegram.org'dan tekrar al ve kurulumu yeniden çalıştır.{R}")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}  ❌ Giriş başarısız: {e}{R}")
        sys.exit(1)
    me = client.get_me()
    print(f"  {G}✅ Giriş başarılı: {me.first_name} (@{me.username or '-'}){R}")

    # ─────────────────────────── ADIM 3: Solanize üyelik (ZORUNLU GEÇİT) ─────────
    print(f"\n{BG}  ADIM 3/4 — Solanize üyeliği kontrol ediliyor...{R}")
    in_group = False
    try:
        for d in client.iter_dialogs(limit=500):
            if d.id == SOURCE_CHAT_ID:
                in_group = True
                break
    except Exception:
        pass
    if not in_group:
        try:
            client.get_entity(SOURCE_CHAT_ID)
            in_group = True
        except Exception:
            in_group = False
    if not in_group:
        print(f"\n{RED}  ❌ Solanize grubunda DEĞİLSİN — kurulum durduruldu.{R}")
        print(f"  {Y}   Bu bot yalnızca Solanize üyelerine sinyal verir.{R}")
        print(f"  {Y}   Önce Solanize grubuna ÜYE ol (yöneticiye başvur), sonra kurulumu TEKRAR çalıştır.{R}\n")
        try:
            client.disconnect()
        except Exception:
            pass
        sys.exit(1)
    print(f"  {G}✅ Solanize üyeliği doğrulandı.{R}")

    # ─────────────────────────── ADIM 4: BASED bot ───────────────────────────────
    print(f"\n{BG}  ADIM 4/4 — CA göndereceğin BASED botun{R}")
    print(f"  {DIM}Alım yapacağın BASED botunun @kullanıcıadı (örn: @based_eth_bot).{R}")
    based = ""
    while True:
        based = ask("BASED bot @kullanıcıadı (bilmiyorsan 'atla' yaz)")
        if based.lower() in ("atla", "skip"):
            based = ""
            print(f"  {Y}⚠️ BASED bot atlandı — sonra /status ile config.json'dan ekleyebilirsin.{R}")
            break
        try:
            ent = client.get_entity(based)
            print(f"  {G}✅ BASED bot bulundu: @{getattr(ent, 'username', None) or based}{R}")
            break
        except Exception:
            print(f"  {RED}  ! Bulunamadı. @kullanıcıadı doğru mu? Tekrar dene (ya da 'atla').{R}")
    client.disconnect()

    # ─────────────────────────── kaydet ──────────────────────────────────────────
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            cfg = json.load(open(CONFIG_FILE, encoding="utf-8"))
        except Exception:
            cfg = {}
    cfg.update({
        "api_id": api_id, "api_hash": api_hash, "based_bot": based, "session": "solanize",
        "master_on": True, "allsol_on": True, "allevm_on": True,
        "hareket_on": False, "hareket_cap": 15000,
    })
    json.dump(cfg, open(CONFIG_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"\n{BG}  ✅ KURULUM TAMAM — giriş yapıldı, ayarlar kaydedildi.{R}")
    print(f"  {DIM}Bot birazdan arka planda başlatılacak. Komutlar: Telegram > Kayıtlı Mesajlar{R}")
    print(f"    {G}/status   /block <handle>   /safe add <handle>   /allevm on 50k{R}\n")


if __name__ == "__main__":
    main()
