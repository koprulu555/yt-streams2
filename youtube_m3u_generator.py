#!/usr/bin/env python3
"""
YouTube M3U Generator - Android App Logic
Android uygulamasının mantığıyla YouTube sayfalarına erişim
"""

import re
import time
import logging
import requests
from urllib.parse import unquote
import os

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('android_style_m3u.log', encoding='utf-8')
    ]
)

class AndroidStyleYouTubeCrawler:
    def __init__(self):
        self.links_file = "links.txt"
        self.output_file = "youtube_streams.m3u"
        
    def read_channels(self):
        """links.txt dosyasını oku"""
        channels = []
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            channel_blocks = content.split('\n\n')
            
            for block in channel_blocks:
                block = block.strip()
                if not block:
                    continue
                    
                channel_data = {}
                lines = block.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('isim='):
                        channel_data['name'] = line.replace('isim=', '').strip()
                    elif line.startswith('içerik='):
                        channel_data['url'] = line.replace('içerik=', '').strip()
                    elif line.startswith('logo='):
                        channel_data['logo'] = line.replace('logo=', '').strip()
                
                if 'name' in channel_data and 'url' in channel_data:
                    if 'logo' not in channel_data:
                        channel_data['logo'] = ''
                    channels.append(channel_data)
            
            logging.info(f"✅ {len(channels)} kanal bulundu")
            return channels
            
        except Exception as e:
            logging.error(f"❌ links.txt okuma hatası: {str(e)}")
            return []

    def fetch_web_content(self, url):
        """Android uygulamasındaki gibi web içeriğini çek"""
        try:
            logging.info(f"   📡 Sayfa çekiliyor: {url}")
            
            # Android tarayıcı benzeri headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            logging.info("   ✅ Sayfa başarıyla çekildi")
            return response.text
            
        except Exception as e:
            logging.error(f"   ❌ Sayfa çekme hatası: {str(e)}")
            return None

    def extract_all_urls(self, html_content):
        """HTML içindeki tüm URL'leri çıkar (Android'deki gibi)"""
        try:
            # Tüm URL'leri bulmak için regex pattern
            url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
            urls = re.findall(url_pattern, html_content)
            
            logging.info(f"   🔍 {len(urls)} URL bulundu")
            return urls
            
        except Exception as e:
            logging.error(f"   ❌ URL çıkarma hatası: {str(e)}")
            return []

    def extract_hls_urls(self, html_content):
        """HTML içinden HLS URL'lerini çıkar"""
        try:
            # Backslash'leri temizle
            clean_html = html_content.replace('\\', '')
            
            hls_urls = []
            
            # Pattern 1: hlsManifestUrl
            pattern1 = r'"hlsManifestUrl":"(https:[^"]+?m3u8[^"]*?)"'
            matches1 = re.findall(pattern1, clean_html)
            hls_urls.extend(matches1)
            
            # Pattern 2: URL içinde m3u8
            pattern2 = r'"url":"(https:[^"]*?m3u8[^"]*?)"'
            matches2 = re.findall(pattern2, clean_html)
            hls_urls.extend(matches2)
            
            # Pattern 3: Doğrudan m3u8 URL'leri
            pattern3 = r'https://[^"\'\s<>]*?googlevideo\.com[^"\'\s<>]*?m3u8[^"\'\s<>]*'
            matches3 = re.findall(pattern3, clean_html)
            hls_urls.extend(matches3)
            
            # Pattern 4: ytInitialPlayerResponse
            pattern4 = r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;'
            matches4 = re.findall(pattern4, clean_html, re.DOTALL)
            for match in matches4:
                hls_from_json = self.extract_hls_from_json(match)
                if hls_from_json:
                    hls_urls.append(hls_from_json)
            
            # Pattern 5: streamingData
            pattern5 = r'"streamingData":\s*({[^}]+"hlsManifestUrl"[^}]+})'
            matches5 = re.findall(pattern5, clean_html)
            for match in matches5:
                if '"hlsManifestUrl":"' in match:
                    url_match = re.search(r'"hlsManifestUrl":"(https:[^"]+?m3u8[^"]*?)"', match)
                    if url_match:
                        hls_urls.append(url_match.group(1))
            
            # Benzersiz URL'leri döndür
            unique_urls = list(set(hls_urls))
            logging.info(f"   🎯 {len(unique_urls)} HLS URL bulundu")
            
            return unique_urls
            
        except Exception as e:
            logging.error(f"   ❌ HLS URL çıkarma hatası: {str(e)}")
            return []

    def extract_hls_from_json(self, json_str):
        """JSON verisinden HLS URL'sini çıkar"""
        try:
            import json
            # JSON'u temizle
            json_str = re.sub(r'/\*.*?\*/', '', json_str)
            data = json.loads(json_str)
            
            # streamingData içinde ara
            if 'streamingData' in data:
                streaming_data = data['streamingData']
                
                if 'hlsManifestUrl' in streaming_data:
                    hls_url = streaming_data['hlsManifestUrl']
                    if '.m3u8' in hls_url:
                        return hls_url.replace('\\u0026', '&')
                
                # adaptiveFormats içinde ara
                if 'adaptiveFormats' in streaming_data:
                    for fmt in streaming_data['adaptiveFormats']:
                        if 'url' in fmt and '.m3u8' in fmt['url'] and 'googlevideo.com' in fmt['url']:
                            return fmt['url']
            
            return None
            
        except Exception as e:
            logging.error(f"   ❌ JSON parse hatası: {str(e)}")
            return None

    def find_best_hls_url(self, urls):
        """En iyi HLS URL'sini seç"""
        if not urls:
            return None
            
        # Öncelikle en uzun URL'yi seç (genellikle daha fazla parametre = daha kaliteli)
        best_url = max(urls, key=len)
        
        # URL'yi temizle
        best_url = best_url.replace('\\u0026', '&').replace('\\/', '/')
        
        return best_url

    def get_hls_url_android_style(self, url, channel_name):
        """Android uygulaması mantığıyla HLS URL'sini al"""
        logging.info(f"   🌐 Kanal: {channel_name}")
        logging.info(f"   🔗 URL: {url}")
        
        # Desktop URL'ye çevir
        desktop_url = url.replace('//m.youtube.com/', '//www.youtube.com/')
        desktop_url = desktop_url.replace('//youtube.com/', '//www.youtube.com/')
        
        # Web içeriğini çek
        html_content = self.fetch_web_content(desktop_url)
        
        if not html_content:
            return None
        
        # Debug için kaydet
        with open(f"debug_{channel_name.replace(' ', '_')}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        logging.info(f"   💾 Sayfa kaynağı debug_{channel_name.replace(' ', '_')}.html'ye kaydedildi")
        
        # Tüm URL'leri çıkar
        all_urls = self.extract_all_urls(html_content)
        
        # HLS URL'lerini çıkar
        hls_urls = self.extract_hls_urls(html_content)
        
        if hls_urls:
            # En iyi HLS URL'sini seç
            best_hls_url = self.find_best_hls_url(hls_urls)
            if best_hls_url:
                logging.info(f"   ✅ HLS URL bulundu: {best_hls_url[:80]}...")
                return best_hls_url
        
        logging.info("   ❌ HLS URL bulunamadı")
        return None

    def create_m3u_header(self):
        """M3U dosyası header'ını oluştur"""
        return f"""#EXTM3U
# Title: YouTube Live Streams
# Description: Android uygulama mantığıyla oluşturulmuş YouTube canlı yayın listesi
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Method: Android Style Web Crawler

"""

    def write_m3u_file(self, streams):
        """M3U dosyasını yaz"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(self.create_m3u_header())
                
                successful_streams = [s for s in streams if s['hls_url']]
                
                for stream in successful_streams:
                    if stream.get('logo'):
                        f.write(f"#EXTINF:-1 tvg-id=\"{stream['name']}\" tvg-name=\"{stream['name']}\" tvg-logo=\"{stream['logo']}\" group-title=\"YouTube\",{stream['name']}\n")
                    else:
                        f.write(f"#EXTINF:-1 tvg-id=\"{stream['name']}\" tvg-name=\"{stream['name']}\" group-title=\"YouTube\",{stream['name']}\n")
                    f.write(f"{stream['hls_url']}\n\n")
            
            logging.info(f"✅ M3U dosyası oluşturuldu: {self.output_file} ({len(successful_streams)} kanal)")
            return True
            
        except Exception as e:
            logging.error(f"❌ M3U dosyası yazma hatası: {str(e)}")
            return False

    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("=" * 60)
        print("🚀 YOUTUBE M3U GENERATOR (ANDROID STYLE) - BAŞLIYOR")
        print("=" * 60)
        
        try:
            # Kanal listesini oku
            channels = self.read_channels()
            if not channels:
                logging.error("❌ Hiç kanal bulunamadı!")
                return False

            print("=" * 60)
            print("📡 HLS URL'LERİ ALINIYOR (ANDROID STYLE)...")
            print("=" * 60)

            streams = []
            success_count = 0

            for i, channel in enumerate(channels, 1):
                print(f"\n🎬 KANAL {i}/{len(channels)}: {channel['name']}")
                print(f"   🔗 URL: {channel['url']}")
                if channel.get('logo'):
                    print(f"   🖼️ LOGO: {channel['logo'][:50]}...")
                
                hls_url = self.get_hls_url_android_style(channel['url'], channel['name'])
                
                if hls_url:
                    streams.append({
                        'name': channel['name'],
                        'url': channel['url'],
                        'logo': channel.get('logo', ''),
                        'hls_url': hls_url
                    })
                    success_count += 1
                    print(f"   ✅ BAŞARILI - HLS URL alındı")
                else:
                    streams.append({
                        'name': channel['name'],
                        'url': channel['url'],
                        'logo': channel.get('logo', ''),
                        'hls_url': None
                    })
                    print(f"   ❌ BAŞARISIZ - HLS URL alınamadı")
                
                # Kısa bekleme
                if i < len(channels):
                    time.sleep(2)

            # M3U dosyasını oluştur
            if streams:
                self.write_m3u_file(streams)
                
                # İstatistikleri göster
                print("\n" + "=" * 60)
                print("📊 İSTATİSTİKLER")
                print("=" * 60)
                print(f"📺 Toplam Kanal: {len(channels)}")
                print(f"✅ Başarılı: {success_count}")
                print(f"❌ Başarısız: {len(channels) - success_count}")
                print(f"📈 Başarı Oranı: {(success_count/len(channels))*100:.1f}%")
                print(f"💾 Çıktı Dosyası: {self.output_file}")
                
            return success_count > 0

        except Exception as e:
            logging.error(f"❌ Beklenmeyen hata: {str(e)}")
            return False

def main():
    """Ana fonksiyon"""
    crawler = AndroidStyleYouTubeCrawler()
    success = crawler.run()
    
    if success:
        print("\n🎉 M3U dosyası başarıyla oluşturuldu!")
    else:
        print("\n💥 M3U dosyası oluşturulamadı!")
        exit(1)

if __name__ == "__main__":
    main()
