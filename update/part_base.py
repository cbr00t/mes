### part.py
from common import *

# Class Defs
class Part(NS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._maxLen = self._maxLen or self.maxLenLimit()
        # self._bufferOut = self.stdout()._buffer                                                                  # stdout - buffer ref
        inputs = self._inputs = self._inputs or {}
        curInputInd = self._curInputInd = self._curInputInd or 0
        self._scrollPos = self._scrollPos or 0
    @staticmethod
    def stack():
        s = getattr(Part, '_stack', None)
        if s is None: s = Part._stack = []
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
    def parentPart(self, value=None):
        # get
        if value is None: return self._parentPart
        # set
        self._parentPart = value
        return self
    def title(self, value=None):
        # get
        if value is None: return self._title or ''
        # set
        self._title = value
        self.onAttrChanged()
        return self
    def editable(self):
        return False
    def label(self, value=None):
        # get
        if value is None: return self._label
        # set
        self._label = value
        return self
    @classmethod
    def maxLenLimit(cls):
        # get
        return cls.stdout().getCols()
    def maxLen(self, value=None):
        limit = self.maxLenLimit()
        # get
        if value is None:
            result = self._maxLen or 0
            return min(result, limit)
        # set
        value = value or 0
        self._maxLen = limit if value < 0 else min(value, limit)
        self.onAttrChanged()
        return self  
    def curInputInd(self, value=None):
        inputs = self._inputs
        count = len(inputs) if inputs else 0
        # get
        if value is None:
            curInd = self._curInputInd
            return curInd if 0 <= curInd < count else 0
        # set
        if 0 <= value < count: self._curInputInd = value
        self.onAttrChanged()
        return self
    def curInputName(self, value=None):
        inputs = self._inputs; curInd = self.curInputInd()
        # get
        if not value:
            return None if not inputs or curInd is None else list(inputs.keys())[curInd]
        # set
        curInd = inputs.keys().index(value) if inputs else None
        self.curInputInd(curInd)
        return self
    def curInput(self):
        # get
        name = self.curInputName()
        return self._inputs.get(name) if name else None
    def scrollPos(self, value=None, defer=True):
        # get
        return self._scrollPos
        # set
        self._scrollPos = value
        self.onAttrChanged(defer)
        return self
    @classmethod
    def Run(cls, *args, **kwargs):
        inst = cls(*args, **kwargs)
        inst.run()
        return inst
    def run(self):
        self.open()
    def open(self):
        cur = Part.current()
        if cur: cur._rendered = False
        Part._stackPush(self)
        Part._currentChanged(False)
        return self
    @staticmethod
    def closeLast():
        item = Part._stackPop()
        Part._currentChanged(True)
        return item.part if item else None
    @staticmethod
    def closeAll():
        if not Part._stackClear(): return False
        Part._currentChanged(True)
        return True
    @staticmethod
    def _currentChanged(revert):
        cur = Part.current(); _clear = False
        if cur:
            cur._toggleSnapshot(revert)
            cur.render()
        else: _clear = True
        if _clear:
            out = Part.stdout()
            out.clear(); out.write('', 0, 0)
        print('part stack len:', len(Part.stack()))
    def canClose(self):
        return True
    # close 'last' part
    def close(self):
        if not self.canClose(): return False
        Part.closeLast()
        return True
    def render(self):
        self._render_ilk()
        self._renderInputs()
        self._render_son()
        self._rendered = True
    def _render_ilk(self):
        self.out_clear()
        # print('title:', self.title())
        self.out_write(self.title() or '', 0, 0)
    def _renderInputs(self):
        _inputs = list((self._inputs or {}).values())
        cur = self.curInputInd()
        rows = self.stdout().getRows() - 1    # başlık harici satır sayısı
        start = self.scrollPos(); end = min(start + rows, len(_inputs))
        for r, i in enumerate(range(start, end), start=1):
            item = _inputs[i]
            label = item.label() if hasattr(item, 'label') else None
            text = item.text() if hasattr(item, 'text') else ''
            if label: data += label; r += 1
            data = '> ' if cur == i else '  '; data += text
            self.out_write(data, r, 0)
    def _render_son(self):
        pass
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
        result = self.onKeyPressed_araIslem(key, _key, duration)
        if result != True:
            if _key == 'esc' or _key == 'f1':
                self.close()
                return True
            elif _key == 'enter':
                item = self.curInput()
                if not item: return None
                if hasattr(item, 'parentPart') and callable(item.parentPart): item.parentPart(self)
                else: setattr(item, '_parentPart', self)
                if hasattr(item, 'run') and callable(item.run): item.run()
                return True
            elif _key == 'up':
                self.selectPrevInput()
            elif _key == 'down':
                self.selectNextInput()
            else: return False
        if result is None: result = True
        self.render()
        return result                                                                                              # key handled by part or Internal result
    def onKeyPressed_araIslem(self, key, _key, duration=None):
        return None
    def onAttrChanged(self, defer=None):
        if defer is None: defer = True
        if not defer and self.active():
            self._rendered = False
            self.render()
        return self
    def selectFirstInput(self):
        return self.selectInput('_first')
    def selectLastInput(self):
        return self.selectInput('_last')
    def selectNextInput(self):
        return self.selectInput('_next')
    def selectPrevInput(self):
        return self.selectInput('_prev')
    def selectInput(self, nameOrDirectionOrIndex):
        if not nameOrDirectionOrIndex:
            return self
        name = nameOrDirectionOrIndex; old = self.curInputInd()
        new = old if isinstance(name, int) else \
              0 if name == '_first' else \
              len(self.inputs)[-1] if name == '_last' else \
              old + 1 if name == '_next' else \
              old - 1 if name == '_prev' else \
              self.inputs.index(name)
        if new is not None: self.curInputInd(new)
        print('selectInput:', name, new, ' old:', old)
        return self
    def _toggleSnapshot(self, revert=False):
        return self
    def out_write(self, data, row=0, col=0, _internal=False):
        self.stdout().write(data, row, col, _internal)
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
