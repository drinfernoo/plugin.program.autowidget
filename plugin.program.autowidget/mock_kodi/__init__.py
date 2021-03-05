# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals, print_function

import functools
import json
import os
import re
import shutil
import sys
import time
import types
import runpy
from urllib.parse import urlparse
import queue
import doctest

import polib

try:
    WindowsError = WindowsError
except NameError:
    WindowsError = Exception


try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

import xbmc
import xbmcaddon
import xbmcdrm
import xbmcgui
import xbmcplugin
import xbmcvfs

PYTHON3 = True if sys.version_info.major == 3 else False
PYTHON2 = not PYTHON3
SUPPORTED_LANGUAGES = {
    "en-de": ("en-de", "eng-deu", "English-Central Europe"),
    "en-aus": ("en-aus", "eng-aus", "English-Australia (12h)"),
    "en-gb": ("en-gb", "eng-gbr", "English-UK (12h)"),
    "en-us": ("en-us", "eng-usa", "English-USA (12h)"),
    "de-de": ("de-de", "ger-deu", "German-Deutschland"),
    "nl-nl": ("nl-nl", "dut-nld", "Dutch-NL"),
}

PLUGIN_NAME = "plugin.program.autowidget"

LOG_LEVEL = "LOGINFO"

def get_input(prompt=""):
    if MOCK.INPUT_QUEUE:
        if MOCK.INPUT_QUEUE.unfinished_tasks:
            MOCK.INPUT_QUEUE.task_done()
        keys = str(MOCK.INPUT_QUEUE.get(True))
        #print(f"{prompt}{keys}")
        return keys
    else:
        if PYTHON2:
            return raw_input(prompt)  # noqa
        else:
            return input(prompt)



def makedirs(name, mode=0o777, exist_ok=False):
    """makedirs(name [, mode=0o777][, exist_ok=False])
    Super-mkdir; create a leaf directory and all intermediate ones.  Works like
    mkdir, except that any intermediate path segment (not just the rightmost)
    will be created if it does not exist. If the target directory already
    exists, raise an OSError if exist_ok is False. Otherwise no exception is
    raised.  This is recursive.
    :param name:Name of the directory to be created
    :type name:str|unicode
    :param mode:Unix file mode for created directories
    :type mode:int
    :param exist_ok:Boolean to indicate whether is should raise on an exception
    :type exist_ok:bool
    """
    try:
        os.makedirs(name, mode, exist_ok)
    except (OSError, FileExistsError, WindowsError):
        if not exist_ok:
            raise

def pick_item(selected, items, start=0):
    """
    >>> abc = ["A","B","C"]
    >>> pick_item("1", abc)
    0
    >>> pick_item("B", abc)
    1
    >>> pick_item("blah", abc) is None
    True
    >>> pick_item("5", abc) is None
    True
    >>> pick_item("0", abc, -1)
    -1
    """

    try:
        action = int(selected) - 1
    except:
        action = next((i for i,item in enumerate(items, start) if str(item)==selected), None)
        if action is None:
            return None
    if not(start <= action < len(items)-start):
        return None
    return action


