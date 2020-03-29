import xbmc
import xbmcaddon
import xbmcgui

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

folder_add = utils.get_art('folder-add.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
share = utils.get_art('share.png')
folder_settings = utils.get_art('folder-settings.png')


def write_path(group_def, path_def=None, update=''):
    filename = os.path.join(_addon_path, '{}.group'.format(group_def['id']))

    if update and path_def:
        for path in group_def['paths']:
            if path['id'] == update:
                group_def['paths'][group_def['paths'].index(path)] = path_def
    elif path_def:
        group_def['paths'].append(path_def)

    with open(filename, 'w') as f:
        f.write(json.dumps(group_def, indent=4))
    
    
def add_path(group_def, labels):
    if group_def['type'] == 'shortcut':
        labels['label'] = xbmcgui.Dialog().input(heading=_addon.getLocalizedString(32043),
                                                 defaultt=labels['label'])
    elif group_def['type'] == 'widget':
        labels['label'] = xbmcgui.Dialog().input(heading=_addon.getLocalizedString(32044),
                                                 defaultt=labels['label'])
    
    labels['id'] = utils.get_valid_filename('{}-{}'.format(labels['label'], time.time()).lower())
    
    write_path(group_def, labels)


def remove_path(group_id, path_id):
    utils.ensure_addon_data()
    
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32035))
    
    if choice:
        group_def = get_group_by_id(group_id)
    
        filename = os.path.join(_addon_path, '{}.group'.format(group_def['id']))
        with open(filename, 'r') as f:
            group_def = json.loads(f.read())
    
        paths = group_def['paths']
        for path_def in paths:
            if path_def.get['id'] == path_id:
                path_name = path_def['name']
                group_def['paths'].remove(path_def)
                dialog.notification('AutoWidget', _addon.getLocalizedString(32045).format(path_name))
                
        with open(filename, 'w') as f:
            f.write(json.dumps(group_def, indent=4))
            
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32036))
        
        
def shift_path(group_id, path_id, target):
    utils.ensure_addon_data()
    
    group_def = get_group_by_id(group_id)
    
    filename = os.path.join(_addon_path, '{}.group'.format(group_def['id']))
    with open(filename, 'r') as f:
        group_json = json.loads(f.read())

    paths = group_json['paths']
    for idx, path_json in enumerate(paths):
        if path_json['id'] == path_id:
            if target == 'up' and idx > 0:
                temp = paths[idx - 1]
                paths[idx - 1] = path_json
                paths[idx] = temp
            elif target == 'down' and idx < len(paths) - 1: 
                temp = paths[idx + 1]
                paths[idx + 1] = path_json
                paths[idx] = temp
            
            break
                
    group_json['paths'] = paths
            
    with open(filename, 'w') as f:
        f.write(json.dumps(group_json, indent=4))
        
    xbmc.executebuiltin('Container.Refresh()')
    
    
def edit_dialog(group_id, path_id):
    utils.ensure_addon_data()
    
    dialog = xbmcgui.Dialog()
    group_def = get_group_by_id(group_id)
    path_def = get_path_by_id(path_id, group_id)
    
    options = []
    
    for key in sorted(path_def.keys()):
        if key == 'art':
            art = path_def['art']
            arts = ['[COLOR {}]{}[/COLOR]'.format('firebrick' if art[i] == '' else 'lawngreen', i.capitalize()) for i in sorted(art.keys())]
            options.append('{}: {}'.format(key, ' / '.join(arts)))
        elif key == 'info':
            options.append('{}: {}'.format(key, ', '.join(sorted(path_def[key].keys()))))
        else:
            options.append('{}: {}'.format(key, path_def[key]))
        
    idx = dialog.select(_addon.getLocalizedString(32048), options)
    if idx < 0:
        return
    
    key = options[idx].split(':')[0]
    edit_path(group_id, path_id, key)
        
        
def edit_path(group_id, path_id, target):
    utils.ensure_addon_data()
    
    updated = False
    dialog = xbmcgui.Dialog()
    group_def = get_group_by_id(group_id)
    path_def = get_path_by_id(path_id, group_id)
    
    if target in ['art', 'info']:
        names = []
        options = []
        _def = path_def[target]
        
        for key in sorted(_def.keys()):
            item = xbmcgui.ListItem('{}: {}'.format(key, _def[key]))
            if target == 'art':
                item.setArt({'icon': _def[key]})
            names.append(key)
            options.append(item)
            
        if target == 'art':
            idx = dialog.select(_addon.getLocalizedString(32046), options, useDetails=True)
        elif target == 'info':
            idx = dialog.select(_addon.getLocalizedString(32047), options)
            
        if idx < 0:
            return
        name = names[idx]
        
        if target == 'art':
            value = dialog.browse(2, _addon.getLocalizedString(32049).format(name.capitalize()),
                                 'files', mask='.jpg|.png', useThumbs=True,
                                 defaultt=_def[name])
        elif target == 'info':
            value = dialog.input(heading=name.capitalize(),
                                 defaultt=_def[name])
        _def[name] = value
        
        updated = True
    else:
        value = dialog.input(heading=target.capitalize(),
                             defaultt=path_def[target])
        path_def[target] = value
        updated = True
        
    if updated:
        write_path(group_def, path_def, update=path_id)
        xbmc.executebuiltin('Container.Refresh()')
    
    
