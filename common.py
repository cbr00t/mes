from time import monotonic, sleep
import json
from traceback import print_exception

# Global Vars
if not 'encoding' in globals():
    encoding = 'utf-8'


# ---------- General Structures ----------
class NS:
    @classmethod
    def _super(cls, self):
        return super(cls, self)
    @classmethod
    def getInstVars(cls):
        return []
    def __init__(self, **kwargs):
        for key in self.getInstVars():
            if not isinstance(key, str):
                raise TypeError(f"instVar key geçersiz: {key}  ({type(key)})")
            setattr(self, key, None)
        for key in kwargs:
            if not isinstance(key, str):
                raise TypeError(f"Geçersiz key: {key} ({type(key)})")
            setattr(self, key, kwargs[key])
    def __getattr__(self, key):
        # __getattr__ sadece __dict__ içinde olmayanlara çalışır
        # print('getattr', key)
        return None
    def __setattr__(self, key, value):
        # print('setattr', key, value)
        object.__setattr__(self, key, value)
    def __repr__(self):
        attrs = ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'NS({attrs})'
class Shared(NS):
    @classmethod
    def getInstVars(cls):
        return super().getInstVars() + ['dev', 'activePart']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateCheck = True
        self.lastTime = NS(); self._globals = NS()
        self.queues = NS()
        self._base64_alphabet = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

# Functions
def to64(value):
    if not value: return value
    if isinstance(value, str): value = value.encode(encoding)
    elif not isinstance(value, (bytes, bytearray)):
        raise TypeError("to64 only accepts str or bytes")
    result = b''; i = 0; _a = shared._base64_alphabet
    while i < len(value):
        block = value[i:i+3]; padding = 3 - len(block)
        block += b'\x00' * padding
        n = (block[0] << 16) + (block[1] << 8) + block[2]
        result += bytes([_a[(n >> 18) & 63]])
        result += bytes([_a[(n >> 12) & 63]])
        result += bytes([_a[(n >> 6) & 63]] if padding < 2 else b'=')
        result += bytes([_a[n & 63]] if padding < 1 else b'=')
        i += 3
    return result.decode(encoding)
def from64(value):
    if isinstance(value, str): value = value.encode('ascii')
    elif not isinstance(value, (bytes, bytearray)):
        raise TypeError("from64 only accepts str or bytes")
    from binascii import a2b_base64 as a2b
    return a2b(value).decode(encoding)
def tuple2Str(value, delim):
    return None if value is None else delim.join(map(str, value))
def str2Tuple(value, delim):
    return None if value is None else tuple(map(int, value.split(delim)))
def ip2Str(value):
    return tuple2Str(value, '.')
def str2IP(value):
    return str2Tuple(value, '.')
def version2Str(value):
    return tuple2Str(value, '.')
def str2Version(value):
    return str2Tuple(value, '.')
def withErrCheckEx(func, exClass):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exClass as ex:
            print(f"[ERROR in {func.__name__}] {ex}")
    return wrapper
def withErrCheck(func):
    return withErrCheckEx(func, Exception)
def dynImport(name, as_ = None):
    mod = __import__(name)
    globals()[as_ or name] = mod
    return mod
def safeImport(name, as_ = None):
    try:
        dynImport(name, as_)
    except Exception as ex:
        print(f"[ModuleError] {name} import failed:", ex)
        return None
def isWindows():
    import os
    return os.name == 'nt'       # Windows

def isCircuitPy():
    try:
        from sys import implementation as impl
        return impl.name == "circuitpython"
    except:
        return False
def splitext(filepath):
    parts = filepath.rsplit('.', 1)
    if len(parts) == 2:
        return parts[0], '.' + parts[1]
    return filepath, ''
def exists(fname):
    try:
        with open(fname): pass
        return True
    except OSError:
        return False
# ----------------------------------------------------------------------------- #


# Global Vars
if not 'shared' in globals():
    shared = Shared()

# Class Defs
class Device(NS):
    @classmethod
    def getInstVars(cls):
        return super().getInstVars() + ['eth', 'req', 'sock', 'keypad', 'lcd', 'led', 'rfid']

# User Functions
def getUpdateUrls():
    from config import server as srv
    updateUrl_postfix = srv.updateUrl_postfix or ''
    # ip = ip2Str(srv.ip)
    ip = 'localhost'
    return [
        f'http://{ip}:{port}{updateUrl_postfix}'
        for port in srv.updatePorts
    ]
def getWSUrl(qs = None, wsPath = None, api = None, https = None):
    from config import local, server as srv
    if https is None: https = False;
    protocolPostfix = 'https' if https else 'http'
    ip = ip2Str(srv.ip); port = srv.wsPort
    wsPath = (wsPath if wsPath else srv.wsPath).strip('/ ')
    result = f'{protocolPostfix}://{ip}:{port}/{wsPath}'
    if api: result += f'/{api}'
    result += f'/?.ip={ip2Str(local.ip)}'
    if qs and isinstance(qs, dict):
        for key, value in qs.items():
            result += f'&{str(key)}'
            if value: result += f'={value}'
    return result.rstrip('&')

def activePart():
    return shared.activePart() if shared.activePart is not None else None
def isIdle():
    from config import local
    idleTime = local.idleTime
    if (idleTime or 0) <= 0: return False
    return shared.lastTime.busy and monotonic() - shared.lastTime.busy > idleTime
def isBusy():
    return shared.lastTime.busy and monotonic() - shared.lastTime.busy <= 0.3
def busy():
    shared.lastTime.busy = monotonic()
def lcdIsBusy():
    return activePart() is not None
def lcdCanBeCleared():
    from config import hw
    clearDelay = hw.lcd.clearDelay
    isBusy = lcdIsBusy(); lastTime = shared.dev.lcd._lastWriteTime
    # print('lcd_lastWriteTime =', lastTime)
    return not isBusy and lastTime and (monotonic() - lastTime) >= clearDelay
def getHeartbeatInterval():
    if isBusy(): return None
    from config import server as srv
    intv = srv.hearbeatInterval
    if (intv or 0) <= 0: return None
    if isIdle(): return intv * 3
    return intv
def heartbeatShouldBeChecked():
    if isBusy(): return False 
    intv = getHeartbeatInterval(); lastTime = shared.lastTime.heartbeat or 0
    return intv and monotonic() - lastTime > intv
def getStatusCheckInterval():
    if isBusy(): return None
    from config import server as srv
    intv = srv.statusCheckInterval
    if (intv or 0) <= 0: return None
    if isIdle(): return intv * 3
    return intv
def statusShouldBeChecked():
    if isBusy(): return False 
    intv = getStatusCheckInterval(); lastTime = shared.lastTime.statusCheck or 0
    return intv and monotonic() - lastTime > intv
def getWSData(api, args = None, data = None, wsPath = None):
    from config import server as srv
    if data is not None and isinstance(data, (dict, list)):
        data = json.dumps(data)
    result = { 'ws': wsPath or srv.wsPath, 'api': api }
    if args: result['args'] = args
    if data is not None: result['data'] = { 'data': data }
    # print('getwsdata', result)
    return result


