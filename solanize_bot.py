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
from telethon.utils import get_peer_id

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
# Mesajdaki ilk x.com/<handle> = olayin oznesi olan hesap (kisisel filtre + aksiyon icin)
HANDLE_RE = re.compile(r'(?:twitter|x)\.com/([A-Za-z0-9_]{1,20})', re.IGNORECASE)
# replied/quoted/liked/unfollowed = OLUMSUZ/riskli aksiyon (rastgele yanit tuzagi) -> atla
BAD_ACTION_RE = re.compile(r'\b(replied|quoted|liked|unfollowed)\b', re.IGNORECASE)
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
    # ── kisisel filtreler (client-side, ana feed'e dokunmaz) ──
    "block_handles": [],   # bu hesaplar iletilmez (orn. elonmusk)
    "block_words": [],     # bu kelimeler gecen mesajlar iletilmez
    "only_handles": [],    # doluysa SADECE bu hesaplar iletilir (beyaz liste)
    "skip_replies": True,  # replied/quoted/liked mesajlari atla (guvenlik)
    # ── alim kurallari ──
    "allsol_cap": 0,       # 0 = tavansiz; >0 ise mcap tavani (bilinmiyorsa iletir)
    "allevm_cap": 0,       # 0 = tavansiz
    "safe_handles": [],    # bu hesaplar HER ZAMAN iletilir (mod+cap+filtre bypass)
    "vip_rules": [],       # [{"handle","keyword","ca"}] handle o kelimeyi gecerse sabit CA'yi ilet
    "extra_sources": [],   # Solanize disinda musterinin ekledigi ekstra kanallar (kendi kaynaklari)
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


def extract_handle(text):
    """Mesajdaki ilk x.com/<handle> = olayin oznesi. Kucuk harf, yoksa None."""
    m = HANDLE_RE.search(text or "")
    return m.group(1).lower() if m else None


def is_bad_action(text):
    """Header (ilk satir) replied/quoted/liked/unfollowed iceriyor mu -> True (atla)."""
    first_line = (text or "").split('\n', 1)[0]
    return bool(BAD_ACTION_RE.search(first_line))


def _norm(h):
    return (h or "").strip().lstrip('@').lower()


def filtered_reason(text):
    """Kisisel filtrelerden biri mesaji engelliyor mu? Engelliyorsa sebep str, degilse None.
    Resurgence (Hareket Algilandi) aksiyon filtresinden MUAF (tweet-aksiyonu degil)."""
    low = (text or "").lower()
    handle = extract_handle(text)
    res = is_resurgence(text)
    # kelime engeli
    for w in config.get("block_words", []):
        if w and w.lower() in low:
            return f"blockword '{w}'"
    # handle engeli
    blocked = {_norm(h) for h in config.get("block_handles", [])}
    if handle and handle in blocked:
        return f"block @{handle}"
    # beyaz liste (doluysa sadece bunlar)
    only = {_norm(h) for h in config.get("only_handles", [])}
    if only and (not handle or handle not in only):
        return f"only-list disi (@{handle or '?'})"
    # aksiyon filtresi (resurgence haric)
    if not res and config.get("skip_replies", True) and is_bad_action(text):
        return "replied/quoted/liked"
    return None


