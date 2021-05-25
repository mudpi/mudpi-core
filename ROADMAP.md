# Roadmap to 1.0

Below is a high level roadmap of features / design goals I want to complete on MudPi. 

## 0.1

- [x]  Raspberry Pi Teperature Sensor
- [x]  Raspberry Pi Float Sensor
- [x]  Raspberry Pi LCD Screen

## 0.2

- [x]  Pump Support for Raspberry Pi using Relay
- [x]  Use Redis to Store Values / State

## 0.3

- [x]  Load system from a Config File
- [x]  Dynamically Load Sensors
- [x]  Create Main Process and use Multi-Threading

## 0.4

- [x]  Communicate to Arduino
- [x]  Create Arduino Sensor Support
- [x]  Arduino Soil Sensor
- [x]  Arduino Float Sensor
- [x]  Arduino Temperature / Moisture Sensor
- [x]  Arduino Onewire

## 0.5

- [x]  Implement event system and using Redis Pub/Sub

## 0.6

- [x]  Add camera support for raspberry pi cam

## 0.7

- [x]  Refactor Workers to better handle events
- [x]  Refactor Pump into more Configurable Dynamic Relays

### 0.7.1

- [x]  Fix temp sensor fot DHT11 and DHT22 [Bug]

### 0.7.2

- [x]  Fix relay not listening to `Switch` event with a value of `0` [Bug]

### 0.7.3 Pull Request & New Library

- [x]  Add "model" to sensor `Humidity` type config
- [x]  Need to Install `Adafruit_DHT`

### 0.7.4

- [x]  Create Arduino Wireless Sensor Node
    - [x]  Wifi

## 0.8

- [x]  Add Controls
    - [x]  Buttons
        - [x]  Momentary
        - [x]  Latching ( Switch?)
    - [x]  Switches
    - [x]  Potentiometer
    - [x]  Joystick (Its 2 pots and a button)
- [x]  Add Light intensity sensor
- [x]  Add support for relays on arduino slaves
- [x]  Add controls for solenoids
- [x]  Refactor config file
    - [x]  Change key names to match syntax across the file
    - [x]  Allow more configuration options
        - [x]  Allow workers to be configured
        - [x]  Allow channels to be configured
- [x]  Add support for buttons
- [x]  Add Actions
- [x]  Add Triggers
- [x]  Remove old LCD screen worker
- [x]  I2C Support?
    - [x]  Sensors
        - [x]  BME680
    - [x]  Screens
        - [x]  20x4
        - [x]  16x2
- [x]  Catch for No Server Configs
- [x]  Check for KeyErrors in the Configs
- [x]  Allow more empty items in config as default
- [x]  Fix Sensor count on `pi sensor worker` print statement
- [x]  Make print statements depend on debug mode better
- [x]  Fix import of `SwitchControl` to make switches work on `pi_control_worker`
- [x]  Investigate `DHT22` sensor types
- [x]  Add ability to configure redis connection in `variables.py`

- [x]  Update nanpy to support Software serial HC12 including channels
    - [x]  Not as reliable as wifi
- [x]  Install Script to install all dependencies
- [x]  Add Batteries and Solar Charging
    - [x]  Allow readings of charge level and battery percent
- [x]  Allow linked sensors and relays (like float sensor to turn off relay - pump)
- [x]  Allow soil readings on solar nodes

**v0.9.1**

- [x]  Add way to trigger dynamic variables in messages to display
    - [x]  snippet replacement to redis key lookup
    - [x]  Provide a redis [key] between square brackets and it will be replaced with value
- [x]  Add action `sequences` to perform actions with delays between
    - [x]  Each step in sequence can have thresholds of its own
    - [x]  Can skip to next step using event
        - [x]  `SequenceNextStep`, `SequencePreviousStep`
        - [x]  If no `duration` is set then you must pass this event to toggle next step
    - [x]  Steps have an optional `delay` before triggering actions
    - [x]  Emits event on start and end of sequence
        - [x]  `SequenceStarted`, `SequenceEnded`
    - [x]  Emits event on each step of sequence
        - [x]  `SequenceStepStarted`, `SequenceStepEnded`
- [x]  Relay Refactoring
    - [x]  The `topic` is no longer required. This will default to `mudpi/relays/[relay_key]`
    - [x]  An exception is thrown if no `key` if found in config
    - [x]  A `name` will be generated from a `key` if one is not provided
- [x]  Sensors
    - [x]  `key` is now be required
    - [x]  A `name` will be generated from a `key` if one is not provided
- [x]  Controls
    - [x]  `key` is now be required
    - [x]  A `name` will be generated from a `key` if one is not provided
- [x]  Merge in Peerys Logger PR#12
    - [x]  Increase debug logging capabilities
    - [x]  Update sequences to use new logger

