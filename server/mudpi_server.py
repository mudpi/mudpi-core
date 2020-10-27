import socket
import sys
import threading
import json
import time

# from logger.Logger import Logger, LOG_LEVEL

# A socket server prototype that was going to be used for devices to communicate.
# Instead we are using nodejs to catch events in redis and emit them over a socket.
# May update this in later version for device communications. Undetermined.

class MudpiServer(object):

	def __init__(self, system_running, host='127.0.0.1', port=7007):
		self.port = int(port)
		self.host = host
		self.system_running = system_running
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_threads = []

		try:
			self.sock.bind((self.host, self.port))
		except socket.error as msg:
			print('Failed to create socket. Error Code: ', str(msg[0]), ' , Error Message: ', msg[1])
			sys.exit()

	def listen(self):
		self.sock.listen(0) # number of clients to listen for.
		print('MudPi Server...\t\t\t\t\033[1;32m Online\033[0;0m ')
		while self.system_running.is_set():
			try:
				client, address = self.sock.accept()
				client.settimeout(60)
				print('Client connected from ', address)
				t = threading.Thread(target = self.listenToClient, args = (client, address))
				self.client_threads.append(t)
				t.start()
			except:
				time.sleep(1)
				pass
		self.sock.close()
		if len(self.client_threads > 0):
			for client in self.client_threads:
				client.join()
		print('Server Shutdown...\t\t\t\033[1;32m Complete\033[0;0m')

	def listenToClient(self, client, address):
		size = 1024
		while self.system_running.is_set():
			try:
				data = client.recv(size)
				if data:
					data = self.decodeMessageData(data)
					print(data)
					response = {
						"status": "OK",
						"code": 200
					}
					client.send(json.dumps(response).encode('utf-8'))
				else:
					pass
					# raise error('Client Disconnected')
			except Exception as e:
				print(e)
				print("Client Disconnected")
				client.close()
				return False
		print('Closing Client Connection...\t\t\033[1;32m Complete\033[0;0m')

	def decodeMessageData(self, message):
		if isinstance(message, dict):
			return message # print('Dict Found')
		elif isinstance(message.decode('utf-8'), str):
			try:
				temp = json.loads(message.decode('utf-8'))
				return temp # print('Json Found')
			except:
				return {'event':'Unknown', 'data':message} # print('Json Error. Str Found')
		else:
			return {'event':'Unknown', 'data':message} # print('Failed to detect type')

if __name__ == "__main__":
	host = ''
	port = 7007
	system_ready = threading.Event()
	system_ready.set()
	server = MudpiServer(system_ready, host, port)
	server.listen();
	try:
		while system_ready.is_set():
			time.sleep(1)
	except KeyboardInterrupt:
		system_ready.clear()
	finally:
		system_ready.clear()