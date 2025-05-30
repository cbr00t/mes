# ==================== core.py ====================
from common import *
from config import mod

class Device:
    def __init__(self, **kwargs):
        self._eth = kwargs.get('_eth')
        self.eth = kwargs.get('eth')
        self.req = kwargs.get('req')
        self.sock = kwargs.get('sock')
        self.lcd = kwargs.get('lcd')
        self.keypad = kwargs.get('keypad')

# Initialization
if not 'dev' in globals():
    dev = None
def getDevice():
    modName_device = mod.device or ('rasppico' if isCircuitPy() else 'local')
    print(f'Device Module = {modName_device}')
    if dev is None:
        dynImport(f'dev_{modName_device}', 'mod_dev')
        print(dev)
    return dev

