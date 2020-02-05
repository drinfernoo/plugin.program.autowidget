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
    
    defined_paths = _addon.getSettingString('service.defined_paths')
    if defined_paths:
        defined_paths = defined_paths.split(',')
        
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
                    dialog.notification('AutoWidget', 'Unsupported path in {}: {}'.format(group.capitalize(), action))
                    
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
    
    
def add_group():
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading='Name for Group') or ''
    
    if group_name:
        xbmc.executebuiltin('RunScript(script.skinshortcuts,type=manage'
                            '&group=autowidget-{})'.format(group_name.lower()), wait=True)
        xbmc.executebuiltin('Container.Refresh()')
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
    params = dict(parse_qsl(path.split('?')[1]))                    
    action_param = params.get('action', '').replace('\"','')
    group_param = params.get('group', '').replace('\"','')
    id = uuid.uuid4()
    
    path_to_saved = os.path.join(_addon_path, '{}.auto'.format(id))
    
    with open(path_to_saved, "w") as f:
        content = '{},{}'.format(action_param, group_param)
        f.write(content)
    
    utils.log('_save_path_details: {}'.format(id))
    return id

        
def _convert_shortcuts(force=False):
    if not os.path.exists(_shortcuts_path):
        return

    for filename in os.listdir(_shortcuts_path):
        if any(term in filename for term in ['powermenu', '.hash',
                                             '.properties']):
            continue
        
        file_path = os.path.join(_shortcuts_path, filename)
        root = ET.parse(file_path).getroot()
        
        for shortcut in root.findall('shortcut'):
            label = shortcut.find('label')
            action = shortcut.find('action')
            
            if action.text:
                if all(term in action.text for term in ['plugin.program.autowidget', '?mode=path', '&action=random']):
                    path = action.text.split(',')
                else:
                    continue
            else:
                continue
                
            _id = _save_path_details(path[1])
            skin_path = 'autowidget-{}-path'.format(_id)
            skin_name = 'autowidget-{}-name'.format(_id)
            path_string = '$INFO[Skin.String({})]'.format(skin_path)
            name_string = '$INFO[Skin.String({})]'.format(skin_name)
            final = action.text.replace(path[1], path_string).replace('\"', '')
            
            utils.log('Setting skin string {} to path {}...'
                      .format(skin_path, final))
            xbmc.executebuiltin('Skin.SetString({},{})'
                                .format(skin_name, path[0]))
            xbmc.executebuiltin('Skin.SetString({},{})'
                                .format(skin_path, path[2]))
            utils.log('{}: {}'.format(skin_name, path[0]))
            utils.log('{}: {}'.format(skin_path, path[2]))
            
            label.text = name_string
            action.text = final
            
            tree = ET.ElementTree(root)
            tree.write(file_path)
                
                
def _convert_properties():
    skin = xbmc.translatePath('special://skin/')
    skin_id = os.path.basename(os.path.normpath(skin))
    props_path = os.path.join(_shortcuts_path, '{}.properties'.format(skin_id))
    
    if not os.path.exists(props_path):
        return
    
    with open(props_path, 'r') as f:
        content = f.read()
    
    prop_list = ast.literal_eval(content)
    
    for prop in prop_list:
        group, menu, property, value = prop[:]
        
        if all(term in value for term in ['plugin.program.autowidget', '?mode=path']):
            _id = _save_path_details(value)
            
            for check_prop in prop_list:
                index = prop_list.index(check_prop)
                check_group, check_menu, check_property, check_value = check_prop[:]
                
                if check_group != group and check_menu != menu:
                    continue
                
                match = re.search(widget_props_pattern, check_property)
                if match:
                    utils.log('{}: {}'.format(match.group(), check_value))
                    
                    if 'name' in match.group().lower():
                        skin_name = 'autowidget-{}-name'.format(_id)
                        name_string = '$INFO[Skin.String({})]'.format(skin_name)
                        check_prop[3] = name_string
                        
                    if 'path' in match.group().lower():
                        skin_path = 'autowidget-{}-path'.format(_id)
                        path_string = '$INFO[Skin.String({})]'.format(skin_path)
                        if 'ActivateWindow'.lower() not in check_prop[3].lower():
                            check_prop[3] = path_string
                    
                utils.log('prop: {}'.format(check_prop))
                prop_list[index] = check_prop
            
            if re.search(activate_window_pattern, value):
                skin_path = 'autowidget-{}-path'.format(_id)
                path_string = '$INFO[Skin.String({})]'.format(skin_path)
                prop[3] = re.sub(activate_window_pattern, value, path_string)
                
                
    with open(props_path, 'w') as f:
        f.write('{}'.format(prop_list))
                    
                
def refresh_paths(notify=False, force=False):
    utils.ensure_addon_data()
    
    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', 'Refreshing AutoWidgets')
    
    if force:
        _convert_shortcuts()
        _convert_properties()
        xbmc.executebuiltin('ReloadSkin()')
    
    for group in find_defined_groups():
        paths = []
        for saved in [saved for saved in os.listdir(_addon_path) if saved.endswith('.auto')]:
            saved_path = os.path.join(_addon_path, saved)
            with open(saved_path, "r") as f:
                params = f.read().split(',')
                
            action = params[0]
            group_param = params[1]
            
            if group_param != group:
                continue
            
            id = os.path.basename(saved_path)[:-5]
            skin_path = 'autowidget-{}-path'.format(id)
            skin_name = 'autowidget-{}-name'.format(id)
        
            if action == 'random' and len(paths) == 0:
                paths = _get_random_paths(group, force)
        
            if len(paths) > 0:
                path = paths.pop()
                xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_name, path[0]))
                xbmc.executebuiltin('Skin.SetString({},{})'
                                .format(skin_path, path[2].replace('\"','')))
                utils.log('{}: {}'.format(skin_name, path[0]))
                utils.log('{}: {}'.format(skin_path, path[2].replace('\"','')))
