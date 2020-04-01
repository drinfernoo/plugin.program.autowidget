import xbmc

from resources.lib import manage
from resources.lib.common import migrate
from resources.lib.common import utils

_windows = {'programs':     ['program', 'script'],
            'addonbrowser': ['addon',   'addons'],
            'music':        ['audio',   'music'],
            'pictures':     ['image',   'picture'],
            'videos':       ['video',   'videos']}


def _get_path(labels):
    _path = xbmc.getInfoLabel('ListItem.FolderPath')
    if _path != 'addons://user/':
        _path = _path.replace('addons://user/', 'plugin://')
    labels['path'] = _path
    
    return labels
    
    
def _get_art(labels):
    labels['art'] = {i: xbmc.getInfoLabel('ListItem.Art({})'.format(i))
                        for i in ['poster', 'fanart', 'banner', 'landscape',
                                  'clearlogo', 'clearart']}
    labels['art'].update({i: xbmc.getInfoLabel('ListItem.{}'
                                               .format(i.capitalize()))
                             for i in ['icon', 'thumb']})
                             
    return labels
    
    
def _get_info(labels):
    labels['info'] = {'plot': xbmc.getInfoLabel('ListItem.Plot')}
    
    return labels
    

def _get_window(labels):
    _path = labels['path'].lower()
    for _key in _windows:
        if any(i in _path for i in _windows[_key]):
            labels['window'] = _key
            
    return labels
    

if __name__ == '__main__':
    utils.ensure_addon_data()
    migrate.migrate_groups()

    labels = {'label': xbmc.getInfoLabel('ListItem.Label'),
              'is_folder': xbmc.getCondVisibility('Container.ListItem.IsFolder'),
              'content': xbmc.getInfoLabel('Container.Content')}
              
    labels = _get_path(labels)
    labels = _get_art(labels)
    labels = _get_info(labels)
    labels = _get_window(labels)
    
    manage.add_from_context(labels)
