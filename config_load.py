import json 

def saveConfig(configs):
	with open(str(input('Config File Name: ')), 'w') as outfile:  
		json.dump(configs, outfile, indent=4)
		#outfile.close()

def loadConfigJson(configs):
	with open('mudpi.config') as loadedfile:
		configs = json.load(loadedfile)
		return configs
		loadedfile.close()

def loadConfig(configs):
	with open("config.mud") as configfile:
		for line in configfile:
			name, var = line.partition("=")[::2]
			configs[name.strip()] = (var)
		configfile.close()