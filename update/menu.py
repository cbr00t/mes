from common import *

class Menu(NS):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    @classmethod
    def isSubMenu(cls):
        return False
    def isCallable(self):
        return self.enabled()
    def enabled(self, value=None):
        # get
        return True if self._enabled is None else self._enabled
        # set
        self._enabled = value
        return self
    def parentPart(self, value=None):
        # get
        if value is None: return self._parentPart
        # set
        self._parentPart = value
        return self
    def id(self, value=None):
        # get
        if value is None:
            result = self._id
            if not result:
                result = self._id = str(self.newID())
            return result
        # set
        self._id = value
        return self
    def text(self, value=None):
        # get
        if value is None: return self._text or ''
        # set
        self._text = value
        return self
    def label(self, value=None):
        # get
        return None
    def run(self, *args, **kwargs):
        return None
    def close(self):
        _parentPart = self.parentPart()
        if _parentPart: _parentPart.close()
        return self
    @classmethod
    def newID(cls):
        result = cls.lastId = (cls.lastId or 0) + 1
        return result

class SubMenu(Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items(self._items)
    @classmethod
    def isSubMenu(cls):
        return True
    def items(self, value=None):
        # get
        return self._items or []
        # set
        self._items = value or []
        return self
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)
        if not self.isCallable(): return None
        from part_menu import MenuPart
        part = MenuPart(_title = self.text(), _source = self, *args, **kwargs)
        part.run()
        return part

class MenuItem(Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def action(self, value=None):
        # getter
        return self._action
        # setter
        self._action = value
        return self
    def run(self, sender=None, *args, **kwargs):
        super().run(sender, *args, **kwargs)
        if not self.isCallable(): return None
        _action = self.action()
        if not _action: return None
        _locals = { 'self': self, 'sender': sender } 
        try:
            if isinstance(_action, str):
                exec(_action, globals(), _locals)
                __action = _locals.get('callback', None)
                if __action is not None: _action = __action
            if not callable(_action): return None
            try: return _action(self, sender, *args, **kwargs)
            except:
                try: return _action(sender, *args, **kwargs)
                except:
                    try: return _action(*args, **kwargs)
                    except: return _action()
        except Exception as ex:
            # print(f'[ERROR]  menu handler execution failed: {ex}')
            raise ex

class MenuSeparator(MenuItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def enabled(self, value=None):
        # get
        return False
    def text(self, value=None):
        # get 
        from part_base import Part
        return '-' * Part.maxLenLimit()
