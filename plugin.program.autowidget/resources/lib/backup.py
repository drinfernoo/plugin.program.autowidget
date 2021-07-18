import xbmcgui

import os
import zipfile

import six

from resources.lib.common import settings
from resources.lib.common import utils

_addon_data = utils.translate_path(settings.get_addon_info("profile"))
_backup_location = utils.translate_path(settings.get_setting_string("backup.location"))


def location():
    dialog = xbmcgui.Dialog()
    folder = dialog.browse(
        0, utils.get_string(30068), "files", defaultt=_backup_location
    )
    del dialog

    if folder:
        settings.set_setting_string("backup.location", folder)


def backup():
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno("AutoWidget", utils.get_string(30071))

    if choice:
        filename = dialog.input(utils.get_string(30072))

        if not filename:
            dialog.notification("AutoWidget", utils.get_string(30073))
            del dialog
            return

        if not os.path.exists(_backup_location):
            try:
                os.makedirs(_backup_location)
            except Exception as e:
                utils.log(str(e), "error")
                dialog.notification("AutoWidget", utils.get_string(30074))
                del dialog
                return

        files = [
            x
            for x in os.listdir(_addon_data)
            if any(
                x.endswith(i)
                for i in [".group", ".widget", ".history", ".cache", ".log"]
            )
        ]
        if len(files) == 0:
            dialog.notification("AutoWidget", utils.get_string(30046))
            del dialog
            return

        path = os.path.join(
            _backup_location, "{}.zip".format(filename.replace(".zip", ""))
        )
        content = six.BytesIO()
        with zipfile.ZipFile(content, "w", zipfile.ZIP_DEFLATED) as z:
            for file in files:
                with open(os.path.join(_addon_data, file), "r") as f:
                    z.writestr(file, six.ensure_text(f.read()))

        with open(path, "wb") as f:
            f.write(content.getvalue())
    del dialog


def restore():
    dialog = xbmcgui.Dialog()
    backup = dialog.browse(
        1, utils.get_string(30075), "files", mask=".zip", defaultt=_backup_location
    )

    if backup.endswith("zip"):
        with zipfile.ZipFile(backup, "r") as z:
            info = z.infolist()
            choice = dialog.yesno(
                "AutoWidget",
                utils.get_string(30076).format(len(info), "s" if len(info) > 1 else ""),
            )

            if choice:
                overwrite = dialog.yesno("AutoWidget", utils.get_string(30077))

                if overwrite:
                    files = [x for x in os.listdir(_addon_data) if x.endswith(".group")]
                    for file in files:
                        utils.remove_file(file)
                z.extractall(_addon_data)
            else:
                dialog.notification("AutoWidget", utils.get_string(30078))
        del dialog
    else:
        dialog.notification("AutoWidget", utils.get_string(30078))
        del dialog
        return
