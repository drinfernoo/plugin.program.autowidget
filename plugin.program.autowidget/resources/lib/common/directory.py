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
    "file",
    "thumbnail",
    "label",
    "lastmodified",
    "productioncode",
    "firstaired",
    "watchedepisodes",
    "id",
]

_default_info_keys = {"type": "mediatype"}

_video_keys = {
    "specialsortepisode": "sortepisode",
    "specialsortseason": "sortseason",
    "track": "tracknumber",
    "showtitle": "tvshowtitle",
    "runtime": "duration",
    "file": "path",
}

_music_keys = {
    "disc": "discnumber",
    "track": "tracknumber",
}

_translations = {"video": _video_keys, "music": _music_keys}
_exclude_params = ["refresh", "reload"]

_info_types = {}
_info_types.update(
    dict.fromkeys(
        ["video", "movie", "set", "tvshow", "season", "episode", "musicvideo"], "video"
    )
)
_info_types.update(dict.fromkeys(["music", "song", "album", "artist"], "music"))


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
    title="", params=None, path=None, info={}, cm=[], art={}, isFolder=False, props={}
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
        def_info = {v: info.get(k, "") for k, v in _default_info_keys.items()}
        mediatype = def_info.get("mediatype", "")
        isFolder = def_info.get("filetype") == "directory"

        for key in {k: v for k, v in info.items() if k not in _exclude_keys}:
            value = info.get(key)
            new_value = None
            if isinstance(value, list):
                if key == "cast":
                    item.setCast(value)
                else:
                    new_value = value
                    # new_value = " / ".join(value)
            elif isinstance(value, dict):
                if key == "resume":
                    pos = value.get("position", 0)
                    total = value.get("total", 0)
                    if pos > 0 and pos < total:
                        props["ResumeTime"] = six.text_type(pos)
                        props["TotalTime"] = six.text_type(total)
                elif key == "art":
                    art = value
                elif key == "customproperties":
                    labels = {k: v for k, v in value.items() if "contextmenulabel" in k}
                    actions = {k: v for k, v in value.items() if "contextmenuaction" in k}
                    if len(labels) == len(actions):
                        items = [(labels["contextmenulabel({})".format(i)], actions["contextmenuaction({})".format(i)]) for i in range(0, len(labels))]
                        cm.extend(items)
                    
                    for prop in value:
                        props[prop] = value[prop]
                elif key == "uniqueid":
                    item.setUniqueIDs(value)
                elif key == "streamdetails":
                    for d in value:
                        if len(value[d]) > 0:
                            item.addStreamInfo(d, value[d][0])
                else:
                    utils.log("Unknown dict-typed info key encountered: {}".format(key))
            else:
                new_value = (
                    value
                    if isinstance(value, int) or isinstance(value, float)
                    else six.text_type(value)
                )
            if new_value is not None:
                valid_keys = _translations.get(mediatype, {})
                new_key = valid_keys.get(key, key)
                def_info[new_key] = new_value

        info_type = _info_types.get(mediatype)
        if info_type:
            item.setInfo(info_type, def_info)
        item.setMimeType(def_info.get("mimetype", ""))

    for prop in props:
        item.setProperty(prop, props[prop])

    if not art.get("landscape") and art.get("thumb"):
        art["landscape"] = art["thumb"]
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
