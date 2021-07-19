from conftest import press

def test_add_widget_cycling():
    """
    >>> getfixture("home_with_dummy") # TODO:
    >>> getfixture("start_kodi")
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) AutoWidget
     2) Dummy
    -------------------------------
    Enter Action Number

    >>> press("c2")
     1) Add to AutoWidget Group

    >>> press("Add to AutoWidget Group")
    Add as
    0) Shortcut
    1) Widget
    2) Clone as Shortcut Group
    3) Explode as Widget Group

    >>> press("Widget")
    Choose a Group
    0) Create New Widget Group

    >>> press("Create New Widget Group")
    Name for Group

    >>> press("Widget1")
    Choose a Group
    0) Create New Widget Group
    1) Widget1

    >>> press("Widget1")
    Widget Label

    >>> press("My Label")
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) AutoWidget
     2) Dummy
    -------------------------------
    Enter Action Number

    >>> press("AutoWidget")
    LOGINFO - plugin.program.autowidget: [ root ]
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) My Groups
     2) Active Widgets
     3) Tools
    -------------------------------
    Enter Action Number
    
    >>> press("My Groups")
    LOGINFO - plugin.program.autowidget: [ mode: group ]
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) Widget1
    -------------------------------
    Enter Action Number

    >>> press("Widget1")
    LOGINFO - plugin.program.autowidget: [ mode: group ][ group: widget1-... ]
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) My Label
     2) Widget1 (Static)
     3) Widget1 (Cycling)
     4) Widget1 (Merged)
    -------------------------------
    Enter Action Number

    >>> press("Widget1 (Cycling)")
    LOGINFO - plugin.program.autowidget: [ mode: path ][ action: cycling ][ group: widget1-... ]
    Choose an Action
    0) Random Path
    1) Next Path

    >>> press("Next Path")
    LOGINFO - plugin.program.autowidget: Empty cache 0B (exp:-1 day, ...
    LOGINFO - plugin.program.autowidget: Blocking cache path read: ...
    LOGINFO - plugin.program.autowidget: Wrote cache ...
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) Dummy Item 1
     2) Dummy Item 2
     3) Dummy Item 3
     4) Dummy Item 4
    ...
     20) Dummy Item 20
    -------------------------------
    Enter Action Number

    """


def test_add_widget_merged():
    """
    >>> getfixture("home_with_dummy") # TODO:
    >>> getfixture("start_kodi")
    -------------------------------
    -1) Back
     0) Home
    -------------------------------
     1) AutoWidget
     2) Dummy
    -------------------------------
    Enter Action Number
    """


def test_cache_widget():
    """
    Add in a widget group
        >>> getfixture("home_with_dummy") 
        >>> getfixture("start_kodi")
        ---...
        ...
        >>> press("c2 > Add to AutoWidget Group > Widget > Create New Widget Group > Widget1"
        ... " > Widget1 > My Label")
         1)...
        ...

    Access it the first time it will get cached
        >>> press("Home > AutoWidget > My Groups > Widget1 > Widget1 (Cycling) > Next Path")
        ---...
        ...
        1) Dummy Item 1
        ...

    Now change the connent of dummy menu

        >>> _ = getfixture("dummy2")
        >>> press("Home > Dummy")
        ---...
        ...
        1) Dummy2 Item 1
        ...

    But our widget is still cached

        >>> press("Home > AutoWidget > My Groups > Widget1 > Widget1 (Cycling) > Next Path")
        ---...
        ...
        1) Dummy Item 1
        ...

    """


# if __name__ == '__main__':
#     autowidget()
#     dummy()
#     home_with_dummy()
#     doctest.testmod(optionflags=doctest.ELLIPSIS|doctest.REPORT_NDIFF|doctest.REPORT_ONLY_FIRST_FAILURE)
#     #teardown()
