import xbmc
import xbmcgui

import random
import time
import hashlib
import json
import threading
import Queue
import os


from resources.lib import manage
from resources.lib.common import utils

skin_string_pattern = 'autowidget-{}-{}'
_properties = ['context.autowidget']

_thread = None


class RefreshService(xbmc.Monitor):

    def __init__(self):
        """Starts all of the actions of AutoWidget's service."""
        super(RefreshService, self).__init__()
        utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', 'notice')
        self.player = xbmc.Player()
        utils.ensure_addon_data()
        self._update_properties()
        self._clean_widgets()
        self._update_widgets()

    def onSettingsChanged(self):
        self._update_properties()

    def _update_properties(self):
        for property in _properties:
            setting = utils.get_setting(property)
            utils.log('{}: {}'.format(property, setting))
            if setting is not None:
                utils.set_property(property, setting)
                utils.log('Property {0} set'.format(property))
            else:
                utils.clear_property(property)
                utils.log('Property {0} cleared'.format(property))

        self._reload_settings()
        
    def _reload_settings(self):
        self.refresh_enabled = utils.get_setting_int('service.refresh_enabled')
        self.refresh_duration = utils.get_setting_float('service.refresh_duration')
        self.refresh_notification = utils.get_setting_int('service.refresh_notification')
        self.refresh_sound = utils.get_setting_bool('service.refresh_sound')
        
        utils.update_container(True)
        
    def _clean_widgets(self):
        for widget_def in manage.find_defined_widgets():
            if not manage.clean(widget_def['id']):
                utils.log('Resetting {}'.format(widget_def['id']))
                update_path(widget_def['id'], None, 'reset')

    def _update_widgets(self):
        self._refresh(True)
        
        while not self.abortRequested():
            for _ in range(0, 60):
                if self.waitForAbort(15):
                    break

            if self.abortRequested():
                break

            if not self._refresh():
                continue
                
    def _refresh(self, startup=False):
        if self.refresh_enabled in [0, 1] and manage.find_defined_widgets():
            notification = False
            if self.refresh_enabled == 1:
                if self.player.isPlayingVideo():
                    utils.log('+++++ PLAYBACK DETECTED, SKIPPING AUTOWIDGET REFRESH +++++',
                              'notice')
                    return
            else:
                if self.refresh_notification == 0:
                    notification = True
                elif self.refresh_notification == 1:
                    if not self.player.isPlayingVideo():
                        notification = True
            
            utils.log('+++++ REFRESHING AUTOWIDGETS +++++', 'notice')
            refresh_paths(notify=notification and not startup)
        else:
            utils.log('+++++ AUTOWIDGET REFRESHING NOT ENABLED +++++',
                      'notice')

def _update_strings(widget_def):
    refresh = skin_string_pattern.format(widget_def['id'], 'refresh')
    utils.set_property(refresh, '{}'.format(time.time()))
    utils.log('Refreshing widget {} to display {}'.format(widget_def['id'],
                                                       widget_def['path']),
                                                       'debug')

def update_path(widget_id, target, path=None):
    widget_def = manage.get_widget_by_id(widget_id)
    if not widget_def:
        return
    
    stack = widget_def.get('stack', [])

    if target == 'next' and path:
        utils.log('Next Page selected from {}'.format(widget_id), 'debug')
        path_def = widget_def['path']
        if isinstance(path_def, dict):
            widget_def['label'] = path_def['label']
        
        stack.append(widget_def['path'])
        widget_def['stack'] = stack
        widget_def['path'] = path
    elif target == 'back' and widget_def.get('stack'):
        utils.log('Previous Page selected from {}'.format(widget_id), 'debug')
        widget_def['path'] = widget_def['stack'][-1]
        widget_def['stack'] = widget_def['stack'][:-1]
        
        if len(widget_def['stack']) == 0:
            widget_def['label'] = ''
    elif target == 'reset':
            if len(stack) > 0:
                widget_def['path'] = widget_def['stack'][0]
                widget_def['stack'] = []
                widget_def['label'] = ''
    
    action = widget_def['path'] if widget_def['action'] != 'merged' else 'merged'
    if isinstance(widget_def['path'], dict):
        action = widget_def['path']['file']['file']
    manage.save_path_details(widget_def)
    _update_strings(widget_def)
    utils.update_container(True)
    back_to_top(target)


