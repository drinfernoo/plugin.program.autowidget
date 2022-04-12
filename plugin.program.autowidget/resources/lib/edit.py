import xbmcgui

import os
import re

import six

from resources.lib import manage
from resources.lib.common import settings
from resources.lib.common import utils

_addon_data = settings.get_addon_info("profile")

advanced = settings.get_setting_bool("context.advanced")
warning_shown = settings.get_setting_bool("context.warning")

filter = {
    "include": ["label", "file", "art", "color"] + utils.art_types,
    "exclude": ["paths", "version", "type", "sort_order"],
}
widget_filter = {
    "include": ["action", "refresh", "path"],
    "exclude": ["stack", "version", "label", "current", "updated"],
}
color_tag = "\[\w+(?: \w+)*\](?:\[\w+(?: \w+)*\])?(\w+)(?:\[\/\w+\])?\[\/\w+\]"
plus = utils.get_art("plus")


def shift_group(group_id, target):
    groups = manage.find_defined_groups()
    group_def = None
    swap_def = None

    for idx, group in enumerate(groups):
        if group["id"] == group_id:
            group_def = group
            if target == "up" and idx >= 0:
                if idx > 0:
                    swap_def = groups[idx - 1]
                    order = group.get("sort_order", "0")
                    new_order = swap_def.get("sort_order", "0")
                    swap_def["sort_order"] = order
                    group["sort_order"] = new_order
                    manage.write_path(swap_def)
                else:
                    new_order = int(groups[-1].get("sort_order", "0")) + 1
                    group["sort_order"] = "{}".format(new_order)
            elif target == "down" and idx <= len(groups) - 1:
                if idx < len(groups) - 1:
                    swap_def = groups[idx + 1]
                    order = group.get("sort_order", "0")
                    new_order = swap_def.get("sort_order", "0")
                    swap_def["sort_order"] = order
                    group["sort_order"] = new_order
                    manage.write_path(swap_def)
                else:
                    new_order = int(groups[0].get("sort_order", "0")) - 1
                    group["sort_order"] = "{}".format(new_order)
            break
    manage.write_path(group_def)
    utils.update_container()


def shift_path(group_id, path_id, target):
    group_def = manage.get_group_by_id(group_id)
    paths = group_def["paths"]
    for idx, path_def in enumerate(paths):
        if path_def["id"] == path_id:
            if target == "up" and idx >= 0:
                if idx > 0:
                    temp = paths[idx - 1]
                    paths[idx - 1] = path_def
                    paths[idx] = temp
                else:
                    paths.append(paths.pop(idx))
            elif target == "down" and idx <= len(paths) - 1:
                if idx < len(paths) - 1:
                    temp = paths[idx + 1]
                    paths[idx + 1] = path_def
                    paths[idx] = temp
                else:
                    paths.insert(0, paths.pop())
            break
    group_def["paths"] = paths
    manage.write_path(group_def)
    utils.update_container(group_def["type"] == "shortcut")


def _remove_group(group_id, over=False):
    dialog = xbmcgui.Dialog()
    group_def = manage.get_group_by_id(group_id)
    group_name = group_def["label"]
    if not over:
        choice = dialog.yesno("AutoWidget", utils.get_string(30024))

    if over or choice:
        file = os.path.join(_addon_data, "{}.group".format(group_id))
        utils.remove_file(file)
        dialog.notification(
            "AutoWidget", utils.get_string(30029).format(six.text_type(group_name))
        )
    del dialog


def _remove_path(path_id, group_id, over=False):
    dialog = xbmcgui.Dialog()
    if not over:
        choice = dialog.yesno("AutoWidget", utils.get_string(30021))

    if over or choice:
        group_def = manage.get_group_by_id(group_id)
        paths = group_def["paths"]
        for path_def in paths:
            if path_def["id"] == path_id:
                path_name = path_def["label"]
                group_def["paths"].remove(path_def)
                dialog.notification(
                    "AutoWidget",
                    utils.get_string(30029).format(six.text_type(path_name)),
                )
        manage.write_path(group_def)
    del dialog


