import xbmcgui

import re
import uuid

import six

from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import cache
from resources.lib.common import directory
from resources.lib.common import settings
from resources.lib.common import utils

folder_shortcut = utils.get_art("folder-shortcut")
folder_sync = utils.get_art("folder-sync")
folder_next = utils.get_art("folder-next")
folder_merged = utils.get_art("folder-dots")
info = utils.get_art("information-outline")
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

_next_page = utils.get_string(30132)
_previous = utils.get_string(30133)
_previous_page = utils.get_string(30134)
_back = utils.get_string(30135)
_page = utils.get_string(30136)


def root_menu():
    directory.add_menu_item(
        title=30007,
        params={"mode": "group"},
        art=utils.get_art("folder"),
        isFolder=True,
    )
    directory.add_menu_item(
        title=30051,
        params={"mode": "widget"},
        art=utils.get_art("folder"),
        isFolder=True,
    )
    directory.add_menu_item(
        title=30008, params={"mode": "tools"}, art=utils.get_art("tools"), isFolder=True
    )

    return True, "AutoWidget", None


def my_groups_menu():
    groups = manage.find_defined_groups()
    if len(groups) > 0:
        for idx, group in enumerate(groups):
            group_name = group["label"]
            group_id = group["id"]
            group_type = group["type"]

            cm = _create_group_context_items(group_id, group_type, idx, len(groups))

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
            title=30045,
            art=utils.get_art("alert"),
            isFolder=False,
            props={"specialsort": "bottom"},
        )
    directory.add_menu_item(
        title=30011,
        params={"mode": "manage", "action": "add_group", "target": "shortcut"},
        art=utils.get_art("folder-shortcut"),
        props={"specialsort": "bottom"},
    )
    directory.add_menu_item(
        title=30010,
        params={"mode": "manage", "action": "add_group", "target": "widget"},
        art=utils.get_art("folder-sync"),
        props={"specialsort": "bottom"},
    )

    return True, utils.get_string(30007), None


def group_menu(group_id):
    _window = utils.get_active_window()
    _id = uuid.uuid4()

    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        utils.log(
            '"{}" is missing, please repoint the widget to fix it.'.format(group_id),
            "error",
        )
        return False, "AutoWidget", None

    group_name = group_def["label"]
    group_type = group_def["type"]
    paths = group_def["paths"]
    content = group_def.get("content")

    if len(paths) > 0:
        utils.log(
            u"Showing {} group: {}".format(group_type, six.text_type(group_name)),
            "debug",
        )
        cm = []
        art = folder_shortcut if group_type == "shortcut" else folder_sync

        for idx, path_def in enumerate(paths):
            if _window == "media":
                cm = _create_path_context_items(
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
            title=30018,
            art=utils.get_art("alert"),
            isFolder=False,
            props={"specialsort": "bottom"},
        )

    return True, group_name, content


