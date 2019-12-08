import xbmc
import xbmcgui


def _wait_for_dialog(success_cond, dialog, timeout=30, auto=False):
    import time
    
    clicked = False
    start = time.time()
    
    cond = 'Window.Is({0})'.format(dialog)
    visible_cond = 'Window.IsVisible({0})'.format(dialog)
    active_cond = 'Window.IsActive({0})'.format(dialog)
    topmost_cond = 'Window.IsTopMost({0})'.format(dialog)
    dialogtopmost_cond = 'Window.IsDialogTopMost({0})'.format(dialog)
    modaltopmost_cond = 'Window.IsModalDialogTopMost({0})'.format(dialog)
    
    xbmc.sleep(1000)
    
    while not xbmc.getCondVisibility(success_cond):
        if timeout > 0:
            if time.time() >= start + timeout:
                xbmc.log('Dialog timed out.', level=xbmc.LOGDEBUG)
                return False

        xbmc.sleep(1000)

        if xbmc.getCondVisibility(visible_cond) and not clicked:
            xbmc.log('Dialog open.', level=xbmc.LOGDEBUG)
            
            # in order to auto-click the dialog
            if auto:
                xbmc.executebuiltin('SendClick(yesnodialog, 11)')
                clicked = True
        else:
            xbmc.log('Waiting for dialog...', level=xbmc.LOGDEBUG)

    xbmc.log('Dialog success!', level=xbmc.LOGDEBUG)
    return True

class Path:
    def __init__(self):
        pass
        
    def add(self):
        showNone = 'False'
        grouping = 'default'
        skinWidget = 'autowidget-{0}'.format(1)
        skinWidgetType = 'autowidgetType-{0}'.format(1)
        skinWidgetName = 'autowidgetName-{0}'.format(1)
        skinWidgetTarget = 'autowidgetTarget-{0}'.format(1)
        skinWidgetPath = 'autowidgetPath-{0}'.format(1)
    
        xbmc.executebuiltin("RunScript(script.skinshortcuts,type=widgets&amp;showNone=False&amp;skinWidgetType=autoWidgetType-1&amp;skinWidgetName=autoWidgetName-1&amp;skinWidgetTarget=autoWidgetTarget-1&amp;skinWidgetPath=autoWidgetPath-1)")
