import xbmc
import xbmcaddon
import xbmcgui


def show_window(group):
    class ShortcutWindow(xbmcgui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            pass
            
        def onInit(self):
            self.setProperty('dialog.group', group)
            
    addon_path = xbmcaddon.Addon().getAddonInfo('path').decode('utf-8')
    sw = ShortcutWindow("shortcut_window.xml",
                        addon_path,
                        defaultSkin='Default',
                        defaultRes='1080i')
    sw.doModal()
    del sw
    
    from resources.lib import path_utils
    path_utils.convert_paths()
