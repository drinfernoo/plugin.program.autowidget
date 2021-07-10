import xbmcgui
import xbmcplugin

import sys

import six

from resources.lib.common import utils

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

_sort_methods = [
    xbmcplugin.SORT_METHOD_UNSORTED,
    xbmcplugin.SORT_METHOD_LABEL,
    xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
    xbmcplugin.SORT_METHOD_DATE,
    xbmcplugin.SORT_METHOD_TITLE,
    xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
    xbmcplugin.SORT_METHOD_LASTPLAYED,
]

_exclude_keys = [
    "type",
    "art",
    "mimetype",
    "thumbnail",
    "file",
    "label",
    "filetype",
    "lastmodified",
    "productioncode",
    "firstaired",
    "runtime",
    "showtitle",
    "specialsortepisode",
    "specialsortseason",
    "track",
    "tvshowid",
    "watchedepisodes",
    "customproperties",
    "id",
]

_exclude_params = ["refresh", "reload"]

_info_types = {
    **dict.fromkeys(
        ["video", "movie", "set", "tvshow", "season", "episode", "musicvideo"], "video"
    ),
    **dict.fromkeys(["music", "song", "album", "artist"], "music"),
}


def add_separator(title="", char="-", sort=""):
    _window = utils.get_active_window()
    sync = utils.get_art("sync")

    props = None
    if sort:
        props = {"specialsort": sort}

    if _window != "media":
        return

    if title:
        if isinstance(title, int):
            title = utils.get_string(title)

        split = (len(title) + 2) / 2
        edge = char * int(40 - split)
        add_menu_item(title="{0} {1} {0}".format(edge, title), art=sync, props=props)
    else:
        add_menu_item(title=char * 80, art=sync, props=props)


def add_sort_methods(handle):
    for method in _sort_methods:
        xbmcplugin.addSortMethod(handle, method)


def add_menu_item(
    title, params=None, path=None, info={}, cm=None, art={}, isFolder=False, props={}
):
    _plugin = sys.argv[0]
    _handle = int(sys.argv[1])

    if params is not None:
        encode = {k: v for k, v in params.items() if k not in _exclude_params}

        _plugin += "?{}".format(urlencode(encode))

        for param in _exclude_params:
            _plugin += "&{}={}".format(param, params.get(param, ""))
    elif path is not None:
        _plugin = path

    if isinstance(title, int):
        title = utils.get_string(title)

    item = xbmcgui.ListItem(title)

    if info:
        def_info = {"mediatype": info.get("type", "")}

        for key in {k: v for k, v in info.items() if k not in _exclude_keys}:
            if isinstance(info[key], list):
                value = info.get(key, [])
                if key == "cast":
                    item.setCast(value)
                else:
                    def_info[key] = " / ".join(value)
            elif isinstance(info[key], dict):
                value = info.get(key, {})
                if key == "resume":
                    pos = value.get("position", 0)
                    total = value.get("total", 0)
                    if pos > 0 and pos < total:
                        props["ResumeTime"] = six.text_type(pos)
                        props["TotalTime"] = six.text_type(total)
                else:
                    utils.log("Unknown dict-typed info key encountered: {}".format(key))
            else:
                value = info.get(key)
                if value is not None:
                    if key == "runtime":
                        def_info["duration"] = value
                    else:
                        def_info[key] = (
                            value
                            if isinstance(value, int) or isinstance(value, float)
                            else six.text_type(value)
                        )

        info_type = _info_types.get(def_info.get("mediatype"))
        if info_type:
            item.setInfo(info_type, def_info)
        item.setMimeType(def_info.get("mimetype", ""))

    for prop in props:
        item.setProperty(prop, props[prop])

    item.setArt(art)

    if cm:
        item.addContextMenuItems(cm)

    xbmcplugin.addDirectoryItem(
        handle=_handle, url=_plugin, listitem=item, isFolder=isFolder
    )


def finish_directory(handle, category, type):
    xbmcplugin.setPluginCategory(handle, category)
    xbmcplugin.setContent(handle, type)
    xbmcplugin.endOfDirectory(handle)
