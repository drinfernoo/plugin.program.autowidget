import xbmcaddon

import six


def get_localized_string(_id, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    s = six.text_type(_addon.getLocalizedString(_id))
    del _addon
    return s


def get_setting(setting, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    s = _addon.getSetting(setting)
    del _addon
    return s


def get_setting_bool(setting, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    try:
        s = _addon.getSettingBool(setting)
    except AttributeError:
        s = bool(_addon.getSetting(setting))
    del _addon
    return s


def get_setting_int(setting, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    try:
        s = _addon.getSettingInt(setting)
    except AttributeError:
        s = int(_addon.getSetting(setting))
    del _addon
    return s


def get_setting_float(setting, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    try:
        s = _addon.getSettingNumber(setting)
    except AttributeError:
        s = float(_addon.getSetting(setting))
    del _addon
    return s


def get_setting_string(setting, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    try:
        s = _addon.getSettingString(setting)
    except AttributeError:
        s = six.text_type(_addon.getSetting(setting))
    del _addon
    return s


def set_setting(setting, value, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    s = _addon.setSetting(setting, value)
    del _addon
    return s


def set_setting_bool(setting, value, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    try:
        s = _addon.setSettingBool(setting, value)
    except AttributeError:
        s = bool(_addon.setSetting(setting, value))
    del _addon
    return s


def set_setting_int(setting, value, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    try:
        s = _addon.setSettingInt(setting, value)
    except AttributeError:
        s = int(_addon.setSetting(setting, value))
    del _addon
    return s


def set_setting_float(setting, value, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    try:
        s = _addon.setSettingNumber(setting, value)
    except AttributeError:
        s = float(_addon.setSetting(setting, value))
    del _addon
    return s


def set_setting_string(setting, value, addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    try:
        s = _addon.setSettingString(setting, value)
    except AttributeError:
        s = six.text_type(_addon.setSetting(setting, value))
    del _addon
    return s


def open_settings(addon=None):
    _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
    s = _addon.openSettings()
    del _addon
    return s


def get_addon_info(label, addon=None):
    s = ""
    try:
        _addon = xbmcaddon.Addon() if not addon else xbmcaddon.Addon(addon)
        s = _addon.getAddonInfo(label)
        del _addon
    except:
        pass
    return s
