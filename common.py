from ring_buffer import *
import json
import gc
import sys
import time
from time import sleep
from sys import implementation as impl

if impl.name == 'cpython':    # CPython = (local)
    import threading, traceback, asyncio
    from time import monotonic
    from asyncio import new_event_loop, set_event_loop
    import tracemalloc
    tracemalloc.start()
    def print_exception(e):
        traceback.print_exception(type(e), e, e.__traceback__)
    # --- MicroPython API emülasyonu ---
    def ticks_ms():
        """Return milliseconds since an unspecified point, monotonic."""
        return int(monotonic() * 1000)
    def ticks_us():
        """Return microseconds since an unspecified point, monotonic."""
        return int(monotonic() * 1_000_000)
    def ticks_diff(t1, t0=0):
        """Return difference between two tick values."""
        return t1 - t0
    def sleep_ms(ms):
        """Sleep given milliseconds."""
        time.sleep(ms / 1000)
    def sleep_us(us):
        """Sleep given microseconds."""
        time.sleep(us / 1_000_000)
    async def asleep(sec):
        """Async sleep in seconds (alias for asyncio.sleep)."""
        await asyncio.sleep(sec)
    async def asleep_ms(ms):
        """Async sleep in milliseconds."""
        await asyncio.sleep(ms / 1000)
    def monotonic():
        """Return monotonic time in seconds."""
        return time.monotonic()
elif impl.name == 'micropython':
    import uasyncio as asyncio
    from asyncio import sleep as asleep, sleep_ms as asleep_ms
    from time import ticks_diff, ticks_ms, sleep_ms, sleep_us
    from sys import print_exception
    def monotonic():
        return ticks_ms() / 1000

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
        self.lastTime = NS()
        self._globals = NS()
        self.queues = NS(key = RingBuffer())
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
def ljust(s, width, fillchar=' '):
    """Return s left-justified in a string of length width."""
    if len(s) >= width:
        return s
    return s + fillchar * (width - len(s))
def rjust(s, width, fillchar=' '):
    """Return s right-justified in a string of length width."""
    if len(s) >= width:
        return s
    return fillchar * (width - len(s)) + s
def substring(s, start, end=None):
    """Return substring from start index up to but not including end index."""
    if end is None:
        return s[start:]
    return s[start:end]
def uidToString(uid):
    result = ''
    for i in uid:
        result = "%02X" % i + result
    return result
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
def isLocalPy():
    return not(isCircuitPy() or isMicroPy())
def isCircuitPy():
    try:
        return impl.name == "circuitpython"
    except:
        return False
def isMicroPy():
    try:
        return impl.name == "micropython"
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
def async_run(proc, *args, **kwargs):
    if isMicroPy():
        try:
            return asyncio.run(proc(*args, **kwargs))
        except KeyboardInterrupt:
            print("\n[async_run] stopped by user (KeyboardInterrupt)")
        except MemoryError as ex:
            print("[async_run] memory error:", ex)
        except Exception as ex:
            print("[async_run] exception:", ex)
            print_exception(ex)
        return  # MicroPython'da loop.close() yok

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(proc(*args, **kwargs))
    except KeyboardInterrupt as ex:
        print("\n[async_run] stopped by user (KeyboardInterrupt)")
    except MemoryError as ex:
        print("[async_run] memory error:", ex)
    except Exception as ex:
        print("[async_run] exception:", ex)
        print_exception(ex)
    finally:
        if isLocalPy():
            # sadece local CPython'da loop kapatılır
            loop.close()
def async_task(proc, *args, **kwargs):
    """Run coroutine as background task with safe exception logging."""
    async def wrapper():
        try:
            await proc(*args, **kwargs)
        except Exception as ex:
            print(f"[ERROR in {proc.__name__}]", ex)
            try:
                print_exception(ex)
            except Exception:
                pass
    try:
        return asyncio.create_task(wrapper())
    except Exception as ex2:
        print("async_task hata:", ex2)
        raise
def thread(proc, *args, **kwargs):
    """Runs new thread in core1"""
    try:
        import _thread
        try:
            return _thread.start_new_thread(proc, args or (), kwargs)
        except Exception as ex2:
            print("thread hatası:", ex2)
            raise
    except Exception:
        # no thread support, asyncio fallback
        return task(proc, *args, **kwargs)
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
def getWSUrlBase(https = None, ip = None, port = None):
    from config import server as srv
    if https is None: https = False
    protocolPostfix = 'https' if https else 'http'
    ip = ip or ip2Str(srv.ip)
    port = port or srv.wsPort
    return f'{protocolPostfix}://{ip}:{port}'
def getWSUrl(qs = None, wsPath = None, api = None, https = None):
    from config import local, server as srv
    base = getWSUrlBase(https)
    wsPath = (wsPath if wsPath else srv.wsPath).strip('/ ')
    result = f'{base}/{wsPath}'
    if api: result += f'/{api}'
    result += f'/?.ip={ip2Str(local.ip)}'
    if qs and isinstance(qs, dict):
        for key, value in qs.items():
            result += f'&{str(key)}'
            if value:
                result += f'={value}'
    print('[DEBUG] wsURL', result)
    return result.rstrip('&')
def getWSData(api, args = None, data = None, wsPath = None):
    from config import server as srv
    mesAPImi = wsPath == 'mes'
    if data is not None and isinstance(data, (dict, list)):
        data = json.dumps(data)
    result = { key: wsPath, 'api': api } if mesAPImi \
             else { 'ws': wsPath or srv.wsPath, 'api': api }
    if args:
        if mesAPImi: result.update(args)
        else: result['args'] = args
    if data is not None:
        result['data'] = { 'data': data }
    # print('getwsdata', result)
    return result

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

