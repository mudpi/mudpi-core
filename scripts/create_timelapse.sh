#!/bin/bash
IMGCOUNT="$(ls -1 $1 | wc -l)"
TOPIC="garden/pi/camera"
echo "Converting $IMGCOUNT Images to Video File"
echo `ffmpeg -r 15 -i $1/mudpi-%05d.jpg -s hd1080 -vcodec libx264 -crf 18 -preset slow /var/www/html/mudpi/public/video/timelapse.mp4`
echo `redis-cli PUBLISH $TOPIC "{\"event\":\"Timelapse\",\"data\":\"\/var\/www\/html\/mudpi\/public\/video\/timelapse.mp4\"}"`