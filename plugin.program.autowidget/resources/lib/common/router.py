import xbmc
import xbmcplugin

import re

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl
    
from resources.lib import backup
from resources.lib import edit
from resources.lib import menu
from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import directory
from resources.lib.common import utils


def _log_params(_plugin, _handle, _params):
    params = dict(parse_qsl(_params))
    logstring = ''
    
    for param in params:
        logstring += '[ {0}: {1} ] '.format(param, params[param])
    
    if not logstring:
        logstring = '[ Root Menu ]'

    utils.log(logstring, level=xbmc.LOGNOTICE)

    return params
    
    
def dispatch(_plugin, _handle, _params):
    _handle = int(_handle)
    params = _log_params(_plugin, _handle, _params)
    category = 'AutoWidget'
    is_dir = False
    is_type = 'files'

    utils.ensure_addon_data()
    
    mode = params.get('mode', '')
    action = params.get('action', '')
    group = params.get('group', '')
    path = params.get('path', '')
    path_id = params.get('path_id', '')
    target = params.get('target', '')
    widget_id = params.get('id', '')
    
    if not mode:
        is_dir, category = menu.root_menu()
    elif mode == 'manage':
        if action == 'add_group':
            manage.add_group(target)
        elif action == 'add_path' and group and target:
            manage.add_path(group, target)
        elif action == 'shift_path' and group and path_id and target:
            edit.shift_path(group, path_id, target)
        elif action == 'edit':
            edit.edit_dialog(group, path_id)
        elif action == 'edit_widget':
            edit.edit_widget_dialog(target)
    elif mode == 'path':
        if action == 'call' and path_id:
            menu.call_path(path_id)
        elif action in ['static', 'cycling'] and group:
            is_dir, category = menu.path_menu(group, action, widget_id)
        elif action == 'merged' and group:
            is_dir, category = menu.merged_path(group, widget_id)
        elif action == 'update' and target:
            refresh.update_path(widget_id, path, target)
        is_type = 'videos'
    elif mode == 'group':
        if not group:
            is_dir, category = menu.my_groups_menu()
        elif target:
            is_dir, category = menu.group_menu(group, target, widget_id)
    elif mode == 'widget':
        is_dir, is_category = menu.active_widgets_menu()
    elif mode == 'refresh':
        if not target:
            refresh.refresh_paths()
        else:
            refresh.refresh(target, force=True, single=True)
    elif mode == 'tools':
        is_dir, category = menu.tools_menu()
    elif mode == 'force':
        refresh.refresh_paths(notify=True, force=True)
    elif mode == 'skindebug':
        xbmc.executebuiltin('Skin.ToggleDebug')
    elif mode == 'wipe':
        utils.wipe()
    elif mode == 'clean':
        manage.clean(notify=True)
    elif mode == 'set_color':
        utils.set_color(setting=True)
    elif mode == 'backup' and action:
        if action == 'location':
            backup.location()
        elif action == 'backup':
            backup.backup()
        elif action == 'restore':
            backup.restore()

    if is_dir:
        directory.add_sort_methods(_handle)
        xbmcplugin.setPluginCategory(_handle, category)
        xbmcplugin.setContent(_handle, is_type)
        xbmcplugin.endOfDirectory(_handle)
