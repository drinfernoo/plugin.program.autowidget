from kodi_six import xbmcgui

import re
import uuid

import six

from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import directory
from resources.lib.common import utils

folder_shortcut = utils.get_art("folder-shortcut")
folder_sync = utils.get_art("folder-sync")
folder_next = utils.get_art("folder-next")
folder_merged = utils.get_art("folder-dots")
info = utils.get_art("information_outline")
merge = utils.get_art("merge")
next = utils.get_art("next")
next_page = utils.get_art("next_page")
refresh_art = utils.get_art("refresh")
remove = utils.get_art("remove")
share = utils.get_art("share")
shuffle = utils.get_art("shuffle")
spray_bottle = utils.get_art("spray-bottle")
sync = utils.get_art("sync")
tools = utils.get_art("tools")
unpack = utils.get_art("unpack")

_next = utils.get_string(209, kodi=True)
_previous = utils.get_string(210, kodi=True)
_next_page = utils.get_string(33078, kodi=True)


def root_menu():
    directory.add_menu_item(
        title=30007,
        params={"mode": "group"},
        art=utils.get_art("folder"),
        isFolder=True,
    )
    directory.add_menu_item(
        title=30052,
        params={"mode": "widget"},
        art=utils.get_art("folder"),
        isFolder=True,
    )
    directory.add_menu_item(
        title=30008, params={"mode": "tools"}, art=utils.get_art("tools"), isFolder=True
    )

    return True, "AutoWidget"


def my_groups_menu():
    groups = manage.find_defined_groups()
    if len(groups) > 0:
        for group in groups:
            group_name = group["label"]
            group_id = group["id"]
            group_type = group["type"]

            cm = [
                (
                    utils.get_string(30042),
                    (
                        "RunPlugin("
                        "plugin://plugin.program.autowidget/"
                        "?mode=manage"
                        "&action=edit"
                        "&group={})"
                    ).format(group_id),
                )
            ]

            directory.add_menu_item(
                title=six.text_type(group_name),
                params={"mode": "group", "group": group_id},
                info=group.get("info", {}),
                art=group.get("art")
                or (
                    utils.get_art("folder-shortcut")
                    if group_type == "shortcut"
                    else utils.get_art("folder-sync")
                ),
                cm=cm,
                isFolder=True,
            )
    else:
        directory.add_menu_item(
            title=30046,
            art=utils.get_art("alert"),
            isFolder=False,
            props={"specialsort": "bottom"},
        )

    return True, utils.get_string(30007)


def group_menu(group_id):
    _window = utils.get_active_window()
    _id = uuid.uuid4()

    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        utils.log(
            '"{}" is missing, please repoint the widget to fix it.'.format(group_id),
            "error",
        )
        return False, "AutoWidget"

    group_name = group_def["label"]
    group_type = group_def["type"]
    paths = group_def["paths"]

    if len(paths) > 0:
        utils.log(
            u"Showing {} group: {}".format(group_type, six.text_type(group_name)),
            "debug",
        )
        cm = []
        art = folder_shortcut if group_type == "shortcut" else folder_sync

        for idx, path_def in enumerate(paths):
            if _window == "media":
                cm = _create_context_items(
                    group_id, path_def["id"], idx, len(paths), group_type
                )

            directory.add_menu_item(
                title=path_def["label"],
                params={"mode": "path", "group": group_id, "path_id": path_def["id"]},
                info=path_def["file"],
                art=path_def["file"].get("art", art),
                cm=cm,
                isFolder=False,
            )

        if _window != "home":
            _create_action_items(group_def, _id)
    else:
        directory.add_menu_item(
            title=30019,
            art=utils.get_art("alert"),
            isFolder=False,
            props={"specialsort": "bottom"},
        )

    return True, group_name


