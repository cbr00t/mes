### devBase.py (Ortak Modül)
from common import *
from config import local, wifi
import rp2
from network import WLAN, STA_IF

class BaseWiFi:
    def __init__(self):
        wlan = self.wlan = WLAN(STA_IF)
        wlan.active(True)
        try:
            import rp2
            rp2.country('TR')   # ülke seçimi (varsa)
        except Exception:
            pass
    def isConnected(self):
        wlan = self.wlan
        return wlan.isconnected()
    def connect(self, ssid = None, passwd = None, timeout = None):
        wlan = self.wlan
        if not wlan: self.init(); wlan = self.wlan
        if not wlan: return False
        print(f'wifi connected = {wlan.isconnected()}')
        if not wlan.isconnected():
            if ssid is None: ssid = wifi.ssid
            if passwd is None: passwd = wifi.passwd
            if timeout is None: timeout = wifi.timeout
            print(f'connecting [{ssid}, {passwd}]')
            if local:
                # nic.ifconfig(('192.168.0.4', '255.255.255.0', '192.168.0.1', '8.8.8.8'))
                wlan.ifconfig((ip2Str(local.ip), ip2Str(local.subnet), ip2Str(local.gateway), ip2Str(local.dns)))
            wlan.connect(ssid, passwd)
            # bağlanana kadar bekle
            t0 = time.ticks_ms()
            while not wlan.isconnected() and (not timeout or ticks_diff(ticks_ms(), t0) < timeout * 1000):
                print("Bağlanıyor...")
                sleep(.5)
            if local and wlan.isconnected():
                wlan.ifconfig((ip2Str(local.ip), ip2Str(local.subnet), ip2Str(local.gateway), ip2Str(local.dns)))
        return True
    def disconnect(self, ssid, passwd):
        wlan = self.wlan
        return wlan.disconnect(ssid, passwd)
    def getConfig(self):
        wlan = self.wlan
        return wlan.ifconfig()
