from time import monotonic, sleep
import json

# ---------- General Structures ----------
class NS:
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
        return super().getInstVars() + ['dev', 'updateCheck', '_lastBusyTime', '_lastLCDTime', '_lastLEDTime']

# Functions
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


# Class Defs
class Device(NS):
    @classmethod
    def getInstVars(cls):
        return super().getInstVars() + ['eth', 'req', 'sock', 'keypad', 'lcd', 'led', 'rfid']

# Global Vars
if not 'shared' in globals():
    shared = Shared(
        updateCheck = True                                          # Auto Update enabled by default (if config.server.autoUpdate is None)
    )

# User Functions
def getUpdateUrls():
    from config import server as srv
    updateUrl_postfix = srv.updateUrl_postfix or ''
    ip = ip2Str(srv.ip)
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
def getHeartbeatInterval():
    if isBusy():
        return None
    from config import server as srv
    hearbeatInterval = srv.hearbeatInterval
    if (hearbeatInterval or 0) <= 0:
        return None
    if isIdle():
        return hearbeatInterval * 3
    return hearbeatInterval

def isIdle():
    from config import local
    idleTime = local.idleTime
    if (idleTime or 0) <= 0:
        return False
    return shared._lastBusyTime and monotonic() - shared._lastBusyTime > idleTime
def isBusy():
    return shared._lastBusyTime and monotonic() - shared._lastBusyTime <= 0.5
def busy():
    shared._lastBusyTime = monotonic()
def lcdIsBusy():
    return shared.activePart is not None
def lcdCanBeCleared():
    isBusy = lcdIsBusy(); lastTime = shared._lastLCDTime
    return not isBusy and lastTime and (monotonic() - lastTime) >= 3
def heartbeatShouldBeChecked():
    if isBusy(): return False 
    hearbeatInterval = getHeartbeatInterval(); lastTime = shared._lastHeartbeatTime or 0
    return hearbeatInterval and monotonic() - lastTime > hearbeatInterval
def getWSData(api, args = None, data = None, wsPath = None):
    from config import server as srv
    if data is not None and isinstance(data, (dict, list)):
        data = json.dumps(data)
    result = { 'ws': wsPath or srv.wsPath, 'api': api }
    if args: result['args'] = args
    if data is not None: result['data'] = { 'data': data }
    # print('getwsdata', result)
    return result

# Initialization
def globalInit():
    initDevice()
    initHandlers()
def initDevice():
    from config import mod
    dev = shared.dev
    if dev is not None:
        return dev
    modName_device = mod.device or ('rasppico' if isCircuitPy() else 'local')
    print(f'Device Module = {modName_device}')
    dynImport(f'dev_{modName_device}', 'mod_dev')
    dev = shared.dev; print(dev)
    return dev
def initHandlers():
    from appHandlers import AppHandlers
    handlers = shared.handlers = AppHandlers()
    return handlers
