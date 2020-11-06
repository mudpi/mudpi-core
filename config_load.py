import json


def load_config_json():
    configs = {}

    with open('mudpi.config') as loadedfile:
        configs = json.load(loadedfile)
        loadedfile.close()
        return configs
