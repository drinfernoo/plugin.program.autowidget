import xbmc
import xbmcaddon
import xbmcgui

import ast
import json
import os
import time

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))

widget_strings = ['autoWidget-{}', 'autoWidgetType-{}', 'autoWidgetName-{}',
                  'autoWidgetTarget-{}', 'autoWidgetPath-{}']

shortcut_strings = ['autoLabel-{}', 'autoAction-{}', 'autoList-{}',
                    'autoType-{}', 'autoThumbnail-{}']
                    
folder_add = utils.get_art('folder-add.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
share = utils.get_art('share.png')


def add_path(group, target, path_def=None):
    if not path_def:
        path_def = {}
    
        widget = ('RunScript(script.skinshortcuts,'
                  'type=widgets'
                  '&showNone=False'
                  '&skinWidget=autoWidget-{0}'
                  '&skinWidgetType=autoWidgetType-{0}'
                  '&skinWidgetTarget=autoWidgetTarget-{0}'
                  '&skinWidgetPath=autoWidgetPath-{0})').format(group)
        
        shortcut = ('RunScript(script.skinshortcuts,'
                    'type=shortcuts'
                    '&custom=True'
                    '&showNone=False'
                    '&skinAction=autoAction-{0}'
                    '&skinList=autoList-{0}'
                    '&skinType=autoType-{0}'
                    '&skinThumbnail=autoThumbnail-{0})').format(group)
                    
        if target == 'widget':
            path = utils.get_skin_string('autoWidgetPath-{}'.format(group))
            xbmc.executebuiltin(widget, wait=True)
            while path == utils.get_skin_string('autoWidgetPath-{}'.format(group)):
                time.sleep(1)
            
            name = utils.get_skin_string('autoWidgetName-{}'.format(group))
            xbmc.executebuiltin('Skin.SetString(autoWidgetName-{})'.format(group), wait=True)
            while name == utils.get_skin_string('autoWidgetName-{}'.format(group)):
                time.sleep(1)
            
            path_def.update({'widget': utils.get_skin_string(widget_strings[0].format(group)),
                             'type': utils.get_skin_string(widget_strings[1].format(group)),
                             'name': utils.get_skin_string(widget_strings[2].format(group)),
                             'target': utils.get_skin_string(widget_strings[3].format(group)),
                             'path': utils.get_skin_string(widget_strings[4].format(group))})
            for label in widget_strings:
                xbmc.executebuiltin('Skin.Reset({})'.format(label.format(group)))
        elif target == 'shortcut':
            action = utils.get_skin_string('autoAction-{}'.format(group))
            xbmc.executebuiltin(shortcut, wait=True)
            while action == utils.get_skin_string('autoAction-{}'.format(group)):
                time.sleep(1)
                
            label = utils.get_skin_string('autoLabel-{}'.format(group))
            xbmc.executebuiltin('Skin.SetString(autoLabel-{})'.format(group), wait=True)
            while label == utils.get_skin_string('autoLabel-{}'.format(group)):
                time.sleep(1)
            
            path_def.update({'label': utils.get_skin_string(shortcut_strings[0].format(group)),
                             'action': utils.get_skin_string(shortcut_strings[1].format(group)),
                             'list': utils.get_skin_string(shortcut_strings[2].format(group)),
                             'type': utils.get_skin_string(shortcut_strings[3].format(group)),
                             'thumbnail': utils.get_skin_string(shortcut_strings[4].format(group))})
            for label in shortcut_strings:
                xbmc.executebuiltin('Skin.Reset({})'.format(label.format(group)))
                          
    filename = os.path.join(_addon_path, '{}.group'.format(group))

    group_json = get_group(group)
    group_json['paths'].append(path_def)
    
    with open(filename, 'w') as f:
        f.write(json.dumps(group_json, indent=4))
        
    xbmc.executebuiltin('Container.Refresh()')
    
   
def add_path_to_group(label, path, icon, groupname=None):
    groups = find_defined_groups();
    names = [group['name'] for group in groups]
    index = -1
    if groupname:
        index = names.index(groupname) + 2
    
    new_widget = xbmcgui.ListItem(_addon.getLocalizedString(32015))
    new_widget.setArt({'icon': folder_add})
    new_shortcut = xbmcgui.ListItem(_addon.getLocalizedString(32017))
    new_shortcut.setArt({'icon': share})
    options = [new_widget, new_shortcut]
    for group in groups:
        item = xbmcgui.ListItem(group['name'])
        item.setArt({'icon': folder_sync if group['type'] == 'widget' else folder_shortcut})
        options.append(item)
    
    dialog = xbmcgui.Dialog()
    choice = dialog.select('Choose a Group', options, preselect=index,
                           useDetails=True)
    
    if choice < 0:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32034))
    elif choice == 0:
        name = add_group('widget')
        add_path_to_group(label, path, icon, name)
    elif choice == 1:
        name = add_group('shortcut')
        add_path_to_group(label, path, icon, name)
    else:
        group = groups[choice - 2]
        
        if group['type'] == 'shortcut':
            path_def = {'label': label,
                        'action': path,
                        'list': '',
                        'type': '',
                        'thumbnail': icon}
        elif group['type'] == 'widget':
            path_def = {'widget': '',
                        'path': path,
                        'type': '',
                        'target': '',
                        'name': label}
                        
        add_path(group['name'], group['type'], path_def)
                

