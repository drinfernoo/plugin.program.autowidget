from kodi_six import xbmcgui

import re
import uuid

import six

from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import directory
from resources.lib.common import utils

folder_shortcut = utils.get_art('folder-shortcut')
folder_sync = utils.get_art('folder-sync')
folder_next = utils.get_art('folder-next')
folder_merged = utils.get_art('folder-dots')
info = utils.get_art('information_outline')
merge = utils.get_art('merge')
next = utils.get_art('next')
next_page = utils.get_art('next_page')
refresh_art = utils.get_art('refresh')
remove = utils.get_art('remove')
share = utils.get_art('share')
shuffle = utils.get_art('shuffle')
spray_bottle = utils.get_art('spray-bottle')
sync = utils.get_art('sync')
tools = utils.get_art('tools')
unpack = utils.get_art('unpack')


def root_menu():
    directory.add_menu_item(title=32007,
                            params={'mode': 'group'},
                            art=utils.get_art('folder'),
                            isFolder=True)
    directory.add_menu_item(title=32074,
                            params={'mode': 'widget'},
                            art=utils.get_art('folder'),
                            isFolder=True)
    directory.add_menu_item(title=32008,
                            params={'mode': 'tools'},
                            art=utils.get_art('tools'),
                            isFolder=True)
                            
    return True, 'AutoWidget'
                            
                            
def my_groups_menu():
    groups = manage.find_defined_groups()
    if len(groups) > 0:
        for group in groups:
            group_name = group['label']
            group_id = group['id']
            group_type = group['type']
            
            cm = [(utils.get_string(32061),
                  ('RunPlugin('
                   'plugin://plugin.program.autowidget/'
                   '?mode=manage'
                   '&action=edit'
                   '&group={})').format(group_id))]
            
            directory.add_menu_item(title=six.text_type(group_name),
                                    params={'mode': 'group',
                                            'group': group_id},
                                    info=group.get('info', {}),
                                    art=group.get('art') or (utils.get_art('folder-shortcut')
                                                             if group_type == 'shortcut'
                                                             else utils.get_art('folder-sync')),
                                    cm=cm,
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32068,
                                art=utils.get_art('alert'),
                                isFolder=False,
                                props={'specialsort': 'bottom'})
                                
    return True, utils.get_string(32007)
    
    
def group_menu(group_id):
    _window = utils.get_active_window()
    _id = uuid.uuid4()

    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        utils.log('\"{}\" is missing, please repoint the widget to fix it.'
                  .format(group_id), 'error')
        return False, 'AutoWidget'

    group_name = group_def['label']
    group_type = group_def['type']
    paths = group_def['paths']

    if len(paths) > 0:
        utils.log(u'Showing {} group: {}'.format(group_type, six.text_type(group_name)),
                  'debug')
        cm = []
        art = folder_shortcut if group_type == 'shortcut' else folder_sync

        for idx, path_def in enumerate(paths):
            if _window == 'media':
                cm = _create_context_items(group_id, path_def['id'], idx,
                                           len(paths), group_type)
            
            directory.add_menu_item(title=path_def['label'],
                                    params={'mode': 'path',
                                            'group': group_id,
                                            'path_id': path_def['id']},
                                    info=path_def['file'],
                                    art=path_def['file']['art'] or art,
                                    cm=cm,
                                    isFolder=False)

        if _window != 'home':
            _create_action_items(group_def, _id)
    else:
        directory.add_menu_item(title=32032,
                                art=utils.get_art('alert'),
                                isFolder=False,
                                props={'specialsort': 'bottom'})

    return True, group_name


