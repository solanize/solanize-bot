#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SOLANIZE BOT kurulum — adım adım. Matrix girişli."""
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(HERE, "config.json")

G = "\033[32m"      # green
BG = "\033[1;92m"   # bright green
DIM = "\033[2;32m"
R = "\033[0m"
CLR = "\033[2J\033[H"

LOGO = r"""
   ____   ___   _        _    _   _ ___ _____ _____
  / ___| / _ \ | |      / \  | \ | |_ _|__  /| ____|
  \___ \| | | || |     / _ \ |  \| || |  / / |  _|
   ___) | |_| || |___ / ___ \| |\  || | / /_ | |___
  |____/ \___/ |_____/_/   \_\_| \_|___/____||_____|
"""


def matrix_intro(duration=2.4):
    cols = 64
    chars = "アァカサタナハマヤラ0123456789ABCDEF$#@%&*+=/<>"
    try:
        sys.stdout.write(CLR)
        t0 = time.time()
        while time.time() - t0 < duration:
            line = "".join(
                (G + random.choice(chars) + R) if random.random() < 0.45 else " "
                for _ in range(cols)
            )
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
            time.sleep(0.028)
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
    print("  Bu bot SENİN Telegram hesabınla çalışır; Solanize verisini KENDİ")
    print("  BASED botuna iletir. Hiçbir bilgi 3. kişiyle paylaşılmaz, sunucumuz yok.\n")
    print(f"  {DIM}1) https://my.telegram.org -> 'API development tools' -> api_id & api_hash al.{R}")
    print(f"  {DIM}2) Solanize grubuna üye olduğundan emin ol (erişim için yöneticiye yaz).{R}")
    print(f"  {DIM}3) İletim yapacağın kendi BASED botunun kullanıcı adını hazırla.{R}\n")

    cfg = {"session": "solanize", "master_on": True, "allsol_on": True,
           "allevm_on": True, "hareket_on": False, "hareket_cap": 15000}

    while True:
        try:
            cfg["api_id"] = int(ask("Telegram api_id (sayı)"))
            break
        except ValueError:
            print("  ! api_id sadece sayı olmalı.")
    cfg["api_hash"] = ask("Telegram api_hash")
    cfg["based_bot"] = ask("BASED bot kullanıcı adı veya id (örn: @benim_based_bot)")

    json.dump(cfg, open(CONFIG_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"\n{BG}  ✅ Kurulum tamam.{R}\n")
    print("  Başlat:")
    print(f"    {G}python3 solanize_bot.py{R}")
    print("  (İlk açılışta telefon numarası + Telegram doğrulama kodu istenir.)\n")
    print("  Telegram > Kayıtlı Mesajlar üzerinden komutlar:")
    print(f"    {G}/status   /on   /off{R}")
    print(f"    {G}/allsol on|off    /allevm on|off    /hareket on 15k|off{R}\n")


if __name__ == "__main__":
    main()
