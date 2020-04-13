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

from resources.lib import convert
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


def refresh(widget_id, widget_def=None, paths=None, force=False, duration=0):
    if not paths:
        paths = []
        
    if not widget_def:
        widget_def = manage.get_widget_by_id(widget_id)
    
    current_time = time.time()
    updated_at = widget_def.get('updated', current_time)
            
    if updated_at < current_time - duration or force:
        path_def = {}
        _id = widget_def['id']
        group_id = widget_def['group']
        action = widget_def['action'].lower()
        setting = widget_def.get('setting')
        label_setting = widget_def.get('label_setting')
        current = widget_def.get('current')

        if action == 'random' and len(paths) == 0:
            paths = _get_random_paths(group_id, force)

        if action == 'next':
            paths = manage.find_defined_paths(group_id)
            next = (current + 1) % len(paths)
            path_def = paths[next]
            widget_def['current'] = next
        elif action == 'random':
            path_def = paths.pop()
        
        widget_def['path'] = path_def['id']
        widget_def['updated'] = current_time
            
        convert.save_path_details(widget_def, _id)
        _update_strings(_id, path_def, setting, label_setting)
        
        xbmc.executebuiltin('Container.Refresh()')
    
    return paths


def refresh_paths(notify=False, force=False, duration=0):
    converted = []
    current_time = time.time()
    
    if force:
        converted = convert.convert_widgets(notify)

    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', _addon.getLocalizedString(32033))
    
    for group_def in manage.find_defined_groups():
        paths = []
        
        widgets = manage.find_defined_widgets(group_def['id'])
        for widget_def in widgets:
            paths = refresh(widget_def['id'], widget_def=widget_def, paths=paths, force=force)

    xbmc.executebuiltin('Container.Refresh()')
    if len(converted) > 0:
        xbmc.executebuiltin('ReloadSkin()')
