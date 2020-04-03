import xbmc
import xbmcaddon

import json
import os

from resources.lib import manage
from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_version = _addon.getAddonInfo('version')

folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')

art_types = ['banner', 'clearart', 'clearlogo', 'fanart', 'icon', 'landscape',
             'poster', 'thumb']
info_labels = ['plot']

one_three_two = [('info', ['plot']),
                  ('paths', [('info', ['plot']),
                             ('art', ['thumb', 'icon', 'poster', 'fanart',
                                      'landscape', 'banner', 'clearlogo',
                                      'clearart']),
                             'target',
                             'label',
                             'content',
                             'window',
                             'version',
                             'is_folder',
                             'path',
                             'id']),
                  ('art', ['thumb', 'icon', 'poster', 'fanart', 'landscape',
                           'banner', 'clearlogo', 'clearart']),
                  'label',
                  'version',
                  'type',
                  'id']
                  
                  
def migrate_groups():
    migrated_groups = []
    for file in [i for i in os.listdir(_addon_path) if i.endswith('.group')]:
        with open(os.path.join(_addon_path, file), 'r') as f:
            try:
                group_def = json.loads(f.read()) 
            except ValueError:
                utils.log('{} is invalid, this is an error!'.format(i),
                          level=xbmc.LOGERROR)
            
        if 'label' not in group_def:
            if 'name' in group_def:
                group_def['label'] = group_def['name']
                group_def = {i: group_def[i] for i in group_def if i != 'name'}
        if 'id' not in group_def:
            if 'label' in group_def:
                group_def['id'] = utils.get_unique_id(group_def['label'])
        if 'version' not in group_def:
            group_def['version'] = _addon_version
        if 'art' not in group_def:
            group_def['art'] = folder_sync if group_def['type'] == 'widget' else folder_shortcut
        else:
            for art in art_types:
                if art not in group_def['art']:
                    group_def['art'][art] = folder_sync[art] if group_def['type'] == 'widget' else folder_shortcut[art]
        if 'info' not in group_def:
            group_def['info'] = {'plot': ''}
        else:
            for info in info_labels:
                if info not in group_def['info']:
                    group_def['info'][info] = ''
                    
        if 'paths' not in group_def:
            group_def['paths'] = []
        else:
            for path_def in group_def['paths']:
                if 'id' not in path_def:
                    if 'label' in path_def:
                        path_def['id'] = utils.get_unique_id(path_def['label'])
                if 'target' in path_def:
                    if path_def['target'] == 'folder':
                        path_def['target'] = 'widget'
                if 'content' not in path_def:
                    if 'type' in path_def:
                        path_def['content'] = path_def['type']
                        path_def = {i: path_def[i] for i in path_def if i != 'type'}
                if 'is_folder' not in path_def:
                    path_def['is_folder'] = 1 if path_def['target'] == 'widget' else 0
                if 'version' not in path_def:
                    path_def['version'] = _addon_version
                if 'art' not in path_def:
                    path_def['art'] = folder_sync if path_def['target'] == 'widget' else folder_shortcut
                else:
                    for art in art_types:
                        if art not in path_def['art']:
                            path_def['art'][art] = folder_sync[art] if path_def['target'] == 'widget' else folder_shortcut[art]
                if 'icon' in path_def:
                    path_def = {i: path_def[i] for i in path_def if i != 'icon'}
                if 'info' not in path_def:
                    path_def['info'] = {'plot': ''}
                else:
                    for info in info_labels:
                        if info not in path_def['info']:
                            path_def['info'][info] = ''
        
        migrated_groups.append((group_def['label'], group_def['id']))
        manage.write_path(group_def)
        
    for file in [i for i in os.listdir(_addon_path) if i.endswith('.widget')]:
        widget_path = os.path.join(_addon_data, file)
        with open(widget_path, 'r') as f:
            try:
                widget_def = json.loads(f.read()) 
            except ValueError:
                utils.log('{} is invalid, this is an error!'.format(i),
                          level=xbmc.LOGERROR)
            
        if 'version' not in widget_def:
            widget_def['version'] = _addon_version
        if 'group' in widget_def:
            for group in migrated_groups:
                if group[0] == widget_def['group']:
                    widget_def['group'] = group[1]
        
        with open(widget_path, 'w') as f:
            try:
                f.write(json.dumps(widget_def, indent=4))
            except Exception as e:
                utils.log('{} couldn\'t be written to: {}'.format(widget_path, e),
                          level=xbmc.LOGERROR)
