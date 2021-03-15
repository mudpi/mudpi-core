""" 
    MQTT Extension
    Includes interfaces for redis to
    get data from events.
"""
import time
import paho.mqtt.client as mqtt
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'mqtt'
    update_interval = 1

    def init(self, config):
        """ Prepare the mqtt connection and components """
        self.connections = {}
        self.loop_started = False
        
        self.config = config

        if not isinstance(config, list):
            config = [config]

        # Prepare clients for mqtt
        for conf in config:
            host = conf.get('host', 'localhost')
            port = conf.get('port', 1883)
            if conf['key'] not in self.connections:
                self.connections[conf['key']] = {'client': None, 
                    'connected': False, 
                    'loop_started': False,
                    'callbacks': {}}

                def on_conn(client, userdata, flags, rc):
                    if rc == 0:
                        self.connections[conf['key']]['connected'] = True

                self.connections[conf['key']]['client'] = mqtt.Client(f'mudpi-{conf["key"]}')
                self.connections[conf['key']]['client'].on_connect = on_conn
                self.connections[conf['key']]['client'].connect(host, port=port)

                while not self.connections[conf['key']]['connected']:
                    if not self.connections[conf['key']]['loop_started']:
                        self.connections[conf['key']]['client'].loop_start()
                        self.connections[conf['key']]['loop_started'] = True
                    time.sleep(0.1)

        return True

    def validate(self, config):
        """ Validate the mqtt connection info """
        config = config[self.namespace]
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            key = conf.get('key')
            if key is None:
                raise ConfigError('MQTT missing a `key` in config for connection')

            host = conf.get('host')
            if host is None:
                conf['host'] = 'localhost'

            port = conf.get('port')
            if port is None:
                conf['port'] = 1883
        return config

    def unload(self):
        """ Unload the extension """
        for conn in self.connections.values():
            conn['client'].loop_stop()
            conn['client'].disconnect()

    def subscribe(self, key, topic, callback):
        """ Listen on a topic and pass event data to callback """
        if topic not in self.connections[key]['callbacks']:
            self.connections[key]['callbacks'][topic] = [callback]
        else:
            if callback not in self.connections[key]['callbacks'][topic]:
                self.connections[key]['callbacks'][topic].append(callback)

        def callback_handler(client, userdata, message):
            # log = f"{message.payload.decode()} {message.topic}"
            if message.topic in self.connections[key]['callbacks']:
                for callbk in self.connections[key]['callbacks'][message.topic]:
                    callbk(message.payload.decode("utf-8"))

        self.connections[key]['client'].on_message = callback_handler
        return self.connections[key]['client'].subscribe(topic)