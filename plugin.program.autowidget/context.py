import xbmc

from resources.lib import add
from resources.lib.common import migrate
from resources.lib.common import utils


if __name__ == '__main__':
    utils.ensure_addon_data()
    migrate.migrate_groups()

    labels = add.build_labels('context')
    add.add(labels)
