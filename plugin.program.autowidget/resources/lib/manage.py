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

from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_version = _addon.getAddonInfo('version')
_home = xbmc.translatePath('special://home/')
if xbmc.getCondVisibility('System.HasAddon(script.skinshortcuts)'):
    _shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    _shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))
else:
    _shortcuts_path = ''

def write_path(group_def, path_def=None, update=''):
    filename = os.path.join(_addon_path, '{}.group'.format(group_def['id']))

    if path_def:
        if update:
            for path in group_def['paths']:
                if path['id'] == update:
                    group_def['paths'][group_def['paths'].index(path)] = path_def
        else:
            group_def['paths'].append(path_def)

    utils.write_json(filename, group_def)


def get_group_by_id(group_id):
    if not group_id:
        return
    
    filename = '{}.group'.format(group_id)
    path = os.path.join(_addon_path, filename)
    
    try:
        group_def = utils.read_json(path)
    except ValueError:
        utils.log('Unable to parse: {}'.format(path))
    
    return group_def


def get_path_by_id(path_id, group_id=None):
    if not path_id:
        return
        
    for defined in find_defined_paths(group_id):
        if defined.get('id', '') == path_id:
            return defined
            
            
def get_widget_by_id(widget_id, group_id=None):
    if not widget_id:
        return
        
    for defined in find_defined_widgets(group_id):
        if defined.get('id', '') == widget_id:
            return defined
    
    
def find_defined_groups(_type=''):
    groups = []
    
    for filename in [x for x in os.listdir(_addon_path) if x.endswith('.group')]:
        path = os.path.join(_addon_path, filename)
        
        try:
            group_def = utils.read_json(path)
        except ValueError:
            utils.log('Unable to parse: {}'.format(path))
        
        if group_def:
            if _type:
                if group_def['type'] == _type:
                    groups.append(group_def)
            else:
                groups.append(group_def)

    return groups
    
    
def find_defined_paths(group_id=None):
    paths = []
    if group_id:
        filename = '{}.group'.format(group_id)
        path = os.path.join(_addon_path, filename)
        
        try:
            group_def = utils.read_json(path)
        except ValueError:
            utils.log('Unable to parse: {}'.format(path))
        
        if group_def:
            return group_def.get('paths', [])
    else:
        for group in find_defined_groups():
            paths.append(find_defined_paths(group_id=group.get('id')))
    
    return paths
    

def find_defined_widgets(group_id=None):
    addon_files = os.listdir(_addon_path)
    widgets = []
    
    widget_files = [x for x in addon_files if x.endswith('.widget')]
    for widget_file in widget_files:
        widget_def = utils.read_json(os.path.join(_addon_path, widget_file))
    
        if widget_def:
            if not group_id:
                widgets.append(widget_def)
            elif group_id == widget_def['group']:
                widgets.append(widget_def)
    
    return widgets
    
    
def clean():
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', utils.getString(32067))

    if not choice:
        return

    to_remove = []
    
    widgets = find_defined_widgets()
    groups = find_defined_groups()
    if _shortcuts_path:
        shortcuts = os.listdir(_shortcuts_path)
        
    for widget_def in widgets:
        remove = True
        widget_id = widget_def['id']
        widget_group = widget_def['group']
        
        for group_def in groups:
            group_id = group_def['id']
            
            if group_id == widget_group:
                remove = False
        
        if shortcuts:
            for shortcut in shortcuts:
                shortcut_file = os.path.join(_shortcuts_path, shortcut)
                shortcut_def = utils.read_file(shortcut_file)
                
                if shortcut_def:
                    if widget_id in shortcut_def:
                        remove = False

        if remove:
            to_remove.append(widget_id)
            
    for remove in to_remove:
        filename = '{}.widget'.format(remove)
        utils.remove_file(os.path.join(_addon_path, filename))
