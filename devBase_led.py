### devBase.py (Ortak Modül)

class BaseLED:
    def write(self, rgb):
        return self
    def clear(self):
        return self.write((0, 0, 0))