def back_to_top(target):
    if target != 'next':
        return
    actions = ['back', 'firstpage', 'right']
    for action in actions:
        utils.call_builtin('Action({})'.format(action), 100)


def refresh(widget_id, widget_def=None, paths=None, force=False, single=False):
    if not widget_def:
        widget_def = manage.get_widget_by_id(widget_id)
    
    if widget_def['action'] in ['static', 'merged']:
        return paths
    
    current_time = time.time()
    updated_at = widget_def.get('updated', 0)
    
    default_refresh = utils.get_setting_float('service.refresh_duration')
    refresh_duration = float(widget_def.get('refresh', default_refresh))
    
    if updated_at <= current_time - (3600 * refresh_duration) or force:
        group_id = widget_def['group']
        action = widget_def.get('action')
        current = int(widget_def.get('current', -1))
        widget_def['stack'] = []
        widget_def['label'] = ''
        
        if not paths:
            paths = manage.find_defined_paths(group_id)
        
        if action:
            if len(paths) > 0:
                next = 0
                if action == 'next':
                    next = (current + 1) % len(paths)
                elif action == 'random':
                    random.shuffle(paths)
                    next = random.randrange(len(paths))
                    
                widget_def['current'] = next
                path_def = paths[next]
                paths.remove(paths[next])
                
                widget_def['path'] = path_def
                if widget_def['path']:
                    widget_def['updated'] = 0 if force else current_time
                        
                    manage.save_path_details(widget_def)
                    _update_strings(widget_def)
                    
        if single:
            utils.update_container(True)
    
    return paths


def refresh_paths(notify=False, force=False):
    if notify:
        dialog = xbmcgui.Dialog()
        dialog.notification('AutoWidget', utils.get_string(32033),
                            sound=utils.get_setting_bool('service.refresh_sound'))

    for group_def in manage.find_defined_groups():
        paths = []
        
        widgets = manage.find_defined_widgets(group_def['id'])
        for widget_def in widgets:
            paths = refresh(widget_def['id'], widget_def=widget_def, paths=paths, force=force)

    utils.update_container(True)

    return True, 'AutoWidget'


def get_files_list(path, titles=None, widget_id=None):
    if not titles:
        titles = []

    hash = hashlib.sha1(path).hexdigest()
    cache_path = os.path.join(utils._addon_path, '{}.cache'.format(hash))
    expiry = utils.cache_expiry(hash)
    files = None

    if os.path.exists(cache_path):
        files = utils.read_json(cache_path)
        utils.log("Read cache (exp in {}s): {}".format(expiry-time.time(), hash), 'notice')
        if expiry < time.time():
            utils.log("Queue cache update for: {}".format(hash), 'notice')
            queue_widget_update(widget_id)
    if not files:
        # We had no old content so have to block and get it now
        files = utils.cache_files(path)
        
    new_files = []
    if 'error' not in files:
        files = files.get('result').get('files')
        if not files:
            utils.log('No items found for {}'.format(path))
            return
            
        filtered_files = [x for x in files if x['title'] not in titles]
        for file in filtered_files:
            new_file = {k: v for k, v in file.items() if v not in [None, '', -1, [], {}]}
            if 'art' in new_file:
                for art in new_file['art']:
                    new_file['art'][art] = utils.clean_artwork_url(file['art'][art])
            new_files.append(new_file)
        utils.log(json.dumps(files), 'debug')
                
        return new_files

def queue_widget_update(widget_id):
    global _thread
    if _thread is None or not _thread.is_alive():
        _thread = Worker()
        _thread.daemon = True
    _thread.queue.put(widget_id)    
    _thread.start()

class Worker(threading.Thread):
    def __init__(self):
        super(Worker, self).__init__()
        self.queue = Queue.Queue()

    def run(self):
        # Just run while we have stuff to process
        while True:
            try:
                # Don't block
                widget_id = self.queue.get(block=False)
                cache_and_update(widget_id)
                self.queue.task_done()
            except Queue.Empty:
                break

def cache_and_update(widget_id):
    widget_def = manage.get_widget_by_id(widget_id)
    if not widget_def:
        return
    widget_path = widget_def.get('path', {})  
    if isinstance(widget_path, dict):
        _label = widget_path['label']
        widget_path = widget_path['file']['file']
    utils.cache_files(widget_path)
    _update_strings(widget_def)


