import xbmc
import xbmcaddon
import xbmcgui

import ast
import codecs
import io
import json
import os
import re
import shutil
import sys
import time
import unicodedata

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
                
                
def wipe(folder=_addon_path):
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', _addon.getLocalizedString(32065))
    
    if choice:
        shutil.rmtree(folder)


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
           'landscape': '',
           'banner': banner_path if os.path.exists(banner_path) else '',
           'thumb': '',
           'clearart': '',
           'clearlogo': ''}
    
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
        
        
def update_container(_type):
    xbmc.executebuiltin('Container.Refresh()')
    if _type == 'shortcut':
        xbmc.executebuiltin('UpdateLibrary(video,AutoWidget)')

        
def prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='\t')


def get_valid_filename(s):
    s = str(s).strip().replace(' ', '_')
    s = unicodedata.normalize('NFKD', s.decode('utf-8'))
    return re.sub(r'(?u)[^-\w.]', '', s)
    
    
def get_unique_id(key):
    return get_valid_filename('{}-{}'.format(key, time.time()).lower())
    
    
def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.items()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
        
    return input


def remove_file(file):
    if os.path.exists(file):
        try:
            os.remove(file)
        except Exception as e:
            log('Could not remove {}: {}'.format(file, e),
                level=xbmc.LOGERROR)


def read_file(file):
    content = None
    if os.path.exists(file):
        with io.open(os.path.join(_addon_path, file), 'r', encoding='utf-8') as f:
            try:
                content = f.read()
            except Exception as e:
                log('Could not read from {}: {}'.format(file, e),
                    level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)
        
    return content
                      

def write_file(file, content):
    with open(file, 'w') as f:
        try:
            f.write(content)
            return True
        except Exception as e:
            log('Could not write to {}: {}'.format(file, e),
                level=xbmc.LOGERROR)
                
    return False
    
    
def read_json(file):
    data = None
    if os.path.exists(file):
        with codecs.open(os.path.join(_addon_path, file), 'r', encoding='utf-8') as f:
            try:
                content = f.read().encode('utf-8')
                data = json.loads(content)
            except Exception as e:
                log('Could not read JSON from {}: {}'.format(file, e),
                    level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)
        
    return convert(data)
    
    
def write_json(file, content):
    with codecs.open(file, 'w', encoding='utf-8') as f:
        try:
            json.dump(content, f, indent=4)
        except Exception as e:
            log('Could not write to {}: {}'.format(file, e),
                level=xbmc.LOGERROR)


def read_xml(file):
    xml = None
    if os.path.exists(file):
        try:
            xml = ElementTree.parse(file).getroot()
        except Exception as e:
            log('Could not read XML from {}: {}'.format(file, e),
                level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)
        
    return xml
    
    
def write_xml(file, content):
    prettify(content)
    tree = ElementTree.ElementTree(content)
    
    try:
        tree.write(file)
    except:
        utils.log('Could not write to {}: {}'.format(file, e),
                  level=xbmc.LOGERROR)