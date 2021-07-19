import mock_kodi
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
import pytest
import tempfile
import shutil


@pytest.fixture
def service():
    # from ..plugin.program.autowidget.resources.lib import refresh # need to ensure loaded late due to caching addon path
    # _monitor = refresh.RefreshService()
    # _monitor.waitForAbort()
    pass

@pytest.fixture
def autowidget():
    mock_kodi.MOCK = mock_kodi.MockKodi()
    mock_kodi.MOCK.SEREN_ROOT =  os.path.abspath(os.path.join(os.path.dirname(__file__),"../plugin.program.autowidget")) 
    mock_kodi.MOCK.PROFILE_ROOT = tempfile.mkdtemp()
    # os.environ['SEREN_INTERACTIVE_MODE'] = 'True'
    mock_kodi.MOCK.INTERACTIVE_MODE = True
    _addon = xbmcaddon.Addon()

            # <item library="context_add.py">
            #     <label>$ADDON[plugin.program.autowidget 32003]</label>
            #     <visible>String.IsEqual(Window(10000).Property(context.autowidget),true)</visible>
            # </item>
    mock_kodi.MOCK.DIRECTORY.register_contextmenu(
        _addon.getLocalizedString(32003),
        "plugin.program.autowidget",
        "context_add", 
        lambda : True
    )

            # <item library="context_refresh.py">
            #     <label>$ADDON[plugin.program.autowidget 32006]</label>
            #     <visible>String.Contains(ListItem.FolderPath, plugin://plugin.program.autowidget)</visible>
            # </item>
    mock_kodi.MOCK.DIRECTORY.register_contextmenu(
        _addon.getLocalizedString(32006),
        "plugin.program.autowidget",
        "context_refresh",
        lambda : True
    )
    path = "plugin://plugin.program.autowidget"
    mock_kodi.MOCK.DIRECTORY.register_action(path, "main")
    yield path
    # teardown after test
    shutil.rmtree(mock_kodi.MOCK.PROFILE_ROOT)

@pytest.fixture
def dummy():
    def dummy_folder(path):
        for i in range(1,21):
            p = "plugin://dummy/item{}".format(i)
            xbmcplugin.addDirectoryItem(
                handle=1,
                url=p,
                listitem=xbmcgui.ListItem("Dummy Item {}".format(i), path=p),
                isFolder=False
            )
        xbmcplugin.endOfDirectory(handle=1)
    path = "plugin://dummy"
    mock_kodi.MOCK.DIRECTORY.register_action(path, dummy_folder)
    return path


@pytest.fixture
def dummy2():
    "Register changed contents under same path"
    def dummy_folder(path):
        for i in range(1, 21):
            p = "plugin://dummy/item{}".format(i)
            xbmcplugin.addDirectoryItem(
                handle=1,
                url=p,
                listitem=xbmcgui.ListItem("Dummy2 Item {}".format(i), path=p),
                isFolder=False
            )
        xbmcplugin.endOfDirectory(handle=1)
    path = "plugin://dummy"
    mock_kodi.MOCK.DIRECTORY.register_action(path, dummy_folder)
    return path


@pytest.fixture
def home_with_dummy(autowidget, dummy):
    def home(path):
        url="plugin://plugin.program.autowidget/"
        xbmcplugin.addDirectoryItem(
            handle=1, 
            url=autowidget,
            listitem=xbmcgui.ListItem("AutoWidget", path=autowidget),  
            isFolder=True
        )
        # add our fake plugin 
        xbmcplugin.addDirectoryItem(
            handle=1, 
            url=dummy,
            listitem=xbmcgui.ListItem("Dummy", path=dummy),
            isFolder=True
        )
        xbmcplugin.endOfDirectory(handle=1)
    mock_kodi.MOCK.DIRECTORY.register_action("", home)


def press(keys):
    for input in keys.split(" > "):
        mock_kodi.MOCK.INPUT_QUEUE.put(input)
    for _ in keys.split(" > "):
        mock_kodi.MOCK.INPUT_QUEUE.join() # wait until the action got processed (ie until we wait for more input)


@pytest.fixture
def start_kodi():
    threading.Thread(target=mock_kodi.MOCK.DIRECTORY.handle_directory, daemon=True).start()
    time.sleep(1) # give the home menu enough time to output

@pytest.fixture
def start_kodi_with_service(start_kodi, service):
    start_kodi()
    t = threading.Thread(target=service, daemon=True).start()
    time.sleep(1) # give the home menu enough time to output
