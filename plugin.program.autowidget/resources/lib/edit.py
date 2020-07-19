import xbmc
import xbmcgui

import os
import re

from resources.lib import manage
from resources.lib.common import utils

advanced = utils.get_setting_bool('context.advanced')
warning_shown = utils.get_setting_bool('context.warning')

filter = {'include': ['label', 'file', 'art'] + utils.art_types,
          'exclude': ['paths']}
color_tag = '\[COLOR \w+\](\w+)\[\/COLOR\]'


def shift_path(group_id, path_id, target):
    group_def = manage.get_group_by_id(group_id)
    paths = group_def['paths']
    for idx, path_def in enumerate(paths):
        if path_def['id'] == path_id:
            if target == 'up' and idx >= 0:
                if idx > 0:
                    temp = paths[idx - 1]
                    paths[idx - 1] = path_def
                    paths[idx] = temp
                else:
                    paths.append(paths.pop(idx))
            elif target == 'down' and idx <= len(paths) - 1: 
                if idx < len(paths) - 1:
                    temp = paths[idx + 1]
                    paths[idx + 1] = path_def
                    paths[idx] = temp
                else:
                    paths.insert(0, paths.pop())
            break
    group_def['paths'] = paths
    manage.write_path(group_def)
    utils.update_container(group_def['type'])


def _remove_group(group_id, over=False):
    dialog = xbmcgui.Dialog()
    group_def = manage.get_group_by_id(group_id)
    group_name = group_def['label']
    if not over:
        choice = dialog.yesno('AutoWidget', utils.get_string(32039))

    if over or choice:
        file = os.path.join(utils._addon_path, '{}.group'.format(group_id))
        utils.remove_file(file)
        dialog.notification('AutoWidget', utils.get_string(32045)
                                               .format(group_name))


def _remove_path(path_id, group_id, over=False):
    dialog = xbmcgui.Dialog()
    if not over:
        choice = dialog.yesno('AutoWidget', utils.get_string(32035))

    if over or choice:
        group_def = manage.get_group_by_id(group_id)
        paths = group_def['paths']
        for path_def in paths:
            if path_def['id'] == path_id:
                path_name = path_def['label']
                group_def['paths'].remove(path_def)
                dialog.notification('AutoWidget',
                                    utils.get_string(32045)
                                         .format(path_name))
        manage.write_path(group_def)


def _remove_widget(widget_id, over=False):
    dialog = xbmcgui.Dialog()
    if not over:
        choice = dialog.yesno('AutoWidget', utils.get_string(32039))

    if over or choice:
        file = os.path.join(utils._addon_path, '{}.widget'.format(widget_id))
        utils.remove_file(file)
        dialog.notification('AutoWidget', utils.get_string(32045)
                                               .format(widget_id))


def _warn():
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', utils.get_string(32058),
                          yeslabel=utils.get_string(32059),
                          nolabel=utils.get_string(32060))
    if choice < 1:
        utils.set_setting('context.advanced', 'false')
        utils.set_setting('context.warning', 'true')
        advanced = False
        warning = True
    else:
        utils.set_setting('context.warning', 'true')
        warning = True


def _show_options(group_def, path_def=None):
    dialog = xbmcgui.Dialog()
    edit_def = path_def if path_def else group_def
    options = _get_options(edit_def)
    remove_label = utils.get_string(32025) if path_def else utils.get_string(32023)
    options.append('[COLOR firebrick]{}[/COLOR]'.format(remove_label))

    idx = dialog.select(utils.get_string(32048), options)
    if idx < 0:
        return
    elif idx == len(options) - 1:
        if path_def:
            _remove_path(path_def['id'], group_def['id'])
            utils.update_container(group_def['type'])
        else:
            _remove_group(group_def['id'])
            utils.update_container(group_def['type'])
        return
    else:
        key = _clean_key(options[idx])

    return _get_value(edit_def, key)


def _get_options(edit_def, useThumbs=False):
    options = []
    all_keys = sorted(edit_def.keys())
    base_keys = [i for i in all_keys if i in filter['include'] and i not in filter['exclude']]

    option_keys = (all_keys if advanced else base_keys)
    for key in option_keys:
        if key in edit_def:
            if key in utils.art_types:
                li = xbmcgui.ListItem('{}: {}'.format(key, edit_def[key]))
                li.setArt({'icon': edit_def[key]})
                options.append(li)
            else:
                formatted_key = '[COLOR goldenrod]{}[/COLOR]'.format(key) if key not in filter['include'] else key
                if isinstance(edit_def[key], dict):
                    label = ', '.join(edit_def[key].keys())
                    options.append('{}: {}'.format(formatted_key, label))
                else:
                    options.append('{}: {}'.format(formatted_key, edit_def[key]))
    return options


def _get_value(edit_def, key):
    dialog = xbmcgui.Dialog()
    
    if isinstance(edit_def[key], dict):
        is_art = key == 'art'
        if is_art:
            label = 'Select Artwork to Edit:'
        else:
            label = 'Select {} to Edit:'.format('Key' if key != 'file' else 'InfoLabel')
        options =_get_options(edit_def[key], useThumbs=is_art)
        idx = dialog.select(label, options, useDetails=is_art)
            
        if idx < 0:
            return
        else:
            subkey = _clean_key(options[idx])
            value = _get_value(edit_def[key], _clean_key(options[idx]))
            if value:
                edit_def[key][subkey] = value
                return edit_def[key]
    else:
        if key in utils.art_types:
            value = dialog.browse(2, utils.get_string(32049).format(key.capitalize()), 
                          shares='files', mask='.jpg|.png', useThumbs=True)
        else:
            value = dialog.input('New Value for {}:'.format(key), defaultt=edit_def[key])

        if value:
            edit_def[key] = value
            return value


