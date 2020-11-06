import redis
import threading
import json
import time

def timed_message(message, delay=3):
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
			print('---------  LCD MudPi  ---------')
			print('|4. Clear Message Queue       |')
			print('|3. Clear Display             |')
			print('|2. Test Message              |')
			print('|1. Add Message               |')
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
						msg = {
							"message":"",
							"duration":10
						}
						msg["message"] = str(input('Enter Message to Display: '))
						msg["duration"] = int(input('Enter Duration to Display (seconds): '))
						
					except:
						msg = {
							"message":"Error Test",
							"duration":10
						}
					message = {
						'event': 'Message',
						'data': msg
					}
				elif option == 2:
					msg = {
						"message":"Test Message\nMudPi Test",
						"duration":15
					}
					message = {
						'event': 'Message',
						'data': msg
					}
				elif option == 3:
					message = {
						'event': 'Clear',
						'data': 1
					}
				elif option == 4:
					message = {
						'event': 'ClearQueue',
						'data': 1
					}
				else:
					timed_message('Option not recognized')
					print(chr(27) + "[2J")
					continue

				if topic is None:
					topic = str(input('Enter the LCD Topic to Broadcast: '))

				if topic is not None and topic != '':
					#Publish the message
					publisher.publish(topic, json.dumps(message))
					print(message)
					timed_message('Message Successfully Queued!')
				else:
					timed_message('Topic Input Invalid')
					time.sleep(2)

		print('Exit')
	except KeyboardInterrupt:
		#Kill The Server
		#r.publish('test', json.dumps({'EXIT':True}))
		print('LCD Message Program Terminated...')
	finally:
		pass
	