class Directory:
    """Directory class to keep track of items added to the virtual directory of the mock"""

    def __init__(self):
        pass

    history = []
    items = []
    last_action = ""
    next_action = ""
    current_list_item = None
    content = "movies"
    sort_method = {}
    action_callbacks = {}
    context_callbacks = []

    def handle_directory(self):
        """
        :return:
        :rtype:
        """
        if not MOCK.INTERACTIVE_MODE:
            return

        while True:
            old_items = self.items
            self.items = []
            self._execute_action()
            if not self.items: # plugin didn't open a menu, keep on teh same one
                self.items = old_items
            else:
                self.current_list_item = None

            while True:

                if self.next_action != self.last_action:
                    self.history.append(self.last_action)
                    self.last_action = self.next_action

                print("-------------------------------")
                print("-1) Back")
                print(" 0) Home")
                print("-------------------------------")
                for idx, item in enumerate(self.items):
                    print(" {}) {}".format(idx + 1, item[1]))

                print("-------------------------------")
                print("Enter Action Number")
                action = get_input()
                if self._try_handle_menu_action(action):
                    break
                elif self._try_handle_context_menu_action(action):
                    break
                elif self._try_handle_action(action):
                    break
                else:
                    print("Please enter a valid entry")

    def _try_handle_menu_action(self, selected):
        action = pick_item(selected, ["Back", "Home"]+[str(i[1]) for i in self.items], -2)
        if action is None:
            return False
        if action == -2:
            if self.history:
                self.next_action = self.history.pop(-1)
                self.last_action = ""
            self.current_list_item = None
            return True
        elif action == -1:
            self.next_action = ""
            self.current_list_item = None
            return True
        else:
            self.next_action = self.items[action][0]
            self.current_list_item = self.items[action][1]
            return True

    def _try_handle_context_menu_action(self, action):
        get_context_check = re.findall(r"^c(\d*)", action)
        if len(get_context_check) == 1:
            cur_item = self.items[int(get_context_check[0]) - 1]
            self.current_list_item = cur_item[1]
            items = []
            for context_item in cur_item[1].cm:
                items.append(
                    (context_item[0], re.findall(r".*?\((.*?)\)", context_item[1])[0])
                )
            # Get contenxt menus from addons
            for label, path, visible in self.context_callbacks:
                # TODO: handle conditions
                items.append(
                    (path, label)
                )
            # Show context menu
                for idx, item in enumerate(items):
                    print(" {}) {}".format(idx + 1, item[1]))

                action = get_input("Enter Context Menu: ")
                action = pick_item(action, ["Back", "Cancel"]+[str(i[1]) for i in items], -2)
                if action is None:
                    return False            
                self.next_action = items[action][0]
                return True
                    
            return True
        return False

    def _try_handle_action(self, action):
        if action.startswith("action"):
            try:
                self.next_action[2] = re.findall(r"action (.*?)$", action)[0]
                return True
            except:
                print("Failed to parse action {}".format(action))
        return False

    def _execute_action(self, next_path=None):
        if next_path is None:
            next_path = self.next_action
        #from resources.lib.modules.globals import g

        #g.init_globals(["", 0, self.next_action])
        for path,script in sorted(self.action_callbacks.items(), reverse=True):
            if not next_path.startswith(path):
                continue
            if type(script) == type(""):
                p = urlparse(next_path)
                sys.argv = ["{}://{}".format(p.scheme, p.hostname), 1, "?"+p.query]
                runpy.run_module(script, run_name='__main__',)
            else:
                script(next_path)
            break

    def get_items_dictionary(self, path=None, properties=[]):
        """
        :return:
        :rtype:
        """
        if path is not None:
            old_items = self.items
            self.items = []
            self._execute_action(path)
        result = json.loads(json.dumps([i.toJSONRPC(properties) for _,i,_ in self.items], cls=JsonEncoder))
        if path is not None:
            self.items = old_items
        else:
            self.items = []
        return result

    def executeInfoLabel(self, value):
        # handle ListItem or Container infolabels
        ListItem = self.current_list_item
        Container = self
        class Window:
            @staticmethod
            def getInfoLabel(key, *params):
                params = [p for p in params if p]
                a = getattr(Window, key)
                if a:
                    return a(*params)

            @staticmethod
            def IsActive(window):
                if window=='home':
                    return self.next_action == ""
                raise Exception(f"Not handled Window.IsActive({window})")

            @staticmethod
            def Property(prop):
                if prop == 'xmlfile':
                    return '<?xml version="1.0" encoding="UTF-8"?><window></window>'

            @staticmethod
            def IsMedia():
                return False
        #value = value.replace(".", ".get")
        v1 = re.sub(r"\.([^\d\W]\w*)\(([.\w]*)\)", r".getInfoLabel('\1','\2')", value) # ListItem.Art(banner)
        v2 = re.sub(r"\.(?!getInfoLabel)([^\d\W]\w*)(?!\()", r".getInfoLabel('\1')", v1) # ListItem.Art
        return eval(v2, locals())
    
    @property
    def ListItem(self):
        return self.current_list_item

    def getInfoLabel(self, key):
        if key == 'Content':
            return self.content
        elif key == 'ListItem':
            return self.current_list_item
        else:
            raise Exception(f"Not found {key}")


    def register_action(self, path, script):
        # TODO: read config from the addon.xml for actions and context menu
        self.action_callbacks[path] = script

    def register_contextmenu(self, label, plugin, module, visible=None):
        # TODO: read config from the addon.xml for actions and context menu
        path = "plugin://{}/{}".format(plugin, module) # HACK: there is probably an offical way to encode
        self.context_callbacks.append((label, path, visible))
        self.action_callbacks[path] = module


