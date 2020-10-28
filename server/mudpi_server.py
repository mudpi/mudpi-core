import socket
import sys
import threading
import json
import time
import redis

from logger.Logger import Logger, LOG_LEVEL

# A socket server used to allow incoming wiresless connections. 
# MudPi will listen on the socket server for clients to join and
# send a message that should be broadcast on the event system.

class MudpiServer(object):

	def __init__(self, config, system_running):
		self.port = int(config.get("port", 7007))
		self.host = config.get("host", "127.0.0.1")
		self.system_running = system_running
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client_threads = []


		try:
			self.sock.bind((self.host, self.port))
		except socket.error as msg:
			Logger.log(LOG_LEVEL['error'], 'Failed to create socket. Error Code: ', str(msg[0]), ' , Error Message: ', msg[1])
			sys.exit()

		# PubSub
		try:
			self.r = config["redis"]
		except KeyError:
			self.r = redis.Redis(host='127.0.0.1', port=6379)

	def listen(self):
		self.sock.listen(0) # number of clients to listen for.
		Logger.log(LOG_LEVEL['info'], 'MudPi Server...\t\t\t\t\033[1;32m Online\033[0;0m ')
		while self.system_running.is_set():
			try:
				client, address = self.sock.accept()
				client.settimeout(600)
				ip, port = client.getpeername()
				Logger.log(LOG_LEVEL['info'], 'Socket \033[1;32mClient {0}\033[0;0m from \033[1;32m{1} Connected\033[0;0m'.format(port, ip))
				t = threading.Thread(target = self.listenToClient, args = (client, address, ip))
				self.client_threads.append(t)
				t.start()
			except Exception as e:
				Logger.log(LOG_LEVEL['error'], e)
				time.sleep(1)
				pass
		self.sock.close()
		if len(self.client_threads > 0):
			for client in self.client_threads:
				client.join()
		Logger.log(LOG_LEVEL['info'], 'Server Shutdown...\t\t\t\033[1;32m Complete\033[0;0m')

	def listenToClient(self, client, address, ip):
		size = 1024
		while self.system_running.is_set():
			try:
				data = client.recv(size)
				if data:
					data = self.decodeMessageData(data)
					if data.get("topic", None) is not None:
						self.r.publish(data["topic"], json.dumps(data))
						Logger.log(LOG_LEVEL['info'], "Socket Event \033[1;36m{event}\033[0;0m from \033[1;36m{source}\033[0;0m Dispatched".format(**data))

						# response = {
						# 	"status": "OK",
						# 	"code": 200
						# }
						# client.send(json.dumps(response).encode('utf-8'))
					else:
						Logger.log(LOG_LEVEL['error'], "Socket Data Recieved. \033[1;31mDispatch Failed:\033[0;0m Missing Data 'Topic'")
						Logger.log(LOG_LEVEL['debug'], data)
				else:
					pass
					# raise error('Client Disconnected')
			except Exception as e:
				Logger.log(LOG_LEVEL['info'], "Socket Client \033[1;31m{0} Disconnected\033[0;0m".format(ip))
				client.close()
				return False
		Logger.log(LOG_LEVEL['info'], 'Closing Client Connection...\t\t\033[1;32m Complete\033[0;0m')

	def decodeMessageData(self, message):
		if isinstance(message, dict):
			return message # print('Dict Found')
		elif isinstance(message.decode('utf-8'), str):
			try:
				temp = json.loads(message.decode('utf-8'))
				return temp # print('Json Found')
			except:
				return {'event':'Unknown', 'data':message.decode('utf-8')} # print('Json Error. Str Found')
		else:
			return {'event':'Unknown', 'data':message} # print('Failed to detect type')

if __name__ == "__main__":
	config = {
		"host": '',
		"port": 7007
	}
	system_ready = threading.Event()
	system_ready.set()
	server = MudpiServer(config, system_ready)
	server.listen();
	try:
		while system_ready.is_set():
			time.sleep(1)
	except KeyboardInterrupt:
		system_ready.clear()
	finally:
		system_ready.clear()