// lcd-server.js
// TCP sunucu ile CircuitPython LCD kontrol uygulaması

const net = require('net');
const readline = require('readline');
const fs = require('fs');

// Sunucu yapılandırması
const PORT = 8088;
const HOST = '0.0.0.0'; // Tüm ağ arayüzlerinden bağlantıyı kabul et
const LOG_FILE = './keypad_log.txt'; // Tuş kayıtları için log dosyası

// Bağlı cihazları saklamak için array
const connectedClients = [];

// Tuş basılma kayıtlarını tutan nesne
const keyLog = {
  events: [],
  MAX_EVENTS: 100 // Bellekte tutulacak maksimum olay sayısı
};

// TCP sunucuyu oluştur
const server = net.createServer((socket) => {
  const clientIP = `${socket.remoteAddress}:${socket.remotePort}`;
  console.log(`Yeni bağlantı: ${clientIP}`);
  
  // Yeni bağlantıyı listeye ekle
  connectedClients.push(socket);
  
  // Veri aldığında
  socket.on('data', (data) => {
    try {
      const message = JSON.parse(data.toString());
      
      // Tuş basma olayı
      if (message.komut === 'key_pressed') {
        console.log(`\x1b[33m[TUŞ BASILDI]\x1b[0m ${message.icerik.key}`);
        logKeyEvent('BASILDI', message.icerik.key);
      }
      
      // Tuş bırakma olayı
      else if (message.komut === 'key_released') {
        console.log(`\x1b[32m[TUŞ BIRAKILDI]\x1b[0m ${message.icerik.key} (${message.icerik.duration}s)`);
        logKeyEvent('BIRAKILDI', message.icerik.key, message.icerik.duration);
      }
      
      // Diğer komut türleri için
      else {
        console.log(`${clientIP}'den mesaj: ${data}`);
      }
    } catch (e) {
      // JSON parse hatası - veri JSON formatında değil
      if (data.length < 100) { // Çok uzun veriler için log bastırmayalım
        console.log(`${clientIP}'den veri: ${data}`);
      }
    }
  });
  
  // Bağlantı kapanınca
  socket.on('close', () => {
    console.log(`${clientIP} bağlantısı kapandı`);
    // Bağlantıyı listeden çıkar
    const index = connectedClients.indexOf(socket);
    if (index !== -1) {
      connectedClients.splice(index, 1);
    }
  });
  
  // Hata oluştuğunda
  socket.on('error', (err) => {
    console.log(`${clientIP} bağlantı hatası: ${err.message}`);
  });
});

// Tuş olaylarını kaydetme fonksiyonu
function logKeyEvent(type, key, duration = null) {
  const timestamp = new Date().toISOString();
  const event = {
    timestamp,
    type,
    key,
    duration
  };
  
  // Olayı bellekteki listeye ekle
  keyLog.events.push(event);
  
  // Liste maksimum boyuta ulaştıysa baştan sil
  if (keyLog.events.length > keyLog.MAX_EVENTS) {
    keyLog.events.shift();
  }
  
  // Olayı dosyaya kaydet
  const logLine = `${timestamp} [${type}] ${key}${duration ? ' Süre: ' + duration + 's' : ''}\n`;
  fs.appendFile(LOG_FILE, logLine, (err) => {
    if (err) {
      console.error('Log dosyasına yazılırken hata:', err);
    }
  });
}

// Sunucuyu başlat
server.listen(PORT, HOST, () => {
  console.log(`\x1b[36m=== LCD KONTROL SUNUCUSU ===\x1b[0m`);
  console.log(`TCP sunucu ${HOST}:${PORT} adresinde çalışıyor`);
  console.log(`Tuş kayıtları '${LOG_FILE}' dosyasına kaydediliyor`);
  console.log('\x1b[36m=== KOMUTLAR ===\x1b[0m');
  console.log('  lcd <satır1> <satır2> <satır3> <satır4> - LCD ekrana yaz');
  console.log('  cls                - LCD ekranı temizle');
  console.log('  clients            - Bağlı cihazları listele');
  console.log('  keylog             - Son 10 tuş kaydını göster');
  console.log('  exit               - Sunucuyu kapat');
  console.log('\nPico cihazından tuşlar basıldığında otomatik olarak görüntülenecek');
});

