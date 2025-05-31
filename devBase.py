### 📁 devBase.py (Ortak Modül)
from common import *
from config import server as srv
from time import sleep, monotonic
import json
import traceback

class BaseEth:
    def __init__(self):
        self.eth = None
    def init(self):
        pass

class BaseRawSocket:
    def __init__(self):
        self.server = srv
        self.sock = None
    def isConnected(self):
        return self.sock is not None
    def open(self):
        pass
    def __iptal_read(self, timeout=None):
        if timeout is None:
            timeout = 5
        if not self.isConnected():
            self.open()
        sock = self.sock; buffer = b""
        start_time = monotonic()
        try:
            sock.settimeout(0.05)
            while True:
                try:
                    chunk = sock.recv(64)
                    if not chunk:
                        break
                    buffer += chunk
                    if b"\n" in buffer:
                        break
                except Exception:
                    # Timeout vs. normal hata farkı yapılabilir ama burada kısa beklemeye devam
                    pass
                if (monotonic() - start_time) > timeout:
                    return None
        except Exception as ex:
            print("[SocketError]", ex)
            traceback.print_exception(ex)
            return None

        # Mesaj tam ise işleme al
        try:
            return self._decodeLine(buffer)
        except Exception as ex:
            print('[SocketDataError]', ex)
            traceback.print_exception(ex)
            return None
    def read(self, timeout=None):
        if timeout is None:
            timeout = 5
        if not self.isConnected():
            self.open()
        sock = self.sock; buffer = b""
        try:
            sock.settimeout(0.05)
            chunk = sock.recv(1)
            if chunk:
                busy()
                buffer += chunk
                sock.settimeout(timeout)
                while b"\n" not in buffer:
                    busy()
                    chunk = sock.recv(256)
                    if not chunk: break
                    buffer += chunk
        except (TimeoutError, RuntimeError):
            return None
        except OSError as ex:
            errNo = None
            try: errNo = ex.errno                          # pylocal
            except AttributeError: errNo = ex.args[0]      # pycircuit
            if errNo == 116:                               # possible timeout
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
                busy()
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
    def __init__(self):
        self._initSession()
    def send(self, url, timeout=None):
        self.send(url, timeout)
    def sendText(self, url, timeout=None):
        result = self.send(url, timeout).text
        print(result)
        return result
    def sendJSON(self, url, timeout=None):
        result = self.send(url, timeout).json()
        print(result)
        return result
    def _initSession(self):
        pass

class BaseKeypad:
    def __init__(self, onPress = None, onRelease = None):
        pass
    def update(self):
        return self
    def set_onPress(self, handler):
        self.onPress = handler
        return self
    def set_onRelease(self, handler):
        self.onRelease = handler
        return self

class BaseLCD:
    def clear(self):
        return self
    def write(self, data, row=0, col=0):
        return self
    def on():
        return self
    def off():
        return self

class BaseLED:
    def write(self, rgb, col):
        return self
    def clear(self, col):
        return self.write((0, 0, 0), col)

class BaseRFID:
    def read(self):
        return None


