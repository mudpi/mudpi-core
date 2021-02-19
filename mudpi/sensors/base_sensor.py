import redis


class BaseSensor:

    def __init__(self, pin, name=None, key=None, redis_conn=None):
        self.pin = pin

        if key is None:
            raise Exception('No "key" Found in Sensor Config')
        else:
            self.key = key.replace(" ", "_").lower()

        if name is None:
            self.name = self.key.replace("_", " ").title()
        else:
            self.name = name

        try:
            self.r = redis_conn if redis_conn is not None else redis.Redis(
                host='127.0.0.1', port=6379)
        except KeyError:
            self.r = redis.Redis(host='127.0.0.1', port=6379)

    def init_sensor(self):
        pass

    def read(self):
        pass

    def read_raw(self):
        pass

    def read_pin(self):
        raise NotImplementedError
