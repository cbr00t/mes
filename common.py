
# ---------- General Structures ----------
class NS:
    def __init__(self, **kwargs):
        for key in kwargs:
            if not isinstance(key, str):
                raise TypeError(f"Geçersiz key: {key} ({type(key)})")
            setattr(self, key, kwargs[key])

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

def getUpdateUrl():
    from config import server
    return server.updateUrl if server.autoUpdate else None
