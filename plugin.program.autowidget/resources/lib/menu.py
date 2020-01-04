import xbmc
import xbmcplugin

import sys

from resources.lib import path_utils
from resources.lib.common import directory
from resources.lib.common import utils

_handle = int(sys.argv[1])


def root_menu():
    directory.add_menu_item(title='Create New Group',
                            params={'mode': 'group', 'action': 'add'},
                            art={'icon': utils.get_art('folder-plus-outline.png')},
                            description='Create a new group of widget paths.')
                            
    for group in path_utils.find_defined_groups():
        directory.add_menu_item(title=group.capitalize(),
                                params={'mode': 'group',
                                        'action': 'view',
                                        'group': group},
                                description='View the "{}" group.'
                                            .format(group),
                                art={'icon': utils.get_art('folder-outline.png')},
                                isFolder=True)
                                
    directory.add_menu_item(title='Tools',
                            params={'mode': 'tools'},
                            art={'icon': utils.get_art('tools.png')},
                            description='Various tools for using AutoWidgets.',
                            isFolder=True)

    xbmcplugin.setContent(_handle, 'files')


def group_menu(group):
    not_media = xbmc.getCondVisibility('!Window.IsMedia')
    paths = path_utils.find_defined_paths(group)
    
    directory.add_menu_item(title='Edit {}'.format(group.capitalize()),
                            params={'mode': 'group',
                                    'action': 'edit',
                                    'group': group},
                            art={'icon': utils.get_art('pencil-outline.png')},
                            description='Edit the "{}" group.'
                                        .format(group))
    directory.add_menu_item(title='Remove Group',
                            params={'mode': 'group',
                                    'action': 'remove',
                                    'group': group},
                            art={'icon': utils.get_art('folder-remove-outline.png')},
                            description='Remove this group definition. Cannot be undone.')
    
    if len(paths) > 0:
        directory.add_menu_item(title='Random Path from {}'.format(group.capitalize()),
                                params={'mode': 'path',
                                        'action': 'random',
                                        'group': group},
                                art={'icon': utils.get_art('shuffle.png')},
                                description='Use a random path from the {} group.'
                                            .format(group.capitalize()),
                                isFolder=True)
    else:
        directory.add_menu_item(title='No AutoWidgets have been defined for this group.',
                                art={'icon': utils.get_art('alert-circle-outline.png')},
                                isFolder=not_media)
    
    xbmcplugin.setPluginCategory(_handle, group.capitalize())
    xbmcplugin.setContent(_handle, 'files')
    
    
def random_path_menu(group):
    not_media = xbmc.getCondVisibility('!Window.IsMedia')
    select_dialog = xbmc.getCondVisibility('Window.IsActive(dialogselect)')
    home = xbmc.getCondVisibility('Window.IsActive(home)')
    paths = path_utils.find_defined_paths(group)
    
    if len(paths) > 0 and not home:
        label = 'following:' if not not_media else '{} group.'.format(group.capitalize())
        directory.add_menu_item(title='Point a widget at this directory to get a random widget from the {}'
                                      .format(label),
                                art={'icon': utils.get_art('shuffle.png')},
                                isFolder=not_media)
                                
        if not not_media:
            directory.add_separator(group)
    
            for path in paths:
                directory.add_menu_item(title=path[0],
                                        params={'mode': 'path',
                                                'action': 'call',
                                                'path': path[1]},
                                        art={'icon': path[3]})
    if home:
        unpack = utils.get_art('package-variant.png')
        sync = utils.get_art('sync.png')
        directory.add_menu_item(title='Initialize Widgets',
                        params={'mode': 'force'},
                        art={'icon': unpack, 'thumb': unpack, 'banner': unpack, 'poster': unpack},
                        description='Initialize this and any other AutoWidgets.')
    
    xbmcplugin.setPluginCategory(_handle, group.capitalize())
    xbmcplugin.setContent(_handle, 'files')
    
    
def tools_menu():
    directory.add_menu_item(title='Force Refresh Widgets',
                            params={'mode': 'force'},
                            art={'icon': utils.get_art('refresh.png')},
                            description='Force all defined widgets to refresh.')
    directory.add_menu_item(title='Clean Old References',
                            params={'mode': 'clean'},
                            art={'icon': utils.get_art('trash-can-outline.png')},
                            description='Clean old references to widgets that are no longer defined.')
    
    xbmcplugin.setPluginCategory(_handle, 'Tools')
    xbmcplugin.setContent(_handle, 'files')
    