class SerenStubs:
    @staticmethod
    def create_stubs():
        """Returns the methods used in the new kodistubs monkey patcher
        :return:Dictionary with the stub mapping
        :rtype:dict
        """
        return {
            "xbmc": {
                "getInfoLabel": SerenStubs.xbmc.getInfoLabel,
                "translatePath": SerenStubs.xbmc.translatePath,
                "log": SerenStubs.xbmc.log,
                "getSupportedMedia": SerenStubs.xbmc.getSupportedMedia,
                "getLanguage": SerenStubs.xbmc.getLanguage,
                "getCondVisibility": SerenStubs.xbmc.getCondVisibility,
                "executebuiltin": SerenStubs.xbmc.executebuiltin,
                "executeJSONRPC": SerenStubs.xbmc.executeJSONRPC,
                "PlayList": SerenStubs.xbmc.PlayList,
                "Monitor": SerenStubs.xbmc.Monitor,
                "validatePath": lambda t: t,
                "sleep": lambda t: time.sleep(t / 1000),
            },
            "xbmcaddon": {"Addon": SerenStubs.xbmcaddon.Addon},
            "xbmcgui": {
                "ListItem": SerenStubs.xbmcgui.ListItem,
                "Window": SerenStubs.xbmcgui.Window,
                "Dialog": SerenStubs.xbmcgui.Dialog,
                "DialogBusy": SerenStubs.xbmcgui.DialogBusy,
                "DialogProgress": SerenStubs.xbmcgui.DialogProgress,
                "DialogProgressBG": SerenStubs.xbmcgui.DialogProgressBG,
            },
            "xbmcplugin": {
                "addDirectoryItem": SerenStubs.xbmcplugin.addDirectoryItem,
                "addDirectoryItems": SerenStubs.xbmcplugin.addDirectoryItems,
                "endOfDirectory": SerenStubs.xbmcplugin.endOfDirectory,
                "addSortMethod": SerenStubs.xbmcplugin.addSortMethod,
                "setContent": SerenStubs.xbmcplugin.setContent,
                "setPluginCategory": SerenStubs.xbmcplugin.setPluginCategory,
            },
            "xbmcvfs": {
                "File": SerenStubs.xbmcvfs.open,
                "exists": os.path.exists,
                "mkdir": os.mkdir,
                "mkdirs": os.makedirs,
                "rmdir": shutil.rmtree,
                "validatePath": lambda t: t,
            },
        }

    class xbmc:
        """Placeholder for the xbmc stubs"""

        @staticmethod
        def translatePath(path):
            """Returns the translated path"""
            valid_dirs = [
                "xbmc",
                "home",
                "temp",
                "masterprofile",
                "profile",
                "subtitles",
                "userdata",
                "database",
                "thumbnails",
                "recordings",
                "screenshots",
                "musicplaylists",
                "videoplaylists",
                "cdrips",
                "skin",
            ]

            if not path.startswith("special://"):
                return path
            parts = path.split("/")[2:]
            assert len(parts) > 1, "Need at least a single root directory"

            name = parts[0]
            assert name in valid_dirs, "{} is not a valid root dir.".format(name)

            parts.pop(0)  # remove name property

            dir_master = os.path.join(MOCK.PROFILE_ROOT, "userdata")

            makedirs(dir_master, exist_ok=True)

            if name == "xbmc":
                return os.path.join(MOCK.XBMC_ROOT, *parts)
            elif name in ("home", "logpath"):
                if not MOCK.RUN_AGAINST_INSTALLATION and all(
                        x in parts for x in ["addons", PLUGIN_NAME]
                ):
                    return MOCK.PROFILE_ROOT
                return os.path.join(MOCK.PROFILE_ROOT, *parts)
            elif name in ("masterprofile", "profile"):
                return os.path.join(dir_master, *parts)
            elif name == "database":
                return os.path.join(dir_master, "Database", *parts)
            elif name == "thumbnails":
                return os.path.join(dir_master, "Thumbnails", *parts)
            elif name == "musicplaylists":
                return os.path.join(dir_master, "playlists", "music", *parts)
            elif name == "videoplaylists":
                return os.path.join(dir_master, "playlists", "video", *parts)
            else:
                import tempfile

                tempdir = os.path.join(tempfile.gettempdir(), "XBMC", name)
                makedirs(tempdir, exist_ok=True)
                return os.path.join(tempdir, *parts)

        @staticmethod
        def getInfoLabel(value):
            """Returns information about infolabels
            :param value:
            :type value:
            :return:
            :rtype:
            """
            if value == "System.BuildVersion":
                if PYTHON2:
                    return "18"
                if PYTHON3:
                    return "19"
            elif any(value.startswith(i) for i in ["ListItem.", "Container.", "Window."]):
                res = MOCK.DIRECTORY.executeInfoLabel(value)
                if res is not None:
                    return res
            print(f"Couldn't find the infolabel: {value}")
            return ""

        @staticmethod
        def getCondVisibility(value):
            if value == "Window.IsMedia":
                return 0
            res = MOCK.DIRECTORY.executeInfoLabel(value)
            if res is not None:
                return res
            print(f"Couldn't find condition: {value}")



        @staticmethod
        def getSupportedMedia(media):
            """Returns the supported file types for the specific media as a string"""
            if media == "video":
                return (
                    ".m4v|.3g2|.3gp|.nsv|.tp|.ts|.ty|.strm|.pls|.rm|.rmvb|.mpd|.m3u|.m3u8|.ifo|.mov|.qt|.divx|.xvid|.bivx|.vob|.nrg|.img|.iso|.pva|.wmv"
                    "|.asf|.asx|.ogm|.m2v|.avi|.bin|.dat|.mpg|.mpeg|.mp4|.mkv|.mk3d|.avc|.vp3|.svq3|.nuv|.viv|.dv|.fli|.flv|.rar|.001|.wpl|.zip|.vdr|.dvr"
                    "-ms|.xsp|.mts|.m2t|.m2ts|.evo|.ogv|.sdp|.avs|.rec|.url|.pxml|.vc1|.h264|.rcv|.rss|.mpls|.webm|.bdmv|.wtv|.pvr|.disc "
                )
            elif media == "music":
                return (
                    ".nsv|.m4a|.flac|.aac|.strm|.pls|.rm|.rma|.mpa|.wav|.wma|.ogg|.mp3|.mp2|.m3u|.gdm|.imf|.m15|.sfx|.uni|.ac3|.dts|.cue|.aif|.aiff|.wpl"
                    "|.ape|.mac|.mpc|.mp+|.mpp|.shn|.zip|.rar|.wv|.dsp|.xsp|.xwav|.waa|.wvs|.wam|.gcm|.idsp|.mpdsp|.mss|.spt|.rsd|.sap|.cmc|.cmr|.dmc|.mpt"
                    "|.mpd|.rmt|.tmc|.tm8|.tm2|.oga|.url|.pxml|.tta|.rss|.wtv|.mka|.tak|.opus|.dff|.dsf|.cdda "
                )
            elif media == "picture":
                return ".png|.jpg|.jpeg|.bmp|.gif|.ico|.tif|.tiff|.tga|.pcx|.cbz|.zip|.cbr|.rar|.rss|.webp|.jp2|.apng"
            return ""

        @staticmethod
        def log(msg, level=xbmc.LOGDEBUG):
            """Write a string to XBMC's log file and the debug window"""
            if PYTHON2:
                levels = [
                    "LOGDEBUG",
                    "LOGINFO",
                    "LOGNOTICE",
                    "LOGWARNING",
                    "LOGERROR",
                    "LOGSEVERE",
                    "LOGFATAL",
                    "LOGNONE",
                ]
            else:
                levels = [
                    "LOGDEBUG",
                    "LOGINFO",
                    "LOGWARNING",
                    "LOGERROR",
                    "LOGSEVERE",
                    "LOGFATAL",
                    "LOGNONE",
                ]
            value = "{} - {}".format(levels[level], msg)
            if levels.index(LOG_LEVEL) <= level:
                print(value)
                MOCK.LOG_HISTORY.append(value)

        @staticmethod
        def getLanguage(format=xbmc.ENGLISH_NAME, region=False):
            """Returns the active language as a string."""
            result = SUPPORTED_LANGUAGES.get(MOCK.KODI_UI_LANGUAGE, ())[format]
            if region:
                return result
            else:
                return result.split("-")[0]

        @staticmethod
        def executebuiltin(function, wait=False):
            """Execute a built in Kodi function"""
            print("EXECUTE BUILTIN: {} wait:{}".format(function, wait))

        @staticmethod
        def executeJSONRPC(jsonrpccommand):
            command = json.loads(jsonrpccommand)
            method = command.get("method")
            if method == 'JSONRPC.Version':
                res = dict(result=dict(version=dict(major=19,minor=0,patch=0)))
            elif method == "Files.GetDirectory":
                path = command['params']['directory']
                props = command['params'].get('properties',[])
                files = MOCK.DIRECTORY.get_items_dictionary(path, properties=props)
                res = dict(result=dict(files=files))
            else:
                raise Exception(f"executeJSONRPC not handled for {method}")
            return json.dumps(res)


        class PlayList(xbmc.PlayList):
            def __init__(self, playList):
                self.list = []

            def add(self, url, listitem=None, index=-1):
                self.list.append([url, listitem])

            def getposition(self):
                return 0

            def clear(self):
                self.list.clear()

            def size(self):
                return len(self.list)

        class Monitor:
            def __init__(self, *args, **kwargs):
                pass

            def abortRequested(self):
                return False

            def waitForAbort(self, timeout=0):
                time.sleep(timeout)
                return True

            def onSettingsChanged(self):
                pass

    class xbmcaddon:
        class Addon(xbmcaddon.Addon):
            def __init__(self, addon_id=None):
                self._id = addon_id
                self._config = {}
                self._strings = {}
                self._current_user_settings = {}

            def _load_addon_config(self):
                # Parse the addon config
                try:
                    filepath = os.path.join(MOCK.SEREN_ROOT, "addon.xml")
                    xml = ElementTree.parse(filepath)
                    self._config = xml.getroot()
                    self._id = self.getAddonInfo("id") or self._id
                except ElementTree.ParseError:
                    pass
                except IOError:
                    pass

            def _load_language_string(self):
                only_digits = re.compile(r"\D")

                langfile = self.get_po_location(
                    xbmc.getLanguage(
                        format=xbmc.ISO_639_1,
                        region=True)
                )
                if os.path.exists(langfile):
                    po = polib.pofile(langfile)
                else:
                    po = polib.pofile(self.get_po_location("en-gb"))
                self._strings = {
                    int(only_digits.sub("", entry.msgctxt)): entry.msgstr
                    if entry.msgstr
                    else entry.msgid
                    for entry in po
                }

            def get_po_location(self, language):
                langfile = os.path.join(
                    MOCK.SEREN_ROOT,
                    "resources",
                    "language",
                    "resource.language.{}".format(language).replace("-", "_"),
                    "strings.po",
                )
                return langfile

            def _load_user_settings(self):
                current_settings_file = os.path.join(
                    os.path.join(
                        MOCK.PROFILE_ROOT,
                        "userdata",
                        "addon_data",
                        PLUGIN_NAME,
                        "settings.xml",
                    )
                )
                if not os.path.exists(current_settings_file):
                    self._init_user_settings()
                    return
                xml = ElementTree.parse(current_settings_file)
                settings = xml.findall("./setting")
                for node in settings:
                    setting_id = node.get("id")
                    setting_value = node.text
                    item = {"id": setting_id}
                    if setting_value:
                        item["value"] = setting_value
                    self._current_user_settings.update({setting_id: item})

            def _init_user_settings(self):
                settings_def_file = os.path.join(
                    os.path.join(
                        MOCK.SEREN_ROOT,
                        "resources",
                        "settings.xml",
                    )
                )
                addon_dir = os.path.join(
                    os.path.join(
                        MOCK.PROFILE_ROOT,
                        "userdata",
                        "addon_data",
                        PLUGIN_NAME,
                    )
                )
                makedirs(addon_dir, exist_ok=True)
                current_settings_file = os.path.join(
                    os.path.join(
                        MOCK.PROFILE_ROOT,
                        "userdata",
                        "addon_data",
                        PLUGIN_NAME,
                        "settings.xml",
                    )
                )
                xml = ElementTree.parse(settings_def_file)
                settings = xml.findall("./category/setting")
                for node in settings:
                    setting_id = node.get("id")
                    setting_value = node.get("default")
                    item = {"id": setting_id}
                    if setting_value:
                        item["value"] = setting_value
                    self._current_user_settings.update({setting_id: item})
                # TODO: write into current_settings_file


            def getAddonInfo(self, key):
                if not self._config:
                    self._load_addon_config()

                properties = [
                    "author",
                    "changelog",
                    "description",
                    "disclaimer",
                    "fanart",
                    "icon",
                    "id",
                    "name",
                    "path",
                    "profile",
                    "stars",
                    "summary",
                    "type",
                    "version",
                ]
                if key not in properties:
                    raise ValueError("{} is not a valid property.".format(key))
                if key == "profile":
                    return "special://profile/addon_data/{0}/".format(self._id)
                if key == "path":
                    return "special://home/addons/{0}".format(self._id)
                if self._config and key in self._config.attrib:
                    return self._config.attrib[key]
                return None

            def getLocalizedString(self, key):
                if not self._strings:
                    self._load_language_string()

                if key in self._strings:
                    return kodi_to_ansi(self._strings[key])
                print("Cannot find localized string {}".format(key))
                return None

            def getSetting(self, key):
                if not self._current_user_settings:
                    self._load_user_settings()
                if key in self._current_user_settings:
                    return self._current_user_settings[key].get("value")
                return None

            def setSetting(self, key, value):
                if not self._current_user_settings:
                    self._load_user_settings()
                self._current_user_settings.update({key: {"value": str(value)}})

    class xbmcplugin:
        @staticmethod
        def addDirectoryItem(handle, url, listitem, isFolder=False, totalItems=0):
            listitem.is_folder = isFolder
            MOCK.DIRECTORY.items.append((url, listitem, isFolder))

        @staticmethod
        def addDirectoryItems(handle, items, totalItems=0):
            MOCK.DIRECTORY.items.extend(items)

        @staticmethod
        def endOfDirectory(
                handle, succeeded=True, updateListing=False, cacheToDisc=True
        ):
            #MOCK.DIRECTORY.handle_directory()
            pass

        @staticmethod
        def setContent(handle, content):
            MOCK.DIRECTORY.content = content

        @staticmethod
        def setPluginCategory(handle, category):
            MOCK.DIRECTORY.content = category


        @staticmethod
        def addSortMethod(handle, sortMethod, label2Mask=""):
            MOCK.DIRECTORY.sort_method = sortMethod

    class xbmcgui:
        class ListItem(xbmcgui.ListItem):
            def __init__(
                    self,
                    label="",
                    label2="",
                    iconImage="",
                    thumbnailImage="",
                    path="",
                    offscreen=False,
            ):
                self.contentLookup = None
                self._label = label
                self._label2 = label2
                self._icon = iconImage
                self._thumb = thumbnailImage
                self._path = path
                self._offscreen = offscreen
                self._props = {}
                self._selected = False
                self.cm = []
                self.vitags = {}
                self.art = {}
                self.votes = {}
                self.info = {}
                self.info_type = ""
                self.uniqueIDs = {}
                self.ratings = {}
                self.contentLookup = True
                self.stream_info = {}
                self.is_folder = False
                self.mimeType = ''

            def addContextMenuItems(self, items, replaceItems=False):
                [self.cm.append(i) for i in items]

            def getLabel(self):
                return self._label

            def getLabel2(self):
                return self._label2

            def getProperty(self, key):
                key = key.lower()
                if key in self._props:
                    return self._props[key]
                return ""

            def getRating(self, key=None): #make key optional for getInfoLabel
                return self.ratings.get(key, 0.0) if key else 0.0

            def getArt(self, key='thumb'):
                return self.art.get(key, "")

            def getPath(self):
                return self._path

            def getVotes(self, key=None):
                if key is None:
                    return self.votes.values[0] if self.votes else 0
                else:
                    return self.votes.get(key, 0)

            def isSelected(self):
                return self._selected

            def select(self, selected):
                self._selected = selected

            def setArt(self, values):
                if not values:
                    return
                self.art.update(values)

            def setIconImage(self, value):
                self._icon = value

            def setInfo(self, type, infoLabels):
                if type:
                    self.info_type = type
                if isinstance(infoLabels, dict):
                    self.info.update(infoLabels)

            def setLabel(self, label):
                self._label = label

            def setLabel2(self, label):
                self._label2 = label

            def setProperty(self, key, value):
                key = key.lower()
                self._props[key] = value

            def setProperties(self, properties):
                for key, value in properties.items():
                    self.setProperty(key, value)

            def setThumbnailImage(self, value):
                self._thumb = value

            def setCast(self, actors):
                """Set cast including thumbnails. Added in v17.0"""
                pass

            def setUniqueIDs(self, ids, **kwargs):
                self.uniqueIDs.update(ids)

            def setRating(self, rating_type, rating, votes=0, default=False):
                self.ratings.update({rating_type: [rating, votes, default]})

            def setContentLookup(self, enable):
                self.contentLookup = enable

            def addStreamInfo(self, cType, dictionary):
                self.stream_info.update({cType: dictionary})

            def setMimeType(self, mimetype):
                self._props['MimeType'] = mimetype

            def __str__(self):
                return self._label

            # Additional methods for infolabels

            def getInfoLabel(self, key, *params):
                # return value or function
                if hasattr(self, 'get'+key):
                    return getattr(self, 'get'+key)(*params)
                if key in self.info:
                    return self.info[key]
                else:
                    return "" # HACK     

            def getFolderPath(self):
                return self._path

            def getIsFolder(self):
                return self.is_folder

            def toJSONRPC(self, properties=[]):
                item = dict(
                    filetype='direcotry' if self.is_folder else 'file',
                    title=self._label,
                    type="unknown",
                    file=self._path,
                    label=self._label,
                    art=self.art,
                    mimetype=self._props.get('MimeType','')
                )
                item.update({k:v for k,v in self.info.items() if k in properties})
                return item

        class Window(xbmcgui.Window):
            def __init__(self, windowId=0):
                self._props = {}

            def clearProperties(self):
                self._props.clear()

            def clearProperty(self, key):
                key = key.lower()
                if key in self._props:
                    del self._props[key]

            def getProperty(self, key):
                key = key.lower()
                if key in self._props:
                    return self._props[key]
                return None

            def setProperty(self, key, value):
                key = key.lower()
                self._props[key] = value

        class Dialog(xbmcgui.Dialog):
            def notification(
                    self,
                    heading,
                    message,
                    icon=xbmcgui.NOTIFICATION_INFO,
                    time=5000,
                    sound=True,
            ):
                if icon == xbmcgui.NOTIFICATION_WARNING:
                    prefix = "[WARNING]"
                elif icon == xbmcgui.NOTIFICATION_ERROR:
                    prefix = "[ERROR]"
                else:
                    prefix = "[INFO]"
                print("NOTIFICATION: {0} {1}: {2}".format(prefix, heading, message))

            def ok(self, heading, message):
                print("{}: \n{}".format(heading, message))
                return True

            def select(
                    self, heading, list, autoclose=False, preselect=None, useDetails=False
            ):
                print(heading)
                action = None
                for idx, i in enumerate(list):
                    print("{}) {}".format(idx, i))
                while action is None:
                    action = pick_item(get_input(), ["Back", "Cancel"] + list, -2)
                if action < 0:
                    return -1
                return action

            def textviewer(self, heading, text, usemono=False):
                print(heading)
                print(text)

            def yesno(
                    self,
                    heading,
                    message,
                    nolabel="",
                    yeslabel="",
                    customlabel="",
                    autoclose=0,
            ):
                if not MOCK.INTERACTIVE_MODE:
                    return 1
                print("")
                print("{}\n{}".format(heading, message))
                print("1) {}/ 0) {}".format(yeslabel, nolabel))
                action = get_input()
                return action
            
            def input(
                self, 
                heading, 
                defaultt="", 
                type=xbmcgui.INPUT_ALPHANUM, 
                option=None, 
                autoclose=None
            ):
                print(heading)
                while True:
                    if type==xbmcgui.INPUT_ALPHANUM:
                        return get_input("Enter AlphaNum:")
                    elif type==xbmcgui.INPUT_NUMERIC:
                        try:
                            return float(get_input("Enter Number:"))
                        except:
                            pass
                    elif type==xbmcgui.INPUT_DATE:
                        date = get_input("Enter Date (DD/MM/YYYY):")
                        #TODO:
                        return date
                    elif type==xbmcgui.INPUT_TIME:
                        time = get_input("Enter Time (HH:MM):")
                        #TODO:
                        return time
                    elif type==xbmcgui.INPUT_IPADDRESS:
                        ip = get_input("Enter IP Address (#.#.#.#):")
                        #TODO:
                        return ip
                    elif type == xbmcgui.INPUT_PASSWORD:
                        return get_input("Enter Password:")
                        # TODO: needs to be md5 hashed, and optionally verified



        class DialogBusy:
            """Show/Hide the progress indicator. Added in v17.0"""

            def create(self):
                print("[BUSY] show")

            def update(self, percent):
                print("[BUSY] update: {0}".format(percent))

            def close(self):
                print("[BUSY] close")

            def iscanceled(self):
                return False

        class DialogProgress(xbmcgui.DialogProgress):
            canceled = False

            def __init__(self):
                self._created = False
                self._heading = None
                self._message = None
                self._percent = -1

            def update(self, percent, message=""):
                if percent:
                    self._percent = percent
                if message:
                    self._message = message
                print(
                    "[PROGRESS] {0}: {1} - {2}%".format(
                        self._heading, self._message, self._percent
                    )
                )

            def create(self, heading, message=""):
                self._created = True
                self._heading = heading
                self._message = message
                self._percent = 0
                print(
                    "[PROGRESS] {0}: {1} - {2}%".format(
                        self._heading, self._message, self._percent
                    )
                )

            def iscanceled(self):
                return self.canceled

            def close(self):
                print("[PROGRESS] closing")

        class DialogProgressBG(xbmcgui.DialogProgressBG):
            def __init__(self):
                self._created = False
                self._heading = ""
                self._message = ""
                self._percent = 0

            def create(self, heading, message=""):
                self._created = True
                self._heading = heading
                self._message = message
                self._percent = 0
                print(
                    "[BACKGROUND] {0}: {1} - {2}%".format(
                        self._heading, self._message, self._percent
                    )
                )

            def close(self):
                self._created = False
                print("[BACKGROUND] closing")

            def update(self, percent=0, heading="", message=""):
                self._percent = percent
                if heading:
                    self._heading = heading
                if message:
                    self._message = message
                print(
                    "[BACKGROUND] {0}: {1} - {2}%".format(
                        self._heading, self._message, self._percent
                    )
                )

            def isFinished(self):
                return not self._created

    class xbmcvfs:
        @staticmethod
        def open(filepath, mode="r"):
            if sys.version_info.major == 3:
                return open(filepath, mode, encoding="utf-8")
            else:
                return open(filepath, mode)


