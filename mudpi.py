import RPi.GPIO as GPIO
import threading
import datetime
import socket
import time
import json
import sys
sys.path.append('..')
from action import Action
from config_load import loadConfigJson
from server.mudpi_server import MudpiServer
from workers.lcd_worker import LCDWorker
from workers.relay_worker import RelayWorker
from workers.camera_worker import CameraWorker
from workers.trigger_worker import TriggerWorker
from workers.pi_sensor_worker import PiSensorWorker
from workers.pi_control_worker import PiControlWorker
from workers.pi_i2c_worker import PiI2CWorker	
try:
	from workers.arduino_worker import ArduinoWorker
	NANPY_ENABLED = True
except ImportError:
	NANPY_ENABLED = False
try:
	from workers.adc_worker import ADCMCP3008Worker
	MCP_ENABLED = True
except ImportError:
	MCP_ENABLED = False
import variables

##############################
#	MudPi Core 
#	Author: Eric Davisson (@theDavisson)
#	https://mudpi.app
#	MudPi Core is a python library to gather sensor readings, control components, 
#	and manage devices using a Raspberry Pi on an event based system using redis. 
#	
CONFIGS = {}
PROGRAM_RUNNING = True
threads = []
actions = {}
relays = []
relayEvents = {}
relay_index = 0
workers = []
nodes = []

print(chr(27) + "[2J")
print('Loading MudPi Configs...\r', end="", flush=True)
CONFIGS = loadConfigJson()
# Waiting for redis and services to be running
time.sleep(5) 
print('Loading MudPi Configs...\t\033[1;32m Complete\033[0;0m')                       
print(chr(27) + "[2J")
# Print a display logo for startup
print("\033[1;32m")
print(' __  __           _ _____ _ ')
print('|  \/  |         | |  __ (_)')
print('| \  / |_   _  __| | |__) | ')
print('| |\/| | | | |/ _` |  ___/ | ')
print('| |  | | |_| | (_| | |   | | ')
print('|_|  |_|\__,_|\__,_|_|   |_| ')
print('_________________________________________________')
print('')
print('Eric Davisson @theDavisson')
print('https://mudpi.app')
print('Version: ', CONFIGS.get('version', '0.8.14'))
print('\033[0;0m')

if CONFIGS['debug'] is True:
	print('\033[1;33mDEBUG MODE ENABLED\033[0;0m')
	print("Loaded Config\n--------------------")
	for index, config in CONFIGS.items():
		if config != '':
			print('%s: %s' % (index, config))
	time.sleep(10)

