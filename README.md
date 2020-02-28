# RTL SDR FM Player

A simple GUI front end player for rtl_fm and RTL SDR FM Streamer.

### Description

Developed to be used on Raspbain with the official Rpi 7 inch touch screen in full screen mode, but should work with any Linux OS in a 800x480 window.

## Prerequisites

### RTL-SDR
https://osmocom.org/projects/rtl-sdr/wiki/Rtl-sdr

Turns your Realtek RTL2832 based DVB dongle into a SDR receiver.
rtl_fm is part of this package.

For Raspbain you can install with apt.

```
      sudo apt install rtl-sdr
```   

### Python keyboard module

For now we’re using Pythons keyboard module to control the volume. Because of this dependency the program must be run with sudo. Maybe there is a better solution?
```
     sudo pip3 install keyboard
```

### RTL SDR FM Streamer
https://github.com/AlbrechtL/rtl_fm_streamer/blob/master/README.md

rtl_fm will work without any additional installation but it’s mono only as far as I can tell.
 RTL SDR Streamer provides stereo and seems, to me, to have better sound quality.
To install you’ll have to build and make it. Follow the link to the README.md.

## Setup

Setup and settings are controlled via the settings.ini file.
You have to add your stations to this file manually. Read the comments, it’s easy.

## Usage 

From the command line cd into the cloned directory and enter
```
    sudo python3 player.py
```
