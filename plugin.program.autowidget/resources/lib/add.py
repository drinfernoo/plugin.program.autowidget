import xbmcgui

import os

try:
    from urllib.parse import parse_qsl
    from urllib.parse import unquote
except ImportError:
    from urlparse import parse_qsl
    from urllib import unquote

from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import settings
from resources.lib.common import utils

_addon_data = utils.translate_path(settings.get_addon_info("profile"))

folder_shortcut = utils.get_art("folder-shortcut")
folder_sync = utils.get_art("folder-sync")
folder_settings = utils.get_art("folder-settings")
folder_clone = utils.get_art("folder-clone")
folder_explode = utils.get_art("folder-explode")
folder_search = utils.get_art("folder-search")

shortcut_types = [  # TODO: Untested
    (utils.get_string(30033), folder_shortcut, "shortcut"),
    (utils.get_string(30034), folder_sync, "widget"),
    (utils.get_string(30060), folder_clone, "clone"),
    (utils.get_string(30061), folder_explode, "explode"),
    (utils.get_string(30035), folder_settings, "settings"),
    (utils.get_string(30200), folder_search, "search"),
]


def add(labels):
    _type = _add_as(labels["file"])
    if not _type:
        return

    if _type not in ["clone", "explode"]:
        labels["target"] = _type
        group_def = _group_dialog(_type)
        if group_def:
            _add_path(group_def, labels)
    elif _type == "clone":
        labels["target"] = "shortcut"
        _copy_path(labels)
    elif _type == "explode":
        labels["target"] = "widget"
        _copy_path(labels)

    utils.update_container(_type == "shortcut")


def build_labels(source, path_def=None, target=""):
    if source == "context" and not path_def and not target:
        content = utils.get_infolabel("Container.Content")
        labels = {
            "label": utils.get_infolabel("ListItem.Label"),
            "content": content if content else "videos",
        }

        path_def = {
            "file": utils.get_infolabel("ListItem.FolderPath"),
            "filetype": "directory"
            if utils.get_condition("Container.ListItem.IsFolder")
            else "file",
            "art": {},
        }  # would be fun to set some "placeholder" art here

        for i in utils.get_info_keys():
            info = utils.get_infolabel("ListItem.{}".format(i.capitalize()))
            if info and not info.startswith("ListItem"):
                path_def[i] = info

        for i in utils.art_types:
            art = utils.get_infolabel("ListItem.Art({})".format(i))
            if art:
                path_def["art"][i] = utils.clean_artwork_url(art)
        for i in ["icon", "thumb"]:
            art = utils.clean_artwork_url(utils.get_infolabel("ListItem.{}".format(i)))
            if art:
                path_def["art"][i] = art
    elif source == "json" and path_def and target:
        labels = {"label": path_def["label"], "content": "videos", "target": target}

    labels["file"] = (
        path_def
        if path_def
        else {key: path_def[key] for key in path_def if path_def[key]}
    )
    path = labels["file"]["file"]

    if path != "addons://user/":
        path = path.replace("addons://user/", "plugin://")
    if "plugin://plugin.video.themoviedb.helper" in path and not "&widget=True" in path:
        path += "&widget=True"
    labels["file"]["file"] = path

    labels["color"] = settings.get_setting_string("ui.color")

    for _key in utils.windows:
        if any(i in path for i in utils.windows[_key]):
            labels["window"] = _key

    return labels


def _add_as(path_def):
    path = path_def["file"]
    types = shortcut_types[:]
    if path_def["filetype"] == "directory" and utils.get_active_window() != "home":
        types = shortcut_types[:4]
    else:
        if (
            any(i in path for i in ["addons://user", "plugin://", "script://"])
            and not parse_qsl(path)
        ) or ("widget", "True") in parse_qsl(path):
            pass
        else:
            types = [shortcut_types[0]]
    if "search" in path.lower():
        types.append(shortcut_types[-1])

    options = []
    for idx, type in enumerate(types):
        li = xbmcgui.ListItem(type[0])

        li.setArt(type[1])
        options.append(li)

    dialog = xbmcgui.Dialog()
    idx = dialog.select(utils.get_string(30062), options, useDetails=True)
    del dialog

    if idx < 0:
        return

    chosen = types[idx]
    return chosen[2]


