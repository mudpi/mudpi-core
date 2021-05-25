from setuptools import find_packages, setup
from mudpi.constants import __version__
setup(
    name='mudpi',
    version=__version__,
    description="Privacy Focused Automation for the Garden & Home",
    author="Eric Davisson",
    author_email="eric@mudpi.app",
    url="https://mudpi.app",
    include_package_data=True,
    package_data={'': ['*.json', '*.yml', '*.config', '*.config.example', '*.sh']},
    packages=find_packages(exclude=['tools', 'tests', 'scripts', 'debug']),
    entry_points={
        'console_scripts': [
            'mudpi = mudpi.__main__:main',
        ],
    },
    install_requires=[
        "redis",
        "pyyaml",
        "paho-mqtt"
    ]
)