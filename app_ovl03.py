from common import *
from config import local
from menu import SubMenu, MenuItem
from time import sleep, monotonic
import json
from traceback import print_exception

def getMenu_main():
    items = getMenuItems_main()
    return SubMenu(_text = 'ANA MENU', _items = items) if items else None
def getMenuItems_main():
    return [
        MenuItem(_text = 'item1', _action = "print('item 1')"),
        SubMenu(_text = 'item2', _items = [
            MenuItem(_text = 'sub-item1', _action = "print(self.text())"),
            MenuItem(_text = 'sub-item2', _action = "print(self.text())"),
            MenuItem(_text = 'sub-item3', _action = "print('sub-item 3')"),
            MenuItem(_text = 'sub-item4', _action = "print('sub-item 4')"),
            MenuItem(_text = 'sub-item5', _action = "print('sub-item 5')"),
            MenuItem(_text = 'CIKIS', _action = "self.close()")
        ]),
        MenuItem(_text = 'CIKIS', _action = "self.close()")
    ]
def getMenu_duraksamaNedenleri():
    def action(self, *args, **kwargs):
        sock = shared.dev.sock
        sock.wsTalk('baslatDurdur', { 'durNedenKod': self.id() })
    recs = getDuraksamaNedenleri()
    items = [MenuItem(_id = rec.get('kod'), _text = rec.get('aciklama'), _action = action) for rec in recs] if recs else None
    print('items:', items)
    if items: items.append(MenuItem(_text = 'CIKIS', _action = "self.close()"))
    return SubMenu(_title = 'Duraksama Secimi', _items = items) if items else None
def getDuraksamaNedenleri():
    cache = shared._globals; result = cache.duraksamaNedenleri
    if not result:
        sock = shared.dev.sock
        result = sock.wsTalk('duraksamaNedenleri')
        cache.duraksamaNedenleri = result
    return result