class MonkeyPatchKodiStub:
    """Helper class for Monkey patching kodistubs to add functionality."""

    def __init__(self):
        self._dict = SerenStubs.create_stubs()

    def trace_log(self):
        self._walk_kodi_dependencies(self._trace_log_decorator)

    def monkey_patch(self):
        self._walk_kodi_dependencies(self._monkey_patch)

    def _walk_kodi_dependencies(self, func):
        [
            self._walk_item(i, func)
            for i in [xbmc, xbmcgui, xbmcaddon, xbmcdrm, xbmcplugin, xbmcvfs]
        ]

    def _walk_item(self, item, func, path=None):
        if path is None:
            path = []
        path.append(item.__name__)
        for k, v in vars(item).items():
            if isinstance(v, (types.FunctionType, staticmethod)):
                result = func(path, v)
                if result:
                    setattr(item, k, result)
            if type(v) is type:
                result = func(path, v)
                if result:
                    setattr(item, k, result)
                else:
                    self._walk_item(v, func, path)
        path.pop(-1)

    @staticmethod
    def _trace_log_decorator(path, func):
        """Add trace logging to the function it decorates.
        :param func: Function to decorate
        :type func: types.FunctionType
        :return: Wrapped function
        :rtype: types.FunctionType
        """
        joined_path = ".".join(path)

        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            try:
                if args:
                    print(
                        "Entering: {}.{} with parameters {}".format(
                            joined_path, func.__name__, args
                        )
                    )
                else:
                    print("Entering: {}.{}".format(joined_path, func.__name__))
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(
                        "Exception in {}.{} : {}".format(joined_path, func.__name__, e)
                    )
                    raise e
            finally:
                print("Exiting: {}.{}".format(joined_path, func.__name__))

        return _wrapped

    @staticmethod
    def _decorate(func, patch):
        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            return patch(func(*args, **kwargs))

        return _wrapped

    def _monkey_patch(self, path, item):
        patch = None
        for p in path:
            if patch:
                patch = patch.get(p, {})
            else:
                patch = self._dict.get(p, {})
        patch = patch.get(item.__name__)
        if patch:
            return patch
        elif isinstance(item, types.FunctionType):
            return self._log_not_patched_method(path, item)

    @staticmethod
    def _log_not_patched_method(path, func):
        """Add logging to the function that indicates that there is not mockey patch available.
        :param path: path of the calling method
        :type path: list[string]
        :param func: Function to decorate
        :type func: types.FunctionType
        :return: Wrapped function
        :rtype: types.FunctionType
        """
        joined_path = ".".join(path)

        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            object_type = "method" if isinstance(func, types.FunctionType) else "object"
            print(
                "Call to not patched {}: {}.{}".format(
                    object_type, joined_path, func.__name__
                )
            )
            return func(*args, **kwargs)

        return _wrapped


