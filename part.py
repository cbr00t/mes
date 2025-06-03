from common import *
from time import monotonic, sleep
import json
from traceback import print_exception

# Class Defs
class Part(NS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        size = self.stdout().getRowCols()
        maxLenLimit = self.__maxLenLimit = (size.cols - 2)
        self._bufferOut = self.stdout()._buffer                                                                  # stdout - buffer ref
        inputs = self._inputs = self._inputs or {}
        curInputInd = self._curInputInd = self._curInputInd or 0
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
    def title(cls):
        return ''
    def editable(self):
        return False
    def curInputInd(self, ind=None):
        inputs = self._inputs; count = len(inputs)
        # get
        if ind is None:
            curInd = self._curInputInd
            return curInd if inputs and 0 <= curInd < count else None
        # set
        if inputs and 0 <= ind < count:
            self._curInputInd = ind
        return self
    def _curInputName(self, name=None):
        inputs = self._inputs; curInd = self.curInputInd()
        if not inputs:
            return None
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
        current = Part.current()
        if current:
            current._toggleSnapshot(revert)
            current.render()
        else:
            Part.stdout().clear()
    def canClose(self):
        return True
    # close 'last' part
    def close(self):
        if not self.canClose(): return False
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
        return False                                                                                               # by default, keyPress NOT handled by part
    def onKeyReleased(self, key, duration = None):
        _key = key.lower(); buf = self._bufferIn
        result = self.onKeyPressed_araIslem(key, delayMS)
        if result != True:
            if _key == 'esc' or _key == 'f1':
                if self.close():
                    return True                                                                                    # by default, keyRelease handled by part
            elif _key == '^':
                self._selectPrevInput()
            elif _key == 'v':
                self._selectNextInput()
            else:
                return False
        self.render()                                                                                              # Render LCD GUI for each keystroke
        if result is None:
            result = True
        return result                                                                                              # key handled by part or Internal result
    def onKeyPressed_araIslem(self, key, delayMS = None):
        return None
    def selectFirstInput(self):
        return self.selectInput('_first')
    def selectLastInput(self):
        return self.selectInput('_last')
    def selectNextInput(self):
        return self.selectInput('_next')
    def selectPrevInput(self):
        return self.selectInput('_prev')
    def selectInput(nameOrDirectionOrIndex):
        if not nameOrDirectionOrIndex:
            return self
        name = nameOrDirectionOrIndex; old = self.curInputInd()
        new = old if isinstance(name, int) else \
              0 if name == '_first' else \
              len(self.inputs)[-1] if name == '_last' else \
              old + 1 if name == '_next' else \
              old - 1 if name == '_prev' else \
              self.inputs.index(name)
        if new is not None:
            self.curInputInd(new)
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
    def stdout(cls):
        if shared.dev is None:
            dynImport('dev_local', 'mod_dev')
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

class InputPart(Part):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._maxLen = self._maxLen or self.__maxLenLimit
        self._bufferIn = self._bufferIn or ''
        curPos = self._curPos = self._curPos or 0
    def editable(self):
        return True
    def maxLen(self, value=None):
        limit = self.__maxLenLimit or 0
        # getter
        if value is None:
            _maxLen = self._maxLen or 0
            return min(_maxLen, limit)
        # setter
        value = value or 0
        self._maxLen = limit if value < 0 else min(value, limit)
        return self  
    def curPos(self, value=None):
        _maxLen = self._maxLen or 0; _maxLen0 = max(_maxLen - 1, 0)
        # getter
        if value is None:
            _pos = self._curPos or 0
            return min(_pos, _maxLen0)
        # setter
        value = value or 0; 
        self._curPos = _maxLen0 if value < 0 else min(value, _maxLen0)
        return self
    def onKeyPressed_araIslem(self, key, duration = None):
        _key = key.lower(); buf = self._bufferIn
        if _key == 'enter':
            self._commitInput(buf)
        elif _key == 'esc':
            if buf: buf = self._bufferIn = buf[:-1]
        elif _key == '^':
            self._curPrev()
        elif _key == 'v':
            self._curNext()
        else:
            maxLen = self.maxLen()
            if len(buf) < maxLen:
                buf += key
                self._commitInput(buf)
        return True
    def _commitInput(self, data):
        if not editable(): return False
        if not (self.validateInput(data)): return False
        result = self.processInput(self, data)
        buf = self._bufferIn = ''
        return result
    def _curNext(self):
        self.curPos(self.curPos() + 1)
        return self
    def _curPrev(self):
        self.curPos(self.curPos() - 1)
        return self
    def _curToStart(self):
        self.curPos(0)
        return self
    def _curToEnd(self):
        self.curPos(-1)
        return self


# Initialize
shared.activePart = Part.current
