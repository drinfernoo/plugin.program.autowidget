import xbmc
import xbmcaddon
import xbmcgui

import ast
import os
import random
import re
import time
import uuid

from xml.etree import ElementTree

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

from resources.lib import manage
from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_shortcuts = xbmcaddon.Addon('script.skinshortcuts')
_shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))

# widget_props_pattern = '\w*[.-]*[wW]idget(\w+)[.-]*\w*'
activate_window_pattern = '(\w+)*\((\w+\)*),*(.*?\)*),*(return)*\)'


def _get_random_paths(group, force=False, change_sec=3600):
    wait_time = 5 if force else change_sec
    now = time.time()
    seed = now - (now % wait_time)
    rand = random.Random(seed)
    paths = manage.find_defined_paths(group)
    rand.shuffle(paths)
    
    utils.log('_get_random_paths: {}'.format(paths))
    return paths
    

def _save_path_details(path):
    match = re.search(activate_window_pattern, path)
    if not match.group(2):
        return
    
    params = dict(parse_qsl(match.group(2).split('?')[1]))
    _id = uuid.uuid4()
    
    path_to_saved = os.path.join(_addon_path, '{}.widget'.format(_id))
    
    with open(path_to_saved, 'w') as f:
        f.write('{}'.format(params))
    
    utils.log('_save_path_details: {}'.format(_id))
    return _id, match
                
                
def _process_widgets():
    if not os.path.exists(_shortcuts_path):
        return
    
    for xml in [x for x in os.listdir(_shortcuts_path)
                 if not any(i in x for i in ['.properties', '.hash',
                                             'settings.xml', 'powermenu'])]:
        xml_path = os.path.join(_shortcuts_path, xml)
        shortcuts = ElementTree.parse(xml_path).getroot()

        for shortcut in shortcuts.findall('shortcut'):
            label_node = shortcut.find('label')
            action_node = shortcut.find('action')

            match = re.search(activate_window_pattern, action_node.text)


def refresh_paths(notify=False, force=False):
    processed = 0
    
    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', 'Refreshing AutoWidgets')
    
    if force:
        _process_widgets()
        # xbmc.executebuiltin('ReloadSkin()')
    
    for group in manage.find_defined_groups():
        paths = []
        groupname = group['name'].lower()
        # saved_path = os.path.join(_addon_path, '{}.group'.format(groupname))
        
        for saved in [saved for saved in os.listdir(_addon_path)
                      if saved.endswith('.widget')]:
            saved_path = os.path.join(_addon_path, saved)
            with open(saved_path, 'r') as f:
                params = ast.literal_eval(f.read())
                
            action = params['action'].lower()
            group_param = params['group'].lower()
            
            if group_param != groupname:
                continue
                
            _id = os.path.basename(saved_path)[:-8]
            skin_path = 'autowidget-{}-path'.format(_id)
            skin_label = 'autowidget-{}-name'.format(_id)
        
            if action == 'random' and len(paths) == 0:
                paths = _get_random_paths(groupname, force)
        
            if len(paths) > 0:
                path = paths.pop()
                xbmc.executebuiltin('Skin.SetString({},{})'.format(skin_label,
                                                                   path['name']))
                xbmc.executebuiltin('Skin.SetString({},{})'
                                .format(skin_path, path['path'].replace('\"','')))
                utils.log('{}: {}'.format(skin_label, path['name']))
                utils.log('{}: {}'.format(skin_path, path['path'].replace('\"','')))
                processed += 1
