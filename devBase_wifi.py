### devBase.py (Ortak Modül)
from common import *
from config import local, wifi

class BaseWiFi:
    def __init__(self):
        wlan = self.wlan = None
    def isConnected(self):
        wlan = self.wlan
        return True
    def connect(self, ssid = None, passwd = None, timeout = None, internal = False):
        wlan = self.wlan
        if not wlan:
            self.init()
            wlan = self.wlan
        if not wlan:
            return False
        print(f'wifi connected = {wlan.isconnected()}')
        if not wlan.isconnected():
            if ssid is None: ssid = wifi.ssid
            if passwd is None: passwd = wifi.passwd
            if timeout is None: timeout = wifi.timeout
            if not (internal or ssid):
                result = self.autoConnect(passwd, timeout)
                if result:
                    wifi.ssid = result[0]
                    return result
            print(f'connecting [{ssid}, {passwd}]')
            if local and local.ip:
                # nic.ifconfig(('192.168.0.4', '255.255.255.0', '192.168.0.1', '8.8.8.8'))
                wlan.ifconfig((ip2Str(local.ip), ip2Str(local.subnet), ip2Str(local.gateway), ip2Str(local.dns)))
            wlan.connect(ssid, passwd)
            # bağlanana kadar bekle
            tryCount = 1 if internal else 3
            for i in range(0, tryCount):
                t0 = ticks_ms()
                while not wlan.isconnected() and (not timeout or ticks_diff(ticks_ms(), t0) < timeout * 1000):
                    print("Bağlanıyor...")
                    sleep(1)
                if wlan.isconnected():
                    break
            gc.collect()
            if not wlan.isconnected():
                return False
            if local:
                if local.ip:
                    wlan.ifconfig((ip2Str(local.ip), ip2Str(local.subnet), ip2Str(local.gateway), ip2Str(local.dns)))
                else: 
                    _c = wlan.ifconfig()
                    print('wifi ifconfig: ', _c)
                    local.ip = str2IP(_c[0])
                    local.subnet = str2IP(_c[1])
                    local.gateway = str2IP(_c[2])
                    local.dns = str2IP(_c[3])
        return True
    def disconnect(self):
        wlan = self.wlan
        return wlan.disconnect()
    def autoConnect(self, passwd=None, timeout=None):
        wlan = self.wlan
        if not wlan:
            self.init()
            wlan = self.wlan
        if passwd is None: passwd = wifi.passwd
        if timeout is None: timeout = wifi.timeout
        print(f'scanning wifi networks...')
        recs = wlan.scan() or []
        if recs:
            recs = sorted(recs, key=lambda x: x[3], reverse=True)
        for rec in recs:
            ssid = rec[0]
            ssid = ssid.strip().decode() if ssid else None
            if not ssid or len(ssid) < 2:
                continue
            gc.collect()
            print(f'  - ({ssid}, {passwd})')
            try:
                result = self.connect(ssid, passwd, timeout, True)
                if result:
                    print(f'!! Auto Connected Wifi: ({ssid}, {passwd})')
                    return (ssid,)
            except Exception as ex:
                print(ex)
                print_exception(ex)
        return None
    def getConfig(self):
        wlan = self.wlan
        return wlan.ifconfig()
