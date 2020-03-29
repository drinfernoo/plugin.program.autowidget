import xbmc
import xbmcaddon

import random

from resources.lib import manage
from resources.lib.common import directory
from resources.lib.common import utils

add = utils.get_art('add.png')
alert = utils.get_art('alert.png')
folder = utils.get_art('folder.png')
folder_add = utils.get_art('folder-add.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
refresh = utils.get_art('refresh.png')
remove = utils.get_art('remove.png')
share = utils.get_art('share.png')
shuffle = utils.get_art('shuffle.png')
sync = utils.get_art('sync.png')
unpack = utils.get_art('unpack.png')

_addon = xbmcaddon.Addon()


def root_menu():
    directory.add_menu_item(title=32015,
                            params={'mode': 'manage', 'action': 'add_group',
                                    'target': 'widget'},
                            art=folder_add,
                            info={'plot': _addon.getLocalizedString(32016)})
                            
    directory.add_menu_item(title=32017,
                            params={'mode': 'manage', 'action': 'add_group',
                                    'target': 'shortcut'},
                            art=folder_shortcut,
                            info={'plot': _addon.getLocalizedString(32018)})
                            
    if len(manage.find_defined_groups()) > 0:
        # //// MY GROUPS ////
        directory.add_separator(title=32007, char='/')
        
        for group in manage.find_defined_groups():
            group_name = group['name']
            group_id = group['id']
            group_type = group['type']
            
            cm = [(_addon.getLocalizedString(32023),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=remove_group'
                   '&group={})').format(group_id)),
                  (_addon.getLocalizedString(32055),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=rename_group'
                   '&group={})').format(group_id))]
            
            directory.add_menu_item(title=group_name,
                                    params={'mode': 'group',
                                            'group': group_id},
                                    info={'plot': _addon.getLocalizedString(32019)
                                                        .format(group_name)},
                                    art=folder_shortcut if group_type == 'shortcut' else folder_sync,
                                    cm=cm,
                                    isFolder=True)

    # //// TOOLS ////
    directory.add_separator(title=32008, char='/')

    directory.add_menu_item(title=32006,
                            params={'mode': 'force'},
                            art=refresh,
                            info={'plot': _addon.getLocalizedString(32020)},
                            isFolder=False)


def group_menu(group_id):
    group = manage.get_group_by_id(group_id)
    group_type = group['type']
    group_name = group['name']
    is_widget = group_type == 'widget'
    is_shortcut = group_type == 'shortcut'
    
    # //// PATHS ////
    paths = manage.find_defined_paths(group_id)
    if paths:
        directory.add_separator(title=32009, char='/')

        for idx, path in enumerate(paths):
            directory.add_menu_item(title=path['label'],
                                    params={'mode': 'path',
                                            'action': 'call',
                                            'group': group_id,
                                            'path': path['id']},
                                    art=path['art'],
                                    cm=_create_context_items(group_id,
                                                             path['id'],
                                                             idx,
                                                             len(paths)))
                                                
    
    # //// ACTIONS ////
    directory.add_separator(title=32010, char='/')

    params = {'mode': 'path', 'group': group_id}

    if len(paths) > 0:
        if is_widget:
            title = _addon.getLocalizedString(32028).format(group_name)
            art = shuffle
            description = _addon.getLocalizedString(32029).format(group_name)
            
            params.update({'action': 'random'})
        elif is_shortcut:
            title = _addon.getLocalizedString(32030).format(group_name)
            art = share
            description = _addon.getLocalizedString(32031).format(group_name)
            params.update({'action': 'shortcuts'})
        
        directory.add_menu_item(title=title,
                                params=params,
                                art=art,
                                info={'plot': description},
                                isFolder=True)
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=True)


def random_path_menu(group_id):
    _window = utils.get_active_window()
    group = manage.get_group_by_id(group_id)
    group_name = group.get('name', '')
    paths = manage.find_defined_paths(group_id)
    
    if len(paths) > 0:
        if _window != 'home':
            directory.add_menu_item(title=32012,
                                    art=folder_sync)
            directory.add_separator(group_name, char='/')
        
            for path in paths:
                if _window != 'home':
                    directory.add_menu_item(title=path['label'],
                                            params={'mode': 'path',
                                                    'action': 'call',
                                                    'group': group_id,
                                                    'path': path['id']},
                                            art=path['art'])
        else:
            directory.add_menu_item(title=32013,
                                    params={'mode': 'force'},
                                    art=unpack,
                                    info={'plot': _addon.getLocalizedString(32014)})
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=True)
                                
    
def shortcut_menu(group_id):
    _window = utils.get_active_window()
    group = manage.get_group_by_id(group_id)
    group_name = group.get('name', '')
    paths = manage.find_defined_paths(group_id)
    
    if len(paths) > 0 and _window != 'home':
        directory.add_menu_item(title=32011,
                                art=folder_shortcut)
        directory.add_separator(group_name, char='/')
    
    for path in paths:
        directory.add_menu_item(title=path['label'],
                                params={'mode': 'path',
                                        'action': 'call',
                                        'group': group_id,
                                        'path': path['id']},
                                art=path['art'],
                                info=path['info'])


def call_path(group_id, path_id):
    path_def = manage.get_path_by_id(path_id, group_id=group_id)
    
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


def _create_context_items(group_id, path_id, idx, length):
    cm = [(_addon.getLocalizedString(32025),
          ('RunPlugin('
           'plugin://plugin.program.autowidget/'
           '?mode=manage'
           '&action=remove_path'
           '&group={}'
           '&path={})').format(group_id, path_id)),
          (_addon.getLocalizedString(32048),
          ('RunPlugin('
           'plugin://plugin.program.autowidget/'
           '?mode=manage'
           '&action=edit_path'
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
