from kodi_six import xbmc
from kodi_six import xbmcaddon
from kodi_six import xbmcgui

import codecs
import contextlib
import io
import json
import os
import string
import time
import unicodedata
import hashlib
import glob

import six
from PIL import Image

try:
    from urllib.parse import unquote
except ImportError:
    from urlparse import unquote


_addon = xbmcaddon.Addon()
_addon_id = _addon.getAddonInfo('id')
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_root = xbmc.translatePath(_addon.getAddonInfo('path'))
_addon_version = _addon.getAddonInfo('version')
_addon_data = xbmc.translatePath('special://profile/addon_data/')

_art_path = os.path.join(_addon_root, 'resources', 'media')
_home = xbmc.translatePath('special://home/')

windows = {'programs': ['program', 'script'],
            'addonbrowser': ['addon', 'addons'],
            'music': ['audio', 'music'],
            'pictures': ['image', 'picture'],
            'videos': ['video', 'videos']}

info_types = ['artist', 'albumartist', 'genre', 'year', 'rating',
              'album', 'track', 'duration', 'comment', 'lyrics',
              'musicbrainztrackid', 'plot', 'art', 'mpaa', 'cast',
              'musicbrainzartistid', 'set', 'showlink', 'top250', 'votes',
              'musicbrainzalbumid', 'disc', 'tag', 'genreid', 'season',
              'musicbrainzalbumartistid', 'size', 'theme', 'mood', 'style',
              'playcount', 'director', 'trailer', 'tagline', 'title',
              'plotoutline', 'originaltitle', 'lastplayed', 'writer', 'studio',
              'country', 'imdbnumber', 'premiered', 'productioncode', 'runtime',
              'firstaired', 'episode', 'showtitle', 'artistid', 'albumid',
              'tvshowid', 'setid', 'watchedepisodes', 'displayartist', 'mimetype',
              'albumartistid', 'description', 'albumlabel', 'sorttitle', 'episodeguide',
              'dateadded', 'lastmodified', 'specialsortseason', 'specialsortepisode']

art_types = ['banner', 'clearart', 'clearlogo', 'fanart', 'icon', 'landscape',
             'poster', 'thumb']
             
# from https://www.rapidtables.com/web/css/css-color.html
colors = ['lightsalmon', 'salmon', 'darksalmon', 'lightcoral', 'indianred', 'crimson', 'firebrick', 'red', 'darkred',  # red
          'coral', 'tomato', 'orangered', 'gold', 'orange', 'darkorange',  # orange
          'lightyellow', 'lemonchiffon', 'lightgoldenrodyellow', 'papayawhip', 'moccasin', 'peachpuff', 'palegoldenrod', 'khaki', 'darkkhaki', 'yellow',  # yellow
          'lawngreen', 'chartreuse', 'limegreen', 'lime', 'forestgreen', 'green', 'darkgreen', 'greenyellow', 'yellowgreen', 'springgreen', 'mediumspringgreen', 'lightgreen', 'palegreen', 'darkseagreen', 'mediumseagreen', 'seagreen', 'olive', 'darkolivegreen', 'olivedrab',  # green
          'lightcyan', 'cyan', 'aqua', 'aquamarine', 'mediumaquamarine', 'paleturquoise', 'turquoise', 'mediumturquoise', 'darkturquoise', 'lightseagreen', 'cadetblue', 'darkcyan', 'teal',  # cyan
          'powderblue', 'lightblue', 'lightskyblue', 'skyblue', 'deepskyblue', 'lightsteelblue', 'dodgerblue', 'cornflowerblue', 'steelblue', 'royalblue', 'blue', 'mediumblue', 'darkblue', 'navy', 'midnightblue', 'mediumslateblue', 'slateblue', 'darkslateblue',  # blue
          'lavender', 'thistle', 'plum', 'violet', 'orchid', 'fuschia', 'magenta', 'mediumorchid', 'mediumpurple', 'blueviolet', 'darkviolet', 'darkorchid', 'darkmagenta', 'purple', 'indigo',  # purple
          'pink', 'lightpink', 'hotpink', 'deeppink', 'palevioletred', 'mediumvioletred',  # pink
          'white', 'snow', 'honeydew', 'mintcream', 'azure', 'aliceblue', 'ghostwhite', 'whitesmoke', 'seashell', 'beige', 'oldlace', 'floralwhite', 'ivory', 'antiquewhite', 'linen', 'lavenderblush', 'mistyrose',  # white
          'gainsboro', 'lightgray', 'silver', 'darkgray', 'gray', 'dimgray', 'lightslategray', 'slategray', 'darkslategray', 'black',  # black
          'cornsilk', 'blanchedalmond', 'bisque', 'navajowhite', 'wheat', 'burlywood', 'tan', 'rosybrown', 'sandybrown', 'goldenrod', 'peru', 'chocolate', 'saddlebrown', 'sienna', 'brown', 'maroon']  # brown

