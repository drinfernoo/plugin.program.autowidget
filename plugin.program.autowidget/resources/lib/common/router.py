import traceback

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl

from resources.lib import add
from resources.lib import backup
from resources.lib import edit
from resources.lib import menu
from resources.lib import manage
from resources.lib import refresh
from resources.lib.common import cache
from resources.lib.common import directory
from resources.lib.common import utils


def _log_params(_params):
    msg = "[{}]"

    params = dict(parse_qsl(_params))
    if params:
        msg = msg.format("][".join([" {}: {} ".format(p, params[p]) for p in params]))
    else:
        msg = msg.format(" root ")
    utils.log(msg, "info")

    return params


def dispatch(_handle, _params):
    params = _log_params(_params)
    category = "AutoWidget"
    is_dir = False
    is_type = "files"

    utils.ensure_addon_data()

    mode = params.get("mode", "")
    action = params.get("action", "")
    group = params.get("group", "")
    path = params.get("path", "")
    path_id = params.get("path_id", "")
    target = params.get("target", "")
    widget_id = params.get("id", "")

    if not mode:
        is_dir, category, is_type = menu.root_menu()
    elif mode == "manage":
        if action == "add_group":
            add.add_group(target)
        elif action == "add_path" and group and target:
            add.add_path(group, target)
        elif action == "shift_path" and group and path_id and target:
            edit.shift_path(group, path_id, target)
        elif action == "shift_group" and group and target:
            edit.shift_group(group, target)
        elif action == "edit":
            edit.edit_dialog(group, type="group")
        elif action == "edit_path":
            edit.edit_dialog(group, path_id)
        elif action == "edit_widget":
            edit.edit_widget_dialog(widget_id)
        elif action == "copy":
            if group and target:
                add.copy_group(group, target)
    elif mode == "group":
        if not group:
            is_dir, category, is_type = menu.my_groups_menu()
        else:
            is_dir, category, is_type = menu.group_menu(group)
    elif mode == "path":
        try:
            if path_id:
                menu.call_path(path_id)
            elif action in ["static", "cycling"] and group:
                is_dir, category, is_type = menu.path_menu(group, action, widget_id)
            elif action == "merged" and group:
                is_dir, category, is_type = menu.merged_path(group, widget_id)
            elif action == "update" and target:
                refresh.update_path(widget_id, target, path)
        except Exception as e:
            utils.log(traceback.format_exc(), "error")
            is_dir, category, is_type = menu.show_error(
                widget_id if widget_id else path_id
            )
    elif mode == "widget":
        is_dir, category, is_type = menu.active_widgets_menu()
    elif mode == "refresh":
        if not widget_id:
            refresh.refresh_paths()
        else:
            refresh.refresh(widget_id, force=True, single=True)
    elif mode == "tools":
        is_dir, category, is_type = menu.tools_menu()
    elif mode == "force":
        refresh.refresh_paths(notify=True, force=True)
    elif mode == "skindebug":
        utils.call_builtin("Skin.ToggleDebug")
    elif mode == "wipe":
        utils.wipe()
    elif mode == "clean":
        if not widget_id:
            manage.clean(notify=True, all=True)
        else:
            edit.remove_widget(widget_id, over=True)
            utils.update_container(True)
    elif mode == "clear_cache":
        if not target:
            cache.clear_cache()
        else:
            cache.clear_cache(target)
    elif mode == "set_color":
        utils.set_color(setting=True)
    elif mode == "backup" and action:
        if action == "location":
            backup.location()
        elif action == "backup":
            backup.backup()
        elif action == "restore":
            backup.restore()

    if is_dir:
        directory.add_sort_methods(_handle)
        directory.finish_directory(
            _handle, category, is_type if is_type not in [None, "none"] else ""
        )