try:
	print('Initializing Garden Control \r', end="", flush=True)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.cleanup()
	# Pause for GPIO to finish
	time.sleep(0.1)
	print('Initializing Garden Control...\t\t\033[1;32m Complete\033[0;0m')
	print('Preparing Threads for Workers\r', end="", flush=True)

	new_messages_waiting = threading.Event() 	# Event to signal LCD to pull new messages
	main_thread_running = threading.Event() 	# Event to signal workers to close
	system_ready = threading.Event() 			# Event to tell workers to begin working
	camera_available = threading.Event() 		# Event to signal if camera can be used

	main_thread_running.set() 					# Main event to tell workers to run/shutdown
	time.sleep(0.1)
	print('Preparing Threads for Workers...\t\033[1;32m Complete\033[0;0m')

	# Worker for Camera
	try:
		c = CameraWorker(CONFIGS['camera'], main_thread_running, system_ready, camera_available)
		print('MudPi Camera...\t\t\t\033[1;32m Initializing\033[0;0m')
		workers.append(c)
		camera_available.set()
	except KeyError:
		print('MudPi Pi Camera...\t\t\t\033[1;31m Disabled\033[0;0m')

	# Workers for pi (Sensors, Controls, Relays, I2C)
	try:
		for worker in CONFIGS['workers']:
			# Create worker for worker
			if worker['type'] == "sensor":
				pw = PiSensorWorker(worker, main_thread_running, system_ready)
				print('MudPi Sensors...\t\t\t\033[1;32m Initializing\033[0;0m')
			elif worker['type'] == "control":
				pw = PiControlWorker(worker, main_thread_running, system_ready)
				print('MudPi Controls...\t\t\t\033[1;32m Initializing\033[0;0m')
			elif worker['type'] == "i2c":
				pw = PiI2CWorker(worker, main_thread_running, system_ready)
				print('MudPi I2C...\t\t\t\t\033[1;32m Initializing\033[0;0m')
			elif worker['type'] == "relay":
				# Add Relay Worker Here for Better Config Control
				print('MudPi Relay...\t\t\t\033[1;32m Initializing\033[0;0m')
			else:
				raise Exception("Unknown Worker Type: " + worker['type'])
			workers.append(pw)
	except KeyError:
		print('MudPi Pi Workers...\t\t\033[1;31m Disabled\033[0;0m')

	# Worker for relays attached to pi
	try:
		for relay in CONFIGS['relays']:
			relayState = {
				"available": threading.Event(), # Event to allow relay to activate
				"active": threading.Event() 	# Event to signal relay to open/close
			}
			relayEvents[relay.get("key", relay_index)] = relayState
			r = RelayWorker(relay, main_thread_running, system_ready, relayState['available'], relayState['active'])
			workers.append(r)
			# Make the relays available, this event is toggled off elsewhere if we need to disable relays
			relayState['available'].set()
			relay_index +=1
	except KeyError:
		print('MudPi Relays Workers...\t\t\033[1;31m Disabled\033[0;0m')

	# Load in Actions
	try:
		for action in CONFIGS["actions"]:
			print('MudPi Actions...\t\t\t\033[1;32m Initializing\033[0;0m')
			a = Action(action)
			a.init_action()
			actions[a.key] = a
	except KeyError:
		print('MudPi Actions...\t\t\t\033[1;31m Disabled\033[0;0m')

	# Worker for Triggers
	try:
		t = TriggerWorker(CONFIGS['triggers'], main_thread_running, system_ready, actions)
		print('MudPi Triggers...\t\t\t\033[1;32m Initializing\033[0;0m')
		workers.append(t)
	except KeyError:
		print('MudPi Triggers...\t\t\t\033[1;31m Disabled\033[0;0m')

	# Worker for nodes attached to pi via serial or wifi[esp8266, esp32]
	# Supported nodes: arduinos, esp8266, ADC-MCP3xxx, probably others (esp32 with custom nanpy fork)
	try:
		for node in CONFIGS['nodes']:
			if node['type'] == "arduino":
				if NANPY_ENABLED:
					print('MudPi Arduino Workers...\t\t\033[1;32m Initializing\033[0;0m')
					t = ArduinoWorker(node, main_thread_running, system_ready)
				else:
					print('Error Loading Nanpy library. Did you pip3 install -r requirements.txt?')
			elif node['type'] == "ADC-MCP3008":
				if MCP_ENABLED:
					print('MudPi ADC Workers...\t\t\033[1;32m Initializing\033[0;0m')
					t = ADCMCP3008Worker(node, main_thread_running, system_ready)
				else:
					print('Error Loading MCP3xxx library. Did you pip3 install -r requirements.txt;?')
			else:
				raise Exception("Unknown Node Type: " + node['type'])
			nodes.append(t)
	except KeyError as e:
		print('MudPi Node Workers...\t\t\033[1;31m Disabled\033[0;0m')

	try:
		if (CONFIGS['server'] is not None):
			print('MudPi Server...\t\t\t\t\033[1;33m Starting\033[0;0m', end='\r', flush=True)
			time.sleep(1)
			server = MudpiServer(main_thread_running, CONFIGS['server']['host'], CONFIGS['server']['port'])
			s = threading.Thread(target=server_worker)
			threads.append(s)
			s.start()
	except KeyError:
		print('No Server Config Found to Load')


	print('MudPi Garden Control...\t\t\t\033[1;32m Initialized\033[0;0m')
	for worker in workers:
		t = worker.run()
		threads.append(t)
		time.sleep(.5)
	for node in nodes:
		t = node.run()
		threads.append(t)
		time.sleep(.5)

	time.sleep(.5)
	print('MudPi Garden Control...\t\t\t\033[1;32m Online\033[0;0m')
	print('_________________________________________________')
	system_ready.set() #Workers will not process until system is ready
	variables.r.set('started_at', str(datetime.datetime.now())) #Store current time to track uptime
	system_message = {'event':'SystemStarted', 'data':1}
	variables.r.publish('mudpi', json.dumps(system_message))
	
	# Hold the program here until its time to graceful shutdown
	while PROGRAM_RUNNING:
		# Main program loop
		# add logging or other system operations here...
		time.sleep(0.1)

except KeyboardInterrupt:
	PROGRAM_RUNNING = False
finally:
	print('MudPi Shutting Down...')
	# Perform any cleanup tasks here...

	try:
		server.sock.shutdown(socket.SHUT_RDWR)
	except:
		pass
	
	# Clear main running event to signal threads to close
	main_thread_running.clear()

	# Shutdown the camera loop
	camera_available.clear()

	# Join all our threads for shutdown
	for thread in threads:
		thread.join()

	print("MudPi Shutting Down...\t\t\t\033[1;32m Complete\033[0;0m")
	print("Mudpi is Now...\t\t\t\t\033[1;31m Offline\033[0;0m")
	
