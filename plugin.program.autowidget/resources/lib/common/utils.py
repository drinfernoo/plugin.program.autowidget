import xbmc
import xbmcgui
import xbmcvfs

import codecs
import contextlib
import io
import json
import os
import string
import time
import unicodedata
import datetime

import six
from PIL import Image

from resources.lib.common import settings

try:
    from urllib.parse import unquote
except ImportError:
    from urlparse import unquote

try:
    translatePath = xbmcvfs.translatePath
except AttributeError:
    translatePath = xbmc.translatePath

_addon_id = settings.get_addon_info("id")
_addon_data = settings.get_addon_info("profile")
_addon_root = translatePath(settings.get_addon_info("path"))

_art_path = os.path.join(_addon_root, "resources", "media")
_home = translatePath("special://home/")

windows = {
    "programs": ["program", "script"],
    "addonbrowser": ["addon", "addons"],
    "music": ["audio", "music"],
    "pictures": ["image", "picture"],
    "videos": ["video", "videos"],
}

art_types = [
    "banner",
    "clearart",
    "clearlogo",
    "fanart",
    "icon",
    "landscape",
    "poster",
    "thumb",
]

# from https://www.rapidtables.com/web/css/css-color.html
colors = [
    "lightsalmon",
    "salmon",
    "darksalmon",
    "lightcoral",
    "indianred",
    "crimson",
    "firebrick",
    "red",
    "darkred",  # red
    "coral",
    "tomato",
    "orangered",
    "gold",
    "orange",
    "darkorange",  # orange
    "lightyellow",
    "lemonchiffon",
    "lightgoldenrodyellow",
    "papayawhip",
    "moccasin",
    "peachpuff",
    "palegoldenrod",
    "khaki",
    "darkkhaki",
    "yellow",  # yellow
    "lawngreen",
    "chartreuse",
    "limegreen",
    "lime",
    "forestgreen",
    "green",
    "darkgreen",
    "greenyellow",
    "yellowgreen",
    "springgreen",
    "mediumspringgreen",
    "lightgreen",
    "palegreen",
    "darkseagreen",
    "mediumseagreen",
    "seagreen",
    "olive",
    "darkolivegreen",
    "olivedrab",  # green
    "lightcyan",
    "cyan",
    "aqua",
    "aquamarine",
    "mediumaquamarine",
    "paleturquoise",
    "turquoise",
    "mediumturquoise",
    "darkturquoise",
    "lightseagreen",
    "cadetblue",
    "darkcyan",
    "teal",  # cyan
    "powderblue",
    "lightblue",
    "lightskyblue",
    "skyblue",
    "deepskyblue",
    "lightsteelblue",
    "dodgerblue",
    "cornflowerblue",
    "steelblue",
    "royalblue",
    "blue",
    "mediumblue",
    "darkblue",
    "navy",
    "midnightblue",
    "mediumslateblue",
    "slateblue",
    "darkslateblue",  # blue
    "lavender",
    "thistle",
    "plum",
    "violet",
    "orchid",
    "fuschia",
    "magenta",
    "mediumorchid",
    "mediumpurple",
    "blueviolet",
    "darkviolet",
    "darkorchid",
    "darkmagenta",
    "purple",
    "indigo",  # purple
    "pink",
    "lightpink",
    "hotpink",
    "deeppink",
    "palevioletred",
    "mediumvioletred",  # pink
    "white",
    "snow",
    "honeydew",
    "mintcream",
    "azure",
    "aliceblue",
    "ghostwhite",
    "whitesmoke",
    "seashell",
    "beige",
    "oldlace",
    "floralwhite",
    "ivory",
    "antiquewhite",
    "linen",
    "lavenderblush",
    "mistyrose",  # white
    "gainsboro",
    "lightgray",
    "silver",
    "darkgray",
    "gray",
    "dimgray",
    "lightslategray",
    "slategray",
    "darkslategray",
    "black",  # black
    "cornsilk",
    "blanchedalmond",
    "bisque",
    "navajowhite",
    "wheat",
    "burlywood",
    "tan",
    "rosybrown",
    "sandybrown",
    "goldenrod",
    "peru",
    "chocolate",
    "saddlebrown",
    "sienna",
    "brown",
    "maroon",
]  # brown


def make_holding_path(label, art, hash=None):
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "files": [
                {
                    "title": label,
                    "label": label,
                    "file": "plugin://plugin.program.autowidget/?mode=clear_cache&target={}&refresh=&reload=".format(
                        hash
                    )
                    if hash
                    else "plugin://plugin.program.autowidget/?mode=force&refresh=&reload=",
                    "art": get_art(art),
                    "filetype": "file",
                }
            ]
        },
    }


