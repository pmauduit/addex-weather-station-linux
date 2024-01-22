#!/usr/bin/env python
# -*- coding: utf-8 -*-

import usb.core
import array
import sys
import os
import time
import datetime
import pytz

import urllib.request
from xml.dom import minidom
import json

# sets the user's timezone
USER_TIMEZONE="Europe/Paris"

# this is the code related to the current location
# it will be given as URL parameter to bing weather services

# currently set to Cognin, France
# old code
CODE_LOCATION="wc:FRXX0147"
# new code
CODE_LOCATION="Cognin,Fr"

# Lattitude / longitude
COORDS_LOCATION=(45.56, 5.89)

# temperature format (C or F)
TEMP_FMT="C"

# URL to bing weather service
# old one
BINGWEATHER_URL= "http://weather.msn.com/data.aspx?wealocations=%s&weadegreetype=%s" % (CODE_LOCATION, TEMP_FMT,)
# new one (as of 2014-10)
BINGWEATHER_URL = "http://weather.service.msn.com/data.aspx?weadegreetype=%s&culture=en-US&weasearchstr=%s&src=outlook" % (TEMP_FMT, CODE_LOCATION,)
# Bing weather service discontinued as of 14th of may 2023.
OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast?latitude=%.2f&longitude=%.2f&hourly=temperature_2m,relativehumidity_2m,weathercode&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto" % (COORDS_LOCATION)

# weathercode to bing skycode mapping
# See WMO interpretation codes here:
# https://open-meteo.com/en/docs
WEATHERCODE_TO_BING = {
 0:  0x20, # clear sky
 1:  0x22, # Mainly clear, partly cloudy, and overcast
 2:  0x22,
 3:  0x22,
 45: 0x21, # Fog and depositing rime fog
 48: 0x21,
 51: 0x2d, # Drizzle: Light, moderate, and dense intensity
 53: 0x2d, # Drizzle: Light, moderate, and dense intensity
 55: 0x2d, # Drizzle: Light, moderate, and dense intensity
 56: 0x12, # Freezing Drizzle: Light and dense intensity
 57: 0x12, # Freezing Drizzle: Light and dense intensity
 61: 0x23, # Rain: Slight, moderate and heavy intensity
 63: 0x23, # Rain: Slight, moderate and heavy intensity
 65: 0x23, # Rain: Slight, moderate and heavy intensity
 66: 0x05, # Freezing Rain: Light and heavy intensity
 67: 0x05,
 71: 0x10, # Snow fall: Slight, moderate, and heavy intensity
 73: 0x10,
 75: 0x10,
 77: 0x10, # Snow grains
 80: 0x23, # Rain showers: Slight, moderate, and violent
 81: 0x23, # Rain showers: Slight, moderate, and violent
 82: 0x23, # Rain showers: Slight, moderate, and violent
 85: 0x6e, # Snow showers slight and heavy
 86: 0x6e,
 95: 0x75, # Thunderstorm: Slight or moderate
 96: 0x75, # Thunderstorm: Slight or moderate
 99: 0x75  # Thunderstorm: Slight or moderate
}

# Our sample packet that would be sent via a URB request
#
#                     0     1     2     3     4     5     6     7     8     9     A     B     C     D     E     F
sample_conf_pkt = [0xa8, 0x00, 0x03, 0x0a, 0x04, 0x0c, 0x26, 0x00, 0x06, 0x24, 0x1f, 0x04, 0x01, 0x00, 0x04, 0x04,
                   0x0d, 0x01, 0x01, 0x1e, 0x04, 0x01, 0x1c, 0x01, 0x01, 0x1e, 0xff]

if TEMP_FMT == "F":
    sample_conf_pkt[0x00] = 0x00


now = datetime.datetime.now(pytz.timezone(USER_TIMEZONE))
# XML parsing
#weather_doc = minidom.parse(urllib.request.urlopen(BINGWEATHER_URL))
#current_weather = weather_doc.getElementsByTagName("current")[0]
#forecasts_nodes = weather_doc.getElementsByTagName("forecast")

# JSON parsing
json_response = urllib.request.urlopen(OPENMETEO_URL)
weather_doc = json.loads(json_response.read())

# outdoor temperature
#ctemp = int(current_weather.getAttribute("temperature"))
ctemp = int(weather_doc['hourly']['temperature_2m'][now.hour])
sample_conf_pkt[0x08] =  ctemp if ctemp > 0 else 0x80  ^ abs(ctemp)


# weather icon (current), skycode
#skycode = current_weather.getAttribute("skycode")
skycode = WEATHERCODE_TO_BING[weather_doc['daily']['weathercode'][0]]
humidity = weather_doc['hourly']['relativehumidity_2m'][now.hour]
sample_conf_pkt[0x09] = int(skycode) % 0x100
# humidity
sample_conf_pkt[0x0A] = int(humidity) % 0x100