def active_widgets_menu():
    manage.clean()
    widgets = sorted(manage.find_defined_widgets(),
                     key=lambda x: x.get('updated'), reverse=True)
    
    if len(widgets) > 0:
        for widget_def in widgets:
            widget_id = widget_def.get('id', '')
            action = widget_def.get('action', '')
            group = widget_def.get('group', '')
            path_def = widget_def.get('path', {})
            
            group_def = manage.get_group_by_id(group)
            
            title = ''
            if path_def and group_def:
                try:
                    if action != 'merged':
                        if isinstance(path_def, dict):
                            label = path_def['label'].encode('utf-8')
                        else:
                            label = widget_def['stack'][0]['label'].encode('utf-8')
                        group_def['label'] = group_def['label'].encode('utf-8')
                    else:
                        label = utils.get_string(32128).format(len(path_def))
                except:
                    pass
                
                title = '{} - {}'.format(label, group_def['label'])
            elif group_def:
                title = group_def.get('label')

            art = {}
            params = {}
            cm = []
            if not action:
                art = folder_shortcut
                title = utils.get_string(32030).format(title)
            else:
                if action in ['random', 'next']:
                    art = shuffle
                    cm.append((utils.get_string(32069), ('RunPlugin('
                                                         'plugin://plugin.program.autowidget/'
                                                         '?mode=refresh'
                                                         '&id={})').format(widget_id)))
                elif action == 'merged':
                    art = merge
                elif action == 'static':
                    art = utils.get_art('folder')
                
            cm.append((utils.get_string(32070), ('RunPlugin('
                                                 'plugin://plugin.program.autowidget/'
                                                 '?mode=manage'
                                                 '&action=edit_widget'
                                                 '&id={})').format(widget_id)))
            
            if not group_def:
                title = '{} - [COLOR firebrick]{}[/COLOR]'.format(widget_id, utils.get_string(32071))
                
            directory.add_menu_item(title=title,
                                    art=art,
                                    params={'mode': 'group',
                                            'group': group},
                                    cm=cm[1:] if not action else cm,
                                    isFolder=True)
    else:
        directory.add_menu_item(title=32072,
                                art=utils.get_art('alert'),
                                isFolder=False,
                                props={'specialsort': 'bottom'})

    return True, utils.get_string(32074)
    
    
def tools_menu():
    directory.add_menu_item(title=32006,
                            params={'mode': 'force'},
                            art=utils.get_art('refresh'),
                            info={'plot': utils.get_string(32020)},
                            isFolder=False)
    directory.add_menu_item(title=32129,
                            params={'mode': 'clean'},
                            art=utils.get_art('spray-bottle'),
                            isFolder=False)
    directory.add_menu_item(title=32064,
                            params={'mode': 'wipe'},
                            art=utils.get_art('remove'),
                            isFolder=False)
    directory.add_menu_item(title=32127,
                            params={'mode': 'skindebug'},
                            art=utils.get_art('bug-outline'),
                            isFolder=False)
                            
    return True, utils.get_string(32008)


def show_path(group_id, path_label, widget_id, path, idx=0, titles=None, num=1, merged=False):
    hide_watched = utils.get_setting_bool('widgets.hide_watched')
    show_next = utils.get_setting_int('widgets.show_next')
    paged_widgets = utils.get_setting_bool('widgets.paged')
    default_color = utils.get_setting('ui.color')
    
    widget_def = manage.get_widget_by_id(widget_id)
    if not widget_def:
        return True, 'AutoWidget'
    
    if not titles:
        titles = []
    
    files = refresh.get_files_list(path, titles, widget_id)
    if not files:
        return titles, path_label
    
    utils.log('Loading items from {}'.format(path), 'debug')
    
    if isinstance(widget_def['path'], list):
        color = widget_def['path'][idx].get('color', default_color)
    elif isinstance(widget_def['path'], six.text_type):
        color = widget_def['stack'][0].get('color', default_color)
    else:
        color = widget_def['path'].get('color', default_color)
    
    stack = widget_def.get('stack', [])
    if stack:
        title = utils.get_string(32110).format(len(stack))
        directory.add_menu_item(title=title,
                                params={'mode': 'path',
                                        'action': 'update',
                                        'id': widget_id,
                                        'path': '',
                                        'target': 'back'},
                                art=utils.get_art('back', color),
                                isFolder=num > 1,
                                props={'specialsort': 'top',
                                       'autoLabel': path_label})
    
    for file in files:
        properties = {'autoLabel': path_label,
                      'autoID': widget_id}
        if 'customproperties' in file:
            for prop in file['customproperties']:
                properties[prop] = file['customproperties'][prop]
        
        clean_pattern = '[^\w \xC0-\xFF]'
        tag_pattern = '(\[[^\]]*\])'
        
        next_pattern = ('(?:^(?:next)?\s*(?:(?:>>)|(?:\.*)$)?)\s*'
                        '(?:page\s*(?:(?:\d+\D*\d?$)|(?:(?:>>)|(?:\.*)$)|(?:\(\d+|.*\)$))?)?$')
        prev_pattern = '^(?:previous(?: page)?)$|^(?:back)$'
        
        cleaned_title = re.sub(tag_pattern, '', file.get('label','').lower()).strip()
        next_item =  re.search(next_pattern, cleaned_title)
        prev_item = re.search(prev_pattern, cleaned_title)
        
        if (prev_item and stack) or (next_item and show_next == 0):
            continue
        elif next_item and show_next > 0:
            label = utils.get_string(32111)
            properties['specialsort'] = 'bottom'
            
            if num > 1:
                if show_next == 1:
                    continue
                    
                label = '{} - {}'.format(label, path_label)

            update_params = {'mode': 'path',
                             'action': 'update',
                             'id': widget_id,
                             'path': file['file'],
                             'target': 'next'}

            directory.add_menu_item(title=label,
                                    params=update_params if paged_widgets and not merged else None,
                                    path=file['file'] if not paged_widgets or merged else None,
                                    art=utils.get_art('next_page', color),
                                    info=file,
                                    isFolder=not paged_widgets or merged,
                                    props=properties)
        else:
            dupe = False
            title = (file['label'], file.get('imdbnumber'))
            for t in titles:
                if t == title:
                    dupe = True
            
            if (hide_watched and file.get('playcount', 0) > 0) or dupe:
                continue

            directory.add_menu_item(title=title[0],
                                    path=file['file'],
                                    art=file['art'],
                                    info=file,
                                    isFolder=file['filetype'] == 'directory',
                                    props=properties)
            
            titles.append(title)

    return titles, path_label
    
    
