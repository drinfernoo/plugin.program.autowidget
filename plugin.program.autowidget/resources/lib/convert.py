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
uuid_pattern = ('\(([0-9a-fA-F]{8}'
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


def _save_path_details(params, _id=''):
    if not _id:
        _id = params['id']
    
    path_to_saved = os.path.join(_addon_path, '{}.widget'.format(_id))
    params['version'] = _addon_version
    if 'current' not in params:
        params['current'] = -1
    
    for param in params:
        if str(params[param]).endswith(',return)'):
            return

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
    
    
def _convert_widgets(notify=False):
    dialog = xbmcgui.Dialog()
    
    converted = []
    
    converted.extend(_convert_skin_strings(converted))
    
    if _shortcuts_path:    
        dialog.notification('AutoWidget', _addon.getLocalizedString(32062))
        converted.extend(_convert_shortcuts(converted))
        converted.extend(_convert_properties(converted))
    
    return converted
    
    
def _convert_skin_strings(converted):
    xml_path = os.path.join(_skin_path, 'settings.xml')
    settings = utils.read_xml(xml_path)
    
    if settings is None:
        return converted
    
    settings = [i for i in settings.findall('setting') if i.text]
    path_settings = [i for i in settings if all(j in i.text
                                            for j in ['plugin.program.autowidget',
                                                      'mode=path'])]
    label_settings = [i for i in settings if re.match(uuid_pattern, i.text)]
    
    for path in path_settings:
        path_id = path.get('id')
        params = dict(parse_qsl(path.text.split('?')[1].replace('\"', '')))
        params['setting'] = path_id
        
        for label in label_settings:
            if params.get('id') in label.text:
                params['label_setting'] = label.get('id')
    
        if params.get('id') not in converted:
            details = _save_path_details(params)
            if details:
                _id = details['id']
                if _id not in converted:
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

            if not action_node.text:
                continue

            match = re.search(activate_window_pattern, action_node.text)
            if not match:
                continue

            groups = list(match.groups())

            if not groups[2] or not all(i in groups[2] for i in [
                'plugin.program.autowidget', 'mode=path']):
                continue

            params = dict(parse_qsl(groups[2].split('?')[1].replace('\"', '')))
            details = _save_path_details(params)
            if not details:
                continue
                
            _id = details['id']
            label_node.text = skin_string_info_pattern.format(_id, 'label')

            groups[1] = skin_string_info_pattern.format(_id, 'target')
            groups[2] = skin_string_info_pattern.format(_id, 'action')

            action_node.text = path_replace_pattern.format(groups[0],
                                                           ','.join(groups[1:]))

            converted.append(_id)

        utils.prettify(shortcuts)
        tree = ElementTree.ElementTree(shortcuts)
        try:
            tree.write(xml_path)
        except:
            utils.log('{} couldn\'t be written to: {}'.format(xml_path, e),
                      level=xbmc.LOGERROR)

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
        
    props = [x for x in content if all(i in x[3]
                                       for i in ['plugin.program.autowidget',
                                                 'mode=path'])]
    for prop in props:
        prop_index = content.index(prop)
        suffix = re.search(widget_param_pattern, prop[2])
        if not suffix:
            continue
        
        if 'ActivateWindow' in prop[3]:
            match = re.search(activate_window_pattern, prop[3])
            if not match:
                continue
                
            groups = list(match.groups())
            if not groups[2] or not all(i in groups[2] for i in ['plugin.program.autowidget', 'mode=path']):
                continue
        
            params = dict(parse_qsl(groups[2].split('?')[1].replace('\"', '')))
        else:
            params = dict(parse_qsl(prop[3].split('?')[1].replace('\"', '')))
        
        details = _save_path_details(params)
        if not details:
            continue
        
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
        
        converted.append(_id)
        
    utils.write_file(props_path, '{}'.format(content))
        
    return converted


def refresh_paths(notify=False, force=False):
    converted = []
    
    if force:
        converted = _convert_widgets(notify)

    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', _addon.getLocalizedString(32033))
    
    for group_def in manage.find_defined_groups():
        paths = []

        for widget_def in manage.find_defined_widgets(group_def['id']):
            path_def = {}
            _id = widget_def['id']
            group_id = widget_def['group']
            action = widget_def['action'].lower()
            setting = widget_def.get('setting')
            label_setting = widget_def.get('label_setting')
            current = widget_def.get('current')

            if action == 'random' and len(paths) == 0:
                paths = _get_random_paths(group_id, force)
            elif action == 'next':
                next_paths = manage.find_defined_paths(group_id)
                next = (current + 1) % len(next_paths)
                path_def = next_paths[next]
                widget_def['current'] = next
                _save_path_details(widget_def, _id)
                
            if action == 'random' and len(paths) > 0:
                path_def = paths.pop()
                
            _update_strings(_id, path_def, setting, label_setting)

    if len(converted) > 0:
        xbmc.executebuiltin('ReloadSkin()')
