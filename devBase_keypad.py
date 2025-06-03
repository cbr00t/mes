### devBase.py (Ortak Modül)

class BaseKeypad:
    def __init__(self, onPress = None, onRelease = None):
        self._lastKeyPressTime = self._lastKeyReleaseTime = None
        pass
    def update(self):
        return self
    def set_onPress(self, handler):
        self.onPress = handler
        return self
    def set_onRelease(self, handler):
        self.onRelease = handler
        return self
