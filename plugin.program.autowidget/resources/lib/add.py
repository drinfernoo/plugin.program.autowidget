import xbmc
import xbmcaddon
import xbmcgui

import os

try:
    from urllib.parse import parse_qsl
    from urllib.parse import unquote
except ImportError:
    from urlparse import parse_qsl
    from urllib import unquote

from resources.lib import manage
from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_version = _addon.getAddonInfo('version')

shortcut_types = [utils.get_string(32051), utils.get_string(32052),
                  utils.get_string(32082), utils.get_string(32083),
                  utils.get_string(32053)]

folder_shortcut = utils.get_art('folder-shortcut')
folder_sync = utils.get_art('folder-sync')
folder_settings = utils.get_art('folder-settings')
folder_clone = utils.get_art('folder-clone')
folder_explode = utils.get_art('folder-explode')


def add(labels):
    _type = _add_as(labels['file'])
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
        labels = {'label': utils.get_infolabel('ListItem.Label'),
                  'content': xbmc.getInfoLabel('Container.Content')}
        
        path_def = {'file': utils.get_infolabel('ListItem.FolderPath'),
                    'filetype': 'directory' if xbmc.getCondVisibility('Container.ListItem.IsFolder') else 'file',
                    'art': {}}  # would be fun to set some "placeholder" art here

        for i in utils.info_types:
            info = utils.get_infolabel('ListItem.{}'.format(i.capitalize()))
            if info and not info.startswith('ListItem'):
                path_def[i] = info

        for i in utils.art_types:
            art = utils.get_infolabel('ListItem.Art({})'.format(i))
            if art:
                path_def['art'][i] = utils.clean_artwork_url(art)
        for i in ['icon', 'thumb']:
            art = utils.clean_artwork_url(utils.get_infolabel('ListItem.{}'.format(i)))
            if art:
                path_def['art'][i] = art
    elif source == 'json' and path_def and target:
        labels = {'label': path_def['label'],
                  'content': '',
                  'target': target}

    labels['file'] = path_def if path_def else {key: path_def[key] for key in path_def if path_def[key]}
    path = labels['file']['file']

    if path != 'addons://user/':
        path = path.replace('addons://user/', 'plugin://')
    if 'plugin://plugin.video.themoviedb.helper' in path and not '&widget=True' in path:
        path += '&widget=True'            
    labels['file']['file'] = path

    for _key in utils.windows:
        if any(i in path for i in utils.windows[_key]):
            labels['window'] = _key

    return labels


def _add_as(path_def):
    art = [folder_shortcut, folder_sync, folder_clone, folder_explode, folder_settings]
    
    path = path_def['file']
    types = shortcut_types[:]
    if path_def['filetype'] == 'directory':
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
    idx = dialog.select(utils.get_string(32084), options, useDetails=True)
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
    ids = [group['id'] for group in groups]
    
    index = -1
    options = []
    offset = 1
    
    if _type == 'widget':
        new_widget = xbmcgui.ListItem(utils.get_string(32015))
        new_widget.setArt(folder_sync)
        options.append(new_widget)
    else:
        new_shortcut = xbmcgui.ListItem(utils.get_string(32017))
        new_shortcut.setArt(folder_shortcut)
        options.append(new_shortcut)
        
    if group_id:
        index = ids.index(group_id) + 1
    
    for group in groups:
        item = xbmcgui.ListItem(group['label'])
        item.setArt(folder_sync if group['type'] == 'widget' else folder_shortcut)
        options.append(item)
    
    dialog = xbmcgui.Dialog()
    choice = dialog.select(utils.get_string(32054), options, preselect=index,
                           useDetails=True)
    
    if choice < 0:
        dialog.notification('AutoWidget', utils.get_string(32034))
    elif (choice, _type) == (0, 'widget'):
        return _group_dialog(_type, add_group('widget'))
    elif choice == 0:
        return _group_dialog(_type, add_group('shortcut'))
    else:
        return groups[choice - offset]


def add_group(target, group_name=''):
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading=utils.get_string(32037),
                              defaultt=group_name)
    group_id = ''
    
    if group_name:
        group_id = utils.get_unique_id(group_name)
        filename = os.path.join(_addon_path, '{}.group'.format(group_id))
        group_def = {'label': group_name,
                     'type': target,
                     'paths': [],
                     'id': group_id,
                     'art': folder_sync if target == 'widget' else folder_shortcut,
                     'version': _addon_version}
    
        utils.write_json(filename, group_def)
        utils.update_container()
    else:
        dialog.notification('AutoWidget', utils.get_string(32038))
    
    return group_id
    
    
def _add_path(group_def, labels, over=False):
    if not over:
        if group_def['type'] == 'shortcut':
            heading = utils.get_string(32043)
        elif group_def['type'] == 'widget':
            heading = utils.get_string(32044)
        
        labels['label'] = xbmcgui.Dialog().input(heading=heading,
                                                 defaultt=labels['label'])
                                                 
    labels['id'] = utils.get_unique_id(labels['label'])
    labels['version'] = _addon_version
    
    manage.write_path(group_def, path_def=labels)
    
    
def _copy_path(path_def):
    dialog = xbmcgui.Dialog()
    
    group_id = add_group(path_def['target'], path_def['label'])
    if not group_id:
        return
        
    group_def = manage.get_group_by_id(group_id)
    files = utils.get_files_list(path_def['file']['file'])
    if not files:
        return
    
    for file in files:
        if file['type'] in ['movie', 'episode', 'musicvideo', 'song']:
            continue
            
        labels = build_labels('json', file, path_def['target'])
        _add_path(group_def, labels, over=True)
    dialog.notification('AutoWidget', '{} paths added to {}'
                                      .format(len(files), group_def['label']))