class MockKodi:
    """KODIStub mock helper"""

    def __init__(self):
        here = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.XBMC_ROOT = here
        #self.XBMC_ROOT = os.environ.get("KODI_ROOT", self.XBMC_ROOT)
        self.PROFILE_ROOT = os.path.abspath(os.path.join(self.XBMC_ROOT, "../"))
        self.PROFILE_ROOT = os.environ.get("KODI_PROFILE_ROOT", self.PROFILE_ROOT)
        self.SEREN_ROOT = os.path.abspath(os.path.join(here, "../"))
        self.KODI_UI_LANGUAGE = os.environ.get("KODI_UI_LANGUAGE", "en-gb")
        self.INTERACTIVE_MODE = (
                os.environ.get("SEREN_INTERACTIVE_MODE", False) == "True"
        )
        self.RUN_AGAINST_INSTALLATION = (
                os.environ.get("SEREN_RUN_AGAINST_INSTALLATION", False) == "True"
        )
        if self.RUN_AGAINST_INSTALLATION and os.path.exists(
                self.get_kodi_installation()
        ):
            self.PROFILE_ROOT = self.get_kodi_installation()
            self.SEREN_ROOT = os.path.join(
                self.PROFILE_ROOT, "addons", PLUGIN_NAME
            )

        self.DIRECTORY = Directory()
        self.LOG_HISTORY = []
        self.INPUT_QUEUE = queue.Queue()
        self._monkey_patcher = MonkeyPatchKodiStub()
        # self._monkey_patcher.trace_log()
        self._monkey_patcher.monkey_patch()

    @staticmethod
    def get_kodi_installation():
        """
        :return:
        :rtype:
        """
        dir_home = os.path.expanduser("~")
        if sys.platform == "win32":
            return os.path.join(dir_home, "AppData", "Roaming", "Kodi")
        return os.path.join(dir_home, ".kodi")


