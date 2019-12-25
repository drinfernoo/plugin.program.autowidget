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

        xbmc.log(logstring, level=xbmc.LOGNOTICE)

        return self.params
        
    def dispatch(self, handle, paramstring):
        self.params = dict(parse_qsl(paramstring))
        self._log_params()
        
        mode = self.params.get('mode', '')
        
        if not mode:
            from resources.lib.gui import main_menu
            self.route = main_menu.MainMenu()
            
        elif mode == 'path':
            from resources.lib import path_utils
            
            action = self.params.get('action', '')
            
            if action == 'add':
                path_utils.Path().add()
        elif mode == 'window':
            from resources.lib import window
            window.show_window()
            
        if self.route:
            self.route.show_menu()
        
        xbmcplugin.setContent(handle, 'files')
        xbmcplugin.endOfDirectory(handle)
