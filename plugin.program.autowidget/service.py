import xbmc
import xbmcaddon

import time

from resources.lib import path_utils
from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_monitor = xbmc.Monitor()
_wait_time = int(_addon.getSetting('service.wait_time'))

utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)
utils.log('+++++ REFRESHING EVERY {} HOURS... +++++'.format(_wait_time), level=xbmc.LOGNOTICE)

utils.ensure_addon_data()
path_utils.refresh_paths()

while not _monitor.abortRequested():
    try:
        if _monitor.waitForAbort(_wait_time * 60 * 60):
            break
            
        path_utils.refresh_paths(notify=True)
    except Exception as e:
        utils.log('{}'.format(e), level=xbmc.LOGERROR)
