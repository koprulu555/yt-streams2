#!/usr/bin/env python3
"""
YouTube M3U Generator - Advanced Anti-Bot Version
"""

import re
import time
import random
import logging
import json
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import requests
from urllib.parse import unquote, urlparse
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
        self.timeout = 45
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
    def setup_driver(self):
        """Advanced Chrome driver kurulumu - anti-bot bypass"""
        try:
            chrome_options = Options()
            
            # Headless mod
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Anti-detection ayarları
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Random user agent
            user_agent = random.choice(self.user_agents)
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Diğer gizlilik ayarları
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-translate")
            
            # Language and region
            chrome_options.add_argument("--accept-lang=tr-TR,tr;q=0.9,en;q=0.8")
            chrome_options.add_argument("--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
            
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
            
            # WebDriver özelliklerini gizle
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en']})")
            
            logging.info("✅ ChromeDriver başarıyla başlatıldı (Anti-Bot Mode)")
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

    def human_like_delay(self):
        """İnsan benzeri rastgele bekleme"""
        delay = random.uniform(1.5, 4.5)
        time.sleep(delay)

    def get_hls_url_selenium(self, url, channel_name):
        """Gelişmiş Selenium ile HLS URL'sini al - anti-bot bypass"""
        try:
            logging.info(f"   🌐 Sayfa açılıyor: {url}")
            
            # Desktop YouTube URL'sine çevir
            desktop_url = url.replace('//m.youtube.com/', '//www.youtube.com/')
            desktop_url = desktop_url.replace('//youtube.com/', '://www.youtube.com/')
            
            # Sayfayı aç
            self.driver.get(desktop_url)
            
            # Sayfanın yüklenmesini bekle
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # İnsan benzeri davranış
            self.human_like_delay()
            
            # Sayfayı biraz kaydır
            self.driver.execute_script("window.scrollTo(0, 300);")
            self.human_like_delay()
            
            # Video player'ın yüklenmesini bekle
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                logging.info("   ✅ Video element bulundu")
            except TimeoutException:
                logging.warning("   ⚠️ Video element zaman aşımı, devam ediliyor...")
            
            # Daha uzun süre bekle (JavaScript ve video player'ın yüklenmesi için)
            time.sleep(8)
            
            # Sayfa kaynağını al
            page_source = self.driver.page_source
            
            # Debug için sayfa kaynağını kaydet
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            logging.info("   📄 Sayfa kaynağı debug_page.html'ye kaydedildi")
            
            # HLS URL'sini bulmak için gelişmiş pattern'ler
            hls_url = self.extract_hls_advanced(page_source)
            
            if hls_url:
                logging.info(f"   ✅ HLS URL bulundu: {hls_url[:80]}...")
                return hls_url
            
            # Alternatif yöntem: Network logging
            hls_url = self.extract_from_network_logs()
            if hls_url:
                logging.info(f"   ✅ HLS URL (network) bulundu: {hls_url[:80]}...")
                return hls_url
                
            # Son çare: JavaScript execution
            hls_url = self.extract_via_javascript()
            if hls_url:
                logging.info(f"   ✅ HLS URL (JavaScript) bulundu: {hls_url[:80]}...")
                return hls_url
            
            logging.warning("   ❌ HLS URL bulunamadı")
            return None
            
        except TimeoutException:
            logging.error("   ⏰ Sayfa yükleme zaman aşımına uğradı")
            return None
        except Exception as e:
            logging.error(f"   ❌ HLS URL alma hatası: {str(e)}")
            return None

    def extract_hls_advanced(self, page_source):
        """Gelişmiş HLS URL extraction"""
        try:
            # Pattern 1: hlsManifestUrl direkt arama
            patterns = [
                r'"hlsManifestUrl":"(https:[^"]+?m3u8[^"]*?)"',
                r'"url":"(https:[^"]*?m3u8[^"]*?)"',
                r'hlsManifestUrl["\']?\s*:\s*["\'](https:[^"\']+?m3u8[^"\']*?)["\']',
                r'https://[^"\'\s<>]*?googlevideo.com[^"\'\s<>]*?m3u8[^"\'\s<>]*',
            ]
            
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        hls_url = match.replace('\\u0026', '&').replace('\\/', '/')
                        if 'googlevideo.com' in hls_url and '.m3u8' in hls_url:
                            # URL'yi temizle
                            hls_url = re.sub(r'\\[xu][0-9a-fA-F]{2,4}', '', hls_url)
                            return hls_url
                except Exception as e:
                    continue
            
            # Pattern 2: JSON verilerinde arama
            json_patterns = [
                r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;',
                r'window\["ytInitialPlayerResponse"\]\s*=\s*({.+?})\s*;',
                r'var ytInitialPlayerResponse\s*=\s*({.+?})\s*;',
            ]
            
            for pattern in json_patterns:
                try:
                    matches = re.findall(pattern, page_source, re.DOTALL)
                    for match in matches:
                        hls_url = self.extract_from_json(match)
                        if hls_url:
                            return hls_url
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logging.error(f"   ❌ Advanced extraction hatası: {str(e)}")
            return None

    def extract_from_json(self, json_str):
        """JSON verisinden HLS URL'sini çıkar"""
        try:
            # JSON'u temizle
            json_str = re.sub(r'/\*.*?\*/', '', json_str)  # Yorumları temizle
            data = json.loads(json_str)
            
            # streamingData içinde ara
            streaming_data = data.get('streamingData', {})
            hls_url = streaming_data.get('hlsManifestUrl', '')
            if hls_url and '.m3u8' in hls_url:
                return hls_url.replace('\\u0026', '&')
            
            # adaptiveFormats içinde ara
            adaptive_formats = streaming_data.get('adaptiveFormats', [])
            for fmt in adaptive_formats:
                url = fmt.get('url', '')
                if '.m3u8' in url and 'googlevideo.com' in url:
                    return url
            
            return None
            
        except Exception:
            return None

    def extract_from_network_logs(self):
        """Network loglarından HLS URL'sini bul"""
        try:
            # Performance loglarını al
            logs = self.driver.get_log('performance')
            
            for entry in logs:
                try:
                    message = json.loads(entry['message'])
                    message_type = message.get('message', {}).get('method', '')
                    
                    if message_type in ['Network.responseReceived', 'Network.requestWillBeSent']:
                        request_url = message['message']['params'].get('request', {}).get('url', '') or \
                                    message['message']['params'].get('response', {}).get('url', '')
                        
                        if '.m3u8' in request_url and 'googlevideo.com' in request_url:
                            return request_url
                            
                except Exception:
                    continue
                    
            return None
            
        except Exception:
            return None

    def extract_via_javascript(self):
        """JavaScript execution ile HLS URL'sini bul"""
        try:
            js_scripts = [
                """
                // YouTube player objesini bul
                var players = document.getElementsByTagName('video');
                for (var i = 0; i < players.length; i++) {
                    if (players[i].src && players[i].src.includes('m3u8')) {
                        return players[i].src;
                    }
                }
                return null;
                """,
                """
                // YouTube iframe API
                var iframe = document.querySelector('iframe');
                if (iframe && iframe.src) {
                    return iframe.src;
                }
                return null;
                """,
                """
                // Network requests'te m3u8 ara
                return window.performance.getEntries()
                    .map(entry => entry.name)
                    .find(name => name.includes('m3u8') && name.includes('googlevideo.com'));
                """
            ]
            
            for js in js_scripts:
                try:
                    result = self.driver.execute_script(js)
                    if result and '.m3u8' in result:
                        return result
                except Exception:
                    continue
                    
            return None
            
        except Exception:
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
        print("🚀 YOUTUBE M3U GENERATOR (ADVANCED ANTI-BOT) - BAŞLIYOR")
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
            print("📡 HLS URL'LERİ ALINIYOR (ADVANCED ANTI-BOT)...")
            print("=" * 60)

            streams = []
            success_count = 0

            for i, channel in enumerate(self.channels, 1):
                print(f"\n🎬 KANAL {i}/{len(self.channels)}: {channel['name']}")
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
