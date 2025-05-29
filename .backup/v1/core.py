# ==================== core.py ====================
from common import *
from config import mod

class Device:
    def __init__(self, **kwargs):
        self.eth = kwargs.get('eth')
        self.req = kwargs.get('req')
        self.sock = kwargs.get('sock')
        self.lcd = kwargs.get('lcd')

# Initialization
if not 'dev' in globals():
    dev = None
def getDevice():
    modName_device = mod.device or ('rasppico' if isCircuitPy() else 'local')
    print(f'Device Module = {modName_device}')
    safeImport(f'dev_{modName_device}', 'mod_dev')
    print(dev)
    return dev
