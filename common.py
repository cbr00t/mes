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
        return super().getInstVars() + ['dev']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updateCheck = True
        self.lastTime = NS()

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


# Global Vars
if not 'shared' in globals():
    shared = Shared()


# Class Defs
class Device(NS):
    @classmethod
    def getInstVars(cls):
        return super().getInstVars() + ['eth', 'req', 'sock', 'keypad', 'lcd', 'led', 'rfid']

class Part(NS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        size = self.stdout().getRowCols()
        self._inMaxLen = (size.cols - 2)
        self._bufferIn = self._bufferIn or ''
        self._bufferOut = self.stdout()._buffer                                                                  # stdout - buffer ref
        inputs = self._inputs = self._inputs or {}
        curInputInd = self.__curInputInd = self.__curInputInd or 0
    @staticmethod
    def stack():
        s = getattr(Part, '_stack', None)
        if s is None:
            s = Part._stack = []
        return s
    @staticmethod
    def current():
        item = Part._stackPeek()
        return item.part if item else None
    @classmethod
    def partName(cls):
        return cls.__name__
    @classmethod
    def title():
        return ''
    def editable(self):
        return False
    def _curInputInd(self, ind = None):
        inputs = self._inputs; count = len(inputs)
        # get
        if ind is None:
            curInd = self.__curInputInd
            return curInd if inputs and 0 <= curInd < count else None
        # set
        if inputs and 0 <= ind < count:
            self.__curInputInd = ind
        return self
    def _curInputName(self, name = None):
        inputs = self._inputs; curInd = self._curInputInd
        if not inputs: return None
        # get
        if not name:
            return None if curInd is None else inputs.keys()[curInd]
        # set
        curInd = inputs.keys().index(name)
        if curInd is not None:
            self._curInputInd = curInd
        return self
    @classmethod
    def Run(cls, *args, **kwargs):
        inst = cls()
        inst.run(*args, **kwargs)
        return inst
    def run(self):
        self.open()
    def open(self):
        Part._stackPush(self)
        Part._currentChanged(False)
        return self
    @staticmethod
    def closeLast():
        item = Part._stackPop()
        if item is None: return None
        Part._currentChanged(True)
        return item.part
    @staticmethod
    def closeAll():
        if not Part._stackClear(): return False
        Part._currentChanged(True)
        return True
    @staticmethod
    def _currentChanged(revert):
        current = Part.current(revert)
        if current:
            current._toggleSnapshot(revert)
            current.render()
        else:
            Part.stdout().clear()
    def canClose(self):
        return True
    # close 'last' part
    def close(self):
        if not self.canClose():
            return False
        Part.closeLast()
        return True
    def render(self):
        out = self.stdout()
        out.clear()
        out.write(self.title() or '', 0, 1)
        # ...
        # ...
    def validateInput(self, data):
        return True
    def processInput(self, data):
        # e.g for IPInputPart:
        #    if len(data) >= 3: self._selectNextInput()
        return True
    def onKeyPressed(self, key):
        return False                                                                                                # by default, keyPress NOT handled by part
    def onKeyReleased(self, key, delayMS = None):
        if not self.editable: return False
        _key = key.lower(); buf = self._bufferIn
        if _key == 'enter':
            self._commitInput(buf)
        elif _key == 'esc':
            if buf: buf = self._bufferIn = buf[:-1]
        elif _key == 'f1':
            if self.close():
                return True                                                                                         # by default, keyRelease handled by part
        elif _key == '^':
            self._selectPrevInput()
        elif _key == 'v':
            self._selectNextInput()
        else:
            limit = self._inMaxLen
            if limit is None or len(buf) < limit:
                buf += key
                self._commitInput(buf)
        self.render()                                                                                               # Render LCD GUI for each keystroke
        return True                                                                                                 # key handled by part
    def _commitInput(self, data):
        if not editable(): return False
        if not (self.validateInput(data)): return False
        result = self.processInput(self, data)
        buf = self._bufferIn = ''
        return result
    def _selectFirstInput(self):
        return self._selectInput('_first')
    def _selectLastInput(self):
        return self._selectInput('_last')
    def _selectNextInput(self):
        return self._selectInput('_next')
    def _selectPrevInput(self):
        return self._selectInput('_prev')
    def _selectInput(nameOrDirectionOrIndex):
        if not nameOrDirectionOrIndex:
            return self
        name = nameOrDirectionOrIndex; old = self._curInputInd()
        new = old if isinstance(name, int) else \
              0 if name == '_first' else \
              len(self.inputs)[-1] if name == '_last' else \
              old + 1 if name == '_next' else \
              old - 1 if name == '_prev' else \
              self.inputs.index(name)
        if new is not None:
            self._curInputInd(new)
    def _toggleSnapshot(self, revert=False):
        out = self.stdout(); cur = Part.current()
        if revert:
            buf = self._bufferOut
            for rowIndex, row in enumerate(buf):
                line = ''.join(row)
                lcd.write(line, rowIndex, 0, _internal=True)                                                         # internal → zaman güncelleme vs olmasın
        self._bufferOut = out._buffer if cur == self else out._readMatrix()                                          # current == self ise lcd buffer referansı , aksinde readMatrix ile buffer kopyası
    def out_write(self, data, row=0, col=0):
        self.stdout().write(data, row, col)
    def out_clear(self):
        self.stdout().clear()
    def out_clearLine(self, row):
        self.stdout().clearLine(row)
    @classmethod
    def stdin():
        return shared.dev.keypad  # ??
    @classmethod
    def stdout():
        return shared.dev.lcd
    @staticmethod
    def _stackPush(part):
        s = Part.stack()
        s.append(NS(part = part))
        return part
    @staticmethod
    def _stackPop():
        s = Part.stack()
        return s.pop() if s else None
    @staticmethod
    def _stackPeek():
        s = Part.stack()
        return s[-1] if s else None
    @staticmethod
    def _stackClear():
        s = Part.stack()
        if not s: return False
        s.clear(); return True

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
    if isBusy(): return None
    from config import server as srv
    hearbeatInterval = srv.hearbeatInterval
    if (hearbeatInterval or 0) <= 0: return None
    if isIdle(): return hearbeatInterval * 3
    return hearbeatInterval

def isIdle():
    from config import local
    idleTime = local.idleTime
    if (idleTime or 0) <= 0: return False
    return shared.lastTime._busy and monotonic() - shared.lastTime._busy > idleTime
def isBusy():
    return shared.lastTime._busy and monotonic() - shared.lastTime._busy <= 0.3
def busy():
    shared.lastTime._busy = monotonic()
def lcdIsBusy():
    return Part.current() is not None
def lcdCanBeCleared():
    isBusy = lcdIsBusy(); lastTime = shared.lastTime._lcd
    return not isBusy and lastTime and (monotonic() - lastTime) >= 3
def heartbeatShouldBeChecked():
    if isBusy(): return False 
    hearbeatInterval = getHeartbeatInterval(); lastTime = shared.lastTime._heartbeat or 0
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

