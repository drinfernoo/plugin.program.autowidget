from resources.lib import refresh
from resources.lib.common import utils


if __name__ == "__main__":
    widget_id = utils.get_infolabel("ListItem.Property(autoID)")
    if widget_id:
        refresh.refresh(widget_id, force=True, single=True)
