from resources.lib.common import utils


if __name__ == "__main__":
    target = utils.get_infolabel("ListItem.Property(autoCache)")
    if target:
        utils.clear_cache(target)
