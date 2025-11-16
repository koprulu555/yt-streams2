#!/usr/bin/env python3
"""
YouTube M3U Generator - Professional yt-dlp Edition (FIXED)
"""

import os
import time
import logging
import json
import subprocess
import re

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
                logging.error("❌ yt-dlp bulunamadı")
                return False
                
        except Exception as e:
            logging.error(f"❌ yt-dlp kontrol hatası: {str(e)}")
            return False

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

    def get_hls_url_ytdlp(self, url, channel_name):
        """yt-dlp ile HLS URL'sini al - DÜZELTİLMİŞ"""
        try:
            logging.info(f"   🌐 yt-dlp ile analiz: {channel_name}")
            
            # DÜZELTME: Eskimiş seçenek kaldırıldı, basitleştirildi
            cmd = [
                self.yt_dlp_path,
                '--dump-json',
                '--no-warnings',
                '--ignore-errors',
                '--geo-bypass',
                '--format', 'best',
                '--no-check-certificate',
                url
            ]
            
            # Komutu çalıştır
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout
            )
            
            # DÜZELTME: Hata durumunda bile çıktıyı kontrol et
            if result.stdout:
                try:
                    video_info = json.loads(result.stdout)
                    hls_url = self.extract_hls_from_ytdlp_info(video_info)
                    if hls_url:
                        logging.info(f"   ✅ HLS URL bulundu: {hls_url[:80]}...")
                        return hls_url
                    else:
                        logging.warning("   ⚠️ HLS URL bulunamadı")
                        return None
                except json.JSONDecodeError:
                    logging.error("   ❌ Geçersiz JSON yanıtı")
                    return None
            else:
                logging.error("   ❌ yt-dlp çıktı vermedi")
                return None
                
        except subprocess.TimeoutExpired:
            logging.error("   ⏰ yt-dlp zaman aşımı")
            return None
        except Exception as e:
            logging.error(f"   ❌ yt-dlp hatası: {str(e)}")
            return None

    def extract_hls_from_ytdlp_info(self, video_info):
        """yt-dlp bilgilerinden HLS URL'sini çıkar"""
        try:
            # 1. Doğrudan URL
            if video_info.get('url') and '.m3u8' in video_info['url']:
                return video_info['url']
            
            # 2. Formatlar içinde HLS arama
            if 'formats' in video_info:
                for fmt in video_info['formats']:
                    # HLS formatlarını kontrol et
                    if fmt.get('protocol') in ['m3u8', 'm3u8_native']:
                        if fmt.get('url') and '.m3u8' in fmt['url']:
                            return fmt['url']
                    
                    # URL'de m3u8 geçenleri kontrol et
                    if fmt.get('url') and '.m3u8' in fmt['url']:
                        return fmt['url']
            
            # 3. requested_formats içinde arama
            if 'requested_formats' in video_info:
                for fmt in video_info['requested_formats']:
                    if fmt.get('url') and '.m3u8' in fmt['url']:
                        return fmt['url']
            
            return None
            
        except Exception as e:
            logging.error(f"   ❌ HLS çıkarma hatası: {str(e)}")
            return None

    def create_m3u_header(self):
        """M3U dosyası header'ını oluştur"""
        return f"""#EXTM3U
# Title: YouTube Live Streams
# Description: yt-dlp ile oluşturulmuş YouTube canlı yayın listesi
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
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
        print("🚀 YOUTUBE M3U GENERATOR (YT-DLP FIXED) - BAŞLIYOR")
        print("=" * 60)
        
        try:
            # yt-dlp kontrolü
            if not self.check_yt_dlp_installation():
                return False

            # Kanal listesini oku
            self.channels = self.read_channels()
            if not self.channels:
                return False

            print("=" * 60)
            print("📡 HLS URL'LERİ ALINIYOR...")
            print("=" * 60)

            streams = []
            success_count = 0

            for i, channel in enumerate(self.channels, 1):
                print(f"\n🎬 KANAL {i}/{len(self.channels)}: {channel['name']}")
                print(f"   🔗 URL: {channel['url']}")
                
                # DÜZELTME: Sadece HLS URL alma fonksiyonunu kullan
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
                
                # Kısa bekleme
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
                
            return success_count > 0

        except Exception as e:
            logging.error(f"❌ Beklenmeyen hata: {str(e)}")
            return False

def main():
    """Ana fonksiyon"""
    generator = YouTubeDLPM3UGenerator()
    success = generator.run()
    
    if success:
        print("\n🎉 M3U dosyası başarıyla oluşturuldu!")
    else:
        print("\n💥 M3U dosyası oluşturulamadı!")
        exit(1)

if __name__ == "__main__":
    main()
