from time import sleep
from picamera import PiCamera
from datetime import datetime, timedelta

def wait():
    # Calculate the delay to the start of the next hour
    next_hour = (datetime.now() + timedelta(hours=1)).replace(
        minute=0, second=0, microsecond=0)
    delay = (next_hour - datetime.now()).seconds
    #sleep(delay)
    sleep(300)


try:
	camera = PiCamera()
	#camera.start_preview()
	#wait()

	#Warmup
	sleep(10)
	for filename in camera.capture_continuous('/home/pi/Desktop/mudpi/img/mudpi-{timestamp:%Y-%m-%d-%H-%M}.jpg'):
	    print('Image Captured %s' % filename)
	    wait()
except KeyboardInterrupt:
	print('Program Ended')	
camera.close()