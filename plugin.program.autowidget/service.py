import xbmc
import xbmcaddon
import xbmcgui

import random

from resources.lib import process
from resources.lib.common import utils

_addon = xbmcaddon.Addon()

properties = ['context.autowidget']
refresh_enabled = _addon.getSettingBool('service.refresh_enabled')
refresh_duration = _addon.getSettingNumber('service.refresh_duration')


class PropertiesUpdater(xbmc.Monitor):
    
    def __init__(self):
        utils.log('+++++ STARTING AUTOWIDGET PROPERTY MONITOR +++++',
                  level=xbmc.LOGNOTICE)
        self._update_properties()
    
    def onSettingsChanged(self):
        self._update_properties()
            
    def _update_properties(self):
        for property in properties:
            self.toggle_property(property)
            
    def toggle_property(self, property, window=10000):
        value = _addon.getSetting(property)
        utils.log('{} = {}'.format(property, value))

        if value == 'true':
            xbmcgui.Window(window).setProperty(property, value)
            utils.log('Property {} set to {} on {}'.format(property, value,
                                                           window))
        elif value == 'false':
            xbmcgui.Window(window).clearProperty(property)
            utils.log('Property {} cleared from {}'.format(property, window))


_monitor = xbmc.Monitor()
_properties_monitor = PropertiesUpdater()

if refresh_enabled:
    utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)

    process.refresh_paths()
    while not _monitor.abortRequested():
        sleep_mins = (45 + int(random.random() * 30)) * 60
        try:
            if _monitor.waitForAbort(sleep_mins * refresh_duration):
                break
                
            process.refresh_paths(notify=True)
        except Exception as e:
            utils.log(e, level=xbmc.LOGERROR)
else:
    utils.log('+++++ AUTOWIDGET SERVICE NOT ENABLED +++++', level=xbmc.LOGNOTICE)
    