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
    title, params=None, path=None, info={}, cm=None, art=None, isFolder=False, props={}
):
    _plugin = sys.argv[0]
    _handle = int(sys.argv[1])

    if params is not None:
        encode = {k: params[k] for k, v in params.items() if k not in _exclude_params}

        _plugin += "?{}".format(urlencode(encode))

        for param in _exclude_params:
            _plugin += "&{}={}".format(param, params.get(param, ""))
    elif path is not None:
        _plugin = path

    if isinstance(title, int):
        title = utils.get_string(title)

    item = xbmcgui.ListItem(title)

    if info:
        def_info = {x: info[x] for x in info if x not in _exclude_keys}
        mediatype = info.get("type", "video")
        if mediatype != "unknown":
            def_info["mediatype"] = mediatype

        for key in def_info:
            i = def_info.get(key)
            if any(key == x for x in ["artist", "cast"]):
                if not i:
                    def_info[key] = []
                elif not isinstance(i, list):
                    def_info[key] = [i]
                elif isinstance(i, list) and key == "cast":
                    cast = []
                    for actor in i:
                        cast.append((actor["name"], actor["role"]))
                    def_info[key] = cast
            elif isinstance(i, list):
                def_info[key] = " / ".join(i)
            else:
                def_info[key] = six.text_type(i)

        runtime = info.get("runtime", 0)
        if runtime > 0:
            def_info["duration"] = runtime

        resume = info.get("resume", {})
        if "resume" in def_info:
            def_info.pop("resume")
        if resume.get("position", 0) > 0:
            props["ResumeTime"] = six.text_type(resume["position"])
            props["TotalTime"] = six.text_type(resume["total"])

        item.setInfo("video", def_info)
        item.setMimeType(def_info.get("mimetype", ""))

    if props:
        try:
            item.setProperties(props)
        except AttributeError:
            for prop in props:
                item.setProperty(prop, props[prop])

    if art:
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
