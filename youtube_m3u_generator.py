#!/usr/bin/env python3
"""
YouTube M3U Generator - Ultimate Anti-Bot Bypass (Fixed)
No API, No Proxy, Pure Selenium Solution
"""

import re
import time
import random
import logging
import json
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
        self.timeout = 60
        
        # Advanced user agents rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        ]
        
    def setup_driver(self):
        """Ultimate Chrome driver setup - Maximum anti-bot protection"""
        try:
            chrome_options = Options()
            
            # Headless mod with new syntax
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Ultimate anti-detection settings
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Random user agent
            user_agent = random.choice(self.user_agents)
            chrome_options.add_argument(f"--user-agent={user_agent}")
            
            # Enhanced privacy and performance settings
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
            
            # Additional stealth arguments
            chrome_options.add_argument("--disable-3d-apis")
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-breakpad")
            chrome_options.add_argument("--disable-crash-reporter")
            chrome_options.add_argument("--disable-device-discovery-notifications")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-features=AudioServiceOutOfProcess")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-back-forward-cache")
            chrome_options.add_argument("--disable-prompt-on-repost")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-site-isolation-trials")
            
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
            
            # Ultimate WebDriver masking
            scripts = [
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
                "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
                "Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en']})",
                "Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8})",
                "Object.defineProperty(navigator, 'deviceMemory', {get: () => 8})",
                "window.chrome = {runtime: {}}",
                """
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                """
            ]
            
            for script in scripts:
                try:
                    self.driver.execute_script(script)
                except:
                    pass
            
            logging.info("✅ Ultimate ChromeDriver başarıyla başlatıldı")
            return True
            
        except Exception as e:
            logging.error(f"❌ ChromeDriver başlatma hatası: {str(e)}")
            return False

    def read_channels(self):
        """links.txt dosyasını oku ve kanal bilgilerini çıkar"""
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

    def human_like_behavior(self):
        """İnsan benzeri davranışlar simüle et"""
        # Rastgele bekleme
        delay = random.uniform(2.0, 6.0)
        time.sleep(delay)
        
        # Rastgele kaydırma
        scroll_amount = random.randint(100, 500)
        self.driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
        
        # Fare hareketi simülasyonu
        try:
            actions = ActionChains(self.driver)
            actions.move_by_offset(random.randint(10, 100), random.randint(10, 100))
            actions.perform()
        except:
            pass

    def wait_for_video_player(self):
        """Video player'ın tam yüklenmesini bekle"""
        try:
            # Video elementini bekle
            WebDriverWait(self.driver, 25).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            logging.info("   ✅ Video element bulundu")
            
            # Daha fazla bekle - video stream'in yüklenmesi için
            time.sleep(10)
            
            # Sayfanın tam yüklenmesini bekle
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            return True
            
        except TimeoutException:
            logging.warning("   ⚠️ Video element zaman aşımı, devam ediliyor...")
            return False

    def extract_hls_from_page_content(self):
        """Sayfa içeriğinden HLS URL'sini çıkar"""
        try:
            page_source = self.driver.page_source
            
            # Debug için kaydet
            with open("debug_page_advanced.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            
            # Gelişmiş regex pattern'leri
            patterns = [
                r'"hlsManifestUrl"\s*:\s*"([^"]+)"',
                r'"url"\s*:\s*"([^"]*\.m3u8[^"]*)"',
                r'hlsManifestUrl["\']?\s*:\s*["\']([^"\']+?)["\']',
                r'https://[^"\'\s<>]*?googlevideo\.com[^"\'\s<>]*?m3u8[^"\'\s<>]*',
                r'\\"hlsManifestUrl\\":\\"([^\\]+)\\"',
                r'\\\\"hlsManifestUrl\\\\":\\\\"([^\\\\]+)\\\\"'
            ]
            
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        hls_url = match.replace('\\u0026', '&').replace('\\/', '/')
                        hls_url = re.sub(r'\\[xu][0-9a-fA-F]{2,4}', '', hls_url)
                        if 'googlevideo.com' in hls_url and '.m3u8' in hls_url:
                            logging.info(f"   ✅ Regex ile HLS bulundu: {hls_url[:80]}...")
                            return hls_url
                except Exception:
                    continue
            
            # JSON verilerinde ara
            json_patterns = [
                r'ytInitialPlayerResponse\s*=\s*({.+?})\s*;',
                r'var ytInitialPlayerResponse\s*=\s*({.+?})\s*;',
                r'window\["ytInitialPlayerResponse"\]\s*=\s*({.+?})\s*;'
            ]
            
            for pattern in json_patterns:
                try:
                    matches = re.findall(pattern, page_source, re.DOTALL)
                    for match in matches:
                        hls_url = self.parse_json_for_hls(match)
                        if hls_url:
                            return hls_url
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logging.error(f"   ❌ Sayfa içerik analiz hatası: {str(e)}")
            return None

    def parse_json_for_hls(self, json_str):
        """JSON verisinden HLS URL'sini çıkar"""
        try:
            # JSON'u temizle
            json_str = re.sub(r'/\*.*?\*/', '', json_str)
            data = json.loads(json_str)
            
            # streamingData içinde ara
            streaming_data = data.get('streamingData', {})
            
            # hlsManifestUrl'yi kontrol et
            hls_url = streaming_data.get('hlsManifestUrl', '')
            if hls_url and '.m3u8' in hls_url:
                return hls_url.replace('\\u0026', '&')
            
            # adaptiveFormats içinde ara
            adaptive_formats = streaming_data.get('adaptiveFormats', [])
            for fmt in adaptive_formats:
                url = fmt.get('url', '')
                if url and '.m3u8' in url and 'googlevideo.com' in url:
                    return url
            
            return None
            
        except Exception:
            return None

    def try_alternative_methods(self, url):
        """Alternatif yöntemler dene"""
        try:
            # JavaScript ile video source'larını kontrol et
            js_scripts = [
                """
                var videos = document.getElementsByTagName('video');
                for (var i = 0; i < videos.length; i++) {
                    if (videos[i].src && videos[i].src.includes('m3u8')) {
                        return videos[i].src;
                    }
                    if (videos[i].currentSrc && videos[i].currentSrc.includes('m3u8')) {
                        return videos[i].currentSrc;
                    }
                }
                return null;
                """,
                """
                // YouTube player objesini kontrol et
                var player = document.getElementById('movie_player');
                if (player && player.getVideoUrl) {
                    var videoUrl = player.getVideoUrl();
                    if (videoUrl && videoUrl.includes('m3u8')) {
                        return videoUrl;
                    }
                }
                return null;
                """,
                """
                // ytInitialPlayerResponse değişkenini doğrudan oku
                if (window.ytInitialPlayerResponse) {
                    return JSON.stringify(window.ytInitialPlayerResponse);
                }
                return null;
                """
            ]
            
            for js in js_scripts:
                try:
                    result = self.driver.execute_script(js)
                    if result and '.m3u8' in result:
                        logging.info(f"   ✅ JavaScript ile HLS bulundu: {result[:80]}...")
                        return result
                    elif result and 'hlsManifestUrl' in result:
                        # Eğer JSON string'i döndüyse, parse et
                        try:
                            data = json.loads(result)
                            streaming_data = data.get('streamingData', {})
                            hls_url = streaming_data.get('hlsManifestUrl', '')
                            if hls_url and '.m3u8' in hls_url:
                                logging.info(f"   ✅ JavaScript JSON'dan HLS bulundu: {hls_url[:80]}...")
                                return hls_url
                        except:
                            pass
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logging.error(f"   ❌ Alternatif metod hatası: {str(e)}")
            return None

    def get_hls_url_ultimate(self, url, channel_name):
        """Ultimate HLS URL alma metodu"""
        try:
            logging.info(f"   🌐 Sayfa açılıyor: {url}")
            
            # Desktop URL'ye çevir
            desktop_url = url.replace('//m.youtube.com/', '//www.youtube.com/')
            desktop_url = desktop_url.replace('//youtube.com/', '//www.youtube.com/')
            
            # Sayfayı aç
            self.driver.get(desktop_url)
            
            # Sayfanın yüklenmesini bekle
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # İnsan benzeri davranış
            self.human_like_behavior()
            
            # Video player'ı bekle
            self.wait_for_video_player()
            
            # Ekstra bekleme süresi
            time.sleep(8)
            
            # 1. Yöntem: Sayfa içeriğinden HLS ara
            hls_url = self.extract_hls_from_page_content()
            if hls_url:
                return hls_url
            
            # 2. Yöntem: Alternatif JavaScript metodları
            hls_url = self.try_alternative_methods(url)
            if hls_url:
                return hls_url
            
            # Son çare: Sayfayı yenile ve tekrar dene
            logging.info("   🔄 Sayfa yenileniyor...")
            self.driver.refresh()
            time.sleep(10)
            
            hls_url = self.extract_hls_from_page_content() or self.try_alternative_methods(url)
            
            if hls_url:
                return hls_url
            
            logging.warning("   ❌ Tüm HLS arama metodları başarısız")
            return None
            
        except Exception as e:
            logging.error(f"   ❌ Ultimate HLS alma hatası: {str(e)}")
            return None

    def create_m3u_header(self):
        """M3U dosyası header'ını oluştur"""
        return f"""#EXTM3U
# Title: YouTube Live Streams
# Description: Tamamen bağımsız YouTube canlı yayın listesi
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Method: Ultimate Anti-Bot Selenium
# Channels: {len(self.channels)}

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
        print("🚀 YOUTUBE M3U GENERATOR (ULTIMATE ANTI-BOT) - BAŞLIYOR")
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
            print("📡 HLS URL'LERİ ALINIYOR (ULTIMATE ANTI-BOT)...")
            print("=" * 60)

            streams = []
            success_count = 0

            for i, channel in enumerate(self.channels, 1):
                print(f"\n🎬 KANAL {i}/{len(self.channels)}: {channel['name']}")
                print(f"   🔗 URL: {channel['url']}")
                if channel.get('logo'):
                    print(f"   🖼️ LOGO: {channel['logo'][:50]}...")
                
                hls_url = self.get_hls_url_ultimate(channel['url'], channel['name'])
                
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
