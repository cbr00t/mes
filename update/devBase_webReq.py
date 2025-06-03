### devBase.py (Ortak Modül)

class BaseWebReq:
    def __init__(self):
        self._initSession()
    def send(self, url, timeout=None):
        return None
    def sendText(self, url, timeout=None):
        result = self.send(url, timeout).text
        print(result)
        return result
    def sendJSON(self, url, timeout=None):
        result = self.send(url, timeout).json()
        print(result)
        return result
    def _initSession(self):
        return self
