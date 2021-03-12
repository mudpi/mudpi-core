""" 
    RTSP Camera Interface
    Connects to a camera rtsp stream
    through the opencv library.
"""
import os
import cv2
import time
from mudpi.utils import decode_event_data
from mudpi.exceptions import ConfigError
from mudpi.extensions import BaseInterface
from mudpi.extensions.camera import Camera
from mudpi.logger.Logger import Logger, LOG_LEVEL

# Minimum time inbetween updates
MIN_UPDATE_INTERVAL = 5


class Interface(BaseInterface):

    update_interval = 1

    def load(self, config):
        """ Load rtsp camera component from configs """
        camera = RTSPCamera(self.mudpi, config)
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

            if not conf.get('source'):
                raise ConfigError('RTSP Camera needs a `source` to stream from.')

            _delay = conf.get('delay', {})
            if _delay:
                h = _delay.get('hours', 0)
                m = _delay.get('minutes', 0)
                s = _delay.get('seconds', 0)
                if h == 0 and m == 0 and s < MIN_UPDATE_INTERVAL:
                    raise ConfigError('RTSP Camera minimum `delay` must be 5 seconds.')
            
        return config


class RTSPCamera(Camera):
    """ RTSP Camera
        Camera connected over RTSP stream
    """

    # Video capture object
    cap = None

    # Resolution tuple for capture
    size = None

    # Resolution tuple for capture
    _detected_size = None

    # Value to scale image to target size
    _scale = None

    # Number of recordings saved
    _rec_count = 0

    """ Properties """
    @property
    def source(self):
        """ State is the last image for display """
        return self.config.get('source', 0)

    @property
    def record_video(self):
        """ Set to True to record video instead of photos """
        return self.config.get('record_video', False)

    """ Methods """
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

    def open_stream(self):
        """ Open the capture stream """
        if not self.cap:
            self.cap = cv2.VideoCapture(str(self.source)) # it can be rtsp or http stream

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self._detected_size:
            self._detected_size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                        int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        if not self.size:
            if self._detected_size[0] > 0:
                self._scale = (self._detected_size[0] - (self._detected_size[0] - self.width)) / self._detected_size[0]
                self.size = (int(self._detected_size[0] * self._scale), int(self._detected_size[1] * self._scale))

        if not self.cap.isOpened():
            self.cap.open(str(self.source))


    """ Actions """
    def capture_image(self, data={}):
        """ Capture a single image from the camera """
        self.check_path()
        self.open_stream()

        if self.cap.isOpened():
            _,frame = self.cap.read()
            self.cap.release() #releasing camera immediately after capturing picture
            if _ and frame is not None:
                image_name = f'{os.path.join(self.path, self.filename)}.jpg'
                frame = cv2.resize(frame, self.size, interpolation = cv2.INTER_AREA)
                cv2.imwrite(image_name, frame)
                self.last_image = os.path.abspath(image_name)
                self.increment_count()
                self.fire({'event': 'ImageCaptured', 'image': image_name})
            # cap.release()

    def capture_recording(self, data={}):
        """ Record a video from the camera """
        self.check_path()
        self.open_stream()
        _duration = data.get('duration', 5)
            
        self.fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        _file_name = f'{os.path.join(self.path, self.filename)}.mp4'
        print(_file_name)
        _writer = cv2.VideoWriter(_file_name, self.fourcc, self.framerate, self.size)

        _start = time.perf_counter()
        while(self.cap.isOpened()):
            ret, frame = self.cap.read()
            if ret and frame is not None:
                frame = cv2.resize(frame, self.size, interpolation = cv2.INTER_AREA)
                # saving recording
                _writer.write(frame)
            
            if time.perf_counter() - _start > _duration:
                break
        self.cap.release()
        _writer.release()
        self.last_image = os.path.abspath(_file_name)
        self.increment_count()
        self.fire({'event': 'RecordingCaptured', 'file': _file_name})

    def unload(self):
        """ Cleanup resources """
        if self.cap:
            self.cap.release()


class CameraStream:
    """ A class for camera stream to run 
        get images and record videos from.
    """

    # TODO: Make this run a worker for faster
    # image processing and recording. Fix the 
    # fps to match the desired duration. Keep
    # all these camera resources seperate from 
    # the component to make log more central.