#!/usr/bin/env python3
"""
Telegram Freespin Kod Scraper -> n8n Webhook -> WhatsApp
Coolify/Docker için optimize edilmiş versiyon
"""

import asyncio
import re
import aiohttp
import os
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto
from datetime import datetime
import base64

# ==================== AYARLAR ====================

# Telegram API
API_ID = int(os.getenv('TELEGRAM_API_ID', '32883187'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '82720ee91180f3bbd9214028a7654348')

# İzlenecek kanal/gruplar
CHANNELS = os.getenv('TELEGRAM_CHANNELS', 'Bonustimee').split(',')

# n8n Webhook URL
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://n8n.nevvmedia.com/webhook/telegram-freespin')

# Session dosyası (volume'da kalıcı olacak)
SESSION_PATH = '/app/session/scraper_session'

# ==================== KOD ÇIKARMA ====================

def extract_codes(text):
    if not text:
        return []
    
    # Önce linkleri temizle (kodlar linkle bitişik gelebiliyor)
    # Örnek: KJMBVFTY2http://dub.run/jojoguncel
    text_clean = re.sub(r'https?://[^\s]+', ' ', text)
    
    patterns = [
        r'\b[A-Z0-9]{8,12}\b',  # KJMBVFTY2 gibi
        r'\b[A-Z]{2,6}[0-9]{2,6}[A-Z0-9]*\b',
    ]
    
    codes = []
    for pattern in patterns:
        matches = re.findall(pattern, text_clean.upper())
        codes.extend(matches)
    
    # Yanlış pozitifleri filtrele
    exclude = {'HTTP', 'HTTPS', 'WWW', 'COM', 'ORG', 'NET', 'TELEGRAM', 'WHATSAPP', 'JOJOGUNCEL', 'RUN'}
    codes = [c for c in codes if c not in exclude and len(c) >= 6]
    
    return list(set(codes))


def extract_platform(text):
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Link bazlı tespit (daha güvenilir)
    if 'jojo' in text_lower or 'dub.run/jojo' in text_lower:
        return 'JOJO'
    
    platforms = ['BAHIGO', 'BETS10', 'MOBILBAHIS', 'TIPOBET', 'BETBOO', 'SUPERBAHIS']
    for p in platforms:
        if p.lower() in text_lower:
            return p
    return None


def extract_link(text):
    if not text:
        return None
    match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
    return match.group() if match else None


# ==================== WEBHOOK GÖNDERME ====================

async def send_to_webhook(code, platform, link, image_base64=None):
    payload = {
        "code": code,
        "platform": platform,
        "link": link,
        "image": image_base64,
        "timestamp": datetime.now().isoformat()
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(WEBHOOK_URL, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    print(f"✅ Webhook gönderildi: {code}")
                    return True
                else:
                    print(f"❌ Webhook hatası: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            return False


# ==================== ANA SCRAPER ====================

async def main():
    print("=" * 50)
    print("🚀 Telegram Freespin Scraper Başlatılıyor...")
    print(f"📡 İzlenen kanallar: {', '.join(CHANNELS)}")
    print(f"🔗 Webhook: {WEBHOOK_URL}")
    print("=" * 50)
    
    # Session klasörünü oluştur
    os.makedirs('/app/session', exist_ok=True)
    
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    
    @client.on(events.NewMessage(chats=CHANNELS))
    async def handler(event):
        message = event.message
        text = message.text or message.message or ""
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 📨 Yeni mesaj!")
        print(f"📝 İçerik: {text[:100]}...")
        
        codes = extract_codes(text)
        
        if codes:
            print(f"🎰 Kod bulundu: {codes[0]}")
            
            platform = extract_platform(text)
            link = extract_link(text)
            
            print(f"📍 Platform: {platform}")
            
            # Resim varsa indir
            image_base64 = None
            if message.media and isinstance(message.media, MessageMediaPhoto):
                print("📸 Resim indiriliyor...")
                image_bytes = await client.download_media(message, bytes)
                image_base64 = base64.b64encode(image_bytes).decode()
            
            # Webhook'a gönder
            await send_to_webhook(codes[0], platform, link, image_base64)
        else:
            print(f"ℹ️ Kod bulunamadı, atlanıyor...")
    
    await client.start()
    print("\n✅ Telegram bağlantısı kuruldu!")
    print("👀 Mesajlar dinleniyor...\n")
    
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