def _get_widget_options(edit_def): 
    options = [] 
     
    all_keys = sorted([i for i in edit_def.keys() if i not in exclude]) 
    base_keys = sorted([i for i in all_keys if i in widget_safe]) 
    keys = all_keys if advanced else base_keys 
     
    for key in keys: 
        disp = '[COLOR goldenrod]{}[/COLOR]'.format(key) if key not in widget_safe else key 
        _def = edit_def[key] 
        label = _def 
         
        if key == 'action': 
            if label == 'random': 
                label = utils.get_string(32079) 
            elif label == 'next': 
                label = utils.get_string(32080) 
            elif label == 'merged': 
                label = utils.get_string(32088) 
        elif key == 'refresh': 
            hh = int(_def) 
            mm = int((_def * 60)  % 60) 
            if hh and mm: 
                label = '{}h {}m'.format(hh, mm) 
            elif not mm: 
                label = '{}h'.format(hh) 
            elif not hh: 
                label = '{}m'.format(mm) 
             
        if not label: 
            label = 'n/a' 
             
        try: 
            label = label.encode('utf-8') 
        except: 
            pass 
                 
        options.append('{}: {}'.format(disp, label)) 
             
    return options 


def _get_widget_value(edit_def, key): 
    dialog = xbmcgui.Dialog() 
     
    if key not in widget_safe: 
        title = utils.get_string(32063).format(key.capitalize()) 
    elif key in edit_def: 
        title = key.capitalize() 
     
    if key == 'action': 
        actions = [utils.get_string(32079), utils.get_string(32080), utils.get_string(32088)] 
        choice = dialog.select(utils.get_string(32081), actions) 
        if choice < 0: 
            return 
             
        value = actions[choice].split(' ')[0].lower() 
    elif key == 'refresh': 
        durations = [] 
        d = 0.25 
        while d <= 12: 
            hh = int(d) 
            mm = int((d * 60) % 60) 
            if hh and mm: 
                label = '{}h {}m'.format(hh, mm) 
            elif not mm: 
                label = '{}h'.format(hh) 
            elif not hh: 
                label = '{}m'.format(mm) 
             
            durations.append(label) 
            d = d + 0.25 
             
        choice = dialog.select('Refresh Duration', durations) 
         
        if choice < 0: 
            return 
             
        duration = durations[choice].split(' ') 
        if len(duration) > 1: 
            value = float(duration[0][:-1]) + (float(duration[1][:-1]) / 60) 
        else: 
            if 'm' in duration[0]: 
                value = float(duration[0][:-1]) / 60 
            elif 'h' in duration[0]: 
                value = float(duration[0][:-1]) 
    else: 
        default = edit_def.get(key) 
        value = dialog.input(title, defaultt=six.text_type(default)) 
     
    if value: 
        edit_def[key] = value 
        return edit_def[key]


def _clean_key(key):
    if isinstance(key, xbmcgui.ListItem):
        key = key.getLabel()
    split = key.split(': ')[0]
    match = re.match(color_tag, split)
    if match:
        clean = re.sub(color_tag, split, match.group(1))
        return clean
    return key.split(': ')[0]


def edit_dialog(group_id, path_id=None, base_key=None):
    dialog = xbmcgui.Dialog()
    updated = False
    if advanced and not warning_shown:
        _warn()
    
    group_def = manage.get_group_by_id(group_id)
    path_def = manage.get_path_by_id(path_id, group_id)
    if not group_def or path_id and not path_def:
        return
    
    updated = _show_options(group_def, path_def)
    if updated:
        utils.log(updated, xbmc.LOGNOTICE)
        manage.write_path(group_def, path_def=path_def, update=path_id)
        utils.update_container(group_def['type'])

        edit_dialog(group_id, path_id)
        
        
def edit_widget_dialog(widget_id): 
    dialog = xbmcgui.Dialog() 
    updated = False 
    if advanced and not warning_shown: 
        _warn() 
         
    widget_def = manage.get_widget_by_id(widget_id) 
    if not widget_def: 
        return 
     
    options = _get_widget_options(widget_def) 
     
    remove_label = utils.get_string(32025) if widget_id else utils.get_string(32023) 
    options.append('[COLOR firebrick]{}[/COLOR]'.format(remove_label)) 
     
    idx = dialog.select(utils.get_string(32048), options) 
    if idx < 0: 
        return 
    elif idx == len(options) - 1: 
        _remove_widget(widget_id) 
        utils.update_container() 
        return 
    else: 
        key = _clean_key(options[idx]) 
         
    updated = _get_widget_value(widget_def, key) 
    utils.log(updated, xbmc.LOGNOTICE) 
     
    if updated: 
        manage.save_path_details(widget_def, widget_id) 
        utils.update_container() 
    edit_widget_dialog(widget_id)