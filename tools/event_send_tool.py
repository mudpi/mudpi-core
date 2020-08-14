import redis
import threading
import json
import time

def timedMessage(message, delay=3):
	for s in range(1,delay):
		remainingTime = delay - s
		print(message + '...{0}s \r'.format(remainingTime), end="", flush=True)
		time.sleep(s)

if __name__ == "__main__": 
	try:
		option = True
		message = {}
		r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
		publisher = r
		topic = None
		while option != 0:
			#Clear the screen command
			print(chr(27) + "[2J")
			print('--------- Redis MudPi ---------')
			print('|3. Test Event                |')
			print('|2. Toggle                    |')
			print('|1. Switch                    |')
			print('|0. Shutdown                  |')
			print('-------------------------------')
			try:
				option = int(input('Enter Option: '))
			except:
				#Catch string input error
				option = 9
			if option != 0:
				if option == 1:
					try:
						new_state = int(input('Enter State to switch to (0 or 1): '))
						if new_state != 0 and new_state != 1:
							new_state = 0
					except:
						new_state = 0
					message = {
						'event': 'Switch',
						'data': new_state
					}
				elif option == 2:
					message = {
						'event': 'Toggle',
						'data': None
					}
				elif option == 3:
					message = {
						'event': "StateChanged",
						'data': "/home/pi/Desktop/mudpi/img/mudpi-0039-2019-04-14-02-21.jpg",
						'source': "camera_1"
					}
					topic = 'garden/pi/camera'
				else:
					timedMessage('Option not recognized')
					print(chr(27) + "[2J")
					continue

				if topic is None:
					topic = str(input('Enter Topic to Broadcast: '))

				if topic is not None and topic != '':
					#Publish the message
					publisher.publish(topic, json.dumps(message))
					print(message)
					timedMessage('Message Successfully Published!')
				else:
					timedMessage('Topic Input Invalid')
					time.sleep(2)

		print('Exit')
	except KeyboardInterrupt:
		#Kill The Server
		#r.publish('test', json.dumps({'EXIT':True}))
		print('Publish Program Terminated...')
	finally:
		pass
	
