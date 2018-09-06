<img alt="MudPi Smart Garden" title="MudPi Smart Garden" src="http://ericdavisson.com/img/mudpi/mudPI_LOGO_small_flat.png" width="200px">

# MudPi Smart Garden
> Configurable smart garden system for your raspberry pi garden project.  

MudPi is a configurable smart garden system that runs on a raspberry pi written in python with no coding required to get started. MudPi is compatible with a variety of sensors on both the raspberry pi and Arduino allowing you create both simple and complex setups. Connect your sensors, edit the configuration file, and your all set!

<img alt="MudPi Smart Garden" title="MudPi Smart Garden Demo" src="http://ericdavisson.com/img/mudpi/mud2.gif">

## Getting Started
To get started, [download](https://github.com/olixr/MudPi/archive/master.zip) the MudPi repository from GitHub, edit your `mudpi.config` configuration file and run the main MudPi script by executing `python3 mudpi.py` from the root of your MudPi installation. Make sure to install the prerequisites below if you have not already.

### Prerequisites
There are a few libraries that need to be installed for a minimal setup. However, if you want to take advantage of all the features of MudPi you will need to also install the additonal requirements. 

**Minimal Requirements**
* Raspberry Pi 
	* OS: [Raspbian GNU/Linux 9](https://www.raspberrypi.org/downloads/raspbian/) [stretch] (or similar distribution) 
* Python 3.4+ (Comes with Raspbian)
* RPi.GPIO 0.6.3 (Comes with Raspbian)
* Redis 3.2* (Redis to store values and Pub/Sub)
	* [Install Redis on your Raspberry Pi](https://habilisbest.com/install-redis-on-your-raspberrypi)
		
```bash
pip install RPi.GPIO
pip install redis
```

**Additional Requirements**
* Arduino Nano / Arduino UNO
	* Flashed with [Nanpy Firmware](https://github.com/nanpy/nanpy-firmware)
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
            "type":"Humidity",
            "pin": 25,
            "name":"Weather Station"
        }
    ]
}

```

Editing the configuration file can be a pain. So I made a [tool to create the config file for you](https://mudpi.app/config) that you can copy paste into your pi easier.

### Running MudPi
Run `mudpi.py` script from the root folder of your mudpi installation. 
```bash
cd your/path/to/mudpi
python3 mudpi.py
```

#### Keep MudPi Running With Supervisord
Using a task monitor like supervisord is excellent to keep MudPi running in the background and only is a `pip install supervisor` away. Using a tool like supervisor allows you to keep MudPi running in the event of errors or system restarts. This is what I do personally. Here is a example config file for supervisord once you get that installed. In my case this was located under `/etc/supervisor/conf.d/` on my raspberry pi. Change the paths and log files names as you need.
```
[program:mudpi]
directory=/var/www/mudpi
command=python3 -u /var/www/mudpi/mudpi.py
autostart=true
autorestart=true
stderr_logfile=/var/www/mudpi/logs/mudpi.err.log
stdout_logfile=/var/www/mudpi/logs/mudpi.out.log
```


### Basic Hardware Example
MudPi is built so you can add sensors and configure the system to your specific setup. You can review more info below under [the sensors section](#sensors) about all the sensor types available to you. 

Here is a basic hardware example to get started with a DHT11 Humidity sensor hooked up to the pi on GPIO pin 25. _This will work the the configuration file example listed above and included by default._

<img alt="MudPi Smart Garden" title="MudPi Smart Garden" src="http://ericdavisson.com/img/mudpi/mudpi-example-1.png" width="300px">



## Configuring MudPi
MudPi loads everything it needs from a JSON formatted file in the root installation folder named `mudpi.config`. You can use my free [configuration tool to create your file](https://mudpi.app/config) as well because I like making your life better.

If you plan to edit the config file manually or want know more about it, below you can find details about each of the configuration options available.

`name` _[String]_

Name of the system. Not used in the core, mainly here in case you wanted to pull for a UI.

`version` 

Version of your system. Not used yet, might be useful for legacy.

`debug` _[Boolean]_

If enabled, MudPi will output more information while the system runs. More information about the startup and cycles will be output.

`server` _[Object]_

Configuration for the MudPi socketio server. _Currently not used_
* `host` _[String]_
	* IP address of server
* `port` _[Integer]_
	* Port to run server on

`redis` _[Object]_

Configuration of redis server to store sensor reads and utilize Pub/Sub
* `host` _[String]_
	* IP address of redis server
* `port` _[Integer]_
	* Port of redis server

`pump` _[Object]_

Configuration for relay that runs pump.
* `pin` _[Integer]_
	* GPIO pin number the relay is hooked up to on the raspberry pi
* `max_duration` _[Integer]_
	* Maximum runtime that the relay should be switched on in seconds
	
`sensors` _[Array]_

An array of objects containing configuration for sensors attached to the raspberry pi. 
*  _[Object]_ (Object of options for sensor)
	* Configuration for a sensor attached to raspberry pi
		* `type` _[String]_
			* Type of sensor. Options: `Float`, `Humidity`
		* `pin` _[Integer]_
			* GPIO pin number on raspberry pi the sensor is connected to
		* `name` _[String]_
			* Name of the sensor. The name will be used as key to store in redis if a key is not specified. 
		* `key` _[String]_ (Optional)
			* Key to store value under in redis. Alphanumeric with underscores only. Must be valid redis key. _If a key is not provided it will use the name converted to lowercase and spaces replaced with underscores._
		* `percent` _[Integer]_ (Float Type Only)
			* For float sensors this value specifies the percent filled the container is. Useful for UI, not critical to core. 
		* `critical` _[Boolean]_ (Float Type Only)
			* For float sensors this value specifies if the liquid level is critical to pump function. **If critical is set to true and the float sensor reads false, the relay will not turn on.** 

`nodes` _[Array]_

An array of objects containing configuration for arduinos attached to the raspberry pi.
* `name` _[String]_
	* Name of Arduino connected to pi. Not important, only useful for UI or sorting sensor reads in the future. 
* `address` _[String]_
	* TTY Serial address of Arduino connected to the raspberry pi over USB.
* `sensors` _[Array]_
	* An array of objects containing configuration options for sensors connected to the node (Arduino). Run `ls /dev` in your raspberry pi terminal to list devices connected. Typically this value is one of `/dev/AMA0`, `/dev/ttyUSB0`, or `/dev/ttyUSB1`.
	* _[Object]_ (Object of options for sensor)
		* Configuration for a sensor attached to an Arduino
			* `type` _[String]_
				* Type of sensor. Options: `Temperature`, `Humidity`, `Soil`, `Rain`, `Light`, `Float`
			* `pin` _[Integer]_
				* GPIO pin number on the Arduino the sensor is connected to
			* `name` _[String]_
				* Name of the sensor. The name will be used as key to store in redis if a key is not specified. 
			* `key` _[String]_ (Optional)
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
                },
                {
                    "pin": "5",
                    "type": "Soil",
                    "name": "Soil Moisture",
		    "key": "garden_soil_moisture"
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
#### Liquid Float Level Switch
0 or 1 digital read of liquid level. If marked critical it will prevent pump from running until it returns 1 (true)
* **type:** `Float`
* **percent:** 0 - 100
* **critical:** true / false
* _Returns:_ [Boolean] 0 or 1
	
#### Humidity Temperature Sensor (DHT)
Take a digital read of humidity and temperature.
* **type:** `Humidity`
* _Returns:_ [Object] {humidity: float, temperature: float}

### Arduino Sensors
#### Soil Moisture
Takes an analog reading of water content in soil.
* **type:** `Soil`
* Pin Type: Analog
* _Returns:_ [Integer] Resistance

#### Liquid Float Level Switch
0 or 1 digital read of liquid level.
* **type:** `Float`
* Pin Type: Digital
* _Returns:_ [Boolean] 0 or 1

#### Humidity Temperature Sensor (DHT)
Take a digital read of humidity and temperature.
* **type:** `Humidity`
* Pin Type: Digital
* _Returns:_ [Object] {humidity: float, temperature: float}

#### Rain Sensor
Takes an analog reading of moisture/rain.
* **type:** `Rain`
* Pin Type: Analog
* _Returns:_ [Integer] Resistance

#### Temperature Sensor (Onewire)
Takes a digital reading of temperature using onewire bus.
* **type:** `Temperature`
* Pin Type: Digital
* _Returns:_ [Object] {temp_0: float, temp_1: float, ...}

#### Light Intesity Sensor (Not Fully Complete)
* **type:** `Light`



## Pump (Relay)
Hooking up a pump to MudPi is done using a relay to protect the raspberry pi from high voltages. Once you have you relay attached you can add the pump options to you configuration.

The pump has two options to configure, a `pin` and `max_duration`. The `pin` is the GPIO on the raspberry pi you hooked the relay up to. `max_duration` is the max runtime of the pump in seconds and determines how long the relay will be powered on for.
```
"pump": {
	"pin": "3",
	"max_duration": "60"
}
```
The example pump configruation above would turn the relay on hooked up through GPIO pin 3 for a maxium of 60 seconds. 

### Toggling the Pump
The pump worker will check redis periodically to see if it should begin a pump cycle. It does this by looking for the `pump_should_be_running` key and checking that it exists. The value can be anything, even false and the pump will still trigger as long as they key is present. Once the key is read and the pump begins a cycle, it will delete the key from redis. Removing this key on your own will not shutoff the current pump cycle, it will only prevent it from starting if it has not already and the key is still set.

In order to shutoff the pump before it has run for the specified `max_duration`, you must set the redis key `pump_shuttoff_override`. Again this key can hold any value, Mudpi only cares that the key exists. Once it detects the existance of this key it will immediatly shutdown the current pump cycle powering off the relay controlling the pump.

MudPi will inform you if the pump is currently running by setting the `pump_running` key. Altering this value will not change the pump state, this value is only set for your convience of checking the pumps current status. 



## Redis
We chose redis to store our values quickly and to utilize its Pub/Sub capabilities since it was able to work across multiple languages (Python, PHP, and Javascript in our case). If you don't have redis installed here is a great guide I used to [Install Redis on your Raspberry Pi](https://habilisbest.com/install-redis-on-your-raspberrypi)

### Storing Values
MudPi will store sensor values in redis for you using the `"name"` you specified for the sensor in the `mudpi.config` file. Note the `"name"` will be slugged (converted to lowercase and spaces replaced with underscores) and used in place of `"key"` if you do not specifically provide one.

So for example a sensor config of:
```
{
	"pin": "3",
	"type": "Humidity",
	"name": "Weather Station"
}
```
Would store the reading in redis with a key of `weather_station`.

If you wanted to specify a key of your own, you can do so in the sensor config with the `"key"` option. Keep in mind this must be a [valid redis key](https://redis.io/topics/data-types-intro) which can be just about anything. However, try to keep this simple but descriptive for your own sake. 

```
{
	"pin": "3",
	"type": "Humidity",
	"name": "Weather Station",
	"key": "your_own_key"
}
```
This config above would save in redis under the key `your_own_key` and the `"name"` would be ignored since a `"key"` option is present in the config. 

### Key Values Stored in Redis
Other than the sensor readings, there are a few other important values MudPi stores into redis for you. These value are listed below with more information. 

_**Note on keys**: storing False in redis can be cast as a string which will read truthy in python. Instead we del the key and only store the key if its True_

#### Main Values
`started_at` _[Timestamp]_
* Timestamp of when MudPi started running. Useful to check uptime.
	
#### Pump Values
`last_watered_at` _[Timestamp]_
* Timestamp of when the last water cycle occured. Useful to check watering frequency. 

`pump_should_be_running` _[Booloean]_
* True or nil(key shouldn't exist) value to tell pump worker if it should start a watering cycle. 
	
`pump_shuttoff_override` _[Booloean]_
* True or nil(key shouldn't exist) value to tell pump worker if set to true to immediatly terminate any active water cycle.
* _Key gets automatically deleted once its read by MudPi_
	
`pump_running` _[Booloean]_
* True or nil value set by MudPi to inform you if the water cycle in the pump worker is active or not.
	

### Redis Events
In addition to storing values in redis, MudPi also will publish events when the sensors return readings or during pump cycle changes. Each event will return a JSON payload with an `event: ExampleEvent` and its `data:'Hello World'`. Below are the events MudPi sends out along with the channel they emit on.

#### Pump Events
**channel:** pump

##### Pump Turned On
```
{
	"event": "PumpTurnedOn",
	"data": 1
}
```

##### Pump Turned Off
```
{
	"event": "PumpTurnedOff",
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



## Connecting an Arduino to MudPi
Often the raspberry pi will meet all of our hardware needs, but there are times we need to extend our system with items such as analog sensors. Unfortunantly the raspberry pi does not have analog GPIO so hooking up an Arduino is a cheap easy way to resolve this. 

Connecting to arduinos is easy with MudPi along with the help of Nanpy. Nanpy allows us to issue commands over serial to our Arduino from our raspberry pi running MudPi. Using a [USB to TTL USB serial module](https://www.amazon.com/gp/product/B07CWKHTLH/ref=oh_aui_detailpage_o04_s00?ie=UTF8&psc=1) you can connect your ardiuno using a USB slot from your raspberry pi. 


Once you have an arduino connected, all that you need to do is update your `mudpi.config` file to include your node configuration and restart MudPi. An example of the node configuration is listed below:
```
    "nodes": [
        {
            "name": "Name of Your Node",
            "address": "/dev/ttyUSB0",
            "sensors": [
                {
                    "pin": "3",
                    "type": "Humidity",
                    "name": "Weather Station"
                },
                {
                    "pin": "5",
                    "type": "Soil",
                    "name": "Soil Moisture",
		    "key": "garden_soil_moisture"
                }
            ]
        }
    ],
```

The most important option to connect to your arduino is the `address`, which is the USB device path of your arduino. You can run `ls /dev` in your terminal to get a listing of devices. Typically the value your looking for is one of `/dev/AMA0`, `/dev/ttyUSB0`, or `/dev/ttyUSB1`.

You can read more in the [configuration section](#configuring-mudpi) for details on each of the options available. Additionally the [sensors section](#sensors) can be reviewed for all the available sensors MudPi supports out of the box.



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
* Shoutout to my buddy Drake who helped me with some of the AC to DC electrical stuff.
	
	

## Why Did You Build This?
Gardening at home was taking more time that I would like and buying a simple timer for the hose was not something I really wanted as a solution. I wanted to build my own automated garden with my raspberry pi I had lying around. I do a good deal of web development during the day so the software aspect wasn’t an issue but I hadn’t touched electronics for years since high school so this was a good refresher. **You can read how I built MudPi and the process of me setting it up at home on the MudPi blog**



## Hardware Tested On
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
- [ ] Multi Pump (Relay) Support

**Maybes**
- [ ] Light Sensors ?
- [ ] Hardware controls (i.e. buttons)


<img alt="MudPi Smart Garden" title="MudPi Smart Garden" src="http://ericdavisson.com/img/mudpi/mudPI_LOGO_small_flat.png" width="50px">
