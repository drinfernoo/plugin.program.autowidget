import xbmc
import xbmcplugin

import sys

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl
    
from resources.lib import menu
from resources.lib import path_utils
from resources.lib.common import utils


def _log_params(_plugin, _handle, _params):
    params = dict(parse_qsl(_params))
    
    logstring = ''
    for param in params:
        logstring += '[ {0}: {1} ] '.format(param, params[param])

    utils.log(logstring, level=xbmc.LOGNOTICE)

    return params
    
def dispatch(_plugin, _handle, _params):
    _handle = int(_handle)
    params = _log_params(_plugin, _handle, _params)
    
    mode = params.get('mode', '')
    action = params.get('action', '')
    group = params.get('group', '')
    path = params.get('path', '')
    
    if not mode:
        menu.root_menu()
    elif mode == 'tools':
        menu.tools_menu()
    elif mode == 'path':
        if action == 'random':
            menu.random_path_menu(group)
        elif action == 'call':
            xbmc.executebuiltin(path)
    elif mode == 'group':
        if action == 'add':
            path_utils.edit_group()
        elif action == 'remove':
            path_utils.remove_group(group)
        elif action == 'edit':
            path_utils.edit_group(group)
        elif action == 'view':
            menu.group_menu(group)
    elif mode == 'force':
        path_utils.refresh_paths(notify=True, force=True)
    elif mode == 'clean':
        utils.clean_old_widgets()
        utils.clean_old_strings()
    
    xbmcplugin.endOfDirectory(_handle)
