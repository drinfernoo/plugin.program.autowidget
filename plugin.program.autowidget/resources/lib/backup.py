import xbmc
import xbmcgui
import xbmcvfs

import os

import zipfile

from resources.lib.common import utils

backup_location = xbmc.translatePath(utils.get_setting('backup.location'))


def location():
    dialog = xbmcgui.Dialog()
    folder = dialog.browse(0, 'Choose Backup Location', 'files', defaultt=backup_location)
    
    if folder:
        utils.set_setting('backup.location', folder)


def backup():
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', 'Do you want to backup your groups? This will not backup any widgets defined in the skin.')
    
    if choice:
        filename = dialog.input('Backup Name')
        
        if not filename:
            dialog.notification('AutoWidget', 'Backup Cancelled.')
            return
            
        if not os.path.exists(backup_location):
            try:
                os.makedirs(backup_location)
            except Exception as e:
                utils.log(str(e), xbmc.LOGERROR)
                dialog.notification('AutoWidget', 'Could not create backup location.')
                return
                
        files = [x for x in os.listdir(utils._addon_path) if x.endswith('.group')]
        if len(files) == 0:
            dialog.notification('AutoWidget', 'No groups have been defined to backup.')
            return
            
        path = os.path.join(backup_location, '{}.zip'.format(filename.replace('.zip', '')))
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zip:
            for file in files:
                zip.write(os.path.join(utils._addon_path, file), file)
                
                
def restore():
    dialog = xbmcgui.Dialog()
    backup = dialog.browse(1, 'Choose Backup to Restore', 'files', mask='.zip', defaultt=backup_location)
    
    if backup.endswith('zip'):
        with zipfile.ZipFile(backup, 'r') as zip:
            info = zip.infolist()
            choice = dialog.yesno('AutoWidget', 'Would you like to restore {} groups from this backup?'.format(len(info)))
            
            if choice:
                overwrite = dialog.yesno('AutoWidget', 'Would you like to erase your current groups before restoring?')
                
                if overwrite:
                    files = [x for x in os.listdir(utils._addon_path) if x.endswith('.group')]
                    for file in files:
                        utils.remove_file(file)
                zip.extractall()
            else:
                dialog.notification('AutoWidget', 'Restore Cancelled.')
    else:
        dialog.notification('AutoWidget', 'Restore Cancelled.')
        return
