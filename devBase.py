### 📁 devBase.py (Ortak Modül)
from common import *
from config import local, server as srv, hw
from time import sleep, monotonic
import json
from traceback import print_exception

class BaseEth:
    def __init__(self):
        self.eth = None
    def init(self):
        pass
    def isConnected(self):
        return True
    def getPool(self):
        return None

class BaseRawSocket:
    def __init__(self):
        self.server = srv
        self.sock = None
    def isConnected(self):
        return self.sock is not None
    @classmethod
    def getDefaultTimeout(self):
        return srv.socketTimeout
    def open(self):
        return not self.isConnected()
    def close(self):
        try: self.sock.close()
        except: pass
        self.sock = None; print(f'! sock_close')
        return self
    def send(self, data):
        self.open()
        buffer = self._encodeLine(data)
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
            print("[SendError]", ex)
            self.close()
            return False
        shared._lastHeartbeatTime = monotonic()
        return True
    def recv(self, timeout=None):
        self.open()
        sock = self.sock; buffer = b''
        try:
            sock.settimeout(0.2); chunk = b''
            try:
                chunk = sock.recv(1)
            except Exception:  # ilk veri gelmezse erken çık
                if timeout is None:
                    return None
            if chunk:
                busy()
                buffer += chunk
            timeout = timeout or self.getDefaultTimeout()
            start = monotonic(); sock.settimeout(0)
            while b'\n' not in buffer:
                busy()
                # print(timeout, monotonic(), start)
                if monotonic() - start >= timeout:
                    return None
                chunk = sock.recv(1024)
                buffer += chunk
        except (RuntimeError, TimeoutError, OSError) as ex:
            errCode = None
            try: errCode = ex.errcode
            except AttributeError: errCode = ex.args[0]
            if errCode != 10035:
                print('[RecvError]', ex)
                print_exception(ex)
            return None
        except Exception as ex:
            print('[RecvException]', ex)
            print_exception(ex)
            return None
        try:
            result = self._decodeLine(buffer)
            shared._lastHeartbeatTime = monotonic()
            return result
        except Exception as ex:
            print('[RecvDataError]', ex)
            print_exception(ex)
            return None
    def talk(self, data, timeout=None):
        self.send(data)
        return self.recv(timeout or self.getDefaultTimeout())
    def sendJSON(self, data):
        return self.send(data)
    def recvJSON(self, timeout=None):
        result = self.recv(timeout)
        if isinstance(result, str):
            for check in [('{', '}'), ('[', ']')]:
                if not result.startswith(check[0]) and result.endswith(check[1]):
                    result = check[0] + result
                elif result.startswith(check[0]) and not result.endswith(check[1]):
                    result += check[1]
        return json.loads(result) if result else None
    def talkJSON(self, data, timeout=None):
        result = self.talk(data, timeout)
        return json.loads(result) if result else None
    def wsSend(self, api, args = None, data = None, wsPath = None):
        return self.sendJSON(getWSData(api, args, data, wsPath))
    def wsRecv(self, timeout=None):
        return self.recvJSON(timeout)
    def wsTalk(self, api, args = None, data = None, wsPath = None, timeout=None):
        return self.talkJSON(getWSData(api, args, data, wsPath), timeout)
    def wsHeartbeat(self, timeout=None):
        result = None
        try:
            if (shared._lastHeartbeatTime or False) <= 0:                   # no check at startup
                return True
            result = self.wsTalk('ping')
            if not result:
                raise RuntimeError('recv response')
            # print('[wsHeartbeat] ', result)
            return True
        except Exception as ex:
            print('[wsHeartbeat]', ex); print_exception(ex)
            return False
        finally:
            if result is None:
                self.close(); self.open()
            shared._lastHeartbeatTime = monotonic()
    def _encodeLine(self, data):
        # print('data-type', type(data), data)
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        if isinstance(data, str):
            if '\n' not in data: data += '\n'
            return data.encode("utf-8")
        elif isinstance(data, bytes):
            if b'\n' not in data: data + b'\n'
            return data
        raise TypeError('RawSocket._encodeLine(): data must be str, dict or bytes')
    def _decodeLine(self, buffer):
        if not buffer:
            return None
        print('    _decodeLine', buffer)
        utf8Bytes = b'\xef\xef\xbb\xbf'
        for byte in utf8Bytes:
            if buffer[0] == byte:
                buffer = buffer[1:]
        data = buffer.decode('utf-8').split('\n')[0]
        try:
            if data:
                data = data.strip()
            print(f'    < sock_recv {len(data)}  Data: {data}')
        except Exception as ex:
            print(f'    < sock_recv {len(data)}  Data: {data}')
            raise ex
        return data

class BaseWebReq:
    def __init__(self):
        self._initSession()
    def send(self, url, timeout=None):
        return None
    def sendText(self, url, timeout=None):
        result = self.send(url, timeout).text
        print(result)
        return result
    def sendJSON(self, url, timeout=None):
        result = self.send(url, timeout).json()
        print(result)
        return result
    def _initSession(self):
        return self

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
    def write(self, data, row=0, col=0):
        shared._lastLCDTime = monotonic()
        return self
    def clearLine(self, row):
        print(f'[LCD] clearLine: row={row}')
        if isinstance(row, (list, range)):
            for _row in row:
                self.clearLine(_row)
            return self
        self.write(' ' * hw.lcd.cols, row, 0)
        shared._lastLCDTime = None
        return self
    def clear(self):
        return self
    def on(self):
        return self
    def off(self):
        return self

class BaseLED:
    def write(self, rgb, col):
        return self
    def clear(self, col):
        return self.write((0, 0, 0), col)

class BaseRFID:
    def read(self):
        return None