def active_widgets_menu():
    widgets = sorted(
        manage.clean(all=True), key=lambda x: x.get("updated", 0), reverse=True
    )

    if len(widgets) > 0:
        for widget_def in widgets:
            widget_id = widget_def.get("id", "")
            action = widget_def.get("action", "")
            group = widget_def.get("group", "")
            path_id = widget_def.get("path", {})

            group_def = manage.get_group_by_id(group)
            path_def = manage.get_path_by_id(path_id, group)

            title = ""
            label = group_def.get("label", "")
            if path_def and group_def:
                try:
                    if action != "merged":
                        label = path_def.get("label", "").encode("utf-8")
                    else:
                        label = utils.get_string(30101).format(len(path_id))
                except:
                    pass

                title = "{} - {}".format(
                    six.ensure_text(label), six.ensure_text(group_def.get("label", ""))
                )
            elif group_def:
                title = group_def.get("label")

            art = {}
            params = {}
            cm = []
            if not action:
                art = folder_shortcut
                title = utils.get_string(30017).format(title)
            else:
                if action in ["random", "next"]:
                    art = shuffle
                    cm.append(
                        (
                            utils.get_string(30046),
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
                    utils.get_string(30047),
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
                    widget_id, utils.get_string(30048)
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
            title=30049,
            art=utils.get_art("alert"),
            isFolder=False,
            props={"specialsort": "bottom"},
        )

    return True, utils.get_string(30051), None


def tools_menu():
    directory.add_menu_item(
        title=30006,
        params={"mode": "force"},
        art=utils.get_art("refresh"),
        isFolder=False,
    )
    directory.add_menu_item(
        title=30102,
        params={"mode": "clean"},
        art=utils.get_art("spray-bottle"),
        isFolder=False,
    )
    directory.add_menu_item(
        title=30042,
        params={"mode": "wipe"},
        art=utils.get_art("remove"),
        isFolder=False,
    )
    directory.add_menu_item(
        title=30100,
        params={"mode": "skindebug"},
        art=utils.get_art("bug-outline"),
        isFolder=False,
    )
    directory.add_menu_item(
        title=30116,
        params={"mode": "clear_cache"},
        art=utils.get_art("cache"),
        isFolder=False,
    )

    return True, utils.get_string(30008), None


def show_path(
    group_id,
    path_label,
    widget_id,
    widget_path,
    idx=0,
    titles=None,
    num=1,
    merged=False,
):
    hide_watched = settings.get_setting_bool("widgets.hide_watched")
    show_next = settings.get_setting_int("widgets.show_next")
    paged_widgets = settings.get_setting_bool("widgets.paged")
    default_color = settings.get_setting_string("ui.color")

    widget_def = manage.get_widget_by_id(widget_id)
    if not widget_def:
        return True, "AutoWidget", None

    content = widget_path.get("content")
    action = widget_def.get("action", "")
    if not titles:
        titles = []

    stack = widget_def.get("stack", [])
    path = widget_path["file"]["file"] if not stack else stack[-1]

    utils.log("Loading items from {}".format(path), "debug")
    files, hash = refresh.get_files_list(path, path_label, widget_id)

    color = widget_path.get("color", default_color)

    if stack:
        title = _previous
        # title = utils.get_string(30084).format(len(stack))
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
        properties = {
            "autoLabel": path_label,
            "autoID": widget_id,
            "autoAction": action,
            "autoCache": hash,
        }
        next_item = False
        prev_item = False
        is_folder = file["filetype"] == "directory"

        if pos == len(files) - 1 and is_folder:
            next_item = _is_page_item(file.get("label", ""))
        elif pos == 0 and is_folder:
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
            # Ensure we precache next page for faster access
            cache.cache_expiry(file["file"], widget_id)
        else:
            filetype = file.get("type", "")
            title = {
                "type": filetype,
                "label": file.get("label"),
                "imdbnumber": file.get("imdbnumber"),
                "showtitle": file.get("showtitle"),
            }
            dupe = refresh.is_duplicate(title, titles)

            if (hide_watched and file.get("playcount", 0) > 0) or dupe:
                continue

            filepath = ""
            info_type = directory.info_types.get(filetype, "video")
            if (
                path.startswith("library://{}/".format(info_type))
                or path.startswith("{}db://".format(info_type) or path.endswith(".xsp"))
            ) and is_folder:
                filepath = directory.make_library_path(
                    info_type, filetype, file.get("id", -1)
                )

            directory.add_menu_item(
                title=file["label"],
                path=file["file"] if not filepath else filepath,
                info=file,
                isFolder=is_folder,
                props=properties,
            )

            titles.append(title)

    return titles, path_label, content


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
            .replace("dependency://", "")
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
            elif path_def["file"]["file"].startswith("pvr://") or path_def["file"].get("type") in ["video", "movie", "episode", "musicvideo", "music", "song"]:
                final_path = "PlayMedia(\"{}\")".format(path_def["file"]["file"])
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


def path_menu(group_id, action, widget_id):
    group_def = manage.get_group_by_id(group_id)
    if not group_def:
        directory.add_menu_item(
            title=30050,
            info={"plot": utils.get_string(30052)},
            art=utils.get_art("alert"),
            isFolder=True,
        )
        return True, "AutoWidget", None

    group_name = group_def.get("label", "")
    paths = group_def.get("paths", [])
    if len(paths) == 0:
        directory.add_menu_item(title=30018, art=utils.get_art("alert"), isFolder=True)
        return True, group_name, None

    widget_def = manage.get_widget_by_id(widget_id, group_id)
    if not widget_def:
        dialog = xbmcgui.Dialog()
        if action == "static":
            idx = manage.choose_paths(
                utils.get_string(30087), paths, indices=True, single=True
            )
            if idx == -1:
                return True, "AutoWidget", None

            widget_def = manage.initialize(group_def, action, widget_id, keep=idx)
        elif action == "cycling":
            idx = dialog.select(
                utils.get_string(30058),
                [utils.get_string(30056), utils.get_string(30057)],
            )
            if idx == -1:
                del dialog
                return True, "AutoWidget", None

            _action = "random" if idx == 0 else "next"

            cycle_paths = manage.choose_paths(
                utils.get_string(30122), paths, threshold=-1, indices=True
            )

            widget_def = manage.initialize(
                group_def, _action, widget_id, keep=cycle_paths
            )
        del dialog

    if widget_def:
        widget_path = widget_def.get("path", "")

        # simple compatibility with pre-3.3.0 widgets
        if isinstance(widget_path, dict):
            widget_path = widget_def.get("path", {}).get("id", "")
            widget_def["path"] = widget_path
            manage.save_path_details(widget_def)

        widget_path = manage.get_path_by_id(widget_path, group_id)

        _label = ""
        if isinstance(widget_path, dict):
            _label = widget_path.get("label", "")

        utils.log("Showing widget {}".format(widget_id), "debug")
        titles, cat, type = show_path(group_id, _label, widget_id, widget_path)
        return titles, cat, type
    else:
        directory.add_menu_item(title=30044, art=info, isFolder=True)
        return True, group_name, None


def merged_path(group_id, widget_id):
    _window = utils.get_active_window()

    group_def = manage.get_group_by_id(group_id)
    group_name = group_def.get("label", "")
    paths = group_def.get("paths", [])
    if len(paths) == 0:
        directory.add_menu_item(title=30018, art=utils.get_art("alert"), isFolder=False)
        return True, group_name, None

    widget_def = manage.get_widget_by_id(widget_id, group_id)
    if widget_def and _window != "dialog":
        paths = widget_def["path"]
    elif not widget_def:
        idxs = manage.choose_paths(utils.get_string(30088), paths, 5)

        if idxs is not None:
            if len(idxs) > 0:
                widget_def = manage.initialize(
                    group_def, "merged", widget_id, keep=idxs
                )
                paths = widget_def["path"]

    if widget_def:
        titles = []
        for idx, path in enumerate(paths):
            # simple compatibility with pre-3.3.0 widgets
            if isinstance(path, dict):
                path = path.get("id", "")
                paths[idx] = path
                widget_def["path"] = paths
                manage.save_path_details(widget_def)

            path_def = manage.get_path_by_id(path, group_id)
            titles, cat, type = show_path(
                group_id,
                path_def["label"],
                widget_id,
                path_def,
                idx=idx,
                titles=titles,
                num=len(paths),
                merged=True,
            )

        return titles, cat, type
    else:
        directory.add_menu_item(title=30044, art=info, isFolder=True)
        return True, group_name, None


def _create_group_context_items(group_id, target, idx, length):
    cm = [
        (
            utils.get_string(30041),
            (
                "RunPlugin("
                "plugin://plugin.program.autowidget/"
                "?mode=manage"
                "&action=edit"
                "&group={})"
            ).format(group_id),
        ),
        (
            utils.get_string(30149) if idx > 0 else utils.get_string(30151),
            (
                "RunPlugin("
                "plugin://plugin.program.autowidget/"
                "?mode=manage"
                "&action=shift_group"
                "&target=up"
                "&group={})"
            ).format(group_id),
        ),
        (
            utils.get_string(30150) if idx < length - 1 else utils.get_string(30152),
            (
                "RunPlugin("
                "plugin://plugin.program.autowidget/"
                "?mode=manage"
                "&action=shift_group"
                "&target=down"
                "&group={})"
            ).format(group_id),
        ),
        (
            utils.get_string(30119),
            (
                "RunPlugin("
                "plugin://plugin.program.autowidget/"
                "?mode=manage"
                "&action=copy"
                "&group={}"
                "&target={})"
            ).format(group_id, target),
        ),
    ]

    return cm


def _create_path_context_items(group_id, path_id, idx, length, target):
    if target not in ["shortcut", "widget"]:
        main_action = utils.get_string(30047)
    else:
        main_action = (
            utils.get_string(30030) if target == "shortcut" else utils.get_string(30113)
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
            utils.get_string(30014) if idx > 0 else utils.get_string(30086),
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
            utils.get_string(30015) if idx < length - 1 else utils.get_string(30085),
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
            title=utils.get_string(30053).format(six.text_type(group_name)),
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
            title=utils.get_string(30016).format(six.text_type(group_name)),
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
            title=utils.get_string(30065).format(six.text_type(group_name)),
            params={
                "mode": "path",
                "action": "merged",
                "group": group_id,
                "id": six.text_type(_id),
                "refresh": refresh,
            },
            art=utils.get_art("merge"),
            isFolder=True,
            props=props,
        )


def _is_page_item(label, next=True):
    tag_pattern = r"(\[[^\]]*\])"
    page_count_pattern = r"(?:\W*(?:(?:\d+\D*\d*))\W*)?"
    # base_pattern = r"^(?:(?:.+)?(?:(?:\b{}\b)|(?:\b{}\b)){{1,2}}{}){{1}}(?:\W+)?$"
    base_pattern_prefix = r"^(?:(?:.+)?(?:"
    word_pattern = r"(?:\b{}\b)"
    base_pattern_suffix = r"){{1,2}}{}){{1}}(?:\W+)?$"

    cleaned_title = re.sub(tag_pattern, "", label.lower()).strip()
    next_page_words = [i.lower() for i in re.split(r"\s+", _next_page)]
    prev_page_words = [i.lower() for i in re.split(r"\s+", _previous_page)]

    next_page_pattern = (
        base_pattern_prefix
        + "|".join([word_pattern.format(i) for i in next_page_words])
        + base_pattern_suffix.format(page_count_pattern)
    )
    prev_page_pattern = (
        base_pattern_prefix
        + "|".join([word_pattern.format(i) for i in prev_page_words])
        + base_pattern_suffix.format(page_count_pattern)
    )

    contains_dir_page = (
        re.search(next_page_pattern if next else prev_page_pattern, cleaned_title)
        is not None
    )

    return contains_dir_page


def show_error(id, props=None):
    directory.add_menu_item(
        title=settings.get_localized_string(30137).format(id),
        art=utils.get_art("alert"),
        props=props,
        isFolder=False,
    )

    return True, id, None


def show_empty(id, props=None):
    directory.add_menu_item(
        title=settings.get_localized_string(30138).format(id),
        art=info,
        props=props,
        isFolder=False,
    )

    return True, id, None
