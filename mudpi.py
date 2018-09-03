import threading
from workers.lcd_worker import LCDWorker
from workers.sensor_worker import SensorWorker
from workers.pi_sensor_worker import PiSensorWorker
from workers.pump_worker import PumpWorker
import RPi.GPIO as GPIO
import time
import datetime
from config_load import loadConfigJson
from server.mudpi_server import MudpiServer
import variables
import socket
# __  __           _ _____ _ 
#|  \/  |         | |  __ (_)
#| \  / |_   _  __| | |__) | 
#| |\/| | | | |/ _` |  ___/ |
#| |  | | |_| | (_| | |   | |
#|_|  |_|\__,_|\__,_|_|   |_|

CONFIGS = {}
PROGRAM_RUNNING = True
print('Loading MudPi Configs...\r', end="", flush=True)
#load the configuration
CONFIGS = loadConfigJson(CONFIGS)
print('Loading MudPi Configs...\t\033[1;32m Complete\033[0;0m')
time.sleep(5) #Waiting for redis and services to be running

#Clear the console if its open for debuggin                             
print(chr(27) + "[2J")
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
print('Version: ', CONFIGS['version'])
print('\033[0;0m')
if CONFIGS['debug'] is True:
	print('\033[1;33mDEBUG MODE ENABLED\033[0;0m')
time.sleep(1)


if CONFIGS['debug'] is True:
	print("Loaded Config\n--------------------")
	for index, config in CONFIGS.items():
		if config != '':
			print('%s: %s' % (index, config))
	#for debugging
	desired_runtime = int(input('\033[1;32m|DEBUG MODE|\033[0;0m Server Runtime (seconds): '))
else:
	desired_runtime = 60

try:
	print('Initializing Garden Control \r', end="", flush=True)
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	GPIO.cleanup()

	time.sleep(0.1)
	print('Initializing Garden Control...\t\t\033[1;32m Complete\033[0;0m')

	print('Preparing Threads for Workers\r', end="", flush=True)

	threads = []
	variables.lcd_message = {'line_1': 'Mudpi Control', 'line_2': 'Is Now Running'}

	new_messages_waiting = threading.Event() #Event to signal LCD to pull new messages
	main_thread_running = threading.Event() #Event to signal workers to close
	system_ready = threading.Event() #Event to tell workers to begin working
	pump_ready = threading.Event() #Event to determine if pump can be turned on
	pump_should_be_running = threading.Event() #Event to tell pump to water cycle
	main_thread_running.set() #Main event to tell workers to run/shutdown

	time.sleep(0.1)
	print('Preparing Threads for Workers...\t\033[1;32m Complete\033[0;0m')

	l = LCDWorker(new_messages_waiting,main_thread_running,system_ready)
	print('Loading LCD Worker')
	l = l.run()
	threads.append(l)

	p = PumpWorker(CONFIGS['pump'], main_thread_running, system_ready, pump_ready, pump_should_be_running)
	print('Loading Pump Worker')
	p = p.run()
	threads.append(p)

	ps = PiSensorWorker(CONFIGS['sensors'], main_thread_running, system_ready, pump_ready)
	print('Loading Pi Sensor Worker')
	ps = ps.run()
	threads.append(ps)

	#t = threading.Thread(target=temp_worker, args=(new_messages_waiting,main_thread_running,system_ready))
	try:
		for node in CONFIGS['nodes']:
			#Create sensor worker for node
			t = SensorWorker(node, main_thread_running, system_ready)
			t = t.run()
			if t is not None:
				threads.append(t)
	except KeyError:
		print('No Nodes Found to Load')


	#Didnt build server worker (this is replaced with nodejs)
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
	variables.r.set('started_at', datetime.datetime.now()) #Store current time to track uptime

	#time.sleep(10)
	#new_messages_waiting.set()
	#pump_ready.set()
	#time.sleep(desired_runtime)

	#Hold the program here until its time to graceful shutdown
	#This is our pump cycle check, Using redis to determine if pump should activate
	while PROGRAM_RUNNING:
		pump_status = variables.r.get('pump_should_be_running')
		if pump_status and not pump_should_be_running.is_set():
			pump_should_be_running.set()
			variables.r.delete('pump_should_be_running')
		if pump_should_be_running.is_set():
			pump_override = variables.r.get('pump_shuttoff_override')
			if pump_override:
				pump_should_be_running.clear()
				variables.r.delete('pump_shuttoff_override')
				message = {'event':'PumpOverrideOff', 'data':1}
				variables.r.publish('pump', json.dumps(message))
		time.sleep(5)

except KeyboardInterrupt:
	PROGRAM_RUNNING = False
finally:
	print('MudPi Shutting Down...')
	#load a client on the server to clear it from waiting
	# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#sock.connect((CONFIGS['SERVER_HOST'], int(CONFIGS['SERVER_PORT'])))
	main_thread_running.clear()
	server.sock.shutdown(socket.SHUT_RDWR)
	# time.sleep(1)
	# sock.close()

	try:
		if t is not None:
			t.join()
	except NameError:
		pass
	l.join()
	s.join()
	p.join()
	ps.join()
	print("MudPi Shutting Down...\t\t\t\033[1;32m Complete\033[0;0m")
	print("Mudpi is Now...\t\t\t\t\033[1;31m Offline\033[0;0m")
	