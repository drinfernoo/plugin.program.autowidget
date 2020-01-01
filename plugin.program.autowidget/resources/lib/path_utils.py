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


def find_defined_groups():
    shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    shortcut_path = xbmc.translatePath(shortcuts.getAddonInfo('profile'))
        
    groups = []
    
    for filename in os.listdir(shortcut_path):
        if filename.startswith('autowidget-') and filename.endswith('.xml'):
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
            label = shortcut.find('label').text
            action = shortcut.find('action').text
            path = action.split('\"')[1]
            paths.append((label, action, path))
        
        return paths
        
        
def get_random_path(group, change_sec=3600):
    now = time.time()
    seed = now - (now % change_sec)
    rand = random.Random()
    paths = find_defined_paths(group)
    random_id = uuid.uuid4()

    return (rand.choice(paths), random_id)
    
    
def add_group():
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading='Name for Group') or ''
    
    if group_name:
        window.show_window(group_name)
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', 'Cannot create a group with no name.')

        
def save_path_reference(action, group, id):
    addon = xbmcaddon.Addon()
    data_path = xbmc.translatePath(addon.getAddonInfo('profile'))
    
    path_to_saved = os.path.join(data_path, '{}.auto'.format(id))
    xbmc.log(path_to_saved)
    
    with open(path_to_saved, "w") as f:
        content = '{},{}'.format(action, group)
        f.write(content)

        
def inject_paths(notify=False):
    addon = xbmcaddon.Addon()
    data_path = xbmc.translatePath(addon.getAddonInfo('profile'))
    shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    shortcut_path = xbmc.translatePath(shortcuts.getAddonInfo('profile'))
    
    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', 'Force refreshing autowidgets')
    
    for filename in os.listdir(shortcut_path):
        if not filename.startswith('autowidget') and not filename.startswith('powermenu') and filename.endswith('.xml'):
            file_path = os.path.join(shortcut_path, filename)
            root = ET.parse(file_path).getroot()
            
            for shortcut in root.findall('shortcut'):
                label = shortcut.find('label')
                action = shortcut.find('action')
                
                # first pass
                if 'plugin.program.autowidget' in action.text:         
                    path = action.text.split('\"')[1]
                    if '?' not in path:
                        continue
                    
                    params = dict(parse_qsl(path.split('?')[1]))
                    
                    action_param = params.get('action', '')
                    group_param = params.get('group', '')
                    
                    if action_param == 'random':
                        path, id = get_random_path(group_param)
                        skin_path = 'autowidget-{}-path'.format(id)
                        skin_label = 'autowidget-{}-label'.format(id)
                        path_string = '$INFO[Skin.String({})]'.format(skin_path)
                        label_string = '$INFO[Skin.String({})]'.format(skin_label)
                        final_path = path[1].replace(path[2], path_string).replace('\"', '')
                        
                        xbmc.log('Setting skin string {} to path {}...'.format(skin_path, path_string))
                        xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_path, path[2]))
                        xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_label, path[0]))
                        
                        label.text = label_string
                        action.text = final_path
                    
                    save_path_reference(action_param, group_param, id)
                    
                    tree = ET.ElementTree(root)
                    tree.write(file_path)
                else:
                    for reference in os.listdir(data_path):
                        ref_path = os.path.join(data_path, reference)
                        with open(ref_path, "r") as f:
                            params = f.read().split(',')
                            
                        id = os.path.basename(ref_path)[:-5]
                        skin_path = 'autowidget-{}-path'.format(id)
                        skin_label = 'autowidget-{}-label'.format(id)
                
                        if params[0] == 'random':
                            path, id = get_random_path(params[1])
                            xbmc.log('Setting skin string {} to path {}...'.format(skin_path, path[2]))
                            xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_path, path[2]))
                            xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_label, path[0]))
