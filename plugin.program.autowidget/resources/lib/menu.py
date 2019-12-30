import xbmcplugin

import sys

from resources.lib import path_utils
from resources.lib.common import directory

_handle = int(sys.argv[1])


def root():
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
                                
    xbmcplugin.setContent(_handle, 'files')


def show_group(group):
    directory.add_menu_item(title='Edit {}'.format(group),
                                params={'mode': 'group',
                                        'action': 'edit',
                                        'group': group},
                                description='Edit the "{}" group.'
                                            .format(group))
                                            
    directory.add_menu_item(title='Random Path',
                            params={'mode': 'path',
                                    'action': 'random',
                                    'group': group},
                            description='Use a random path from the "{}" group.'
                                        .format(group),
                            isFolder=True)
                            
    xbmcplugin.setContent(_handle, 'files')
