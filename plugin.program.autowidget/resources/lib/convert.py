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
_addon_version = _addon.getAddonInfo('version')

if xbmc.getCondVisibility('System.HasAddon(script.skinshortcuts)'):
    _shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    _shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))
else:
    _shortcuts_path = ''
_skin_root = xbmc.translatePath('special://skin/')
_skin_id = os.path.basename(os.path.normpath(_skin_root))
_skin = xbmcaddon.Addon(_skin_id)
_skin_path = xbmc.translatePath(_skin.getAddonInfo('profile'))

activate_window_pattern = '(\w+)*\((\w+\)*),*(.*?\)*),*(return)*\)'
skin_string_pattern = 'autowidget-{}-{}'
skin_string_info_pattern = '$INFO[Skin.String({})]'.format(skin_string_pattern)
path_replace_pattern = '{}({})'
widget_param_pattern = '^(?:\w+)(\W\w+)?$'
uuid_pattern = ('[0-9a-fA-F]{8}'
                '\-[0-9a-fA-F]{4}'
                '\-[0-9a-fA-F]{4}'
                '\-[0-9a-fA-F]{4}'
                '\-[0-9a-fA-F]{12}')
label_pattern = ('^(?:AutoWidget - )?'
                 '(?:Random|Next) Path from .+'
                 '\(([0-9a-fA-F]{8}'
                 '\-[0-9a-fA-F]{4}'
                 '\-[0-9a-fA-F]{4}'
                 '\-[0-9a-fA-F]{4}'
                 '\-[0-9a-fA-F]{12})\)$')


def _get_random_paths(group_id, force=False, change_sec=3600):
    wait_time = 5 if force else change_sec
    now = time.time()
    seed = now - (now % wait_time)
    rand = random.Random(seed)
    paths = manage.find_defined_paths(group_id)
    rand.shuffle(paths)

    return paths


def save_path_details(params, _id=''):
    for param in params:
        if str(params[param]).endswith(',return)'):
            return
    
    if not _id:
        _id = params.get('id')
        if not _id:
            return
    
    path_to_saved = os.path.join(_addon_path, '{}.widget'.format(_id))
    params['version'] = _addon_version
    
    if 'refresh' not in params:
        params['refresh'] = utils.get_setting_float('service.refresh_duration')

    utils.write_json(path_to_saved, params)

    return params


def _update_strings(_id, path_def, setting=None, label_setting=None):
    if not path_def:
        return
    
    label = path_def['label']
    action = path_def['path']
    
    if setting:
        if label_setting:
            utils.log('Setting {} to {}'.format(label_setting, label))
            utils.set_skin_string(label_setting, label)
        
        utils.log('Setting {} to {}'.format(setting, action))
        utils.set_skin_string(setting, action)
    else:
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
    
    
def convert_widgets(notify=False):
    dialog = xbmcgui.Dialog()
    
    converted = []
    
    converted.extend(_convert_skin_strings(converted))
    
    if _shortcuts_path:    
        dialog.notification('AutoWidget', utils.get_string(32062))
        converted.extend(_convert_shortcuts(converted))
        converted.extend(_convert_properties(converted))
    
    return converted
    
    
def _convert_skin_strings(converted):
    xml_path = os.path.join(_skin_path, 'settings.xml')
    settings = utils.read_xml(xml_path)
    
    if settings is None:
        return converted
    
    settings = [i for i in settings.findall('setting') if i.text]
    path_settings = [i for i in settings if 'plugin.program.autowidget' in i.text
                                         and re.search(uuid_pattern, i.text)
                                         and not re.match(activate_window_pattern, i.text)]
    label_settings = [i for i in settings if 'plugin.program.autowidget' not in i.text
                                         and re.match(label_pattern, i.text)]
    for path in path_settings:
        path_id = path.get('id')
        if not path_id:
            continue
            
        params = dict(parse_qsl(path.text.split('?')[1].replace('\"', '')))
        
        _id = params.get('id')
        if params.get('target') == 'shortcut':
            pass
        else:
            params['path_setting'] = path_id
            for label in label_settings:
                if _id in label.text:
                    params['label_setting'] = label.get('id')
                    break
    
        if _id and _id not in converted:
            save_path_details(params)
            converted.append(_id)

    return converted