def remove_widget(widget_id, over=False):
    dialog = xbmcgui.Dialog()
    if not over:
        choice = dialog.yesno("AutoWidget", utils.get_string(30024))

    if over or choice:
        file = os.path.join(_addon_data, "{}.widget".format(widget_id))
        utils.remove_file(file)
        dialog.notification("AutoWidget", utils.get_string(30029).format(widget_id))
    del dialog


def _warn():
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno(
        "AutoWidget",
        utils.get_string(30038),
        yeslabel=utils.get_string(30039),
        nolabel=utils.get_string(30040),
    )
    del dialog
    if choice < 1:
        settings.set_setting_bool("context.advanced", False)
        settings.set_setting_bool("context.warning", True)
    else:
        settings.set_setting_bool("context.warning", True)


def _show_options(group_def, path_def=None, type=""):
    edit_def = path_def if path_def else group_def
    options = _get_options(edit_def)
    remove_label = utils.get_string(30013) if path_def else utils.get_string(30012)
    options.append(u"[COLOR firebrick]{}[/COLOR]".format(six.ensure_text(remove_label)))
    if not type:
        target = path_def["target"] if path_def else group_def["type"]
        if target not in ["shortcut", "widget", "settings"]:
            main_action = utils.get_string(30047)
        else:
            main_action = (
                utils.get_string(30030)
                if target in ["shortcut", "settings"]
                else utils.get_string(30113)
            )
    else:
        main_action = utils.get_string(30041)

    dialog = xbmcgui.Dialog()
    idx = dialog.select(main_action, options)
    del dialog

    if idx < 0:
        return
    elif idx == len(options) - 1:
        if path_def:
            _remove_path(path_def["id"], group_def["id"])
            utils.update_container(group_def["type"] == "shortcut")
        else:
            _remove_group(group_def["id"])
            utils.update_container(group_def["type"] == "shortcut")
        return
    else:
        key = _clean_key(options[idx])

    return _get_value(edit_def, key)


def _show_widget_options(edit_def):
    options = _get_widget_options(edit_def)
    options.append("[COLOR firebrick]{}[/COLOR]".format(utils.get_string(30089)))

    dialog = xbmcgui.Dialog()
    idx = dialog.select(utils.get_string(30047), options)
    del dialog

    if idx < 0:
        return
    elif idx == len(options) - 1:
        remove_widget(edit_def["id"])
        utils.update_container()
        return
    else:
        key = _clean_key(options[idx])

    return _get_widget_value(edit_def, key)


def _get_options(edit_def, useThumbs=None):
    options = []
    all_keys = sorted(edit_def.keys())
    base_keys = [i for i in all_keys if i in filter["include"]]

    option_keys = [
        i for i in (all_keys if advanced else base_keys) if i not in filter["exclude"]
    ]
    for key in option_keys:
        if edit_def.get(key) is not None:
            if key in utils.art_types:
                li = xbmcgui.ListItem("[B]{}[/B]: {}".format(key, edit_def[key]))
                li.setArt({"icon": edit_def[key]})
                options.append(li)
            elif key == "color":
                options.append(
                    "[B]{0}[/B]: [COLOR {1}]{1}[/COLOR]".format(key, edit_def[key])
                )
            else:
                formatted_key = (
                    "[COLOR goldenrod]{}[/COLOR]".format(key)
                    if key not in filter["include"]
                    else key
                )
                if isinstance(edit_def[key], dict):
                    label = ", ".join(edit_def[key].keys())
                    options.append("[B]{}[/B]: {}".format(formatted_key, label))
                else:
                    v = edit_def[key]
                    try:
                        options.append("[B]{}[/B]: {}".format(formatted_key, v))
                    except UnicodeEncodeError:
                        options.append(
                            "[B]{}[/B]: {}".format(formatted_key, v.encode("utf-8"))
                        )

    if useThumbs is not None:
        new_item = xbmcgui.ListItem(
            utils.get_string(30054) if not useThumbs else utils.get_string(30055)
        )
        new_item.setArt(plus)
        options.append(new_item)

    return options


