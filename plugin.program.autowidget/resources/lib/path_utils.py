import xbmc
import xbmcaddon
import xbmcgui

import os
import random
import six
import time
import uuid

if six.PY3:
    from urllib.parse import parse_qsl
elif six.PY2:
    from urlparse import parse_qsl

from xml.etree import ElementTree as ET

from resources.lib import window

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_shortcuts = xbmcaddon.Addon('script.skinshortcuts')
_shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))


def _find_defined_groups():
    groups = []
    
    for filename in os.listdir(_shortcuts_path):
        if filename.startswith('autowidget-') and filename.endswith('.DATA.xml'):
            group_name = filename[11:-9]
            groups.append(group_name)
            
    return groups
    
    
def _find_defined_paths(group=None):
    shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    shortcut_path = xbmc.translatePath(shortcuts.getAddonInfo('profile'))
        
    paths = []
    
    if group:
        filename = 'autowidget-{}.DATA.xml'.format(group)
    
    if filename:
        tree = ET.parse(os.path.join(_shortcuts_path, filename))
        root = tree.getroot()
                
        for shortcut in root.findall('shortcut'):
            label = shortcut.find('label').text
            action = shortcut.find('action').text
            path = action.split('\"')[1]
            paths.append((label, action, path))
    else:
        for group in find_defined_groups():
            paths.append(find_defined_paths(group))
        
    return paths
        
        
def _get_random_paths(group, change_sec=3600):
    now = time.time()
    seed = now - (now % change_sec)
    rand = random.Random(seed)
    
    paths = find_defined_paths(group)

    return rand.sample(len(paths), paths)
    
    
def add_group():
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading='Name for Group') or ''
    
    if group_name:
        window.show_window(group_name)
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', 'Cannot create a group with no name.')

        
def _save_path_details(path):
    params = dict(parse_qsl(path.split('?')[1]))                    
    action_param = params.get('action', '')
    group_param = params.get('group', '')
    id = uuid.uuid4()
    
    path_to_saved = os.path.join(_addon_path, '{}.auto'.format(id))
    
    with open(path_to_saved, "w") as f:
        content = '{},{}'.format(action, group)
        f.write(content)
        
    return id

        
def convert_paths():
    total_paths = find_defined_paths()
    
    for filename in os.listdir(_shortcuts_path):
        if 'autowidget' in filename:
            file_path = os.path.join(_shortcuts_path, filename)
            root = ET.parse(file_path).getroot()
            
            for shortcut in root.findall('shortcut'):
                label = shortcut.find('label')
                action = shorcut.find('action')
                
                if all(term in action.text for term in ['plugin.program.autowidget', '?mode']):
                    path = action.text.split('\"')[1]
                else:
                    continue
                    
                id = save_path_details(path)
                skin_path = 'autowidget-{}-path'.format(id)
                skin_label = 'autowidget-{}-label'.format(id)
                path_string = '$INFO[Skin.String({})]'.format(skin_path)
                label_string = '$INFO[Skin.String({})]'.format(skin_label)
                final = path[1].replace(path[2], path_string).replace('\"', '')
                
                xbmc.log('Setting skin string {} to path {}...'.format(skin_path, path_string))
                xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_path, path[2]))
                xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_label, path[0]))
                
                label.text = label_string
                action.text = final
                
                tree = ET.ElementTree(root)
                tree.write(file_path)
                
    # xbmc.executebuiltin('ReloadSkin()')
                
                
def refresh_paths(notify=False):
    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', 'Refreshing AutoWidgets')
    
    paths = []
    
    for saved in os.listdir(_addon_path):
        if not saved.endswith('.auto'):
            continue
            
        saved_path = os.path.join(_addon_path, saved)
        with open(saved_path, "r") as f:
            params = f.read().split(',')
            
        id = os.path.basename(saved_path)[:-5]
        skin_path = 'autowidget-{}-path'.format(id)
        skin_label = 'autowidget-{}-label'.format(id)

        action = params[0]
        group = params[1]
        
        if action == 'random' and len(paths) == 0:
            paths = get_random_paths(group)
        
        path = paths.pop()
        # xbmc.log('Setting skin string {} to path {}...'.format(skin_path, path[2]))
        xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_path, path[2]))
        xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_label, path[0]))
