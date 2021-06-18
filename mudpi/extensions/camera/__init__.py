""" 
    Camera Extension
    Capture images or stream from an IP 
    (rtsp) camera or raspberry pi camera. 
"""
import os
import time
import datetime
from mudpi.extensions import Component, BaseExtension


NAMESPACE = 'camera'
UPDATE_INTERVAL = 60

class Extension(BaseExtension):
    namespace = NAMESPACE
    update_interval = UPDATE_INTERVAL

    def init(self, config):
        """ Prepare the extension """
        self.config = config[self.namespace]
        
        self.manager.init(self.config)

        self.manager.register_component_actions('capture', action='capture_image')
        self.manager.register_component_actions('record', action='capture_recording')
        return True


class Camera(Component):
    """ Base Camera
        Base Camera for all camera interfaces
    """

    """ Properties """
    @property
    def id(self):
        """ Unique id or key """
        return self.config.get('key').lower()

    @property
    def name(self):
        """ Friendly name of control """
        return self.config.get('name') or f"{self.id.replace('_', ' ').title()}"

    @property
    def state(self):
        """ State is the last image for display """
        return self.last_image

    @property
    def filename(self):
        """ Return the name you want images and recordings saved as 
            Image: {filename}-{image-count}
            Video: {filename}-{date}
        """
        return self.config.get('filename',  self.id) + f'_{self.file_suffix}'

    @property
    def file_suffix(self):
        """ Return file suffix based on `sequential_naming`"""
        return f'{self.image_count:05}' if self.sequential_naming else \
            datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    

    @property
    def count_start(self):
        """ Return starting count """
        return self.config.get('count_start', 0)

    @property
    def max_count(self):
        """ Return max number of images before it overwrites"""
        return self.config.get('max_count', 500)

    @property
    def sequential_naming(self):
        """ Return True if files should save with 
            counter instead of datetime 
        """
        return self.config.get('sequential_naming', False)

    @property
    def path(self):
        """ Return path to save files too"""
        return os.path.join(self.config.get('path', os.getcwd()))

    @property
    def width(self):
        """ Return width in px """
        return self.config.get('resolution', {}).get('x',1920) #1280

    @property
    def height(self):
        """ Return height in px """
        return self.config.get('resolution', {}).get('y',1080) #720

    @property
    def resolution(self):
        """ Return a dict of (width in px, height in px)
            Default: 1080p
        """
        return {'x': self.width, 'y': self.height}

    @property
    def framerate(self):
        """ Return frames per seconds for recording """
        return self.config.get('framerate', 15)

    @property
    def delay(self):
        """ Return a dict with delay photos should be taken """
        _delay = self.config.get('delay', {"hours":0, "minutes":10, "seconds":0})
        return datetime.timedelta(
                hours=_delay.get('hours', 0), minutes=_delay.get('minutes', 0),
                seconds=_delay.get('seconds', 0))

    @property
    def next_interval(self):
        """ Return next time after delay """
        return (datetime.datetime.now() + self.delay).replace(microsecond=0)

    @property
    def topic(self):
        """ Return topic to listen for commands on """
        return self.config.get('topic', f'{NAMESPACE}/{self.id}')

    @property
    def duration(self):
        """ Return how long the current state has been applied in seconds """
        self._current_duration = time.perf_counter() - self._duration_start
        return round(self._current_duration, 4)

    @property
    def record_duration(self):
        """ Return number of seconds for recording """
        return self.config.get('record_duration', 5)

    @property
    def json_attributes(self):
        """ Return a list of attribute keys to export in json """
        return [
            'filename',
            'file_suffix',
            'count_start',
            'max_count',
            'height',
            'width',
            'resolution',
            'path',
            'sequential_naming',
            'framerate',
            'topic',
            'record_duration',
            'image_count',
            'last_image'
        ]


    """ Methods """
    def fire(self, data={}):
        """ Fire a control event """
        event_data = {
            'event': 'CameraUpdated',
            'data': {
                'component_id': self.id,
                'name': self.name,
                'updated_at': str(datetime.datetime.now().replace(microsecond=0)),
                'state': self.state,
                'last_image': self.last_image
        }}
        event_data['data'].update(data)
        self.mudpi.events.publish(NAMESPACE, event_data)

    def reset_duration(self):
        """ Reset the duration of the current state """
        self._duration_start = time.perf_counter()
        return self._duration_start

    def check_path(self, path_addon=None):
        """ Checks the set path and makes sure directories exist """
        _path = os.path.join(self.path) if not path_addon else os.path.join(self.path, path_addon)
        if not os.path.exists(_path):
            # Attempt to create missing directory
            os.makedirs(self.path, exist_ok=True)

    def increment_count(self):
        """ Update the image counter """
        self.image_count +=1
        if self.image_count > self.max_count:
            self.image_count = self.count_start # overflow


    """ Actions """
    def capture_image(self, data={}):
        """ Capture a single image from the camera
            it should use the file name and increment 
            counter for sequenetial images """
        # call self.increment_count() after each image saved
        pass

    def capture_recording(self, data={}):
        """ Record a video from the camera """
        pass

    """ Internal Methods 
    Do Not Override """
    def _init(self):
        """ Init hook for base component """
        # A string of the last image taken
        self.last_image = None

        # Number of images captured
        self.image_count = 0

        # Duration tracking. Set high to cause capture on first load
        self._duration_start = -(60 * 60 * 24)
    