def _get_widget_options(edit_def):
    options = []
    all_keys = sorted(edit_def.keys())
    base_keys = [i for i in all_keys if i in widget_filter["include"]]

    option_keys = [
        i
        for i in (all_keys if advanced else base_keys)
        if i not in widget_filter["exclude"]
    ]
    for key in option_keys:
        if key in edit_def and (edit_def[key] and edit_def[key] != -1):
            formatted_key = (
                "[COLOR goldenrod]{}[/COLOR]".format(key)
                if key not in widget_filter["include"]
                else key
            )
            _def = edit_def[key]
            label = _def

            if key == "action":
                if label == "random":
                    label = utils.get_string(30056)
                elif label == "next":
                    label = utils.get_string(30057)
                elif label in ["merged", "static"]:
                    continue
            elif key == "refresh":
                if edit_def["action"] in ["static", "merged"]:
                    continue
                hh = int(_def)
                mm = int((_def * 60) % 60)
                if hh and mm:
                    label = "{}h {}m".format(hh, mm)
                elif not mm:
                    label = "{}h".format(hh)
                elif not hh:
                    label = "{}m".format(mm)
            elif key == "path":
                if edit_def["action"] not in ["static", "merged"]:
                    continue

                paths = []
                if isinstance(_def, list):
                    for i in _def:
                        paths.append(i["label"])
                    label = ", ".join(paths)
                else:
                    label = _def

        try:
            options.append("[B]{}[/B]: {}".format(formatted_key, label))
        except UnicodeEncodeError:
            options.append("[B]{}[/B]: {}".format(formatted_key, label.encode("utf-8")))

    return options


def _get_value(edit_def, key):
    dialog = xbmcgui.Dialog()
    if isinstance(edit_def[_clean_key(key)], dict):
        is_art = key == "art"
        label = utils.get_string(30090) if is_art else utils.get_string(30091)
        options = _get_options(edit_def[key], useThumbs=is_art)

        idx = dialog.select(label, options, useDetails=is_art)

        if idx < 0:
            del dialog
            return
        elif idx == len(options) - 1:
            keys = utils.info_types if key == "file" else utils.art_types
            add_options = [
                i
                for i in keys
                if (i not in edit_def[key] or edit_def[key][i] in [None, "", -1])
            ]
            add_idx = dialog.select(
                utils.get_string(30093) if key == "file" else utils.get_string(30092),
                add_options,
            )
            if add_idx < 0:
                del dialog
                return
            if key == "file":
                value = dialog.input(
                    utils.get_string(30094).format(add_options[add_idx])
                )
                if value is not None:
                    edit_def[key][add_options[add_idx]] = value
                    del dialog
                    return edit_def[key][add_options[add_idx]]
            elif key == "art":
                value = dialog.browse(
                    2,
                    utils.get_string(30031).format(add_options[add_idx].capitalize()),
                    shares="files",
                    mask=".jpg|.png",
                    useThumbs=True,
                )
                if value is not None:
                    edit_def[key][add_options[add_idx]] = utils.clean_artwork_url(value)
                    del dialog
                    return edit_def[key]
        else:
            subkey = _clean_key(options[idx])
            value = _get_value(edit_def[key], _clean_key(options[idx]))
            if value is not None:
                edit_def[key][subkey] = value
                del dialog
                return edit_def[key]
    else:
        default = edit_def[key]
        if key in utils.art_types:
            value = dialog.browse(
                2,
                utils.get_string(30031).format(key.capitalize()),
                shares="files",
                mask=".jpg|.png",
                useThumbs=True,
                defaultt=default,
            )
        elif key == "filetype":
            options = ["file", "directory"]
            type = dialog.select(
                utils.get_string(30095), options, preselect=options.index(default)
            )
            value = options[type]
        elif key == "color":
            value = utils.set_color()
        elif key == "content":
            options = [
                "none",
                "files",
                "movies",
                "tvshows",
                "episodes",
                "videos",
                "artists",
                "albums",
                "songs",
                "musicvideos",
                "images",
                "games",
                "genres",
                "years",
                "actors",
                "playlists",
                "plugins",
                "studios",
                "directors",
                "sets",
                "tags",
                "countries",
                "roles",
                "images",
                "addons",
                "livetv",
            ]
            type = dialog.select(
                utils.get_string(30118),
                options,
                preselect=options.index(default if default in options else "none"),
            )
            value = options[type]
        else:
            value = dialog.input(utils.get_string(30094).format(key), defaultt=default)

        if value == default:
            clear = dialog.yesno(
                "AutoWidget",
                utils.get_string(30096).format(
                    "art" if key in utils.art_types else "value", key, default
                ),
                yeslabel=utils.get_string(30097),
                nolabel=utils.get_string(30098),
            )
            if clear:
                value = ""
        del dialog
        if value is not None:
            if key in utils.art_types:
                edit_def[key] = utils.clean_artwork_url(value)
            else:
                edit_def[key] = value
            return value


