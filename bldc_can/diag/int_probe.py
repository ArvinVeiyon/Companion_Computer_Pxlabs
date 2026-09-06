#!/usr/bin/env python3
"""Is GPIO25 (MCP2515 /INT) actively driven high, i.e. is the die powered?

A powered MCP2515 holds /INT high (push-pull) with no interrupt pending, so it
wins against a pull-down.  An unconnected/unpowered pin follows whatever bias we
apply.  SPI stays bound and idle throughout, so there is no MOSI to back-feed.
"""
import fcntl, os, struct, time
GET_LINE=0xC250B407; GET_VALUES=0xC010B40E
F_INPUT,F_PULL_UP,F_PULL_DOWN=1<<2,1<<8,1<<9
PINCONF="/sys/kernel/debug/pinctrl/1f000d0000.gpio-pinctrl-rp1/pinconf-pins"

def open_line(chip,offs,flags):
    off=list(offs)+[0]*(64-len(offs))
    b=struct.pack("64I",*off)+b"int_probe".ljust(32,b"\0")[:32]
    b+=struct.pack("QI5I",flags,0,0,0,0,0,0)+b"\0"*240
    b+=struct.pack("II5Ii",len(offs),0,0,0,0,0,0,0)
    return struct.unpack("i",fcntl.ioctl(chip,GET_LINE,b)[-4:])[0]

def val(fd): return struct.unpack("QQ",fcntl.ioctl(fd,GET_VALUES,struct.pack("QQ",0,1)))[0]&1

def bias(off):
    for l in open(PINCONF):
        if l.startswith(f"pin {off} ("):
            return ("pull up (1" in l, "pull down (1" in l)
    return (None,None)

chip=os.open("/dev/gpiochip4",os.O_RDWR)
for name,off in (("INT gpio25",25),("MISO gpio9",9)):
    out=[]
    for label,flag in (("pull-up",F_PULL_UP),("pull-down",F_PULL_DOWN)):
        fd=open_line(chip,[off],F_INPUT|flag); time.sleep(0.2)
        s="".join(str(val(fd)) for _ in range(10)); pu,pd=bias(off); os.close(fd)
        applied = (pu and not pd) if label=="pull-up" else (pd and not pu)
        out.append(f"{label}->{s}{'' if applied else '  [BIAS NOT APPLIED]'}")
    print(f"{name}:  "+"   ".join(out))
os.close(chip)
print("\npull-up 1s + pull-down 0s = floating (nothing driving it)")
print("pull-up 1s + pull-down 1s = actively driven HIGH  <- a powered MCP2515 /INT")
