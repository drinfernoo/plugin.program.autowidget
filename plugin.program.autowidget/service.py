import xbmc
import xbmcaddon
import xbmcgui

import random

from resources.lib import process
from resources.lib.common import utils

_monitor = xbmc.Monitor()
_addon = xbmcaddon.Addon()
refresh_duration = _addon.getSettingNumber('service.refresh_duration')

utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)

process.refresh_paths()

if _addon.getSettingBool('context.autowidget'):
        xbmcgui.Window(10000).setProperty('context.autowidget', 'True')

while not _monitor.abortRequested():
    sleep_mins = (45 + int(random.random() * 30)) * 60
    try:
        if _monitor.waitForAbort(sleep_mins * refresh_duration):
            break
            
        process.refresh_paths(notify=True)
    except Exception as e:
        utils.log('{}'.format(e), level=xbmc.LOGERROR)
