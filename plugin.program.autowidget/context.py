import xbmc

from resources.lib import manage
from resources.lib.common import utils


if __name__ == '__main__':
    utils.ensure_addon_data()

    labels = {'label': xbmc.getInfoLabel('ListItem.Label'),
              'path': xbmc.getInfoLabel('ListItem.FolderPath'),
              'is_folder': xbmc.getCondVisibility('Container.ListItem.IsFolder'),
              'content': xbmc.getInfoLabel('Container.Content')}
              
    art = {'icon': xbmc.getInfoLabel('ListItem.Icon'),
           'thumb': xbmc.getInfoLabel('ListItem.Thumb'),
           'poster': xbmc.getInfoLabel('ListItem.Art(poster)'),
           'fanart': xbmc.getInfoLabel('ListItem.Art(fanart)'),
           'banner': xbmc.getInfoLabel('ListItem.Art(banner)'),
           'landscape': xbmc.getInfoLabel('ListItem.Art(landscape)'),
           'clearlogo': xbmc.getInfoLabel('ListItem.Art(clearlogo)'),
           'clearart': xbmc.getInfoLabel('ListItem.Art(clearart)')}
    labels['art'] = art
    
    window = 'files'
    if 'video' in labels['path'].lower():
        window = 'videos'
    elif 'audio' in labels['path'].lower():
        window = 'music'
    labels['window'] = window
    
    _type = manage.add_as(labels['path'], labels['is_folder'])
    labels['target'] = _type
    group = manage.group_dialog(_type)
    if group:
        manage.add_path(group, labels)
