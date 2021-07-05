import xbmcgui

import os
import zipfile

import six

from resources.lib.common import utils

_backup_location = utils.translate_path(utils.get_setting("backup.location"))
dialog = xbmcgui.Dialog()


def location():
    folder = dialog.browse(
        0, utils.get_string(30068), "files", defaultt=backup_location
    )
    if folder:
        utils.set_setting("backup.location", folder)


def backup():
    choice = dialog.yesno("AutoWidget", utils.get_string(30071))

    if choice:
        filename = dialog.input(utils.get_string(30072))

        if not filename:
            dialog.notification("AutoWidget", utils.get_string(30073))
            return

        if not os.path.exists(_backup_location):
            try:
                os.makedirs(_backup_location)
            except Exception as e:
                utils.log(str(e), "error")
                dialog.notification("AutoWidget", utils.get_string(30074))
                return

        files = [x for x in os.listdir(utils._addon_path) if x.endswith(".group")]
        if len(files) == 0:
            dialog.notification("AutoWidget", utils.get_string(30046))
            return

        path = os.path.join(
            _backup_location, "{}.zip".format(filename.replace(".zip", ""))
        )
        content = six.BytesIO()
        with zipfile.ZipFile(content, "w", zipfile.ZIP_DEFLATED) as z:
            for file in files:
                with open(os.path.join(utils._addon_path, file), "r") as f:
                    z.writestr(file, six.ensure_text(f.read()))

        with open(path, "wb") as f:
            f.write(content.getvalue())


def restore():
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
                    files = [
                        x for x in os.listdir(utils._addon_path) if x.endswith(".group")
                    ]
                    for file in files:
                        utils.remove_file(file)
                z.extractall(utils._addon_path)
            else:
                dialog.notification("AutoWidget", utils.get_string(30078))
    else:
        dialog.notification("AutoWidget", utils.get_string(30078))
        return
