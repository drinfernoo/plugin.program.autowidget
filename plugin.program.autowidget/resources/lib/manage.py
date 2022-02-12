import xbmcgui
import xbmcvfs

import os
import random

from resources.lib.common import settings
from resources.lib.common import utils

_addon_data = settings.get_addon_info("profile")
_userdata = "special://profile/"
_skin_shortcuts = settings.get_addon_info("profile", addon="script.skinshortcuts")


def clean(widget_id=None, notify=False, all=False):
    if all:
        for widget in find_defined_widgets():
            clean(widget_id=widget["id"])
        return find_defined_widgets()

    files = []
    dialog = xbmcgui.Dialog()

    params = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "Addons.GetAddons",
        "params": {"type": "xbmc.gui.skin"},
    }
    addons = utils.call_jsonrpc(params)
    if "error" not in addons:
        for addon in addons["result"]["addons"]:
            path = os.path.join(
                settings.get_addon_info("profile", addon=addon["addonid"]),
                "settings.xml",
            )
            if xbmcvfs.exists(path):
                files.append(path)
    if _skin_shortcuts and xbmcvfs.exists(_skin_shortcuts):
        for xml in xbmcvfs.listdir(_skin_shortcuts)[1]:
            ext = xml.split(".")
            if ext[-1] in ["xml", "properties"]:
                path = os.path.join(_skin_shortcuts, xml)
                files.append(path)

    removed = 0

    if widget_id:
        found = False
        for file in files:
            if widget_id in utils.read_file(file):
                found = True
                utils.log("{} found in {}; not cleaning".format(widget_id, file))
                break
        if not found:
            utils.log("{} not found; cleaning".format(widget_id))
            utils.remove_file(os.path.join(_addon_data, "{}.widget".format(widget_id)))
            del dialog
            return True
        del dialog
        return False

    for widget in find_defined_widgets():
        found = False
        if get_group_by_id(widget["group"]):
            found = True
        else:
            for file in files:
                if widget["id"] in utils.read_file(file):
                    found = True
                    utils.log("{} found in {}; not cleaning".format(widget["id"], file))
                    break
        if not found:
            utils.log("{} not found; cleaning".format(widget["id"]))
            utils.remove_file(
                os.path.join(_addon_data, "{}.widget".format(widget["id"]))
            )
            removed += 1
    if notify:
        dialog.notification(
            "AutoWidget",
            utils.get_string(30105).format("No" if removed == 0 else removed),
        )
        del dialog
    del dialog


def initialize(group_def, action, widget_id, save=True, keep=None):
    duration = settings.get_setting_float("service.refresh_duration")
    paths = group_def.get("paths", [])
    path_def = []
    cycle_paths = []

    path_idx = 0
    if action != "merged":
        if action == "static" and keep is not None:
            path_def = paths[keep]["id"]
        elif action in ["random", "next"]:
            if keep is None:
                path_idx = random.randrange(len(paths)) if action == "random" else 0
            else:
                path_idx = (
                    keep[random.randrange(len(keep))] if action == "random" else keep[0]
                )
                for idx in keep:
                    cycle_paths.append(paths[idx]["id"])
            path_def = paths[path_idx]["id"]
    elif action == "merged" and keep:
        for idx in keep:
            path_def.append(paths[idx]["id"])

    params = {
        "action": action,
        "id": widget_id,
        "group": group_def["id"],
        "refresh": duration,
        "path": path_def,
        "version": settings.get_addon_info("version"),
        "current": path_idx,
    }
    if cycle_paths:
        params["cycle_paths"] = cycle_paths

    if save:
        save_path_details(params)

    return params


def write_path(group_def, path_def=None, update=""):
    filename = os.path.join(_addon_data, "{}.group".format(group_def["id"]))

    if path_def:
        if update:
            for path in group_def["paths"]:
                if path["id"] == update:
                    path["version"] = settings.get_addon_info("version")
                    group_def["paths"][group_def["paths"].index(path)] = path_def
        else:
            group_def["paths"].append(path_def)

    group_def["version"] = settings.get_addon_info("version")
    utils.write_json(filename, group_def)