def route_decision(text):
    """Mesaji degerlendirir -> iletilecek [(ca, tag), ...] doner (bos liste = iletme).
    Sira: vip -> safe -> hareket -> normal(allsol/allevm + opsiyonel cap).
    safe/vip; mod, cap ve kisisel filtreleri BYPASS eder."""
    handle = extract_handle(text)
    is_safe = bool(handle and _norm(handle) in {_norm(h) for h in config.get("safe_handles", [])})
    if not is_safe and filtered_reason(text):
        return []
    sol = extract_solana(text)
    evm = extract_evm(text)
    low = (text or "").lower()
    # 1) vip kural: handle + kelime -> sabit CA
    for r in config.get("vip_rules", []):
        if handle and _norm(handle) == _norm(r.get("handle")) and (r.get("keyword") or "").lower() in low and r.get("ca"):
            return [(r["ca"], f"VIP @{handle}")]
    # 3) safe handle -> her zaman
    if is_safe:
        ca = sol or evm
        return [(ca, f"SAFE @{handle}")] if ca else []
    # 4) hareket (mcap tavanli; mcap yoksa atla)
    if is_resurgence(text):
        if not config.get("hareket_on"):
            return []
        mc = parse_mcap(text)
        cap = float(config.get("hareket_cap") or 15000)
        if mc is None or mc > cap:
            return []
        ca = sol or evm
        return [(ca, f"HAREKET(<={int(cap)})")] if ca else []
    # 5) normal: allsol/allevm + opsiyonel mcap tavani (mcap bilinmiyorsa iletir)
    out = []
    mc = parse_mcap(text)
    if sol and config.get("allsol_on"):
        cap = float(config.get("allsol_cap") or 0)
        if not (cap and mc is not None and mc > cap):
            out.append((sol, "SOL"))
    if evm and config.get("allevm_on"):
        cap = float(config.get("allevm_cap") or 0)
        if not (cap and mc is not None and mc > cap):
            out.append((evm, "EVM"))
    return out


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

    client = TelegramClient(os.path.join(HERE, config["session"]), int(config["api_id"]), config["api_hash"])
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

    @client.on(events.NewMessage(incoming=True))
    async def on_source(event):
        if not config.get("master_on"):
            return
        cid = event.chat_id
        if cid == SOURCE_CHAT_ID:
            # resmi Solanize feed: SADECE resmi hesap (gruptaki diğer üye/bot bloklanır)
            if event.sender_id != SOLANIZE_SENDER_ID:
                return
        elif cid not in {int(x) for x in config.get("extra_sources", [])}:
            return  # ne Solanize ne de eklenen kaynak -> yok say
        text = event.message.text or event.message.message or ""
        if not text:
            return
        for ca, tag in route_decision(text):
            if ca:
                await forward_ca(ca, tag)

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
            if arg == 'on':
                config["allsol_cap"] = parse_amount_k(p[2]) if len(p) > 2 else 0
            _c = config.get("allsol_cap") or 0
            reply = f"Solana iletimi: {'AÇIK' if config['allsol_on'] else 'KAPALI'}" + (f" (mcap ≤ {int(_c)})" if config['allsol_on'] and _c else "")
        elif cmd == '/allevm':
            config["allevm_on"] = (arg == 'on')
            if arg == 'on':
                config["allevm_cap"] = parse_amount_k(p[2]) if len(p) > 2 else 0
            _c = config.get("allevm_cap") or 0
            reply = f"EVM iletimi: {'AÇIK' if config['allevm_on'] else 'KAPALI'}" + (f" (mcap ≤ {int(_c)})" if config['allevm_on'] and _c else "")
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
        elif cmd == '/block':
            if not arg:
                reply = "Kullanım: /block <handle>   (örn: /block elonmusk)"; changed = False
            else:
                h = _norm(arg); bl = config.get("block_handles", [])
                if h in [_norm(x) for x in bl]:
                    reply = f"⚠️ Zaten engelli: @{h}"; changed = False
                else:
                    bl.append(h); config["block_handles"] = bl
                    reply = f"⛔ Engellendi: @{h}  (bu hesabın sinyalleri artık iletilmez)\nToplam engelli: {len(bl)}"
        elif cmd == '/unblock':
            h = _norm(arg); bl = [x for x in config.get("block_handles", []) if _norm(x) != h]
            config["block_handles"] = bl
            reply = f"✅ Engel kaldırıldı: @{h}\nKalan: {len(bl)}"
        elif cmd == '/only':
            if arg in ('clear', 'temizle', 'off'):
                config["only_handles"] = []
                reply = "✅ Beyaz liste temizlendi (artık tüm hesaplar işlenir)"
            elif len(p) > 1:
                hs = [_norm(x) for x in p[1:] if _norm(x)]
                config["only_handles"] = hs
                reply = "⭐ Beyaz liste: SADECE bunlar işlenecek:\n" + ", ".join('@' + h for h in hs)
            else:
                only = config.get("only_handles", [])
                reply = ("Kullanım: /only <handle...>  |  /only clear\n"
                         + ("Şu an: " + ", ".join('@' + _norm(h) for h in only) if only else "Şu an: kapalı (hepsi işlenir)"))
                changed = False
        elif cmd == '/blocklist':
            if arg == 'add':
                if len(p) < 3:
                    reply = "Kullanım: /blocklist add <kelime>"; changed = False
                else:
                    w = t.split(None, 2)[2].strip().lower(); bw = config.get("block_words", [])
                    if w in [x.lower() for x in bw]:
                        reply = f"⚠️ Zaten var: '{w}'"; changed = False
                    else:
                        bw.append(w); config["block_words"] = bw
                        reply = f"⛔ Kelime engellendi: '{w}'\nToplam kelime: {len(bw)}"
            elif arg == 'remove':
                w = t.split(None, 2)[2].strip().lower() if len(p) > 2 else ""
                bw = [x for x in config.get("block_words", []) if x.lower() != w]
                config["block_words"] = bw
                reply = f"✅ Kelime kaldırıldı: '{w}'\nKalan kelime: {len(bw)}"
            else:
                bl = config.get("block_handles", []); bw = config.get("block_words", []); only = config.get("only_handles", [])
                reply = ("🧹 FİLTRELER\n"
                         "⛔ Engelli hesaplar: " + (", ".join('@' + _norm(h) for h in bl) if bl else "yok") + "\n"
                         "⛔ Engelli kelimeler: " + (", ".join(bw) if bw else "yok") + "\n"
                         "⭐ Beyaz liste: " + (", ".join('@' + _norm(h) for h in only) if only else "kapalı") + "\n"
                         f"↩️ Yanıt/alıntı atla: {'AÇIK (güvenli)' if config.get('skip_replies', True) else 'KAPALI (riskli)'}\n\n"
                         "Kelime ekle/çıkar: /blocklist add <kelime>  |  /blocklist remove <kelime>")
                changed = False
        elif cmd == '/replies':
            if arg not in ('on', 'off'):
                reply = "Kullanım: /replies on (yanıtları da al) | /replies off (atla, güvenli)"; changed = False
            else:
                config["skip_replies"] = (arg == 'off')
                reply = f"Yanıt/alıntı mesajları: {'İŞLENİYOR (riskli)' if arg == 'on' else 'ATLANIYOR (güvenli)'}"
        elif cmd == '/safe':
            if arg == 'add':
                if len(p) < 3:
                    reply = "Kullanım: /safe add <handle>"; changed = False
                else:
                    h = _norm(p[2]); sh = config.get("safe_handles", [])
                    if h in [_norm(x) for x in sh]:
                        reply = f"⚠️ Zaten safe: @{h}"; changed = False
                    else:
                        sh.append(h); config["safe_handles"] = sh
                        reply = f"⭐ Safe eklendi: @{h}  (bu hesap HER ZAMAN iletilir — mod/tavan/filtre bypass)\nToplam: {len(sh)}"
            elif arg == 'remove':
                h = _norm(p[2]) if len(p) > 2 else ""
                sh = [x for x in config.get("safe_handles", []) if _norm(x) != h]
                config["safe_handles"] = sh
                reply = f"✅ Safe kaldırıldı: @{h}\nKalan: {len(sh)}"
            else:
                sh = config.get("safe_handles", [])
                reply = ("⭐ Safe hesaplar (her zaman iletilir):\n" + (", ".join('@' + _norm(x) for x in sh) if sh else "yok")
                         + "\n\nEkle/çıkar: /safe add <handle>  |  /safe remove <handle>")
                changed = False
        elif cmd == '/vip':
            if len(p) < 4:
                reply = "Kullanım: /vip <handle> <kelime> <ca>\n(o handle o kelimeyi geçince sabit CA iletilir)"; changed = False
            else:
                vh = _norm(p[1]); vk = p[2].lower(); vca = p[3].strip()
                vr = [r for r in config.get("vip_rules", []) if _norm(r.get("handle")) != vh]
                vr.append({"handle": vh, "keyword": vk, "ca": vca}); config["vip_rules"] = vr
                reply = f"🎯 VIP kural: @{vh} + '{vk}' → {vca}\nToplam: {len(vr)}"
        elif cmd == '/unvip':
            vh = _norm(arg); vr = [r for r in config.get("vip_rules", []) if _norm(r.get("handle")) != vh]
            config["vip_rules"] = vr
            reply = f"✅ VIP kural silindi: @{vh}\nKalan: {len(vr)}"
        elif cmd == '/viplist':
            vr = config.get("vip_rules", [])
            reply = "🎯 VIP kurallar:\n" + ("\n".join(f"@{r['handle']} + '{r['keyword']}' → {r['ca']}" for r in vr) if vr else "yok")
            changed = False
        elif cmd == '/retry':
            if len(p) > 1:
                rca = p[1].strip(); _seen.discard(rca)
                await forward_ca(rca, "RETRY")
                reply = f"🔁 Tekrar iletildi: {rca}"; changed = False
            else:
                reply = "Kullanım: /retry <ca>"; changed = False
        elif cmd == '/addtg':
            if not arg:
                reply = "Kullanım: /addtg <kanal_id veya @kullaniciadi>  (ÜYE olduğun kanal)"; changed = False
            else:
                raw = p[1].strip()
                try:
                    cid = int(raw) if raw.lstrip('-').isdigit() else get_peer_id(await client.get_entity(raw))
                    ex = config.get("extra_sources", [])
                    if cid in ex:
                        reply = f"⚠️ Zaten ekli: {cid}"
                    else:
                        ex.append(cid); config["extra_sources"] = ex; save_config(config)
                        reply = f"📡 Kaynak eklendi: {cid}\nToplam ek kaynak: {len(ex)}\n(Bu kanaldaki sinyaller de kurallarından geçip BASED'e iletilir)"
                except Exception as e:
                    reply = f"❌ Eklenemedi: {e}\n(Bu kanala ÜYE olmalısın)"
                changed = False
        elif cmd == '/deltg':
            try:
                raw = p[1].strip()
                cid = int(raw) if raw.lstrip('-').isdigit() else get_peer_id(await client.get_entity(raw))
            except Exception:
                cid = None
            ex = [x for x in config.get("extra_sources", []) if x != cid]
            config["extra_sources"] = ex; save_config(config)
            reply = f"✅ Kaynak silindi.\nKalan ek kaynak: {len(ex)}"; changed = False
        elif cmd == '/listtg':
            ex = config.get("extra_sources", [])
            reply = f"📡 Ek kaynaklar ({len(ex)}):\n" + ("\n".join(str(x) for x in ex) if ex else "yok") + "\n(Solanize her zaman dinlenir)"
            changed = False
        elif cmd == '/status':
            bl = config.get("block_handles", []); bw = config.get("block_words", []); only = config.get("only_handles", [])
            _sc = config.get("allsol_cap") or 0; _ec = config.get("allevm_cap") or 0
            reply = ("📊 DURUM\n"
                     f"Bot: {'🟢 AÇIK' if config.get('master_on') else '🔴 KAPALI'}\n"
                     f"Solana (allsol): {'AÇIK' if config.get('allsol_on') else 'KAPALI'}" + (f" (≤{int(_sc)})" if config.get('allsol_on') and _sc else "") + "\n"
                     f"EVM (allevm): {'AÇIK' if config.get('allevm_on') else 'KAPALI'}" + (f" (≤{int(_ec)})" if config.get('allevm_on') and _ec else "") + "\n"
                     f"Hareket: {'AÇIK (≤' + str(int(config.get('hareket_cap', 15000))) + ')' if config.get('hareket_on') else 'KAPALI'}\n"
                     f"BASED bot: {config.get('based_bot') or '(ayarlı değil)'}\n"
                     f"— Kurallar — ⭐safe:{len(config.get('safe_handles', []))} 🎯vip:{len(config.get('vip_rules', []))} 📡kaynak:{len(config.get('extra_sources', []))}\n"
                     f"— Filtreler — ⛔hesap:{len(bl)} kelime:{len(bw)} beyaz:{len(only) or '-'} ↩️yanıt-atla:{'✓' if config.get('skip_replies', True) else '✗'}")
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
    print("   /status  /on  /off  /allsol on [cap]  /allevm on [cap]  /hareket on 15k|off")
    print("   Filtre: /block <handle>  /unblock  /blocklist [add|remove <kelime>]  /only <handle...>  /replies on|off")
    print("   Kural : /safe add|remove <handle>  /vip <handle> <kelime> <ca>  /retry <ca>  (+ /viplist)")
    print("   Kaynak: /addtg <id|@kanal>  /deltg  /listtg   (kendi kanallarını da dinlet)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nçıkıldı.")
