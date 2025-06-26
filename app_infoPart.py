from common import *
from config import local
from part_base import *
from menu import *

class InfoPart(Part):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source(self._source or self.defaultSource(), defer=True)
    def defaultSource(self):
        return None
    def source(self, value=None, defer=False):
        # get
        if value is None:
            result = self._source
            if isinstance(result, tuple):
                result, *_res = result
                if len(_res) >= 1: _args = _res[0]
                if len(_res) == 2: _kwargs = _res[1]
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
        _lastId = self._lastId or 0
        if isinstance(_source, Menu): _source.parentPart(self)
        for _item in _source:
            item = NS(text = _item) if isinstance(_item, str) else _item
            text = item.get('text') if isinstance(item, dict) else item.text
            # if not text: continue
            id = item.get('id') if isinstance(item, dict) else item.id
            if not id:
                _lastId += 1; id = str(_lastId)
                if isinstance(item, dict): item['id'] = id
                else: item.id = id
            if hasattr(item, 'parentPart') and callable(item.parentPart): item.parentPart(self)
            else: setattr(item, 'parentPart', self)
            self.addInput(id, item)
        self.onAttrChanged()
        return self

class DeviceInfoPart(InfoPart):
    def title(self):
        # get
        return 'CIHAZ BILGISI'
    def defaultSource(self):
        from config import local, server as srv, app
        return [
            f'Ver :{version2Str(app.version)}',
            f'D.IP:{ip2Str(local.ip)}',
            f'S.IP:{ip2Str(srv.ip)}',
            f'Port:{srv.rawPort}'
        ]
