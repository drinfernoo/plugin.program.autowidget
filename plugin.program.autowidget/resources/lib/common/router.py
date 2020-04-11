import xbmc
import xbmcplugin

import sys

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl
    
from resources.lib import edit
from resources.lib import menu
from resources.lib import manage
from resources.lib import convert
from resources.lib.common import migrate
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
    
    category = 'AutoWidget'
    is_dir = False
    is_type = 'files'

    utils.ensure_addon_data()
    migrate.migrate_groups()
    
    mode = params.get('mode', '')
    action = params.get('action', '')
    group = params.get('group', '')
    path = params.get('path', '')
    target = params.get('target', '')
    
    if not mode:
        is_dir, category = menu.root_menu()
    elif mode == 'manage':
        if action == 'add_group':
            manage.add_group(target)
        elif action == 'add_path' and group and target:
            manage.add_path(group, target)
        elif action == 'shift_path' and group and path and target:
            edit.shift_path(group, path, target)
        elif action == 'edit':
            if not path:
                edit.edit_dialog(group)
            else:
                edit.edit_dialog(group, path)
    elif mode == 'path':
        if action == 'call' and group and path:
            menu.call_path(group, path)
        elif action == 'random' and group:
            is_dir, category = menu.random_path_menu(group)
            is_type = 'videos'
        elif action == 'shortcuts' and group:
            is_dir, category = menu.shortcut_menu(group)
            is_type = 'videos'
    elif mode == 'group':
        if not group:
            is_dir, category = menu.groups_menu()
        elif target:
            if target == 'shortcut':
                is_dir, category = menu.shortcut_menu(group)
                is_type = 'videos'
            elif target == 'widget':
                is_dir, category = menu.widget_menu(group)
    elif mode == 'tools':
        is_dir, category = menu.tools_menu()
    elif mode == 'force':
        convert.refresh_paths(notify=True, force=True)
    elif mode == 'wipe':
        utils.wipe()
    elif mode == 'clean':
        manage.clean()

    if is_dir:
        xbmcplugin.setPluginCategory(_handle, category)
        xbmcplugin.setContent(_handle, is_type)
        xbmcplugin.endOfDirectory(_handle)
