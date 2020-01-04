import xbmcplugin

import sys

from resources.lib import path_utils
from resources.lib.common import directory

_handle = int(sys.argv[1])


def root_menu():
    directory.add_menu_item(title='Create New Group',
                            params={'mode': 'group', 'action': 'add'},
                            description='Create a new group of widget paths.')
                            
    for group in path_utils.find_defined_groups():
        directory.add_menu_item(title=group,
                                params={'mode': 'group',
                                        'action': 'view',
                                        'group': group},
                                description='View the "{}" group.'
                                            .format(group),
                                isFolder=True)
                                
    directory.add_menu_item(title='Tools',
                            params={'mode': 'tools'},
                            description='Various tools for using AutoWidgets.',
                            isFolder=True)
                                
    xbmcplugin.setContent(_handle, 'files')


def group_menu(group):
    directory.add_menu_item(title='Edit {}'.format(group),
                            params={'mode': 'group',
                                    'action': 'edit',
                                    'group': group},
                            description='Edit the "{}" group.'
                                        .format(group))
    directory.add_menu_item(title='Remove Group',
                            params={'mode': 'group',
                                    'action': 'remove',
                                    'group': group},
                            description='Remove this group definition. Cannot be undone.')
    directory.add_menu_item(title='Random Path',
                            params={'mode': 'path',
                                    'action': 'random',
                                    'group': group},
                            description='Use a random path from the "{}" group.'
                                        .format(group),
                            isFolder=True)
                            
    xbmcplugin.setContent(_handle, 'files')
    
    
def tools_menu():
    directory.add_menu_item(title='Force Refresh Widgets',
                            params={'mode': 'force'},
                            description='Force all defined widgets to refresh.')
    directory.add_menu_item(title='Clean Old References',
                            params={'mode': 'clean'},
                            description='Clean old references to widgets that are no longer defined.')
