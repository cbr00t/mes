### devBase.py (Ortak Modül)

class BaseKeypad:
    def __init__(self, onPressed=None, onReleased=None):
        self._lastKeyPressTime = self._lastKeyReleaseTime = None
        self.onPressed = onPressed; self.onReleased = onReleased
        pass
    async def loop(self):
        return self
    async def update(self):
        return self
    def set_onPressed(self, handler):
        self.onPressed = handler
        return self
    def set_onReleased(self, handler):
        self.onReleased = handler
        return self
