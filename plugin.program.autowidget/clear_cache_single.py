from resources.lib.common import cache
from resources.lib.common import utils


if __name__ == "__main__":
    target = utils.get_infolabel("ListItem.Property(autoCache)")
    if target:
        cache.clear_cache(target)
