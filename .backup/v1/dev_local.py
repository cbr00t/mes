from time import sleep
import json
import socket
import requests
from common import *
import config as cfg
import core

# ---------- Ethernet Class (Mock) ----------
class Eth:
    def __init__(self):
        local = cfg.local
        self.ifconfig = (local.ip, local.subnet, local.gateway, local.dns)
    def init(self):
        print("[LocalEth] initialized with:", self.ifconfig)
        return self    # simüle edilmiş Ethernet objesi

# ---------- Web Requests Class ----------
class WebReq:
    def __init__(self):
        self.eth = dev.eth
    def send(self, url):
        print(f'get request: {url}')
        result = requests.get(url)
        print(f'... result: [{result}]')
        return result
    def sendText(self, url):
        result = self.send(url).text
        print(result)
        return result
    def sendJSON(self, url):
        result = self.send(url).json()
        print(result)
        return result

# ---------- Raw TCP Socket Class ----------
class RawSocket:
    def __init__(self):
        self.server = cfg.server
        self.sock = None
    def isConnected(self):
        return self.sock is not None
    def open(self):
        srv = self.server
        sock = self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ep = (ip2Str(srv.ip), srv.rawPort)                                         # !! (ip, port) ==> Tuple !!
        sock.connect(ep)
        print(f'! sock_open: [{ep[0]}:{ep[1]}]')
        return self
    def read(self, timeout=0.05):
        if not self.isConnected():
            return None
        sock = self.sock; buffer = b""
        try:
            # 1. Blocking + timeout (örneğin 50ms)
            sock.settimeout(timeout)
            try:
                chunk = sock.recv(4096)
                buffer += chunk
            except Exception:
                # Veri yoksa veya timeout olduysa => None dön
                return None
            # 2. Veri geldiyse → blocking moda geç, '\n' gelene kadar oku
            self.sock.settimeout(None)  # sonsuza kadar bekle
            while b"\n" not in buffer:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break  # bağlantı kapandı
                    buffer += chunk
                except Exception:
                    break
        except Exception as ex:
            print("[SocketError]", ex)
            self.close()
        # 3. Satırı ayır
        line = buffer.split(b"\n", 1)[0]
        try:
            data = line.decode('utf-8-sig').strip()
            size = len(data)
            print(f'< sock_recv {size} Bytes: [{data}]')
            return json.loads(data)
        except Exception as e:
            return {
                "_parseError": str(e),
                'raw': data if 'data' in locals() else buffer.decode(errors='ignore')
            }
    def write(self, data):
        if not self.isConnected(): return None
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data += "\n"
            buffer = data.encode("utf-8")
        elif isinstance(data, bytes):
            buffer = data + b"\n"
        else:
            raise TypeError("RawSocket.write(): data must be str, dict or bytes")
        sock = self.sock; totalSize = 0;
        try:
            while totalSize < len(buffer):
                size = sock.send(buffer[totalSize:])
                if size == 0:
                    raise RuntimeError('Socket connection broken during send')
                totalSize += size
            print(f'> sock_send {totalSize} Bytes: [{data}]')
        except Exception as ex:
            print("[SocketError]", ex)
            self.close()
            return self
        return self
    def close(self):
        try: self.sock.close()
        except: pass
        self.sock = None
        print(f'! sock_close')
        return self
    def talk(self, data):
        self.write(data)
        result = self.read()
        return result

# ---------- LED Class (Mock) ----------
class LED:
    def __init__(self):
        print("[LED] (mock) initialized.")
    def clear(self):
        print("[LED] cleared.")
        return self
    def write(self, data, row=0, col=0):
        print(f"[LED] write @({row},{col}):", data)
        return self


# ---------- Device Initialization ----------
dev = core.dev = core.Device()
@withErrCheck
def setup_eth(): dev.eth = Eth().init()
@withErrCheck
def setup_req(): dev.req = WebReq()
@withErrCheck
def setup_sock(): dev.sock = RawSocket()
@withErrCheck
def setup_led(): dev.led = LED()
steps = [setup_eth, setup_req, setup_sock, setup_led]
for step in steps:
    step()

