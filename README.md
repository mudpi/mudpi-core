<img alt="MudPi Smart Garden" title="MudPi Smart Garden" src="http://ericdavisson.com/img/mudpi/mudPI_LOGO_small_flat.png" width="200px">

# MudPi Smart Garden
> Configurable smart garden system for your raspberry pi garden project.  

MudPi is a configurable smart garden system that runs on a raspberry pi written in python with no coding required to get started. MudPi is compatible with a variety of sensors on both the raspberry pi and Arduino allowing you create both simple and complex setups. Connect your sensors, edit the configuration file, and your all set!

## Getting Started
To get started, download the MudPi repository from GitHub, edit your configuration file and run the main MudPi script. Make sure to install the prerequisites below if you have not already.

### Prerequisites
There are a few libraries that need to be installed for a minimal setup. However, if you want to take advantage of all the features of MudPi you will need:

**Minimal Requirements**
* Raspberry Pi 
	* Raspbian GNU/Linux 9 [stretch] (or similar distribution) 
* Python 3.5 
	- (3.4 Included with Raspbian)
* RPi.GPIO 0.6.3 
	* (Comes with Raspbian)
* Redis 3.2* (Redis to store values and Pub/Sub)
	* [Install Redis on your Raspberry Pi](https://habilisbest.com/install-redis-on-your-raspberrypi)
		
```bash
pip install RPi.GPIO
pip install redis
```

**Additional Requirements**
* Arduino Nano / Arduino UNO
* Nanpy 0.9.6* (Allows control over Arduino from raspberry pi)
	
```bash
pip install nanpy
```

### Installing
Once you have met the prerequisites above you are ready to install MudPi which only takes a few minutes to get up and running.

Clone MudPi repository from GitHub into a folder of your choice.

```bash
cd path/to/install/mudpi
git clone https://github.com/olixr/mudpi.git
```

Edit the **mudpi.config** file located in the root of the MudPi installation. It uses a JSON object for the formatting. An example configuration file is included by default like the one below.

```json
{
    "name": "MudPi",
    "version": 0.5,
    "debug": false,
    "server": {
        "host": "127.0.0.1",
        "port": 6602
    },
    "redis": {
        "host": "127.0.0.1",
        "port": 6379
    },
    "pump": {
        "pin": 13,
        "max_duration":30
    },
    "sensors": [
        {
            "type":"Float",
            "pin": 19,
            "name":"Water Tank Low",
            "percent":5
        }
    ]
}

```

Editing the configuration file can be a pain. So I made a tool to create a file for you that you can copy paste for ease. [Eric Davisson](http://ericdavisson.com/)

### Running MudPi
Run `mudpi.py` script from the root folder of your mudpi installation. 
```bash
cd your/path/to/mudpi
python3 mudpi.py
```

#### Keep MudPi Running With Supervisord
Using a task monitor like supervisord is excellent to keep MudPi running in the background and only is a `pip install supervisor` away. This is what I do personally. Here is a example config file for supervisord once you get that installed. Change the paths and log files names as you need.
```
[program:mudpi]
directory=/var/www/mudpi
command=python3 -u /var/www/mudpi/mudpi.py
autostart=true
autorestart=true
stderr_logfile=/var/www/mudpi/logs/mudpi.err.log
stdout_logfile=/var/www/mudpi/logs/mudpi.out.log
```


## Configuring MudPi
MudPi loads everything it needs from a JSON formatted file in the root installation folder named `mudpi.config`. You can use my free configuration tool to create your file as well because I like making your life better. [Eric Davisson](http://ericdavisson.com/)

If you plan to edit the config file manually or want know more about it, below you can find details about each of the configuration options available.

* **name** [String]
	* Name of the system. Not used in the core, mainly here in case you wanted to pull for a UI.

* **version** 
	* Version of your system. Not used yet, might be useful for legacy.

* **debug** [Boolean]
	* If enabled, MudPi will output more information while the system runs. More information about the startup and cycles will be output.

* **server** [Object]
	* Configuration for the MudPi socketio server. _Currently not used_
		* **host** [String]
			* IP address of server
		* **port** [Integer]
			* Port to run server on

* **redis** [Object]
	* Configuration of redis server to store sensor reads and utilize Pub/Sub
		* **host** [String]
			* IP address of redis server
		* **port** [Integer]
			* Port of redis server

* **pump** [Object]
	* Configuration for relay that runs pump.
		* **pin** [Integer]
			* GPIO pin number the relay is hooked up to on the raspberry pi
		* **max_duration** [Integer]
			* Maximum runtime that the relay should be switched on in seconds
	
* **sensors** [Array]
	* An array of objects containing configuration for sensors attached to the raspberry pi. 
	* **sensor** [Object]
		* Configuration for a sensor attached to raspberry pi
			* **type** [String]
				* Type of sensor. Options: `Float`, `Humidity`
			* **pin** [Integer]
				* GPIO pin number on raspberry pi the sensor is connected to
			* **name** [String]
				* Name of the sensor. The name will be used as key to store in redis if a key is not specified. 
			* **key** [String] (Optional)
				* Key to store value under in redis. Alphanumeric with underscores only. Must be valid redis key. _If a key is not provided it will use the name converted to lowercase and spaces replaced with underscores._
			* **percent** [Integer] (Float Type Only)
				* For float sensors this value specifies the percent filled the container is. Useful for UI, not critical to core. 
			* **critical** [Boolean] (Float Type Only)
				* For float sensors this value specifies if the liquid level is critical to pump function. **If critical is set to true and the float sensor reads false, the relay will not turn on.** 

* **nodes** [Array]
	* An array of objects containing configuration for arduinos attached to the raspberry pi.
	* **name** [String]
		* Name of Arduino	 connected to pi. Not important, only useful for UI or sorting sensor reads in the future. 
	* **address** [String]
		* TTY Serial address of Arduino connected to the raspberry pi over USB.
	* **sensors** [Array]
		* An array of objects containing configuration options for sensors connected to the node (Arduino). Run `ls /dev` in your raspberry pi terminal to list devices connected. Typically this value is one of `/dev/AMA0`, `/dev/ttyUSB0`, or `/dev/ttyUSB1`.
		* **sensor** [Object]
			* Configuration for a sensor attached to an Arduino
				* **type** [String]
					* Type of sensor. Options: `Temperature`, `Humidity`, `Soil`, `Rain`, `Light`, `Float`
				* **pin** [Integer]
					* GPIO pin number on the Arduino the sensor is connected to
				* **name** [String]
					* Name of the sensor. The name will be used as key to store in redis if a key is not specified. 
				* **key** [String] (Optional)
					* Key to store value under in redis. Alphanumeric with underscores only. Must be valid redis key. _If a key is not provided it will use the name converted to lowercase and spaces replaced with underscores._

Here is a more complex example configuration file with an Arduino connected to USB 0
```json
{
    "name": "MudPi",
    "version": 0.5,
    "debug": false,
    "server": {
        "host": "127.0.0.1",
        "port": 6602
    },
    "redis": {
        "host": "127.0.0.1",
        "port": 6379
    },
    "pump": {
        "pin": 13,
        "max_duration":900
    },
    "nodes": [
        {
            "name": "Outside Garden Box",
            "address": "/dev/ttyUSB0",
            "sensors": [
                {
                    "pin": "3",
                    "type": "Humidity",
                    "name": "Weather Station"
                }
            ]
        }
    ],
    "sensors": [
		  {
            "type":"Float",
            "pin": 20,
            "name":"Water Tank Full",
            "percent":100
        },
        {
            "type":"Float",
            "pin": 19,
            "name":"Water Tank Low",
            "percent":5,
	    "critical":true
        }
    ]
}

```

## Sensors
There are a number of sensors supported by default with MudPi for both the raspberry pi and arduino. Here are the options for adding the sensor to your system. You can read about the formatting in the configuration file above for adding the sensor.

### Pi Sensors
* Liquid Float Level Switch
	* 0 or 1 digital read of liquid level.
	* **type:** Float
	* _Returns:_ [Boolean] 0 or 1
* Humidity Temperature Sensor (DHT)
	* Take a digital read of humidity and temperature.
	* **type:** Humidity
	* _Returns:_ [Object] {humidity: float, temperature: float}

### Arduino Sensors
* Soil Moisture
	* Takes an analog reading of water content in soil.
	* **type:** Soil
	* _Returns:_ [Integer] Resistance
* Liquid Float Level Switch
	* 0 or 1 digital read of liquid level.
	* **type:** Float
	* _Returns:_ [Boolean] 0 or 1
* Humidity Temperature Sensor (DHT)
	* Take a digital read of humidity and temperature.
	* **type:** Humidity
	* _Returns:_ [Object] {humidity: float, temperature: float}
* Rain Sensor
	* Takes an analog reading of moisture/rain.
	* **type:** Rain
	* _Returns:_ [Integer] Resistance
* Temperature Sensor (Onewire)
	* Takes a digital reading of temperature using onewire bus.
	* **type:** Temperature
	* _Returns:_ [Object] {temp_0: float, temp_1: float, ...}
* Light Intesity Sensor (Not Fully Complete)
	* **type:** Light

## Redis
We chose redis to store our values quickly and to utilize its Pub/Sub capabilities since it was able to work across multiple languages Python, PHP, and Javascript in our case). If you don't have redis installed here is a great guide I used: [Install Redis on your Raspberry Pi](https://habilisbest.com/install-redis-on-your-raspberrypi)

### Storing Values
MudPi will store your values in redis for you using the name you specified for the sensor in the `mudpi.config` file. Note the name will be slugged (converted to lowercase and spaces replaced with underscores) and used as the key if you do not specifically provide one.

So for example a sensor config of:
```
{
	"pin": "3",
	"type": "Humidity",
	"name": "Weather Station"
}
```
Would store the reading in redis with a key of `weather_station`.

If you wanted to specify a key of your own, you can do so in the sensor config with the `key` option. Keep in mind this must be a [valid redis key](https://redis.io/topics/data-types-intro) which can be just about anything. However, try to keep this simple but descriptive for your own sake. 

```
{
	"pin": "3",
	"type": "Humidity",
	"name": "Weather Station",
	"key": "your_own_key"
}
```

### Key Values Stored in Redis
Other than the sensor readings, there are a few other important values MudPi stores into redis for you. These value are listed below with more information. 

_**Note on keys**: storing False in redis can be cast as a string which will read truthy in python. Instead we del the key and only store the key if its True_

#### Main Values
* **started_at** [Timestamp]
	* Timestamp of when MudPi started running. Useful to check uptime.
	
#### Pump Values
* **last_watered_at** [Timestamp]
	* Timestamp of when the last water cycle occured. Useful to check watering frequency. 
* **pump_should_be_running** [Booloean]
	* True or nil(key shouldn't exist) value to tell pump worker if it should start a watering cycle. 
* **pump_shuttoff_override** [Booloean]
	* True or nil(key shouldn't exist) value to tell pump worker to immediatly terminate any active water cycle.
	* _Key gets automatically deleted once its read by MudPi_
* **pump_running** [Booloean]
	* True or nil value set by MudPi to inform you if the water cycle in the pump worker is active or not.
	

### Redis Events
In addition to storing values in redis, MudPi also will publish events when the sensors are read or during pump cycle changes. Each event will return a JSON payload with an `event: ExampleEvent` and its `data:'Hello World'`. Below are the events MudPi sends out along with the channel they emit on.

#### Pump Events
**channel:** pump

##### Pump Turned On
```
{
	"event": "PumpTurnedOff",
	"data": 1
}
```

##### Pump Turned Off
```
{
	"event": "PumpTurnedOn",
	"data": 1
}
```

##### Pump Override Off
```
{
	"event": "PumpOverrideOff",
	"data": 1
}
```

#### Pi Sensor Events
**channel:** pi-sensors

##### Sensor Update
Data will be an object of all your sensor readings. 
```
{
	"event": "PiSensorUpdate",
	"data": {...}
}
```

#### Arduino Sensor Events
**channel:** sensors

##### Sensor Update
Data will be an object of all your sensor readings. 
```
{
	"event": "SensorUpdate",
	"data": {...}
}
```


## How It Works
Here is a diagram of the core architecture for MudPi and how it works:

![alt text](http://ericdavisson.com/img/Mudpi-architecture.png)

MudPi consists of multiple workers that are each responsible for a certain set of actions. Currently there are 3 workers included in MudPi, they are as follows:

**Pump Worker**
Responsible for checking if the relay should be on that controls the pump

**Pi Sensor Worker**
Runs any sensors attached to the raspberry pi and stores their readings to rediscover every 5 seconds by default.

**Node Sensor Worker**
Controls any Arduino(s) attached to the raspberry pi over serial connection and stores sensor readings attached to the Aquino GPIO every 15 seconds by default. 

MudPi takes advantage of multi threading to prevent blocking sensor reads or long processing cycles. Each worker will run on its own thread and uses threading events to communicate internally. This is why redis is used to utilize its Pub/Sub capabilities for externally interacting with threads such as telling the system to turn on the relay to power the pump.  

The Raspberry Pi does not have analog GPIO which can be useful in more complex setups to hook up additional sensors that use analog connections.  In order to get analog GPIO we use arduinos connect to the raspberry pi over usb to serial. 

To control the arduinos we wanted a master/slave system where one raspberry pi could control one or more arduinos if it needed to. I found there already was this [great library called Nanpy](https://github.com/nanpy/nanpy) which does just that. Each node sensor worker described above uses Nanpy to connect over serial and issue and analog or digital read.

Redis is used to store sensor read values in memory and communicate using its Pub_Sub capabilities. Each time a sensor or node worker runs a cycle it events an event over redis with a JSON payload containing the read values. You can easily make a script to log the values periodically to a database_file or hook up to a GUI to monitor it. Even better convert the events to socketio for live monitoring. 



## Debugging
I included two folders `tests` and `debug` for helping make sure things are working correctly. They include a few checks for sensor reads, communication between devices and GPIO tests. 

Simply cd into the folder and run the script using python3
```
cd path/to/mudpi/debug
python3 blink.py
```

### Caveats
While I was creating MudPi there was a ton of debugging along the way. I experienced a bunch of odd behavior that ranged from bugs in code, weird things due to small electronics, and still unknowns (aka leaving solder flux on connections...). 

Here are a few things I ran into:
* When using DHT11 temperature sensor on an Arduino it would connect and read correctly on the first script run for as long as the script ran for. However on the second run the sensor/device would timeout and never work unless I rebooted. 
* Temperature one wire probes tested and read fine on their own but as soon as they were loaded with other sensors they would always return bad readings.
* Rain sensors are a bit difficult to get accurate time ranges of rain because moisture and corrosion on the sensor cause elongated moisture readings. I had to typically wipe them off once or twice a week.
* Flux and small electronics can have leak voltage quite easily if your not super clean with your hardware work which can interfere with readings.
* Reading False from redis in python can be cast as a string by default which is truthy and caused a long confusing bug. Instead of storing false we just removed the key from redis using a `del` command and check for it the keys existance in MudPi.


## Contributing
This was a side project for me to scratch my own itch at home. Any contributions you can make will be greatly appreciated. This is one of the first projects I am able to share publicly and I hope if comes of great use to other looking to build something similar.


## Versioning
Breaking.Major.Minor


## Authors
* Eric Davisson  - [Website](http://ericdavisson.com)
* Twitter.com/theDavisson


## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details


## Acknowledgments
* Nanpy
	* This library made the Arduino side of this project possible allowing me to setup a master/slave system of raspberry pi and Arduinos. 
* Shoutout to my buddy who helped me with some of the AC to DC electrical stuff.
	

## Why Did You Build This?
Gardening at home was taking more time that I would like and buying a simple timer for the hose was not something I really wanted as a solution. I wanted to build my own automated garden with my raspberry pi I had lying around. I do a good deal of web development during the day so the software aspect wasn’t an issue but I hadn’t touched electronics for years since high school so this was a good refresher. **You can read how I built MudPi and the process of me setting it up at home on the MudPi blog**


## Tested On
These are the devices and sensors I tested and used with MudPi successfully. Many sensors are similar so it will work with a range more than what is listed below. 

* [Raspberry Pi 2 Model B+](https://www.raspberrypi.org/products/raspberry-pi-2-model-b/)
* [Arduino Nano (ELEGOO offbrand)](https://www.amazon.com/ELEGOO-Arduino-ATmega328P-without-compatible/dp/B0713XK923)
* [Arduino Uno](https://store.arduino.cc/usa/arduino-uno-rev3)
* [Horizontal Liquid Float Switch](https://www.amazon.com/gp/product/B01HLPGJUQ/ref=oh_aui_detailpage_o07_s00?ie=UTF8&psc=1)
* [4 Channel DC 5V Relay](https://www.amazon.com/gp/product/B00KTEN3TM/ref=oh_aui_detailpage_o08_s00?ie=UTF8&psc=1)
* [DS18B20 Temperature Sensors](https://www.amazon.com/gp/product/B018KFX5X0/ref=oh_aui_detailpage_o08_s00?ie=UTF8&psc=1)
* [DHT11 Temperature/Humidity Sensor](https://www.amazon.com/gp/product/B01DKC2GQ0/ref=oh_aui_detailpage_o07_s05?ie=UTF8&psc=1)
* [Rain Sensor](https://www.amazon.com/gp/product/B01D9JK2F6/ref=oh_aui_detailpage_o03_s00?ie=UTF8&psc=1)
* [DFROBOT Analog Capacitive Soil Moisture Sensor](https://www.amazon.com/gp/product/B01GHY0N4K/ref=oh_aui_detailpage_o01_s00?ie=UTF8&psc=1)
* [USB to TTL USB 2.0 Serial Module UART](https://www.amazon.com/gp/product/B07CWKHTLH/ref=oh_aui_detailpage_o04_s00?ie=UTF8&psc=1)

If you have a sensor MudPi is not working with or you want to add more configuration options please submit a pull request and help a single developer out :)


## What’s Next?
There are still some items remaining for MudPi that I would like to complete. I am aiming for more sensor support and working on other methods of communication like wifi and I2C. There are tweaks to the configuration and existing modules that still need to be completed for better error handling and allowing better customization. Additionally there are a few more features left to complete like solenoids for zoned watering, or a flow meter for accurate water usage. 

**Todos**
- [ ] Pi Onewire Temperature Sensor Script (Dallas Temperature)
- [ ] Solenoid and Zone Control Scripts
- [ ] Flowmeter Script
- [ ] More configuration control (i.e. custom redis keys for pump checks)
- [ ] Retry and Restart System After Serial Timeout During Prolonged Use
- [ ] Camera Feature (Pi)
- [ ] Finish LCD Screen Support

**Maybes**
- [ ] Light Sensors ?
- [ ] Hardware controls (i.e. buttons)


<img alt="MudPi Smart Garden" title="MudPi Smart Garden" src="http://ericdavisson.com/img/mudpi/mudPI_LOGO_small_flat.png" width="50px">
