from common import *
from config import hw

class BaseLCD:
    @classmethod
    def __init__(self):
        self._rc_status = hw.lcd.rc_status
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
        rowCount = self.getRows(); colCount = self.getCols()
        if row < 0: row = rowCount + row      # !!  (rowCount + (-value)
        if col < 0: col = colCount + col      # !!  (colCount + (-value)
        if not (0 <= row < rowCount):
            return self
        buf = self._buffer
        self.move(row, col)
        for i, ch in enumerate(data):
            if col + i < colCount:
                old = buf[row][col+i] or ''
                if ch != old:
                    buf[row][col+i] = ch
                    self._writeChar(ch)
        return self
    def _writeChar(self, ch, row=None, col=None):
        return self
    def clearLine(self, row):
        if isinstance(row, range):
            row = range(row.start, row.stop + 1)
        if isinstance(row, (list, range)):
            for _row in row:
                self.clearLine(_row)
            return self
        cols = hw.lcd.cols
        data = ' ' * cols
        self.write(data, row, 0, True)
        self._lastWriteTime = None
        return self
    def writeLine(self, data, row=0, col=0, _internal=False):
        lines = self.readLines()
        if row < len(lines):
            line = lines[row]
            segment = line[col:col + len(data)]
        if segment.strip() == data.strip():
            # print(f'!! same lcd line segment: [{data}]')
            return self
        if col > 0:
            _data = ' ' * (col - 1)
            self.write(_data, row, 0, True)
        result = self.write(data, row, col, _internal)
        endOffset = col + len(data)
        padding = hw.lcd.cols - endOffset
        if padding > 0:
            _data = ' ' * padding
            self.write(_data, row, endOffset, True)
        if col == 0:
            self.move(row, col)    # for fast cursor seek in same line
        return result
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
        if lcdIsBusy(): return self
        return self.writeLine(data, row, col, _internal)
    def clearLineIfReady(self, row, _internal=False):
        if lcdIsBusy():
            return self
        if isinstance(row, range):
            row = range(row.start, row.stop + 1)
        if isinstance(row, (list, range)):
            for _row in row: self.clearLineIfReady(_row)
            return self
        if not _internal and ''.join(self._buffer[row]).strip() == '':
            return self
        return self.clearLine(row)
    def clearIfReady(self):
        if lcdIsBusy():
            return self
        for r in range(self.getRows()):
            self.clearLine(r)
        return self
        # return self.clear()
    def writeStatus(self, ch):
        rcs = self._rc_status
        if rcs:
            self.write(ch or ' ', *rcs)
            # self.write(ch or ' ', rcs[0], rcs[1])
        return self
    def clearStatus(self, ch):
        return self.writeStatus(None)
    def move(self, row=0, col=0):
        return self
    def on(self):
        return self
    def off(self):
        return self
    def blink(self):
        return self
    def unblink(self):
        return self
    def showCursor(self):
        return self
    def hideCursor(self):
        return self
    def _printBuffer(self):
        cols = shared.dev.lcd.getCols(); limit = cols + 4
        lines = self._read(asString=True)
        print('#' * limit)
        for line in lines:
            text = ljust(line, cols)
            print(f'# {text} #')
        print('#' * limit)
        print()
