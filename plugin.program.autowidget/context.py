import xbmc

if __name__ == '__main__':
    import web_pdb; web_pdb.set_trace()
    label = xbmc.getInfoLabel('ListItem.Label')
    path = xbmc.getInfoLabel('Container.ListItem.FolderPath')
    icon = xbmc.getInfoLabel('ListItem.Icon')
    
    xbmc.executebuiltin(('RunPlugin(plugin://plugin.program.autowidget/'
                                   '?mode=manage'
                                   '&action=add_path_to_group'
                                   '&label={}'
                                   '&path={}'
                                   '&icon={})').format(label, path, icon))
    