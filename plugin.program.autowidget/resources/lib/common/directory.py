import xbmcgui
import xbmcplugin

import sys

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus
    
    
def add_separator(title=''):
    if title:
        split = (len(title) + 2) / 2
        edge = '-' * (40 - split)
        add_menu_item(title='{} {} {}'.format(edge, title.capitalize(), edge))
    else:
        add_menu_item(title='-' * 80)

    
def add_menu_item(title, params=None, description='', art={}, isFolder=False):
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
    if art:
        item.setArt(art)
    
    xbmcplugin.addDirectoryItem(handle=_handle, url=_plugin, listitem=item,
                                isFolder=isFolder)