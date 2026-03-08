#!/bin/bash

#/usr/local/bin/usr/bin/mavlink-routerd  #-e 192.168.192.63:14555 -e 192.168.192.247:14555  -e 0.0.0.0:14550 /dev/ttyAMA0:921600 &
#sleep 10
/usr/local/bin/MicroXRCEAgent serial --dev /dev/ttyAMA0 -b 115200  #/tmp/microxrceagent.log 2>&1 &

