import json


def saveConfig(configs):
    with open(str(input('Config File Name: ')), 'w') as outfile:
        json.dump(configs, outfile, indent=4)
    # outfile.close()


def loadConfigJson():
    with open('mudpi.config') as loadedfile:
        configs = json.load(loadedfile)
        loadedfile.close()
        return configs


def loadConfig(configs):
    with open("config.mud") as configfile:
        for line in configfile:
            name, var = line.partition("=")[::2]
            configs[name.strip()] = (var)
        configfile.close()
