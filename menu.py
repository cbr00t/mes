from common import *
from part_base import  *

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
        if value is None:
            return self._text or ''
        # set
        self._text = value
        return self
    def call(self, sender=None, *args, **kwargs):
        return None
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
    def call(self, sender=None, *args, **kwargs):
        super().call(sender, *args, **kwargs)
        if not self.isCallable(): return None
        if sender is not None:
            _cls = sender.__class__
            _cls.Run(_source=self.items())
        return None

class MenuItem(Menu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        h = shared.handlers                                                           # shared => from common import *
        if isinstance(_action, str):
            handler = getattr(h, _action, None)
        if not callable(_action): return None
        try:
            return handler(*args, **kwargs)
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
