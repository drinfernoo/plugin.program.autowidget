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
    from ..plugin.program.autowidget.resources.lib import refresh # need to ensure loaded late due to caching addon path
    _monitor = refresh.RefreshService()
    _monitor.waitForAbort()

@pytest.fixture
def autowidget():
    mock_kodi.MOCK = mock_kodi.MockKodi()
    mock_kodi.MOCK.SEREN_ROOT =  os.path.abspath(os.path.join(os.path.dirname(__file__),"../plugin.program.autowidget")) 
    mock_kodi.MOCK.PROFILE_ROOT = tempfile.mkdtemp()
    #os.environ['SEREN_INTERACTIVE_MODE'] = 'True'
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
            listitem=xbmcgui.ListItem("Dummy",path=dummy),
            isFolder=True
        )
        xbmcplugin.endOfDirectory(handle=1)
    mock_kodi.MOCK.DIRECTORY.register_action("", home)

def press(keys):
    mock_kodi.MOCK.INPUT_QUEUE.put(keys)
    mock_kodi.MOCK.INPUT_QUEUE.join() # wait until the action got processed (ie until we wait for more input)

def start_kodi(use_service=True):
    threading.Thread(target=mock_kodi.MOCK.DIRECTORY.handle_directory, daemon = True).start()
    time.sleep(1) # give the home menu enough time to output
    if use_service:
        t = threading.Thread(target=service, daemon = True).start()
        time.sleep(1) # give the home menu enough time to output


def test_add_widget_cycling():
    """
    >>> getfixture("home_with_dummy") # TODO:
    >>> start_kodi(False)
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) AutoWidget
     2) Dummy
    -------------------------------
    Enter Action Number

    >>> press("c2")
     1) Add to AutoWidget Group

    >>> press("Add to AutoWidget Group")
    Add as
    0) Shortcut
    1) Widget
    2) Clone as Shortcut Group
    3) Explode as Widget Group

    >>> press("Widget")
    Choose a Group
    0) Create New Widget Group

    >>> press("Create New Widget Group")
    Name for Group

    >>> press("Widget1")
    Choose a Group
    0) Create New Widget Group
    1) Widget1

    >>> press("Widget1")
    Widget Label

    >>> press("My Label")
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) AutoWidget
     2) Dummy
    -------------------------------
    Enter Action Number

    >>> press("AutoWidget")
    LOGINFO - plugin.program.autowidget: [ root ]
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) My Groups
     2) Active Widgets
     3) Tools
    -------------------------------
    Enter Action Number
    
    >>> press("My Groups")
    LOGINFO - plugin.program.autowidget: [ mode: group ]
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) Widget1
    -------------------------------
    Enter Action Number

    >>> press("Widget1")
    LOGINFO - plugin.program.autowidget: [ mode: group ][ group: widget1-... ]
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) My Label
     2) Widget1 (Static)
     3) Widget1 (Cycling)
     4) Widget1 (Merged)
    -------------------------------
    Enter Action Number

    >>> press("Widget1 (Cycling)")
    LOGINFO - plugin.program.autowidget: [ mode: path ][ action: cycling ][ group: widget1-... ]
    Choose an Action
    0) Random Path
    1) Next Path

    >>> press("Next Path")
    LOGINFO - plugin.program.autowidget: Empty cache 0B (exp:-1 day, ...
    LOGINFO - plugin.program.autowidget: Blocking cache path read: ...
    LOGINFO - plugin.program.autowidget: Wrote cache ...
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) Dummy Item 1
     2) Dummy Item 2
     3) Dummy Item 3
     4) Dummy Item 4
    ...
     20) Dummy Item 20
    -------------------------------
    Enter Action Number

    """

def test_add_widget_merged():
    """
    >>> getfixture("home_with_dummy") # TODO:
    >>> start_kodi(False)
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) AutoWidget
     2) Dummy
    -------------------------------
    Enter Action Number
    """

# if __name__ == '__main__':
#     autowidget()
#     dummy()
#     home_with_dummy()
#     doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.REPORT_NDIFF|doctest.REPORT_ONLY_FIRST_FAILURE)
#     #teardown()