def ft(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


def log(msg, level="debug"):
    _level = xbmc.LOGDEBUG
    debug = settings.get_setting_bool("logging.debug")
    logpath = os.path.join(_addon_data, "aw_debug.log")

    if level == "debug":
        _level = xbmc.LOGDEBUG
    elif level in ["notice", "info"]:
        try:
            _level = xbmc.LOGNOTICE
        except AttributeError:
            _level = xbmc.LOGINFO
    elif level == "error":
        _level = xbmc.LOGERROR

    msg = u"{}: {}".format(_addon_id, six.text_type(msg))
    try:
        xbmc.log(msg, _level)
    except UnicodeEncodeError:
        xbmc.log(msg.encode("utf-8"), _level)
    if debug:
        debug_size = xbmcvfs.Stat(logpath).st_size() if xbmcvfs.exists(logpath) else 0
        debug_msg = u"{}  {}{}".format(time.ctime(), level.upper(), msg[25:])
        write_file(logpath, debug_msg + "\n", mode="a" if debug_size < 1048576 else "w")


def ensure_addon_data():
    if not xbmcvfs.exists(_addon_data):
        xbmcvfs.mkdirs(_addon_data)


def wipe(folder=_addon_data, over=False):
    dialog = xbmcgui.Dialog()
    choice = None
    if not over:
        choice = dialog.yesno("AutoWidget", get_string(30043))
        del dialog

    if choice or over:
        dirs = xbmcvfs.listdir(folder)[0]
        files = xbmcvfs.listdir(folder)[1]

        for f in files:
            path = os.path.join(folder, f)
            remove_file(path)
        for d in dirs:
            path = os.path.join(folder, d)
            wipe(path, True)
            xbmcvfs.rmdir(path, True)


def get_art(filename, color=None):
    art = {}
    if not color:
        color = settings.get_setting_string("ui.color")

    themed_path = os.path.join(_addon_data, color)
    if not xbmcvfs.exists(themed_path):
        xbmcvfs.mkdirs(themed_path)

    for i in art_types:
        _i = i
        if i == "thumb":
            _i = "icon"
        path = os.path.join(_art_path, _i, "{}.png".format(filename))
        new_path = ""

        if xbmcvfs.exists(path):
            if color.lower() not in ["white", "#ffffff"]:
                new_path = os.path.join(themed_path, "{}-{}.png".format(filename, _i))
                if not xbmcvfs.exists(new_path):
                    new_bytes = six.BytesIO()
                    icon = Image.open(path).convert("RGBA")
                    overlay = Image.new("RGBA", icon.size, color)
                    Image.composite(overlay, icon, icon).save(new_bytes, format='png')
                    write_file(new_path, new_bytes.getvalue())
            art[i] = clean_artwork_url(new_path if xbmcvfs.exists(new_path) else path)

    return art


def set_color(setting=False):
    dialog = xbmcgui.Dialog()
    color = settings.get_setting_string("ui.color")

    choice = dialog.yesno(
        "AutoWidget",
        get_string(30106),
        yeslabel=get_string(30107),
        nolabel=get_string(30108),
    )

    if choice:
        value = dialog.input(get_string(30109)).lower()
    else:
        value = dialog.select(
            get_string(30110),
            ["[COLOR {0}]{0}[/COLOR]".format(i) for i in colors],
            preselect=colors.index(color) if color in colors else -1,
        )
        if value > -1:
            value = colors[value]

    if value != -1:
        if value not in colors:
            if len(value) < 6:
                dialog.notification("AutoWidget", get_string(30111))
                del dialog
                return
            elif len(value) == 6 and not value.startswith("#"):
                value = "#{}".format(value)
        if setting:
            settings.set_setting_string("ui.color", value)

    del dialog
    return value


def get_active_window():
    # 'home'
    # 'dialogXXX'
    # etc...
    #
    # 'Window.Property(xmlfile)' gives full path to current window XML, this gives
    # JUST the title of the file, with no extension
    xml_file = os.path.basename(get_infolabel("Window.Property(xmlfile)").lower())[:-4]

    if xbmc.getCondVisibility("Window.IsMedia()"):
        return "media"
    elif "dialog" in xml_file:
        return "dialog"
    elif xbmc.getCondVisibility("Window.IsActive(home)"):
        return "home"
    else:
        pass


def update_container(reload=False):
    refresh_time = os.path.join(_addon_data, "refresh.time")
    in_media = get_active_window() == "media"
    in_plugin = in_media and get_infolabel("Container.PluginName") == _addon_id
    is_scanning = get_condition("Library.IsScanningVideo") or get_condition(
        "Library.IsScanningMusic"
    )
    if is_scanning:
        return

    if reload:
        if in_media:
            write_file(refresh_time, six.text_type(time.time()))
        else:
            log("Triggering library update to reload widgets", "debug")
            xbmc.executebuiltin("UpdateLibrary(video, AutoWidget)")
            if xbmcvfs.exists(refresh_time):
                remove_file(refresh_time)
    if in_plugin:
        xbmc.executebuiltin("Container.Refresh()")


def get_valid_filename(filename):
    whitelist = "-_.() {}{}".format(string.ascii_letters, string.digits)
    char_limit = 255

    filename = filename.replace(" ", "_")
    cleaned_filename = (
        unicodedata.normalize("NFKD", filename).encode("ASCII", "ignore").decode()
    )

    cleaned_filename = "".join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename) > char_limit:
        print(
            "Warning, filename truncated because it was over {} characters. "
            "Filenames may no longer be unique".format(char_limit)
        )

    return cleaned_filename[:char_limit]


