import xbmc
import xbmcaddon
import xbmcgui

import random
import uuid

from resources.lib import manage
from resources.lib.common import directory
from resources.lib.common import utils

add = utils.get_art('add.png')
alert = utils.get_art('alert.png')
folder = utils.get_art('folder.png')
folder_add = utils.get_art('folder-add.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
folder_next = utils.get_art('folder-next.png')
refresh = utils.get_art('refresh.png')
remove = utils.get_art('remove.png')
share = utils.get_art('share.png')
shuffle = utils.get_art('shuffle.png')
sync = utils.get_art('sync.png')
tools = utils.get_art('tools.png')
unpack = utils.get_art('unpack.png')

_addon = xbmcaddon.Addon()

label_warning_shown = _addon.getSettingBool('label.warning')


def _warn():
    dialog = xbmcgui.Dialog()
    dialog.ok('AutoWidget', 'The unique identifier in the number in this path\'s label is [B]necessary[/B] for AutoWidget to refresh it correctly. Don\'t change the label given to this widget, or it may be unable to update correctly. This wessage [COLOR firebrick]will not[/COLOR] be shown again.')
    
    _addon.setSetting('label.warning', 'true')
    label_warning_shown = True


def root_menu():
    directory.add_menu_item(title=32007,
                            params={'mode': 'group'},
                            art=folder,
                            isFolder=True)
    directory.add_menu_item(title=32008,
                            params={'mode': 'tools'},
                            art=tools,
                            isFolder=True)
    return True, 'AutoWidget'

    
def tools_menu():
    directory.add_menu_item(title=32006,
                            params={'mode': 'force'},
                            art=refresh,
                            info={'plot': _addon.getLocalizedString(32020)},
                            isFolder=False)
    directory.add_menu_item(title=32066,
                            params={'mode': 'clean'},
                            art=remove,
                            isFolder=False)    
    directory.add_menu_item(title=32064,
                            params={'mode': 'wipe'},
                            art=remove,
                            isFolder=False)
    return True, _addon.getLocalizedString(32008)
                            
                            
def my_groups_menu():
    if len(manage.find_defined_groups()) > 0:
        for group in manage.find_defined_groups():
            group_name = group['label']
            group_id = group['id']
            group_type = group['type']
            
            cm = [(_addon.getLocalizedString(32061),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=edit'
                   '&group={})').format(group_id))]
            
            directory.add_menu_item(title=group_name,
                                    params={'mode': 'group',
                                            'group': group_id,
                                            'target': group_type},
                                    info=group.get('info'),
                                    art=group.get('art') or (folder_shortcut if group_type == 'shortcut' else folder_sync),
                                    cm=cm,
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32068,
                                art=alert,
                                isFolder=False)
    return True, _addon.getLocalizedString(32007)
    
    
def group_menu(group_id, target):
    _id = uuid.uuid4()
    _window = utils.get_active_window()
    
    group = manage.get_group_by_id(group_id)
    if not group:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'.format(group_id),
                  level=xbmc.LOGERROR)
        return
    
    group_name = group['label'].decode('utf-8')
    
    paths = manage.find_defined_paths(group_id)
    if paths:
        cm = []
        art = folder_shortcut if target == 'shortcut' else folder_sync
        
        for idx, path in enumerate(paths):
            if _window == 'media':
                cm = _create_context_items(group_id, path['id'], idx, len(paths))
            
            directory.add_menu_item(title=path['label'],
                                    params={'mode': 'path',
                                            'action': 'call',
                                            'group': group_id,
                                            'path': path['id'],
                                            'id': str(_id)},
                                    info=path.get('info'),
                                    art=path.get('art') or art,
                                    cm=cm,
                                    isFolder=False)
        if target == 'widget':
            directory.add_separator(title=32010, char='/')

            title = _addon.getLocalizedString(32028).format(_id)
            description = _addon.getLocalizedString(32029).format(group_name)
            
            rand = random.randrange(len(group['paths']) - 1)
            
            directory.add_menu_item(title=title,
                                    params={'mode': 'path',
                                            'action': 'random',
                                            'group': group_id,
                                            'id': '{}'.format(_id)},
                                    art=folder_sync,
                                    info={'plot': description},
                                    isFolder=True)
            directory.add_menu_item(title='Next Path ({})'.format(_id),
                                    params={'mode': 'path',
                                            'action': 'next',
                                            'group': group_id,
                                            'id': '{}'.format(_id)},
                                    art=folder_next,
                                    info={'plot': description},
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False)
    
    return True, group_name
    
    
