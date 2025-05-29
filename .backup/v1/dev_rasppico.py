from common import *
import core
import config as cfg
from time import sleep
for name in ['board', 'busio', 'digitalio', 'adafruit_requests', 'adafruit_connection_manager']:
    safeImport(name)
try:
    from lcd.lcd import LCD
    from lcd.i2c_pcf8574_interface import I2CPCF8574Interface
except Exception as ex:
    print(ex)
try:
    from adafruit_wiznet5k.adafruit_wiznet5k import WIZNET5K
except Exception as ex:
    print(ex)


# ---------- Ethernet Class ----------
class Eth:
    def __init__(self):
        self._cs = digitalio.DigitalInOut(board.GP17)
        self._spi = busio.SPI(board.GP18, board.GP19, board.GP16)
    def init(self):
        local = cfg.local; is_dhcp = not cfg.ip
        self.eth = WIZNET5K(self._spi, self._cs, is_dhcp=is_dhcp)
        if not is_dhcp:
            self._eth.ifconfig = (local.ip, local.subnet, local.gateway, local.dns)
        return self.eth

# ---------- Web Requests Class ----------
class WebReq:
    def __init__(self):
        pool = self._pool = adafruit_connection_manager.get_radio_socketpool(dev.eth)
        self.session = adafruit_requests.Session(pool, None)
    def send(self, url):
        print(f'get request: {url}')
        result = self.session.get(url)
        print(f'... result: [{result}]')
        return result
    def sendText(self, url):
        result = self.send(url).text
        print(result)
        return result
    def sendJSON(self, url):
        result = self.send(url).json()
        print(result)
        return result

# ---------- Raw TCP Socket Class ----------
class RawSocket:
    def __init__(self):
        self.server = cfg.server
        self.sock = None
        self._pool = adafruit_connection_manager.get_radio_socketpool(dev.eth)
    def isConnected(self):
        return not self.sock is None
    def open(self):
        srv = self.server
        sock = self.sock = self._pool.socket()
        ep = (ip2Str(srv.ip), srv.rawPort)
        sock.connect(ep)
        print(f'! sock_open: [{ep[0]}:{ep[1]}]')
        return self
    def read(self, timeout=0.05):
        if not self.isConnected():
            return None
        sock = self.sock; buffer = b""
        try:
            # 1. Blocking + timeout (örneğin 50ms)
            sock.settimeout(timeout)
            try:
                chunk = sock.recv(4096)
                buffer += chunk
            except Exception:
                # Veri yoksa veya timeout olduysa => None dön
                return None
            # 2. Veri geldiyse → blocking moda geç, '\n' gelene kadar oku
            self.sock.settimeout(None)  # sonsuza kadar bekle
            while b"\n" not in buffer:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break    # bağlantı kapandı
                    buffer += chunk
                except Exception:
                    break
        except Exception as ex:
            print("[SocketError]", ex)
            self.close()
        # 3. Satırı ayır
        line = buffer.split(b"\n", 1)[0]
        try:
            data = line.decode('utf-8-sig').strip()
            size = len(data)
            print(f'< sock_recv {size} Bytes: [{data}]')
            return json.loads(data)
        except Exception as e:
            return {
                "_parseError": str(e),
                'raw': data if 'data' in locals() else buffer.decode(errors='ignore')
            }
    def write(self, data):
        if not self.isConnected():
            return None
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data += "\n"
            buffer = data.encode("utf-8")
        elif isinstance(data, bytes):
            buffer = data + b"\n"
        else:
            raise TypeError("RawSocket.write(): data must be str, dict or bytes")
        sock = self.sock; totalSize = 0
        try:
            while totalSize < len(buffer):
                size = sock.send(buffer[totalSize:])
                if size == 0:
                    raise RuntimeError('Socket connection broken during send')
                totalSize += size
        except Exception as ex:
            print("[SocketError]", ex)
            self.close()
            return self
        print(f'> sock_send {totalSize} Bytes: [{data}]')
        return self
    def close(self):
        try: self.sock.close()
        except: pass
        self.sock = None
        print(f'! sock_close')
        return self
    def talk(self, data):
        self.write(data)
        result = self.read()
        return result

# ---------- LED Control Class ----------
class LED:
    def __init__(self):
        i2c = busio.I2C(board.GP1, board.GP0)
        interface = I2CPCF8574Interface(i2c, 0x27)
        self.lcd = LCD(interface, num_rows=4, num_cols=20)
    def clear(self):
        self.lcd.clear()
        return self
    def write(self, data, row=0, col=0):
        lcd = self.lcd
        lcd.set_cursor_pos(row, col)
        lcd.print(data)
        return self


# ---------- Device Initialization ----------
dev = core.dev = core.Device()
def setup_eth(): dev.eth = Eth().init()
def setup_req(): dev.req = WebReq()
def setup_sock(): dev.sock = RawSocket()
def setup_led(): dev.led = LED()

steps = []
if ('Eth' in globals()): steps.append(setup_eth)
steps.extend([setup_req, setup_sock])
if ('LED' in globals()): steps.append(setup_eth)
for step in steps:
    withErrCheck(step)
