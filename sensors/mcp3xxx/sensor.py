import adafruit_mcp3xxx.mcp3008 as MCP

# Base sensor class to extend all other mcp3xxx sensors from.
from sensors.base_sensor import BaseSensor


class Sensor(BaseSensor):
    PINS = {
        0: MCP.P0,
        1: MCP.P1,
        2: MCP.P2,
        3: MCP.P3,
        4: MCP.P4,
        5: MCP.P5,
        6: MCP.P6,
        7: MCP.P7,
    }

    def __init__(self, pin: int, mcp, name=None, key=None, redis_conn=None):
        super().__init__(
            pin=pin,
            name=name,
            key=key,
            redis_conn=redis_conn
        )
        self.mcp = mcp
        self.topic = None

    def read_raw(self):
        """
        Read the sensor(s) but return the raw voltage, useful for debugging

        Returns:

        """
        return self.topic.voltage

    def read_pin(self):
        """
        Read the pin from the mcp3xxx as unaltered digital value

        Returns:

        """
        return self.topic.value
