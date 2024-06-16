#!/bin/bash

# See also majestic.yaml
# Get the current date and time in the format YYYYMMDD-HHMMSS
DATE=$(date +"%Y%m%d-%H%M%S")

# Use the date and time to create a filename
FILENAME="video-${DATE}.mp4"

# Run the GStreamer pipeline with the dynamic filename
gst-launch-1.0 -e udpsrc port=5600 \
! 'application/x-rtp, encoding-name=H265, payload=96' \
! rtph265depay \
! tee name=t \
t. ! queue ! avdec_h265 ! autovideosink \
t. ! queue ! h265parse ! mp4mux ! filesink location=$FILENAME
