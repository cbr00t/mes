#Bu projeyi denemek için servisten
#{"komut":"ekranayaz","icerik":{"satir1":"savas","satir2":"gormek","satir3":"deneme","satir4":"123"}}
import time
import board
import busio
import digitalio
import json
from lcd.lcd import LCD
from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
from keypad_handler2 import KeypadHandler  # Yeni optimize edilmiş keypad_handler2 dosyasını kullan
from hardware_config import HARDWARE_CONFIG

import adafruit_connection_manager
import adafruit_requests
from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K

# === LCD AYARLARI ===
sda, scl = board.GP0, board.GP1
i2c = busio.I2C(scl, sda)
lcd = LCD(I2CPCF8574Interface(i2c, 0x27), num_rows=4, num_cols=20)

def lcd_clear():
    lcd.clear()

def lcd_write(msg, row=0, col=0):
    if msg is None:
        msg = ""
    msg = str(msg)[:20]
    lcd.set_cursor_pos(row, col)
    lcd.print(msg)

def lcd_write_lines(lines):
    for i in range(4):
        line = lines[i] if i < len(lines) else ""
        lcd_write(line, i, 0)

# Sunucuya JSON mesajı gönderme fonksiyonu
def send_to_server(komut, icerik):
    try:
        if sock:
            message = json.dumps({"komut": komut, "icerik": icerik})
            sock.send(message.encode('utf-8'))
            print(f"Gönderilen: {message}")
    except Exception as e:
        print(f"Gönderme hatası: {e}")

# === TUŞ TAKIMI AYARLARI ===
rows = [getattr(board, pin) for pin in HARDWARE_CONFIG["rows"]]
cols = [getattr(board, pin) for pin in HARDWARE_CONFIG["cols"]]
keys = HARDWARE_CONFIG["keys"]

# === TUŞ OLAYLARI ===
def on_key_pressed(key):
    print(f"BASILDI: {key}")
    #lcd_clear()
    #lcd_write(f"BASILDI: {key}", 0)
    
    # Artık tuş basma olaylarını göndermiyoruz
    # send_to_server("key_pressed", {"key": key})

def on_key_released(key, duration):
    print(f"CEKILDI: {key}")
    #lcd_clear()
    #lcd_write(f"CEKILDI: {key}", 0)
    #lcd_write(f"SURE: {duration:.2f}s", 1)
    
    # Sadece tuş bırakma olaylarını gönder
    send_to_server("key_released", {
        "key": key, 
        "duration": f"{duration:.2f}"
    })

keypad = KeypadHandler(rows, cols, keys, on_key_pressed, on_key_released)

# === LCD AÇILIŞ MESAJI ===
lcd.set_backlight(True)
lcd_clear()
lcd_write("DHCP baglaniyor...", 0)

# === ETHERNET BAĞLANTISI ===
try:
    cs = digitalio.DigitalInOut(board.GP17)
    reset = digitalio.DigitalInOut(board.GP20)
    spi = busio.SPI(board.GP18, board.GP19, board.GP16)

    eth = WIZNET5K(spi, cs, reset, is_dhcp=True)

    while not eth.link_status:
        lcd_write("Baglanti bekleniyor...", 1)
        time.sleep(0.5)

    lcd_clear()
    lcd_write("IP ALINDI:", 0)
    lcd_write(eth.pretty_ip(eth.ip_address), 1)
    time.sleep(2)

    # Ping yerine HTTP isteği ile test
    lcd_clear()
    lcd_write("Ping: 192.168.1.1", 0)
    start = time.monotonic()
    try:
        pool = adafruit_connection_manager.get_radio_socketpool(eth)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(eth)
        requests = adafruit_requests.Session(pool, ssl_context)
        response = requests.get("http://192.168.1.1")
        duration = time.monotonic() - start
        lcd_write(f"Ping OK: {duration:.2f}s", 1)
        response.close()
    except Exception as e:
        duration = time.monotonic() - start
        print("Ping FAIL:", str(e))
        print(f"Süre: {duration:.2f}s")

    time.sleep(2)

except Exception as e:
    print("ETH HATA:", str(e))
    while True:
        time.sleep(1)

# === TCP SUNUCUYA BAĞLANTI VE ANA DÖNGÜ ===
# Yeni MacBook IP adresi:
REMOTE_IP = "192.168.0.117"
REMOTE_PORT = 8088
RECONNECT_INTERVAL = 5  # 10 saniyeden 5 saniyeye düşürüldü

buffer = b""
sock = None

# Performans iyileştirmeleri
last_keypad_check = time.monotonic()
KEYPAD_CHECK_INTERVAL = 0.0002  # 2ms'de bir tuş takımı kontrolü

while True:
    current_time = time.monotonic()
    
    # Tuş takımını kontrol et - kısa basışları yakalamak için daha sık
    if current_time - last_keypad_check >= KEYPAD_CHECK_INTERVAL:
        keypad.update()
        last_keypad_check = current_time

    try:
        if sock is None:
            lcd_clear()
            lcd_write("Baglaniyor...", 0)
            sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
            sock.settimeout(0.5)  # 1 saniye yerine 0.5 saniye timeout
            sock.connect((REMOTE_IP, REMOTE_PORT))
            lcd_write("Baglanti kuruldu", 1)
            buffer = b""
            # Bağlandıktan hemen sonra bekleme süresini kaldırdık
            # time.sleep(1) - Bu satırı kaldırdık

        try:
            data = sock.recv(1024)
            if data:
                buffer += data
                decoded = buffer.decode("utf-8")
                if "}" in decoded:
                    json_text = decoded.split("}", 1)[0] + "}"
                    buffer = b""
                    parsed = json.loads(json_text)

                    if parsed.get("komut") == "ekranayaz":
                        icerik = parsed.get("icerik", {})
                        lines = [
                            icerik.get("satir1", ""),
                            icerik.get("satir2", ""),
                            icerik.get("satir3", ""),
                            icerik.get("satir4", "")
                        ]
                        lcd_clear()
                        lcd_write_lines(lines)
        except Exception:
            pass  # veri gelmediyse ya da eksik geldiyse

    except Exception as e:
        print("TCP Baglanti hatasi:", str(e))
        lcd_clear()
        lcd_write("Baglanti koptu", 0)
        time.sleep(RECONNECT_INTERVAL)
        if sock:
            try:
                sock.close()
            except:
                pass
            sock = None

    # Döngü hızını artırma
    time.sleep(0.002)  # Ana döngü bekleme süresi: 2ms