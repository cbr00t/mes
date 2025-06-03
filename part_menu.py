### part.py
from common import *
from part_base import  *

class MenuPart(Part):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source(self._source or [], defer=True)
    def source(self, value=None, defer=False):
        # Getter
        if value is None:
            return self._source
        # Setter
        old = self._source
        self._source = value or []
        _inputs = self._inputs = {}
        _lastId = self._lastId or 0
        for item in self._source or []:
            text = item.get('text') if isinstance(item, dict) else item.text
            # if not text: continue
            id = item.get('id') if isinstance(item, dict) else item.id
            if not id:
                _lastId += 1; id = str(_lastId)
                if isinstance(item, dict): item['id'] = id
                else: item.id = id
            _inputs[id] = item
        if not defer: self.onAttrChanged()
        return self
    def render(self):
        super.render(self)


# p = MenuPart(_source = [ NS(text='item1') ]).source([ NS(id='i1', text='item2'), NS(id='i2', text='item3'), NS(text='item4') ]); p._inputs