MOCK = MockKodi()


class JsonEncoder(json.JSONEncoder):
    """Json encoder for serialising all objects"""

    def default(self, o):
        """
        :param o:
        :type o:
        :return:
        :rtype:
        """
        return o.__dict__


def kodi_to_ansi(string):
    """
    :param string:
    :type string:
    :return:
    :rtype:
    """
    if string is None:
        return None
    string = string.replace("[B]", "\033[1m")
    string = string.replace("[/B]", "\033[21m")
    string = string.replace("[I]", "\033[3m")
    string = string.replace("[/I]", "\033[23m")
    string = string.replace("[COLOR gray]", "\033[30;1m")
    string = string.replace("[COLOR red]", "\033[31m")
    string = string.replace("[COLOR green]", "\033[32m")
    string = string.replace("[COLOR yellow]", "\033[33m")
    string = string.replace("[COLOR blue]", "\033[34m")
    string = string.replace("[COLOR purple]", "\033[35m")
    string = string.replace("[COLOR cyan]", "\033[36m")
    string = string.replace("[COLOR white]", "\033[37m")
    string = string.replace("[/COLOR]", "\033[39;0m")
    return string


class MockKodiUILanguage(object):
    def __init__(self, new_language):
        self.new_language = new_language
        self.original_language = MOCK.KODI_UI_LANGUAGE

    def __enter__(self):
        MOCK.KODI_UI_LANGUAGE = self.new_language
        return self.new_language

    def __exit__(self, exc_type, exc_val, exc_tb):
        MOCK.KODI_UI_LANGUAGE = self.original_language

if __name__ == '__main__':
    doctest.testmod()
