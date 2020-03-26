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
folder_remove = utils.get_art('folder-remove.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
refresh = utils.get_art('refresh.png')
remove = utils.get_art('remove.png')
share = utils.get_art('share.png')
shuffle = utils.get_art('shuffle.png')
sync = utils.get_art('sync.png')
trash = utils.get_art('trash.png')
unpack = utils.get_art('unpack.png')

_addon = xbmcaddon.Addon()


def root_menu():
    directory.add_menu_item(title=32015,
                            params={'mode': 'manage', 'action': 'add_group',
                                    'target': 'widget'},
                            art={'icon': folder_add},
                            description=32016)
                            
    directory.add_menu_item(title=32017,
                            params={'mode': 'manage', 'action': 'add_group',
                                    'target': 'shortcut'},
                            art={'icon': share},
                            description=32018)
                            
    if len(manage.find_defined_groups()) > 0:
        # //// MY GROUPS ////
        directory.add_separator(title=32007, char='/')
        
        for group in manage.find_defined_groups():
            group_name = group['name']
            _type = group['type']
            
            directory.add_menu_item(title=group_name.capitalize(),
                                    params={'mode': 'group',
                                            'group': group_name},
                                    description=_addon.getLocalizedString(32019)
                                                .format(group_name),
                                    art={'icon': folder_shortcut if _type == 'shortcut' else folder_sync},
                                    cm=[(_addon.getLocalizedString(32023),
                                        ('RunPlugin('
                                         'plugin://plugin.program.autowidget/'
                                         '?mode=manage'
                                         '&action=remove_group'
                                         '&group={})').format(group_name))],
                                    isFolder=True)

    # //// TOOLS ////
    directory.add_separator(title=32008, char='/')

    directory.add_menu_item(title=32006,
                            params={'mode': 'force'},
                            art={'icon': refresh},
                            description=32020,
                            isFolder=False)


def group_menu(group):
    target = manage.get_group_by_name(group)['type']

    # directory.add_menu_item(title=32021,
                            # params={'mode': 'manage', 'action': 'add_path',
                                    # 'group': group, 'target': target},
                            # art={'icon': add},
                            # description=32022)
    
    directory.add_menu_item(title=32023,
                            params={'mode': 'manage',
                                    'action': 'remove_group',
                                    'group': group},
                            art={'icon': remove},
                            description=32024)
    
    # //// PATHS ////
    paths = manage.find_defined_paths(group)
    if paths:
        directory.add_separator(title=32009, char='/')

        for idx, path in enumerate(paths):
            directory.add_menu_item(title=path['label'],
                                    params={'mode': 'path',
                                            'action': 'call',
                                            'group': group,
                                            'path': path['label']},
                                    art=path['art'],
                                    cm=_create_context_items(group,
                                                             path['label'],
                                                             idx,
                                                             len(paths)))
                                                
    
    # //// ACTIONS ////
    directory.add_separator(title=32010, char='/')
    
    is_widget = target == 'widget'
    is_shortcut = target == 'shortcut'

    params = {'mode': 'path', 'group': group}
    groupname = group.capitalize()

    if len(paths) > 0:
        if is_widget:
            title = _addon.getLocalizedString(32028).format(groupname)
            art = {'icon': shuffle}
            description = _addon.getLocalizedString(32029).format(groupname)
            
            params.update({'action': 'random'})
        elif is_shortcut:
            title = _addon.getLocalizedString(32030).format(groupname)
            art = {'icon': share}
            description = _addon.getLocalizedString(32031).format(groupname)
            params.update({'action': 'shortcuts'})
        
        directory.add_menu_item(title=title,
                                params=params,
                                art=art,
                                description=description,
                                isFolder=True)
    else:
        directory.add_menu_item(title=32032,
                                art={'icon': alert},
                                isFolder=True)


def random_path_menu(group):
    _window = utils.get_active_window()
    paths = manage.find_defined_paths(group)
    
    if len(paths) > 0:
        if _window != 'home':
            directory.add_menu_item(title=32012,
                                    art={'icon': folder_sync})
            directory.add_separator(group, char='/')
        
            for path in paths:
                if _window != 'home':
                    directory.add_menu_item(title=path['label'],
                                            params={'mode': 'path',
                                                    'action': 'call',
                                                    'group': group,
                                                    'path': path['label'],
                                                    'target': 'widget'})
        else:
            directory.add_menu_item(title=32013,
                                    params={'mode': 'force'},
                                    art={'icon': unpack,
                                         'thumb': unpack,
                                         'banner': unpack,
                                         'poster': unpack},
                                    description=32014)
    else:
        directory.add_menu_item(title=32032,
                                art={'icon': alert},
                                isFolder=True)
                                
    
def shortcut_menu(group):
    _window = utils.get_active_window()
    paths = manage.find_defined_paths(group)
    
    if len(paths) > 0 and _window != 'home':
        directory.add_menu_item(title=32011,
                                art={'icon': folder_shortcut})
        directory.add_separator(group, char='/')
    
    for path in paths:
        directory.add_menu_item(title=path['label'],
                                params={'mode': 'path',
                                        'action': 'call',
                                        'group': group,
                                        'path': path['label']},
                                art=path['art'])


def call_path(group, path):
    path_def = manage.get_path_by_name(group, path)
    window = utils.get_active_window()
    
    if window == 'home':
        xbmc.executebuiltin('Dialog.Close(busydialog)')
        
    if path_def['target'] == 'shortcut':
        xbmc.executebuiltin('RunPlugin({})'.format(path_def['path']))
    else:
        xbmc.executebuiltin('ActivateWindow({},{},return)'.format(path_def['window'],
                                                                 path_def['path']))


def _create_context_items(group, path_name, idx, length):
    cm = [(_addon.getLocalizedString(32025), ('RunPlugin('
                                              'plugin://plugin.program.autowidget/'
                                              '?mode=manage'
                                              '&action=remove_path'
                                              '&group={}'
                                              '&path={})').format(group, path_name)),
          ('Edit Path', ('RunPlugin('
                         'plugin://plugin.program.autowidget/'
                         '?mode=manage'
                         '&action=edit_path'
                         '&group={}'
                         '&path={})').format(group, path_name))]
    if idx > 0:
        cm.append((_addon.getLocalizedString(32026), ('RunPlugin('
                                                      'plugin://plugin.program.autowidget/'
                                                      '?mode=manage'
                                                      '&action=shift_path'
                                                      '&target=up'
                                                      '&group={}'
                                                      '&path={})').format(group, path_name)))
    if idx < length - 1:
        cm.append((_addon.getLocalizedString(32027), ('RunPlugin('
                                                      'plugin://plugin.program.autowidget/'
                                                      '?mode=manage'
                                                      '&action=shift_path'
                                                      '&target=down'
                                                      '&group={}'
                                                      '&path={})').format(group, path_name)))
                                                      
    return cm
