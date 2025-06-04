from common import *
from part_base import  *

class Menu(NS):
    def __init__(self, *args, **kwargs):
        super().__init(*args, **kwargs)
    @classmethod
    def isSubMenu(cls):
        return False
    def isCallable(self):
        return self.enabled()
    def enabled(self, value=None):
        # getter
        return True if self._enabled is None else self._enabled
        # setter
        self._enabled = value
        return self
    def call(self, sender=None, *args, **kwargs):
        return None
    def id(value=None):
        # getter
        if value is None:
            result = self._id
            if not result:
                result = self._id = str(self.newID())
            return result
        #setter
        self._id = value
        return self
    @classmethod
    def newID(cls):
        result = cls.lastId = (cls.lastId or 0) + 1
        return result

class SubMenu(Menu):
    def __init__(self, *args, **kwargs):
        super().__init(*args, **kwargs)
        self.items(self._items)
    @classmethod
    def isSubMenu(cls):
        return True
    def items(self, value=None):
        # getter
        return self._items or []
        # setter
        self._items = value or []
        return self
    def call(self, sender=None, *args, **kwargs):
        super().call(sender, *args, **kwargs)
        if not self.isCallable(): return None
        if sender is not None:
            _cls = sender.__class__
            _cls.Run(_source=self.items())
        return None

class MenuItem(Menu):
    def __init__(self, *args, **kwargs):
        super().__init(*args, **kwargs)
    def action(self, value=None):
        # getter
        return self._action
        # setter
        self._action = value
        return self
    def call(self, sender=None, *args, **kwargs):
        super().call(sender, *args, **kwargs)
        if not self.isCallable(): return None
        _action = self.action()
        if not _action: return None
        if isinstance(action, str):
            handler = getattr(h, action, None)
        if not isinstance(action, callable): return None
        try:
            return handler(*args, **kwargs)
        except Exception as ex:
            # print(f'[ERROR]  menu handler execution failed: {ex}')
            raise ex

class MenuSeparator(MenuItem):
    def enabled(self, value=None):
        # get
        return False
    def text(self, value=None):
        # get 
        from part_base import Part
        return '-' * Part.maxLenLimit()
