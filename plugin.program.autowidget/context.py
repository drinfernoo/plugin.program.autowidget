import xbmc
import xbmcaddon
import xbmcgui

import sys

from resources.lib import manage
from resources.lib.common import utils

_addon = xbmcaddon.Addon()

folder_add = utils.get_art('folder-add.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
share = utils.get_art('share.png')


def _group_dialog(is_folder, groupname=None):
    groups = manage.find_defined_groups();
    names = [group['name'] for group in groups]
    
    index = -1
    options = []
    offset = 1
    
    if is_folder:
        new_widget = xbmcgui.ListItem(_addon.getLocalizedString(32015))
        new_widget.setArt({'icon': folder_add})
        options.append(new_widget)
        offset = 2
        
    if groupname:
        index = names.index(groupname) + offset
    
    new_shortcut = xbmcgui.ListItem(_addon.getLocalizedString(32017))
    new_shortcut.setArt({'icon': share})
    options.append(new_shortcut)
    
    for group in groups:
        item = xbmcgui.ListItem(group['name'])
        item.setArt({'icon': folder_sync if group['type'] == 'widget' else folder_shortcut})
        options.append(item)
    
    dialog = xbmcgui.Dialog()
    choice = dialog.select('Choose a Group', options, preselect=index,
                           useDetails=True)
    
    if choice < 0:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32034))
    elif (choice, offset) == (0, 2):
        return _group_dialog(is_folder, manage.add_group('widget'))
    elif (choice, offset) in [(0, 1), (1, 2)]:
        return _group_dialog(is_folder, manage.add_group('shortcut'))
    else:
        return groups[choice - offset]


if __name__ == '__main__':
    labels = {'label': xbmc.getInfoLabel('ListItem.Label'),
              'path': xbmc.getInfoLabel('ListItem.FolderPath'),
              'icon': xbmc.getInfoLabel('ListItem.Icon'),
              'is_folder': xbmc.getCondVisibility('Container.ListItem.IsFolder'),
              'content': xbmc.getInfoLabel('Container.Content'),
              'window': xbmcgui.getCurrentWindowId()}
    
    group = _group_dialog(labels['is_folder'])
    if group:
        manage.add_path(group, labels)
