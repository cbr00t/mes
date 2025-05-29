### 📁 devBase.py (Yrtak Modül)
from common import *
import config as cfg
import json

class BaseRawSocket:
    def __init__(self):
        self.server = cfg.server
        self.sock = None

    def isConnected(self):
        return self.sock is not None

    def close(self):
        try: self.sock.close()
        except: pass
        self.sock = None
        print(f'! sock_close')
        return self

    def talk(self, data):
        self.write(data)
        return self.read()

    def _prepareData(self, data):
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data += "\n"
            return data.encode("utf-8")
        elif isinstance(data, bytes):
            return data + b"\n"
        raise TypeError("RawSocket.write(): data must be str, dict or bytes")

    def _decodeLine(self, buffer):
        line = buffer.split(b"\n", 1)[0]
        try:
            data = line.decode('utf-8-sig').strip()
            print(f'< sock_recv {len(data)} Bytes: [{data}]')
            return json.loads(data)
        except Exception as e:
            return {"_parseError": str(e), 'raw': line.decode(errors='ignore') if line else ''}


class BaseWebReq:
    def sendText(self, url):
        result = self.send(url).text
        print(result)
        return result

    def sendJSON(self, url):
        result = self.send(url).json()
        print(result)
        return result
