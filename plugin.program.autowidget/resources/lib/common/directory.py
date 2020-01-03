import xbmcgui
import xbmcplugin

import six
import sys

if six.PY3:
    from urllib.parse import quote_plus
elif six.PY2:
    from urllib import quote_plus

    
def add_menu_item(title, params=None, description='', isFolder=False):
    _plugin = sys.argv[0]
    _handle = int(sys.argv[1])
    _params = sys.argv[2][1:]

    if params is not None:
        mode = quote_plus(params.get('mode', ''))
        _plugin += '?{0}={1}'.format('mode', mode)
        
        for param in params:
            if param == 'mode':
                continue
                
            # build URI to send to router
            _param = quote_plus(params.get(param, ''))
            _plugin += '&{0}={1}'.format(param, _param)

    # build list item
    item = xbmcgui.ListItem(title)
    xbmcplugin.addDirectoryItem(handle=_handle, url=_plugin, listitem=item,
                                isFolder=isFolder)