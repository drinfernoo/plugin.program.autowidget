import xbmc

import sys


def log(msg, level=xbmc.LOGDEBUG):
    msg = '{}: {}'.format(sys.argv[0], msg)
    xbmc.log(msg, level)
