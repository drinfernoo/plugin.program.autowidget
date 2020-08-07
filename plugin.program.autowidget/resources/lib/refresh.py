import xbmc
import xbmcgui

import random
import time

from resources.lib import manage
from resources.lib.common import utils

skin_string_pattern = 'autowidget-{}-{}'
_properties = ['context.autowidget']


class RefreshService(xbmc.Monitor):

    def __init__(self):
        """Starts all of the actions of AutoWidget's service."""
        super(RefreshService, self).__init__()
        utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)
        self.player = xbmc.Player()
        utils.ensure_addon_data()
        self._update_properties()
        self._update_labels()
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
        
        self._clean_widgets()
        utils.update_container(True)
        
    def _clean_widgets(self):
        manage.clean()
        for widget_def in manage.find_defined_widgets():
            utils.log('Resetting {}'.format(widget_def['id']), level=xbmc.LOGDEBUG)
            update_path(widget_def['id'], None, 'reset')

    def _update_labels(self):
        for widget_def in manage.find_defined_widgets():
            path_def = manage.get_path_by_id(widget_def.get('path'),
                                             group_id=widget_def['group'])
            if not path_def:
                continue
            
            if widget_def.get('updated', 0) > 0:
                _update_strings(widget_def['id'], path_def)

    def _update_widgets(self):
        self._refresh(True)
        
        while not self.abortRequested():
            if self.waitForAbort(60 * 15):
                break

            if not self._refresh():
                continue
                
    def _refresh(self, startup=False):
        if self.refresh_enabled in [0, 1] and manage.find_defined_widgets():
            notification = False
            if self.refresh_enabled == 1:
                if self.player.isPlayingVideo():
                    utils.log('+++++ PLAYBACK DETECTED, SKIPPING AUTOWIDGET REFRESH +++++',
                              level=xbmc.LOGNOTICE)
                    return
            else:
                if self.refresh_notification == 0:
                    notification = True
                elif self.refresh_notification == 1:
                    if not self.player.isPlayingVideo():
                        notification = True
            
            utils.log('+++++ REFRESHING AUTOWIDGETS +++++', level=xbmc.LOGNOTICE)
            refresh_paths(notify=notification and not startup)
        else:
            utils.log('+++++ AUTOWIDGET REFRESHING NOT ENABLED +++++',
                      level=xbmc.LOGNOTICE)


def _update_strings(widget_id, path_def):
    if path_def:
        refresh = skin_string_pattern.format(widget_id, 'refresh')
        utils.set_property(refresh, '{}'.format(time.time()))


def update_path(widget_id, path, target):
    widget_def = manage.get_widget_by_id(widget_id)
    if not widget_def:
        return
    
    stack = widget_def.get('stack', [])

    if target == 'next':
        path_def = widget_def['path']
        if isinstance(path_def, dict):
            widget_def['label'] = path_def['label']
        
        stack.append(widget_def['path'])
        widget_def['stack'] = stack
        widget_def['path'] = path
    elif target == 'back':
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
    _update_strings(widget_id)
    manage.save_path_details(widget_def)
    back_to_top(target)
    utils.update_container(True)


def back_to_top(target):
    if target != 'next':
        return
    actions = ['back', 'firstpage', 'right']
    for action in actions:
        xbmc.sleep(100)
        xbmc.executebuiltin('Action({})'.format(action))


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
        _id = widget_def['id']
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
                    _update_strings(_id)
                    
        if single and utils.get_active_window() == 'media':
            utils.update_container()
    
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
