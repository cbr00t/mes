### part.py
from common import *
from part_base import  *

class MenuPart(Part):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source(self._source or [], defer=True)
    def editable(self):
        return True
    def source(self, value=None, defer=False):
        from menu import SubMenu
        # get
        if value is None:
            result = self._source
            _args = []; _kwargs = {}
            if isinstance(result, tuple):
                result, *_rest = result
                if len(_rest) >= 1: _args = _rest[0]
                if len(_rest) == 2: _kwargs = _rest[1]
            if isinstance(result, str):
                h = shared.handlers
                result = getattr(h, result, None)
            if callable(result):
                result = result(*_args, **_kwargs)
            return result
        # set
        old = self._source
        _source = value or []
        if _source:
            _source = _source.items() if isinstance(_source, SubMenu) else \
                      _source if isinstance(_source, (str, tuple, list)) or callable(_source) else \
                      [_source]
        _source = self._source = _source or []
        inputs = self._inputs = {}
        _lastId = self._lastId or 0
        for item in _source:
            text = item.get('text') if isinstance(item, dict) else item.text
            # if not text: continue
            id = item.get('id') if isinstance(item, dict) else item.id
            if not id:
                _lastId += 1; id = str(_lastId)
                if isinstance(item, dict): item['id'] = id
                else: item.id = id
            inputs[id] = item
        if not defer: self.onAttrChanged()
        return self
    def onKeyPressed_araIslem(self, key, _key, duration=None):
        result = super().onKeyPressed_araIslem(key, _key, duration)
        if result is not None: return result
        if _key == 'enter':
            item = self.curInput()
            if not item: return None
            if item.isCallable(): item.call(sender=self)
            return True
        return None
    def _render(self):
        super()._render()
        inputs = self._inputs; cur = self.curInputInd()
        i = -1; r = 0
        if cur is None: cur = -1
        # ** aslında self.scrollPos() da tutulup, scroll varsa, cur. item indisi row=2 de olacak sekilde render edilmeli
        for item in inputs.values():
            i += 1; r += 1
            data = '> ' if cur == i else '  '
            data += item.text()
            self.out_write(data, r, 0)

# p = MenuPart(_source = [ NS(text='item1') ]).source([ NS(id='i1', text='item2'), NS(id='i2', text='item3'), NS(text='item4') ]); p._inputs