_startup_time = time.time() #TODO: could get reloaded so not accurate?


def log(msg, level='debug'):
    _level = xbmc.LOGDEBUG
    debug = get_setting_bool('logging.debug')
    logpath = os.path.join(_addon_path, 'aw_debug.log')

    if level == 'debug':
        _level = xbmc.LOGDEBUG
    elif level in ['notice', 'info']:
        try:
            _level = xbmc.LOGNOTICE
        except AttributeError:
            _level = xbmc.LOGINFO
    elif level == 'error':
        _level = xbmc.LOGERROR

    msg = u'{}: {}'.format(_addon_id, six.text_type(msg))
    xbmc.log(msg, _level)
    if debug:
        debug_size = os.path.getsize(logpath) if os.path.exists(logpath) else 0
        debug_msg = u'{}  {}{}'.format(time.ctime(), level.upper(), msg[25:])
        write_file(logpath, debug_msg + '\n', mode='a' if debug_size < 1048576 else 'w')


def ensure_addon_data():
    if not os.path.exists(_addon_path):
        os.makedirs(_addon_path)


def wipe(folder=_addon_path):
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', get_string(32065))

    if choice:
        for root, dirs, files in os.walk(folder):
            backup_location = xbmc.translatePath(
                                  _addon.getSetting('backup.location'))
            for name in files:
                file = os.path.join(root, name)
                if backup_location not in file:
                    os.remove(file)
            for name in dirs:
                dir = os.path.join(root, name)
                if backup_location[:-1] not in dir:
                    os.rmdir(dir)


def get_art(filename, color=None):
    art = {}
    if not color:
        color = get_setting('ui.color')
    
    themed_path = os.path.join(_addon_path, color)
    if not os.path.exists(themed_path):
        os.makedirs(themed_path)
    
    for i in art_types:
        _i = i
        if i == 'thumb':
            _i = 'icon'
        path = os.path.join(_art_path, _i, '{}.png'.format(filename))
        new_path = ''
        
        if os.path.exists(path):
            if color.lower() not in ['white', '#ffffff']:
                new_path = os.path.join(themed_path, '{}-{}.png'.format(filename, _i))
                if not os.path.exists(new_path):
                    icon = Image.open(path).convert('RGBA')
                    overlay = Image.new('RGBA', icon.size, color)
                    Image.composite(overlay, icon, icon).save(new_path)
            art[i] = clean_artwork_url(new_path if os.path.exists(new_path) else path)

    return art


def set_color(setting=False):
    dialog = xbmcgui.Dialog()
    color = get_setting('ui.color')
    
    choice = dialog.yesno('AutoWidget', get_string(32133),
                          yeslabel=get_string(32134), nolabel=get_string(32135))
    
    if choice:
        value = dialog.input(get_string(32136)).lower()
    else:
        value = dialog.select(get_string(32137),
                              ['[COLOR {0}]{0}[/COLOR]'.format(i) for i in colors],
                              preselect=colors.index(color) if color in colors else -1)
        if value > -1:
            value = colors[value]

    if value != -1:
        if value not in colors:
            if len(value) < 6:
                dialog.notification('AutoWidget', get_string(32138))
                return
            elif len(value) == 6 and not value.startswith('#'):
                value = '#{}'.format(value)
        if setting:
            set_setting('ui.color', value)
            
    return value


