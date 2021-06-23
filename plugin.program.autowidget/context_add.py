from resources.lib import add
from resources.lib.common import utils


if __name__ == "__main__":
    utils.ensure_addon_data()

    labels = add.build_labels("context")
    add.add(labels)
