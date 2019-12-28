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
        
    def _log_params(self, _plugin, _handle, _params):
        self.params = dict(parse_qsl(_params))
        
        logstring = '{0} ({1}): '.format(_plugin, _handle)
        for param in self.params:
            logstring += '[ {0}: {1} ] '.format(param, self.params[param])

        xbmc.log(logstring, level=xbmc.LOGNOTICE)

        return self.params
        
    def dispatch(self, _plugin, _handle, _params):
        _handle = int(_handle)
        self._log_params(_plugin, _handle, _params)
        
        mode = self.params.get('mode', '')
        
        if not mode:
            from resources.lib import menu
            menu.root()
            
        elif mode == 'path':
            from resources.lib import path_utils
            
            action = self.params.get('action', '')
            group = self.params.get('group', '')
            
            if action == 'random':
                pass
                # path = path_utils.get_random_path(group)
                
        elif mode == 'group':
            action = self.params.get('action', '')
            
            if action == 'add':
                from resources.lib import path_utils
                path_utils.add_group()
            elif action == 'view':
                from resources.lib import menu
                
                group = self.params.get('group', '')
                menu.show_group(group)
            elif action == 'edit':
                from resources.lib import window
                
                group = self.params.get('group', '')
                window.show_window(group)
        
        xbmcplugin.endOfDirectory(_handle)