def get_active_window():
    xml_file = get_infolabel('Window.Property(xmlfile)').lower()

    if xbmc.getCondVisibility('Window.IsMedia()'):
        return 'media'
    elif 'dialog' in xml_file:
        return 'dialog'
    elif xbmc.getCondVisibility('Window.IsActive(home)'):
        return 'home'
    else:
        pass


def update_container(reload=False):
    if reload:
        log('Triggering library update to reload widgets', 'debug')
        xbmc.executebuiltin('UpdateLibrary(video, AutoWidget)')
    if get_active_window() == 'media':
        xbmc.executebuiltin('Container.Refresh()')


def _prettify(elem):
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='\t')


def get_valid_filename(filename):
    whitelist = '-_.() {}{}'.format(string.ascii_letters, string.digits)
    char_limit = 255

    filename = filename.replace(' ','_')
    cleaned_filename = unicodedata.normalize('NFKD',
                                             filename).encode('ASCII',
                                                              'ignore').decode()

    cleaned_filename = ''.join(c for c in cleaned_filename if c in whitelist)
    if len(cleaned_filename) > char_limit:
        print('Warning, filename truncated because it was over {} characters. '
              'Filenames may no longer be unique'.format(char_limit))
              
    return cleaned_filename[:char_limit]    


def get_unique_id(key):
    return '{}-{}'.format(get_valid_filename(six.ensure_text(key)),
                          time.time()).lower()


def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.items()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, six.text_type):
        return six.ensure_text(input)
        
    return input


def remove_file(file):
    if os.path.exists(file):
        try:
            os.remove(file)
        except Exception as e:
            log('Could not remove {}: {}'.format(file, e),
                level='error')


def read_file(file):
    content = None
    if os.path.exists(file):
        with io.open(os.path.join(_addon_path, file), 'r', encoding='utf-8') as f:
            try:
                content = f.read()
            except Exception as e:
                log('Could not read from {}: {}'.format(file, e),
                    level='error')
    else:
        log('{} does not exist.'.format(file), level='error')

    return content


def write_file(file, content, mode='w'):
    with open(file, mode) as f:
        try:
            f.write(content)
            return True
        except Exception as e:
            log('Could not write to {}: {}'.format(file, e),
                level='error')

    return False


def read_json(file, log_file=False):
    data = None
    if os.path.exists(file):
        with codecs.open(os.path.join(_addon_path, file), 'r', encoding='utf-8') as f:
            content = six.ensure_text(f.read())
            try:
                data = json.loads(content)
            except ValueError as e:
                log('Could not read JSON from {}: {}'.format(file, e),
                    level='error')
                if log_file:
                    log(content, level='notice')
    else:
        log('{} does not exist.'.format(file), level='error')

    return convert(data)


def write_json(file, content):
    with codecs.open(file, 'w', encoding='utf-8') as f:
        try:
            json.dump(content, f, indent=4)
        except Exception as e:
            log('Could not write to {}: {}'.format(file, e),
                level='error')


def set_setting(setting, value):
    return _addon.setSetting(setting, value)


def get_setting(setting):
    return _addon.getSetting(setting)


def get_setting_bool(setting):
    try:
        return _addon.getSettingBool(setting)
    except AttributeError:
        return bool(_addon.getSetting(setting))


def get_setting_int(setting):
    try:
        return _addon.getSettingInt(setting)
    except AttributeError:
        return int(_addon.getSetting(setting))


def get_setting_float(setting):
    try:
        return _addon.getSettingNumber(setting)
    except AttributeError:
        return float(_addon.getSetting(setting))


def get_skin_string(string):
    return get_infolabel('Skin.String({})'.format(string))


def set_skin_string(string, value):
    xbmc.executebuiltin('Skin.SetString({},{})'.format(string, value))


def translate_path(path):
    return xbmc.translatePath(path)


def get_string(_id):
    return six.text_type(_addon.getLocalizedString(_id))


