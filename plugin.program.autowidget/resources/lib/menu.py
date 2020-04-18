import xbmc
import xbmcaddon
import xbmcgui

import random
import time
import uuid

import six

from resources.lib import manage
from resources.lib.common import directory
from resources.lib.common import utils

add = utils.get_art('add.png')
alert = utils.get_art('alert.png')
folder = utils.get_art('folder.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
folder_next = utils.get_art('folder-next.png')
refresh = utils.get_art('refresh.png')
remove = utils.get_art('remove.png')
share = utils.get_art('share.png')
shuffle = utils.get_art('shuffle.png')
sync = utils.get_art('sync.png')
tools = utils.get_art('tools.png')
unpack = utils.get_art('unpack.png')

_addon = xbmcaddon.Addon()

label_warning_shown = utils.getSettingBool('label.warning')


def _warn():
    dialog = xbmcgui.Dialog()
    dialog.ok('AutoWidget', ('The unique identifier in the number in this path'
                             '\'s label is [B]necessary[/B] for AutoWidget to '
                             'refresh it correctly. Don\'t change the label '
                             'given to this widget, or it may be unable to '
                             'update correctly. This wessage '
                             '[COLOR firebrick]will not[/COLOR] be shown '
                             'again.'))
    
    _addon.setSetting('label.warning', 'true')
    label_warning_shown = True


def root_menu():
    directory.add_menu_item(title=32007,
                            params={'mode': 'group'},
                            art=folder,
                            isFolder=True)
    directory.add_menu_item(title='Active Widgets',
                            params={'mode': 'widget'},
                            art=folder,
                            isFolder=True)
    directory.add_menu_item(title=32008,
                            params={'mode': 'tools'},
                            art=tools,
                            isFolder=True)
    return True, 'AutoWidget'
                            
                            
def my_groups_menu():
    groups = manage.find_defined_groups()
    if len(groups) > 0:
        for group in groups:
            _id = uuid.uuid4()
            group_name = group['label']
            group_id = group['id']
            group_type = group['type']
            
            cm = [(utils.getString(32061),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=edit'
                   '&group={})').format(group_id))]
            
            directory.add_menu_item(title=group_name,
                                    params={'mode': 'group',
                                            'group': group_id,
                                            'target': group_type,
                                            'id': six.text_type(_id)},
                                    info=group.get('info'),
                                    art=group.get('art') or (folder_shortcut
                                                             if group_type == 'shortcut'
                                                             else folder_sync),
                                    cm=cm,
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32068,
                                art=alert,
                                isFolder=False)
    return True, utils.getString(32007)
    
    
def group_menu(group_id, target, _id):
    _window = utils.get_active_window()
    
    group = manage.get_group_by_id(group_id)
    if not group:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'.format(group_id),
                  level=xbmc.LOGERROR)
        return False, 'AutoWidget'
    
    group_name = group['label']
    
    paths = manage.find_defined_paths(group_id)
    if len(paths) > 0:
        cm = []
        art = folder_shortcut if target == 'shortcut' else folder_sync
        
        for idx, path in enumerate(paths):
            if _window == 'media':
                cm = _create_context_items(group_id, path['id'], idx, len(paths))
            
            directory.add_menu_item(title=path['label'],
                                    params={'mode': 'path',
                                            'action': 'call',
                                            'group': group_id,
                                            'path': path['id']},
                                    info=path.get('info'),
                                    art=path.get('art') or art,
                                    cm=cm,
                                    isFolder=False)
        if target == 'widget' and _window != 'home':
            directory.add_separator(title=32010, char='/')

            description = utils.getString(32029).format(group_name)
            
            directory.add_menu_item(title='Random Path from {} ({})'.format(group_name, _id),
                                    params={'mode': 'path',
                                            'action': 'random',
                                            'group': group_id,
                                            'id': six.text_type(_id)},
                                    art=folder_sync,
                                    info={'plot': description},
                                    isFolder=True)
            directory.add_menu_item(title='Next Path from {} ({})'.format(group_name, _id),
                                    params={'mode': 'path',
                                            'action': 'next',
                                            'group': group_id,
                                            'id': six.text_type(_id)},
                                    art=folder_next,
                                    info={'plot': description},
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False)
    
    return True, group_name
    
    
