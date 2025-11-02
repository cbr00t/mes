# microws.py — Minimal, asenkron WebSocket istemcisi (MicroPython, ws://)
# - uasyncio tabanlı
# - client->server TÜM frame'ler maskeli (RFC6455)
# - Kolay API: start(), send(), send_json(), close()
# - Otomatik yeniden bağlanma, heartbeat (ping/pong)
# Not: Bu sürüm WSS/TLS içermez.

import uasyncio as asyncio
import usocket as socket
import ubinascii, urandom, ustruct
import time
try:
    import ujson as json
except:
    import json

__all__ = ["MicroWS"]

# -------- Basit asenkron kuyruk --------
class _SimpleQueue:
    def __init__(self, maxsize=0):
        self._buf = []
        self._max = maxsize
    async def put(self, item):
        while self._max and len(self._buf) >= self._max:
            await asyncio.sleep_ms(5)
        self._buf.append(item)
    async def get(self):
        while not self._buf:
            await asyncio.sleep_ms(5)
        return self._buf.pop(0)

# -------- Yardımcılar: framing & IO --------
def _gen_key():
    rnd = bytes([urandom.getrandbits(8) for _ in range(16)])
    return ubinascii.b2a_base64(rnd).strip().decode()

def _build_handshake(host_header, path="/"):
    key = _gen_key()
    return (
        "GET {p} HTTP/1.1\r\n"
        "Host: {h}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: {k}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    ).format(p=path, h=host_header, k=key).encode()

def _mask_payload(payload):
    mask = bytes([urandom.getrandbits(8) for _ in range(4)])
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return mask, masked

def _frame(opcode, payload=b""):
    # Client -> Server TÜM frame'ler maskeli olmalı
    frame = bytearray()
    frame.append(0x80 | (opcode & 0x0F))  # FIN=1 + opcode
    ln = len(payload)
    maskbit = 0x80
    if ln <= 125:
        frame.append(maskbit | ln)
    elif ln < 65536:
        frame.append(maskbit | 126)
        frame += ustruct.pack("!H", ln)
    else:
        frame.append(maskbit | 127)
        frame += ustruct.pack("!Q", ln)
    mask, masked = _mask_payload(payload)
    frame += mask
    return bytes(frame) + masked

def _frame_text(s): return _frame(0x1, s.encode())
def _frame_ping():  return _frame(0x9, b"")
def _frame_pong():  return _frame(0xA, b"")
def _frame_close(): return _frame(0x8, b"")

async def _nb_sendall(sock, data):
    view = memoryview(data)
    sent = 0
    total = len(view)
    while sent < total:
        try:
            n = sock.send(view[sent:]) or 0
            sent += n
        except OSError as e:
            if getattr(e, 'args', [None])[0] in (11, 110, 115):  # EAGAIN/EINPROGRESS
                await asyncio.sleep_ms(0)
                continue
            raise
        await asyncio.sleep_ms(0)

async def _nb_recv(sock, nbytes, timeout_ms=10000):
    buf = bytearray()
    start = time.ticks_ms()
    while len(buf) < nbytes:
        if timeout_ms is not None and time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
            raise OSError("recv timeout")
        try:
            chunk = sock.recv(nbytes - len(buf))
            if chunk:
                buf += chunk
            else:
                await asyncio.sleep_ms(0)
        except OSError as e:
            if getattr(e, 'args', [None])[0] in (11, 115):
                await asyncio.sleep_ms(0)
                continue
            raise
    return bytes(buf)

async def _nb_read_until(sock, pattern=b"\r\n\r\n", maxlen=4096, timeout_ms=10000):
    buf = bytearray()
    plen = len(pattern)
    start = time.ticks_ms()
    while True:
        if timeout_ms is not None and time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
            raise OSError("read_until timeout")
        try:
            ch = sock.recv(1)
            if ch:
                buf += ch
                if len(buf) >= plen and buf[-plen:] == pattern:
                    return bytes(buf)
                if len(buf) > maxlen:
                    raise OSError("header too long")
            else:
                await asyncio.sleep_ms(0)
        except OSError as e:
            if getattr(e, 'args', [None])[0] in (11, 115):
                await asyncio.sleep_ms(0)
                continue
            raise

# -------- Ana sınıf --------
class MicroWS:
    """
    Kullanım:
        ws = MicroWS("192.168.1.6", 8080, "/")
        asyncio.create_task(ws.start(on_message=cb))
        await ws.send("hello")
        await ws.close()
    """
    def __init__(self, ip, port, path="/", reconnect=True, heartbeat_s=15, send_q_size=50):
        self.ip = ip
        self.port = port
        self.path = path
        self.reconnect = reconnect
        self.heartbeat_s = heartbeat_s
        self.sock = None
        self._running = False
        self._send_q = _SimpleQueue(maxsize=send_q_size)
        # Callbacks
        self.on_open = None
        self.on_message = None   # str veya JSON parse edilmiş obje
        self.on_close = None
        self.on_error = None

    # ---- Public API ----
    async def start(self, on_message=None, on_open=None, on_close=None, on_error=None):
        if on_message: self.on_message = on_message
        if on_open:    self.on_open = on_open
        if on_close:   self.on_close = on_close
        if on_error:   self.on_error = on_error
        while True:
            try:
                await self._run_once()
                if not self.reconnect:
                    break
                await asyncio.sleep(3)
            except Exception as e:
                await self._call(self.on_error, e)
                if not self.reconnect:
                    break
                await asyncio.sleep(3)

    async def send(self, text):
        await self._send_q.put(text)

    async def send_json(self, obj):
        await self._send_q.put(json.dumps(obj))

    async def close(self):
        self._running = False
        try:
            if self.sock:
                try:
                    await _nb_sendall(self.sock, _frame_close())
                except:
                    pass
                self.sock.close()
        except:
            pass

    # ---- Dahili ----
    async def _call(self, cb, *args):
        if not cb:
            return
        try:
            r = cb(*args)
            # async callback ise await et
            if hasattr(r, "__await__"):
                await r
        except:
            pass

    async def _connect(self):
        s = socket.socket()
        s.setblocking(False)
        try:
            try:
                s.connect((self.ip, self.port))
            except OSError as e:
                if getattr(e, 'args', [None])[0] not in (115, 106, 118, 120, 150):
                    raise
            req = _build_handshake("%s:%d" % (self.ip, self.port), self.path)
            await _nb_sendall(s, req)
            header_bytes = await _nb_read_until(s, b"\r\n\r\n", maxlen=4096, timeout_ms=8000)
            try:
                header = header_bytes.decode()
            except:
                header = str(header_bytes)
            if (" 101 " not in header) or ("upgrade: websocket" not in header.lower()):
                raise OSError("handshake failed:\n" + header)
            self.sock = s
            self._running = True
        except Exception:
            try:
                s.close()
            except:
                pass
            raise

    async def _sender(self):
        while self._running:
            msg = await self._send_q.get()
            try:
                await _nb_sendall(self.sock, _frame_text(msg))
            except Exception as e:
                await self._call(self.on_error, e)
                self._running = False
            await asyncio.sleep_ms(0)

    async def _receiver(self):
        while self._running:
            try:
                hdr = await _nb_recv(self.sock, 2, timeout_ms=15000)
                b1, b2 = hdr[0], hdr[1]
                opcode = b1 & 0x0F
                ln = b2 & 0x7F
                if ln == 126:
                    ext = await _nb_recv(self.sock, 2)
                    ln = ustruct.unpack("!H", ext)[0]
                elif ln == 127:
                    ext = await _nb_recv(self.sock, 8)
                    ln = ustruct.unpack("!Q", ext)[0]
                masked = bool(b2 & 0x80)
                mask = await _nb_recv(self.sock, 4) if masked else None
                payload = await _nb_recv(self.sock, ln) if ln else b""
                if mask:
                    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

                if opcode == 0x1:
                    try:
                        txt = payload.decode()
                        try:
                            obj = json.loads(txt)
                            await self._call(self.on_message, obj)
                        except ValueError:
                            await self._call(self.on_message, txt)
                    except:
                        await self._call(self.on_message, payload)
                elif opcode == 0x8:
                    self._running = False
                elif opcode == 0x9:
                    try:
                        await _nb_sendall(self.sock, _frame_pong())
                    except:
                        self._running = False
                # 0xA (pong): geç
            except Exception as e:
                await self._call(self.on_error, e)
                self._running = False
            await asyncio.sleep_ms(0)

    async def _heartbeater(self):
        if not self.heartbeat_s or self.heartbeat_s < 5:
            return
        while self._running:
            try:
                await _nb_sendall(self.sock, _frame_ping())
            except Exception as e:
                await self._call(self.on_error, e)
                self._running = False
            await asyncio.sleep(self.heartbeat_s)

    async def _run_once(self):
        await self._connect()
        await self._call(self.on_open)
        t1 = asyncio.create_task(self._sender())
        t2 = asyncio.create_task(self._receiver())
        t3 = asyncio.create_task(self._heartbeater())
        try:
            await asyncio.gather(t1, t2, t3)
        finally:
            await self._call(self.on_close)
            try:
                if self.sock:
                    self.sock.close()
            except:
                pass
            self.sock = None
            self._running = False
