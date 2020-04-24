# AutoWidget
AutoWidget is a program add-on for Kodi, designed to give a more dynamic
and interesting experience to using skin widgets. 

## Requirements
While AutoWidget doesn't **depend** on any other add-ons, it is specifically designed for use with skins that use Skin Shortcuts to manage their menu and/or widgets. While a significant amount of work has gone into making sure that it will work with almost any skin which supports Skin Shortcuts, there may be special circumstances that haven't been accounted for. Feel free to open an issue if you find a skin or section where AutoWidget isn't able to initialize and/or update its widgets.

## Steps to Install
1. Go to the Kodi file manager.
2. Click on "Add source".
3. The path for the source is `https://drinfernoo.github.io/` (Give it the name "drinfernoo").
4. Go to "Add-ons", and choose "Install from zip".
5. a. For AutoWidget's Stable repo, install `repository.autowidget-1.0.zip`.
   b. For AutoWidget's Dev repo (for testing purposes **only**), install `repository.autowidget.dev-1.0.zip`.
6. Return to "Add-ons", and choose "Install from repository".
7. Choose the repository you installed (stable or dev), and install AutoWidget from Program Add-ons.

## How to Use
AutoWidget is intended to work with any non-media path in Kodi. To add a path to an AutoWidget group, open the context menu on the item, and choose "Add to AutoWidget Group". Depending on the type of the item you're adding, you'll be able to add it as either a Shortcut, a Widget, or a Settings Shortcut (for direct plugin items only). After choosing the type of path you want to add the item as, you can then choose (or make a new) a group to add it to.

After you've set up groups with paths in them, it's time to point widgets at them. In your skin of choice's Skin Shortcuts management dialog, you can point any widget at an AutoWidget path.

To use a random AutoWidget, point a widget at `AutoWidget -> *Your Widget Group*-> Random Path from *Your Widget Group* -> Use as widget`. After Skin Shortcuts rebuilds the skin's menu, the widget you just set (and any other uninitialized AutoWidget) will be displayed with a single icon, labeled "Initialize Widgets". Choosing this item will cause a skin reload, but will initialize any defined AutoWidgets, and allow them to be refreshed on AutoWidget's schedule, automatically replacing the widget content with random path from the defined group, every so often (every two hours, by default).

Lastley, but certainly not leastly, by navigating to `AutoWidget -> *Your Shortcut Group*-> Shortcuts from *Your Shortcut Group* -> Use as widget`, you'll end up with a shortcut widget, similar to what many skins call a "submenu" or "category" widget.

Advanced topics will be covered on the wiki soon.

## Troubleshooting
> **After my widget got initialized, it changed back to Poster and lost its sorting/limit rules! What gives?**

This is a limitation of the way that Skin Shortcuts represents widgets internally. Widget attributes like aspect, item limit, and sorting method will be reset after an AutoWidget is initialized, but can be set afterwards, and will stay.

> **My widget never changes anymore! Who's in charge here?**

After initializing an AutoWidget, if either the label or the widget action are changed manually, they will quit updating correctly, and the widget will need to be set up again.

> **The label on my widget changes, but the widget takes forever to update! I'm writing a letter to the editor!**

Unfortunately, there isn't a reliable way for AutoWidget to know whether or not a widget's content has changed, so it must change the label and widget path at the same time. Any time waiting for a widget to change its content is simply the time it takes for the new path to load. In the case of library paths, this can be almost instant, but plugin paths can often take longer to load.

> **Some other thing isn't working for me! I wanna speak with your manager!**

Gladly! Simply [open an issue](https://www.github.com/drinfernoo/plugin.program.autowidget/issues/) :grin:
