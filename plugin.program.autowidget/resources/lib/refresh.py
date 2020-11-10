import xbmc
import xbmcgui

import random
import time
import hashlib
import json
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
        utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', 'info')
        self.player = Player()
        utils.ensure_addon_data()
        self._update_properties()
        self._clean_widgets()
        self._update_widgets()
        # Shutting down. Close thread
        if _thread is not None:
            _thread.stop()

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

    def tick(self, step, max, abort_check = lambda: False):
        "yield every Step secords until you get to Max or abort_check returns True"
        i = 0
        while i < max and not abort_check():
            if self.waitForAbort(step):
                break
            i += step
            yield i

    def _update_widgets(self):
        self._refresh(True)
        
        while not self.abortRequested():
            for _ in self.tick(15, 60*15):
                # TODO: somehow delay to all other plugins loaded?
                for hash, widget_ids in utils.pop_cache_queue():
                    cache_and_update(widget_ids)
                    # # wait 5s or for the skin to reload the widget
                    # # this should reduce churn at startup where widgets take too long too long show up
                    # before_update = time.time() # TODO: have .access file so we can put above update
                    # while _ in self.tick(1, 10, lambda: utils.last_read(hash) > before_update):
                    #     pass
                    # utils.log("paused queue until read {:.2} for {}".format(utils.last_read(hash)-before_update, hash[:5]), 'info') 
                    if self.abortRequested():
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
                              'info')
                    return
            else:
                if self.refresh_notification == 0:
                    notification = True
                elif self.refresh_notification == 1:
                    if not self.player.isPlayingVideo():
                        notification = True
            
            utils.log('+++++ REFRESHING AUTOWIDGETS +++++', 'info')
            refresh_paths(notify=notification and not startup)
        else:
            utils.log('+++++ AUTOWIDGET REFRESHING NOT ENABLED +++++',
                      'info')

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
    expiry, files = utils.cache_expiry(hash, widget_id)
    if files is None:
        # We had no old content so have to block and get it now
        utils.log("Blocking cache path read: {}".format(hash[:5]), "info")
        files = utils.cache_files(path, widget_id)
        
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

def cache_and_update(widget_ids):
    assert widget_ids
    seen = set()
    for widget_id in widget_ids:
        widget_def = manage.get_widget_by_id(widget_id)
        if not widget_def:
            continue
        widget_path = widget_def.get('path', {})  
        if isinstance(widget_path, dict):
            _label = widget_path['label']
            widget_path = widget_path['file']['file']
        if widget_path not in seen:
            utils.cache_files(widget_path, widget_id)
        seen.add(widget_path)
        _update_strings(widget_def)



# As soon as stop playing schedule a widget update on potentially changed widgets
# Try to guess which widgets should be updated based on which normal change after playback
class Player(xbmc.Player):
    def __init__(self):
        super(Player, self).__init__()
        self.publish = None
        self.totalTime = -1
        self.playingTime = 0
        self.info = {}

    def playing_type(self):
        """
        @return: [music|movie|episode|stream|liveTV|recordedTV|PVRradio|unknown]
        """
        # TODO: taken from callbacks plugin. have as a dependcy instead?
        substrings = ['-trailer', 'http://']
        isMovie = False
        if self.isPlayingAudio():
            return "music"
        else:
            if xbmc.getCondVisibility('VideoPlayer.Content(movies)'):
                isMovie = True
        try:
            filename = self.getPlayingFile()
        except RuntimeError:
            filename = ''
        if filename != '':
            if filename[0:3] == 'pvr':
                if xbmc.getCondVisibility('Pvr.IsPlayingTv'):
                    return 'liveTV'
                elif xbmc.getCondVisibility('Pvr.IsPlayingRecording'):
                    return 'recordedTV'
                elif xbmc.getCondVisibility('Pvr.IsPlayingRadio'):
                    return 'PVRradio'
                else:
                    for string in substrings:
                        if string in filename:
                            isMovie = False
                            break
        if isMovie:
            return "movie"
        elif xbmc.getCondVisibility('VideoPlayer.Content(episodes)'):
            # Check for tv show title and season to make sure it's really an episode
            if xbmc.getInfoLabel('VideoPlayer.Season') != "" and xbmc.getInfoLabel('VideoPlayer.TVShowTitle') != "":
                return "episode"
        elif xbmc.getCondVisibility('Player.IsInternetStream'):
            return 'stream'
        else:
            return 'unknown'


    def onPlayBackStarted(self):
        # self.getInfo()
        try:
            self.totalTime = self.getTotalTime()
        except RuntimeError:
            self.totalTime = -1
        finally:
            if self.totalTime == 0:
                self.totalTime = -1
        # self.recordPlay()

    def onPlayBackEnded(self):
        #import ptvsd; ptvsd.enable_attach(address=('127.0.0.1', 5678)); ptvsd.wait_for_attach()
        utils.log("AutoWidget onPlayBackEnded callback", 'notice')

        # Once a playback ends. 
        # TODO: We don't know it was scrobed so might not result in widget changes? Used watched status instead?
        # Work out which cached paths are most likely to change based on playback history

        # wait for a bit so scrobing can happen
        time.sleep(5) 
        for hash in utils.widgets_changed_by_watching():
            # Queue them for refresh
            utils.push_cache_queue(hash)
            utils.log("Queued cache update: {}".format(hash[:5]), 'notice')


        # Record playback in a history db so we can potentially use this for future predictions.
        try:
            tt = self.totalTime
            tp = self.playingTime
            pp = int(100 * tp / tt)
        except RuntimeError:
            pp = -1
        except OverflowError:
            pp = -1
        self.totalTime = -1.0
        self.playingTime = 0.0
        self.info = {}
        utils.save_playback_history(self.playing_type, pp)

    def onPlayBackStopped(self):
        self.onPlayBackEnded()

    def onPlayBackPaused(self):
        pass

    def onPlayBackResumed(self):
        pass

    def onPlayBackSeek(self, time, seekOffset):
        pass

    def onPlayBackSeekChapter(self, chapter):
        pass

    def onPlayBackSpeedChanged(self, speed):
        pass

    def onQueueNextItem(self):
        topic = Topic('onQueueNextItem')
        pass