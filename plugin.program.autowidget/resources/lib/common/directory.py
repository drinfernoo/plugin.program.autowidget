import xbmcgui
import xbmcplugin

import string
import sys

from resources.lib.common import utils

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

    
def add_separator(title='', char='-'):
    _window = utils.get_active_window()
    sync = utils.get_art('sync.png')

    if _window != 'media':
        return

    if title:
        if isinstance(title, int):
            title = utils.get_string(title)
            
        split = (len(title) + 2) / 2
        edge = char * int(40 - split)
        add_menu_item(title='{0} {1} {0}'.format(edge,
                                                 string.capwords(title)),
                      art=sync)
    else:
        add_menu_item(title=char * 80, art=sync)

    
def add_menu_item(title, params=None, info=None, cm=None, art=None,
                  isFolder=False):
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

    if isinstance(title, int):
        title = utils.get_string(title)
    
    def_info = {}
    if info:
        def_info.update(info)
        for key in def_info:
            if any(key == i for i in ['artist', 'cast']):
                i = def_info[key]
                if not i:
                    def_info[key] = []
                elif not isinstance(i, list):
                    def_info[key] = [def_info[key]]
    
    def_art = {}
    if art:
        def_art.update(art)
    
    def_cm = []    
    if cm:
        def_cm.extend(cm)
        
    # build list item
    item = xbmcgui.ListItem(title)
    item.setInfo('video', def_info)
    item.setArt(def_art)
    item.addContextMenuItems(def_cm)
    
    xbmcplugin.addDirectoryItem(handle=_handle, url=_plugin, listitem=item,
                                isFolder=isFolder)