def remove_path(group, path):
    utils.ensure_addon_data()
    
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32035))
    
    if choice:
        group_def = get_group(group)
    
        filename = os.path.join(_addon_path, '{}.group'.format(group_def['name']))
        with open(filename, 'r') as f:
            group_json = json.loads(f.read())
    
        paths = group_json['paths']
        for path_json in paths:
            if path_json.get('name', '') == path or path_json.get('label', '') == path:
                group_json['paths'].remove(path_json)
                
        with open(filename, 'w') as f:
            f.write(json.dumps(group_json, indent=4))
            
        xbmc.executebuiltin('Container.Refresh()'.format(group))
    else:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32036))
        
        
def shift_path(group, path, target):
    utils.ensure_addon_data()
    
    group_def = get_group(group)
    
    filename = os.path.join(_addon_path, '{}.group'.format(group_def['name']))
    with open(filename, 'r') as f:
        group_json = json.loads(f.read())

    paths = group_json['paths']
    for idx, path_json in enumerate(paths):
        if path_json.get('name', '') == path or path_json.get('label', '') == path:
            if target == 'up' and idx > 0:
                temp = paths[idx - 1]
                group_json['paths'][idx - 1] = paths[idx]
                group_json['paths'][idx] = temp
            elif target == 'down' and idx < len(paths) - 1:
                temp = paths[idx + 1]
                group_json['paths'][idx + 1] = paths[idx]
                group_json['paths'][idx] = temp
            
    with open(filename, 'w') as f:
        f.write(json.dumps(group_json, indent=4))
        
    xbmc.executebuiltin('Container.Refresh()'.format(group))
        

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
    group = dialog.input(heading=_addon.getLocalizedString(32037)) or ''
    
    if group:
        filename = os.path.join(_addon_path, '{}.group'.format(group.lower()))
        group_def = {'name': group, 'type': target, 'paths': []}
    
        with open(filename, 'w+') as f:
            f.write(json.dumps(group_def, indent=4))
            
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32038))
    
    return group
        

def remove_group(group):
    utils.ensure_addon_data()
    
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32039))
    
    if choice:
        filename = '{}.group'.format(group).lower()
        filepath = os.path.join(_addon_path, filename)
        try:
            os.remove(filepath)
        except Exception as e:
            utils.log('{}'.format(e), level=xbmc.LOGERROR)
        
        xbmc.executebuiltin('Container.Update(plugin://plugin.program.autowidget/)')
    else:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32040))
