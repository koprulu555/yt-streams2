#!/usr/bin/env python3
"""
YouTube M3U Generator - Professional Version
Yeni links.txt formatına uygun olarak güncellendi
"""

import re
import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from urllib.parse import unquote
import os

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('m3u_generator.log', encoding='utf-8')
    ]
)

class YouTubeM3UGenerator:
    def __init__(self):
        self.driver = None
        self.links_file = "links.txt"
        self.output_file = "youtube_streams.m3u"
        self.timeout = 30
        
    def setup_driver(self):
        """Chrome driver kurulumu"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # GitHub Actions için Chrome path
            if os.path.exists('/usr/bin/chromium-browser'):
                chrome_options.binary_location = '/usr/bin/chromium-browser'
            
            # ChromeDriver service ayarları
            service = Service(
                executable_path='/usr/bin/chromedriver' 
                if os.path.exists('/usr/bin/chromedriver') 
                else 'chromedriver'
            )
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logging.info("✅ ChromeDriver başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logging.error(f"❌ ChromeDriver başlatma hatası: {str(e)}")
            return False

    def read_channels(self):
        """Yeni formatlı links.txt dosyasını oku ve kanal bilgilerini çıkar"""
        channels = []
        try:
            with open(self.links_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Her kanal bloğunu ayır (boş satırlarla ayrılmış)
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
                
                # Tüm gerekli alanlar varsa kanalı ekle
                if 'name' in channel_data and 'url' in channel_data:
                    # Logo yoksa boş string olarak ayarla
                    if 'logo' not in channel_data:
                        channel_data['logo'] = ''
                    channels.append(channel_data)
            
            logging.info(f"✅ {len(channels)} kanal bulundu")
            return channels
            
        except Exception as e:
            logging.error(f"❌ links.txt okuma hatası: {str(e)}")
            return []

    def get_hls_url_selenium(self, url, channel_name):
        """Selenium ile HLS URL'sini al"""
        try:
            logging.info(f"   🌐 Sayfa açılıyor: {url}")
            
            # Desktop YouTube URL'sine çevir (daha stabil)
            desktop_url = url.replace('//m.youtube.com/', '//www.youtube.com/')
            desktop_url = desktop_url.replace('//youtube.com/', '//www.youtube.com/')
            
            self.driver.get(desktop_url)
            
            # Sayfanın yüklenmesini bekle
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Daha uzun süre bekle (JavaScript ve video player'ın yüklenmesi için)
            time.sleep(8)
            
            # Sayfa kaynağını al
            page_source = self.driver.page_source
            
            # Debug için sayfa kaynağını kaydet
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            logging.info("   📄 Sayfa kaynağı debug_page.html'ye kaydedildi")
            
            # HLS URL'sini bulmak için farklı pattern'ler dene
            hls_url = self.extract_hls_from_page_source(page_source)
            
            if hls_url:
                logging.info(f"   ✅ HLS URL bulundu: {hls_url[:100]}...")
                return hls_url
            else:
                # Alternatif yöntem: JavaScript execution
                hls_url = self.extract_hls_via_javascript()
                if hls_url:
                    logging.info(f"   ✅ HLS URL (JavaScript) bulundu: {hls_url[:100]}...")
                    return hls_url
                
                # Network requests'i dinle
                hls_url = self.extract_hls_from_network_requests()
                if hls_url:
                    logging.info(f"   ✅ HLS URL (network) bulundu: {hls_url[:100]}...")
                    return hls_url
            
            logging.warning("   ❌ HLS URL bulunamadı")
            return None
            
        except TimeoutException:
            logging.error("   ⏰ Sayfa yükleme zaman aşımına uğradı")
            return None
        except Exception as e:
            logging.error(f"   ❌ HLS URL alma hatası: {str(e)}")
            return None

    def extract_hls_from_page_source(self, page_source):
        """Sayfa kaynağından HLS URL'sini çıkar"""
        try:
            # Pattern 1: Doğrudan hlsManifestUrl
            pattern1 = r'"hlsManifestUrl":"(https:[^"]+)"'
            matches = re.findall(pattern1, page_source)
            for match in matches:
                hls_url = match.replace('\\u0026', '&').replace('\\/', '/')
                if '.m3u8' in hls_url and 'googlevideo.com' in hls_url:
                    return hls_url
            
            # Pattern 2: URL içinde m3u8 geçen
            pattern2 = r'"url":"(https:[^"]*m3u8[^"]*)"'
            matches = re.findall(pattern2, page_source)
            for match in matches:
                hls_url = match.replace('\\u0026', '&').replace('\\/', '/')
                if 'googlevideo.com' in hls_url:
                    return hls_url
            
            # Pattern 3: Adaptive formats içinde arama
            pattern3 = r'"adaptiveFormats":\s*(\[.*?\])'
            matches = re.findall(pattern3, page_source, re.DOTALL)
            for match in matches:
                try:
                    formats = json.loads(match)
                    for fmt in formats:
                        url = fmt.get('url', '')
                        if '.m3u8' in url and 'googlevideo.com' in url:
                            return url
                except:
                    continue
            
            # Pattern 4: streamingData içinde arama
            pattern4 = r'"streamingData":\s*({.*?})'
            matches = re.findall(pattern4, page_source, re.DOTALL)
            for match in matches:
                try:
                    streaming_data = json.loads(match)
                    hls_url = streaming_data.get('hlsManifestUrl', '')
                    if hls_url and '.m3u8' in hls_url:
                        return hls_url.replace('\\u0026', '&')
                except:
                    continue
            
            return None
            
        except Exception as e:
            logging.error(f"   ❌ HLS extraction hatası: {str(e)}")
            return None

    def extract_hls_via_javascript(self):
        """JavaScript execution ile HLS URL'sini bul"""
        try:
            # Video element'ini kontrol et
            js_script = """
            var video = document.querySelector('video');
            if (video && video.src) {
                return video.src;
            }
            
            // YouTube player data
            var ytPlayer = document.getElementById('movie_player');
            if (ytPlayer && ytPlayer.getVideoData) {
                var videoData = ytPlayer.getVideoData();
                if (videoData && videoData.dashmpd) {
                    return videoData.dashmpd;
                }
            }
            
            // Network requests'te m3u8 ara
            return null;
            """
            
            result = self.driver.execute_script(js_script)
            if result and '.m3u8' in result:
                return result
                
        except Exception:
            pass
        
        return None

    def extract_hls_from_network_requests(self):
        """Network loglarından HLS URL'sini bul"""
        try:
            performance_logs = self.driver.get_log('performance')
            for entry in performance_logs:
                try:
                    message = json.loads(entry['message'])
                    message_type = message.get('message', {}).get('method', '')
                    
                    if message_type == 'Network.responseReceived':
                        response = message['message']['params']['response']
                        url = response.get('url', '')
                        
                        if '.m3u8' in url and 'googlevideo.com' in url:
                            return url
                            
                except Exception:
                    continue
        except Exception:
            pass
        
        return None

    def create_m3u_header(self):
        """M3U dosyası header'ını oluştur"""
        return f"""#EXTM3U
# Title: YouTube Live Streams
# Description: Otomatik olarak oluşturulmuş YouTube canlı yayın listesi
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Total Channels: {len(self.channels)}

"""

    def write_m3u_file(self, streams):
        """M3U dosyasını yaz - logo bilgilerini de ekle"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(self.create_m3u_header())
                
                for stream in streams:
                    if stream['hls_url']:
                        # Logo varsa tvg-logo parametresini ekle
                        if stream.get('logo'):
                            f.write(f"#EXTINF:-1 tvg-id=\"{stream['name']}\" tvg-name=\"{stream['name']}\" tvg-logo=\"{stream['logo']}\" group-title=\"YouTube\",{stream['name']}\n")
                        else:
                            f.write(f"#EXTINF:-1 tvg-id=\"{stream['name']}\" tvg-name=\"{stream['name']}\" group-title=\"YouTube\",{stream['name']}\n")
                        f.write(f"{stream['hls_url']}\n\n")
            
            logging.info(f"✅ M3U dosyası oluşturuldu: {self.output_file}")
            return True
            
        except Exception as e:
            logging.error(f"❌ M3U dosyası yazma hatası: {str(e)}")
            return False

    def cleanup(self):
        """Driver'ı temizle"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass

    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("=" * 60)
        print("🚀 YOUTUBE M3U GENERATOR (PROFESSIONAL EDITION) - BAŞLIYOR")
        print("=" * 60)
        
        try:
            # Kanal listesini oku
            self.channels = self.read_channels()
            if not self.channels:
                logging.error("❌ Hiç kanal bulunamadı!")
                return False

            # Driver'ı başlat
            if not self.setup_driver():
                return False

            print("=" * 60)
            print("📡 HLS URL'LERİ ALINIYOR (SELENIUM)...")
            print("=" * 60)

            streams = []
            success_count = 0

            for channel in self.channels:
                print(f"\n🎬 KANAL: {channel['name']}")
                print(f"   🔗 URL: {channel['url']}")
                if channel.get('logo'):
                    print(f"   🖼️ LOGO: {channel['logo'][:50]}...")
                
                hls_url = self.get_hls_url_selenium(channel['url'], channel['name'])
                
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

            # M3U dosyasını oluştur
            if streams:
                self.write_m3u_file(streams)
                
                # İstatistikleri göster
                print("\n" + "=" * 60)
                print("📊 İSTATİSTİKLER")
                print("=" * 60)
                print(f"📺 Toplam Kanal: {len(self.channels)}")
                print(f"✅ Başarılı: {success_count}")
                print(f"❌ Başarısız: {len(self.channels) - success_count}")
                print(f"📈 Başarı Oranı: {(success_count/len(self.channels))*100:.1f}%")
                print(f"💾 Çıktı Dosyası: {self.output_file}")
                
            return success_count > 0

        except Exception as e:
            logging.error(f"❌ Beklenmeyen hata: {str(e)}")
            return False
        finally:
            self.cleanup()

def main():
    """Ana fonksiyon"""
    generator = YouTubeM3UGenerator()
    success = generator.run()
    
    if success:
        print("\n🎉 M3U dosyası başarıyla oluşturuldu!")
    else:
        print("\n💥 M3U dosyası oluşturulamadı!")
        exit(1)

if __name__ == "__main__":
    main()
