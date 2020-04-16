import xbmc
import xbmcaddon
import xbmcgui

import json
import os
import re

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

from resources.lib import manage
from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_version = _addon.getAddonInfo('version')
_home = xbmc.translatePath('special://home/')

shortcut_types = [_addon.getLocalizedString(32051), _addon.getLocalizedString(32052),
          'Clone as Shortcut Group', 'Explode as Widget Group',
          'Settings Shortcut']

folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
folder_settings = utils.get_art('folder-settings.png')
folder_clone = utils.get_art('folder-clone.png')
folder_explode = utils.get_art('folder-explode.png')


def add(labels):
    _type = _add_as(labels['path'], labels['is_folder'])
    if not _type:
        return
    
    if _type not in ['clone', 'explode']:
        labels['target'] = _type
        group_def = _group_dialog(_type)
        if group_def:
            _add_path(group_def, labels)
    elif _type == 'clone':
        labels['target'] = 'shortcut'
        _copy_path(labels)
    elif _type == 'explode':
        labels['target'] = 'widget'
        _copy_path(labels)
        
    utils.update_container(_type)
            
            
def build_labels(source, path_def=None, target=''):
    if source == 'context' and not path_def and not target:
        labels = {'label': xbmc.getInfoLabel('ListItem.Label'),
                  'is_folder': xbmc.getCondVisibility('Container.ListItem.IsFolder'),
                  'content': xbmc.getInfoLabel('Container.Content')}
        
        path = xbmc.getInfoLabel('ListItem.FolderPath')
        
        labels['info'] = {}
        for i in utils.info_types:
            info = xbmc.getInfoLabel('ListItem.{}'.format(i.capitalize()))
            if info and not info.startswith('ListItem'):
                labels['info'][i] = info
                                 
        labels['art'] = {}
        for i in utils.art_types:
            art = xbmc.getInfoLabel('ListItem.Art({})'.format(i.capitalize()))
            if art:
                labels['art'][i] = art
        for i in ['icon', 'thumb']:
            art = xbmc.getInfoLabel('ListItem.{}'.format(i.capitalize()))
            if art:
                labels['art'][i] = art
    elif source == 'json' and path_def and target:
        labels = {'label': path_def['label'],
                  'is_folder': path_def['filetype'] == 'directory',
                  'content': '',
                  'target': target}
        
        path = path_def['file']
        
        labels['info'] = {}
        for i in [i for i in utils.info_types if i not in utils.art_types]:
            if i in path_def and i not in ['art', 'title', 'file']:
                labels['info'][i] = path_def[i]
        
        labels['art'] = {}
        for i in utils.art_types:
            if i in path_def['art']:
                labels['art'][i] = path_def['art'][i]
    
    if path != 'addons://user/':
        path = path.replace('addons://user/', 'plugin://')
    labels['path'] = path
    
    for _key in utils.windows:
            if any(i in path for i in utils.windows[_key]):
                labels['window'] = _key
                
    for label in labels['art']:
        labels['art'][label] = labels['art'][label].replace(_home, 'special://home/')
        
    return labels
            
            
def _add_as(path, is_folder):
    art = [folder_shortcut, folder_sync, folder_clone, folder_explode, folder_settings]
    
    types = shortcut_types[:]
    if is_folder:
        types = shortcut_types[:4]
    else:
        if any(i in path for i in ['addons://user', 'plugin://']) and not parse_qsl(path):
            pass
        else:
            types = [shortcut_types[0]]

    options = []
    for idx, type in enumerate(types):
        li = xbmcgui.ListItem(type)
        
        li.setArt(art[idx])
        options.append(li)
    
    dialog = xbmcgui.Dialog()
    idx = dialog.select('Add as...', options, useDetails=True)
    if idx < 0:
        return
    
    chosen = types[idx]
    if chosen in [shortcut_types[0], shortcut_types[4]]:
        return 'shortcut'
    elif chosen == shortcut_types[1]:
        return 'widget'
    elif chosen == shortcut_types[2]:
        return 'clone'
    elif chosen == shortcut_types[3]:
        return 'explode'
            
            
def _group_dialog(_type, group_id=None):
    _type = 'shortcut' if _type == 'settings' else _type
    groups = manage.find_defined_groups(_type)
    names = [group['label'] for group in groups]
    ids = [group['id'] for group in groups]
    
    index = -1
    options = []
    offset = 1
    
    if _type == 'widget':
        new_widget = xbmcgui.ListItem(_addon.getLocalizedString(32015))
        new_widget.setArt(folder_sync)
        options.append(new_widget)
    else:
        new_shortcut = xbmcgui.ListItem(_addon.getLocalizedString(32017))
        new_shortcut.setArt(folder_shortcut)
        options.append(new_shortcut)
        
    if group_id:
        index = ids.index(group_id) + 1
    
    for group in groups:
        item = xbmcgui.ListItem(group['label'])
        item.setArt(folder_sync if group['type'] == 'widget' else folder_shortcut)
        options.append(item)
    
    dialog = xbmcgui.Dialog()
    choice = dialog.select(_addon.getLocalizedString(32054), options, preselect=index,
                           useDetails=True)
    
    if choice < 0:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32034))
    elif (choice, _type) == (0, 'widget'):
        return _group_dialog(_type, add_group('widget'))
    elif choice == 0:
        return _group_dialog(_type, add_group('shortcut'))
    else:
        return groups[choice - offset]


def add_group(target):
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading=_addon.getLocalizedString(32037))
    group_id = ''
    
    if group_name:
        group_id = utils.get_unique_id(group_name)
        filename = os.path.join(_addon_path, '{}.group'.format(group_id))
        group_def = {'label': group_name,
                     'type': target,
                     'paths': [],
                     'id': group_id,
                     'info': {},
                     'art': folder_sync if target == 'widget' else folder_shortcut,
                     'version': _addon_version}
    
        utils.write_json(filename, group_def)
            
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32038))
    
    return group_id
    
    
def _add_path(group_def, labels, over=False):
    if not over:
        if group_def['type'] == 'shortcut':
            heading = _addon.getLocalizedString(32043)
        elif group_def['type'] == 'widget':
            heading = _addon.getLocalizedString(32044)
        
        labels['label'] = xbmcgui.Dialog().input(heading=heading,
                                                 defaultt=labels['label'])
                                                 
    labels['id'] = utils.get_unique_id(labels['label'])
    labels['version'] = _addon_version
    
    manage.write_path(group_def, path_def=labels)
    
    
def _copy_path(path_def):
    params = {'jsonrpc': '2.0', 'method': 'Files.GetDirectory',
              'params': {'directory': path_def['path'],
                         'properties': utils.info_types},
              'id': 1}
    group_id = add_group(path_def['target'])
    if not group_id:
        return
        
    group_def = manage.get_group_by_id(group_id)
    files = xbmc.executeJSONRPC(json.dumps(params))
    if 'error' not in files:
        files = json.loads(files)['result']['files']
        for file in files:
            if file['type'] in ['movie', 'episode', 'musicvideo', 'song']:
                continue
            
            labels = build_labels('json', file, path_def['target'])
            _add_path(group_def, labels, over=True)
