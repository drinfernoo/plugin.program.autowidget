from mock_kodi import MOCK
import os
import threading
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
from mock_kodi import makedirs
import runpy
from urllib.parse import urlparse
import sys
import doctest
import time


def execute_callback():
    runpy.run_module('foobar', run_name='__main__')

def start_service():
    from resources.lib import refresh
    _monitor = refresh.RefreshService()
    _monitor.waitForAbort()

def setup():
    #item.setInfo('video', def_info)
    #item.setMimeType(def_info.get('mimetype', ''))
    #item.setArt(def_art)
    #item.addContextMenuItems(def_cm)
    _addon = xbmcaddon.Addon()
    # create dirs
    _addon_id = _addon.getAddonInfo('id')
    _addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
    _addon_root = xbmc.translatePath(_addon.getAddonInfo('path'))
    makedirs(_addon_path, exist_ok=True)
            


    # load the context menus
    #_addon._config 

            # <item library="context_add.py">
            #     <label>$ADDON[plugin.program.autowidget 32003]</label>
            #     <visible>String.IsEqual(Window(10000).Property(context.autowidget),true)</visible>
            # </item>
    MOCK.DIRECTORY.register_contextmenu(
        _addon.getLocalizedString(32003),
        "plugin.program.autowidget",
        "context_add", 
        lambda : True
    )

            # <item library="context_refresh.py">
            #     <label>$ADDON[plugin.program.autowidget 32006]</label>
            #     <visible>String.Contains(ListItem.FolderPath, plugin://plugin.program.autowidget)</visible>
            # </item>
    MOCK.DIRECTORY.register_contextmenu(
        _addon.getLocalizedString(32006),
        "plugin.program.autowidget",
        "context_refresh", 
        lambda : True
    )

    MOCK.DIRECTORY.register_action("plugin://plugin.program.autowidget", "main")

    def home(path):
        xbmcplugin.addDirectoryItem(
            handle=1, 
            url="plugin://plugin.program.autowidget/", 
            listitem=xbmcgui.ListItem("AutoWidget"),  
            isFolder=True
        )
        # add our fake plugin    
        xbmcplugin.addDirectoryItem(
            handle=1, 
            url="plugin://dummy/", 
            listitem=xbmcgui.ListItem("Dummy"),
            isFolder=True
        )
        xbmcplugin.endOfDirectory(handle=1)
    MOCK.DIRECTORY.register_action("", home)

    def dummy_folder(path):
        for i in range(1,20):
            p = "plugin://dummy/item{}".format(i)
            xbmcplugin.addDirectoryItem(
                handle=1, 
                url=p, 
                listitem=xbmcgui.ListItem("Dummy Item {}".format(i), path=p),
                isFolder=False
            )
        xbmcplugin.endOfDirectory(handle=1)
    MOCK.DIRECTORY.register_action("plugin://dummy", dummy_folder)
    #t = threading.Thread(target=start_service).start()

def press(keys):
    MOCK.INPUT_QUEUE.put(keys)
    MOCK.INPUT_QUEUE.join()

def test_add_widget_group():
    """
    >>> t = threading.Thread(target=MOCK.DIRECTORY.handle_directory, daemon = True)
    >>> t.start(); time.sleep(1)
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) AutoWidget
     2) Dummy
    <BLANKLINE>
    Enter Action Number

    >>> press("c2")
     1) Add to AutoWidget Group
    <BLANKLINE>

    >>> press(1)
    Add as
    0) Shortcut
    1) Widget
    2) Clone as Shortcut Group
    3) Explode as Widget Group

    >>> press(1)
    Widget
    Choose a Group
    0) Create New Widget Group

    >>> press(0)
    Create New Widget Group
    Name for Group

    >>> press("Widget1")
    Choose a Group
    0) Create New Widget Group
    1) Widget1

    >>> press(1)
    Widget1
    Widget Label

    >>> press("My Label")
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) AutoWidget
     2) Dummy
    <BLANKLINE>
    Enter Action Number

    Ensure the Widget is there
    >>> press(1)


    """

if __name__ == '__main__':
    os.environ['SEREN_INTERACTIVE_MODE'] = 'True'
    setup()
    doctest.testmod()
