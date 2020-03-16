import xbmc
import xbmcaddon
import xbmcgui

import ast
import json
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
_skin = xbmc.translatePath('special://skin/')
_skin_name = os.path.basename(os.path.normpath(_skin))

activate_window_pattern = '(\w+)*\((\w+\)*),*(.*?\)*),*(return)*\)'
skin_string_pattern = 'autowidget-{}-{}'
skin_string_info_pattern = '$INFO[Skin.String({})]'.format(skin_string_pattern)
path_replace_pattern = '{}({})'


def _get_random_paths(group, force=False, change_sec=3600):
    wait_time = 5 if force else change_sec
    now = time.time()
    seed = now - (now % wait_time)
    rand = random.Random(seed)
    paths = manage.find_defined_paths(group)
    rand.shuffle(paths)

    return paths


def _save_path_details(path):
    params = dict(parse_qsl(path.split('?')[1].replace('\"', '')))
    _id = uuid.uuid4()

    path_to_saved = os.path.join(_addon_path, '{}.widget'.format(_id))
    params.update({'id': '{}'.format(_id)})

    with open(path_to_saved, 'w') as f:
        f.write(json.dumps(params, indent=4))

    return params


def _update_strings(_id, path_def):
    label = path_def['label']
    action = path_def['path']
    target = path_def['window']
    label_string = skin_string_pattern.format(_id, 'label')
    action_string = skin_string_pattern.format(_id, 'action')
    target_string = skin_string_pattern.format(_id, 'target')

    utils.log('Setting {} to {}'.format(label_string, label))
    utils.log('Setting {} to {}'.format(action_string, action))
    utils.log('Setting {} to {}'.format(target_string, target))
    utils.set_skin_string(label_string, label)
    utils.set_skin_string(action_string, action)
    utils.set_skin_string(target_string, target)
    
    
def _convert_widgets():
    converted = _convert_shortcuts()
    
    if converted == 0:
        converted = _convert_properties()
    
    return converted


def _convert_shortcuts():
    converted = 0
    
    for xml in [x for x in os.listdir(_shortcuts_path)
                if x.endswith('.DATA.xml') and 'powermenu' not in x]:
        xml_path = os.path.join(_shortcuts_path, xml)
        
        try:
            shortcuts = ElementTree.parse(xml_path).getroot()
        except ParseError:
            utils.log('Unable to parse: {}'.format(xml))

        for shortcut in shortcuts.findall('shortcut'):
            label_node = shortcut.find('label')
            action_node = shortcut.find('action')

            if not action_node.text:
                continue

            match = re.search(activate_window_pattern, action_node.text)
            if not match:
                continue

            groups = list(match.groups())

            if not groups[2] or not all(i in groups[2] for i in [
                'plugin.program.autowidget', 'mode=path', 'action=random']):
                continue

            details = _save_path_details(groups[2])
            _id = details['id']
            label_node.text = skin_string_info_pattern.format(_id, 'label')

            # groups[0] = skin_string_pattern.format(_id, 'command')
            groups[1] = skin_string_info_pattern.format(_id, 'target')
            groups[2] = skin_string_info_pattern.format(_id, 'action')

            action_node.text = path_replace_pattern.format(groups[0],
                                                           ','.join(groups[1:]))

            if details['action'] == 'random':
                paths = _get_random_paths(details['group'], force=True)

                if paths:
                    path = paths.pop()
                    _update_strings(_id, path)

            converted += 1

        utils.prettify(shortcuts)
        tree = ElementTree.ElementTree(shortcuts)
        tree.write(xml_path)

    return converted
        
        
def _convert_properties():
    converted = 0

    if not os.path.exists(_shortcuts_path):
        return
        
    props_path = os.path.join(_shortcuts_path,
                              '{}.properties'.format(_skin_name))
    with open(props_path, 'r') as f:
        props = ast.literal_eval(f.read())
        
    for prop in props:
        match = re.search(activate_window_pattern, prop[3])
        if match:
            groups = match.groups()
            if all(i in groups[2] for i in ['plugin.program.autowidget',
                                            'mode=path',
                                            'action=random']):
                utils.log('{}'.format(groups))
                
    return converted


def refresh_paths(notify=False, force=False):
    converted = 0
    utils.ensure_addon_data()

    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', _addon.getLocalizedString(32033))

    if force:
        converted = _convert_widgets()

    for group_def in manage.find_defined_groups():
        paths = []

        for widget in [x for x in os.listdir(_addon_path) if x.endswith(
                '.widget')]:
            saved_path = os.path.join(_addon_path, widget)
            with open(saved_path, 'r') as f:
                widget_json = json.loads(f.read())

            if group_def['name'] == widget_json['group']:
                _id = widget_json['id']
                group = widget_json['group'].lower().replace('\"', '')
                action = widget_json['action'].lower()

                if action == 'random' and len(paths) == 0:
                    paths = _get_random_paths(group, force)

                if paths:
                    path = paths.pop()
                    _update_strings(_id, path)

    if converted > 0:
        xbmc.executebuiltin('ReloadSkin()')
    else:
        xbmc.executebuiltin('UpdateLibrary(Video,UpdateWidgets,true)')
