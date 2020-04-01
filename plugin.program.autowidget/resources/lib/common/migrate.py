import xbmc
import xbmcaddon

import json
import os

from resources.lib import manage

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_version = _addon.getAddonInfo('version')

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
    for file in [i for i in os.listdir(_addon_path) if i.endswith('.group')]:
        with open(os.path.join(_addon_path, file), 'r') as f:
            group_def = json.loads(f.read())
            
        if 'label' not in group_def:
            if 'name' in group_def:
                group_def['label'] = group_def['name']
                group_def = {i: group_def[i] for i in group_def if i != 'name'}
            manage.write_path(group_def)
