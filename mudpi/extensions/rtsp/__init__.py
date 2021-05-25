""" 
    RTSP Camera Extension
    Connects to a RTSP or HTTP camera
    stream to capture images and record
    videos.
"""
from mudpi.extensions import BaseExtension


class Extension(BaseExtension):
    namespace = 'rtsp'
    update_interval = 1
 