def active_widgets_menu():
    widgets = sorted(
        manage.clean(all=True), key=lambda x: x.get("updated", 0), reverse=True
    )

    if len(widgets) > 0:
        for widget_def in widgets:
            widget_id = widget_def.get("id", "")
            action = widget_def.get("action", "")
            group = widget_def.get("group", "")
            path_def = widget_def.get("path", {})

            group_def = manage.get_group_by_id(group)

            title = ""
            if path_def and group_def:
                try:
                    if action != "merged":
                        if isinstance(path_def, dict):
                            label = path_def["label"].encode("utf-8")
                        else:
                            label = widget_def["stack"][0]["label"].encode("utf-8")
                        group_def["label"] = group_def["label"].encode("utf-8")
                    else:
                        label = utils.get_string(30102).format(len(path_def))
                except:
                    pass

                title = "{} - {}".format(
                    six.ensure_text(label), six.ensure_text(group_def["label"])
                )
            elif group_def:
                title = group_def.get("label")

            art = {}
            params = {}
            cm = []
            if not action:
                art = folder_shortcut
                title = utils.get_string(30018).format(title)
            else:
                if action in ["random", "next"]:
                    art = shuffle
                    cm.append(
                        (
                            utils.get_string(30047),
                            (
                                "RunPlugin("
                                "plugin://plugin.program.autowidget/"
                                "?mode=refresh"
                                "&id={})"
                            ).format(widget_id),
                        )
                    )
                elif action == "merged":
                    art = merge
                elif action == "static":
                    art = utils.get_art("folder")

            cm.append(
                (
                    utils.get_string(30048),
                    (
                        "RunPlugin("
                        "plugin://plugin.program.autowidget/"
                        "?mode=manage"
                        "&action=edit_widget"
                        "&id={})"
                    ).format(widget_id),
                )
            )

            if not group_def:
                title = "{} - [COLOR firebrick]{}[/COLOR]".format(
                    widget_id, utils.get_string(30049)
                )

            directory.add_menu_item(
                title=title,
                art=art,
                params={"mode": "group", "group": group},
                cm=cm[1:] if not action else cm,
                isFolder=True,
            )
    else:
        directory.add_menu_item(
            title=30050,
            art=utils.get_art("alert"),
            isFolder=False,
            props={"specialsort": "bottom"},
        )

    return True, utils.get_string(30052)


def tools_menu():
    directory.add_menu_item(
        title=30006,
        params={"mode": "force"},
        art=utils.get_art("refresh"),
        info={"plot": utils.get_string(30012)},
        isFolder=False,
    )
    directory.add_menu_item(
        title=30103,
        params={"mode": "clean"},
        art=utils.get_art("spray-bottle"),
        isFolder=False,
    )
    directory.add_menu_item(
        title=30043,
        params={"mode": "wipe"},
        art=utils.get_art("remove"),
        isFolder=False,
    )
    directory.add_menu_item(
        title=30101,
        params={"mode": "skindebug"},
        art=utils.get_art("bug-outline"),
        isFolder=False,
    )

    return True, utils.get_string(30008)


def show_path(
    group_id, path_label, widget_id, path, idx=0, titles=None, num=1, merged=False
):
    hide_watched = utils.get_setting_bool("widgets.hide_watched")
    show_next = utils.get_setting_int("widgets.show_next")
    paged_widgets = utils.get_setting_bool("widgets.paged")
    default_color = utils.get_setting("ui.color")

    widget_def = manage.get_widget_by_id(widget_id)
    if not widget_def:
        return True, "AutoWidget"

    if not titles:
        titles = []

    files = refresh.get_files_list(path, widget_id)
    if not files:
        return titles, path_label

    utils.log("Loading items from {}".format(path), "debug")

    if isinstance(widget_def["path"], list):
        color = widget_def["path"][idx].get("color", default_color)
    elif isinstance(widget_def["path"], six.text_type):
        color = widget_def["stack"][0].get("color", default_color)
    else:
        color = widget_def["path"].get("color", default_color)

    stack = widget_def.get("stack", [])
    if stack:
        title = _previous
        # title = utils.get_string(30085).format(len(stack))
        directory.add_menu_item(
            title=title,
            params={
                "mode": "path",
                "action": "update",
                "id": widget_id,
                "path": "",
                "target": "back",
            },
            art=utils.get_art("back", color),
            isFolder=num > 1,
            props={"specialsort": "top", "autoLabel": path_label},
        )

    for pos, file in enumerate(files):
        properties = {"autoLabel": path_label, "autoID": widget_id}
        next_item = False
        prev_item = False

        if "customproperties" in file:
            for prop in file["customproperties"]:
                properties[prop] = file["customproperties"][prop]

        if pos == len(files) - 1:
            next_item = _is_page_item(file.get("label", ""))
        elif pos == 0:
            prev_item = _is_page_item(file.get("label", ""), next=False)

        if (prev_item and stack) or (next_item and show_next == 0):
            continue
        elif next_item and show_next > 0:
            label = _next_page
            properties["specialsort"] = "bottom"

            if num > 1:
                if show_next == 1:
                    continue

                label = "{} - {}".format(label, path_label)

            update_params = {
                "mode": "path",
                "action": "update",
                "id": widget_id,
                "path": file["file"],
                "target": "next",
            }

            directory.add_menu_item(
                title=label,
                params=update_params if paged_widgets and not merged else None,
                path=file["file"] if not paged_widgets or merged else None,
                art=utils.get_art("next_page", color),
                info=file,
                isFolder=not paged_widgets or merged,
                props=properties,
            )
        else:
            title = {
                "type": file.get("type"),
                "label": file.get("label"),
                "imdbnumber": file.get("imdbnumber"),
                "showtitle": file.get("showtitle"),
            }
            dupe = refresh.is_duplicate(title, titles)

            if (hide_watched and file.get("playcount", 0) > 0) or dupe:
                continue

            art = file.get("art", {})
            if not art.get("landscape") and art.get("thumb"):
                art["landscape"] = art["thumb"]

            directory.add_menu_item(
                title=file["label"],
                path=file["file"],
                art=art,
                info=file,
                isFolder=file["filetype"] == "directory",
                props=properties,
            )

            titles.append(title)

    return titles, path_label


