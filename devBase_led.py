### devBase.py (Ortak Modül)

from common import *
from config import hw

class BaseLED:
    def __init__(self):
        pass
    def write(self, color):
        if isinstance(color, str):
            color = color.upper()
            # (G, R, B)
            color = (
                (0x00, 0x00, 0x00) if color == 'SIYAH'   or color == 'BLACK'   else \
                (0xFF, 0xFF, 0xFF) if color == 'BEYAZ'   or color == 'WHITE'   else \
                (0x00, 0xFF, 0x00) if color == 'YESIL'   or color == 'GREEN'   else \
                (0x00, 0x00, 0xFF) if color == 'MAVI'    or color == 'BLUE'    else \
                (0xFF, 0x00, 0x00) if color == 'KIRMIZI' or color == 'RED'     else \
                (0xFF, 0xFF, 0x00) if color == 'SARI'    or color == 'YELLOW'  else \
                (0xFF, 0x00, 0xFF) if color == 'MOR'     or color == 'PURPLE'  else \
                (0xFF, 0x80, 0x00) if color == 'TURUNCU' or color == 'ORANGE'  else \
                (0x00, 0xFF, 0xFF) if color == 'TURKUAZ' or color == 'CYAN'    else \
                None
            )
        if color is None:
            raise Exception(f'Renk değeri hatalı: [{color}]')
        return self._write(color)
    def _write(self, color):
        return self
    def clear(self):
        return self
    def brightness(self, value):
        return self
