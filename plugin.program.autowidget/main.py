import sys

from resources.lib.common import router


if __name__ == '__main__':
    _plugin, _handle = sys.argv[:1]
    _params = sys.argv[2][1:]
    
    router.dispatch(_plugin, _handle, _params)