def call_path(group_id, path_id):
    path_def = manage.get_path_by_id(path_id, group_id=group_id)
    if not path_def:
        return
    
    xbmc.executebuiltin('Dialog.Close(busydialog)')
        
    if path_def['target'] == 'shortcut':
        if path_def['is_folder'] == 0:
            if path_def['content'] == 'addons':
                xbmc.executebuiltin('ActivateWindow({},{},return)'.format(path_def['window'],
                                                                          path_def['path']))
            else:
                if path_def['path'] == 'addons://install/':
                    xbmc.executebuiltin('InstallFromZip')
                else:
                    xbmc.executebuiltin('RunPlugin({})'.format(path_def['path']))
        else:
            xbmc.executebuiltin('ActivateWindow({},{},return)'.format(path_def['window'],
                                                                      path_def['path']))
    elif path_def['target'] == 'widget':
        xbmc.executebuiltin('ActivateWindow({},{},return)'.format(path_def['window'],
                                                                  path_def['path']))
    elif path_def['target'] == 'settings':
        xbmc.executebuiltin('Addon.OpenSettings({})'.format(path_def['path'].replace('plugin://', '')))


def random_path(group_id):
    _window = utils.get_active_window()
    
    if _window not in ['home', 'media'] and not label_warning_shown:
        _warn()
    
    dir = _window == 'media'
    
    group = manage.get_group_by_id(group_id)
    if not group:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'.format(group_id),
                  level=xbmc.LOGERROR)
        return
    
    group_name = group.get('label', '')
    paths = manage.find_defined_paths(group_id)
    
    if len(paths) > 0:
        if _window == 'media':
            rand = random.randrange(len(group['paths']) - 1)
            call_path(group_id, paths[rand]['id'])
        else:
            directory.add_menu_item(title=32013,
                                    params={'mode': 'force'},
                                    art=unpack,
                                    info={'plot': _addon.getLocalizedString(32014)},
                                    isFolder=False)
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=True)
    return dir, group_name
    
    
def next_path(group_id):
    _window = utils.get_active_window()
    
    if _window not in ['home', 'media'] and not label_warning_shown:
        _warn()
    
    dir = _window != 'media'
    
    group = manage.get_group_by_id(group_id)
    if not group:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'.format(group_id),
                  level=xbmc.LOGERROR)
        return
    
    group_name = group.get('label', '')
    paths = manage.find_defined_paths(group_id)
    
    if len(paths) > 0:
        if _window == 'media':
            rand = random.randrange(len(group['paths']) - 1)
            call_path(group_id, paths[rand]['id'])
        else:
            directory.add_menu_item(title=32013,
                                    params={'mode': 'force'},
                                    art=unpack,
                                    info={'plot': _addon.getLocalizedString(32014)},
                                    isFolder=False)
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=True)
    return dir, group_name


def _create_context_items(group_id, path_id, idx, length):
    cm = [(_addon.getLocalizedString(32048),
          ('RunPlugin('
           'plugin://plugin.program.autowidget/'
           '?mode=manage'
           '&action=edit'
           '&group={}'
           '&path={})').format(group_id, path_id))]
    if idx > 0:
        cm.append((_addon.getLocalizedString(32026),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=shift_path'
                   '&target=up'
                   '&group={}'
                   '&path={})').format(group_id, path_id)))
    if idx < length - 1:
        cm.append((_addon.getLocalizedString(32027),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=shift_path'
                   '&target=down'
                   '&group={}'
                   '&path={})').format(group_id, path_id)))
                                                      
    return cm
