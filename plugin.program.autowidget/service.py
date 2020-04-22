import xbmc

from resources.lib import refresh

_monitor = refresh.RefreshService()
_monitor.waitForAbort()
