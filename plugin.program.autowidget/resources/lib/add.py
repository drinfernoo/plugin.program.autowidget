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

_addon_data = settings.get_addon_info("profile")

shortcut_types = [
    30032,
    30033,
    30059,
    30060,
    30034,
]

type_labels = [
    30144,
    30145,
    30146,
    30147,
    30148,
]

folder_shortcut = utils.get_art("folder-shortcut")
folder_sync = utils.get_art("folder-sync")
folder_settings = utils.get_art("folder-settings")
folder_clone = utils.get_art("folder-clone")
folder_explode = utils.get_art("folder-explode")


def add(labels):
    _type = _add_as(labels["file"])
    if not _type:
        return

    if _type not in ["clone", "explode"]:
        labels["target"] = _type
        group_def = _group_dialog(_type)
        if group_def:
            _add_path(group_def, labels)
    else:
        labels["target"] = "shortcut" if _type == "clone" else "widget"
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

        for i in utils.get_info_keys() + ["DBType"]:
            info = utils.get_infolabel("ListItem.{}".format(i.capitalize()))
            if info and not info.startswith("ListItem"):
                path_def[i if i != "DBType" else "type"] = info

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
        path = path.replace("addons://dependencies/", "dependency://")
    if "plugin://plugin.video.themoviedb.helper" in path and not "&widget=True" in path:
        path += "&widget=True"
    labels["file"]["file"] = path

    labels["color"] = settings.get_setting_string("ui.color")

    for _key in utils.windows:
        if any(i in path for i in utils.windows[_key]):
            labels["window"] = _key

    return labels


def _add_as(path_def):
    art = [folder_shortcut, folder_sync, folder_clone, folder_explode, folder_settings]

    path = path_def["file"]
    types = list(zip(shortcut_types[:], type_labels[:]))
    if path_def["filetype"] == "directory" and utils.get_active_window() != "home":
        types = list(zip(shortcut_types[:4], type_labels[:4]))
    else:
        if any(
            i in path for i in ["addons://user", "plugin://", "script://"]
        ) and not parse_qsl(path):
            pass
        elif "dependency://" in path:
            types = [(shortcut_types[4], type_labels[4])]
        else:
            types = [(shortcut_types[0], type_labels[0])]

    options = []
    for idx, type in enumerate(types):
        li = xbmcgui.ListItem(utils.get_string(type[0]), utils.get_string(type[1]))

        li.setArt(art[idx])
        options.append(li)

    dialog = xbmcgui.Dialog()
    idx = dialog.select(utils.get_string(30061), options, useDetails=True)
    del dialog

    if idx < 0:
        return

    chosen = types[idx][0]
    if chosen == shortcut_types[0]:
        return "shortcut"
    elif chosen == shortcut_types[1]:
        return "widget"
    elif chosen == shortcut_types[2]:
        return "clone"
    elif chosen == shortcut_types[3]:
        return "explode"
    elif chosen == shortcut_types[4]:
        return "settings"


def _group_dialog(_type, group_id=None):
    _type = "shortcut" if _type == "settings" else _type
    groups = manage.find_defined_groups(_type)
    ids = [group["id"] for group in groups]

    index = -1
    options = []
    offset = 1

    if _type == "widget":
        new_widget = xbmcgui.ListItem(utils.get_string(30010))
        new_widget.setArt(folder_sync)
        options.append(new_widget)
    else:
        new_shortcut = xbmcgui.ListItem(utils.get_string(30011))
        new_shortcut.setArt(folder_shortcut)
        options.append(new_shortcut)

    if group_id:
        index = ids.index(group_id) + 1

    for group in groups:
        item = xbmcgui.ListItem(group["label"])
        item.setArt(folder_sync if group["type"] == "widget" else folder_shortcut)
        options.append(item)

    dialog = xbmcgui.Dialog()
    choice = dialog.select(
        utils.get_string(30035), options, preselect=index, useDetails=True
    )
    del dialog

    if choice < 0:
        dialog = xbmcgui.Dialog()
        dialog.notification("AutoWidget", utils.get_string(30020))
        del dialog
    elif (choice, _type) == (0, "widget"):
        return _group_dialog(_type, add_group("widget"))
    elif choice == 0:
        return _group_dialog(_type, add_group("shortcut"))
    else:
        return groups[choice - offset]


def add_group(target, group_name=""):
    dialog = xbmcgui.Dialog()
    group_name = dialog.input(heading=utils.get_string(30022), defaultt=group_name)
    group_id = ""

    if group_name:
        group_id = utils.get_unique_id(group_name)
        filename = os.path.join(_addon_data, "{}.group".format(group_id))
        group_def = {
            "label": group_name,
            "type": target,
            "paths": [],
            "id": group_id,
            "art": folder_sync if target == "widget" else folder_shortcut,
            "version": settings.get_addon_info("version"),
            "content": "",
            "sort_order": "{}".format(int(manage.highest_group_sort_order()) + 1),
        }

        utils.write_json(filename, group_def)
    else:
        dialog.notification("AutoWidget", utils.get_string(30023))

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
        utils.get_string(30120), paths, indices=False
    )
    manage.write_path(new_group_def)

    utils.update_container()


def _add_path(group_def, labels, over=False):
    if not over:
        if group_def["type"] == "shortcut":
            heading = utils.get_string(30027)
        elif group_def["type"] == "widget":
            heading = utils.get_string(30028)

        dialog = xbmcgui.Dialog()
        labels["label"] = dialog.input(heading=heading, defaultt=labels["label"])
        del dialog

    labels["id"] = utils.get_unique_id(labels["label"])
    labels["version"] = settings.get_addon_info("version")

    if labels["target"] == "settings":
        labels["file"]["filetype"] = "file"
        labels["file"]["file"] = labels["file"]["file"].split("&")[0]
    elif labels["target"] == "shortcut" and labels["file"]["filetype"] == "file":
        labels["content"] = None

    manage.write_path(group_def, path_def=labels)


def _copy_path(path_def):
    group_def = _group_dialog(path_def['target'])
    if not group_def:
        return

    progress = xbmcgui.DialogProgressBG()
    progress.create("AutoWidget", utils.get_string(30141))
    progress.update(1, "AutoWidget", utils.get_string(30142))

    files, hash = refresh.get_files_list(path_def["file"]["file"], background=False)
    if not files:
        progress.close()
        return
    done = 0
    for file in files:
        done += 1
        if file["type"] in ["movie", "episode", "musicvideo", "song"]:
            continue
        progress.update(
            int(done / float(len(files)) * 100),
            heading=utils.get_string(30141),
            message=file.get("label"),
        )

        labels = build_labels("json", file, path_def["target"])
        _add_path(group_def, labels, over=True)
    progress.close()
    del progress
    dialog = xbmcgui.Dialog()
    dialog.notification(
        "AutoWidget", utils.get_string(30104).format(len(files), group_def["label"])
    )
    del dialog
