import threading
import RPi.GPIO as GPIO
import time
import datetime
import socket
import sys
import json
sys.path.append('..')
from workers.lcd_worker import LCDWorker
from workers.arduino_worker import ArduinoWorker
from workers.arduino_control_worker import ArduinoControlWorker
from workers.adc_worker import ADCMCP3008Worker
from workers.pi_sensor_worker import PiSensorWorker
from workers.relay_worker import RelayWorker
from workers.camera_worker import CameraWorker
from config_load import loadConfigJson
from server.mudpi_server import MudpiServer
import variables

# __  __           _ _____ _ 
#|  \/  |         | |  __ (_)
#| \  / |_   _  __| | |__) | 
#| |\/| | | | |/ _` |  ___/ |
#| |  | | |_| | (_| | |   | |
#|_|  |_|\__,_|\__,_|_|   |_|
# https://mudpi.app

CONFIGS = {}
PROGRAM_RUNNING = True
print(chr(27) + "[2J")
print('Loading MudPi Configs...\r', end="", flush=True)
#load the configuration
CONFIGS = loadConfigJson(CONFIGS)
#Waiting for redis and services to be running
time.sleep(5) 
print('Loading MudPi Configs...\t\033[1;32m Complete\033[0;0m')
time.sleep(1)

#Clear the console if its open for debugging                           
print(chr(27) + "[2J")
#Print a display logo for startup
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
print('Version: ', CONFIGS.get('version', '0.8.0'))
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
	#Pause for GPIO to finish
	time.sleep(0.1)
	print('Initializing Garden Control...\t\t\033[1;32m Complete\033[0;0m')
	print('Preparing Threads for Workers\r', end="", flush=True)

	threads = []
	relays = []
	relayEvents = {}
	relay_index = 0
	variables.lcd_message = {'line_1': 'Mudpi Control', 'line_2': 'Is Now Running'}

	new_messages_waiting = threading.Event() #Event to signal LCD to pull new messages
	main_thread_running = threading.Event() #Event to signal workers to close
	system_ready = threading.Event() #Event to tell workers to begin working
	camera_available = threading.Event() #Event to signal if camera can be used
	main_thread_running.set() #Main event to tell workers to run/shutdown

	time.sleep(0.1)
	print('Preparing Threads for Workers...\t\033[1;32m Complete\033[0;0m')

	#l = LCDWorker(new_messages_waiting,main_thread_running,system_ready)
	#print('Loading LCD Worker')
	#l = l.run()
	#threads.append(l)

	# Worker for Camera
	try:
		c = CameraWorker(CONFIGS['camera'], main_thread_running, system_ready, camera_available)
		print('Loading Pi Camera Worker')
		c = c.run()
		threads.append(c)
		camera_available.set()
	except KeyError:
		print('No Camera Found to Load')

	# Worker for sensors attached to pi
	try:
		ps = PiSensorWorker(CONFIGS['sensors'], main_thread_running, system_ready)
		print('Loading Pi Sensor Worker')
		ps = ps.run()
		threads.append(ps)
	except KeyError:
		print('No Sensors Found to Load')

	# Worker for relays attached to pi
	try:
		for relay in CONFIGS['relays']:
			#Create a threading event for each relay to check status
			relayState = {
				"available": threading.Event(), #Event to allow relay to activate
				"active": threading.Event() #Event to signal relay to open/close
			}
			#Store the relays under the key or index if no key is found, this way we can reference the right relays
			relayEvents[relay.get("key", relay_index)] = relayState
			#Create sensor worker for a relay
			r = RelayWorker(relay, main_thread_running, system_ready, relayState['available'], relayState['active'])
			r = r.run()
			#Make the relays available, this event is toggled off elsewhere if we need to disable relays
			relayState['available'].set()
			relay_index +=1
			if r is not None:
				threads.append(r)
	except KeyError:
		print('No Relays Found to Load')

	# Worker for nodes attached to pi via serial or wifi[esp8266]
	# Supported nodes: arduinos, esp8266, ADC-MCP3xxx, probably others
	try:
		for node in CONFIGS['nodes']:
			# Create worker for node
			if node['type'] == "arduino":
				t = ArduinoWorker(node, main_thread_running, system_ready)
				# if node['controls'] is not None:
				# 	acw = ArduinoControlWorker(node, main_thread_running, system_ready, t.connection)
				# 	acw = acw.run()
				# 	if acw is not None:
				# 		threads.append(acw)
			elif node['type'] == "ADC-MCP3008":
				t = ADCMCP3008Worker(node, main_thread_running, system_ready)
			else:
				raise Exception("Unknown Node Type: " + node['type'])
			t = t.run()
			if t is not None:
				threads.append(t)
	except KeyError:
		print('Invalid or no Nodes found to Load')


	#Decided not to build server worker (this is replaced with nodejs, expressjs)
	#Maybe use this for internal communication across devices if using wireless
	def server_worker():
		server.listen()
	print('Initializing Server')
	server = MudpiServer(main_thread_running, CONFIGS['server']['host'], CONFIGS['server']['port'])
	s = threading.Thread(target=server_worker)
	threads.append(s)
	s.start()


	time.sleep(.5)
	print('MudPi Garden Control...\t\t\t\033[1;32m Online\033[0;0m')
	print('_________________________________________________')
	system_ready.set() #Workers will not process until system is ready
	variables.r.set('started_at', str(datetime.datetime.now())) #Store current time to track uptime
	system_message = {'event':'SystemStarted', 'data':1}
	variables.r.publish('mudpi', json.dumps(system_message))
	

	#Hold the program here until its time to graceful shutdown
	#This is our pump cycle check, Using redis to determine if pump should activate
	while PROGRAM_RUNNING:
		# Main program loop
		# add logging or other system operations here...
		time.sleep(0.1)

except KeyboardInterrupt:
	PROGRAM_RUNNING = False
finally:
	print('MudPi Shutting Down...')
	#Perform any cleanup tasks here...

	#load a client on the server to clear it from waiting
	# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#sock.connect((CONFIGS['SERVER_HOST'], int(CONFIGS['SERVER_PORT'])))
	server.sock.shutdown(socket.SHUT_RDWR)
	# time.sleep(1)
	# sock.close()
	
	#Clear main running event to signal threads to close
	main_thread_running.clear()

	#Shutdown the camera loop
	camera_available.clear()

	#Join all our threads for shutdown
	for thread in threads:
		thread.join()

	print("MudPi Shutting Down...\t\t\t\033[1;32m Complete\033[0;0m")
	print("Mudpi is Now...\t\t\t\t\033[1;31m Offline\033[0;0m")
	