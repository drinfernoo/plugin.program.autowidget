import xbmcaddon
import xbmcgui


def show_window(group):
    from resources.lib import path_utils
    
    class ShortcutWindow(xbmcgui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            pass
            
        def onInit(self):
            groups = path_utils.find_defined_groups()
            group_string = 'mainmenu|{}'.format('|'.join(groups))
            
            self.setProperty('dialog.group', group)
            self.setProperty('dialog.group_list', group_string)
            
            
            
    addon_path = xbmcaddon.Addon().getAddonInfo('path').decode('utf-8')
    sw = ShortcutWindow("shortcut_window.xml",
                        addon_path,
                        defaultSkin='Default',
                        defaultRes='1080i')
    sw.doModal()
    del sw

    path_utils.refresh_paths(force=True)
