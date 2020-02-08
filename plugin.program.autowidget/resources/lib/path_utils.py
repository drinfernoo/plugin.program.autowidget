import xbmc
import xbmcaddon
import xbmcgui

import ast
import os
import random
import re
import shutil
import time
import uuid

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

from xml.etree import ElementTree as ET

from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_shortcuts = xbmcaddon.Addon('script.skinshortcuts')
_shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))

widget_props_pattern = '\w*[.-]*[wW]idget(\w+)[.-]*\w*'
activate_window_pattern = '[aA]ctivate[wW]indow[(]\w+,(.*)(?:,[rR]eturn)?[)]'
refresh_quantity = _addon.getSettingInt('service.refresh_quantity')

def find_defined_groups():
    groups = []
    
    if not os.path.exists(_shortcuts_path):
        return
    
    if os.path.exists(_shortcuts_path):
        for filename in os.listdir(_shortcuts_path):
            if filename.startswith('autowidget') and filename.endswith('DATA.xml'):
                group_name = filename[11:-9]
                groups.append(group_name)

    utils.log('find_defined_groups: {}'.format(groups))
    return groups
    
    
def find_defined_paths(group=None):
    paths = []
    filename = ''
        
    if group:
        filename = 'autowidget-{}.DATA.xml'.format(group)
        path = os.path.join(_shortcuts_path, filename)
        
        if os.path.exists(path):
            tree = ET.parse(os.path.join(_shortcuts_path, filename))
            root = tree.getroot()
                    
            for shortcut in root.findall('shortcut'):
                label = shortcut.find('label').text
                action = shortcut.find('action').text
                icon = shortcut.find('thumb').text

                try:
                    path = action.split(',')[1]
                except:
                    dialog = xbmcgui.Dialog()
                    dialog.notification('AutoWidget',
                                        'Unsupported path in {}: {}'.format(group.capitalize(), action))
                    
                paths.append((label, action, path, icon))
    else:
        for group in find_defined_groups():
            paths.append(find_defined_paths(group))
    
    utils.log('find_defined_paths: {}'.format(paths))
    return paths
    
        
def _get_random_paths(group, force=False, change_sec=3600):
    wait_time = 5 if force else change_sec
    now = time.time()
    seed = now - (now % wait_time)
    rand = random.Random(seed)
    paths = find_defined_paths(group)
    rand.shuffle(paths)
    
    utils.log('_get_random_paths: {}'.format(paths))
    return paths
    
    
def edit_group(group=None):
    if not group:
        dialog = xbmcgui.Dialog()
        group = dialog.input(heading='Name for Group') or ''
    
    if group:
        xbmc.executebuiltin('RunScript(script.skinshortcuts,type=manage'
                            '&group=autowidget-{})'.format(group), wait=True)
        # xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', 'Cannot create a group with no name.')
        

def remove_group(group):
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', 'Are you sure you want to remove this group? This action [B]cannot[/B] be undone.')
    
    if choice:
        filename = 'autowidget-{}.DATA.xml'.format(group).lower()
        filepath = os.path.join(_shortcuts_path, filename)
        try:
            os.remove(filepath)
        except Exception as e:
            utils.log('{}'.format(e), level=xbmc.LOGERROR)
            
        utils.ensure_addon_data()
        for file in os.listdir(_addon_path):
            savedpath = os.path.join(_addon_path, file)
            with open(savedpath, 'r') as f:
                content = f.read()
            
            if group in content:
                try:
                    os.remove(savedpath)
                except Exception as e:
                    utils.log('{}'.format(e), level=xbmc.LOGERROR)
        
        xbmc.executebuiltin('Container.Update(plugin://plugin.program.autowidget/)')
    else:
        dialog.notification('AutoWidget', 'Cannot create a group with no name.')

        
def _save_path_details(path):
    split = path.split('\"')[1].split('?')[1]
    params = dict(parse_qsl(split))
    action_param = params.get('action', '').replace('\"','')
    group_param = params.get('group', '').replace('\"','')
    id = uuid.uuid4()
    
    path_to_saved = os.path.join(_addon_path, '{}.auto'.format(id))
    
    with open(path_to_saved, "w") as f:
        content = '{},{}'.format(action_param, group_param)
        f.write(content)
    
    utils.log('_save_path_details: {}'.format(id))
    return id
                
                
def _process_widgets():
    skin = xbmc.translatePath('special://skin/')
    skin_id = os.path.basename(os.path.normpath(skin))
    props_path = os.path.join(_shortcuts_path, '{}.properties'.format(skin_id))
    
    if not os.path.exists(props_path):
        return
    
    with open(props_path, 'r') as f:
        prop_list = ast.literal_eval(f.read())
    
    convert_list = [prop for prop in prop_list
                    if all(param in prop[3] for param in
                           ['plugin.program.autowidget',
                            'mode=path', 'action=random'])]
    finished_props = [prop for prop in prop_list if prop not in convert_list]
    
    for convert in convert_list:
        menu, group = convert[0:2]
        
        _id = _save_path_details(convert[3])
        label_str = '$INFO[Skin.String(autowidget-{}-label)]'.format(_id)
        path_str = '$INFO[Skin.String(autowidget-{}-path)]'.format(_id)
        
        # fix shortcut xmls
        xml_path = os.path.join(_shortcuts_path,
                                '{}.DATA.xml'.format(menu.replace('.', '-')))
        shortcuts = ET.parse(xml_path).getroot()
        for shortcut in shortcuts.findall('shortcut'):
            action = shortcut.find('action')
            label = shortcut.find('label')
            
            if action.text.replace('&amp;', '&') in convert[3]:
                label.text = label_str
                
                if re.search(activate_window_pattern, convert[3]):
                    action.text = re.sub(activate_window_pattern, convert[3],
                                         path_str)
                
        tree = ET.ElementTree(shortcuts)
        tree.write(xml_path)
        
        # fix properties
        if re.search(activate_window_pattern, convert[3]):
            convert[3] = re.sub(activate_window_pattern, convert[3], path_str)
            
        finished_props.append(convert)
            
    with open(props_path, 'w') as f:
        f.write('{}'.format(finished_props))


def refresh_paths(notify=False, force=False):
    processed = 0
    utils.ensure_addon_data()
    
    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', 'Refreshing AutoWidgets')
    
    if force:
        _process_widgets()
        xbmc.executebuiltin('ReloadSkin()')
    
    for group in find_defined_groups():
        paths = []
        
        for saved in [saved for saved in os.listdir(_addon_path)
                      if saved.endswith('.auto')]:            
            if processed > refresh_quantity:
                break
            
            saved_path = os.path.join(_addon_path, saved)
            with open(saved_path, 'r') as f:
                params = f.read().split(',')
                
            action = params[0]
            group_param = params[1]
            
            if group_param != group:
                continue
                
            _id = os.path.basename(saved_path)[:-5]
            skin_path = 'autowidget-{}-path'.format(_id)
            skin_label = 'autowidget-{}-label'.format(_id)
        
            if action == 'random' and len(paths) == 0:
                paths = _get_random_paths(group, force)
        
            if len(paths) > 0:
                path = paths.pop()
                xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_label,
                                                                   path[0]))
                xbmc.executebuiltin('Skin.SetString({},{})'
                                .format(skin_path, path[2].replace('\"','')))
                utils.log('{}: {}'.format(skin_label, path[0]))
                utils.log('{}: {}'.format(skin_path, path[2].replace('\"','')))
                processed += 1
