import json 

def loadConfigJson():
	configs = {}
	with open('mudpi.config') as loadedfile:
		configs = json.load(loadedfile)
		loadedfile.close()
		return configs
