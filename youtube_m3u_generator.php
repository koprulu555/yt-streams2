<?php
/**
 * YouTube M3U Generator - Google Search Referer Method
 * Google üzerinden YouTube'a erişim
 */

class YouTubeM3UGenerator {
    private $links_file = "links.txt";
    private $output_file = "youtube_streams.m3u";
    
    public function __construct() {
        $this->setupLogging();
    }
    
    private function setupLogging() {
        ini_set('log_errors', 1);
        ini_set('error_log', 'php_m3u_generator.log');
    }
    
    private function log($message, $level = 'INFO') {
        $timestamp = date('Y-m-d H:i:s');
        $logMessage = "$timestamp - $level - $message\n";
        echo $logMessage;
        error_log($logMessage);
    }
    
    public function readChannels() {
        $channels = [];
        try {
            if (!file_exists($this->links_file)) {
                $this->log("❌ links.txt dosyası bulunamadı", 'ERROR');
                return $channels;
            }
            
            $content = file_get_contents($this->links_file);
            $content = trim($content);
            
            $channel_blocks = explode("\n\n", $content);
            
            foreach ($channel_blocks as $block) {
                $block = trim($block);
                if (empty($block)) continue;
                
                $channel_data = [];
                $lines = explode("\n", $block);
                
                foreach ($lines as $line) {
                    $line = trim($line);
                    if (strpos($line, 'isim=') === 0) {
                        $channel_data['name'] = trim(str_replace('isim=', '', $line));
                    } elseif (strpos($line, 'içerik=') === 0) {
                        $channel_data['url'] = trim(str_replace('içerik=', '', $line));
                    } elseif (strpos($line, 'logo=') === 0) {
                        $channel_data['logo'] = trim(str_replace('logo=', '', $line));
                    }
                }
                
                if (isset($channel_data['name']) && isset($channel_data['url'])) {
                    if (!isset($channel_data['logo'])) {
                        $channel_data['logo'] = '';
                    }
                    $channels[] = $channel_data;
                }
            }
            
            $this->log("✅ " . count($channels) . " kanal bulundu");
            return $channels;
            
        } catch (Exception $e) {
            $this->log("❌ links.txt okuma hatası: " . $e->getMessage(), 'ERROR');
            return [];
        }
    }
    