def set_property(property, value, window=10000):
    xbmcgui.Window(window).setProperty(property, value)

def get_property(property, window=10000):
    return xbmcgui.Window(window).getProperty(property)

def push_queue(property, value):
    set_property(property, ",".join(get_property(property).split(",") + [value]))

def pop_queue(property):
    queue = get_property(property).split(',')
    value = queue.pop()
    set_property(property, ",".join(queue))
    return value

def clear_property(property, window=10000):
    xbmcgui.Window(window).clearProperty(property)


def get_infolabel(label):
    return xbmc.getInfoLabel(label)


def get_condition(cond):
    return xbmc.getCondVisibility(cond)


def clean_artwork_url(url):
    url = unquote(url).replace(_home, 'special://home/').replace('image://', '')
    if url.endswith('/'):
        url = url[:-1]
    return url


def _get_json_version():
    params = {'jsonrpc': '2.0', 'id': 1,
              'method': 'JSONRPC.Version'}
    result = json.loads(call_jsonrpc(json.dumps(params)))['result']['version']
    return (result['major'], result['minor'], result['patch'])

def cache_files(path, widget_id):
    hash = hashlib.sha1(six.text_type(path)).hexdigest()
    cache_path = os.path.join(_addon_path, '{}.cache'.format(hash))
    version = _get_json_version()
    props = version == (10, 3, 1) or (version[0] >= 11 and version[1] >= 12)
    props_info = info_types + ['customproperties']
    params = {'jsonrpc': '2.0', 'method': 'Files.GetDirectory',
              'params': {'properties': info_types if not props else props_info,
                         'directory': path},
              'id': 1}
    files_json = call_jsonrpc(json.dumps(params))
    files = json.loads(files_json)
    write_json(cache_path, files)
    expiry = cache_expiry(hash, widget_id, add=hashlib.sha1(files_json.encode('utf8')).hexdigest())
    log("Wrote cache (exp in {}s): {}".format(expiry-time.time(), hash), 'notice')
    return files


def cache_expiry(hash, widget_id, add=None):
    # Currently just caches for 5 min so that the background refresh doesn't go in a loop.
    # In the future it will cache for longer based on the history of how often in changed
    # and when it changed in relation to events like events events.
    # It should also manage the cache files to remove any too old.
    # The cache expiry can also be used later to schedule a future background update.

    # Read file every time as we might be called from multiple processes
    _history_path = os.path.join(_addon_path, '{}.history'.format(hash))
    cache_data = read_json(_history_path)
    if not cache_data:
        _history = {}
    history = cache_data.setdefault('history', [])
    if add:
        history.append( (time.time(), add))
        widgets = cache_data.setdefault('widgets', [])
        if widget_id not in widgets:
            widgets.append(widget_id)
        write_json(_history_path, cache_data)
    # predict next update time 
    if not history:
        return time.time() - 20 # make sure its expired so it updates correctly
    else:
        return history[-1][0] + 60*5 # just cache 5m until background update is done


def widgets_changed_by_watching():
    # Predict which widgets the skin might have that could have changed based on recently finish
    # watching something
    
    # Simple version. Anything updated recently (since startup?)
    all_cache = filter(os.path.isfile, glob.glob(os.path.join(_addon_path, "*.history")))
    log("recently updated cache {}".format(all_cache), 'notice')
    for path in sorted(all_cache, key=os.path.getmtime):
        cache_data = read_json(path)
        history = cache_data.setdefault('history', [])
        last_update = history[-1][0]
        if last_update > _startup_time:
            for widget_id in cache_data.get('widgets',[]):
                yield widget_id




def save_playback_history(media_type, playback_percentage):
    # Record in json when things got played to help predict which widgets will change after playback
    pass

def call_builtin(action, delay=0):
    if delay:
        xbmc.sleep(delay)
    xbmc.executebuiltin(six.text_type(action))


def call_jsonrpc(request):
    return xbmc.executeJSONRPC(request)


@contextlib.contextmanager
def timing(description):
    start = time.time()
    yield
    elapsed = time.time() - start

    log('{}: {}'.format(description, elapsed))
