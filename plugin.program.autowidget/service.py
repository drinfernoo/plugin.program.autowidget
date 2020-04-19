import xbmc
import xbmcaddon
import xbmcgui

import random

from resources.lib import refresh
from resources.lib import manage
from resources.lib.common import utils

_properties = ['context.autowidget']

class AutoWidgetService(xbmc.Monitor):

    def __init__(self):
        utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)
        utils.ensure_addon_data()
        self._update_properties()
        self._update_widgets()

    def onSettingsChanged(self):
        self._update_properties()

    def _reload_settings(self):
        self.refresh_enabled = utils.getSettingInt('service.refresh_enabled')
        self.refresh_duration = utils.getSettingNumber('service.refresh_duration')
        self.refresh_notification = utils.getSettingInt('service.refresh_notification')

    def _update_properties(self, window=10000):
        self._addon = xbmcaddon.Addon()

        for property in _properties:
            setting = self._addon.getSetting(property)
            utils.log('{}: {}'.format(property, setting))
            if setting is not None:
                xbmcgui.Window(window).setProperty(property, setting)
                utils.log('Property {0} set'.format(property))
            else:
                xbmcgui.Window(window).clearProperty(property)
                utils.log('Property {0} cleared'.format(property))

        self._reload_settings()
        
    def _refresh(self):
        if self.refresh_enabled in [0, 1]:
            notification = False
            if self.refresh_enabled == 1:
                if _player.isPlayingVideo():
                    utils.log('+++++ PLAYBACK DETECTED, SKIPPING AUTOWIDGET REFRESH +++++',
                              level=xbmc.LOGNOTICE)
                    return
            else:
                if self.refresh_notification == 0:
                    notification = True
                elif self.refresh_notification == 1:
                    if not _player.isPlayingVideo():
                        notification = True
            
            utils.log('+++++ REFRESHING AUTOWIDGETS +++++', level=xbmc.LOGNOTICE)
            refresh.refresh_paths(notify=notification)
        else:
            utils.log('+++++ AUTOWIDGET REFRESHING NOT ENABLED +++++',
                      level=xbmc.LOGNOTICE)

    def _update_widgets(self):
        self._refresh()
        
        while not self.abortRequested():
            if self.waitForAbort(60 * 15):
                break

            if not self._refresh():
                continue


_player = xbmc.Player()
_monitor = AutoWidgetService()
_monitor.waitForAbort()
