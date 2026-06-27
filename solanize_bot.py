#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLANIZE BOT — bağımsız, kişisel veri-iletici.
Solanize veri kaynağından gelen contract adreslerini SENİN BASED botuna iletir.
Tamamen senin Telegram hesabınla (userbot) çalışır. Hiçbir 3. parti anahtar yoktur.
"""
import asyncio
import json
import os
import re

from telethon import TelegramClient, events

# ── Sabit veri kaynağı (Solanize grubu/kanalı). Erişim için ÜYE olman gerekir. ──
SOURCE_CHAT_ID = -1002943870565
# Sadece RESMİ feed hesabının mesajları işlenir; gruptaki başka üye/bot (örn. analiz botları)
# ne paylaşırsa paylaşsın YOK SAYILIR. Böylece sadece güvenilir feed BASED'e gider.
SOLANIZE_SENDER_ID = 7045395519

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(HERE, "config.json")

# ── CA yakalama (regex tabanlı, güvenilir) ──
SOL_RE = re.compile(r'(?:^|[^0-9A-Za-z])#?([1-9A-HJ-NP-Za-km-z]{32,44})(?=$|[^0-9A-Za-z])')
EVM_RE = re.compile(r'0x[a-fA-F0-9]{40}')
FDV_RE = re.compile(r'(?:FDV|MC|MCAP|Market\s*Cap)\s*:?\s*\$?\s*([\d.,]+)\s*([KMB])?', re.IGNORECASE)
BASE_MINTS = {
    "So11111111111111111111111111111111111111112",   # WSOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",   # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",   # USDT
}

DEFAULTS = {
    "api_id": 0, "api_hash": "", "session": "solanize",
    "based_bot": "",          # @kullaniciadi veya numeric id
    "master_on": True,
    "allsol_on": True,
    "allevm_on": True,
    "hareket_on": False,
    "hareket_cap": 15000,
}


def _ca_zone(text):
    i = text.upper().find('CONTRACT')
    return text[i:] if i != -1 else text


def extract_solana(text):
    cas = [c for c in SOL_RE.findall(_ca_zone(text)) if c not in BASE_MINTS]
    if not cas:
        return None
    pump = [c for c in cas if c.endswith('pump')]
    return pump[0] if pump else cas[0]


def extract_evm(text):
    cas = EVM_RE.findall(_ca_zone(text))
    return cas[0] if cas else None


def parse_mcap(text):
    m = FDV_RE.search(text)
    if not m:
        return None
    try:
        num = float(m.group(1).replace(',', ''))
    except Exception:
        return None
    return num * {'K': 1e3, 'M': 1e6, 'B': 1e9}.get((m.group(2) or '').upper(), 1)


def is_resurgence(text):
    low = text.lower()
    return ('hareket algıland' in low) or ('resurging' in low) or ('resurgence' in low)


def parse_amount_k(s):
    s = s.lower().replace('$', '').replace(',', '')
    mult = 1
    if s.endswith('k'):
        mult, s = 1e3, s[:-1]
    elif s.endswith('m'):
        mult, s = 1e6, s[:-1]
    try:
        return float(s) * mult
    except Exception:
        return 15000


def load_config():
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_FILE):
        try:
            cfg.update(json.load(open(CONFIG_FILE, encoding='utf-8')))
        except Exception:
            pass
    return cfg


def save_config(cfg):
    json.dump(cfg, open(CONFIG_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


config = load_config()
_seen = set()


async def main():
    if not config.get("api_id") or not config.get("api_hash"):
        print("❌ Ayar eksik. Önce çalıştır:  python3 setup.py")
        return

    client = TelegramClient(config["session"], int(config["api_id"]), config["api_hash"])
    await client.start()
    me = await client.get_me()
    my_id = me.id
    print(f"✅ SOLANIZE BOT bağlandı: {me.first_name} (@{me.username or '-'})")

    async def forward_ca(ca, tag):
        if ca in _seen:
            return
        _seen.add(ca)
        target = config.get("based_bot")
        if not target:
            return
        try:
            if str(target).lstrip('-').isdigit():
                target = int(target)
            await client.send_message(target, str(ca))
            print(f"➡️  {tag}: {ca}")
        except Exception as e:
            print(f"⚠️ iletim hatası: {e}")

    @client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
    async def on_source(event):
        # SADECE resmi feed hesabı; gruptaki diğer üye/bot (Rick vb.) bloklanır
        if event.sender_id != SOLANIZE_SENDER_ID:
            return
        if not config.get("master_on"):
            return
        text = event.message.text or event.message.message or ""
        if not text:
            return
        if is_resurgence(text):
            if not config.get("hareket_on"):
                return
            mc = parse_mcap(text)
            cap = float(config.get("hareket_cap") or 15000)
            if mc is None or mc > cap:
                return
            ca = extract_solana(text) or extract_evm(text)
            if ca:
                await forward_ca(ca, f"HAREKET(<={int(cap)})")
            return
        sol = extract_solana(text)
        if sol and config.get("allsol_on"):
            await forward_ca(sol, "SOL")
        evm = extract_evm(text)
        if evm and config.get("allevm_on"):
            await forward_ca(evm, "EVM")

    @client.on(events.NewMessage(outgoing=True))
    async def on_cmd(event):
        # Komutlar SADECE Kayıtlı Mesajlar'dan (kendine yazınca)
        if event.chat_id != my_id:
            return
        t = (event.message.text or "").strip()
        if not t.startswith('/'):
            return
        p = t.split()
        cmd = p[0].lower()
        arg = p[1].lower() if len(p) > 1 else ""
        changed = True
        if cmd == '/on':
            config["master_on"] = True
            reply = "🟢 BOT AÇIK"
        elif cmd == '/off':
            config["master_on"] = False
            reply = "🔴 BOT KAPALI"
        elif cmd == '/allsol':
            config["allsol_on"] = (arg == 'on')
            reply = f"Solana iletimi: {'AÇIK' if config['allsol_on'] else 'KAPALI'}"
        elif cmd == '/allevm':
            config["allevm_on"] = (arg == 'on')
            reply = f"EVM iletimi: {'AÇIK' if config['allevm_on'] else 'KAPALI'}"
        elif cmd == '/hareket':
            if arg == 'off':
                config["hareket_on"] = False
                reply = "Hareket Algılandı iletimi: KAPALI"
            elif arg == 'on':
                cap = parse_amount_k(p[2]) if len(p) > 2 else 15000
                config["hareket_on"] = True
                config["hareket_cap"] = cap
                reply = f"Hareket Algılandı iletimi: AÇIK (<= {int(cap)} mcap)"
            else:
                reply = "Kullanım: /hareket on 15k  |  /hareket off"
                changed = False
        elif cmd == '/status':
            reply = ("📊 DURUM\n"
                     f"Bot: {'🟢 AÇIK' if config.get('master_on') else '🔴 KAPALI'}\n"
                     f"Solana (allsol): {'AÇIK' if config.get('allsol_on') else 'KAPALI'}\n"
                     f"EVM (allevm): {'AÇIK' if config.get('allevm_on') else 'KAPALI'}\n"
                     f"Hareket: {'AÇIK (<=' + str(int(config.get('hareket_cap', 15000))) + ')' if config.get('hareket_on') else 'KAPALI'}\n"
                     f"BASED bot: {config.get('based_bot') or '(ayarlı değil)'}")
            changed = False
        else:
            return
        if changed:
            save_config(config)
        try:
            await event.edit(reply)
        except Exception:
            await client.send_message(my_id, reply)

    print("📡 Solanize dinleniyor.")
    print("   Komutlar -> Telegram > Kayıtlı Mesajlar:")
    print("   /status  /on  /off  /allsol on|off  /allevm on|off  /hareket on 15k|off")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nçıkıldı.")
