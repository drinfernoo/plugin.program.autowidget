import xbmc
import xbmcgui

import os
import random
import time

from resources.lib import convert
from resources.lib import manage
from resources.lib.common import utils

skin_string_pattern = 'autowidget-{}-{}'


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
    
    try:
        label = label.encode('utf-8')
    except:
        pass
    
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


def refresh(widget_id, widget_def=None, paths=None, force=False):
    if not paths:
        paths = []
        
    if not widget_def:
        widget_def = manage.get_widget_by_id(widget_id)
    
    current_time = time.time()
    updated_at = widget_def.get('updated', current_time)
    
    default_refresh = utils.getSettingNumber('service.refresh_duration')
    refresh = float(widget_def.get('refresh', default_refresh))
            
    if updated_at <= current_time - (3600 * refresh) or force:
        path_def = {}
        _id = widget_def['id']
        group_id = widget_def['group']
        action = widget_def.get('action')
        setting = widget_def.get('path_setting')
        label_setting = widget_def.get('label_setting')
        current = widget_def.get('current')
        
        if action:
            if action == 'random' and len(paths) == 0:
                paths = _get_random_paths(group_id, force)

            if action == 'next':
                paths = manage.find_defined_paths(group_id)
                next = (current + 1) % len(paths)
                path_def = paths[next]
                widget_def['current'] = next
            elif action == 'random':
                path_def = paths.pop()
                paths = manage.find_defined_paths(group_id)
                widget_def['current'] = paths.index(path_def)
            
            widget_def['path'] = path_def['id']
            widget_def['updated'] = current_time
                
            convert.save_path_details(widget_def, _id)
            _update_strings(_id, path_def, setting, label_setting)
            
            xbmc.executebuiltin('Container.Refresh()')
    
    return paths


def refresh_paths(notify=False, force=False):
    converted = []
    current_time = time.time()
    
    if force:
        converted = convert.convert_widgets(notify)

    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', utils.getString(32033))
    
    for group_def in manage.find_defined_groups():
        paths = []
        
        widgets = manage.find_defined_widgets(group_def['id'])
        for widget_def in widgets:
            paths = refresh(widget_def['id'], widget_def=widget_def, paths=paths, force=force)

    xbmc.executebuiltin('Container.Refresh()')
    if len(converted) > 0 and utils.shortcuts_path:
        xbmc.executebuiltin('ReloadSkin()')
