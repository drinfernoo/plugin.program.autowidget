import xbmcgui
import xbmcplugin

import string
import sys

import six

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

    
def add_menu_item(title, params=None, path=None, info=None, cm=None, art=None,
                  isFolder=False, sort=None):
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
    elif path is not None:
        _plugin = path

    if isinstance(title, int):
        title = utils.get_string(title)
    
    def_info = {}
    if info:
        def_info = {x: info[x] for x in info if x not in ['type']}
        def_info['mediatype'] = info.get('type', 'video')

        for key in info:
            i = info.get(key)
            if any(key == x for x in ['artist', 'cast']):
                if not i:
                    def_info[key] = []
                elif not isinstance(i, list):
                    def_info[key] = [i]
                elif isinstance(i, list) and key == 'cast':
                    cast = []
                    for actor in i:
                        cast.append((actor['name'], actor['role']))
                    def_info[key] = cast
            elif isinstance(i, list):
                def_info[key] = ' / '.join(i)
            elif key == 'type':
                def_info['mediatype'] = i
            else:
                def_info[key] = six.text_type(i)
    
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
    if sort:
        item.setProperty('SpecialSort', sort)
    
    xbmcplugin.addDirectoryItem(handle=_handle, url=_plugin, listitem=item,
                                isFolder=isFolder)
