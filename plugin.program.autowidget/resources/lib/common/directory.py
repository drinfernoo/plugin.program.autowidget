import xbmc
import xbmcgui
import xbmcplugin

import string
import sys

import six

from resources.lib.common import utils

try:
    from urllib.parse import urlencode
    from urllib.parse import unquote
except ImportError:
    from urllib import urlencode
    from urllib import unquote

_sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED,
                 xbmcplugin.SORT_METHOD_LABEL,
                 xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
                 xbmcplugin.SORT_METHOD_DATE,
                 xbmcplugin.SORT_METHOD_TITLE,
                 xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
                 xbmcplugin.SORT_METHOD_LASTPLAYED]

sync = utils.get_art('sync.png')

    
def add_separator(title='', char='-', sort=''):
    _window = utils.get_active_window()

    props = None
    if sort:
        props = {'specialsort': sort}
    
    if _window != 'media':
        return

    if title:
        if isinstance(title, int):
            title = utils.get_string(title)
            
        split = (len(title) + 2) / 2
        edge = char * int(40 - split)
        add_menu_item(title='{0} {1} {0}'.format(edge,
                                                 string.capwords(title)),
                      art=sync,
                      props=props)
    else:
        add_menu_item(title=char * 80, art=sync, props=props)


def add_sort_methods(handle):
    for method in _sort_methods:
        xbmcplugin.addSortMethod(handle, method)
        
    
def add_menu_item(title, params=None, path=None, info=None, cm=None, art=None,
                  isFolder=False, props=None):
    _plugin = sys.argv[0]
    _handle = int(sys.argv[1])
    _params = sys.argv[2][1:]

    if params is not None:
        if 'path' in params:
            encode = {k: params[k] for k, v in params.items() if k != 'path'}
        else:
            encode = params
        
        _plugin += '?{}'.format(urlencode(encode))
        
        if 'path' in params:
            _plugin += '&path={}'.format(params['path'])
    elif path is not None:
        _plugin = path

    if isinstance(title, int):
        title = utils.get_string(title)

    def_info = {}
    if info:
        def_info = info

    # build list item
    item = xbmcgui.ListItem(title)
    item.setInfo('video', def_info)
    item.setMimeType(def_info.get('mimetype', ''))
    item.setArt(art if art else {})
    item.addContextMenuItems(cm if cm else [])
    
    if props:
        item.setProperties(props)

    xbmcplugin.addDirectoryItem(handle=_handle, url=_plugin, listitem=item,
                                isFolder=isFolder)
