# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import sys
    from resources.lib.common import router

    _plugin = sys.argv[0]
    _handle = int(sys.argv[1])
    _params = sys.argv[2][1:]
    
    dispatcher = router.Router()
    dispatcher.dispatch(_plugin, _handle, _params)