// Komut satırı arayüzü
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: '\x1b[36mLCDServer>\x1b[0m '
});

rl.prompt();

rl.on('line', (line) => {
  const args = line.trim().split(' ');
  const command = args[0].toLowerCase();
  
  switch (command) {
    case 'lcd':
      // Ekrana yazma komutu: lcd satır1 satır2 satır3 satır4
      const satir1 = args[1] || '';
      const satir2 = args[2] || '';
      const satir3 = args[3] || '';
      const satir4 = args[4] || '';
      
      const lcdCommand = {
        komut: "ekranayaz",
        icerik: {
          satir1, 
          satir2, 
          satir3, 
          satir4
        }
      };
      
      sendToAllClients(JSON.stringify(lcdCommand));
      console.log(`LCD komut gönderildi: ${JSON.stringify(lcdCommand)}`);
      break;
      
    case 'cls':
      // Ekranı temizleme komutu
      const clearCommand = {
        komut: "ekranayaz",
        icerik: {
          satir1: "", 
          satir2: "", 
          satir3: "", 
          satir4: ""
        }
      };
      
      sendToAllClients(JSON.stringify(clearCommand));
      console.log('Ekran temizleme komutu gönderildi');
      break;
    
    case 'keylog':
      // Son tuş kayıtlarını göster
      console.log('\x1b[36m=== SON TUŞ KAYITLARI ===\x1b[0m');
      
      if (keyLog.events.length === 0) {
        console.log('Henüz kaydedilmiş tuş olayı yok');
      } else {
        // Son 10 olayı göster (veya daha az varsa tümünü)
        const numEvents = Math.min(10, keyLog.events.length);
        const recentEvents = keyLog.events.slice(-numEvents);
        
        recentEvents.forEach((event, index) => {
          const timeStr = event.timestamp.split('T')[1].split('.')[0]; // Sadece saat kısmını al
          const color = event.type === 'BASILDI' ? '\x1b[33m' : '\x1b[32m';
          const durationStr = event.duration ? ` (${event.duration}s)` : '';
          console.log(`${index+1}. ${timeStr} ${color}[${event.type}]\x1b[0m ${event.key}${durationStr}`);
        });
        
        console.log(`\nToplam ${keyLog.events.length} kayıt (${LOG_FILE} dosyasında tam log mevcut)`);
      }
      break;
      
    case 'clients':
      // Bağlı cihazları listeleme
      if (connectedClients.length === 0) {
        console.log('Bağlı cihaz yok');
      } else {
        console.log(`Bağlı cihaz sayısı: ${connectedClients.length}`);
        connectedClients.forEach((client, index) => {
          console.log(`  ${index + 1}. ${client.remoteAddress}:${client.remotePort}`);
        });
      }
      break;
      
    case 'exit':
      // Sunucuyu kapat
      console.log('Sunucu kapatılıyor...');
      server.close(() => {
        console.log('Sunucu kapatıldı');
        process.exit(0);
      });
      break;
      
    default:
      console.log('Bilinmeyen komut. Geçerli komutlar: lcd, cls, keylog, clients, exit');
  }
  
  rl.prompt();
}).on('close', () => {
  console.log('CLI kapatılıyor');
  process.exit(0);
});

// Tüm bağlı cihazlara mesaj gönderme fonksiyonu
function sendToAllClients(message) {
  if (connectedClients.length === 0) {
    console.log('Bağlı cihaz olmadığından komut gönderilemedi!');
    return;
  }
  
  connectedClients.forEach((client, index) => {
    client.write(message, (err) => {
      if (err) {
        console.log(`Hata: ${client.remoteAddress}:${client.remotePort} adresine gönderilirken hata oluştu`);
      } else {
        console.log(`${client.remoteAddress}:${client.remotePort} adresine gönderildi`);
      }
    });
  });
}