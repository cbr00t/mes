# wiznet5k_micropython_test.py
# MicroPython (RP2040) + W5500 (SPI) DHCP + basit HTTP GET

from machine import Pin, SPI
import time
import network

try:
    import urequests as requests
except ImportError:
    import requests  # bazı firmware'lerde isim 'requests' olabilir

# ==== Pin eşleşmeleri (CircuitPython'dakiyle aynı olsun diye) ====
# Sen CP'de spi1 kullanıyordun; RP2040'ta SPI1 varsayılan pinleri:
# SCK=GP10, MOSI=GP11, MISO=GP12
SPI_BUS = 1
SCK   = 10
MOSI  = 11
MISO  = 12
CS    = 17   # Chip Select
RST   = 20   # Reset (opsiyonel ama tavsiye edilir)

# ==== SPI ve NIC (WIZNET5K) başlat ====
spi = SPI(SPI_BUS, baudrate=20_000_000, polarity=0, phase=0,
          sck=Pin(SCK), mosi=Pin(MOSI), miso=Pin(MISO))

cs   = Pin(CS,  Pin.OUT)
rst  = Pin(RST, Pin.OUT)

# Donanım reset (temiz başlangıç için iyi olur)
rst.value(0); time.sleep_ms(50)
rst.value(1); time.sleep_ms(50)

# network.WIZNET5K sürücüsü MicroPython'a gömülü olmalı
assert hasattr(network, "WIZNET5K"), "Bu firmware'de WIZNET5K sürücüsü yok!"

nic = network.WIZNET5K(spi, cs, rst)

def wait_link(timeout_s=10):
    t0 = time.ticks_ms()
    while not nic.isconnected():
        # DHCP başlat
        nic.active(True)
        try:
            nic.ifconfig('dhcp')
        except Exception:
            pass
        # Link ve IP oluşana kadar bekle
        if nic.isconnected():
            break
        if time.ticks_diff(time.ticks_ms(), t0) > timeout_s*1000:
            return False
        time.sleep(0.5)
    return True

def test_ethernet():
    print("Ethernet bağlanıyor (DHCP)...")
    ok = wait_link(timeout_s=15)
    if not ok:
        print("❌ DHCP/IP alınamadı (kablonun takılı olduğundan ve switch/router'ın açık olduğundan emin olun).")
        return

    ip, mask, gw, dns = nic.ifconfig()
    print("✅ IP:", ip, "  Mask:", mask, "  GW:", gw, "  DNS:", dns)

    # Basit HTTP GET
    URL = "http://httpbin.org/json"
    try:
        print("GET", URL)
        r = requests.get(URL, timeout=10)
        print("HTTP durum:", r.status_code)
        try:
            print("Gelen JSON:", r.json())
        except ValueError:
            print("Gelen metin:", r.text)
        r.close()
    except Exception as e:
        print("İstek hatası:", e)

if __name__ == "__main__":
    try:
        test_ethernet()
    finally:
        # İstersen bağlantıyı kapatabilirsin:
        # nic.active(False)
        pass
