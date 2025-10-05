# pico2w_httpbin_json.py
# MicroPython 1.21+ (Pico W / Pico 2 W) için
import time
import json
import gc

# Wi-Fi
import network
try:
    import rp2
    rp2.country('TR')   # ülke seçimi (varsa)
except Exception:
    pass

# HTTP/HTTPS istekleri
try:
    import urequests as requests
except ImportError:
    import requests  # bazı derlemelerde isim 'requests' olabilir

SSID = "NAX_1"
PASSWORD = "rrffy9cphq"

HTTPS_URL = "https://httpbin.org/json"
HTTP_URL  = "http://httpbin.org/json"


def wifi_connect(ssid: str, password: str, timeout_s: int = 15) -> network.WLAN:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Wi-Fi'ye bağlanılıyor...")
        wlan.connect(ssid, password)
        t0 = time.ticks_ms()
        # bağlanana kadar bekle
        while not wlan.isconnected() and time.ticks_diff(time.ticks_ms(), t0) < timeout_s * 1000:
            print(".", end="")
            time.sleep(0.3)
        print()
    if not wlan.isconnected():
        raise RuntimeError("Wi-Fi bağlanamadı (SSID/şifre veya sinyal kontrol).")
    print("Bağlandı. IP:", wlan.ifconfig()[0])
    return wlan


def fetch_and_print(url: str, timeout_s: int = 15) -> bool:
    """URL'den JSON çekip ekrana basar. Başarılıysa True, aksi halde False döndürür."""
    print("\nGET", url)
    r = None
    try:
        r = requests.get(url, timeout=timeout_s)
        print("HTTP durum:", r.status_code)
        # JSON olmayan yanıt ihtimaline karşı koruma:
        try:
            data = r.json()
        except ValueError:
            # JSON parse edilemediyse ham metni göster
            data = r.text
        print("Gelen JSON/Metin:")
        print(data)
        return True
    except Exception as e:
        print("Hata:", e)
        return False
    finally:
        try:
            if r is not None:
                r.close()
        except Exception:
            pass
        gc.collect()


def main():
    wifi_connect(SSID, PASSWORD)
    current_url = HTTPS_URL  # önce HTTPS dene

    while True:
        ok = fetch_and_print(current_url, timeout_s=20)
        if not ok:
            # HTTPS hata verdiyse HTTP'ye düş
            if current_url.startswith("https://"):
                print("⚠️  HTTPS başarısız oldu, HTTP ile tekrar denenecek.")
                current_url = HTTP_URL
            else:
                # HTTP de başarısızsa bir sonraki döngüde tekrar dene
                pass

        time.sleep(5)  # 5 sn sonra tekrar dene


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDurduruldu.")
