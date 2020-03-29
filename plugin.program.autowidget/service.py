import xbmc
import xbmcaddon
import xbmcgui

import random

from resources.lib import convert
from resources.lib.common import utils

_properties = ['context.autowidget', 'context.advanced']
_player = xbmc.Player()

class AutoWidgetService(xbmc.Monitor):

    def __init__(self):
        utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)
        self._update_properties()
        self._update_widgets()

    def onSettingsChanged(self):
        self._update_properties()

    def _reload_settings(self):
        self.refresh_enabled = self._addon.getSettingInt('service.refresh_enabled')
        self.refresh_duration = self._addon.getSettingNumber('service.refresh_duration')
        self.refresh_notification = self._addon.getSettingInt('service.refresh_notification')

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

    def _update_widgets(self):
        try:
            while not self.abortRequested():
                delay = (45 + int(random.random() * 30)) * 60 
                if self.waitForAbort(delay * self.refresh_duration):
                    break

                if self.refresh_enabled in [0, 1]:
                    notification = False
                    if self.refresh_enabled == 1:
                        if _player.isPlayingVideo():
                            utils.log('+++++ PLAYBACK DETECTED, SKIPPING AUTOWIDGET REFRESH +++++', level=xbmc.LOGNOTICE)
                            continue
                    else:
                        if self.refresh_notification == 0:
                            notification = True
                        elif self.refresh_notification == 1:
                            if not _player.isPlayingVideo():
                                notification = True
                    
                    utils.log('+++++ REFRESHING AUTOWIDGETS +++++', level=xbmc.LOGNOTICE)
                    convert.refresh_paths(notify=notification)
                else:
                    utils.log('+++++ AUTOWIDGET REFRESHING NOT ENABLED +++++', level=xbmc.LOGNOTICE)
        except Exception as e:
            utils.log(e, level=xbmc.LOGERROR)


_monitor = AutoWidgetService()
_monitor.waitForAbort()