## 0.10.0

- [x]  Updated Socket `Server` to Allow Incoming Data
    - [x]  Make the socket server relay events
- [x]  Displays on Nodes
- [x]  Optimize workers to use new `wait` method for faster responses
    - [x]  See how its used in `sequence_worker.py` -ERIC NOTE
- [x]  Relay Failsafe Durations
- [x]  Allow `Display` messages to be added to front of the queue
- [x]  Build `StateMachine` that stores state of everything
- [x]  Look into making base `Component` class that all controls and sensors inherit from
- [x]  refactor `Workers` to reduce code duplication
- [x]  Change `event` system to work on adapter pattern
    - [x]  `Redis` adapter
    - [x]  `MQTT` adapter
- [x]  Update events to be more streamlined
    - [x]  Changing event channels to more standard
- [x]  Trigger Groups needs `key` passed down properly
- [x]  Add `before`, `after` and `between` trigger types for **datetime** comparisons
- [x]  Add `sun` triggers that check time against sun data
- [x]  Create a `timer` trigger
    - [x]  reset the timer
    - [x]  Does something while timer `active`
    - [x]  Does something when timer finished
- [x]  Allow password for `redis`
- [x]  Allow password for `mqtt`
- [x]  Add triggers for `nfc`
- [x]  Add tag `sensor` for `nfc`

## 1.0

- [ ]  Update custom actions configs
- [ ]  Add `--clear_cache` flag to clear cache on run
- [ ]  Make a simple `api`
- [ ]  Allow better `templating` in dynamic messages and other areas of system
- [ ]  Merge in the weather API from @icyspace
- [ ]  Add a `Solarbeam` client to connect online
- [ ]  Generic Event Trigger
- [ ]  MCP3208 Updates
- [ ]  Device discovery
    - [ ]  Allow configurations to be posted on event system
    - [ ]  MQTT
    - [ ]  Redis
    - [ ]  Socket
- [ ]  Additional Sensor Support
    - [ ]  Add Flowmeter Support
    - [ ]  Add in PH Sensor support
    - [ ]  Add in EC sensor support
    - [ ]  Debug the Onewire temp again
    - [ ]  Voltage Meter
    - [x]  Add in better defaults for float sensors.
- [x]  Allow nanpy to run over wireless serial??

## 1.0+

- [ ]  Remote control with infrared?
- [ ]  Motion Sensors
- [ ]  Motor Controls
- [ ]  Interface with Homeassistnt IO
- [ ]  Interface with Google home?
- [ ]  `alarms` are like **timers** but require you to shut them off

### *Need Hardware

- [ ]  Interface with z-wave
- [ ]  Make Oled display worker? (need parts)
- [ ]  Any additional sensors (could use part donations)

## Non Core Tasks

- [ ]  Passive Nodes Can be Provisioned over BLE automaticially
- [ ]  Update config on site
- [ ]  Make Solarbeam proto page
- [ ]  Push assistant changes with solarbeam account
- [ ]  Fix configs on solarbeam dashboard

**Mudpi Gateway / Sensors** 

[MudPi Gateway & Firmware](https://www.notion.so/MudPi-Gateway-Firmware-1cb3fc4416b04b5dbd2349a10cfc0fd8)

- [ ]  Create MudPi Gateway
    - [ ]  433MHZ | 915MHZ | BLE | LORA
    - [x]  Wifi
    - [x]  Socket
        - [x]  Port 7007
    - [x]  Websockets
    - [x]  MQTT
- [x]  Create MudPi Passive sensors firmware
    - [ ]  Bluetooth | 433MHZ | 915MHZ | BLE?
    - [x]  Wifi?
    - [ ]  Allow Wifi to be configured
    - [ ]  Fall back to hotspot
    - [ ]  Update passive node to support lora
- [ ]  Look into ESP-MESH


## Fixes in v0.10.0 to do

- ~~Investigate the displays~~
- ~~Make dynamic messages in displays work with substate (i.e. `.` parsing in tag)~~
- ~~Make toggles listen to events~~
- ~~Fix typos on docs about actions~~
- ~~Allow actions to accept data in the configs~~

    ```jsx
    action: 'example.toggle'
    data: 
    	component_id: 'example'
    	state: true
    ```

- ~~Add `analog` to nanpy sensor docs~~
- ~~Restore states for components is not called~~
- ~~Make sun sensor check for time on last reading after restore to adjust next update~~
- ~~Add UUID to events to prevent issues~~
- ~~Fix the GPIO button edge detect~~
- ~~Add way to send message to front of display queue~~
- ~~Check `state_keys` to make sure component is loaded before restoring~~
- ~~Fix the `node` reconnect (There is bad self.config['name'] in debug print)~~
