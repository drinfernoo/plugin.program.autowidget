import xbmcgui
import xbmcplugin

import six
import sys

if six.PY3:
    from urllib.parse import quote_plus
elif six.PY2:
    from urllib import quote_plus

    
def add_menu_item(title, params=None, description='', isFolder=False):
    u = sys.argv[0]

    if params is not None:
        u += "?{0}={1}".format('mode', quote_plus(params.get('mode', "")))
        
        for param in params:
            if param == 'mode':
                continue
                
            # build URI to send to router
            u += "&{0}={1}".format(param, quote_plus(params.get(param, "")))

    # build list item
    item = xbmcgui.ListItem(title)
    item.setInfo(type="video", infoLabels={"title": title})

    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u,
                                     listitem=item, isFolder=isFolder)
    return ok