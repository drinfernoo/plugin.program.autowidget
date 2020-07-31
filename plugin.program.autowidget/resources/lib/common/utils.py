import xbmc
import xbmcaddon
import xbmcgui

import codecs
import io
import json
import os
import string
import time
import unicodedata

import six
from PIL import Image

from xml.dom import minidom
from xml.etree import ElementTree

try:
    from urllib.parse import unquote
except ImportError:
    from urlparse import unquote

_addon = xbmcaddon.Addon()
_addon_id = _addon.getAddonInfo('id')
_addon_path = xbmc.translatePath(_addon.getAddonInfo('profile'))
_addon_root = xbmc.translatePath(_addon.getAddonInfo('path'))
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


def log(msg, level=xbmc.LOGDEBUG):
    msg = '{}: {}'.format(_addon_id, msg)
    xbmc.log(msg, level)


def ensure_addon_data():
    if not os.path.exists(_addon_path):
        os.makedirs(_addon_path)


def wipe(folder=_addon_path):
    dialog = xbmcgui.Dialog()
    choice = dialog.yesno('AutoWidget', get_string(32065))
    backup_location = xbmc.translatePath(get_setting('backup.location'))

    if choice:
        for root, dirs, files in os.walk(folder):
            for name in files:
                file = os.path.join(root, name)
                if backup_location not in file:
                    os.remove(file)
            for name in dirs:
                dir = os.path.join(root, name)
                if backup_location[:-1] not in dir:
                    os.rmdir(dir)


def get_art(filename):
    art = {}
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


def set_color():
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
            
    if value:
        if value not in colors:
            if len(value) < 6:
                dialog.notification('AutoWidget', get_string(32138))
                return
            elif len(value) == 6 and not value.startswith('#'):
                value = '#{}'.format(value)
                
        set_setting('ui.color', value)


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


def update_container(_type='', reload=False):
    xbmc.executebuiltin('UpdateLibrary(video, AutoWidget)')

    if reload:
        xbmc.executebuiltin('ReloadSkin()')
    else:
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
                level=xbmc.LOGERROR)


def read_file(file):
    content = None
    if os.path.exists(file):
        with io.open(os.path.join(_addon_path, file), 'r', encoding='utf-8') as f:
            try:
                content = f.read()
            except Exception as e:
                log('Could not read from {}: {}'.format(file, e),
                    level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)

    return content


def write_file(file, content):
    with open(file, 'w') as f:
        try:
            f.write(content)
            return True
        except Exception as e:
            log('Could not write to {}: {}'.format(file, e),
                level=xbmc.LOGERROR)

    return False


def read_json(file):
    data = None
    if os.path.exists(file):
        with codecs.open(os.path.join(_addon_path, file), 'r', encoding='utf-8') as f:
            try:
                content = six.ensure_text(f.read())
                data = json.loads(content)
            except Exception as e:
                log('Could not read JSON from {}: {}'.format(file, e),
                    level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)

    return convert(data)


def write_json(file, content):
    with codecs.open(file, 'w', encoding='utf-8') as f:
        try:
            json.dump(content, f, indent=4)
        except Exception as e:
            log('Could not write to {}: {}'.format(file, e),
                level=xbmc.LOGERROR)


def read_xml(file):
    xml = None
    if os.path.exists(file):
        try:
            xml = ElementTree.parse(file).getroot()
        except Exception as e:
            log('Could not read XML from {}: {}'.format(file, e),
                level=xbmc.LOGERROR)
    else:
        log('{} does not exist.'.format(file), level=xbmc.LOGERROR)

    return xml


def write_xml(file, content):
    _prettify(content)
    tree = ElementTree.ElementTree(content)

    try:
        tree.write(file)
    except Exception as e:
        log('Could not write to {}: {}'.format(file, e),
                  level=xbmc.LOGERROR)


def set_setting(setting, value):
    return _addon.setSetting(setting, value)


def get_setting(setting):
    return _addon.getSetting(setting)


def get_setting_bool(setting):
    try:
        return _addon.getSettingBool(setting)
    except:
        return bool(_addon.getSetting(setting))


def get_setting_int(setting):
    try:
        return _addon.getSettingInt(setting)
    except:
        return int(_addon.getSetting(setting))


def get_setting_float(setting):
    try:
        return _addon.getSettingNumber(setting)
    except:
        return float(_addon.getSetting(setting))


def get_skin_string(string):
    return get_infolabel('Skin.String({})'.format(string))


def set_skin_string(string, value):
    xbmc.executebuiltin('Skin.SetString({},{})'.format(string, value))


def get_string(_id):
    return six.text_type(_addon.getLocalizedString(_id))


def set_property(property, value, window=10000):
    xbmcgui.Window(window).setProperty(property, value)


def clear_property(property, window=10000):
    xbmcgui.Window(window).clearProperty(property)


def get_infolabel(label):
    return xbmc.getInfoLabel(label)


def clean_artwork_url(url):
    url = unquote(url).replace(_home, 'special://home/').replace('image://', '')
    if url.endswith('/'):
        url = url[:-1]
    return url


def _get_json_version():
    params = {'jsonrpc': '2.0', 'id': 1,
              'method': 'JSONRPC.Version'}
    result = json.loads(xbmc.executeJSONRPC(json.dumps(params)))['result']['version']
    return (result['major'], result['minor'], result['patch'])


def get_files_list(path, titles=None):
    if not titles:
        titles = []
    version = _get_json_version()
    props = version == (10, 3, 1) or (version[0] >= 11 and version[1] >= 12)
    props_info = info_types + ['customproperties']
    params = {'jsonrpc': '2.0', 'method': 'Files.GetDirectory',
              'params': {'properties': info_types if not props else props_info,
                         'directory': path},
              'id': 1}
    
    files = json.loads(xbmc.executeJSONRPC(json.dumps(params)))
    new_files = []
    if 'error' not in files:
        files = files['result']['files']
        filtered_files = [x for x in files if x['title'] not in titles]
        for file in filtered_files:
            new_file = {k: v for k, v in file.items() if v not in [None, '', -1, [], {}]}
            if 'art' in new_file:
                for art in new_file['art']:
                    new_file['art'][art] = clean_artwork_url(file['art'][art])
            new_files.append(new_file)
                
        return new_files