    private function extractVideoId($url) {
        // YouTube URL'lerinden video ID'sini çıkar
        $patterns = [
            '/youtube\.com\/watch\?v=([^&]+)/',
            '/youtu\.be\/([^?]+)/',
            '/youtube\.com\/embed\/([^?]+)/',
            '/youtube\.com\/v\/([^?]+)/'
        ];
        
        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $url, $matches)) {
                return $matches[1];
            }
        }
        return null;
    }
    
    private function getGoogleSearchUrl($youtube_url) {
        // YouTube URL'sini Google'da arayacak URL oluştur
        $encoded_url = urlencode($youtube_url);
        return "https://www.google.com/search?q=" . $encoded_url . "&btnI=I'm+Feeling+Lucky";
    }
    
    private function getHLSURL($url, $channel_name) {
        $this->log("   🌐 Google üzerinden YouTube'a erişiliyor: $url");
        
        // Video ID'sini çıkar
        $videoId = $this->extractVideoId($url);
        if (!$videoId) {
            $this->log("   ❌ Video ID bulunamadı");
            return null;
        }
        
        $this->log("   🆔 Video ID: $videoId");
        
        // Mobile YouTube URL'sini oluştur
        $mobile_url = "https://m.youtube.com/watch?v=" . $videoId;
        
        // Google arama URL'sini oluştur
        $google_search_url = $this->getGoogleSearchUrl($mobile_url);
        $this->log("   🔍 Google arama URL: " . $google_search_url);
        
        // Önce Google'dan sayfayı çek (I'm Feeling Lucky ile doğrudan YouTube'a yönlendirme)
        $final_url = $this->getFinalUrlFromGoogle($google_search_url);
        
        if ($final_url) {
            $this->log("   📍 Google yönlendirmesi: $final_url");
            
            // Google referansı ile YouTube'dan sayfayı çek
            $html = $this->fetchYouTubeViaGoogle($final_url, $google_search_url);
        } else {
            // Google yönlendirmesi olmazsa doğrudan YouTube'a git
            $this->log("   ⚠️ Google yönlendirmesi başarısız, doğrudan erişim denenecek");
            $html = $this->fetchYouTubeViaGoogle($mobile_url, "https://www.google.com/");
        }
        
        if (!$html) {
            $this->log("   ❌ Sayfa çekilemedi");
            return null;
        }
        
        // Debug için kaydet
        file_put_contents('debug_page_google.html', $html);
        $this->log("   📄 Sayfa kaynağı debug_page_google.html'ye kaydedildi");
        
        // HLS URL'sini ara
        $hls_url = $this->extractHLSFromHTML($html);
        
        if ($hls_url) {
            $this->log("   ✅ HLS URL bulundu: " . substr($hls_url, 0, 80) . "...");
            return $hls_url;
        }
        
        $this->log("   ❌ HLS URL bulunamadı");
        return null;
    }
    
    private function getFinalUrlFromGoogle($google_url) {
        $ch = curl_init();
        
        curl_setopt_array($ch, [
            CURLOPT_URL => $google_url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_TIMEOUT => 15,
            CURLOPT_CONNECTTIMEOUT => 10,
            CURLOPT_HEADER => true,
            CURLOPT_NOBODY => true
        ]);
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $redirect_url = curl_getinfo($ch, CURLINFO_REDIRECT_URL);
        curl_close($ch);
        
        if ($redirect_url && strpos($redirect_url, 'youtube.com') !== false) {
            return $redirect_url;
        }
        
        return null;
    }
    
    private function fetchYouTubeViaGoogle($youtube_url, $referer) {
        $ch = curl_init();
        
        $headers = [
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language: tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control: no-cache',
            'Connection: keep-alive',
            'Referer: ' . $referer,
            'Upgrade-Insecure-Requests: 1',
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Sec-Fetch-Dest: document',
            'Sec-Fetch-Mode: navigate',
            'Sec-Fetch-Site: cross-site'
        ];
        
        curl_setopt_array($ch, [
            CURLOPT_URL => $youtube_url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_CONNECTTIMEOUT => 15,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_REFERER => $referer
        ]);
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($http_code !== 200 || $error) {
            $this->log("   ⚠️ HTTP $http_code - cURL error: $error", 'WARNING');
            return null;
        }
        
        return $response;
    }
    
    private function extractHLSFromHTML($html) {
        // Backslash'leri temizle
        $clean_html = str_replace('\\', '', $html);
        
        // Pattern 1: hlsManifestUrl direkt arama
        if (preg_match('/"hlsManifestUrl":"(https:[^"]+?m3u8[^"]*?)"/', $clean_html, $matches)) {
            $hls_url = $matches[1];
            if (strpos($hls_url, 'googlevideo.com') !== false) {
                return $hls_url;
            }
        }
        
        // Pattern 2: ytInitialPlayerResponse içinde arama
        if (preg_match('/ytInitialPlayerResponse\s*=\s*({.+?})\s*;/s', $html, $matches)) {
            $json_str = $matches[1];
            $hls_url = $this->extractHLSFromJSON($json_str);
            if ($hls_url) {
                return $hls_url;
            }
        }
        
        // Pattern 3: window["ytInitialPlayerResponse"] içinde arama
        if (preg_match('/window\["ytInitialPlayerResponse"\]\s*=\s*({.+?})\s*;/s', $html, $matches)) {
            $json_str = $matches[1];
            $hls_url = $this->extractHLSFromJSON($json_str);
            if ($hls_url) {
                return $hls_url;
            }
        }
        
        // Pattern 4: Doğrudan m3u8 URL'leri
        if (preg_match('/https:\/\/[^"\'\s<>]*?googlevideo\.com[^"\'\s<>]*?m3u8[^"\'\s<>]*/', $clean_html, $matches)) {
            return $matches[0];
        }
        
        return null;
    }
    
    private function extractHLSFromJSON($json_str) {
        try {
            // JSON'u temizle
            $json_str = preg_replace('/\/\*.*?\*\//', '', $json_str);
            $data = json_decode($json_str, true);
            
            if (!$data) {
                return null;
            }
            
            // streamingData içinde ara
            if (isset($data['streamingData']['hlsManifestUrl'])) {
                $hls_url = $data['streamingData']['hlsManifestUrl'];
                if (strpos($hls_url, '.m3u8') !== false) {
                    return $hls_url;
                }
            }
            
            // adaptiveFormats içinde ara
            if (isset($data['streamingData']['adaptiveFormats'])) {
                foreach ($data['streamingData']['adaptiveFormats'] as $format) {
                    if (isset($format['url']) && strpos($format['url'], '.m3u8') !== false && strpos($format['url'], 'googlevideo.com') !== false) {
                        return $format['url'];
                    }
                }
            }
            
            return null;
            
        } catch (Exception $e) {
            $this->log("   ❌ JSON parse hatası: " . $e->getMessage(), 'ERROR');
            return null;
        }
    }
    
    public function createM3UFile($streams) {
        try {
            $header = "#EXTM3U\n";
            $header .= "# Title: YouTube Live Streams\n";
            $header .= "# Description: Google araması üzerinden otomatik oluşturulmuş YouTube canlı yayın listesi\n";
            $header .= "# Generated: " . date('Y-m-d H:i:s') . "\n";
            $header .= "# Method: Google Search Referer Technique\n";
            $header .= "# Total Channels: " . count($streams) . "\n\n";
            
            $content = $header;
            $successful_count = 0;
            
            foreach ($streams as $stream) {
                if ($stream['hls_url']) {
                    if (!empty($stream['logo'])) {
                        $content .= "#EXTINF:-1 tvg-id=\"{$stream['name']}\" tvg-name=\"{$stream['name']}\" tvg-logo=\"{$stream['logo']}\" group-title=\"YouTube\",{$stream['name']}\n";
                    } else {
                        $content .= "#EXTINF:-1 tvg-id=\"{$stream['name']}\" tvg-name=\"{$stream['name']}\" group-title=\"YouTube\",{$stream['name']}\n";
                    }
                    $content .= "{$stream['hls_url']}\n\n";
                    $successful_count++;
                }
            }
            
            if (file_put_contents($this->output_file, $content) !== false) {
                $this->log("✅ M3U dosyası oluşturuldu: {$this->output_file} ($successful_count kanal)");
                return true;
            } else {
                $this->log("❌ M3U dosyası yazılamadı", 'ERROR');
                return false;
            }
            
        } catch (Exception $e) {
            $this->log("❌ M3U dosyası oluşturma hatası: " . $e->getMessage(), 'ERROR');
            return false;
        }
    }
    
    public function run() {
        echo "============================================================\n";
        echo "🚀 YOUTUBE M3U GENERATOR (GOOGLE REFERER) - BAŞLIYOR\n";
        echo "============================================================\n";
        
        try {
            // Kanal listesini oku
            $channels = $this->readChannels();
            if (empty($channels)) {
                $this->log("❌ Hiç kanal bulunamadı!", 'ERROR');
                return false;
            }
            
            echo "============================================================\n";
            echo "📡 HLS URL'LERİ ALINIYOR (GOOGLE ARAMA İLE)...\n";
            echo "============================================================\n";
            
            $streams = [];
            $success_count = 0;
            
            foreach ($channels as $i => $channel) {
                $channel_num = $i + 1;
                $total_channels = count($channels);
                
                echo "\n🎬 KANAL $channel_num/$total_channels: {$channel['name']}\n";
                echo "   🔗 URL: {$channel['url']}\n";
                if (!empty($channel['logo'])) {
                    echo "   🖼️ LOGO: " . substr($channel['logo'], 0, 50) . "...\n";
                }
                
                $hls_url = $this->getHLSURL($channel['url'], $channel['name']);
                
                if ($hls_url) {
                    $streams[] = [
                        'name' => $channel['name'],
                        'url' => $channel['url'],
                        'logo' => $channel['logo'],
                        'hls_url' => $hls_url
                    ];
                    $success_count++;
                    echo "   ✅ BAŞARILI - HLS URL alındı\n";
                } else {
                    $streams[] = [
                        'name' => $channel['name'],
                        'url' => $channel['url'],
                        'logo' => $channel['logo'],
                        'hls_url' => null
                    ];
                    echo "   ❌ BAŞARISIZ - HLS URL alınamadı\n";
                }
                
                // Kısa bekleme (rate limiting için)
                if ($i < count($channels) - 1) {
                    sleep(2);
                }
            }
            
            // M3U dosyasını oluştur
            if (!empty($streams)) {
                $this->createM3UFile($streams);
                
                // İstatistikleri göster
                echo "\n============================================================\n";
                echo "📊 İSTATİSTİKLER\n";
                echo "============================================================\n";
                echo "📺 Toplam Kanal: " . count($channels) . "\n";
                echo "✅ Başarılı: $success_count\n";
                echo "❌ Başarısız: " . (count($channels) - $success_count) . "\n";
                echo "📈 Başarı Oranı: " . number_format(($success_count / count($channels)) * 100, 1) . "%\n";
                echo "💾 Çıktı Dosyası: {$this->output_file}\n";
                
                return $success_count > 0;
            }
            
            return false;
            
        } catch (Exception $e) {
            $this->log("❌ Beklenmeyen hata: " . $e->getMessage(), 'ERROR');
            return false;
        }
    }
}

// Ana çalıştırma
try {
    $generator = new YouTubeM3UGenerator();
    $success = $generator->run();
    
    if ($success) {
        echo "\n🎉 M3U dosyası başarıyla oluşturuldu!\n";
    } else {
        echo "\n💥 M3U dosyası oluşturulamadı!\n";
        exit(1);
    }
} catch (Exception $e) {
    echo "❌ Kritik hata: " . $e->getMessage() . "\n";
    exit(1);
}
?>
