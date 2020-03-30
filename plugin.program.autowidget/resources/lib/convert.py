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
if xbmc.getCondVisibility('System.HasAddon(script.skinshortcuts)'):
    _shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    _shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))
else:
    _shortcuts_path = ''
_skin_root = xbmc.translatePath('special://skin/')
_skin_id = os.path.basename(os.path.normpath(_skin_path))
_skin = xbmcaddon.Addon(_skin_id)
_skin_path = xbmc.translatePath(_skin.getAddonInfo('profile'))

activate_window_pattern = '(\w+)*\((\w+\)*),*(.*?\)*),*(return)*\)'
skin_string_pattern = 'autowidget-{}-{}'
skin_string_info_pattern = '$INFO[Skin.String({})]'.format(skin_string_pattern)
path_replace_pattern = '{}({})'
widget_param_pattern = '^(?:\w+)(\W\w+)?$'


def _get_random_paths(group_id, force=False, change_sec=3600):
    wait_time = 5 if force else change_sec
    now = time.time()
    seed = now - (now % wait_time)
    rand = random.Random(seed)
    paths = manage.find_defined_paths(group_id)
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
    
    
def _convert_widgets(notify=False):
    dialog = xbmcgui.Dialog()
    
    converted = _convert_skin_strings()
    
    if _shortcuts_path:    
        dialog.notification('AutoWidget', 'Converting new widgets...')
        converted += _convert_shortcuts() + _convert_properties()
    
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

            converted += 1

        utils.prettify(shortcuts)
        tree = ElementTree.ElementTree(shortcuts)
        tree.write(xml_path)

    return converted

        
def _convert_properties():
    converted = 0

    props_path = os.path.join(_shortcuts_path,
                              '{}.properties'.format(_skin_id))
    with open(props_path, 'r') as f:
        content = ast.literal_eval(f.read())
    
    props = [x for x in content if all(i in x[3]
                                       for i in ['plugin.program.autowidget',
                                                 'mode=path', 'action=random'])]
    for prop in props:
        prop_index = content.index(prop)
        suffix = re.search(widget_param_pattern, prop[2])
        if not suffix:
            continue
            
        details = _save_path_details(prop[3])
        _id = details['id']
        prop[3] = skin_string_info_pattern.format(_id, 'action')
        content[prop_index] = prop
        
        params = [x for x in content if x[:2] == prop[:2]
                  and re.search(widget_param_pattern,
                                x[2]) and re.search(widget_param_pattern,
                                                    x[2]).groups() == suffix.groups()]
        for param in params:
            param_index = content.index(param)
            norm = param[2].lower()
            if 'name' in norm and not 'sort' in norm:
                param[3] = skin_string_info_pattern.format(_id, 'label')
            elif 'target' in norm:
                param[3] = skin_string_info_pattern.format(_id, 'target')
            
            content[param_index] = param
        
        converted += 1
        
    with open(props_path, 'w') as f:
        f.write('{}'.format(content))
        
    return converted


def _convert_skin_strings():
    converted = 0
    
    xml_path = os.path.join(_skin_path, 'settings.xml')
    try:
        settings = ElementTree.parse(xml_path).getroot()
    except ParseError:
        utils.log('Unable to parse: {}/settings.xml'.format(_skin_id))
        
    for setting in settings.findall('setting'):
        if not setting.text or not all(i in setting.text
                                       for i in ['plugin.program.autowidget',
                                                 'mode=path',
                                                 'action=random']):
            continue
            
        details = _save_path_details(setting.text)
        _id = details['id']
        setting.text = skin_string_info_pattern.format(_id, 'label')
        
        converted += 1

    utils.prettify(settings)
    tree = ElementTree.ElementTree(settings)
    tree.write(xml_path)
    
    return converted


def refresh_paths(notify=False, force=False):
    converted = 0
    utils.ensure_addon_data()

    if force:
        converted = _convert_widgets(notify)

    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', _addon.getLocalizedString(32033))
    
    for group_def in manage.find_defined_groups():
        paths = []

        for widget in [x for x in os.listdir(_addon_path) if x.endswith(
                '.widget')]:
            saved_path = os.path.join(_addon_path, widget)
            with open(saved_path, 'r') as f:
                widget_json = json.loads(f.read())

            if group_def['id'] == widget_json['group']:
                _id = widget_json['id']
                group_id = widget_json['group']
                action = widget_json['action'].lower()

                if action == 'random' and len(paths) == 0:
                    paths = _get_random_paths(group_id, force)

                if paths:
                    path = paths.pop()
                    _update_strings(_id, path)

    if converted > 0:
        xbmc.executebuiltin('ReloadSkin()')
