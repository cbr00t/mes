### devBase.py (Ortak Modül)
from common import *
from config import server as srv
from time import sleep, monotonic
import json
from traceback import print_exception

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
        self._open(); connected = self.isConnected()
        self.onOpen() if connected else self.onClose()
        return connected
    def _open(self):
        if not self.isConnected():
            busy(); srv = self.server
            print('! sock open:', f'{ip2Str(srv.ip)}:{srv.rawPort}')
        return not self.isConnected()
    def close(self):
        if self.isConnected():
            try: busy(); self.sock.close()
            except: pass
            self.sock = None; print('! sock close')
        self.onClose()
        return self
    def onOpen(self):
        dev = shared.dev; lcd = dev.lcd if dev else None
        if lcd: lcd.write('^', 0, lcd.getCols() - 6)
    def onClose(self):
        dev = shared.dev; lcd = dev.lcd if dev else None
        if lcd: lcd.write('x', 0, lcd.getCols() - 6)
    def send(self, data):
        if not self.isConnected(): return False
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
            print('  >> sock send:', totalSize)
        except Exception as ex:
            print('  !! sock send:', ex)
            self.close()
            return False
        shared.lastTime.heartbeat = monotonic()
        return True
    def recv(self, timeout=None):
        if not self.isConnected(): return None
        sock = self.sock; buffer = b''
        try:
            sock.settimeout(0.02); chunk = b''
            try:
                chunk = sock.recv(1)
            except Exception:  # ilk veri gelmezse erken çık
                if timeout is None: return None
            if chunk: buffer += chunk
            timeout = timeout or self.getDefaultTimeout()
            sock.settimeout(0); start = monotonic()
            lastError = None
            while b'\n' not in buffer:
                chunk = None
                try:
                    chunk = sock.recv(512)
                    if chunk: buffer += chunk
                except Exception as ex:
                    lastError = ex
                # print(timeout, monotonic(), start)
                if monotonic() - start >= timeout:
                    if lastError: raise lastError
                    return None
            busy()
        except (RuntimeError, TimeoutError, OSError) as ex:
            errCode = None
            try: errCode = ex.errcode
            except AttributeError: errCode = ex.args[0]
            # if errCode == 10054:
            #    self.close()
            if not (isinstance(ex, TimeoutError) or errCode == 116 or errCode == 10035):
                print('  !! sock recv:', ex)
                print_exception(ex)
            return None
        except Exception as ex:
            print('  !! sock recv:', ex); print_exception(ex)
            return None
        try:
            result = self._decodeLine(buffer)
            shared.lastTime.heartbeat = monotonic()
            return result
        except Exception as ex:
            print('  !! sock recv:', ex); print_exception(ex)
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
    def wsCheckStatusIfNeed(self, timeout=None):
        return self.wsCheckStatus(timeout) if statusShouldBeChecked() else False
    def wsCheckStatus(self, timeout=None):
        result = None
        try:
            result = self.wsTalk('tekilTezgahBilgi')
            if not result: raise RuntimeError('check failed')
            if isinstance(result, str): result = json.loads(result)
            if result: shared.curStatus = result
            # print('[wsCheckStatus] ', result)
            return True
        except Exception as ex:
            print('  !! wsStatusCheck:', ex)
            return False
        finally:
            if result is None: self.close()
            shared.lastTime.statusCheck = monotonic()
    def wsHeartbeatIfNeed(self, timeout=None):
        return self.wsHeartbeat(timeout) if heartbeatShouldBeChecked() else True
    def wsHeartbeat(self, timeout=None):
        result = None
        try:
            result = self.wsTalk('ping')
            if not result: raise RuntimeError('check failed')
            # print('[wsHeartbeat] ', result)
            return True
        except Exception as ex:
            print('  !! wsHeartbeat:', ex)
            return False
        finally:
            if result is None: self.close()
            shared.lastTime.heartbeat = monotonic()
    def _encodeLine(self, data):
        # print('data-type', type(data), data)
        if isinstance(data, (dict, list)): data = json.dumps(data)
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
        # print('    _decodeLine', buffer)
        utf8Bytes = b'\xef\xef\xbb\xbf'
        for byte in utf8Bytes:
            if buffer[0] == byte:
                buffer = buffer[1:]
        data = buffer.decode('utf-8').splitlines()[0]
        try:
            if data: data = data.rstrip()
            print('    << sock recv:', len(data))
        except Exception as ex:
            print('    !! sock recv:', ex)
            raise ex
        return data
