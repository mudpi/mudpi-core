import json
import time

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

if __name__ == "__main__": 

	settings = { 'name':'MudPi', 'version':0.1, 'redis_host':'127.0.0.1', 'nodes': [ { 'name': 'Bed 1', 'address': '/tty/USB0'}, { 'name': 'Bed 2', 'address': '/tty/USB1'} ] }
	configs = {}
	data = {}
	data = loadConfigJson(data)
	print(json.dumps(data, indent=4))
