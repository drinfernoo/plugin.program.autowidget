import xbmc

import random

from resources.lib import manage
from resources.lib.common import directory
from resources.lib.common import utils

folder_remove = utils.get_art('folder-remove.png')
folder = utils.get_art('folder.png')
folder_sync = utils.get_art('folder-sync.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
share = utils.get_art('share.png')
shuffle = utils.get_art('shuffle.png')
alert = utils.get_art('alert.png')
add = utils.get_art('add.png')
unpack = utils.get_art('unpack.png')
sync = utils.get_art('sync.png')
folder_add = utils.get_art('folder-add.png')
refresh = utils.get_art('refresh.png')
trash = utils.get_art('trash.png')
remove = utils.get_art('remove.png')


def root_menu():
    _create_menu()

    directory.add_separator(title='My Groups', char='/')
    _groups_menu()

    directory.add_separator(title='Tools', char='/')
    _tools_menu()


def group_menu(group):
    _manage_menu(group)
    _paths_menu(group)
    _actions_menu(group)
    
    
def shortcut_menu(group):
    _window = utils.get_active_window()
    paths = manage.find_defined_paths(group)
    
    if len(paths) > 0 and _window == 'media':
        directory.add_menu_item(title=('Point a widget at this directory to get'
                                       ' a random widget from the following:'),
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
        directory.add_menu_item(title=('Point a widget at this directory to get'
                                       ' a widget containing the following:'),
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
        directory.add_menu_item(title='Initialize Widgets',
                                params={'mode': 'force'},
                                art={'icon': unpack, 'thumb': unpack, 'banner': unpack, 'poster': unpack},
                                description='Initialize this and any other AutoWidgets.')


def call_path(path, target):
    _window = utils.get_active_window()

    if not path.startswith('ActivateWindow') and target:
        path = 'ActivateWindow({},{},return)'.format(target, path)

    if _window != 'dialog':
        if _window == 'home':
            xbmc.executebuiltin('Dialog.Close(busydialog)')
        xbmc.executebuiltin(path)
    
    
def _create_menu():
    directory.add_menu_item(title='Create New Widget Group',
                            params={'mode': 'manage', 'action': 'add_group',
                                    'target': 'widget'},
                            art={'icon': folder_add},
                            description='Create a new group of widgets.',
                            isFolder=False)
                            
    directory.add_menu_item(title='Create New Shortcut Group',
                            params={'mode': 'manage', 'action': 'add_group',
                                    'target': 'shortcut'},
                            art={'icon': share},
                            description='Create a new group of shortcuts.',
                            isFolder=False)
    
    
def _groups_menu():
    for group in manage.find_defined_groups():
        group_name = group.get('name', '')
        _type = group.get('type', '')
        directory.add_menu_item(title=group_name.capitalize(),
                                params={'mode': 'group',
                                        'group': group_name},
                                description='View the "{}" group.'
                                            .format(group_name),
                                art={'icon': folder_shortcut if _type == 'shortcut' else folder_sync},
                                isFolder=True)
    
    
def _tools_menu():
    _window = utils.get_active_window()

    directory.add_menu_item(title='Force Refresh Widgets',
                            params={'mode': 'force'},
                            art={'icon': refresh},
                            description='Force all defined widgets to refresh.',
                            isFolder=_window == 'dialog')
    directory.add_menu_item(title='Clean Old References',
                            params={'mode': 'clean'},
                            art={'icon': trash},
                            description='Clean old references to widgets that are no longer defined.',
                            isFolder=_window == 'dialog')
                            
                            
def _manage_menu(group):
    target = manage.get_group(group)['type']

    directory.add_menu_item(title='Add Path',
                            params={'mode': 'manage', 'action': 'add_path',
                                    'group': group, 'target': target},
                            art={'icon': add})
    
    directory.add_menu_item(title='Remove Group',
                            params={'mode': 'manage',
                                    'action': 'remove_group',
                                    'group': group},
                            art={'icon': remove},
                            description='Remove this group definition. Cannot be undone.')
                            
                            
def _paths_menu(group):
    target = manage.get_group(group)['type']
    paths = manage.find_defined_paths(group)

    for path in paths:
        widget = target == 'widget'
        directory.add_menu_item(title=path['name'] if widget else path['label'],
                                params={'mode': 'path',
                                        'action': 'call',
                                        'path': path['path'] if widget else path['action'],
                                        'target': path['type'] if widget else ''},
                                art={'icon': share},
                                description='Show a list of shortcuts from the {} group.'
                                            .format(group.capitalize()))
                                            
                                            
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
            title = 'Random Path from {}'.format(group.capitalize())
            art = {'icon': shuffle}
            description = 'Use a random path from the {} group.'.format(group.capitalize())
            if is_media:
                index = random.randrange(len(paths))
                params.update({'action': 'call',
                               'path': paths[index]['path'],
                               'target': paths[index]['type']})
            else:
                params.update({'action': 'random',
                               'group': group})
        elif is_shortcut:
            title = 'Shortcuts from {}'.format(group.capitalize())
            art = {'icon': share}
            description = 'Show a list of shortcuts from the {} group.'.format(group.capitalize())
            params.update({'action': 'shortcuts',
                           'group': group})
        
        directory.add_menu_item(title=title,
                                params=params,
                                art=art,
                                description=description,
                                isFolder=not is_media)
    else:
        directory.add_menu_item(title='No AutoWidgets have been defined for this group.',
                                art={'icon': alert},
                                isFolder=not is_media)
