### 📁 devBase.py (Ortak Modül)
from common import *
import config as cfg
from time import sleep, monotonic
import json
import traceback

class BaseRawSocket:
    def __init__(self):
        self.server = cfg.server
        self.sock = None
    def isConnected(self):
        return self.sock is not None
    def read(self, timeout=None):
        if timeout is None:
            timeout = 5
        if not self.isConnected():
            self.open()
        sock = self.sock; buffer = b""
        try:
            sock.settimeout(0.1)
            chunk = sock.recv(128)
            buffer += chunk
            sock.settimeout(timeout)
            while b"\n" not in buffer:
                chunk = sock.recv(128)
                if not chunk: break
                buffer += chunk
        except (TimeoutError, RuntimeError):
            return None
        except OSError as ex:
            errNo = None
            try: errNo = ex.errno                          # pylocal
            except AttributeError: errNo = ex.args[0]      # pycircuit
            if errNo == 116:    # possible timeout
                return None
            print('oserr', errNo)
            if errNo == 10054:
                self.close()
            raise
        except Exception as ex:
            print("[SocketError]", ex)
            traceback.print_exception(ex)
        try:
            return self._decodeLine(buffer)
        except Exception as ex:
            print('[SocketDataError]', ex)
            traceback.print_exception(ex)
            return None
    def write(self, data):
        if not self.isConnected(): return False
        buffer = self._prepareData(data)
        sock = self.sock; totalSize = 0
        try:
            while totalSize < len(buffer):
                size = sock.send(buffer[totalSize:])
                if size == 0:
                    self.close()
                    raise RuntimeError('Socket connection broken during send')
                totalSize += size
            print(f'> sock_send {totalSize}  Data: {data}')
        except Exception as ex:
            print("[SocketError]", ex)
            self.close()
            return False
        return True 
    def close(self):
        try: self.sock.close()
        except: pass
        self.sock = None
        print(f'! sock_close')
        return self
    def talk(self, data, timeout=None):
        self.write(data)
        return self.read(timeout)
    
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
        if not buffer:
            return None
        line = buffer.split(b'\n', 1)[0]
        data = line.decode()
        if data.startswith('\ufeff'):
            data = data[1:]    # UTF-8 BOM temizle
        try:
            if data: data = data.strip()
            print(f'< sock_recv {len(data)}  Data: {data}')
        except Exception as ex:
            print(f'< sock_recv {len(data)}  Data: {data}')
            raise ex
        return data

class BaseWebReq:
    def sendText(self, url, timeout=None):
        result = self.send(url, timeout).text
        print(result)
        return result
    def sendJSON(self, url, timeout=None):
        result = self.send(url, timeout).json()
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

