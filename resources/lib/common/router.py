import xbmc
import xbmcplugin

import six
import sys

if six.PY3:
    from urllib.parse import parse_qsl
elif six.PY2:
    from urlparse import parse_qsl
    

class Router:
    def __init__(self):
        self.route = None
        self.params = {}
        
    def _log_params(self):
        _plugin = sys.argv[0]
        
        logstring = '{0}: '.format(_plugin)
        for param in self.params:
            logstring += '[ {0}: {1} ] '.format(param, self.params[param])

        xbmc.log(logstring, level=xbmc.LOGDEBUG)

        return self.params
        
    def dispatch(self, handle, paramstring):
        self.params = dict(parse_qsl(paramstring))
        self._log_params()
        
        
        
        xbmcplugin.setContent(handle, 'files')
        xbmcplugin.endOfDirectory(handle)