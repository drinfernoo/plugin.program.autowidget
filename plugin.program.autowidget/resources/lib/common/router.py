import xbmc
import xbmcplugin

import re

try:
    from urllib.parse import parse_qsl
    from urllib.parse import quote_plus
    from urllib.parse import unquote
except ImportError:
    from urllib import quote_plus
    from urlparse import parse_qsl
    from urlparse import unquote
    
from resources.lib import backup
from resources.lib import edit
from resources.lib import menu
from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import directory
from resources.lib.common import utils

info_match_pattern = '\$INFO\[(.*)\]'
encoded_info_match_pattern = '%24INFO\%5b(.*)\%5d'
path_match_pattern = '\&path=(.*)'
path_sub_pattern = '&path={}'
reload_match_pattern = '(%26reload%3d.*)'


def _log_params(_plugin, _handle, _params):
    info_match = re.search(info_match_pattern, _params, flags=re.I)
    encoded_info_match = re.search(encoded_info_match_pattern, _params, flags=re.I)
    if info_match:
        label_match = info_match.groups()[0]
        _params = re.sub(info_match_pattern, utils.get_infolabel(label_match),
                         _params, flags=re.I)
    elif encoded_info_match:
        label_match = unquote(encoded_info_match.groups()[0])
        _params = re.sub(encoded_info_match_pattern, utils.get_infolabel(label_match),
                         _params, flags=re.I)
    
    path_match = re.search(path_match_pattern, _params, flags=re.I)
    if path_match:
        match = path_match.groups()[0]
        
        
        _params = re.sub(path_match_pattern,
                         '',
                         _params,
                         flags=re.I)
        _params += path_sub_pattern.format(quote_plus(match))
        reload_match = re.search(reload_match_pattern, _params, flags=re.I)
        if reload_match:
            match = reload_match.groups()[0]
            _params = re.sub(reload_match_pattern,
                             unquote(match),
                             _params,
                             flags=re.I)
    
    params = dict(parse_qsl(_params))
    logstring = ''
    
    for param in params:
        params[param] = unquote(params[param])
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
        if action == 'call' and path:
            menu.call_path(path)
        elif action in ['static', 'cycling'] and group:
            is_dir, category = menu.path_menu(group, action, _id, path)
        elif action == 'merged' and group:
            is_dir, category = menu.merged_path(group, _id)
        elif action == 'update' and path and target:
            refresh.update_path(_id, path, target)
        is_type = 'videos'
    elif mode == 'group':
        if not group:
            is_dir, category = menu.my_groups_menu()
        elif target:
            is_dir, category = menu.group_menu(group, target, _id)
    elif mode == 'widget':
        is_dir, is_category = menu.active_widgets_menu()
    elif mode == 'refresh':
        if not target:
            refresh.refresh_paths()
        else:
            refresh.refresh(target, force=True)
            utils.update_container()
    elif mode == 'tools':
        is_dir, category = menu.tools_menu()
    elif mode == 'force':
        refresh.refresh_paths(notify=True, force=True)
    elif mode == 'skindebug':
        xbmc.executebuiltin('Skin.ToggleDebug')
    elif mode == 'wipe':
        utils.wipe()
    elif mode == 'clean':
        manage.clean()
    elif mode == 'set_color':
        utils.set_color()
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
