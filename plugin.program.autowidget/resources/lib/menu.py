import xbmc
import xbmcaddon
import xbmcgui

import json
import random
import re
import time
import uuid

import six

from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import directory
from resources.lib.common import utils

add = utils.get_art('add.png')
alert = utils.get_art('alert.png')
back = utils.get_art('back.png')
folder = utils.get_art('folder.png')
folder_shortcut = utils.get_art('folder-shortcut.png')
folder_sync = utils.get_art('folder-sync.png')
folder_next = utils.get_art('folder-next.png')
folder_merged = utils.get_art('folder-dots.png')
merge = utils.get_art('merge.png')
next = utils.get_art('next.png')
next_page = utils.get_art('next_page.png')
refresh_art = utils.get_art('refresh.png')
remove = utils.get_art('remove.png')
share = utils.get_art('share.png')
shuffle = utils.get_art('shuffle.png')
sync = utils.get_art('sync.png')
tools = utils.get_art('tools.png')
unpack = utils.get_art('unpack.png')

_addon = xbmcaddon.Addon()


def root_menu():
    directory.add_menu_item(title=32007,
                            params={'mode': 'group'},
                            art=folder,
                            isFolder=True)
    directory.add_menu_item(title=32074,
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
            
            cm = [(utils.get_string(32061),
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
                                isFolder=False,
                                props={'specialsort': 'bottom'})
                                
    return True, utils.get_string(32007)
    
    
def group_menu(group_id, target, _id):
    _window = utils.get_active_window()
    
    group = manage.get_group_by_id(group_id)
    if not group:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'
                  .format(group_id),
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
            directory.add_separator(title=32010, char='/', sort='bottom')

            path_param = '\"$INFO[Window(10000).Property(autowidget-{}-action)]\"'.format(_id)

            directory.add_menu_item(title=utils.get_string(32028)
                                          .format(group_name),
                                    params={'mode': 'path',
                                            'action': 'random',
                                            'group': group_id,
                                            'id': six.text_type(_id),
                                            'path': path_param},
                                    art=shuffle,
                                    isFolder=True,
                                    props={'specialsort': 'bottom'})
            directory.add_menu_item(title=utils.get_string(32076)
                                          .format(group_name),
                                    params={'mode': 'path',
                                            'action': 'next',
                                            'group': group_id,
                                            'id': six.text_type(_id),
                                            'path': path_param},
                                    art=next,
                                    isFolder=True,
                                    props={'specialsort': 'bottom'})
            directory.add_menu_item(title=utils.get_string(32089)
                                          .format(group_name),
                                    params={'mode': 'path',
                                            'action': 'merged',
                                            'group': group_id,
                                            'id': six.text_type(_id)},
                                    art=merge,
                                    isFolder=True,
                                    props={'specialsort': 'bottom'})
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False,
                                props={'specialsort': 'bottom'})
    
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

            art = {}
            params = {}
            if not action:
                art = folder_shortcut
                params = {'mode': 'group',
                          'group': group,
                          'target': 'shortcut',
                          'id': six.text_type(_id)}
                title = utils.get_string(32030).format(title)
            elif action in ['random', 'next', 'merged']:
                if action == 'random':
                    art = folder_sync
                elif action == 'next':
                    art = folder_next
                elif action == 'merged':
                    art = folder_merged
                
                params = {'mode': 'group',
                          'group': group,
                          'target': 'widget',
                          'id': six.text_type(_id)}
                
            cm = [(utils.get_string(32069), ('RunPlugin('
                                            'plugin://plugin.program.autowidget/'
                                            '?mode=refresh'
                                            '&target={})').format(_id)),
                  (utils.get_string(32070), ('RunPlugin('
                                            'plugin://plugin.program.autowidget/'
                                            '?mode=manage'
                                            '&action=edit_widget'
                                            '&target={})').format(_id))]
            
            if not group_def:
                title = '{} - [COLOR firebrick]{}[/COLOR]'.format(_id, utils.get_string(32071))
                
            directory.add_menu_item(title=title,
                                    art=art,
                                    params=params,
                                    cm=cm[1:] if not action else cm,
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32072,
                                art=alert,
                                isFolder=False,
                                props={'specialsort': 'bottom'})

    return True, utils.get_string(32074)
    
    
def tools_menu():
    directory.add_menu_item(title=32006,
                            params={'mode': 'force'},
                            art=refresh_art,
                            info={'plot': utils.get_string(32020)},
                            isFolder=False)
    directory.add_menu_item(title=32064,
                            params={'mode': 'wipe'},
                            art=remove,
                            isFolder=False)
                            
    return True, utils.get_string(32008)
    
    
def _initialize(group_def, action, _id, save=True):
    duration = utils.get_setting_float('service.refresh_duration')
    
    paths = group_def['paths']
    rand_idx = random.randrange(len(paths))
    init_path = paths[0]['id'] if action == 'next' else paths[rand_idx]['id']
    
    params = {'action': action,
              'id': _id,
              'group': group_def['id'],
              'refresh': duration,
              'path': init_path}
    if save:
        details = manage.save_path_details(params)
        refresh.refresh(_id)
        return details
    else:
        return params
    
def show_path(group_id, path_id, _id, titles=None, num=1):
    params = {'jsonrpc': '2.0', 'method': 'Files.GetDirectory',
              'params': {'properties': utils.info_types},
              'id': 1}
    
    widget_def = manage.get_widget_by_id(_id)
    path_def = manage.get_path_by_id(path_id, group_id=group_id)
    if not widget_def:
        return True, 'AutoWidget'
        
    if not path_def:
        if widget_def:
            path_def = manage.get_path_by_id(widget_def['path'],
                                             group_id=widget_def['group'])
        params['params']['directory'] = path_id
    else:
        params['params']['directory'] = path_def['path']
    
    if path_def:
        path_label = path_def.get('label', 'AutoWidget')
    else:
        path_label = widget_def.get('label', '')
    
    if not titles:
        titles = []
    
    files = json.loads(xbmc.executeJSONRPC(json.dumps(params)))
    stack = widget_def.get('stack', [])
    if stack:
        directory.add_menu_item(title='Previous Page',
                                params={'mode': 'path',
                                        'action': 'update',
                                        'id': _id,
                                        'path': stack[-1],
                                        'target': 'back'},
                                art=back,
                                isFolder=num > 1,
                                props={'specialsort': 'top',
                                       'widget': path_label})
    
    if 'error' not in files:
        files = files['result']['files']
        filtered_files = [x for x in files if x['label'] not in titles]

        for file in filtered_files:
            labels = {}
            for label in file:
                labels[label] = file[label]
            
            labels['title'] = file['label']
            
            hide_watched = utils.get_setting_bool('widgets.hide_watched')
            show_next = utils.get_setting_bool('widgets.show_next')
            sort_next = utils.get_setting_int('widgets.sort_next')
            
            next_item = re.sub('[^\w \xC0-\xFF]', '', labels['title'].lower()).strip() in ['next', 'next page']
            prev_item = re.sub('[^\w \xC0-\xFF]', '', labels['title'].lower()).strip() in ['previous', 'previous page', 'back']
            
            sort_to_end = next_item and sort_next == 1
            if prev_item and stack:
                continue
            
            if not next_item or sort_next != 2:
                props = {'widget': path_label}
                if next_item:
                    if not show_next:
                        continue
                
                    labels['title'] = 'Next Page'
                    if sort_to_end:
                        props['specialsort'] = 'bottom'
                    
                    if num > 1:
                        labels['title'] = '{} - {}'.format(labels['title'],
                                                           path_label)
                    
                    directory.add_menu_item(title=labels['title'],
                                            params={'mode': 'path',
                                                    'action': 'update',
                                                    'id': _id,
                                                    'path': file['file'],
                                                    'target': 'next'} if num == 1 else None,
                                            path=file['file'] if num > 1 else None,
                                            art=next_page,
                                            info=labels,
                                            isFolder=num > 1,
                                            props=props)
                else:
                    if hide_watched and labels.get('playcount', 0) > 0:
                        continue
                
                    directory.add_menu_item(title=labels['title'],
                                            path=file['file'],
                                            art=labels['art'],
                                            info=labels,
                                            isFolder=file['filetype'] == 'directory',
                                            props=props)
                    
                    titles.append(labels['title'])
         
    return titles, path_label
    
    
def call_path(group_id, path_id):
    path_def = manage.get_path_by_id(path_id, group_id=group_id)
    if not path_def:
        return
    
    xbmc.executebuiltin('Dialog.Close(busydialog)')
    xbmc.sleep(500)
    final_path = ''
    
    if path_def['target'] == 'shortcut' and path_def['is_folder'] == 0 \
                                        and path_def['content'] != 'addons':
        if path_def['path'] == 'addons://install/':
            final_path = 'InstallFromZip'
        elif path_def['content'] == 'files': 
            final_path = 'RunPlugin({})'.format(path_def['path'])
        elif path_def['path'].startswith('androidapp://sources/apps/'):
            final_path = 'StartAndroidActivity({})'.format(path_def['path']
                                                           .replace('androidapp://sources/apps/', ''))
        elif all(i in path_def['path'] for i in ['(', ')']) and '://' not in path_def['path']:
            final_path = path_def['path']
        else:
            final_path = 'PlayMedia({})'.format(path_def['path'])
    elif path_def['target'] == 'widget' or path_def['is_folder'] == 1 \
                                        or path_def['content'] == 'addons':
        final_path = 'ActivateWindow({},{},return)'.format(path_def.get('window', 'Videos'),
                                                           path_def['path'])
    elif path_def['target'] == 'settings':
        final_path = 'Addon.OpenSettings({})'.format(path_def['path']
                                                     .replace('plugin://', ''))
        
    if final_path:
        xbmc.executebuiltin(final_path)
        
    return False, path_def['label']


def update_path(_id, path, target):
    widget_def = manage.get_widget_by_id(_id)
    if not widget_def:
        return
        
    stack = widget_def.get('stack', [])
    
    if target == 'next':
        path_id = widget_def['path'].split('-')
        if len(path_id) > 1:
            if time.ctime(float(path_id[1])):
                path_def = manage.get_path_by_id(widget_def['path'], group_id=widget_def['group'])
                widget_def['label'] = path_def['label']
        
        stack.append(widget_def['path'])
        widget_def['stack'] = stack
        widget_def['path'] = path
    elif target == 'back':
        widget_def['path'] = widget_def['stack'][-1]
        widget_def['stack'] = widget_def['stack'][:-1]
        
        if len(widget_def['stack']) == 0:
            widget_def['label'] = ''
        
    utils.set_property('autowidget-{}-action'.format(_id), widget_def['path'])
    manage.save_path_details(widget_def, _id)
    utils.update_container()


def path_menu(group_id, action, _id, path=None):
    _window = utils.get_active_window()
    
    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'
                  .format(group_id),
                  level=xbmc.LOGERROR)
        return False, 'AutoWidget'
    
    group_name = group_def.get('label', '')
    paths = group_def.get('paths', [])
    
    widget_def = manage.get_widget_by_id(_id, group_id)
    
    if not widget_def:
        widget_def = _initialize(group_def, action, _id, save=_window not in ['dialog', 'media'])
    
    if len(paths) > 0 and widget_def:
        if _window == 'media':
            rand = random.randrange(len(paths))
            return call_path(group_id, paths[rand]['id'])
        else:
            path_id = path if path else widget_def.get('path', '')
            titles, cat = show_path(group_id, path_id, _id)
            return titles, cat
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False)
        return True, group_name
        
    return True, group_name
        
        
def merged_path(group_id, _id):
    _window = utils.get_active_window()
    
    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'
                  .format(group_id),
                  level=xbmc.LOGERROR)
        return False, 'AutoWidget'
    
    group_name = group_def.get('label', '')
    paths = manage.find_defined_paths(group_id)
    
    if len(paths) > 0:
        titles = []

        for path_def in paths:
            titles, cat = show_path(group_id, path_def['id'], _id, num=len(paths))
                    
        return True, group_name
    else:
        directory.add_menu_item(title=32032,
                                art=alert,
                                isFolder=False)
        return False, group_name


def _create_context_items(group_id, path_id, idx, length):
    cm = [(utils.get_string(32048),
          ('RunPlugin('
           'plugin://plugin.program.autowidget/'
           '?mode=manage'
           '&action=edit'
           '&group={}'
           '&path={})').format(group_id, path_id))]
    if idx > 0:
        cm.append((utils.get_string(32026),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=shift_path'
                   '&target=up'
                   '&group={}'
                   '&path={})').format(group_id, path_id)))
    if idx < length - 1:
        cm.append((utils.get_string(32027),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=shift_path'
                   '&target=down'
                   '&group={}'
                   '&path={})').format(group_id, path_id)))
                                                      
    return cm
