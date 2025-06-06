### part.py
from common import *
from part_base import  *

class InputPart(Part):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._val = self._val or ''
        self._curPos = self._curPos or len(self.val())
    def renderStartPos(self):
        return 2
    def editable(self):
        return True
    def val(self, value=None):
        # get
        if value is None: return self._val or ''
        # set
        self._val = value or ''
        return self
    def curPos(self, value=None):
        _maxLen = self._maxLen or 0; _maxLen0 = max(_maxLen - 1, 0)
        # get
        if value is None:
            _pos = self._curPos or 0
            return min(_pos, _maxLen0)
        # set
        value = value or 0;
        self._curPos = 0 if value <= 0 else min(value, _maxLen0)
        return self
    def onKeyPressed_araIslem(self, key, _key, duration=None):
        result = super().onKeyPressed_araIslem(key, _key, duration)
        if result is not None: return result
        _val = self.val()
        if _key == 'enter':
            if self.commitInput():
                self.close()
            return True
        elif _key == 'esc' or _key == 'x':
            if _key == 'esc':
                self.close(); return True
            if _val:
                _val = _val[:-1]; self.val(_val)
                self.curPrev()
        elif _key == 'up':
            self.curPrev()
        elif _key == 'down':
            self.curNext()
        else:
            maxLen = self.maxLen() - self.renderStartPos()
            if len(_val) + 1 < maxLen:
                _val += key; self.val(_val)
                if self.commitInput(): _val = self.val(); self.curNext()
                else: _val = self.val()[:-1]; self.val(_val)
        self.render()
        return True
    def _render_son(self):
        super()._render_son()
        start = self.renderStartPos(); cur = self.curPos()
        self.out_write(self.val(), 1, start)
        self.out_write('^', 2, start + cur)
    def commitInput(self, data=None):
        if not self.editable(): return False
        if data is None: data = self.val()
        if not self.validateInput(data): return False
        result = self.processInput(data)
        return result
    def curNext(self):
        self.curPos(self.curPos() + 1)
        return self
    def curPrev(self):
        self.curPos(self.curPos() - 1)
        return self
    def curToStart(self):
        self.curPos(0)
        return self
    def curToEnd(self):
        self.curPos(-1)
        return self
