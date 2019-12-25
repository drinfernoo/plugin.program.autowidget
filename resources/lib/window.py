import xbmc
import xbmcaddon
import xbmcgui


def show_window():
    class ShortcutWindow(xbmcgui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            pass
                
    addon_path = xbmcaddon.Addon().getAddonInfo(‘path’).decode(‘utf-8’)
    sw = ShortcutWindow("shortcut_window.xml",
                        addon_path,
                        defaultSkin='Default',
                        defaultRes='1080i')
    sw.doModal()
    del sw