def save_path_details(params):
    path_to_saved = os.path.join(_addon_data, "{}.widget".format(params["id"]))
    params["version"] = settings.get_addon_info("version")
    utils.write_json(path_to_saved, params)

    return params


def get_group_by_id(group_id):
    if not group_id:
        return {}

    filename = "{}.group".format(group_id)
    path = os.path.join(_addon_data, filename)

    try:
        group_def = utils.read_json(path)
    except ValueError:
        utils.log("Unable to parse: {}".format(path))
        return

    return group_def


def get_path_by_id(path_id, group_id=None):
    if not path_id:
        return {}

    for defined in find_defined_paths(group_id):
        if defined.get("id", "") == path_id:
            return defined


def get_widget_by_id(widget_id, group_id=None):
    if not widget_id:
        return {}

    for defined in find_defined_widgets(group_id):
        if defined.get("id", "") == widget_id:
            return defined


def highest_group_sort_order():
    groups = find_defined_groups()
    return groups[-1].get("sort_order", 0) if len(groups) > 0 else 0


def find_defined_groups(_type=""):
    groups = []
    sort_order = 0

    for filename in [
        x for x in xbmcvfs.listdir(_addon_data)[1] if x.endswith(".group")
    ]:
        path = os.path.join(_addon_data, filename)

        group_def = utils.read_json(path)
        if group_def:
            if not group_def.get("sort_order"):
                group_def["sort_order"] = "{}".format(sort_order)
                utils.write_json(path, group_def)
            if group_def.get("content") is None:
                group_def["content"] = ""
                utils.write_json(path, group_def)

            if _type:
                if group_def["type"] == _type:
                    groups.append(group_def)
            else:
                groups.append(group_def)
        sort_order += 1

    return sorted(groups, key=lambda x: int(x["sort_order"]))


def find_defined_paths(group_id=None):
    if group_id:
        filename = "{}.group".format(group_id)
        path = os.path.join(_addon_data, filename)

        group_def = utils.read_json(path)
        if group_def:
            return group_def.get("paths", [])
        else:
            return []
    else:
        paths = []
        for group in find_defined_groups():
            group_paths = find_defined_paths(group_id=group.get("id"))
            for path in group_paths:
                paths.append(path)
        return paths


def find_defined_widgets(group_id=None):
    addon_files = xbmcvfs.listdir(_addon_data)[1]
    widgets = []

    widget_files = [x for x in addon_files if x.endswith(".widget")]
    for widget_file in widget_files:
        widget_def = utils.read_json(os.path.join(_addon_data, widget_file))

        if widget_def:
            if not group_id:
                widgets.append(widget_def)
            elif group_id == widget_def["group"]:
                widgets.append(widget_def)

    return widgets


def choose_paths(
    label=utils.get_string(30121),
    paths=None,
    threshold=None,
    indices=True,
    single=False,
):
    if paths is None:
        return []

    idx = None
    idxs = []
    dialog = xbmcgui.Dialog()

    if len(paths) == 1:
        if indices:
            return 0 if single else [0]
        else:
            return paths[0] if single else [paths[0]]

    if single:
        idx = dialog.select(
            label,
            [i["label"] for i in paths],
        )
    else:
        idxs = dialog.multiselect(
            label,
            [i["label"] for i in paths],
            preselect=(
                list(range(len(paths)))
                if len(paths) <= threshold or threshold == -1
                else []
            )
            if threshold is not None
            else list(range(len(paths))),
        )
    del dialog

    if single and idx is not None:
        return idx if indices else paths[idx]
    elif not single and idxs is not None:
        return idxs if indices else [paths[i] for i in idxs]
