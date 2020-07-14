import xbmc
import xbmcgui

import os

from resources.lib import manage
from resources.lib.common import utils

advanced = utils.get_setting_bool('context.advanced')
warning_shown = utils.get_setting_bool('context.warning')

filter = {'include': ['label', 'file', 'art'],
          'exclude': ['paths']}


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

    option_keys = (all_keys if advanced else base_keys) + utils.art_types
    for key in option_keys:
        if key in edit_def:
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
        value = dialog.input('New Value for {}:'.format(key))
        if value:
            edit_def[key] = value

        return value


def _clean_key(key):
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