import usb.core
import usb.util
import sys
import os
import time

#sample_conf_pkt= [0xa8, 0x0b, 0x0c, 0x06, 0x02, 0x14, 0x1c, 0x25,
#                  0x05, 0x09, 0x5d, 0x06, 0x04, 0x0b, 0x08, 0x04,
#                  0x0b, 0x07, 0x81, 0x1e, 0x09, 0x03, 0x1c, 0x09,
#                  0x01, 0x1e, 0xff]
#                     0     1     2     3     4     5     6     7     8     9     A     B     C     D     E     F
sample_conf_pkt = [0x10, 0x00, 0x03, 0x0a, 0x04, 0x0c, 0x26, 0x00, 0x06, 0x24, 0x1f, 0x04, 0x01, 0x00, 0x04, 0x04,
                   0x0d, 0x01, 0x01, 0x1e, 0x04, 0x01, 0x1c, 0x01, 0x01, 0x1e, 0xff]

weather_station = usb.core.find(idVendor=0x04f3, idProduct=0x0001)

if weather_station is None:
    raise ValueError('Device not found')

weather_station.set_configuration()

# Nothing to "read" from the device

# for bRequest in range(255):
#     try:
#         ret = weather_station.ctrl_transfer(0xc0, bRequest, 0, 0, 1)
#         print "bRequest ", bRequest
#         print ret
#     except Exception as e:
#         print "Exception caught: ", e
#         pass

# ctrl_transfer( bmRequestType, bmRequest, wValue, wIndex, nBytes)

for i in range(256):
    if i < 0xb0:
        continue
    print "Current try: ", hex(i)
    sample_conf_pkt[0x10] = i
    ret = weather_station.ctrl_transfer(0x40, 0x41, 0xfa54, 0, ''.join([chr(x) for x in sample_conf_pkt]))
    time.sleep(6)


print "done"