# current max
#ctm = int(forecasts_nodes[0].getAttribute("high"))
ctm = int(weather_doc['daily']['temperature_2m_max'][0])
sample_conf_pkt[0x0B] =  ctm if ctm > 0 else 0x80 ^ abs(ctm)

# current min
#ctmin = int(forecasts_nodes[0].getAttribute("low"))
ctmin =  int(weather_doc['daily']['temperature_2m_min'][0])
sample_conf_pkt[0x0C] = ctmin if ctmin > 0 else 0x80 ^ abs(ctmin)

# current weather icon (forecast[0] skycodeday)
#skycodeday = forecasts_nodes[0].getAttribute("skycodeday")
skycodeday =  WEATHERCODE_TO_BING[weather_doc['daily']['weathercode'][0]]
sample_conf_pkt[0x0D] = int(skycodeday)

# next days (4 frames)
#tmax = int(forecasts_nodes[1].getAttribute("high"))
#tmin = int(forecasts_nodes[1].getAttribute("low"))
#skycodeday = int(forecasts_nodes[1].getAttribute("skycodeday"))
tmax = int(weather_doc['daily']['temperature_2m_max'][1])
tmin = int(weather_doc['daily']['temperature_2m_min'][1])
skycodeday = WEATHERCODE_TO_BING[int(weather_doc['daily']['weathercode'][1])]
sample_conf_pkt[0x0E] = tmax if tmax > 0 else 0x80 ^ abs(tmax)
sample_conf_pkt[0x0F] = tmin if tmin > 0 else 0x80 ^ abs(tmin)
sample_conf_pkt[0x10] = skycodeday

#tmax = int(forecasts_nodes[2].getAttribute("high"))
#tmin = int(forecasts_nodes[2].getAttribute("low"))
#skycodeday = int(forecasts_nodes[1].getAttribute("skycodeday"))
tmax = int(weather_doc['daily']['temperature_2m_max'][2])
tmin = int(weather_doc['daily']['temperature_2m_min'][2])
skycodeday = WEATHERCODE_TO_BING[int(weather_doc['daily']['weathercode'][2])]
sample_conf_pkt[0x11] = tmax if tmax > 0 else 0x80 ^ abs(tmax)
sample_conf_pkt[0x12] = tmin if tmin > 0 else 0x80 ^ abs(tmin)
sample_conf_pkt[0x13] = skycodeday

#tmax = int(forecasts_nodes[2].getAttribute("high"))
#tmin = int(forecasts_nodes[2].getAttribute("low"))
#skycodeday = int(forecasts_nodes[1].getAttribute("skycodeday"))
tmax = int(weather_doc['daily']['temperature_2m_max'][3])
tmin = int(weather_doc['daily']['temperature_2m_min'][3])
skycodeday = WEATHERCODE_TO_BING[int(weather_doc['daily']['weathercode'][3])]
sample_conf_pkt[0x14] = tmax if tmax > 0 else 0x80 ^ abs(tmax)
sample_conf_pkt[0x15] = tmin if tmin > 0 else 0x80 ^ abs(tmin)
sample_conf_pkt[0x16] = skycodeday

#tmax = int(forecasts_nodes[2].getAttribute("high"))
#tmin = int(forecasts_nodes[2].getAttribute("low"))
#skycodeday = int(forecasts_nodes[1].getAttribute("skycodeday"))
tmax = int(weather_doc['daily']['temperature_2m_max'][4])
tmin = int(weather_doc['daily']['temperature_2m_min'][4])
skycodeday = WEATHERCODE_TO_BING[int(weather_doc['daily']['weathercode'][4])]
sample_conf_pkt[0x17] = tmax if tmax > 0 else 0x80 ^ abs(tmax)
sample_conf_pkt[0x18] = tmin if tmin > 0 else 0x80 ^ abs(tmin)
sample_conf_pkt[0x19] = skycodeday


# Find the first weather_station attached
# (you don't have more than one, do you ?)
weather_station = usb.core.find(idVendor=0x04f3, idProduct=0x0001)



# Setting up time relying on the machine date/time
sample_conf_pkt[0x01] = now.year % 2000
sample_conf_pkt[0x02] = now.month
sample_conf_pkt[0x03] = now.day
# weekday returns 0 if monday, the protocol expects 0 to be sunday
# can it also depend on the locale configuration ?
sample_conf_pkt[0x04] = (now.weekday() + 1) % 7
sample_conf_pkt[0x05] = now.hour
sample_conf_pkt[0x06] = now.minute
sample_conf_pkt[0x07] = now.second


if weather_station is None:
    raise ValueError('Device not found')

weather_station.set_configuration()

ret = weather_station.ctrl_transfer(0x40, 0x41, 0xfa54, 0, array.array('B', sample_conf_pkt))

print(sample_conf_pkt)
print("done: {} bytes transferred".format(ret))
