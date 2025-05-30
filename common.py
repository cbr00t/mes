from time import monotonic

# ---------- General Structures ----------
class NS:
    def __init__(self, **kwargs):
        for key in kwargs:
            if not isinstance(key, str):
                raise TypeError(f"Geçersiz key: {key} ({type(key)})")
            setattr(self, key, kwargs[key])
    def __getattr__(self, key):
        # __getattr__ sadece __dict__ içinde olmayanlara çalışır
        return None
    def __setattr__(self, key, value):
        self.__dict__[key] = value
    def __repr__(self):
        attrs = ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'NS({attrs})'

def str2IP(value):
    return None if value is None else tuple(map(int, value.split('.')))
def ip2Str(value):
    return None if value is None else '.'.join(map(str, value))
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

def getUpdateUrls():
    from config import server as srv
    if not srv.autoUpdate:
        return None
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
    from config import server as srv
    hearbeatInterval = srv.hearbeatInterval
    if (isIdle()):
        hearbeatInterval *= 10
    return hearbeatInterval

_lastBusyTime = None
def isIdle():
    from config import local
    idleTime = local.idleTime
    if (idleTime or 0) <= 0:
        return False
    return _lastBusyTime and monotonic() - _lastBusyTime > idleTime
def busy():
    global _lastBusyTime
    _lastBusyTime = monotonic()


