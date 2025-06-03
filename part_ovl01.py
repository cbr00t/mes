### part.py
from common import *

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
    def active(self):
        return self == Part.current()
    @classmethod
    def partName(cls):
        return cls.__name__
    def title(self, value=None):
        # Getter
        if value is None:
            return self._title or ''
        # Setter
        changed = self._title != value; self._title = value
        if changed: self.onAttrChanged()
        return self
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
        inst = cls(*args, **kwargs)
        inst.run()
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
        self._rendered = True
    def validateInput(self, data):
        return True
    def processInput(self, data):
        # e.g for IPInputPart:
        #    if len(data) >= 3: self._selectNextInput()
        return True
    def onKeyPressed(self, key):
        return False                                                                                               # by default, keyPress NOT handled by part
    def onKeyReleased(self, key, duration = None):
        _key = key.lower()
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
    def onAttrChanged(self, defer = False):
        self._rendered = False
        if not defer and self.active(): self.render()
        return self
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
        return self
    def _toggleSnapshot(self, revert=False):
        out = self.stdout(); cur = Part.current()
        if revert:
            buf = self._bufferOut
            for rowIndex, row in enumerate(buf):
                line = ''.join(row)
                self.out_write(line, rowIndex, 0, _internal=True)                                                  # internal → zaman güncelleme vs olmasın
        self._bufferOut = out._buffer if cur == self else out._readMatrix()                                        # current == self ise lcd buffer referansı , aksinde readMatrix ile buffer kopyası
        self._rendered = False
        return self
    def out_write(self, data, row=0, col=0, _internal=False):
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
