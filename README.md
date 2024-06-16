# NOTE

I will refer [OpenIPC](https://openipc.org/) device as *client* and your
receiving end as *host*.  Of
 course, host and client can be the same machine,
as long as the network
 connection is established.

Modify [`majestic.yaml`](majestic.yaml) (located in `/etc/majestic.yaml`), the `outgoing` section and enable the
UDP server at host first ([`recv.sh`](recv.sh)), which using
[GStreamer](https://gstreamer.freedesktop.org/), so make sure your host have
installed it and its plugins. see
[*installing*](https://gstreamer.freedesktop.org/documentation/installing/index.html?gi-language=c)
for details.

Basically [majestic](#majestic) is sending RTP stream (whose payload is H.265 or
H.264, depends on the configuration) to the host via RTP over UDP, acting like following GStreamer pipeline:

```bash
HOST="127.0.0.1"
PORT=5600
SRC_DEVICE="/dev/video0"
gst-launch-1.0 -e \
    v4l2src device=$SRC_DEVICE ! \
    "video/x-raw" ! \
    videoconvert  ! \
    x264enc tune=zerolatency ! \
    rtph264pay ! \
    udpsink host=$HOST port=$PORT
```

Bypassing the [video for linux](https://en.wikipedia.org/wiki/Video4Linux)
(V4L2) interface, directly access the ISP and vendor specific codec, latency
could be minimized, which framework like GStreamer struggles to do.

## Scripts

- use [`serve.py`](serve.py) to capture the stream from the client and save it as
a file. For [majestic](#majestic) it should be
[RTP](https://en.wikipedia.org/wiki/Real-time_Transport_Protocol) stream.
- use [`decode.py`](decode.py) to decode the header of RTP stream and the
[NAL](https://en.wikipedia.org/wiki/Network_Abstraction_Layer) units of the
[H.265](https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding) stream.
- use [`depay_cat.py`](depay_cat.py) to view each captured UDP payload.

I believe
[`rtph265depay`](https://gstreamer.freedesktop.org/documentation/rtp/rtph265depay.html?gi-language=c)
is doing something magic.  If you unwrap the RTP stream manually (replace the
RTP header with `000001` magic) you can't get a valid H.265 stream. I need to
investigate this further.

## majestic

[majestic](https://github.com/OpenIPC/wiki/blob/master/en/majestic-streamer.md) is a closed-source software.

> A universal IP-camera streamer. This software is the major part of the OpenIPC
Firmware. Although it is not fully open source at this stage of development, we
are considering opening up the codebase when the software matures enough and
gets enough funding for open development.

> Majestic code while is not open, provides unprecedented performance and
capabilities for a wide range of hardware. The author of Majestic streamer is
looking into possibilities to open-source the codebase after he secures enough
funds to support further open development.

- [majestic in OpenIPC Wiki](https://github.com/OpenIPC/wiki/blob/master/en/majestic-streamer.md)
- [OpenIPC majestic Telegram Channel](https://t.me/s/openipc_dev?before=105808)
- [Troubleshooting Majestic](https://github.com/OpenIPC/wiki/blob/master/en/trouble-majestic.md)
- [OpenIPC/majestic-plugins](https://github.com/OpenIPC/majestic-plugins)
- [OpenIPC/smolrtsp](https://github.com/OpenIPC/smolrtsp)

```bash
killall majestic
/usr/bin/majestic -s
```

Note that you could use other streamer for OpenIPC, like [OpenIPC/mini](https://github.com/OpenIPC/mini), [Venc](https://github.com/OpenIPC/silicon_research)

### Note

I could almost guess what majestic is doing. majestic reads video stream from
vendor [ISP](https://en.wikipedia.org/wiki/Image_processor) (Image Signal
Processor). CMOS/CCD sensor is connected to the ISP, via [MIPI/CSI
interface](https://en.wikipedia.org/wiki/Camera_Serial_Interface). The image
acquired by the ISP (usually YUYV or NV12) is then encoded by the
[VPU](https://en.wikipedia.org/wiki/Video_processing_unit) (Video Processing
Unit) and sent to the outside by either RTSP or RTP over UDP, or just saving it
in disk.

There's nothing secret about this, but vendor codec is causing the headache.
There's too much vendor-specific stuff.

## Note for me

```bash
busybox ps -o pid,user,args
busybox netstat -l
```

```bash
gst-launch-1.0 -e filesrc location=output/o.265 ! h265parse ! avdec_h265 ! videoconvert ! jpegenc ! multifilesink location=frame_%05d.jpg
ffprobe -analyzeduration 100M -probesize 100M output/o.265
ffmpeg -report -i output/o.265 -f null -
h265nal output/o.265 -d > nal.txt
ffmpeg -i output/o.265 -c:v copy output.mp4
```
