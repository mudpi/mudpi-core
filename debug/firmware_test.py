from nanpy.arduinotree import ArduinoTree
from nanpy.serialmanager import SerialManager


def fw_check():
    connection = SerialManager(device=str(input('Enter Device Port: ')))
    a = ArduinoTree(connection=connection)

    print('Firmware classes enabled in cfg.h:')
    print('  ' + '\n  '.join(a.connection.classinfo.firmware_name_list))

    d = a.define.as_dict
    print(
        '\nYour firmware was built on:\n  %s %s' %
        (d.get('__DATE__'), d.get('__TIME__')))


if __name__ == '__main__':
    fw_check()