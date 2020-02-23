import xbmc

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


def root_menu():
    _create_menu()

    if len(manage.find_defined_groups()) > 0:
        directory.add_separator(title=32007, char='/')
        _groups_menu()

    directory.add_separator(title=32008, char='/')
    _tools_menu()


def group_menu(group):
    _manage_menu(group)
    
    if len(manage.find_defined_paths(group)) > 0:
        directory.add_separator(title=32009, char='/')
        _paths_menu(group)
    
    directory.add_separator(title=32010, char='/')
    _actions_menu(group)
    
    
def shortcut_menu(group):
    _window = utils.get_active_window()
    paths = manage.find_defined_paths(group)
    
    if len(paths) > 0 and _window == 'media':
        directory.add_menu_item(title=32011,
                                art={'icon': folder_shortcut})
        directory.add_separator(group)
    
    for path in paths:
        directory.add_menu_item(title=path['label'],
                                params={'mode': 'path',
                                        'action': 'call',
                                        'path': path['action']},
                                art={'icon': path['thumbnail']})
    
    
def random_path_menu(group):
    _window = utils.get_active_window()
    paths = manage.find_defined_paths(group)
    
    if len(paths) > 0 and _window == 'media':
        directory.add_menu_item(title=32012,
                                art={'icon': folder_sync})
        directory.add_separator(group)
    
    for path in paths:
        if _window != 'home':
            directory.add_menu_item(title=path['name'],
                                    params={'mode': 'path',
                                            'action': 'call',
                                            'path': path['path'],
                                            'target': path['type']})
    if _window == 'home':
        directory.add_menu_item(title=32013,
                                params={'mode': 'force'},
                                art={'icon': unpack,
                                     'thumb': unpack,
                                     'banner': unpack,
                                     'poster': unpack},
                                description=32014)


def call_path(path, target):
    window = utils.get_active_window()
            
    if window == 'home':
        xbmc.executebuiltin('Dialog.Close(busydialog)')
    
    if not path.startswith('ActivateWindow'):
        if window == 'media':
            xbmc.executebuiltin('Container.Update({})'.format(path))
        elif target:
            path = 'ActivateWindow({},{},return)'.format(target, path)
    
    if window != 'dialog':
        xbmc.executebuiltin(path)
    
    
def _create_menu():
    _window = utils.get_active_window()
    
    directory.add_menu_item(title=32015,
                            params={'mode': 'manage', 'action': 'add_group',
                                    'target': 'widget'},
                            art={'icon': folder_add},
                            description=32016,
                            isFolder=_window == 'dialog')
                            
    directory.add_menu_item(title=32017,
                            params={'mode': 'manage', 'action': 'add_group',
                                    'target': 'shortcut'},
                            art={'icon': share},
                            description=32018,
                            isFolder=_window == 'dialog')
    
    
def _groups_menu():
    for group in manage.find_defined_groups():
        group_name = group.get('name', '')
        _type = group.get('type', '')
        directory.add_menu_item(title=group_name.capitalize(),
                                params={'mode': 'group',
                                        'group': group_name},
                                description=_addon.getLocalizedString(32019)
                                            .format(group_name),
                                art={'icon': folder_shortcut if _type == 'shortcut' else folder_sync},
                                cm=[(32023,
                                    ('RunPlugin('
                                     'plugin://plugin.program.autowidget/'
                                     '?mode=manage'
                                     '&action=remove_group'
                                     '&group={})').format(group_name))],
                                isFolder=True)
    
    
def _tools_menu():
    _window = utils.get_active_window()

    directory.add_menu_item(title=32006,
                            params={'mode': 'force'},
                            art={'icon': refresh},
                            description=32020,
                            isFolder=_window == 'dialog')
    # directory.add_menu_item(title='Clean Old References',
                            # params={'mode': 'clean'},
                            # art={'icon': trash},
                            # description='Clean old references to widgets that are no longer defined.',
                            # isFolder=_window == 'dialog')
                            
                            
def _manage_menu(group):
    target = manage.get_group(group)['type']

    directory.add_menu_item(title=32021,
                            params={'mode': 'manage', 'action': 'add_path',
                                    'group': group, 'target': target},
                            art={'icon': add},
                            description=32022)
    
    directory.add_menu_item(title=32023,
                            params={'mode': 'manage',
                                    'action': 'remove_group',
                                    'group': group},
                            art={'icon': remove},
                            description=32024)
                            
                            
def _paths_menu(group):
    target = manage.get_group(group)['type']
    paths = manage.find_defined_paths(group)

    for idx, path in enumerate(paths):
        widget = target == 'widget'
        path_name = path['name'] if widget else path['label']
        
        cm = [(_addon.getLocalizedString(32025), ('RunPlugin('
                                                  'plugin://plugin.program.autowidget/'
                                                  '?mode=manage'
                                                  '&action=remove_path'
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
        if idx < len(paths) - 1:
            cm.append((_addon.getLocalizedString(32027), ('RunPlugin('
                                                          'plugin://plugin.program.autowidget/'
                                                          '?mode=manage'
                                                          '&action=shift_path'
                                                          '&target=down'
                                                          '&group={}'
                                                          '&path={})').format(group, path_name)))
        
        directory.add_menu_item(title=path_name,
                                params={'mode': 'path',
                                        'action': 'call',
                                        'path': path['path'] if widget else path['action'],
                                        'target': path['type'] if widget else ''},
                                art={'icon': path.get('thumbnail', '') or share},
                                cm=cm)
                                            
                                            
def _actions_menu(group):
    _window = utils.get_active_window()
    is_media = _window == 'media'

    target = manage.get_group(group)['type']
    paths = manage.find_defined_paths(group)

    is_widget = target == 'widget'
    is_shortcut = target == 'shortcut'

    params = {'mode': 'path'}

    if len(paths) > 0:
        if is_widget:
            title = _addon.getLocalizedString(32028).format(group.capitalize())
            art = {'icon': shuffle}
            description = _addon.getLocalizedString(32029).format(group.capitalize())
            if is_media:
                index = random.randrange(len(paths))
                params.update({'action': 'call',
                               'path': paths[index]['path'],
                               'target': paths[index]['type']})
            else:
                params.update({'action': 'random',
                               'group': group})
        elif is_shortcut:
            title = _addon.getLocalizedString(32030).format(group.capitalize())
            art = {'icon': share}
            description = _addon.getLocalizedString(32031).format(group.capitalize())
            params.update({'action': 'shortcuts',
                           'group': group})
        
        directory.add_menu_item(title=title,
                                params=params,
                                art=art,
                                description=description,
                                isFolder=not is_media)
    else:
        directory.add_menu_item(title=32032,
                                art={'icon': alert},
                                isFolder=not is_media)
