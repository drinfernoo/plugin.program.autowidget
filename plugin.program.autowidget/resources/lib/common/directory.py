import xbmcgui
import xbmcplugin

import sys

import six

from resources.lib.common import settings
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

_remove_keys = [
    "fanart",
    "file",
    "filetype",
    "id",
    "label",
    "lastmodified",
    "mimetype",
    "runtime",
    "showtitle",
    "thumbnail",
    "type",
    "watchedepisodes",
    "cast",
    "castandrole",
    "productioncode",
    "specialsortepisode",
    "specialsortseason",
    "track",
    "tvshowid",
    "disc",
    "firstaired",
]

_video_keys = {
    "specialsortepisode": "sortepisode",
    "specialsortseason": "sortseason",
    "track": "tracknumber",
    "showtitle": "tvshowtitle",
    "runtime": "duration",
    "file": "path",
    "type": "mediatype",
    "tvshowid": "id",
    "id": "dbid",
}

_music_keys = {"disc": "discnumber", "track": "tracknumber", "type": "mediatype"}

_translations = {"video": _video_keys, "music": _music_keys}
_exclude_params = ["refresh", "reload"]

info_types = {}
info_types.update(
    dict.fromkeys(
        ["video", "movie", "set", "tvshow", "season", "episode", "musicvideo"], "video"
    )
)
info_types.update(dict.fromkeys(["music", "song", "album", "artist"], "music"))


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
    title="",
    params=None,
    path=None,
    info=None,
    cm=None,
    art=None,
    isFolder=False,
    props=None,
):
    _plugin = sys.argv[0]
    _handle = int(sys.argv[1])

    if params is not None and isinstance(params, dict):
        encode = {k: v for k, v in params.items() if k not in _exclude_params}

        _plugin += "?{}".format(urlencode(encode))

        for param in _exclude_params:
            _plugin += "&{}={}".format(param, params.get(param, ""))
    elif path is not None and isinstance(path, six.text_type):
        _plugin = path

    if isinstance(title, int):
        title = utils.get_string(title)

    item = xbmcgui.ListItem(title)

    if info is not None and isinstance(info, dict):
        def_info = {}
        mediatype = info.get("type", "unknown")
        info_type = info_types.get(mediatype, "video")

        for key, value in info.items():
            new_value = None
            if isinstance(value, list):
                if key in ["cast", "castandrole"]:
                    item.setCast(value)
                else:
                    new_value = [six.text_type(i) for i in value]
            elif isinstance(value, dict):
                if key == "resume":
                    pos = value.get("position", 0)
                    total = value.get("total", 0)
                    if pos > 0 and pos < total:
                        if props is None:
                            props = {}
                        props["ResumeTime"] = six.text_type(pos)
                        props["TotalTime"] = six.text_type(total)
                elif key == "art":
                    if art is None:
                        art = value
                elif key == "customproperties":
                    # THIS BLOCK IS FOR ATTACHING CONTEXT MENU ITEMS TO WIDGET ITEMS
                    # BUT DOESN'T WORK, DUE TO KODI LIMITATIONS.
                    #
                    # context_items = {
                    #     k: v for k, v in value.items() if "contextmenu" in k
                    # }
                    # items = [
                    #     (
                    #         context_items.get("contextmenulabel({})".format(i)),
                    #         context_items.get("contextmenuaction({})".format(i)),
                    #     )
                    #     for i in range(0, len(context_items) // 2)
                    # ]
                    # if cm is None:
                    #     cm = []
                    # cm.extend(items)

                    if props is None:
                        props = {}
                    props.update(value)
                elif key == "uniqueid":
                    item.setUniqueIDs(value)
                elif key == "streamdetails":
                    for d in value:
                        if len(value[d]) > 0:
                            item.addStreamInfo(d, value[d][0])
                else:
                    utils.log("Unknown dict-typed info key encountered: {}".format(key))
            else:
                if key == "mimetype":
                    item.setMimeType(value)
                elif key == "artist":
                    new_value = [value]
                else:
                    new_value = (
                        value
                        if isinstance(value, (int, float))
                        else six.text_type(value)
                    )
            if new_value is not None:
                valid_keys = _translations.get(info_types.get(mediatype, ""), {})
                new_key = valid_keys.get(key, key)
                def_info[new_key] = new_value

        for key in _remove_keys:
            def_info.pop(key, None)

        item.setInfo(info_type, def_info)

    if props is not None and isinstance(props, dict):
        for prop in props:
            item.setProperty(prop, six.text_type(props[prop]))

    if art is not None and isinstance(art, dict):
        if info:
            path = info.get("file", "")
            if any(i in path for i in ["studios", "countries", "genres"]):
                if "studios" in path:
                    art["icon"] = "resource://{}/{}.png".format(
                        settings.get_setting("icons.studios"), info.get("label", "")
                    )
                elif "countries" in path:
                    art["icon"] = "resource://{}/{}.png".format(
                        settings.get_setting("icons.countries"), info.get("label", "")
                    )
                elif "genres" in path:
                    if "videodb" in path:
                        art["icon"] = "resource://{}/{}.png".format(
                            settings.get_setting("icons.video_genre_icons"),
                            info.get("label", ""),
                        )
                        art["fanart"] = "resource://{}/{}.jpg".format(
                            settings.get_setting("icons.video_genre_fanart"),
                            info.get("label", ""),
                        )
                    elif "musicdb" in path:
                        art["icon"] = "resource://{}/{}.jpg".format(
                            settings.get_setting("icons.music_genre_icons"),
                            info.get("label", ""),
                        )
                        art["fanart"] = "resource://{}/{}.jpg".format(
                            settings.get_setting("icons.music_genre_fanart"),
                            info.get("label", ""),
                        )

        if not any([art.get(i) for i in ["landscape", "poster"]]) and all(
            [art.get(i) for i in ["thumb", "fanart"]]
        ):
            art["landscape"] = art["thumb"]
        item.setArt(art)

    if cm is not None and isinstance(cm, list):
        item.addContextMenuItems(cm)

    xbmcplugin.addDirectoryItem(
        handle=_handle, url=_plugin, listitem=item, isFolder=isFolder
    )

    return _plugin


def make_library_path(library, type, id):
    if not library or not type or id == -1:
        return ""

    path = "{}db://".format(library)
    if library == "video":
        if type == "tvshow":
            path = "{}{}s/titles/{}".format(path, type, id)
    elif library == "music":
        if type in ["artist", "album"]:
            path = "{}{}s/{}/".format(path, type, id)
    return path


def finish_directory(handle, category, type):
    xbmcplugin.setPluginCategory(handle, category)
    xbmcplugin.setContent(handle, type)
    xbmcplugin.endOfDirectory(handle)
