import redis
import threading
import redis_sub
import json
import time

if __name__ == "__main__": 
	try:
		r = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)
		client = redis_sub.Listener(r, [str(input('Enter Channel to Listen on: '))])
		client.start()
	except KeyboardInterrupt:
		#Kill The Server
		r.publish('test', json.dumps({'EXIT':True}))
	finally:
		pass
	