def call_path(path_id):
    path_def = manage.get_path_by_id(path_id)
    if not path_def:
        return
    
    utils.call_builtin('Dialog.Close(busydialog)', 500)
    final_path = ''
    
    if path_def['target'] == 'shortcut' and path_def['file']['filetype'] == 'file' \
                                        and path_def['content'] != 'addons':
        if path_def['file']['file'] == 'addons://install/':
            final_path = 'InstallFromZip'
        elif not path_def['content'] or path_def['content'] == 'files': 
            if path_def['file']['file'].startswith('androidapp://sources/apps/'):
                final_path = 'StartAndroidActivity({})'.format(path_def['file']['file']
                                                               .replace('androidapp://sources/apps/', ''))
            elif path_def['file']['file'].startswith('pvr://'):
                final_path = 'PlayMedia({})'.format(path_def['file']['file'])
            else:
                final_path = 'RunPlugin({})'.format(path_def['file']['file'])
        elif all(i in path_def['file']['file'] for i in ['(', ')']) and '://' not in path_def['file']['file']:
            final_path = path_def['file']['file']
        else:
            final_path = 'PlayMedia({})'.format(path_def['file']['file'])
    elif path_def['target'] == 'widget' or path_def['file']['filetype'] == 'directory' \
                                        or path_def['content'] == 'addons':
        final_path = 'ActivateWindow({},{},return)'.format(path_def.get('window', 'Videos'),
                                                           path_def['file']['file'])
    elif path_def['target'] == 'settings':
        final_path = 'Addon.OpenSettings({})'.format(path_def['file']['file']
                                                     .replace('plugin://', ''))
        
    if final_path:
        utils.log('Calling path from {} using {}'.format(path_id, final_path), 'debug')
        utils.call_builtin(final_path)
        
    return False, path_def['label']


def path_menu(group_id, action, widget_id):
    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        directory.add_menu_item(title=32073,
                                info={'plot': utils.get_string(32075)},
                                art=utils.get_art('alert'),
                                isFolder=True)
        return True, 'AutoWidget'
        
    group_name = group_def.get('label', '')
    paths = group_def.get('paths', [])
    if len(paths) == 0:
        directory.add_menu_item(title=32032,
                                art=utils.get_art('alert'),
                                isFolder=True)
        return True, group_name

    widget_def = manage.get_widget_by_id(widget_id, group_id)
    if not widget_def:
        dialog = xbmcgui.Dialog()
        if action == 'static':
            idx = dialog.select(utils.get_string(32114), [i['label'] for i in paths])
            if idx == -1:
                return True, 'AutoWidget'
            
            widget_def = manage.initialize(group_def, action, widget_id, keep=idx)
        elif action == 'cycling':
            idx = dialog.select(utils.get_string(32081), [utils.get_string(32079),
                                                          utils.get_string(32080)])
            if idx == -1:
                return True, 'AutoWidget'
            
            _action = 'random' if idx == 0 else 'next'
            widget_def = manage.initialize(group_def, _action, widget_id)
    
    if widget_def:
        widget_path = widget_def.get('path', {})
        
        if isinstance(widget_path, dict):
            _label = widget_path['label']
            widget_path = widget_path['file']['file']
        else:
            stack = widget_def.get('stack', [])
            if stack:
                _label = stack[0]['label']
            else:
                _label = widget_def.get('label', '')
        utils.log('Showing widget {}'.format(widget_id), 'debug')
        titles, cat = show_path(group_id, _label, widget_id, widget_path)
        return titles, cat
    else:
        directory.add_menu_item(title=32067,
                                art=utils.get_art('information_outline'),
                                isFolder=True)
        return True, group_name
        
        
