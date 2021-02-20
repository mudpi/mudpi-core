import json
import time
import random
import paho.mqtt.client as mqtt

from . import Adaptor


class MQTTAdaptor(Adaptor):
    key = 'mqtt'

    connected = False
    loop_started = False
    callbacks = {}

    def connect(self):
        """ Make mqtt connection and setup broker """

        def on_conn(client, userdata, flags, rc):
            if rc == 0:
                self.connected = True

        host = self.config.get('host', "localhost")
        # port = self.config.get('port', 1883)
        # TODO: Add authentication support
        self.connection = mqtt.Client(f'mudpi-{random.randint(0, 100)}')
        self.connection.on_connect = on_conn
        self.connection.connect(host)
        while not self.connected:
            self.get_message()
            time.sleep(0.1)
        return True

    def disconnect(self):
        """ Close active connections and cleanup subscribers """
        self.connection.loop_stop()
        self.connection.disconnect()
        return True

    def subscribe(self, topic, callback):
        """ Listen on a topic and pass event data to callback """
        if topic not in self.callbacks:
            self.callbacks[topic] = [callback]
        else:
            if callback not in self.callbacks[topic]:
                self.callbacks[topic]

        def callback_handler(client, userdata, message):
            # log = f"{message.payload.decode()} {message.topic}"
            if message.topic in self.callbacks:
                for callbk in self.callbacks[message.topic]:
                    callbk(message.payload)

        self.connection.on_message = callback_handler
        return self.connection.subscribe(topic)

    def unsubscribe(self, topic):
        """ Stop listening for events on a topic """
        del self.callbacks[topic]
        return self.connection.unsubscribe(topic)

    def publish(self, topic, data=None):
        """ Publish an event on the topic """
        if data:
            return self.connection.publish(topic, json.dumps(data))

        return self.connection.publish(topic)

    def get_message(self):
        """ Check for new messages waiting """
        if not self.loop_started:
            self.connection.loop_start()
            self.loop_started = True