def _group_dialog(_type, group_id=None):
    _type = "shortcut" if _type == "settings" else _type
    groups = manage.find_defined_groups(_type)
    ids = [group["id"] for group in groups]

    index = -1
    options = []
    offset = 1

    new_item = None  # TODO: Test this bit of refactoring
    new_art = {}
    if _type == "widget":
        new_item = xbmcgui.ListItem(utils.get_string(30010))
    elif _type == "shortcut":
        new_item = xbmcgui.ListItem(utils.get_string(30011))
    elif _type == "search":
        new_item = xbmcgui.ListItem(utils.get_string(30201))
    new_item.setArt(new_art)
    options.append(new_item)

    if group_id:
        index = ids.index(group_id) + 1

    for group in groups:
        item = xbmcgui.ListItem(group["label"])
        art = folder_shortcut
        if group["type"] == "widget":
            art = folder_sync
        elif group["type"] == "search":
            art = folder_search
        item.setArt(art)
        options.append(item)

    dialog = xbmcgui.Dialog()
    choice = dialog.select(
        utils.get_string(30036), options, preselect=index, useDetails=True
    )
    del dialog

    if choice < 0:
        dialog = xbmcgui.Dialog()
        dialog.notification("AutoWidget", utils.get_string(30021))
        del dialog
    elif choice == 0 and _type in [
        "widget",
        "shortcut",
        "search",
    ]:  # TODO: Test this bit of refactoring
        return _group_dialog(_type, add_group(_type))
    else:
        return groups[choice - offset]


def add_group(target, group_name=""):
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading=utils.get_string(30023), defaultt=group_name)
    group_id = ""

    if group_name:
        group_id = utils.get_unique_id(group_name)
        filename = os.path.join(_addon_data, "{}.group".format(group_id))
        art = folder_shortcut
        if target == "widget":
            art = folder_sync
        elif target == "search":
            art = folder_search

        group_def = {
            "label": group_name,
            "type": target,
            "paths": [],
            "id": group_id,
            "art": art,
            "version": settings.get_addon_info("version"),
            "content": None,
        }

        utils.write_json(filename, group_def)
    else:
        dialog.notification("AutoWidget", utils.get_string(30024))

    del dialog
    return group_id


def copy_group(group_id, type):
    old_group_def = manage.get_group_by_id(group_id)

    new_group_id = add_group(type, old_group_def.get("label"))
    if not new_group_id:
        return
    new_group_def = manage.get_group_by_id(new_group_id)
    new_group_def["art"] = old_group_def.get("art", {})
    new_group_def["content"] = old_group_def.get(
        "content", new_group_def.get("content", "files")
    )

    paths = old_group_def.get("paths", [])
    new_group_def["paths"] = manage.choose_paths(
        utils.get_string(30121), paths, indices=False
    )
    manage.write_path(new_group_def)

    utils.update_container()


def _add_path(group_def, labels, over=False):
    labels["id"] = utils.get_unique_id(labels["label"])
    labels["version"] = settings.get_addon_info("version")

    if not over:
        dialog = xbmcgui.Dialog()
        if group_def["type"] == "shortcut":
            heading = utils.get_string(30028)
        elif group_def["type"] == "widget":
            heading = utils.get_string(30029)
        elif group_def["type"] == "search":
            heading = utils.get_string(30202)
            term = dialog.input(heading=utils.get_string(30203))
            # TODO: Seems some (most?) addons URL encode their search queries by default...
            #       Using a non-encoded query seems to work just fine, but replacement
            #       doesn't quite "just work" here, because the user needs to enter their
            #       "Search Term" as a URL-encoded string. This also doesn't handle different
            #       cases or anything unexpected at all.
            labels["file"]["file"] = labels["file"]["file"].replace(
                term, "{}-searchterm".format(labels["id"])
            )

        labels["label"] = dialog.input(heading=heading, defaultt=labels["label"])
        del dialog

    if labels["target"] == "settings":
        labels["file"]["filetype"] = "file"
        labels["file"]["file"] = labels["file"]["file"].split("&")[0]
    elif labels["target"] == "shortcut" and labels["file"]["filetype"] == "file":
        labels["content"] = None

    manage.write_path(group_def, path_def=labels)


def _copy_path(path_def):
    group_id = add_group(path_def["target"], path_def["label"])
    if not group_id:
        return

    group_def = manage.get_group_by_id(group_id)
    files, hash = refresh.get_files_list(path_def["file"]["file"])
    if not files:
        return

    for file in files:
        if file.get("type") in ["movie", "episode", "musicvideo", "song"]:
            continue

        labels = build_labels("json", file, path_def["target"])
        _add_path(group_def, labels, over=True)
    dialog = xbmcgui.Dialog()
    dialog.notification(
        "AutoWidget", utils.get_string(30105).format(len(files), group_def["label"])
    )
    del dialog
