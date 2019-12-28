import xbmc
import xbmcaddon
import xbmcgui

import os
import random

from xml.etree import ElementTree as ET

from resources.lib import window


def find_defined_groups():
    shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    shortcut_path = xbmc.translatePath(shortcuts.getAddonInfo('profile'))
        
    groups = []
    
    for filename in os.listdir(shortcut_path):
        if filename.startswith('autowidget-') and filename.endswith('.DATA.xml'):
            group_name = filename[11:-9]
            groups.append(group_name)
            
    return groups
    
def find_defined_paths(group):
        shortcuts = xbmcaddon.Addon('script.skinshortcuts')
        shortcut_path = xbmc.translatePath(shortcuts.getAddonInfo('profile'))
        
        paths = []
        filename = 'autowidget-{}.DATA.xml'.format(group)
        
        tree = ET.parse(os.path.join(shortcut_path, filename))
        root = tree.getroot()
                
        for shortcut in root.findall('shortcut'):
            action = shortcut.find('action').text
            paths.append(action)
        
        return paths
        
        
def get_random_path(group):
    paths = find_defined_paths(group)
    index = random.randint(0, len(paths)-1)

    return paths[index]
    
    
def add_group():
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading='Name for Group') or ''
    
    if group_name:
        window.show_window(group_name)
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', 'Cannot create a group with no name.')