def rename_group(group_id):
    dialog = xbmcgui.Dialog()
    group_def = get_group_by_id(group_id)
    
    old_name = group_def['name']
    new_name = dialog.input(heading=_addon.getLocalizedString(32050).format(old_name),
                            defaultt=old_name)
    
    if new_name:
        group_def['name'] = new_name
        write_path(group_def)
        xbmc.executebuiltin('Container.Refresh()')
            
            
def get_group_by_id(group_id):
    filename = '{}.group'.format(group_id)
    path = os.path.join(_addon_path, filename)
    
    if os.path.exists(path):
        with open(path, 'r') as f:
            group_def = json.loads(f.read())
        
        return group_def
        
    return None

# def get_path_by_name(group, path):
    # for defined in find_defined_paths(group):
        # if defined.get('label', '') == path:
            # return defined
            
            
def get_path_by_id(path_id, group_id=None):
    for defined in find_defined_paths(group_id):
        if defined.get('id', '') == path_id:
            return defined
    
    
def find_defined_groups(_type=''):
    groups = []
    
    for filename in [x for x in os.listdir(_addon_path) if x.endswith('.group')]:
        path = os.path.join(_addon_path, filename)
        
        with open(path, 'r') as f:
            group_json = json.loads(f.read())
        
        if _type:
            if group_json['type'] == _type:
                groups.append(group_json)
        else:
            groups.append(group_json)

    return groups
    
    
def find_defined_paths(group_id=None):
    paths = []
    if group_id:
        filename = '{}.group'.format(group_id)
        path = os.path.join(_addon_path, filename)
        
        if os.path.exists(path):
            with open(path, 'r') as f:
                group_json = json.loads(f.read())
            
            return group_json['paths']
    else:
        for group in find_defined_groups():
            paths.append(find_defined_paths(group_id=group.get['id']))
    
    return paths
    

def add_group(target):
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading=_addon.getLocalizedString(32037))
    group_id = ''
    
    if group_name:
        group_id = utils.get_valid_filename('{}-{}'.format(group_name, time.time()).lower())
        filename = os.path.join(_addon_path, '{}.group'.format(group_id))
        group_def = {'name': group_name,
                     'type': target,
                     'paths': [],
                     'id': group_id}
    
        with open(filename, 'w+') as f:
            f.write(json.dumps(group_def, indent=4))
            
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32038))
    
    return group_id
        

def remove_group(group_id, over=False):
    utils.ensure_addon_data()
    
    group_def = get_group_by_id(group_id)
    group_name = group_def['name']
    
    dialog = xbmcgui.Dialog()
    if not over:
        choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32039))
    
    if over or choice:
        filename = '{}.group'.format(group_id)
        filepath = os.path.join(_addon_path, filename)
        try:
            os.remove(filepath)
        except Exception as e:
            utils.log('{}'.format(e), level=xbmc.LOGERROR)
            
        dialog.notification('AutoWidget', _addon.getLocalizedString(32045).format(group_name))
        
        xbmc.executebuiltin('Container.Update(plugin://plugin.program.autowidget/)')
    else:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32040))


def add_as(path, is_folder):
    types = [_addon.getLocalizedString(32051), _addon.getLocalizedString(32052),
             _addon.getLocalizedString(32053)]
    
    if is_folder:
        types = types[:2]
    else:
        if path.startswith('addons://user'):
            pass
        else:
            types = [types[0]]

    options = []
    for type in types:
        li = xbmcgui.ListItem(type)
        
        icon = ''
        if type == _addon.getLocalizedString(32051):
            icon = folder_shortcut
        elif type == _addon.getLocalizedString(32052):
            icon = folder_sync
        elif type == _addon.getLocalizedString(32053):
            icon = folder_settings
            
        li.setArt(icon)
        options.append(li)
    
    dialog = xbmcgui.Dialog()
    idx = dialog.select('Add as', options, useDetails=True)
    if idx < 0:
        return ''
    
    return types[idx].lower()


def group_dialog(_type, group_id=None):
    _type = 'shortcut' if _type == 'settings' else _type
    groups = find_defined_groups(_type)
    names = [group['name'] for group in groups]
    ids = [group['id'] for group in groups]
    
    index = -1
    options = []
    offset = 1
    
    if _type == 'widget':
        new_widget = xbmcgui.ListItem(_addon.getLocalizedString(32015))
        new_widget.setArt(folder_add)
        options.append(new_widget)
    else:
        new_shortcut = xbmcgui.ListItem(_addon.getLocalizedString(32017))
        new_shortcut.setArt(share)
        options.append(new_shortcut)
        
    if group_id:
        index = ids.index(group_id) + 1
    
    for group in groups:
        item = xbmcgui.ListItem(group['name'])
        item.setArt(folder_sync if group['type'] == 'widget' else folder_shortcut)
        options.append(item)
    
    dialog = xbmcgui.Dialog()
    choice = dialog.select(_addon.getLocalizedString(32054), options, preselect=index,
                           useDetails=True)
    
    if choice < 0:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32034))
    elif (choice, _type) == (0, 'widget'):
        return group_dialog(_type, add_group('widget'))
    elif choice == 0:
        return group_dialog(_type, add_group('shortcut'))
    else:
        return groups[choice - offset]
