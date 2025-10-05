from common import *
from config import local
from menu import SubMenu, MenuItem

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
    def defAction(self, *args, **kwargs):
        sock = shared.dev.sock
        if sock.wsTalk('baslatDurdur', { 'durNedenKod': self.id() }):
            self.close()
    # def action_close(self, *args, **kwargs):
    #     self.close()
    recs = getDuraksamaNedenleri()
    items = [MenuItem(_id = rec.get('kod'), _text = rec.get('aciklama'), _action = defAction) \
                for rec in recs] if recs else None
    print('items:', items)
    if items: items.append(MenuItem(_text = 'CIKIS', _action = "self.close()"))
    return SubMenu(_text = 'Duraksama Secimi', _items = items) if items else None
def getDuraksamaNedenleri():
    cache = shared._globals; result = cache.duraksamaNedenleri
    if not result:
        sock = shared.dev.sock
        result = sock.wsTalk('duraksamaNedenleri')
        if isinstance(result, str): result = json.loads(result)
        cache.duraksamaNedenleri = result
    return result
