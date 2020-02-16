import xbmc
import xbmcaddon
import xbmcgui

import os
import shutil
import sys

_addon = xbmcaddon.Addon()
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_root = xbmc.translatePath(_addon.getAddonInfo('path'))
_art_path = os.path.join(_addon_root, 'resources', 'media')
_shortcuts = xbmcaddon.Addon('script.skinshortcuts')
_shortcuts_path = xbmc.translatePath(_shortcuts.getAddonInfo('profile'))


def log(msg, level=xbmc.LOGDEBUG):
    msg = '{}: {}'.format(sys.argv[0], msg)
    xbmc.log(msg, level)


def ensure_addon_data():
    if not os.path.exists(_addon_path):
        os.makedirs(_addon_path)
    
    
def get_skin_string(string):
    return xbmc.getInfoLabel('Skin.String({})'.format(string))
    
    
def get_art(filename):
    image_path = os.path.join(_art_path, filename)
    
    return image_path if os.path.exists(image_path) else ''
    
    
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


def clean_old_widgets():
    w = 0
    for file in os.listdir(_addon_path):
        if not file.endswith('.auto'):
            continue
        
        found = False
        ref_path = os.path.join(_addon_path, file)
            
        for shortcut in os.listdir(_shortcuts_path):
            file_path = os.path.join(_shortcuts_path, shortcut)
            with open(file_path, 'r') as f:
                content = f.read()
                
            if file[:-5] in content:
                found = True
                w += 1
                break
        
        if not found:
            try:
                os.remove(ref_path)
            except Exception as e:
                log('Could not remove old widget reference: {}'
                    .format(file), level=xbmc.LOGNOTICE)
                log('{}'.format(e), level=xbmc.LOGERROR)
    log('{} stale widget references removed.'.format(w))
                
                
def clean_old_strings():
    dialog = xbmcgui.Dialog()
    skin = xbmc.translatePath('special://skin/')
    skin_id = os.path.basename(os.path.normpath(skin))
    skin_addon = xbmcaddon.Addon(skin_id)
    skin_path = xbmc.translatePath(skin_addon.getAddonInfo('profile'))
    skin_settings = os.path.join(skin_path, 'settings.xml')

    new_lines = []    
    with open(skin_settings, 'r') as f:
        for line in f.readlines():
            if '\"' in line:
                setting = line.split('\"')[1]
                if setting.startswith('autowidget'):
                    id = setting[11:-5] if setting.endswith('-path') else setting[11:-6]
                    ref_name = '{}.auto'.format(id)
                    ref_path = os.path.join(_addon_path, ref_name)
                    if os.path.exists(ref_path):
                       new_lines.append(line) 
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
    
    temp_file = os.path.join(_addon_path, 'temp_settings.xml')
    with open(temp_file, 'w') as f:
        for line in new_lines:
            f.write(line)
    
    with open(temp_file, 'r') as f:
        log(f.read())
    
    shutil.copy(temp_file, skin_settings)
    os.remove(temp_file)
    
    close = dialog.yesno('AutoWidget', 'In order to successfully remove old references, Kodi needs to be restarted. Would you like to close Kodi now?')
    if close:
        os._exit(1)
