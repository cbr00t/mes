### devBase.py (Ortak Modül)

from common import *
from config import hw

class BaseLED:
    def __init__(self):
        self.state = NS(
            # led, brightness
            last = [None, 0]
        )
        pass
    def write(self, color):
        feed()
        if color is None:
            color = ''
        if isinstance(color, str):
            color = color.upper()
            # color = color or 'KAPALI'
            # if color == 'KAPALI':
            #     self.brightness(hw.led.brightness)
            #     return self
            
            # (G, R, B)
            color = (
                (0x00, 0x00, 0x00) if color in ('SIYAH', 'BLACK', 'KAPALI', 'OFF') else \
                (0xFF, 0xFF, 0xFF) if color == 'BEYAZ'   or color == 'WHITE'   else \
                (0x00, 0xFF, 0x00) if color == 'YESIL'   or color == 'GREEN'   else \
                (0x00, 0x00, 0xFF) if color == 'MAVI'    or color == 'BLUE'    else \
                (0xFF, 0x00, 0x00) if color == 'KIRMIZI' or color == 'RED'     else \
                (0xFF, 0xFF, 0x00) if color == 'SARI'    or color == 'YELLOW'  else \
                (0xFF, 0x00, 0xFF) if color == 'MOR'     or color == 'PURPLE'  else \
                (0x00, 0xFF, 0xFF) if color == 'TURKUAZ' or color == 'CYAN'    else \
                (0xAA, 0x40, 0x00) if color == 'TURUNCU' or color == 'ORANGE'  else \
                (0xFF, 0x45, 0x00) if color == 'ORANGERED' else \
                (0xFF, 0x45, 0x00) if color in ('ORANGERED',) else \
                (0xFF, 0x64, 0x00) if color in ('AMBER',) else \
                (0xFF, 0x00, 0x80) if color in ('ROSE', 'MAGENTA_RED') else \
                (0x80, 0x32, 0x00) if color in ('DARKAMBER', 'AMBER_DIM') else \
                (0x80, 0x00, 0x00) if color in ('BROWN',) else \
                None
            )
        if color is None:
            raise Exception(f'Renk değeri hatalı: [{color}]')
        l = self.state.last
        if color == l[0]:
            return self
        result = self._write(color)
        l[0] = color
        if not l[1]:
            self.brightness()
        return result
    def _write(self, color):
        return self
    def clear(self):
        self.write('SIYAH')
        return self
    def brightness(self, value):
        feed()
        result = self._brightness(value)
        l = self.state.last
        if value is not None:
            l[1] = value
        return result
    def _brightness(self, value):
        return self
