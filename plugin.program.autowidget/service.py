import xbmc
import xbmcaddon
import xbmcgui

import random

from resources.lib import process
from resources.lib.common import utils

_properties = ['context.autowidget']


class AutoWidgetService(xbmc.Monitor):

    def __init__(self):
        utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)
        self._update_properties()
        self._update_widgets()

    def onSettingsChanged(self):
        self._update_properties()

    def _reload_settings(self):
        self.refresh_enabled = self._addon.getSettingBool('service.refresh_enabled')
        self.refresh_duration = self._addon.getSettingNumber('service.refresh_duration')

    def _update_properties(self, window=10000):
        self._addon = xbmcaddon.Addon()

        for property in _properties:
            utils.log('{}: {}'.format(property, xbmcaddon.Addon().getSetting(property)))
            if self._addon.getSetting(property) == 'true':
                xbmcgui.Window(window).setProperty(property, 'true')
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

                if self.refresh_enabled:
                    process.refresh_paths(notify=True)
                else:
                    utils.log('+++++ AUTOWIDGET SERVICE NOT ENABLED +++++', level=xbmc.LOGNOTICE)
        except Exception as e:
            utils.log(e, level=xbmc.LOGERROR)


_monitor = AutoWidgetService()
_monitor.waitForAbort()
