### devBase.py (Ortak Modül)
from common import *
# from config import hw
from mfrc522 import MFRC522

class BaseRFID:
    def __init__(self):
        self.lastCard = [0]
        reader = self.reader = MFRC522(spi_id=0,sck=2,miso=4,mosi=3,cs=1,rst=0)
        reader.init()
    def reset(self):
        self.lastCard = [0]
        return self
    async def read(self):
        reader = self.reader
        lastCard = self.lastCard
        (stat, tag_type) = reader.request(reader.REQIDL)
        if stat != reader.OK:
            self.reset()
            return None
        (stat, uid) = reader.SelectTagSN()
        if uid == lastCard:
            return None
        if stat != reader.OK:
            self.reset()
            return None        
        print('debug6')
        print("Card detected {}  uid={}".format(hex(int.from_bytes(bytes(uid),"little",False)).upper(),reader.tohexstring(uid)))
        if reader.IsNTAG():
            print("Got NTAG{}".format(reader.NTAG))
            reader.MFRC522_Dump_NTAG(Start=0, End=reader.NTAG_MaxPage)
            #print("Write Page 5  to 0x1,0x2,0x3,0x4  in 2 second")
            #utime.sleep(2)
            #data = [1,2,3,4]
            #reader.writeNTAGPage(5,data)
            #reader.MFRC522_Dump_NTAG(Start=5,End=6)
        else:
            (stat, tag_type) = reader.request(reader.REQIDL)
            if stat != reader.OK:
                self.reset()
                return None
            (stat, uid2) = reader.SelectTagSN()
            if not (stat == reader.OK and uid == uid2):
                return None
            defaultKey = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
            reader.MFRC522_DumpClassic1K(uid, Start=0, End=64, keyA=defaultKey)
        lastCard = self.lastCard = uid
        await asleep(.05)
        return None

