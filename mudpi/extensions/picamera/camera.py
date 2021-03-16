""" 
    Picamera Interface
    Connects to a raspberry pi camera
    through the picamera library.
"""
from picamera import PiCamera
from mudpi.utils import decode_event_data
from mudpi.exceptions import ConfigError
from mudpi.extensions import BaseInterface
from mudpi.extensions.camera import Camera
from mudpi.logger.Logger import Logger, LOG_LEVEL


class Interface(BaseInterface):

    def load(self, config):
        """ Load pi camera component from configs """
        camera = RaspberryPiCamera(self.mudpi, config)
        if camera:
            self.add_component(camera)
        return True

    def validate(self, config):
        """ Validate the camera config """
        if not isinstance(config, list):
            config = [config]

        for conf in config:
            if not conf.get('path'):
                raise ConfigError('Camera needs a `path` to save files to.')
            
        return config


class RaspberryPiCamera(Camera):
    """ Base Camera
        Base Camera for all camera interfaces
    """

    # Pi camera object
    camera = None

    """ Properties """
    @property
    def record_video(self):
        """ Set to True to record video instead of photos """
        return self.config.get('record_video', False)


    """ Methods """
    def init(self):
        """ Prepare the Picamera """
        self.camera = PiCamera(
                resolution=(self.width, self.height))
        # Below we calibrate the camera for consistent imaging
        self.camera.framerate = self.framerate
        # Wait for the automatic gain control to settle
        time.sleep(2)
        # Now fix the values
        self.camera.shutter_speed = self.camera.exposure_speed
        self.camera.exposure_mode = 'off'
        g = self.camera.awb_gains
        self.camera.awb_mode = 'off'
        self.camera.awb_gains = g

    def update(self):
        """ Main update loop to check when to capture images """
        if self.mudpi.is_prepared:
            if self.duration > self.delay.total_seconds():
                if self.record_video:
                    self.capture_recording(duration=self.record_duration)
                else:
                    self.capture_image()
                print(f'Camera {self.id} time:{self.duration}')
                self.reset_duration()


    """ Actions """
    def capture_image(self, data={}):
        """ Capture a single image from the camera
            it should use the file name and increment 
            counter for sequenetial images """
        if self.camera:
            image_name = f'{os.path.join(self.path, self.filename)}.jpg'
            self.camera.capture(image_name)
            self.last_image = os.path.abspath(image_name)
            self.increment_count()
            self.fire({'event': 'ImageCaptured', 'image': image_name})

    def capture_recording(self, data={}):
        """ Record a video from the camera """
        _duration = data.get('duration', 5)
        if self.camera:
            _file_name = f'{os.path.join(self.path, self.filename)}.h264'
            self.camera.start_recording(_file_name)
            self.camera.wait_recording(_duration)
            self.camera.stop_recording()
            self.last_image = os.path.abspath(_file_name)
            self.increment_count()
            self.fire({'event': 'RecordingCaptured', 'file': _file_name})
            