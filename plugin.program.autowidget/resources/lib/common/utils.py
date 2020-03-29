import xbmc
import xbmcaddon
import xbmcgui

import os
import re
import shutil
import sys

from xml.dom import minidom
from xml.etree import ElementTree

_addon = xbmcaddon.Addon()
_addon_id = _addon.getAddonInfo('id')
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_root = xbmc.translatePath(_addon.getAddonInfo('path'))
_art_path = os.path.join(_addon_root, 'resources', 'media')
if xbmc.getCondVisibility('System.HasAddon(script.skinshortcuts)'):
    _shortcuts = xbmcaddon.Addon('script.skinshortcuts')
    _shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))
else:
    _shortcuts_path = ''


def log(msg, level=xbmc.LOGDEBUG):
    msg = '{}: {}'.format(_addon_id, msg)
    xbmc.log(msg, level)


def ensure_addon_data():
    for path in [_addon_path, _shortcuts_path]:
        if path:
            if not os.path.exists(path):
                os.makedirs(path)


def set_skin_string(string, value):
    xbmc.executebuiltin('Skin.SetString({},{})'.format(string, value))
    
    
def get_skin_string(string):
    return xbmc.getInfoLabel('Skin.String({})'.format(string))
    
    
def get_art(filename):
    icon_path = os.path.join(_art_path, filename)
    poster_path = os.path.join(_art_path, 'poster', filename)
    fanart_path = os.path.join(_art_path, 'fanart', filename)
    banner_path = os.path.join(_art_path, 'banner', filename)
    
    art = {'icon': icon_path if os.path.exists(icon_path) else '',
           'poster': poster_path if os.path.exists(poster_path) else '',
           'fanart': fanart_path if os.path.exists(fanart_path) else '',
           'landscape': fanart_path if os.path.exists(fanart_path) else '',
           'banner': banner_path if os.path.exists(banner_path) else ''}
    
    return art
    
    
def get_active_window():
    xml_file = xbmc.getInfoLabel('Window.Property(xmlfile)').lower()

    if xbmc.getCondVisibility('Window.IsMedia()'):
        return 'media'
    elif 'dialog' in xml_file:
        return 'dialog'
    elif xbmc.getCondVisibility('Window.IsActive(home)'):
        return 'home'
    else:
        pass

        
def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)
