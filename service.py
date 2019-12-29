import xbmc
import xbmcaddon

from resources.lib import path_utils

_addon = xbmcaddon.Addon()
_monitor = xbmc.Monitor()
xbmc.log('+++++ STARTING AUTOWIDGET SERVICE +++++', level=xbmc.LOGNOTICE)

wait_time = _addon.getSettingInt('service.wait_time')

while not _monitor.abortRequested():
    try:
        if _monitor.waitForAbort(wait_time):
            break
        
        path_utils.inject_paths()
    except Exception as e:
        xbmc.log('{}'.format(e), level=xbmc.LOGERROR)
