import sys
import json
import socket
import inspect
import subprocess
from copy import deepcopy
from mudpi.extensions import Component, BaseExtension, BaseInterface

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_module_classes(module_name):
    """ Get all the classes from a module """
    clsmembers = inspect.getmembers(sys.modules[module_name], inspect.isclass)
    return clsmembers


def decode_event_data(message):
    """ Attempt to decode event formatted data """
    try:
        message = message.decode('utf-8')
    except Exception as error:
        pass

    if isinstance(message, dict):
        # print('Dict Found')
        return message
    elif isinstance(message, str):
        try:
            temp = json.loads(message)
            # print('Json Found')
            return temp
        except Exception as error:
            # print('Json Error. Str Found')
            return {'event': 'Unknown', 'data': message}
    else:
        # print('Failed to detect type')
        return {'event': 'Unknown', 'data': message}


def install_package(package, upgrade=False, target=None):
    """ 
    Install a PyPi package with pip in the background.
    Returns boolean. 
    """
    pip_args = [sys.executable, '-m', 'pip', 'install', '--quiet', package]
    if upgrade:
        pip_args.append('--upgrade')
    if target:
        pip_args += ['--target', os.path.abspath(target)]
    try:
        return 0 == subprocess.call(pip_args)
    except subprocess.SubprocessError:
        return False


def is_package_installed(package):
    """ Check if a package is already installed """
    reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
    if '==' not in package:
        installed_packages = [r.decode().split('==')[0].lower() for r in reqs.split()]
    else:
        installed_packages = [r.decode().lower() for r in reqs.split()]

    return package in installed_packages


def is_extension(cls):
    """ Check if a class is a MudPi Extension.
        Accepts class or instance of class 
    """
    if not inspect.isclass(cls):
        if hasattr(cls, '__class__'):
            cls = cls.__class__
        else:
            return False
    return issubclass(cls, BaseExtension)


def is_interface(cls):
    """ Check if a class is a MudPi Extension.
        Accepts class or instance of class 
    """
    if not inspect.isclass(cls):
        if hasattr(cls, '__class__'):
            cls = cls.__class__
        else:
            return False
    return issubclass(cls, BaseInterface)


def is_component(cls):
    """ Check if a class is a MudPi component.
        Accepts class or instance of class 
    """
    if not inspect.isclass(cls):
        if hasattr(cls, '__class__'):
            cls = cls.__class__
        else:
            return False
    return issubclass(cls, Component)