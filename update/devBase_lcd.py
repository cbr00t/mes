from common import *
from config import hw
from time import sleep, monotonic

class BaseLCD:
    @classmethod
    def __init__(self):
        self._lastWriteTime = None
        size = self.getRowCols()
        self._buffer = [['' for _ in range(size.cols)] for _ in range(size.rows)]          # lcd matrix data buffer
    @classmethod
    def getRowCols(cls):
        cfg = hw.lcd
        return NS(rows = cfg.rows, cols = cfg.cols)
    @classmethod
    def getRows(cls):
        return cls.getRowCols().rows
    @classmethod
    def getCols(cls):
        return cls.getRowCols().cols
    def _read(self, asString=False):
        buf = self._buffer
        return [''.join(row) for row in buf] if asString else buf
    def readMatrix(self):
        return [row[:] for row in self._buffer]
    def readBuffer(self):
        return self._read(False)
    def readLines(self):
        return '\n'.join(self.readLines())
    def readString(self):
        return self.readLines().join('\n')
    def write(self, data, row=0, col=0, _internal=False):
        if not _internal: self._lastWriteTime = monotonic()
        rowCount = self.getRows()
        if not (0 <= row < rowCount): return self
        buf = self._buffer
        for i, ch in enumerate(data):
            if col + i < len(buf[row]):
                buf[row][col + i] = ch
        return self
    def clearLine(self, row):
        if isinstance(row, range): row = range(row.start, row.stop + 1)
        if isinstance(row, (list, range)):
            for _row in row: self.clearLine(_row)
            return self
        self.write(' ' * hw.lcd.cols, row, 0, True)
        self._lastWriteTime = None
        return self
    def clear(self):
        self._lastWriteTime = None
        self._buffer = [['' for _ in range(len(row))] for row in self._buffer]
        return self
    def writeIfReady(self, data, row=0, col=0,  _internal=False):
        if not lcdIsBusy():
            return self.write(data, row, col, _internal)
    def clearLineIfReady(self, row):
        if lcdCanBeCleared():
            return self.clearLine(row)
    def clearIfReady(self):
        if lcdCanBeCleared():
            return self.clear()
    def on(self):
        return self
    def off(self):
        return self
    def _printBuffer(self):
        cols = shared.dev.lcd.getCols(); limit = cols + 4
        lines = self._read(asString=True)
        print('#' * limit)
        for line in lines:
            text = line.ljust(cols)
            print(f'# {text} #')
        print('#' * limit)
        print()