def call_path(path_id):
    path_def = manage.get_path_by_id(path_id)
    if not path_def:
        return

    utils.call_builtin("Dialog.Close(busydialog)", 500)
    final_path = ""

    if path_def["target"] == "settings":
        final_path = "Addon.OpenSettings({})".format(
            path_def["file"]["file"]
            .replace("plugin://", "")
            .replace("script://", "")
            .split("/")[0]
        )
    elif (
        path_def["target"] == "shortcut"
        and path_def["file"]["filetype"] == "file"
        and path_def["content"] != "addons"
    ):
        if path_def["file"]["file"] == "addons://install/":
            final_path = "InstallFromZip"
        elif not path_def["content"] or path_def["content"] == "files":
            if path_def["file"]["file"].startswith("androidapp://sources/apps/"):
                final_path = "StartAndroidActivity({})".format(
                    path_def["file"]["file"].replace("androidapp://sources/apps/", "")
                )
            elif path_def["file"]["file"].startswith("pvr://"):
                final_path = "PlayMedia({})".format(path_def["file"]["file"])
            else:
                final_path = "RunPlugin({})".format(path_def["file"]["file"])
        elif (
            all(i in path_def["file"]["file"] for i in ["(", ")"])
            and "://" not in path_def["file"]["file"]
        ):
            final_path = path_def["file"]["file"]
        else:
            final_path = "PlayMedia({})".format(path_def["file"]["file"])
    elif (
        path_def["target"] == "widget"
        or path_def["file"]["filetype"] == "directory"
        or path_def["content"] == "addons"
    ):
        final_path = "ActivateWindow({},{},return)".format(
            path_def.get("window", "Videos"), path_def["file"]["file"]
        )

    if final_path:
        utils.log("Calling path from {} using {}".format(path_id, final_path), "debug")
        utils.call_builtin(final_path)

    return False, path_def["label"]


def path_menu(group_id, action, widget_id):
    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        directory.add_menu_item(
            title=30051,
            info={"plot": utils.get_string(30053)},
            art=utils.get_art("alert"),
            isFolder=True,
        )
        return True, "AutoWidget"

    group_name = group_def.get("label", "")
    paths = group_def.get("paths", [])
    if len(paths) == 0:
        directory.add_menu_item(title=30019, art=utils.get_art("alert"), isFolder=True)
        return True, group_name

    widget_def = manage.get_widget_by_id(widget_id, group_id)
    if not widget_def:
        dialog = xbmcgui.Dialog()
        if action == "static":
            idx = dialog.select(utils.get_string(30088), [i["label"] for i in paths])
            if idx == -1:
                return True, "AutoWidget"

            widget_def = manage.initialize(group_def, action, widget_id, keep=idx)
        elif action == "cycling":
            idx = dialog.select(
                utils.get_string(30059),
                [utils.get_string(30057), utils.get_string(30058)],
            )
            if idx == -1:
                return True, "AutoWidget"

            _action = "random" if idx == 0 else "next"
            widget_def = manage.initialize(group_def, _action, widget_id)

    if widget_def:
        widget_path = widget_def.get("path", {})

        if isinstance(widget_path, dict):
            _label = widget_path["label"]
            widget_path = widget_path["file"]["file"]
        else:
            stack = widget_def.get("stack", [])
            if stack:
                _label = stack[0]["label"]
            else:
                _label = widget_def.get("label", "")
        utils.log("Showing widget {}".format(widget_id), "debug")
        titles, cat = show_path(group_id, _label, widget_id, widget_path)
        return titles, cat
    else:
        directory.add_menu_item(
            title=30045, art=utils.get_art("information_outline"), isFolder=True
        )
        return True, group_name


