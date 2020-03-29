import xbmc

from resources.lib import manage
from resources.lib.common import utils


if __name__ == '__main__':
    utils.ensure_addon_data()

    labels = {'label': xbmc.getInfoLabel('ListItem.Label'),
              'is_folder': xbmc.getCondVisibility('Container.ListItem.IsFolder'),
              'content': xbmc.getInfoLabel('Container.Content')}
              
    path = xbmc.getInfoLabel('ListItem.FolderPath')
    if path != 'addons://user/':
        path = path.replace('addons://user/', 'plugin://')
    labels['path'] = path
              
    art = {'icon': xbmc.getInfoLabel('ListItem.Icon'),
           'thumb': xbmc.getInfoLabel('ListItem.Thumb'),
           'poster': xbmc.getInfoLabel('ListItem.Art(poster)'),
           'fanart': xbmc.getInfoLabel('ListItem.Art(fanart)'),
           'banner': xbmc.getInfoLabel('ListItem.Art(banner)'),
           'landscape': xbmc.getInfoLabel('ListItem.Art(landscape)'),
           'clearlogo': xbmc.getInfoLabel('ListItem.Art(clearlogo)'),
           'clearart': xbmc.getInfoLabel('ListItem.Art(clearart)')}
    labels['art'] = art
    
    labels['info'] = {'plot': xbmc.getInfoLabel('ListItem.Plot')}
    
    window = 'files'
    if any(i in labels['path'].lower() for i in ['addon', 'addons']):
        window = 'addonbrowser'
    elif any(i in labels['path'].lower() for i in ['audio', 'music']):
        window = 'music'
    elif any(i in labels['path'].lower() for i in ['image', 'picture']):
        window = 'pictures'
    elif any(i in labels['path'].lower() for i in ['video', 'videos']):
        window = 'videos'
    labels['window'] = window
    
    _type = manage.add_as(labels['path'], labels['is_folder'])
    if _type:
        labels['target'] = _type
        group = manage.group_dialog(_type)
        if group:
            manage.add_path(group, labels)
