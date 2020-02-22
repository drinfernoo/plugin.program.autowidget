import xbmc

import sys

if __name__ == '__main__':
    label = xbmc.getInfoLabel('ListItem.Label')
    path = xbmc.getInfoLabel('Container.ListItem.FolderPath').replace('&', '%26')
    icon = xbmc.getInfoLabel('ListItem.Icon')
    
    xbmc.executebuiltin(('RunPlugin(plugin://plugin.program.autowidget/'
                                   '?mode=manage'
                                   '&action=add_path_to_group'
                                   '&label={}'
                                   '&path={}'
                                   '&icon={})').format(label, path, icon))
    