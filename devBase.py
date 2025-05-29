### 📁 devBase.py (Yrtak Modül)
from common import *
import config as cfg
import json

class BaseRawSocket:
    def __init__(self):
        self.server = cfg.server
        self.sock = None

    def isConnected(self):
        return self.sock is not None
    
    def read(self, timeout=0.05):
        if not self.isConnected(): return None
        sock = self.sock; buffer = b""
        try:
            sock.settimeout(timeout)
            try:
                chunk = sock.recv(4096)
                buffer += chunk
            except Exception:
                return None
            self.sock.settimeout(None)
            while b"\n" not in buffer:
                try:
                    chunk = sock.recv(4096)
                    if not chunk: break
                    buffer += chunk
                except Exception: break
        except Exception as ex:
            print("[SocketError]", ex)
            self.close()
        return self._decodeLine(buffer)

    def write(self, data):
        if not self.isConnected(): return None
        buffer = self._prepareData(data)
        sock = self.sock; totalSize = 0
        try:
            while totalSize < len(buffer):
                size = sock.send(buffer[totalSize:])
                if size == 0: raise RuntimeError('Socket connection broken during send')
                totalSize += size
            print(f'> sock_send {totalSize}  Data: {data}')
        except Exception as ex:
            print("[SocketError]", ex)
            self.close()
        return self
    
    def close(self):
        try: self.sock.close()
        except: pass
        self.sock = None
        print(f'! sock_close')
        return self

    def talk(self, data):
        self.write(data)
        return self.read()

    def _prepareData(self, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data += "\n"
            return data.encode("utf-8")
        elif isinstance(data, bytes):
            return data + b"\n"
        raise TypeError("RawSocket.write(): data must be str, dict or bytes")

    def _decodeLine(self, buffer):
        line = buffer.split(b'\n', 1)[0]
        data = line.decode()
        if data.startswith('\ufeff'):
            data = data[1:]    # UTF-8 BOM temizle
        try:
            if data: data = data.strip()
            result = json.loads(data)
            print(f'< sock_recv {len(data)}  Data: {data}')
        except Exception as ex:
            print(f'< sock_recv {len(data)}  Data: {data}')
            raise ex
        return result

class BaseWebReq:
    def sendText(self, url):
        result = self.send(url).text
        print(result)
        return result

    def sendJSON(self, url):
        result = self.send(url).json()
        print(result)
        return result

class BaseKeypad:
    def update(self):
        return self
    def set_onPress(self, handler):
        self.onPress = handler
        return self
    def set_onRelease(self, handler):
        self.onRelease = handler
        return self