def merged_path(group_id, widget_id):
    _window = utils.get_active_window()

    group_def = manage.get_group_by_id(group_id)
    group_name = group_def.get('label', '')
    paths = group_def.get('paths', [])
    if len(paths) == 0:
        directory.add_menu_item(title=32032,
                                art=utils.get_art('alert'),
                                isFolder=False)
        return True, group_name
    
    widget_def = manage.get_widget_by_id(widget_id, group_id)
    if widget_def and _window != 'dialog':
        paths = widget_def['path']
    elif not widget_def:
        dialog = xbmcgui.Dialog()
        idxs = dialog.multiselect(utils.get_string(32115),
                                  [i['label'] for i in paths],
                                  preselect=list(range(len(paths))) if len(paths) <= 5 else [])

        if idxs is not None:
            if len(idxs) > 0:
                widget_def = manage.initialize(group_def, 'merged',
                                               widget_id, keep=idxs)
                paths = widget_def['path']
        
    if widget_def:
        titles = []
        for idx, path_def in enumerate(paths):
            titles, cat = show_path(group_id, path_def['label'],
                                    widget_id, path_def['file']['file'], idx=idx,
                                    titles=titles, num=len(paths), merged=True)

        return titles, cat
    else:
        directory.add_menu_item(title=32067,
                                art=utils.get_art('information_outline'),
                                isFolder=True)
        return True, group_name


def _create_context_items(group_id, path_id, idx, length, target):
    cm = [(utils.get_string(32048) if target == 'shortcut' else utils.get_string(32140),
              ('RunPlugin('
               'plugin://plugin.program.autowidget/'
               '?mode=manage'
               '&action=edit_path'
               '&group={}'
               '&path_id={})').format(group_id, path_id)),
          (utils.get_string(32026) if idx > 0 else utils.get_string(32113),
              ('RunPlugin('
               'plugin://plugin.program.autowidget/'
               '?mode=manage'
               '&action=shift_path'
               '&target=up'
               '&group={}'
               '&path_id={})').format(group_id, path_id)),
          (utils.get_string(32027) if idx < length - 1 else utils.get_string(32112),
              ('RunPlugin('
               'plugin://plugin.program.autowidget/'
               '?mode=manage'
               '&action=shift_path'
               '&target=down'
               '&group={}'
               '&path_id={})').format(group_id, path_id))]

    return cm


def _create_action_items(group_def, _id):
    refresh = '$INFO[Window(10000).Property(autowidget-{}-refresh)]'.format(_id)
    props = {'specialsort': 'bottom'}
    
    group_id = group_def['id']
    group_name = group_def['label']
    group_type = group_def['type']
    
    if group_type == 'widget':
        directory.add_separator(title=32010, char='/', sort='bottom')
        directory.add_menu_item(title=utils.get_string(32076)
                                      .format(six.text_type(group_name)),
                                params={'mode': 'path',
                                        'action': 'static',
                                        'group': group_id,
                                        'id': six.text_type(_id),
                                        'refresh': refresh},
                                art=utils.get_art('folder'),
                                isFolder=True,
                                props=props)
        directory.add_menu_item(title=utils.get_string(32028)
                                      .format(six.text_type(group_name)),
                                params={'mode': 'path',
                                        'action': 'cycling',
                                        'group': group_id,
                                        'id': six.text_type(_id),
                                        'refresh': refresh},
                                art=utils.get_art('shuffle'),
                                isFolder=True,
                                props=props)
        directory.add_menu_item(title=utils.get_string(32089)
                                      .format(six.text_type(group_name)),
                                params={'mode': 'path',
                                        'action': 'merged',
                                        'group': group_id,
                                        'id': six.text_type(_id)},
                                art=utils.get_art('merge'),
                                isFolder=True,
                                props=props)
