#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import re
import time
import os

def links_dosyasini_oku():
    """links.txt dosyasını oku ve kanal listesini döndür"""
    kanallar = []
    
    try:
        with open('links.txt', 'r', encoding='utf-8') as dosya:
            icerik = dosya.read()
            print("✅ links.txt dosyası okundu")
    except FileNotFoundError:
        print("❌ links.txt dosyası bulunamadı!")
        return kanallar
    
    satirlar = icerik.split('\n')
    mevcut_kanal = {}
    
    for satir in satirlar:
        satir = satir.strip()
        if not satir:
            if mevcut_kanal:
                kanallar.append(mevcut_kanal)
                mevcut_kanal = {}
            continue
        
        if satir.startswith('isim='):
            mevcut_kanal['isim'] = satir[5:]
        elif satir.startswith('içerik='):
            mevcut_kanal['icerik'] = satir[7:]
        elif satir.startswith('logo='):
            mevcut_kanal['logo'] = satir[5:]
    
    if mevcut_kanal:
        kanallar.append(mevcut_kanal)
    
    print(f"📊 {len(kanallar)} kanal bulundu")
    return kanallar

def setup_selenium():
    """Selenium driver'ını kur"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Chrome'u başlat
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_hls_url_selenium(driver, youtube_url):
    """Selenium ile HLS URL'sini al"""
    try:
        print(f"   🌐 Sayfa açılıyor: {youtube_url}")
        driver.get(youtube_url)
        
        # Sayfanın yüklenmesini bekle (30 saniye)
        WebDriverWait(driver, 30).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # Sayfa kaynağını al
        page_source = driver.page_source
        
        # HLS URL'sini regex ile ara
        patterns = [
            r'"hlsManifestUrl":"(https:[^"]+m3u8[^"]*)"',
            r'"hlsManifestUrl":"(https:[^"]+)"',
            r'hlsManifestUrl["\']?\s*:\s*["\'](https:[^"\']+m3u8[^"\']*)["\']',
            r'"url":"(https:[^"]+m3u8[^"]*)"',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                for match in matches:
                    hls_url = match.replace('\\u0026', '&').replace('\\/', '/').replace('\\\\u0026', '&')
                    if 'm3u8' in hls_url and 'googlevideo.com' in hls_url:
                        print(f"   ✅ HLS URL bulundu")
                        return hls_url
        
        print("   ❌ HLS URL bulunamadı")
        return None
        
    except TimeoutException:
        print("   ❌ Sayfa zaman aşımına uğradı")
        return None
    except Exception as e:
        print(f"   ❌ Selenium hatası: {str(e)}")
        return None

def m3u_dosyasi_olustur(kanallar):
    """M3U dosyasını oluştur"""
    m3u_icerik = "#EXTM3U\n"
    basarili_kanallar = 0
    
    for kanal in kanallar:
        if 'hls_url' in kanal and kanal['hls_url']:
            m3u_icerik += f'#EXTINF:-1 tvg-id="{kanal["isim"]}" tvg-name="{kanal["isim"]}" tvg-logo="{kanal["logo"]}" group-title="YouTube",{kanal["isim"]}\n'
            m3u_icerik += f'{kanal["hls_url"]}\n'
            basarili_kanallar += 1
    
    try:
        with open('youtube.m3u', 'w', encoding='utf-8') as dosya:
            dosya.write(m3u_icerik)
        print(f"✅ youtube.m3u dosyası oluşturuldu ({basarili_kanallar} kanal)")
        return basarili_kanallar
    except Exception as e:
        print(f"❌ M3U dosyası yazılamadı: {e}")
        return 0

def main():
    print("=" * 60)
    print("🚀 YOUTUBE M3U GENERATOR (SELENIUM) - BAŞLIYOR")
    print("=" * 60)
    
    # 1. links.txt dosyasını oku
    kanallar = links_dosyasini_oku()
    if not kanallar:
        print("❌ İşlem iptal edildi: Kanallar bulunamadı")
        return
    
    # 2. Selenium driver'ını başlat
    print("🖥️ Selenium driver başlatılıyor...")
    driver = setup_selenium()
    
    try:
        # 3. Her kanal için HLS URL'sini al
        print("\n" + "=" * 60)
        print("📡 HLS URL'LERİ ALINIYOR (SELENIUM)...")
        print("=" * 60)
        
        for kanal in kanallar:
            print(f"\n🎬 KANAL: {kanal['isim']}")
            print(f"   🔗 URL: {kanal['icerik']}")
            
            hls_url = get_hls_url_selenium(driver, kanal['icerik'])
            
            if hls_url:
                kanal['hls_url'] = hls_url
                print(f"   ✅ BAŞARILI - HLS URL alındı")
            else:
                print(f"   ❌ BAŞARISIZ - HLS URL alınamadı")
            
            # Bekleme
            time.sleep(5)
        
        # 4. M3U dosyasını oluştur
        print("\n" + "=" * 60)
        print("📝 M3U DOSYASI OLUŞTURULUYOR...")
        print("=" * 60)
        
        basarili_sayisi = m3u_dosyasi_olustur(kanallar)
        
        # 5. Sonuçları göster
        print("\n" + "=" * 60)
        print("🎉 SONUÇLAR")
        print("=" * 60)
        print(f"📊 Toplam Kanal: {len(kanallar)}")
        print(f"✅ Başarılı: {basarili_sayisi}")
        print(f"❌ Başarısız: {len(kanallar) - basarili_sayisi}")

    finally:
        # Driver'ı kapat
        driver.quit()
        print("🖥️ Selenium driver kapatıldı")

if __name__ == "__main__":
    main()
