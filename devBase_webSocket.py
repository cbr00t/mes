# ---------- devBase_ws.py (BaseWebSocket) ----------
from common import *
from config import local, server as srv

class BaseWebSocket:
    def __init__(self):
        qs = {'key': 'mes'}
        url = getWSUrl(qs, wsPath='ws/genel', api='webSocket')
        # MicroPython bazen 'http' yerine 'ws' bekler; güvenlik için düzelt:
        if url.startswith("http://"):
            url = "ws://" + url[len("http://"):]
        elif url.startswith("https://"):
            url = "wss://" + url[len("https://"):]
        self.url = url
        self.ws = None
        self._lastSend = None
        self._lastRecv = None
    # ---- lifecycle ---------------------------------------------------------
    def isConnected(self):
        return self.ws is not None
    async def open(self):
        """Public open; çağıran kod bunu kullanır."""
        url = self.url
        try:
            print("ws connecting to:", url)
            ok = await self._open()
            if ok:
                print("! ws_open", url)
            return ok
        except Exception as ex:
            print("[ERROR] ws open:", ex); print_exception(ex)
            await self.close()
            return False
    async def _open(self):
        """Platform-özel bağlantı: alt sınıfta (MicroPython/CPython) override edilir."""
        raise NotImplementedError()
    async def close(self):
        if self.ws:
            try:
                # uwebsockets ve websockets kütüphaneleri için ortak kapanış
                maybe_coro = getattr(self.ws, 'close', None)
                if callable(maybe_coro):
                    res = maybe_coro()
                    if hasattr(res, '__await__'):
                        await res
            except Exception as ex:
                print("[WARN] ws close:", ex)
            finally:
                self.ws = None
        return True
    # ---- ws helpers --------------------------------------------------------
    async def send(self, text: str):
        if not self.ws:
            raise RuntimeError('WebSocket not connected')
        try:
            send_fn = getattr(self.ws, 'send', None)
            if not callable(send_fn):
                raise RuntimeError('ws.send not available')
            # print('[DEBUG] ws before send')
            res = send_fn(text)
            # print('[DEBUG] ws before send - await')
            if hasattr(res, '__await__'):
                await res
            # print('[DEBUG] ws after send - await')
            self._lastSend = monotonic()
            await asleep(.05)
            # debug:
            # print(">>", text)
            return True
        except Exception as ex:
            msg = ex.args[0] if ex.args and ex.args[0] else str(ex)
            print(f'[ERROR] ws recv: {msg}')
            print_exception(ex)
            await self.close()
            return False
    async def recv(self, timeout=None):
        if not self.ws:
            return None
        try:
            recv_fn = getattr(self.ws, 'recv', None)
            if not callable(recv_fn):
                raise RuntimeError('ws.recv not available')
            # print('[DEBUG] ws before recv')
            res = recv_fn()
            # print('[DEBUG] ws before recv - await')
            if hasattr(res, '__await__'):
                text = await asyncio.wait_for(res, timeout) if timeout else await res
            else:
                text = res
            # print('[DEBUG] ws after recv - await')
            if text is None:
                return None
            self._lastRecv = monotonic()
            await asleep(.05)
            return text
        # except asyncio.TimeoutError:
        #     print('[WARN] ws recv timeout')
        #     return None
        except Exception as ex:
            msg = ex.args[0] if ex.args and ex.args[0] else str(ex)
            print(f'[ERROR] ws recv: {msg}')
            if ex.__class__.__name__.lower() not in ('timeouterror', 'timeout'):
                print_exception(ex)
            return None

    # ---- protocol (JSON payload) ------------------------------------------
    async def wsSend(self, api, args=None, data=None, wsPath=None):
        """Sunucuya JSON komutu gönderir."""
        args = args or {}
        args['.ip'] = ip2Str(local.ip)
        payload = getWSData(api, args=args, data=data, wsPath=wsPath)
        text = json.dumps(payload)
        return await self.send(text)
    async def wsRecv(self, timeout=None):
        """Sunucudan JSON bekler, çözüp dict/list döndürür."""
        text = await self.recv(timeout or srv.socketTimeout)
        # print('******************* text = ', text)
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            # plain text dönebilir; ham veriyi dön
            return text
    async def wsTalk(self, api, args=None, data=None, wsPath=None, timeout=None):
        """Gönder + cevap bekle (tek istek/tek cevap)."""
        if not self.isConnected():
            return None
        if not await self.wsSend(api, args, data, wsPath):
            return None
        return await self.wsRecv(timeout or srv.socketTimeout)
    # ---- app-level checks (heartbeat/status) -------------------------------
    async def wsHeartbeatIfNeed(self):
        if not self.isConnected():
            return False
        if not heartbeatShouldBeChecked():
            return False
        try:
            if await self.wsSend('ping'):
                shared.lastTime.heartbeat = monotonic()
                return True
        except Exception as ex:
            print("[ERROR] wsHeartbeat:", ex); print_exception(ex)
        return False
