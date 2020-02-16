import xbmc
import xbmcplugin

import sys

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl
    
from resources.lib import menu
from resources.lib import manage
from resources.lib import process
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
    target = params.get('target', '')
    
    if not mode:
        menu.root_menu()
    elif mode == 'manage':
        if action == 'add_group':
            manage.add_group(target)
        elif action == 'remove_group' and group:
            manage.remove_group(group)
        elif action == 'add_path' and group and target:
            manage.add_path(group, target)
        # elif action == 'remove_path' and path:
            # manage.remove_path(path)
    elif mode == 'path':
        if action == 'call' and path:
            window = utils.get_active_window()
            
            if window == 'home':
                xbmc.executebuiltin('Dialog.Close(busydialog)')
            
            if not path.startswith('ActivateWindow') and target:
                path = 'ActivateWindow({},{},return)'.format(target, path)
            
            if window != 'dialog':
                xbmc.executebuiltin(path)
        elif action == 'random' and group:
            menu.random_path_menu(group)
        elif action == 'shortcuts' and group:
            menu.shortcut_menu(group)
    elif mode == 'group' and group:
        menu.group_menu(group)
    elif mode == 'force':
        process.refresh_paths(notify=True, force=True)
    elif mode == 'clean':
        utils.clean_old_widgets()
        utils.clean_old_strings()
    
    xbmcplugin.endOfDirectory(_handle)
