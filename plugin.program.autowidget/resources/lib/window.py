import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import path_utils


def show_window(group):
    class ShortcutWindow(xbmcgui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            pass
            
        def onInit(self):
            self.setProperty('dialog.group', group)
            
        def close(self):
            path_utils.convert_paths()
            super().close()
                
    addon_path = xbmcaddon.Addon().getAddonInfo('path').decode('utf-8')
    sw = ShortcutWindow("shortcut_window.xml",
                        addon_path,
                        defaultSkin='Default',
                        defaultRes='1080i')
    sw.doModal()
    del sw
