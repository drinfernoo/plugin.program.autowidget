import xbmc
import xbmcaddon
import xbmcgui

import json
import re

from resources.lib import manage
from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))

advanced = _addon.getSettingBool('context.advanced')
warning_shown = _addon.getSettingBool('context.warning')


def shift_path(group_id, path_id, target):
    group = manage.get_group_by_id(group_id)
    
    filename = os.path.join(_addon_path, '{}.group'.format(group['id']))
    with open(filename, 'r') as f:
        group_def = json.loads(f.read())

    paths = group_def['paths']
    for idx, path_def in enumerate(paths):
        if path_def['id'] == path_id:
            if target == 'up' and idx > 0:
                temp = paths[idx - 1]
                paths[idx - 1] = path_json
                paths[idx] = temp
            elif target == 'down' and idx < len(paths) - 1: 
                temp = paths[idx + 1]
                paths[idx + 1] = path_json
                paths[idx] = temp
            
            break

    group_def['paths'] = paths

    with open(filename, 'w') as f:
        f.write(json.dumps(group_def, indent=4))
        
    xbmc.executebuiltin('Container.Refresh()')
    

def _rename_group(group_id):
    dialog = xbmcgui.Dialog()
    group_def = get_group_by_id(group_id)
    
    old_name = group_def['label']
    new_name = dialog.input(heading=_addon.getLocalizedString(32050).format(old_name),
                            defaultt=old_name)
    
    if new_name:
        group_def['label'] = new_name
        manage.write_path(group_def)
        xbmc.executebuiltin('Container.Refresh()')
        
def _remove_group(group_id, over=False):
    group_def = get_group_by_id(group_id)
    group_name = group_def['label']
    
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
        
        
def _remove_path(path_id, group_id):
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32035))
    
    if choice:
        filename = os.path.join(_addon_path, '{}.group'.format(group_id))
        with open(filename, 'r') as f:
            group_def = json.loads(f.read())
    
        paths = group_def['paths']
        for path_def in paths:
            if path_def['id'] == path_id:
                path_name = path_def['label']
                group_def['paths'].remove(path_def)
                dialog.notification('AutoWidget', _addon.getLocalizedString(32045).format(path_name))
                
        with open(filename, 'w') as f:
            f.write(json.dumps(group_def, indent=4))
            
        xbmc.executebuiltin('Container.Refresh()')
    else:
        dialog.notification('AutoWidget', _addon.getLocalizedString(32036))
        
        
def edit_dialog(group_id, path_id=''):
    updated = False
    dialog = xbmcgui.Dialog()
    
    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        return
        
    if path_id:
        path_def = manage.get_path_by_id(path_id, group_id)
    
    options = []
    if advanced and not warning_shown:
        choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32058),
                              yeslabel=_addon.getLocalizedString(32059),
                              nolabel=_addon.getLocalizedString(32060))
        if choice < 1:
            _addon.setSetting('context.advanced', 'false')
            _addon.setSetting('context.warning', 'true')
        elif choice == 1:
            _addon.setSetting('context.warning', 'true')
    
    warn = ['content', 'id', 'is_folder', 'target', 'window', 'version', 'type']
    all_keys = sorted(group_def.keys())
    base_keys = [i for i in all_keys if i not in warn]
    
    keys = all_keys if advanced else base_keys
    edit_def = path_def if path_id else group_def
    for key in keys:
        if key == 'paths':
            continue
    
        if key in warn:
            label = '[COLOR goldenrod]{}[/COLOR]'.format(key)
        else:
            label = key
            
        if key == 'art':
            art = edit_def['art']
            arts = ['[COLOR {}]{}[/COLOR]'.format('firebrick' if not art[i] else 'lawngreen', i.capitalize()) for i in sorted(art.keys())]
            options.append('{}: {}'.format(label, ' / '.join(arts)))
        elif key == 'info':
            options.append('{}: {}'.format(label, ', '.join(sorted(edit_def[key].keys()))))
        elif key in edit_def:
            options.append('{}: {}'.format(label, edit_def[key]))
    
    remove_label = _addon.getLocalizedString(32025) if path_id else _addon.getLocalizedString(32023)
    options.append('[COLOR firebrick]{}[/COLOR]'.format(remove_label))
    idx = dialog.select(_addon.getLocalizedString(32048), options)
    if idx < 0:
        return
    elif idx == len(options) - 1:
        if path_id:
            _remove_path(path_id, group_id)
        else:
            _remove_group(group_id)
        return
        
    target = options[idx].split(':')[0]
    color = re.match('\[COLOR \w+\](\w+)\[\/COLOR\]', target)
    if color:
        target = color.group(1)
    
    if target in ['art', 'info']:
        names = []
        options = []
        _def = edit_def[target]
        
        for _key in sorted(_def.keys()):
            item = xbmcgui.ListItem('{}: {}'.format(_key, _def[_key]))
            if target == 'art':
                item.setArt({'icon': _def[_key]})
            names.append(_key)
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
                                 
        if value:
            _def[name] = value
            updated = True
    elif target == 'label' and not path_id:
        _rename_group(group_id)
    elif target in warn:
        value = dialog.input(heading=_addon.getLocalizedString(32063).format(target.capitalize()),
                             defaultt=edit_def[target])
        if value:
            edit_def[target] = value
            updated = True
    else:
        value = dialog.input(heading=target.capitalize(),
                             defaultt=edit_def[target])
        if value:
            edit_def[target] = value
            updated = True
        
    if updated:
        if path_id:
            manage.write_path(group_def, path_def=path_def, update=path_id)
        else:
            manage.write_path(group_def)
            
        xbmc.executebuiltin('Container.Refresh()')
