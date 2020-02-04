import xbmc
import xbmcaddon

import random
import time

from resources.lib import path_utils
from resources.lib.common import utils

_addon = xbmcaddon.Addon()
_monitor = xbmc.Monitor()

utils.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)
utils.log('+++++ REFRESHING EVERY {} HOURS... +++++'.format(_wait_time), level=xbmc.LOGNOTICE)

path_utils.refresh_paths()

while not _monitor.abortRequested():
    sleep_mins = 45 + int(random.random() * 30)
    try:
        if _monitor.waitForAbort(sleep_mins * 60):
            break
            
        path_utils.refresh_paths(notify=True)
    except Exception as e:
        utils.log('{}'.format(e), level=xbmc.LOGERROR)
