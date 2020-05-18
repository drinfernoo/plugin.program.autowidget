import xbmc
import xbmcgui
import xbmcvfs

import os

import zipfile

from resources.lib.common import utils

backup_location = xbmc.translatePath(utils.get_setting('backup.location'))


def location():
    dialog = xbmcgui.Dialog()
    folder = dialog.browse(0, utils.get_string(32091), 'files', defaultt=backup_location)
    
    if folder:
        utils.set_setting('backup.location', folder)


def backup():
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', utils.get_string(32094))
    
    if choice:
        filename = dialog.input(utils.get_string(32095))
        
        if not filename:
            dialog.notification('AutoWidget', utils.get_string(32096))
            return
            
        if not os.path.exists(backup_location):
            try:
                os.makedirs(backup_location)
            except Exception as e:
                utils.log(str(e), level=xbmc.LOGERROR)
                dialog.notification('AutoWidget', utils.get_string(32097))
                return
                
        files = [x for x in os.listdir(utils._addon_path) if x.endswith('.group')]
        if len(files) == 0:
            dialog.notification('AutoWidget', utils.get_string(32068))
            return
            
        path = os.path.join(backup_location, '{}.zip'.format(filename.replace('.zip', '')))
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zip:
            for file in files:
                zip.write(os.path.join(utils._addon_path, file), file)
                
                
def restore():
    dialog = xbmcgui.Dialog()
    backup = dialog.browse(1, utils.get_string(32098), 'files', mask='.zip', defaultt=backup_location)
    
    if backup.endswith('zip'):
        with zipfile.ZipFile(backup, 'r') as zip:
            info = zip.infolist()
            choice = dialog.yesno('AutoWidget', utils.get_string(32099).format(len(info), 's' if len(info) > 1 else ''))
            
            if choice:
                overwrite = dialog.yesno('AutoWidget', utils.get_string(32100))
                
                if overwrite:
                    files = [x for x in os.listdir(utils._addon_path) if x.endswith('.group')]
                    for file in files:
                        utils.remove_file(file)
                zip.extractall(utils._addon_path)
            else:
                dialog.notification('AutoWidget', utils.get_string(32101))
    else:
        dialog.notification('AutoWidget', utils.get_string(32101))
        return