def _get_widget_value(edit_def, key):
    dialog = xbmcgui.Dialog()
    if key == "action":
        actions = [utils.get_string(30056), utils.get_string(30057)]
        choice = dialog.select(utils.get_string(30058), actions)
        if choice < 0:
            del dialog
            return

        value = actions[choice].split(" ")[0].lower()
    elif key == "refresh":
        durations = []
        d = 0.25
        while d <= 12:
            hh = int(d)
            mm = int((d * 60) % 60)
            if hh and mm:
                label = "{}h {}m".format(hh, mm)
            elif not mm:
                label = "{}h".format(hh)
            elif not hh:
                label = "{}m".format(mm)

            durations.append(label)
            d = d + 0.25

        choice = dialog.select(utils.get_string(30099), durations)

        if choice < 0:
            del dialog
            return

        duration = durations[choice].split(" ")
        if len(duration) > 1:
            value = float(duration[0][:-1]) + (float(duration[1][:-1]) / 60)
        else:
            if "m" in duration[0]:
                value = float(duration[0][:-1]) / 60
            elif "h" in duration[0]:
                value = float(duration[0][:-1])
    elif key == "path":
        groups = manage.find_defined_paths(edit_def["group"])
        labels = [i["label"] for i in groups]
        if isinstance(edit_def[key], list):
            paths = []
            choice = dialog.multiselect(utils.get_string(30088), labels)
            if choice:
                for i in choice:
                    paths.append(groups[i])
                value = paths
            del dialog
        else:
            choice = dialog.select(utils.get_string(30087), labels)
            if choice < 0:
                del dialog
                return
            value = groups[choice]
    else:
        default = edit_def.get(key)
        value = dialog.input(
            utils.get_string(30094).format(key), defaultt=six.text_type(default)
        )

    del dialog
    if value:
        edit_def[key] = value
        return value


def _clean_key(key):
    if isinstance(key, xbmcgui.ListItem):
        key = key.getLabel()
    split = key.split(": ")[0]
    match = re.match(color_tag, split)
    if match:
        clean = re.sub(color_tag, split, match.group(1))
        return clean
    return key.split(": ")[0]


def edit_dialog(group_id, path_id=None, base_key=None, type=""):
    updated = False
    if advanced and not warning_shown:
        _warn()

    group_def = manage.get_group_by_id(group_id)
    path_def = manage.get_path_by_id(path_id, group_id)
    if not group_def or path_id and not path_def:
        return

    updated = _show_options(group_def, path_def, type)
    if updated:
        manage.write_path(group_def, path_def=path_def, update=path_id)
        utils.update_container(group_def["type"] == "shortcut")

        edit_dialog(group_id, path_id, type)


def edit_widget_dialog(widget_id):
    updated = False
    if advanced and not warning_shown:
        _warn()

    widget_def = manage.get_widget_by_id(widget_id)
    if not widget_def:
        return

    updated = _show_widget_options(widget_def)
    if updated:
        manage.save_path_details(widget_def)
        utils.update_container(True)
        edit_widget_dialog(widget_id)
