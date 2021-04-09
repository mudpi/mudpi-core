"""Dump all possible values from the AVR."""

import inspect
from nanpy.arduinotree import ArduinoTree
from nanpy.serialmanager import SerialManager
from pprint import pprint
from nanpy.classinfo import FirmwareMissingFeatureError

FORMAT = '%-20s = %20s'


def dump(obj, selected_names=None):
    if selected_names:
        ls = selected_names
    else:
        ls = dir(obj)
    for attr in ls:
        if not attr.startswith('__'):
            if not inspect.ismethod(getattr(obj, attr)):
                print(FORMAT % (attr, getattr(obj, attr)))


def dump_dict(d):
    for defname in sorted(d.keys()):
        defvalue = d[defname]
        print(FORMAT % (defname, defvalue))

def myprint(template, name, func):
    try:
        print(template % (name, func()))
    except FirmwareMissingFeatureError:
        pass

def dumpall():
    connection = SerialManager()
    a = ArduinoTree(connection=connection)

    if a.vcc:
        myprint(FORMAT + ' V', 'read_vcc', lambda : a.vcc.read())
    myprint(FORMAT + ' sec', 'uptime', lambda : a.api.millis() / 1000.0)

    print('')
    print('================================')
    print('firmware classes:')
    print('================================')
    pprint(a.connection.classinfo.firmware_name_list)

    print('')
    print('================================')
    print('defines:')
    print('================================')
    dump_dict(a.define.as_dict)

    if a.esp:
        print('')
        print('================================')
        print('ESP:')
        print('================================')
        myprint(FORMAT , 'getVcc', lambda :a.esp.getVcc())
        myprint(FORMAT , 'getFreeHeap', lambda :a.esp.getFreeHeap())
        myprint(FORMAT , 'getChipId', lambda :a.esp.getChipId())
        myprint(FORMAT , 'getSdkVersion', lambda :a.esp.getSdkVersion())
        myprint(FORMAT , 'getBootVersion', lambda :a.esp.getBootVersion())
        myprint(FORMAT , 'getBootMode', lambda :a.esp.getBootMode())
        myprint(FORMAT , 'getCpuFreqMHz', lambda :a.esp.getCpuFreqMHz())
        myprint(FORMAT , 'getFlashChipId', lambda :a.esp.getFlashChipId())
        myprint(FORMAT , 'getFlashChipRealSize', lambda :a.esp.getFlashChipRealSize())
        myprint(FORMAT , 'getFlashChipSize', lambda :a.esp.getFlashChipSize())
        myprint(FORMAT , 'getFlashChipSpeed', lambda :a.esp.getFlashChipSpeed())
        myprint(FORMAT , 'getFlashChipMode', lambda :a.esp.getFlashChipMode())
        myprint(FORMAT , 'getFlashChipSizeByChipId', lambda :a.esp.getFlashChipSizeByChipId())
        myprint(FORMAT , 'getResetReason', lambda :a.esp.getResetReason())
        myprint(FORMAT , 'getResetInfo', lambda :a.esp.getResetInfo())
        myprint(FORMAT , 'getSketchSize', lambda :a.esp.getSketchSize())
        myprint(FORMAT , 'getFreeSketchSpace', lambda :a.esp.getFreeSketchSpace())

    print('')
    print('================================')
    print('pins:')
    print('================================')

    myprint(FORMAT , 'total_pin_count', lambda :a.pin.count)
    myprint(FORMAT , 'digital_names', lambda :a.pin.names_digital)
    myprint(FORMAT , 'analog_names', lambda :a.pin.names_analog)

    for pin_number in range(a.pin.count):
        print('---------- pin_number=%s ---------------' % pin_number)
        pin = a.pin.get(pin_number)
        dump(
            pin,
            'name pin_number pin_number_analog is_digital is_analog avr_pin mode digital_value analog_value programming_function'.split())
        if pin.pwm.available:
            print('--- pwm ---')
            dump(pin.pwm, '''frequency frequencies_available base_divisor divisor divisors_available
                                timer_mode
                                timer_register_name_a
                                timer_register_name_b
                                wgm
            '''.split())


    if a.register:
        print('')
        print('================================')
        print('registers:')
        print('================================')
        for x in a.register.names:
            r = a.register.get(x)
            if r.size == 2:
                v = '0x%04X' % r.value
            else:
                v = '  0x%02X' % r.value
    
            print('%-20s = %s @0x%2X (size:%s)' % (r.name, v, r.address, r.size))

        

if __name__ == '__main__':
    dumpall()