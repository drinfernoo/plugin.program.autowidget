import xbmc
import xbmcplugin

import six
import sys

if six.PY3:
    from urllib.parse import parse_qsl
elif six.PY2:
    from urlparse import parse_qsl
    

def _log_params(_plugin, _handle, _params):
    params = dict(parse_qsl(_params))
    
    logstring = '{0} ({1}): '.format(_plugin, _handle)
    for param in params:
        logstring += '[ {0}: {1} ] '.format(param, params[param])

    xbmc.log(logstring, level=xbmc.LOGNOTICE)

    return params
    
def dispatch(_plugin, _handle, _params):
    _handle = int(_handle)
    params = _log_params(_plugin, _handle, _params)
    
    mode = params.get('mode', '')
    
    if not mode:
        from resources.lib import menu
        menu.root()
        
    elif mode == 'path':
        action = params.get('action', '')
        group = params.get('group', '')
        
        if action == 'random':
            pass
            # path = path_utils.get_random_path(group)
            
    elif mode == 'group':
        action = params.get('action', '')
        
        if action == 'add':
            from resources.lib import path_utils
            path_utils.add_group()
        elif action == 'view':
            from resources.lib import menu
            
            group = params.get('group', '')
            menu.show_group(group)
        elif action == 'edit':
            from resources.lib import window
            
            group = params.get('group', '')
            window.show_window(group)
    elif mode == 'force':
        from resources.lib import path_utils
        path_utils.inject_paths(notify=True)
    
    xbmcplugin.endOfDirectory(_handle)
