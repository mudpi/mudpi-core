import redis
import json

print('Add a Message to the Queue')

r = redis.Redis(host='127.0.0.1', port=6379)
line1 = str(input('Line 1 Text: '))
line2 = str(input('Line 2 Text: '))
old_messages = r.get('lcdmessages')
messages = []
if old_messages:
	messages = json.loads(old_messages.decode('utf-8'))
testmessage = {'line_1': line1, 'line_2': line2}

messages.append(testmessage)

r.set('lcdmessages', json.dumps(messages))

print('Value set in redis and in queue')