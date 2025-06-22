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
    def readLines(self):
        return [''.join(line) for line in self._read(False)]
    def readString(self):
        return '\n'.join(self.readLines())
    def write(self, data, row=0, col=0, _internal=False):
        if not _internal: self._lastWriteTime = monotonic()
        rowCount = self.getRows()
        if not (0 <= row < rowCount): return self
        buf = self._buffer
        for i, ch in enumerate(data):
            if col + i < len(buf[row]):
                buf[row][col + i] = ch
        return self
    def writeLine(self, data, row=0, col=0, _internal=False):
        self.clearLine(row)
        return self.write(data, row, col, internal)
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
        cols = self.getCols(); rows = self.getRows()
        self._buffer = [['' for _ in range(cols)] for _ in range(rows)]
        return self
    def writeIfReady(self, data, row=0, col=0, _internal=False):
        if lcdIsBusy(): return self
        if not _internal:
            cur = self._buffer[row]; old = ''.join(cur[col : col + len(data)])
            if data == old: return self
        return self.write(data, row, col, _internal)
    def writeLineIfReady(self, data, row=0, col=0, _internal=False):
        self.clearLineIfReady(row)
        return self.writeIfReady(data, row, col, _internal)
    def clearLineIfReady(self, row, _internal=False):
        if lcdIsBusy(): return self
        if isinstance(row, range): row = range(row.start, row.stop + 1)
        if isinstance(row, (list, range)):
            for _row in row: self.clearLineIfReady(_row)
            return self
        if not _internal:
            if ''.join(self._buffer[row]).strip() == '': return self
        return self.clearLine(row)
    def clearIfReady(self):
        if lcdIsBusy(): return self
        for r in range(self.getRows()):
            self.clearLineIfReady(r)
        return self
        # return self.clear()
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
