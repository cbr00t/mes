### part.py
from common import *
from part_base import  *

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
