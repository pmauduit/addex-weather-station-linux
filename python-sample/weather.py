#!/usr/bin/env python
# -*- coding: utf-8 -*-

import usb.core
import array
import sys
import os
import time
import datetime

import urllib.request
from xml.dom import minidom

# this is the code related to the current location
# it will be given as URL parameter to bing weather services

# currently set to Chambéry, France
# old code
CODE_LOCATION="wc:FRXX0147"
# new code
CODE_LOCATION="Chamb%C3%A9ry,Fr"

# temperature format (C or F)
TEMP_FMT="C"

# URL to bing weather service
# old one
BINGWEATHER_URL= "http://weather.msn.com/data.aspx?wealocations=%s&weadegreetype=%s" % (CODE_LOCATION, TEMP_FMT,)
# new one (as of 2014-10)
BINGWEATHER_URL = "http://weather.service.msn.com/data.aspx?weadegreetype=%s&culture=en-US&weasearchstr=%s&src=outlook" % (TEMP_FMT, CODE_LOCATION,)

# Our sample packet that would be send via a URB request
#
#                     0     1     2     3     4     5     6     7     8     9     A     B     C     D     E     F
sample_conf_pkt = [0xa8, 0x00, 0x03, 0x0a, 0x04, 0x0c, 0x26, 0x00, 0x06, 0x24, 0x1f, 0x04, 0x01, 0x00, 0x04, 0x04,
                   0x0d, 0x01, 0x01, 0x1e, 0x04, 0x01, 0x1c, 0x01, 0x01, 0x1e, 0xff]

if TEMP_FMT == "F":
    sample_conf_pkt[0x00] = 0x00


# XML parsing
weather_doc = minidom.parse(urllib.request.urlopen(BINGWEATHER_URL))
current_weather = weather_doc.getElementsByTagName("current")[0]
forecasts_nodes = weather_doc.getElementsByTagName("forecast")


# outdoor temperature
ctemp = int(current_weather.getAttribute("temperature"))
sample_conf_pkt[0x08] =  ctemp if ctemp > 0 else 0x80  ^ abs(ctemp)
# weather icon (current), skycode
sample_conf_pkt[0x09] = int(current_weather.getAttribute("skycode")) % 256
# humidity
sample_conf_pkt[0x0A] = int(current_weather.getAttribute("humidity")) % 256

# current max
ctm = int(forecasts_nodes[0].getAttribute("high"))
sample_conf_pkt[0x0B] =  ctm if ctm > 0 else 0x80 ^ abs(ctm)

# current min
ctmin = int(forecasts_nodes[0].getAttribute("low"))
sample_conf_pkt[0x0C] = ctmin if ctmin > 0 else 0x80 ^ abs(ctmin)


# current weather icon (forecast[0] skycodeday)
sample_conf_pkt[0x0D] = int(forecasts_nodes[0].getAttribute("skycodeday")) % 256

# next days (4 frames)
tmax = int(forecasts_nodes[1].getAttribute("high"))
tmin = int(forecasts_nodes[1].getAttribute("low"))
sample_conf_pkt[0x0E] = tmax if tmax > 0 else 0x80 ^ abs(tmax)
sample_conf_pkt[0x0F] = tmin if tmin > 0 else 0x80 ^ abs(tmin)
sample_conf_pkt[0x10] = int(forecasts_nodes[1].getAttribute("skycodeday")) % 256

tmax = int(forecasts_nodes[2].getAttribute("high"))
tmin = int(forecasts_nodes[2].getAttribute("low"))
sample_conf_pkt[0x11] = tmax if tmax > 0 else 0x80 ^ abs(tmax)
sample_conf_pkt[0x12] = tmin if tmin > 0 else 0x80 ^ abs(tmin)
sample_conf_pkt[0x13] = int(forecasts_nodes[2].getAttribute("skycodeday")) % 256

tmax = int(forecasts_nodes[3].getAttribute("high"))
tmin = int(forecasts_nodes[3].getAttribute("low"))
sample_conf_pkt[0x14] = tmax if tmax > 0 else 0x80 ^ abs(tmax)
sample_conf_pkt[0x15] = tmin if tmin > 0 else 0x80 ^ abs(tmin)
sample_conf_pkt[0x16] = int(forecasts_nodes[3].getAttribute("skycodeday")) % 256

tmax = int(forecasts_nodes[4].getAttribute("high"))
tmin = int(forecasts_nodes[4].getAttribute("low"))
sample_conf_pkt[0x17] = tmax if tmax > 0 else 0x80 ^ abs(tmax)
sample_conf_pkt[0x18] = tmin if tmin > 0 else 0x80 ^ abs(tmin)
sample_conf_pkt[0x19] = int(forecasts_nodes[4].getAttribute("skycodeday")) % 256


# Find the first weather_station attached
# (you don't have more than one, do you ?)
weather_station = usb.core.find(idVendor=0x04f3, idProduct=0x0001)


# Setting up time relying on the machine date/time
sample_conf_pkt[0x01] = datetime.datetime.now().year % 2000
sample_conf_pkt[0x02] = datetime.datetime.now().month
sample_conf_pkt[0x03] = datetime.datetime.now().day
# weekday returns 0 if monday, the protocol expect 0 to be sunday ...
sample_conf_pkt[0x04] = (datetime.datetime.now().weekday() + 1) % 7
sample_conf_pkt[0x05] = datetime.datetime.now().hour
sample_conf_pkt[0x06] = datetime.datetime.now().minute
sample_conf_pkt[0x07] = datetime.datetime.now().second


if weather_station is None:
    raise ValueError('Device not found')

weather_station.set_configuration()

ret = weather_station.ctrl_transfer(0x40, 0x41, 0xfa54, 0, array.array('B', sample_conf_pkt))

print("done: {} bytes transferred".format(ret))
