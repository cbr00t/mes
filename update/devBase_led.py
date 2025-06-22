### devBase.py (Ortak Modül)

class BaseLED:
    def write(self, rgb, col):
        return self
    def clear(self, col):
        return self.write((0, 0, 0), col)