def get_unique_id(key):
    return "{}-{}".format(get_valid_filename(six.ensure_text(key)), time.time()).lower()


def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.items()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, six.text_type):
        return six.ensure_text(input)

    return input


def remove_file(file):
    if xbmcvfs.exists(file):
        try:
            xbmcvfs.delete(file)
        except OSError as e:
            log("Could not remove {}: {}".format(file, e), level="error")


def read_file(file):
    content = None
    if xbmcvfs.exists(file):
        with contextlib.closing(xbmcvfs.File(file)) as f:
            try:
                content = f.read()
            except Exception as e:
                log("Could not read from {}: {}".format(file, e), level="error")
    else:
        log("{} does not exist.".format(file), level="error")

    return content


def write_file(file, content, mode="w"):
    with contextlib.closing(xbmcvfs.File(file, mode)) as f:
        try:
            f.write(content)
            return True
        except Exception as e:
            log("Could not write to {}: {}".format(file, e), level="error")

    return False


def read_json(file, log_file=False, default={}):
    data = None
    # path = os.path.join(_addon_data, file) if _addon_data not in file else file
    path = translatePath(file)
    if not os.path.exists(path):
        log("{} does not exist.".format(file), level="error")
        return default
    with contextlib.closing(xbmcvfs.File(file, "r")) as f:
        try:
            content = six.ensure_text(f.read())
            data = json.loads(content)
        except (ValueError, TypeError, UnicodeDecodeError, NameError, FileNotFoundError) as e:
            log("Could not read JSON from {}: {}".format(file, e), level="error")
            if log_file:
                log(content, level="info")
            os.remove(path)
            return default

    return convert(data)


def write_json(file, content):
    with contextlib.closing(xbmcvfs.File(file, "w")) as f:
        try:
            f.write(bytearray(json.dumps(content, indent=4).encode('utf-8')))
        except Exception as e:
            log("Could not write to {}: {}".format(file, e), level="error")
            return False
    return True


def get_string(_id, kodi=False):
    if kodi:
        return six.text_type(xbmc.getLocalizedString(_id))
    return settings.get_localized_string(_id)


def set_property(property, value, window=10000):
    xbmcgui.Window(window).setProperty(property, value)


def get_property(property, window=10000):
    return xbmcgui.Window(window).getProperty(property)


def clear_property(property, window=10000):
    xbmcgui.Window(window).clearProperty(property)


def get_infolabel(label):
    return xbmc.getInfoLabel(label)


def get_condition(cond):
    return xbmc.getCondVisibility(cond)


def clean_artwork_url(url):
    if url.startswith("image://") and "@" in url:
        url = url.replace(_home, "special://home/").rstrip("/")
    else:
        url = (
            unquote(url)
            .replace(_home, "special://home/")
            .replace("image://", "")
            .rstrip("/")
        )
    return url


def get_info_keys():
    params = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "JSONRPC.Introspect",
        "params": {
            "getmetadata": True,
            "filter": {
                "getreferences": True,
                "id": "List.Fields.Files",
                "type": "type",
            },
        },
    }
    info_keys = call_jsonrpc(params)
    return info_keys["result"]["types"]["List.Fields.Files"]["items"]["enums"]


def call_builtin(action, delay=0):
    if delay:
        xbmc.sleep(delay)
    xbmc.executebuiltin(six.text_type(action))


def call_jsonrpc(request):
    call = json.dumps(request)
    response = xbmc.executeJSONRPC(call)
    return json.loads(response)


@contextlib.contextmanager
def timing(description):
    start = time.time()
    yield
    elapsed = time.time() - start

    log("{}: {}".format(description, ft(elapsed)))