def active_widgets_menu():
    widgets = manage.find_defined_widgets()
    
    if len(widgets) > 0:
        for widget_def in widgets:
            _id = widget_def.get('id', '')
            action = widget_def.get('action', '')
            group = widget_def.get('group', '')
            path = widget_def.get('path', '')
            updated = widget_def.get('updated', '')
            
            path_def = manage.get_path_by_id(path, group)
            group_def = manage.get_group_by_id(group)
            
            title = ''
            if path_def and group_def:
                try:
                    path_def['label'] = path_def['label'].encode('utf-8')
                    group_def['label'] = group_def['label'].encode('utf-8')
                except:
                    pass
            
                title = '{} - {}'.format(path_def['label'], group_def['label'])
            elif group_def:
                title = group_def.get('label')
                
            last = time.strftime('%Y-%m-%d %I:%M:%S', time.localtime(float(updated)))
            
            if not action:
                art = folder_shortcut
                params = {'mode': 'group',
                          'group': group,
                          'target': 'shortcut',
                          'id': six.text_type(_id)}
                title = 'Shortcuts from {}'.format(title)
            elif action in ['random', 'next']:
                art = folder_sync if action == 'random' else folder_next
                params = {'mode': 'group',
                          'group': group,
                          'target': 'widget',
                          'id': six.text_type(_id)}
                
            cm = [('Refresh Path', ('RunPlugin('
                                    'plugin://plugin.program.autowidget/'
                                    '?mode=refresh'
                                    '&target={})').format(_id)),
                  ('Edit Widget', ('RunPlugin('
                                   'plugin://plugin.program.autowidget/'
                                   '?mode=manage'
                                   '&action=edit_widget'
                                   '&target={})').format(_id))]
            
            if not group_def:
                title = '{} - [COLOR firebrick]Orphaned[/COLOR]'.format(_id)
                
            directory.add_menu_item(title=title,
                                    art=art,
                                    params=params,
                                    info={'lastplayed': last},
                                    cm=cm[1:] if not action else cm,
                                    isFolder=True)
    else:
        directory.add_menu_item(title='No AutoWidgets have been intialized.',
                                art=alert,
                                isFolder=False)

    return True, 'Active Widgets'
    
    
def tools_menu():
    directory.add_menu_item(title=32006,
                            params={'mode': 'force'},
                            art=refresh,
                            info={'plot': utils.getString(32020)},
                            isFolder=False)
    directory.add_menu_item(title=32066,
                            params={'mode': 'clean'},
                            art=remove,
                            isFolder=False)    
    directory.add_menu_item(title=32064,
                            params={'mode': 'wipe'},
                            art=remove,
                            isFolder=False)
    return True, utils.getString(32008)
    
    
def call_path(group_id, path_id):
    path_def = manage.get_path_by_id(path_id, group_id=group_id)
    if not path_def:
        return
    
    xbmc.executebuiltin('Dialog.Close(busydialog)')
        
    if path_def['target'] == 'shortcut':
        if path_def['is_folder'] == 0:
            if path_def['content'] == 'addons':
                xbmc.executebuiltin('ActivateWindow({},{},return)'.format(path_def['window'],
                                                                          path_def['path']))
            else:
                if path_def['path'] == 'addons://install/':
                    xbmc.executebuiltin('InstallFromZip')
                else:
                    xbmc.executebuiltin('RunPlugin({})'.format(path_def['path']))
        else:
            xbmc.executebuiltin('ActivateWindow({},{},return)'.format(path_def['window'],
                                                                      path_def['path']))
    elif path_def['target'] == 'widget':
        xbmc.executebuiltin('ActivateWindow({},{},return)'.format(path_def['window'],
                                                                  path_def['path']))
    elif path_def['target'] == 'settings':
        xbmc.executebuiltin('Addon.OpenSettings({})'.format(path_def['path'].replace('plugin://', '')))


def random_path(group_id):
    _window = utils.get_active_window()
    
    if _window not in ['home', 'media'] and not label_warning_shown:
        _warn()
    
    group = manage.get_group_by_id(group_id)
    if not group:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'.format(group_id),
                  level=xbmc.LOGERROR)
        return False, 'AutoWidget'
    
    group_name = group.get('label', '')
    paths = manage.find_defined_paths(group_id)
    
    if len(paths) > 0:
        if _window == 'media':
            rand = random.randrange(len(paths))
            call_path(group_id, paths[rand]['id'])
            return False, group_name
        else:
            directory.add_menu_item(title=32013,
                                    params={'mode': 'force'},
                                    art=unpack,
                                    info={'plot': utils.getString(32014)},
                                    isFolder=False)
            return True, group_name
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False)
        return False, group_name
    
    
def next_path(group_id):
    _window = utils.get_active_window()
    
    if _window not in ['home', 'media'] and not label_warning_shown:
        _warn()
    
    group = manage.get_group_by_id(group_id)
    if not group:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'.format(group_id),
                  level=xbmc.LOGERROR)
        return False, 'AutoWidget'
    
    group_name = group.get('label', '')
    paths = manage.find_defined_paths(group_id)
    
    if len(paths) > 0:
        if _window == 'media':
            call_path(group_id, paths[0]['id'])
            return False, group_name
        else:
            directory.add_menu_item(title=32013,
                                    params={'mode': 'force'},
                                    art=unpack,
                                    info={'plot': utils.getString(32014)},
                                    isFolder=False)
            return True, group_name
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False)
        return False, group_name


def _create_context_items(group_id, path_id, idx, length):
    cm = [(utils.getString(32048),
          ('RunPlugin('
           'plugin://plugin.program.autowidget/'
           '?mode=manage'
           '&action=edit'
           '&group={}'
           '&path={})').format(group_id, path_id))]
    if idx > 0:
        cm.append((utils.getString(32026),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=shift_path'
                   '&target=up'
                   '&group={}'
                   '&path={})').format(group_id, path_id)))
    if idx < length - 1:
        cm.append((utils.getString(32027),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=shift_path'
                   '&target=down'
                   '&group={}'
                   '&path={})').format(group_id, path_id)))
                                                      
    return cm
