import socket
import sys
import threading
import pickle

# A socket server prototype that was going to be used for devices to communicate.
# Instead we are using nodejs to catch events in redis and emit them over a socket.
# May update this in later version for device communications. Undetermined.

class MudpiServer(object):

	def __init__(self, system_running, host='127.0.0.1', port=6601):
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
		self.sock.listen(10) #number of clients to listen for
		print('MudPi Server...\t\t\t\t\033[1;32m Running\033[0;0m ')
		while self.system_running.is_set():
			try:
				client, address = self.sock.accept()
				client.settimeout(60)
				print('Client connected from ', address)
				t = threading.Thread(target = self.listenToClient, args = (client, address))
				self.client_threads.append(t)
				t.start()
			except:
				pass
		print('Server Shutdown...\r', end="", flush=True)
		self.sock.close()
		print('Server Shutdown...\t\t\t\033[1;32m Complete\033[0;0m')

	def listenToClient(self, client, address):
		size = 1024
		while self.system_running.is_set():
			try:
				data = pickle.loads(client.recv(size))
				if data:
					print(data)
					response = data
					client.send(pickle.dumps(data))
				else:
					raise error('Client Disconnected')
			except:
				client.close()
				return false
		print('Closing Client Connection...\t\t\033[1;32m Complete\033[0;0m')

if __name__ == "__main__":
	host = '127.0.0.1'
	port = 6002
	server = MudpiServer(host, port)
	server.listen();
	while True:
		pass