def merged_path(group_id, widget_id):
    _window = utils.get_active_window()

    group_def = manage.get_group_by_id(group_id)
    group_name = group_def.get("label", "")
    paths = group_def.get("paths", [])
    if len(paths) == 0:
        directory.add_menu_item(title=30019, art=utils.get_art("alert"), isFolder=False)
        return True, group_name

    widget_def = manage.get_widget_by_id(widget_id, group_id)
    if widget_def and _window != "dialog":
        paths = widget_def["path"]
    elif not widget_def:
        dialog = xbmcgui.Dialog()
        idxs = dialog.multiselect(
            utils.get_string(30089),
            [i["label"] for i in paths],
            preselect=list(range(len(paths))) if len(paths) <= 5 else [],
        )

        if idxs is not None:
            if len(idxs) > 0:
                widget_def = manage.initialize(
                    group_def, "merged", widget_id, keep=idxs
                )
                paths = widget_def["path"]

    if widget_def:
        titles = []
        for idx, path_def in enumerate(paths):
            titles, cat = show_path(
                group_id,
                path_def["label"],
                widget_id,
                path_def["file"]["file"],
                idx=idx,
                titles=titles,
                num=len(paths),
                merged=True,
            )

        return titles, cat
    else:
        directory.add_menu_item(
            title=30045, art=utils.get_art("information_outline"), isFolder=True
        )
        return True, group_name


def _create_context_items(group_id, path_id, idx, length, target):
    if target not in ["shortcut", "widget"]:
        main_action = utils.get_string(30048)
    else:
        main_action = (
            utils.get_string(30031) if target == "shortcut" else utils.get_string(30114)
        )

    cm = [
        (
            main_action,
            (
                "RunPlugin("
                "plugin://plugin.program.autowidget/"
                "?mode=manage"
                "&action=edit_path"
                "&group={}"
                "&path_id={})"
            ).format(group_id, path_id),
        ),
        (
            utils.get_string(30015) if idx > 0 else utils.get_string(30087),
            (
                "RunPlugin("
                "plugin://plugin.program.autowidget/"
                "?mode=manage"
                "&action=shift_path"
                "&target=up"
                "&group={}"
                "&path_id={})"
            ).format(group_id, path_id),
        ),
        (
            utils.get_string(30016) if idx < length - 1 else utils.get_string(30086),
            (
                "RunPlugin("
                "plugin://plugin.program.autowidget/"
                "?mode=manage"
                "&action=shift_path"
                "&target=down"
                "&group={}"
                "&path_id={})"
            ).format(group_id, path_id),
        ),
    ]

    return cm


def _create_action_items(group_def, _id):
    refresh = "$INFO[Window(10000).Property(autowidget-{}-refresh)]".format(_id)
    props = {"specialsort": "bottom"}

    group_id = group_def["id"]
    group_name = group_def["label"]
    group_type = group_def["type"]

    if group_type == "widget":
        directory.add_separator(title=30009, char="/", sort="bottom")
        directory.add_menu_item(
            title=utils.get_string(30054).format(six.text_type(group_name)),
            params={
                "mode": "path",
                "action": "static",
                "group": group_id,
                "id": six.text_type(_id),
                "refresh": refresh,
            },
            art=utils.get_art("folder"),
            isFolder=True,
            props=props,
        )
        directory.add_menu_item(
            title=utils.get_string(30017).format(six.text_type(group_name)),
            params={
                "mode": "path",
                "action": "cycling",
                "group": group_id,
                "id": six.text_type(_id),
                "refresh": refresh,
            },
            art=utils.get_art("shuffle"),
            isFolder=True,
            props=props,
        )
        directory.add_menu_item(
            title=utils.get_string(30066).format(six.text_type(group_name)),
            params={
                "mode": "path",
                "action": "merged",
                "group": group_id,
                "id": six.text_type(_id),
            },
            art=utils.get_art("merge"),
            isFolder=True,
            props=props,
        )


def _is_page_item(label, next=True):
    tag_pattern = "(\[[^\]]*\])"
    page_count_pattern = "(?:\W*(?:(?:\d+\D*\d*))\W*)?"
    base_pattern = "^(?:(?:\W*)?\s*(?:{})+\s*{})?$"
    next_pattern = base_pattern.format(_next.lower(), page_count_pattern)
    next_page_pattern = base_pattern.format(_next_page.lower(), page_count_pattern)
    prev_pattern = "^(?:(?:(?:{})\s*(?:page)?)|(?:back)?)\s*{}$".format(_previous, page_count_pattern)

    cleaned_title = re.sub(tag_pattern, "", label.lower()).strip()
    next_page_words = _next_page.split("\s*")

    if next:
        contains_next = re.search(next_pattern, cleaned_title) is not None
        contains_next_page = re.search(next_page_pattern, cleaned_title) is not None
        word_matches = [
            re.search(base_pattern.format(i, page_count_pattern), cleaned_title)
            for i in next_page_words
        ]
        return (
            contains_next
            or contains_next_page
            or any(i is not None for i in word_matches)
        )
    else:
        return re.search(prev_pattern, cleaned_title)
