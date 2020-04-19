import xbmc
import xbmcgui

import os
import random
import time

from resources.lib import convert
from resources.lib import manage
from resources.lib.common import utils

skin_string_pattern = 'autowidget-{}-{}'


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


def refresh(widget_id, widget_def=None, seen=None, force=False, single=False):
    if not widget_def:
        widget_def = manage.get_widget_by_id(widget_id)
    
    if not single:
        seen = [i['current'] for i in manage.find_defined_widgets(widget_def['group'])]
    
    current_time = time.time()
    updated_at = widget_def.get('updated', current_time)
    
    default_refresh = utils.getSettingNumber('service.refresh_duration')
    refresh_duration = float(widget_def.get('refresh', default_refresh))
            
    if updated_at <= current_time - (3600 * refresh_duration) or force:
        path_def = {}
        _id = widget_def['id']
        group_id = widget_def['group']
        action = widget_def.get('action')
        setting = widget_def.get('path_setting')
        label_setting = widget_def.get('label_setting')
        current = widget_def.get('current')
        if len(seen) == 0:
            seen.append(current)
        
        if action:
            paths = manage.find_defined_paths(group_id)
        
            if action == 'next':
                next = (current + 1) % len(paths)
            elif action == 'random':
                next = random.randrange(len(paths))
                
            if next in seen:
                seen = refresh(widget_id, widget_def, seen=seen, force=force)
            else:                        
                widget_def['current'] = next
                seen.append(next)
                path_def = paths[next]
            
            widget_def['path'] = path_def.get('id')
            if widget_def['path']:
                widget_def['updated'] = current_time
                    
                convert.save_path_details(widget_def, _id)
                _update_strings(_id, path_def, setting, label_setting)
                
                xbmc.executebuiltin('Container.Refresh()')
    
    return seen


def refresh_paths(notify=False, force=False):
    converted = []
    current_time = time.time()
    
    if force:
        converted = convert.convert_widgets(notify)

    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', utils.getString(32033))
    
    for group_def in manage.find_defined_groups():
        seen = []
        
        widgets = manage.find_defined_widgets(group_def['id'])
        for widget_def in widgets:
            seen = refresh(widget_def['id'], widget_def=widget_def, seen=seen, force=force)

    xbmc.executebuiltin('Container.Refresh()')
    if len(converted) > 0 and utils.shortcuts_path:
        xbmc.executebuiltin('ReloadSkin()')
