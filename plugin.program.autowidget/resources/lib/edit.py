import xbmc
import xbmcaddon
import xbmcgui

import os
import re

from resources.lib import manage
from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_home = xbmc.translatePath('special://home/')

advanced = _addon.getSettingBool('context.advanced')
warning_shown = _addon.getSettingBool('context.warning')

types = ['banner', 'clearart', 'clearlogo', 'fanart', 'icon', 'landscape',
         'poster', 'thumb']
warn = ['content', 'id', 'is_folder', 'target', 'window', 'version', 'type']
exclude = ['paths']


def _update_container(_type):
    xbmc.executebuiltin('Container.Refresh()')
    if _type == 'shortcut':
        xbmc.executebuiltin('UpdateLibrary(video)')


def shift_path(group_id, path_id, target):
    group_def = manage.get_group_by_id(group_id)
    
    paths = group_def['paths']
    for idx, path_def in enumerate(paths):
        if path_def['id'] == path_id:
            if target == 'up' and idx > 0:
                temp = paths[idx - 1]
                paths[idx - 1] = path_def
                paths[idx] = temp
            elif target == 'down' and idx < len(paths) - 1: 
                temp = paths[idx + 1]
                paths[idx + 1] = path_def
                paths[idx] = temp
            break

    group_def['paths'] = paths
    manage.write_path(group_def)
    _update_container(group_def['type'])
        
        
def _remove_group(group_id, over=False):
    dialog = xbmcgui.Dialog()
    group_def = manage.get_group_by_id(group_id)
    group_name = group_def['label']
    
    if not over:
        choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32039))
    
    if over or choice:
        file = os.path.join(_addon_path, '{}.group'.format(group_id))
        utils.remove_file(file)
            
        dialog.notification('AutoWidget', _addon.getLocalizedString(32045)
                                                .format(group_name))
        
        
def _remove_path(path_id, group_id):
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32035))
    
    if choice:
        group_def = manage.get_group_by_id(group_id)
    
        paths = group_def['paths']
        for path_def in paths:
            if path_def['id'] == path_id:
                path_name = path_def['label'].decode('utf-8')
                group_def['paths'].remove(path_def)
                dialog.notification('AutoWidget',
                                    _addon.getLocalizedString(32045)
                                          .format(path_name))
                
        manage.write_path(group_def)
        
        
def _warn():
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32058),
                          yeslabel=_addon.getLocalizedString(32059),
                          nolabel=_addon.getLocalizedString(32060))
    if choice < 1:
        _addon.setSetting('context.advanced', 'false')
        _addon.setSetting('context.warning', 'true')
        advanced = False
        warning = True
    else:
        _addon.setSetting('context.warning', 'true')
        warning = True
        
        
def _get_options(edit_def, use_thumbs=False):
    options = []
    label = 'n/a'
    
    all_keys = sorted([i for i in edit_def.keys() if i not in exclude])
    base_keys = sorted([i for i in all_keys if i not in warn])
    keys = all_keys if advanced else base_keys

    for key in keys:
        disp = '[COLOR goldenrod]{}[/COLOR]'.format(key) if key in warn else key
        _def = edit_def[key]
        
        if isinstance(_def, dict):
            _keys = sorted(_def.keys())
        
            if key == 'art':
                arts = ['[COLOR {}]{}[/COLOR]'
                        .format('firebrick' if not _def[i]
                           else 'lawngreen',
                                i.capitalize())
                        for i in _keys]
                label = ' / '.join(arts)
            elif key == 'info':
                label = ', '.join(_keys)
        elif key in edit_def:
            if key in types:
                item = xbmcgui.ListItem('{}: {}'.format(key, edit_def[key]))
                if use_thumbs:
                    item.setArt({'icon': edit_def[key]})
                options.append(item)
                label = ''
            else:
                label = _def
                if not label:
                    label = 'n/a'
                    
        if label:
            options.append('{}: {}'.format(disp, label))
        
    return options
    
    
def _get_value(edit_def, key):
    dialog = xbmcgui.Dialog()
    
    if isinstance(edit_def.get(key), dict):
        _def = edit_def[key]
        if key == 'art':
            options = _get_options(_def, use_thumbs=True)
            idx = dialog.select(_addon.getLocalizedString(32046), options, useDetails=True)
        else:
            options = _get_options(_def)
            idx = dialog.select(_addon.getLocalizedString(32047), options)
        if idx < 0:
            return
        
        _key = _clean_key(options[idx])
        value = _get_value(_def, _key)
        if value:
            _def[_key] = value
            return _def[_key]
    elif key in types:
        default = edit_def[key] if not edit_def[key].lower().startswith('http') else ''
        value = dialog.browse(2, _addon.getLocalizedString(32049).format(key.capitalize()),
                              shares='files', mask='.jpg|.png', useThumbs=True,
                              defaultt=default)
        if value:
            edit_def[key] = value.replace(_home, 'special://home/')
            return edit_def[key]
    else:
        if key in warn:
            title = _addon.getLocalizedString(32063).format(key.capitalize())
        elif key in edit_def:
            title = key.capitalize()
            
        value = dialog.input(heading=title,
                             defaultt=str(edit_def[key]))
        if value:
            edit_def[key] = value
            return edit_def[key]


def _clean_key(key):
    if isinstance(key, xbmcgui.ListItem):
        key = key.getLabel()
    key = key.split(':')[0]
    color = re.match('\[COLOR \w+\](\w+)\[\/COLOR\]', key)
    if color:
        key = color.group(1)
    
    return key

        
def edit_dialog(group_id, path_id=''):
    dialog = xbmcgui.Dialog()
    updated = False
    if advanced and not warning_shown:
        _warn()
    
    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        return
    if path_id:
        path_def = manage.get_path_by_id(path_id, group_id)
        if not path_def:
            return
        
    edit_def = path_def if path_id else group_def
    options = _get_options(edit_def)
    
    remove_label = _addon.getLocalizedString(32025) if path_id else _addon.getLocalizedString(32023)
    options.append('[COLOR firebrick]{}[/COLOR]'.format(remove_label))
    
    idx = dialog.select(_addon.getLocalizedString(32048), options)
    if idx < 0:
        return
    elif idx == len(options) - 1:
        if path_id:
            _remove_path(path_id, group_id)
            _update_container(group_def['type'])
        else:
            _remove_group(group_id)
            _update_container(group_def['type'])
        return
    else:
        key = _clean_key(options[idx])
    
    updated = _get_value(edit_def, key)
    utils.log(updated, xbmc.LOGNOTICE)

    if updated:
        if path_id:
            manage.write_path(group_def, path_def=path_def, update=path_id)
        else:
            manage.write_path(group_def)
            
        _update_container(group_def['type'])
