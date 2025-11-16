#!/usr/bin/env python3
"""
YouTube M3U Generator - Professional yt-dlp Edition
Advanced HLS URL extraction using yt-dlp
"""

import os
import sys
import time
import logging
import json
import subprocess
import re
from urllib.parse import unquote
import requests

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ytdlp_m3u_generator.log', encoding='utf-8')
    ]
)

class YouTubeDLPM3UGenerator:
    def __init__(self):
        self.links_file = "links.txt"
        self.output_file = "youtube_streams.m3u"
        self.yt_dlp_path = "yt-dlp"
        self.timeout = 45
        
    def check_yt_dlp_installation(self):
        """yt-dlp'nin kurulu olup olmadığını kontrol et"""
        try:
            result = subprocess.run([
                self.yt_dlp_path, 
                '--version'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logging.info(f"✅ yt-dlp bulundu: {result.stdout.strip()}")
                return True
            else:
                logging.error("❌ yt-dlp bulunamadı veya çalıştırılamıyor")
                return False
                
        except Exception as e:
            logging.error(f"❌ yt-dlp kontrol hatası: {str(e)}")
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

    def extract_video_id(self, url):
        """URL'den video ID'sini çıkar"""
        try:
            patterns = [
                r'(?:v=|/v/|youtu\.be/|/embed/)([^&?/]+)',
                r'youtube\.com/watch\?v=([^&?/]+)',
                r'youtube\.com/embed/([^&?/]+)',
                r'youtu\.be/([^&?/]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    video_id = video_id.split('&')[0].split('?')[0]
                    return video_id
            return None
            
        except Exception as e:
            logging.error(f"❌ Video ID çıkarma hatası: {e}")
            return None

    def get_hls_url_ytdlp(self, url, channel_name):
        """yt-dlp ile HLS URL'sini al - profesyonel yöntem"""
        try:
            logging.info(f"   🌐 yt-dlp ile analiz: {url}")
            
            # yt-dlp komutunu oluştur
            cmd = [
                self.yt_dlp_path,
                '--dump-json',
                '--no-warnings',
                '--ignore-errors',
                '--geo-bypass',
                '--format', 'best',
                '--youtube-skip-dash-manifest',
                '--no-check-certificate',
                '--socket-timeout', '30',
                '--source-address', '0.0.0.0',
                url
            ]
            
            # Komutu çalıştır
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout,
                check=False
            )
            
            if result.returncode != 0:
                logging.warning(f"   ⚠️ yt-dlp hata kodu: {result.returncode}")
                if result.stderr:
                    logging.warning(f"   ⚠️ yt-dlp stderr: {result.stderr[:200]}")
            
            # JSON çıktısını parse et
            if result.stdout:
                try:
                    video_info = json.loads(result.stdout)
                    return self.extract_hls_from_ytdlp_info(video_info, url)
                except json.JSONDecodeError as e:
                    logging.error(f"   ❌ JSON parse hatası: {e}")
                    return None
            else:
                logging.error("   ❌ yt-dlp çıktı vermedi")
                return None
                
        except subprocess.TimeoutExpired:
            logging.error("   ⏰ yt-dlp zaman aşımına uğradı")
            return None
        except Exception as e:
            logging.error(f"   ❌ yt-dlp işleme hatası: {str(e)}")
            return None

    def extract_hls_from_ytdlp_info(self, video_info, original_url):
        """yt-dlp bilgilerinden HLS URL'sini çıkar"""
        try:
            hls_urls = []
            
            # 1. Doğrudan HLS URL'si
            if video_info.get('url') and '.m3u8' in video_info.get('url', ''):
                hls_urls.append(video_info['url'])
            
            # 2. Formatlar içinde HLS arama
            if 'formats' in video_info:
                for fmt in video_info['formats']:
                    # HLS formatlarını kontrol et
                    if any(keyword in fmt.get('format_note', '').lower() for keyword in ['hls', 'm3u8']):
                        if fmt.get('url') and '.m3u8' in fmt['url']:
                            hls_urls.append(fmt['url'])
                    
                    # Protocol HLS ise
                    if fmt.get('protocol') in ['m3u8', 'm3u8_native']:
                        if fmt.get('url'):
                            hls_urls.append(fmt['url'])
            
            # 3. requested_formats içinde arama
            if 'requested_formats' in video_info:
                for fmt in video_info['requested_formats']:
                    if fmt.get('url') and '.m3u8' in fmt['url']:
                        hls_urls.append(fmt['url'])
            
            # 4. En iyi HLS URL'sini seç
            if hls_urls:
                # En uzun URL'yi seç (genellikle daha fazla parametre = daha kaliteli)
                best_url = max(hls_urls, key=len)
                logging.info(f"   ✅ yt-dlp ile HLS URL bulundu: {best_url[:80]}...")
                return best_url
            
            # 5. Eğer HLS bulunamazsa, normal URL'yi dene
            if video_info.get('url'):
                logging.info(f"   ℹ️  HLS bulunamadı, normal URL kullanılıyor: {video_info['url'][:80]}...")
                return video_info['url']
            
            logging.warning("   ❌ yt-dlp HLS URL bulamadı")
            return None
            
        except Exception as e:
            logging.error(f"   ❌ HLS extraction hatası: {str(e)}")
            return None

    def get_stream_info_ytdlp(self, url, channel_name):
        """yt-dlp ile gelişmiş stream bilgisi al"""
        try:
            logging.info(f"   🔍 Gelişmiş analiz: {channel_name}")
            
            cmd = [
                self.yt_dlp_path,
                '--list-formats',
                '--no-warnings',
                '--ignore-errors',
                url
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                hls_lines = [line for line in lines if 'm3u8' in line.lower()]
                
                if hls_lines:
                    logging.info(f"   📊 Mevcut HLS formatları: {len(hls_lines)}")
                    for line in hls_lines[:3]:  # İlk 3 formatı göster
                        logging.info(f"      📝 {line.strip()}")
                    return True
                else:
                    logging.warning("   ⚠️ HLS formatı bulunamadı")
                    return False
            else:
                logging.error(f"   ❌ Format listeleme hatası: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"   ❌ Stream info hatası: {str(e)}")
            return False

    def create_m3u_header(self):
        """M3U dosyası header'ını oluştur"""
        return f"""#EXTM3U
# Title: YouTube Live Streams (yt-dlp Professional)
# Description: yt-dlp ile profesyonel olarak oluşturulmuş YouTube canlı yayın listesi
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# Method: yt-dlp Advanced Extraction
# Total Channels: {len(self.channels)}

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
        print("🚀 YOUTUBE M3U GENERATOR (PRO YT-DLP EDITION) - BAŞLIYOR")
        print("=" * 60)
        
        try:
            # yt-dlp kontrolü
            if not self.check_yt_dlp_installation():
                logging.error("❌ yt-dlp kurulu değil! Lütfen önce yt-dlp'yi kurun.")
                return False

            # Kanal listesini oku
            self.channels = self.read_channels()
            if not self.channels:
                logging.error("❌ Hiç kanal bulunamadı!")
                return False

            print("=" * 60)
            print("📡 HLS URL'LERİ ALINIYOR (YT-DLP PROFESSIONAL)...")
            print("=" * 60)

            streams = []
            success_count = 0

            for i, channel in enumerate(self.channels, 1):
                print(f"\n🎬 KANAL {i}/{len(self.channels)}: {channel['name']}")
                print(f"   🔗 URL: {channel['url']}")
                if channel.get('logo'):
                    print(f"   🖼️ LOGO: {channel['logo'][:50]}...")
                
                # Önce stream bilgilerini al
                has_streams = self.get_stream_info_ytdlp(channel['url'], channel['name'])
                
                # HLS URL'sini al
                hls_url = self.get_hls_url_ytdlp(channel['url'], channel['name'])
                
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
                
                # Rate limiting
                if i < len(self.channels):
                    time.sleep(2)

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
                print(f"🔧 Kullanılan Araç: yt-dlp (Professional Edition)")
                
            return success_count > 0

        except Exception as e:
            logging.error(f"❌ Beklenmeyen hata: {str(e)}")
            return False

def main():
    """Ana fonksiyon"""
    generator = YouTubeDLPM3UGenerator()
    success = generator.run()
    
    if success:
        print("\n🎉 PROFESYONEL M3U dosyası başarıyla oluşturuldu!")
        print("   🚀 yt-dlp ile maksimum başarı oranı!")
    else:
        print("\n💥 M3U dosyası oluşturulamadı!")
        exit(1)

if __name__ == "__main__":
    main()
