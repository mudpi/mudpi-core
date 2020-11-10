import json


def load_config_json():
    """

    Returns:
        Dictionary from json file.
    """

    with open('mudpi.config') as loadedfile:
        configs = json.load(loadedfile)
        loadedfile.close()
        return configs


def get_config_item(config, item, default=None, replace_char='_'):
    """

    Args:
        config:
        item:
        default:

    Returns:
        Configuration item
    """

    value = config.get(item, default)

    if type(value) == str:
        value = value.replace(" ", replace_char).lower()

    return value
