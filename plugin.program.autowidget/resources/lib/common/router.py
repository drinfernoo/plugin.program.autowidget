import xbmc
import xbmcplugin

import sys

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl
    
from resources.lib import backup
from resources.lib import edit
from resources.lib import menu
from resources.lib import manage
from resources.lib import refresh
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
    target = params.get('target', '')
    _id = params.get('id', '')
    
    if not mode:
        is_dir, category = menu.root_menu()
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    elif mode == 'manage':
        if action == 'add_group':
            manage.add_group(target)
        elif action == 'add_path' and group and target:
            manage.add_path(group, target)
        elif action == 'shift_path' and group and path and target:
            edit.shift_path(group, path, target)
        elif action == 'edit':
            edit.edit_dialog(group, path)
        elif action == 'edit_widget':
            edit.edit_widget_dialog(target)
    elif mode == 'path':
        if action == 'call' and group and path:
            menu.call_path(group, path)
        elif action == 'random' and group:
            is_dir, category = menu.random_path(group)
        elif action == 'next' and group:
            is_dir, category = menu.next_path(group)
        elif action == 'merged' and group:
            is_dir, category = menu.merged_path(group)
    elif mode == 'group':
        if not group:
            is_dir, category = menu.my_groups_menu()
            xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL)
        elif target:
            is_dir, category = menu.group_menu(group, target, _id)
            xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    elif mode == 'widget':
        is_dir, is_category = menu.active_widgets_menu()
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    elif mode == 'refresh':
        if not target:
            refresh.refresh_paths(notify=True)
        else:
            refresh.refresh(target, force=True)
    elif mode == 'tools':
        is_dir, category = menu.tools_menu()
        xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    elif mode == 'force':
        refresh.refresh_paths(notify=True, force=True)
    elif mode == 'wipe':
        utils.wipe()
    elif mode == 'clean':
        manage.clean()
    elif mode == 'backup' and action:
        if action == 'location':
            backup.location()
        elif action == 'backup':
            backup.backup()
        elif action == 'restore':
            backup.restore()

    if is_dir:
        xbmcplugin.setPluginCategory(_handle, category)
        xbmcplugin.setContent(_handle, is_type)
        xbmcplugin.endOfDirectory(_handle)
