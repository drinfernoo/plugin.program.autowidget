import sys

from resources.lib.common import router
from resources.lib.common import utils


if __name__ == "__main__":
    _handle = int(sys.argv[1])
    _params = sys.argv[2][1:]

    with utils.timing(_params):
        router.dispatch(_handle, _params)