def _convert_shortcuts(converted):    
    shortcut_files = os.listdir(_shortcuts_path)
    shortcut_files = [x for x in shortcut_files if x.endswith('.DATA.xml')
                                                and 'powermenu' not in x]
    for xml in shortcut_files:
        xml_path = os.path.join(_shortcuts_path, xml)
        shortcuts = utils.read_xml(xml_path)
        
        if shortcuts is None:
            continue

        for shortcut in shortcuts.findall('shortcut'):
            label_node = shortcut.find('label')
            action_node = shortcut.find('action')

            match = re.search(activate_window_pattern,
                              action_node.text if action_node.text else '')
            if not match:
                continue
            
            groups = list(match.groups())

            if not groups or len(groups) < 2:
                continue

            id_match = re.search(uuid_pattern, groups[2])
            if 'plugin.program.autowidget' in groups[2] and id_match:
                params = dict(parse_qsl(groups[2].split('?')[1].replace('\"', '')))
                if not params:
                    continue
                    
                _id = params.get('id')
                if params.get('target') == 'shortcut':
                    pass
                else:
                    label_node.text = skin_string_info_pattern.format(_id,
                                                                  'label')

                    groups[1], groups[2] = (skin_string_info_pattern.format(_id,
                                            i) for i in ['target', 'action'])

                    action_node.text = path_replace_pattern.format(groups[0],
                                                                   ','.join(groups[1:]))
                if _id and _id not in converted:
                    save_path_details(params)
                    converted.append(_id)

        utils.write_xml(xml_path, shortcuts)

    return converted

        
def _convert_properties(converted):
    props_path = os.path.join(_shortcuts_path,
                              '{}.properties'.format(_skin_id))
    if not os.path.exists(props_path):
        return converted
        
    try:
        content = ast.literal_eval(utils.read_file(props_path))
    except Exception as e:
        utils.log('Unable to parse: {}'.format(props_path))
        return converted
    
    
    props = [x for x in content if 'plugin.program.autowidget' in x[3]
                                and re.search(uuid_pattern, x[3])]
    label_props = [x for x in content if 'plugin.program.autowidget' not in x[3]
                                      and re.search(uuid_pattern, x[3])]
    for prop in props:        
        if 'ActivateWindow' in prop[3]:
            match = re.search(activate_window_pattern, prop[3])
            if not match:
                continue

            groups = list(match.groups())
            if not groups or len(groups) < 2:
                continue
                
            id_match = re.search(uuid_pattern, groups[2])
            if 'plugin.program.autowidget' in groups[2] and id_match:
                params = dict(parse_qsl(groups[2].split('?')[1].replace('\"', '')))
                
            if not params:
                continue
            
            _id = params.get('id')
            groups[1], groups[2] = (skin_string_info_pattern.format(_id,
                                            i) for i in ['target', 'action'])

            if params.get('target') != 'shortcut':
                prop[3] = path_replace_pattern.format(groups[0],
                                                      ','.join(groups[1:]))
        else:
            params = dict(parse_qsl(prop[3].split('?')[1].replace('\"', '')))
            if not params:
                continue
            
            _id = params.get('id')
            if params.get('target') != 'shortcut':
                prop[3] = skin_string_info_pattern.format(_id, 'action')
        
        
        if params.get('target') == 'shortcut':
            pass
        else:        
            params['path_prop'] = prop[:3]
            
            for label_prop in label_props:
                if _id in label_prop[3]:
                    label_prop[3] = skin_string_info_pattern.format(_id, 'label')
                    params['label_prop'] = label_prop[:3]
                    break
        
        if _id and _id not in converted:
            save_path_details(params)
            converted.append(_id)
    
    inner_content = ''
    for idx, line in enumerate(content):
        inner_content += '{}{}'.format(line, ',\n' if idx < len(content) else '')
    final_content = '[{}]'.format(inner_content)
    
    utils.write_file(props_path, final_content)
        
    return converted
