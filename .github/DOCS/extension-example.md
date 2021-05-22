# Example
The `example` extension provides a set of interfaces to the core components for demonstration purposes. Example components don't connect to any real system but mimic functionality for testing.

This extension does not take an extension level configs and is focused on [interfaces.]({{url('docs/developers-interfaces')}})

---
<div class="mb-2"></div>

## Sensor Interface
Provides a [sensor]({{url('docs/sensors')}}) that returns a random integer. 

<table class="mt-2 mb-4">
<thead><tr><td width="15%">Option</td><td width="15%">Type</td><td width="15%">Required</td><td width="55%">Description</td></tr></thead>
<tbody>
    <tr><td class="font-600">key</td><td class="text-italic text-sm">[String]</td><td>Yes</td><td class="text-xs">Unique slug id for the component</td></tr>
    <tr><td class="font-600">name</td><td class="text-italic text-sm">[String]</td><td>No</td><td class="text-xs">Friendly display name of component. Useful for UI.</td></tr>
    <tr><td class="font-600">data</td><td class="text-italic text-sm">[Integer]</td><td>No</td><td class="text-xs">Returns a number between 0 and <code>data</code>. <strong>Default 10</strong></td></tr>
</tbody>
</table>

### Config Examples
Here is a config of a complete example sensor.

```json
"sensor": [{
    "key": "example_sensor_1",
    "interface": "example",
    "data": 10
}]
```

---
<div class="mb-2"></div>

## Control Interface
Provides a [control]({{url('docs/controls')}}) that will randomly change its state based on `update_chance`. 

<table class="mt-2 mb-4">
<thead><tr><td width="15%">Option</td><td width="15%">Type</td><td width="15%">Required</td><td width="55%">Description</td></tr></thead>
<tbody>
    <tr><td class="font-600">key</td><td class="text-italic text-sm">[String]</td><td>Yes</td><td class="text-xs">Unique slug id for the component</td></tr>
    <tr><td class="font-600">name</td><td class="text-italic text-sm">[String]</td><td>No</td><td class="text-xs">Friendly display name of component. Useful for UI.</td></tr>
    <tr><td class="font-600">update_chance</td><td class="text-italic text-sm">[Integer]</td><td>No</td><td class="text-xs">Percent chance (0-100) it should change state. Default <code>25</code></td></tr>
    <tr><td class="font-600">type</td><td class="text-italic text-sm">[String]</td><td>No</td><td class="text-xs">Type of control behavior. Options: <code>button</code> <code>control</code> or <code>potentiometer</code>. Default: <code>button</code></td></tr>
</tbody>
</table>

### Config
Here is a config of a complete example control.

```json
"control": [{
    "key": "example_control_1",
    "interface": "example",
    "update_chance": 10,
    "type": "switch"
}]
```

---
<div class="mb-2"></div>

## Toggle Interface
Provides a [toggle]({{url('docs/toggles')}}) that is a boolean in memory you can toggle. 

<table class="mt-2 mb-4">
<thead><tr><td width="15%">Option</td><td width="15%">Type</td><td width="15%">Required</td><td width="55%">Description</td></tr></thead>
<tbody>
    <tr><td class="font-600">key</td><td class="text-italic text-sm">[String]</td><td>Yes</td><td class="text-xs">Unique slug id for the component</td></tr>
    <tr><td class="font-600">name</td><td class="text-italic text-sm">[String]</td><td>No</td><td class="text-xs">Friendly display name of component. Useful for UI.</td></tr>
    <tr><td class="font-600">max_duration</td><td class="text-italic text-sm">[Integer]</td><td>No</td><td class="text-xs">Failsafe duration (in seconds) to turn off toggle after. 0 means off. Default <code>0</code></td></tr>
</tbody>
</table>

### Config
Here is a config of a complete example toggle.

```json
"toggle": [{
    "key": "example_toggle_1",
    "interface": "example",
    "max_duration": 360
}]
```

---
<div class="mb-2"></div>

## Character Display Interface
Provides a [character display]({{url('docs/lcd_displays')}}) that prints messages to the log. 

<table class="mt-2 mb-4">
<thead><tr><td width="15%">Option</td><td width="15%">Type</td><td width="15%">Required</td><td width="55%">Description</td></tr></thead>
<tbody>
    <tr><td class="font-600">key</td><td class="text-italic text-sm">[String]</td><td>Yes</td><td class="text-xs">Unique slug id for the component</td></tr>
    <tr><td class="font-600">name</td><td class="text-italic text-sm">[String]</td><td>No</td><td class="text-xs">Friendly display name of component. Useful for UI.</td></tr>
    <tr><td class="font-600">message_limit</td><td class="text-italic text-sm">[Integer]</td><td>No</td><td class="text-xs">Max number of messages to take in queue before overwriting. Default <code>20</code></td></tr>
    <tr><td class="font-600">max_duration</td><td class="text-italic text-sm">[Integer]</td><td>No</td><td class="text-xs">Max duration allowed to display a message in seconds. Default <code>60</code></td></tr>
    <tr><td class="font-600">default_duration</td><td class="text-italic text-sm">[Integer]</td><td>No</td><td class="text-xs">Default duration fallback if one is not set for a new message. Default <code>5</code></td></tr>
    <tr><td class="font-600">topic</td><td class="text-italic text-sm">[String]</td><td>No</td><td class="text-xs">Topic display listens on for events. Default <code>char_display/{key}</code></td></tr>
</tbody>
</table>

### Config
Here is a config of a complete example character display.

```json
"char_display": [{
    "key": "example_display_1",
    "interface": "example",
    "max_duration": 30,
    "default_duration": 10,
    "topic": "char_display/example_display_1"
}]
```

