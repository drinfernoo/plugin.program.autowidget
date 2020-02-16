import xbmc
import xbmcaddon
import xbmcgui

import os
import time

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

import json

from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))


def add_path(group, target):
    path_def = {}
    
    widget = ('RunScript(script.skinshortcuts,'
              'type=widgets'
              '&showNone=False'
              '&skinWidget=autoWidget-{0}'
              '&skinWidgetType=autoWidgetType-{0}'
              '&skinWidgetName=autoWidgetName-{0}'
              '&skinWidgetTarget=autoWidgetTarget-{0}'
              '&skinWidgetPath=autoWidgetPath-{0})').format(group)
    
    shortcut = ('RunScript(script.skinshortcuts,'
                'type=shortcuts'
                '&custom=True'
                '&showNone=False'
                '&skinLabel=autoLabel-{0}'
                '&skinAction=autoAction-{0}'
                '&skinList=autoList-{0}'
                '&skinType=autoType-{0}'
                '&skinThumbnail=autoThumbnail-{0})').format(group)
                
    if target == 'widget':
        path = utils.get_skin_string('autoWidgetPath-{}'.format(group))
        xbmc.executebuiltin(widget, wait=True)
        
        while path == utils.get_skin_string('autoWidgetPath-{}'.format(group)):
            time.sleep(1)
        
        path_def.update({'widget': utils.get_skin_string('autoWidget-{}'.format(group)),
                         'type': utils.get_skin_string('autoWidgetType-{}'.format(group)),
                         'name': utils.get_skin_string('autoWidgetName-{}'.format(group)),
                         'target': utils.get_skin_string('autoWidgetTarget-{}'.format(group)),
                         'path': utils.get_skin_string('autoWidgetPath-{}'.format(group))})
    elif target == 'shortcut':
        action = utils.get_skin_string('autoAction-{}'.format(group))
        xbmc.executebuiltin(shortcut, wait=True)
        
        while action == utils.get_skin_string('autoAction-{}'.format(group)):
            time.sleep(1)
        
        path_def.update({'label': utils.get_skin_string('autoLabel-{}'.format(group)),
                         'action': utils.get_skin_string('autoAction-{}'.format(group)),
                         'list': utils.get_skin_string('autoList-{}'.format(group)),
                         'type': utils.get_skin_string('autoType-{}'.format(group)),
                         'thumbnail': utils.get_skin_string('autoThumbnail-{}'.format(group))})
                          
    filename = os.path.join(_addon_path, '{}.group'.format(group))

    with open(filename, 'r') as f:
        group_json = json.loads(f.read())
        group_json['paths'].append(path_def)
    
    with open(filename, 'w') as f:
        f.write(json.dumps(group_json))
        
    xbmc.executebuiltin('Container.Refresh()')
        

def get_group(group):
    for defined in find_defined_groups():
        if defined.get('name', '') == group:
            return defined
    
    
def find_defined_groups():
    groups = []
    
    for filename in [x for x in os.listdir(_addon_path) if x.endswith('.group')]:
        path = os.path.join(_addon_path, filename)
        
        with open(path, 'r') as f:
            group_json = json.loads(f.read())
        
        groups.append(group_json)

    utils.log('find_defined_groups: {}'.format(groups))
    return groups
    
    
def find_defined_paths(group=None):
    paths = []
    filename = ''
        
    if group:
        filename = '{}.group'.format(group)
        path = os.path.join(_addon_path, filename)
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                group_json = json.loads(f.read())
            
            return group_json['paths']
    else:
        for group in find_defined_groups():
            paths.append(find_defined_paths(group.get('name', '')))
    
    utils.log('find_defined_paths: {}'.format(paths))
    return paths
    

def add_group(target):
    dialog = xbmcgui.Dialog()
    group = dialog.input(heading='Name for Group') or ''
    
    if group:
        filename = os.path.join(_addon_path, '{}.group'.format(group.lower()))
        group_def = {'name': group, 'type': target, 'paths': []}
        group_json = json.dumps(group_def)
    
        with open(filename, 'w+') as f:
            f.write(group_json)
            
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', 'Cannot create a group with no name.')
        

def remove_group(group):
    utils.ensure_addon_data()
    
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', ('Are you sure you want to remove this group?'
                                         ' This action [B]cannot[/B] be undone.'))
    
    if choice:
        filename = '{}.group'.format(group).lower()
        filepath = os.path.join(_addon_path, filename)
        try:
            os.remove(filepath)
        except Exception as e:
            utils.log('{}'.format(e), level=xbmc.LOGERROR)
        
        xbmc.executebuiltin('Container.Update(plugin://plugin.program.autowidget/)')
    else:
        dialog.notification('AutoWidget', 'Cannot create a group with no name.')
